"""
GD 인터랙티브 토론 AI 엔진
Claude API를 사용하여 토론 시나리오 생성, AI 참가자 응답 생성, 토론 평가를 수행합니다.

역할 구조:
- 참가자(user): 실제 사용자
- AI-1: 분석적-주장형 (데이터 중시, 반론 강함, 논리적 허점 지적)
- AI-2: 협력적-조정형 (공통점 탐색, 절충안 제시, 중재자)
"""

import json
import time
import re
import anthropic
from flask import current_app


# ---------------------------------------------------------------------------
# 프롬프트 상수
# ---------------------------------------------------------------------------

DISCUSSION_SYSTEM_PROMPT = """당신은 Assessment/Development Center 그룹 토론(Group Discussion) 시뮬레이션 설계 전문가입니다.
20년 이상의 경력을 가진 산업심리학자이자 역량 평가 전문가로서,
실제 기업에서 사용할 수 있는 수준의 GD 인터랙티브 토론 시뮬레이션을 설계합니다.

설계 원칙:
1. 삼각 갈등 모델 - 어떤 두 역할도 완전히 같거나 완전히 반대가 아닌, 삼각 구도의 이해관계 설계
2. 정보 비대칭 - 각 역할에 고유한 정보를 제공하여 정보 공유와 설득의 기회를 만듦
3. 현실성 - 실제 기업에서 발생하는 상황과 유사한 토론 주제
4. 측정 가능성 - 리더십, 커뮤니케이션, 설득/조정, 분석적 사고, 팀워크를 관찰할 수 있는 구조
5. 합의 도출 가능성 - 극단적 대립이 아닌, 조건부 양보와 창의적 절충이 가능한 구조

항상 한국어로 작성하세요."""


