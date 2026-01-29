---
name: commit-expert
description: (opencode - Skill) 스마트 커밋 도우미. Conventional Commits 규칙 준수(한글, 개조식, 이모지 금지) 및 main 브랜치 보호 기능을 제공합니다. 커밋 메시지 작성, 브랜치 관리, 자동 스테이징 로직을 포함합니다. "커밋해줘", "commit", "변경사항 저장" 등의 요청 시 사용합니다.
---

# Commit Expert

엄격한 규칙에 따라 Git 커밋을 처리하는 전문가 스킬입니다.

## Workflow

1.  **Git Status 확인**: `git status` 명령어로 현재 상태를 파악하십시오.
2.  **Branch Protection (Main 보호)**:
    *   현재 브랜치가 `main` 또는 `master`인지 확인하십시오.
    *   만약 맞다면, 직접 커밋을 **절대 금지**합니다.
    *   변경 사항을 분석하여 적절한 Feature 브랜치 이름(`feature/간단한-설명`)을 제안하고, `git checkout -b <branch-name>`으로 브랜치를 생성/이동하십시오.
3.  **Staging Logic**:
    *   **스테이징된 파일이 있는 경우**: 해당 파일들만 커밋 대상입니다.
    *   **스테이징된 파일이 없는 경우**: `git add .` 명령으로 **모든 변경사항**을 스테이징하십시오. (Untracked files 포함)
4.  **Commit Message 작성**:
    *   `git diff --cached` 내용을 분석하여 메시지를 작성하십시오.
    *   **형식 (Format)**: Conventional Commits 준수
        *   `feat`: 새로운 기능 (Feature)
        *   `fix`: 버그 수정 (Bug fix)
        *   `refactor`: 리팩토링 (기능 변경 없음)
        *   `chore`: 빌드, 패키지 매니저, 문서 등 기타 변경
        *   `docs`: 문서 변경
        *   `style`: 코드 포맷팅 (로직 변경 없음)
        *   `test`: 테스트 코드
    *   **언어**: **반드시 한국어 (Korean Only)**
    *   **스타일**:
        *   **개조식, 명사형 종결** (예: "수정함" (X) -> "수정" (O), "추가했습니다" (X) -> "추가" (O))
        *   **이모지 절대 사용 금지**
        *   완전한 문장 사용 지양
    *   **길이**: 전체 메시지 **10줄 미만**
    *   **구조**:
        ```
        <type>: <summary (명사형)>

        - <detail 1 (명사형)>
        - <detail 2 (명사형)>
        ```
5.  **Execution (실행)**:
    *   작성된 메시지로 `git commit -m "..."`을 실행하십시오.
    *   **Push 금지**: 별도의 명시적인 명령("푸시해줘", "배포해줘" 등)이 없다면 `git push`는 **절대 실행하지 마십시오**.

## Examples

### Good Example
```
fix: 로그인 페이지 유효성 검사 오류 수정

- 이메일 정규식 패턴 개선
- 비밀번호 최소 길이 조건 변경 (8자 -> 10자)
- 에러 메시지 가독성 향상
```

### Bad Examples
*   `🐛 fix: 로그인 버그 수정했습니다.` (이모지 사용, 존댓말 문장)
*   `Update login logic` (영어 사용)
*   `로그인 수정` (Type 누락)
