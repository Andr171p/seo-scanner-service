from typing import Annotated, Any, Final

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Text, func
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ..settings import settings

# ======================Кастомные SQLAlchemy аннотации типов======================
StrUnique = Annotated[str, mapped_column(unique=True)]
StrText = Annotated[str | None, mapped_column(Text, nullable=True)]
UUIDPrimary = Annotated[
    UUID,
    mapped_column(
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid()
    )
]
DatetimeDefault = Annotated[
    datetime, mapped_column(DateTime(timezone=True), server_default=func.now())
]
DatetimeOnupdate = Annotated[
    datetime,
    mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
]
JsonDict = Annotated[dict[str, Any], mapped_column(JSON)]

# ======================Инициализация зависимостей базы данных======================
engine: Final[AsyncEngine] = create_async_engine(url=settings.postgres.sqlalchemy_url, echo=True)

sessionmaker: Final[async_sessionmaker[AsyncSession]] = async_sessionmaker(
    engine, class_=AsyncSession, autoflush=False, expire_on_commit=False
)

# ======================Базовый класс для создания таблиц======================


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    id: Mapped[UUIDPrimary]
    created_at: Mapped[DatetimeDefault]
    updated_at: Mapped[DatetimeOnupdate]


async def create_tables() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
