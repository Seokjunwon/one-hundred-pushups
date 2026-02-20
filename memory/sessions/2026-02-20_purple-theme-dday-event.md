# 세션: 2026-02-20 딥퍼플 테마 + D-Day 이벤트

## 작업 내용

### 1. PWA 아이콘 리디자인
- 기존: 💪 이모지 + 파란색 배경
- 변경: "100" 텍스트 + 딥퍼플 그라데이션 (#4C1D95 → #7C3AED)
- Pillow 스크립트로 8개 사이즈 생성 (72~512px)
- 라운드 코너 22%, 미세 텍스트 쉐도우

### 2. 컨셉컬러 딥퍼플 전면 적용 (마켓컬리풍)
- CSS 변수: `--primary` #6366F1 → #5B21B6
- `--primary-dark`: #4F46E5 → #4C1D95
- `--primary-light`: #EEF2FF → #EDE9FE
- `--primary-gradient`: #6366F1/#8B5CF6 → #4C1D95/#7C3AED
- 헤더 아이콘: 단색 → rgba(255,255,255,0.15) 글래스
- 모든 box-shadow rgba 값 업데이트
- manifest.json theme_color: #3B82F6 → #4C1D95

### 3. 상단 헤더 리디자인
- 흰색 배경 → 딥퍼플 그라데이션 (#2E1065 → #4C1D95)
- h1, p 색상 → 흰색
- meta theme-color: #4C1D95

### 4. D-Day 이벤트 기능 (신규)
- **DB 모델**: Event(title, target_date, is_active), EventParticipant(event_id, user_id)
- **API**: GET /api/event, POST join/leave, POST admin/event, DELETE admin/event/<id>
- **공지 바**: 헤더-유저바 사이, 딥퍼플 바, D-day + 제목 표시
- **이벤트 상세 화면**: D-Day 히어로, 참석/취소 버튼, 참석자 명단, 홈으로 가기
- **관리자**: 바텀시트에 D-Day 섹션 (현재 이벤트 표시, 제목+날짜 입력, 등록/삭제)
- 새 이벤트 등록 시 기존 활성 이벤트 자동 비활성화

### 5. 컨셉컬러 통일 마무리
- 오늘의 푸시업 아이콘: 퍼플 그라데이션 배경 (#EDE9FE → #DDD6FE)
- 캘린더/명예의전당/보유자산 카드: 상단 3px 퍼플 악센트 + 제목색 퍼플
- 참석명단 .is-me: border-left → inset box-shadow (오버플로 수정)

## 커밋 이력
- `6137c88` UI: PWA 아이콘 리디자인 + 딥퍼플 컬러 테마 적용
- `ca4f8dc` Feature: D-Day 이벤트 기능 추가 (공지바 + 참석 관리)
- `37e0ab6` Fix: 서비스워커 캐시 v9
- `d74a709` UI: 컨셉컬러 통일 + 참석명단 컬러 오버플로 수정

## 서비스 워커
- 캐시 버전: v7 → v8 → v9 → v10

## import 변경
- app.py: `from models import ... Event, EventParticipant` 추가
