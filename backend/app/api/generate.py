"""
시나리오 생성 API
AI를 사용하여 DC 시뮬레이션 시나리오를 생성하는 엔드포인트
"""

from flask import jsonify, request, send_file
from app.api import bp
from app.services.scenario_generator import get_generator
from app.services.export_service import export_to_markdown, export_package


@bp.route('/generate/single', methods=['POST'])
def generate_single():
    """단일 기법 시나리오 생성"""
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'message': '요청 데이터가 없습니다.'}), 400

    method = data.get('method')
    valid_methods = (
        'in_basket', 'role_playing', 'presentation',
        'group_discussion', 'gd_assigned_role', 'gd_free_discussion', 'case_study'
    )
    if method not in valid_methods:
        return jsonify({
            'success': False,
            'message': f'지원하지 않는 기법입니다: {method}. '
                       f'{", ".join(valid_methods)} 중 선택하세요.'
        }), 400

    params = {
        'evaluation_purpose': data.get('evaluation_purpose', '역량 진단'),
        'target_level': data.get('target_level', '과장'),
        'industry': data.get('industry', 'IT/소프트웨어'),
        'job_function': data.get('job_function', '경영기획'),
        'competencies': data.get('competencies', ['의사결정', '리더십', '커뮤니케이션']),
        'difficulty': data.get('difficulty', 3),
        'duration': data.get('duration', 30),
    }

    # 기법별 추가 파라미터
    if method == 'in_basket':
        params['doc_count'] = data.get('doc_count', 10)
    elif method == 'role_playing':
        params['rounds'] = data.get('rounds', 2)
    elif method == 'presentation':
        params['prep_time'] = data.get('prep_time')
        params['present_time'] = data.get('present_time')
    elif method in ('group_discussion', 'gd_assigned_role', 'gd_free_discussion'):
        params['participant_count'] = data.get('participant_count', 5)
        params['gd_type'] = data.get('gd_type', 'free')
    elif method == 'case_study':
        pass

    try:
        generator = get_generator()
        scenario = generator.generate(method, params)

        return jsonify({
            'success': True,
            'data': {
                'method': method,
                'scenario': scenario
            }
        }), 200

    except ValueError:
        return jsonify({'success': False, 'message': '요청 데이터가 올바르지 않습니다.'}), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '시나리오 생성 중 오류가 발생했습니다.'
        }), 500


@bp.route('/generate/all', methods=['POST'])
def generate_all():
    """선택된 모든 기법의 시나리오 일괄 생성"""
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'message': '요청 데이터가 없습니다.'}), 400

    params = {
        'evaluation_purpose': data.get('evaluation_purpose', '역량 진단'),
        'target_level': data.get('target_level', '과장'),
        'industry': data.get('industry', 'IT/소프트웨어'),
        'job_function': data.get('job_function', '경영기획'),
        'competencies': data.get('competencies', ['의사결정', '리더십', '커뮤니케이션']),
        'difficulty': data.get('difficulty', 3),
    }

    methods = data.get('methods', ['in_basket', 'role_playing', 'presentation', 'group_discussion'])

    # 기법별 시간/옵션
    method_settings = data.get('method_settings', {})
    for method in methods:
        settings = method_settings.get(method, {})
        if method == 'in_basket':
            params['doc_count'] = settings.get('doc_count', 10)
        elif method == 'role_playing':
            params['rounds'] = settings.get('rounds', 2)
        elif method in ('group_discussion', 'gd_assigned_role', 'gd_free_discussion'):
            params['participant_count'] = settings.get('participant_count', 5)
            params['gd_type'] = settings.get('gd_type', 'free')
        elif method == 'case_study':
            pass

    try:
        generator = get_generator()
        result = generator.generate_all(params, methods)

        return jsonify({
            'success': True,
            'data': result
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': '시나리오 생성 중 오류가 발생했습니다.'
        }), 500


@bp.route('/generate/regenerate-part', methods=['POST'])
def regenerate_part():
    """시나리오의 특정 부분만 재생성"""
    data = request.get_json()

    method = data.get('method')
    params = data.get('params', {})
    part = data.get('part')  # 예: "documents", "evaluation_criteria"
    current_scenario = data.get('current_scenario', {})

    if not method or not part or not current_scenario:
        return jsonify({
            'success': False,
            'message': 'method, part, current_scenario는 필수입니다.'
        }), 400

    try:
        generator = get_generator()
        updated = generator.regenerate_part(method, params, part, current_scenario)

        return jsonify({
            'success': True,
            'data': {'scenario': updated}
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': '재생성 중 오류가 발생했습니다.'
        }), 500


@bp.route('/generate/customize', methods=['POST'])
def customize_scenario():
    """사용자 지시에 따라 시나리오 수정"""
    data = request.get_json()

    method = data.get('method')
    current_scenario = data.get('current_scenario', {})
    instruction = data.get('instruction', '')

    if not method or not current_scenario or not instruction:
        return jsonify({
            'success': False,
            'message': 'method, current_scenario, instruction은 필수입니다.'
        }), 400

    try:
        generator = get_generator()
        updated = generator.customize_scenario(method, current_scenario, instruction)

        return jsonify({
            'success': True,
            'data': {'scenario': updated}
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': '수정 중 오류가 발생했습니다.'
        }), 500


@bp.route('/export/markdown', methods=['POST'])
def export_markdown():
    """시나리오를 마크다운으로 내보내기"""
    data = request.get_json()

    method = data.get('method')
    scenario = data.get('scenario', {})

    if not method or not scenario:
        return jsonify({
            'success': False,
            'message': 'method와 scenario는 필수입니다.'
        }), 400

    try:
        md_content = export_to_markdown(scenario, method)
        return jsonify({
            'success': True,
            'data': {'markdown': md_content}
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': '내보내기 중 오류가 발생했습니다.'
        }), 500


@bp.route('/export/package', methods=['POST'])
def export_zip_package():
    """전체 시나리오를 ZIP 패키지로 내보내기"""
    data = request.get_json()

    project_name = data.get('project_name', 'DC_시뮬레이션')
    scenarios = data.get('scenarios', {})

    if not scenarios:
        return jsonify({
            'success': False,
            'message': '내보낼 시나리오가 없습니다.'
        }), 400

    try:
        zip_buffer = export_package(project_name, scenarios)

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'{project_name}.zip'
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'message': '패키지 생성 중 오류가 발생했습니다.'
        }), 500
