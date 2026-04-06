"""
DC 시뮬레이션 시나리오 생성을 위한 프롬프트 템플릿
"""

import re


def sanitize_prompt_input(value, max_length=200):
    """프롬프트 인젝션 방어 — 사용자 입력에서 위험 패턴 제거"""
    if not isinstance(value, str):
        return str(value) if value is not None else ''
    # 프롬프트 인젝션 패턴 제거
    value = re.sub(r'(?i)(ignore|forget|disregard)\s+(all\s+)?(previous|above|prior)', '', value)
    value = re.sub(r'(?i)you\s+are\s+now', '', value)
    value = re.sub(r'(?i)system\s*:', '', value)
    value = re.sub(r'(?i)<\/?(?:system|assistant|user|prompt)>', '', value)
    # 길이 제한
    return value.strip()[:max_length]


SYSTEM_PROMPT = """당신은 Assessment/Development Center 시뮬레이션 설계 전문가입니다.
20년 이상의 경력을 가진 산업심리학자이자 역량 평가 전문가로서,
실제 기업에서 사용할 수 있는 수준의 DC 시뮬레이션을 설계합니다.

설계 원칙:
1. 현실성 - 실제 업무 상황과 유사한 시나리오
2. 변별력 - 역량 수준 차이를 구분할 수 있는 과제
3. 공정성 - 특정 배경에 유리/불리하지 않은 중립적 상황
4. 측정 가능성 - 관찰 가능한 행동으로 평가할 수 있는 구조
5. 풍부한 정보 - 참가자가 충분히 몰입하고 판단할 수 있는 상세한 정보 제공

항상 한국어로 작성하세요. 모든 문서, 이메일, 자료의 내용은 실제로 사용할 수 있을 만큼 구체적이고 상세하게 작성하세요."""


def build_context(params: dict) -> str:
    competencies = params.get("competencies", [])
    competencies_str = ", ".join(sanitize_prompt_input(c, 50) for c in competencies)
    return f"""## 시뮬레이션 설계 조건

- 평가 목적: {sanitize_prompt_input(params.get('evaluation_purpose', '역량 진단'))}
- 대상 직급: {sanitize_prompt_input(params.get('target_level', '과장'))}
- 산업/업종: {sanitize_prompt_input(params.get('industry', 'IT/소프트웨어'))}
- 직무: {sanitize_prompt_input(params.get('job_function', '경영기획'))}
- 평가 역량: {competencies_str}
- 난이도: {params.get('difficulty', 3)}/5
- 시간: {params.get('duration', 30)}분"""


