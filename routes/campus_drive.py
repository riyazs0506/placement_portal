"""
routes/campus_drive.py — Campus Drive v2.3

NEW FEATURES:
  - Drive types: recruitment | internship | both
  - Stipend + internship duration fields
  - Planned rounds at drive creation time
  - HR manual student selection per round (click to select/reject/hold)
  - Download opted-in students list (CSV)
  - Download selected/rejected students after each round (CSV)
  - Auto-notify selected + rejected students after each round
  - Round progression: HR selects → next round auto-created or final offer
  - Full placement result lifecycle
"""
import csv, io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from database import get_db
from models import (
    User, UserRole, CampusDrive, DriveOptIn, DriveRound, DriveRoundResult,
    DriveStatus, OptStatus, RoundType, RoundStatus, Exam, ExamSubmission,
    ExamType, Notification, NotifType, NotificationRead, PlacementResult,
    PlacementStatus, DriveType, RoundShortlist,
    STAFF_ROLES, COMPANY_ROLES, OFFICER_ROLES
)
from auth import get_current_user
from services.websocket_manager import ws_manager

router = APIRouter(prefix="/campus-drive", tags=["campus-drive"])


# ═══════════════════════════════════════
# Helpers
# ═══════════════════════════════════════

def check_eligibility(student: User, drive: CampusDrive) -> dict:
    reasons, eligible = [], True
    depts   = drive.eligible_departments or []
    batches = drive.eligible_batches or []
    if depts and student.department not in depts:
        eligible = False; reasons.append(f"Department '{student.department}' not eligible")
    if batches and student.batch_year not in batches:
        eligible = False; reasons.append(f"Batch {student.batch_year} not eligible")
    if drive.min_cgpa and (student.cgpa or 0) < drive.min_cgpa:
        eligible = False; reasons.append(f"CGPA {student.cgpa or 0} < min {drive.min_cgpa}")
    if drive.min_tenth_percent and (student.tenth_percent or 0) < drive.min_tenth_percent:
        eligible = False; reasons.append(f"10th% too low")
    if drive.min_twelfth_percent and (student.twelfth_percent or 0) < drive.min_twelfth_percent:
        eligible = False; reasons.append(f"12th% too low")
    if (student.backlogs or 0) > drive.max_backlogs:
        eligible = False; reasons.append(f"Backlogs {student.backlogs} > allowed {drive.max_backlogs}")
    return {"eligible": eligible, "reasons": reasons}


def round_to_dict(r: DriveRound) -> dict:
    passed = sum(1 for x in r.results if x.passed)
    # Count HR shortlist selections
    shortlisted = [s for s in r.shortlist_entries] if hasattr(r, 'shortlist_entries') else []
    return {
        "id": r.id, "round_number": r.round_number,
        "round_type": r.round_type, "custom_name": r.custom_name,
        "description": r.description, "status": r.status,
        "passing_score": r.passing_score, "exam_id": r.exam_id,
        "passed_count": passed, "failed_count": len(r.results) - passed,
        "total_results": len(r.results),
    }


def drive_to_dict(drive: CampusDrive, db: Session, current_user: Optional[User] = None) -> dict:
    opted_in_count = db.query(DriveOptIn).filter(
        DriveOptIn.drive_id == drive.id, DriveOptIn.status == OptStatus.opted_in).count()
    d = {
        "id": drive.id, "title": drive.title, "job_role": drive.job_role,
        "job_description": drive.job_description, "package_lpa": drive.package_lpa,
        "location": drive.location,
        "company_name": drive.company.company_name if drive.company else "",
        "company_id": drive.company_id,
        "drive_type": drive.drive_type,
        "stipend_amount": drive.stipend_amount,
        "internship_duration": drive.internship_duration,
        "planned_rounds": drive.planned_rounds or [],
        "eligible_departments": drive.eligible_departments or [],
        "eligible_batches": drive.eligible_batches or [],
        "min_cgpa": drive.min_cgpa, "min_tenth_percent": drive.min_tenth_percent,
        "min_twelfth_percent": drive.min_twelfth_percent, "max_backlogs": drive.max_backlogs,
        "requested_date": drive.requested_date.isoformat() if drive.requested_date else None,
        "confirmed_date": drive.confirmed_date.isoformat() if drive.confirmed_date else None,
        "venue": drive.venue, "status": drive.status, "response_open": drive.response_open,
        "officer_notes": drive.officer_notes, "opted_in_count": opted_in_count,
        "created_at": drive.created_at.isoformat() if drive.created_at else None,
        "rounds": [round_to_dict(r) for r in drive.rounds],
    }
    if current_user and current_user.role == UserRole.student:
        opt = db.query(DriveOptIn).filter(
            DriveOptIn.drive_id == drive.id, DriveOptIn.student_id == current_user.id).first()
        d["my_opt_status"] = opt.status if opt else None
        d["eligibility"]   = check_eligibility(current_user, drive)
        pr = db.query(PlacementResult).filter(
            PlacementResult.drive_id == drive.id,
            PlacementResult.student_id == current_user.id).first()
        d["placement_result"] = {
            "status": pr.status, "offer_role": pr.offer_role,
            "offer_package_lpa": pr.offer_package_lpa,
            "joining_date": pr.joining_date,
            "has_offer_letter": bool(pr.offer_letter_text)
        } if pr else None
    return d


def _notify(db, sender_id, student_id, notif_type, title, message, drive_id=None):
    db.add(Notification(
        sender_id=sender_id, notif_type=notif_type,
        target_user_id=student_id, drive_id=drive_id,
        title=title, message=message))


def _students_csv(rows: list, fields: list) -> StreamingResponse:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction='ignore')
    w.writeheader()
    w.writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=students.csv"})


# ═══════════════════════════════════════
# Schemas
# ═══════════════════════════════════════

class DriveCreateSchema(BaseModel):
    title: str
    job_role: str
    job_description: Optional[str]    = None
    drive_type: DriveType             = DriveType.recruitment
    package_lpa: Optional[float]      = None
    stipend_amount: Optional[float]   = None
    internship_duration: Optional[str]= None
    location: Optional[str]           = None
    eligible_departments: List[str]   = []
    eligible_batches: List[int]       = []
    min_cgpa: Optional[float]         = None
    min_tenth_percent: Optional[float]= None
    min_twelfth_percent: Optional[float]=None
    max_backlogs: int                 = 0
    requested_date: Optional[datetime]= None
    venue: Optional[str]              = None
    planned_rounds: List[str]         = []   # ["aptitude","coding","technical","hr"]

class ApproveSchema(BaseModel):
    confirmed_date: Optional[datetime] = None
    officer_notes: Optional[str]       = None

class RoundCreateSchema(BaseModel):
    round_number: int
    round_type: RoundType             = RoundType.aptitude
    custom_name: Optional[str]        = None
    description: Optional[str]        = None
    passing_score: int                = 0
    exam_id: Optional[int]            = None
    shortlisted_students: Optional[List[int]] = None

class RoundSelectSchema(BaseModel):
    """HR taps each student as selected/rejected/hold."""
    selections: List[dict]   # [{student_id, status, notes}]

class NotifSchema(BaseModel):
    title: str
    message: str
    notif_type: NotifType
    target_role: Optional[str] = None

