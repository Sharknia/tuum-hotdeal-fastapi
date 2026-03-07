# FUR-17 CI/CD 속도 계측 및 최적화 계획

## 1. 목표

`Deploy to Production` GitHub Actions 실행 시간을 계측하고, 최적화 필요 여부를 판단한 뒤 후속 실행 계획을 정의한다.

## 2. 계측 방법

- 워크플로우: `Deploy to Production` (`.github/workflows/deploy.yml`)
- 수집 대상: 최근 `main` 브랜치 `push` 성공 런 중 `Build & Push`/`Deploy`가 실제 실행된 6건
- 수집 명령:
  - `gh run list --workflow "Deploy to Production" --limit 40 --json ...`
  - `gh api repos/Sharknia/tuum-hotdeal-fastapi/actions/runs/<run_id>/jobs?per_page=100`
- 계측 시각(UTC): `2026-03-07`

## 3. 계측 결과

### 3.1 전체 워크플로우 시간(초)

| Run ID | Total | 비고 |
| --- | ---: | --- |
| 22794721038 | 184 | [FUR-16] 프록시 재시도 누적 백오프 예산 상한 도입 |
| 22792927022 | 137 | feat: tune crawling concurrency and backoff safety |
| 22757425031 | 855 | test: decouple pytest init from prod env (#4) |
| 22602177414 | 126 | fix: 좀비 카운트 게이트 종료 코드 안정화 |
| 22487450859 | 180 | fix: 웹 서비스 Doppler 실행 경로 복구 |
| 22310172041 | 147 | Merge branch 'fix/deploy-startup-readiness' into main |

- 중앙값: **163.5s**
- 최소/최대: **126s / 855s**

### 3.2 잡 평균 소요(초)

| Job | 평균 | 중앙값 |
| --- | ---: | ---: |
| Build & Push | 160.7 | 57.5 |
| Test | 49.7 | 50.0 |
| Deploy | 37.8 | 29.5 |
| Lint | 20.2 | 19.5 |

### 3.3 스텝 평균 소요(초)

| Step | 평균 | 중앙값 |
| --- | ---: | ---: |
| Build & Push :: Build and push | 135.2 | 33.0 |
| Deploy :: Deploy to server | 33.5 | 25.5 |
| Test :: Run tests | 30.2 | 30.5 |

## 4. 판단

최적화는 **필요**하다.

- 병목의 핵심은 `Build & Push :: Build and push`이며 변동폭이 크다.
- 최장 런(`22757425031`)에서 `Build and push` 스텝만 `672s` 소요됐다.
- 해당 런의 커밋(`62e1d85`) 변경 파일은 `.env.test`, `pytest.ini`만 확인되어, 테스트 설정 변경에도 배포 경로가 실행되는 비효율이 확인됐다.

## 5. 최적화 계획(우선순위)

1. **배포 조건 분리(우선순위 P0)**
   - `changes` 필터를 `backend_ci`와 `backend_deploy`로 분리
   - `lint/test`는 `backend_ci`, `build/deploy/tag`는 `backend_deploy` 기준으로 실행
   - 목표: 테스트/문서/설정 변경에서 불필요 배포 제거

2. **Docker build 캐시 안정화(우선순위 P1)**
   - Buildx 캐시를 `type=gha` + `type=registry` 병행으로 강화
   - 목표: 캐시 미스 시에도 빌드 시간 변동성 완화

3. **변경 전/후 성능 비교 자동화(우선순위 P1)**
   - 최근 5회 기준 잡/스텝 시간 비교표를 PR 본문 또는 문서에 고정 기록
   - 목표: 개선 효과를 정량적으로 추적

## 6. 후속 이슈

- `FUR-19`: [CI/CD] 백엔드 CI/배포 경로 분리 및 Docker Build 캐시 안정화
  - URL: `https://linear.app/furychick/issue/FUR-19/cicd-백엔드-ci배포-경로-분리-및-docker-build-캐시-안정화`
  - 상태: `Backlog`
  - 관계: `FUR-17`과 `related`, `FUR-17 blocks FUR-19`
