# 서비스 로직

비즈니스 로직 계층이다. 모델/DB 접근은 `models`와 `db`에 맡기고, 여기서는 추상화된 동작을 담당한다.

## 구성
- `embedding_service.py`: 문서/사용자 임베딩 생성
- `llm_service.py`: 뉴스레터 요약 생성 (LLM/Mock 지원)
- `recommendation.py`: 후보 검색 + 랭킹 + 다양성 제어
- `rec_features.py`: Phase 2 학습/랭킹용 피처 생성
- `keyword_extraction.py`: TF-IDF + 간단 NER 키워드 추출

## 추천 파이프라인 (요약)
1. 온보딩 선호 기반 사용자 임베딩
2. pgvector 유사도 검색으로 후보 추출
3. 랭커 모델 존재 시 확률 점수 사용, 없으면 휴리스틱 점수
4. MMR 리랭킹 + 카테고리/토픽 다양성 제한

## 운영 팁
- 랭커 변경 시 `RANKER_META_PATH`로 피처 호환성 체크
- `MMR_LAMBDA`로 다양성/정확도 균형 조절
