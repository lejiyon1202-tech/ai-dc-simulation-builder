-- DC 시뮬레이션 빌더 초기 DB 설정
-- PostgreSQL 초기화 스크립트

-- 확장 프로그램 활성화
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 기본 스키마 확인 (테이블 생성은 Flask-SQLAlchemy가 담당)
SELECT 'Database initialized successfully' AS status;
