from fastapi import Request
from fastapi.templating import Jinja2Templates

from config import BASE_DIR

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def get_current_user(request: Request) -> dict | None:
    return request.session.get("user")


def wants_json(request: Request) -> bool:
    return "application/json" in request.headers.get("accept", "")
