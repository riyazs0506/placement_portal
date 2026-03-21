-- =============================================================
--  University Placement Portal — Complete SQL Schema + Demo Data
--  Compatible with: SQLite (default), PostgreSQL, MySQL
--  Generated for: placement_portal_v2
-- =============================================================

-- -------------------------------------------------------------
-- DROP existing tables (safe re-run)
-- -------------------------------------------------------------
DROP TABLE IF EXISTS notification_reads;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS drive_round_results;
DROP TABLE IF EXISTS drive_rounds;
DROP TABLE IF EXISTS drive_opt_ins;
DROP TABLE IF EXISTS campus_drives;
DROP TABLE IF EXISTS exam_submissions;
DROP TABLE IF EXISTS exam_questions;
DROP TABLE IF EXISTS exams;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS users;


-- =============================================================
-- TABLE: users
-- =============================================================
CREATE TABLE users (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                VARCHAR(200)    NOT NULL,
    email               VARCHAR(200)    NOT NULL UNIQUE,
    password_hash       VARCHAR(300)    NOT NULL,

    -- Role: one of the 12 enum values
    role                VARCHAR(50)     NOT NULL DEFAULT 'student'
                        CHECK(role IN (
                            'head_admin','placement_officer',
                            'senior_staff','staff','junior_staff',
                            'company_hr_manager','company_tech_interviewer',
                            'company_recruitment_mgr','company_team_leader',
                            'company_officer','company','student'
                        )),

    -- Student academic fields
    department          VARCHAR(100),
    batch_year          INTEGER,
    cgpa                REAL,
    tenth_percent       REAL,
    twelfth_percent     REAL,
    backlogs            INTEGER         DEFAULT 0,
    roll_number         VARCHAR(50),

    -- Company fields
    company_name        VARCHAR(200),
    company_designation VARCHAR(200),

    is_active           BOOLEAN         NOT NULL DEFAULT 1,
    created_at          DATETIME        DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME
);

CREATE INDEX idx_users_email  ON users(email);
CREATE INDEX idx_users_role   ON users(role);
CREATE INDEX idx_users_dept   ON users(department);


-- =============================================================
-- TABLE: questions
-- =============================================================
CREATE TABLE questions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    question_text   TEXT            NOT NULL,
    question_type   VARCHAR(20)     NOT NULL DEFAULT 'mcq'
                    CHECK(question_type IN ('mcq','coding')),
    subject         VARCHAR(100),
    difficulty      VARCHAR(20)     DEFAULT 'medium'
                    CHECK(difficulty IN ('easy','medium','hard')),
    marks           INTEGER         NOT NULL DEFAULT 1,

    -- MCQ options
    option_a        TEXT,
    option_b        TEXT,
    option_c        TEXT,
    option_d        TEXT,
    correct_answer  VARCHAR(1)
                    CHECK(correct_answer IN ('A','B','C','D', NULL)),

    -- Coding
    starter_code    TEXT,
    expected_output TEXT,
    test_cases      TEXT            DEFAULT '[]',   -- JSON array

    created_by_id   INTEGER         REFERENCES users(id) ON DELETE SET NULL,
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_questions_type   ON questions(question_type);
CREATE INDEX idx_questions_subject ON questions(subject);


-- =============================================================
-- TABLE: exams
-- =============================================================
CREATE TABLE exams (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    title               VARCHAR(300)    NOT NULL,
    description         TEXT,
    duration_minutes    INTEGER         NOT NULL DEFAULT 60,
    total_marks         INTEGER         NOT NULL DEFAULT 0,
    passing_marks       INTEGER         NOT NULL DEFAULT 0,
    target_departments  VARCHAR(500),
    start_time          DATETIME,

    status              VARCHAR(20)     NOT NULL DEFAULT 'draft'
                        CHECK(status IN ('draft','scheduled','active','completed')),

    -- IMPORTANT: online = shown in /exams list; campus = drive-round only
    exam_type           VARCHAR(10)     NOT NULL DEFAULT 'online'
                        CHECK(exam_type IN ('online','campus')),

    otp_required        BOOLEAN         NOT NULL DEFAULT 0,
    exam_otp            VARCHAR(10),

    -- Link to a campus drive round (campus exams only)
    drive_round_id      INTEGER         REFERENCES drive_rounds(id) ON DELETE SET NULL,

    created_by_id       INTEGER         NOT NULL REFERENCES users(id),
    created_at          DATETIME        DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME
);

CREATE INDEX idx_exams_status    ON exams(status);
CREATE INDEX idx_exams_type      ON exams(exam_type);


-- =============================================================
-- TABLE: exam_questions  (exam ↔ question join)
-- =============================================================
CREATE TABLE exam_questions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id      INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    question_id  INTEGER NOT NULL REFERENCES questions(id),
    order_number INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_eq_exam ON exam_questions(exam_id);


