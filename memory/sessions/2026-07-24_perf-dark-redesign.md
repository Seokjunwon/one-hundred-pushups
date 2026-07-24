# 2026-07-24 세션: 속도 대폭 개선 + 다크 프리미엄 디자인 리뉴얼

> 커밋: `5aac981` (main 푸시 → Render 자동 배포 완료)

---

## 1. 속도 개선 (사용자 불만: "진입 시 이번달 기록 로딩 느림, 달력 클릭 반응 느림")

### 원인 진단
- 진입 시 순차 워터폴: `loadMonthOptions()`(불필요한 API) await 후에야 나머지 로드
- `loadCalendar()` 내부에서 `loadRanking()` 중복 호출 → 진입 시 랭킹 2회 fetch
- 달력 클릭: toggle API → calendar 재조회 → ranking 재조회, 왕복 3번을 다 기다린 후 화면 반영
- 백엔드 `/api/calendar`: records 쿼리 + calculate_penalty 내부 동일 쿼리 = Supabase 왕복 2배

### 해결
- **stale-while-revalidate**: localStorage 캐시(`calCache:{uid}:{y}-{m}`, `rankCache:{y}-{m}`)로 즉시 렌더 → 백그라운드 fetch 갱신 (체감 로딩 0초)
- **낙관적 업데이트**: `toggleDay()` 화면 먼저 반영 + `recalcLocalStats()`로 벌금 로컬 재계산, 서버 실패 시 `flip()` 롤백, 서버 상태 불일치 시 보정
- 월 목록 클라이언트 생성 (API 호출 제거), `onMonthChange()`로 캘린더+랭킹 병렬
- 백엔드 단일 쿼리로 벌금 계산, Inter 웹폰트 로드 제거
- 검증: 로컬 서버에서 벌금 계산 정확성 확인 (7/24 기준 평일 18일), puppeteer로 서버 응답 전 즉시 반영 확인

## 2. 디자인 리뉴얼 (사용자: "너무 촌스러, 대폭 업그레이드")

### 리서치
- 사용자가 릴스 캡처로 refero.design / godly.website / mobbin / saaslandingpage 제시
- GitHub 최고 인기 디자인 리포 조사 → **awesome-design-md (VoltAgent, 71K★)** 선정
- **Binance DESIGN.md** 채택 (옐로우×딥블랙 — 기존 카카오옐로우 브랜드 유지하며 프리미엄화)
- 기준 문서를 프로젝트 루트 `DESIGN.md`로 저장 (이 프로젝트 전용. 다른 프로젝트는 각자 DESIGN.md 선택)

### 적용
- `<style>` 블록 전체 교체 (마크업/JS 무변경 → 기능 리스크 0)
- 토큰: canvas #0B0E11 / card #1E2329 / elev·hairline #2B3139 / primary #FCD535 / ink #181A20
- 원칙: 단일 액센트, 플랫 컬러블록, tabular-nums, 헤어라인 구분, 글로우·그라데이션 제거
- 달력: 완료=옐로우+블랙, 오늘=옐로우 링, 미완료=레드 틴트, 일=빨강/토=파랑
- 1위 골드 이펙트 → 옐로우 브랜드 톤 통일 (기존 색상충돌 백로그 해소)
- PWA 아이콘 8종 Pillow 재생성(딥블랙+옐로우 배지), manifest/theme-color #0B0E11, 상태바 black-translucent
- 서비스워커 v16 → v17

### 검증 (전역 CLAUDE.md 매뉴얼 표준 방식)
- puppeteer-core + 시스템 크롬(헤드리스, 412×915 dpr1.5)로 실스크린샷: 로그인/메인/달력/랭킹
- 주의: PWA 배너(fixed)가 달력 클릭을 가로챔 → 검증 시 display:none 처리 (lessons.md L9)
- 테스트 유저/레코드 로컬 SQLite에서 정리 완료

## 3. 다음 세션 확인 사항

- [ ] Render 배포 후 실기기에서 새 다크 디자인 + 서비스워커 v17 갱신 확인 (한 번 껐다 켜기 필요할 수 있음)
- [ ] PWA 아이콘은 재설치 전까지 구버전(옐로우 배경)으로 남을 수 있음
- [ ] 기존 todo [A] 프로덕션 검증 항목 (4-24 세션분) 여전히 미확인
- 사용자 질문 있었음: "디자인 학습이 모든 프로젝트에 적용되나?" → 이 폴더만. 전역 적용 원하면 전역 CLAUDE.md에 방법론 규칙 추가 제안해둠 (답변 완료, 추가 요청 없음)