class PlacementResultSchema(BaseModel):
    student_id: int
    status: PlacementStatus
    offer_role: Optional[str]         = None
    offer_package_lpa: Optional[float]= None
    joining_date: Optional[str]       = None
    offer_letter_text: Optional[str]  = None
    notes: Optional[str]              = None


# ═══════════════════════════════════════
# Drive CRUD
# ═══════════════════════════════════════

@router.post("/create")
async def create_drive(data: DriveCreateSchema, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    if current_user.role not in COMPANY_ROLES:
        raise HTTPException(403, "Company access required")

    drive = CampusDrive(
        company_id=current_user.id, title=data.title, job_role=data.job_role,
        job_description=data.job_description,
        drive_type=data.drive_type, package_lpa=data.package_lpa,
        stipend_amount=data.stipend_amount, internship_duration=data.internship_duration,
        location=data.location, eligible_departments=data.eligible_departments,
        eligible_batches=data.eligible_batches, min_cgpa=data.min_cgpa,
        min_tenth_percent=data.min_tenth_percent, min_twelfth_percent=data.min_twelfth_percent,
        max_backlogs=data.max_backlogs, requested_date=data.requested_date,
        venue=data.venue, planned_rounds=data.planned_rounds, status=DriveStatus.pending)
    db.add(drive)
    db.flush()

    # Notify all placement officers
    for officer in db.query(User).filter(User.role == UserRole.placement_officer, User.is_active == True).all():
        db.add(Notification(
            sender_id=current_user.id, notif_type=NotifType.company_to_placement,
            target_user_id=officer.id, drive_id=drive.id,
            title=f"New Campus Drive: {drive.title}",
            message=f"{current_user.company_name} submitted a new {data.drive_type} drive for {data.job_role}. Please review and approve."))
    db.commit()
    db.refresh(drive)
    await ws_manager.broadcast({"type": "drive_created", "drive_id": drive.id})
    return {"message": "Drive created successfully", "drive_id": drive.id}


@router.get("/drives")
def list_drives(db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    is_company = current_user.role in COMPANY_ROLES
    is_staff   = current_user.role in STAFF_ROLES

    if is_company:
        drives = db.query(CampusDrive).filter(CampusDrive.company_id == current_user.id)\
                   .order_by(CampusDrive.created_at.desc()).all()
    elif is_staff:
        drives = db.query(CampusDrive).order_by(CampusDrive.created_at.desc()).all()
    else:
        # Students: approved drives with open response
        drives = db.query(CampusDrive).filter(
            CampusDrive.status.in_([DriveStatus.approved, DriveStatus.ongoing])
        ).order_by(CampusDrive.created_at.desc()).all()

    return [drive_to_dict(d, db, current_user) for d in drives]


@router.get("/drives/dashboard-preview")
def dashboard_drives(db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.student:
        return []
    interacted = db.query(DriveOptIn.drive_id).filter(
        DriveOptIn.student_id == current_user.id).subquery()
    drives = db.query(CampusDrive).filter(
        CampusDrive.status.in_([DriveStatus.approved, DriveStatus.ongoing]),
        CampusDrive.response_open == True,
        ~CampusDrive.id.in_(interacted)
    ).order_by(CampusDrive.created_at.desc()).limit(5).all()
    result = []
    for d in drives:
        elig = check_eligibility(current_user, d)
        if elig["eligible"]:
            result.append(drive_to_dict(d, db, current_user))
    return result


@router.get("/drives/{drive_id}")
def get_drive(drive_id: int, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    drive = db.query(CampusDrive).filter(CampusDrive.id == drive_id).first()
    if not drive: raise HTTPException(404, "Drive not found")
    return drive_to_dict(drive, db, current_user)


@router.post("/drives/{drive_id}/request-visit")
async def request_visit(drive_id: int, data: dict,
                        db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    drive = db.query(CampusDrive).filter(CampusDrive.id == drive_id).first()
    if not drive: raise HTTPException(404, "Not found")
    if current_user.id != drive.company_id and current_user.role not in COMPANY_ROLES:
        raise HTTPException(403, "Company only")
    if "requested_date" in data:
        drive.requested_date = datetime.fromisoformat(data["requested_date"])
    if "venue" in data:
        drive.venue = data.get("venue","")
    db.commit()
    return {"message": "Visit request updated"}


@router.post("/drives/{drive_id}/approve")
async def approve_drive(drive_id: int, data: ApproveSchema,
                        db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    if current_user.role not in OFFICER_ROLES:
        raise HTTPException(403, "Officer access required")
    drive = db.query(CampusDrive).filter(CampusDrive.id == drive_id).first()
    if not drive: raise HTTPException(404, "Not found")
    drive.status = DriveStatus.approved
    if data.confirmed_date: drive.confirmed_date = data.confirmed_date
    if data.officer_notes:  drive.officer_notes  = data.officer_notes
    drive.response_open = True

    # Notify company
    _notify(db, current_user.id, drive.company_id, NotifType.system,
            f"Drive Approved: {drive.title}",
            f"Your campus drive has been approved. Response is now open for students.",
            drive.id)
    db.commit()
    await ws_manager.broadcast({"type": "drive_approved", "drive_id": drive_id})
    return {"message": "Drive approved and response opened"}


@router.post("/drives/{drive_id}/reschedule")
async def reschedule_drive(drive_id: int, data: ApproveSchema,
                           db: Session = Depends(get_db),
                           current_user: User = Depends(get_current_user)):
    if current_user.role not in OFFICER_ROLES:
        raise HTTPException(403, "Officer access required")
    drive = db.query(CampusDrive).filter(CampusDrive.id == drive_id).first()
    if not drive: raise HTTPException(404, "Not found")
    drive.status = DriveStatus.rescheduled
    if data.confirmed_date: drive.confirmed_date = data.confirmed_date
    if data.officer_notes:  drive.officer_notes  = data.officer_notes
    _notify(db, current_user.id, drive.company_id, NotifType.system,
            f"Drive Rescheduled: {drive.title}",
            f"Drive has been rescheduled. Notes: {data.officer_notes or 'N/A'}", drive.id)
    db.commit()
    return {"message": "Drive rescheduled"}


@router.post("/drives/{drive_id}/reject")
async def reject_drive(drive_id: int, data: ApproveSchema,
                       db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    if current_user.role not in OFFICER_ROLES:
        raise HTTPException(403, "Officer access required")
    drive = db.query(CampusDrive).filter(CampusDrive.id == drive_id).first()
    if not drive: raise HTTPException(404, "Not found")
    drive.status = DriveStatus.rejected
    if data.officer_notes: drive.officer_notes = data.officer_notes
    _notify(db, current_user.id, drive.company_id, NotifType.system,
            f"Drive Rejected: {drive.title}",
            f"Your drive was rejected. Reason: {data.officer_notes or 'Not specified'}", drive.id)
    db.commit()
    return {"message": "Drive rejected"}


@router.put("/drives/{drive_id}/response-toggle")
async def toggle_response(drive_id: int, db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    drive = db.query(CampusDrive).filter(CampusDrive.id == drive_id).first()
    if not drive: raise HTTPException(404, "Not found")
    is_owner = current_user.id == drive.company_id
    is_officer = current_user.role in OFFICER_ROLES
    if not (is_owner or is_officer):
        raise HTTPException(403, "Only the company or placement officer can toggle response")
    drive.response_open = not drive.response_open
    db.commit()
    await ws_manager.broadcast({"type": "response_toggled", "drive_id": drive_id,
                                 "open": drive.response_open})
    return {"message": f"Response {'opened' if drive.response_open else 'closed'}",
            "response_open": drive.response_open}


# ═══════════════════════════════════════
# Opt In / Out
# ═══════════════════════════════════════

@router.post("/drives/{drive_id}/opt-in")
async def opt_in(drive_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.student:
        raise HTTPException(403, "Students only")
    drive = db.query(CampusDrive).filter(CampusDrive.id == drive_id).first()
    if not drive: raise HTTPException(404, "Drive not found")
    if not drive.response_open:
        raise HTTPException(400, "Response window is closed")
    elig = check_eligibility(current_user, drive)
    if not elig["eligible"]:
        raise HTTPException(400, f"Not eligible: {'; '.join(elig['reasons'])}")
    existing = db.query(DriveOptIn).filter(
        DriveOptIn.drive_id == drive_id, DriveOptIn.student_id == current_user.id).first()
    if existing:
        existing.status = OptStatus.opted_in
    else:
        db.add(DriveOptIn(drive_id=drive_id, student_id=current_user.id, status=OptStatus.opted_in))
    db.commit()
    await ws_manager.broadcast({"type": "optin_update", "drive_id": drive_id,
                                 "student_id": current_user.id})
    return {"message": "Opted in successfully"}


@router.post("/drives/{drive_id}/opt-out")
async def opt_out(drive_id: int, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.student:
        raise HTTPException(403, "Students only")
    existing = db.query(DriveOptIn).filter(
        DriveOptIn.drive_id == drive_id, DriveOptIn.student_id == current_user.id).first()
    if not existing: raise HTTPException(404, "Not opted in")
    existing.status = OptStatus.opted_out
    db.commit()
    return {"message": "Opted out"}


# ═══════════════════════════════════════
# Student Lists & Downloads
# ═══════════════════════════════════════

@router.get("/drives/{drive_id}/opted-students")
def opted_students(drive_id: int, filter_status: str = "opted_in",
                   db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    q = db.query(DriveOptIn).filter(DriveOptIn.drive_id == drive_id)
    if filter_status:
        q = q.filter(DriveOptIn.status == OptStatus(filter_status))
    opts = q.all()
    students = []
    for o in opts:
        s = o.student
        # Latest round result
        latest_round = None
        for rnd in db.query(DriveRound).filter(DriveRound.drive_id == drive_id)\
                      .order_by(DriveRound.round_number.desc()).all():
            res = db.query(DriveRoundResult).filter(
                DriveRoundResult.round_id == rnd.id,
                DriveRoundResult.student_id == s.id).first()
            if res:
                latest_round = {"round_number": rnd.round_number,
                                "passed": res.passed, "score": res.score}
                break
        pr = db.query(PlacementResult).filter(
            PlacementResult.drive_id == drive_id,
            PlacementResult.student_id == s.id).first()
        students.append({
            "student_id": s.id, "name": s.name, "email": s.email,
            "roll_number": s.roll_number, "department": s.department,
            "batch_year": s.batch_year, "cgpa": s.cgpa,
            "tenth_percent": s.tenth_percent, "twelfth_percent": s.twelfth_percent,
            "backlogs": s.backlogs, "phone": s.phone,
            "opt_status": o.status, "opted_at": o.opted_at.isoformat() if o.opted_at else None,
            "latest_round": latest_round,
            "placement_status": pr.status if pr else None,
        })
    return {"students": students, "total": len(students)}


@router.get("/drives/{drive_id}/opted-students/download")
def download_opted_students(drive_id: int,
                             db: Session = Depends(get_db),
                             current_user: User = Depends(get_current_user)):
    """Download opted-in students as CSV."""
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    opts = db.query(DriveOptIn).filter(
        DriveOptIn.drive_id == drive_id,
        DriveOptIn.status == OptStatus.opted_in).all()
    rows = []
    for o in opts:
        s = o.student
        rows.append({
            "Name": s.name, "Roll Number": s.roll_number or "",
            "Email": s.email, "Department": s.department or "",
            "Batch Year": s.batch_year or "", "CGPA": s.cgpa or "",
            "10th %": s.tenth_percent or "", "12th %": s.twelfth_percent or "",
            "Backlogs": s.backlogs or 0, "Phone": s.phone or "",
            "Opted At": o.opted_at.strftime("%Y-%m-%d %H:%M") if o.opted_at else "",
        })
    fields = ["Name","Roll Number","Email","Department","Batch Year","CGPA",
              "10th %","12th %","Backlogs","Phone","Opted At"]
    return _students_csv(rows, fields)


@router.get("/drives/{drive_id}/rounds/{round_id}/shortlist/download")
def download_round_shortlist(drive_id: int, round_id: int,
                              status: str = "selected",
                              db: Session = Depends(get_db),
                              current_user: User = Depends(get_current_user)):
    """Download selected or rejected students for a round as CSV."""
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    entries = db.query(RoundShortlist).filter(
        RoundShortlist.round_id == round_id,
        RoundShortlist.status == status).all()
    rows = []
    for e in entries:
        s = e.student
        rows.append({
            "Name": s.name, "Roll Number": s.roll_number or "",
            "Email": s.email, "Department": s.department or "",
            "Batch Year": s.batch_year or "", "CGPA": s.cgpa or "",
            "Round Status": e.status, "HR Notes": e.hr_notes or "",
            "Notified": "Yes" if e.notified else "No",
        })
    fields = ["Name","Roll Number","Email","Department","Batch Year","CGPA",
              "Round Status","HR Notes","Notified"]
    drive = db.query(CampusDrive).filter(CampusDrive.id == drive_id).first()
    rnd   = db.query(DriveRound).filter(DriveRound.id == round_id).first()
    fname = f"{getattr(drive,'title','drive')}_Round{getattr(rnd,'round_number',round_id)}_{status}.csv"
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction='ignore')
    w.writeheader(); w.writerows(rows); buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": f"attachment; filename={fname}"})


# ═══════════════════════════════════════
# Rounds
# ═══════════════════════════════════════

@router.post("/drives/{drive_id}/rounds")
async def create_round(drive_id: int, data: RoundCreateSchema,
                       db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    drive = db.query(CampusDrive).filter(CampusDrive.id == drive_id).first()
    if not drive: raise HTTPException(404, "Drive not found")
    if drive.response_open:
        raise HTTPException(400, "Close the response window before adding rounds")

    rnd = DriveRound(
        drive_id=drive_id, round_number=data.round_number,
        round_type=data.round_type, custom_name=data.custom_name,
        description=data.description, passing_score=data.passing_score,
        exam_id=data.exam_id, status=RoundStatus.pending)
    db.add(rnd)
    db.flush()

    # Notify opted-in students about this round
    opted = db.query(DriveOptIn).filter(
        DriveOptIn.drive_id == drive_id, DriveOptIn.status == OptStatus.opted_in).all()
    notified = data.shortlisted_students or [o.student_id for o in opted]
    for sid in notified:
        _notify(db, current_user.id, sid, NotifType.round_result,
                f"Round {data.round_number} Created — {drive.title}",
                f"Round {data.round_number} ({data.round_type}) has been created. "
                f"Please check the campus drive portal for details.",
                drive_id)
    db.commit()
    await ws_manager.broadcast({"type": "round_created", "drive_id": drive_id,
                                 "round_id": rnd.id})
    return {"message": "Round created", "round_id": rnd.id, "notified_count": len(notified)}


@router.delete("/rounds/{round_id}")
async def delete_round(round_id: int, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    rnd = db.query(DriveRound).filter(DriveRound.id == round_id).first()
    if not rnd: raise HTTPException(404, "Not found")
    db.delete(rnd); db.commit()
    return {"message": "Round deleted"}


@router.post("/rounds/{round_id}/complete")
async def complete_round(round_id: int, db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    """Mark round as completed. Auto-grades from exam submissions if linked."""
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    rnd = db.query(DriveRound).filter(DriveRound.id == round_id).first()
    if not rnd: raise HTTPException(404, "Not found")

    # If linked to campus exam, sync results from ExamSubmission
    if rnd.exam_id:
        subs = db.query(ExamSubmission).filter(ExamSubmission.exam_id == rnd.exam_id).all()
        for sub in subs:
            ex = db.query(DriveRoundResult).filter(
                DriveRoundResult.round_id == round_id,
                DriveRoundResult.student_id == sub.student_id).first()
            passed = sub.score >= rnd.passing_score
            if ex:
                ex.score = sub.score; ex.passed = passed
            else:
                db.add(DriveRoundResult(round_id=round_id, student_id=sub.student_id,
                                        score=sub.score, passed=passed))
    rnd.status = RoundStatus.completed
    db.commit()

    # Notify students of results (if not already via HR shortlist)
    results = db.query(DriveRoundResult).filter(DriveRoundResult.round_id == round_id).all()
    for res in results:
        if not res.notified:
            _notify(db, current_user.id, res.student_id, NotifType.round_result,
                    f"Round {rnd.round_number} Result — {rnd.drive.title}",
                    f"You {'passed' if res.passed else 'did not pass'} Round {rnd.round_number}.",
                    rnd.drive_id)
            res.notified = True
    db.commit()
    await ws_manager.broadcast({"type": "round_completed", "round_id": round_id,
                                 "drive_id": rnd.drive_id})
    return {"message": f"Round {rnd.round_number} completed",
            "total_results": len(results)}


@router.get("/rounds/{round_id}/results")
def get_round_results(round_id: int, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    results = db.query(DriveRoundResult).filter(DriveRoundResult.round_id == round_id).all()
    return [{"student_id": r.student_id, "name": r.student.name,
             "roll_number": r.student.roll_number, "email": r.student.email,
             "department": r.student.department,
             "score": r.score, "passed": r.passed, "notes": r.notes} for r in results]


@router.post("/rounds/{round_id}/results")
async def set_round_results(round_id: int, data: dict,
                            db: Session = Depends(get_db),
                            current_user: User = Depends(get_current_user)):
    """Manually set/update results for a round."""
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    rnd = db.query(DriveRound).filter(DriveRound.id == round_id).first()
    if not rnd: raise HTTPException(404, "Not found")
    results = data.get("results", [])
    for r in results:
        ex = db.query(DriveRoundResult).filter(
            DriveRoundResult.round_id == round_id,
            DriveRoundResult.student_id == r["student_id"]).first()
        if ex:
            ex.passed = r.get("passed", ex.passed)
            ex.score  = r.get("score", ex.score)
            ex.notes  = r.get("notes", ex.notes)
        else:
            db.add(DriveRoundResult(round_id=round_id, student_id=r["student_id"],
                                    passed=r.get("passed", False),
                                    score=r.get("score"), notes=r.get("notes")))
    db.commit()
    return {"message": "Results saved"}


# ═══════════════════════════════════════
# HR Round Selection (NEW v2.3)
# ═══════════════════════════════════════

@router.get("/rounds/{round_id}/students")
def round_students(round_id: int, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    """
    Returns all students eligible for this round.
    For round 1: all opted-in students.
    For round N: students selected in round N-1.
    """
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    rnd = db.query(DriveRound).filter(DriveRound.id == round_id).first()
    if not rnd: raise HTTPException(404, "Not found")

    drive_id = rnd.drive_id

    if rnd.round_number == 1:
        # All opted-in students
        opts = db.query(DriveOptIn).filter(
            DriveOptIn.drive_id == drive_id,
            DriveOptIn.status == OptStatus.opted_in).all()
        student_ids = [o.student_id for o in opts]
    else:
        # Students selected in previous round
        prev = db.query(DriveRound).filter(
            DriveRound.drive_id == drive_id,
            DriveRound.round_number == rnd.round_number - 1).first()
        if not prev:
            student_ids = []
        else:
            shortlists = db.query(RoundShortlist).filter(
                RoundShortlist.round_id == prev.id,
                RoundShortlist.status == "selected").all()
            student_ids = [s.student_id for s in shortlists]

    students = []
    for sid in student_ids:
        s = db.query(User).filter(User.id == sid).first()
        if not s: continue
        # Check if already selected/rejected in this round
        sl = db.query(RoundShortlist).filter(
            RoundShortlist.round_id == round_id,
            RoundShortlist.student_id == sid).first()
        # Round result (from exam)
        res = db.query(DriveRoundResult).filter(
            DriveRoundResult.round_id == round_id,
            DriveRoundResult.student_id == sid).first()
        students.append({
            "student_id": sid, "name": s.name, "email": s.email,
            "roll_number": s.roll_number or "", "department": s.department or "",
            "batch_year": s.batch_year, "cgpa": s.cgpa, "phone": s.phone,
            "exam_score": res.score if res else None,
            "exam_passed": res.passed if res else None,
            "hr_status": sl.status if sl else None,   # selected|rejected|hold|None
            "hr_notes": sl.hr_notes if sl else None,
        })
    return {"students": students, "round": round_to_dict(rnd), "total": len(students)}


@router.post("/rounds/{round_id}/select-students")
async def hr_select_students(round_id: int, data: RoundSelectSchema,
                             db: Session = Depends(get_db),
                             current_user: User = Depends(get_current_user)):
    """
    HR taps each student to mark as selected / rejected / hold.
    Sends notification to each student.
    """
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    rnd = db.query(DriveRound).filter(DriveRound.id == round_id).first()
    if not rnd: raise HTTPException(404, "Round not found")

    drive = db.query(CampusDrive).filter(CampusDrive.id == rnd.drive_id).first()
    notified_count = 0

    for sel in data.selections:
        sid    = sel.get("student_id")
        status = sel.get("status", "selected")   # selected|rejected|hold
        notes  = sel.get("notes", "")

        if status not in ("selected", "rejected", "hold"):
            continue

        # Upsert shortlist entry
        sl = db.query(RoundShortlist).filter(
            RoundShortlist.round_id == round_id,
            RoundShortlist.student_id == sid).first()
        if sl:
            old_status = sl.status
            sl.status   = status
            sl.hr_notes = notes
        else:
            old_status = None
            sl = RoundShortlist(round_id=round_id, student_id=sid,
                                status=status, hr_notes=notes)
            db.add(sl)
        db.flush()

        # Notify student if status changed
        if old_status != status:
            if status == "selected":
                title = f"✅ Selected for Round {rnd.round_number + 1} — {drive.title}"
                msg   = f"Congratulations! You have been selected by {drive.company.company_name} to proceed to Round {rnd.round_number + 1}. Keep it up!"
            elif status == "rejected":
                title = f"❌ Round {rnd.round_number} Result — {drive.title}"
                msg   = f"Thank you for participating in Round {rnd.round_number} of {drive.company.company_name}'s drive. Unfortunately, you have not been selected to proceed. We wish you the best!"
            else:  # hold
                title = f"⏸ On Hold — {drive.title}"
                msg   = f"Your application for Round {rnd.round_number} of {drive.company.company_name}'s drive is on hold. You will be notified soon."

            _notify(db, current_user.id, sid, NotifType.round_result,
                    title, msg, rnd.drive_id)
            sl.notified = True
            notified_count += 1

    db.commit()
    await ws_manager.broadcast({"type": "results_updated", "drive_id": rnd.drive_id,
                                 "round_id": round_id})
    return {"message": f"Selections saved. {notified_count} students notified."}


@router.get("/rounds/{round_id}/shortlist")
def get_round_shortlist(round_id: int, status: str = "",
                        db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    """Get HR shortlist for a round, optionally filtered by status."""
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    q = db.query(RoundShortlist).filter(RoundShortlist.round_id == round_id)
    if status:
        q = q.filter(RoundShortlist.status == status)
    entries = q.all()
    return [{
        "student_id": e.student_id, "name": e.student.name,
        "roll_number": e.student.roll_number or "", "email": e.student.email,
        "department": e.student.department or "", "batch_year": e.student.batch_year,
        "cgpa": e.student.cgpa, "status": e.status,
        "hr_notes": e.hr_notes, "notified": e.notified,
    } for e in entries]


# ═══════════════════════════════════════
# Placement Results & Offer Letters
# ═══════════════════════════════════════

@router.post("/drives/{drive_id}/placement-results")
async def set_placement_result(drive_id: int, data: PlacementResultSchema,
                               db: Session = Depends(get_db),
                               current_user: User = Depends(get_current_user)):
    if current_user.role not in (OFFICER_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Officer or company only")
    drive = db.query(CampusDrive).filter(CampusDrive.id == drive_id).first()
    if not drive: raise HTTPException(404, "Drive not found")

    pr = db.query(PlacementResult).filter(
        PlacementResult.drive_id == drive_id,
        PlacementResult.student_id == data.student_id).first()
    if pr:
        pr.status = data.status; pr.offer_role = data.offer_role
        pr.offer_package_lpa = data.offer_package_lpa; pr.joining_date = data.joining_date
        if data.offer_letter_text: pr.offer_letter_text = data.offer_letter_text
        pr.notes = data.notes
    else:
        pr = PlacementResult(
            drive_id=drive_id, student_id=data.student_id, status=data.status,
            offer_role=data.offer_role, offer_package_lpa=data.offer_package_lpa,
            joining_date=data.joining_date, offer_letter_text=data.offer_letter_text,
            notes=data.notes)
        db.add(pr)
    db.flush()

    # Notify student
    if data.status == PlacementStatus.selected:
        title = f"🎉 Offer Letter — {drive.title}"
        msg   = (f"Congratulations! You have been selected by {drive.company.company_name} "
                 f"for the role of {data.offer_role or drive.job_role}. "
                 f"Package: {data.offer_package_lpa} LPA. "
                 f"Your offer letter is available for download.")
    elif data.status == PlacementStatus.rejected:
        title = f"Drive Result — {drive.title}"
        msg   = (f"Thank you for participating in {drive.company.company_name}'s placement drive. "
                 f"Unfortunately, you have not been selected at this time.")
    elif data.status == PlacementStatus.shortlisted:
        title = f"⭐ Shortlisted — {drive.title}"
        msg   = f"You have been shortlisted by {drive.company.company_name}. Further rounds may follow."
    else:
        title = f"⏸ Application On Hold — {drive.title}"
        msg   = f"Your application with {drive.company.company_name} is currently on hold."

    _notify(db, current_user.id, data.student_id, NotifType.offer_letter, title, msg, drive_id)
    db.commit()
    await ws_manager.broadcast({"type": "placement_result", "drive_id": drive_id,
                                 "student_id": data.student_id})
    return {"message": "Placement result saved and student notified"}


@router.get("/drives/{drive_id}/placement-results")
def list_placement_results(drive_id: int, db: Session = Depends(get_db),
                           current_user: User = Depends(get_current_user)):
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    results = db.query(PlacementResult).filter(PlacementResult.drive_id == drive_id).all()
    return [{
        "student_id": r.student_id, "name": r.student.name,
        "roll_number": r.student.roll_number, "email": r.student.email,
        "department": r.student.department,
        "status": r.status, "offer_role": r.offer_role,
        "offer_package_lpa": r.offer_package_lpa, "joining_date": r.joining_date,
        "has_offer_letter": bool(r.offer_letter_text),
    } for r in results]


@router.get("/placement-results/mine")
def my_placement_results(db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.student:
        raise HTTPException(403, "Students only")
    results = db.query(PlacementResult).filter(
        PlacementResult.student_id == current_user.id).all()
    return [{
        "drive_id": r.drive_id,
        "drive_title": r.drive.title if r.drive else "",
        "company": r.drive.company.company_name if r.drive and r.drive.company else "",
        "status": r.status, "offer_role": r.offer_role,
        "offer_package_lpa": r.offer_package_lpa, "joining_date": r.joining_date,
        "has_offer_letter": bool(r.offer_letter_text),
    } for r in results]


@router.get("/drives/{drive_id}/offer-letter/{student_id}")
def download_offer_letter(drive_id: int, student_id: int,
                           db: Session = Depends(get_db),
                           current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.student and current_user.id != student_id:
        raise HTTPException(403, "You can only download your own offer letter")
    pr = db.query(PlacementResult).filter(
        PlacementResult.drive_id == drive_id,
        PlacementResult.student_id == student_id,
        PlacementResult.status == PlacementStatus.selected).first()
    if not pr: raise HTTPException(404, "Offer letter not found or not selected")
    if not pr.offer_letter_text: raise HTTPException(404, "Offer letter not yet uploaded")

    drive   = db.query(CampusDrive).filter(CampusDrive.id == drive_id).first()
    student = db.query(User).filter(User.id == student_id).first()
    company_name = drive.company.company_name if drive and drive.company else "Company"

    html_content = pr.offer_letter_text if "<html" in pr.offer_letter_text.lower() else f"""
<!DOCTYPE html><html><head><meta charset="UTF-8">
<title>Offer Letter – {drive.title if drive else 'Campus Drive'}</title>
<style>
  body{{font-family:Arial,sans-serif;max-width:800px;margin:40px auto;padding:40px;}}
  h1{{color:#1e293b;border-bottom:3px solid #2563eb;padding-bottom:10px;}}
  .meta{{color:#64748b;font-size:14px;margin-bottom:20px;line-height:1.8;}}
  .content{{line-height:1.9;color:#374151;}}
  .signature{{margin-top:50px;border-top:1px solid #e2e8f0;padding-top:20px;}}
  @media print{{body{{border:none;}}}}
</style></head><body>
<h1>Offer Letter</h1>
<div class="meta">
  <strong>To:</strong> {student.name if student else 'Student'} ({student.roll_number if student else ''})<br>
  <strong>Company:</strong> {company_name}<br>
  <strong>Role:</strong> {pr.offer_role or (drive.job_role if drive else 'N/A')}<br>
  <strong>Package:</strong> {pr.offer_package_lpa} LPA<br>
  {f'<strong>Joining Date:</strong> {pr.joining_date}<br>' if pr.joining_date else ''}
  <strong>Date:</strong> {datetime.now().strftime('%d %B %Y')}
</div>
<div class="content">{pr.offer_letter_text}</div>
<div class="signature">
  <p><strong>Authorized Signatory</strong><br>{company_name}<br>HR Department</p>
</div>
</body></html>"""

    safe_name = f"offer_letter_{drive_id}_{student_id}.html"
    return HTMLResponse(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}"',
            "Cache-Control": "no-cache",
        },
    )




@router.get("/drives/{drive_id}/master-download")
def download_master_report(drive_id: int,
                            db: Session = Depends(get_db),
                            current_user: User = Depends(get_current_user)):
    """
    Single ZIP-like CSV with all stages:
      Sheet 1: All opted-in students
      Sheet 2: Round-by-round selections
      Sheet 3: Final placed students
    Returns a CSV with a 'Stage' column so it can be filtered in Excel.
    """
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")

    drive = db.query(CampusDrive).filter(CampusDrive.id == drive_id).first()
    if not drive: raise HTTPException(404, "Drive not found")

    rows = []
    FIELDS = [
        "Stage","Name","Roll Number","Email","Department","Batch Year",
        "CGPA","10th %","12th %","Backlogs","Phone",
        "Round","HR Status","HR Notes","Exam Score","Offer Role","Package (LPA)","Joining Date"
    ]

    # ── Section 1: All opted-in ──
    opts = db.query(DriveOptIn).filter(
        DriveOptIn.drive_id == drive_id,
        DriveOptIn.status == OptStatus.opted_in).all()
    for o in opts:
        s = o.student
        rows.append({
            "Stage": "Opted In",
            "Name": s.name, "Roll Number": s.roll_number or "",
            "Email": s.email, "Department": s.department or "",
            "Batch Year": s.batch_year or "", "CGPA": s.cgpa or "",
            "10th %": s.tenth_percent or "", "12th %": s.twelfth_percent or "",
            "Backlogs": s.backlogs or 0, "Phone": s.phone or "",
            "Round":"","HR Status":"","HR Notes":"","Exam Score":"",
            "Offer Role":"","Package (LPA)":"","Joining Date":"",
        })

    # ── Section 2: Round selections ──
    rounds = db.query(DriveRound).filter(
        DriveRound.drive_id == drive_id).order_by(DriveRound.round_number).all()
    for rnd in rounds:
        shortlist = db.query(RoundShortlist).filter(
            RoundShortlist.round_id == rnd.id).all()
        for e in shortlist:
            s = e.student
            res = db.query(DriveRoundResult).filter(
                DriveRoundResult.round_id == rnd.id,
                DriveRoundResult.student_id == s.id).first()
            rows.append({
                "Stage": f"Round {rnd.round_number} — {rnd.round_type.value}",
                "Name": s.name, "Roll Number": s.roll_number or "",
                "Email": s.email, "Department": s.department or "",
                "Batch Year": s.batch_year or "", "CGPA": s.cgpa or "",
                "10th %": s.tenth_percent or "", "12th %": s.twelfth_percent or "",
                "Backlogs": s.backlogs or 0, "Phone": s.phone or "",
                "Round": rnd.round_number,
                "HR Status": e.status,
                "HR Notes": e.hr_notes or "",
                "Exam Score": res.score if res else "",
                "Offer Role":"","Package (LPA)":"","Joining Date":"",
            })

    # ── Section 3: Final placed ──
    placed = db.query(PlacementResult).filter(
        PlacementResult.drive_id == drive_id).all()
    for p in placed:
        s = p.student
        rows.append({
            "Stage": f"Final — {p.status.value}",
            "Name": s.name, "Roll Number": s.roll_number or "",
            "Email": s.email, "Department": s.department or "",
            "Batch Year": s.batch_year or "", "CGPA": s.cgpa or "",
            "10th %": s.tenth_percent or "", "12th %": s.twelfth_percent or "",
            "Backlogs": s.backlogs or 0, "Phone": s.phone or "",
            "Round":"","HR Status": p.status.value,"HR Notes":"","Exam Score":"",
            "Offer Role": p.offer_role or "",
            "Package (LPA)": p.offer_package_lpa or "",
            "Joining Date": p.joining_date or "",
        })

    fname = f"{drive.title.replace(' ','_')}_MasterReport.csv"
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, extrasaction='ignore')
    w.writeheader(); w.writerows(rows); buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": f"attachment; filename={fname}"})


@router.get("/drives/{drive_id}/placed-students/download")
def download_placed_students(drive_id: int,
                              db: Session = Depends(get_db),
                              current_user: User = Depends(get_current_user)):
    """Download only final-selected (placed) students."""
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    placed = db.query(PlacementResult).filter(
        PlacementResult.drive_id == drive_id,
        PlacementResult.status == PlacementStatus.selected).all()
    rows = []
    for p in placed:
        s = p.student
        rows.append({
            "Name": s.name, "Roll Number": s.roll_number or "",
            "Email": s.email, "Phone": s.phone or "",
            "Department": s.department or "", "Batch Year": s.batch_year or "",
            "CGPA": s.cgpa or "", "LinkedIn": s.linkedin_url or "",
            "Offer Role": p.offer_role or "",
            "Package (LPA)": p.offer_package_lpa or "",
            "Joining Date": p.joining_date or "",
        })
    drive = db.query(CampusDrive).filter(CampusDrive.id == drive_id).first()
    fname = f"{getattr(drive,'title','drive').replace(' ','_')}_PlacedStudents.csv"
    buf = io.StringIO()
    fields = ["Name","Roll Number","Email","Phone","Department","Batch Year","CGPA",
              "LinkedIn","Offer Role","Package (LPA)","Joining Date"]
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction='ignore')
    w.writeheader(); w.writerows(rows); buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": f"attachment; filename={fname}"})

# ═══════════════════════════════════════
# Stats & Notifications
# ═══════════════════════════════════════

@router.get("/overview/stats")
def overview_stats(db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    if current_user.role in COMPANY_ROLES:
        drives = db.query(CampusDrive).filter(CampusDrive.company_id == current_user.id).all()
    else:
        drives = db.query(CampusDrive).all()
    drive_ids = [d.id for d in drives]
    return {
        "total_drives":   len(drives),
        "pending":        sum(1 for d in drives if d.status == DriveStatus.pending),
        "approved":       sum(1 for d in drives if d.status == DriveStatus.approved),
        "completed":      sum(1 for d in drives if d.status == DriveStatus.completed),
        "total_selected": db.query(PlacementResult).filter(
            PlacementResult.drive_id.in_(drive_ids),
            PlacementResult.status == PlacementStatus.selected).count() if drive_ids else 0,
        "total_opted_in": db.query(DriveOptIn).filter(
            DriveOptIn.drive_id.in_(drive_ids),
            DriveOptIn.status == OptStatus.opted_in).count() if drive_ids else 0,
    }


@router.post("/drives/{drive_id}/notify")
async def send_drive_notification(drive_id: int, data: NotifSchema,
                                  db: Session = Depends(get_db),
                                  current_user: User = Depends(get_current_user)):
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    drive = db.query(CampusDrive).filter(CampusDrive.id == drive_id).first()
    if not drive: raise HTTPException(404, "Drive not found")
    if data.notif_type == NotifType.company_to_students:
        opts = db.query(DriveOptIn).filter(
            DriveOptIn.drive_id == drive_id, DriveOptIn.status == OptStatus.opted_in).all()
        for o in opts:
            _notify(db, current_user.id, o.student_id, data.notif_type,
                    data.title, data.message, drive_id)
    elif data.notif_type == NotifType.company_to_placement:
        for officer in db.query(User).filter(User.role == UserRole.placement_officer).all():
            _notify(db, current_user.id, officer.id, data.notif_type,
                    data.title, data.message, drive_id)
    else:
        db.add(Notification(sender_id=current_user.id, notif_type=data.notif_type,
                            drive_id=drive_id, title=data.title, message=data.message))
    db.commit()
    return {"message": "Notification sent"}


@router.get("/notifications/mine")
def my_notifications(db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    read_ids = {r.notification_id for r in db.query(NotificationRead).filter(
        NotificationRead.user_id == current_user.id).all()}
    notifs = db.query(Notification).filter(
        or_(
            Notification.target_user_id == current_user.id,
            and_(Notification.target_user_id.is_(None),
                 Notification.target_role == current_user.role.value),
            and_(Notification.target_user_id.is_(None),
                 Notification.target_role.is_(None))
        )
    ).order_by(Notification.created_at.desc()).limit(50).all()
    return [{
        "id": n.id, "title": n.title, "message": n.message,
        "notif_type": n.notif_type, "drive_id": n.drive_id,
        "created_at": n.created_at.isoformat() if n.created_at else None,
        "is_read": n.id in read_ids,
    } for n in notifs]


@router.post("/notifications/{notif_id}/read")
def mark_read(notif_id: int, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    ex = db.query(NotificationRead).filter(
        NotificationRead.notification_id == notif_id,
        NotificationRead.user_id == current_user.id).first()
    if not ex:
        db.add(NotificationRead(notification_id=notif_id, user_id=current_user.id))
        db.commit()
    return {"message": "Marked read"}


@router.post("/notifications/read-all")
def mark_all_read(db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    notifs = db.query(Notification).filter(
        or_(Notification.target_user_id == current_user.id,
            Notification.target_role == current_user.role.value)).all()
    existing = {r.notification_id for r in db.query(NotificationRead).filter(
        NotificationRead.user_id == current_user.id).all()}
    for n in notifs:
        if n.id not in existing:
            db.add(NotificationRead(notification_id=n.id, user_id=current_user.id))
    db.commit()
    return {"message": "All marked read"}


@router.get("/notifications/unread-count")
def unread_count(db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    read_ids = {r.notification_id for r in db.query(NotificationRead).filter(
        NotificationRead.user_id == current_user.id).all()}
    total = db.query(Notification).filter(
        or_(Notification.target_user_id == current_user.id,
            Notification.target_role == current_user.role.value)).count()
    return {"unread": max(0, total - len(read_ids))}


# ═══════════════════════════════════════════════════════════════
# COMPREHENSIVE DOWNLOAD SYSTEM (v2.3)
# ═══════════════════════════════════════════════════════════════

def _safe_filename(name: str) -> str:
    """Strip non-ASCII and spaces for safe Content-Disposition header."""
    import re
    name = re.sub(r"[^\w\-.]", "_", name.replace(" ", "_"))
    return name[:80] if len(name) > 80 else name


def _make_csv(rows: list, fields: list, filename: str) -> StreamingResponse:
    """
    Build a UTF-8 CSV with BOM so Excel on Windows opens it correctly.
    Adds Content-Disposition with properly quoted filename.
    """
    buf = io.StringIO()
    # UTF-8 BOM so Excel auto-detects encoding
    buf.write("\ufeff")
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore",
                       lineterminator="\r\n")
    w.writeheader()
    w.writerows(rows)
    buf.seek(0)
    safe = _safe_filename(filename)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={
            "Content-Disposition": f'attachment; filename="{safe}"',
            "Content-Type": "text/csv; charset=utf-8-sig",
            "Cache-Control": "no-cache",
        },
    )


@router.get("/drives/{drive_id}/download/opted-in")
def dl_opted_in(drive_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    """All opted-in students for a drive."""
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    drive = db.query(CampusDrive).filter(CampusDrive.id == drive_id).first()
    if not drive: raise HTTPException(404, "Drive not found")
    opts = db.query(DriveOptIn).filter(
        DriveOptIn.drive_id == drive_id, DriveOptIn.status == OptStatus.opted_in).all()
    rows = []
    for o in opts:
        s = o.student
        pr = db.query(PlacementResult).filter(
            PlacementResult.drive_id == drive_id, PlacementResult.student_id == s.id).first()
        rows.append({
            "Name": s.name, "Roll Number": s.roll_number or "",
            "Email": s.email, "Phone": s.phone or "",
            "Department": s.department or "", "Batch Year": s.batch_year or "",
            "CGPA": s.cgpa or "", "10th%": s.tenth_percent or "",
            "12th%": s.twelfth_percent or "", "Backlogs": s.backlogs or 0,
            "Skills": ", ".join(s.skills or []),
            "LinkedIn": s.linkedin_url or "", "Resume": s.resume_url or "",
            "Opted At": o.opted_at.strftime("%Y-%m-%d %H:%M") if o.opted_at else "",
            "Final Status": pr.status if pr else "In Progress",
        })
    fields = ["Name","Roll Number","Email","Phone","Department","Batch Year",
              "CGPA","10th%","12th%","Backlogs","Skills","LinkedIn","Resume",
              "Opted At","Final Status"]
    fname = f"{drive.title.replace(' ','_')}_opted_in.csv"
    return _make_csv(rows, fields, fname)


@router.get("/drives/{drive_id}/download/round/{round_num}")
def dl_round_selected(drive_id: int, round_num: int,
                      db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    """Students selected by HR in a specific round."""
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    drive = db.query(CampusDrive).filter(CampusDrive.id == drive_id).first()
    if not drive: raise HTTPException(404, "Drive not found")
    rnd = db.query(DriveRound).filter(
        DriveRound.drive_id == drive_id, DriveRound.round_number == round_num).first()
    if not rnd: raise HTTPException(404, f"Round {round_num} not found")
    # Get HR shortlist selections for this round
    entries = db.query(RoundShortlist).filter(RoundShortlist.round_id == rnd.id).all()
    rows = []
    for e in entries:
        s = e.student
        res = db.query(DriveRoundResult).filter(
            DriveRoundResult.round_id == rnd.id,
            DriveRoundResult.student_id == s.id).first()
        rows.append({
            "Name": s.name, "Roll Number": s.roll_number or "",
            "Email": s.email, "Phone": s.phone or "",
            "Department": s.department or "", "Batch Year": s.batch_year or "",
            "CGPA": s.cgpa or "",
            "Exam Score": res.score if res else "",
            "Exam Result": ("Pass" if res.passed else "Fail") if res else "",
            "HR Decision": e.status,  # selected|rejected|hold
            "HR Notes": e.hr_notes or "",
            "Notified": "Yes" if e.notified else "No",
        })
    fields = ["Name","Roll Number","Email","Phone","Department","Batch Year",
              "CGPA","Exam Score","Exam Result","HR Decision","HR Notes","Notified"]
    fname = f"{drive.title.replace(' ','_')}_Round{round_num}_results.csv"
    return _make_csv(rows, fields, fname)


@router.get("/drives/{drive_id}/download/placed")
def dl_placed_students(drive_id: int, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    """Final placed (selected) students only."""
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    drive = db.query(CampusDrive).filter(CampusDrive.id == drive_id).first()
    if not drive: raise HTTPException(404, "Drive not found")
    results = db.query(PlacementResult).filter(
        PlacementResult.drive_id == drive_id,
        PlacementResult.status == PlacementStatus.selected).all()
    rows = []
    for r in results:
        s = r.student
        rows.append({
            "Name": s.name, "Roll Number": s.roll_number or "",
            "Email": s.email, "Phone": s.phone or "",
            "Department": s.department or "", "Batch Year": s.batch_year or "",
            "CGPA": s.cgpa or "",
            "Offer Role": r.offer_role or drive.job_role,
            "Package LPA": r.offer_package_lpa or drive.package_lpa or "",
            "Joining Date": r.joining_date or "",
            "Offer Letter": "Yes" if r.offer_letter_text else "No",
            "LinkedIn": s.linkedin_url or "",
        })
    fields = ["Name","Roll Number","Email","Phone","Department","Batch Year",
              "CGPA","Offer Role","Package LPA","Joining Date","Offer Letter","LinkedIn"]
    fname = f"{drive.title.replace(' ','_')}_placed_students.csv"
    return _make_csv(rows, fields, fname)


@router.get("/drives/{drive_id}/download/full-report")
def dl_full_report(drive_id: int, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    """Complete drive report: all opted-in students with round results and final status."""
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    drive = db.query(CampusDrive).filter(CampusDrive.id == drive_id).first()
    if not drive: raise HTTPException(404, "Drive not found")
    opts = db.query(DriveOptIn).filter(
        DriveOptIn.drive_id == drive_id, DriveOptIn.status == OptStatus.opted_in).all()
    rounds = db.query(DriveRound).filter(
        DriveRound.drive_id == drive_id).order_by(DriveRound.round_number).all()
    rows = []
    base_fields = ["Name","Roll Number","Email","Phone","Department","Batch Year","CGPA","10th%","12th%","Backlogs"]
    round_fields = []
    for rnd in rounds:
        round_fields += [f"R{rnd.round_number} Score", f"R{rnd.round_number} Result", f"R{rnd.round_number} HR Decision"]
    extra_fields = ["Final Status","Offer Role","Package LPA","Joining Date"]
    all_fields = base_fields + round_fields + extra_fields

    for o in opts:
        s = o.student
        pr = db.query(PlacementResult).filter(
            PlacementResult.drive_id == drive_id, PlacementResult.student_id == s.id).first()
        row = {
            "Name": s.name, "Roll Number": s.roll_number or "",
            "Email": s.email, "Phone": s.phone or "",
            "Department": s.department or "", "Batch Year": s.batch_year or "",
            "CGPA": s.cgpa or "", "10th%": s.tenth_percent or "",
            "12th%": s.twelfth_percent or "", "Backlogs": s.backlogs or 0,
        }
        for rnd in rounds:
            res = db.query(DriveRoundResult).filter(
                DriveRoundResult.round_id == rnd.id,
                DriveRoundResult.student_id == s.id).first()
            sl = db.query(RoundShortlist).filter(
                RoundShortlist.round_id == rnd.id,
                RoundShortlist.student_id == s.id).first()
            row[f"R{rnd.round_number} Score"]       = res.score if res else ""
            row[f"R{rnd.round_number} Result"]      = ("Pass" if res.passed else "Fail") if res else ""
            row[f"R{rnd.round_number} HR Decision"] = sl.status if sl else ""
        row["Final Status"]  = pr.status if pr else "In Progress"
        row["Offer Role"]    = pr.offer_role if pr else ""
        row["Package LPA"]   = pr.offer_package_lpa if pr else ""
        row["Joining Date"]  = pr.joining_date if pr else ""
        rows.append(row)

    fname = f"{drive.title.replace(' ','_')}_full_report.csv"
    return _make_csv(rows, all_fields, fname)


@router.get("/drives/{drive_id}/download-summary")
def drive_download_summary(drive_id: int, db: Session = Depends(get_db),
                            current_user: User = Depends(get_current_user)):
    """Returns available download links for this drive."""
    if current_user.role not in (STAFF_ROLES | COMPANY_ROLES):
        raise HTTPException(403, "Staff or company only")
    drive = db.query(CampusDrive).filter(CampusDrive.id == drive_id).first()
    if not drive: raise HTTPException(404, "Drive not found")
    rounds = db.query(DriveRound).filter(
        DriveRound.drive_id == drive_id).order_by(DriveRound.round_number).all()
    opted_count = db.query(DriveOptIn).filter(
        DriveOptIn.drive_id == drive_id, DriveOptIn.status == OptStatus.opted_in).count()
    placed_count = db.query(PlacementResult).filter(
        PlacementResult.drive_id == drive_id,
        PlacementResult.status == PlacementStatus.selected).count()
    return {
        "drive_title": drive.title,
        "opted_in_count": opted_count,
        "placed_count": placed_count,
        "downloads": [
            {"label": f"All Opted-In Students ({opted_count})",
             "url": f"/api/campus-drive/drives/{drive_id}/download/opted-in",
             "icon": "fa-users", "color": "#2563eb"},
        ] + [
            {"label": f"Round {r.round_number} — {r.custom_name or r.round_type.title()} Results",
             "url": f"/api/campus-drive/drives/{drive_id}/download/round/{r.round_number}",
             "icon": "fa-list-check", "color": "#7c3aed"}
            for r in rounds
        ] + [
            {"label": f"Final Placed Students ({placed_count})",
             "url": f"/api/campus-drive/drives/{drive_id}/download/placed",
             "icon": "fa-trophy", "color": "#16a34a"},
            {"label": "Full Drive Report (All rounds + all students)",
             "url": f"/api/campus-drive/drives/{drive_id}/download/full-report",
             "icon": "fa-file-excel", "color": "#059669"},
        ]
    }
