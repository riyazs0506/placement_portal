# University Placement Portal v2.0

FastAPI + Jinja2 + SQLAlchemy full-stack university placement management system.

---

## Quick Start

```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```
Open http://localhost:8000

---

## Registration Secret Keys

| Role | Key |
|---|---|
| Student | *(no key needed)* |
| Staff / Senior / Junior Staff | `STAFF@2024` |
| Placement Officer | `OFFICER@2024` |
| Head Admin | `ADMIN@SUPER2024` |
| All Company roles | `COMPANY@2024` |

Change these in production via environment variables:
```
STAFF_SECRET_KEY=...
OFFICER_SECRET_KEY=...
ADMIN_SECRET_KEY=...
COMPANY_SECRET_KEY=...
```

---

## Registration URLs

| Who | URL |
|---|---|
| Student | `/register` |
| Staff / Placement Officer | `/register/staff` |
| Company (HR, Interviewer, etc.) | `/register/company` |

---

## Company Roles Available

- HR Manager
- Technical Interviewer
- Recruitment Manager
- Team Leader
- Company Officer
- General / Other

---

## Campus Drive Workflow

1. **Company** creates drive + job at `/campus-drives/create`
2. **Company** requests campus visit (date + venue)
3. **Placement Officer** approves / reschedules / rejects
4. On approval, **student response opens** — eligible students opt in/out
5. **Company** closes response → creates rounds (Aptitude, Coding, GD, Technical, HR, Custom)
6. Each round can optionally **link to a campus exam**
7. When round is completed → **pass students auto-advance** (DriveRoundResult updated)
8. Staff/company can send **community notifications** to students / officers

---

## Online vs Campus Exams

- **Online exams** (`exam_type=online`): Visible in `/exams` — students can take independently
- **Campus exams** (`exam_type=campus`): Linked to a drive round — NOT visible in exam list
- Campus exams are only accessible via the drive round flow

---

## Malpractice Detection

Thresholds (auto-flag submission):
- Tab switches ≥ 3
- Window blur ≥ 10
- Copy/paste events ≥ 5

Flagged submissions are visible in `/api/exams/{id}/malpractice-report`

---

## After Exam Completion

- Score shown on result screen
- Auto-redirect to `/dashboard` after **5-second countdown**
- Campus exams → DriveRoundResult updated automatically

---

## Project Structure

```
placement_portal/
├── main.py                    ← FastAPI app, all routes, error handlers
├── models.py                  ← All SQLAlchemy models
├── database.py                ← DB engine + session
├── auth.py                    ← JWT + secret key validation
├── requirements.txt
├── routes/
│   ├── users.py               ← Register, login, profile
│   ├── exam.py                ← Exam CRUD, submit, malpractice
│   ├── campus_drive.py        ← Full drive lifecycle + notifications
│   ├── questions.py           ← Question bank
│   ├── dashboard.py           ← Dashboard stats
│   └── compiler.py            ← Code execution
├── services/
│   ├── websocket_manager.py   ← WebSocket broadcast
│   └── compiler.py            ← Python/C/C++/Java sandbox
├── templates/
│   ├── base.html
│   ├── auth/
│   │   ├── login.html
│   │   ├── register_student.html
│   │   ├── register_staff.html
│   │   └── register_company.html
│   ├── dashboard/index.html
│   ├── exam/
│   │   ├── exam_list.html
│   │   ├── exam_create.html
│   │   └── exam_page.html     ← Fullscreen exam with malpractice + redirect
│   ├── campus_drive/
│   │   ├── drive_list.html
│   │   ├── drive_create.html
│   │   └── drive_detail.html  ← Full drive management
│   ├── community/
│   │   └── notifications.html
│   ├── questions/bank.html
│   └── errors/
│       ├── 404.html
│       ├── 403.html
│       └── 500.html
└── static/js/app.js           ← Nav, auth, toast, API helpers
```
