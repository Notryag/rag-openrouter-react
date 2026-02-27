import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from repositories import user_repository


class AuthService:
    def __init__(self, jwt_secret: str, jwt_algorithm: str, access_token_expire_minutes: int):
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.access_token_expire_minutes = access_token_expire_minutes

    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 390000)
        return f"{salt}${digest.hex()}"

    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        try:
            salt, expected = stored_hash.split("$", 1)
        except ValueError:
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 390000)
        return secrets.compare_digest(digest.hex(), expected)

    def create_access_token(self, user_id: int, username: str) -> str:
        expires = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            "sub": str(user_id),
            "username": username,
            "exp": expires,
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def register_user(self, username: str, password: str):
        existing = user_repository.get_user_by_username(username)
        if existing is not None:
            raise HTTPException(status_code=409, detail="Username already exists")
        user_id = user_repository.create_user(username, self.hash_password(password))
        return {"id": user_id, "username": username}

    def login_user(self, username: str, password: str):
        row = user_repository.get_user_by_username(username)
        if row is None or not self.verify_password(password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        token = self.create_access_token(int(row["id"]), row["username"])
        return {"access_token": token, "username": row["username"]}

    def get_current_user_optional(self, credentials: Optional[HTTPAuthorizationCredentials]):
        if credentials is None:
            return None
        try:
            payload = jwt.decode(credentials.credentials, self.jwt_secret, algorithms=[self.jwt_algorithm])
            user_id = int(payload.get("sub"))
            username = payload.get("username")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")

        row = user_repository.get_user_by_id(user_id)
        if row is None:
            raise HTTPException(status_code=401, detail="User not found")
        return {"id": int(row["id"]), "username": row["username"]}

    @staticmethod
    def require_user(user):
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        return user
