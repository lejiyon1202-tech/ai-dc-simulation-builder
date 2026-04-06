"""
마스터 데이터 시드 스크립트
평가목적, 직급, 산업, 직무, 역량, 평가기법 초기 데이터
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import (
    EvaluationPurpose, TargetLevel, Industry, JobFunction,
    CompetencyCategory, Competency, AssessmentMethod
)


def seed_evaluation_purposes():
    purposes = [
        ('promotion', '승진심사', '직급 승진을 위한 역량 평가', 1),
        ('recruitment', '채용선발', '신규 채용 후보자 역량 평가', 2),
        ('leadership_dev', '리더십개발', '리더십 역량 진단 및 개발 계획 수립', 3),
        ('competency_assessment', '역량진단', '현재 역량 수준 진단 및 피드백', 4),
        ('training', '교육훈련', '교육 프로그램 연계를 위한 역량 평가', 5),
        ('job_transfer', '직무전환', '직무 전환 적합성 평가', 6),
        ('high_performer', '고성과자선발', '고성과자 선발 및 육성을 위한 평가', 7),
        ('talent_pool', '핵심인재풀', '핵심인재풀 구성을 위한 평가', 8),
    ]
    for name, name_ko, desc, order in purposes:
        if not EvaluationPurpose.query.filter_by(name=name).first():
            db.session.add(EvaluationPurpose(
                name=name, name_ko=name_ko, description=desc,
                is_active=True, order_index=order
            ))


def seed_target_levels():
    levels = [
        ('c_level', 'C-Level', 1),
        ('executive', '임원', 2),
        ('general_manager', '부장', 3),
        ('deputy_gm', '차장', 4),
        ('manager', '과장', 5),
        ('assistant_manager', '대리', 6),
        ('staff', '사원', 7),
        ('new_hire', '신입', 8),
        ('intern', '인턴', 9),
    ]
    for name, name_ko, order in levels:
        if not TargetLevel.query.filter_by(name=name).first():
            db.session.add(TargetLevel(
                name=name, name_ko=name_ko,
                level_order=order, is_active=True
            ))


def seed_industries():
    industries = [
        # 제조업
        ('manufacturing_auto', '자동차/부품', '제조업', '자동차 및 자동차 부품 제조'),
        ('manufacturing_electronics', '전자/반도체', '제조업', '전자제품 및 반도체 제조'),
        ('manufacturing_chemical', '화학/소재', '제조업', '화학 제품 및 신소재'),
        ('manufacturing_food', '식품/음료', '제조업', '식품 및 음료 제조'),
        ('manufacturing_pharma', '제약/바이오', '제조업', '제약 및 바이오 산업'),
        ('manufacturing_machinery', '기계/장비', '제조업', '산업용 기계 및 장비 제조'),
        # IT/소프트웨어
        ('it_software', 'IT/소프트웨어', 'IT/소프트웨어', '소프트웨어 개발 및 IT 서비스'),
        ('it_platform', '플랫폼/인터넷', 'IT/소프트웨어', '인터넷 플랫폼 서비스'),
        ('it_ai', 'AI/빅데이터', 'IT/소프트웨어', '인공지능 및 빅데이터'),
        ('it_game', '게임', 'IT/소프트웨어', '게임 개발 및 퍼블리싱'),
        ('it_security', '정보보안', 'IT/소프트웨어', '사이버 보안 및 정보보호'),
        # 금융
        ('finance_bank', '은행', '금융', '시중은행 및 특수은행'),
        ('finance_securities', '증권/자산운용', '금융', '증권사 및 자산운용'),
        ('finance_insurance', '보험', '금융', '생명보험 및 손해보험'),
        ('finance_fintech', '핀테크', '금융', '금융 기술 서비스'),
        # 서비스
        ('service_consulting', '컨설팅', '서비스', '경영 컨설팅'),
        ('service_logistics', '물류/유통', '서비스', '물류 및 유통 서비스'),
        ('service_retail', '리테일/유통', '서비스', '소매 유통'),
        ('service_hospitality', '호텔/관광', '서비스', '호텔 및 관광 서비스'),
        ('service_media', '미디어/엔터', '서비스', '미디어 및 엔터테인먼트'),
        # 건설/에너지
        ('construction', '건설/건축', '건설/에너지', '건설 및 건축'),
        ('energy', '에너지/전력', '건설/에너지', '에너지 및 전력'),
        # 공공/교육/의료
        ('public_sector', '공공기관', '공공/교육/의료', '정부 및 공공기관'),
        ('education', '교육', '공공/교육/의료', '교육 기관 및 에듀테크'),
        ('healthcare', '의료/헬스케어', '공공/교육/의료', '병원 및 헬스케어'),
        # 기타
        ('telecom', '통신', '기타', '통신 및 네트워크'),
        ('aerospace', '항공/우주', '기타', '항공 및 우주'),
        ('fashion', '패션/뷰티', '기타', '패션 및 뷰티'),
        ('agriculture', '농업/식품가공', '기타', '농업 및 식품 가공'),
        ('ngo', 'NGO/비영리', '기타', '비영리 단체'),
    ]
    for name, name_ko, category, desc in industries:
        if not Industry.query.filter_by(name=name).first():
            db.session.add(Industry(
                name=name, name_ko=name_ko,
                category=category, description=desc, is_active=True
            ))


def seed_job_functions():
    functions = [
        # 경영
        ('strategic_planning', '경영기획', '경영', '경영 전략 수립 및 사업 계획'),
        ('general_management', '총괄경영', '경영', '사업부/법인 총괄 경영'),
        ('new_business', '신사업개발', '경영', '신규 사업 발굴 및 추진'),
        ('investor_relations', 'IR/대외협력', '경영', '투자자 관계 및 대외 협력'),
        # 영업/마케팅
        ('sales', '영업', '영업/마케팅', 'B2B/B2C 영업 및 거래처 관리'),
        ('marketing', '마케팅', '영업/마케팅', '마케팅 전략 및 브랜드 관리'),
        ('product_management', '상품기획', '영업/마케팅', '상품/서비스 기획'),
        ('customer_service', '고객서비스', '영업/마케팅', '고객 응대 및 서비스 관리'),
        ('trade', '무역/수출', '영업/마케팅', '해외 무역 및 수출입'),
        # IT/개발
        ('software_dev', 'SW개발', 'IT/개발', '소프트웨어 설계 및 개발'),
        ('data_analytics', '데이터분석', 'IT/개발', '데이터 분석 및 인사이트 도출'),
        ('it_infra', 'IT인프라', 'IT/개발', 'IT 인프라 구축 및 운영'),
        ('project_management', '프로젝트관리', 'IT/개발', 'IT 프로젝트 관리'),
        # 지원
        ('hr', '인사', '지원', '채용, 평가, 보상, 교육'),
        ('finance_accounting', '재무/회계', '지원', '재무 관리 및 회계'),
        ('legal', '법무', '지원', '법률 자문 및 계약 관리'),
        ('general_affairs', '총무', '지원', '총무 및 시설 관리'),
        ('procurement', '구매/조달', '지원', '자재 구매 및 조달'),
        ('public_relations', '홍보', '지원', '기업 홍보 및 커뮤니케이션'),
        # 생산/품질
        ('production', '생산관리', '생산/품질', '생산 계획 및 공정 관리'),
        ('quality', '품질관리', '생산/품질', '품질 보증 및 관리'),
        ('rnd', '연구개발', '생산/품질', '기술 연구 및 제품 개발'),
        ('safety', '안전/환경', '생산/품질', '산업 안전 및 환경 관리'),
        ('scm', 'SCM/물류', '생산/품질', '공급망 관리 및 물류'),
        # 전문
        ('design', '디자인', '전문', 'UX/UI, 제품 디자인'),
        ('contents', '콘텐츠기획', '전문', '콘텐츠 기획 및 제작'),
        ('education_training', '교육/강의', '전문', '교육 프로그램 기획 및 강의'),
    ]
    for name, name_ko, category, desc in functions:
        if not JobFunction.query.filter_by(name=name).first():
            db.session.add(JobFunction(
                name=name, name_ko=name_ko,
                category=category, description=desc, is_active=True
            ))


def seed_competencies():
    categories_data = [
        {
            'name': 'leadership', 'name_ko': '리더십', 'color': '#2563EB',
            'description': '조직을 이끌고 성과를 창출하는 역량',
            'order': 1,
            'competencies': [
                ('vision', '비전제시', '조직의 미래 방향을 제시하고 구성원을 동기부여하는 역량'),
                ('motivation', '동기부여', '구성원의 잠재력을 이끌어내고 동기를 부여하는 역량'),
                ('teamwork', '팀워크', '팀원 간 협력을 촉진하고 시너지를 창출하는 역량'),
                ('conflict_mgmt', '갈등관리', '갈등 상황을 건설적으로 해결하는 역량'),
                ('change_mgmt', '변화주도', '변화를 이끌고 조직의 적응을 돕는 역량'),
                ('delegation', '위임/권한부여', '적절한 업무 위임과 권한 부여를 통해 성과를 달성하는 역량'),
                ('coaching', '코칭/육성', '구성원의 성장을 지원하고 역량을 개발시키는 역량'),
                ('influence', '영향력', '타인의 생각과 행동에 긍정적 영향을 미치는 역량'),
            ]
        },
        {
            'name': 'thinking', 'name_ko': '사고력', 'color': '#7C3AED',
            'description': '복잡한 문제를 분석하고 해결하는 역량',
            'order': 2,
            'competencies': [
                ('analysis', '분석적사고', '복잡한 정보를 체계적으로 분석하는 역량'),
                ('creativity', '창의적사고', '새로운 아이디어와 접근 방법을 도출하는 역량'),
                ('strategic', '전략적사고', '장기적 관점에서 전략을 수립하는 역량'),
                ('problem_solving', '문제해결', '문제의 본질을 파악하고 효과적으로 해결하는 역량'),
                ('decision_making', '의사결정', '주어진 정보를 바탕으로 합리적인 결정을 내리는 역량'),
                ('systemic', '종합적판단', '다양한 요소를 고려하여 종합적으로 판단하는 역량'),
                ('info_processing', '정보활용', '필요한 정보를 수집, 정리, 활용하는 역량'),
            ]
        },
        {
            'name': 'interpersonal', 'name_ko': '대인관계', 'color': '#059669',
            'description': '효과적인 의사소통과 관계 구축 역량',
            'order': 3,
            'competencies': [
                ('communication', '의사소통', '명확하고 효과적으로 소통하는 역량'),
                ('collaboration', '협업', '부서/직급을 넘어 효과적으로 협력하는 역량'),
                ('customer_focus', '고객지향', '고객의 니즈를 파악하고 만족시키는 역량'),
                ('persuasion', '설득/협상', '논리적으로 설득하고 합의를 도출하는 역량'),
                ('networking', '네트워킹', '전략적 관계를 구축하고 활용하는 역량'),
                ('empathy', '공감/경청', '상대방의 입장을 이해하고 공감하는 역량'),
                ('presentation', '프레젠테이션', '핵심 내용을 효과적으로 전달하는 역량'),
            ]
        },
        {
            'name': 'execution', 'name_ko': '실행력', 'color': '#DC2626',
            'description': '목표를 달성하기 위해 실행하는 역량',
            'order': 4,
            'competencies': [
                ('result_orientation', '성과지향', '목표를 설정하고 달성하기 위해 노력하는 역량'),
                ('responsibility', '책임감', '맡은 업무에 대해 끝까지 책임지는 역량'),
                ('drive', '추진력', '어려움 속에서도 목표를 향해 밀고 나가는 역량'),
                ('planning', '계획수립', '체계적인 실행 계획을 수립하는 역량'),
                ('time_mgmt', '시간관리', '업무 우선순위를 정하고 효율적으로 시간을 관리하는 역량'),
                ('risk_mgmt', '리스크관리', '잠재적 위험을 식별하고 대응하는 역량'),
                ('resource_mgmt', '자원관리', '인적/물적 자원을 효과적으로 배분하고 관리하는 역량'),
            ]
        },
        {
            'name': 'self_management', 'name_ko': '자기관리', 'color': '#EA580C',
            'description': '자기 자신을 관리하고 성장시키는 역량',
            'order': 5,
            'competencies': [
                ('self_development', '자기개발', '지속적으로 학습하고 성장하는 역량'),
                ('stress_mgmt', '스트레스관리', '압박 상황에서도 안정적으로 업무를 수행하는 역량'),
                ('adaptability', '적응력', '변화하는 환경에 유연하게 적응하는 역량'),
                ('learning_agility', '학습민첩성', '새로운 지식과 기술을 빠르게 습득하는 역량'),
                ('self_reflection', '성찰', '자신의 행동과 결과를 돌아보고 개선하는 역량'),
                ('integrity', '윤리/정직', '높은 윤리 기준을 유지하며 정직하게 행동하는 역량'),
            ]
        },
        {
            'name': 'global_digital', 'name_ko': '글로벌/디지털', 'color': '#0891B2',
            'description': '글로벌 환경과 디지털 기술 활용 역량',
            'order': 6,
            'competencies': [
                ('global_mindset', '글로벌마인드', '다문화 환경에서 효과적으로 활동하는 역량'),
                ('digital_literacy', '디지털역량', '디지털 기술을 이해하고 활용하는 역량'),
                ('innovation', '혁신', '기존 방식을 개선하고 새로운 가치를 창출하는 역량'),
                ('diversity', '다양성포용', '다양한 배경과 관점을 존중하고 포용하는 역량'),
                ('data_driven', '데이터기반사고', '데이터를 기반으로 의사결정하는 역량'),
            ]
        },
    ]

    for cat_data in categories_data:
        category = CompetencyCategory.query.filter_by(name=cat_data['name']).first()
        if not category:
            category = CompetencyCategory(
                name=cat_data['name'],
                name_ko=cat_data['name_ko'],
                description=cat_data['description'],
                color=cat_data['color'],
                is_active=True,
                order_index=cat_data['order']
            )
            db.session.add(category)
            db.session.flush()

        for idx, (comp_name, comp_name_ko, comp_desc) in enumerate(cat_data['competencies'], 1):
            if not Competency.query.filter_by(name=comp_name, category_id=category.id).first():
                db.session.add(Competency(
                    category_id=category.id,
                    name=comp_name,
                    name_ko=comp_name_ko,
                    description=comp_desc,
                    is_active=True,
                    order_index=idx
                ))


def seed_assessment_methods():
    methods = [
        ('in_basket', 'In-basket (서류함기법)',
         '제한된 시간 내에 다양한 서류(이메일, 보고서, 메모 등)를 처리하는 과제를 통해 의사결정, 우선순위 설정, 위임 능력 등을 평가합니다.',
         60, 3),
        ('role_playing', 'Role-playing (역할극)',
         '특정 역할을 부여받고 상대역과의 면담/대화를 통해 대인관계, 갈등관리, 설득력 등을 평가합니다.',
         30, 3),
        ('presentation', 'Presentation (발표)',
         '주어진 자료를 분석하여 발표하고 질의응답에 대응하는 과제를 통해 분석력, 전달력, 대응력 등을 평가합니다.',
         40, 3),
        ('group_discussion', 'Group Discussion (집단토론)',
         '여러 참가자가 주어진 주제에 대해 토론하여 합의를 도출하는 과제를 통해 리더십, 협업, 설득력 등을 평가합니다.',
         45, 3),
        ('gd_assigned_role', '집단토론 - 역할부여형',
         '참가자에게 특정 역할(부서/입장)을 부여하고 해당 관점에서 토론하여 합의를 도출하는 과제입니다.',
         45, 3),
        ('gd_free_discussion', '집단토론 - 자유토론형',
         '모든 참가자가 동일한 자료를 바탕으로 자유롭게 토론하여 결론을 도출하는 과제입니다.',
         45, 3),
        ('case_study', 'Case Study (사례분석)',
         '실제 기업 사례를 분석하고 문제 진단, 원인 분석, 해결방안을 도출하는 과제입니다.',
         60, 3),
    ]
    for name, name_ko, desc, duration, difficulty in methods:
        if not AssessmentMethod.query.filter_by(name=name).first():
            db.session.add(AssessmentMethod(
                name=name, name_ko=name_ko, description=desc,
                default_duration=duration, default_difficulty=difficulty,
                is_active=True
            ))


def seed_all():
    """모든 시드 데이터를 삽입합니다."""
    print("시드 데이터 삽입을 시작합니다...")

    seed_evaluation_purposes()
    print("  - 평가목적 완료")

    seed_target_levels()
    print("  - 대상직급 완료")

    seed_industries()
    print("  - 산업업종 완료")

    seed_job_functions()
    print("  - 직무 완료")

    seed_competencies()
    print("  - 역량 카테고리 및 역량 완료")

    seed_assessment_methods()
    print("  - 평가기법 완료")

    db.session.commit()
    print("모든 시드 데이터가 성공적으로 삽입되었습니다.")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        seed_all()
