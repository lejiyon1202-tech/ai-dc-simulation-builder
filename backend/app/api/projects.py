"""
프로젝트 관리 API
프로젝트 CRUD, 시뮬레이션 연결
"""
import json
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import bp
from app.models import Project, Simulation
from app import db


@bp.route('/projects', methods=['GET'])
@jwt_required()
def list_projects():
    """현재 사용자의 프로젝트 목록 조회"""
    try:
        current_user_id = int(get_jwt_identity())
        projects = Project.query.filter_by(user_id=current_user_id)\
                                .order_by(Project.updated_at.desc()).all()

        return jsonify({
            'success': True,
            'data': [p.to_dict() for p in projects]
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': '프로젝트 조회 중 오류가 발생했습니다.'}), 500


@bp.route('/projects/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    """프로젝트 상세 조회"""
    try:
        current_user_id = int(get_jwt_identity())
        project = Project.query.filter_by(id=project_id, user_id=current_user_id).first()
        if not project:
            return jsonify({'success': False, 'message': '프로젝트를 찾을 수 없습니다.'}), 404

        data = project.to_dict()
        data['simulations'] = [s.to_dict() for s in project.simulations]

        return jsonify({'success': True, 'data': data}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': '프로젝트 조회 중 오류가 발생했습니다.'}), 500


@bp.route('/projects', methods=['POST'])
@jwt_required()
def create_project():
    """프로젝트 생성"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '요청 데이터가 없습니다.'}), 400

        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'success': False, 'message': '프로젝트명은 필수입니다.'}), 400

        competencies = data.get('competencies')
        if competencies and isinstance(competencies, list):
            competencies = json.dumps(competencies, ensure_ascii=False)

        project = Project(
            name=name,
            description=(data.get('description') or '').strip(),
            user_id=current_user_id,
            evaluation_purpose=data.get('evaluation_purpose'),
            target_level=data.get('target_level'),
            industry=data.get('industry'),
            job_function=data.get('job_function'),
            competencies=competencies,
        )
        db.session.add(project)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '프로젝트가 생성되었습니다.',
            'data': project.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': '프로젝트 생성 중 오류가 발생했습니다.'}), 500


@bp.route('/projects/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    """프로젝트 수정"""
    try:
        current_user_id = int(get_jwt_identity())
        project = Project.query.filter_by(id=project_id, user_id=current_user_id).first()
        if not project:
            return jsonify({'success': False, 'message': '프로젝트를 찾을 수 없습니다.'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '요청 데이터가 없습니다.'}), 400

        if 'name' in data:
            project.name = (data['name'] or '').strip()
        if 'description' in data:
            project.description = (data['description'] or '').strip()
        if 'status' in data:
            project.status = data['status']
        if 'evaluation_purpose' in data:
            project.evaluation_purpose = data['evaluation_purpose']
        if 'target_level' in data:
            project.target_level = data['target_level']
        if 'industry' in data:
            project.industry = data['industry']
        if 'job_function' in data:
            project.job_function = data['job_function']
        if 'competencies' in data:
            comps = data['competencies']
            project.competencies = json.dumps(comps, ensure_ascii=False) if isinstance(comps, list) else comps

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '프로젝트가 수정되었습니다.',
            'data': project.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': '프로젝트 수정 중 오류가 발생했습니다.'}), 500


@bp.route('/projects/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    """프로젝트 삭제"""
    try:
        current_user_id = int(get_jwt_identity())
        project = Project.query.filter_by(id=project_id, user_id=current_user_id).first()
        if not project:
            return jsonify({'success': False, 'message': '프로젝트를 찾을 수 없습니다.'}), 404

        db.session.delete(project)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '프로젝트가 삭제되었습니다.'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': '프로젝트 삭제 중 오류가 발생했습니다.'}), 500
