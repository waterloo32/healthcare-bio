"""FastAPI API 서버 + 프론트엔드 정적 파일 서빙 (PRD FR-13~16, 8.6)."""
import datetime as dt
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import String, cast, func, or_, select

from .categories import CATEGORY_LABELS_KO, CATEGORY_ORDER, PRIORITY_CATEGORIES
from .db import get_session, init_db
from .models import Article
from .serialize import article_to_dict
from .sources import SOURCES

# 정적 배포(GitHub Pages) 소스가 docs/ 이므로 로컬 개발 서버도 동일 디렉터리를 서빙한다.
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "docs"

app = FastAPI(title="바이오/헬스케어 뉴스 큐레이션 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/articles")
def list_articles(
    category: str | None = None,
    source: str | None = None,
    q: str | None = None,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    session_gen = get_session()
    session = next(session_gen)
    try:
        stmt = select(Article).where(Article.is_duplicate.is_(False))

        if category:
            stmt = stmt.where(
                or_(
                    Article.primary_category == category,
                    cast(Article.secondary_categories, String).like(f'%"{category}"%'),
                )
            )
        if source:
            stmt = stmt.where(Article.source_key == source)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(or_(Article.title.ilike(like), Article.raw_text.ilike(like)))
        if date_from:
            stmt = stmt.where(Article.published_at >= dt.datetime.combine(date_from, dt.time.min))
        if date_to:
            stmt = stmt.where(Article.published_at <= dt.datetime.combine(date_to, dt.time.max))

        total = session.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

        stmt = (
            stmt.order_by(Article.published_at.desc().nulls_last(), Article.collected_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        articles = session.execute(stmt).scalars().all()

        return {
            "items": [article_to_dict(a) for a in articles],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    finally:
        session.close()


@app.get("/api/categories")
def list_categories():
    return [
        {"key": key, "label": CATEGORY_LABELS_KO[key], "priority": key in PRIORITY_CATEGORIES}
        for key in CATEGORY_ORDER
    ]


@app.get("/api/sources")
def list_sources():
    return [{"key": s.key, "name": s.name} for s in SOURCES]


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
