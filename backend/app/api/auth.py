"""
인증 API
사용자 등록, 로그인, 토큰 갱신
"""
from flask import jsonify, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from app.api import bp
from app.models import User
from app import db


@bp.route('/auth/register', methods=['POST'])
def register():
    """사용자 등록"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '요청 데이터가 없습니다.'}), 400

        username = (data.get('username') or '').strip()
        email = (data.get('email') or '').strip()
        password = data.get('password') or ''

        if not username or not email or not password:
            return jsonify({'success': False, 'message': '사용자명, 이메일, 비밀번호는 필수입니다.'}), 400

        if len(username) > 80 or len(email) > 120:
            return jsonify({'success': False, 'message': '입력 길이가 초과되었습니다.'}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': '이미 사용 중인 사용자명입니다.'}), 409

        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': '이미 사용 중인 이메일입니다.'}), 409

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()

        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        return jsonify({
            'success': True,
            'message': '회원가입이 완료되었습니다.',
            'data': {
                'user': user.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token,
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': '회원가입 처리 중 오류가 발생했습니다.'}), 500


@bp.route('/auth/login', methods=['POST'])
def login():
    """로그인"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '요청 데이터가 없습니다.'}), 400

        username = (data.get('username') or '').strip()
        password = data.get('password') or ''

        if not username or not password:
            return jsonify({'success': False, 'message': '사용자명과 비밀번호는 필수입니다.'}), 400

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({'success': False, 'message': '사용자명 또는 비밀번호가 올바르지 않습니다.'}), 401

        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        return jsonify({
            'success': True,
            'message': '로그인 성공',
            'data': {
                'user': user.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token,
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': '로그인 처리 중 오류가 발생했습니다.'}), 500


@bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """토큰 갱신"""
    try:
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=current_user_id)

        return jsonify({
            'success': True,
            'data': {'access_token': access_token}
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': '토큰 갱신 중 오류가 발생했습니다.'}), 500


@bp.route('/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """현재 사용자 정보 조회"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        if not user:
            return jsonify({'success': False, 'message': '사용자를 찾을 수 없습니다.'}), 404

        return jsonify({
            'success': True,
            'data': user.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': '사용자 정보 조회 중 오류가 발생했습니다.'}), 500
