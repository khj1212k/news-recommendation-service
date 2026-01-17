# 스크립트 모음

이 폴더는 운영/검증/배치 트리거용 유틸리티 스크립트를 제공한다.

## 주요 스크립트
- `trigger_dag.sh`: Airflow DAG 수동 실행
- `integration_test.sh`: 전체 E2E 스모크 테스트
- `check_rss_sources.py`: RSS 카탈로그 연결/응답 확인
- `init_db.sql`: DB 초기화 보조 스크립트

## 사용 예시
```bash
./scripts/trigger_dag.sh
./scripts/integration_test.sh
python scripts/check_rss_sources.py
```

## 운영 팁
- 스크립트 실행 전 Docker Compose 서비스가 실행 중이어야 한다.
- `integration_test.sh`는 백엔드 상태 확인과 간단 피드 요청까지 수행한다.
