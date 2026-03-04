"""Natural language parsing for workout and meal logging.

Uses a fast extraction model (GPT-4o-mini by default) to turn free-text
descriptions into structured data.
"""

import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from src.config import settings


# ---------------------------------------------------------------------------
# Structured output models
# ---------------------------------------------------------------------------
class ParsedSet(BaseModel):
    reps: int
    weight_lbs: float | None = None
    rpe: float | None = None
    is_warmup: bool = False


class ParsedExercise(BaseModel):
    name: str
    sets: list[ParsedSet]


class ParsedWorkout(BaseModel):
    exercises: list[ParsedExercise]
    duration_minutes: int | None = None
    overall_rpe: float | None = None
    notes: str | None = None


class ParsedMeal(BaseModel):
    meal_type: str | None = Field(None, description="breakfast, lunch, dinner, snack")
    description: str
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    calories: int | None = None


# ---------------------------------------------------------------------------
# Lazy-loaded agents
# ---------------------------------------------------------------------------
_workout_parser: Agent | None = None
_meal_parser: Agent | None = None


def get_workout_parser() -> Agent:
    global _workout_parser
    if _workout_parser is None:
        _workout_parser = Agent(
            settings.extraction_model,
            result_type=ParsedWorkout,
            system_prompt="""You parse natural-language workout logs into structured data.

Common notations:
- "225x5x3" = 225 lbs, 5 reps, 3 sets
- "3x10 @RPE 8" = 3 sets of 10 reps at RPE 8
- "BW" or "bodyweight" = weight_lbs is null

If the user mentions duration (e.g. "45 min session"), fill duration_minutes.
If they mention overall difficulty, fill overall_rpe.
Extract every exercise and every set mentioned.""",
        )
    return _workout_parser


def get_meal_parser() -> Agent:
    global _meal_parser
    if _meal_parser is None:
        _meal_parser = Agent(
            settings.extraction_model,
            result_type=ParsedMeal,
            system_prompt="""You parse natural-language meal descriptions into structured data.

Estimate macros from common foods when reasonable. For example:
- "chicken breast 8 oz" → ~50g protein, ~0g carbs, ~3g fat, ~230 cal
- "cup of rice" → ~5g protein, ~45g carbs, ~0g fat, ~210 cal

Sum totals if multiple items are described. If meal type is obvious
(e.g. "breakfast"), set meal_type accordingly.
Be conservative with estimates — round to the nearest 5g.""",
        )
    return _meal_parser


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------
@logfire.instrument("nl:parse_workout")
async def parse_workout_text(text: str) -> ParsedWorkout:
    """Parse free-text workout description into structured data."""
    agent = get_workout_parser()
    result = await agent.run(text)
    return result.data


@logfire.instrument("nl:parse_meal")
async def parse_meal_text(text: str) -> ParsedMeal:
    """Parse free-text meal description into structured data."""
    agent = get_meal_parser()
    result = await agent.run(text)
    return result.data
