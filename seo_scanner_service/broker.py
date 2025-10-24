from uuid import UUID

from faststream import FastStream
from faststream.rabbit import RabbitBroker
from pydantic import BaseModel, HttpUrl, NonNegativeInt

from .database.quieries import persist_website
from .scanner import scan_website_seo_optimization
from .settings import settings


class StartScanEvent(BaseModel):
    url: HttpUrl


class ScanCompletedEvent(BaseModel):
    website_id: UUID
    url: HttpUrl
    page_count: NonNegativeInt


broker = RabbitBroker(url=settings.rabbitmq.url)

faststream_app = FastStream(broker)


@broker.subscriber("start_scan")
@broker.publisher("scan_completed")
async def handle_start_seo_scan(event: StartScanEvent) -> ScanCompletedEvent:
    website = await scan_website_seo_optimization(event.url)
    await persist_website(website)
    return ScanCompletedEvent(
        website_id=website.id, url=website.url, page_count=website.page_count
    )
