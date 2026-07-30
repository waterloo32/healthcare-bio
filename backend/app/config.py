"""전역 설정값. PRD 8.2(수집기), 8.6(저장) 참고."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{(DATA_DIR / 'news.db').as_posix()}"

# PRD FR-6 / 8.2: User-Agent에 연락처/용도 명시
CONTACT_EMAIL = "hyeonah1310@gmail.com"
USER_AGENT = (
    "BioHealthNewsCurationBot/0.1 "
    f"(personal research use; contact: {CONTACT_EMAIL})"
)

REQUEST_TIMEOUT_SECONDS = 15
REQUEST_DELAY_SECONDS = 1.5  # 소스별 요청 간 지연 (PRD 8.2)
MAX_ARTICLES_PER_SOURCE_PER_RUN = 30

# 요약 문장 수 (PRD FR-10)
SUMMARY_SENTENCE_COUNT = 3

# 제목 유사도 dedup 임계값 (PRD FR-4)
TITLE_SIMILARITY_THRESHOLD = 0.85
DEDUP_WINDOW_DAYS = 14
