"""1회 수집 배치 실행 CLI (PRD 8.2: cron/Task Scheduler로 1일 1~4회 실행).

사용법:
    .venv\\Scripts\\python.exe backend\\run_collect.py
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # Windows 콘솔 한글 로그 깨짐 방지

from app.config import LOG_DIR  # noqa: E402
from app.db import SessionLocal, init_db  # noqa: E402
from app.pipeline import run_collection_cycle  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "collect.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("run_collect")


def main() -> None:
    init_db()
    session = SessionLocal()
    try:
        run = run_collection_cycle(session)
        source_logs = list(run.source_logs)
    finally:
        session.close()

    total_fetched = sum(log.fetched_count for log in source_logs)
    total_new = sum(log.new_count for log in source_logs)
    ok_sources = sum(1 for log in source_logs if log.status == "ok")
    total_sources = len(source_logs)
    success_rate = (ok_sources / total_sources * 100) if total_sources else 0.0

    logger.info(
        "수집 완료: 소스 %d/%d 성공(%.0f%%), 신규 기사 %d건 (총 조회 %d건)",
        ok_sources, total_sources, success_rate, total_new, total_fetched,
    )
    if success_rate < 95:
        logger.warning("소스 성공률이 목표치(95%%) 미달입니다. 실패 로그를 확인하세요.")  # FR-5
        for log in source_logs:
            if log.status != "ok":
                logger.warning("  - %s: %s (%s)", log.source_key, log.status, log.error_message)


if __name__ == "__main__":
    main()
