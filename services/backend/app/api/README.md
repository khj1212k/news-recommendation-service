# API 라우터

## 엔드포인트 요약
- `POST /auth/signup`: 회원가입, 토큰 발급
- `POST /auth/login`: 로그인, 토큰 발급
- `GET /feed`: 개인화 피드
- `GET /topics/popular`: 인기 토픽
- `GET /newsletter/{id}`: 뉴스레터 상세 (출처/인용 포함)
- `POST /events`: 사용자 이벤트 로깅
- `GET/POST /me/preferences`: 온보딩 선호 조회/저장

## 인증 흐름
1. `/auth/signup` 또는 `/auth/login`
2. 응답의 `access_token`을 `Authorization: Bearer <token>`으로 사용

## 이벤트 로깅
- event_type: impression, click, dwell, hide, follow, save
- context: page, rank_position, session_id 등

## 응답 포맷
Pydantic 스키마는 `services/backend/app/schemas`에 정의되어 있다.
