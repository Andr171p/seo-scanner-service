import asyncio
import logging

from seo_scanner_service.broker import app


async def main() -> None:
    await app.broker.start()
    await app.broker.publish(message={"site_url": "http://www.diocon.ru/"}, queue="start_seo_scan")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
