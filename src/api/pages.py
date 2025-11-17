"""Page routes for serving HTML with HTMX"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.auth import current_active_user
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
async def dashboard(request: Request):
    """Dashboard page - authentication checked client-side"""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": "Dashboard"},
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
async def workouts_page(request: Request):
    """Workouts page - authentication checked client-side"""
    return templates.TemplateResponse(
        "workouts.html",
        {"request": request, "title": "Workouts"},
    )


@router.get("/nutrition", response_class=HTMLResponse)
async def nutrition_page(request: Request):
    """Nutrition page - authentication checked client-side"""
    return templates.TemplateResponse(
        "nutrition.html",
        {"request": request, "title": "Nutrition"},
    )
