"""AI analysis and cache models"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, SQLModel


class AnalysisCache(SQLModel, table=True):
    """Cached AI analysis results"""

    __tablename__ = "analysis_cache"

    id: int = Field(primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    analysis_type: str = Field(
        max_length=50
    )  # weekly_review, progress_summary, etc.
    analysis_date: datetime = Field(index=True)
    results: dict = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScheduledJob(SQLModel, table=True):
    """Background job scheduling tracking"""

    __tablename__ = "scheduled_jobs"

    id: int = Field(primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    job_type: str = Field(
        max_length=50
    )  # weekly_review, plan_adjustment, etc.
    schedule_expression: str = Field(max_length=100)  # cron format
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    is_active: bool = Field(default=True)
