"""
DC 시뮬레이션 빌더 - 간편 실행 서버
브라우저에서 바로 시뮬레이션을 설계하고 생성할 수 있습니다.

사용법:
    python run.py
    → 브라우저에서 http://localhost:5000 접속
"""

import json
import os
import sys
import time
import re
import uuid
from io import BytesIO

from flask import Flask, jsonify, request, send_file, render_template_string, render_template
from flask_cors import CORS

# 프롬프트 import - app 패키지를 거치지 않고 직접 import
services_path = os.path.join(os.path.dirname(__file__), 'backend', 'app', 'services')
sys.path.insert(0, services_path)
from prompts import SYSTEM_PROMPT, get_prompt
from export_service import export_to_markdown, export_package

import anthropic
import threading

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
CORS(app)

# ─────────────────────────────────────────────
# 시나리오 생성 엔진
# ─────────────────────────────────────────────

client = None
generated_scenarios = {}  # 세션별 시나리오 저장


def _cleanup_stale_data():
    """1시간 이상 된 세션 삭제, generated_scenarios 최대 50개 유지"""
    now = time.time()

    # discussion_sessions: 1시간(3600초) 이상 된 세션 삭제
    expired_sessions = [
        sid for sid, sess in discussion_sessions.items()
        if now - sess.get("created_at", now) > 3600
    ]
    for sid in expired_sessions:
        del discussion_sessions[sid]

    # generated_scenarios: 최대 50개 유지 (오래된 것부터 삭제)
    if len(generated_scenarios) > 50:
        keys_to_remove = list(generated_scenarios.keys())[: len(generated_scenarios) - 50]
        for key in keys_to_remove:
            del generated_scenarios[key]

    # 5분(300초) 후 다시 실행
    timer = threading.Timer(300, _cleanup_stale_data)
    timer.daemon = True
    timer.start()


def get_client():
    global client
    if client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY 환경변수를 설정해주세요.")
        client = anthropic.Anthropic(api_key=api_key, timeout=300.0)
    return client


