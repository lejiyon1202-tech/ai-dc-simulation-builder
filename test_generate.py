"""
시나리오 생성 엔진 독립 테스트 스크립트
Flask 서버 없이 바로 시나리오를 생성하고 확인할 수 있습니다.

사용법:
    python test_generate.py
"""

import json
import os
import sys
import time
import re

import anthropic

# 프롬프트 모듈 직접 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from app.services.prompts import SYSTEM_PROMPT, get_prompt


def generate_scenario(method: str, params: dict) -> dict:
    """시나리오를 생성합니다."""
    client = anthropic.Anthropic()
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    prompt = get_prompt(method, params)

    print(f"\n  Claude API 호출 중... (모델: {model})")
    start = time.time()

    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    elapsed = time.time() - start
    text = response.content[0].text

    print(f"  완료! ({elapsed:.1f}초, 입력: {response.usage.input_tokens}토큰, 출력: {response.usage.output_tokens}토큰)")

    # JSON 파싱
    json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    json_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    return {"raw_text": text}


def main():
    # API 키 확인
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    print("=" * 60)
    print("DC 시뮬레이션 시나리오 생성 테스트")
    print("=" * 60)

    # 테스트 파라미터
    params = {
        "evaluation_purpose": "승진 심사",
        "target_level": "과장/팀장",
        "industry": "IT/소프트웨어",
        "job_function": "경영기획",
        "competencies": ["의사결정", "리더십", "커뮤니케이션", "문제해결", "전략적 사고"],
        "difficulty": 3,
        "duration": 30,
    }

    print(f"\n설정:")
    print(f"  평가 목적: {params['evaluation_purpose']}")
    print(f"  대상 직급: {params['target_level']}")
    print(f"  산업: {params['industry']}")
    print(f"  직무: {params['job_function']}")
    print(f"  역량: {', '.join(params['competencies'])}")
    print(f"  난이도: {params['difficulty']}/5")

    # 기법 선택
    print("\n어떤 기법을 테스트할까요?")
    print("  1. In-basket (서류함)")
    print("  2. Role-playing (역할극)")
    print("  3. Presentation (발표)")
    print("  4. Group Discussion (집단토론)")
    print("  5. 전부 다")

    choice = input("\n선택 (1-5): ").strip()

    methods_map = {
        "1": ["in_basket"],
        "2": ["role_playing"],
        "3": ["presentation"],
        "4": ["group_discussion"],
        "5": ["in_basket", "role_playing", "presentation", "group_discussion"],
    }

    methods = methods_map.get(choice, ["in_basket"])

    # 기법별 추가 파라미터
    method_names = {
        "in_basket": "In-basket (서류함)",
        "role_playing": "Role-playing (역할극)",
        "presentation": "Presentation (발표)",
        "group_discussion": "Group Discussion (집단토론)",
    }

    results = {}
    output_dir = os.path.join(os.path.dirname(__file__), "test_output")
    os.makedirs(output_dir, exist_ok=True)

    for method in methods:
        print(f"\n{'─' * 50}")
        print(f"생성 중: {method_names[method]}")
        print(f"{'─' * 50}")

        method_params = {**params}
        if method == "in_basket":
            method_params["doc_count"] = 8
        elif method == "role_playing":
            method_params["rounds"] = 2
        elif method == "group_discussion":
            method_params["participant_count"] = 5

        scenario = generate_scenario(method, method_params)
        results[method] = scenario

        # 결과 저장
        output_file = os.path.join(output_dir, f"{method}_scenario.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(scenario, f, ensure_ascii=False, indent=2)
        print(f"  저장됨: {output_file}")

        # 요약 출력
        if "raw_text" not in scenario:
            print(f"\n  제목: {scenario.get('title', 'N/A')}")
            if method == "in_basket":
                docs = scenario.get("documents", [])
                print(f"  서류 수: {len(docs)}개")
                for doc in docs[:3]:
                    print(f"    - [{doc.get('urgency', '?')}] {doc.get('subject', '')}")
                if len(docs) > 3:
                    print(f"    ... 외 {len(docs) - 3}개")
            elif method == "role_playing":
                rounds = scenario.get("rounds", [])
                print(f"  라운드 수: {len(rounds)}")
                for r in rounds:
                    cp = r.get("counterpart", {})
                    print(f"    - 라운드 {r.get('round_number')}: {cp.get('name', '')} ({cp.get('title', '')})")
            elif method == "presentation":
                mats = scenario.get("materials", [])
                print(f"  제공 자료: {len(mats)}개")
                qa = scenario.get("qa_questions", {})
                print(f"  질문: 기본 {len(qa.get('basic', []))}개 + 심화 {len(qa.get('advanced', []))}개")
            elif method == "group_discussion":
                topic = scenario.get("topic", {})
                print(f"  토론 주제: {topic.get('statement', 'N/A')}")
                cards = scenario.get("role_cards", [])
                print(f"  역할 카드: {len(cards)}개")
        else:
            print("  (JSON 파싱 실패 - raw text 저장됨)")

    print(f"\n{'=' * 60}")
    print(f"완료! 결과물 위치: {output_dir}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
