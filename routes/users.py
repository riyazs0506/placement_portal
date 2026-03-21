"""
routes/users.py — User registration, login, profile update (v2.3)

Profile includes: personal info, academic details, skills, certifications,
projects, social links — all updatable. Completeness score shown.
"""
import csv, io
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any

from database import get_db
from models import (User, UserRole, COMPANY_ROLES, STAFF_ROLES,
                    DriveOptIn, PlacementResult, ExamSubmission, OptStatus)
from auth import (hash_password, verify_password, create_access_token,
                  get_current_user, validate_registration_key)

router     = APIRouter(prefix="/users", tags=["users"])
templates  = Jinja2Templates(directory="templates")


# ─── Schemas ─────────────────────────────────────────────────────

class RegisterSchema(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.student
    secret_key: Optional[str] = None
    department:      Optional[str]   = None
    batch_year:      Optional[int]   = None
    cgpa:            Optional[float] = None
    tenth_percent:   Optional[float] = None
    twelfth_percent: Optional[float] = None
    backlogs:        Optional[int]   = 0
    roll_number:     Optional[str]   = None
    phone:           Optional[str]   = None
    company_name:        Optional[str] = None
    company_designation: Optional[str] = None


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdateSchema(BaseModel):
    # Basic
    name:             Optional[str]   = None
    phone:            Optional[str]   = None
    address:          Optional[str]   = None
    bio:              Optional[str]   = None
    # Academic
    department:       Optional[str]   = None
    batch_year:       Optional[int]   = None
    cgpa:             Optional[float] = None
    tenth_percent:    Optional[float] = None
    twelfth_percent:  Optional[float] = None
    backlogs:         Optional[int]   = None
    roll_number:      Optional[str]   = None
    # Social / links
    linkedin_url:     Optional[str]   = None
    github_url:       Optional[str]   = None
    portfolio_url:    Optional[str]   = None
    resume_url:       Optional[str]   = None
    # JSON fields
    skills:           Optional[List[str]] = None
    languages:        Optional[List[str]] = None
    certifications:   Optional[List[Any]] = None   # [{name,issuer,year,url}]
    projects:         Optional[List[Any]] = None   # [{title,desc,url,tech}]
    # Company
    company_name:        Optional[str] = None
    company_designation: Optional[str] = None


class PasswordChangeSchema(BaseModel):
    old_password: str
    new_password: str


# ─── Helpers ─────────────────────────────────────────────────────

def _profile_completeness(user: User) -> dict:
    checks = {
        "Phone number":          bool(user.phone),
        "Bio / About":           bool(user.bio),
        "CGPA":                  user.cgpa is not None,
        "10th percentage":       user.tenth_percent is not None,
        "12th percentage":       user.twelfth_percent is not None,
        "Roll number":           bool(user.roll_number),
        "Department":            bool(user.department),
        "Batch year":            user.batch_year is not None,
        "Skills (at least 2)":   len(user.skills or []) >= 2,
        "LinkedIn profile":      bool(user.linkedin_url),
        "At least 1 project":    bool(user.projects),
        "At least 1 cert":       bool(user.certifications),
    }
    done = sum(1 for v in checks.values() if v)
    pct  = round(done / len(checks) * 100)
    return {"score": pct, "done": done, "total": len(checks),
            "missing": [k for k, v in checks.items() if not v],
            "checks": checks}


def _user_to_dict(user: User, include_sensitive: bool = False) -> dict:
    d = {
        "id": user.id, "name": user.name, "email": user.email,
        "role": user.role, "phone": user.phone,
        "address": user.address, "bio": user.bio,
        "department": user.department, "batch_year": user.batch_year,
        "cgpa": user.cgpa, "tenth_percent": user.tenth_percent,
        "twelfth_percent": user.twelfth_percent, "backlogs": user.backlogs or 0,
        "roll_number": user.roll_number,
        "linkedin_url": user.linkedin_url, "github_url": user.github_url,
        "portfolio_url": user.portfolio_url, "resume_url": user.resume_url,
        "skills": user.skills or [], "languages": user.languages or [],
        "certifications": user.certifications or [],
        "projects": user.projects or [],
        "company_name": user.company_name,
        "company_designation": user.company_designation,
        "profile_complete": user.profile_complete,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
    if user.role == UserRole.student:
        d["completeness"] = _profile_completeness(user)
    return d


# ─── HTML Pages ───────────────────────────────────────────────────

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("auth/register_student.html", {"request": request})

@router.get("/register/staff", response_class=HTMLResponse)
def register_staff_page(request: Request):
    return templates.TemplateResponse("auth/register_staff.html", {"request": request})

@router.get("/register/company", response_class=HTMLResponse)
def register_company_page(request: Request):
    return templates.TemplateResponse("auth/register_company.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


# ─── Auth Endpoints ───────────────────────────────────────────────

@router.post("/register")
def register(data: RegisterSchema, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email already registered")
    if not validate_registration_key(data.role, data.secret_key):
        raise HTTPException(403, "Invalid or missing secret key for the selected role")
    user = User(
        name=data.name, email=data.email,
        password_hash=hash_password(data.password), role=data.role,
        department=data.department, batch_year=data.batch_year,
        cgpa=data.cgpa, tenth_percent=data.tenth_percent,
        twelfth_percent=data.twelfth_percent, backlogs=data.backlogs or 0,
        roll_number=data.roll_number, phone=data.phone,
        company_name=data.company_name,
        company_designation=data.company_designation,
        # Profile fields — initialise to empty so JSON columns never crash
        skills=[], languages=[], certifications=[], projects=[],
        profile_complete=False,
    )
    db.add(user); db.commit(); db.refresh(user)
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"message": "Registration successful", "token": token,
            "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}}


@router.post("/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(403, "Account is deactivated")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"token": token, "user": {
        "id": user.id, "name": user.name, "email": user.email,
        "role": user.role, "company_name": user.company_name,
    }}


@router.post("/logout")
def logout():
    return {"message": "Logged out"}


# ─── Profile Endpoints ────────────────────────────────────────────

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return _user_to_dict(current_user, include_sensitive=True)


@router.put("/me")
def update_profile(data: ProfileUpdateSchema, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    """Update any profile field. Only provided (non-None) fields are updated."""
    update_fields = data.dict(exclude_none=True)
    for field, value in update_fields.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)

    # Recompute profile_complete for students
    if current_user.role == UserRole.student:
        c = _profile_completeness(current_user)
        current_user.profile_complete = c["score"] >= 70

    db.commit(); db.refresh(current_user)
    return {"message": "Profile updated successfully",
            "user": _user_to_dict(current_user, True)}


@router.post("/me/password")
def change_password(data: PasswordChangeSchema, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(400, "Current password is incorrect")
    if len(data.new_password) < 6:
        raise HTTPException(400, "New password must be at least 6 characters")
    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@router.get("/profile/{user_id}")
def get_user_profile(user_id: int, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    """View another user's profile (staff/company can view any student)."""
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user: raise HTTPException(404, "User not found")
    # Students can only view their own profile
    if current_user.role == UserRole.student and current_user.id != user_id:
        raise HTTPException(403, "Cannot view other profiles")
    return _user_to_dict(user)


@router.get("/list")
def list_users(role: Optional[str] = None, department: Optional[str] = None,
               batch_year: Optional[int] = None,
               db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company access required")
    q = db.query(User).filter(User.is_active == True)
    if role:
        try: q = q.filter(User.role == UserRole(role))
        except ValueError: raise HTTPException(400, f"Unknown role: {role}")
    if department:
        q = q.filter(User.department == department)
    if batch_year:
        q = q.filter(User.batch_year == batch_year)
    users = q.order_by(User.created_at.desc()).all()
    return [{"id": u.id, "name": u.name, "email": u.email, "role": u.role,
             "department": u.department, "batch_year": u.batch_year,
             "cgpa": u.cgpa, "roll_number": u.roll_number,
             "phone": u.phone, "company_name": u.company_name,
             "is_active": u.is_active, "profile_complete": u.profile_complete}
            for u in users]


@router.get("/students/download")
def download_students(department: Optional[str] = None,
                      batch_year: Optional[int] = None,
                      db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    """Download all students as CSV."""
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    q = db.query(User).filter(User.role == UserRole.student, User.is_active == True)
    if department: q = q.filter(User.department == department)
    if batch_year:  q = q.filter(User.batch_year == batch_year)
    students = q.all()
    buf = io.StringIO()
    fields = ["Name","Roll Number","Email","Phone","Department","Batch Year",
              "CGPA","10th%","12th%","Backlogs","Skills","LinkedIn","Profile Score"]
    w = csv.DictWriter(buf, fieldnames=fields)
    w.writeheader()
    for s in students:
        c = _profile_completeness(s)
        w.writerow({
            "Name": s.name, "Roll Number": s.roll_number or "",
            "Email": s.email, "Phone": s.phone or "",
            "Department": s.department or "", "Batch Year": s.batch_year or "",
            "CGPA": s.cgpa or "", "10th%": s.tenth_percent or "",
            "12th%": s.twelfth_percent or "", "Backlogs": s.backlogs or 0,
            "Skills": ", ".join(s.skills or []),
            "LinkedIn": s.linkedin_url or "",
            "Profile Score": f"{c['score']}%",
        })
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=students.csv"})


@router.delete("/admin/deactivate/{user_id}")
def deactivate_user(user_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    if current_user.role not in {UserRole.head_admin}:
        raise HTTPException(403, "Admin only")
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(404, "User not found")
    user.is_active = False; db.commit()
    return {"message": "User deactivated"}
