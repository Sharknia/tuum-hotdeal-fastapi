from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.src.core.dependencies.auth import authenticate_admin_user
from app.src.domain.user.schemas import AuthenticatedUser
from app.worker_main import job

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.post(
    "/hotdeals/trigger-search",
    status_code=status.HTTP_202_ACCEPTED,
    summary="수동으로 핫딜 검색을 실행합니다. (관리자 권한 필요)",
)
async def trigger_hotdeal_search(
    background_tasks: BackgroundTasks,
    # 아래 의존성 주입으로 관리자 권한을 가진 사용자만 이 엔드포인트에 접근할 수 있습니다.
    _: AuthenticatedUser = Depends(authenticate_admin_user),
):
    """
    백그라운드에서 핫딜 크롤링 및 분석 작업을 실행합니다.
    작업 실행 요청만 받고 즉시 응답을 반환하며, 실제 작업은 비동기적으로 처리됩니다.
    """
    background_tasks.add_task(job)
    return {"message": "핫딜 검색 작업이 백그라운드에서 시작되었습니다."}
