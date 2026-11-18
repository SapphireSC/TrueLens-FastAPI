import os
import hashlib
import hmac

from sqlmodel import Session, select

from models.truelens_model import User
from schemas.truelens_schema import UserRegister


def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        salt = hashlib.sha256(os.urandom(16)).hexdigest()[:16]
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    if "$" not in stored_hash:
        return False
    salt, _ = stored_hash.split("$", 1)
    expected = hash_password(password, salt=salt)
    return hmac.compare_digest(expected, stored_hash)


def get_user_by_username(session: Session, username: str) -> User | None:
    clean_uname = username.strip().lower()
    statement = select(User).where(User.username == clean_uname)
    return session.exec(statement).first()


def register_user(session: Session, data: UserRegister) -> User:
    clean_uname = data.username.strip().lower()
    clean_email = data.email.strip().lower()

    if get_user_by_username(session, clean_uname):
        raise ValueError("Username sudah digunakan. Silakan pilih username lain.")

    salt = hashlib.sha256(os.urandom(16)).hexdigest()[:16]
    pw_hash = hash_password(data.password, salt=salt)

    new_user = User(
        username=clean_uname,
        email=clean_email,
        password_hash=pw_hash,
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user


def authenticate_user(session: Session, username: str, password: str) -> User | None:
    user = get_user_by_username(session, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
