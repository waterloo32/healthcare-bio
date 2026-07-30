"""SQLite -> 정적 JSON 내보내기 (GitHub Pages 배포용).

GitHub Actions가 run_collect.py 실행 뒤 이 스크립트를 실행해 docs/data/*.json을
갱신하고, 그 결과를 저장소에 커밋한다. 프론트엔드(docs/app.js)는 이 JSON을 그대로 읽는다.

사용법:
    .venv\\Scripts\\python.exe backend\\export_static.py
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import select  # noqa: E402

from app.config import BASE_DIR  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import Article  # noqa: E402
from app.serialize import article_to_dict  # noqa: E402

OUTPUT_DIR = BASE_DIR / "docs" / "data"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    session = SessionLocal()
    try:
        articles = (
            session.execute(
                select(Article)
                .where(Article.is_duplicate.is_(False))
                .order_by(Article.published_at.desc().nulls_last(), Article.collected_at.desc())
            )
            .scalars()
            .all()
        )
        data = [article_to_dict(a) for a in articles]
    finally:
        session.close()

    (OUTPUT_DIR / "articles.json").write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )
    (OUTPUT_DIR / "meta.json").write_text(
        json.dumps(
            {"generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "count": len(data)},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"Exported {len(data)} articles to {OUTPUT_DIR / 'articles.json'}")


if __name__ == "__main__":
    main()
