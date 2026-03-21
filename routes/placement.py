"""
routes/placement.py — Placement results, offer letters, analytics dashboard.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from database import get_db
from models import (User, UserRole, CampusDrive, PlacementResult, PlacementStatus,
                    DriveOptIn, OptStatus, STAFF_ROLES, COMPANY_ROLES)
from auth import get_current_user

router = APIRouter(prefix="/placement", tags=["placement"])


@router.get("/stats/college")
def college_placement_stats(db: Session = Depends(get_db),
                              current_user: User = Depends(get_current_user)):
    """Overall college placement statistics — for head/officer/staff."""
    if current_user.role not in STAFF_ROLES:
        raise HTTPException(403, "Staff access required")
    total_students = db.query(User).filter(User.role == UserRole.student, User.is_active == True).count()
    total_drives = db.query(CampusDrive).count()
    approved_drives = db.query(CampusDrive).filter(
        CampusDrive.status.in_(["approved","ongoing","completed"])).count()
    selected = db.query(PlacementResult).filter(
        PlacementResult.status == PlacementStatus.selected).count()
    opted_in = db.query(DriveOptIn).filter(DriveOptIn.status == OptStatus.opted_in).count()
    companies = db.query(func.count(func.distinct(CampusDrive.company_id))).scalar()
    return {
        "total_students": total_students,
        "total_drives": total_drives,
        "approved_drives": approved_drives,
        "students_selected": selected,
        "placement_rate": round(selected / total_students * 100, 1) if total_students else 0,
        "students_opted_in": opted_in,
        "companies_visiting": companies,
    }


@router.get("/stats/student")
def student_placement_stats(db: Session = Depends(get_db),
                              current_user: User = Depends(get_current_user)):
    """Personal placement stats for a student."""
    if current_user.role != UserRole.student:
        raise HTTPException(403, "Students only")
    opted = db.query(DriveOptIn).filter(
        DriveOptIn.student_id == current_user.id, DriveOptIn.status == OptStatus.opted_in).count()
    results = db.query(PlacementResult).filter(
        PlacementResult.student_id == current_user.id).all()
    selected = [r for r in results if r.status == PlacementStatus.selected]
    return {
        "drives_opted": opted,
        "drives_applied": len(results),
        "shortlisted": sum(1 for r in results if r.status == PlacementStatus.shortlisted),
        "selected": len(selected),
        "rejected": sum(1 for r in results if r.status == PlacementStatus.rejected),
        "offer_letters_available": sum(1 for r in selected if r.offer_letter_text),
    }
