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
from io import BytesIO

from flask import Flask, jsonify, request, send_file, render_template_string
from flask_cors import CORS

# 프롬프트 import - app 패키지를 거치지 않고 직접 import
services_path = os.path.join(os.path.dirname(__file__), 'backend', 'app', 'services')
sys.path.insert(0, services_path)
from prompts import SYSTEM_PROMPT, get_prompt
from export_service import export_to_markdown, export_package

import anthropic

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
CORS(app)

# ─────────────────────────────────────────────
# 시나리오 생성 엔진
# ─────────────────────────────────────────────

client = None
generated_scenarios = {}  # 세션별 시나리오 저장


def get_client():
    global client
    if client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY 환경변수를 설정해주세요.")
        client = anthropic.Anthropic(api_key=api_key)
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
    data = request.get_json()
    method = data.get("method")
    params = data.get("params", {})
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

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
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

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
    scenario = data.get("scenario") or generated_scenarios.get(method, {})
    md = export_to_markdown(scenario, method)
    return jsonify({"success": True, "markdown": md})


@app.route("/api/export/zip", methods=["POST"])
def api_export_zip():
    """ZIP 패키지 내보내기"""
    data = request.get_json()
    project_name = data.get("project_name", "DC_시뮬레이션")
    scenarios = data.get("scenarios") or generated_scenarios

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
    from flask import render_template
    return render_template('index.html')


