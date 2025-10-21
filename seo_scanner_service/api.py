from typing import Final

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, status

from .broker import faststream_app
from .database import get_pages
from .schemas import Page


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    await faststream_app.broker.start()
    await faststream_app.broker.publish({"url": "http://www.diocon.ru/"}, queue="start_scan")
    yield
    await faststream_app.broker.stop()


app: Final[FastAPI] = FastAPI(lifespan=lifespan)


@app.get(
    path="/api/v1/sites/{site_id}/pages",
    status_code=status.HTTP_200_OK,
    response_model=list[Page],
    summary="Получение всех отсканированных страниц сайта",
)
async def get_site_pages(site_id: UUID) -> list[Page]:
    return await get_pages(site_id)
