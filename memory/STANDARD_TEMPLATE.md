# Claude Code 메모리 표준 템플릿

새 프로젝트에 이 구조를 적용하려면 아래 단계를 따르세요.

---

## 1. 프로젝트 폴더 구조 생성

```
프로젝트루트/
  memory/
    LATEST_CONTEXT.md       ← 최신 프로젝트 상태 (git 추적)
    STANDARD_TEMPLATE.md    ← 이 파일 (가이드)
    sessions/
      YYYY-MM-DD_주제.md    ← 세션별 작업 기록
```

## 2. Claude 자동 로드 메모리 설정

`~/.claude/projects/<프로젝트경로>/memory/MEMORY.md`에 다음 내용 작성:

```markdown
# 프로젝트 이름

## 프로젝트 개요
- 한 줄 설명, 기술 스택, 배포 환경

## 세션 시작 시 규칙
1. `memory/LATEST_CONTEXT.md` 읽어서 최신 상태 파악
2. 필요 시 `memory/sessions/` 최근 기록 참조

## 세션 종료 시 규칙
1. `memory/LATEST_CONTEXT.md` 업데이트
2. `memory/sessions/YYYY-MM-DD_<주제>.md` 세션 기록 생성

## 핵심 주의사항
- 프로젝트별 중요 규칙들
```

## 3. 운영 흐름

1. **세션 시작** → MEMORY.md 자동 로드 → 규칙에 따라 LATEST_CONTEXT.md 읽기
2. **작업 완료** → LATEST_CONTEXT.md 업데이트 + sessions/ 세션 기록 생성
3. **커밋/푸시** → GitHub에 백업, 다른 PC에서도 복원 가능

## 4. 핵심 원칙

- **MEMORY.md**: 200줄 미만, 프로젝트 개요 + 규칙만 (자동 로드됨)
- **LATEST_CONTEXT.md**: 현재 상태 전체 (파일 구조, API, UI, 주의사항)
- **sessions/**: 세션별 상세 기록 (무엇을 했는지, 커밋 해시, 변경 내용)
