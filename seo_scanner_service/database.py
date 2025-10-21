from typing import Annotated, Any, Final

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Text, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, joinedload, mapped_column, relationship

from .schemas import Page, Site
from .settings import settings

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


class SiteModel(Base):
    __tablename__ = "sites"

    url: Mapped[str]
    page_count: Mapped[int]

    pages: Mapped[list["PageModel"]] = relationship(back_populates="site")


class PageModel(Base):
    __tablename__ = "pages"

    site_id: Mapped[UUID] = mapped_column(ForeignKey("sites.id"), unique=False)
    url: Mapped[str]
    rendering_time: Mapped[int]
    seo_logs: Mapped[list["SEOLogModel"]] = relationship(back_populates="page")
    content: Mapped["PageContentModel"] = relationship(
        back_populates="page", uselist=False
    )

    site: Mapped["SiteModel"] = relationship(back_populates="pages")


class PageContentModel(Base):
    __tablename__ = "page_contents"

    page_id: Mapped[UUID] = mapped_column(ForeignKey("pages.id"), unique=True)
    meta: Mapped[JsonDict]
    text: Mapped[StrText]

    page: Mapped["PageModel"] = relationship(back_populates="content")


class SEOLogModel(Base):
    __tablename__ = "seo_logs"

    page_id: Mapped[UUID] = mapped_column(ForeignKey("pages.id"), unique=False)
    level: Mapped[str]
    message: Mapped[str]
    category: Mapped[str]
    element: Mapped[str]

    page: Mapped["PageModel"] = relationship(back_populates="seo_logs")


async def create_site(site: Site) -> None:
    try:
        async with sessionmaker() as session:
            session.add(SiteModel(**site.model_dump()))
            await session.commit()
    except SQLAlchemyError:
        ...


async def add_pages(site_id: UUID, pages: list[Page]) -> None:
    try:
        async with sessionmaker() as session:
            models = [
                PageModel(
                    id=page.id,
                    site_id=site_id,
                    url=str(page.url),
                    rendering_time=page.rendering_time,
                    seo_logs=[
                        SEOLogModel(
                            page_id=page.id,
                            level=seo_log.level,
                            message=seo_log.message,
                            category=seo_log.category,
                            element=seo_log.element,
                        )
                        for seo_log in page.seo_logs
                    ],
                    content=PageContentModel(
                        page_id=page.id,
                        meta=page.content.meta.model_dump(),
                        text=page.content.text,
                    )
                )
                for page in pages
            ]
            session.add_all(models)
            await session.flush()
            await session.commit()
    except SQLAlchemyError:
        ...


async def get_pages(site_id: UUID) -> list[Page]:
    try:
        async with sessionmaker() as session:
            stmt = (
                select(PageModel)
                .options(
                    joinedload(PageModel.seo_logs),
                    joinedload(PageModel.content)
                )
                .where(PageModel.site_id == site_id)
            )
            results = await session.execute(stmt)
            models = results.scalars().all()
            return [Page.model_validate(model) for model in models]
    except SQLAlchemyError:
        ...
