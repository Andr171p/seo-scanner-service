from typing import Self

from collections import Counter
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, NonNegativeFloat, NonNegativeInt


class _Entity(BaseModel):
    id: UUID = Field(default_factory=uuid4)

    model_config = ConfigDict(from_attributes=True)


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


class LogLevelDistribution(BaseModel):
    """Распределение SEO логов на сайте"""
    critical: NonNegativeInt = 0
    error: NonNegativeInt = 0
    warning: NonNegativeInt = 0
    info: NonNegativeInt = 0
    optimal: NonNegativeInt = 0
    good: NonNegativeInt = 0
    great: NonNegativeInt = 0

    @classmethod
    def from_counter(cls, counter: Counter) -> Self:
        return cls(**{level: counter[level] for level in LogLevel})


class Website(_Entity):
    """Отсканированный web-сайт"""
    url: HttpUrl
    seo_score: NonNegativeFloat = Field(ge=0, le=100)
    page_count: NonNegativeInt
    pages: list[Page]

    @classmethod
    def from_pages(cls, url: HttpUrl, pages: list[Page]) -> Self:
        return cls(
            url=url,
            seo_score=cls.compute_seo_score(pages),
            page_count=len(pages),
            pages=pages,
        )

    @staticmethod
    def compute_seo_score(pages: list[Page]) -> NonNegativeFloat:
        """Вычисляет оценку SEO оптимизации сайта"""
        # Собираем все логи
        all_logs = [log for page in pages for log in page.seo_logs]
        if not all_logs:
            return 100.0
        # Группируем по "хорошим" и "плохим" логам
        positive_levels = {LogLevel.OPTIMAL, LogLevel.GOOD, LogLevel.GREAT, LogLevel.INFO}
        negative_levels = {LogLevel.CRITICAL, LogLevel.ERROR, LogLevel.WARNING}
        positive_count = sum(1 for log in all_logs if log.level in positive_levels)
        negative_count = sum(1 for log in all_logs if log.level in negative_levels)  # noqa: F841
        total_count = len(all_logs)
        # Вычисляем процент положительных логов
        positive_ratio = positive_count / total_count if total_count > 0 else 0
        # Штрафуем за критические ошибки сильнее
        critical_ratio = sum(1 for log in all_logs if log.level == LogLevel.CRITICAL) / total_count
        # Формула расчета
        base_score = positive_ratio * 100
        critical_penalty = critical_ratio * 50  # Сильный штраф за критические ошибки
        final_score = base_score - critical_penalty
        return max(0.0, min(100.0, final_score))

    def get_seo_log_level_distribution(self) -> LogLevelDistribution:
        """Получение распределение SEO логов (замечаний) по их уровням"""
        levels = (seo_log.level for page in self.pages for seo_log in page.seo_logs)
        counter = Counter(levels)
        return LogLevelDistribution.from_counter(counter)

    def get_pages_by_log_level(self, level: LogLevel) -> list[Page]:
        """Получение страниц содержащих лог указанного уровня"""
        return [
            page for page in self.pages
            if any(seo_log.level == level for seo_log in page.seo_logs)
        ]
