from uuid import UUID

from faststream import FastStream
from faststream.rabbit import RabbitBroker
from pydantic import BaseModel, HttpUrl, NonNegativeInt

from .database import add_pages, create_site
from .schemas import Site
from .scanner import scan_site_seo_optimization
from .settings import settings


class StartScanEvent(BaseModel):
    url: HttpUrl


class CompletedScanEvent(BaseModel):
    site_id: UUID
    url: HttpUrl
    page_count: NonNegativeInt


broker = RabbitBroker(url=settings.rabbitmq.url)

app = FastStream(broker)


@broker.subscriber("start_scan")
@broker.publisher("completed_seo_scan")
async def handle_start_seo_scan(event: StartScanEvent) -> CompletedScanEvent:
    pages = await scan_site_seo_optimization(event.url)
    site = Site(url=event.url, page_count=len(pages))
    await create_site(site)
    await add_pages(pages)
    return CompletedScanEvent(site_id=site.id, url=site.url, page_count=site.page_count)