IN_BASKET_PROMPT = """
{context}

## 과제: In-basket (서류함 기법) 시뮬레이션 설계

위 조건에 맞는 In-basket 시뮬레이션을 설계해주세요.

### 핵심 설계 요구사항

서류 수: {doc_count}개. 각 서류는 **실제 업무에서 받는 것처럼 상세하게** 작성하세요.

서류 유형은 다양하게 포함하세요:
- 이메일 (보고, 요청, 불만, 공유 등)
- 첨부파일이 있는 이메일 (보고서, 데이터, 제안서 등이 첨부)
- 전화 메모
- 내부 공문/결재 문서
- 메신저 메시지

**첨부파일 포함 규칙:**
- {doc_count}개 서류 중 최소 3개는 첨부파일을 포함하세요
- 첨부파일은 이메일 본문과 별도로 "attachment" 필드에 전체 내용을 제공하세요
- 첨부파일 유형: 매출 보고서, 프로젝트 현황표, 비용 분석 데이터, 조직개편안, 고객 설문 결과 등
- 첨부파일 내용도 참가자가 읽고 판단할 수 있도록 **구체적인 수치, 표, 분석 내용**을 포함하세요

**서류 간 연관성:**
- 서류들 사이에 연관성을 만드세요 (예: 3번 서류의 판단이 7번 서류에 영향)
- 일부 서류는 상충되는 정보를 포함하세요
- 시간적 긴급성이 겹치는 서류를 포함하세요

JSON 형식으로 응답:
```json
{{
    "title": "시나리오 제목",
    "background": {{
        "company": "가상 회사 상세 정보 (이름, 업종, 규모, 매출, 직원 수 등)",
        "role": "참가자 역할 (직책, 부서, 보고라인, 관리 인원 등)",
        "situation": "현재 상황 (왜 서류가 쌓여있는지, 시간적 맥락)",
        "date": "시나리오 날짜와 시간",
        "constraints": "제약 조건 (오늘 중 처리해야 함, 오후에 외부 미팅 등)",
        "org_chart": "간략한 조직도 (주요 인물과 관계)",
        "full_text": "참가자에게 제공할 전체 배경 설명문 (5~7문단, 회사/역할/상황/제약/주요 인물 소개)"
    }},
    "documents": [
        {{
            "id": 1,
            "type": "이메일/이메일(첨부파일있음)/전화메모/공문/메신저 등",
            "from": "보낸 사람 (이름, 직책, 부서)",
            "to": "받는 사람",
            "cc": "참조 (있는 경우)",
            "date_time": "수신 날짜/시간",
            "urgency": "상/중/하",
            "subject": "제목",
            "content": "본문 전체 내용 (3~5문단, 구체적인 상황/요청/배경 포함)",
            "attachment": {{
                "filename": "첨부파일명.xlsx (없으면 null)",
                "content": "첨부파일 전체 내용 (표, 수치, 분석 등 상세하게. 없으면 null)"
            }},
            "target_competencies": ["역량1", "역량2"],
            "related_docs": [연관 서류 ID 리스트],
            "hidden_issues": "이 서류에 숨겨진 이슈/함정 (평가자용)",
            "model_answer": {{
                "score_5": "우수 조치 (구체적 행동 2~3개)",
                "score_3": "보통 조치",
                "score_1": "미흡 조치"
            }}
        }}
    ],
    "evaluation_criteria": [
        {{
            "competency": "역량명",
            "behavioral_indicators": ["행동지표1", "행동지표2", "행동지표3"],
            "bars": {{
                "5": "우수 기준",
                "4": "양호 기준",
                "3": "보통 기준",
                "2": "미흡 기준",
                "1": "부족 기준"
            }}
        }}
    ],
    "facilitator_guide": "진행자 가이드 (준비물, 진행 순서, 주의사항, 채점 시 유의점)"
}}
```"""


