import datetime as dt

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Article(Base):
    """PRD 8.5 데이터 모델."""

    __tablename__ = "articles"
    __table_args__ = (UniqueConstraint("source_url", name="uq_article_source_url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    source_key: Mapped[str] = mapped_column(String(64), index=True)
    source_name: Mapped[str] = mapped_column(String(128))
    source_url: Mapped[str] = mapped_column(String(1024), index=True)

    title: Mapped[str] = mapped_column(String(512))
    normalized_title: Mapped[str] = mapped_column(String(512), index=True)

    published_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    collected_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_text_failed: Mapped[bool] = mapped_column(default=False)

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_failed: Mapped[bool] = mapped_column(default=False)  # FR-12

    primary_category: Mapped[str] = mapped_column(String(32), index=True)
    secondary_categories: Mapped[list] = mapped_column(JSON, default=list)  # FR-8
    classification_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    dedup_group_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)  # FR-4
    is_duplicate: Mapped[bool] = mapped_column(default=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Article id={self.id} title={self.title!r}>"


class CollectionRun(Base):
    """수집 배치 실행 기록 (FR-5, 목표 지표: 소스당 수집 성공률)."""

    __tablename__ = "collection_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    source_logs: Mapped[list["SourceRunLog"]] = relationship(back_populates="run")


class SourceRunLog(Base):
    """소스별 수집 성공/실패 로그 (FR-5)."""

    __tablename__ = "source_run_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("collection_runs.id"))
    source_key: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16))  # ok | failed | skipped_robots
    fetched_count: Mapped[int] = mapped_column(Integer, default=0)
    new_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    run: Mapped[CollectionRun] = relationship(back_populates="source_logs")
