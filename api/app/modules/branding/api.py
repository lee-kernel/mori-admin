from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.decorators import operation_log
from app.db.session import get_db
from app.modules.auth.dependencies import require_admin_permission
from app.modules.branding.schemas import Branding
from app.modules.branding.service import MAX_LOGO_BYTES, get_branding, normalize_logo, save_logo
from app.schemas.response import ApiResponse
from app.utils.response import success


router = APIRouter(prefix="/system", tags=["branding"])


@router.get("/branding", response_model=ApiResponse[Branding])
def read_branding(db: Session = Depends(get_db)) -> ApiResponse[Branding]:
    return success(get_branding(db))


@router.put(
    "/branding/logo",
    response_model=ApiResponse[Branding],
    dependencies=[Depends(require_admin_permission("branding.edit")), operation_log("更新系统 Logo")],
)
async def update_logo(request: Request, db: Session = Depends(get_db)) -> ApiResponse[Branding]:
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > MAX_LOGO_BYTES:
            raise HTTPException(413, "Logo 文件不能超过 1 MB")
        data.extend(chunk)
    try:
        logo = await run_in_threadpool(normalize_logo, bytes(data))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return success(await run_in_threadpool(save_logo, db, logo))


@router.delete(
    "/branding/logo",
    response_model=ApiResponse[Branding],
    dependencies=[Depends(require_admin_permission("branding.edit")), operation_log("重置系统 Logo")],
)
def reset_logo(db: Session = Depends(get_db)) -> ApiResponse[Branding]:
    return success(save_logo(db, None))
