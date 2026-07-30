"""추출 요약기 (PRD 8.4 옵션 A — MVP 권장안, 무비용).

주의(PRD FR-11 대비 알려진 한계, 12절 오픈 이슈 #1과 동일):
추출 요약은 원문 문장을 그대로 골라 붙이는 방식이라 "재구성"을 완전히 만족하지 못한다.
품질이 부족하면 PRD 8.4 옵션 C(LLM 보강)를 소량 예산으로 병행 검토할 것.
"""
import re

from .config import SUMMARY_SENTENCE_COUNT

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "with",
    "at", "by", "from", "up", "about", "into", "over", "after", "is", "are",
    "was", "were", "be", "been", "being", "it", "its", "this", "that", "as",
    "has", "have", "had", "will", "would", "could", "should", "can", "not",
    "than", "then", "so", "if", "which", "who", "whom", "their", "they",
    "he", "she", "his", "her", "we", "our", "you", "your", "said", "says",
}

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
_WORD_RE = re.compile(r"[a-zA-Z']+")

MIN_SENTENCE_LEN = 25


def _split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    sentences = _SENTENCE_SPLIT_RE.split(text)
    return [s.strip() for s in sentences if len(s.strip()) >= MIN_SENTENCE_LEN]


def _word_frequencies(sentences: list[str]) -> dict[str, float]:
    freq: dict[str, int] = {}
    for sentence in sentences:
        for word in _WORD_RE.findall(sentence.lower()):
            if word in _STOPWORDS or len(word) < 3:
                continue
            freq[word] = freq.get(word, 0) + 1
    if not freq:
        return {}
    max_freq = max(freq.values())
    return {word: count / max_freq for word, count in freq.items()}


def summarize(raw_text: str | None, title: str = "") -> tuple[str | None, bool]:
    """Returns (summary, summary_failed)."""
    if not raw_text or len(raw_text.strip()) < MIN_SENTENCE_LEN:
        return None, True

    sentences = _split_sentences(raw_text)
    if not sentences:
        # 문장 분리가 안 되면 첫 문단(원문 앞부분)을 그대로 대체 표시 (FR-12)
        fallback = raw_text.strip()[:400]
        return (fallback if fallback else None), True

    if len(sentences) <= SUMMARY_SENTENCE_COUNT:
        return " ".join(sentences), False

    weights = _word_frequencies(sentences)

    scored = []
    for idx, sentence in enumerate(sentences):
        words = [w.lower() for w in _WORD_RE.findall(sentence) if len(w) >= 3]
        if not words:
            continue
        word_score = sum(weights.get(w, 0) for w in words) / len(words)
        position_bonus = 1.0 if idx == 0 else (0.4 if idx == 1 else 0.0)
        scored.append((idx, word_score + position_bonus))

    if not scored:
        return " ".join(sentences[:SUMMARY_SENTENCE_COUNT]), False

    top_indices = {
        idx for idx, _ in sorted(scored, key=lambda x: x[1], reverse=True)[:SUMMARY_SENTENCE_COUNT]
    }
    ordered = [sentences[i] for i in sorted(top_indices)]
    return " ".join(ordered), False
