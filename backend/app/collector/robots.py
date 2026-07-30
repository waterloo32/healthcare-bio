"""robots.txt 준수 확인 (PRD FR-6)."""
import urllib.robotparser
from urllib.parse import urlparse

import httpx

from ..config import REQUEST_TIMEOUT_SECONDS, USER_AGENT

_cache: dict[str, urllib.robotparser.RobotFileParser] = {}


def _robots_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"


def _get_parser(url: str) -> urllib.robotparser.RobotFileParser:
    robots_url = _robots_url(url)
    if robots_url in _cache:
        return _cache[robots_url]

    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
    try:
        resp = httpx.get(
            robots_url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT_SECONDS,
            follow_redirects=True,
        )
        if resp.status_code >= 400:
            # robots.txt가 없으면 관례상 전체 허용으로 간주
            parser.parse([])
        else:
            parser.parse(resp.text.splitlines())
    except httpx.HTTPError:
        # 접근 실패 시 보수적으로 허용하지 않음 대신, 상위 레벨에서 재시도/로그 처리하도록
        # 여기서는 "판단 불가"를 표시하기 위해 빈 규칙(전체 허용)으로 두지 않고 예외를 올린다.
        raise

    _cache[robots_url] = parser
    return parser


def can_fetch(url: str) -> bool:
    """해당 URL을 USER_AGENT로 크롤링해도 되는지 확인. 판단 불가 시 False(보수적)."""
    try:
        parser = _get_parser(url)
    except httpx.HTTPError:
        return False
    return parser.can_fetch(USER_AGENT, url)
