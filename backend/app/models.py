from datetime import datetime
from app import db
from flask_sqlalchemy import SQLAlchemy
import json

class User(db.Model):
    """사용자 모델"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    projects = db.relationship('Project', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Project(db.Model):
    """프로젝트 모델"""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), default='draft')  # draft, in_progress, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # JSON 필드로 선택 옵션 저장
    evaluation_purpose = db.Column(db.String(100))  # 평가목적
    target_level = db.Column(db.String(50))  # 대상직급
    industry = db.Column(db.String(100))  # 산업업종
    job_function = db.Column(db.String(100))  # 직무
    competencies = db.Column(db.Text)  # JSON 형태로 선택된 역량들 저장
    
    # 관계
    simulations = db.relationship('Simulation', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'status': self.status,
            'evaluation_purpose': self.evaluation_purpose,
            'target_level': self.target_level,
            'industry': self.industry,
            'job_function': self.job_function,
            'competencies': json.loads(self.competencies) if self.competencies else [],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class AssessmentMethod(db.Model):
    """평가 기법 마스터 데이터"""
    __tablename__ = 'assessment_methods'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # In-basket, Role-playing, etc.
    name_ko = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    default_duration = db.Column(db.Integer, default=60)  # 기본 시간(분)
    default_difficulty = db.Column(db.Integer, default=3)  # 1-5 난이도
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_ko': self.name_ko,
            'description': self.description,
            'default_duration': self.default_duration,
            'default_difficulty': self.default_difficulty,
            'is_active': self.is_active
        }

class Simulation(db.Model):
    """시뮬레이션 모델"""
    __tablename__ = 'simulations'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    method_id = db.Column(db.Integer, db.ForeignKey('assessment_methods.id'), nullable=False)
    
    # 설정 정보
    duration = db.Column(db.Integer, nullable=False)  # 시간(분)
    difficulty = db.Column(db.Integer, nullable=False)  # 1-5 난이도
    
    # 생성된 시나리오 내용
    scenario_title = db.Column(db.String(200))
    scenario_content = db.Column(db.Text)
    materials = db.Column(db.Text)  # JSON 형태로 자료 저장
    evaluation_criteria = db.Column(db.Text)  # JSON 형태로 평가 기준 저장
    
    # 생성 정보
    is_generated = db.Column(db.Boolean, default=False)
    generation_status = db.Column(db.String(50), default='pending')  # pending, generating, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    method = db.relationship('AssessmentMethod', backref='simulations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'method_id': self.method_id,
            'method': self.method.to_dict() if self.method else None,
            'duration': self.duration,
            'difficulty': self.difficulty,
            'scenario_title': self.scenario_title,
            'scenario_content': self.scenario_content,
            'materials': json.loads(self.materials) if self.materials else [],
            'evaluation_criteria': json.loads(self.evaluation_criteria) if self.evaluation_criteria else [],
            'is_generated': self.is_generated,
            'generation_status': self.generation_status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class EvaluationPurpose(db.Model):
    """평가목적 마스터 데이터"""
    __tablename__ = 'evaluation_purposes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    name_ko = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    order_index = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_ko': self.name_ko,
            'description': self.description,
            'is_active': self.is_active
        }

class TargetLevel(db.Model):
    """대상직급 마스터 데이터"""
    __tablename__ = 'target_levels'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    name_ko = db.Column(db.String(100), nullable=False)
    level_order = db.Column(db.Integer, default=0)  # 직급 순서
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_ko': self.name_ko,
            'level_order': self.level_order,
            'is_active': self.is_active
        }

class Industry(db.Model):
    """산업업종 마스터 데이터"""
    __tablename__ = 'industries'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    name_ko = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100))  # 대분류
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_ko': self.name_ko,
            'category': self.category,
            'description': self.description,
            'is_active': self.is_active
        }

class JobFunction(db.Model):
    """직무 마스터 데이터"""
    __tablename__ = 'job_functions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    name_ko = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100))  # 직무 대분류
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_ko': self.name_ko,
            'category': self.category,
            'description': self.description,
            'is_active': self.is_active
        }

class CompetencyCategory(db.Model):
    """역량 카테고리 모델"""
    __tablename__ = 'competency_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    name_ko = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#2563EB')  # 카테고리별 색상
    is_active = db.Column(db.Boolean, default=True)
    order_index = db.Column(db.Integer, default=0)
    
    # 관계
    competencies = db.relationship('Competency', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_ko': self.name_ko,
            'description': self.description,
            'color': self.color,
            'is_active': self.is_active,
            'competencies': [comp.to_dict() for comp in self.competencies if comp.is_active]
        }

class Competency(db.Model):
    """역량 모델"""
    __tablename__ = 'competencies'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('competency_categories.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    name_ko = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    behavioral_indicators = db.Column(db.Text)  # JSON 형태로 행동지표 저장
    is_active = db.Column(db.Boolean, default=True)
    order_index = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'name': self.name,
            'name_ko': self.name_ko,
            'description': self.description,
            'behavioral_indicators': json.loads(self.behavioral_indicators) if self.behavioral_indicators else [],
            'is_active': self.is_active
        }

class GenerationHistory(db.Model):
    """AI 생성 히스토리 모델"""
    __tablename__ = 'generation_history'
    
    id = db.Column(db.Integer, primary_key=True)
    simulation_id = db.Column(db.Integer, db.ForeignKey('simulations.id'), nullable=False)
    prompt_used = db.Column(db.Text)  # 사용된 프롬프트
    ai_response = db.Column(db.Text)  # AI 응답
    generation_time = db.Column(db.Float)  # 생성 소요 시간(초)
    tokens_used = db.Column(db.Integer)  # 사용된 토큰 수
    status = db.Column(db.String(50))  # success, failed, timeout
    error_message = db.Column(db.Text)  # 에러 발생 시 메시지
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'simulation_id': self.simulation_id,
            'generation_time': self.generation_time,
            'tokens_used': self.tokens_used,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat()
        }