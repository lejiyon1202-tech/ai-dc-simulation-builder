"""
토론 시뮬레이션 API
토론 세션 생성, 메시지 교환, 평가 등 토론 시뮬레이션 관련 엔드포인트
"""

import json
import logging
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import bp
from app.models import DiscussionSession, DiscussionMessage, SessionEvaluation
from app import db

logger = logging.getLogger(__name__)

VALID_PHASES = ('briefing', 'intro', 'discussion', 'consensus', 'summary')
VALID_STATUSES = ('preparing', 'briefing', 'intro', 'discussion', 'consensus',
                  'summary', 'evaluating', 'completed')
VALID_TOPIC_TYPES = ('resource_allocation', 'policy_decision',
                     'crisis_response', 'priority_setting')


def _get_discussion_engine():
    """discussion_engine 서비스 인스턴스를 가져온다."""
    from app.services.discussion_engine import get_discussion_engine
    return get_discussion_engine()


def _get_session_or_404(session_id, user_id):
    """세션을 조회하고, 존재하지 않거나 권한이 없으면 None과 에러 응답을 반환한다."""
    session = DiscussionSession.query.get(session_id)
    if not session:
        return None, (jsonify({
            'success': False,
            'message': '토론 세션을 찾을 수 없습니다.'
        }), 404)
    if session.user_id != user_id:
        return None, (jsonify({
            'success': False,
            'message': '해당 세션에 대한 접근 권한이 없습니다.'
        }), 403)
    return session, None


def _get_next_sequence_number(session_id):
    """해당 세션의 다음 sequence_number를 반환한다."""
    last_msg = (DiscussionMessage.query
                .filter_by(session_id=session_id)
                .order_by(DiscussionMessage.sequence_number.desc())
                .first())
    return (last_msg.sequence_number + 1) if last_msg else 1


