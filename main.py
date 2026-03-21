"""
main.py — University Placement Portal v2.1
FastAPI application entry point.
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import logging

from database import create_tables
from services.websocket_manager import ws_manager

from routes.users        import router as users_router
from routes.exam         import router as exam_router
from routes.questions    import router as questions_router
from routes.campus_drive import router as drive_router
from routes.dashboard    import router as dashboard_router
from routes.compiler     import router as compiler_router
from routes.placement    import router as placement_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="University Placement Portal", version="2.1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def on_startup():
    create_tables()
@app.get("/health")
def health_check():
    """Render health check endpoint."""
    return {"status": "ok", "version": "2.3"}


    logger.info("✅ Tables ready")


# ─────────────────────────────────────────
# Error Handlers
# ─────────────────────────────────────────

@app.exception_handler(404)
async def not_found(request: Request, exc):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            content={"detail": f"Endpoint not found: {request.url.path}"},
            status_code=404)
    return templates.TemplateResponse("errors/404.html", {"request": request}, status_code=404)


@app.exception_handler(403)
async def forbidden(request: Request, exc):
    if request.url.path.startswith("/api"):
        return JSONResponse(content={"detail": "Forbidden"}, status_code=403)
    return templates.TemplateResponse("errors/403.html", {"request": request}, status_code=403)


@app.exception_handler(500)
async def server_error(request: Request, exc):
    logger.error(f"500 error: {exc}")
    if request.url.path.startswith("/api"):
        return JSONResponse(
            content={"detail": "Internal server error"},
            status_code=500)
    return templates.TemplateResponse("errors/500.html", {"request": request}, status_code=500)


# ─────────────────────────────────────────
# API Routers
# ─────────────────────────────────────────

app.include_router(users_router,     prefix="/api")
app.include_router(exam_router,      prefix="/api")
app.include_router(questions_router, prefix="/api")
app.include_router(drive_router,     prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(compiler_router,  prefix="/api")
app.include_router(placement_router, prefix="/api")


# ─────────────────────────────────────────
# Page Routes
# ─────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register_student(request: Request):
    return templates.TemplateResponse("auth/register_student.html", {"request": request})

@app.get("/register/staff", response_class=HTMLResponse)
def register_staff(request: Request):
    return templates.TemplateResponse("auth/register_staff.html", {"request": request})

@app.get("/register/company", response_class=HTMLResponse)
def register_company(request: Request):
    return templates.TemplateResponse("auth/register_company.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard/index.html", {"request": request})

@app.get("/exams", response_class=HTMLResponse)
def exams_page(request: Request):
    return templates.TemplateResponse("exam/exam_list.html", {"request": request})

@app.get("/exams/create", response_class=HTMLResponse)
def exam_create(request: Request):
    return templates.TemplateResponse("exam/exam_create.html", {"request": request})

@app.get("/exams/monitor/{batch_id}", response_class=HTMLResponse)
def exam_monitor_page(request: Request, batch_id: int):
    return templates.TemplateResponse("exam/exam_monitor.html",
                                      {"request": request, "batch_id": batch_id})

@app.get("/exams/{exam_id}/batches", response_class=HTMLResponse)
def exam_batches_page(request: Request, exam_id: int):
    return templates.TemplateResponse("exam/exam_batches.html",
                                      {"request": request, "exam_id": exam_id})

@app.get("/exams/{exam_id}", response_class=HTMLResponse)
def exam_detail(request: Request, exam_id: int):
    return templates.TemplateResponse("exam/exam_page.html",
                                      {"request": request, "exam_id": exam_id})

@app.get("/questions", response_class=HTMLResponse)
def questions_page(request: Request):
    return templates.TemplateResponse("questions/bank.html", {"request": request})

@app.get("/campus-drives", response_class=HTMLResponse)
def drives_list(request: Request):
    return templates.TemplateResponse("campus_drive/drive_list.html", {"request": request})

@app.get("/campus-drives/create", response_class=HTMLResponse)
def drive_create(request: Request):
    return templates.TemplateResponse("campus_drive/drive_create.html", {"request": request})

@app.get("/campus-drives/{drive_id}", response_class=HTMLResponse)
def drive_detail(request: Request, drive_id: int):
    return templates.TemplateResponse("campus_drive/drive_detail.html",
                                      {"request": request, "drive_id": drive_id})

@app.get("/notifications", response_class=HTMLResponse)
def notifications_page(request: Request):
    return templates.TemplateResponse("community/notifications.html", {"request": request})

@app.get("/placement-results", response_class=HTMLResponse)
def placement_results(request: Request):
    return templates.TemplateResponse("placement/results.html", {"request": request})

@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    return templates.TemplateResponse("auth/profile.html", {"request": request})

@app.get("/profile/{user_id}", response_class=HTMLResponse)
def view_profile(request: Request, user_id: int):
    return templates.TemplateResponse("auth/profile.html",
                                      {"request": request, "view_user_id": user_id})

@app.get("/analytics", response_class=HTMLResponse)
def analytics_page(request: Request):
    return templates.TemplateResponse("dashboard/analytics.html", {"request": request})


# ─────────────────────────────────────────
# WebSocket — Real-time updates
# ─────────────────────────────────────────

@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    return templates.TemplateResponse("profile/profile.html", {"request": request})

@app.get("/profile/{user_id}", response_class=HTMLResponse)
def view_profile_page(request: Request, user_id: int):
    return templates.TemplateResponse("profile/view_profile.html",
                                      {"request": request, "user_id": user_id})

@app.websocket("/ws/exam/{exam_id}")
async def exam_ws(websocket: WebSocket, exam_id: int):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.websocket("/ws/drive/{drive_id}")
async def drive_ws(websocket: WebSocket, drive_id: int):
    """Real-time updates for a specific campus drive."""
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.websocket("/ws/notifications/{user_id}")
async def notification_ws(websocket: WebSocket, user_id: int):
    """Real-time notification badge updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

