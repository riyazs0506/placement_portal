"""
models.py — Complete database models for University Placement Portal v2.1
"""
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float,
    ForeignKey, Enum as SAEnum, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


# ─────────────────────────────────────────
# Enums
# ─────────────────────────────────────────

class UserRole(str, enum.Enum):
    head_admin               = "head_admin"
    placement_officer        = "placement_officer"
    senior_staff             = "senior_staff"
    staff                    = "staff"
    junior_staff             = "junior_staff"
    company_hr_manager       = "company_hr_manager"
    company_tech_interviewer = "company_tech_interviewer"
    company_recruitment_mgr  = "company_recruitment_mgr"
    company_team_leader      = "company_team_leader"
    company_officer          = "company_officer"
    company                  = "company"
    student                  = "student"


COMPANY_ROLES = {
    UserRole.company_hr_manager, UserRole.company_tech_interviewer,
    UserRole.company_recruitment_mgr, UserRole.company_team_leader,
    UserRole.company_officer, UserRole.company,
}

STAFF_ROLES = {
    UserRole.head_admin, UserRole.placement_officer,
    UserRole.senior_staff, UserRole.staff, UserRole.junior_staff,
}

# Roles allowed to toggle drive response (NOT regular staff)
OFFICER_ROLES = {UserRole.head_admin, UserRole.placement_officer}


class ExamStatus(str, enum.Enum):
    draft     = "draft"
    scheduled = "scheduled"
    active    = "active"
    completed = "completed"


class ExamType(str, enum.Enum):
    online = "online"   # visible in /exams list
    campus = "campus"   # linked to drive round — NOT in /exams list


class DriveStatus(str, enum.Enum):
    pending     = "pending"
    approved    = "approved"
    rescheduled = "rescheduled"
    rejected    = "rejected"
    ongoing     = "ongoing"
    completed   = "completed"


class OptStatus(str, enum.Enum):
    opted_in  = "opted_in"
    opted_out = "opted_out"


class RoundType(str, enum.Enum):
    aptitude         = "aptitude"
    coding           = "coding"
    group_discussion = "group_discussion"
    technical        = "technical"
    hr               = "hr"
    custom           = "custom"


class RoundStatus(str, enum.Enum):
    pending   = "pending"
    active    = "active"
    completed = "completed"


class NotifType(str, enum.Enum):
    company_to_students  = "company_to_students"
    head_to_staff        = "head_to_staff"
    company_to_placement = "company_to_placement"
    round_result         = "round_result"       # auto: student moved to next round
    offer_letter         = "offer_letter"       # student received offer
    system               = "system"


class PlacementStatus(str, enum.Enum):
    shortlisted = "shortlisted"
    selected    = "selected"
    rejected    = "rejected"
    on_hold     = "on_hold"


class DriveType(str, enum.Enum):
    recruitment  = "recruitment"   # full-time job
    internship   = "internship"    # internship only
    both         = "both"          # internship + recruitment


# ─────────────────────────────────────────
# User
# ─────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(200), nullable=False)
    email         = Column(String(200), unique=True, index=True, nullable=False)
    password_hash = Column(String(300), nullable=False)
    role          = Column(SAEnum(UserRole), default=UserRole.student, nullable=False)

    # Student fields
    department      = Column(String(100), nullable=True)
    batch_year      = Column(Integer, nullable=True)
    cgpa            = Column(Float, nullable=True)
    tenth_percent   = Column(Float, nullable=True)
    twelfth_percent = Column(Float, nullable=True)
    backlogs        = Column(Integer, default=0)
    roll_number     = Column(String(50), nullable=True)
    phone           = Column(String(20), nullable=True)

    # Extended student profile fields (v2.4)
    address         = Column(Text, nullable=True)
    linkedin_url    = Column(String(500), nullable=True)
    github_url      = Column(String(500), nullable=True)
    portfolio_url   = Column(String(500), nullable=True)
    skills          = Column(JSON, default=list)        # ["Python","React",…]
    languages       = Column(JSON, default=list)        # ["English","Tamil",…]
    certifications  = Column(JSON, default=list)        # [{name,issuer,year}]
    projects        = Column(JSON, default=list)        # [{title,desc,url}]
    bio             = Column(Text, nullable=True)
    resume_url      = Column(String(500), nullable=True)  # external link
    profile_complete= Column(Boolean, default=False)

    # Company fields
    company_name        = Column(String(200), nullable=True)
    company_designation = Column(String(200), nullable=True)

    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    exams_created      = relationship("Exam", back_populates="created_by", foreign_keys="Exam.created_by_id")
    submissions        = relationship("ExamSubmission", back_populates="student")
    drive_opt_ins      = relationship("DriveOptIn", back_populates="student")
    notifications_sent = relationship("Notification", back_populates="sender", foreign_keys="Notification.sender_id")
    notification_reads = relationship("NotificationRead", back_populates="user")

    @property
    def is_company(self):
        return self.role in COMPANY_ROLES

    @property
    def is_staff_member(self):
        return self.role in STAFF_ROLES