@bp.route('/discussion/create-session', methods=['POST'])
@jwt_required()
def create_discussion_session():
    """토론 시뮬레이션 세션 생성"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'message': '요청 데이터가 없습니다.'}), 400

    # 필수 입력값 검증
    industry = data.get('industry')
    target_level = data.get('target_level')
    topic_type = data.get('topic_type')
    difficulty = data.get('difficulty', 3)

    if not industry or not target_level or not topic_type:
        return jsonify({
            'success': False,
            'message': 'industry, target_level, topic_type은 필수입니다.'
        }), 400

    if topic_type not in VALID_TOPIC_TYPES:
        return jsonify({
            'success': False,
            'message': f'지원하지 않는 토론 유형입니다: {topic_type}. '
                       f'{", ".join(VALID_TOPIC_TYPES)} 중 선택하세요.'
        }), 400

    if not isinstance(difficulty, int) or difficulty < 1 or difficulty > 5:
        return jsonify({
            'success': False,
            'message': 'difficulty는 1~5 사이의 정수여야 합니다.'
        }), 400

    competencies = data.get('competencies', [])
    if competencies and not isinstance(competencies, list):
        return jsonify({
            'success': False,
            'message': 'competencies는 배열 형태여야 합니다.'
        }), 400

    try:
        engine = _get_discussion_engine()
        scenario = engine.generate_discussion_scenario(
            industry=industry,
            target_level=target_level,
            topic_type=topic_type,
            difficulty=difficulty,
            competencies=competencies
        )

        session = DiscussionSession(
            user_id=current_user_id,
            topic_title=scenario.get('topic_title', ''),
            topic_description=scenario.get('topic_description', ''),
            topic_type=topic_type,
            industry=industry,
            target_level=target_level,
            difficulty=difficulty,
            # 참가자(사용자) 역할
            participant_role=scenario.get('participant_role', ''),
            participant_role_description=scenario.get('participant_role_description', ''),
            participant_materials=json.dumps(
                scenario.get('participant_materials'), ensure_ascii=False
            ) if scenario.get('participant_materials') else None,
            # AI 참가자 1
            ai1_name=scenario.get('ai1_name', ''),
            ai1_role=scenario.get('ai1_role', ''),
            ai1_role_description=scenario.get('ai1_role_description', ''),
            ai1_style=scenario.get('ai1_style', 'analytical_assertive'),
            ai1_materials=json.dumps(
                scenario.get('ai1_materials'), ensure_ascii=False
            ) if scenario.get('ai1_materials') else None,
            # AI 참가자 2
            ai2_name=scenario.get('ai2_name', ''),
            ai2_role=scenario.get('ai2_role', ''),
            ai2_role_description=scenario.get('ai2_role_description', ''),
            ai2_style=scenario.get('ai2_style', 'collaborative_mediating'),
            ai2_materials=json.dumps(
                scenario.get('ai2_materials'), ensure_ascii=False
            ) if scenario.get('ai2_materials') else None,
            # 공통 자료 및 역량
            common_materials=json.dumps(
                scenario.get('common_materials'), ensure_ascii=False
            ) if scenario.get('common_materials') else None,
            competencies=json.dumps(competencies, ensure_ascii=False) if competencies else None,
            status='preparing',
            total_duration=data.get('duration', 30)
        )
        db.session.add(session)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': session.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f'토론 세션 생성 중 오류: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': '토론 세션 생성 중 오류가 발생했습니다.'
        }), 500


@bp.route('/discussion/session/<int:session_id>', methods=['GET'])
@jwt_required()
def get_discussion_session(session_id):
    """토론 세션 정보 조회 (메시지 히스토리 + 평가 포함)"""
    current_user_id = get_jwt_identity()

    session, error = _get_session_or_404(session_id, current_user_id)
    if error:
        return error

    return jsonify({
        'success': True,
        'data': session.to_dict(include_messages=True, include_evaluation=True)
    }), 200


@bp.route('/discussion/session/<int:session_id>/message', methods=['POST'])
@jwt_required()
def send_discussion_message(session_id):
    """토론 메시지 전송 및 AI 응답 생성"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get('content'):
        return jsonify({'success': False, 'message': 'content는 필수입니다.'}), 400

    content = data['content'].strip()
    if not content:
        return jsonify({'success': False, 'message': '빈 메시지는 전송할 수 없습니다.'}), 400

    if len(content) > 5000:
        return jsonify({
            'success': False,
            'message': '메시지는 5000자를 초과할 수 없습니다.'
        }), 400

    session, error = _get_session_or_404(session_id, current_user_id)
    if error:
        return error

    if session.status in ('completed', 'evaluating'):
        return jsonify({
            'success': False,
            'message': '이미 종료되었거나 평가 중인 토론 세션입니다.'
        }), 400

    try:
        seq = _get_next_sequence_number(session.id)

        # 사용자 메시지 저장
        user_message = DiscussionMessage(
            session_id=session.id,
            sender_type='user',
            sender_name=session.participant_role or '참가자',
            content=content,
            message_type='statement',
            phase=session.status,
            sequence_number=seq
        )
        db.session.add(user_message)
        db.session.flush()

        # AI 응답 생성
        engine = _get_discussion_engine()
        message_history = [m.to_dict() for m in session.messages]

        # 다음 발언자 결정
        updated_history = message_history + [user_message.to_dict()]
        last_speaker_name = user_message.sender_type or 'user'
        next_speaker = engine.determine_next_speaker(
            current_phase=session.status,
            message_history=updated_history,
            last_speaker=last_speaker_name
        )

        # AI 응답 생성
        ai_response = engine.generate_ai_response(
            session=session.to_dict(),
            sender=next_speaker,
            message_history=updated_history,
            current_phase=session.status
        )

        # AI 메시지 저장
        ai_messages = []
        responses = ai_response if isinstance(ai_response, list) else [ai_response]
        for resp in responses:
            seq += 1
            ai_msg = DiscussionMessage(
                session_id=session.id,
                sender_type=resp.get('sender_type', 'ai1'),
                sender_name=resp.get('sender_name', resp.get('sender', 'AI')),
                content=resp.get('content', ''),
                message_type=resp.get('message_type', 'statement'),
                phase=session.status,
                sequence_number=seq
            )
            db.session.add(ai_msg)
            ai_messages.append(ai_msg)

        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'user_message': user_message.to_dict(),
                'ai_responses': [m.to_dict() for m in ai_messages]
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f'토론 메시지 처리 중 오류: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': '메시지 처리 중 오류가 발생했습니다.'
        }), 500


