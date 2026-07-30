"""RSS 기반 수집기 (PRD FR-1~6, 8.2)."""
import calendar
import datetime as dt
import logging
import time

import feedparser
import httpx
from bs4 import BeautifulSoup

from ..config import (
    MAX_ARTICLES_PER_SOURCE_PER_RUN,
    REQUEST_DELAY_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    USER_AGENT,
)
from ..sources import Source
from . import robots
from .article_fetcher import extract_article_text, fetch_html

logger = logging.getLogger(__name__)


class SourceCollectionResult:
    def __init__(self, source_key: str):
        self.source_key = source_key
        self.status = "ok"  # ok | failed | skipped_robots
        self.fetched_count = 0
        self.new_count = 0
        self.error_message: str | None = None
        self.articles: list[dict] = []


def _parsed_time_to_datetime(struct_time) -> dt.datetime | None:
    if not struct_time:
        return None
    return dt.datetime.utcfromtimestamp(calendar.timegm(struct_time))


def _clean_feed_text(raw: str) -> str:
    """일부 소스(Fierce 계열)의 RSS 필드에 HTML 태그/엔티티가 그대로 섞여 나오는 문제 방지."""
    if not raw:
        return raw
    text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
    return " ".join(text.split())


def collect_source(source: Source, existing_urls: set[str]) -> SourceCollectionResult:
    result = SourceCollectionResult(source.key)

    if not robots.can_fetch(source.rss_url):
        result.status = "skipped_robots"
        result.error_message = "robots.txt disallows RSS feed path"
        logger.warning("[%s] robots.txt disallows %s", source.key, source.rss_url)
        return result

    try:
        resp = httpx.get(
            source.rss_url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT_SECONDS,
            follow_redirects=True,
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        result.status = "failed"
        result.error_message = f"RSS fetch error: {exc}"
        logger.error("[%s] RSS fetch failed: %s", source.key, exc)
        return result

    feed = feedparser.parse(resp.content)
    if feed.bozo and not feed.entries:
        result.status = "failed"
        result.error_message = f"Feed parse error: {feed.bozo_exception}"
        logger.error("[%s] feed parse failed: %s", source.key, feed.bozo_exception)
        return result

    entries = feed.entries[:MAX_ARTICLES_PER_SOURCE_PER_RUN]
    result.fetched_count = len(entries)

    for entry in entries:
        link = entry.get("link")
        raw_title = entry.get("title")
        if not link or not raw_title:
            continue
        if link in existing_urls:
            continue  # FR-4: 동일 URL 중복

        title = _clean_feed_text(raw_title)

        published_at = _parsed_time_to_datetime(
            entry.get("published_parsed") or entry.get("updated_parsed")
        )
        feed_summary = _clean_feed_text(entry.get("summary", ""))

        raw_text = None
        raw_text_failed = True
        if robots.can_fetch(link):
            time.sleep(REQUEST_DELAY_SECONDS)  # 8.2: 요청 간 지연
            html = fetch_html(link)
            if html:
                raw_text = extract_article_text(html, source.body_selectors)
                raw_text_failed = raw_text is None
        else:
            logger.info("[%s] robots.txt disallows article page %s", source.key, link)

        if not raw_text:
            # FR-12 대비: RSS 자체 요약(설명)을 원문 텍스트 대체로 사용
            raw_text = feed_summary or None

        result.articles.append(
            {
                "source_key": source.key,
                "source_name": source.name,
                "source_url": link,
                "title": title,
                "published_at": published_at,
                "raw_text": raw_text,
                "raw_text_failed": raw_text_failed,
            }
        )
        result.new_count += 1

    return result
