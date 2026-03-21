"""
auth.py — JWT authentication helpers and role-based dependencies.
All config is read from environment variables (set in .env or Render dashboard).
"""
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole, STAFF_ROLES, COMPANY_ROLES

# ── JWT Configuration ─────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "placement_portal_dev_secret_change_in_production")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")

# Supports both ACCESS_TOKEN_EXPIRE_MINUTES (from env) and JWT_ACCESS_TOKEN_EXPIRE_MINUTES
_expire_env = (
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES") or
    "1440"   # default 24 hours
)
ACCESS_TOKEN_EXPIRE_MINUTES = int(_expire_env)

# ── Registration Secret Keys ──────────────────────────────────────────────
STAFF_SECRET_KEY   = os.getenv("STAFF_SECRET_KEY",   "STAFF@2024")
COMPANY_SECRET_KEY = os.getenv("COMPANY_SECRET_KEY", "COMPANY@2024")
ADMIN_SECRET_KEY   = os.getenv("ADMIN_SECRET_KEY",   "ADMIN@SUPER2024")
OFFICER_SECRET_KEY = os.getenv("OFFICER_SECRET_KEY", "OFFICER@2024")

ROLE_SECRET_MAP = {
    UserRole.head_admin:               ADMIN_SECRET_KEY,
    UserRole.placement_officer:        OFFICER_SECRET_KEY,
    UserRole.senior_staff:             STAFF_SECRET_KEY,
    UserRole.staff:                    STAFF_SECRET_KEY,
    UserRole.junior_staff:             STAFF_SECRET_KEY,
    UserRole.company_hr_manager:       COMPANY_SECRET_KEY,
    UserRole.company_tech_interviewer: COMPANY_SECRET_KEY,
    UserRole.company_recruitment_mgr:  COMPANY_SECRET_KEY,
    UserRole.company_team_leader:      COMPANY_SECRET_KEY,
    UserRole.company_officer:          COMPANY_SECRET_KEY,
    UserRole.company:                  COMPANY_SECRET_KEY,
    UserRole.student:                  None,
}

pwd_context   = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def require_roles(*roles: UserRole):
    def _dep(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return _dep


def require_staff(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Staff access required")
    return current_user


def require_company(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in COMPANY_ROLES:
        raise HTTPException(status_code=403, detail="Company access required")
    return current_user


def require_student(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.student:
        raise HTTPException(status_code=403, detail="Student access required")
    return current_user


def require_head_or_officer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {UserRole.head_admin, UserRole.placement_officer}:
        raise HTTPException(status_code=403, detail="Head admin or placement officer required")
    return current_user


def validate_registration_key(role: UserRole, secret_key: Optional[str]) -> bool:
    required = ROLE_SECRET_MAP.get(role)
    if required is None:
        return True   # student — no key needed
    if not secret_key:
        return False
    return secret_key == required


def require_staff_or_company(current_user: User = Depends(get_current_user)) -> User:
    """Allow both staff AND company roles to create/manage exams."""
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(status_code=403, detail="Staff or company access required")
    return current_user
