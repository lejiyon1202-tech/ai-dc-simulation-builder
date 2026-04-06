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
    discussion_sessions = db.relationship('DiscussionSession', backref='user', lazy=True)
    
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

class DiscussionSession(db.Model):
    """Group Discussion 토론 세션 모델"""
    __tablename__ = 'discussion_sessions'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 토론 주제 정보
    topic_title = db.Column(db.String(300), nullable=False)
    topic_description = db.Column(db.Text)
    topic_type = db.Column(db.String(50), nullable=False)  # resource_allocation / policy_decision / crisis_response / priority_setting
    industry = db.Column(db.String(100))
    target_level = db.Column(db.String(50))
    difficulty = db.Column(db.Integer, default=3)  # 1-5 난이도

    # 참가자(사용자) 역할 정보
    participant_role = db.Column(db.String(200))
    participant_role_description = db.Column(db.Text)
    participant_materials = db.Column(db.Text)  # JSON 형태로 참가자 전용 자료 저장

    # AI 참가자 1 정보
    ai1_name = db.Column(db.String(100))
    ai1_role = db.Column(db.String(200))
    ai1_role_description = db.Column(db.Text)
    ai1_style = db.Column(db.String(50))  # analytical_assertive
    ai1_materials = db.Column(db.Text)  # JSON 형태로 AI 1 전용 자료 저장

    # AI 참가자 2 정보
    ai2_name = db.Column(db.String(100))
    ai2_role = db.Column(db.String(200))
    ai2_role_description = db.Column(db.Text)
    ai2_style = db.Column(db.String(50))  # collaborative_mediating
    ai2_materials = db.Column(db.Text)  # JSON 형태로 AI 2 전용 자료 저장

    # 공통 자료 및 역량
    common_materials = db.Column(db.Text)  # JSON 형태로 공통 자료 저장
    competencies = db.Column(db.Text)  # JSON 형태로 평가 대상 역량 목록 저장

    # 세션 상태 관리
    status = db.Column(db.String(50), default='preparing')  # preparing / briefing / intro / discussion / consensus / summary / evaluating / completed
    current_phase_end_time = db.Column(db.DateTime, nullable=True)
    total_duration = db.Column(db.Integer, default=30)  # 총 토론 시간(분)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    project = db.relationship('Project', backref='discussion_sessions')
    messages = db.relationship('DiscussionMessage', backref='session', lazy=True,
                               cascade='all, delete-orphan', order_by='DiscussionMessage.sequence_number')
    evaluation = db.relationship('SessionEvaluation', backref='session', uselist=False,
                                 cascade='all, delete-orphan')

    def to_dict(self, include_messages=False, include_evaluation=False):
        result = {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'topic_title': self.topic_title,
            'topic_description': self.topic_description,
            'topic_type': self.topic_type,
            'industry': self.industry,
            'target_level': self.target_level,
            'difficulty': self.difficulty,
            'participant_role': self.participant_role,
            'participant_role_description': self.participant_role_description,
            'participant_materials': json.loads(self.participant_materials) if self.participant_materials else None,
            'ai1_name': self.ai1_name,
            'ai1_role': self.ai1_role,
            'ai1_role_description': self.ai1_role_description,
            'ai1_style': self.ai1_style,
            'ai1_materials': json.loads(self.ai1_materials) if self.ai1_materials else None,
            'ai2_name': self.ai2_name,
            'ai2_role': self.ai2_role,
            'ai2_role_description': self.ai2_role_description,
            'ai2_style': self.ai2_style,
            'ai2_materials': json.loads(self.ai2_materials) if self.ai2_materials else None,
            'common_materials': json.loads(self.common_materials) if self.common_materials else None,
            'competencies': json.loads(self.competencies) if self.competencies else [],
            'status': self.status,
            'current_phase_end_time': self.current_phase_end_time.isoformat() if self.current_phase_end_time else None,
            'total_duration': self.total_duration,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        if include_messages:
            result['messages'] = [m.to_dict() for m in self.messages]
        if include_evaluation and self.evaluation:
            result['evaluation'] = self.evaluation.to_dict()
        return result


class DiscussionMessage(db.Model):
    """토론 메시지 모델"""
    __tablename__ = 'discussion_messages'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('discussion_sessions.id'), nullable=False)
    sender_type = db.Column(db.String(20), nullable=False)  # user / ai1 / ai2 / system
    sender_name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), default='statement')  # statement / question / rebuttal / agreement / summary / facilitation
    phase = db.Column(db.String(50))  # 메시지가 속한 토론 단계
    sequence_number = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'sender_type': self.sender_type,
            'sender_name': self.sender_name,
            'content': self.content,
            'message_type': self.message_type,
            'phase': self.phase,
            'sequence_number': self.sequence_number,
            'created_at': self.created_at.isoformat(),
        }


class SessionEvaluation(db.Model):
    """세션 평가 결과 모델"""
    __tablename__ = 'session_evaluations'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('discussion_sessions.id'), nullable=False, unique=True)
    overall_score = db.Column(db.Float)  # 종합 점수
    competency_scores = db.Column(db.Text)  # JSON: {역량명: {score, weight, behavioral_examples: []}}
    strengths = db.Column(db.Text)  # JSON: [{competency, description, evidence}]
    development_areas = db.Column(db.Text)  # JSON: [{competency, description, evidence, suggestion}]
    detailed_feedback = db.Column(db.Text)  # 역량별 상세 피드백
    development_guide = db.Column(db.Text)  # JSON 형태로 개발 가이드 저장
    participation_stats = db.Column(db.Text)  # JSON: {total_messages, avg_length, phase_distribution, ...}
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'overall_score': self.overall_score,
            'competency_scores': json.loads(self.competency_scores) if self.competency_scores else {},
            'strengths': json.loads(self.strengths) if self.strengths else [],
            'development_areas': json.loads(self.development_areas) if self.development_areas else [],
            'detailed_feedback': self.detailed_feedback,
            'development_guide': json.loads(self.development_guide) if self.development_guide else None,
            'participation_stats': json.loads(self.participation_stats) if self.participation_stats else {},
            'created_at': self.created_at.isoformat(),
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