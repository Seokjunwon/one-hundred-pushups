# 100챌린지 - 프로젝트 컨텍스트

> 이 문서는 Claude와 작업 시 빠른 컨텍스트 파악을 위한 문서입니다.

---

## 프로젝트 정보

| 항목 | 내용 |
|------|------|
| **프로젝트명** | 100챌린지 (One Hundred Push-ups) |
| **목적** | 소모임 내 매일 100개 푸시업 챌린지 + 벌금 관리 |
| **사이트** | https://one-hundred-pushups.onrender.com |
| **GitHub** | https://github.com/Seokjunwon/one-hundred-pushups |
| **DB** | Supabase PostgreSQL (Session Pooler) |
| **배포** | Render (GitHub 연동 자동 배포) |

---

## 기술 스택

```
Backend:  Flask 3.0 + SQLAlchemy (Python 3.11)
Frontend: Vanilla JS (단일 HTML SPA)
Database: PostgreSQL (Supabase) / SQLite (로컬 개발)
PWA:      manifest.json + Service Worker
배포:     Render + WhiteNoise (정적 파일)
```

---

## 파일 구조

```
one-hundred-pushups/
├── app.py                 # Flask 메인 (라우트, API)
├── models.py              # SQLAlchemy 모델 (User, PushupRecord)
├── templates/
│   └── index.html         # 프론트엔드 전체 (HTML+CSS+JS)
├── static/
│   ├── manifest.json      # PWA 매니페스트
│   ├── service-worker.js  # 서비스 워커
│   └── icons/             # PWA 아이콘 (72~512px)
├── requirements.txt       # Python 의존성
├── render.yaml            # Render 배포 설정
├── Procfile               # gunicorn 실행
└── CLAUDE_CONTEXT.md      # 이 파일
```

---

## 현재 데이터 모델

```python
class User:
    id: int (PK)
    name: str (unique)  # 로그인 식별자
    created_at: datetime

class PushupRecord:
    id: int (PK)
    user_id: int (FK → User)
    date: date
    completed: bool
    created_at: datetime
```

---

## API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/` | 메인 페이지 |
| POST | `/api/login` | 로그인 (이름으로) |
| GET | `/api/calendar/<year>/<month>` | 캘린더 데이터 |
| POST | `/api/toggle` | 완료 상태 토글 |
| GET | `/api/ranking` | 명예의전당 랭킹 |
| GET | `/api/available-months` | 조회 가능 월 목록 |
| GET | `/manifest.json` | PWA 매니페스트 |
| GET | `/service-worker.js` | 서비스 워커 |

---

## 현재 구현된 기능

### 인증
- [x] 이름 입력만으로 로그인 (비밀번호 없음)
- [x] localStorage 세션 저장 (브라우저 종료 후에도 유지)

### 핵심 기능
- [x] 캘린더 UI로 푸시업 완료 체크/취소
- [x] 과거 날짜 수정 가능
- [x] 평일만 카운트 (주말/공휴일 자동 제외)
- [x] 한국 공휴일 자동 반영 (`holidays` 라이브러리)
- [x] 월별 벌금 계산 (미완료 평일 × 10,000원)

### 명예의전당
- [x] 벌금 기준 랭킹 (적은 순 → 먼저 체크한 순)
- [x] 상위 3명만 표시 + 더보기/접기 버튼

### PWA
- [x] 홈 화면 설치 지원
- [x] 설치 유도 배너 (하단 슬라이드)
- [x] 3일간 "나중에" 선택 시 재표시 안 함
- [x] Service Worker 캐싱

---

## 현재 한계점 (고도화 필요)

| 항목 | 현재 | 문제점 |
|------|------|--------|
| **인증** | 이름만 입력 | 보안 없음, 사칭 가능 |
| **그룹** | 단일 그룹 (전체 공유) | 여러 모임 운영 불가 |
| **관리** | 없음 | 그룹장/멤버 구분 없음 |
| **초대** | 없음 | 누구나 이름만 알면 참여 |

---

## 확장 로드맵 (Step by Step)

### Phase 1: 인증 강화
- 소셜 로그인 (카카오/구글) 또는 이메일+비밀번호
- JWT 기반 세션 관리
- 기존 사용자 마이그레이션 방안 필요

### Phase 2: 그룹 시스템
- 그룹 생성/참여/탈퇴
- 초대 코드 또는 초대 링크
- 그룹별 독립 랭킹
- 한 유저가 여러 그룹 참여 가능

### Phase 3: 그룹 관리
- 그룹장(owner) 권한
  - 멤버 강퇴
  - 그룹 설정 변경
  - 그룹 삭제
- 챌린지 규칙 커스터마이징
  - 벌금 금액 설정
  - 목표 개수 설정
  - 평일/매일 선택

### Phase 4: 고도화
- 푸시 알림 (미완료 시 리마인더)
- 카카오톡 알림 연동
- 통계 대시보드 (주간/월간 트렌드)
- 챌린지 종류 확장 (스쿼트, 플랭크 등)

---

## 확장 시 예상 데이터 모델

```python
class User:
    id: int
    email: str (nullable, 소셜 로그인 시)
    social_provider: str (kakao/google/null)
    social_id: str
    name: str
    created_at: datetime

class Group:
    id: int
    name: str
    invite_code: str (unique, 6자리)
    owner_id: int (FK → User)
    settings: JSON  # {"penalty": 10000, "goal": 100, "weekdays_only": true}
    created_at: datetime

class GroupMember:
    id: int
    group_id: int (FK → Group)
    user_id: int (FK → User)
    role: str  # "owner" | "member"
    joined_at: datetime

class PushupRecord:
    id: int
    user_id: int (FK → User)
    group_id: int (FK → Group)  # 추가
    date: date
    completed: bool
    created_at: datetime
```

---

## 개발 환경 설정

```bash
# 의존성 설치
pip install -r requirements.txt

# 로컬 실행 (SQLite 사용)
python app.py

# 환경 변수 (배포 시)
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://...  # Supabase 연결 문자열
```

---

## 배포 방법

```bash
# 변경사항 커밋 & 푸시 → Render 자동 배포
git add .
git commit -m "커밋 메시지"
git push origin main
```

**주의**: Service Worker 캐시 버전 업데이트 필요 시 `static/service-worker.js`의 `CACHE_NAME`, `STATIC_CACHE` 버전 숫자 증가

---

## 작업 시 참고사항

1. **프론트엔드**: `templates/index.html` 단일 파일에 HTML+CSS+JS 모두 포함
2. **공휴일**: `holidays.KR()` 사용, 자동으로 한국 공휴일 반영
3. **캐시 문제**: 모바일 업데이트 안 될 시 Service Worker 버전 올리고 재배포
4. **DB 마이그레이션**: 현재 없음, 스키마 변경 시 수동 대응 필요

---

## 대화 히스토리 요약

1. 명예의전당 더보기/접기 기능 추가
2. PWA 설정 (manifest, service-worker, 아이콘)
3. 앱 설치 유도 배너 구현
4. 앱 아이콘을 💪 이모지로 변경
5. 앱 이름을 "100챌린지"로 변경

**다음 작업 방향**: 인증 강화 → 그룹 시스템 순으로 단계적 확장 예정

---

*마지막 업데이트: 2026-02-04*
