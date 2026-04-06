"""
DC 시뮬레이션 문서 내보내기 서비스
생성된 시나리오를 Word, PDF 등의 문서 패키지로 변환합니다.
"""

import json
import os
import zipfile
import tempfile
from io import BytesIO


def export_to_markdown(scenario: dict, method: str) -> str:
    """시나리오를 마크다운 문서로 변환합니다."""
    md = ""

    if method == "in_basket":
        md = _export_in_basket_md(scenario)
    elif method == "role_playing":
        md = _export_role_playing_md(scenario)
    elif method == "presentation":
        md = _export_presentation_md(scenario)
    elif method in ("group_discussion", "gd_assigned_role"):
        md = _export_group_discussion_md(scenario)
    elif method == "gd_free_discussion":
        md = _export_gd_free_discussion_md(scenario)
    elif method == "case_study":
        md = _export_case_study_md(scenario)

    return md


def _export_in_basket_md(s: dict) -> str:
    """In-basket 시나리오를 마크다운으로 변환"""
    md = f"# 📥 In-basket: {s.get('title', '서류함 기법')}\n\n"

    # 배경
    bg = s.get("background", {})
    md += "## 1. 시나리오 배경\n\n"
    md += f"{bg.get('full_text', bg.get('situation', ''))}\n\n"
    md += f"- **회사**: {bg.get('company', '')}\n"
    md += f"- **역할**: {bg.get('role', '')}\n"
    md += f"- **날짜**: {bg.get('date', '')}\n"
    md += f"- **제약 조건**: {bg.get('constraints', '')}\n\n"

    # 서류
    docs = s.get("documents", [])
    md += f"## 2. 서류 목록 ({len(docs)}건)\n\n"
    for doc in docs:
        urgency_icon = {"상": "🔴", "중": "🟡", "하": "🟢"}.get(doc.get("urgency", "중"), "⚪")
        md += f"### 서류 {doc.get('id', '')}: {doc.get('subject', '')}\n\n"
        md += f"- **유형**: {doc.get('type', '')}\n"
        md += f"- **발신**: {doc.get('from', '')}\n"
        md += f"- **긴급도**: {urgency_icon} {doc.get('urgency', '')}\n"
        md += f"- **측정 역량**: {', '.join(doc.get('target_competencies', []))}\n\n"
        md += f"**내용:**\n\n{doc.get('content', '')}\n\n"

        ma = doc.get("model_answer", {})
        if ma:
            md += "**모범 조치:**\n\n"
            md += f"| 점수 | 조치 |\n|------|------|\n"
            md += f"| 5점 (우수) | {ma.get('score_5', '')} |\n"
            md += f"| 3점 (보통) | {ma.get('score_3', '')} |\n"
            md += f"| 1점 (미흡) | {ma.get('score_1', '')} |\n\n"
        md += "---\n\n"

    # 평가 기준
    md += _export_evaluation_criteria(s)
    # 진행자 가이드
    md += f"## 4. 진행자 가이드\n\n{s.get('facilitator_guide', '')}\n"

    return md


