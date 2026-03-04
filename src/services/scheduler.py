"""Background scheduling with APScheduler 3.x.

Runs periodic jobs such as the weekly progress analysis for all active users.
"""

import logging
from datetime import UTC, datetime

import logfire
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import select

from src.models import AnalysisCache, User
from src.services.ai import analyze_progress
from src.services.cache import cache_set

logger = logging.getLogger(__name__)


@logfire.instrument("scheduler:analyze_single_user")
async def _analyze_single_user(
    user: User,
    session: AsyncSession,
) -> None:
    """Run progress analysis for a single user and persist the result."""
    try:
        # Fetch last 30 days of data (simplified — extend with real queries)
        from src.models import MealLog, WeightLog, WorkoutSession

        cutoff = datetime.now(UTC)

        workouts_result = await session.execute(
            select(WorkoutSession)
            .where(WorkoutSession.user_id == user.id)
            .order_by(WorkoutSession.completed_date.desc())
            .limit(30)
        )
        workouts = [
            {
                "date": str(w.completed_date),
                "duration": w.duration_minutes,
                "rpe": w.overall_rpe,
            }
            for w in workouts_result.scalars().all()
        ]

        meals_result = await session.execute(
            select(MealLog)
            .where(MealLog.user_id == user.id)
            .order_by(MealLog.date.desc())
            .limit(60)
        )
        meals = [
            {
                "date": str(m.date),
                "calories": m.calories,
                "protein": m.protein_g,
            }
            for m in meals_result.scalars().all()
        ]

        weights_result = await session.execute(
            select(WeightLog)
            .where(WeightLog.user_id == user.id)
            .order_by(WeightLog.date.desc())
            .limit(30)
        )
        weights = [
            {"date": str(w.date), "weight_lbs": w.weight_lbs}
            for w in weights_result.scalars().all()
        ]

        if not workouts and not meals and not weights:
            logger.info("No data for user %s — skipping analysis", user.id)
            return

        analysis = await analyze_progress(workouts, weights, meals)

        # Persist to DB
        cache_entry = AnalysisCache(
            user_id=user.id,
            analysis_type="weekly_review",
            analysis_date=cutoff,
            results={"summary": analysis},
        )
        session.add(cache_entry)
        await session.commit()

        # Cache in Redis
        await cache_set(
            f"analysis:{user.id}:weekly",
            {"summary": analysis, "date": cutoff.isoformat()},
        )

        logger.info("Weekly analysis completed for user %s", user.id)

    except Exception:
        logger.exception("Failed to analyse user %s", user.id)


@logfire.instrument("scheduler:weekly_analysis_job")
async def weekly_analysis_job(session_maker: async_sessionmaker) -> None:
    """Run weekly progress analysis for all active users."""
    logger.info("Starting weekly analysis job")
    async with session_maker() as session:
        result = await session.execute(
            select(User).where(User.is_active == True)  # noqa: E712
        )
        users = result.scalars().all()
        logger.info("Found %d active users for analysis", len(users))

        for user in users:
            await _analyze_single_user(user, session)

    logger.info("Weekly analysis job complete")


def setup_scheduler(session_maker: async_sessionmaker) -> AsyncIOScheduler:
    """Create and configure the scheduler (does not start it)."""
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        weekly_analysis_job,
        trigger=CronTrigger(day_of_week="mon", hour=6, minute=0),
        args=[session_maker],
        id="weekly_analysis",
        name="Weekly progress analysis",
        replace_existing=True,
    )

    return scheduler
