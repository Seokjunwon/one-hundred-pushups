# 100챌린지 - 최신 컨텍스트

> 마지막 업데이트: 2026-02-15

---

## 프로젝트 개요

매일 100개 푸시업 챌린지 웹앱. 미완료 평일 1일당 ₩10,000 벌금 시스템.

- **스택**: Flask + SQLAlchemy + PostgreSQL(Supabase) / 바닐라 JS SPA / PWA
- **배포**: Render.com (main 푸시 시 자동 배포)
- **관리자**: 원석준, 김병석 (하드코딩: `ADMIN_USERS`)

---

## 파일 구조

| 파일 | 역할 |
|------|------|
| `app.py` | Flask 백엔드 (모든 API 엔드포인트) |
| `models.py` | SQLAlchemy 모델 (User, PushupRecord, StockHolding, CashAsset, SiteConfig) |
| `templates/index.html` | 단일 파일 프론트엔드 (HTML + CSS + JS 전부 포함) |
| `requirements.txt` | Python 의존성 |
| `render.yaml` | Render 배포 설정 |
| `static/service-worker.js` | PWA 서비스 워커 (현재 캐시 v6) |
| `static/manifest.json` | PWA 매니페스트 |
| `.env.example` | 환경변수 예시 |

---

## DB 모델

- **User**: id, name, created_at
- **PushupRecord**: id, user_id(FK), date, completed, created_at
- **StockHolding**: id, symbol, shares, added_by(FK), created_at, updated_at
- **CashAsset**: id, amount(KRW), updated_by(FK), updated_at (단일 행)
- **SiteConfig**: id, key(unique), value, updated_by(FK), updated_at (key-value 설정 저장)

---

## 주요 기능 & API

### 핵심 기능
- 로그인 (이름 입력) → `/api/login` (is_admin 포함)
- 캘린더 체크/해제 → `/api/calendar/<year>/<month>`, `/api/toggle`
- 벌금 랭킹 (명예의전당) → `/api/ranking` (단일 쿼리 최적화 완료)
- 월 선택 → `/api/available-months`

### 그룹 자산 관리 (관리자 전용 편집)
- 전체 자산 조회 → `GET /api/assets` (실시간 주가 + KRW 환산)
- 주식 CRUD → `POST/PUT/DELETE /api/admin/stock`
- 현금 수정 → `PUT /api/admin/cash`
- 전체 저장 → `POST /api/admin/save-all`
- Finnhub API 키 관리 → `GET/PUT /api/admin/finnhub-key`, `POST /api/admin/finnhub-test`
- 주가 프록시 → `GET /api/stock-price/<symbol>`

### 외부 API
- **Finnhub**: 미국 주식 실시간 시세 (Quote endpoint, 60초 인메모리 캐시)
- **open.er-api.com**: USD/KRW 환율 (5분 인메모리 캐시, 실패 시 1350 폴백)
- API 키는 DB(SiteConfig)에 저장, 없으면 환경변수 폴백

---

## UI 구성 (index.html 내 순서)

1. **헤더** - 앱 아이콘 + 제목
2. **유저바** - 이름, 관리자 톱니바퀴(⚙), 로그아웃
3. **월 선택** 드롭다운
4. **벌금 카드** (stats-card) - 이번달 벌금, 달성률 배지, 완료/미완료/총평일, 벌금계좌 복사
5. **오늘 체크 버튼** (todayAction)
6. **캘린더 그리드** (calendar-card)
7. **명예의전당** (ranking-card) - 3명까지 표시 + 더보기/접기
8. **보유자산 카드** (asset-card) - 총자산(KRW), 주식목록, 환율, 업데이트시간, 현금
9. **관리자 바텀시트** - API키 관리, 주식 추가/편집/삭제, 현금 입력, 저장하기 버튼
10. **로그인 화면** (loginScreen) - 이름 입력

---

## 최근 완료된 작업 (이번 세션)

1. 벌금계좌 정보 + 복사 아이콘 버튼 추가 (stats-card 하단)
2. 벌금 카드 높이 축소 (padding, font-size, gap 조정)
3. 명예의전당 로딩 최적화 (N+1 쿼리 → 단일 쿼리, 병렬 로딩)

---

## 주의사항

- `models.py`의 `avg_price` 컬럼 추가는 **취소됨** (절대 추가하지 말 것)
- 서비스 워커 캐시 버전 변경 시 `CACHE_NAME`과 `STATIC_CACHE` **둘 다** 업데이트 필요
- `db.create_all()`은 새 테이블만 생성, 기존 테이블 컬럼 변경 불가
- 기존 사용자 영향 없도록 backward-compatible 개발 필수
- 벌금계좌: (카카오)7942-14-57728 김병석
