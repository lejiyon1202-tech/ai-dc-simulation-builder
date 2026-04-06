"""
선택 옵션 관리 API
평가목적, 대상직급, 산업업종, 직무, 역량 등의 마스터 데이터 관리
"""
from flask import jsonify, request
from app.api import bp
from app.models import (
    EvaluationPurpose, TargetLevel, Industry, JobFunction,
    CompetencyCategory, Competency, AssessmentMethod
)
from app import db

@bp.route('/options/evaluation-purposes', methods=['GET'])
def get_evaluation_purposes():
    """평가목적 옵션 조회"""
    try:
        purposes = EvaluationPurpose.query.filter_by(is_active=True)\
                                         .order_by(EvaluationPurpose.order_index).all()
        
        return jsonify({
            'success': True,
            'data': [purpose.to_dict() for purpose in purposes]
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '평가목적 조회 중 오류가 발생했습니다.'
        }), 500

@bp.route('/options/target-levels', methods=['GET'])
def get_target_levels():
    """대상직급 옵션 조회"""
    try:
        levels = TargetLevel.query.filter_by(is_active=True)\
                                 .order_by(TargetLevel.level_order).all()
        
        return jsonify({
            'success': True,
            'data': [level.to_dict() for level in levels]
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '대상직급 조회 중 오류가 발생했습니다.'
        }), 500

@bp.route('/options/industries', methods=['GET'])
def get_industries():
    """산업업종 옵션 조회"""
    try:
        industries = Industry.query.filter_by(is_active=True)\
                                  .order_by(Industry.category, Industry.name_ko).all()
        
        # 카테고리별로 그룹화
        grouped_industries = {}
        for industry in industries:
            category = industry.category or '기타'
            if category not in grouped_industries:
                grouped_industries[category] = []
            grouped_industries[category].append(industry.to_dict())
        
        return jsonify({
            'success': True,
            'data': grouped_industries
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '산업업종 조회 중 오류가 발생했습니다.'
        }), 500

@bp.route('/options/job-functions', methods=['GET'])
def get_job_functions():
    """직무 옵션 조회"""
    try:
        job_functions = JobFunction.query.filter_by(is_active=True)\
                                        .order_by(JobFunction.category, JobFunction.name_ko).all()
        
        # 카테고리별로 그룹화
        grouped_functions = {}
        for job_function in job_functions:
            category = job_function.category or '기타'
            if category not in grouped_functions:
                grouped_functions[category] = []
            grouped_functions[category].append(job_function.to_dict())
        
        return jsonify({
            'success': True,
            'data': grouped_functions
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '직무 조회 중 오류가 발생했습니다.'
        }), 500

@bp.route('/options/competencies', methods=['GET'])
def get_competencies():
    """역량 옵션 조회 (카테고리별)"""
    try:
        categories = CompetencyCategory.query.filter_by(is_active=True)\
                                           .order_by(CompetencyCategory.order_index).all()
        
        return jsonify({
            'success': True,
            'data': [category.to_dict() for category in categories]
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '역량 조회 중 오류가 발생했습니다.'
        }), 500

@bp.route('/options/assessment-methods', methods=['GET'])
def get_assessment_methods():
    """평가 기법 옵션 조회"""
    try:
        methods = AssessmentMethod.query.filter_by(is_active=True).all()
        
        return jsonify({
            'success': True,
            'data': [method.to_dict() for method in methods]
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '평가 기법 조회 중 오류가 발생했습니다.'
        }), 500

@bp.route('/options/all', methods=['GET'])
def get_all_options():
    """모든 선택 옵션을 한 번에 조회"""
    try:
        # 평가목적
        purposes = EvaluationPurpose.query.filter_by(is_active=True)\
                                         .order_by(EvaluationPurpose.order_index).all()
        
        # 대상직급
        levels = TargetLevel.query.filter_by(is_active=True)\
                                 .order_by(TargetLevel.level_order).all()
        
        # 산업업종 (카테고리별)
        industries = Industry.query.filter_by(is_active=True)\
                                  .order_by(Industry.category, Industry.name_ko).all()
        grouped_industries = {}
        for industry in industries:
            category = industry.category or '기타'
            if category not in grouped_industries:
                grouped_industries[category] = []
            grouped_industries[category].append(industry.to_dict())
        
        # 직무 (카테고리별)
        job_functions = JobFunction.query.filter_by(is_active=True)\
                                        .order_by(JobFunction.category, JobFunction.name_ko).all()
        grouped_functions = {}
        for job_function in job_functions:
            category = job_function.category or '기타'
            if category not in grouped_functions:
                grouped_functions[category] = []
            grouped_functions[category].append(job_function.to_dict())
        
        # 역량 (카테고리별)
        competency_categories = CompetencyCategory.query.filter_by(is_active=True)\
                                                      .order_by(CompetencyCategory.order_index).all()
        
        # 평가 기법
        methods = AssessmentMethod.query.filter_by(is_active=True).all()
        
        return jsonify({
            'success': True,
            'data': {
                'evaluation_purposes': [purpose.to_dict() for purpose in purposes],
                'target_levels': [level.to_dict() for level in levels],
                'industries': grouped_industries,
                'job_functions': grouped_functions,
                'competencies': [category.to_dict() for category in competency_categories],
                'assessment_methods': [method.to_dict() for method in methods]
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '옵션 조회 중 오류가 발생했습니다.'
        }), 500