def _export_role_playing_md(s: dict) -> str:
    """Role-playing 시나리오를 마크다운으로 변환"""
    md = f"# 🎭 Role-playing: {s.get('title', '역할극')}\n\n"

    rounds = s.get("rounds", [])
    for r in rounds:
        md += f"## 라운드 {r.get('round_number', '')}\n\n"

        # 참가자용
        sit = r.get("situation_for_participant", {})
        md += "### 참가자용 상황 설명\n\n"
        md += f"{sit.get('full_text', sit.get('context', ''))}\n\n"
        md += f"- **역할**: {sit.get('role', '')}\n"
        md += f"- **목표**: {sit.get('objective', '')}\n"
        md += f"- **제약**: {sit.get('constraints', '')}\n\n"

        # 상대역용
        cp = r.get("counterpart", {})
        md += "### 상대역 행동 지침 (평가자/배우용)\n\n"
        md += f"- **이름**: {cp.get('name', '')}\n"
        md += f"- **직책**: {cp.get('title', '')}\n"
        md += f"- **성격**: {cp.get('personality', '')}\n"
        md += f"- **감정 상태**: {cp.get('emotional_state', '')}\n"
        md += f"- **핵심 요구**: {cp.get('core_need', '')}\n\n"

        md += f"**시작 대사:**\n> \"{cp.get('opening_line', '')}\"\n\n"

        rs = cp.get("response_scenarios", {})
        if rs:
            md += "**참가자 반응별 대응:**\n\n"
            md += f"| 참가자 반응 | 상대역 대응 |\n|------------|------------|\n"
            for k, v in rs.items():
                label = {"empathy": "공감", "ignore": "무시", "solution": "해결책 제시",
                         "aggressive": "공격적", "compromise": "타협"}.get(k, k)
                md += f"| {label} | {v} |\n"
            md += "\n"

        md += f"- **양보 불가**: {cp.get('non_negotiable', '')}\n"
        md += f"- **양보 가능**: {cp.get('negotiable', '')}\n\n"

        key_lines = cp.get("key_lines", [])
        if key_lines:
            md += "**주요 대사:**\n"
            for line in key_lines:
                md += f'> "{line}"\n\n'

        md += "---\n\n"

    md += _export_evaluation_criteria(s)
    md += f"## 진행자 가이드\n\n{s.get('facilitator_guide', '')}\n"
    return md


def _export_presentation_md(s: dict) -> str:
    """Presentation 시나리오를 마크다운으로 변환"""
    md = f"# 📊 Presentation: {s.get('title', '발표 과제')}\n\n"

    ti = s.get("task_instruction", {})
    md += "## 1. 과제 지시문\n\n"
    md += f"{ti.get('full_text', ti.get('overview', ''))}\n\n"
    md += f"- **발표 대상**: {ti.get('audience', '')}\n"
    md += f"- **기대 구성**: {ti.get('expected_structure', '')}\n"
    md += f"- **제약 조건**: {ti.get('constraints', '')}\n\n"

    materials = s.get("materials", [])
    md += f"## 2. 제공 자료 ({len(materials)}건)\n\n"
    for mat in materials:
        md += f"### 자료 {mat.get('id', '')}: {mat.get('title', '')}\n"
        md += f"*유형: {mat.get('type', '')}*\n\n"
        md += f"{mat.get('content', '')}\n\n"
        if mat.get("has_conflicting_info"):
            md += f"⚠️ **상충 정보**: {mat.get('conflict_detail', '')}\n\n"
        md += "---\n\n"

    qa = s.get("qa_questions", {})
    md += "## 3. 질의응답 질문\n\n"
    md += "### 기본 질문\n\n"
    for q in qa.get("basic", []):
        md += f"**Q**: {q.get('question', '')}\n"
        md += f"- 측정 의도: {q.get('intent', '')}\n"
        md += f"- 좋은 답변 방향: {q.get('good_answer_guide', '')}\n\n"

    md += "### 심화/압박 질문\n\n"
    for q in qa.get("advanced", []):
        md += f"**Q**: {q.get('question', '')}\n"
        md += f"- 측정 의도: {q.get('intent', '')}\n"
        md += f"- 좋은 답변 방향: {q.get('good_answer_guide', '')}\n\n"

    md += _export_evaluation_criteria(s)
    md += f"## 진행자 가이드\n\n{s.get('facilitator_guide', '')}\n"
    return md


