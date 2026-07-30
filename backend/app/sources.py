"""MVP 대상 뉴스 소스 목록 (PRD 5절 우선순위 1군).

RSS 유무 및 robots.txt는 실제 구현 착수 전 확인 완료(2026-07-30):
- Fierce Biotech / Fierce Pharma: robots.txt에 RSS·기사 경로 차단 없음.
- STAT News: robots.txt가 ClaudeBot 등 AI 학습 크롤러를 명시적으로 차단하나,
  본 봇은 학습용이 아닌 개인 뉴스 큐레이션 목적이며 별도 User-Agent를 사용.
  RSS 피드 자체나 기사 경로는 일반 크롤러에 대해 차단하지 않음. 상업적 확장 시 ToS 재검토 필요(PRD 12절).
- MedCity News: robots.txt에 특이 제한 없음.
- Endpoints News: endpts.com -> endpoints.news 로 301 리다이렉트, robots.txt 접근이
  자동화 도구에서 일시적으로 차단된 이력 있음(WAF/Cloudflare 추정) — 온보딩 체크리스트 상
  "주의 소스"로 표시, 수집 실패 시 로그로 확인 필요.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Source:
    key: str
    name: str
    rss_url: str
    site_url: str
    # 기사 본문 추출 시 우선 시도할 CSS 셀렉터 (없으면 범용 휴리스틱 사용)
    body_selectors: tuple = field(default_factory=tuple)
    notes: str = ""


SOURCES: list[Source] = [
    Source(
        key="fierce_biotech",
        name="Fierce Biotech",
        rss_url="https://www.fiercebiotech.com/rss/xml",
        site_url="https://www.fiercebiotech.com",
        body_selectors=(".article-body", "[itemprop='articleBody']", "article"),
    ),
    Source(
        key="fierce_pharma",
        name="Fierce Pharma",
        rss_url="https://www.fiercepharma.com/rss/xml",
        site_url="https://www.fiercepharma.com",
        body_selectors=(".article-body", "[itemprop='articleBody']", "article"),
    ),
    Source(
        key="endpoints_news",
        name="Endpoints News",
        rss_url="https://endpoints.news/feed",
        site_url="https://endpoints.news",
        body_selectors=(".entry-content", "article"),
        notes="robots.txt 접근이 자동화 도구에서 간헐적으로 차단됨. 실패율 모니터링 필요.",
    ),
    Source(
        key="stat_news",
        name="STAT News",
        rss_url="https://www.statnews.com/feed/",
        site_url="https://www.statnews.com",
        body_selectors=(".entry-content", "article"),
        notes="일부 기사는 STAT+ 유료 콘텐츠(본문 미공개, 제목/요약만 노출 권장).",
    ),
    Source(
        key="medcity_news",
        name="MedCity News",
        rss_url="https://medcitynews.com/feed/",
        site_url="https://medcitynews.com",
        body_selectors=(".entry-content", "article"),
    ),
]


def get_source(key: str) -> Source | None:
    for s in SOURCES:
        if s.key == key:
            return s
    return None
