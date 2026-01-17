# Frontend (Next.js)

뉴스 추천 서비스를 사용자에게 보여주는 UI 레이어다.

## 주요 페이지
- `/signup`, `/login`: 인증
- `/onboarding`: 카테고리/키워드 선호 설정
- `/`: 개인화 피드
- `/popular`: 카테고리별 인기 토픽
- `/newsletter/[id]`: 뉴스레터 상세 + 출처

## 구성
- `app/`: Next.js App Router
- `components/`: 카드/피드백 UI
- `app/lib/api.ts`: API 호출
- `app/lib/storage.ts`: 토큰 저장

## 환경 변수
- `NEXT_PUBLIC_API_BASE_URL`: 백엔드 API 주소

## 실행
```bash
npm install
npm run dev
```

## 이벤트 로깅
- 카드 노출, 클릭, 저장, 숨김 등은 `/events` API로 전송
- `rank_position`을 포함해 랭킹 학습 데이터로 활용
