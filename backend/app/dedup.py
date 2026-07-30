"""중복 기사 병합 (PRD FR-4).

URL 완전 일치는 수집 단계(rss_collector)에서 이미 걸러진다.
여기서는 서로 다른 매체가 같은 사건을 보도했을 때 제목 유사도로 묶어준다.
"""
import datetime as dt
import re
import uuid
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import DEDUP_WINDOW_DAYS, TITLE_SIMILARITY_THRESHOLD
from .models import Article

_SITE_SUFFIX_RE = re.compile(r"\s*[\|\-–—]\s*[A-Za-z0-9 .]{2,40}$")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9 ]+")
_WS_RE = re.compile(r"\s+")


def normalize_title(title: str) -> str:
    text = title.lower()
    text = _SITE_SUFFIX_RE.sub("", text)
    text = _NON_ALNUM_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    return text


def _title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def assign_dedup_group(session: Session, normalized_title: str, published_at: dt.datetime | None) -> tuple[str, bool]:
    """가장 유사한 기존 기사를 찾아 그룹 ID를 재사용한다.

    Returns:
        (dedup_group_id, is_duplicate)
    """
    since = dt.datetime.utcnow() - dt.timedelta(days=DEDUP_WINDOW_DAYS)
    candidates = session.execute(
        select(Article).where(Article.collected_at >= since)
    ).scalars().all()

    best_match: Article | None = None
    best_ratio = 0.0
    for candidate in candidates:
        ratio = _title_similarity(normalized_title, candidate.normalized_title)
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = candidate

    if best_match and best_ratio >= TITLE_SIMILARITY_THRESHOLD:
        group_id = best_match.dedup_group_id or f"g-{uuid.uuid4().hex[:12]}"
        best_match.dedup_group_id = group_id
        return group_id, True

    return f"g-{uuid.uuid4().hex[:12]}", False
