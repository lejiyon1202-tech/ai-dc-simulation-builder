import os
from datetime import timedelta
from dotenv import load_dotenv

# .env를 프로젝트 루트(backend/ 상위)와 backend/ 양쪽에서 탐색
_backend_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_backend_dir)

# 프로젝트 루트의 .env 우선, 없으면 backend/.env
for _env_path in [
    os.path.join(_project_root, '.env'),
    os.path.join(_backend_dir, '.env'),
]:
    if os.path.exists(_env_path):
        load_dotenv(_env_path)
        break
else:
    load_dotenv()  # 기본 탐색 폴백

class Config:
    """기본 설정"""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Anthropic Claude API 설정
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514')
    
    # 파일 업로드 설정
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Redis 설정 (사용 시 환경변수 필수)
    REDIS_URL = os.environ.get('REDIS_URL')

    # Celery 설정 (사용 시 환경변수 필수)
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')

class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or os.urandom(32).hex()
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///dc_simulator_dev.db'
    CORS_ORIGINS = ['http://localhost:5000', 'http://localhost:3000', 'http://localhost']

class ProductionConfig(Config):
    """운영 환경 설정"""
    DEBUG = False

    @staticmethod
    def init_app(app):
        """프로덕션 필수 환경변수 검증"""
        required = ['SECRET_KEY', 'JWT_SECRET_KEY', 'DATABASE_URL']
        missing = [k for k in required if not os.environ.get(k)]
        if missing:
            raise RuntimeError(f'프로덕션 필수 환경변수 미설정: {", ".join(missing)}')

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '')
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else []

class TestingConfig(Config):
    """테스트 환경 설정"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}