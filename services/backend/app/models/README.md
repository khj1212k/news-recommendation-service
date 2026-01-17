# 모델(ORM)

이 폴더는 SQLAlchemy 모델 정의를 담는다. 모든 테이블은 Alembic 마이그레이션과 연결된다.

## 핵심 엔티티
- `sources`: 뉴스 소스 메타/약관/허용 여부
- `articles`: 원문, 정제문, 해시, 메타데이터
- `article_keywords`: 키워드 및 점수
- `topics`: 토픽/클러스터, 인기 지표, 센트로이드
- `topic_articles`: 토픽-기사 연결
- `newsletters`: 토픽 기반 뉴스레터
- `newsletter_citations`: 문장 단위 근거/출처
- `newsletter_embeddings`: 뉴스레터 임베딩

## 사용자/이벤트
- `users`: 사용자 계정
- `user_preferences`: 카테고리/키워드 선호
- `user_embeddings`: 사용자 임베딩
- `events`: 행동 로그

## 주의사항
- 임베딩 차원 변경 시 마이그레이션 필요
- `metadata_` 컬럼은 JSONB로 유연하게 확장 가능
