#!/bin/bash

# 에러 발생 시 즉시 중단
set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}[Deploy Skill] 배포 프로세스를 시작합니다...${NC}"

# 1. 현재 브랜치 확인
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" == "main" ]; then
    echo -e "${RED}[Error] main 브랜치에서는 이 스크립트를 실행할 수 없습니다.${NC}"
    echo "기능 브랜치에서 실행해주세요."
    exit 1
fi

# 커밋되지 않은 변경사항 확인
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}[Error] 커밋되지 않은 변경사항이 있습니다. 먼저 커밋하거나 스태시해주세요.${NC}"
    exit 1
fi

echo -e "${GREEN}[1/5] 현재 브랜치: $CURRENT_BRANCH${NC}"

# 2. 테스트 및 린터 실행
echo -e "${YELLOW}[2/5] 코드 품질 검사를 시작합니다...${NC}"

echo "Running Ruff Linter..."
poetry run ruff check .
if [ $? -ne 0 ]; then
    echo -e "${RED}[Error] 린터 검사에 실패했습니다.${NC}"
    exit 1
fi

echo "Running Pytest..."
poetry run pytest
if [ $? -ne 0 ]; then
    echo -e "${RED}[Error] 테스트에 실패했습니다.${NC}"
    exit 1
fi

echo -e "${GREEN}모든 테스트와 린터 검사를 통과했습니다.${NC}"

# 3. main 브랜치 업데이트
echo -e "${YELLOW}[3/5] main 브랜치를 업데이트합니다...${NC}"
git checkout main
git pull origin main

# 4. 병합 및 푸시
echo -e "${YELLOW}[4/5] $CURRENT_BRANCH 내용을 main에 병합합니다...${NC}"
git merge --no-ff "$CURRENT_BRANCH" -m "Merge branch '$CURRENT_BRANCH' into main"

echo "Pushing to origin main..."
git push origin main

# 5. 브랜치 정리
echo -e "${YELLOW}[5/5] 작업 브랜치를 정리합니다...${NC}"

# 로컬 브랜치 삭제
git branch -d "$CURRENT_BRANCH"

# 원격 브랜치 삭제
echo "Deleting remote branch '$CURRENT_BRANCH'..."
git push origin --delete "$CURRENT_BRANCH" || echo -e "${YELLOW}[Warning] 원격 브랜치 삭제 실패 (이미 삭제되었거나 존재하지 않음)${NC}"

echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}   배포(Merge & Push)가 성공적으로 완료되었습니다!   ${NC}"
echo -e "${GREEN}   Github Actions가 자동으로 배포를 시작할 것입니다.   ${NC}"
echo -e "${GREEN}======================================================${NC}"
