from datetime import datetime
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
import bcrypt
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.config import SECRET_KEY

router = APIRouter()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


@router.get("/login", response_class=HTMLResponse, name="login")
async def login_page(request: Request, db: Session = Depends(get_db)):
    return request.app.state.templates.TemplateResponse(
        request,
        "login.html",
        {"active_page": "login", "error": None, "current_user": get_current_user(request, db)},
    )


@router.get("/register", response_class=HTMLResponse, name="register")
async def register_page(request: Request, db: Session = Depends(get_db)):
    return request.app.state.templates.TemplateResponse(
        request,
        "register.html",
        {"active_page": "register", "error": None, "current_user": get_current_user(request, db)},
    )


@router.post("/login", response_class=HTMLResponse, name="login_post")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return request.app.state.templates.TemplateResponse(
            request,
            "login.html",
            {"active_page": "login", "error": "Username atau password salah.", "current_user": get_current_user(request, db)},
            status_code=400,
        )
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)


@router.post("/registers", name="registers_post")
async def registers_post(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing:
        return request.app.state.templates.TemplateResponse(
            request,
            "register.html",
            {"active_page": "register", "error": "Username atau email sudah terdaftar.", "current_user": get_current_user(request, db)},
            status_code=400,
        )
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        created_at=datetime.now(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)


@router.post("/logout", name="logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
