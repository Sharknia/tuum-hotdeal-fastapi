# Skill Creator Upgrade: Dual-Gen & Auto-Registration

## TL;DR

> **Quick Summary**: `skill-creator` 스킬을 업그레이드하여, 명령어 한 번으로 Claude(`.claude`)와 OpenCode(`.agents`) 양쪽 환경에 스킬을 생성하고 `AGENTS.md`에 자동 등록하도록 수정합니다.
> 
> **Deliverables**:
> - 수정된 `init_skill.py` (Dual-Gen 및 AGENTS.md 등록 로직 포함)
> - 수정된 `SKILL.md` (새로운 사용 가이드)
> 
> **Estimated Effort**: Short
> **Parallel Execution**: Sequential (Single script modification)

---

## Context

### Original Request
`skill-creator`를 사용하여 스킬 생성 시, `.claude`와 `.agents` 폴더에 모두 생성하고 `AGENTS.md`의 `<available_skills>` 목록에도 자동으로 추가되길 원함. 단일 명령어로 처리되어야 함.

### Key Decisions
- **자동화 범위**: 파일 생성(2곳) + 등록(1곳)을 `init_skill.py` 실행 한 번으로 처리.
- **설명(Description) 처리**: `--desc` 옵션으로 입력을 받되, 미입력 시 "TODO"로 자동 처리하여 프로세스가 중단되지 않게 함.
- **AGENTS.md 역할**: OpenCode 시스템이 스킬을 인식하기 위한 필수 "전화번호부". 이 파일 수정이 없으면 스킬이 동작하지 않으므로 자동화 필수.

---

## Work Objectives

### Core Objective
`skill-creator` 프로세스를 단일화하여 Claude/OpenCode 환경 간의 동기화를 보장하고 수동 등록의 번거로움을 제거.

### Concrete Deliverables
- [ ] `.claude/skills/skill-creator/scripts/init_skill.py` (로직 수정됨)
- [ ] `.claude/skills/skill-creator/SKILL.md` (문서 수정됨)
- [ ] (동기화) `.agents/skills/skill-creator/` 내 파일들

### Definition of Done
- [ ] `scripts/init_skill.py test-skill` 실행 시:
    1. `.claude/skills/test-skill` 생성됨
    2. `.agents/skills/test-skill` 생성됨
    3. `AGENTS.md`에 `<name>test-skill</name>` 항목이 추가됨

---

## Verification Strategy

### Automated Verification Only
> **CRITICAL**: 사용자 개입 없는 자동 검증 수행

**Script Logic Test**:
```bash
# Agent executes:
# 1. Run the modified script
python3 .claude/skills/skill-creator/scripts/init_skill.py verification-skill --desc "Verification Test" --path .

# 2. Verify Output 1 (.claude)
ls -F .claude/skills/verification-skill/SKILL.md

# 3. Verify Output 2 (.agents)
ls -F .agents/skills/verification-skill/SKILL.md

# 4. Verify AGENTS.md update
grep "<name>verification-skill</name>" AGENTS.md

# 5. Cleanup
rm -rf .claude/skills/verification-skill .agents/skills/verification-skill
git checkout AGENTS.md  # Revert changes
```

---

## TODOs

- [ ] 1. Modify `init_skill.py` for Dual Generation & Registration

  **What to do**:
  - `init_skill.py` 스크립트를 수정하여 다음 기능을 추가:
    1. **Project Root Detection**: `AGENTS.md` 위치를 찾아 프로젝트 루트로 인식.
    2. **Dual Path Logic**: `.claude/skills/{name}`과 `.agents/skills/{name}` 경로 자동 설정.
    3. **Registration Logic**: `AGENTS.md` 파일을 읽어 `</available_skills>` 태그 직전에 새 스킬 정보 삽입.
    4. **Argument Parsing**: `--desc` (설명) 옵션 추가.

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`python-expert`]

  **Acceptance Criteria**:
  - [ ] `python3 init_skill.py my-test --desc "Test"` 실행 시 에러 없이 종료 (Exit code 0)
  - [ ] `.claude` 및 `.agents` 폴더 양쪽에 파일 생성 확인
  - [ ] `AGENTS.md` 파일 내 `<name>my-test</name>` 문자열 존재 확인

  **Commit**: YES
  - Message: `feat(skill-creator): support dual-generation and auto-registration`
  - Files: `.claude/skills/skill-creator/scripts/init_skill.py`

- [ ] 2. Update `SKILL.md` Documentation & Sync

  **What to do**:
  - `.claude/skills/skill-creator/SKILL.md` 문서 수정:
    - "Step 6: Registering" 섹션을 "자동 등록됨"으로 변경.
    - 새로운 명령어 사용법 (`--desc` 옵션 등) 예시 추가.
  - 수정된 파일들을 `.agents/skills/skill-creator/`로 복사하여 동기화.

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: [`git-master`]

  **Acceptance Criteria**:
  - [ ] `SKILL.md`에 `init_skill.py`의 새로운 사용법이 반영됨
  - [ ] `.claude`와 `.agents` 폴더의 `skill-creator` 내용이 동일함

  **Commit**: YES
  - Message: `docs(skill-creator): update usage guide for auto-registration`
  - Files: `.claude/skills/skill-creator/SKILL.md`, `.agents/skills/skill-creator/*`

---

## Success Criteria

### Verification Commands
```bash
# 1. Create a dummy skill
python3 .claude/skills/skill-creator/scripts/init_skill.py auto-gen-test --desc "Auto Gen Test" --path .

# 2. Check if registered
grep "auto-gen-test" AGENTS.md

# 3. Check if files exist
test -d .claude/skills/auto-gen-test && echo "Claude OK"
test -d .agents/skills/auto-gen-test && echo "Agents OK"
```
