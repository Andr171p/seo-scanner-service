from typing import Final

import logging
import re

from bs4 import BeautifulSoup
from playwright.async_api import Page

from ..schemas import LogLevel, SEOLog
from .nlp import compare_texts
from .parsers import extract_markdown_text

logger = logging.getLogger(__name__)

OPTIMAL_TITLE_LENGTH = 55
OPTIMAL_TITLE_DELTA = 10
SEMANTIC_TAGS: Final[list[str]] = [
    "header", "nav", "main", "article", "section", "aside", "footer"
]
MAX_META_DESCRIPTION_LENGTH = 160
MIN_META_DESCRIPTION_LENGTH = 120
SHORT_RELEVANCE_SCORE, CRITICAL_RELEVANCE_SCORE = 0.5, 0.3
GREAT_SEMANTIC_TAG_COUNT = 4


def check_title(soup: BeautifulSoup) -> list[SEOLog]:
    """Проверка тега <title>"""
    findings: list[SEOLog] = []
    tag = soup.find("title")
    if not tag:
        return [SEOLog(
            level=LogLevel.CRITICAL,
            message="Отсутсвует тэг <title>!",
            category="title",
            element="title"
        )]
    text = tag.get_text().strip()
    if not text:
        return [SEOLog(
            level=LogLevel.CRITICAL,
            message="Тег <title> пустой!",
            category="title",
            element="title"
        )]
    if len(text) < OPTIMAL_TITLE_LENGTH - OPTIMAL_TITLE_DELTA:
        findings.append(SEOLog(
            level=LogLevel.WARNING,
            message=f"""Title слишком короткий ({len(text)} символов)!
            Оптимальная длина от {OPTIMAL_TITLE_LENGTH - OPTIMAL_TITLE_DELTA}
            до {OPTIMAL_TITLE_LENGTH + OPTIMAL_TITLE_DELTA}.""",
            category="title",
            element="title"
        ))
    elif len(text) > OPTIMAL_TITLE_LENGTH + OPTIMAL_TITLE_DELTA:
        findings.append(SEOLog(
            level=LogLevel.WARNING,
            message=f"""Title слишком длинный ({len(text)} символов)!
            Оптимальная длина от {OPTIMAL_TITLE_LENGTH - OPTIMAL_TITLE_DELTA}
            до {OPTIMAL_TITLE_LENGTH + OPTIMAL_TITLE_DELTA}.""",
            category="title",
            element="title"
        ))
    else:
        findings.append(SEOLog(
            level=LogLevel.OPTIMAL,
            message=f"Оптимальная длина title ({len(text)} символов)",
            category="title",
            element="title"
        ))
    return findings


def check_meta_description(soup: BeautifulSoup) -> list[SEOLog]:
    """Проверка meta описания страницы"""
    findings: list[SEOLog] = []
    meta_description = soup.find("meta", attrs={"name": "description"})
    if not meta_description:
        return [SEOLog(
            level=LogLevel.CRITICAL,
            message="Отсутствует meta-описание",
            category="meta",
            element="meta"
        )]
    content = meta_description.get("content", "").strip()
    if not content:
        return [SEOLog(
            level=LogLevel.CRITICAL,
            message="Пустое meta-описание",
            category="meta",
            element="meta"
        )]
    if len(content) > MAX_META_DESCRIPTION_LENGTH:
        findings.append(SEOLog(
            level=LogLevel.WARNING,
            message=f"Meta-описание слишком длинное ({len(content)} символов)! "
            f"Рекомендуемая длина от {MIN_META_DESCRIPTION_LENGTH} "
            f"до {MAX_META_DESCRIPTION_LENGTH} символов.",
            category="meta",
            element="meta"
        ))
    elif MIN_META_DESCRIPTION_LENGTH <= len(content) <= MIN_META_DESCRIPTION_LENGTH:
        findings.append(SEOLog(
            level=LogLevel.OPTIMAL,
            message=f"Оптимальная длина meta-описания ({len(content)} символов)",
            category="meta",
            element="meta"
        ))
    else:
        findings.append(SEOLog(
            level=LogLevel.WARNING,
            message=f"Meta-описание слишком короткое ({len(content)} символов)! "
            f"Рекомендуемая длина от {MIN_META_DESCRIPTION_LENGTH} "
            f"до {MAX_META_DESCRIPTION_LENGTH}",
            category="meta",
            element="meta"
        ))
    return findings


def check_heading(soup: BeautifulSoup) -> list[SEOLog]:
    """Проверка структуры заголовков"""
    findings: list[SEOLog] = []
    h1_tags = soup.find_all("h1")
    if len(h1_tags) == 0:
        findings.append(SEOLog(
            level=LogLevel.CRITICAL,
            message="Отсутствует тег H1",
            category="heading",
            element="h1"
        ))
    elif len(h1_tags) > 1:
        findings.append(SEOLog(
            level=LogLevel.WARNING,
            message=f"Найдено {len(h1_tags)} тегов H1. Рекомендуется только один H1 на страницу",
            category="heading",
            element="h1"
        ))
    elif len(h1_tags) == 1:
        findings.append(SEOLog(
            level=LogLevel.OPTIMAL,
            message="Оптимальное количество H1 тегов (ровно 1)",
            category="heading",
            element="h1"
        ))
    headings = soup.find_all(re.compile(r"^h[1-6]$"))
    last_level = 0
    hierarchy_correct = True
    for heading in headings:
        level = int(heading.name[1])
        if level > last_level + 1:
            findings.append(SEOLog(
                level=LogLevel.WARNING,
                message=f"Нарушена иерархия заголовков: H{level} после H{last_level}",
                category="heading",
                element=heading.name
            ))
            hierarchy_correct = False
        last_level = level
    if hierarchy_correct:
        findings.append(SEOLog(
            level=LogLevel.GREAT,
            message="Правильная иерархия заголовков",
            category="heading",
            element=f"h1-h{last_level}"
        ))
    return findings


