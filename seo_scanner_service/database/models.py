from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, JsonDict, StrText


class WebsiteModel(Base):
    __tablename__ = "websites"

    url: Mapped[str]
    seo_score: Mapped[float]
    page_count: Mapped[int]

    pages: Mapped[list["PageModel"]] = relationship(back_populates="website")


class PageModel(Base):
    __tablename__ = "pages"

    website_id: Mapped[UUID] = mapped_column(ForeignKey("websites.id"), unique=False)
    url: Mapped[str]
    rendering_time: Mapped[int]
    seo_logs: Mapped[list["SEOLogModel"]] = relationship(back_populates="page")
    content: Mapped["PageContentModel"] = relationship(
        back_populates="page", uselist=False
    )

    website: Mapped["WebsiteModel"] = relationship(back_populates="pages")


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
