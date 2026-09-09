"""
Authentification par session Flask (pas de dépendance externe).

- login_required : bloque l'accès si personne n'est connecté
- require_role : bloque l'accès si l'utilisateur n'a pas le rôle attendu
"""

import json
from functools import wraps
from pathlib import Path

from flask import abort, redirect, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

USERS_PATH = Path(__file__).resolve().parent.parent / "data" / "users.json"


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return check_password_hash(hashed_password, password)


def authenticate_user(username: str, password: str) -> dict | None:
    for user in load_users():
        if user.get("username") == username and user.get("enabled", False):
            stored_password = user.get("password", "")
            if verify_password(password, stored_password):
                return user
    return None


def load_users() -> list[dict]:
    if not USERS_PATH.exists():
        return []
    try:
        with USERS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


def save_users(users: list[dict]) -> None:
    USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with USERS_PATH.open("w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("connexion"))
        return f(*args, **kwargs)
    return wrapper


def require_role(role: str):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("connexion"))
            if session.get("role") != role:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(f):
    return require_role("admin")(f)