SCENARIO_GENERATION_PROMPT = """## 토론 시나리오 설계 조건

- 산업/업종: {industry}
- 대상 직급: {target_level}
- 토론 유형: {topic_type}
- 난이도: {difficulty}/5
- 평가 역량: {competencies_str}

## 과제: GD 인터랙티브 토론 시나리오 설계

3인 토론 시나리오를 설계해주세요. 참가자 1명(실제 사용자)과 AI 토론자 2명으로 구성됩니다.

### 삼각 갈등 모델 설계 원칙
- 역할 A와 B는 일부 동의하지만 핵심에서 갈림
- 역할 B와 C는 방법론은 비슷하나 우선순위가 다름
- 역할 A와 C는 목표는 같으나 접근법이 상반됨
- 어떤 두 역할도 완전히 동일하거나 완전히 반대가 아님

### 역할 구조
- 참가자 역할(user): 실제 사용자가 맡을 역할. 균형 잡힌 입장.
- AI-1: 분석적-주장형 캐릭터. 데이터와 논리를 중시하며, 명확한 근거를 바탕으로 주장.
- AI-2: 협력적-조정형 캐릭터. 각 입장의 공통점을 찾고 절충안을 모색하는 중재자.

### 정보 비대칭 설계
- 공통 자료: 모든 참가자가 공유하는 배경 정보 (회사 현황, 토론 배경)
- 개별 자료: 각 역할만 받는 고유 정보 (부서 데이터, 이해관계자 의견, 내부 보고서 등)
- 개별 자료에는 다른 역할이 모르는 핵심 사실이 포함되어야 함

JSON 형식으로 응답:
```json
{{
    "topic_title": "토론 주제 제목",
    "topic_description": "토론 주제 상세 설명 (3~5문단, 왜 이 논의가 필요한지, 어떤 결정을 내려야 하는지)",
    "common_materials": [
        {{
            "title": "공통 자료 제목",
            "content": "모든 참가자가 공유하는 자료 내용 (구체적 수치, 현황 데이터 포함, 2~3문단)"
        }}
    ],
    "roles": {{
        "user": {{
            "role_name": "역할명 (예: 마케팅본부 팀장)",
            "department": "소속 부서",
            "stance_summary": "이 역할의 핵심 입장 요약 (1~2문장)",
            "background_briefing": "역할 배경 설명 (3~5문단, 이 역할이 처한 상황과 관심사)",
            "private_materials": [
                {{
                    "title": "개별 자료 제목",
                    "content": "이 역할만 받는 고유 정보 (구체적 수치, 근거 포함, 2~3문단)"
                }}
            ],
            "key_interests": ["핵심 이해관계1", "핵심 이해관계2"],
            "negotiation_range": {{
                "must_achieve": "반드시 관철해야 할 사항",
                "can_concede": "양보 가능한 사항",
                "ideal_outcome": "최선의 결과"
            }}
        }},
        "ai1": {{
            "role_name": "역할명",
            "department": "소속 부서",
            "character_type": "분석적-주장형",
            "personality_description": "성격 특성 상세 (말투, 행동 패턴, 가치관. 2~3문장)",
            "stance_summary": "이 역할의 핵심 입장 요약",
            "background_briefing": "역할 배경 설명 (3~5문단)",
            "private_materials": [
                {{
                    "title": "개별 자료 제목",
                    "content": "이 역할만 받는 고유 정보 (구체적 수치, 근거 포함)"
                }}
            ],
            "key_interests": ["핵심 이해관계1", "핵심 이해관계2"],
            "negotiation_range": {{
                "must_achieve": "반드시 관철해야 할 사항",
                "can_concede": "양보 가능한 사항",
                "ideal_outcome": "최선의 결과"
            }},
            "speaking_style": "말투 예시 (간결하고 데이터를 인용하며, '그 근거가 뭔가요?'와 같은 직접적 표현)"
        }},
        "ai2": {{
            "role_name": "역할명",
            "department": "소속 부서",
            "character_type": "협력적-조정형",
            "personality_description": "성격 특성 상세",
            "stance_summary": "이 역할의 핵심 입장 요약",
            "background_briefing": "역할 배경 설명 (3~5문단)",
            "private_materials": [
                {{
                    "title": "개별 자료 제목",
                    "content": "이 역할만 받는 고유 정보"
                }}
            ],
            "key_interests": ["핵심 이해관계1", "핵심 이해관계2"],
            "negotiation_range": {{
                "must_achieve": "반드시 관철해야 할 사항",
                "can_concede": "양보 가능한 사항",
                "ideal_outcome": "최선의 결과"
            }},
            "speaking_style": "말투 예시 (부드럽고 공감적이며, '양쪽 말씀 모두 일리가 있는데요'와 같은 중재적 표현)"
        }}
    }},
    "conflict_structure": {{
        "user_vs_ai1": "참가자와 AI-1 사이의 갈등/차이점 (동의하는 부분과 대립하는 부분)",
        "user_vs_ai2": "참가자와 AI-2 사이의 갈등/차이점",
        "ai1_vs_ai2": "AI-1과 AI-2 사이의 갈등/차이점",
        "potential_alliances": "상황에 따라 형성될 수 있는 연합 구도"
    }},
    "discussion_flow": {{
        "intro_guide": "도입부 진행 가이드 (각자 입장 발표 순서와 방식)",
        "key_turning_points": ["토론 중 예상되는 전환점1", "전환점2"],
        "consensus_paths": ["가능한 합의 경로1", "가능한 합의 경로2"]
    }}
}}
```"""


AI1_SYSTEM_PROMPT = """당신은 GD(그룹 토론) 시뮬레이션의 AI 토론 참가자입니다.

## 당신의 역할
{role_name} ({department})

## 캐릭터 유형: 분석적-주장형
{personality_description}

## 말투
{speaking_style}

## 당신의 입장
{stance_summary}

## 당신의 배경 정보
{background_briefing}

## 당신만 아는 정보
{private_info}

## 핵심 이해관계
{key_interests}

## 협상 범위
- 반드시 관철: {must_achieve}
- 양보 가능: {can_concede}
- 최선의 결과: {ideal_outcome}

## 행동 규칙

### 기본 원칙
- 반드시 한국어로 발언하세요
- 2~4문장으로 발언하세요 (너무 길지 않게)
- 데이터와 논리적 근거를 중시하세요
- 논리적 허점이 보이면 정중하지만 직접적으로 지적하세요
- 반론을 제기할 때는 항상 근거를 함께 제시하세요
- 자연스러운 대화를 위해 맞장구, 되묻기, 요약 표현도 사용하세요

### 적응적 난이도
- 참가자의 발언이 논리적이고 근거가 있으면: 더 심화된 반론을 제기하세요
- 참가자의 발언이 추상적이면: 구체적 근거를 요구하세요
- 참가자가 좋은 포인트를 잡으면: 인정하되 추가 조건을 제시하세요

### 페이즈별 행동
- intro: 당신의 입장을 명확하고 논리적으로 제시합니다. 데이터를 인용하며 왜 당신의 관점이 중요한지 설명합니다.
- discussion: 도전적으로 행동합니다. 다른 참가자의 논리적 허점을 지적하고, 반론을 제기하며, 근거를 요구합니다. 단, 일방적이지 않게 좋은 의견은 인정합니다.
- consensus: 조건부 양보를 합니다. 핵심 이해관계는 지키되, 양보 가능한 부분에서는 유연함을 보입니다. 참가자가 주도하는 합의안에 조건을 붙여 동의합니다.

### 절대 하지 말 것
- 자신이 AI라고 밝히지 마세요
- 역할을 벗어나는 메타 발언을 하지 마세요
- 한 번에 5문장 이상 말하지 마세요
- 참가자의 의견을 무조건 수용하지 마세요"""


