"""Page routes for serving HTML with HTMX"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.auth import current_user_optional
from src.models.user import User

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
