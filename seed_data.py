"""
seed_data.py — Insert complete demo/sample data into the Placement Portal database.

Run AFTER starting the app at least once (so tables are created):
    python seed_data.py

Or run standalone:
    python seed_data.py --create-tables

Passwords:
  admin@college.edu     → Admin@123
  officer@college.edu   → Officer@123
  staff1@college.edu    → Staff@123
  staff2@college.edu    → Staff@123
  hr@tcs.com            → TCS@123
  All students          → Student@123
"""

import sys, json
from datetime import datetime, timedelta

# Allow running without full app environment
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def hash_pw(p): return pwd_context.hash(p)
except ImportError:
    import hashlib
    print("WARNING: passlib not installed. Using SHA256 placeholder hashes.")
    print("Install: pip install passlib[bcrypt]")
    def hash_pw(p): return "$2b$12$PLACEHOLDER_" + hashlib.sha256(p.encode()).hexdigest()[:40]

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
except ImportError:
    print("ERROR: sqlalchemy not installed. Run: pip install sqlalchemy")
    sys.exit(1)

# ── Database connection ──────────────────────────────────────
DATABASE_URL = "sqlite:///./placement_portal.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create tables if needed
if "--create-tables" in sys.argv:
    try:
        sys.path.insert(0, ".")
        from database import Base
        import models  # noqa — registers all models
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created")
    except Exception as e:
        print(f"Could not create tables: {e}")

Session = sessionmaker(bind=engine)
db = Session()

def run(sql, params=None):
    db.execute(text(sql), params or {})

def insert(table, **kwargs):
    cols = ", ".join(kwargs.keys())
    vals = ", ".join(f":{k}" for k in kwargs.keys())
    db.execute(text(f"INSERT INTO {table} ({cols}) VALUES ({vals})"), kwargs)

def get_id(table, condition, params):
    row = db.execute(text(f"SELECT id FROM {table} WHERE {condition}"), params).fetchone()
    return row[0] if row else None


print("🌱 Seeding demo data…")

# ─────────────────────────────────────────────────────────────
# 1. USERS
# ─────────────────────────────────────────────────────────────
print("  → Inserting users…")