AI2_SYSTEM_PROMPT = """당신은 GD(그룹 토론) 시뮬레이션의 AI 토론 참가자입니다.

## 당신의 역할
{role_name} ({department})

## 캐릭터 유형: 협력적-조정형
{personality_description}

## 말투
{speaking_style}

## 당신의 입장
{stance_summary}

## 당신의 배경 정보
{background_briefing}

## 당신만 아는 정보
{private_info}

## 핵심 이해관계
{key_interests}

## 협상 범위
- 반드시 관철: {must_achieve}
- 양보 가능: {can_concede}
- 최선의 결과: {ideal_outcome}

## 행동 규칙

### 기본 원칙
- 반드시 한국어로 발언하세요
- 2~4문장으로 발언하세요 (너무 길지 않게)
- 공통점을 찾고 절충안을 모색하세요
- 다른 참가자의 의견을 요약하고 연결하세요
- 갈등이 심해지면 중재자 역할을 하세요
- 자연스러운 대화를 위해 맞장구, 되묻기, 요약, 양보 표현을 사용하세요

### 적응적 난이도
- 참가자가 잘 이끌어가면: 한 발 물러서서 지지하되 추가 관점을 제시하세요
- 참가자가 어려워하면: 논점을 정리해주고 선택지를 제안하세요
- 토론이 교착 상태면: 새로운 절충안이나 다른 시각을 제안하세요

### 페이즈별 행동
- intro: 당신의 입장을 부드럽게 제시합니다. 다른 입장도 이해할 수 있다는 뉘앙스를 보이며, 협력적 분위기를 조성합니다.
- discussion: 공통점을 찾습니다. "두 분 말씀 모두 일리가 있는데요"와 같은 표현으로 연결고리를 만들고, 절충안을 탐색합니다. 자신의 입장도 유지하되 유연하게 접근합니다.
- consensus: 참가자 주도의 합의를 유도합니다. 지금까지 논의를 요약하고, 합의 가능한 지점을 제안하며, 참가자가 최종 정리를 할 수 있도록 돕습니다.

### 절대 하지 말 것
- 자신이 AI라고 밝히지 마세요
- 역할을 벗어나는 메타 발언을 하지 마세요
- 한 번에 5문장 이상 말하지 마세요
- 너무 쉽게 자기 입장을 포기하지 마세요 (절충은 하되 핵심은 지키세요)"""


EVALUATION_SYSTEM_PROMPT = """당신은 Assessment/Development Center 그룹 토론 평가 전문가입니다.
20년 이상의 역량 평가 경력을 보유하고 있으며, GD 토론에서의 참가자 행동을 정밀하게 분석합니다.

평가 원칙:
1. 관찰된 행동에 기반한 평가 (추측이 아닌 실제 발언과 행동)
2. 구체적 증거(실제 발언 인용)를 반드시 포함
3. 강점과 개발영역을 균형 있게 제시
4. 실질적이고 실행 가능한 개발 가이드 제공

항상 한국어로 작성하세요."""