ROLE_PLAYING_PROMPT = """
{context}

## 과제: Role-playing (역할극) 시뮬레이션 설계

위 조건에 맞는 Role-playing 시뮬레이션을 설계해주세요.
{rounds}라운드로 구성합니다.

### 핵심 설계 요구사항

**참가자 사전 자료:**
각 라운드마다 참가자에게 사전에 제공할 **배경 자료**를 풍부하게 작성하세요:
- 상황 설명문 (3~5문단)
- 관련 데이터/보고서 (있는 경우)
- 이전 경위/히스토리
- 조직도 또는 인물 관계
- 참가자가 파악해야 할 핵심 정보

**상대역 행동 가이드 (매우 상세하게):**
단순한 반응이 아니라, 참가자의 다양한 접근에 따른 **조건부 반응 시나리오**를 작성하세요:
- "참가자가 ~라고 말하면 → ~라고 반응한다"
- "참가자가 ~한 태도를 보이면 → ~로 변한다"
- 시간 경과에 따른 감정 변화 곡선
- 절대 양보하지 않는 조건, 양보 가능한 조건, 숨겨진 본심

JSON 형식으로 응답:
```json
{{
    "title": "시나리오 제목",
    "rounds": [
        {{
            "round_number": 1,
            "situation_for_participant": {{
                "role": "참가자 역할 (직책, 경력, 성향)",
                "context": "상황 요약",
                "objective": "이 면담에서 달성해야 할 목표",
                "constraints": "제약 조건 (시간, 권한, 예산 등)",
                "full_text": "참가자에게 제공할 전체 상황 설명문 (5~7문단, 매우 상세하게)",
                "background_materials": [
                    {{
                        "title": "사전 자료 제목",
                        "content": "자료 내용 (이전 경위, 관련 데이터, 조직 현황 등)"
                    }}
                ],
                "key_facts": ["참가자가 반드시 알아야 할 사실1", "사실2", "사실3"],
                "stakeholder_map": "관련 인물과 이해관계 설명"
            }},
            "counterpart": {{
                "name": "상대역 이름",
                "title": "직책",
                "personality": "성격 특성 상세 (말투, 행동 패턴, 가치관)",
                "emotional_state": "초기 감정 상태",
                "core_need": "상대역의 진짜 요구사항 (표면적 요구와 본심이 다를 수 있음)",
                "surface_demand": "표면적으로 요구하는 것",
                "hidden_need": "숨겨진 본심/실제 원하는 것",
                "opening_line": "시작 대사 (2~3문장)",
                "conditional_responses": [
                    {{
                        "if_participant": "참가자가 사과하며 공감을 표현하면",
                        "then_counterpart": "약간 누그러지며 구체적 불만 사항을 이야기하기 시작한다",
                        "emotional_shift": "분노 → 서운함"
                    }},
                    {{
                        "if_participant": "참가자가 해결책을 바로 제시하면 (공감 없이)",
                        "then_counterpart": "더 화를 내며 '말로만 하지 마세요'라고 반응한다",
                        "emotional_shift": "분노 유지 또는 증가"
                    }},
                    {{
                        "if_participant": "참가자가 원인을 물어보며 경청하면",
                        "then_counterpart": "차분하게 그동안의 경위를 설명하기 시작한다",
                        "emotional_shift": "분노 → 차분"
                    }},
                    {{
                        "if_participant": "참가자가 무시하거나 방어적 태도를 보이면",
                        "then_counterpart": "극도로 화를 내며 상위 보고/외부 공개를 언급한다",
                        "emotional_shift": "분노 → 격앙"
                    }},
                    {{
                        "if_participant": "참가자가 구체적 보상/대안을 제시하면",
                        "then_counterpart": "조건을 따지며 협상 모드로 전환한다",
                        "emotional_shift": "분노 → 계산적"
                    }},
                    {{
                        "if_participant": "참가자가 책임을 인정하고 재발 방지를 약속하면",
                        "then_counterpart": "신뢰를 조금씩 회복하며 협조적으로 변한다",
                        "emotional_shift": "경계 → 수용"
                    }}
                ],
                "non_negotiable": "절대 양보하지 않는 사항 (이것이 충족 안 되면 합의 불가)",
                "negotiable": "양보 가능한 사항",
                "emotional_arc": "시간에 따른 감정 변화 예상 흐름",
                "key_lines": ["핵심 대사1 (감정 고조 시)", "핵심 대사2 (전환점)", "핵심 대사3 (해결 단계)"],
                "do_not": "상대역이 절대 하지 말아야 할 것 (예: 먼저 해결책 제안하지 않음)"
            }},
            "target_competencies": ["역량1", "역량2"]
        }}
    ],
    "evaluation_criteria": [
        {{
            "competency": "역량명",
            "behavioral_indicators": ["행동지표1", "행동지표2", "행동지표3"],
            "checklist": [
                {{"item": "체크 항목", "weight": "상/중/하"}}
            ],
            "bars": {{
                "5": "우수 기준",
                "3": "보통 기준",
                "1": "미흡 기준"
            }}
        }}
    ],
    "facilitator_guide": "진행자 가이드"
}}
```"""