def _export_group_discussion_md(s: dict) -> str:
    """Group Discussion 시나리오를 마크다운으로 변환"""
    md = f"# 💬 Group Discussion: {s.get('title', '집단토론')}\n\n"

    topic = s.get("topic", {})
    md += "## 1. 토론 주제\n\n"
    md += f"### {topic.get('statement', '')}\n\n"
    md += f"{topic.get('full_text', topic.get('background', ''))}\n\n"

    positions = topic.get("expected_positions", [])
    if positions:
        md += "**예상 입장:**\n"
        for p in positions:
            md += f"- {p}\n"
        md += "\n"

    materials = s.get("materials", [])
    if materials:
        md += f"## 2. 배경 자료 ({len(materials)}건)\n\n"
        for mat in materials:
            md += f"### {mat.get('title', '')}\n"
            md += f"{mat.get('content', '')}\n"
            md += f"*관점: {mat.get('perspective', '')}*\n\n---\n\n"

    role_cards = s.get("role_cards", [])
    if role_cards:
        md += f"## 3. 역할 카드 ({len(role_cards)}개)\n\n"
        for card in role_cards:
            md += f"### 역할 {card.get('role_number', '')}: {card.get('department', '')}\n"
            md += f"{card.get('card_text', '')}\n\n"

    rules = s.get("discussion_rules", {})
    md += "## 4. 토론 규칙\n\n"
    md += f"- **시간**: {rules.get('duration', '')}분\n"
    md += f"- **형식**: {rules.get('format', '')}\n"
    md += f"- **목표**: {rules.get('goal', '')}\n"
    for rule in rules.get("rules", []):
        md += f"- {rule}\n"
    md += "\n"

    observer = s.get("observer_sheet", {})
    if observer:
        md += "## 5. 관찰자 평가 시트\n\n"
        md += "### 관찰 항목\n"
        for item in observer.get("individual_items", []):
            md += f"- [ ] {item}\n"
        md += "\n"

        md += "### 역량별 평가\n\n"
        for comp in observer.get("competency_mapping", []):
            md += f"**{comp.get('competency', '')}**\n"
            for b in comp.get("observable_behaviors", []):
                md += f"- {b}\n"
            bars = comp.get("bars", {})
            if bars:
                md += f"\n| 점수 | 기준 |\n|------|------|\n"
                for score in ["5", "3", "1"]:
                    if score in bars:
                        md += f"| {score}점 | {bars[score]} |\n"
                md += "\n"

    md += _export_evaluation_criteria(s)
    md += f"## 진행자 가이드\n\n{s.get('facilitator_guide', '')}\n"
    return md


def _export_gd_free_discussion_md(s: dict) -> str:
    """자유토론형 집단토론 시나리오를 마크다운으로 변환"""
    md = f"# 💬 집단토론 (자유토론형): {s.get('title', '자유토론')}\n\n"

    topic = s.get("topic", {})
    md += "## 1. 토론 주제\n\n"
    md += f"### {topic.get('statement', '')}\n\n"
    md += f"{topic.get('full_text', topic.get('background', ''))}\n\n"

    materials = s.get("materials", s.get("common_materials", []))
    if materials:
        md += f"## 2. 공통 자료 ({len(materials)}건)\n\n"
        for mat in materials:
            md += f"### {mat.get('title', '')}\n"
            md += f"{mat.get('content', '')}\n\n---\n\n"

    guide = s.get("discussion_guide", {})
    if guide:
        md += "## 3. 토론 진행 가이드\n\n"
        for phase in guide.get("phases", []):
            md += f"### {phase.get('name', '')}\n"
            md += f"- 시간: {phase.get('duration', '')}분\n"
            md += f"- 활동: {phase.get('activity', '')}\n\n"

    rules = s.get("discussion_rules", {})
    md += "## 4. 토론 규칙\n\n"
    md += f"- **시간**: {rules.get('duration', '')}분\n"
    md += f"- **형식**: {rules.get('format', '')}\n"
    md += f"- **목표**: {rules.get('goal', '')}\n"
    for rule in rules.get("rules", []):
        md += f"- {rule}\n"
    md += "\n"

    md += _export_evaluation_criteria(s)
    md += f"## 진행자 가이드\n\n{s.get('facilitator_guide', '')}\n"
    return md


