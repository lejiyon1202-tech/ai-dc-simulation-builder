"""
DC 시뮬레이션 시나리오 생성 엔진
Claude API를 사용하여 4가지 평가 기법의 시나리오를 자동 생성합니다.
"""

import json
import time
import re
import anthropic
from flask import current_app
from app.services.prompts import SYSTEM_PROMPT, get_prompt


class ScenarioGenerator:
    """AI 기반 DC 시뮬레이션 시나리오 생성기"""

    def __init__(self):
        self.client = None
        self.model = None

    def _init_client(self):
        """Anthropic 클라이언트를 초기화합니다."""
        if self.client is None:
            api_key = current_app.config.get("ANTHROPIC_API_KEY")
            if not api_key:
                print("[ScenarioGenerator] ERROR: ANTHROPIC_API_KEY not set")
                raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")
            print(f"[ScenarioGenerator] API key loaded (len={len(api_key)})")
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = current_app.config.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    def generate(self, method: str, params: dict) -> dict:
        """
        시나리오를 생성합니다.

        Args:
            method: 평가 기법 (in_basket, role_playing, presentation, group_discussion)
            params: 생성 파라미터
                - evaluation_purpose: 평가 목적
                - target_level: 대상 직급
                - industry: 산업/업종
                - job_function: 직무
                - competencies: 평가 역량 리스트
                - difficulty: 난이도 (1-5)
                - duration: 시간(분)
                - 기법별 추가 파라미터

        Returns:
            생성된 시나리오 딕셔너리
        """
        self._init_client()

        prompt = get_prompt(method, params)
        start_time = time.time()

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        generation_time = time.time() - start_time
        response_text = response.content[0].text

        # JSON 파싱
        scenario = self._parse_json_response(response_text)

        # 메타데이터 추가
        scenario["_meta"] = {
            "method": method,
            "params": params,
            "generation_time_seconds": round(generation_time, 2),
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "model": self.model,
        }

        return scenario

    def generate_all(self, params: dict, methods: list = None) -> dict:
        """
        선택된 모든 기법의 시나리오를 한 번에 생성합니다.

        Args:
            params: 공통 파라미터
            methods: 생성할 기법 리스트 (기본: 4가지 전부)

        Returns:
            기법별 시나리오 딕셔너리
        """
        if methods is None:
            methods = ["in_basket", "role_playing", "presentation", "group_discussion"]

        results = {}
        errors = {}

        for method in methods:
            method_params = {**params}

            # 기법별 기본값 설정
            if method == "in_basket":
                method_params.setdefault("duration", 30)
                method_params.setdefault("doc_count", 10)
            elif method == "role_playing":
                method_params.setdefault("duration", 20)
                method_params.setdefault("rounds", 2)
            elif method == "presentation":
                method_params.setdefault("duration", 30)
            elif method == "group_discussion":
                method_params.setdefault("duration", 40)
                method_params.setdefault("participant_count", 5)
            elif method == "gd_assigned_role":
                method_params.setdefault("duration", 45)
                method_params.setdefault("participant_count", 5)
                method_params.setdefault("gd_type", "assigned_role")
            elif method == "gd_free_discussion":
                method_params.setdefault("duration", 45)
                method_params.setdefault("participant_count", 5)
                method_params.setdefault("gd_type", "free")
            elif method == "case_study":
                method_params.setdefault("duration", 60)

            try:
                results[method] = self.generate(method, method_params)
            except Exception as e:
                errors[method] = str(e)

        return {"scenarios": results, "errors": errors}

    def regenerate_part(self, method: str, params: dict, part: str, current_scenario: dict) -> dict:
        """
        시나리오의 특정 부분만 재생성합니다.

        Args:
            method: 평가 기법
            params: 원래 파라미터
            part: 재생성할 부분 (예: "documents", "evaluation_criteria")
            current_scenario: 현재 시나리오

        Returns:
            업데이트된 시나리오
        """
        self._init_client()

        context_json = json.dumps(current_scenario, ensure_ascii=False, indent=2)

        prompt = f"""다음은 현재 생성된 {method} 시나리오입니다:

```json
{context_json}
```

위 시나리오에서 '{part}' 부분만 새롭게 재생성해주세요.
나머지 부분은 유지하고, '{part}' 부분만 다른 내용으로 만들어주세요.
동일한 JSON 구조를 유지하되, '{part}' 키의 값만 새로운 내용으로 교체하세요.

'{part}' 부분만 JSON으로 응답하세요."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        new_part = self._parse_json_response(response.content[0].text)

        # 기존 시나리오에 새 부분 병합
        updated = {**current_scenario}
        if isinstance(new_part, dict):
            if part in new_part:
                updated[part] = new_part[part]
            else:
                updated[part] = new_part
        else:
            updated[part] = new_part

        return updated

    def customize_scenario(self, method: str, current_scenario: dict, instruction: str) -> dict:
        """
        사용자의 자유 지시에 따라 시나리오를 수정합니다.

        Args:
            method: 평가 기법
            current_scenario: 현재 시나리오
            instruction: 사용자의 수정 지시

        Returns:
            수정된 시나리오
        """
        self._init_client()

        context_json = json.dumps(current_scenario, ensure_ascii=False, indent=2)

        prompt = f"""다음은 현재 생성된 {method} 시나리오입니다:

```json
{context_json}
```

사용자의 수정 요청:
"{instruction}"

위 요청에 맞게 시나리오를 수정하세요.
수정된 전체 시나리오를 동일한 JSON 구조로 응답하세요."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        return self._parse_json_response(response.content[0].text)

    def _parse_json_response(self, text: str) -> dict:
        """AI 응답에서 JSON을 추출하고 파싱합니다."""
        # ```json ... ``` 블록 추출
        json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # JSON 배열이나 객체 직접 찾기
            json_match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                return {"raw_text": text, "parse_error": "JSON을 찾을 수 없습니다"}

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # 불완전한 JSON 복구 시도
            try:
                # 끝부분이 잘린 경우 닫기 시도
                fixed = json_str.rstrip()
                open_braces = fixed.count("{") - fixed.count("}")
                open_brackets = fixed.count("[") - fixed.count("]")
                fixed += "]" * open_brackets + "}" * open_braces
                return json.loads(fixed)
            except json.JSONDecodeError:
                return {"raw_text": text, "parse_error": str(e)}


# 싱글턴 인스턴스
_generator = None


def get_generator() -> ScenarioGenerator:
    """ScenarioGenerator 싱글턴 인스턴스를 반환합니다."""
    global _generator
    if _generator is None:
        _generator = ScenarioGenerator()
    return _generator