def parse_json_response(text):
    """AI 응답에서 JSON 추출"""
    # 1. ```json ... ``` 코드블록
    json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # 2. ``` ... ``` 코드블록 (json 태그 없는 경우)
    json_match = re.search(r"```\s*([\[{].*?)\s*```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # 3. 텍스트에서 { ... } 오브젝트 추출
    json_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # 4. 텍스트에서 [ ... ] 배열 추출 → 첫 번째 오브젝트 반환
    json_match = re.search(r"(\[.*\])", text, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group(1))
            if isinstance(result, list) and result:
                return result[0]
            return result
        except json.JSONDecodeError:
            pass

    return {"raw_text": text, "parse_error": True}


# ─────────────────────────────────────────────
# API 엔드포인트
# ─────────────────────────────────────────────

@app.route("/api/generate", methods=["POST"])
def api_generate():
    """시나리오 생성"""
    data = request.get_json() or {}
    method = data.get("method")
    params = data.get("params", {})
    model = DEFAULT_MODEL

    if not method:
        return jsonify({"success": False, "error": "method는 필수 파라미터입니다."}), 400

    difficulty = params.get("difficulty")
    if difficulty is not None:
        try:
            difficulty = int(difficulty)
            if not (1 <= difficulty <= 5):
                return jsonify({"success": False, "error": "difficulty는 1~5 사이 값이어야 합니다."}), 400
            params["difficulty"] = difficulty
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "difficulty는 숫자여야 합니다."}), 400

    try:
        c = get_client()
        prompt = get_prompt(method, params)

        start = time.time()
        response = c.messages.create(
            model=model,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        elapsed = time.time() - start

        if not response.content:
            raise ValueError("API 응답이 비어있습니다.")
        scenario = parse_json_response(response.content[0].text)
        scenario["_meta"] = {
            "method": method,
            "generation_time": round(elapsed, 1),
            "tokens": response.usage.input_tokens + response.usage.output_tokens,
        }

        # 메모리에 저장
        generated_scenarios[method] = scenario

        return jsonify({"success": True, "scenario": scenario})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/refine", methods=["POST"])
def api_refine():
    """AI 시나리오 수정"""
    data = request.get_json()
    method = data.get("method")
    scenario = data.get("scenario")
    instruction = data.get("instruction")
    model = DEFAULT_MODEL

    try:
        c = get_client()
        prompt = f"""다음은 DC(Development Center) 시뮬레이션의 '{method}' 기법으로 생성된 시나리오 JSON입니다.

현재 시나리오:
```json
{json.dumps(scenario, ensure_ascii=False, indent=2)}
```

수정 요청사항:
{instruction}

위 수정 요청사항을 반영하여 시나리오를 수정해주세요.
수정되지 않은 부분은 그대로 유지하고, 요청한 부분만 변경하세요.
반드시 원본과 동일한 JSON 구조로 반환해주세요. JSON 코드블록(```json ... ```) 형식으로만 응답하세요."""

        response = c.messages.create(
            model=model,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        if not response.content:
            raise ValueError("API 응답이 비어있습니다.")
        updated = parse_json_response(response.content[0].text)
        if "_meta" not in updated:
            updated["_meta"] = scenario.get("_meta", {})
        updated["_meta"]["last_refined"] = instruction[:60]
        generated_scenarios[method] = updated

        return jsonify({"success": True, "scenario": updated})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/export/markdown", methods=["POST"])
def api_export_md():
    """마크다운 내보내기"""
    data = request.get_json()
    method = data.get("method")
    scenario = data.get("scenario") if data.get("scenario") else generated_scenarios.get(method, {})
    md = export_to_markdown(scenario, method)
    return jsonify({"success": True, "markdown": md})


@app.route("/api/export/zip", methods=["POST"])
def api_export_zip():
    """ZIP 패키지 내보내기"""
    data = request.get_json()
    project_name = data.get("project_name", "DC_시뮬레이션")
    scenarios = data.get("scenarios") if data.get("scenarios") else generated_scenarios

    if not scenarios:
        return jsonify({"success": False, "error": "생성된 시나리오가 없습니다."}), 400

    zip_buffer = export_package(project_name, scenarios)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"{project_name}.zip",
    )


# ─────────────────────────────────────────────
# 웹 UI
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template('index.html')


@app.route("/discussion")
def discussion_page():
    return render_template('discussion.html')


# ─────────────────────────────────────────────
# GD 인터랙티브 토론 기능
# ─────────────────────────────────────────────

discussion_sessions = {}  # session_id -> session 데이터


DISCUSSION_SCENARIO_PROMPT = """당신은 Development Center(DC) 평가용 집단토론 시나리오 설계 전문가입니다.

다음 조건에 맞는 3인 토론 시나리오를 설계해주세요:
- 산업: {industry}
- 대상 직급: {target_level}
- 토론 유형: {topic_type}
- 난이도: {difficulty}/5

## 설계 원칙
1. **삼각 갈등 모델**: 3명의 참가자가 각각 다른 이해관계를 가지되, 어떤 두 명도 완전히 같거나 완전히 반대가 아닌 구조
2. 각 역할에 고유한 부서/직책/이해관계 부여
3. 공통 자료(전체 공유)와 역할별 비밀 자료(해당 역할만 알고 있는 정보) 제공
4. 현실적이고 구체적인 수치/데이터 포함

## 역할 구성
- participant (참가자/사용자): 특정 부서 역할
- ai_1 (AI-1, 분석적-주장형): 데이터 중시, 논리적, 반론이 강함
- ai_2 (AI-2, 협력적-조정형): 공통점 탐색, 절충안 제시, 관계 중시

## 출력 형식 (반드시 JSON)
```json
{{
  "topic": "토론 주제 (한 문장)",
  "background": "배경 상황 설명 (3-5문장)",
  "common_materials": [
    {{"title": "자료명", "content": "자료 내용 (구체적 수치 포함)"}}
  ],
  "roles": {{
    "participant": {{
      "name": "한국식 이름",
      "department": "부서명",
      "position": "직책",
      "interest": "이 역할의 핵심 이해관계 (2-3문장)",
      "private_materials": [
        {{"title": "비밀자료명", "content": "이 역할만 아는 정보"}}
      ]
    }},
    "ai_1": {{
      "name": "한국식 이름",
      "department": "부서명",
      "position": "직책",
      "interest": "이 역할의 핵심 이해관계 (2-3문장)",
      "private_materials": [
        {{"title": "비밀자료명", "content": "이 역할만 아는 정보"}}
      ],
      "personality": "분석적-주장형: 데이터를 근거로 논리적으로 주장하며, 감정보다 사실에 기반한 반론을 펼침"
    }},
    "ai_2": {{
      "name": "한국식 이름",
      "department": "부서명",
      "position": "직책",
      "interest": "이 역할의 핵심 이해관계 (2-3문장)",
      "private_materials": [
        {{"title": "비밀자료명", "content": "이 역할만 아는 정보"}}
      ],
      "personality": "협력적-조정형: 각자의 입장에서 공통점을 찾고 절충안을 제시하며, 대화를 건설적 방향으로 이끔"
    }}
  }},
  "discussion_guide": {{
    "opening_question": "토론을 시작하는 핵심 질문",
    "key_tensions": ["갈등 포인트 1", "갈등 포인트 2", "갈등 포인트 3"],
    "possible_consensus_areas": ["합의 가능 영역 1", "합의 가능 영역 2"]
  }}
}}
```

JSON 코드블록으로만 응답하세요."""


@app.route("/api/discussion/create-session", methods=["POST"])
def discussion_create_session():
    """토론 세션 생성"""
    data = request.get_json()
    industry = data.get("industry", "IT/소프트웨어")
    target_level = data.get("target_level", "과장")
    topic_type = data.get("topic_type", "자원배분형")
    difficulty = data.get("difficulty", 3)

    if not all([industry, target_level, topic_type]):
        return jsonify({"success": False, "error": "필수 파라미터가 누락되었습니다."}), 400

    model = DEFAULT_MODEL

    try:
        c = get_client()
        prompt = DISCUSSION_SCENARIO_PROMPT.format(
            industry=industry,
            target_level=target_level,
            topic_type=topic_type,
            difficulty=difficulty,
        )

        start = time.time()
        response = c.messages.create(
            model=model,
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
        )
        elapsed = time.time() - start

        scenario = parse_json_response(response.content[0].text)
        if scenario.get("parse_error"):
            return jsonify({"success": False, "error": "시나리오 생성 결과를 파싱할 수 없습니다."}), 500

        session_id = str(uuid.uuid4())
        session = {
            "session_id": session_id,
            "industry": industry,
            "target_level": target_level,
            "topic_type": topic_type,
            "difficulty": difficulty,
            "scenario": scenario,
            "phase": "briefing",
            "messages": [],
            "created_at": time.time(),
            "generation_time": round(elapsed, 1),
            "ai_turn_counter": 0,
        }

        discussion_sessions[session_id] = session
        return jsonify({"success": True, "session": session})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def _build_ai_character_prompt(session, ai_role):
    """AI 캐릭터 시스템 프롬프트 구성"""
    scenario = session["scenario"]
    role_info = scenario["roles"][ai_role]
    other_ai = "ai_2" if ai_role == "ai_1" else "ai_1"
    participant_info = scenario["roles"]["participant"]
    other_info = scenario["roles"][other_ai]

    style = (
        "당신은 분석적-주장형 토론자입니다. 데이터와 논리를 중시하며, 상대 주장의 허점을 정확히 짚습니다. "
        "감정보다 사실에 기반하여 반론합니다. 자신의 입장을 명확히 주장하되 근거를 항상 제시합니다."
        if ai_role == "ai_1"
        else "당신은 협력적-조정형 토론자입니다. 각 참가자의 입장에서 공통점을 찾고 절충안을 제시합니다. "
        "대화를 건설적 방향으로 이끌며, 갈등을 완화하면서도 핵심 쟁점은 놓치지 않습니다."
    )

    return f"""당신은 DC(Development Center) 집단토론 시뮬레이션의 참가자입니다.

## 당신의 역할
- 이름: {role_info['name']}
- 부서: {role_info['department']}
- 직책: {role_info['position']}
- 이해관계: {role_info['interest']}

## 토론 주제
{scenario['topic']}

## 배경
{scenario['background']}

## 당신의 성격/스타일
{style}

## 당신만 아는 비밀 자료
{json.dumps(role_info.get('private_materials', []), ensure_ascii=False)}

## 다른 참가자 정보
- {participant_info['name']} ({participant_info['department']}, {participant_info['position']})
- {other_info['name']} ({other_info['department']}, {other_info['position']})

## 발언 규칙
1. 반드시 한국어로 발언하세요
2. 2-4문장으로 간결하게 발언하세요
3. 비즈니스 회의 톤을 유지하세요 (존댓말 사용)
4. 자신의 이해관계와 비밀 자료를 자연스럽게 반영하세요
5. 적응적 난이도: 상대 발언이 짧고 단순하면 질문으로 유도하고, 길고 논리적이면 더 강한 반론을 제시하세요
6. 이름을 직접 부르지 말고, "~님" 혹은 직책으로 호칭하세요
7. 현재 토론 단계에 맞게 발언하세요"""


def _get_ai_response(session, ai_role, extra_instruction=""):
    """AI 캐릭터 응답 생성"""
    model = DEFAULT_MODEL
    c = get_client()
    system_prompt = _build_ai_character_prompt(session, ai_role)

    # 메시지 히스토리를 대화 형태로 구성
    history_text = ""
    for msg in session["messages"]:
        sender_label = msg.get("sender_name", msg["sender"])
        history_text += f"[{sender_label}]: {msg['content']}\n"

    user_prompt = f"""지금까지의 토론 내용:
{history_text if history_text else "(아직 발언이 없습니다)"}

{extra_instruction}

위 맥락을 고려하여 당신의 차례에 맞는 발언을 해주세요. 발언 내용만 출력하세요 (이름이나 레이블 없이)."""

    response = c.messages.create(
        model=model,
        max_tokens=500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return response.content[0].text.strip()


@app.route("/api/discussion/message", methods=["POST"])
def discussion_message():
    """사용자 발언 처리 및 AI 응답 생성"""
    data = request.get_json()
    session_id = data.get("session_id")
    content = data.get("content", "").strip()

    if not session_id or session_id not in discussion_sessions:
        return jsonify({"success": False, "error": "유효하지 않은 세션입니다."}), 404

    if not content:
        return jsonify({"success": False, "error": "발언 내용을 입력해주세요."}), 400

    session = discussion_sessions[session_id]
    participant_name = session["scenario"]["roles"]["participant"]["name"]

    # 사용자 메시지 추가
    user_msg = {
        "sender": "participant",
        "sender_name": participant_name,
        "content": content,
        "timestamp": time.time(),
    }
    session["messages"].append(user_msg)

    # AI 응답 결정: 번갈아가며, 때때로 2명 연속
    session["ai_turn_counter"] += 1
    counter = session["ai_turn_counter"]

    ai_responses = []
    try:
        # 기본: 번갈아가며 응답
        if counter % 2 == 1:
            first_ai = "ai_1"
            second_ai = "ai_2"
        else:
            first_ai = "ai_2"
            second_ai = "ai_1"

        # 첫 번째 AI 응답
        first_role = session["scenario"]["roles"][first_ai]
        first_content = _get_ai_response(session, first_ai)
        first_msg = {
            "sender": first_ai,
            "sender_name": first_role["name"],
            "content": first_content,
            "timestamp": time.time(),
        }
        session["messages"].append(first_msg)
        ai_responses.append(first_msg)

        # 때때로 (3턴마다) 두 번째 AI도 반응
        if counter % 3 == 0:
            second_role = session["scenario"]["roles"][second_ai]
            second_content = _get_ai_response(
                session, second_ai,
                extra_instruction="방금 다른 참가자의 발언에 대해 즉각 반응하세요."
            )
            second_msg = {
                "sender": second_ai,
                "sender_name": second_role["name"],
                "content": second_content,
                "timestamp": time.time(),
            }
            session["messages"].append(second_msg)
            ai_responses.append(second_msg)

        return jsonify({
            "success": True,
            "user_message": user_msg,
            "ai_responses": ai_responses,
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/discussion/phase", methods=["POST"])
def discussion_phase():
    """토론 단계 변경"""
    data = request.get_json()
    session_id = data.get("session_id")
    phase = data.get("phase")

    if not session_id or session_id not in discussion_sessions:
        return jsonify({"success": False, "error": "유효하지 않은 세션입니다."}), 404

    valid_phases = ["briefing", "intro", "discussion", "consensus"]
    if phase not in valid_phases:
        return jsonify({"success": False, "error": f"유효하지 않은 단계입니다. ({', '.join(valid_phases)})"}), 400

    session = discussion_sessions[session_id]
    session["phase"] = phase
    new_messages = []

    try:
        if phase == "intro":
            # AI 2명의 초기 입장 발언 자동 생성
            for ai_role in ["ai_1", "ai_2"]:
                role_info = session["scenario"]["roles"][ai_role]
                content = _get_ai_response(
                    session, ai_role,
                    extra_instruction="토론이 시작됩니다. 자신의 입장을 간략하게 밝혀주세요. 2-3문장으로 자신의 핵심 주장과 근거를 제시하세요."
                )
                msg = {
                    "sender": ai_role,
                    "sender_name": role_info["name"],
                    "content": content,
                    "timestamp": time.time(),
                }
                session["messages"].append(msg)
                new_messages.append(msg)

        elif phase == "consensus":
            sys_msg = {
                "sender": "system",
                "sender_name": "시스템",
                "content": "합의 도출 단계입니다. 지금까지 논의된 내용을 바탕으로 모든 참가자가 수용할 수 있는 합의안을 도출해주세요. 각자의 핵심 이해관계를 반영한 절충안을 제시하는 것이 중요합니다.",
                "timestamp": time.time(),
            }
            session["messages"].append(sys_msg)
            new_messages.append(sys_msg)

        elif phase == "discussion":
            sys_msg = {
                "sender": "system",
                "sender_name": "시스템",
                "content": "자유 토론 단계입니다. 각자의 입장을 바탕으로 자유롭게 의견을 교환해주세요.",
                "timestamp": time.time(),
            }
            session["messages"].append(sys_msg)
            new_messages.append(sys_msg)

        return jsonify({
            "success": True,
            "phase": phase,
            "messages": new_messages,
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


EVALUATION_PROMPT = """당신은 Development Center(DC) 집단토론 평가 전문가입니다.

다음은 3인 집단토론의 전체 기록입니다. 'participant'가 평가 대상자이고, 나머지는 AI 참가자입니다.

## 토론 주제
{topic}

## 토론 배경
{background}

## 참가자 역할
- participant ({participant_name}): {participant_role}
- ai_1 ({ai1_name}): {ai1_role}
- ai_2 ({ai2_name}): {ai2_role}

## 전체 토론 기록
{transcript}

## 평가 기준
5가지 역량을 각각 5점 만점으로 평가하세요:
1. **리더십**: 토론 방향 제시, 주도적 의견 개진, 논의 구조화
2. **커뮤니케이션**: 명확한 의사표현, 경청, 적절한 질문
3. **설득/조정/통합**: 논리적 설득, 이견 조정, 다양한 의견 통합
4. **분석적 사고**: 문제 분석, 데이터 활용, 대안 제시
5. **팀워크**: 협력적 태도, 타인 의견 존중, 건설적 피드백

## 출력 형식 (반드시 JSON)
```json
{{
  "overall_score": 3.5,
  "competency_scores": {{
    "리더십": {{"score": 3.5, "max_score": 5, "description": "평가 근거 설명"}},
    "커뮤니케이션": {{"score": 4.0, "max_score": 5, "description": "평가 근거 설명"}},
    "설득/조정/통합": {{"score": 3.0, "max_score": 5, "description": "평가 근거 설명"}},
    "분석적 사고": {{"score": 3.5, "max_score": 5, "description": "평가 근거 설명"}},
    "팀워크": {{"score": 4.0, "max_score": 5, "description": "평가 근거 설명"}}
  }},
  "strengths": [
    {{"title": "강점 제목", "description": "구체적 설명", "evidence": "실제 발언 인용"}}
  ],
  "development_areas": [
    {{"title": "개발 영역 제목", "description": "구체적 설명", "evidence": "관련 발언 인용 또는 부재한 행동", "suggestion": "개선 제안"}}
  ]
}}
```

JSON 코드블록으로만 응답하세요."""


@app.route("/api/discussion/evaluate", methods=["POST"])
def discussion_evaluate():
    """토론 평가"""
    data = request.get_json()
    session_id = data.get("session_id")

    if not session_id or session_id not in discussion_sessions:
        return jsonify({"success": False, "error": "유효하지 않은 세션입니다."}), 404

    session = discussion_sessions[session_id]
    scenario = session["scenario"]
    messages = session["messages"]

    # 참여 통계 계산
    user_messages = [m for m in messages if m["sender"] == "participant"]
    ai_messages = [m for m in messages if m["sender"] in ("ai_1", "ai_2")]
    total_messages = len([m for m in messages if m["sender"] != "system"])
    avg_length = (
        round(sum(len(m["content"]) for m in user_messages) / len(user_messages))
        if user_messages else 0
    )

    # 토론 기록 텍스트화
    transcript = ""
    for msg in messages:
        if msg["sender"] == "system":
            transcript += f"\n--- [{msg['content']}] ---\n"
        else:
            transcript += f"[{msg['sender_name']}] ({msg['sender']}): {msg['content']}\n"

    roles = scenario["roles"]
    model = DEFAULT_MODEL

    try:
        c = get_client()
        prompt = EVALUATION_PROMPT.format(
            topic=scenario.get("topic", ""),
            background=scenario.get("background", ""),
            participant_name=roles["participant"]["name"],
            participant_role=roles["participant"]["interest"],
            ai1_name=roles["ai_1"]["name"],
            ai1_role=roles["ai_1"]["interest"],
            ai2_name=roles["ai_2"]["name"],
            ai2_role=roles["ai_2"]["interest"],
            transcript=transcript,
        )

        response = c.messages.create(
            model=model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )

        evaluation = parse_json_response(response.content[0].text)
        if evaluation.get("parse_error"):
            return jsonify({"success": False, "error": "평가 결과를 파싱할 수 없습니다."}), 500

        evaluation["participation_stats"] = {
            "total_messages": total_messages,
            "user_messages": len(user_messages),
            "ai_messages": len(ai_messages),
            "avg_length": avg_length,
        }

        return jsonify({"success": True, "evaluation": evaluation})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/discussion/session/<session_id>", methods=["GET"])
def discussion_get_session(session_id):
    """세션 정보 조회"""
    if session_id not in discussion_sessions:
        return jsonify({"success": False, "error": "세션을 찾을 수 없습니다."}), 404

    session = discussion_sessions[session_id]
    return jsonify({"success": True, "session": session})


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  DC Simulation Builder")
    print("  http://localhost:5000 에서 접속하세요")
    print("=" * 50 + "\n")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("  ⚠️  ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        print("  시나리오 생성을 사용하려면 API 키를 설정하세요:")
        print("  export ANTHROPIC_API_KEY=sk-ant-...\n")
    # 메모리 정리 스레드 시작
    _cleanup_stale_data()

    debug_mode = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