# ─────────────────────────────────────────
# Questions
# ─────────────────────────────────────────

class Question(Base):
    __tablename__ = "questions"

    id            = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), default="mcq")
    subject       = Column(String(100), nullable=True)
    difficulty    = Column(String(20), default="medium")
    marks         = Column(Integer, default=1)

    option_a       = Column(Text, nullable=True)
    option_b       = Column(Text, nullable=True)
    option_c       = Column(Text, nullable=True)
    option_d       = Column(Text, nullable=True)
    correct_answer = Column(String(1), nullable=True)

    starter_code    = Column(Text, nullable=True)
    expected_output = Column(Text, nullable=True)
    test_cases      = Column(JSON, default=list)

    created_by_id  = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at     = Column(DateTime, server_default=func.now())

    exam_questions = relationship("ExamQuestion", back_populates="question")


# ─────────────────────────────────────────
# Exams
# ─────────────────────────────────────────

class Exam(Base):
    __tablename__ = "exams"

    id                 = Column(Integer, primary_key=True, index=True)
    title              = Column(String(300), nullable=False)
    description        = Column(Text, nullable=True)
    duration_minutes   = Column(Integer, default=60)
    total_marks        = Column(Integer, default=0)
    passing_marks      = Column(Integer, default=0)
    target_departments = Column(String(500), nullable=True)
    start_time         = Column(DateTime, nullable=True)
    status             = Column(SAEnum(ExamStatus), default=ExamStatus.draft)
    otp_required       = Column(Boolean, default=False)
    exam_otp           = Column(String(10), nullable=True)
    exam_type          = Column(SAEnum(ExamType), default=ExamType.online)
    drive_round_id     = Column(Integer, ForeignKey("drive_rounds.id"), nullable=True)

    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, onupdate=func.now())

    created_by     = relationship("User", back_populates="exams_created", foreign_keys=[created_by_id])
    exam_questions = relationship("ExamQuestion", back_populates="exam", cascade="all, delete-orphan")
    submissions    = relationship("ExamSubmission", back_populates="exam")
    drive_round    = relationship("DriveRound", back_populates="exam",
                                  foreign_keys=[drive_round_id],
                                  primaryjoin="Exam.drive_round_id == DriveRound.id")


class ExamQuestion(Base):
    __tablename__ = "exam_questions"

    id           = Column(Integer, primary_key=True)
    exam_id      = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"))
    question_id  = Column(Integer, ForeignKey("questions.id"))
    order_number = Column(Integer, default=0)

    exam     = relationship("Exam", back_populates="exam_questions")
    question = relationship("Question", back_populates="exam_questions")


class ExamSubmission(Base):
    __tablename__ = "exam_submissions"

    id           = Column(Integer, primary_key=True, index=True)
    exam_id      = Column(Integer, ForeignKey("exams.id"), nullable=False)
    student_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    answers      = Column(JSON, default=dict)
    score        = Column(Integer, default=0)
    total_marks  = Column(Integer, default=0)
    passed       = Column(Boolean, default=False)
    submitted_at = Column(DateTime, server_default=func.now())

    # Malpractice
    tab_switch_count  = Column(Integer, default=0)
    blur_count        = Column(Integer, default=0)
    copy_paste_count  = Column(Integer, default=0)
    malpractice_flag  = Column(Boolean, default=False)
    malpractice_notes = Column(Text, nullable=True)

    exam    = relationship("Exam", back_populates="submissions")
    student = relationship("User", back_populates="submissions")

    __table_args__ = (UniqueConstraint("exam_id", "student_id"),)


# ─────────────────────────────────────────
# Campus Drives
# ─────────────────────────────────────────

