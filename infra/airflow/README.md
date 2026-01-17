# Airflow 배치

이 폴더는 Airflow 배치 실행 환경을 정의한다. 로컬 개발용 LocalExecutor 구성이며, DAG는 하루 4회 실행된다.

## 구성
- `Dockerfile`: Airflow 이미지 빌드 및 파이프라인 의존성 설치
- `dags/news_pipeline_daily_4x.py`: 파이프라인 DAG 정의

## 실행 방식
- Docker Compose에서 `airflow` 서비스로 실행
- `airflow standalone`을 사용해 Web UI + Scheduler + Worker를 단일 컨테이너에서 구동

## 환경 변수
- `AIRFLOW__CORE__EXECUTOR`: LocalExecutor
- `AIRFLOW__CORE__DEFAULT_TIMEZONE`: Asia/Seoul
- `DATABASE_URL`: 파이프라인이 사용하는 뉴스 DB 연결 문자열

## 운영 포인트
- 배치 태스크는 `services/backend/app/pipeline/cli.py`의 태스크를 호출
- 태스크별 로그는 `/opt/airflow/logs`에 저장
