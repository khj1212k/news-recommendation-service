# 문서 모음

이 폴더는 프로젝트 설명과 실행 가이드를 모아둔 곳이다.

## 구성
- `overview_ko.md`: 전체 아키텍처/데이터 모델/추천 시스템 요약
- `usage_ko.md`: 로컬 실행, DAG 트리거, API 사용법
- `sources/`: 신문사 RSS 카탈로그 및 커버리지 참고 자료

## 권장 읽는 순서
1. `docs/overview_ko.md`
2. `docs/usage_ko.md`
3. `docs/sources/rss_sources_catalog.yaml`

## 실무 활용 팁
- 소스 추가는 `services/backend/config/sources.yaml`에 반영
- 파이프라인 변경 시 DAG(`infra/airflow/dags`)와 함께 문서 업데이트 권장
