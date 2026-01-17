# 파이프라인 (Batch)

뉴스 수집부터 뉴스레터 생성까지의 배치 파이프라인 로직을 포함한다.

## 핵심 태스크
- `fetch_articles`: RSS/신문사 어댑터로 기사 수집, URL 기준 upsert
- `clean_normalize`: 텍스트 정제, 언어 감지, 품질 체크
- `deduplicate`: URL 정규화 + 유사도 기반 근접 중복 제거
- `extract_keywords`: TF‑IDF + NER 하이브리드 키워드
- `assign_topics`: 임베딩 유사도 기반 토픽 할당/생성
- `generate_newsletters`: 토픽 기반 뉴스레터 생성 + 문장별 인용 저장
- `embed_newsletters`: 뉴스레터 임베딩 저장
- `update_popularity`: 토픽별 기사 수 집계

## 어댑터
- `adapters/rss.py`: 일반 RSS 수집
- `adapters/newspaper.py`: 신문사 RSS + CSS selector 본문 추출

## 아이덴포턴시
- 기사 URL 기준 upsert
- 토픽/뉴스레터는 content_hash로 재생성 방지
- 임베딩은 content_hash + dim 비교 후 재생성

## 설정
- `services/backend/config/sources.yaml`에서 소스 정의
- `NEWS_MAX_ITEMS_PER_SOURCE`, `TOPIC_SIMILARITY_THRESHOLD` 등으로 튜닝
