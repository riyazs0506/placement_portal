"""
routes/compiler.py — Code execution router.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from auth import get_current_user
from models import User
from services.compiler import run_code

router = APIRouter(prefix="/compiler", tags=["compiler"])


class RunCodeSchema(BaseModel):
    code: str
    language: str
    stdin_input: Optional[str] = ""


@router.post("/run")
def execute_code(data: RunCodeSchema, current_user: User = Depends(get_current_user)):
    supported = ["python", "c", "cpp", "java"]
    if data.language.lower() not in supported:
        raise HTTPException(status_code=400, detail=f"Unsupported language. Supported: {supported}")
    if len(data.code) > 10000:
        raise HTTPException(status_code=400, detail="Code too long (max 10,000 chars)")
    return run_code(data.code, data.language, data.stdin_input)
