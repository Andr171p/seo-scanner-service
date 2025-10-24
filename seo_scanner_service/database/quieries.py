from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from ..exceptions import ReadingError, WritingError
from ..schemas import Website
from .base import sessionmaker
from .models import PageContentModel, PageModel, SEOLogModel, WebsiteModel


async def persist_website(website: Website) -> None:
    try:
        async with sessionmaker() as session:
            model = WebsiteModel(
                id=website.id,
                url=str(website.url),
                seo_score=website.seo_score,
                page_count=website.page_count,
                pages=[
                    PageModel(
                        website_id=website.id,
                        url=str(page.url),
                        rendering_time=page.rendering_time,
                        seo_logs=[
                            SEOLogModel(page_id=page.id, **seo_log.model_dump())
                            for seo_log in page.seo_logs
                        ],
                        content=PageContentModel(page_id=page.id, **page.content.model_dump()),
                    )
                    for page in website.pages
                ]
            )
            session.add(model)
            await session.commit()
    except SQLAlchemyError as e:
        raise WritingError(f"Error while persisting website, error: {e}") from e


async def read_all_websites(page: int, limit: int) -> list[Website]:
    try:
        async with sessionmaker() as session:
            offset = (page - 1) * limit
            stmt = (
                select(WebsiteModel)
                .options(
                    joinedload(WebsiteModel.pages)
                    .options(
                        joinedload(PageModel.seo_logs),
                        joinedload(PageModel.content)
                    )
                )
                .offset(offset)
                .limit(limit)
            )
            results = await session.execute(stmt)
            models = results.unique().scalars().all()
        return [Website.model_validate(model) for model in models]
    except SQLAlchemyError as e:
        raise ReadingError(f"Error while reading websites, error: {e}") from e


async def read_website(id: UUID) -> Website | None:  # noqa: A002
    try:
        async with sessionmaker() as session:
            stmt = (
                select(WebsiteModel)
                .options(
                    joinedload(WebsiteModel.pages)
                    .options(
                        joinedload(PageModel.seo_logs),
                        joinedload(PageModel.content)
                    )
                )
                .where(WebsiteModel.id == id)
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return Website.model_validate(model) if model else None
    except SQLAlchemyError as e:
        raise ReadingError(f"Error while reading pages, error: {e}") from e
