# 100챌린지 — Lessons Learned

> 같은 실수/비효율을 반복하지 않기 위해 세션별로 기록. 새 세션 시작 시 반드시 1회 훑어볼 것.

---

## 2026-04-24 세션

### [L1] 한국 주식 회사명은 네이버 m.stock API가 표준
- **교훈**: 한국 종목의 한글 회사명이 필요하면 `https://m.stock.naver.com/api/stock/{code}/basic` 엔드포인트를 **우선 시도**할 것. `stockName` 필드에 "삼성전자" 같은 한글명이 깔끔하게 제공됨.
- **배경**: Yahoo Finance `shortName`은 "SamsungElec" 같은 영문 축약이거나 `"247540.KS,0P0001GZPV,623889"` 같은 깨진 값을 종종 반환. KOSPI/KOSDAQ 구분 없이 `.KS` 먼저 시도하면 잘못된 종목으로 매칭되는 케이스 존재.
- **적용**: 한국 관련 금융 데이터(시세, 회사명, 재무제표 등) 기능 만들 때 항상 네이버/다음 먼저 확인. 글로벌 API로 시간 낭비 말 것.

### [L2] 옐로우/밝은 배경 위 텍스트는 무조건 검정
- **교훈**: `background: var(--primary)` (#FEE500 카카오옐로우) 요소에 `color: white`은 **절대 금지**. 가독성 0. 카카오 공식 스타일대로 `color: #191600` (near-black) 사용.
- **배경**: 머스터드 옐로우(#CA8A04) 첫 구현 시 gradient + white 텍스트로 시작 → 사용자가 "너무 진하다"고 밝은 옐로우로 변경 요청 → 흰 글씨 완전히 안 보임. CSS 변수 `--primary-ink: #191600` 도입으로 일괄 해결.
- **적용**: 옐로우/라임/민트/핑크 등 밝은 primary 컬러를 쓰는 프로젝트에서는 **`--primary-ink` 변수를 반드시 짝으로 정의**하고, primary 배경 요소엔 항상 ink를 쓸 것.

### [L3] ALTER TABLE try/except 패턴은 실제로 잘 작동
- **교훈**: `db.create_all()`은 기존 테이블 ALTER를 못 하지만, 아래 패턴으로 안전하게 컬럼 추가 가능:
  ```python
  try:
      db.session.execute(db.text("ALTER TABLE ... ADD COLUMN ..."))
      db.session.commit()
  except Exception:
      db.session.rollback()
  ```
- **배경**: 이전 메모리에 "avg_price 컬럼 추가 취소됨 — 절대 추가하지 말 것" 룰이 있었지만 실제 코드엔 이미 avg_price가 포함돼 잘 돌고 있었음. 이번 세션에 `current_price`, `name` 2개 컬럼을 같은 패턴으로 추가했고 문제없음.
- **적용**: 같은 패턴으로 안전하게 스키마 확장 가능. 단, 프로덕션(Supabase PostgreSQL) 첫 실행 시 Render 로그로 성공 여부 확인.
- **주의**: 이전 메모리의 "avg_price 룰"은 **outdated, 무시**. 메모리에 있는 과거 제약도 현재 코드와 맞는지 검증할 것.

### [L4] Windows 콘솔에서 한글 출력 디버깅
- **교훈**: Git Bash/기본 터미널은 cp949라 한글이 `�Ｚ����`로 깨짐. 진짜 깨진 건지 콘솔 인코딩 문제인지 구분 필요.
- **확인 방법**:
  ```python
  import sys; sys.stdout.reconfigure(encoding='utf-8')
  # 또는
  print(s.encode('utf-8').hex())  # 헥사 덤프로 실제 바이트 확인
  ```
- **적용**: 한국어 응답 검증 시 항상 UTF-8 재설정 또는 hex 확인.

### [L5] Bash에서 `UID`는 readonly 변수
- **교훈**: `UID=...` 하면 "readonly variable" 에러로 파이프라인 중단. 다른 변수명 사용.
- **적용**: 사용자 ID는 `MYID`, `USER_ID`, `UID_VAR` 같은 이름 사용.

### [L6] 보라색 → 새 컬러 전환 시 rgba까지 체크
- **교훈**: CSS 변수(`--primary`)만 바꿔도 대부분 적용되지만, 하드코딩된 `rgba(91, 33, 182, 0.12)` 같은 shadow 값들은 자동 전환 안 됨. `grep rgba\(91` 전수조사 + python 일괄 치환 필수.
- **이번 케이스**: 보라 rgba 24개 지점 + hex 7개 지점 수동 발견 후 스크립트로 일괄 교체.

---

## 2026-07-24 세션

### [L7] 체감 속도는 네트워크 제거 + 낙관적 업데이트가 답
- **교훈**: "느리다"는 불만의 대부분은 서버 왕복을 UI가 기다리는 구조 문제. (1) stale-while-revalidate(localStorage 캐시 즉시 렌더 → 백그라운드 갱신), (2) 낙관적 업데이트(화면 먼저, 서버는 뒤에, 실패 시 롤백), (3) 클라이언트에서 계산 가능한 것(월 목록, 벌금 재계산)은 API 호출 자체를 제거.
- **적용**: 모바일/PWA 프로젝트에서 조회성 데이터는 기본적으로 캐시 즉시 렌더 패턴 사용.

### [L8] 디자인 업그레이드는 DESIGN.md 토큰 시스템으로
- **교훈**: 감으로 색만 바꾸면 촌스러움 반복. GitHub awesome-design-md(71K★) 류의 브랜드 DESIGN.md를 가져와 토큰(컬러 롤/타이포/radius/간격/컴포넌트)째로 적용하는 게 훨씬 빠르고 결과가 좋음. 이번엔 Binance(옐로우×딥블랙) 시스템 적용 — 프로젝트 루트 `DESIGN.md`로 보존.
- **핵심 원칙**: 단일 액센트 컬러(희소하게), 플랫 컬러블록(명도 단차로 엘리베이션), 숫자는 tabular-nums, 밝은 액센트 위 텍스트는 블랙.
- **적용**: 마크업/JS는 건드리지 않고 `<style>` 블록만 통째 교체하면 기능 리스크 없이 전면 리뉴얼 가능.

### [L10] 디자인 리뉴얼은 코드 전에 "방향 합의"부터 (2026-07-25)
- **교훈**: 디자인 취향 작업에서 2회 연속 거부당함 — 다크 Binance 테마("촌스럽다"), 네오브루탈리즘 블랙보더+Archivo Black("복고 픽셀 같다"). 3번째에 AskUserQuestion으로 ASCII 미리보기 3안을 제시하고 고르게 한 뒤(토스풍 미니멀 선택) 만들었더니 한 번에 통과.
- **이 사용자(원석준)의 확정 취향**: 토스/카카오뱅크류 미니멀 — 밝은 톤, 테두리 없음, 여백, 절제된 액센트. 두꺼운 보더·하드섀도·무거운 디스플레이 폰트·과한 장식 = 촌스럽다고 느낌.
- **적용**: 전면 리디자인 요청 시 반드시 (1) 방향 2~3안을 미리보기와 함께 먼저 제시 → (2) 선택받고 구현 → (3) 스크린샷 검증 → 배포. CSS 전체 교체 방식(마크업/JS 무변경)은 유효했음 — 유지.

### [L9] puppeteer 클릭 검증 시 fixed 요소 주의
- **교훈**: PWA 설치 배너 같은 position:fixed 요소가 클릭 대상을 덮으면 puppeteer 클릭이 배너로 가로채져 "기능이 안 되는 것처럼" 보임. 검증 스크립트에서는 배너를 display:none 처리 후 진행할 것. fullPage 스크린샷에서 숨겨진 fixed 요소(바텀시트)가 보이는 것도 캡처 아티팩트임.

---

## 누적 룰

### [R1] 세션 시작 프로토콜
1. `memory/LATEST_CONTEXT.md` 읽기 (필수)
2. `tasks/todo.md` 읽기 (필수)
3. 필요 시 `memory/sessions/*.md` 최근 파일 참고
4. 사용자에게 "이전 세션 컨텍스트 로드 완료" 알림

### [R2] DB 모델 변경 규칙
- `models.py`에 컬럼 추가 후 `app.py`의 `with app.app_context():` 블록에 ALTER TABLE try/except 마이그레이션 코드 추가
- 기존 데이터 영향 없는 nullable 또는 default 값 필수
- Supabase 프로덕션 배포 후 Render 로그로 마이그레이션 성공 확인

### [R3] 서비스워커 캐시 버전
- `static/service-worker.js`의 `CACHE_NAME`과 `STATIC_CACHE` 둘 다 올릴 것
- 정적 리소스(CSS/JS/아이콘) 변경 시마다 올려야 사용자 기기에서 갱신

### [R4] 컬러 테마 변경 체크리스트
- [ ] `:root` CSS 변수
- [ ] 하드코딩된 hex (grep)
- [ ] 하드코딩된 rgba (grep)
- [ ] 페이지 `<meta name="theme-color">`
- [ ] `manifest.json` theme_color
- [ ] PWA 아이콘 (Pillow 재생성)
- [ ] 서비스워커 캐시 버전
