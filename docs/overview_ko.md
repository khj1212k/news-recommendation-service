# 한국어 뉴스 추천 서비스 개요

## 목표
- 한국어 뉴스 수집 → 정제/중복제거/키워드/토픽화 → 근거 기반 뉴스레터 생성 → 임베딩 저장 → 개인화 추천까지의 E2E 파이프라인 제공.
- 로컬에서 바로 실행 가능한 Docker Compose 기반 MVP이면서, 추후 확장(모델/소스/벡터DB 교체)에 유리한 모듈화 구조.

## 기술 스택
- Backend: FastAPI, SQLAlchemy, Alembic, Python 3.11
- Batch: Airflow 2.8 (LocalExecutor), 단일 DAG `news_pipeline_daily_4x`
- DB: PostgreSQL 15 + pgvector
- Frontend: Next.js 14 (App Router) + TypeScript + Tailwind
- ML/RecSys: scikit-learn 기반 Phase 2 학습/평가 파이프라인
- LLM/임베딩: OpenAI/Anthropic(설정 가능), sentence-transformers

## 아키텍처 요약
- **수집/배치**: Airflow DAG가 하루 4회(Asia/Seoul 기준) 실행되어 수집 → 정제 → 중복제거 → 키워드 → 토픽 할당/병합 → 뉴스레터 생성(근거 포함) → 임베딩 → 인기 업데이트까지 수행.
- **저장**: PostgreSQL + pgvector에 기사/토픽/뉴스레터/임베딩/이벤트/사용자 선호를 저장하며, 테이블 간 관계로 **계보(lineage)** 추적 가능.
- **API**: 인증/피드/인기 토픽/뉴스레터 상세/이벤트 로깅 제공.
- **UI**: 회원가입/로그인, 온보딩(카테고리/키워드), 개인화 피드, 인기 토픽, 뉴스레터 상세 페이지 제공.

## 배치 파이프라인 (Airflow DAG)
- DAG: `news_pipeline_daily_4x`
- 스케줄: `0 0,8,12,18 * * *` (Asia/Seoul)
- 태스크 순서
  1. `fetch_articles`: 소스 어댑터별 기사 수집 및 **upsert** (idempotent)
  2. `clean_normalize`: 텍스트 정제 + 언어 감지 + 품질 체크
  3. `deduplicate`: URL 정규화 + 근접중복 제거
  4. `extract_keywords`: TF‑IDF + 간단 NER 결합 키워드 추출
  5. `assign_topics`: 임베딩 유사도 기반 토픽 할당/생성 + 병합
  6. `generate_newsletters`: 근거 기반 뉴스레터 생성 + 문장별 인용 저장
  7. `embed_newsletters`: 콘텐츠 해시 기반 캐시/스킵
  8. `update_popularity`: 토픽별 원문 기사 수 카운트

## 데이터 모델 (핵심 테이블)
- `sources`: 수집 소스 메타(약관/파생 가능 여부 포함)
- `articles`: 원문, 정제문, 해시, 버전, 메타데이터
- `article_keywords`: 기사별 키워드/점수/방법
- `topics`: 토픽 제목/카테고리/인기도/센터 임베딩
- `topic_articles`: 토픽-기사 연결 및 점수
- `newsletters`: 토픽 기반 뉴스레터 본문/모델/해시/상태
- `newsletter_citations`: 뉴스레터 문장별 근거(기사 ID + 인용구 + 오프셋)
- `newsletter_embeddings`: 뉴스레터 임베딩
- `users`, `user_preferences`, `user_embeddings`, `events`: 인증/선호/행동 로그

## 추천 시스템
- **Phase 1 (구현)**
  - 온보딩 선호(카테고리/키워드) 기반 유저 임베딩 생성
  - pgvector로 유사도 상위 후보 검색
  - 점수 = 유사도 + 최신성 보너스 + 인기 보너스 - 중복 패널티
  - 카테고리/토픽 다양성 제한
  - MMR 리랭킹으로 유사 기사 과다 노출 방지
  - “왜 추천됐나요” 사유 반환
- **Phase 2 (실행 가능)**
  - Two‑tower retrieval + 경량 랭커(HistGradientBoostingClassifier)
  - 이벤트 기반 라벨링, 시간 분할 평가, Recall@K/NDCG@K/MAP@K 등 제공
  - 클릭 이벤트 가중 평균으로 사용자 임베딩 업데이트(최근성 반영)

## 프론트엔드 화면
- `/signup`, `/login`: 인증
- `/onboarding`: 카테고리/키워드 선택
- `/`: 개인화 피드(추천 사유 표시)
- `/popular`: 카테고리별 인기 토픽
- `/newsletter/[id]`: 뉴스레터 상세 + 출처/피드백 이벤트

## 법적/보안 정책
- 기본 수집 소스는 `korea.kr` 정책브리핑 RSS (KOGL Type-1 표시 여부를 HTML 패턴으로 확인)
- 약관에 따라 전체 본문/파생물 저장 여부를 소스 메타로 구분하며, 허용되지 않은 소스는 스킵
- 인증/JWT, 비밀번호 강력 해싱(bcrypt), 시크릿은 환경변수로 관리

## 관측/테스트
- 파이프라인 태스크별 메트릭 로그(`log_metrics`) 기록
- 유닛 테스트: 어댑터, 중복제거, 키워드, 토픽 기준, 캐시, 인증, 이벤트
- 통합 테스트: `scripts/integration_test.sh`

## 레포 구조
```
repo/
  docker-compose.yml
  .env.example
  README.md
  docs/
    overview_ko.md
    usage_ko.md
  infra/
    airflow/
      dags/
      Dockerfile
  services/
    backend/
      app/
      tests/
      alembic/
      Dockerfile
    frontend/
      app/
      components/
      Dockerfile
  ml/
    training/
    evaluation/
  scripts/
```

## 주요 환경 변수
- 서비스/포트: `POSTGRES_PORT`, `BACKEND_PORT`, `FRONTEND_PORT`, `AIRFLOW_PORT`
- 소스: `NEWS_SOURCES_FILE`, `NEWS_REQUEST_TIMEOUT`, `NEWS_MAX_ITEMS_PER_SOURCE`
- 파이프라인: `TOPIC_SIMILARITY_THRESHOLD`, `TOPIC_MERGE_THRESHOLD`, `DEDUP_NEAR_THRESHOLD`, `NEWSLETTER_MIN_BULLETS`, `NEWSLETTER_MAX_BULLETS`
- 모델/LLM: `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_DIM`, `LLM_PROVIDER`, `LLM_MODEL`, `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`, `MOCK_LLM`
- 추천: `RANKER_MODEL_PATH`, `RANKER_META_PATH`, `MMR_LAMBDA`, `MMR_MAX_CANDIDATES`, `USER_EMBEDDING_DECAY_HOURS`
- 타임존: `TIMEZONE` (기본 `Asia/Seoul`)