-- =============================================================
-- TABLE: exam_submissions
-- =============================================================
CREATE TABLE exam_submissions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id          INTEGER NOT NULL REFERENCES exams(id),
    student_id       INTEGER NOT NULL REFERENCES users(id),
    answers          TEXT    DEFAULT '{}',   -- JSON {question_id: answer}
    score            INTEGER NOT NULL DEFAULT 0,
    total_marks      INTEGER NOT NULL DEFAULT 0,
    passed           BOOLEAN NOT NULL DEFAULT 0,
    submitted_at     DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Malpractice tracking
    tab_switch_count  INTEGER DEFAULT 0,
    blur_count        INTEGER DEFAULT 0,
    copy_paste_count  INTEGER DEFAULT 0,
    malpractice_flag  BOOLEAN DEFAULT 0,
    malpractice_notes TEXT,

    UNIQUE(exam_id, student_id)   -- one submission per student per exam
);

CREATE INDEX idx_submissions_exam    ON exam_submissions(exam_id);
CREATE INDEX idx_submissions_student ON exam_submissions(student_id);
CREATE INDEX idx_submissions_malp    ON exam_submissions(malpractice_flag);


-- =============================================================
-- TABLE: campus_drives
-- =============================================================
CREATE TABLE campus_drives (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id      INTEGER NOT NULL REFERENCES users(id),

    title           VARCHAR(300) NOT NULL,
    job_role        VARCHAR(200) NOT NULL,
    job_description TEXT,
    package_lpa     REAL,
    location        VARCHAR(200),

    -- Eligibility (JSON arrays)
    eligible_departments TEXT DEFAULT '[]',  -- ["CS","IT","ECE"]
    eligible_batches     TEXT DEFAULT '[]',  -- [2024,2025]
    min_cgpa             REAL,
    min_tenth_percent    REAL,
    min_twelfth_percent  REAL,
    max_backlogs         INTEGER DEFAULT 0,

    -- Visit scheduling
    requested_date  DATETIME,
    confirmed_date  DATETIME,
    venue           VARCHAR(500),

    -- Workflow state
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK(status IN ('pending','approved','rescheduled','rejected','ongoing','completed')),
    response_open   BOOLEAN NOT NULL DEFAULT 0,
    officer_notes   TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE INDEX idx_drives_status     ON campus_drives(status);
CREATE INDEX idx_drives_company    ON campus_drives(company_id);


-- =============================================================
-- TABLE: drive_opt_ins
-- =============================================================
CREATE TABLE drive_opt_ins (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    drive_id   INTEGER NOT NULL REFERENCES campus_drives(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(id),
    status     VARCHAR(20) NOT NULL DEFAULT 'opted_in'
               CHECK(status IN ('opted_in','opted_out')),
    opted_at   DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(drive_id, student_id)
);

CREATE INDEX idx_optins_drive   ON drive_opt_ins(drive_id);
CREATE INDEX idx_optins_student ON drive_opt_ins(student_id);


-- =============================================================
-- TABLE: drive_rounds
-- =============================================================
CREATE TABLE drive_rounds (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    drive_id      INTEGER NOT NULL REFERENCES campus_drives(id) ON DELETE CASCADE,
    round_number  INTEGER NOT NULL,
    round_type    VARCHAR(30) NOT NULL DEFAULT 'aptitude'
                  CHECK(round_type IN (
                      'aptitude','coding','group_discussion',
                      'technical','hr','custom'
                  )),
    custom_name   VARCHAR(200),
    description   TEXT,
    status        VARCHAR(20) NOT NULL DEFAULT 'pending'
                  CHECK(status IN ('pending','active','completed')),
    passing_score INTEGER DEFAULT 0,

    -- Optional linked campus exam
    exam_id       INTEGER REFERENCES exams(id) ON DELETE SET NULL,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rounds_drive ON drive_rounds(drive_id);


-- =============================================================
-- TABLE: drive_round_results
-- =============================================================
CREATE TABLE drive_round_results (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id   INTEGER NOT NULL REFERENCES drive_rounds(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(id),
    passed     BOOLEAN NOT NULL DEFAULT 0,
    score      INTEGER,
    notes      TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(round_id, student_id)
);

CREATE INDEX idx_results_round   ON drive_round_results(round_id);
CREATE INDEX idx_results_student ON drive_round_results(student_id);


-- =============================================================
-- TABLE: notifications
-- =============================================================
CREATE TABLE notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id   INTEGER NOT NULL REFERENCES users(id),
    notif_type  VARCHAR(40) NOT NULL
                CHECK(notif_type IN (
                    'company_to_students','head_to_staff',
                    'company_to_placement','system'
                )),
    target_role VARCHAR(100),   -- NULL = all roles
    drive_id    INTEGER REFERENCES campus_drives(id) ON DELETE SET NULL,
    title       VARCHAR(300) NOT NULL,
    message     TEXT NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifs_type   ON notifications(notif_type);
CREATE INDEX idx_notifs_sender ON notifications(sender_id);


-- =============================================================
-- TABLE: notification_reads
-- =============================================================
CREATE TABLE notification_reads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    notification_id INTEGER NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    read_at         DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(notification_id, user_id)
);

CREATE INDEX idx_notif_reads_user ON notification_reads(user_id);
