"""규칙 기반 카테고리 분류기 (PRD FR-7~9, 8.3).

1차: 제목/본문 키워드 사전 매칭. 제목 매칭에 더 높은 가중치를 준다.
2차(LLM 보강)는 MVP 범위 밖(PRD 8.3의 "선택" 항목) — 필요 시 이 모듈의
classify() 반환값(신뢰도 점수)을 기준으로 애매한 건만 골라 후처리하면 된다.
"""
import re

from .categories import (
    CATEGORY_INVESTMENT_MA,
    CATEGORY_MARKETING,
    CATEGORY_NEW_BUSINESS,
    CATEGORY_ORDER,
    CATEGORY_OTHER,
    CATEGORY_REGULATORY,
    CATEGORY_RND_CLINICAL,
    CATEGORY_SERVICE_LAUNCH,
)

TITLE_WEIGHT = 3
BODY_WEIGHT = 1
SECONDARY_MIN_SCORE = 2
MAX_SECONDARY = 2

KEYWORDS: dict[str, list[str]] = {
    CATEGORY_MARKETING: [
        "campaign", "branding", "rebrand", "marketing", "advertising",
        "direct-to-consumer", "dtc", "influencer", "sponsorship", "ad campaign",
        "brand strategy", "brand awareness",
    ],
    CATEGORY_NEW_BUSINESS: [
        "new business unit", "business unit", "restructuring", "reorganization",
        "strategic partnership", "joint venture", "expands into", "enters the market",
        "diversif", "strategy shift", "expansion into", "new division",
    ],
    CATEGORY_SERVICE_LAUNCH: [
        "launches", "launch of", "unveils", "rolls out", "debuts", "introduces",
        "platform", "digital health", "telehealth", "mobile app", "new feature",
        "upgrades platform", "service update",
    ],
    CATEGORY_RND_CLINICAL: [
        "clinical trial", "phase 1", "phase 2", "phase 3", "phase i", "phase ii",
        "phase iii", "trial results", "study shows", "preclinical", "topline data",
        "data readout", "published in", "research finds",
    ],
    CATEGORY_INVESTMENT_MA: [
        "acquire", "acquisition", "merger", "merges with", "ipo", "series a",
        "series b", "series c", "funding round", "raises $", "venture capital",
        "buyout", "takes stake", "to acquire",
    ],
    CATEGORY_REGULATORY: [
        "fda approv", "fda clearance", "fda grants", "regulatory", "crl",
        "complete response letter", "ema approv", "warning letter", "fda guidance",
        "label expansion", "fda rejects",
    ],
}


def _count_hits(pattern_list: list[str], text: str) -> int:
    count = 0
    for kw in pattern_list:
        count += len(re.findall(re.escape(kw), text))
    return count


def classify(title: str, raw_text: str | None) -> tuple[str, list[str], float]:
    """Returns (primary_category, secondary_categories, confidence)."""
    title_lower = (title or "").lower()
    body_lower = (raw_text or "").lower()

    scores: dict[str, int] = {}
    for category, keywords in KEYWORDS.items():
        score = (
            _count_hits(keywords, title_lower) * TITLE_WEIGHT
            + _count_hits(keywords, body_lower) * BODY_WEIGHT
        )
        if score > 0:
            scores[category] = score

    if not scores:
        return CATEGORY_OTHER, [], 0.2

    # 동점이면 카테고리 노출 우선순위(CATEGORY_ORDER)가 앞선 쪽을 primary로 선택 (FR-9)
    ordered_categories = sorted(
        scores.items(),
        key=lambda item: (-item[1], CATEGORY_ORDER.index(item[0])),
    )
    primary_category = ordered_categories[0][0]
    top_score = ordered_categories[0][1]

    secondary = [
        cat for cat, score in ordered_categories[1:]
        if score >= SECONDARY_MIN_SCORE
    ][:MAX_SECONDARY]

    total_score = sum(scores.values())
    confidence = round(min(0.95, top_score / total_score), 2) if total_score else 0.2

    return primary_category, secondary, confidence
