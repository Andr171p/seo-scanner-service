from typing import Final

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, HTTPException, status

from .broker import faststream_app
from .database.quieries import read_website
from .schemas import Website


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    await faststream_app.broker.start()
    await faststream_app.broker.publish({"url": "http://www.diocon.ru/"}, queue="start_scan")
    yield
    await faststream_app.broker.stop()


app: Final[FastAPI] = FastAPI(lifespan=lifespan)


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
