from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from config import config
import os

# 확장 프로그램 초기화
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_name=None):
    """애플리케이션 팩토리"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 확장 프로그램 초기화
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # CORS 설정 - 환경별 origin 허용
    allowed_origins = app.config.get('CORS_ORIGINS', [
        'http://localhost:3000',
        'http://localhost',
        'http://localhost:80',
    ])
    CORS(app, origins=allowed_origins, supports_credentials=True)

    # 헬스체크 엔드포인트
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy'}), 200

    # 블루프린트 등록
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # 업로드 폴더 생성
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # 애플리케이션 컨텍스트 내에서 DB 테이블 생성 및 시드 데이터
    with app.app_context():
        db.create_all()
        # 마스터 데이터가 비어있으면 자동 시드
        from app.models import EvaluationPurpose
        if EvaluationPurpose.query.count() == 0:
            try:
                from seed_data import seed_all
                seed_all()
            except Exception as e:
                app.logger.warning(f'시드 데이터 삽입 실패 (무시됨): {e}')

    return app

from app import models