USERS = [
    # Staff
    dict(name="Dr. Rajesh Kumar",   email="admin@college.edu",   password="Admin@123",   role="head_admin",
         department=None, batch_year=None, cgpa=None, tenth_percent=None, twelfth_percent=None, backlogs=0,
         roll_number=None, company_name=None, company_designation=None),

    dict(name="Mrs. Priya Nair",    email="officer@college.edu", password="Officer@123", role="placement_officer",
         department=None, batch_year=None, cgpa=None, tenth_percent=None, twelfth_percent=None, backlogs=0,
         roll_number=None, company_name=None, company_designation=None),

    dict(name="Mr. Arjun Mehta",    email="staff1@college.edu",  password="Staff@123",   role="senior_staff",
         department=None, batch_year=None, cgpa=None, tenth_percent=None, twelfth_percent=None, backlogs=0,
         roll_number=None, company_name=None, company_designation=None),

    dict(name="Ms. Kavitha Rajan",  email="staff2@college.edu",  password="Staff@123",   role="staff",
         department=None, batch_year=None, cgpa=None, tenth_percent=None, twelfth_percent=None, backlogs=0,
         roll_number=None, company_name=None, company_designation=None),

    # TCS
    dict(name="Ravi Sharma",        email="hr@tcs.com",          password="TCS@123",     role="company_hr_manager",
         department=None, batch_year=None, cgpa=None, tenth_percent=None, twelfth_percent=None, backlogs=0,
         roll_number=None, company_name="TCS Ltd", company_designation="HR Manager"),

    dict(name="Deepa Krishnan",     email="tech@tcs.com",        password="TCS@123",     role="company_tech_interviewer",
         department=None, batch_year=None, cgpa=None, tenth_percent=None, twelfth_percent=None, backlogs=0,
         roll_number=None, company_name="TCS Ltd", company_designation="Technical Lead"),

    dict(name="Suresh Babu",        email="recruit@tcs.com",     password="TCS@123",     role="company_recruitment_mgr",
         department=None, batch_year=None, cgpa=None, tenth_percent=None, twelfth_percent=None, backlogs=0,
         roll_number=None, company_name="TCS Ltd", company_designation="Recruitment Manager"),

    # Infosys
    dict(name="Ananya Iyer",        email="hr@infosys.com",      password="Infosys@123", role="company_hr_manager",
         department=None, batch_year=None, cgpa=None, tenth_percent=None, twelfth_percent=None, backlogs=0,
         roll_number=None, company_name="Infosys Ltd", company_designation="HR Manager"),

    dict(name="Vikram Patel",       email="tech@infosys.com",    password="Infosys@123", role="company_tech_interviewer",
         department=None, batch_year=None, cgpa=None, tenth_percent=None, twelfth_percent=None, backlogs=0,
         roll_number=None, company_name="Infosys Ltd", company_designation="Senior Engineer"),

    # Wipro
    dict(name="Sneha Pillai",       email="hr@wipro.com",        password="Wipro@123",   role="company_hr_manager",
         department=None, batch_year=None, cgpa=None, tenth_percent=None, twelfth_percent=None, backlogs=0,
         roll_number=None, company_name="Wipro Technologies", company_designation="HR Lead"),

    dict(name="Karthik Nair",       email="team@wipro.com",      password="Wipro@123",   role="company_team_leader",
         department=None, batch_year=None, cgpa=None, tenth_percent=None, twelfth_percent=None, backlogs=0,
         roll_number=None, company_name="Wipro Technologies", company_designation="Team Lead"),

    # Students (CS)
    dict(name="Arun Kumar S",       email="arun@student.edu",    password="Student@123", role="student",
         department="CS", batch_year=2025, cgpa=8.7, tenth_percent=88.5, twelfth_percent=82.0, backlogs=0,
         roll_number="21CS001", company_name=None, company_designation=None),

    dict(name="Sathish Kumar T",    email="sathish@student.edu", password="Student@123", role="student",
         department="IT", batch_year=2025, cgpa=9.1, tenth_percent=95.0, twelfth_percent=91.0, backlogs=0,
         roll_number="21IT005", company_name=None, company_designation=None),

    dict(name="Anitha Selvam",      email="anitha@student.edu",  password="Student@123", role="student",
         department="CS", batch_year=2025, cgpa=8.9, tenth_percent=92.0, twelfth_percent=88.0, backlogs=0,
         roll_number="21CS008", company_name=None, company_designation=None),

    dict(name="Vijay Shankar",      email="vijay@student.edu",   password="Student@123", role="student",
         department="CS", batch_year=2025, cgpa=8.4, tenth_percent=85.0, twelfth_percent=80.0, backlogs=0,
         roll_number="21CS011", company_name=None, company_designation=None),

    # Students (IT/ECE)
    dict(name="Priya Devi M",       email="priya@student.edu",   password="Student@123", role="student",
         department="IT", batch_year=2025, cgpa=7.9, tenth_percent=76.0, twelfth_percent=79.5, backlogs=0,
         roll_number="21IT002", company_name=None, company_designation=None),

    dict(name="Mohammed Farhan",    email="farhan@student.edu",  password="Student@123", role="student",
         department="ECE", batch_year=2025, cgpa=8.2, tenth_percent=90.0, twelfth_percent=85.0, backlogs=0,
         roll_number="21EC003", company_name=None, company_designation=None),

    dict(name="Divya Bharathi K",   email="divya@student.edu",   password="Student@123", role="student",
         department="EEE", batch_year=2025, cgpa=7.4, tenth_percent=72.0, twelfth_percent=74.0, backlogs=0,
         roll_number="21EE006", company_name=None, company_designation=None),

    # Below-threshold students (to demo eligibility filter)
    dict(name="Lakshmi Narayanan",  email="lakshmi@student.edu", password="Student@123", role="student",
         department="CS", batch_year=2025, cgpa=6.5, tenth_percent=65.0, twelfth_percent=68.0, backlogs=1,
         roll_number="21CS004", company_name=None, company_designation=None),

    dict(name="Meena Kumari P",     email="meena@student.edu",   password="Student@123", role="student",
         department="ECE", batch_year=2025, cgpa=5.8, tenth_percent=60.0, twelfth_percent=62.0, backlogs=2,
         roll_number="21EC010", company_name=None, company_designation=None),

    dict(name="Ragul Murugan",      email="ragul@student.edu",   password="Student@123", role="student",
         department="MECH", batch_year=2025, cgpa=6.8, tenth_percent=70.0, twelfth_percent=71.5, backlogs=0,
         roll_number="21ME007", company_name=None, company_designation=None),

    dict(name="Bala Krishnan R",    email="bala@student.edu",    password="Student@123", role="student",
         department="IT", batch_year=2026, cgpa=7.2, tenth_percent=68.0, twelfth_percent=72.0, backlogs=0,
         roll_number="22IT009", company_name=None, company_designation=None),

    dict(name="Deepika Ramesh",     email="deepika@student.edu", password="Student@123", role="student",
         department="MBA", batch_year=2025, cgpa=7.6, tenth_percent=74.0, twelfth_percent=76.0, backlogs=0,
         roll_number="21MB012", company_name=None, company_designation=None),
]

