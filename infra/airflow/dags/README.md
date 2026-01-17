# DAG 안내

## DAG: news_pipeline_daily_4x
- 스케줄: `0 0,8,12,18 * * *` (Asia/Seoul)
- 목적: 기사 수집 → 정제/중복 제거 → 키워드 → 토픽 할당 → 뉴스레터 생성 → 임베딩 → 인기 업데이트

## 태스크 순서
1. `fetch_articles`
2. `clean_normalize`
3. `deduplicate`
4. `extract_keywords`
5. `assign_topics`
6. `generate_newsletters`
7. `embed_newsletters`
8. `update_popularity`

## 실행 방식
각 태스크는 `services/backend/app/pipeline/cli.py`의 커맨드를 실행한다.