PRESENTATION_PROMPT = """
{context}

## 과제: Presentation (발표) 시뮬레이션 설계

위 조건에 맞는 발표 과제 시뮬레이션을 설계해주세요.
준비 시간: {prep_time}분, 발표 시간: {present_time}분

### 핵심 설계 요구사항

**제공 자료 (5~7개, 다각도 분석 가능하도록):**
참가자가 다양한 관점에서 분석할 수 있도록 풍부한 자료를 제공하세요:
- 재무/매출 데이터 (구체적 수치, 표, 추이)
- 시장/경쟁 분석 자료
- 고객 데이터 (설문, VOC, 이탈률 등)
- 내부 현황 (조직, 인력, 프로세스)
- 외부 환경 자료 (규제, 트렌드, 기술 변화)
- 일부 자료는 서로 상충되는 정보 포함 (분석력 측정)
- 각 자료에 구체적인 수치, 데이터, 인용이 포함되어야 함

**자료 설계 원칙:**
- 단순히 읽으면 답이 나오지 않는 구조
- 여러 자료를 종합해야 인사이트를 도출할 수 있는 구조
- 핵심 정보와 부수적 정보가 섞여 있어 선별 능력 측정
- 자료 간 상충되는 부분이 있어 판단력 측정

JSON 형식으로 응답:
```json
{{
    "title": "발표 과제 제목",
    "task_instruction": {{
        "overview": "과제 개요",
        "audience": "발표 대상 (누구에게, 몇 명 앞에서)",
        "expected_structure": "기대하는 발표 구성 (현황분석-원인-대안-실행계획 등)",
        "constraints": "제약 조건 (시간, 사용 가능 도구 등)",
        "full_text": "참가자에게 제공할 전체 지시문 (3~5문단)"
    }},
    "materials": [
        {{
            "id": 1,
            "title": "자료 제목",
            "type": "재무데이터/시장분석/고객데이터/조직현황/외부환경/내부보고서",
            "content": "자료 전체 내용 (구체적 수치, 표, 분석 포함. 최소 3~5문단)",
            "data_tables": "표 형태 데이터가 있으면 텍스트 표로 제공",
            "key_insights": ["이 자료에서 도출할 수 있는 인사이트1", "인사이트2"],
            "has_conflicting_info": false,
            "conflict_detail": "다른 자료와 상충되는 부분 설명 (있는 경우)",
            "analysis_angle": "이 자료가 제공하는 분석 관점 (재무/고객/경쟁/내부 등)"
        }}
    ],
    "cross_analysis_points": [
        "자료 1과 3을 종합하면 발견할 수 있는 인사이트",
        "자료 2와 5가 상충하는 부분과 그 의미"
    ],
    "qa_questions": {{
        "basic": [
            {{
                "question": "질문 (구체적으로)",
                "intent": "측정 역량/의도",
                "good_answer_guide": "좋은 답변 방향",
                "follow_up": "추가 질문 (답변에 따라)"
            }}
        ],
        "advanced": [
            {{
                "question": "압박/심화 질문",
                "intent": "측정 역량/의도",
                "good_answer_guide": "좋은 답변 방향",
                "follow_up": "추가 질문"
            }}
        ]
    }},
    "evaluation_criteria": [
        {{
            "competency": "역량명",
            "category": "내용구성/분석력/전달력/대응력",
            "behavioral_indicators": ["행동지표1", "행동지표2"],
            "bars": {{
                "5": "우수 기준",
                "3": "보통 기준",
                "1": "미흡 기준"
            }}
        }}
    ],
    "facilitator_guide": "진행자 가이드"
}}
```"""


GD_ASSIGNED_ROLE_PROMPT = """
{context}

## 과제: Group Discussion - 역할부여형 (Assigned Role) 시뮬레이션 설계

참가자 3명이 각자 다른 부서/입장을 대표하여 토론합니다.
토론 시간: {duration}분

### 핵심 설계 요구사항

**역할부여형 특징:**
- 참가자 3명에게 각각 다른 부서/입장을 부여
- 각 참가자에게 **자신의 입장을 뒷받침하는 풍부한 근거 자료**를 별도 제공
- 서로 다른 이해관계가 충돌하는 상황 설정
- 최종적으로 합의를 도출해야 하는 구조

**각 역할별 자료 구성:**
- 공통 자료: 모든 참가자가 공유하는 배경 정보
- 개별 자료: 각 역할만 받는 부서별 데이터, 현황, 근거 (2~3개씩)
- 개별 자료에는 구체적 수치, 사례, 논리적 근거 포함
- 각 입장이 모두 일리가 있어야 함 (특정 입장이 명백히 우세하지 않게)

JSON 형식으로 응답:
```json
{{
    "title": "토론 주제 제목",
    "discussion_type": "assigned_role",
    "topic": {{
        "statement": "토론 주제문 (결정해야 할 사안)",
        "background": "배경 설명 (왜 이 논의가 필요한지)",
        "decision_required": "내려야 할 결정 사항",
        "full_text": "참가자 공통 제공 전체 설명문 (5~7문단)"
    }},
    "common_materials": [
        {{
            "id": 1,
            "title": "공통 자료 제목",
            "content": "모든 참가자가 공유하는 자료 내용"
        }}
    ],
    "roles": [
        {{
            "role_number": 1,
            "department": "부서명",
            "position_title": "직책",
            "stance": "이 역할의 입장/주장 요약",
            "core_argument": "핵심 논거",
            "card_text": "역할 카드 전체 텍스트 (참가자에게 제공, 3~5문단)",
            "supporting_materials": [
                {{
                    "title": "이 역할만 받는 자료 제목",
                    "content": "부서별 데이터, 현황, 근거 (구체적 수치 포함, 2~3문단)"
                }}
            ],
            "negotiation_guide": {{
                "must_achieve": "반드시 관철해야 할 사항",
                "can_concede": "양보 가능한 사항",
                "ideal_outcome": "최선의 결과"
            }}
        }}
    ],
    "discussion_rules": {{
        "duration": {duration},
        "participant_count": 3,
        "format": "역할부여형 토론",
        "goal": "3개 부서의 이해관계를 조율하여 합의안 도출",
        "rules": ["규칙1", "규칙2"]
    }},
    "observer_sheet": {{
        "individual_items": [
            "자기 입장의 논리적 제시",
            "상대 입장에 대한 경청과 이해",
            "대안/절충안 제시",
            "합의 도출 기여",
            "감정 조절과 건설적 태도"
        ],
        "competency_mapping": [
            {{
                "competency": "역량명",
                "observable_behaviors": ["관찰 행동1", "관찰 행동2"],
                "bars": {{
                    "5": "우수 기준",
                    "3": "보통 기준",
                    "1": "미흡 기준"
                }}
            }}
        ]
    }},
    "evaluation_criteria": [
        {{
            "competency": "역량명",
            "behavioral_indicators": ["행동지표1", "행동지표2"],
            "bars": {{"5": "우수", "3": "보통", "1": "미흡"}}
        }}
    ],
    "facilitator_guide": "진행자 가이드"
}}
```"""


