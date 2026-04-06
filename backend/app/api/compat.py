"""
호환 라우트 — 프론트엔드 API 경로 ↔ 백엔드 라우트 브릿지
run_legacy.py의 API 경로를 backend 핸들러에 매핑합니다.

프론트엔드가 호출하는 경로:
  /api/generate          → /api/generate/single
  /api/refine            → /api/generate/regenerate-part
  /api/export/zip        → /api/export/package
  /api/discussion/message  → /api/discussion/session/:id/message (body에서 session_id)
  /api/discussion/phase    → /api/discussion/session/:id/phase (body에서 session_id)
  /api/discussion/evaluate → /api/discussion/session/:id/evaluate (body에서 session_id)
"""
from flask import request, jsonify
from app.api import bp


@bp.route('/generate', methods=['POST'])
def compat_generate():
    """프론트엔드 /api/generate → /api/generate/single 포워딩"""
    from app.api.generate import generate_single
    return generate_single()


@bp.route('/refine', methods=['POST'])
def compat_refine():
    """프론트엔드 /api/refine → /api/generate/regenerate-part 포워딩"""
    from app.api.generate import regenerate_part
    return regenerate_part()


@bp.route('/export/zip', methods=['POST'])
def compat_export_zip():
    """프론트엔드 /api/export/zip → /api/export/package 포워딩"""
    from app.api.generate import export_zip_package
    return export_zip_package()


@bp.route('/discussion/message', methods=['POST'])
def compat_discussion_message():
    """프론트엔드 /api/discussion/message (body에 session_id) → 세션 라우트 포워딩"""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'session_id는 필수입니다.'}), 400

    from app.api.discussion import send_discussion_message
    return send_discussion_message(int(session_id))


@bp.route('/discussion/phase', methods=['POST'])
def compat_discussion_phase():
    """프론트엔드 /api/discussion/phase (body에 session_id) → 세션 라우트 포워딩"""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'session_id는 필수입니다.'}), 400

    from app.api.discussion import update_discussion_phase
    return update_discussion_phase(int(session_id))


@bp.route('/discussion/evaluate', methods=['POST'])
def compat_discussion_evaluate():
    """프론트엔드 /api/discussion/evaluate (body에 session_id) → 세션 라우트 포워딩"""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'message': 'session_id는 필수입니다.'}), 400

    from app.api.discussion import evaluate_discussion_session
    return evaluate_discussion_session(int(session_id))
