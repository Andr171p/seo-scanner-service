import logging
from collections.abc import AsyncIterator

from playwright.async_api import Browser, Page
from pydantic import HttpUrl
from tqdm import tqdm

from .stealth import create_new_stealth_context

TIMEOUT = 600
MIN_TEXT_LENGTH = 10
MIN_SCROLL_ATTEMPT = 10
LARGE_PAGE_SCROLL_STEP = 1000

logger = logging.getLogger(__name__)


async def get_current_page(browser: Browser) -> Page:
    """Получает текущую страницу в браузере.

    :param browser: Playwright браузер.
    :return Текущая страница.
    """
    if not browser.contexts:
        context = await create_new_stealth_context(browser)
        return await context.new_page()
    context = browser.contexts[0]
    if not context.pages:
        return await context.new_page()
    return context.pages[-1]


async def iter_pages(browser: Browser, urls: list[HttpUrl]) -> AsyncIterator[Page]:
    """Итерация по Playwright страницам.
    Открывает страницу используя Stealth context.

    :param browser: Текущий Playwright браузер.
    :param urls: URL страниц, которые нужно посетить.
    :return Открытая страница.
    """
    for url in tqdm(urls):
        page = await get_current_page(browser)
        await page.goto(str(url))
        yield page


async def smooth_scroll(page: Page, step: int) -> bool:
    """Выполняет один шаг скролла и возвращает True если достигнут конец"""
    scrolled = await page.evaluate(f"""
        (function() {{
            const startPosition = window.pageYOffset;
            window.scrollBy({{
                top: {step},
                behavior: 'smooth'
            }});
            return window.pageYOffset !== startPosition;
        }})()
    """)
    return not scrolled


async def scroll_page_to_bottom(
        page: Page,
        scroll_delay: int = 1000,
        scroll_step: int = 300,
        max_scroll_attempts: int = 100
) -> None:
    """Плавный скроллинг страницы до её конца.

    :param page: Текущая Playwright страница.
    :param scroll_delay: Задержка между скроллами в миллисекундах.
    :param scroll_step: Размер шага скролла в пикселях (по умолчанию 300 px).
    :param max_scroll_attempts: Максимальное количество попыток скролла страницы.
    """
    scroll_attempts = 0
    last_height = await page.evaluate(
        "document.body.scrollHeight || document.documentElement.scrollHeight"
    )
    while scroll_attempts < max_scroll_attempts:
        scroll_attempts += 1
        reached_end = await smooth_scroll(page, scroll_step)
        if reached_end:
            break
        await page.wait_for_timeout(scroll_delay)
        new_height = await page.evaluate(  # Проверка изменение высоты
            "Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, "
            "document.body.offsetHeight, document.documentElement.offsetHeight, "
            "document.body.clientHeight, document.documentElement.clientHeight)"
        )
        current_position = await page.evaluate(  # Проверка текущей позиции
            "window.pageYOffset + window.innerHeight"
        )
        if (new_height == last_height and
                current_position >= new_height - 10):  # Допуск в 10px
            break
        last_height = new_height
        # Динамическое увеличение шага для длинных страниц
        if scroll_attempts > MIN_SCROLL_ATTEMPT and scroll_step < LARGE_PAGE_SCROLL_STEP:
            scroll_step = min(1000, scroll_step + 100)
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
