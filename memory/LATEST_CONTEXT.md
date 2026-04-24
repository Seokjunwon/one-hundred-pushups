# 100챌린지 - 최신 컨텍스트

> 마지막 업데이트: 2026-04-24

---

## 프로젝트 개요

매일 100개 푸시업 챌린지 웹앱. 미완료 평일 1일당 ₩10,000 벌금 시스템.

- **스택**: Flask + SQLAlchemy + PostgreSQL(Supabase) / 바닐라 JS SPA / PWA
- **배포**: Render.com (main 푸시 시 자동 배포)
- **관리자**: 원석준, 김병석 (하드코딩: `ADMIN_USERS`)
- **사이트**: https://one-hundred-pushups.onrender.com

---

## 파일 구조

| 파일 | 역할 |
|------|------|
| `app.py` | Flask 백엔드 (모든 API 엔드포인트, ~840줄) |
| `models.py` | SQLAlchemy 모델 7개 |
| `templates/index.html` | 단일 파일 프론트엔드 (HTML + CSS + JS, ~3100줄) |
| `requirements.txt` | Python 의존성 |
| `render.yaml` | Render 배포 설정 |
| `static/service-worker.js` | PWA 서비스 워커 (현재 캐시 **v15**) |
| `static/manifest.json` | PWA 매니페스트 (theme_color: #CA8A04) |
| `static/icons/` | PWA 아이콘 (72~512px, "100" 텍스트 + 딥퍼플 그라데이션 - 미교체) |
| `memory/` | 세션 메모리 시스템 |

---

## 디자인 테마

- **컨셉컬러**: 화이트톤 + 진한 머스터드 옐로우 (모던 미니멀)
- `--primary`: #CA8A04 (mustard)
- `--primary-dark`: #854D0E
- `--primary-light`: #FEF9C3
- `--primary-pale`: #FFFBEB
- `--primary-gradient`: linear-gradient(135deg, #854D0E → #CA8A04)
- `--dark-hero`: linear-gradient(135deg, #0F172A → #1E293B → #334155) (차콜; 벌금카드/이벤트히어로용)
- **폰트**: Pretendard Variable (CDN, trendy 한국어 타이포)
- **헤더**: 화이트 배경 + 하단 보더 + 옐로우 그라데이션 아이콘
- **카드**: 흰색 + 미세 보더 + 연한 옐로우 오버레이 (::before)
- **벌금 카드 / 이벤트 히어로 / 자산 총액 카드 / 공지바**: `var(--dark-hero)` 차콜 그라데이션
- **자산 카드**: 화이트 요약(평가금액 + 수익률 +X%(+원) + 총투자금/현금보유 메타)
- **한국식 등락 컬러**: 상승=빨강(#DC2626), 하락=파랑(#2563EB)
- **명예의전당 1위**: 골드 배경 + 별(✦) 트윙클 10개 + 폭죽 burst 3개 + "멋지다" 자동 표시
- **PWA 아이콘**: 현재도 딥퍼플 그라데이션(미교체). theme_color만 #CA8A04로 변경.

---

## DB 모델 (7개)

- **User**: id, name, created_at
- **PushupRecord**: id, user_id(FK), date, completed, created_at (unique: user_id+date)
- **StockHolding**: id, symbol, shares, avg_price, current_price, added_by(FK), created_at, updated_at
  - `current_price`: KR 주식 현재가 폴백용 (Yahoo API 실패 시). US는 미사용(항상 0).
- **CashAsset**: id, amount(KRW), updated_by(FK), updated_at (단일 행)
- **SiteConfig**: id, key(unique), value, updated_by(FK), updated_at (key-value 설정 저장)
- **Event**: id, title, target_date, is_active, created_by(FK), created_at
- **EventParticipant**: id, event_id(FK), user_id(FK), joined_at (unique: event_id+user_id)

---

## 주요 기능 & API

### 핵심 기능
- 로그인 (이름 입력) → `/api/login` (is_admin 포함)
- 캘린더 체크/해제 → `/api/calendar/<year>/<month>`, `/api/toggle`
- 벌금 랭킹 (명예의전당) → `/api/ranking` (단일 쿼리 최적화 완료)
- 월 선택 → `/api/available-months`

### D-Day 이벤트 (신규)
- 활성 이벤트 조회 → `GET /api/event?user_id=`
- 이벤트 참석 → `POST /api/event/join`
- 이벤트 참석 취소 → `POST /api/event/leave`
- 이벤트 생성 (관리자) → `POST /api/admin/event`
- 이벤트 삭제 (관리자) → `DELETE /api/admin/event/<id>`

### 그룹 자산 관리 (관리자 전용 편집)
- 전체 자산 조회 → `GET /api/assets` (실시간 주가 + KRW 환산)
- 주식 CRUD → `POST/PUT/DELETE /api/admin/stock`
- 현금 수정 → `PUT /api/admin/cash`
- 전체 저장 → `POST /api/admin/save-all`
- Finnhub API 키 관리 → `GET/PUT /api/admin/finnhub-key`, `POST /api/admin/finnhub-test`
- 주가 프록시 → `GET /api/stock-price/<symbol>`

### 회원 관리 (관리자)
- 회원 목록 → `GET /api/admin/users`
- 회원 삭제 → `DELETE /api/admin/user/<id>`

### 외부 API
- **Finnhub**: 미국 주식 실시간 시세 (Quote endpoint, 60초 인메모리 캐시). 영문 심볼.
- **Yahoo Finance** (`query1.finance.yahoo.com/v8/finance/chart`): 한국 주식 실시간 시세. 종목코드 6자리 + `.KS`(KOSPI) → `.KQ`(KOSDAQ) 순 시도. No API key. User-Agent 헤더 필요.
- **open.er-api.com**: USD/KRW 환율 (5분 인메모리 캐시, 실패 시 1350 폴백)
- API 키는 DB(SiteConfig)에 저장, 없으면 환경변수 폴백

### 종목 시장 구분
- `detect_market(symbol)`: 6자리 숫자 → `'KR'`, 영문 → `'US'`
- 프론트 관리자 폼: 나스닥/코스피/코스닥 select로 입력 힌트 동적 변경
- `/api/assets` 응답에 `market`, `currency`, `cost_krw`, `gain_krw`, `gain_percent` 추가; 전체는 `total_cost_krw`, `total_gain_krw`, `total_gain_percent` 추가

---

## UI 구성 (index.html 내 순서)

1. **헤더** - 딥퍼플 배경 + "100" 아이콘 + "100챌린지" 흰색 제목
2. **유저바** - 이름, 관리자 톱니바퀴(⚙), 로그아웃
3. **공지 바** (notice-bar) - D-Day + 이벤트 제목, 클릭 → 이벤트 상세
4. **월 선택** 드롭다운
5. **벌금 카드** (stats-card) - 이번달 벌금, 달성률 배지, 완료/미완료/총평일, 벌금계좌 복사
6. **오늘 체크 버튼** (todayAction) - 퍼플 그라데이션 아이콘
7. **캘린더 그리드** (calendar-card) - 퍼플 상단 악센트
8. **명예의전당** (ranking-card) - 퍼플 상단 악센트, 3명까지 표시 + 더보기/접기
9. **보유자산 카드** (asset-card) - 퍼플 상단 악센트, 총자산(KRW), 주식목록, 환율, 현금
10. **이벤트 상세 화면** (eventScreen) - D-Day 히어로 + 참석/취소 + 참석자 명단 + 홈으로 가기
11. **관리자 바텀시트** - API키, D-Day 이벤트, 주식, 현금, 회원 관리, 저장하기
12. **로그인 화면** (loginScreen)
13. **PWA 설치 배너**

---

## 최근 커밋 히스토리

```
ab1e2f0 Fix: 타임존 버그 수정 - date.today()를 KST 기준으로 변경
e1b8a07 UI: 명예의전당 1위 이름 뒤에 '멋지다' 자동 표시
9b5fe18 UI: 1위 효과 개선 - 별 반짝임 + 폭죽 이펙트로 교체
a910e0f UI: 명예의전당 1등 반짝이 효과 추가
76a2c6e UI: 카드 디자인 리뉴얼 - 퍼플 글로우 + 자산 총액 퍼플 통일
d74a709 UI: 컨셉컬러 통일 + 참석명단 컬러 오버플로 수정
ca4f8dc Feature: D-Day 이벤트 기능 추가 (공지바 + 참석 관리)
6137c88 UI: PWA 아이콘 리디자인 + 딥퍼플 컬러 테마 적용
```

---

## 주의사항

- **타임존**: 서버(Render)는 UTC, 사용자는 KST → `today_kst()` 헬퍼 사용 필수 (`date.today()` 사용 금지)
- `models.py`의 `avg_price` 컬럼 추가는 **취소됨** (절대 추가하지 말 것)
- 서비스 워커 캐시 변경 시 `CACHE_NAME`과 `STATIC_CACHE` **둘 다** 업데이트 필요 (현재 v14)
- `db.create_all()`은 새 테이블만 생성, 기존 테이블 컬럼 변경 불가
- 기존 사용자 영향 없도록 backward-compatible 개발 필수
- 벌금계좌: (카카오)7942-14-57728 김병석
- PWA 아이콘 재생성 시: Pillow 스크립트로 gradient + "100" 텍스트 렌더링
