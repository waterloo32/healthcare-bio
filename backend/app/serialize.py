"""Article -> API/정적 JSON 공통 직렬화 (main.py API와 export_static.py가 공유)."""
from .categories import CATEGORY_LABELS_KO
from .models import Article


def article_to_dict(article: Article) -> dict:
    return {
        "id": article.id,
        "source_key": article.source_key,
        "source_name": article.source_name,
        "source_url": article.source_url,
        "title": article.title,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "collected_at": article.collected_at.isoformat(),
        "summary": article.summary,
        "summary_failed": article.summary_failed,
        "primary_category": article.primary_category,
        "primary_category_label": CATEGORY_LABELS_KO.get(article.primary_category, article.primary_category),
        "secondary_categories": article.secondary_categories or [],
        "secondary_category_labels": [
            CATEGORY_LABELS_KO.get(c, c) for c in (article.secondary_categories or [])
        ],
        "classification_confidence": article.classification_confidence,
    }
