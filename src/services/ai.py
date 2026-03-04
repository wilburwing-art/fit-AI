"""AI services using PydanticAI"""

import hashlib
import os

import logfire
from pydantic import BaseModel
from pydantic_ai import Agent

from src.config import settings
from src.services.cache import cache_get, cache_set

# Set provider API keys from settings — PydanticAI reads from env vars
if settings.anthropic_api_key:
    os.environ.setdefault("ANTHROPIC_API_KEY", settings.anthropic_api_key)
if settings.openai_api_key:
    os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
if settings.google_api_key:
    os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)


# ---------------------------------------------------------------------------
# Structured output models
# ---------------------------------------------------------------------------
class WorkoutPlanOutput(BaseModel):
    """Structured workout plan output"""

    weeks: int
    phases: list[dict]
    exercises: list[str]
    frequency: int  # workouts per week
    rationale: str


class MealPlanOutput(BaseModel):
    """Structured meal plan output"""

    daily_protein_g: int
    daily_carbs_g: int
    daily_fat_g: int
    daily_calories: int
    meal_suggestions: list[str]
    rationale: str


# ---------------------------------------------------------------------------
# Lazy-loaded agents (initialised on first use)
# ---------------------------------------------------------------------------
_planning_agent: Agent | None = None
_nutrition_agent: Agent | None = None
_analysis_agent: Agent | None = None
_long_context_agent: Agent | None = None
_coaching_agent: Agent | None = None


def get_planning_agent() -> Agent:
    """Get or create the planning agent (uses planning_model — Opus by default)."""
    global _planning_agent
    if _planning_agent is None:
        _planning_agent = Agent(
            settings.planning_model,
            result_type=WorkoutPlanOutput,
            system_prompt="""You are an expert strength coach and personal trainer.

    Your role is to create safe, effective, and personalized workout programs
    based on the user's goals, experience level, equipment access, and constraints.

    Guidelines:
    1. Prioritize safety and sustainable progress
    2. Account for recovery capacity based on age, experience, and lifestyle
    3. Use progressive overload principles
    4. Recommend appropriate exercise selection for available equipment
    5. Consider any injuries or limitations
    6. Balance training volume with recovery

    Always explain your reasoning clearly and provide specific, actionable plans.""",
        )
    return _planning_agent


def get_nutrition_agent() -> Agent:
    """Get or create the nutrition agent (uses coaching_model — Sonnet by default)."""
    global _nutrition_agent
    if _nutrition_agent is None:
        _nutrition_agent = Agent(
            settings.coaching_model,
            result_type=MealPlanOutput,
            system_prompt="""You are an expert sports nutritionist and dietitian.

    Your role is to recommend appropriate macro targets and meal suggestions
    based on the user's goals, activity level, and preferences.

    Guidelines:
    1. Use evidence-based nutrition principles
    2. Prioritize protein intake for muscle recovery and growth
    3. Adjust carbs and fats based on training volume and goals
    4. Consider dietary preferences and restrictions
    5. Provide practical, sustainable recommendations
    6. Calculate appropriate calorie targets for goals

    Always explain your reasoning and provide specific, actionable guidance.""",
        )
    return _nutrition_agent


def get_analysis_agent() -> Agent:
    """Get or create the analysis agent (uses analysis_model — Sonnet by default)."""
    global _analysis_agent
    if _analysis_agent is None:
        _analysis_agent = Agent(
            settings.analysis_model,
            system_prompt="""You are an AI fitness coach analyzing user progress.

        Review the provided data and identify:
        - Progress trends (improving, plateauing, declining)
        - Potential issues or concerns
        - Correlation between training, nutrition, and results
        - Specific, actionable recommendations

        Be supportive but honest. Celebrate wins and provide constructive feedback.""",
        )
    return _analysis_agent


def get_coaching_agent() -> Agent:
    """Get or create the coaching agent (uses coaching_model — Sonnet by default)."""
    global _coaching_agent
    if _coaching_agent is None:
        _coaching_agent = Agent(
            settings.coaching_model,
            system_prompt="""You are an expert fitness coach and sports scientist.

Answer the user's question using the provided context about their recent training,
nutrition, and body metrics. Be concise, evidence-based, and actionable.

Guidelines:
1. Reference their actual data when relevant (weights lifted, calories, trends)
2. Give specific, practical advice — not generic tips
3. If the question is outside your expertise, say so
4. Keep answers focused: 2-4 paragraphs max
5. Be encouraging but honest about areas needing improvement""",
        )
    return _coaching_agent