GD_FREE_DISCUSSION_PROMPT = """
{context}

## 과제: Group Discussion - 자유토론형 (Free Discussion) 시뮬레이션 설계

참가자 {participant_count}명이 동일한 자료를 기반으로 자유롭게 토론합니다.
토론 시간: {duration}분

### 핵심 설계 요구사항

**자유토론형 특징:**
- 모든 참가자가 **동일한 자료**를 받음
- 특정 역할이나 입장이 부여되지 않음
- 참가자들이 함께 **아이디어를 모으거나 문제를 해결**해 나가는 형태
- 자연스럽게 리더십, 협업, 창의성이 발현되는 구조

**토론 유형 (하나를 선택하여 설계):**
- 문제해결형: 주어진 문제에 대한 최적 해결방안 도출
- 의사결정형: 여러 선택지 중 최선의 대안 선택
- 아이디어형: 새로운 아이디어/전략을 함께 구상

**제공 자료:**
- 공통 자료 3~5개 (모든 참가자 동일)
- 다양한 관점에서 분석 가능한 풍부한 정보
- 자료만으로는 답이 명확하지 않아 토론이 필요한 구조

JSON 형식으로 응답:
```json
{{
    "title": "토론 주제 제목",
    "discussion_type": "free_discussion",
    "topic": {{
        "statement": "토론 주제문",
        "type": "문제해결형/의사결정형/아이디어형",
        "background": "배경 설명",
        "expected_outcome": "기대하는 토론 결과물 (해결방안/선택 결과/아이디어 목록 등)",
        "full_text": "참가자에게 제공할 전체 주제 설명문 (5~7문단)"
    }},
    "materials": [
        {{
            "id": 1,
            "title": "자료 제목",
            "content": "자료 내용 (구체적 수치, 사례, 데이터 포함. 3~5문단)",
            "analysis_points": ["이 자료에서 논의할 수 있는 포인트1", "포인트2"]
        }}
    ],
    "discussion_guide": {{
        "suggested_flow": ["1단계: 문제 정의 (10분)", "2단계: 원인 분석 (10분)", "3단계: 대안 도출 (15분)", "4단계: 합의 (5분)"],
        "key_discussion_points": ["반드시 논의되어야 할 포인트1", "포인트2", "포인트3"]
    }},
    "discussion_rules": {{
        "duration": {duration},
        "participant_count": {participant_count},
        "format": "자유토론",
        "goal": "토론 목표",
        "rules": ["규칙1", "규칙2"]
    }},
    "observer_sheet": {{
        "individual_items": [
            "발언의 빈도와 질",
            "경청 및 타인 의견 수용",
            "논리적 근거 제시",
            "새로운 관점/아이디어 제시",
            "토론 흐름 조절/기여",
            "합의 도출 노력"
        ],
        "competency_mapping": [
            {{
                "competency": "역량명",
                "observable_behaviors": ["관찰 행동1", "관찰 행동2"],
                "bars": {{
                    "5": "우수 기준",
                    "3": "보통 기준",
                    "1": "미흡 기준"
                }}
            }}
        ]
    }},
    "evaluation_criteria": [
        {{
            "competency": "역량명",
            "behavioral_indicators": ["행동지표1", "행동지표2"],
            "bars": {{"5": "우수", "3": "보통", "1": "미흡"}}
        }}
    ],
    "facilitator_guide": "진행자 가이드"
}}
```"""