class CampusDrive(Base):
    __tablename__ = "campus_drives"

    id              = Column(Integer, primary_key=True, index=True)
    company_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    title           = Column(String(300), nullable=False)
    job_role        = Column(String(200), nullable=False)
    job_description = Column(Text, nullable=True)
    package_lpa     = Column(Float, nullable=True)
    location        = Column(String(200), nullable=True)

    eligible_departments = Column(JSON, default=list)
    eligible_batches     = Column(JSON, default=list)
    min_cgpa             = Column(Float, nullable=True)
    min_tenth_percent    = Column(Float, nullable=True)
    min_twelfth_percent  = Column(Float, nullable=True)
    max_backlogs         = Column(Integer, default=0)

    requested_date = Column(DateTime, nullable=True)
    confirmed_date = Column(DateTime, nullable=True)
    venue          = Column(String(500), nullable=True)

    # Drive type (recruitment / internship / both) — v2.3
    drive_type     = Column(SAEnum(DriveType), default=DriveType.recruitment)
    stipend_amount = Column(Float, nullable=True)      # for internship
    internship_duration = Column(String(100), nullable=True)  # e.g. "6 months"
    # Rounds plan (JSON list of round types created at drive setup time)
    planned_rounds = Column(JSON, default=list)

    status        = Column(SAEnum(DriveStatus), default=DriveStatus.pending)
    response_open = Column(Boolean, default=False)
    officer_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    company          = relationship("User", foreign_keys=[company_id])
    opt_ins          = relationship("DriveOptIn", back_populates="drive", cascade="all, delete-orphan")
    rounds           = relationship("DriveRound", back_populates="drive",
                                    cascade="all, delete-orphan", order_by="DriveRound.round_number")
    placement_results = relationship("PlacementResult", back_populates="drive", cascade="all, delete-orphan")


class DriveOptIn(Base):
    __tablename__ = "drive_opt_ins"

    id         = Column(Integer, primary_key=True)
    drive_id   = Column(Integer, ForeignKey("campus_drives.id", ondelete="CASCADE"))
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status     = Column(SAEnum(OptStatus), default=OptStatus.opted_in)
    opted_at   = Column(DateTime, server_default=func.now())

    drive   = relationship("CampusDrive", back_populates="opt_ins")
    student = relationship("User")

    __table_args__ = (UniqueConstraint("drive_id", "student_id"),)


class DriveRound(Base):
    __tablename__ = "drive_rounds"

    id            = Column(Integer, primary_key=True, index=True)
    drive_id      = Column(Integer, ForeignKey("campus_drives.id", ondelete="CASCADE"))
    round_number  = Column(Integer, nullable=False)
    round_type    = Column(SAEnum(RoundType), default=RoundType.aptitude)
    custom_name   = Column(String(200), nullable=True)
    description   = Column(Text, nullable=True)
    status        = Column(SAEnum(RoundStatus), default=RoundStatus.pending)
    passing_score = Column(Integer, default=0)
    exam_id       = Column(Integer, nullable=True)
    created_at    = Column(DateTime, server_default=func.now())

    drive   = relationship("CampusDrive", back_populates="rounds")
    results = relationship("DriveRoundResult", back_populates="round", cascade="all, delete-orphan")
    shortlist_entries = relationship("RoundShortlist", cascade="all, delete-orphan",
                                     primaryjoin="DriveRound.id == foreign(RoundShortlist.round_id)")
    exam    = relationship("Exam", back_populates="drive_round",
                           foreign_keys="[Exam.drive_round_id]",
                           primaryjoin="DriveRound.id == Exam.drive_round_id",
                           uselist=False)


class DriveRoundResult(Base):
    __tablename__ = "drive_round_results"

    id         = Column(Integer, primary_key=True)
    round_id   = Column(Integer, ForeignKey("drive_rounds.id", ondelete="CASCADE"))
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    passed     = Column(Boolean, default=False)
    score      = Column(Integer, nullable=True)
    notes      = Column(Text, nullable=True)
    notified   = Column(Boolean, default=False)  # whether student was notified
    created_at = Column(DateTime, server_default=func.now())

    round   = relationship("DriveRound", back_populates="results")
    student = relationship("User")

    __table_args__ = (UniqueConstraint("round_id", "student_id"),)


# ─────────────────────────────────────────
# Placement Results / Offer Letters
# ─────────────────────────────────────────

