import contextlib
import sys
from collections.abc import AsyncIterator

from alembic import command, config
from pydantic.networks import PostgresDsn
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.settings import settings


def create_engine(url: str | PostgresDsn):
    url = str(url)
    use_echo = settings.debug
    connect_args = {}
    return create_async_engine(
        url,
        echo=use_echo,
        future=True,  # use the sqlalchemy 2.0 classes
        connect_args=connect_args,
    )


def generate_test_db_dsn(dsn: str | PostgresDsn) -> str:
    part_dsn, db_name = str(dsn).rsplit("/", 1)
    return f"{part_dsn}/test_{db_name}"


engine = create_engine(settings.database_url)
if "pytest" in sys.modules:
    # a bug forces us recreate the engine and pint it to the testing database
    engine = create_engine(generate_test_db_dsn(settings.database_url))


def run_upgrade(connection, cfg):
    cfg.attributes["connection"] = connection
    command.upgrade(cfg, "head")


async def init_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(run_upgrade, config.Config("alembic.ini"))


async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        yield session


@contextlib.asynccontextmanager
async def async_session_manager(
    auto_commit=True, session_overwrite: AsyncSession | None = None
) -> AsyncIterator[AsyncSession]:
    if session_overwrite:
        yield session_overwrite
    else:
        async with async_session_maker() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                raise e
            else:
                if auto_commit:
                    await session.commit()
