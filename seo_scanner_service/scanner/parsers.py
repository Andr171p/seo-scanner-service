import logging

import html_to_markdown
from bs4 import BeautifulSoup
from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from ..schemas import PageMeta

logger = logging.getLogger(__name__)

MIN_TEXT_LENGTH = 10


def extract_markdown_text(soup: BeautifulSoup) -> str:
    """Извлекает текст со страницы в формате Markdown"""
    for element in soup.find_all({
        "script", "style", "svg", "path", "meta", "link", "nav", "footer", "header"
    }):
        element.decompose()
    body = soup.find("body")
    if body is None:
        return ""
    # Основные семантические элементы в порядке важности
    elements = body.find_all({"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "td", "th"})
    return "\n".join([html_to_markdown.convert(str(element)) for element in elements])


async def extract_page_text(page: Page) -> str:
    """Извлекает весь текст с текущей страницы из body.

    :param page: Текущая Playwright страница.
    :return: Текстовый контент страницы.
    """
    try:
        await page.wait_for_load_state("networkidle", timeout=5_000)
    except PlaywrightTimeoutError:
        # Fallback в случае неудачного ожидания загрузки страницы
        logger.warning("Networkidle timeout for %s, using domcontentloaded", page.url)
        await page.wait_for_load_state("domcontentloaded")
    content = await page.content()
    soup = BeautifulSoup(content, "html.parser")
    return extract_markdown_text(soup)


async def extract_page_meta(page: Page) -> PageMeta:
    """Извлекает мета-данные страницы.

    :param page: Текущая Playwright страница.
    :return: Извлечённые мета-данные страницы.
    """
    title = await page.title()
    description_element = await page.query_selector("meta[name='description']")
    if description_element is None:
        return PageMeta(title=title, description="")
    description = await description_element.get_attribute("content")
    return PageMeta(title=title, description=description)
