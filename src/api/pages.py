"""Page routes for serving HTML with HTMX"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select

from src.auth import current_user_optional
from src.database import DatabaseSession
from src.models import Exercise
from src.models.user import User
from src.models.workout import UserExercisePreference

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Home page"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Fit Agent - AI-Powered Fitness Tracking"},
    )


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: User | None = Depends(current_user_optional),
):
    """Dashboard page - requires authentication"""
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": "Dashboard", "user": user},
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "title": "Login"},
    )


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Registration page"""
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "title": "Register"},
    )


@router.get("/workouts", response_class=HTMLResponse)
async def workouts_page(
    request: Request,
    user: User | None = Depends(current_user_optional),
):
    """Workouts page - requires authentication"""
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        "workouts.html",
        {"request": request, "title": "Workouts", "user": user},
    )


@router.get("/nutrition", response_class=HTMLResponse)
async def nutrition_page(
    request: Request,
    user: User | None = Depends(current_user_optional),
):
    """Nutrition page - requires authentication"""
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        "nutrition.html",
        {"request": request, "title": "Nutrition", "user": user},
    )


@router.get("/preferences", response_class=HTMLResponse)
async def preferences_page(
    request: Request,
    user: User | None = Depends(current_user_optional),
):
    """Training preferences page - requires authentication"""
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        "preferences.html",
        {"request": request, "title": "Training Preferences", "user": user},
    )


@router.get("/calendar", response_class=HTMLResponse)
async def calendar_page(
    request: Request,
    user: User | None = Depends(current_user_optional),
):
    """Calendar view page - requires authentication"""
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        "calendar.html",
        {"request": request, "title": "Calendar", "user": user},
    )


@router.get("/coach", response_class=HTMLResponse)
async def coach_page(
    request: Request,
    user: User | None = Depends(current_user_optional),
):
    """AI coaching Q&A page - requires authentication"""
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        "coach.html",
        {"request": request, "title": "Coach", "user": user},
    )


@router.get("/exercises", response_class=HTMLResponse)
async def exercises_page(
    request: Request,
    user: User | None = Depends(current_user_optional),
):
    """Exercise library browse page - requires authentication"""
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        "exercises/index.html",
        {"request": request, "title": "Exercises", "user": user},
    )


@router.get("/exercises/{exercise_id}", response_class=HTMLResponse)
async def exercise_detail_page(
    exercise_id: int,
    request: Request,
    session: DatabaseSession,
    user: User | None = Depends(current_user_optional),
):
    """Exercise detail page - requires authentication"""
    if user is None:
        return RedirectResponse(url="/login", status_code=303)

    exercise = await session.get(Exercise, exercise_id)
    if not exercise:
        return RedirectResponse(url="/exercises", status_code=303)

    # Get user's preference for this exercise
    user_preference = None
    if user:
        result = await session.execute(
            select(UserExercisePreference).where(
                UserExercisePreference.user_id == user.id,
                UserExercisePreference.exercise_id == exercise_id,
            )
        )
        pref = result.scalar_one_or_none()
        if pref:
            user_preference = pref.preference

    return templates.TemplateResponse(
        "exercises/detail.html",
        {
            "request": request,
            "title": exercise.name,
            "user": user,
            "exercise": exercise,
            "user_preference": user_preference,
        },
    )