for u in USERS:
    existing = get_id("users", "email = :email", {"email": u["email"]})
    if existing:
        print(f"    skip (exists): {u['email']}")
        continue
    insert("users",
        name=u["name"], email=u["email"],
        password_hash=hash_pw(u["password"]), role=u["role"],
        department=u["department"], batch_year=u["batch_year"],
        cgpa=u["cgpa"], tenth_percent=u["tenth_percent"],
        twelfth_percent=u["twelfth_percent"], backlogs=u["backlogs"],
        roll_number=u["roll_number"],
        company_name=u["company_name"], company_designation=u["company_designation"],
        is_active=1)
    print(f"    ✓ {u['role']:30s} {u['email']}")


# ─────────────────────────────────────────────────────────────
# 2. QUESTIONS
# ─────────────────────────────────────────────────────────────
print("  → Inserting questions…")

staff_id = get_id("users", "email = :e", {"e": "staff1@college.edu"})

QUESTIONS = [
    # Aptitude MCQ
    dict(question_text="A train travels 360 km in 4 hours. What is its speed in m/s?",
         question_type="mcq", subject="Aptitude", difficulty="easy", marks=1,
         option_a="25 m/s", option_b="90 m/s", option_c="100 m/s", option_d="72 m/s",
         correct_answer="A", starter_code=None, expected_output=None, test_cases="[]"),

    dict(question_text="If 5 workers complete a task in 12 days, how many days will 15 workers take?",
         question_type="mcq", subject="Aptitude", difficulty="easy", marks=1,
         option_a="4 days", option_b="6 days", option_c="3 days", option_d="36 days",
         correct_answer="A", starter_code=None, expected_output=None, test_cases="[]"),

    dict(question_text="What is the next number in the series: 2, 6, 12, 20, 30, ?",
         question_type="mcq", subject="Reasoning", difficulty="medium", marks=2,
         option_a="40", option_b="42", option_c="44", option_d="36",
         correct_answer="B", starter_code=None, expected_output=None, test_cases="[]"),

    dict(question_text="A shopkeeper gives 20% discount and still earns 25% profit. What is the ratio of MP to CP?",
         question_type="mcq", subject="Aptitude", difficulty="hard", marks=3,
         option_a="25:16", option_b="15:8", option_c="5:3", option_d="4:3",
         correct_answer="A", starter_code=None, expected_output=None, test_cases="[]"),

    dict(question_text="Which data structure uses LIFO (Last In, First Out) order?",
         question_type="mcq", subject="Data Structures", difficulty="easy", marks=1,
         option_a="Queue", option_b="Stack", option_c="Linked List", option_d="Tree",
         correct_answer="B", starter_code=None, expected_output=None, test_cases="[]"),

    dict(question_text="What is the time complexity of binary search?",
         question_type="mcq", subject="Algorithms", difficulty="easy", marks=1,
         option_a="O(n)", option_b="O(n²)", option_c="O(log n)", option_d="O(n log n)",
         correct_answer="C", starter_code=None, expected_output=None, test_cases="[]"),

    dict(question_text="Which of the following is NOT a valid SQL join type?",
         question_type="mcq", subject="Database", difficulty="medium", marks=2,
         option_a="INNER JOIN", option_b="OUTER JOIN", option_c="DIAGONAL JOIN", option_d="CROSS JOIN",
         correct_answer="C", starter_code=None, expected_output=None, test_cases="[]"),

    dict(question_text="In Python, what is the output of: print(type(3/2))?",
         question_type="mcq", subject="Python", difficulty="easy", marks=1,
         option_a="<class 'int'>", option_b="<class 'float'>", option_c="<class 'complex'>", option_d="Error",
         correct_answer="B", starter_code=None, expected_output=None, test_cases="[]"),

    dict(question_text="What does OOP stand for?",
         question_type="mcq", subject="Programming", difficulty="easy", marks=1,
         option_a="Object Oriented Programming", option_b="Open Object Protocol", option_c="Object Order Process", option_d="None",
         correct_answer="A", starter_code=None, expected_output=None, test_cases="[]"),

    dict(question_text="Which HTTP method is idempotent and used to retrieve data?",
         question_type="mcq", subject="Web", difficulty="medium", marks=2,
         option_a="POST", option_b="DELETE", option_c="GET", option_d="PATCH",
         correct_answer="C", starter_code=None, expected_output=None, test_cases="[]"),

    # Verbal / Reasoning MCQ
    dict(question_text="Choose the word most similar in meaning to 'ELOQUENT':",
         question_type="mcq", subject="Verbal", difficulty="medium", marks=1,
         option_a="Silent", option_b="Articulate", option_c="Clumsy", option_d="Boring",
         correct_answer="B", starter_code=None, expected_output=None, test_cases="[]"),

    dict(question_text="If MANGO is coded as NBOPP, how is APPLE coded?",
         question_type="mcq", subject="Reasoning", difficulty="medium", marks=2,
         option_a="BQQMF", option_b="BPQMF", option_c="CQQMF", option_d="BQQLF",
         correct_answer="A", starter_code=None, expected_output=None, test_cases="[]"),

    # Coding questions
    dict(question_text="Write a Python function to find the factorial of a given number n. Print the result.",
         question_type="coding", subject="Python", difficulty="easy", marks=5,
         option_a=None, option_b=None, option_c=None, option_d=None, correct_answer=None,
         starter_code="def factorial(n):\n    # Write your code here\n    pass\n\nn = int(input())\nprint(factorial(n))",
         expected_output="120",
         test_cases=json.dumps([
             {"input": "5", "output": "120", "is_hidden": False},
             {"input": "0", "output": "1",   "is_hidden": False},
             {"input": "10","output": "3628800", "is_hidden": True},
         ])),

    dict(question_text="Given a list of integers, return the sum of all even numbers.",
         question_type="coding", subject="Python", difficulty="easy", marks=5,
         option_a=None, option_b=None, option_c=None, option_d=None, correct_answer=None,
         starter_code="n = int(input())\nnums = list(map(int, input().split()))\n# Write your code here\n",
         expected_output="12",
         test_cases=json.dumps([
             {"input": "5\n1 2 3 4 5",  "output": "6",  "is_hidden": False},
             {"input": "4\n2 4 6 8",    "output": "20", "is_hidden": False},
             {"input": "6\n1 3 5 7 9 11","output": "0", "is_hidden": True},
         ])),

    dict(question_text="Write a program to check if a given string is a palindrome. Print 'YES' or 'NO'.",
         question_type="coding", subject="Strings", difficulty="medium", marks=8,
         option_a=None, option_b=None, option_c=None, option_d=None, correct_answer=None,
         starter_code="s = input().strip()\n# Write your code here\n",
         expected_output="YES",
         test_cases=json.dumps([
             {"input": "racecar", "output": "YES", "is_hidden": False},
             {"input": "hello",   "output": "NO",  "is_hidden": False},
             {"input": "madam",   "output": "YES", "is_hidden": True},
             {"input": "python",  "output": "NO",  "is_hidden": True},
         ])),

    dict(question_text="Find the second largest element in an array of n integers.",
         question_type="coding", subject="Arrays", difficulty="medium", marks=8,
         option_a=None, option_b=None, option_c=None, option_d=None, correct_answer=None,
         starter_code="n = int(input())\narr = list(map(int, input().split()))\n# Write your code here\n",
         expected_output="7",
         test_cases=json.dumps([
             {"input": "5\n3 1 4 1 5",   "output": "4",  "is_hidden": False},
             {"input": "4\n10 20 5 30",  "output": "20", "is_hidden": False},
             {"input": "3\n100 90 80",   "output": "90", "is_hidden": True},
         ])),
]

