# Backend 테스트

## 구성
- `test_auth.py`: 인증/토큰 발급
- `test_event_logging.py`: 이벤트 저장
- `test_keyword_extraction.py`: 키워드 추출
- `test_newspaper_adapter.py`: 신문사 어댑터
- `test_rec_features.py`: 추천 피처
- `test_topic_assignment.py`: 토픽 임계치

## 실행
```bash
PYTHONPATH=/app pytest -q /app/tests
```

## 주의사항
- DB 의존 테스트는 Docker 환경에서 실행 권장
- 일부 테스트는 외부 네트워크 없이도 동작하도록 모킹 사용
