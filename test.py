import asyncio
import logging

from pydantic import HttpUrl

from seo_scanner_service.scanner import scan_website_seo_optimization

url = "http://www.diocon.ru/"
url1 = "https://tyumen-soft.ru/"


async def main() -> None:
    website = await scan_website_seo_optimization(HttpUrl(url1))
    print(website.model_dump(exclude={"pages"}))  # noqa: T201
    for page in website.pages:
        print(page.model_dump(exclude={"content"}))  # noqa: T201
    print(website.get_seo_log_level_distribution())  # noqa: T201

    with open("tyumen-soft.json", "w", encoding="utf-8") as file:  # noqa: FURB103
        file.write(website.model_dump_json(indent=2, ensure_ascii=False))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
