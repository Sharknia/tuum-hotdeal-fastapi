# Skill Creator Update Plan: Dual Mode Support

## TL;DR

> **Quick Summary**: Modify `skill-creator` to support simultaneous generation of skills for both Claude (`.claude/skills`) and OpenCode (`.agents/skills`) environments.
> 
> **Deliverables**:
> - Updated `init_skill.py` with `--dual` flag, root detection, and rollback logic.
> - Updated `SKILL.md` (in both locations) with new usage instructions.
> 
> **Estimated Effort**: Short (1 hour)
> **Parallel Execution**: Sequential

---

## Context

### Original Request
Modify `skill-creator` to create skills for both Claude and OpenCode simultaneously when used.

### Interview Summary
**Key Decisions**:
- **Update Both**: Modify instructions (`SKILL.md`) AND the automation script (`init_skill.py`).
- **Always Both Strategy**: Add a `--dual` flag to the script to handle simultaneous creation.
- **Manual Registration**: The script will *print* the XML for `AGENTS.md` (safest approach), rather than auto-editing.

### Metis Review
**Identified Gaps (Addressed in Plan)**:
- **Root Detection**: Script must robustness find project root to locate `.claude` and `.agents` folders.
- **Rollback**: If creation fails in the second location, the first must be cleaned up to prevent partial state.
- **Conflict Handling**: Explicit error if `--dual` and `--path` are used together.
- **Synchronization**: Both copies of `SKILL.md` must be updated.

---

## Work Objectives

### Core Objective
Enable one-command creation of dual-compatible skills.

### Concrete Deliverables
- `init_skill.py` (updated in `.claude` and `.agents`)
- `SKILL.md` (updated in `.claude` and `.agents`)

### Definition of Done
- [x] `init_skill.py my-skill --dual` creates directories in both locations.
- [x] `init_skill.py my-skill --dual` prints valid XML for `AGENTS.md`.
- [x] `SKILL.md` accurately reflects the new `--dual` workflow.

### Must Have
- Robust error handling (rollback on failure).
- Clear output instructions for the user.

### Must NOT Have
- Automatic editing of `AGENTS.md` (print XML only).

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: N/A (Python script)
- **User wants tests**: Manual verification is sufficient for this utility script.
- **QA approach**: Manual verification via `interactive_bash` or `Bash`.

### Automated Verification Procedures

**For Script Logic**:
```bash
# Agent runs:
python3 .agents/skills/skill-creator/scripts/init_skill.py test-skill-dual --dual
# Assert: Output contains "✅ Created skill directory" (twice)
# Assert: Output contains "<available_skills>" XML snippet
# Assert: Directory .claude/skills/test-skill-dual exists
# Assert: Directory .agents/skills/test-skill-dual exists

# Cleanup:
rm -rf .claude/skills/test-skill-dual .agents/skills/test-skill-dual
```

---

## Execution Strategy

### Parallel Execution Waves
Sequential execution is preferred to ensure consistency between the two locations.

### Agent Dispatch Summary
- **Task 1**: Update `init_skill.py` (script logic).
- **Task 2**: Update `SKILL.md` (instructions).
- **Task 3**: Sync changes to second location.

---

## TODOs

- [x] 1. Update `init_skill.py` logic

  **What to do**:
  - Modify `.agents/skills/skill-creator/scripts/init_skill.py`:
    - Add `import argparse` (or keep `sys.argv` but handle flags robustly).
    - Add `find_project_root()` function (look for `.git` or `AGENTS.md`).
    - Implement `--dual` logic:
      - Resolve paths: `{root}/.claude/skills/{name}` and `{root}/.agents/skills/{name}`.
      - Call `init_skill` for both.
      - If second fails, `shutil.rmtree` first (rollback).
      - Print `AGENTS.md` XML template.
    - Ensure `--path` still works.
    - Error if both flags present.

  **Recommended Agent Profile**:
  - **Category**: `quick` (Python script modification)
  - **Skills**: `python`

  **References**:
  - Current script: `.agents/skills/skill-creator/scripts/init_skill.py`

  **Acceptance Criteria**:
  - [x] `init_skill.py --help` (or invalid args) shows `--dual` option.
  - [x] Running with `--dual` creates both directories.
  - [x] XML snippet is printed.

- [x] 2. Update `SKILL.md` instructions

  **What to do**:
  - Modify `.agents/skills/skill-creator/SKILL.md`:
    - **Step 3**: Change command to `scripts/init_skill.py <name> --dual`.
    - **Step 3**: Explain that this creates skill in both `.claude` and `.agents`.
    - **Step 6**: Update "Registering" section.
      - State that script provides the XML.
      - Reiterate that `AGENTS.md` edit is mandatory for OpenCode.

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: `markdown`

  **Acceptance Criteria**:
  - [x] Step 3 mentions `--dual`.
  - [x] Step 6 explains using the script output.

- [x] 3. Sync changes to `.claude` directory

  **What to do**:
  - Copy `.agents/skills/skill-creator/scripts/init_skill.py` to `.claude/skills/skill-creator/scripts/init_skill.py`.
  - Copy `.agents/skills/skill-creator/SKILL.md` to `.claude/skills/skill-creator/SKILL.md`.

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `bash`

  **Acceptance Criteria**:
  - [x] Both directories have identical, updated files.
  - [x] `diff` returns empty.

---

## Success Criteria

### Verification Commands
```bash
# 1. Run dual creation
./.agents/skills/skill-creator/scripts/init_skill.py test-dual-skill --dual

# 2. Check existence
ls -d .claude/skills/test-dual-skill
ls -d .agents/skills/test-dual-skill

# 3. Check output for XML
# (Visually confirm XML block in output)

# 4. Cleanup
rm -rf .claude/skills/test-dual-skill .agents/skills/test-dual-skill
```