def _export_case_study_md(s: dict) -> str:
    """Case Study 시나리오를 마크다운으로 변환"""
    md = f"# 📋 Case Study: {s.get('title', '사례분석')}\n\n"

    # 사례 개요
    overview = s.get("case_overview", s.get("background", {}))
    md += "## 1. 사례 개요\n\n"
    md += f"{overview.get('full_text', overview.get('situation', ''))}\n\n"
    if overview.get("company"):
        md += f"- **기업**: {overview.get('company', '')}\n"
    if overview.get("industry"):
        md += f"- **산업**: {overview.get('industry', '')}\n"
    if overview.get("key_issue"):
        md += f"- **핵심 이슈**: {overview.get('key_issue', '')}\n"
    md += "\n"

    # 제공 데이터/자료
    data = s.get("provided_data", s.get("materials", []))
    if data:
        md += f"## 2. 제공 자료 ({len(data)}건)\n\n"
        for d in data:
            md += f"### {d.get('title', d.get('id', ''))}\n"
            md += f"{d.get('content', '')}\n\n---\n\n"

    # 분석 과제
    tasks = s.get("analysis_tasks", s.get("questions", []))
    if tasks:
        md += f"## 3. 분석 과제 ({len(tasks)}개)\n\n"
        for i, t in enumerate(tasks, 1):
            if isinstance(t, dict):
                md += f"### 과제 {i}: {t.get('question', t.get('title', ''))}\n"
                md += f"{t.get('description', '')}\n"
                if t.get("guide"):
                    md += f"- **가이드**: {t.get('guide', '')}\n"
                md += "\n"
            else:
                md += f"### 과제 {i}\n{t}\n\n"

    # 모범답안
    model_answer = s.get("model_answer", {})
    if model_answer:
        md += "## 4. 모범답안 가이드 (평가자용)\n\n"
        if isinstance(model_answer, dict):
            for k, v in model_answer.items():
                md += f"### {k}\n{v}\n\n"
        elif isinstance(model_answer, str):
            md += f"{model_answer}\n\n"

    md += _export_evaluation_criteria(s)
    md += f"## 진행자 가이드\n\n{s.get('facilitator_guide', '')}\n"
    return md


def _export_evaluation_criteria(s: dict) -> str:
    """공통 평가 기준 섹션"""
    criteria = s.get("evaluation_criteria", [])
    if not criteria:
        return ""

    md = "## 평가 기준표\n\n"
    for c in criteria:
        md += f"### {c.get('competency', '')}\n\n"
        indicators = c.get("behavioral_indicators", [])
        if indicators:
            md += "**행동 지표:**\n"
            for ind in indicators:
                md += f"- {ind}\n"
            md += "\n"

        bars = c.get("bars", {})
        if bars:
            md += "| 점수 | 기준 |\n|------|------|\n"
            for score in sorted(bars.keys(), reverse=True):
                md += f"| {score}점 | {bars[score]} |\n"
            md += "\n"

    return md


def export_package(project_name: str, scenarios: dict) -> BytesIO:
    """
    전체 시나리오를 ZIP 패키지로 내보냅니다.

    Args:
        project_name: 프로젝트 이름
        scenarios: 기법별 시나리오 딕셔너리

    Returns:
        ZIP 파일의 BytesIO 객체
    """
    buffer = BytesIO()

    method_names = {
        "in_basket": "01_인바스켓(In-basket)",
        "role_playing": "02_역할극(Role-playing)",
        "presentation": "03_발표(Presentation)",
        "group_discussion": "04_집단토론(Group Discussion)",
        "gd_assigned_role": "04_집단토론_역할부여형",
        "gd_free_discussion": "05_집단토론_자유토론형",
        "case_study": "06_사례분석(Case Study)",
    }

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 전체 개요 문서
        overview = f"# {project_name} - DC 시뮬레이션 패키지\n\n"
        overview += "## 포함된 시뮬레이션\n\n"

        for method, scenario in scenarios.items():
            folder = method_names.get(method, method)
            title = scenario.get("title", method)
            overview += f"- **{folder}**: {title}\n"

            # 기법별 마크다운 문서
            md_content = export_to_markdown(scenario, method)
            zf.writestr(f"{project_name}/{folder}/시나리오_전체.md", md_content)

            # JSON 원본 데이터 (나중에 수정/재활용용)
            json_content = json.dumps(scenario, ensure_ascii=False, indent=2)
            zf.writestr(f"{project_name}/{folder}/scenario_data.json", json_content)

            # 기법별 개별 문서 분리
            if method == "in_basket":
                _zip_in_basket_docs(zf, project_name, folder, scenario)
            elif method == "role_playing":
                _zip_role_playing_docs(zf, project_name, folder, scenario)
            elif method == "presentation":
                _zip_presentation_docs(zf, project_name, folder, scenario)
            elif method in ("group_discussion", "gd_assigned_role"):
                _zip_group_discussion_docs(zf, project_name, folder, scenario)
            elif method == "gd_free_discussion":
                _zip_gd_free_discussion_docs(zf, project_name, folder, scenario)
            elif method == "case_study":
                _zip_case_study_docs(zf, project_name, folder, scenario)

        overview += f"\n\n생성일: 자동 생성됨\n"
        zf.writestr(f"{project_name}/README.md", overview)

    buffer.seek(0)
    return buffer