for q in QUESTIONS:
    insert("questions",
        question_text=q["question_text"],
        question_type=q["question_type"],
        subject=q["subject"],
        difficulty=q["difficulty"],
        marks=q["marks"],
        option_a=q.get("option_a"), option_b=q.get("option_b"),
        option_c=q.get("option_c"), option_d=q.get("option_d"),
        correct_answer=q.get("correct_answer"),
        starter_code=q.get("starter_code"),
        expected_output=q.get("expected_output"),
        test_cases=q.get("test_cases", "[]"),
        created_by_id=staff_id)
print(f"    ✓ {len(QUESTIONS)} questions inserted")


# ─────────────────────────────────────────────────────────────
# 3. EXAMS
# ─────────────────────────────────────────────────────────────
print("  → Inserting exams…")

# Get question IDs
q_ids = [row[0] for row in db.execute(text("SELECT id FROM questions ORDER BY id")).fetchall()]
mcq_ids = [row[0] for row in db.execute(text("SELECT id FROM questions WHERE question_type='mcq' ORDER BY id")).fetchall()]
coding_ids = [row[0] for row in db.execute(text("SELECT id FROM questions WHERE question_type='coding' ORDER BY id")).fetchall()]

EXAMS = [
    dict(title="General Aptitude Test – Batch 2025", exam_type="online",
         description="Covers numerical, verbal, and reasoning ability. For all departments.",
         duration_minutes=60, passing_marks=15, status="active",
         target_departments="CS,IT,ECE,EEE,MECH,CIVIL",
         question_ids=mcq_ids[:10]),

    dict(title="TCS Aptitude Round 1", exam_type="campus",
         description="Aptitude test for TCS campus drive. Linked to drive round.",
         duration_minutes=45, passing_marks=12, status="active",
         target_departments="CS,IT,ECE",
         question_ids=mcq_ids[:8]),

    dict(title="Coding Assessment – Online", exam_type="online",
         description="Python coding round for placement preparation.",
         duration_minutes=90, passing_marks=10, status="active",
         target_departments="CS,IT",
         question_ids=coding_ids[:3]),

    dict(title="Infosys Technical Round", exam_type="campus",
         description="Technical test for Infosys campus drive.",
         duration_minutes=60, passing_marks=20, status="draft",
         target_departments="CS,IT,ECE",
         question_ids=mcq_ids[3:10] + coding_ids[:2]),

    dict(title="Mock Placement Test – Practice", exam_type="online",
         description="Full-length mock test with MCQ and coding sections.",
         duration_minutes=120, passing_marks=25, status="scheduled",
         target_departments="CS,IT,ECE,EEE",
         question_ids=q_ids[:12]),
]

