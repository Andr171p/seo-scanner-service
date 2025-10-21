from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, NonNegativeFloat, NonNegativeInt


class _Entity(BaseModel):
    id: UUID = Field(default_factory=uuid4)

    model_config = ConfigDict(from_attributes=True)


class Site(_Entity):
    url: HttpUrl
    page_count: NonNegativeInt


class LogLevel(StrEnum):
    """Уровни значимости SEO замечания"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    OPTIMAL = "optimal"
    GOOD = "good"
    GREAT = "great"


class SEOLog(BaseModel):
    """Обнаружение на странице связанные с SEO оптимизацией

    Attributes:
        level: Значимость замечания.
        message: Человеко-читаемое сообщение.
        category: Категория к которой относится замечание, например: 'heading', 'title', ...
        element: HTML элемент страницы к которому относится замечание.
    """
    level: LogLevel
    message: str
    category: str
    element: str


class PageMeta(BaseModel):
    """Meta-контент на странице (находиться в head)"""
    title: str
    description: str


class PageContent(BaseModel):
    """Текстовый контент на странице"""
    meta: PageMeta
    text: str = ""


class Page(_Entity):
    """Результат SEO сканирования страницы"""
    url: HttpUrl
    rendering_time: NonNegativeFloat
    seo_logs: list[SEOLog]
    content: PageContent
