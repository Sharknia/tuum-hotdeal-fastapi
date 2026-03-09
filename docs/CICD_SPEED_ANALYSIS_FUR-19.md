# FUR-19 CI/CD 경로 분리 및 캐시 보강 비교 리포트

## 1. 측정 범위

- 워크플로우: `Deploy to Production` (`.github/workflows/deploy.yml`)
- 기준 런: `main` 브랜치 `push` 성공 최근 5회 (측정 시각: `2026-03-09 UTC`)
- 수집 명령:
  - `gh run list --workflow "Deploy to Production" --branch main --status success --limit 30 --json ...`
  - `gh api repos/Sharknia/tuum-hotdeal-fastapi/actions/runs/<run_id>/jobs`
  - `gh api repos/Sharknia/tuum-hotdeal-fastapi/commits/<sha>`

## 2. 비교 방법

- **변경 전(Before)**: 각 런의 실제 소요 시간.
- **변경 후(After, 추정)**: 동일 런에 FUR-19의 새 분기 규칙(`backend_ci`/`backend_deploy`)을 적용해 재계산.
  - `backend_deploy=false`로 분류되는 런은 `Build & Push`, `Deploy`, `Create Tag` 시간을 0으로 처리.
  - `backend_deploy=true` 런은 기존 경로 유지(시간 동일 가정).
- 참고: 캐시 보강(`gha + registry`)의 추가 개선 효과는 배포 후 실측 런 누적 시 별도 업데이트 필요.

## 3. 런 단위 비교 (최근 5회)

| Run ID | Head | 변경 핵심 | backend_deploy | Before Total(s) | After Total(s, 추정) | 절감(s) |
| --- | --- | --- | --- | ---: | ---: | ---: |
| 22833502386 | `00a7349` | `docs/CICD_SPEED_ANALYSIS_FUR-17.md` | false | 10 | 10 | 0 |
| 22794721038 | `22aeb94` | `app/**`, `tests/**` | true | 184 | 184 | 0 |
| 22792927022 | `db3c4f2` | `app/**`, `tests/**`, `docs/**` | true | 137 | 137 | 0 |
| 22757425031 | `62e1d85` | `.env.test`, `pytest.ini` | false | 855 | 68 | 787 |
| 22602177414 | `adac48e` | `.github/workflows/deploy.yml`, `tests/**` | false | 126 | 68 | 58 |

- Total 중앙값: **137s → 68s** (추정 `-69s`)
- Total 최소/최대: **10~855s → 10~184s** (변동성 축소)

## 4. 잡/스텝 비교 (최근 5회 중앙값)

| 항목 | Before 중앙값(s) | After 중앙값(s, 추정) | 비고 |
| --- | ---: | ---: | --- |
| Job: Detect Changes | 5 | 5 | 동일 |
| Job: Lint | 19 | 19 | 동일 |
| Job: Test | 50 | 50 | 동일 |
| Job: Build & Push | 37 | 0 | `backend_deploy=false` 런에서 생략 |
| Job: Deploy | 28 | 0 | `backend_deploy=false` 런에서 생략 |
| Job: Create Tag | 4 | 0 | 배포 성공 런에서만 생성 |
| Step: Build & Push :: Build and push | 16 | 0 | 생략 런 반영 |
| Step: Deploy :: Deploy to server | 24 | 0 | 생략 런 반영 |

## 5. 결론

- 테스트/설정 중심 변경(`.env.test`, `pytest.ini`, `tests/**`)에서 배포 경로를 분리하면 대기시간과 변동폭이 크게 줄어든다.
- 런타임 영향 변경(`app/**`, `alembic/**`, 이미지/컴포즈/엔트리포인트/핵심 설정 파일)은 기존 `Lint/Test -> Build -> Deploy -> Tag` 경로를 유지한다.
- Docker Build 캐시는 `GHA + registry` 병행으로 구성되어, GHA 캐시 미스 시 registry 캐시를 폴백으로 사용할 수 있다.