exam_ids = []
for e in EXAMS:
    total = db.execute(text(
        "SELECT COALESCE(SUM(marks),0) FROM questions WHERE id IN (" +
        ",".join(str(i) for i in e["question_ids"]) + ")"
    )).fetchone()[0] if e["question_ids"] else 0

    insert("exams",
        title=e["title"], description=e["description"],
        duration_minutes=e["duration_minutes"], total_marks=total,
        passing_marks=e["passing_marks"], target_departments=e["target_departments"],
        status=e["status"], exam_type=e["exam_type"],
        otp_required=0, created_by_id=staff_id)

    eid = db.execute(text("SELECT last_insert_rowid()")).fetchone()[0]
    exam_ids.append(eid)

    for order, qid in enumerate(e["question_ids"]):
        insert("exam_questions", exam_id=eid, question_id=qid, order_number=order)

print(f"    ✓ {len(EXAMS)} exams inserted (IDs: {exam_ids})")


# ─────────────────────────────────────────────────────────────
# 4. CAMPUS DRIVES
# ─────────────────────────────────────────────────────────────
print("  → Inserting campus drives…")

tcs_id      = get_id("users", "email = :e", {"e": "hr@tcs.com"})
infosys_id  = get_id("users", "email = :e", {"e": "hr@infosys.com"})
wipro_id    = get_id("users", "email = :e", {"e": "hr@wipro.com"})

now = datetime.utcnow()

DRIVES = [
    dict(
        company_id=tcs_id, title="TCS NQT 2025 – Software Developer",
        job_role="Software Developer", job_description=(
            "TCS is hiring 2025 batch graduates for its National Qualifier Test. "
            "Selected candidates will join as Software Developer Trainees. "
            "6-month training at TCS campus followed by project allocation. "
            "Roles include development, testing, and support across domains."
        ),
        package_lpa=3.5, location="Chennai",
        eligible_departments='["CS","IT","ECE"]', eligible_batches='[2025]',
        min_cgpa=6.0, min_tenth_percent=60.0, min_twelfth_percent=60.0, max_backlogs=0,
        requested_date=(now + timedelta(days=10)).isoformat(),
        confirmed_date=(now + timedelta(days=10)).isoformat(),
        venue="Main Auditorium, Block A",
        status="approved", response_open=1, officer_notes="Dates confirmed with company."
    ),
    dict(
        company_id=infosys_id, title="Infosys Fresher Drive 2025 – Systems Engineer",
        job_role="Systems Engineer", job_description=(
            "Infosys is recruiting fresh graduates for Systems Engineer role. "
            "Successful candidates will undergo an intensive 3-month training program. "
            "Work on diverse projects across financial services, healthcare, and retail. "
            "Attractive compensation with performance bonuses."
        ),
        package_lpa=4.0, location="Bangalore",
        eligible_departments='["CS","IT","ECE","EEE"]', eligible_batches='[2025]',
        min_cgpa=6.5, min_tenth_percent=65.0, min_twelfth_percent=65.0, max_backlogs=0,
        requested_date=(now + timedelta(days=20)).isoformat(),
        confirmed_date=(now + timedelta(days=20)).isoformat(),
        venue="Conference Hall, Block B",
        status="approved", response_open=1, officer_notes="Infosys visit approved."
    ),
    dict(
        company_id=wipro_id, title="Wipro Elite NLTH 2025 – Project Engineer",
        job_role="Project Engineer", job_description=(
            "Wipro's Elite National Level Talent Hunt for Project Engineer positions. "
            "Higher package for top performers. Work on cutting-edge technology projects."
        ),
        package_lpa=6.5, location="Hyderabad",
        eligible_departments='["CS","IT"]', eligible_batches='[2025]',
        min_cgpa=7.5, min_tenth_percent=70.0, min_twelfth_percent=70.0, max_backlogs=0,
        requested_date=(now + timedelta(days=30)).isoformat(),
        confirmed_date=None, venue=None,
        status="pending", response_open=0, officer_notes=None
    ),
    dict(
        company_id=tcs_id, title="TCS BPS – Business Process Services 2024",
        job_role="Process Associate", job_description="Customer support and BPS roles. Previous batch completed.",
        package_lpa=2.5, location="Pune",
        eligible_departments='["CS","IT","ECE","EEE","MECH","CIVIL","MBA","MCA","BSC"]',
        eligible_batches='[2024]',
        min_cgpa=5.0, min_tenth_percent=50.0, min_twelfth_percent=50.0, max_backlogs=2,
        requested_date=(now - timedelta(days=60)).isoformat(),
        confirmed_date=(now - timedelta(days=60)).isoformat(),
        venue="Seminar Hall",
        status="completed", response_open=0, officer_notes="Drive completed successfully. 18 selected."
    ),
]