class PlacementResult(Base):
    __tablename__ = "placement_results"

    id                = Column(Integer, primary_key=True, index=True)
    drive_id          = Column(Integer, ForeignKey("campus_drives.id", ondelete="CASCADE"))
    student_id        = Column(Integer, ForeignKey("users.id"))
    status            = Column(SAEnum(PlacementStatus), default=PlacementStatus.shortlisted)
    round_id          = Column(Integer, ForeignKey("drive_rounds.id"), nullable=True)
    offer_role        = Column(String(200), nullable=True)
    offer_package_lpa = Column(Float, nullable=True)
    joining_date      = Column(String(50), nullable=True)
    offer_letter_text = Column(Text, nullable=True)
    notes             = Column(Text, nullable=True)
    created_at        = Column(DateTime, server_default=func.now())
    updated_at        = Column(DateTime, onupdate=func.now())

    drive   = relationship("CampusDrive", back_populates="placement_results")
    student = relationship("User")
    round   = relationship("DriveRound")

    __table_args__ = (UniqueConstraint("drive_id", "student_id"),)


# ─────────────────────────────────────────
# Notifications
# ─────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id          = Column(Integer, primary_key=True, index=True)
    sender_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    notif_type  = Column(SAEnum(NotifType), nullable=False)
    target_role = Column(String(100), nullable=True)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # direct to one user
    drive_id    = Column(Integer, ForeignKey("campus_drives.id"), nullable=True)
    title       = Column(String(300), nullable=False)
    message     = Column(Text, nullable=False)
    created_at  = Column(DateTime, server_default=func.now())

    sender      = relationship("User", back_populates="notifications_sent", foreign_keys=[sender_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
    reads       = relationship("NotificationRead", back_populates="notification", cascade="all, delete-orphan")


class NotificationRead(Base):
    __tablename__ = "notification_reads"

    id              = Column(Integer, primary_key=True)
    notification_id = Column(Integer, ForeignKey("notifications.id", ondelete="CASCADE"))
    user_id         = Column(Integer, ForeignKey("users.id"))
    read_at         = Column(DateTime, server_default=func.now())

    notification = relationship("Notification", back_populates="reads")
    user         = relationship("User", back_populates="notification_reads")

    __table_args__ = (UniqueConstraint("notification_id", "user_id"),)


# ─────────────────────────────────────────
# Round HR Selection (v2.3 NEW)
# ─────────────────────────────────────────

class RoundShortlist(Base):
    """
    HR manually selects students for a round.
    student_status: 'selected' | 'rejected' | 'hold'
    """
    __tablename__ = "round_shortlists"

    id          = Column(Integer, primary_key=True, index=True)
    round_id    = Column(Integer, ForeignKey("drive_rounds.id", ondelete="CASCADE"))
    student_id  = Column(Integer, ForeignKey("users.id"), nullable=False)
    status      = Column(String(20), default="selected")  # selected|rejected|hold
    hr_notes    = Column(Text, nullable=True)
    notified    = Column(Boolean, default=False)
    created_at  = Column(DateTime, server_default=func.now())

    round   = relationship("DriveRound")
    student = relationship("User")

    __table_args__ = (UniqueConstraint("round_id", "student_id"),)


# ─────────────────────────────────────────
# Exam Batch Monitoring (v2.2 NEW)
# ─────────────────────────────────────────

class ExamBatch(Base):
    """
    A batch assigns a subset of opted-in students to one staff invigilator
    for a specific exam. Staff generate OTP per-batch and monitor their students.
    """
    __tablename__ = "exam_batches"

    id            = Column(Integer, primary_key=True, index=True)
    exam_id       = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    staff_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    batch_name    = Column(String(100), nullable=False)   # e.g. "Batch A", "Hall 1"
    otp           = Column(String(10), nullable=True)     # staff-generated OTP for this batch
    otp_active    = Column(Boolean, default=False)        # True once staff enables it
    exam_enabled  = Column(Boolean, default=False)        # staff taps "Start Exam" for batch
    created_at    = Column(DateTime, server_default=func.now())

    exam    = relationship("Exam", foreign_keys=[exam_id])
    staff   = relationship("User", foreign_keys=[staff_id])
    members = relationship("ExamBatchMember", back_populates="batch",
                           cascade="all, delete-orphan")


class ExamBatchMember(Base):
    """Individual student assigned to a batch."""
    __tablename__ = "exam_batch_members"

    id         = Column(Integer, primary_key=True)
    batch_id   = Column(Integer, ForeignKey("exam_batches.id", ondelete="CASCADE"))
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    otp_entered = Column(Boolean, default=False)   # student entered OTP
    is_present  = Column(Boolean, default=False)   # student started exam
    joined_at   = Column(DateTime, nullable=True)

    batch   = relationship("ExamBatch", back_populates="members")
    student = relationship("User")

    __table_args__ = (UniqueConstraint("batch_id", "student_id"),)
