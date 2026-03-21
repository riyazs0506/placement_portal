"""
routes/dashboard.py — Dashboard and analytics page routes.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import User, Exam, ExamSubmission, CampusDrive, DriveOptIn, Question, UserRole, OptStatus
from auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard/index.html", {"request": request})


@router.get("/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.student:
        subs = db.query(ExamSubmission).filter(ExamSubmission.student_id == current_user.id).all()
        opted_drives = db.query(DriveOptIn).filter(
            DriveOptIn.student_id == current_user.id,
            DriveOptIn.status == OptStatus.opted_in
        ).count()
        return {
            "exams_taken": len(subs),
            "exams_passed": sum(1 for s in subs if s.passed),
            "avg_score": round(sum(s.score for s in subs) / len(subs), 1) if subs else 0,
            "drives_opted": opted_drives,
        }

    total_students = db.query(User).filter(User.role == UserRole.student).count()
    total_exams = db.query(Exam).count()
    total_drives = db.query(CampusDrive).count()
    total_questions = db.query(Question).count()
    all_subs = db.query(ExamSubmission).all()

    return {
        "total_students": total_students,
        "total_exams": total_exams,
        "total_drives": total_drives,
        "total_questions": total_questions,
        "total_submissions": len(all_subs),
        "pass_rate": round(sum(1 for s in all_subs if s.passed) / len(all_subs) * 100, 1) if all_subs else 0,
    }
