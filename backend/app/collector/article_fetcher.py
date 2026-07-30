"""개별 기사 페이지에서 본문 텍스트를 추출한다 (PRD FR-3, 8.2)."""
import httpx
from bs4 import BeautifulSoup

from ..config import REQUEST_TIMEOUT_SECONDS, USER_AGENT

STRIP_TAGS = ["script", "style", "nav", "header", "footer", "aside", "form", "iframe", "noscript"]
MIN_PARAGRAPH_LEN = 40
MIN_BODY_LEN = 200


def fetch_html(url: str) -> bytes | None:
    try:
        resp = httpx.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT_SECONDS,
            follow_redirects=True,
        )
        resp.raise_for_status()
        # resp.text 대신 원본 바이트를 반환: 일부 사이트가 charset을 헤더에 명시하지 않아
        # httpx의 인코딩 추정이 틀리는 경우가 있음. BeautifulSoup(UnicodeDammit)이
        # HTML meta 태그를 보고 인코딩을 다시 판별하도록 함.
        return resp.content
    except httpx.HTTPError:
        return None


def _paragraphs_text(container) -> str:
    parts = []
    for p in container.find_all("p"):
        text = p.get_text(" ", strip=True)
        if len(text) >= MIN_PARAGRAPH_LEN or (not parts and text):
            parts.append(text)
    return "\n".join(parts)


def extract_article_text(html: bytes | str, body_selectors: tuple = ()) -> str | None:
    """소스별 셀렉터를 우선 시도하고, 실패하면 범용 텍스트-밀도 휴리스틱으로 대체."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()

    for selector in body_selectors:
        container = soup.select_one(selector)
        if container:
            text = _paragraphs_text(container)
            if len(text) >= MIN_BODY_LEN:
                return text

    article_tag = soup.find("article")
    if article_tag:
        text = _paragraphs_text(article_tag)
        if len(text) >= MIN_BODY_LEN:
            return text

    best_text = ""
    for cand in soup.find_all(["div", "section", "main"]):
        text = _paragraphs_text(cand)
        if len(text) > len(best_text):
            best_text = text
    if len(best_text) >= MIN_BODY_LEN:
        return best_text

    return None
