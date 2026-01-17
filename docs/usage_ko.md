# 서비스 사용 방법 (로컬 실행)

## 1) 사전 준비
- Docker Desktop 또는 Docker Engine + Docker Compose
- (선택) 로컬 포트 충돌 시 `.env`에서 포트 변경

## 2) 환경 변수 설정
```bash
cp .env.example .env
```
- 실제 LLM 사용을 위해 `.env`에 `OPENAI_API_KEY`를 설정하세요.
- 기본 뉴스 소스는 `services/backend/config/sources.yaml`에 정의됩니다.
- 포트 변경 예시:
  - `POSTGRES_PORT=5433`
  - `BACKEND_PORT=8001`
  - `FRONTEND_PORT=3001`
  - `AIRFLOW_PORT=8081`

## 3) 서비스 실행
```bash
docker compose up --build
```
- 기본 포트
  - Backend: `http://localhost:8000`
  - Frontend: `http://localhost:3000`
  - Airflow UI: `http://localhost:8080`
- Airflow 기본 계정: `admin` / `admin`

## 3-1) 뉴스 소스 변경 (선택)
- `services/backend/config/sources.yaml`에서 RSS 목록을 수정하세요.
- `allow_fulltext`, `allow_derivatives`가 `true`인 소스만 수집됩니다.
- `license_required_patterns`는 HTML 내 라이선스 표식을 확인하기 위한 문자열 목록입니다.

## 4) 배치 파이프라인 실행
```bash
./scripts/trigger_dag.sh
# 또는
# docker compose exec airflow airflow dags trigger news_pipeline_daily_4x
```
- 성공 시 정책브리핑(RSS) 기사 기반으로 토픽/뉴스레터/임베딩이 생성됩니다.
- 동일 DAG 재실행은 **idempotent**하게 동작하도록 설계되어 있습니다.

## 5) 웹에서 사용하기
1. `http://localhost:3000` 접속
2. 회원가입 → 온보딩(카테고리/키워드 선택)
3. 개인화 피드 확인
4. 인기 페이지에서 카테고리별 인기 토픽 확인
5. 뉴스레터 상세에서 출처/피드백 확인

## 6) API로 사용하기
### 회원가입
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"strongpassword"}'
```

### 로그인
```bash
curl -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"strongpassword"}'
```

### 개인화 피드
```bash
curl -H "Authorization: Bearer ${TOKEN}" http://localhost:8000/feed
```

### 인기 토픽
```bash
curl http://localhost:8000/topics/popular?category=경제
```

### 뉴스레터 상세
```bash
curl http://localhost:8000/newsletter/{newsletter_id}
```

### 이벤트 로깅
```bash
curl -X POST http://localhost:8000/events \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{"event_type":"click","newsletter_id":"...","topic_id":"...","value":1.0,"context":{"page":"feed"}}'
```

### 온보딩 선호 조회/저장
```bash
curl -H "Authorization: Bearer ${TOKEN}" http://localhost:8000/me/preferences

curl -X POST http://localhost:8000/me/preferences \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{"categories":["경제","사회"],"keywords":["AI","반도체"]}'
```

## 7) 통합 테스트
```bash
./scripts/integration_test.sh
```
- Docker Compose 실행 → DAG 트리거 → 회원가입/피드 조회까지 자동 수행합니다.

## 8) Phase 2 학습/평가
```bash
PYTHONPATH=services/backend \
DATABASE_URL=postgresql+psycopg2://news:news_password@localhost:5432/news \
RANKER_MODEL_PATH=ml/artifacts/ranker.pkl \
python ml/training/train_phase2.py

PYTHONPATH=services/backend \
DATABASE_URL=postgresql+psycopg2://news:news_password@localhost:5432/news \
RANKER_MODEL_PATH=ml/artifacts/ranker.pkl \
python ml/evaluation/evaluate_offline.py
```

## 9) 문제 해결
- 포트 충돌: `.env`에서 포트 변경 후 재시작
- 데이터 초기화: `docker compose down -v` (DB 볼륨 삭제)
- 임베딩 차원 변경 후 오류: 기존 DB 볼륨 삭제 또는 마이그레이션 적용
- Airflow 로그 확인: `docker compose exec airflow ls -la /opt/airflow/logs`
