"""
DC 시뮬레이션 빌더 - 통합 실행 서버
backend/ 앱 팩토리를 사용하여 단일 진입점으로 실행합니다.

사용법:
    python run.py
    → 브라우저에서 http://localhost:5000 접속
"""

import os
import sys
from dotenv import load_dotenv

# 프로젝트 루트의 .env를 먼저 로드 (config.py import 전에)
_root = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_root, '.env'))

# backend 패키지를 import 경로에 추가
backend_path = os.path.join(_root, 'backend')
sys.path.insert(0, backend_path)

from app import create_app, db
from flask import render_template, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def create_unified_app():
    """통합 앱 생성 — backend 팩토리 + 프론트엔드 템플릿 서빙"""
    app = create_app()

    # ─── Rate Limiting ───
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=['60 per minute'],
        storage_uri='memory://',
    )
    # AI 생성 엔드포인트 강화 제한
    limiter.limit('10 per minute')(app.view_functions.get('api.generate_single', lambda: None))
    limiter.limit('10 per minute')(app.view_functions.get('api.compat_generate', lambda: None))
    limiter.limit('5 per minute')(app.view_functions.get('api.evaluate_discussion_session', lambda: None))

    # 템플릿 폴더를 프로젝트 루트의 templates/로 설정
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    app.template_folder = template_dir

    # ─── 프론트엔드 페이지 서빙 ───
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/discussion')
    def discussion():
        return render_template('discussion.html')

    # ─── 헬스체크 (기존 호환) ───
    @app.route('/api/health')
    def api_health():
        return {'status': 'ok', 'service': 'dc-simulation-builder'}, 200

    return app


if __name__ == '__main__':
    print('\n' + '=' * 50)
    print('  DC Simulation Builder (통합 서버)')
    print('  http://localhost:5000 에서 접속하세요')
    print('=' * 50 + '\n')

    if not os.environ.get('ANTHROPIC_API_KEY'):
        print('  [WARNING] ANTHROPIC_API_KEY is not set.')
        print('  To use scenario generation, set the API key:')
        print('  export ANTHROPIC_API_KEY=sk-ant-...\n')

    app = create_unified_app()
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
