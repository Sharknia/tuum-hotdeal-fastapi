# CI/CD 및 배포 아키텍처 가이드

이 문서는 프로젝트의 지속적 통합(CI) 및 지속적 배포(CD) 파이프라인과 운영 서버의 아키텍처에 대해 설명합니다.

## 1. CI/CD 파이프라인 개요

본 프로젝트는 GitHub Actions를 사용하여 `main` 브랜치에 코드가 푸시될 때마다 자동으로 빌드 및 배포를 수행합니다.

### 파이프라인 단계 (Stages)
1. **Lint**: `Ruff`를 사용하여 코드 스타일 및 정적 분석을 수행합니다.
2. **Test**: `Pytest`를 통해 유닛 테스트 및 통합 테스트를 실행합니다.
3. **Build**: Docker 이미지를 빌드하고 GitHub Container Registry (GHCR)에 푸시합니다.
    - **특이사항**: 빌드 타겟 플랫폼은 **`linux/arm64`**로 지정되어 있습니다.
4. **Deploy**: 운영 서버에 SSH로 접속하여 최신 이미지를 반영합니다.
5. **Tag**: 배포 성공 시 `deploy-YYYYMMDD-SHA` 형식의 Git 태그를 자동으로 생성하고 푸시합니다.

## 2. 배포 아키텍처 및 인프라

### 배포 구성도
- **Reverse Proxy**: Nginx (호스트 머신에 별도 설치됨)
- **Application**: Docker Compose 기반 컨테이너 환경
- **Port**: 애플리케이션 포트는 호스트의 **10000**번 포트에 바인딩되어 있습니다.
- **Secrets Management**: [Doppler](https://doppler.com)를 통해 런타임에 환경 변수를 주입합니다.
- **Database**: 외부 PostgreSQL 데이터베이스를 사용합니다.

### 시크릿 관리 (Doppler)
배포 시 `DOPPLER_TOKEN`을 GitHub Secrets에서 가져와 서버로 전달하며, 컨테이너 실행 시 Doppler CLI가 실시간으로 환경 변수를 주입합니다. 이를 통해 서버 내부에 물리적인 `.env` 파일을 두지 않아 보안을 강화했습니다.

### 배포 방식
`deploy.yml` 워크플로우는 SSH를 통해 서버에 접속한 후 다음 명령을 순차적으로 실행합니다:
1. `docker compose -f docker-compose.prod.yml pull`: GHCR에서 최신 이미지를 가져옵니다.
2. `docker compose -f docker-compose.prod.yml up -d --force-recreate`: 컨테이너를 재시작하여 새 버전을 적용합니다.

## 3. 알려진 제한 사항 및 주의 사항

### 정적 파일(Static Files) 관련 리스크
현재 배포 파이프라인은 `docker-compose.prod.yml` 파일만 서버로 전송하며, **`static/` 폴더의 내용을 호스트 머신으로 복사하지 않습니다.**
- `main.py`에서 프로덕션 환경(`ENVIRONMENT=prod`)일 경우 FastAPI의 `StaticFiles` 서빙 기능이 비활성화되도록 설정되어 있습니다.
- 따라서 프론트엔드 정적 파일의 변경 사항이 필요한 경우, 별도의 호스트 레벨 파일 복사 프로세스나 Nginx 설정 업데이트가 필요할 수 있습니다.

### 빌드 타겟 플랫폼
GitHub Actions의 빌드 스텝은 `linux/arm64` 플랫폼을 타겟으로 합니다. 만약 x86_64(Intel/AMD) 기반 서버로 배포 환경이 변경될 경우, `deploy.yml`의 `platforms` 설정을 수정해야 합니다.