drive_ids = []
for d in DRIVES:
    insert("campus_drives",
        company_id=d["company_id"], title=d["title"], job_role=d["job_role"],
        job_description=d["job_description"], package_lpa=d["package_lpa"],
        location=d["location"], eligible_departments=d["eligible_departments"],
        eligible_batches=d["eligible_batches"], min_cgpa=d["min_cgpa"],
        min_tenth_percent=d["min_tenth_percent"], min_twelfth_percent=d["min_twelfth_percent"],
        max_backlogs=d["max_backlogs"], requested_date=d["requested_date"],
        confirmed_date=d["confirmed_date"], venue=d["venue"],
        status=d["status"], response_open=d["response_open"], officer_notes=d["officer_notes"])
    did = db.execute(text("SELECT last_insert_rowid()")).fetchone()[0]
    drive_ids.append(did)
print(f"    ✓ {len(DRIVES)} campus drives inserted (IDs: {drive_ids})")


# ─────────────────────────────────────────────────────────────
# 5. OPT-INS (TCS Drive — drive_ids[0], Infosys — drive_ids[1])
# ─────────────────────────────────────────────────────────────
print("  → Inserting student opt-ins…")

student_emails_tcs = [
    ("arun@student.edu",    "opted_in"),
    ("sathish@student.edu", "opted_in"),
    ("anitha@student.edu",  "opted_in"),
    ("vijay@student.edu",   "opted_in"),
    ("priya@student.edu",   "opted_in"),
    ("farhan@student.edu",  "opted_in"),
    ("lakshmi@student.edu", "opted_out"),  # below threshold (backlogs)
]

student_emails_infosys = [
    ("arun@student.edu",    "opted_in"),
    ("sathish@student.edu", "opted_in"),
    ("anitha@student.edu",  "opted_in"),
    ("farhan@student.edu",  "opted_in"),
    ("divya@student.edu",   "opted_in"),
    ("vijay@student.edu",   "opted_in"),
]

for email, status in student_emails_tcs:
    sid = get_id("users", "email = :e", {"e": email})
    if sid:
        insert("drive_opt_ins", drive_id=drive_ids[0], student_id=sid, status=status)

for email, status in student_emails_infosys:
    sid = get_id("users", "email = :e", {"e": email})
    if sid:
        insert("drive_opt_ins", drive_id=drive_ids[1], student_id=sid, status=status)

print(f"    ✓ {len(student_emails_tcs)} TCS opt-ins, {len(student_emails_infosys)} Infosys opt-ins")


# ─────────────────────────────────────────────────────────────
# 6. DRIVE ROUNDS (TCS Drive — 3 rounds)
# ─────────────────────────────────────────────────────────────
print("  → Inserting drive rounds…")

# TCS Rounds
insert("drive_rounds", drive_id=drive_ids[0], round_number=1, round_type="aptitude",
       custom_name=None, description="Written aptitude test – 45 minutes. 50 questions.",
       status="completed", passing_score=30, exam_id=exam_ids[1])
round1_id = db.execute(text("SELECT last_insert_rowid()")).fetchone()[0]

# Link exam to drive round
db.execute(text("UPDATE exams SET drive_round_id = :rid WHERE id = :eid"),
           {"rid": round1_id, "eid": exam_ids[1]})

insert("drive_rounds", drive_id=drive_ids[0], round_number=2, round_type="coding",
       custom_name=None, description="Coding round – Python/Java. 3 problems in 60 minutes.",
       status="pending", passing_score=10, exam_id=None)
round2_id = db.execute(text("SELECT last_insert_rowid()")).fetchone()[0]

