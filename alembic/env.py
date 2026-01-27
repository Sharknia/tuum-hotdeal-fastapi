import os
import sys
from logging.config import fileConfig

# ---- 추가 시작 ----
from sqlalchemy import engine_from_config, pool

# 프로젝트 루트를 sys.path에 추가
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_dir)

# config 모듈 임포트
# from app.src.core.config import settings # 기존 방식 주석 처리
import app.src.core.config  # 상대 경로 방식으로 임포트 시도
from alembic import context

settings = app.src.core.config.settings  # settings 객체 접근


# 모델 및 Base 임포트 경로 수정
from app.src.core.database import Base  # 기존 방식 주석 처리

# ---- 추가 끝 ----

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

# ---- 수정 시작 ----
# 모델을 이 시점에서 임포트하여 metadata에 등록되도록 함
# from app.src.domain.user.models import User # 기존 방식 주석 처리
import app.src.domain.hotdeal.models
import app.src.domain.mail.models
import app.src.domain.user.models
import app.src.domain.admin.models

User = app.src.domain.user.models.User
Keyword = app.src.domain.hotdeal.models.Keyword
MailLog = app.src.domain.mail.models.MailLog
KeywordSite = app.src.domain.hotdeal.models.KeywordSite
WorkerLog = app.src.domain.admin.models.WorkerLog
target_metadata = Base.metadata  # 우리 프로젝트의 Base.metadata 사용
# ---- 수정 끝 ----

# other values from the config, defined by the needs of env.py,
# can be acquired:-
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # ---- 수정 시작 ----
    # settings 객체에서 DATABASE_URL 가져오기 (Alembic은 동기 URL 사용)
    # url = os.getenv("DATABASE_URL") # 기존 방식 제거
    url = settings.DATABASE_URL
    # if not url: # pydantic-settings가 처리하므로 불필요
    #     raise ValueError(
    #         "DATABASE_URL environment variable not set for Alembic offline mode"
    #     )
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    # ---- 수정 끝 ----

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # ---- 수정 시작 ----
    # settings 객체에서 DATABASE_URL 가져오기 (Alembic은 동기 URL 사용)
    db_url = settings.DATABASE_URL

    # SQLAlchemy 엔진 설정 구성
    connectable = engine_from_config(
        {"sqlalchemy.url": db_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    # ---- 수정 끝 ----

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