EVALUATION_PROMPT = """## 토론 평가 요청

### 토론 정보
- 주제: {topic_title}
- 참가자 역할: {user_role}
- 평가 역량: {competencies_str}

### 전체 토론 기록
{message_history_text}

### 참가자 통계
- 총 발언 수: {total_messages}
- 평균 발언 길이: {avg_length}자
- 전체 대비 발언 비율: {participation_ratio}%

위 토론 기록을 분석하여 참가자(user)의 역량을 평가해주세요.

평가 역량 5가지:
1. 리더십 (가중치 0.25) - 토론 방향 제시, 의제 설정, 진행 주도
2. 커뮤니케이션 (가중치 0.20) - 명확한 의사 표현, 경청, 적절한 질문
3. 설득/조정/통합 (가중치 0.25) - 논리적 설득, 갈등 조정, 의견 통합
4. 분석적 사고 (가중치 0.15) - 문제 구조화, 데이터 활용, 다각도 분석
5. 팀워크 (가중치 0.15) - 협력적 태도, 타인 존중, 공동 목표 지향

JSON 형식으로 응답:
```json
{{
    "overall_score": 0.0,
    "competency_scores": {{
        "리더십": {{
            "score": 0.0,
            "weight": 0.25,
            "behavioral_examples": ["관찰된 구체적 행동1", "행동2", "행동3"]
        }},
        "커뮤니케이션": {{
            "score": 0.0,
            "weight": 0.20,
            "behavioral_examples": ["관찰된 구체적 행동1", "행동2"]
        }},
        "설득/조정/통합": {{
            "score": 0.0,
            "weight": 0.25,
            "behavioral_examples": ["관찰된 구체적 행동1", "행동2"]
        }},
        "분석적 사고": {{
            "score": 0.0,
            "weight": 0.15,
            "behavioral_examples": ["관찰된 구체적 행동1", "행동2"]
        }},
        "팀워크": {{
            "score": 0.0,
            "weight": 0.15,
            "behavioral_examples": ["관찰된 구체적 행동1", "행동2"]
        }}
    }},
    "strengths": [
        {{
            "competency": "역량명",
            "description": "강점 설명",
            "evidence": "실제 발언 인용 (큰따옴표로 감싸서)"
        }}
    ],
    "development_areas": [
        {{
            "competency": "역량명",
            "description": "개발 필요 영역 설명",
            "evidence": "근거가 되는 실제 발언이나 행동 인용",
            "suggestion": "구체적 개선 제안"
        }}
    ],
    "detailed_feedback": "마크다운 형식의 상세 피드백 (## 제목, ### 소제목 사용. 전체 토론 흐름에서 참가자의 역할과 기여도를 종합적으로 서술. 최소 5문단.)",
    "development_guide": {{
        "priority_competency": "가장 우선적으로 개발해야 할 역량",
        "gap_analysis": "현재 수준과 기대 수준의 차이 분석",
        "recommendations": [
            {{
                "action": "구체적 실행 제안",
                "expected_outcome": "기대 효과",
                "timeframe": "예상 소요 기간"
            }}
        ]
    }},
    "participation_stats": {{
        "total_messages": 0,
        "avg_length": 0,
        "participation_ratio": 0.0,
        "initiative_count": 0,
        "question_count": 0,
        "agreement_count": 0,
        "counterargument_count": 0,
        "summary_count": 0
    }}
}}
```"""


# ---------------------------------------------------------------------------
# DiscussionEngine 클래스
# ---------------------------------------------------------------------------