def check_images(soup: BeautifulSoup) -> list[SEOLog]:
    """Проверка изображений"""
    findings: list[SEOLog] = []
    images = soup.find_all("img")
    if not images:
        return [SEOLog(
            level=LogLevel.INFO,
            message="На странице нет изображений",
            category="image",
            element="img"
        )]
    images_with_alt = 0  # Количество изображений с описанием
    images_without_description = 0  # Изображения без описания
    for image in images:
        alt, src = image.get("alt", ""), image.get("src", "")
        if not alt:
            findings.append(SEOLog(
                level=LogLevel.WARNING,
                message="Изображение без атрибута 'alt'",
                category="image",
                element="img"
            ))
        else:
            images_with_alt += 1
        if (
                (src and any(
                    type in src.lower()
                    for type in ["image", "img", "picture"])  # noqa: A001
                )
                and not any(
                    extension in src.lower()
                    for extension in [".jpg", ".jpeg", ".png", ".webp"]
            )
        ):
            images_without_description += 1
    if images_without_description > 0:
        findings.append(SEOLog(
            level=LogLevel.WARNING,
            message=f"В названии файлов {images_without_description}"
            " изображений нет описания!",
            category="image",
            element="img"
        ))
    return findings


def check_semantic_structure(soup: BeautifulSoup) -> list[SEOLog]:
    """Проверка семантической структуры"""
    findings: list[SEOLog] = []
    used_semantic_tags: list[str] = []
    for semantic_tag in SEMANTIC_TAGS:
        elements = soup.find_all(semantic_tag)
        if not elements:
            findings.append(SEOLog(
                level=LogLevel.INFO,
                message=f"Не используется сематический тег <{semantic_tag}>",
                category="semantic",
                element=semantic_tag
            ))
        else:
            used_semantic_tags.append(semantic_tag)
    if used_semantic_tags:
        findings.append(SEOLog(
            level=LogLevel.GOOD,
            message=f"Используются семантические теги: {', '.join(used_semantic_tags)}",
            category="semantic",
            element=";".join(used_semantic_tags)
        ))
    if len(used_semantic_tags) > GREAT_SEMANTIC_TAG_COUNT:
        findings.append(SEOLog(
            level=LogLevel.GREAT,
            message="Отличное использование семантической разметки",
            category="semantic",
            element=";".join(used_semantic_tags)
        ))
    return findings


def check_meta_and_body_relevance(soup: BeautifulSoup) -> list[SEOLog]:
    """Проверяет сематическое соответствие между meta-описанием и контентом на странице"""
    findings: list[SEOLog] = []
    meta_description = soup.find("meta", attrs={"name": "description"})
    if not meta_description:
        return findings
    content = meta_description.get("content", "").strip()
    body = soup.find("body")
    if body is None:
        return [SEOLog(
            level=LogLevel.CRITICAL,
            message="Страница с пустым контентом",
            category="semantic",
            element="body"
        )]
    text = extract_markdown_text(soup)
    similarity_score = compare_texts(content, text)
    if CRITICAL_RELEVANCE_SCORE < similarity_score < SHORT_RELEVANCE_SCORE:
        findings.append(SEOLog(
            level=LogLevel.INFO,
            message="Соответствие meta-описания к контенту страницы, "
            f"Релевантность: {similarity_score * 100:.1f}%",
            category="semantic",
            element="body"
        ))
    elif similarity_score <= CRITICAL_RELEVANCE_SCORE:
        findings.append(SEOLog(
            level=LogLevel.WARNING,
            message="Низкое соответствие meta-описания к контенту страницы, "
            f"Релевантность: {similarity_score * 100:.1f}%",
            category="semantic",
            element="body"
        ))
    else:
        findings.append(SEOLog(
            level=LogLevel.GREAT,
            message="Высокое описание meta-описания к контенту страницы "
            f"Релевантность: ({similarity_score * 100:.1f}%)",
            category="semantic",
            element="body"
        ))
    return findings


async def lint_page(page: Page) -> list[SEOLog]:
    """Выполняет SEO линтинг страницы. Возвращает найденные замечания.

    :param page: Объект Playwright страницы.
    :return Список найденных SEO замечаний страницы.
    """
    await page.wait_for_selector("body:not(:empty)")
    content = await page.content()
    soup = BeautifulSoup(content, "html.parser")
    return [
        *check_title(soup),
        *check_meta_description(soup),
        *check_heading(soup),
        *check_images(soup),
        *check_semantic_structure(soup),
        *check_meta_and_body_relevance(soup),
    ]