def get_long_context_agent() -> Agent:
    """Get or create the long-context agent (uses long_context_model — Gemini by default)."""
    global _long_context_agent
    if _long_context_agent is None:
        _long_context_agent = Agent(
            settings.long_context_model,
            system_prompt="""You are a fitness data analyst with access to a user's
        complete training history. Provide deep, longitudinal insights that span
        months or years of data. Identify long-term trends, periodisation
        effectiveness, and macro-level recommendations.""",
        )
    return _long_context_agent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _hash_params(*args: object) -> str:
    """SHA-256 hash of arguments, truncated to 16 hex chars."""
    raw = "|".join(str(a) for a in args)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------
@logfire.instrument("ai:generate_workout_plan")
async def generate_workout_plan(
    user_goals: str,
    experience_level: str,
    equipment_access: list[str],
    time_availability: int,
    injuries: str | None = None,
    age: int | None = None,
) -> WorkoutPlanOutput:
    """Generate a personalized workout plan using AI"""
    # Check cache
    cache_key = f"plan:{_hash_params(user_goals, experience_level, sorted(equipment_access), time_availability, injuries, age)}"
    cached = await cache_get(cache_key)
    if cached:
        return WorkoutPlanOutput(**cached)

    prompt = f"""Create a personalized workout program for this user:

Goals: {user_goals}
Experience Level: {experience_level}
Available Equipment: {", ".join(equipment_access)}
Time Availability: {time_availability} minutes per week
Age: {age if age else "Not specified"}
Injuries/Limitations: {injuries if injuries else "None"}

Generate a complete workout plan with:
- Appropriate training frequency (workouts per week)
- Program duration and phases
- Specific exercises
- Clear rationale for your recommendations
"""

    agent = get_planning_agent()
    result = await agent.run(prompt)
    await cache_set(cache_key, result.data.model_dump())
    return result.data


@logfire.instrument("ai:generate_nutrition_targets")
async def generate_nutrition_targets(
    user_goals: str,
    weight_lbs: float,
    activity_level: str,
    dietary_preferences: str | None = None,
) -> MealPlanOutput:
    """Generate personalized nutrition targets using AI"""
    # Check cache
    cache_key = f"nutrition:{_hash_params(user_goals, weight_lbs, activity_level, dietary_preferences)}"
    cached = await cache_get(cache_key)
    if cached:
        return MealPlanOutput(**cached)

    prompt = f"""Create personalized nutrition targets for this user:

Goals: {user_goals}
Current Weight: {weight_lbs} lbs
Activity Level: {activity_level}
Dietary Preferences: {dietary_preferences if dietary_preferences else "None"}

Generate nutrition recommendations with:
- Daily macro targets (protein, carbs, fats)
- Total daily calorie target
- Sample meal suggestions
- Clear rationale for your recommendations
"""

    agent = get_nutrition_agent()
    result = await agent.run(prompt)
    await cache_set(cache_key, result.data.model_dump())
    return result.data


@logfire.instrument("ai:analyze_progress")
async def analyze_progress(
    workout_history: list[dict],
    weight_history: list[dict],
    meal_history: list[dict],
) -> str:
    """Analyze user progress and provide insights"""
    agent = get_analysis_agent()

    prompt = f"""Analyze this user's recent fitness data:

Workout History:
{workout_history}

Weight History:
{weight_history}

Meal History:
{meal_history}

Provide a concise analysis with:
1. Key observations
2. Progress assessment
3. Specific recommendations for improvement
"""

    result = await agent.run(prompt)
    return result.data


@logfire.instrument("ai:coaching_qa")
async def coaching_qa(question: str, user_context: str) -> str:
    """Answer a coaching question with user context."""
    agent = get_coaching_agent()

    prompt = f"""User context:
{user_context}

Question: {question}"""

    result = await agent.run(prompt)
    return result.data