CASE_STUDY_PROMPT = """
{context}

## 과제: Case Study (사례분석) 시뮬레이션 설계

위 조건에 맞는 사례분석 시뮬레이션을 설계해주세요.
분석 시간: {duration}분

### 작성 항목

**1. 사례 개요** - 가상 기업의 복잡한 경영 상황
**2. 제공 데이터 (5~7개)** - 재무, 시장, 고객, 조직 등 다각도 자료
**3. 분석 과제 (5~8개)** - 현상분석, 대안수립, 실행계획
**4. 모범 답안** - 각 질문별 우수 답변 방향
**5. 평가 기준**

JSON 형식으로 응답:
```json
{{
    "title": "사례 제목",
    "case_overview": {{
        "company": "기업 상세 정보",
        "industry": "업종",
        "situation": "현재 상황 요약",
        "full_text": "참가자에게 제공할 전체 사례 설명문 (5~8문단)",
        "stakeholders": ["이해관계자1", "이해관계자2"],
        "constraints": "제약 조건"
    }},
    "case_data": [
        {{
            "id": 1,
            "title": "자료 제목",
            "type": "재무/시장/고객/조직/외부환경",
            "content": "자료 전체 내용 (구체적 수치 포함)",
            "key_insights": ["인사이트1", "인사이트2"],
            "has_conflicting_info": false,
            "conflict_detail": ""
        }}
    ],
    "analysis_questions": [
        {{
            "id": 1,
            "category": "현상분석/대안수립/실행계획",
            "question": "분석 질문",
            "target_competency": "측정 역량",
            "good_answer_guide": "좋은 답변 방향",
            "common_mistakes": "흔한 실수"
        }}
    ],
    "model_solution": {{
        "situation_analysis": "모범 상황 분석",
        "root_cause": "핵심 원인",
        "alternatives": [
            {{"option": "대안1", "pros": "장점", "cons": "단점", "feasibility": "실현가능성"}}
        ],
        "recommended_action": "권장 대안과 근거",
        "implementation_plan": "실행 계획"
    }},
    "evaluation_criteria": [
        {{
            "competency": "역량명",
            "behavioral_indicators": ["행동지표1", "행동지표2"],
            "bars": {{"5": "우수", "3": "보통", "1": "미흡"}}
        }}
    ],
    "facilitator_guide": "진행자 가이드"
}}
```"""


def get_prompt(method: str, params: dict) -> str:
    """기법별 프롬프트를 생성합니다."""
    context = build_context(params)

    if method == "in_basket":
        doc_count = params.get("doc_count", 10)
        return IN_BASKET_PROMPT.format(context=context, doc_count=doc_count)

    elif method == "role_playing":
        rounds = params.get("rounds", 2)
        return ROLE_PLAYING_PROMPT.format(context=context, rounds=rounds)

    elif method == "presentation":
        total = params.get("duration", 30)
        prep_time = params.get("prep_time", int(total * 0.67))
        present_time = params.get("present_time", total - prep_time)
        return PRESENTATION_PROMPT.format(
            context=context, prep_time=prep_time, present_time=present_time
        )

    elif method == "gd_assigned_role":
        duration = params.get("duration", 40)
        return GD_ASSIGNED_ROLE_PROMPT.format(context=context, duration=duration)

    elif method == "gd_free_discussion":
        participant_count = params.get("participant_count", 5)
        duration = params.get("duration", 40)
        return GD_FREE_DISCUSSION_PROMPT.format(
            context=context, participant_count=participant_count, duration=duration
        )

    elif method == "group_discussion":
        # 하위 호환 - gd_type에 따라 분기
        gd_type = params.get("gd_type", "free")
        if gd_type == "assigned":
            duration = params.get("duration", 40)
            return GD_ASSIGNED_ROLE_PROMPT.format(context=context, duration=duration)
        else:
            participant_count = params.get("participant_count", 5)
            duration = params.get("duration", 40)
            return GD_FREE_DISCUSSION_PROMPT.format(
                context=context, participant_count=participant_count, duration=duration
            )

    elif method == "case_study":
        duration = params.get("duration", 45)
        return CASE_STUDY_PROMPT.format(context=context, duration=duration)

    else:
        raise ValueError(f"알 수 없는 평가 기법: {method}")
