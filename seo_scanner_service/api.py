from typing import Final

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, status

from .database import get_pages
from .schemas import Page


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    ...


app: Final[FastAPI] = FastAPI(lifespan=lifespan)


@app.get(
    path="/api/v1/sites/{site_id}/pages",
    status_code=status.HTTP_200_OK,
    response_model=list[Page],
    summary="",
)
async def get_site_pages(site_id: UUID) -> list[Page]:
    return await get_pages(site_id)