insert("drive_rounds", drive_id=drive_ids[0], round_number=3, round_type="hr",
       custom_name=None, description="HR Interview – face to face with HR panel.",
       status="pending", passing_score=0, exam_id=None)

# Infosys Rounds
insert("drive_rounds", drive_id=drive_ids[1], round_number=1, round_type="aptitude",
       custom_name=None, description="Online aptitude screening",
       status="pending", passing_score=25, exam_id=None)

insert("drive_rounds", drive_id=drive_ids[1], round_number=2, round_type="technical",
       custom_name=None, description="Technical interview with engineering team",
       status="pending", passing_score=0, exam_id=None)

insert("drive_rounds", drive_id=drive_ids[1], round_number=3, round_type="group_discussion",
       custom_name=None, description="Group discussion – 10 students per group",
       status="pending", passing_score=0, exam_id=None)

insert("drive_rounds", drive_id=drive_ids[1], round_number=4, round_type="hr",
       custom_name=None, description="Final HR round",
       status="pending", passing_score=0, exam_id=None)

print(f"    ✓ Rounds inserted for TCS (3) and Infosys (4)")


# ─────────────────────────────────────────────────────────────
# 7. DRIVE ROUND RESULTS (TCS Round 1 — completed)
# ─────────────────────────────────────────────────────────────
print("  → Inserting round results (TCS Round 1)…")

ROUND1_RESULTS = [
    ("arun@student.edu",    True,  38, "Excellent performance"),
    ("sathish@student.edu", True,  42, "Top scorer"),
    ("anitha@student.edu",  True,  35, "Good"),
    ("vijay@student.edu",   True,  31, "Passed"),
    ("priya@student.edu",   False, 25, "Needs improvement"),
    ("farhan@student.edu",  True,  33, "Passed"),
]

for email, passed, score, notes in ROUND1_RESULTS:
    sid = get_id("users", "email = :e", {"e": email})
    if sid:
        insert("drive_round_results", round_id=round1_id, student_id=sid,
               passed=1 if passed else 0, score=score, notes=notes)

print(f"    ✓ {len(ROUND1_RESULTS)} round results inserted")


# ─────────────────────────────────────────────────────────────
# 8. EXAM SUBMISSIONS (General Aptitude Test — exam_ids[0])
# ─────────────────────────────────────────────────────────────
print("  → Inserting exam submissions…")

SUBMISSIONS = [
    ("arun@student.edu",    18, True,  0, 1,  0, False),
    ("sathish@student.edu", 20, True,  0, 0,  0, False),
    ("anitha@student.edu",  17, True,  1, 2,  0, False),
    ("vijay@student.edu",   16, True,  0, 0,  0, False),
    ("priya@student.edu",   13, False, 0, 1,  0, False),
    ("farhan@student.edu",  15, True,  0, 0,  0, False),
    ("divya@student.edu",   11, False, 4, 12, 1, True),   # malpractice flagged
    ("lakshmi@student.edu", 10, False, 3, 5,  6, True),   # malpractice flagged
]

total_marks_apt = db.execute(text(
    f"SELECT COALESCE(SUM(q.marks),0) FROM questions q JOIN exam_questions eq ON q.id=eq.question_id WHERE eq.exam_id={exam_ids[0]}"
)).fetchone()[0]

for email, score, passed, tabs, blurs, copies, malp in SUBMISSIONS:
    sid = get_id("users", "email = :e", {"e": email})
    if not sid: continue
    notes_parts = []
    if tabs >= 3: notes_parts.append(f"Tab switches: {tabs}")
    if blurs >= 10: notes_parts.append(f"Window blur: {blurs}")
    if copies >= 5: notes_parts.append(f"Copy/paste: {copies}")

    insert("exam_submissions",
        exam_id=exam_ids[0], student_id=sid,
        answers='{}', score=score, total_marks=total_marks_apt, passed=1 if passed else 0,
        tab_switch_count=tabs, blur_count=blurs, copy_paste_count=copies,
        malpractice_flag=1 if malp else 0,
        malpractice_notes=", ".join(notes_parts) if notes_parts else None)

print(f"    ✓ {len(SUBMISSIONS)} exam submissions inserted")


# ─────────────────────────────────────────────────────────────
# 9. NOTIFICATIONS
# ─────────────────────────────────────────────────────────────
print("  → Inserting notifications…")

admin_id   = get_id("users", "email = :e", {"e": "admin@college.edu"})
officer_id = get_id("users", "email = :e", {"e": "officer@college.edu"})

