"""AI services using PydanticAI"""

from pydantic import BaseModel
from pydantic_ai import Agent

from src.config import settings


# Structured output models
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


# Lazy-loaded agents (initialized on first use)
_planning_agent: Agent | None = None
_nutrition_agent: Agent | None = None


def get_planning_agent() -> Agent:
    """Get or create the planning agent"""
    global _planning_agent
    if _planning_agent is None:
        _planning_agent = Agent(
            "anthropic:claude-sonnet-4-5-20250929",
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
    """Get or create the nutrition agent"""
    global _nutrition_agent
    if _nutrition_agent is None:
        _nutrition_agent = Agent(
            "anthropic:claude-sonnet-4-5-20250929",
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


async def generate_workout_plan(
    user_goals: str,
    experience_level: str,
    equipment_access: list[str],
    time_availability: int,
    injuries: str | None = None,
    age: int | None = None,
) -> WorkoutPlanOutput:
    """Generate a personalized workout plan using AI

    Args:
        user_goals: User's fitness goals (e.g., "build muscle", "lose weight")
        experience_level: "beginner", "intermediate", or "advanced"
        equipment_access: List of available equipment
        time_availability: Minutes available per week
        injuries: Any injuries or limitations
        age: User's age

    Returns:
        Structured workout plan with exercises and rationale
    """
    prompt = f"""Create a personalized workout program for this user:

Goals: {user_goals}
Experience Level: {experience_level}
Available Equipment: {', '.join(equipment_access)}
Time Availability: {time_availability} minutes per week
Age: {age if age else 'Not specified'}
Injuries/Limitations: {injuries if injuries else 'None'}

Generate a complete workout plan with:
- Appropriate training frequency (workouts per week)
- Program duration and phases
- Specific exercises
- Clear rationale for your recommendations
"""

    agent = get_planning_agent()
    result = await agent.run(prompt)
    return result.data


async def generate_nutrition_targets(
    user_goals: str,
    weight_lbs: float,
    activity_level: str,
    dietary_preferences: str | None = None,
) -> MealPlanOutput:
    """Generate personalized nutrition targets using AI

    Args:
        user_goals: User's fitness goals
        weight_lbs: Current weight in pounds
        activity_level: "sedentary", "moderate", or "active"
        dietary_preferences: Any dietary restrictions or preferences

    Returns:
        Structured nutrition plan with macro targets and meal suggestions
    """
    prompt = f"""Create personalized nutrition targets for this user:

Goals: {user_goals}
Current Weight: {weight_lbs} lbs
Activity Level: {activity_level}
Dietary Preferences: {dietary_preferences if dietary_preferences else 'None'}

Generate nutrition recommendations with:
- Daily macro targets (protein, carbs, fats)
- Total daily calorie target
- Sample meal suggestions
- Clear rationale for your recommendations
"""

    agent = get_nutrition_agent()
    result = await agent.run(prompt)
    return result.data


async def analyze_progress(
    workout_history: list[dict],
    weight_history: list[dict],
    meal_history: list[dict],
) -> str:
    """Analyze user progress and provide insights

    Args:
        workout_history: Recent workout data
        weight_history: Recent weight measurements
        meal_history: Recent meal logs

    Returns:
        Analysis summary with insights and recommendations
    """
    analysis_agent = Agent(
        "anthropic:claude-sonnet-4-5-20250929",
        system_prompt="""You are an AI fitness coach analyzing user progress.

        Review the provided data and identify:
        - Progress trends (improving, plateauing, declining)
        - Potential issues or concerns
        - Correlation between training, nutrition, and results
        - Specific, actionable recommendations

        Be supportive but honest. Celebrate wins and provide constructive feedback.""",
    )

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

    result = await analysis_agent.run(prompt)
    return result.data
