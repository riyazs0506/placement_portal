"""
routes/questions.py — Question bank management.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from database import get_db
from models import Question, User, STAFF_ROLES
from auth import get_current_user, require_staff

router = APIRouter(prefix="/questions", tags=["questions"])
templates = Jinja2Templates(directory="templates")


class QuestionCreateSchema(BaseModel):
    question_text: str
    question_type: str = "mcq"
    subject: Optional[str] = None
    difficulty: str = "medium"
    marks: int = 1
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_answer: Optional[str] = None
    starter_code: Optional[str] = None
    expected_output: Optional[str] = None
    test_cases: Optional[List[dict]] = []


@router.get("/bank", response_class=HTMLResponse)
def question_bank_page(request: Request):
    return templates.TemplateResponse("questions/bank.html", {"request": request})


@router.post("/create")
def create_question(
    data: QuestionCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    q = Question(
        question_text=data.question_text,
        question_type=data.question_type,
        subject=data.subject,
        difficulty=data.difficulty,
        marks=data.marks,
        option_a=data.option_a,
        option_b=data.option_b,
        option_c=data.option_c,
        option_d=data.option_d,
        correct_answer=data.correct_answer,
        starter_code=data.starter_code,
        expected_output=data.expected_output,
        test_cases=data.test_cases or [],
        created_by_id=current_user.id,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return {"message": "Question created", "question_id": q.id}


@router.get("/list")
def list_questions(
    question_type: Optional[str] = None,
    subject: Optional[str] = None,
    difficulty: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),   # FIX: allow all authenticated users
):
    q = db.query(Question)
    if question_type:
        q = q.filter(Question.question_type == question_type)
    if subject:
        q = q.filter(Question.subject.ilike(f"%{subject}%"))
    if difficulty:
        q = q.filter(Question.difficulty == difficulty)
    if search:
        q = q.filter(Question.question_text.ilike(f"%{search}%"))

    total = q.count()
    questions = q.order_by(Question.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "questions": [
            {
                "id": qu.id,
                "question_text": qu.question_text,
                "question_type": qu.question_type,
                "subject": qu.subject,
                "difficulty": qu.difficulty,
                "marks": qu.marks,
                "option_a": qu.option_a,
                "option_b": qu.option_b,
                "option_c": qu.option_c,
                "option_d": qu.option_d,
                "correct_answer": qu.correct_answer,
                "starter_code": qu.starter_code,
                "test_cases": qu.test_cases,
            }
            for qu in questions
        ],
    }


@router.delete("/{question_id}")
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(q)
    db.commit()
    return {"message": "Question deleted"}
