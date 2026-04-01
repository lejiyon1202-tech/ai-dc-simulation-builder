"""
프로젝트 관리 API
DC 시뮬레이션 프로젝트의 CRUD 기능
"""
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import bp
from app.models import Project, User
from app import db
import json

@bp.route('/projects', methods=['GET'])
@jwt_required()
def get_projects():
    """사용자의 프로젝트 목록 조회"""
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        
        query = Project.query.filter_by(user_id=current_user_id)
        
        # 상태 필터링
        if status:
            query = query.filter_by(status=status)
        
        # 페이지네이션
        projects = query.order_by(Project.updated_at.desc())\
                       .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': {
                'projects': [project.to_dict() for project in projects.items],
                'pagination': {
                    'page': projects.page,
                    'pages': projects.pages,
                    'per_page': projects.per_page,
                    'total': projects.total,
                    'has_next': projects.has_next,
                    'has_prev': projects.has_prev
                }
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'프로젝트 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/projects', methods=['POST'])
@jwt_required()
def create_project():
    """새 프로젝트 생성"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # 필수 필드 검증
        if not data or not data.get('name'):
            return jsonify({
                'success': False,
                'message': '프로젝트 이름은 필수입니다.'
            }), 400
        
        # 새 프로젝트 생성
        project = Project(
            name=data['name'],
            description=data.get('description', ''),
            user_id=current_user_id,
            evaluation_purpose=data.get('evaluation_purpose'),
            target_level=data.get('target_level'),
            industry=data.get('industry'),
            job_function=data.get('job_function'),
            competencies=json.dumps(data.get('competencies', [])) if data.get('competencies') else None
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '프로젝트가 성공적으로 생성되었습니다.',
            'data': project.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'프로젝트 생성 중 오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/projects/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    """특정 프로젝트 상세 조회"""
    try:
        current_user_id = get_jwt_identity()
        
        project = Project.query.filter_by(
            id=project_id, 
            user_id=current_user_id
        ).first()
        
        if not project:
            return jsonify({
                'success': False,
                'message': '프로젝트를 찾을 수 없습니다.'
            }), 404
        
        # 시뮬레이션 정보도 함께 조회
        project_data = project.to_dict()
        project_data['simulations'] = [sim.to_dict() for sim in project.simulations]
        
        return jsonify({
            'success': True,
            'data': project_data
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'프로젝트 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/projects/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    """프로젝트 정보 수정"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        project = Project.query.filter_by(
            id=project_id, 
            user_id=current_user_id
        ).first()
        
        if not project:
            return jsonify({
                'success': False,
                'message': '프로젝트를 찾을 수 없습니다.'
            }), 404
        
        # 프로젝트 정보 업데이트
        if 'name' in data:
            project.name = data['name']
        if 'description' in data:
            project.description = data['description']
        if 'evaluation_purpose' in data:
            project.evaluation_purpose = data['evaluation_purpose']
        if 'target_level' in data:
            project.target_level = data['target_level']
        if 'industry' in data:
            project.industry = data['industry']
        if 'job_function' in data:
            project.job_function = data['job_function']
        if 'competencies' in data:
            project.competencies = json.dumps(data['competencies'])
        if 'status' in data:
            project.status = data['status']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '프로젝트가 성공적으로 수정되었습니다.',
            'data': project.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'프로젝트 수정 중 오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/projects/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    """프로젝트 삭제"""
    try:
        current_user_id = get_jwt_identity()
        
        project = Project.query.filter_by(
            id=project_id, 
            user_id=current_user_id
        ).first()
        
        if not project:
            return jsonify({
                'success': False,
                'message': '프로젝트를 찾을 수 없습니다.'
            }), 404
        
        # 프로젝트 및 관련 시뮬레이션 삭제 (CASCADE로 처리됨)
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '프로젝트가 성공적으로 삭제되었습니다.'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'프로젝트 삭제 중 오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/projects/<int:project_id>/duplicate', methods=['POST'])
@jwt_required()
def duplicate_project(project_id):
    """프로젝트 복제"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        original_project = Project.query.filter_by(
            id=project_id, 
            user_id=current_user_id
        ).first()
        
        if not original_project:
            return jsonify({
                'success': False,
                'message': '복제할 프로젝트를 찾을 수 없습니다.'
            }), 404
        
        # 새 프로젝트 생성 (복제)
        new_name = data.get('name', f"{original_project.name} (복사본)")
        
        new_project = Project(
            name=new_name,
            description=original_project.description,
            user_id=current_user_id,
            evaluation_purpose=original_project.evaluation_purpose,
            target_level=original_project.target_level,
            industry=original_project.industry,
            job_function=original_project.job_function,
            competencies=original_project.competencies,
            status='draft'
        )
        
        db.session.add(new_project)
        db.session.flush()  # ID 생성을 위해 flush
        
        # 원본 프로젝트의 시뮬레이션도 복제
        for simulation in original_project.simulations:
            from app.models import Simulation
            new_simulation = Simulation(
                project_id=new_project.id,
                method_id=simulation.method_id,
                duration=simulation.duration,
                difficulty=simulation.difficulty,
                scenario_title=simulation.scenario_title,
                scenario_content=simulation.scenario_content,
                materials=simulation.materials,
                evaluation_criteria=simulation.evaluation_criteria,
                is_generated=simulation.is_generated,
                generation_status='pending' if simulation.is_generated else 'pending'
            )
            db.session.add(new_simulation)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '프로젝트가 성공적으로 복제되었습니다.',
            'data': new_project.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'프로젝트 복제 중 오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/projects/stats', methods=['GET'])
@jwt_required()
def get_project_stats():
    """사용자의 프로젝트 통계 조회"""
    try:
        current_user_id = get_jwt_identity()
        
        # 전체 프로젝트 수
        total_projects = Project.query.filter_by(user_id=current_user_id).count()
        
        # 상태별 프로젝트 수
        draft_count = Project.query.filter_by(user_id=current_user_id, status='draft').count()
        in_progress_count = Project.query.filter_by(user_id=current_user_id, status='in_progress').count()
        completed_count = Project.query.filter_by(user_id=current_user_id, status='completed').count()
        
        # 최근 프로젝트
        recent_projects = Project.query.filter_by(user_id=current_user_id)\
                                     .order_by(Project.updated_at.desc())\
                                     .limit(5).all()
        
        return jsonify({
            'success': True,
            'data': {
                'total_projects': total_projects,
                'status_counts': {
                    'draft': draft_count,
                    'in_progress': in_progress_count,
                    'completed': completed_count
                },
                'recent_projects': [project.to_dict() for project in recent_projects]
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'프로젝트 통계 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500