from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlmodel import Session

from config import get_session
from routes.common import get_current_user, templates, wants_json
from schemas.truelens_schema import UserRegister
from services.truelens_service import authenticate_user, register_user

router = APIRouter()


@router.get("/account", name="account")
def account_page(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/login?msg=login_required", status_code=303)
    return templates.TemplateResponse(
        request,
        "account.html",
        context={"active_page": "account", "current_user": current_user},
    )


@router.get("/login", name="login")
def login_page(request: Request, msg: str = ""):
    current_user = get_current_user(request)
    if current_user:
        return RedirectResponse(url="/", status_code=303)
    success_msg = None
    if msg == "registered":
        success_msg = "Registrasi berhasil! Silakan masuk dengan akun Anda."
    elif msg == "logged_out":
        success_msg = "Anda telah berhasil keluar."
    elif msg == "login_required":
        success_msg = "Silakan masuk terlebih dahulu untuk mengakses fitur tersebut."
    return templates.TemplateResponse(
        request,
        "login.html",
        context={
            "active_page": "login",
            "current_user": None,
            "error": None,
            "success_message": success_msg,
        },
    )


@router.post("/login", name="login_post")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    user = authenticate_user(session, username, password)
    if not user:
        if wants_json(request):
            return JSONResponse(
                {"ok": False, "error": "Username atau password tidak sesuai."},
                status_code=400,
            )
        return templates.TemplateResponse(
            request,
            "login.html",
            context={
                "active_page": "login",
                "current_user": None,
                "error": "Username atau password tidak sesuai.",
                "success_message": None,
                "username_val": username,
            },
            status_code=400,
        )

    request.session["user"] = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.strftime("%d %b %Y"),
    }
    if wants_json(request):
        return JSONResponse({"ok": True, "redirect": "/"})
    return RedirectResponse(url="/", status_code=303)


@router.get("/register", name="register")
def register_page(request: Request):
    current_user = get_current_user(request)
    if current_user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        request,
        "register.html",
        context={
            "active_page": "register",
            "current_user": None,
            "error": None,
        },
    )


@router.post("/register", name="registers_post")
def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    if len(password) < 4:
        if wants_json(request):
            return JSONResponse(
                {"ok": False, "error": "Password minimal terdiri dari 4 karakter."},
                status_code=400,
            )
        return templates.TemplateResponse(
            request,
            "register.html",
            context={
                "active_page": "register",
                "current_user": None,
                "error": "Password minimal terdiri dari 4 karakter.",
                "username_val": username,
                "email_val": email,
            },
            status_code=400,
        )

    try:
        data = UserRegister(username=username, email=email, password=password)
        register_user(session, data)
        if wants_json(request):
            return JSONResponse(
                {
                    "ok": True,
                    "mode": "login",
                    "message": "Registrasi berhasil! Silakan masuk dengan akun Anda.",
                }
            )
        return RedirectResponse(url="/login?msg=registered", status_code=303)
    except ValueError as err:
        if wants_json(request):
            return JSONResponse({"ok": False, "error": str(err)}, status_code=400)
        return templates.TemplateResponse(
            request,
            "register.html",
            context={
                "active_page": "register",
                "current_user": None,
                "error": str(err),
                "username_val": username,
                "email_val": email,
            },
            status_code=400,
        )


@router.post("/logout", name="logout")
@router.get("/logout")
def logout_user(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