NOTIFS = [
    dict(sender_id=tcs_id, notif_type="company_to_students", target_role="student",
         drive_id=drive_ids[0],
         title="TCS Drive Tomorrow – Reporting Instructions",
         message=(
             "Dear Students, TCS campus drive is scheduled for tomorrow. "
             "Please report to Main Auditorium by 8:30 AM with your college ID, "
             "2 passport photos, and all academic mark sheets. "
             "Formal dress is mandatory. All opted-in students must confirm attendance."
         )),

    dict(sender_id=infosys_id, notif_type="company_to_students", target_role="student",
         drive_id=drive_ids[1],
         title="Infosys Drive – Documents Required",
         message=(
             "Infosys Systems Engineer drive is coming up. Please carry: "
             "1) Updated resume (2 copies) 2) All semester marksheets "
             "3) Aadhar card copy 4) Passport size photo. "
             "Aptitude round starts at 10:00 AM sharp."
         )),

    dict(sender_id=admin_id, notif_type="head_to_staff", target_role="placement_officer",
         drive_id=None,
         title="Campus Drive Season – Staff Briefing",
         message=(
             "All placement staff: We have 3 companies visiting this month. "
             "Please ensure all classrooms are booked and AV equipment is tested. "
             "Coordinate with department HoDs for student lists by Friday."
         )),

    dict(sender_id=tcs_id, notif_type="company_to_placement", target_role="placement_officer",
         drive_id=drive_ids[0],
         title="TCS – Updated Eligibility Criteria",
         message=(
             "Please note: TCS has updated eligibility to include students with "
             "one active backlog for BPS roles only. Please update student lists accordingly. "
             "Contact: ravi.sharma@tcs.com for queries."
         )),

    dict(sender_id=admin_id, notif_type="system", target_role=None,
         drive_id=None,
         title="Portal Maintenance – Sunday 2 AM",
         message=(
             "The placement portal will undergo maintenance on Sunday from 2:00 AM to 4:00 AM. "
             "Please complete all submissions before this window. "
             "Contact IT support for any issues."
         )),

    dict(sender_id=officer_id, notif_type="head_to_staff", target_role="staff",
         drive_id=drive_ids[0],
         title="Pre-Drive Checklist – TCS",
         message=(
             "Staff team: Please complete the pre-drive checklist: "
             "1) Verify opted-in student count (currently 6) "
             "2) Print attendance sheets "
             "3) Coordinate with TCS coordinator Ravi Sharma "
             "4) Set up Round 1 exam hall. Thank you."
         )),
]

for n in NOTIFS:
    insert("notifications",
        sender_id=n["sender_id"], notif_type=n["notif_type"],
        target_role=n.get("target_role"), drive_id=n.get("drive_id"),
        title=n["title"], message=n["message"])

print(f"    ✓ {len(NOTIFS)} notifications inserted")


# ─────────────────────────────────────────────────────────────
# Commit
# ─────────────────────────────────────────────────────────────
db.commit()
db.close()

print()
print("=" * 60)
print("✅ SEEDING COMPLETE!")
print("=" * 60)
print()
print("LOGIN CREDENTIALS:")
print("-" * 45)
creds = [
    ("Head Admin",         "admin@college.edu",   "Admin@123"),
    ("Placement Officer",  "officer@college.edu", "Officer@123"),
    ("Senior Staff",       "staff1@college.edu",  "Staff@123"),
    ("TCS HR Manager",     "hr@tcs.com",          "TCS@123"),
    ("Infosys HR",         "hr@infosys.com",       "Infosys@123"),
    ("Wipro HR",           "hr@wipro.com",         "Wipro@123"),
    ("Student (Arun)",     "arun@student.edu",    "Student@123"),
    ("Student (Sathish)",  "sathish@student.edu", "Student@123"),
    ("Student (Anitha)",   "anitha@student.edu",  "Student@123"),
]
for role, email, pwd in creds:
    print(f"  {role:25s} | {email:30s} | {pwd}")
print()
print("DEMO DATA SUMMARY:")
print(f"  Users      : 23 (4 staff, 7 company, 12 students)")
print(f"  Questions  : {len(QUESTIONS)} (12 MCQ, 4 coding)")
print(f"  Exams      : {len(EXAMS)} (3 online, 2 campus)")
print(f"  Drives     : {len(DRIVES)} (2 approved, 1 pending, 1 completed)")
print(f"  Opt-ins    : {len(student_emails_tcs)+len(student_emails_infosys)} across 2 drives")
print(f"  Rounds     : 7 (3 for TCS, 4 for Infosys)")
print(f"  Results    : {len(ROUND1_RESULTS)} (TCS Round 1 completed)")
print(f"  Submissions: {len(SUBMISSIONS)} (2 malpractice flagged)")
print(f"  Notifications: {len(NOTIFS)}")
PYEOF