_UNUSED_OLD_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DC Simulation Builder</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', -apple-system, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            min-height: 100vh;
        }

        /* 헤더 */
        .header {
            background: linear-gradient(135deg, #1e293b, #334155);
            padding: 20px 40px;
            border-bottom: 1px solid #475569;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .header h1 { font-size: 24px; color: #38bdf8; }
        .header .subtitle { color: #94a3b8; font-size: 14px; }

        /* 진행 바 */
        .progress-bar {
            background: #1e293b;
            padding: 15px 40px;
            border-bottom: 1px solid #334155;
        }
        .steps {
            display: flex;
            gap: 0;
            justify-content: center;
        }
        .step {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            cursor: pointer;
            border-radius: 6px;
            font-size: 13px;
            transition: all 0.2s;
        }
        .step:hover { background: #334155; }
        .step.active { background: #1d4ed8; color: white; }
        .step.done { color: #4ade80; }
        .step .num {
            width: 24px; height: 24px;
            border-radius: 50%;
            background: #475569;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
        }
        .step.active .num { background: #60a5fa; }
        .step.done .num { background: #22c55e; }
        .step-arrow { color: #475569; margin: 0 4px; }

        /* 메인 컨텐츠 */
        .main {
            max-width: 900px;
            margin: 30px auto;
            padding: 0 20px;
        }

        .section-title {
            font-size: 20px;
            margin-bottom: 8px;
            color: #f1f5f9;
        }
        .section-desc {
            color: #94a3b8;
            margin-bottom: 20px;
            font-size: 14px;
        }

        /* 선택 카드 그리드 */
        .option-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
            gap: 10px;
            margin-bottom: 30px;
        }
        .option-card {
            background: #1e293b;
            border: 2px solid #334155;
            border-radius: 10px;
            padding: 14px;
            cursor: pointer;
            transition: all 0.2s;
            text-align: center;
            font-size: 14px;
        }
        .option-card:hover {
            border-color: #60a5fa;
            background: #1e3a5f;
        }
        .option-card.selected {
            border-color: #3b82f6;
            background: #1e3a8a;
            box-shadow: 0 0 12px rgba(59, 130, 246, 0.3);
        }
        .option-card .icon { font-size: 24px; margin-bottom: 6px; }

        /* 카테고리 그룹 */
        .category-group {
            margin-bottom: 20px;
        }
        .category-label {
            font-size: 13px;
            color: #60a5fa;
            margin-bottom: 8px;
            font-weight: 600;
            padding-left: 4px;
        }

        /* 역량 다중선택 */
        .competency-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 8px;
        }
        .comp-chip {
            background: #1e293b;
            border: 1px solid #475569;
            border-radius: 20px;
            padding: 8px 14px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
            text-align: center;
        }
        .comp-chip:hover { border-color: #60a5fa; }
        .comp-chip.selected {
            background: #1e3a8a;
            border-color: #3b82f6;
            color: #93c5fd;
        }
        .comp-count {
            text-align: right;
            font-size: 13px;
            color: #94a3b8;
            margin-top: 8px;
        }

        /* 기법 설정 */
        .method-card {
            background: #1e293b;
            border: 2px solid #334155;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 12px;
            transition: all 0.2s;
        }
        .method-card.selected { border-color: #3b82f6; }
        .method-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }
        .method-header input[type="checkbox"] {
            width: 20px; height: 20px;
            accent-color: #3b82f6;
        }
        .method-header .name { font-size: 16px; font-weight: 600; }
        .method-settings {
            display: flex;
            gap: 20px;
            padding-left: 32px;
            flex-wrap: wrap;
        }
        .method-settings label {
            font-size: 13px;
            color: #94a3b8;
        }
        .method-settings input, .method-settings select {
            background: #0f172a;
            border: 1px solid #475569;
            color: #e2e8f0;
            padding: 6px 10px;
            border-radius: 6px;
            width: 80px;
            margin-left: 6px;
        }

        /* 버튼 */
        .btn-group {
            display: flex;
            justify-content: space-between;
            margin-top: 30px;
        }
        .btn {
            padding: 12px 28px;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }
        .btn-prev { background: #334155; color: #e2e8f0; }
        .btn-prev:hover { background: #475569; }
        .btn-next { background: #2563eb; color: white; }
        .btn-next:hover { background: #1d4ed8; }
        .btn-generate {
            background: linear-gradient(135deg, #059669, #10b981);
            color: white;
            padding: 16px 40px;
            font-size: 17px;
        }
        .btn-generate:hover { background: linear-gradient(135deg, #047857, #059669); }
        .btn-generate:disabled {
            background: #475569;
            cursor: not-allowed;
        }

        /* 결과 화면 */
        .result-container {
            background: #1e293b;
            border-radius: 12px;
            padding: 24px;
            margin-top: 20px;
        }
        .result-tabs {
            display: flex;
            gap: 4px;
            margin-bottom: 16px;
            border-bottom: 1px solid #334155;
            padding-bottom: 8px;
        }
        .result-tab {
            padding: 8px 16px;
            border-radius: 6px 6px 0 0;
            cursor: pointer;
            font-size: 14px;
            color: #94a3b8;
            transition: all 0.2s;
        }
        .result-tab:hover { color: #e2e8f0; }
        .result-tab.active {
            background: #334155;
            color: #60a5fa;
        }
        .result-content {
            background: #0f172a;
            border-radius: 8px;
            padding: 20px;
            max-height: 600px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-size: 14px;
            line-height: 1.7;
        }
        .result-content h1 { color: #60a5fa; font-size: 20px; margin: 16px 0 8px; }
        .result-content h2 { color: #38bdf8; font-size: 17px; margin: 14px 0 6px; }
        .result-content h3 { color: #7dd3fc; font-size: 15px; margin: 10px 0 4px; }

        /* 로딩 */
        .loading {
            text-align: center;
            padding: 60px;
        }
        .spinner {
            width: 50px; height: 50px;
            border: 4px solid #334155;
            border-top: 4px solid #3b82f6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .loading-text { color: #94a3b8; font-size: 15px; }
        .loading-agent { color: #60a5fa; font-size: 14px; margin-top: 8px; }

        /* 요약 사이드바 */
        .summary-bar {
            position: fixed;
            right: 20px;
            top: 140px;
            width: 220px;
            background: #1e293b;
            border-radius: 12px;
            padding: 16px;
            border: 1px solid #334155;
            font-size: 13px;
        }
        .summary-bar h3 {
            color: #60a5fa;
            margin-bottom: 12px;
            font-size: 14px;
        }
        .summary-item {
            margin-bottom: 8px;
            color: #94a3b8;
        }
        .summary-item .val {
            color: #e2e8f0;
            font-weight: 500;
        }

        /* 내보내기 버튼 */
        .export-group {
            display: flex;
            gap: 10px;
            margin-top: 16px;
        }
        .btn-export {
            padding: 10px 20px;
            border: 1px solid #475569;
            background: #1e293b;
            color: #e2e8f0;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }
        .btn-export:hover { border-color: #60a5fa; background: #1e3a5f; }

        @media (max-width: 1200px) {
            .summary-bar { display: none; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>DC Simulation Builder</h1>
            <div class="subtitle">AI 기반 Development Center 시뮬레이션 설계 도구</div>
        </div>
    </div>

    <div class="progress-bar">
        <div class="steps" id="stepBar"></div>
    </div>

    <div class="main" id="mainContent"></div>

    <div class="summary-bar" id="summaryBar" style="display:none;">
        <h3>현재 설정</h3>
        <div id="summaryContent"></div>
    </div>

    <script>
    // ─────────────────────────────────────────
    // 데이터 정의
    // ─────────────────────────────────────────

    const DATA = {
        purposes: [
            {id: 'promotion', label: '승진 심사', icon: '📈'},
            {id: 'hiring', label: '채용 선발', icon: '👥'},
            {id: 'leadership', label: '리더십 개발', icon: '🎯'},
            {id: 'diagnosis', label: '역량 진단', icon: '🔍'},
            {id: 'training', label: '교육/훈련', icon: '📚'},
            {id: 'transfer', label: '직무 전환', icon: '🔄'},
            {id: 'highperf', label: '고성과자 선발', icon: '⭐'},
            {id: 'talentpool', label: '핵심인재 풀', icon: '💎'},
        ],
        levels: [
            {id: 'c-level', label: 'C-Level', group: '임원급'},
            {id: 'executive', label: '임원/본부장', group: '임원급'},
            {id: 'director', label: '부장/실장', group: '관리자급'},
            {id: 'deputy', label: '차장', group: '관리자급'},
            {id: 'manager', label: '과장/팀장', group: '관리자급'},
            {id: 'senior', label: '대리/선임', group: '실무급'},
            {id: 'staff', label: '사원/주임', group: '실무급'},
            {id: 'newbie', label: '신입사원', group: '기타'},
            {id: 'intern', label: '인턴', group: '기타'},
        ],
        industries: {
            '제조': ['자동차','반도체/전자','화학/소재','기계/장비','식품/음료','의류/섬유','철강/금속','조선/해양','바이오/제약'],
            '서비스': ['금융/보험','유통/리테일','호텔/외식','물류/운송','의료/헬스케어','교육','미디어/엔터','컨설팅','광고/마케팅'],
            'IT/테크': ['소프트웨어','플랫폼/SaaS','게임','AI/데이터','보안','통신','핀테크','이커머스','클라우드'],
            '공공/기타': ['공공기관','공기업','비영리/NGO','에너지','건설/부동산','농업/수산'],
        },
        jobs: {
            '경영/관리': ['경영기획','전략기획','사업개발','프로젝트관리','총무/행정'],
            '영업/마케팅': ['B2B 영업','B2C 영업','해외영업','마케팅','브랜드관리','CRM'],
            '개발/기술': ['소프트웨어개발','데이터분석','인프라/DevOps','제품개발','연구/R&D','품질관리(QA)'],
            '지원': ['인사/HR','재무/회계','법무','고객서비스','구매/조달','홍보/IR'],
            '생산/현장': ['생산관리','공정관리','안전관리','물류관리','시설관리'],
        },
        competencies: {
            '리더십 역량': {color:'#3b82f6', items:['비전 제시','동기부여','코칭/육성','변화관리','임파워먼트','솔선수범','팀빌딩','갈등관리','영향력']},
            '사고 역량': {color:'#8b5cf6', items:['전략적 사고','분석적 사고','창의적 사고','문제해결','의사결정','기획력','정보수집/활용','논리적 사고','혁신지향']},
            '대인관계 역량': {color:'#06b6d4', items:['커뮤니케이션','협상력','설득력','고객지향','팀워크/협업','네트워킹','경청','갈등해결','이해관계자관리']},
            '실행 역량': {color:'#f59e0b', items:['목표지향','추진력/실행력','책임감','시간관리','위기관리','프로세스관리','품질지향','자원관리','성과관리']},
            '자기관리 역량': {color:'#10b981', items:['스트레스관리','자기개발','윤리의식','적응력/유연성','긍정적 태도','자기인식','감정조절','회복탄력성','프로페셔널리즘']},
            '글로벌/디지털': {color:'#ec4899', items:['글로벌 마인드','다문화 이해','디지털 리터러시','데이터 활용','외국어 소통','디지털 혁신']},
        },
    };

    const STEPS = [
        {num: 1, label: '평가 목적'},
        {num: 2, label: '대상 직급'},
        {num: 3, label: '산업/업종'},
        {num: 4, label: '직무'},
        {num: 5, label: '평가 역량'},
        {num: 6, label: '기법 설정'},
        {num: 7, label: '생성'},
    ];

    // ─────────────────────────────────────────
    // 상태 관리
    // ─────────────────────────────────────────

    let state = {
        step: 1,
        purpose: '',
        level: '',
        industry: '',
        job: '',
        competencies: [],
        methods: {
            in_basket: {enabled: true, duration: 30, difficulty: 3, doc_count: 10},
            role_playing: {enabled: true, duration: 20, difficulty: 3, rounds: 2},
            presentation: {enabled: true, duration: 30, difficulty: 3},
            group_discussion: {enabled: true, duration: 40, difficulty: 3, participant_count: 5},
        },
        results: {},
        generating: false,
    };

    // ─────────────────────────────────────────
    // 렌더링
    // ─────────────────────────────────────────

    function render() {
        renderStepBar();
        renderContent();
        renderSummary();
    }

    function renderStepBar() {
        const bar = document.getElementById('stepBar');
        bar.innerHTML = STEPS.map((s, i) => {
            let cls = 'step';
            if (s.num === state.step) cls += ' active';
            else if (s.num < state.step) cls += ' done';
            const arrow = i < STEPS.length - 1 ? '<span class="step-arrow">›</span>' : '';
            return `<div class="${cls}" onclick="goStep(${s.num})">
                <span class="num">${s.num < state.step ? '✓' : s.num}</span>
                ${s.label}
            </div>${arrow}`;
        }).join('');
    }

    function renderContent() {
        const main = document.getElementById('mainContent');
        switch(state.step) {
            case 1: main.innerHTML = renderPurpose(); break;
            case 2: main.innerHTML = renderLevel(); break;
            case 3: main.innerHTML = renderIndustry(); break;
            case 4: main.innerHTML = renderJob(); break;
            case 5: main.innerHTML = renderCompetencies(); break;
            case 6: main.innerHTML = renderMethods(); break;
            case 7: main.innerHTML = renderGenerate(); break;
        }
    }

    function renderPurpose() {
        return `
            <h2 class="section-title">평가 목적을 선택하세요</h2>
            <p class="section-desc">이 DC 시뮬레이션의 목적은 무엇인가요?</p>
            <div class="option-grid">
                ${DATA.purposes.map(p => `
                    <div class="option-card ${state.purpose === p.label ? 'selected' : ''}"
                         onclick="select('purpose','${p.label}')">
                        <div class="icon">${p.icon}</div>
                        ${p.label}
                    </div>
                `).join('')}
            </div>
            ${navButtons()}
        `;
    }

    function renderLevel() {
        const groups = {};
        DATA.levels.forEach(l => {
            if (!groups[l.group]) groups[l.group] = [];
            groups[l.group].push(l);
        });
        return `
            <h2 class="section-title">대상 직급을 선택하세요</h2>
            <p class="section-desc">평가 대상자의 직급을 선택하세요.</p>
            ${Object.entries(groups).map(([group, items]) => `
                <div class="category-group">
                    <div class="category-label">${group}</div>
                    <div class="option-grid">
                        ${items.map(l => `
                            <div class="option-card ${state.level === l.label ? 'selected' : ''}"
                                 onclick="select('level','${l.label}')">
                                ${l.label}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('')}
            ${navButtons()}
        `;
    }

    function renderIndustry() {
        return `
            <h2 class="section-title">산업/업종을 선택하세요</h2>
            <p class="section-desc">평가 대상자가 속한 산업 분야를 선택하세요.</p>
            ${Object.entries(DATA.industries).map(([cat, items]) => `
                <div class="category-group">
                    <div class="category-label">${cat}</div>
                    <div class="option-grid">
                        ${items.map(item => `
                            <div class="option-card ${state.industry === item ? 'selected' : ''}"
                                 onclick="select('industry','${item}')">
                                ${item}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('')}
            ${navButtons()}
        `;
    }

    function renderJob() {
        return `
            <h2 class="section-title">직무를 선택하세요</h2>
            <p class="section-desc">평가 대상자의 직무를 선택하세요.</p>
            ${Object.entries(DATA.jobs).map(([cat, items]) => `
                <div class="category-group">
                    <div class="category-label">${cat}</div>
                    <div class="option-grid">
                        ${items.map(item => `
                            <div class="option-card ${state.job === item ? 'selected' : ''}"
                                 onclick="select('job','${item}')">
                                ${item}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('')}
            ${navButtons()}
        `;
    }

    function renderCompetencies() {
        return `
            <h2 class="section-title">평가 역량을 선택하세요</h2>
            <p class="section-desc">측정할 역량을 선택하세요. (4~8개 권장)</p>
            ${Object.entries(DATA.competencies).map(([cat, data]) => `
                <div class="category-group">
                    <div class="category-label" style="color:${data.color}">${cat}</div>
                    <div class="competency-grid">
                        ${data.items.map(item => `
                            <div class="comp-chip ${state.competencies.includes(item) ? 'selected' : ''}"
                                 onclick="toggleComp('${item}')">
                                ${item}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('')}
            <div class="comp-count">선택됨: ${state.competencies.length}개 / 권장: 4~8개</div>
            ${navButtons()}
        `;
    }

    function renderMethods() {
        const methods = [
            {key:'in_basket', icon:'📥', name:'In-basket (서류함)', desc:'가상 업무 서류를 판단/처리',
             extra:'<label>서류 수<input type="number" value="${state.methods.in_basket.doc_count}" min="5" max="15" onchange="setMethodOpt(\'in_basket\',\'doc_count\',this.value)"></label>'},
            {key:'role_playing', icon:'🎭', name:'Role-playing (역할극)', desc:'특정 상황에서 역할 수행',
             extra:'<label>라운드<input type="number" value="${state.methods.role_playing.rounds}" min="1" max="4" onchange="setMethodOpt(\'role_playing\',\'rounds\',this.value)"></label>'},
            {key:'presentation', icon:'📊', name:'Presentation (발표)', desc:'자료 분석 후 발표', extra:''},
            {key:'group_discussion', icon:'💬', name:'Group Discussion (집단토론)', desc:'그룹 토론 참여',
             extra:'<label>참가자 수<input type="number" value="${state.methods.group_discussion.participant_count}" min="3" max="8" onchange="setMethodOpt(\'group_discussion\',\'participant_count\',this.value)"></label>'},
        ];

        return `
            <h2 class="section-title">평가 기법을 설정하세요</h2>
            <p class="section-desc">사용할 기법을 선택하고 시간/난이도를 설정하세요.</p>
            ${methods.map(m => `
                <div class="method-card ${state.methods[m.key].enabled ? 'selected' : ''}">
                    <div class="method-header">
                        <input type="checkbox" ${state.methods[m.key].enabled ? 'checked' : ''}
                               onchange="toggleMethod('${m.key}')">
                        <span style="font-size:20px">${m.icon}</span>
                        <span class="name">${m.name}</span>
                        <span style="color:#94a3b8;font-size:13px;margin-left:auto">${m.desc}</span>
                    </div>
                    ${state.methods[m.key].enabled ? `
                    <div class="method-settings">
                        <label>시간(분)
                            <input type="number" value="${state.methods[m.key].duration}"
                                   min="10" max="90"
                                   onchange="setMethodOpt('${m.key}','duration',this.value)">
                        </label>
                        <label>난이도
                            <select onchange="setMethodOpt('${m.key}','difficulty',this.value)">
                                <option value="1" ${state.methods[m.key].difficulty==1?'selected':''}>1 (쉬움)</option>
                                <option value="2" ${state.methods[m.key].difficulty==2?'selected':''}>2</option>
                                <option value="3" ${state.methods[m.key].difficulty==3?'selected':''}>3 (보통)</option>
                                <option value="4" ${state.methods[m.key].difficulty==4?'selected':''}>4</option>
                                <option value="5" ${state.methods[m.key].difficulty==5?'selected':''}>5 (어려움)</option>
                            </select>
                        </label>
                        ${m.extra}
                    </div>` : ''}
                </div>
            `).join('')}
            ${navButtons()}
        `;
    }

    function renderGenerate() {
        if (state.generating) {
            return `
                <div class="loading">
                    <div class="spinner"></div>
                    <div class="loading-text">시나리오를 생성하고 있습니다...</div>
                    <div class="loading-agent" id="loadingStatus">Claude AI가 시나리오를 설계 중입니다</div>
                </div>
            `;
        }

        if (Object.keys(state.results).length > 0) {
            return renderResults();
        }

        // 최종 확인 & 생성 버튼
        const enabledMethods = Object.entries(state.methods).filter(([k,v]) => v.enabled);
        const methodNames = {
            in_basket: '📥 In-basket', role_playing: '🎭 Role-playing',
            presentation: '📊 Presentation', group_discussion: '💬 Group Discussion'
        };

        return `
            <h2 class="section-title">시뮬레이션 생성</h2>
            <p class="section-desc">설정을 확인하고 생성 버튼을 눌러주세요.</p>

            <div class="result-container">
                <h3 style="color:#60a5fa; margin-bottom:16px;">설정 요약</h3>
                <table style="width:100%; font-size:14px;">
                    <tr><td style="color:#94a3b8; padding:6px 0; width:120px;">평가 목적</td><td>${state.purpose}</td></tr>
                    <tr><td style="color:#94a3b8; padding:6px 0;">대상 직급</td><td>${state.level}</td></tr>
                    <tr><td style="color:#94a3b8; padding:6px 0;">산업/업종</td><td>${state.industry}</td></tr>
                    <tr><td style="color:#94a3b8; padding:6px 0;">직무</td><td>${state.job}</td></tr>
                    <tr><td style="color:#94a3b8; padding:6px 0;">평가 역량</td><td>${state.competencies.join(', ')}</td></tr>
                    <tr><td style="color:#94a3b8; padding:6px 0;">사용 기법</td>
                        <td>${enabledMethods.map(([k,v]) => `${methodNames[k]} (${v.duration}분, 난이도${v.difficulty})`).join('<br>')}</td>
                    </tr>
                </table>
            </div>

            <div style="text-align:center; margin-top:30px;">
                <button class="btn btn-generate" onclick="startGenerate()">
                    AI 시나리오 생성 시작
                </button>
                <p style="color:#94a3b8; font-size:13px; margin-top:10px;">
                    기법당 약 30초~1분 소요됩니다
                </p>
            </div>

            <div class="btn-group">
                <button class="btn btn-prev" onclick="prevStep()">← 이전</button>
                <div></div>
            </div>
        `;
    }

    function renderResults() {
        const methodNames = {
            in_basket: '📥 In-basket', role_playing: '🎭 Role-playing',
            presentation: '📊 Presentation', group_discussion: '💬 Group Discussion'
        };
        const tabs = Object.keys(state.results);
        const activeTab = state.activeResultTab || tabs[0];

        return `
            <h2 class="section-title">생성 완료!</h2>
            <p class="section-desc">아래에서 생성된 시나리오를 확인하세요.</p>

            <div class="export-group">
                <button class="btn-export" onclick="exportZip()">📦 ZIP 패키지 다운로드</button>
                <button class="btn-export" onclick="exportCurrentMd()">📄 현재 탭 마크다운 복사</button>
                <button class="btn btn-prev" onclick="resetAll()" style="margin-left:auto;">🔄 처음부터 다시</button>
            </div>

            <div class="result-container" style="margin-top:16px;">
                <div class="result-tabs">
                    ${tabs.map(t => `
                        <div class="result-tab ${t === activeTab ? 'active' : ''}"
                             onclick="switchTab('${t}')">
                            ${methodNames[t] || t}
                        </div>
                    `).join('')}
                </div>
                <div class="result-content" id="resultContent">
                    ${formatScenario(state.results[activeTab], activeTab)}
                </div>
            </div>
        `;
    }

    function formatScenario(scenario, method) {
        if (!scenario) return '시나리오가 없습니다.';
        if (scenario.parse_error) return scenario.raw_text || 'JSON 파싱 실패';

        let html = `<h1>${scenario.title || method}</h1>\n\n`;

        if (method === 'in_basket') {
            const bg = scenario.background || {};
            html += `<h2>시나리오 배경</h2>\n${bg.full_text || bg.situation || ''}\n\n`;
            const docs = scenario.documents || [];
            html += `<h2>서류 목록 (${docs.length}건)</h2>\n\n`;
            docs.forEach(doc => {
                const icon = {상:'🔴',중:'🟡',하:'🟢'}[doc.urgency] || '⚪';
                html += `<h3>${icon} 서류${doc.id}: ${doc.subject}</h3>\n`;
                html += `발신: ${doc.from} | 유형: ${doc.type} | 역량: ${(doc.target_competencies||[]).join(', ')}\n\n`;
                html += `${doc.content}\n\n`;
                if (doc.model_answer) {
                    html += `[모범답안] 5점: ${doc.model_answer.score_5}\n`;
                    html += `          3점: ${doc.model_answer.score_3}\n`;
                    html += `          1점: ${doc.model_answer.score_1}\n\n`;
                }
            });
        } else if (method === 'role_playing') {
            (scenario.rounds || []).forEach(r => {
                const sit = r.situation_for_participant || {};
                const cp = r.counterpart || {};
                html += `<h2>라운드 ${r.round_number}</h2>\n`;
                html += `<h3>참가자 상황</h3>\n${sit.full_text || sit.context || ''}\n\n`;
                html += `<h3>상대역: ${cp.name} (${cp.title})</h3>\n`;
                html += `감정: ${cp.emotional_state} | 핵심요구: ${cp.core_need}\n\n`;
                html += `시작 대사: "${cp.opening_line}"\n\n`;
                const rs = cp.response_scenarios || {};
                Object.entries(rs).forEach(([k,v]) => {
                    html += `  ${k}: ${v}\n`;
                });
                html += '\n';
            });
        } else if (method === 'presentation') {
            const ti = scenario.task_instruction || {};
            html += `<h2>과제 지시문</h2>\n${ti.full_text || ti.overview || ''}\n\n`;
            (scenario.materials || []).forEach(m => {
                html += `<h3>자료 ${m.id}: ${m.title}</h3>\n${m.content}\n\n`;
            });
            const qa = scenario.qa_questions || {};
            html += `<h2>질의응답</h2>\n`;
            (qa.basic || []).forEach(q => html += `[기본] Q: ${q.question}\n`);
            (qa.advanced || []).forEach(q => html += `[심화] Q: ${q.question}\n`);
        } else if (method === 'group_discussion') {
            const topic = scenario.topic || {};
            html += `<h2>토론 주제</h2>\n${topic.statement || ''}\n\n${topic.full_text || topic.background || ''}\n\n`;
            (scenario.role_cards || []).forEach(c => {
                html += `<h3>역할 ${c.role_number}: ${c.department}</h3>\n${c.card_text}\n\n`;
            });
        }

        // 평가 기준
        const criteria = scenario.evaluation_criteria || [];
        if (criteria.length > 0) {
            html += `<h2>평가 기준</h2>\n`;
            criteria.forEach(c => {
                html += `<h3>${c.competency}</h3>\n`;
                (c.behavioral_indicators || []).forEach(b => html += `  - ${b}\n`);
                const bars = c.bars || {};
                Object.entries(bars).forEach(([s,v]) => html += `  ${s}점: ${v}\n`);
                html += '\n';
            });
        }

        if (scenario._meta) {
            html += `\n---\n생성 시간: ${scenario._meta.generation_time}초 | 토큰: ${scenario._meta.tokens}`;
        }

        return html;
    }

    // ─────────────────────────────────────────
    // 액션
    // ─────────────────────────────────────────

    function select(field, value) {
        state[field] = value;
        render();
    }

    function toggleComp(comp) {
        const idx = state.competencies.indexOf(comp);
        if (idx >= 0) state.competencies.splice(idx, 1);
        else state.competencies.push(comp);
        render();
    }

    function toggleMethod(key) {
        state.methods[key].enabled = !state.methods[key].enabled;
        render();
    }

    function setMethodOpt(method, key, value) {
        state.methods[method][key] = parseInt(value);
    }

    function goStep(n) { state.step = n; render(); }
    function nextStep() { if (state.step < 7) state.step++; render(); }
    function prevStep() { if (state.step > 1) state.step--; render(); }

    function switchTab(tab) {
        state.activeResultTab = tab;
        render();
    }

    function resetAll() {
        state = {
            step: 1, purpose: '', level: '', industry: '', job: '',
            competencies: [],
            methods: {
                in_basket: {enabled: true, duration: 30, difficulty: 3, doc_count: 10},
                role_playing: {enabled: true, duration: 20, difficulty: 3, rounds: 2},
                presentation: {enabled: true, duration: 30, difficulty: 3},
                group_discussion: {enabled: true, duration: 40, difficulty: 3, participant_count: 5},
            },
            results: {}, generating: false,
        };
        render();
    }

    async function startGenerate() {
        state.generating = true;
        state.results = {};
        render();

        const enabledMethods = Object.entries(state.methods)
            .filter(([k,v]) => v.enabled)
            .map(([k,v]) => k);

        const methodNames = {
            in_basket: 'In-basket (서류함)', role_playing: 'Role-playing (역할극)',
            presentation: 'Presentation (발표)', group_discussion: 'Group Discussion (집단토론)'
        };

        for (const method of enabledMethods) {
            const statusEl = document.getElementById('loadingStatus');
            if (statusEl) statusEl.textContent = `${methodNames[method]} 생성 중...`;

            try {
                const res = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        method: method,
                        params: {
                            evaluation_purpose: state.purpose,
                            target_level: state.level,
                            industry: state.industry,
                            job_function: state.job,
                            competencies: state.competencies,
                            difficulty: state.methods[method].difficulty,
                            duration: state.methods[method].duration,
                            doc_count: state.methods[method].doc_count,
                            rounds: state.methods[method].rounds,
                            participant_count: state.methods[method].participant_count,
                        }
                    })
                });
                const data = await res.json();
                if (data.success) {
                    state.results[method] = data.scenario;
                }
            } catch (e) {
                console.error(method, e);
            }
        }

        state.generating = false;
        state.activeResultTab = enabledMethods[0];
        render();
    }

    async function exportZip() {
        const res = await fetch('/api/export/zip', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                project_name: `DC_${state.purpose}_${state.level}`,
                scenarios: state.results
            })
        });
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `DC_시뮬레이션_${state.purpose}.zip`;
        a.click();
        URL.revokeObjectURL(url);
    }

    async function exportCurrentMd() {
        const tab = state.activeResultTab;
        const res = await fetch('/api/export/markdown', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({method: tab, scenario: state.results[tab]})
        });
        const data = await res.json();
        if (data.success) {
            navigator.clipboard.writeText(data.markdown);
            alert('마크다운이 클립보드에 복사되었습니다!');
        }
    }

    function navButtons() {
        return `
            <div class="btn-group">
                ${state.step > 1 ? '<button class="btn btn-prev" onclick="prevStep()">← 이전</button>' : '<div></div>'}
                <button class="btn btn-next" onclick="nextStep()">다음 →</button>
            </div>
        `;
    }

    function renderSummary() {
        const bar = document.getElementById('summaryBar');
        const content = document.getElementById('summaryContent');
        if (state.step < 2) { bar.style.display = 'none'; return; }
        bar.style.display = 'block';
        let html = '';
        if (state.purpose) html += `<div class="summary-item">목적: <span class="val">${state.purpose}</span></div>`;
        if (state.level) html += `<div class="summary-item">직급: <span class="val">${state.level}</span></div>`;
        if (state.industry) html += `<div class="summary-item">업종: <span class="val">${state.industry}</span></div>`;
        if (state.job) html += `<div class="summary-item">직무: <span class="val">${state.job}</span></div>`;
        if (state.competencies.length) html += `<div class="summary-item">역량: <span class="val">${state.competencies.length}개</span></div>`;
        content.innerHTML = html;
    }

    // 초기 렌더링
    render();
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  DC Simulation Builder")
    print("  http://localhost:5000 에서 접속하세요")
    print("=" * 50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
