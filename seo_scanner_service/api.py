from typing import Final

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import PositiveInt

from .broker import faststream_app
from .database.base import create_tables
from .database.quieries import read_all_websites, read_website
from .schemas import LogLevelDistribution, Website


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    await create_tables()
    await faststream_app.broker.start()
    await faststream_app.broker.publish({"url": "http://www.diocon.ru/"}, queue="start_scan")
    yield
    await faststream_app.broker.stop()


app: Final[FastAPI] = FastAPI(lifespan=lifespan)


@app.get(
    path="/api/v1/websites",
    status_code=status.HTTP_200_OK,
    response_model=list[Website],
    summary="Получение всех отсканированных сайтов",
)
async def get_websites(
        page: PositiveInt = Query(...), limit: PositiveInt = Query(...)
) -> list[Website]:
    return await read_all_websites(page, limit)


@app.get(
    path="/api/v1/websites/{id}",
    status_code=status.HTTP_200_OK,
    response_model=Website,
    summary="Получение отсканированного сайта",
)
async def get_website(id: UUID) -> Website:  # noqa: A002
    website = await read_website(id)
    if website is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found")
    return website


@app.get(
    path="/api/v1/websites/{id}/seo-logs/distribution",
    status_code=status.HTTP_200_OK,
    response_model=LogLevelDistribution,
    summary="Получение распределение SEO логов по уровням"
)
async def get_website_seo_logs_distribution(id: UUID) -> LogLevelDistribution:  # noqa: A002
    website = await read_website(id)
    if website is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found")
    return website.get_seo_log_level_distribution()
