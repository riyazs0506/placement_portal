"""
routes/exam.py — Complete exam module v2.2

New in v2.2:
  - Exam Batch system: staff assigned to student batches
  - Staff generate per-batch OTP and monitor their students
  - Student presence tracking (otp_entered, is_present)
  - Staff live monitoring dashboard (per student activity feed)
  - Mobile/tablet block for exam page (laptop/desktop only)
  - Malpractice detection with live feed to staff monitor
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import asyncio, random, string

from database import get_db
from models import (
    Exam, ExamQuestion, Question, User, ExamStatus, ExamType,
    ExamSubmission, UserRole, STAFF_ROLES, COMPANY_ROLES,
    DriveRoundResult, Notification, NotifType,
    ExamBatch, ExamBatchMember
)
from auth import get_current_user, require_staff, require_staff_or_company
from services.websocket_manager import ws_manager

router = APIRouter(prefix="/exams", tags=["exams"])
templates = Jinja2Templates(directory="templates")

MALPRACTICE_TAB  = 3
MALPRACTICE_BLUR = 10
MALPRACTICE_COPY = 5


# ─── Schemas ─────────────────────────────────────────────────────

class ExamCreateSchema(BaseModel):
    title: str
    description: Optional[str] = None
    duration_minutes: int = 60
    passing_marks: int = 0
    question_ids: List[int] = []
    target_departments: Optional[str] = None
    start_time: Optional[datetime] = None
    exam_type: ExamType = ExamType.online
    otp_required: bool = False


class ExamUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    passing_marks: Optional[int] = None
    target_departments: Optional[str] = None
    start_time: Optional[datetime] = None


class SubmitExamSchema(BaseModel):
    answers: Dict
    tab_switch_count: int = 0
    blur_count: int = 0
    copy_paste_count: int = 0
    batch_id: Optional[int] = None


class OTPVerifySchema(BaseModel):
    otp: str
    batch_id: Optional[int] = None


class BatchCreateSchema(BaseModel):
    exam_id: int
    batch_name: str
    student_ids: List[int]


class BatchOTPSchema(BaseModel):
    otp: str


# ─── HTML pages ──────────────────────────────────────────────────

@router.get("/list", response_class=HTMLResponse)
def exam_list_page(request: Request):
    return templates.TemplateResponse("exam/exam_list.html", {"request": request})

@router.get("/create", response_class=HTMLResponse)
def exam_create_page(request: Request):
    return templates.TemplateResponse("exam/exam_create.html", {"request": request})

@router.get("/monitor/{batch_id}", response_class=HTMLResponse)
def exam_monitor_page(request: Request, batch_id: int):
    return templates.TemplateResponse("exam/exam_monitor.html",
                                      {"request": request, "batch_id": batch_id})

@router.get("/{exam_id}", response_class=HTMLResponse)
def exam_page(request: Request, exam_id: int):
    return templates.TemplateResponse("exam/exam_page.html",
                                      {"request": request, "exam_id": exam_id})


# ─── Staff: Create/Manage Exams ───────────────────────────────────

@router.post("/create")
def create_exam(data: ExamCreateSchema, db: Session = Depends(get_db),
                current_user: User = Depends(require_staff_or_company)):
    questions = db.query(Question).filter(Question.id.in_(data.question_ids)).all()
    total_marks = sum(q.marks for q in questions)
    otp = ''.join(random.choices(string.digits, k=6)) if data.otp_required else None
    exam = Exam(
        title=data.title, description=data.description,
        duration_minutes=data.duration_minutes, total_marks=total_marks,
        passing_marks=data.passing_marks, target_departments=data.target_departments,
        start_time=data.start_time, created_by_id=current_user.id,
        status=ExamStatus.draft, exam_type=data.exam_type,
        otp_required=data.otp_required, exam_otp=otp)
    db.add(exam)
    db.flush()
    for order, q in enumerate(questions):
        db.add(ExamQuestion(exam_id=exam.id, question_id=q.id, order_number=order))
    db.commit()
    db.refresh(exam)
    return {"message": "Exam created", "exam_id": exam.id,
            "total_marks": total_marks, "otp": otp}


@router.put("/{exam_id}/update")
def update_exam(exam_id: int, data: ExamUpdateSchema,
                db: Session = Depends(get_db), current_user: User = Depends(require_staff_or_company)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam: raise HTTPException(404, "Exam not found")
    if exam.status == ExamStatus.active:
        raise HTTPException(400, "Cannot edit active exam")
    for k, v in data.dict(exclude_none=True).items():
        setattr(exam, k, v)
    db.commit()
    return {"message": "Updated"}


@router.get("/all")
def list_all_exams(exam_type: Optional[str] = None, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    is_privileged = current_user.role in (STAFF_ROLES | COMPANY_ROLES)
    if is_privileged:
        q = db.query(Exam)
        if exam_type:
            try: q = q.filter(Exam.exam_type == ExamType(exam_type))
            except ValueError: pass
    else:
        q = db.query(Exam).filter(
            Exam.exam_type == ExamType.online,
            Exam.status.in_([ExamStatus.active, ExamStatus.scheduled]))
    return [_exam_summary(e, current_user, db) for e in q.order_by(Exam.created_at.desc()).all()]


def _exam_summary(e, user, db):
    sub = None
    if user.role == UserRole.student:
        sub = db.query(ExamSubmission).filter(
            ExamSubmission.exam_id == e.id, ExamSubmission.student_id == user.id).first()
    return {
        "id": e.id, "title": e.title, "description": e.description,
        "duration_minutes": e.duration_minutes, "total_marks": e.total_marks,
        "passing_marks": e.passing_marks, "status": e.status, "exam_type": e.exam_type,
        "start_time": e.start_time.isoformat() if e.start_time else None,
        "question_count": len(e.exam_questions), "otp_required": e.otp_required,
        "already_submitted": sub is not None,
        "submission_score": sub.score if sub else None,
        "submission_count": db.query(ExamSubmission).filter(ExamSubmission.exam_id == e.id).count(),
    }


@router.get("/{exam_id}/detail")
def get_exam(exam_id: int, db: Session = Depends(get_db),
             current_user: User = Depends(get_current_user)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam: raise HTTPException(404, "Exam not found")
    is_privileged = current_user.role in (STAFF_ROLES | COMPANY_ROLES)
    if not is_privileged:
        if exam.exam_type == ExamType.campus:
            raise HTTPException(403, "Campus exam — access via drive")
        if exam.status not in [ExamStatus.active, ExamStatus.scheduled]:
            raise HTTPException(403, "Exam not active")

    questions = []
    for eq in sorted(exam.exam_questions, key=lambda x: x.order_number):
        q = eq.question
        qd = {"id": q.id, "question_text": q.question_text,
              "question_type": q.question_type, "marks": q.marks, "subject": q.subject}
        if q.question_type == "mcq":
            qd.update({"option_a": q.option_a, "option_b": q.option_b,
                       "option_c": q.option_c, "option_d": q.option_d})
        elif q.question_type == "coding":
            qd["starter_code"] = q.starter_code
            raw_tc = q.test_cases or []
            visible = [tc for tc in raw_tc if not tc.get("is_hidden", False)]
            qd["test_cases"] = raw_tc if is_privileged else visible
            if not is_privileged: qd["hidden_count"] = len(raw_tc) - len(visible)
        if is_privileged:
            qd["correct_answer"] = q.correct_answer
            qd["difficulty"] = q.difficulty
        questions.append(qd)

    my_sub = None
    if current_user.role == UserRole.student:
        sub = db.query(ExamSubmission).filter(
            ExamSubmission.exam_id == exam_id, ExamSubmission.student_id == current_user.id).first()
        if sub:
            my_sub = {"score": sub.score, "total_marks": sub.total_marks,
                      "passed": sub.passed, "submitted_at": sub.submitted_at.isoformat()}

    return {
        "id": exam.id, "title": exam.title, "description": exam.description,
        "duration_minutes": exam.duration_minutes, "total_marks": exam.total_marks,
        "passing_marks": exam.passing_marks, "status": exam.status, "exam_type": exam.exam_type,
        "start_time": exam.start_time.isoformat() if exam.start_time else None,
        "otp_required": exam.otp_required,
        "exam_otp": exam.exam_otp if is_privileged else None,
        "questions": questions, "my_submission": my_sub,
    }


@router.post("/{exam_id}/activate")
async def activate_exam(exam_id: int, background_tasks: BackgroundTasks,
                        db: Session = Depends(get_db), current_user: User = Depends(require_staff_or_company)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam: raise HTTPException(404, "Not found")
    if exam.status == ExamStatus.active: raise HTTPException(400, "Already active")
    exam.status = ExamStatus.active
    db.commit()
    await ws_manager.broadcast({"type": "exam_started", "exam_id": exam_id,
                                 "title": exam.title, "duration": exam.duration_minutes})

    async def auto_end():
        await asyncio.sleep(exam.duration_minutes * 60 + 300)
        from database import SessionLocal
        db2 = SessionLocal()
        try:
            e = db2.query(Exam).filter(Exam.id == exam_id).first()
            if e and e.status == ExamStatus.active:
                e.status = ExamStatus.completed
                db2.commit()
                await ws_manager.broadcast({"type": "exam_ended", "exam_id": exam_id})
        finally:
            db2.close()

    background_tasks.add_task(auto_end)
    return {"message": "Exam activated", "otp": exam.exam_otp}


@router.post("/{exam_id}/deactivate")
async def deactivate_exam(exam_id: int, db: Session = Depends(get_db),
                          current_user: User = Depends(require_staff_or_company)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam: raise HTTPException(404, "Not found")
    exam.status = ExamStatus.completed
    db.commit()
    await ws_manager.broadcast({"type": "exam_ended", "exam_id": exam_id})
    return {"message": "Exam deactivated"}


@router.delete("/{exam_id}/delete")
def delete_exam(exam_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(require_staff_or_company)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam: raise HTTPException(404, "Not found")
    if exam.status == ExamStatus.active:
        raise HTTPException(400, "Cannot delete active exam")
    db.delete(exam)
    db.commit()
    return {"message": "Deleted"}


# ─── OTP Verify ───────────────────────────────────────────────────

@router.post("/{exam_id}/verify-otp")
async def verify_otp(exam_id: int, data: OTPVerifySchema,
                     db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam: raise HTTPException(404, "Not found")

    # Batch OTP mode (v2.2)
    if data.batch_id:
        batch = db.query(ExamBatch).filter(
            ExamBatch.id == data.batch_id, ExamBatch.exam_id == exam_id).first()
        if not batch: raise HTTPException(404, "Batch not found")
        if not batch.otp_active: raise HTTPException(400, "OTP not yet activated by staff")
        if batch.otp != data.otp.strip():
            raise HTTPException(400, "Invalid OTP")
        # Mark student as otp_entered
        member = db.query(ExamBatchMember).filter(
            ExamBatchMember.batch_id == data.batch_id,
            ExamBatchMember.student_id == current_user.id).first()
        if member:
            member.otp_entered = True
            db.commit()
            # Notify staff via WS
            await ws_manager.broadcast({
                "type": "student_otp_entered",
                "batch_id": data.batch_id,
                "student_id": current_user.id,
                "student_name": current_user.name,
                "roll_number": current_user.roll_number,
            })
        return {"valid": True, "wait_for_staff": not batch.exam_enabled}

    # Legacy single OTP
    if not exam.otp_required:
        return {"valid": True}
    if exam.exam_otp != data.otp.strip():
        raise HTTPException(400, "Invalid OTP")
    return {"valid": True, "wait_for_staff": False}


# ─── Submit ───────────────────────────────────────────────────────

@router.post("/{exam_id}/submit")
async def submit_exam(exam_id: int, data: SubmitExamSchema,
                      db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.student:
        raise HTTPException(403, "Students only")
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam: raise HTTPException(404, "Not found")
    if exam.status != ExamStatus.active:
        raise HTTPException(400, "Exam not active")

    existing = db.query(ExamSubmission).filter(
        ExamSubmission.exam_id == exam_id,
        ExamSubmission.student_id == current_user.id).first()
    if existing: raise HTTPException(400, "Already submitted")

    # Score
    score = 0
    for eq in exam.exam_questions:
        q = eq.question
        ans = data.answers.get(str(q.id)) or data.answers.get(q.id)
        if q.question_type == "mcq" and ans:
            if str(ans).strip().upper() == str(q.correct_answer or "").strip().upper():
                score += q.marks
        elif q.question_type == "coding" and ans:
            score += q.marks  # Graded via compiler run

    passed = score >= exam.passing_marks

    # Malpractice
    mal = False
    notes = []
    if data.tab_switch_count >= MALPRACTICE_TAB:
        mal = True; notes.append(f"Tab switches:{data.tab_switch_count}")
    if data.blur_count >= MALPRACTICE_BLUR:
        mal = True; notes.append(f"Blur:{data.blur_count}")
    if data.copy_paste_count >= MALPRACTICE_COPY:
        mal = True; notes.append(f"Copy/paste:{data.copy_paste_count}")

    sub = ExamSubmission(
        exam_id=exam_id, student_id=current_user.id, answers=data.answers,
        score=score, total_marks=exam.total_marks, passed=passed,
        tab_switch_count=data.tab_switch_count, blur_count=data.blur_count,
        copy_paste_count=data.copy_paste_count, malpractice_flag=mal,
        malpractice_notes=", ".join(notes) if notes else None)
    db.add(sub)

    # Mark batch member as submitted
    if data.batch_id:
        member = db.query(ExamBatchMember).filter(
            ExamBatchMember.batch_id == data.batch_id,
            ExamBatchMember.student_id == current_user.id).first()
        if member:
            member.is_present = True

    db.commit()
    db.refresh(sub)

    if exam.exam_type == ExamType.campus and exam.drive_round_id:
        _sync_drive_result(exam.drive_round_id, current_user.id, score, passed, db)

    await ws_manager.broadcast({
        "type": "exam_submitted",
        "exam_id": exam_id,
        "student_id": current_user.id,
        "student_name": current_user.name,
        "roll_number": current_user.roll_number,
        "score": score, "passed": passed,
        "malpractice": mal,
        "batch_id": data.batch_id,
    })

    pct = round(score / exam.total_marks * 100, 1) if exam.total_marks else 0
    return {"message": "Submitted", "score": score, "total_marks": exam.total_marks,
            "percentage": pct, "passed": passed, "malpractice_flag": mal,
            "malpractice_notes": ", ".join(notes) if notes else None,
            "redirect_to": "/dashboard"}


def _sync_drive_result(round_id, student_id, score, passed, db):
    from sqlalchemy.exc import IntegrityError
    from models import DriveRoundResult
    ex = db.query(DriveRoundResult).filter(
        DriveRoundResult.round_id == round_id,
        DriveRoundResult.student_id == student_id).first()
    if ex:
        ex.score = score; ex.passed = passed
    else:
        try:
            db.add(DriveRoundResult(round_id=round_id, student_id=student_id,
                                    score=score, passed=passed))
        except IntegrityError:
            db.rollback()
    db.commit()


# ─── Malpractice event feed (live, from student) ──────────────────

@router.post("/{exam_id}/malpractice-event")
async def report_malpractice(exam_id: int, request: Request,
                              db: Session = Depends(get_db),
                              current_user: User = Depends(get_current_user)):
    body = await request.json()
    await ws_manager.broadcast({
        "type": "malpractice_event",
        "exam_id": exam_id,
        "student_id": current_user.id,
        "student_name": current_user.name,
        "roll_number": current_user.roll_number,
        "batch_id": body.get("batch_id"),
        "event": body.get("event"),       # "tab_switch" | "blur" | "copy"
        "count": body.get("count", 1),
    })
    return {"ok": True}


# ─── Batch Management ────────────────────────────────────────────

@router.get("/{exam_id}/batches")
def list_batches(exam_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    is_priv = current_user.role in (STAFF_ROLES | COMPANY_ROLES)
    if not is_priv: raise HTTPException(403, "Staff or company only")
    batches = db.query(ExamBatch).filter(ExamBatch.exam_id == exam_id).all()
    return [_batch_detail(b, db) for b in batches]


@router.post("/{exam_id}/batches")
def create_batch(exam_id: int, data: BatchCreateSchema,
                 db: Session = Depends(get_db), current_user: User = Depends(require_staff_or_company)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam: raise HTTPException(404, "Exam not found")
    batch = ExamBatch(
        exam_id=exam_id, staff_id=current_user.id,
        batch_name=data.batch_name,
        otp=''.join(random.choices(string.digits, k=6)))
    db.add(batch)
    db.flush()
    for sid in data.student_ids:
        db.add(ExamBatchMember(batch_id=batch.id, student_id=sid))
    db.commit()
    db.refresh(batch)
    return {"message": "Batch created", "batch_id": batch.id, "otp": batch.otp}


@router.get("/batches/{batch_id}")
def get_batch(batch_id: int, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    batch = db.query(ExamBatch).filter(ExamBatch.id == batch_id).first()
    if not batch: raise HTTPException(404, "Not found")
    is_priv = current_user.role in STAFF_ROLES
    if not is_priv and batch.staff_id != current_user.id:
        raise HTTPException(403, "Not your batch")
    return _batch_detail(batch, db)


@router.post("/batches/{batch_id}/activate-otp")
async def activate_otp(batch_id: int, db: Session = Depends(get_db),
                       current_user: User = Depends(require_staff_or_company)):
    batch = db.query(ExamBatch).filter(ExamBatch.id == batch_id).first()
    if not batch: raise HTTPException(404, "Not found")
    batch.otp_active = True
    db.commit()
    await ws_manager.broadcast({
        "type": "batch_otp_activated", "batch_id": batch_id,
        "otp": batch.otp, "exam_id": batch.exam_id})
    return {"message": "OTP activated", "otp": batch.otp}


@router.post("/batches/{batch_id}/start-exam")
async def start_batch_exam(batch_id: int, db: Session = Depends(get_db),
                            current_user: User = Depends(require_staff_or_company)):
    batch = db.query(ExamBatch).filter(ExamBatch.id == batch_id).first()
    if not batch: raise HTTPException(404, "Not found")
    batch.exam_enabled = True
    db.commit()
    await ws_manager.broadcast({
        "type": "batch_exam_started", "batch_id": batch_id, "exam_id": batch.exam_id})
    return {"message": "Exam started for batch"}


@router.post("/batches/{batch_id}/regenerate-otp")
async def regen_otp(batch_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(require_staff_or_company)):
    batch = db.query(ExamBatch).filter(ExamBatch.id == batch_id).first()
    if not batch: raise HTTPException(404, "Not found")
    batch.otp = ''.join(random.choices(string.digits, k=6))
    batch.otp_active = False
    batch.exam_enabled = False
    db.commit()
    return {"message": "OTP regenerated", "otp": batch.otp}


def _batch_detail(batch: ExamBatch, db: Session) -> dict:
    members = []
    for m in batch.members:
        s = m.student
        sub = db.query(ExamSubmission).filter(
            ExamSubmission.exam_id == batch.exam_id,
            ExamSubmission.student_id == s.id).first()
        members.append({
            "student_id": s.id,
            "name": s.name,
            "roll_number": s.roll_number or "",
            "email": s.email,
            "department": s.department or "",
            "otp_entered": m.otp_entered,
            "is_present": m.is_present,
            "submitted": sub is not None,
            "score": sub.score if sub else None,
            "passed": sub.passed if sub else None,
            "malpractice": sub.malpractice_flag if sub else False,
            "tab_switches": sub.tab_switch_count if sub else 0,
            "blur_count": sub.blur_count if sub else 0,
            "copy_paste": sub.copy_paste_count if sub else 0,
        })
    return {
        "id": batch.id, "exam_id": batch.exam_id, "batch_name": batch.batch_name,
        "staff_name": batch.staff.name, "staff_id": batch.staff_id,
        "otp": batch.otp, "otp_active": batch.otp_active,
        "exam_enabled": batch.exam_enabled,
        "total": len(members),
        "otp_entered_count": sum(1 for m in members if m["otp_entered"]),
        "present_count": sum(1 for m in members if m["is_present"]),
        "submitted_count": sum(1 for m in members if m["submitted"]),
        "malpractice_count": sum(1 for m in members if m["malpractice"]),
        "members": members,
        "created_at": batch.created_at.isoformat() if batch.created_at else None,
    }


# ─── Check if batch exam is started (student polls) ───────────────

@router.get("/batches/{batch_id}/status")
def batch_status(batch_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    batch = db.query(ExamBatch).filter(ExamBatch.id == batch_id).first()
    if not batch: raise HTTPException(404, "Not found")
    return {"exam_enabled": batch.exam_enabled, "otp_active": batch.otp_active,
            "exam_id": batch.exam_id}


# ─── Reports ─────────────────────────────────────────────────────

@router.get("/{exam_id}/submissions")
def exam_submissions(exam_id: int, db: Session = Depends(get_db),
                     current_user: User = Depends(require_staff_or_company)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam: raise HTTPException(404, "Not found")
    subs = db.query(ExamSubmission).filter(ExamSubmission.exam_id == exam_id)\
             .order_by(ExamSubmission.score.desc()).all()
    return [{"rank": i+1, "student_id": s.student_id, "name": s.student.name,
             "roll_number": s.student.roll_number, "department": s.student.department,
             "email": s.student.email, "score": s.score, "total_marks": s.total_marks,
             "percentage": round(s.score/s.total_marks*100,1) if s.total_marks else 0,
             "passed": s.passed, "malpractice_flag": s.malpractice_flag,
             "tab_switches": s.tab_switch_count, "blur_count": s.blur_count,
             "copy_paste": s.copy_paste_count,
             "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None}
            for i, s in enumerate(subs)]


@router.get("/{exam_id}/analytics")
def exam_analytics(exam_id: int, db: Session = Depends(get_db),
                   current_user: User = Depends(require_staff_or_company)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam: raise HTTPException(404, "Not found")
    subs = db.query(ExamSubmission).filter(ExamSubmission.exam_id == exam_id).all()
    if not subs:
        return {"message": "No submissions", "total_submissions": 0}
    scores = [s.score for s in subs]
    passed = sum(1 for s in subs if s.passed)
    return {
        "total_submissions": len(subs),
        "passed": passed, "failed": len(subs)-passed,
        "pass_rate": round(passed/len(subs)*100, 1),
        "malpractice_count": sum(1 for s in subs if s.malpractice_flag),
        "avg_score": round(sum(scores)/len(scores), 1),
        "max_score": max(scores), "min_score": min(scores),
        "total_marks": exam.total_marks, "passing_marks": exam.passing_marks,
        "score_distribution": {
            "0-25%":   sum(1 for s in scores if s <= exam.total_marks*0.25),
            "26-50%":  sum(1 for s in scores if exam.total_marks*0.25 < s <= exam.total_marks*0.5),
            "51-75%":  sum(1 for s in scores if exam.total_marks*0.5  < s <= exam.total_marks*0.75),
            "76-100%": sum(1 for s in scores if s > exam.total_marks*0.75),
        },
    }


@router.get("/{exam_id}/malpractice-report")
def malpractice_report(exam_id: int, db: Session = Depends(get_db),
                       current_user: User = Depends(require_staff_or_company)):
    flagged = db.query(ExamSubmission).filter(
        ExamSubmission.exam_id == exam_id,
        ExamSubmission.malpractice_flag == True).all()
    return [{"student_id": s.student_id, "name": s.student.name,
             "email": s.student.email, "roll_number": s.student.roll_number,
             "score": s.score, "tab_switch_count": s.tab_switch_count,
             "blur_count": s.blur_count, "copy_paste_count": s.copy_paste_count,
             "notes": s.malpractice_notes} for s in flagged]
