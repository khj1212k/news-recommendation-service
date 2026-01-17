# Backend (FastAPI)

뉴스 수집 결과를 조회하고 개인화 추천을 제공하는 API 서버다. 인증, 피드, 뉴스레터 상세, 이벤트 로깅을 제공한다.

## 주요 기능
- JWT 기반 인증 (회원가입/로그인)
- 개인화 피드 `/feed`
- 인기 토픽 `/topics/popular`
- 뉴스레터 상세 `/newsletter/{id}` (출처/인용 포함)
- 이벤트 로깅 `/events`
- 온보딩 선호 `/me/preferences`

## 실행 방법
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 마이그레이션
```bash
alembic upgrade head
```

## 환경 변수
- `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`
- `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_DIM`
- `LLM_PROVIDER`, `LLM_MODEL`, `MOCK_LLM`
- `RANKER_MODEL_PATH`, `RANKER_META_PATH`, `MMR_LAMBDA`

## 디렉토리 요약
- `app/api`: FastAPI 라우터
- `app/models`: ORM 모델
- `app/services`: 추천/임베딩/LLM 로직
- `app/pipeline`: 배치 파이프라인 태스크
- `tests`: 유닛 테스트

## 개발/테스트
```bash
PYTHONPATH=/app pytest -q /app/tests
```