def _zip_in_basket_docs(zf, project_name, folder, scenario):
    """In-basket 개별 서류 파일 생성"""
    bg = scenario.get("background", {})
    zf.writestr(
        f"{project_name}/{folder}/참가자용_배경설명.md",
        f"# 시나리오 배경\n\n{bg.get('full_text', bg.get('situation', ''))}\n",
    )

    for doc in scenario.get("documents", []):
        doc_id = doc.get("id", "")
        subject = doc.get("subject", "").replace("/", "_")
        content = f"# {doc.get('subject', '')}\n\n"
        content += f"**발신**: {doc.get('from', '')}\n"
        content += f"**유형**: {doc.get('type', '')}\n"
        content += f"**긴급도**: {doc.get('urgency', '')}\n\n---\n\n"
        content += doc.get("content", "")
        zf.writestr(f"{project_name}/{folder}/서류/서류{doc_id:02d}_{subject}.md", content)

    # 채점표
    scoring = "# 채점 가이드\n\n"
    for doc in scenario.get("documents", []):
        ma = doc.get("model_answer", {})
        scoring += f"## 서류 {doc.get('id', '')}: {doc.get('subject', '')}\n"
        scoring += f"- 5점: {ma.get('score_5', '')}\n"
        scoring += f"- 3점: {ma.get('score_3', '')}\n"
        scoring += f"- 1점: {ma.get('score_1', '')}\n\n"
    zf.writestr(f"{project_name}/{folder}/평가자용_채점가이드.md", scoring)


def _zip_role_playing_docs(zf, project_name, folder, scenario):
    """Role-playing 개별 문서 생성"""
    for r in scenario.get("rounds", []):
        rn = r.get("round_number", 1)
        sit = r.get("situation_for_participant", {})
        zf.writestr(
            f"{project_name}/{folder}/라운드{rn}_참가자용.md",
            f"# 라운드 {rn} - 상황 설명\n\n{sit.get('full_text', sit.get('context', ''))}\n",
        )

        cp = r.get("counterpart", {})
        actor_guide = f"# 라운드 {rn} - 상대역 행동 지침\n\n"
        actor_guide += f"**이름**: {cp.get('name', '')}\n"
        actor_guide += f"**직책**: {cp.get('title', '')}\n"
        actor_guide += f"**감정**: {cp.get('emotional_state', '')}\n\n"
        actor_guide += f"## 시작 대사\n> \"{cp.get('opening_line', '')}\"\n\n"
        actor_guide += "## 반응별 대응\n\n"
        for k, v in cp.get("response_scenarios", {}).items():
            actor_guide += f"- **{k}**: {v}\n"
        zf.writestr(f"{project_name}/{folder}/라운드{rn}_상대역지침.md", actor_guide)


def _zip_presentation_docs(zf, project_name, folder, scenario):
    """Presentation 개별 문서 생성"""
    ti = scenario.get("task_instruction", {})
    zf.writestr(
        f"{project_name}/{folder}/참가자용_과제지시문.md",
        f"# 발표 과제\n\n{ti.get('full_text', ti.get('overview', ''))}\n",
    )

    for mat in scenario.get("materials", []):
        mat_id = mat.get("id", "")
        title = mat.get("title", "").replace("/", "_")
        zf.writestr(
            f"{project_name}/{folder}/제공자료/자료{mat_id}_{title}.md",
            f"# {mat.get('title', '')}\n\n{mat.get('content', '')}\n",
        )

    qa = scenario.get("qa_questions", {})
    qa_doc = "# 질의응답 질문 목록 (평가자용)\n\n"
    qa_doc += "## 기본 질문\n"
    for q in qa.get("basic", []):
        qa_doc += f"- **Q**: {q.get('question', '')}\n  - 의도: {q.get('intent', '')}\n\n"
    qa_doc += "## 심화 질문\n"
    for q in qa.get("advanced", []):
        qa_doc += f"- **Q**: {q.get('question', '')}\n  - 의도: {q.get('intent', '')}\n\n"
    zf.writestr(f"{project_name}/{folder}/평가자용_질의목록.md", qa_doc)


