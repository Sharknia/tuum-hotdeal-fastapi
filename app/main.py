# app/main.py

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

import app.src.domain.hotdeal.models
import app.src.domain.mail.models
import app.src.domain.user.models
from app.src.core.config import settings
from app.src.core.exceptions.base_exceptions import BaseHTTPException
from app.src.core.logger import logger
from app.src.domain.admin.v1 import router as admin_router
from app.src.domain.hotdeal.v1 import router as hotdeal_router
from app.src.domain.user.v1 import router as user_router

# CORS 설정
if settings.ENVIRONMENT == "local":
    origins = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ]
elif settings.ENVIRONMENT == "dev":
    origins = [
        "https://dev.tuum.day",
        "https://dev-api.tuum.day",
    ]
elif settings.ENVIRONMENT == "prod":
    origins = [
        "https://www.tuum.day",
        "https://tuum.day",
        "https://api.tuum.day",
    ]
else:
    origins = []


# Lifespan 핸들러
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 애플리케이션 시작
    logger.info("애플리케이션 시작...")
    logger.info("origins: %s", origins)
    yield

    # 애플리케이션 종료
    logger.info("애플리케이션 종료...")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom OpenAPI 설정
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Your API Title",
        version="1.0.0",
        description="This is a custom OpenAPI schema",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

app.include_router(user_router.router, prefix="/api/user")
app.include_router(hotdeal_router.router, prefix="/api/hotdeal")
app.include_router(admin_router.router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.exception_handler(BaseHTTPException)
async def base_http_exception_handler(
    request: Request,
    exc: BaseHTTPException,
):
    logger.error(
        "Error: %s, Status: %s, Desc: %s",
        exc.detail,
        exc.status_code,
        exc.description,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "description": exc.description,
            "detail": exc.detail,
        },
    )


if settings.ENVIRONMENT == "local":
    # 특정 HTML 페이지 서빙 라우트 (API 라우터 뒤, StaticFiles 앞)
    @app.get("/", response_class=RedirectResponse)
    async def read_root():
        return RedirectResponse(url="/index.html")

    @app.get("/login", response_class=FileResponse)
    async def login_page():
        return FileResponse("static/login.html")

    @app.get("/signup", response_class=FileResponse)
    async def signup_page():
        return FileResponse("static/signup.html")

    @app.get("/hotdeal", response_class=FileResponse)
    async def hotdeal_page():
        return FileResponse("static/hotdeal.html")

    # Static files 마운트 (가장 마지막에)
    app.mount("/", StaticFiles(directory="static"), name="static")
