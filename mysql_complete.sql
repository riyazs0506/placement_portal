-- ================================================================
-- UNIVERSITY PLACEMENT PORTAL v2 — Complete MySQL Schema
-- MERGED: Original schema + Campus Drive + Notifications + All Roles
-- ================================================================
-- HOW TO USE:
--   1. Open MySQL Workbench (or any MySQL client)
--   2. Copy this ENTIRE file and paste → Execute (Ctrl+Shift+Enter)
--   3. Then run the SAMPLE DATA section at the bottom
-- ================================================================

DROP DATABASE IF EXISTS placement_portal;

CREATE DATABASE placement_portal
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE placement_portal;

-- ================================================================
-- TABLE 1: users
-- 12 roles: head_admin, placement_officer, senior_staff, staff,
--           junior_staff, company_hr_manager, company_tech_interviewer,
--           company_recruitment_mgr, company_team_leader,
--           company_officer, company, student
-- ================================================================
CREATE TABLE users (
    id                   INT           NOT NULL AUTO_INCREMENT,
    name                 VARCHAR(200)  NOT NULL,
    email                VARCHAR(200)  NOT NULL,
    password_hash        VARCHAR(300)  NOT NULL,
    role                 VARCHAR(50)   NOT NULL DEFAULT 'student',

    -- Student fields
    roll_number          VARCHAR(50)   NULL,
    department           VARCHAR(100)  NULL,
    batch_year           INT           NULL,
    cgpa                 DECIMAL(4,2)  NULL,
    tenth_percent        DECIMAL(5,2)  NULL,
    twelfth_percent      DECIMAL(5,2)  NULL,
    backlogs             INT           NOT NULL DEFAULT 0,
    phone                VARCHAR(20)   NULL,

    -- Company fields
    company_name         VARCHAR(200)  NULL,
    company_designation  VARCHAR(200)  NULL,

    is_active            TINYINT(1)    NOT NULL DEFAULT 1,
    created_at           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME      NULL ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE  KEY uq_users_email      (email),
    INDEX        idx_users_role     (role),
    INDEX        idx_users_dept     (department),
    INDEX        idx_users_active   (is_active),

    CONSTRAINT chk_users_role CHECK (role IN (
        'head_admin','placement_officer','senior_staff','staff','junior_staff',
        'company_hr_manager','company_tech_interviewer','company_recruitment_mgr',
        'company_team_leader','company_officer','company','student'
    )),
    CONSTRAINT chk_cgpa      CHECK (cgpa            IS NULL OR (cgpa BETWEEN 0 AND 10)),
    CONSTRAINT chk_tenth     CHECK (tenth_percent   IS NULL OR (tenth_percent BETWEEN 0 AND 100)),
    CONSTRAINT chk_twelfth   CHECK (twelfth_percent IS NULL OR (twelfth_percent BETWEEN 0 AND 100)),
    CONSTRAINT chk_backlogs  CHECK (backlogs >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
-- TABLE 2: questions
-- ================================================================
CREATE TABLE questions (
    id              INT     NOT NULL AUTO_INCREMENT,
    question_text   TEXT    NOT NULL,
    question_type   ENUM('mcq','coding') NOT NULL DEFAULT 'mcq',
    subject         VARCHAR(100) NULL,
    difficulty      ENUM('easy','medium','hard') NOT NULL DEFAULT 'medium',
    marks           INT     NOT NULL DEFAULT 1,

    -- MCQ
    option_a        TEXT    NULL,
    option_b        TEXT    NULL,
    option_c        TEXT    NULL,
    option_d        TEXT    NULL,
    correct_answer  VARCHAR(1) NULL,

    -- Coding
    starter_code    TEXT    NULL,
    expected_output TEXT    NULL,
    test_cases      JSON    NULL,

    created_by_id   INT     NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    INDEX idx_q_type       (question_type),
    INDEX idx_q_subject    (subject),
    INDEX idx_q_difficulty (difficulty),
    INDEX idx_q_created_by (created_by_id),

    CONSTRAINT fk_q_created_by
        FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT chk_q_answer CHECK (correct_answer IN ('A','B','C','D') OR correct_answer IS NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
-- TABLE 3: exams
-- exam_type: 'online' = visible in student exam list
--            'campus' = only accessible via campus drive round
-- ================================================================
CREATE TABLE exams (
    id                    INT          NOT NULL AUTO_INCREMENT,
    title                 VARCHAR(300) NOT NULL,
    description           TEXT         NULL,
    duration_minutes      INT          NOT NULL DEFAULT 60,
    total_marks           INT          NOT NULL DEFAULT 0,
    passing_marks         INT          NOT NULL DEFAULT 0,
    target_departments    VARCHAR(500) NULL,
    start_time            DATETIME     NULL,
    end_time              DATETIME     NULL,

    status                ENUM('draft','scheduled','active','completed')
                                       NOT NULL DEFAULT 'draft',

    -- online = student exam list | campus = drive round only
    exam_type             ENUM('online','campus') NOT NULL DEFAULT 'online',

    otp_required          TINYINT(1)   NOT NULL DEFAULT 0,
    exam_otp              VARCHAR(20)  NULL,

    -- If campus exam, linked drive round
    drive_round_id        INT          NULL,

    -- Seating (from original schema)
    total_students_expected INT        NULL,
    rooms_json            JSON         NULL,

    created_by_id         INT          NULL,
    created_at            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            DATETIME     NULL ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    INDEX idx_exams_status     (status),
    INDEX idx_exams_type       (exam_type),
    INDEX idx_exams_start_time (start_time),
    INDEX idx_exams_created_by (created_by_id),
    INDEX idx_exams_drive_round(drive_round_id),

    CONSTRAINT fk_exams_created_by
        FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL
    -- drive_round_id FK added after drive_rounds table is created
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
-- TABLE 4: exam_questions
-- ================================================================
CREATE TABLE exam_questions (
    id           INT NOT NULL AUTO_INCREMENT,
    exam_id      INT NOT NULL,
    question_id  INT NOT NULL,
    order_number INT NOT NULL DEFAULT 0,

    PRIMARY KEY (id),
    UNIQUE KEY uq_exam_question (exam_id, question_id),
    INDEX idx_eq_exam_id     (exam_id),
    INDEX idx_eq_question_id (question_id),

    CONSTRAINT fk_eq_exam
        FOREIGN KEY (exam_id)     REFERENCES exams(id)     ON DELETE CASCADE,
    CONSTRAINT fk_eq_question
        FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
-- TABLE 5: exam_submissions
-- Full malpractice tracking: tab switches, blur, copy/paste
-- ================================================================
CREATE TABLE exam_submissions (
    id                  INT         NOT NULL AUTO_INCREMENT,
    exam_id             INT         NOT NULL,
    student_id          INT         NOT NULL,
    answers             JSON        NULL,
    score               INT         NOT NULL DEFAULT 0,
    total_marks         INT         NOT NULL DEFAULT 0,
    passed              TINYINT(1)  NOT NULL DEFAULT 0,
    submitted_at        DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    time_taken_seconds  INT         NULL,
    is_auto_submitted   TINYINT(1)  NOT NULL DEFAULT 0,

    -- Malpractice counters
    tab_switch_count    INT         NOT NULL DEFAULT 0,
    blur_count          INT         NOT NULL DEFAULT 0,
    copy_paste_count    INT         NOT NULL DEFAULT 0,
    malpractice_flag    TINYINT(1)  NOT NULL DEFAULT 0,
    malpractice_notes   TEXT        NULL,

    PRIMARY KEY (id),
    UNIQUE KEY uq_submission   (exam_id, student_id),
    INDEX idx_sub_exam_id      (exam_id),
    INDEX idx_sub_student_id   (student_id),
    INDEX idx_sub_malpractice  (malpractice_flag),

    CONSTRAINT fk_sub_exam
        FOREIGN KEY (exam_id)    REFERENCES exams(id) ON DELETE CASCADE,
    CONSTRAINT fk_sub_student
        FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
-- TABLE 6: results
-- Approval + release workflow (from original schema)
-- ================================================================
CREATE TABLE results (
    id              INT          NOT NULL AUTO_INCREMENT,
    exam_id         INT          NOT NULL,
    student_id      INT          NOT NULL,
    submission_id   INT          NULL,

    total_marks     INT          NOT NULL DEFAULT 0,
    obtained_marks  DECIMAL(8,2) NOT NULL DEFAULT 0.00,
    percentage      DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    is_passed       TINYINT(1)   NOT NULL DEFAULT 0,
    `rank`          INT          NULL,

    is_approved     TINYINT(1)   NOT NULL DEFAULT 0,
    is_released     TINYINT(1)   NOT NULL DEFAULT 0,
    approved_by     INT          NULL,
    approved_at     DATETIME     NULL,
    calculated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_result        (exam_id, student_id),
    INDEX idx_res_exam_id       (exam_id),
    INDEX idx_res_student_id    (student_id),
    INDEX idx_res_percentage    (percentage),
    INDEX idx_res_rank          (`rank`),
    INDEX idx_res_is_approved   (is_approved),
    INDEX idx_res_is_released   (is_released),

    CONSTRAINT fk_res_exam
        FOREIGN KEY (exam_id)       REFERENCES exams(id)            ON DELETE CASCADE,
    CONSTRAINT fk_res_student
        FOREIGN KEY (student_id)    REFERENCES users(id)            ON DELETE CASCADE,
    CONSTRAINT fk_res_submission
        FOREIGN KEY (submission_id) REFERENCES exam_submissions(id) ON DELETE SET NULL,
    CONSTRAINT fk_res_approved_by
        FOREIGN KEY (approved_by)   REFERENCES users(id)            ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
-- TABLE 7: exam_attendance
-- OTP verification, IP tracking, seating, block/reactivate
-- ================================================================
CREATE TABLE exam_attendance (
    id              INT          NOT NULL AUTO_INCREMENT,
    exam_id         INT          NOT NULL,
    student_id      INT          NOT NULL,
    status          ENUM('absent','present') NOT NULL DEFAULT 'absent',
    otp_verified    TINYINT(1)   NOT NULL DEFAULT 0,
    otp_verified_at DATETIME     NULL,
    is_blocked      TINYINT(1)   NOT NULL DEFAULT 0,
    blocked_reason  VARCHAR(300) NULL,
    reactivated     TINYINT(1)   NOT NULL DEFAULT 0,
    ip_address      VARCHAR(50)  NULL,
    device_info     VARCHAR(300) NULL,
    seat_number     VARCHAR(20)  NULL,
    room_name       VARCHAR(100) NULL,
    marked_by_id    INT          NULL,
    marked_at       DATETIME     NULL,

    PRIMARY KEY (id),
    UNIQUE KEY uq_att           (exam_id, student_id),
    INDEX idx_att_exam          (exam_id),
    INDEX idx_att_student       (student_id),
    INDEX idx_att_status        (status),
    INDEX idx_att_otp_verified  (otp_verified),
    INDEX idx_att_blocked       (is_blocked),

    CONSTRAINT fk_att_exam
        FOREIGN KEY (exam_id)      REFERENCES exams(id) ON DELETE CASCADE,
    CONSTRAINT fk_att_student
        FOREIGN KEY (student_id)   REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_att_marked
        FOREIGN KEY (marked_by_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
-- TABLE 8: malpractice
-- Staff-logged violations per student per exam
-- ================================================================
CREATE TABLE malpractice (
    id            INT          NOT NULL AUTO_INCREMENT,
    exam_id       INT          NOT NULL,
    student_id    INT          NOT NULL,
    violations    INT          NOT NULL DEFAULT 0,
    violation_log JSON         NULL,
    action        ENUM('warning','penalised','expelled','reinstated') NULL,
    action_note   VARCHAR(500) NULL,
    action_by_id  INT          NULL,
    action_at     DATETIME     NULL,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_mal           (exam_id, student_id),
    INDEX idx_mal_exam          (exam_id),
    INDEX idx_mal_student       (student_id),
    INDEX idx_mal_action        (action),

    CONSTRAINT fk_mal_exam
        FOREIGN KEY (exam_id)      REFERENCES exams(id) ON DELETE CASCADE,
    CONSTRAINT fk_mal_student
        FOREIGN KEY (student_id)   REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_mal_actionby
        FOREIGN KEY (action_by_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
-- TABLE 9: campus_drives
-- Full lifecycle: request → approve → opt-in → rounds → results
-- ================================================================
CREATE TABLE campus_drives (
    id                   INT          NOT NULL AUTO_INCREMENT,
    company_id           INT          NOT NULL,

    title                VARCHAR(300) NOT NULL,
    job_role             VARCHAR(200) NOT NULL,
    job_description      TEXT         NULL,
    package_lpa          DECIMAL(6,2) NULL,
    location             VARCHAR(200) NULL,

    -- Eligibility (JSON arrays)
    eligible_departments JSON         NULL,  -- ["CS","IT","ECE"]
    eligible_batches     JSON         NULL,  -- [2024,2025]
    min_cgpa             DECIMAL(4,2) NULL,
    min_tenth_percent    DECIMAL(5,2) NULL,
    min_twelfth_percent  DECIMAL(5,2) NULL,
    max_backlogs         INT          NOT NULL DEFAULT 0,

    -- Visit scheduling
    requested_date       DATETIME     NULL,
    confirmed_date       DATETIME     NULL,
    venue                VARCHAR(500) NULL,

    -- Workflow
    status               ENUM('pending','approved','rescheduled','rejected','ongoing','completed')
                                      NOT NULL DEFAULT 'pending',
    response_open        TINYINT(1)   NOT NULL DEFAULT 0,
    officer_notes        TEXT         NULL,

    created_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME     NULL ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    INDEX idx_drives_status   (status),
    INDEX idx_drives_company  (company_id),
    INDEX idx_drives_resp     (response_open),

    CONSTRAINT fk_drives_company
        FOREIGN KEY (company_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_drive_status CHECK (status IN (
        'pending','approved','rescheduled','rejected','ongoing','completed'
    ))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
-- TABLE 10: drive_opt_ins
-- Students opt in or out of an approved campus drive
-- ================================================================
CREATE TABLE drive_opt_ins (
    id         INT      NOT NULL AUTO_INCREMENT,
    drive_id   INT      NOT NULL,
    student_id INT      NOT NULL,
    status     ENUM('opted_in','opted_out') NOT NULL DEFAULT 'opted_in',
    opted_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_optin        (drive_id, student_id),
    INDEX idx_optin_drive      (drive_id),
    INDEX idx_optin_student    (student_id),
    INDEX idx_optin_status     (status),

    CONSTRAINT fk_optin_drive
        FOREIGN KEY (drive_id)   REFERENCES campus_drives(id) ON DELETE CASCADE,
    CONSTRAINT fk_optin_student
        FOREIGN KEY (student_id) REFERENCES users(id)         ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
-- TABLE 11: drive_rounds
-- Aptitude → Coding → GD → Technical → HR → Custom
-- ================================================================
CREATE TABLE drive_rounds (
    id            INT          NOT NULL AUTO_INCREMENT,
    drive_id      INT          NOT NULL,
    round_number  INT          NOT NULL,
    round_type    ENUM('aptitude','coding','group_discussion','technical','hr','custom')
                               NOT NULL DEFAULT 'aptitude',
    custom_name   VARCHAR(200) NULL,
    description   TEXT         NULL,
    status        ENUM('pending','active','completed') NOT NULL DEFAULT 'pending',
    passing_score INT          NOT NULL DEFAULT 0,
    exam_id       INT          NULL,  -- linked campus exam (optional)
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_round          (drive_id, round_number),
    INDEX idx_rounds_drive       (drive_id),
    INDEX idx_rounds_status      (status),
    INDEX idx_rounds_exam        (exam_id),

    CONSTRAINT fk_rounds_drive
        FOREIGN KEY (drive_id) REFERENCES campus_drives(id) ON DELETE CASCADE,
    CONSTRAINT fk_rounds_exam
        FOREIGN KEY (exam_id)  REFERENCES exams(id)         ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
-- TABLE 12: drive_round_results
-- Pass/fail per student per round — auto-updated from exam submissions
-- ================================================================
CREATE TABLE drive_round_results (
    id         INT      NOT NULL AUTO_INCREMENT,
    round_id   INT      NOT NULL,
    student_id INT      NOT NULL,
    passed     TINYINT(1) NOT NULL DEFAULT 0,
    score      INT      NULL,
    notes      TEXT     NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_round_result    (round_id, student_id),
    INDEX idx_rr_round            (round_id),
    INDEX idx_rr_student          (student_id),
    INDEX idx_rr_passed           (passed),

    CONSTRAINT fk_rr_round
        FOREIGN KEY (round_id)   REFERENCES drive_rounds(id) ON DELETE CASCADE,
    CONSTRAINT fk_rr_student
        FOREIGN KEY (student_id) REFERENCES users(id)        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
-- TABLE 13: notifications
-- company→students | head→staff | company→placement | system
-- ================================================================
CREATE TABLE notifications (
    id          INT          NOT NULL AUTO_INCREMENT,
    sender_id   INT          NOT NULL,
    notif_type  ENUM('company_to_students','head_to_staff','company_to_placement','system')
                             NOT NULL,
    target_role VARCHAR(100) NULL,   -- NULL = broadcast to all
    drive_id    INT          NULL,
    title       VARCHAR(300) NOT NULL,
    message     TEXT         NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    INDEX idx_notif_type    (notif_type),
    INDEX idx_notif_sender  (sender_id),
    INDEX idx_notif_drive   (drive_id),
    INDEX idx_notif_role    (target_role),

    CONSTRAINT fk_notif_sender
        FOREIGN KEY (sender_id) REFERENCES users(id)         ON DELETE CASCADE,
    CONSTRAINT fk_notif_drive
        FOREIGN KEY (drive_id)  REFERENCES campus_drives(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
-- TABLE 14: notification_reads
-- Track which users have read which notifications
-- ================================================================
CREATE TABLE notification_reads (
    id              INT      NOT NULL AUTO_INCREMENT,
    notification_id INT      NOT NULL,
    user_id         INT      NOT NULL,
    read_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_notif_read   (notification_id, user_id),
    INDEX idx_nr_notification  (notification_id),
    INDEX idx_nr_user          (user_id),

    CONSTRAINT fk_nr_notification
        FOREIGN KEY (notification_id) REFERENCES notifications(id) ON DELETE CASCADE,
    CONSTRAINT fk_nr_user
        FOREIGN KEY (user_id)         REFERENCES users(id)         ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
-- ADD FK: exams.drive_round_id → drive_rounds.id
-- (added after drive_rounds table exists)
-- ================================================================
ALTER TABLE exams
    ADD CONSTRAINT fk_exams_drive_round
        FOREIGN KEY (drive_round_id) REFERENCES drive_rounds(id) ON DELETE SET NULL;


-- ================================================================
-- USEFUL VIEWS
-- ================================================================

-- View: student eligibility summary
CREATE VIEW v_student_profile AS
SELECT
    u.id,
    u.name,
    u.email,
    u.role,
    u.department,
    u.batch_year,
    u.cgpa,
    u.tenth_percent,
    u.twelfth_percent,
    u.backlogs,
    u.roll_number,
    u.is_active
FROM users u
WHERE u.role = 'student';

-- View: drive overview with opt-in counts
CREATE VIEW v_drive_overview AS
SELECT
    d.id,
    d.title,
    d.job_role,
    u.name         AS company_name,
    u.company_name AS company,
    d.package_lpa,
    d.location,
    d.status,
    d.response_open,
    d.confirmed_date,
    d.venue,
    COUNT(CASE WHEN o.status = 'opted_in'  THEN 1 END) AS opted_in_count,
    COUNT(CASE WHEN o.status = 'opted_out' THEN 1 END) AS opted_out_count,
    COUNT(r.id)                                         AS round_count
FROM campus_drives d
JOIN users u          ON u.id = d.company_id
LEFT JOIN drive_opt_ins  o ON o.drive_id = d.id
LEFT JOIN drive_rounds   r ON r.drive_id = d.id
GROUP BY d.id, d.title, d.job_role, u.name, u.company_name,
         d.package_lpa, d.location, d.status, d.response_open,
         d.confirmed_date, d.venue;

-- View: exam results with approval status
CREATE VIEW v_exam_results AS
SELECT
    r.id,
    e.title         AS exam_title,
    e.exam_type,
    u.name          AS student_name,
    u.roll_number,
    u.department,
    r.obtained_marks,
    r.total_marks,
    r.percentage,
    r.is_passed,
    r.`rank`,
    r.is_approved,
    r.is_released,
    r.calculated_at,
    s.tab_switch_count,
    s.blur_count,
    s.copy_paste_count,
    s.malpractice_flag
FROM results r
JOIN exams           e ON e.id = r.exam_id
JOIN users           u ON u.id = r.student_id
LEFT JOIN exam_submissions s ON s.id = r.submission_id;

-- View: malpractice report
CREATE VIEW v_malpractice_report AS
SELECT
    m.id,
    e.title         AS exam_title,
    u.name          AS student_name,
    u.roll_number,
    u.department,
    s.tab_switch_count,
    s.blur_count,
    s.copy_paste_count,
    s.malpractice_flag,
    m.violations,
    m.action,
    m.action_note,
    a.name          AS action_by,
    m.action_at
FROM malpractice m
JOIN exams           e ON e.id = m.exam_id
JOIN users           u ON u.id = m.student_id
LEFT JOIN exam_submissions s ON s.exam_id = m.exam_id AND s.student_id = m.student_id
LEFT JOIN users          a ON a.id = m.action_by_id;


-- ================================================================
-- ================================================================
-- SAMPLE / DEMO DATA
-- ================================================================
-- ================================================================


-- ================================================================
-- USERS
-- NOTE: All passwords below are bcrypt hashes.
--   admin@college.edu    → Admin@123
--   officer@college.edu  → Officer@123
--   staff1@college.edu   → Staff@123
--   hr@tcs.com           → TCS@123
--   *@student.edu        → Student@123
--
-- If login fails, regenerate hashes with:
--   python seed_data.py
-- ================================================================

INSERT INTO users
    (name, email, password_hash, role,
     department, batch_year, cgpa, tenth_percent, twelfth_percent,
     backlogs, roll_number, phone, company_name, company_designation)
VALUES

-- ── Staff ─────────────────────────────────────────────────
('Dr. Rajesh Kumar',
 'admin@college.edu',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4tbQJLNWCi',
 'head_admin',
 NULL, NULL, NULL, NULL, NULL, 0, NULL, NULL, NULL, NULL),

('Mrs. Priya Nair',
 'officer@college.edu',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'placement_officer',
 NULL, NULL, NULL, NULL, NULL, 0, NULL, NULL, NULL, NULL),

('Mr. Arjun Mehta',
 'staff1@college.edu',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'senior_staff',
 NULL, NULL, NULL, NULL, NULL, 0, NULL, NULL, NULL, NULL),

('Ms. Kavitha Rajan',
 'staff2@college.edu',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'staff',
 NULL, NULL, NULL, NULL, NULL, 0, NULL, NULL, NULL, NULL),

-- ── TCS Company ───────────────────────────────────────────
('Ravi Sharma',
 'hr@tcs.com',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'company_hr_manager',
 NULL, NULL, NULL, NULL, NULL, 0, NULL, '+91 9800000001', 'TCS Ltd', 'HR Manager'),

('Deepa Krishnan',
 'tech@tcs.com',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'company_tech_interviewer',
 NULL, NULL, NULL, NULL, NULL, 0, NULL, '+91 9800000002', 'TCS Ltd', 'Technical Lead'),

('Suresh Babu',
 'recruit@tcs.com',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'company_recruitment_mgr',
 NULL, NULL, NULL, NULL, NULL, 0, NULL, '+91 9800000003', 'TCS Ltd', 'Recruitment Manager'),

-- ── Infosys Company ───────────────────────────────────────
('Ananya Iyer',
 'hr@infosys.com',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'company_hr_manager',
 NULL, NULL, NULL, NULL, NULL, 0, NULL, '+91 9800000004', 'Infosys Ltd', 'HR Manager'),

('Vikram Patel',
 'tech@infosys.com',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'company_tech_interviewer',
 NULL, NULL, NULL, NULL, NULL, 0, NULL, '+91 9800000005', 'Infosys Ltd', 'Senior Engineer'),

-- ── Wipro Company ─────────────────────────────────────────
('Sneha Pillai',
 'hr@wipro.com',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'company_hr_manager',
 NULL, NULL, NULL, NULL, NULL, 0, NULL, '+91 9800000006', 'Wipro Technologies', 'HR Lead'),

('Karthik Nair',
 'team@wipro.com',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'company_team_leader',
 NULL, NULL, NULL, NULL, NULL, 0, NULL, '+91 9800000007', 'Wipro Technologies', 'Team Lead'),

-- ── Students ──────────────────────────────────────────────
('Arun Kumar S',
 'arun@student.edu',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'student',
 'CS', 2025, 8.70, 88.50, 82.00, 0, '21CS001', '+91 9876500001', NULL, NULL),

('Sathish Kumar T',
 'sathish@student.edu',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'student',
 'IT', 2025, 9.10, 95.00, 91.00, 0, '21IT005', '+91 9876500002', NULL, NULL),

('Anitha Selvam',
 'anitha@student.edu',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'student',
 'CS', 2025, 8.90, 92.00, 88.00, 0, '21CS008', '+91 9876500003', NULL, NULL),

('Vijay Shankar',
 'vijay@student.edu',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'student',
 'CS', 2025, 8.40, 85.00, 80.00, 0, '21CS011', '+91 9876500004', NULL, NULL),

('Priya Devi M',
 'priya@student.edu',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'student',
 'IT', 2025, 7.90, 76.00, 79.50, 0, '21IT002', '+91 9876500005', NULL, NULL),

('Mohammed Farhan',
 'farhan@student.edu',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'student',
 'ECE', 2025, 8.20, 90.00, 85.00, 0, '21EC003', '+91 9876500006', NULL, NULL),

('Divya Bharathi K',
 'divya@student.edu',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'student',
 'EEE', 2025, 7.40, 72.00, 74.00, 0, '21EE006', '+91 9876500007', NULL, NULL),

('Lakshmi Narayanan',
 'lakshmi@student.edu',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'student',
 'CS', 2025, 6.50, 65.00, 68.00, 1, '21CS004', '+91 9876500008', NULL, NULL),

('Meena Kumari P',
 'meena@student.edu',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'student',
 'ECE', 2025, 5.80, 60.00, 62.00, 2, '21EC010', '+91 9876500009', NULL, NULL),

('Ragul Murugan',
 'ragul@student.edu',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'student',
 'MECH', 2025, 6.80, 70.00, 71.50, 0, '21ME007', '+91 9876500010', NULL, NULL),

('Bala Krishnan R',
 'bala@student.edu',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'student',
 'IT', 2026, 7.20, 68.00, 72.00, 0, '22IT009', '+91 9876500011', NULL, NULL),

('Deepika Ramesh',
 'deepika@student.edu',
 '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
 'student',
 'MBA', 2025, 7.60, 74.00, 76.00, 0, '21MB012', '+91 9876500012', NULL, NULL);


-- ================================================================
-- QUESTIONS — MCQ
-- ================================================================
INSERT INTO questions
    (question_text, question_type, subject, difficulty, marks,
     option_a, option_b, option_c, option_d, correct_answer)
VALUES
-- Aptitude
('A train travels 360 km in 4 hours. What is its speed in m/s?',
 'mcq','Aptitude','easy',1, '25 m/s','90 m/s','100 m/s','72 m/s','A'),
('If 5 workers complete a task in 12 days, how many days will 15 workers take?',
 'mcq','Aptitude','easy',1, '4 days','6 days','3 days','36 days','A'),
('What is 15% of 200?',
 'mcq','Aptitude','easy',1, '25','30','35','40','B'),
('Average of 5 numbers is 25. One excluded, average becomes 20. Excluded number?',
 'mcq','Aptitude','medium',2, '40','45','50','55','B'),
('A shopkeeper gives 20% discount and still earns 25% profit. Ratio of MP to CP?',
 'mcq','Aptitude','hard',3, '25:16','15:8','5:3','4:3','A'),
-- Reasoning
('What is the next number in the series: 2, 6, 12, 20, 30, ?',
 'mcq','Reasoning','medium',2, '40','42','44','36','B'),
('If MANGO is coded as NBOPP, how is APPLE coded?',
 'mcq','Reasoning','medium',2, 'BQQMF','BPQMF','CQQMF','BQQLF','A'),
-- Verbal
('Choose the word most similar in meaning to ELOQUENT:',
 'mcq','Verbal','medium',1, 'Silent','Articulate','Clumsy','Boring','B'),
('Antonym of TRANSPARENT:',
 'mcq','Verbal','easy',1, 'Clear','Obvious','Opaque','Visible','C'),
-- Data Structures / Algorithms
('Which data structure uses LIFO (Last In, First Out) order?',
 'mcq','Data Structures','easy',1, 'Queue','Stack','Array','Linked List','B'),
('Time complexity of Binary Search?',
 'mcq','Algorithms','easy',1, 'O(n)','O(n²)','O(log n)','O(n log n)','C'),
('Sorting algorithm with best average-case time complexity?',
 'mcq','Algorithms','medium',2, 'Bubble Sort','Selection Sort','Merge Sort','Insertion Sort','C'),
-- Python
('In Python, what is the output of: print(type(3/2))?',
 'mcq','Python','easy',1, "<class 'int'>","<class 'float'>","<class 'complex'>",'Error','B'),
('Keyword to define a function in Python?',
 'mcq','Python','easy',1, 'function','func','define','def','D'),
('What does len("Hello") return?',
 'mcq','Python','easy',1, '4','5','6','Error','B'),
('Exception handling in Python uses?',
 'mcq','Python','easy',1, 'try...catch','try...except','try...handle','try...error','B'),
('Output of: print(2 ** 10)?',
 'mcq','Python','medium',1, '20','100','512','1024','D'),
-- Database
('Which is NOT a valid SQL JOIN type?',
 'mcq','Database','medium',2, 'INNER JOIN','OUTER JOIN','DIAGONAL JOIN','CROSS JOIN','C'),
('SQL command to retrieve data?',
 'mcq','Database','easy',1, 'INSERT','UPDATE','SELECT','DELETE','C'),
('What does a PRIMARY KEY ensure?',
 'mcq','Database','medium',2, 'No duplicates and no NULLs','Only no NULLs','Only no duplicates','Unique across tables','A'),
-- Web / Technical
('Which HTTP method is idempotent and retrieves data?',
 'mcq','Web','medium',2, 'POST','DELETE','GET','PATCH','C'),
('What does OOP stand for?',
 'mcq','Technical','easy',1, 'Object Oriented Programming','Open Object Protocol','Object Order Process','None','A'),
('What does CPU stand for?',
 'mcq','Technical','easy',1, 'Central Processing Unit','Central Program Unit','Computer Processing Unit','Central Processor Utility','A'),
('Which is NOT an OOP language?',
 'mcq','Technical','easy',1, 'Java','Python','C','C++','C');


-- ================================================================
-- QUESTIONS — Coding
-- ================================================================
INSERT INTO questions
    (question_text, question_type, subject, difficulty, marks,
     starter_code, expected_output, test_cases)
VALUES
(
 'Write a Python function to find the factorial of n. Print the result.',
 'coding','Python','easy',5,
 'def factorial(n):\n    # Write your code here\n    pass\n\nn = int(input())\nprint(factorial(n))',
 '120',
 JSON_ARRAY(
     JSON_OBJECT('input','5',  'output','120',     'is_hidden',false),
     JSON_OBJECT('input','0',  'output','1',       'is_hidden',false),
     JSON_OBJECT('input','10', 'output','3628800', 'is_hidden',true)
 )
),
(
 'Given a list of integers, print the sum of all even numbers.',
 'coding','Python','easy',5,
 'n = int(input())\nnums = list(map(int, input().split()))\n# Write your code here',
 '6',
 JSON_ARRAY(
     JSON_OBJECT('input','5\n1 2 3 4 5',   'output','6',  'is_hidden',false),
     JSON_OBJECT('input','4\n2 4 6 8',     'output','20', 'is_hidden',false),
     JSON_OBJECT('input','6\n1 3 5 7 9 11','output','0',  'is_hidden',true)
 )
),
(
 'Check if a given string is a palindrome. Print YES or NO.',
 'coding','Strings','medium',8,
 's = input().strip()\n# Write your code here',
 'YES',
 JSON_ARRAY(
     JSON_OBJECT('input','racecar','output','YES','is_hidden',false),
     JSON_OBJECT('input','hello',  'output','NO', 'is_hidden',false),
     JSON_OBJECT('input','madam',  'output','YES','is_hidden',true),
     JSON_OBJECT('input','python', 'output','NO', 'is_hidden',true)
 )
),
(
 'Find the second largest element in an array of n integers.',
 'coding','Arrays','medium',8,
 'n = int(input())\narr = list(map(int, input().split()))\n# Write your code here',
 '4',
 JSON_ARRAY(
     JSON_OBJECT('input','5\n3 1 4 1 5', 'output','4',  'is_hidden',false),
     JSON_OBJECT('input','4\n10 20 5 30','output','20', 'is_hidden',false),
     JSON_OBJECT('input','3\n100 90 80', 'output','90', 'is_hidden',true)
 )
),
(
 'Write a function that returns True if a number is prime, False otherwise.',
 'coding','Python','medium',5,
 'def is_prime(n):\n    # Write your code here\n    pass\n\nprint(is_prime(int(input())))',
 'True',
 JSON_ARRAY(
     JSON_OBJECT('input','7', 'output','True', 'is_hidden',false),
     JSON_OBJECT('input','10','output','False','is_hidden',false),
     JSON_OBJECT('input','2', 'output','True', 'is_hidden',true)
 )
),
(
 'Reverse a string without using built-in reverse functions.',
 'coding','Strings','easy',3,
 'def reverse_string(s):\n    # Write your code here\n    pass\n\nprint(reverse_string(input()))',
 'olleh',
 JSON_ARRAY(
     JSON_OBJECT('input','hello', 'output','olleh', 'is_hidden',false),
     JSON_OBJECT('input','Python','output','nohtyP','is_hidden',false)
 )
);


-- ================================================================
-- EXAMS
-- ================================================================
INSERT INTO exams
    (title, description, duration_minutes, total_marks, passing_marks,
     status, exam_type, target_departments, created_by_id)
VALUES
-- Online exams (visible to students)
('General Aptitude Test – Batch 2025',
 'Covers numerical, verbal and reasoning ability for all departments.',
 60, 0, 15, 'active', 'online',
 'CS,IT,ECE,EEE,MECH,CIVIL', 3),

('Coding Assessment – Python Online',
 'Python coding round for placement preparation.',
 90, 0, 10, 'active', 'online',
 'CS,IT', 3),

('Mock Placement Test – Practice',
 'Full-length mock test with MCQ and coding sections.',
 120, 0, 25, 'scheduled', 'online',
 'CS,IT,ECE,EEE', 3),

-- Campus exams (drive round only — not shown in student exam list)
('TCS Aptitude Round 1',
 'Aptitude test for TCS campus drive.',
 45, 0, 12, 'active', 'campus',
 'CS,IT,ECE', 3),

('Infosys Technical Round',
 'Technical assessment for Infosys campus drive.',
 60, 0, 20, 'draft', 'campus',
 'CS,IT,ECE', 3);


-- Attach questions to Exam 1 (General Aptitude — first 15 MCQs)
INSERT INTO exam_questions (exam_id, question_id, order_number)
SELECT 1, id, ROW_NUMBER() OVER (ORDER BY id) - 1
FROM questions WHERE question_type = 'mcq' LIMIT 15;

-- Attach questions to Exam 2 (Coding — 3 coding questions)
INSERT INTO exam_questions (exam_id, question_id, order_number)
SELECT 2, id, ROW_NUMBER() OVER (ORDER BY id) - 1
FROM questions WHERE question_type = 'coding' LIMIT 3;

-- Attach questions to Exam 3 (Mock — 8 MCQ + 2 coding)
INSERT INTO exam_questions (exam_id, question_id, order_number)
SELECT 3, id, ROW_NUMBER() OVER (ORDER BY id) - 1
FROM questions WHERE question_type = 'mcq' LIMIT 8;

INSERT INTO exam_questions (exam_id, question_id, order_number)
SELECT 3, id, ROW_NUMBER() OVER (ORDER BY id) + 7
FROM questions WHERE question_type = 'coding' LIMIT 2;

-- Attach questions to Exam 4 (TCS Aptitude Campus — first 10 MCQs)
INSERT INTO exam_questions (exam_id, question_id, order_number)
SELECT 4, id, ROW_NUMBER() OVER (ORDER BY id) - 1
FROM questions WHERE question_type = 'mcq' LIMIT 10;

-- Attach questions to Exam 5 (Infosys Technical — 8 MCQ + 2 coding)
INSERT INTO exam_questions (exam_id, question_id, order_number)
SELECT 5, id, ROW_NUMBER() OVER (ORDER BY id) - 1
FROM questions WHERE question_type = 'mcq'    LIMIT 8;

INSERT INTO exam_questions (exam_id, question_id, order_number)
SELECT 5, id, ROW_NUMBER() OVER (ORDER BY id) + 7
FROM questions WHERE question_type = 'coding' LIMIT 2;

-- Recompute total_marks for all exams
-- (disable safe update mode for this bulk update, re-enable after)
SET SQL_SAFE_UPDATES = 0;

UPDATE exams e
JOIN (
    SELECT eq.exam_id, COALESCE(SUM(q.marks), 0) AS computed_marks
    FROM exam_questions eq
    JOIN questions q ON q.id = eq.question_id
    GROUP BY eq.exam_id
) AS totals ON totals.exam_id = e.id
SET e.total_marks = totals.computed_marks;

SET SQL_SAFE_UPDATES = 1;


-- ================================================================
-- CAMPUS DRIVES
-- ================================================================
INSERT INTO campus_drives
    (company_id, title, job_role, job_description, package_lpa, location,
     eligible_departments, eligible_batches,
     min_cgpa, min_tenth_percent, min_twelfth_percent, max_backlogs,
     requested_date, confirmed_date, venue, status, response_open, officer_notes)
VALUES
-- TCS — approved, response open
(
    (SELECT id FROM users WHERE email = 'hr@tcs.com'),
    'TCS NQT 2025 – Software Developer',
    'Software Developer',
    'TCS is hiring 2025 batch graduates for the National Qualifier Test. Selected candidates join as Software Developer Trainees. 6-month training at TCS campus followed by project allocation across domains.',
    3.50, 'Chennai',
    JSON_ARRAY('CS','IT','ECE'), JSON_ARRAY(2025),
    6.00, 60.00, 60.00, 0,
    DATE_ADD(NOW(), INTERVAL 10 DAY),
    DATE_ADD(NOW(), INTERVAL 10 DAY),
    'Main Auditorium, Block A',
    'approved', 1, 'Dates confirmed with company. 6 students eligible.'
),
-- Infosys — approved, response open
(
    (SELECT id FROM users WHERE email = 'hr@infosys.com'),
    'Infosys Fresher Drive 2025 – Systems Engineer',
    'Systems Engineer',
    'Infosys recruiting fresh graduates for Systems Engineer role. 3-month training program followed by project allocation. Work on diverse projects across financial services, healthcare, and retail verticals.',
    4.00, 'Bangalore',
    JSON_ARRAY('CS','IT','ECE','EEE'), JSON_ARRAY(2025),
    6.50, 65.00, 65.00, 0,
    DATE_ADD(NOW(), INTERVAL 20 DAY),
    DATE_ADD(NOW(), INTERVAL 20 DAY),
    'Conference Hall, Block B',
    'approved', 1, 'Infosys visit approved. All docs received.'
),
-- Wipro — pending approval
(
    (SELECT id FROM users WHERE email = 'hr@wipro.com'),
    'Wipro Elite NLTH 2025 – Project Engineer',
    'Project Engineer',
    'Wipro Elite National Level Talent Hunt for Project Engineer. Higher package for top performers. Work on cutting-edge technology projects globally.',
    6.50, 'Hyderabad',
    JSON_ARRAY('CS','IT'), JSON_ARRAY(2025),
    7.50, 70.00, 70.00, 0,
    DATE_ADD(NOW(), INTERVAL 30 DAY),
    NULL, NULL,
    'pending', 0, NULL
),
-- TCS BPS — completed
(
    (SELECT id FROM users WHERE email = 'hr@tcs.com'),
    'TCS BPS – Business Process Services 2024',
    'Process Associate',
    'Customer support and BPS roles. Previous batch completed drive.',
    2.50, 'Pune',
    JSON_ARRAY('CS','IT','ECE','EEE','MECH','CIVIL','MBA','MCA','BSC'), JSON_ARRAY(2024),
    5.00, 50.00, 50.00, 2,
    DATE_SUB(NOW(), INTERVAL 60 DAY),
    DATE_SUB(NOW(), INTERVAL 60 DAY),
    'Seminar Hall, Block C',
    'completed', 0, 'Drive completed successfully. 18 students selected.'
);


-- ================================================================
-- DRIVE OPT-INS
-- ================================================================

-- TCS Drive (drive_id = 1)
INSERT INTO drive_opt_ins (drive_id, student_id, status) VALUES
(1, (SELECT id FROM users WHERE email = 'arun@student.edu'),    'opted_in'),
(1, (SELECT id FROM users WHERE email = 'sathish@student.edu'), 'opted_in'),
(1, (SELECT id FROM users WHERE email = 'anitha@student.edu'),  'opted_in'),
(1, (SELECT id FROM users WHERE email = 'vijay@student.edu'),   'opted_in'),
(1, (SELECT id FROM users WHERE email = 'priya@student.edu'),   'opted_in'),
(1, (SELECT id FROM users WHERE email = 'farhan@student.edu'),  'opted_in'),
(1, (SELECT id FROM users WHERE email = 'lakshmi@student.edu'), 'opted_out');  -- below threshold

-- Infosys Drive (drive_id = 2)
INSERT INTO drive_opt_ins (drive_id, student_id, status) VALUES
(2, (SELECT id FROM users WHERE email = 'arun@student.edu'),    'opted_in'),
(2, (SELECT id FROM users WHERE email = 'sathish@student.edu'), 'opted_in'),
(2, (SELECT id FROM users WHERE email = 'anitha@student.edu'),  'opted_in'),
(2, (SELECT id FROM users WHERE email = 'farhan@student.edu'),  'opted_in'),
(2, (SELECT id FROM users WHERE email = 'divya@student.edu'),   'opted_in'),
(2, (SELECT id FROM users WHERE email = 'vijay@student.edu'),   'opted_in');


-- ================================================================
-- DRIVE ROUNDS
-- ================================================================

-- TCS: 3 rounds
INSERT INTO drive_rounds
    (drive_id, round_number, round_type, description, status, passing_score, exam_id)
VALUES
(1, 1, 'aptitude',
 'Written aptitude test – 45 minutes. Tests numerical, verbal and reasoning.',
 'completed', 30, 4),   -- linked to Exam 4 (TCS Aptitude Campus)

(1, 2, 'coding',
 'Coding round – Python or Java. 3 problems in 60 minutes.',
 'pending', 10, NULL),

(1, 3, 'hr',
 'HR Interview – face to face with HR panel. Evaluates communication and attitude.',
 'pending', 0, NULL);

-- Update Exam 4 to link to TCS Round 1
UPDATE exams SET drive_round_id = (
    SELECT id FROM drive_rounds WHERE drive_id = 1 AND round_number = 1
) WHERE id = 4;  -- WHERE on PRIMARY KEY — safe update compatible

-- Infosys: 4 rounds
INSERT INTO drive_rounds
    (drive_id, round_number, round_type, description, status, passing_score)
VALUES
(2, 1, 'aptitude',         'Online aptitude screening – 60 minutes.',        'pending', 25),
(2, 2, 'technical',        'Technical interview with engineering team.',      'pending', 0),
(2, 3, 'group_discussion', 'Group discussion – 10 students per group.',      'pending', 0),
(2, 4, 'hr',               'Final HR round – compensation and joining date.', 'pending', 0);


-- ================================================================
-- DRIVE ROUND RESULTS (TCS Round 1 — completed)
-- ================================================================
INSERT INTO drive_round_results (round_id, student_id, passed, score, notes) VALUES
(
    (SELECT id FROM drive_rounds WHERE drive_id = 1 AND round_number = 1),
    (SELECT id FROM users WHERE email = 'arun@student.edu'),    1, 38, 'Excellent performance'
),
(
    (SELECT id FROM drive_rounds WHERE drive_id = 1 AND round_number = 1),
    (SELECT id FROM users WHERE email = 'sathish@student.edu'), 1, 42, 'Top scorer'
),
(
    (SELECT id FROM drive_rounds WHERE drive_id = 1 AND round_number = 1),
    (SELECT id FROM users WHERE email = 'anitha@student.edu'),  1, 35, 'Good'
),
(
    (SELECT id FROM drive_rounds WHERE drive_id = 1 AND round_number = 1),
    (SELECT id FROM users WHERE email = 'vijay@student.edu'),   1, 31, 'Passed'
),
(
    (SELECT id FROM drive_rounds WHERE drive_id = 1 AND round_number = 1),
    (SELECT id FROM users WHERE email = 'priya@student.edu'),   0, 25, 'Did not reach passing score'
),
(
    (SELECT id FROM drive_rounds WHERE drive_id = 1 AND round_number = 1),
    (SELECT id FROM users WHERE email = 'farhan@student.edu'),  1, 33, 'Passed'
);


-- ================================================================
-- EXAM SUBMISSIONS (General Aptitude — Exam 1)
-- ================================================================
INSERT INTO exam_submissions
    (exam_id, student_id, answers, score, total_marks, passed,
     tab_switch_count, blur_count, copy_paste_count, malpractice_flag, malpractice_notes)
VALUES
(1, (SELECT id FROM users WHERE email='arun@student.edu'),    '{}', 18, 17, 1, 0, 1,  0, 0, NULL),
(1, (SELECT id FROM users WHERE email='sathish@student.edu'), '{}', 20, 17, 1, 0, 0,  0, 0, NULL),
(1, (SELECT id FROM users WHERE email='anitha@student.edu'),  '{}', 17, 17, 1, 1, 2,  0, 0, NULL),
(1, (SELECT id FROM users WHERE email='vijay@student.edu'),   '{}', 16, 17, 1, 0, 0,  0, 0, NULL),
(1, (SELECT id FROM users WHERE email='priya@student.edu'),   '{}', 13, 17, 0, 0, 1,  0, 0, NULL),
(1, (SELECT id FROM users WHERE email='farhan@student.edu'),  '{}', 15, 17, 1, 0, 0,  0, 0, NULL),
-- Malpractice flagged
(1, (SELECT id FROM users WHERE email='divya@student.edu'),   '{}', 11, 17, 0, 4, 12, 1, 1, 'Tab switches: 4, Window blur: 12'),
(1, (SELECT id FROM users WHERE email='lakshmi@student.edu'), '{}', 10, 17, 0, 3, 5,  6, 1, 'Tab switches: 3, Copy/paste: 6');


-- ================================================================
-- RESULTS (linked to submissions, NOT released yet)
-- ================================================================
INSERT INTO results
    (exam_id, student_id, submission_id,
     total_marks, obtained_marks, percentage, is_passed, `rank`,
     is_approved, is_released)
VALUES
(1,(SELECT id FROM users WHERE email='sathish@student.edu'),(SELECT id FROM exam_submissions WHERE student_id=(SELECT id FROM users WHERE email='sathish@student.edu') AND exam_id=1), 17,20.00,117.65,1,1, 0,0),
(1,(SELECT id FROM users WHERE email='anitha@student.edu'), (SELECT id FROM exam_submissions WHERE student_id=(SELECT id FROM users WHERE email='anitha@student.edu')  AND exam_id=1), 17,17.00,100.00,1,2, 0,0),
(1,(SELECT id FROM users WHERE email='arun@student.edu'),   (SELECT id FROM exam_submissions WHERE student_id=(SELECT id FROM users WHERE email='arun@student.edu')    AND exam_id=1), 17,18.00,105.88,1,3, 0,0),
(1,(SELECT id FROM users WHERE email='vijay@student.edu'),  (SELECT id FROM exam_submissions WHERE student_id=(SELECT id FROM users WHERE email='vijay@student.edu')   AND exam_id=1), 17,16.00,94.12, 1,4, 0,0),
(1,(SELECT id FROM users WHERE email='farhan@student.edu'), (SELECT id FROM exam_submissions WHERE student_id=(SELECT id FROM users WHERE email='farhan@student.edu')  AND exam_id=1), 17,15.00,88.24, 1,5, 0,0),
(1,(SELECT id FROM users WHERE email='priya@student.edu'),  (SELECT id FROM exam_submissions WHERE student_id=(SELECT id FROM users WHERE email='priya@student.edu')   AND exam_id=1), 17,13.00,76.47, 0,6, 0,0),
(1,(SELECT id FROM users WHERE email='divya@student.edu'),  (SELECT id FROM exam_submissions WHERE student_id=(SELECT id FROM users WHERE email='divya@student.edu')   AND exam_id=1), 17,11.00,64.71, 0,7, 0,0),
(1,(SELECT id FROM users WHERE email='lakshmi@student.edu'),(SELECT id FROM exam_submissions WHERE student_id=(SELECT id FROM users WHERE email='lakshmi@student.edu') AND exam_id=1), 17,10.00,58.82, 0,8, 0,0);


-- ================================================================
-- EXAM ATTENDANCE
-- ================================================================
INSERT INTO exam_attendance (exam_id, student_id, status, otp_verified, ip_address, seat_number, room_name) VALUES
(1,(SELECT id FROM users WHERE email='arun@student.edu'),    'present',1,'192.168.1.11','A01','Lab 101'),
(1,(SELECT id FROM users WHERE email='sathish@student.edu'), 'present',1,'192.168.1.12','A02','Lab 101'),
(1,(SELECT id FROM users WHERE email='anitha@student.edu'),  'present',1,'192.168.1.13','A03','Lab 101'),
(1,(SELECT id FROM users WHERE email='vijay@student.edu'),   'present',1,'192.168.1.14','A04','Lab 101'),
(1,(SELECT id FROM users WHERE email='priya@student.edu'),   'present',1,'192.168.1.15','A05','Lab 101'),
(1,(SELECT id FROM users WHERE email='farhan@student.edu'),  'present',1,'192.168.1.16','A06','Lab 101'),
(1,(SELECT id FROM users WHERE email='divya@student.edu'),   'present',1,'192.168.1.17','A07','Lab 101'),
(1,(SELECT id FROM users WHERE email='lakshmi@student.edu'), 'present',1,'192.168.1.18','A08','Lab 101'),
(1,(SELECT id FROM users WHERE email='ragul@student.edu'),   'absent', 0, NULL,         NULL, NULL),
(1,(SELECT id FROM users WHERE email='meena@student.edu'),   'absent', 0, NULL,         NULL, NULL);


-- ================================================================
-- MALPRACTICE RECORDS (for flagged submissions)
-- ================================================================
INSERT INTO malpractice
    (exam_id, student_id, violations, violation_log, action, action_note, action_by_id, action_at)
VALUES
(
    1,
    (SELECT id FROM users WHERE email = 'divya@student.edu'),
    5,
    JSON_ARRAY(
        JSON_OBJECT('event','tab_switch', 'count',4, 'time','00:15:23'),
        JSON_OBJECT('event','window_blur','count',12,'time','00:22:47')
    ),
    'warning',
    'First offense warning issued. Score retained but flagged for review.',
    (SELECT id FROM users WHERE email = 'staff1@college.edu'),
    NOW()
),
(
    1,
    (SELECT id FROM users WHERE email = 'lakshmi@student.edu'),
    4,
    JSON_ARRAY(
        JSON_OBJECT('event','tab_switch',  'count',3,'time','00:08:11'),
        JSON_OBJECT('event','copy_paste',  'count',6,'time','00:31:05')
    ),
    'penalised',
    'Score reduced by 30% due to copy-paste violations during coding section.',
    (SELECT id FROM users WHERE email = 'staff1@college.edu'),
    NOW()
);


-- ================================================================
-- NOTIFICATIONS
-- ================================================================
INSERT INTO notifications (sender_id, notif_type, target_role, drive_id, title, message)
VALUES
(
    (SELECT id FROM users WHERE email = 'hr@tcs.com'),
    'company_to_students', 'student', 1,
    'TCS Drive Tomorrow – Reporting Instructions',
    'Dear Students, TCS campus drive is scheduled for tomorrow. Please report to Main Auditorium by 8:30 AM with your college ID, 2 passport photos, and all academic mark sheets. Formal dress is mandatory. All opted-in students must confirm attendance by 6 PM today.'
),
(
    (SELECT id FROM users WHERE email = 'hr@infosys.com'),
    'company_to_students', 'student', 2,
    'Infosys Drive – Documents Required',
    'Infosys Systems Engineer drive is coming up. Please carry: 1) Updated resume (2 copies) 2) All semester marksheets 3) Aadhar card copy 4) Passport size photo. Aptitude round starts at 10:00 AM sharp. No late entries permitted.'
),
(
    (SELECT id FROM users WHERE email = 'admin@college.edu'),
    'head_to_staff', 'placement_officer', NULL,
    'Campus Drive Season – Staff Briefing',
    'All placement staff: We have 3 companies visiting this month. Please ensure all classrooms are booked and AV equipment is tested. Coordinate with department HoDs for eligible student lists by Friday EOD. Report any issues immediately.'
),
(
    (SELECT id FROM users WHERE email = 'hr@tcs.com'),
    'company_to_placement', 'placement_officer', 1,
    'TCS – Updated Eligibility Criteria',
    'Please note: TCS has updated eligibility to include students with one active backlog for BPS roles only. Kindly update student lists accordingly and re-notify eligible students. Contact: ravi.sharma@tcs.com for queries.'
),
(
    (SELECT id FROM users WHERE email = 'admin@college.edu'),
    'system', NULL, NULL,
    'Portal Maintenance – Sunday 2 AM to 4 AM',
    'The placement portal will undergo scheduled maintenance on Sunday from 2:00 AM to 4:00 AM. Please complete all submissions and uploads before this window. System will be fully operational post-maintenance. Contact IT support for urgent issues.'
),
(
    (SELECT id FROM users WHERE email = 'officer@college.edu'),
    'head_to_staff', 'staff', 1,
    'Pre-Drive Checklist – TCS Tomorrow',
    'Staff team: Please complete the pre-drive checklist before 7:30 AM tomorrow: 1) Verify opted-in student count (currently 6) 2) Print attendance sheets 3) Coordinate with TCS coordinator Ravi Sharma (+91 9800000001) 4) Set up Round 1 exam hall with 30 systems 5) Keep refreshments ready.'
);


-- ================================================================
-- VERIFICATION — Run these SELECT queries to confirm data
-- ================================================================
SELECT '=== TABLES CREATED ===' AS section;
SHOW TABLES;

SELECT '=== ROW COUNTS ===' AS section;
SELECT 'users'               AS tbl, COUNT(*) AS rows FROM users            UNION ALL
SELECT 'questions',                   COUNT(*)        FROM questions         UNION ALL
SELECT 'exams',                       COUNT(*)        FROM exams             UNION ALL
SELECT 'exam_questions',              COUNT(*)        FROM exam_questions    UNION ALL
SELECT 'exam_submissions',            COUNT(*)        FROM exam_submissions  UNION ALL
SELECT 'results',                     COUNT(*)        FROM results           UNION ALL
SELECT 'exam_attendance',             COUNT(*)        FROM exam_attendance   UNION ALL
SELECT 'malpractice',                 COUNT(*)        FROM malpractice       UNION ALL
SELECT 'campus_drives',               COUNT(*)        FROM campus_drives     UNION ALL
SELECT 'drive_opt_ins',               COUNT(*)        FROM drive_opt_ins     UNION ALL
SELECT 'drive_rounds',                COUNT(*)        FROM drive_rounds      UNION ALL
SELECT 'drive_round_results',         COUNT(*)        FROM drive_round_results UNION ALL
SELECT 'notifications',               COUNT(*)        FROM notifications     UNION ALL
SELECT 'notification_reads',          COUNT(*)        FROM notification_reads;

SELECT '=== USERS BY ROLE ===' AS section;
SELECT role, COUNT(*) AS total FROM users GROUP BY role ORDER BY role;

SELECT '=== EXAMS ===' AS section;
SELECT id, title, status, exam_type, total_marks, passing_marks FROM exams ORDER BY id;

SELECT '=== CAMPUS DRIVES ===' AS section;
SELECT d.id, d.title, d.status,
       IF(d.response_open, 'OPEN', 'CLOSED') AS response,
       COUNT(o.id) AS opted_in
FROM campus_drives d
LEFT JOIN drive_opt_ins o ON o.drive_id = d.id AND o.status = 'opted_in'
GROUP BY d.id, d.title, d.status, d.response_open;

SELECT '=== MALPRACTICE SUMMARY ===' AS section;
SELECT malpractice_flag, COUNT(*) AS submissions
FROM exam_submissions GROUP BY malpractice_flag;

SELECT '=== RESULTS (not yet released) ===' AS section;
SELECT u.name, e.title, r.percentage, r.is_passed,
       IF(r.is_approved,'APPROVED','PENDING')  AS approval,
       IF(r.is_released,'RELEASED','HIDDEN')   AS visibility
FROM results r
JOIN users u ON u.id = r.student_id
JOIN exams e ON e.id = r.exam_id
ORDER BY r.percentage DESC;


-- ================================================================
-- USEFUL REFERENCE COMMANDS (uncomment as needed)
-- ================================================================

-- Release ALL results instantly (bypass approval for testing)
-- SET SQL_SAFE_UPDATES = 0;
-- UPDATE results SET is_approved=1, is_released=1, approved_at=NOW() WHERE id > 0;
-- SET SQL_SAFE_UPDATES = 1;

-- Approve results for exam 1 (officer user)
-- UPDATE results SET is_approved=1,
--     approved_by=(SELECT id FROM users WHERE email='officer@college.edu'), approved_at=NOW()
-- WHERE exam_id=1 AND id > 0;

-- Release approved results for exam 1
-- UPDATE results SET is_released=1
-- WHERE exam_id=1 AND is_approved=1 AND id > 0;

-- Reset for re-testing
-- SET SQL_SAFE_UPDATES = 0;
-- UPDATE results SET is_approved=0, is_released=0, approved_by=NULL, approved_at=NULL WHERE id > 0;
-- SET SQL_SAFE_UPDATES = 1;

-- Check approval pipeline
-- SELECT e.title, COUNT(*) total, SUM(is_approved) approved, SUM(is_released) released
-- FROM results r JOIN exams e ON e.id=r.exam_id GROUP BY r.exam_id, e.title;

-- View drive overview (uses the VIEW created above)
-- SELECT * FROM v_drive_overview;

-- View malpractice report
-- SELECT * FROM v_malpractice_report;

-- View full results with malpractice
-- SELECT * FROM v_exam_results ORDER BY percentage DESC;
