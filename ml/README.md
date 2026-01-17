# ML / RecSys

이 폴더는 추천 모델 학습/평가 스크립트를 포함한다. API 서버는 기본적으로 Phase 1을 사용하며, Phase 2 모델은 오프라인 학습 후 적용된다.

## 구성
- `training/train_phase2.py`: 이벤트 로그로 랭커 학습
- `evaluation/evaluate_offline.py`: Recall/NDCG/MAP 등 오프라인 평가

## 학습 파이프라인(Phase 2)
- 라벨 생성: click/save/follow = positive, impression/hide = negative
- 시간 분할: 과거 80% train, 최근 20% test
- 모델: `HistGradientBoostingClassifier`
- 피처: 유사도, 최신성, 인기, 토픽/카테고리 클릭 수, 키워드 오버랩 등
- 사용자 임베딩: 최근 이벤트 가중 평균(감쇠)

## 실행 방법
```bash
PYTHONPATH=services/backend \
DATABASE_URL=postgresql+psycopg2://news:news_password@localhost:5432/news \
RANKER_MODEL_PATH=ml/artifacts/ranker.pkl \
RANKER_META_PATH=ml/artifacts/ranker_meta.json \
python ml/training/train_phase2.py

PYTHONPATH=services/backend \
DATABASE_URL=postgresql+psycopg2://news:news_password@localhost:5432/news \
python ml/evaluation/evaluate_offline.py
```

## 결과물
- `ml/artifacts/ranker.pkl`: 학습 모델
- `ml/artifacts/ranker_meta.json`: 피처 메타데이터

## 운영 팁
- `USER_EMBEDDING_DECAY_HOURS`로 사용자 임베딩의 최근성 반영 강도 조절
- 모델 업데이트 후 API 서버 재시작 권장
