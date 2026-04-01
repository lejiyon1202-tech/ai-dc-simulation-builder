from flask import Flask
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
    
    # CORS 설정
    CORS(app, origins=['http://localhost:3000'])
    
    # 블루프린트 등록
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # 업로드 폴더 생성
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    return app

from app import models