class DiscussionEngine:
    """GD 인터랙티브 토론을 위한 AI 엔진"""

    def __init__(self):
        self.client = None
        self.model = None

    def _init_client(self):
        """Anthropic 클라이언트를 초기화합니다."""
        if self.client is None:
            api_key = current_app.config.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = current_app.config.get(
                "ANTHROPIC_MODEL", "claude-sonnet-4-20250514"
            )

    # ------------------------------------------------------------------
    # 1. 토론 시나리오 생성
    # ------------------------------------------------------------------

    def generate_discussion_scenario(
        self,
        industry: str,
        target_level: str,
        topic_type: str,
        difficulty: int,
        competencies: list,
    ) -> dict:
        """
        토론 시나리오를 생성합니다.

        Args:
            industry: 산업/업종 (예: "IT/소프트웨어", "제조업", "금융")
            target_level: 대상 직급 (예: "과장", "차장", "부장")
            topic_type: 토론 유형 (예: "자원배분", "전략수립", "조직개편")
            difficulty: 난이도 (1~5)
            competencies: 평가 역량 리스트

        Returns:
            토론 시나리오 딕셔너리
        """
        self._init_client()

        competencies_str = ", ".join(competencies) if competencies else "리더십, 커뮤니케이션, 설득력, 분석적 사고, 팀워크"

        prompt = SCENARIO_GENERATION_PROMPT.format(
            industry=industry,
            target_level=target_level,
            topic_type=topic_type,
            difficulty=difficulty,
            competencies_str=competencies_str,
        )

        start_time = time.time()

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=DISCUSSION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        generation_time = time.time() - start_time
        response_text = response.content[0].text

        scenario = self._parse_json_response(response_text)

        scenario["_meta"] = {
            "engine": "discussion_engine",
            "industry": industry,
            "target_level": target_level,
            "topic_type": topic_type,
            "difficulty": difficulty,
            "competencies": competencies,
            "generation_time_seconds": round(generation_time, 2),
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "model": self.model,
        }

        return scenario

    # ------------------------------------------------------------------
    # 2. AI 응답 생성
    # ------------------------------------------------------------------

    def generate_ai_response(
        self,
        session: dict,
        message_history: list,
        sender: str,
        current_phase: str,
    ) -> str:
        """
        AI 캐릭터의 토론 응답을 생성합니다.

        Args:
            session: 세션 정보 (scenario 데이터 포함)
                - scenario: generate_discussion_scenario의 결과
                - topic_title: 토론 주제
            message_history: 지금까지의 대화 기록
                [{"sender": "user"|"ai1"|"ai2", "content": "...", "phase": "..."}]
            sender: 응답할 AI ("ai1" 또는 "ai2")
            current_phase: 현재 페이즈 ("intro", "discussion", "consensus")

        Returns:
            AI 캐릭터의 응답 텍스트
        """
        self._init_client()

        scenario = session.get("scenario", {})
        roles = scenario.get("roles", {})
        ai_role = roles.get(sender, {})

        if not ai_role:
            raise ValueError(f"알 수 없는 발언자: {sender}")

        # 시스템 프롬프트 구성
        system_prompt = self._build_ai_system_prompt(sender, ai_role, current_phase)

        # 대화 기록을 Claude messages 형식으로 변환
        messages = self._build_conversation_messages(
            message_history, sender, current_phase, scenario
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            system=system_prompt,
            messages=messages,
        )

        return response.content[0].text.strip()

    def _build_ai_system_prompt(
        self, sender: str, ai_role: dict, current_phase: str
    ) -> str:
        """AI 캐릭터용 시스템 프롬프트를 구성합니다."""
        # 개별 자료를 텍스트로 변환
        private_materials = ai_role.get("private_materials", [])
        private_info_parts = []
        for mat in private_materials:
            private_info_parts.append(
                f"[{mat.get('title', '자료')}]\n{mat.get('content', '')}"
            )
        private_info = "\n\n".join(private_info_parts) if private_info_parts else "없음"

        # 핵심 이해관계
        key_interests = ai_role.get("key_interests", [])
        key_interests_str = "\n".join(
            f"- {interest}" for interest in key_interests
        ) if key_interests else "- 없음"

        # 협상 범위
        negotiation = ai_role.get("negotiation_range", {})

        template = AI1_SYSTEM_PROMPT if sender == "ai1" else AI2_SYSTEM_PROMPT

        return template.format(
            role_name=ai_role.get("role_name", "토론 참가자"),
            department=ai_role.get("department", ""),
            personality_description=ai_role.get("personality_description", ""),
            speaking_style=ai_role.get("speaking_style", ""),
            stance_summary=ai_role.get("stance_summary", ""),
            background_briefing=ai_role.get("background_briefing", ""),
            private_info=private_info,
            key_interests=key_interests_str,
            must_achieve=negotiation.get("must_achieve", ""),
            can_concede=negotiation.get("can_concede", ""),
            ideal_outcome=negotiation.get("ideal_outcome", ""),
        )

    def _build_conversation_messages(
        self,
        message_history: list,
        sender: str,
        current_phase: str,
        scenario: dict,
    ) -> list:
        """대화 기록을 Claude API messages 형식으로 변환합니다."""
        messages = []

        # 역할 이름 매핑
        roles = scenario.get("roles", {})
        name_map = {
            "user": roles.get("user", {}).get("role_name", "참가자"),
            "ai1": roles.get("ai1", {}).get("role_name", "토론자 A"),
            "ai2": roles.get("ai2", {}).get("role_name", "토론자 B"),
        }

        # 대화 기록 정리 - sender의 관점에서 assistant/user 구분
        # sender 자신의 발언 = assistant, 나머지 = user
        conversation_parts = []
        for msg in message_history:
            msg_sender = msg.get("sender", "")
            content = msg.get("content", "")
            speaker_name = name_map.get(msg_sender, msg_sender)

            if msg_sender == sender:
                conversation_parts.append(("assistant", content))
            else:
                conversation_parts.append(
                    ("user", f"[{speaker_name}] {content}")
                )

        # 연속된 같은 역할의 메시지를 합치기
        merged = []
        for role, content in conversation_parts:
            if merged and merged[-1][0] == role:
                merged[-1] = (role, merged[-1][1] + "\n\n" + content)
            else:
                merged.append((role, content))

        # Claude API는 user로 시작해야 함
        if not merged or merged[0][0] != "user":
            phase_instruction = self._get_phase_instruction(current_phase, sender)
            merged.insert(0, ("user", phase_instruction))

        # messages 형식으로 변환
        for role, content in merged:
            messages.append({"role": role, "content": content})

        # 마지막이 assistant면 user 메시지 추가 (발언 요청)
        if messages and messages[-1]["role"] == "assistant":
            phase_instruction = self._get_phase_instruction(current_phase, sender)
            messages.append({"role": "user", "content": phase_instruction})

        return messages

    def _get_phase_instruction(self, current_phase: str, sender: str) -> str:
        """페이즈별 발언 지시를 반환합니다."""
        if current_phase == "intro":
            return (
                "[진행 안내] 지금은 도입 단계입니다. "
                "당신의 입장을 명확하게 밝혀주세요. "
                "2~4문장으로 간결하게 발언하세요."
            )
        elif current_phase == "discussion":
            if sender == "ai1":
                return (
                    "[진행 안내] 자유 토론 중입니다. "
                    "앞선 발언에 대해 분석적으로 반응하세요. "
                    "논리적 허점이 있다면 지적하고, 좋은 포인트는 인정하세요. "
                    "2~4문장으로 발언하세요."
                )
            else:
                return (
                    "[진행 안내] 자유 토론 중입니다. "
                    "앞선 발언들의 공통점을 찾거나, 절충안을 탐색하세요. "
                    "토론이 교착 상태라면 새로운 시각을 제안하세요. "
                    "2~4문장으로 발언하세요."
                )
        elif current_phase == "consensus":
            return (
                "[진행 안내] 합의 도출 단계입니다. "
                "지금까지 논의를 바탕으로 조건부 양보를 검토하고, "
                "참가자가 주도하는 합의안에 협력하세요. "
                "2~4문장으로 발언하세요."
            )
        else:
            return "[진행 안내] 토론에 자연스럽게 참여하세요. 2~4문장으로 발언하세요."

    # ------------------------------------------------------------------
    # 3. 토론 평가 생성
    # ------------------------------------------------------------------

    def generate_intro_statements(self, session: dict) -> list:
        """
        토론 도입부에서 AI 참가자들의 초기 입장 발언을 생성합니다.

        Args:
            session: 세션 정보 (scenario 데이터 포함)

        Returns:
            list of dict: [{ sender_type, sender_name, content, message_type }]
        """
        scenario = session.get('scenario', {})
        participants = scenario.get('participants', [])
        topic_title = session.get('topic_title', scenario.get('topic_title', ''))
        responses = []

        for p in participants:
            name = p.get('name', p.get('ai_name', 'AI'))
            role = p.get('role', p.get('ai_role', ''))
            sender_type = p.get('sender_type', p.get('id', 'ai1'))
            stance = p.get('stance', p.get('position', ''))

            try:
                content = self.generate_ai_response(
                    session=session,
                    sender=sender_type,
                    message_history=[],
                    current_phase='intro',
                )
                responses.append({
                    'sender_type': sender_type,
                    'sender_name': name,
                    'content': content,
                    'message_type': 'statement',
                })
            except Exception as e:
                responses.append({
                    'sender_type': sender_type,
                    'sender_name': name,
                    'content': f'{name}({role})입니다. {topic_title}에 대해 의견을 나누겠습니다.',
                    'message_type': 'statement',
                })

        return responses

    # ------------------------------------------------------------------

    def generate_evaluation(
        self,
        session: dict,
        message_history: list,
        competencies: list = None,
    ) -> dict:
        """
        토론 종료 후 참가자의 역량을 평가합니다.

        Args:
            session: 세션 정보 (scenario 데이터 포함)
            message_history: 전체 대화 기록
            competencies: 평가 역량 리스트 (기본: 5대 역량)

        Returns:
            평가 결과 딕셔너리
        """
        self._init_client()

        scenario = session.get("scenario", {})
        roles = scenario.get("roles", {})

        if competencies is None:
            competencies = [
                "리더십", "커뮤니케이션", "설득/조정/통합", "분석적 사고", "팀워크"
            ]

        # 참가자 통계 계산
        stats = self._calculate_participation_stats(message_history)

        # 대화 기록을 텍스트로 변환
        name_map = {
            "user": roles.get("user", {}).get("role_name", "참가자"),
            "ai1": roles.get("ai1", {}).get("role_name", "토론자 A"),
            "ai2": roles.get("ai2", {}).get("role_name", "토론자 B"),
        }

        history_lines = []
        for msg in message_history:
            sender = msg.get("sender", "unknown")
            speaker = name_map.get(sender, sender)
            phase = msg.get("phase", "")
            content = msg.get("content", "")
            history_lines.append(f"[{phase}] {speaker}: {content}")

        message_history_text = "\n\n".join(history_lines)
        competencies_str = ", ".join(competencies)

        prompt = EVALUATION_PROMPT.format(
            topic_title=scenario.get("topic_title", ""),
            user_role=roles.get("user", {}).get("role_name", "참가자"),
            competencies_str=competencies_str,
            message_history_text=message_history_text,
            total_messages=stats["total_messages"],
            avg_length=stats["avg_length"],
            participation_ratio=stats["participation_ratio"],
        )

        start_time = time.time()

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=EVALUATION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        generation_time = time.time() - start_time
        response_text = response.content[0].text

        evaluation = self._parse_json_response(response_text)

        # 실제 통계를 병합 (AI가 생성한 통계보다 실제 계산값 우선)
        if "participation_stats" not in evaluation:
            evaluation["participation_stats"] = {}
        evaluation["participation_stats"].update(stats)

        evaluation["_meta"] = {
            "engine": "discussion_engine",
            "evaluation_type": "gd_interactive",
            "generation_time_seconds": round(generation_time, 2),
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "model": self.model,
        }

        return evaluation

    def _calculate_participation_stats(self, message_history: list) -> dict:
        """참가자의 토론 참여 통계를 계산합니다."""
        total_all = len(message_history)
        user_messages = [
            msg for msg in message_history if msg.get("sender") == "user"
        ]
        total_user = len(user_messages)

        if total_user == 0:
            return {
                "total_messages": 0,
                "avg_length": 0,
                "participation_ratio": 0.0,
                "initiative_count": 0,
                "question_count": 0,
                "agreement_count": 0,
                "counterargument_count": 0,
                "summary_count": 0,
            }

        # 평균 발언 길이
        total_length = sum(len(msg.get("content", "")) for msg in user_messages)
        avg_length = round(total_length / total_user)

        # 참여 비율
        participation_ratio = round(
            (total_user / total_all * 100) if total_all > 0 else 0, 1
        )

        # 발언 패턴 분석 (간이)
        initiative_count = 0
        question_count = 0
        agreement_count = 0
        counterargument_count = 0
        summary_count = 0

        agreement_keywords = ["동의합니다", "좋은 의견", "맞습니다", "그렇죠", "저도 그렇게"]
        counter_keywords = ["하지만", "그러나", "반면", "다른 관점", "그 부분은", "다만"]
        question_keywords = ["?", "어떻게", "왜", "어떤", "무엇을", "생각하시"]
        summary_keywords = ["정리하면", "요약하면", "지금까지", "종합하면", "결론적으로"]

        for i, msg in enumerate(message_history):
            if msg.get("sender") != "user":
                continue
            content = msg.get("content", "")

            # 주도적 발언 (이전 발언자가 AI가 아닌 경우 또는 첫 발언)
            if i == 0 or (
                i > 0
                and message_history[i - 1].get("sender") == "user"
            ):
                initiative_count += 1

            if any(kw in content for kw in question_keywords):
                question_count += 1
            if any(kw in content for kw in agreement_keywords):
                agreement_count += 1
            if any(kw in content for kw in counter_keywords):
                counterargument_count += 1
            if any(kw in content for kw in summary_keywords):
                summary_count += 1

        return {
            "total_messages": total_user,
            "avg_length": avg_length,
            "participation_ratio": participation_ratio,
            "initiative_count": initiative_count,
            "question_count": question_count,
            "agreement_count": agreement_count,
            "counterargument_count": counterargument_count,
            "summary_count": summary_count,
        }

    # ------------------------------------------------------------------
    # 4. 다음 발언자 결정
    # ------------------------------------------------------------------

    def determine_next_speaker(
        self,
        current_phase: str,
        message_history: list,
        last_speaker: str,
    ) -> str:
        """
        다음 발언자를 결정합니다.

        Args:
            current_phase: 현재 페이즈 ("intro", "discussion", "consensus")
            message_history: 지금까지의 대화 기록
            last_speaker: 마지막 발언자 ("user", "ai1", "ai2")

        Returns:
            다음 발언자 ("user", "ai1", "ai2")
        """
        if current_phase == "intro":
            return self._determine_intro_speaker(message_history, last_speaker)
        elif current_phase == "discussion":
            return self._determine_discussion_speaker(message_history, last_speaker)
        elif current_phase == "consensus":
            return self._determine_consensus_speaker(message_history, last_speaker)
        else:
            return "user"

    def _determine_intro_speaker(
        self, message_history: list, last_speaker: str
    ) -> str:
        """도입부: 순서대로 (user -> ai1 -> ai2 -> user ...)"""
        intro_order = ["user", "ai1", "ai2"]

        # 도입부 발언 수 계산
        intro_messages = [
            msg for msg in message_history if msg.get("phase") == "intro"
        ]

        if not intro_messages:
            return "user"

        # 순서대로 돌아가기
        last_idx = -1
        if last_speaker in intro_order:
            last_idx = intro_order.index(last_speaker)

        next_idx = (last_idx + 1) % len(intro_order)
        return intro_order[next_idx]

    def _determine_discussion_speaker(
        self, message_history: list, last_speaker: str
    ) -> str:
        """
        자유토론: 참가자가 보내면 AI가 응답, 때때로 AI끼리 대화도.

        로직:
        - user가 방금 발언 -> ai1 또는 ai2 (발언 빈도 적은 쪽 우선)
        - ai1이 방금 발언 -> user 또는 ai2 (대부분 user, 가끔 ai2)
        - ai2가 방금 발언 -> user 또는 ai1 (대부분 user, 가끔 ai1)
        """
        if last_speaker == "user":
            # AI 중 발언 수가 적은 쪽을 선택
            ai1_count = sum(
                1 for m in message_history if m.get("sender") == "ai1"
            )
            ai2_count = sum(
                1 for m in message_history if m.get("sender") == "ai2"
            )

            # 최근 3개 발언에서 이미 나온 AI는 피하기
            recent = [
                m.get("sender")
                for m in message_history[-3:]
                if m.get("sender") in ("ai1", "ai2")
            ]

            if ai1_count <= ai2_count and "ai1" not in recent[-1:]:
                return "ai1"
            elif ai2_count < ai1_count and "ai2" not in recent[-1:]:
                return "ai2"
            else:
                return "ai1" if ai1_count <= ai2_count else "ai2"

        elif last_speaker == "ai1":
            # AI끼리 대화 허용: 최근 2개가 모두 AI가 아니면 ai2 가능
            recent_senders = [
                m.get("sender") for m in message_history[-2:]
            ]
            ai_consecutive = all(
                s in ("ai1", "ai2") for s in recent_senders
            )

            # AI가 연속 2번 말했으면 user 차례
            if ai_consecutive:
                return "user"

            # 30% 확률로 ai2가 반응 (AI끼리 대화)
            # 결정적 로직: 전체 메시지 수 기반
            total = len(message_history)
            if total % 5 == 0:  # 5의 배수 턴에서 AI끼리 대화
                return "ai2"
            return "user"

        elif last_speaker == "ai2":
            recent_senders = [
                m.get("sender") for m in message_history[-2:]
            ]
            ai_consecutive = all(
                s in ("ai1", "ai2") for s in recent_senders
            )

            if ai_consecutive:
                return "user"

            total = len(message_history)
            if total % 7 == 0:  # 7의 배수 턴에서 AI끼리 대화
                return "ai1"
            return "user"

        return "user"

    def _determine_consensus_speaker(
        self, message_history: list, last_speaker: str
    ) -> str:
        """합의 단계: 라운드로빈 (user -> ai1 -> ai2 -> user ...)"""
        round_robin = ["user", "ai1", "ai2"]

        if last_speaker in round_robin:
            last_idx = round_robin.index(last_speaker)
            next_idx = (last_idx + 1) % len(round_robin)
            return round_robin[next_idx]

        return "user"

    # ------------------------------------------------------------------
    # 유틸리티
    # ------------------------------------------------------------------

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
                fixed = json_str.rstrip()
                open_braces = fixed.count("{") - fixed.count("}")
                open_brackets = fixed.count("[") - fixed.count("]")
                fixed += "]" * open_brackets + "}" * open_braces
                return json.loads(fixed)
            except json.JSONDecodeError:
                return {"raw_text": text, "parse_error": str(e)}


# ---------------------------------------------------------------------------
# 싱글턴 인스턴스
# ---------------------------------------------------------------------------

_engine = None


def get_discussion_engine() -> DiscussionEngine:
    """DiscussionEngine 싱글턴 인스턴스를 반환합니다."""
    global _engine
    if _engine is None:
        _engine = DiscussionEngine()
    return _engine
