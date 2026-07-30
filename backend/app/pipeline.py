"""수집 -> 파싱 -> dedup -> 분류 -> 요약 -> 저장 파이프라인 (PRD 8.1 전체 구성)."""
import datetime as dt
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from .classifier import classify
from .collector.rss_collector import collect_source
from .dedup import assign_dedup_group, normalize_title
from .models import Article, CollectionRun, SourceRunLog
from .sources import SOURCES
from .summarizer import summarize

logger = logging.getLogger(__name__)


def run_collection_cycle(session: Session) -> CollectionRun:
    run = CollectionRun(started_at=dt.datetime.utcnow())
    session.add(run)
    session.flush()  # run.id 확보

    existing_urls = set(session.execute(select(Article.source_url)).scalars().all())

    for source in SOURCES:
        log_entry = SourceRunLog(run_id=run.id, source_key=source.key, status="ok")
        try:
            result = collect_source(source, existing_urls)
        except Exception as exc:  # noqa: BLE001 - 소스 하나 실패가 전체 배치를 막으면 안 됨 (FR-5)
            logger.exception("[%s] 수집 중 예외 발생", source.key)
            log_entry.status = "failed"
            log_entry.error_message = str(exc)
            session.add(log_entry)
            continue

        log_entry.status = result.status
        log_entry.fetched_count = result.fetched_count
        log_entry.new_count = result.new_count
        log_entry.error_message = result.error_message
        session.add(log_entry)

        for article_data in result.articles:
            if article_data["source_url"] in existing_urls:
                continue

            norm_title = normalize_title(article_data["title"])
            dedup_group_id, is_duplicate = assign_dedup_group(
                session, norm_title, article_data["published_at"]
            )

            primary_category, secondary_categories, confidence = classify(
                article_data["title"], article_data["raw_text"]
            )
            summary, summary_failed = summarize(
                article_data["raw_text"], article_data["title"]
            )

            article = Article(
                source_key=article_data["source_key"],
                source_name=article_data["source_name"],
                source_url=article_data["source_url"],
                title=article_data["title"],
                normalized_title=norm_title,
                published_at=article_data["published_at"],
                raw_text=article_data["raw_text"],
                raw_text_failed=article_data["raw_text_failed"],
                summary=summary,
                summary_failed=summary_failed,
                primary_category=primary_category,
                secondary_categories=secondary_categories,
                classification_confidence=confidence,
                dedup_group_id=dedup_group_id,
                is_duplicate=is_duplicate,
            )
            session.add(article)
            existing_urls.add(article_data["source_url"])

        session.commit()
        logger.info(
            "[%s] status=%s fetched=%d new=%d",
            source.key, log_entry.status, log_entry.fetched_count, log_entry.new_count,
        )

    run.finished_at = dt.datetime.utcnow()
    session.commit()
    return run
