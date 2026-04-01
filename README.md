# 🏢 AI Development Center 시뮬레이션 빌더

## 📋 프로젝트 개요

AI Development Center 시뮬레이션 빌더는 **DC(Development Center) 평가 시뮬레이션을 설계하고 제작하는 웹 애플리케이션**입니다. 다양한 평가 기법을 활용하여 조직의 인재 평가 및 개발을 위한 맞춤형 시뮬레이션을 생성할 수 있습니다.

### ✨ 주요 기능

- **4가지 평가 기법**: In-basket, Role-playing, Presentation, Group Discussion
- **8개 선택 카테고리**: 평가목적, 대상직급, 산업업종, 직무, 평가역량 등
- **AI 기반 시나리오 생성**: 선택 조합에 맞는 맞춤형 시나리오 자동 생성
- **문서 패키지 출력**: 완성된 시뮬레이션을 문서로 내보내기
- **직관적인 UI**: 클릭 기반의 간편한 선택 인터페이스

## 🛠 기술 스택

### Frontend
- **React 18**: 사용자 인터페이스
- **Styled Components**: 스타일링
- **Zustand**: 상태 관리
- **React Hook Form**: 폼 관리
- **Framer Motion**: 애니메이션
- **Lucide React**: 아이콘

### Backend
- **Python Flask**: 웹 프레임워크
- **SQLAlchemy**: ORM
- **OpenAI API**: AI 시나리오 생성
- **SQLite/PostgreSQL**: 데이터베이스
- **JWT**: 인증
- **Celery**: 비동기 작업 처리

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone https://github.com/your-org/ai-dc-simulation-builder.git
cd ai-dc-simulation-builder
```

### 2. 백엔드 설정
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
cd backend
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일을 편집하여 OpenAI API 키 등을 설정

# 데이터베이스 초기화
flask db init
flask db migrate
flask db upgrade

# 마스터 데이터 설정
python seed_data.py

# 서버 실행
flask run
```

### 3. 프론트엔드 설정
```bash
# 새 터미널에서
cd frontend
npm install
npm start
```

### 4. 접속
- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:5000

## 🎯 사용 가이드

### 1. 프로젝트 생성
1. 메인 화면에서 "새 프로젝트" 버튼 클릭
2. 프로젝트명과 설명 입력

### 2. 선택 단계별 가이드

#### 📌 평가 목적 선택
- **승진심사**: 상급자 역할 수행 능력 평가
- **채용선발**: 신규 채용자 적합성 평가
- **리더십개발**: 리더십 역량 개발 및 강화
- **역량진단**: 현재 역량 수준 진단
- **교육훈련**: 교육 프로그램 연계 평가
- **직무전환**: 새로운 직무 적응 능력 평가
- **고성과자선발**: 핵심 인재 선별
- **핵심인재풀**: 차세대 리더 육성 대상 선정

#### 👔 대상 직급 선택
- **C-Level**: 최고경영진 (CEO, CTO, CFO 등)
- **임원**: 이사급 이상
- **부장**: 부서장급
- **차장**: 중간관리자
- **과장**: 팀장급
- **대리**: 선임급
- **사원**: 일반직
- **신입**: 신규입사자
- **인턴**: 인턴십 과정

#### 🏭 산업 업종 (30개 업종)
제조업, 서비스업, IT/소프트웨어, 금융업, 건설업, 교육업, 의료업, 유통업, 미디어, 컨설팅 등 다양한 업종 지원

#### 💼 직무 분야 (27개 직무)
경영기획, 영업마케팅, IT개발, 인사, 재무회계, 법무, 구매, 생산관리, 품질관리, R&D 등

#### 🎯 평가 역량 (6개 카테고리, 54개 역량)

**리더십**: 비전제시, 동기부여, 팀워크, 갈등관리, 변화주도 등
**사고**: 분석적사고, 창의적사고, 전략적사고, 문제해결, 의사결정 등
**대인관계**: 의사소통, 협업, 고객지향, 설득력, 네트워킹 등
**실행**: 성과지향, 책임감, 추진력, 계획수립, 일정관리 등
**자기관리**: 자기개발, 스트레스관리, 적응력, 학습능력, 성찰 등
**글로벌디지털**: 글로벌마인드, 디지털역량, 혁신성, 다양성포용 등

### 3. 평가 기법별 설정

#### 📋 In-Basket (서류함 기법)
- **특징**: 실무 상황을 모방한 문서 처리 시뮬레이션
- **시간 설정**: 60-120분
- **난이도**: 1-5 단계
- **구성요소**: 메모, 보고서, 이메일, 회의자료 등

#### 🎭 Role-Playing (역할연기)
- **특징**: 특정 역할을 맡아 상호작용하는 시뮬레이션
- **시간 설정**: 30-90분
- **난이도**: 1-5 단계
- **구성요소**: 역할 설정, 갈등 상황, 목표와 제약조건

#### 📊 Presentation (발표)
- **특징**: 주어진 주제로 발표하는 시뮬레이션
- **시간 설정**: 20-60분
- **난이도**: 1-5 단계
- **구성요소**: 발표 주제, 청중 설정, 평가 기준

#### 👥 Group Discussion (집단토의)
- **특징**: 팀 단위 문제해결 토론 시뮬레이션
- **시간 설정**: 45-120분
- **난이도**: 1-5 단계
- **구성요소**: 토론 주제, 역할 분배, 결론 도출

### 4. AI 시나리오 생성
1. 모든 선택 완료 후 "시나리오 생성" 버튼 클릭
2. AI가 선택 조합에 맞는 맞춤형 시나리오 자동 생성
3. 생성된 시나리오 미리보기 및 편집 가능

### 5. 문서 패키지 내보내기
- **PDF 형태**: 완성된 시뮬레이션 문서
- **포함 내용**: 시나리오, 평가 기준, 진행 가이드, 평가 양식

## 📚 문서

- [📋 사용자 가이드](docs/USER_GUIDE.md)
- [🔧 API 문서](docs/API_DOCUMENTATION.md)
- [🏗 시스템 아키텍처](docs/SYSTEM_ARCHITECTURE.md)
- [💻 개발자 가이드](docs/DEVELOPER_GUIDE.md)
- [🎨 디자인 시스템](design-system.md)

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📞 문의

- 프로젝트 링크: [https://github.com/your-org/ai-dc-simulation-builder](https://github.com/your-org/ai-dc-simulation-builder)
- 이슈 리포트: [Issues](https://github.com/your-org/ai-dc-simulation-builder/issues)

---

Made with ❤️ by AI Development Center Team