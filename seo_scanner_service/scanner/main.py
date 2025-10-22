import logging

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright
from pydantic import HttpUrl

from ..schemas import Page, PageContent, Website
from .linting import lint_page
from .parsers import extract_page_meta, extract_page_text
from .performance import measure_page_rendering_time
from .tree import PRIORITY_KEYWORDS, build_site_tree, extract_key_pages
from .utils import iter_pages, scroll_page_to_bottom

logger = logging.getLogger(__name__)


async def scan_website_seo_optimization(url: HttpUrl) -> Website:
    """Сканирует SEO оптимизацию сайта"""
    tree = build_site_tree(url)
    urls = extract_key_pages(tree, list(PRIORITY_KEYWORDS), max_result=15)
    scanned_pages: list[Page] = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        async for page in iter_pages(browser, urls):
            try:
                rendering_info = await measure_page_rendering_time(page, page.url)
                await scroll_page_to_bottom(page)
                seo_logs = await lint_page(page)
                meta = await extract_page_meta(page)
                text = await extract_page_text(page)
                scanned_pages.append(Page(
                    url=HttpUrl(page.url),
                    rendering_time=rendering_info.dom_content_loaded / 1000,
                    seo_logs=seo_logs,
                    content=PageContent(meta=meta, text=text),
                ))
            except (PlaywrightTimeoutError, TimeoutError):
                logger.warning("Very long page loading time, skip to net page")
                continue
    return Website.from_pages(url, scanned_pages)