@bp.route('/discussion/session/<int:session_id>/phase', methods=['POST'])
@jwt_required()
def update_discussion_phase(session_id):
    """토론 단계 업데이트"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get('phase'):
        return jsonify({'success': False, 'message': 'phase는 필수입니다.'}), 400

    phase = data['phase']
    if phase not in VALID_PHASES:
        return jsonify({
            'success': False,
            'message': f'지원하지 않는 단계입니다: {phase}. '
                       f'{", ".join(VALID_PHASES)} 중 선택하세요.'
        }), 400

    session, error = _get_session_or_404(session_id, current_user_id)
    if error:
        return error

    if session.status in ('completed', 'evaluating'):
        return jsonify({
            'success': False,
            'message': '이미 종료되었거나 평가 중인 토론 세션입니다.'
        }), 400

    try:
        session.status = phase
        ai_messages = []

        # intro 단계에서는 AI 참가자들의 초기 입장 발언을 자동 생성
        if phase == 'intro':
            engine = _get_discussion_engine()

            intro_responses = engine.generate_intro_statements(
                session=session.to_dict()
            )

            seq = _get_next_sequence_number(session.id)
            for resp in intro_responses:
                ai_msg = DiscussionMessage(
                    session_id=session.id,
                    sender_type=resp.get('sender_type', 'ai1'),
                    sender_name=resp.get('sender_name', resp.get('sender', 'AI')),
                    content=resp.get('content', ''),
                    message_type=resp.get('message_type', 'statement'),
                    phase='intro',
                    sequence_number=seq
                )
                db.session.add(ai_msg)
                ai_messages.append(ai_msg)
                seq += 1

        db.session.commit()

        response_data = {
            'phase': phase,
        }
        if ai_messages:
            response_data['ai_messages'] = [m.to_dict() for m in ai_messages]

        return jsonify({
            'success': True,
            'data': response_data
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f'토론 단계 업데이트 중 오류: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': '단계 업데이트 중 오류가 발생했습니다.'
        }), 500


@bp.route('/discussion/session/<int:session_id>/evaluate', methods=['POST'])
@jwt_required()
def evaluate_discussion_session(session_id):
    """토론 세션 평가"""
    current_user_id = get_jwt_identity()

    session, error = _get_session_or_404(session_id, current_user_id)
    if error:
        return error

    if session.evaluation:
        return jsonify({
            'success': False,
            'message': '이미 평가가 완료된 세션입니다.'
        }), 400

    try:
        # 평가 중 상태로 변경
        session.status = 'evaluating'
        db.session.flush()

        engine = _get_discussion_engine()
        message_history = [m.to_dict() for m in session.messages]
        competencies = json.loads(session.competencies) if session.competencies else []

        evaluation_result = engine.generate_evaluation(
            session=session.to_dict(),
            message_history=message_history,
            competencies=competencies
        )

        # 평가 결과 저장
        evaluation = SessionEvaluation(
            session_id=session.id,
            overall_score=evaluation_result.get('overall_score'),
            competency_scores=json.dumps(
                evaluation_result.get('competency_scores', {}), ensure_ascii=False
            ),
            strengths=json.dumps(
                evaluation_result.get('strengths', []), ensure_ascii=False
            ),
            development_areas=json.dumps(
                evaluation_result.get('development_areas', []), ensure_ascii=False
            ),
            detailed_feedback=evaluation_result.get('detailed_feedback', ''),
            development_guide=json.dumps(
                evaluation_result.get('development_guide'), ensure_ascii=False
            ) if evaluation_result.get('development_guide') else None,
            participation_stats=json.dumps(
                evaluation_result.get('participation_stats', {}), ensure_ascii=False
            )
        )
        db.session.add(evaluation)

        # 세션 상태를 completed로 변경
        session.status = 'completed'
        db.session.commit()

        return jsonify({
            'success': True,
            'data': evaluation.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f'토론 평가 중 오류: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': '평가 중 오류가 발생했습니다.'
        }), 500


@bp.route('/discussion/sessions', methods=['GET'])
@jwt_required()
def list_discussion_sessions():
    """현재 사용자의 토론 세션 목록 조회 (페이지네이션 + 상태 필터)"""
    current_user_id = get_jwt_identity()

    # 쿼리 파라미터
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')

    # 범위 보정
    per_page = max(1, min(per_page, 50))
    page = max(1, page)

    query = DiscussionSession.query.filter_by(user_id=current_user_id)

    if status:
        if status not in VALID_STATUSES:
            return jsonify({
                'success': False,
                'message': f'유효하지 않은 상태 필터입니다. '
                           f'{", ".join(VALID_STATUSES)} 중 선택하세요.'
            }), 400
        query = query.filter_by(status=status)

    query = query.order_by(DiscussionSession.updated_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'success': True,
        'data': {
            'sessions': [s.to_dict() for s in pagination.items],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
    }), 200


@bp.route('/discussion/session/<int:session_id>', methods=['DELETE'])
@jwt_required()
def delete_discussion_session(session_id):
    """토론 세션 삭제"""
    current_user_id = get_jwt_identity()

    session, error = _get_session_or_404(session_id, current_user_id)
    if error:
        return error

    try:
        db.session.delete(session)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '토론 세션이 삭제되었습니다.'
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f'토론 세션 삭제 중 오류: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': '세션 삭제 중 오류가 발생했습니다.'
        }), 500