def _zip_group_discussion_docs(zf, project_name, folder, scenario):
    """Group Discussion 개별 문서 생성"""
    topic = scenario.get("topic", {})
    zf.writestr(
        f"{project_name}/{folder}/참가자용_토론주제.md",
        f"# 토론 주제\n\n{topic.get('full_text', topic.get('background', ''))}\n",
    )

    for card in scenario.get("role_cards", []):
        rn = card.get("role_number", "")
        dept = card.get("department", "").replace("/", "_")
        zf.writestr(
            f"{project_name}/{folder}/역할카드/역할{rn}_{dept}.md",
            f"# 역할 카드 {rn}\n\n{card.get('card_text', '')}\n",
        )

    observer = scenario.get("observer_sheet", {})
    if observer:
        sheet = "# 관찰자 평가 시트\n\n## 개인별 관찰 기록\n\n"
        sheet += "| 참가자 | " + " | ".join(observer.get("individual_items", [])) + " |\n"
        sheet += "|--------|" + "|".join(["--------"] * len(observer.get("individual_items", []))) + "|\n"
        sheet += "|        |" + "|".join(["        "] * len(observer.get("individual_items", []))) + "|\n"
        zf.writestr(f"{project_name}/{folder}/평가자용_관찰시트.md", sheet)


def _zip_gd_free_discussion_docs(zf, project_name, folder, scenario):
    """자유토론형 집단토론 개별 문서 생성"""
    topic = scenario.get("topic", {})
    zf.writestr(
        f"{project_name}/{folder}/참가자용_토론주제.md",
        f"# 토론 주제\n\n{topic.get('full_text', topic.get('background', ''))}\n",
    )

    materials = scenario.get("materials", scenario.get("common_materials", []))
    for i, mat in enumerate(materials, 1):
        title = mat.get("title", f"자료{i}").replace("/", "_")
        zf.writestr(
            f"{project_name}/{folder}/공통자료/{title}.md",
            f"# {mat.get('title', '')}\n\n{mat.get('content', '')}\n",
        )


def _zip_case_study_docs(zf, project_name, folder, scenario):
    """Case Study 개별 문서 생성"""
    overview = scenario.get("case_overview", scenario.get("background", {}))
    zf.writestr(
        f"{project_name}/{folder}/참가자용_사례개요.md",
        f"# 사례 개요\n\n{overview.get('full_text', overview.get('situation', ''))}\n",
    )

    data = scenario.get("provided_data", scenario.get("materials", []))
    for i, d in enumerate(data, 1):
        title = d.get("title", f"자료{i}").replace("/", "_")
        zf.writestr(
            f"{project_name}/{folder}/제공자료/{title}.md",
            f"# {d.get('title', '')}\n\n{d.get('content', '')}\n",
        )

    tasks = scenario.get("analysis_tasks", scenario.get("questions", []))
    if tasks:
        task_doc = "# 분석 과제\n\n"
        for i, t in enumerate(tasks, 1):
            if isinstance(t, dict):
                task_doc += f"## 과제 {i}: {t.get('question', t.get('title', ''))}\n"
                task_doc += f"{t.get('description', '')}\n\n"
            else:
                task_doc += f"## 과제 {i}\n{t}\n\n"
        zf.writestr(f"{project_name}/{folder}/참가자용_분석과제.md", task_doc)

    model_answer = scenario.get("model_answer", {})
    if model_answer:
        answer_doc = "# 모범답안 가이드 (평가자용)\n\n"
        if isinstance(model_answer, dict):
            for k, v in model_answer.items():
                answer_doc += f"## {k}\n{v}\n\n"
        elif isinstance(model_answer, str):
            answer_doc += f"{model_answer}\n"
        zf.writestr(f"{project_name}/{folder}/평가자용_모범답안.md", answer_doc)
