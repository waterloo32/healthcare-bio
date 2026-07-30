import datetime as dt

from pydantic import BaseModel, ConfigDict

from .categories import CATEGORY_LABELS_KO, PRIORITY_CATEGORIES


class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_name: str
    source_url: str
    title: str
    published_at: dt.datetime | None
    collected_at: dt.datetime
    summary: str | None
    summary_failed: bool
    primary_category: str
    secondary_categories: list[str]
    classification_confidence: float

    @property
    def primary_category_label(self) -> str:
        return CATEGORY_LABELS_KO.get(self.primary_category, self.primary_category)


class ArticleListOut(BaseModel):
    items: list[dict]
    total: int
    page: int
    page_size: int


class CategoryOut(BaseModel):
    key: str
    label: str
    priority: bool


class SourceOut(BaseModel):
    key: str
    name: str
