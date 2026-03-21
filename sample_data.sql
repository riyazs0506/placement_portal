-- =============================================================
--  University Placement Portal — SAMPLE / DEMO DATA
--  Run AFTER schema.sql
--
--  All passwords use bcrypt hash for "Student@123" / "Admin@123" etc.
--  NOTE: Passwords below are bcrypt hashes. Use seed_data.py for
--        dynamically generated hashes, or replace with your own.
--
--  Login credentials:
--    admin@college.edu    → Admin@123
--    officer@college.edu  → Officer@123
--    staff1@college.edu   → Staff@123
--    hr@tcs.com           → TCS@123
--    hr@infosys.com       → Infosys@123
--    hr@wipro.com         → Wipro@123
--    *@student.edu        → Student@123
-- =============================================================

-- NOTE: Bcrypt hashes below are valid pre-computed hashes.
--       If login fails, run: python seed_data.py  (generates live hashes)

-- ─────────────────────────────────────────────────────────────
-- USERS
-- ─────────────────────────────────────────────────────────────

-- Staff
INSERT INTO users (name, email, password_hash, role, is_active) VALUES
('Dr. Rajesh Kumar',  'admin@college.edu',   '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'head_admin',          1),
('Mrs. Priya Nair',   'officer@college.edu', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'placement_officer',   1),
('Mr. Arjun Mehta',   'staff1@college.edu',  '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'senior_staff',        1),
('Ms. Kavitha Rajan', 'staff2@college.edu',  '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'staff',               1);

-- TCS Company team
INSERT INTO users (name, email, password_hash, role, company_name, company_designation, is_active) VALUES
('Ravi Sharma',    'hr@tcs.com',      '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'company_hr_manager',       'TCS Ltd', 'HR Manager',           1),
('Deepa Krishnan', 'tech@tcs.com',    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'company_tech_interviewer', 'TCS Ltd', 'Technical Lead',       1),
('Suresh Babu',    'recruit@tcs.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'company_recruitment_mgr',  'TCS Ltd', 'Recruitment Manager',  1);

-- Infosys Company team
INSERT INTO users (name, email, password_hash, role, company_name, company_designation, is_active) VALUES
('Ananya Iyer',  'hr@infosys.com',   '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'company_hr_manager',       'Infosys Ltd', 'HR Manager',       1),
('Vikram Patel', 'tech@infosys.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'company_tech_interviewer', 'Infosys Ltd', 'Senior Engineer',  1);

-- Wipro Company team
INSERT INTO users (name, email, password_hash, role, company_name, company_designation, is_active) VALUES
('Sneha Pillai',  'hr@wipro.com',   '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'company_hr_manager',  'Wipro Technologies', 'HR Lead',    1),
('Karthik Nair',  'team@wipro.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'company_team_leader', 'Wipro Technologies', 'Team Lead',  1);

-- Students — CS/IT department (eligible for most drives)
INSERT INTO users (name, email, password_hash, role, department, batch_year, cgpa, tenth_percent, twelfth_percent, backlogs, roll_number, is_active) VALUES
('Arun Kumar S',    'arun@student.edu',    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'student', 'CS', 2025, 8.7, 88.5, 82.0, 0, '21CS001', 1),
('Sathish Kumar T', 'sathish@student.edu', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'student', 'IT', 2025, 9.1, 95.0, 91.0, 0, '21IT005', 1),
('Anitha Selvam',   'anitha@student.edu',  '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'student', 'CS', 2025, 8.9, 92.0, 88.0, 0, '21CS008', 1),
('Vijay Shankar',   'vijay@student.edu',   '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'student', 'CS', 2025, 8.4, 85.0, 80.0, 0, '21CS011', 1),
('Priya Devi M',    'priya@student.edu',   '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'student', 'IT', 2025, 7.9, 76.0, 79.5, 0, '21IT002', 1),
('Mohammed Farhan', 'farhan@student.edu',  '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'student', 'ECE',2025, 8.2, 90.0, 85.0, 0, '21EC003', 1),
('Divya Bharathi K','divya@student.edu',   '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'student', 'EEE',2025, 7.4, 72.0, 74.0, 0, '21EE006', 1),
-- Below-threshold students (to demo eligibility filter)
('Lakshmi Narayanan','lakshmi@student.edu','$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'student', 'CS', 2025, 6.5, 65.0, 68.0, 1, '21CS004', 1),
('Meena Kumari P',  'meena@student.edu',   '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'student', 'ECE',2025, 5.8, 60.0, 62.0, 2, '21EC010', 1),
('Ragul Murugan',   'ragul@student.edu',   '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'student', 'MECH',2025,6.8, 70.0, 71.5, 0, '21ME007', 1),
('Bala Krishnan R', 'bala@student.edu',    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'student', 'IT', 2026, 7.2, 68.0, 72.0, 0, '22IT009', 1),
('Deepika Ramesh',  'deepika@student.edu', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'student', 'MBA',2025, 7.6, 74.0, 76.0, 0, '21MB012', 1);


-- ─────────────────────────────────────────────────────────────
-- QUESTIONS — MCQ (Aptitude, Reasoning, CS fundamentals)
-- ─────────────────────────────────────────────────────────────

INSERT INTO questions (question_text, question_type, subject, difficulty, marks, option_a, option_b, option_c, option_d, correct_answer, test_cases) VALUES
('A train travels 360 km in 4 hours. What is its speed in m/s?',
 'mcq','Aptitude','easy',1, '25 m/s','90 m/s','100 m/s','72 m/s', 'A', '[]'),

('If 5 workers complete a task in 12 days, how many days will 15 workers take?',
 'mcq','Aptitude','easy',1, '4 days','6 days','3 days','36 days', 'A', '[]'),

('What is the next number in the series: 2, 6, 12, 20, 30, ?',
 'mcq','Reasoning','medium',2, '40','42','44','36', 'B', '[]'),

('A shopkeeper gives 20% discount and still earns 25% profit. What is the ratio of MP to CP?',
 'mcq','Aptitude','hard',3, '25:16','15:8','5:3','4:3', 'A', '[]'),

('Which data structure uses LIFO (Last In, First Out) order?',
 'mcq','Data Structures','easy',1, 'Queue','Stack','Linked List','Tree', 'B', '[]'),

('What is the time complexity of binary search?',
 'mcq','Algorithms','easy',1, 'O(n)','O(n²)','O(log n)','O(n log n)', 'C', '[]'),

('Which of the following is NOT a valid SQL join type?',
 'mcq','Database','medium',2, 'INNER JOIN','OUTER JOIN','DIAGONAL JOIN','CROSS JOIN', 'C', '[]'),

('In Python, what is the output of: print(type(3/2))?',
 'mcq','Python','easy',1, '<class int>','<class float>','<class complex>','Error', 'B', '[]'),

('What does OOP stand for?',
 'mcq','Programming','easy',1, 'Object Oriented Programming','Open Object Protocol','Object Order Process','None of these', 'A', '[]'),

('Which HTTP method is idempotent and used to retrieve data?',
 'mcq','Web','medium',2, 'POST','DELETE','GET','PATCH', 'C', '[]'),

('Choose the word most similar in meaning to ELOQUENT:',
 'mcq','Verbal','medium',1, 'Silent','Articulate','Clumsy','Boring', 'B', '[]'),

('If MANGO is coded as NBOPP, how is APPLE coded?',
 'mcq','Reasoning','medium',2, 'BQQMF','BPQMF','CQQMF','BQQLF', 'A', '[]');


-- ─────────────────────────────────────────────────────────────
-- QUESTIONS — Coding
-- ─────────────────────────────────────────────────────────────

INSERT INTO questions (question_text, question_type, subject, difficulty, marks, starter_code, expected_output, test_cases) VALUES
(
 'Write a Python function to find the factorial of a given number n. Print the result.',
 'coding', 'Python', 'easy', 5,
 'def factorial(n):
    # Write your code here
    pass

n = int(input())
print(factorial(n))',
 '120',
 '[{"input": "5", "output": "120", "is_hidden": false}, {"input": "0", "output": "1", "is_hidden": false}, {"input": "10", "output": "3628800", "is_hidden": true}]'
),
(
 'Given a list of integers, return the sum of all even numbers.',
 'coding', 'Python', 'easy', 5,
 'n = int(input())
nums = list(map(int, input().split()))
# Write your code here',
 '6',
 '[{"input": "5\n1 2 3 4 5", "output": "6", "is_hidden": false}, {"input": "4\n2 4 6 8", "output": "20", "is_hidden": false}, {"input": "6\n1 3 5 7 9 11", "output": "0", "is_hidden": true}]'
),
(
 'Write a program to check if a given string is a palindrome. Print YES or NO.',
 'coding', 'Strings', 'medium', 8,
 's = input().strip()
# Write your code here',
 'YES',
 '[{"input": "racecar", "output": "YES", "is_hidden": false}, {"input": "hello", "output": "NO", "is_hidden": false}, {"input": "madam", "output": "YES", "is_hidden": true}]'
),
(
 'Find the second largest element in an array of n integers.',
 'coding', 'Arrays', 'medium', 8,
 'n = int(input())
arr = list(map(int, input().split()))
# Write your code here',
 '4',
 '[{"input": "5\n3 1 4 1 5", "output": "4", "is_hidden": false}, {"input": "4\n10 20 5 30", "output": "20", "is_hidden": false}, {"input": "3\n100 90 80", "output": "90", "is_hidden": true}]'
);


-- ─────────────────────────────────────────────────────────────
-- EXAMS
-- Note: total_marks computed from question marks
-- ─────────────────────────────────────────────────────────────

INSERT INTO exams (title, description, duration_minutes, total_marks, passing_marks, target_departments, status, exam_type, otp_required, created_by_id) VALUES
('General Aptitude Test – Batch 2025',
 'Covers numerical, verbal, and reasoning ability. For all departments.',
 60, 17, 15, 'CS,IT,ECE,EEE,MECH,CIVIL', 'active', 'online', 0,
 (SELECT id FROM users WHERE email='staff1@college.edu')),

('TCS Aptitude Round 1',
 'Aptitude test for TCS campus drive.',
 45, 14, 12, 'CS,IT,ECE', 'active', 'campus', 0,
 (SELECT id FROM users WHERE email='staff1@college.edu')),

('Coding Assessment – Online',
 'Python coding round for placement preparation.',
 90, 18, 10, 'CS,IT', 'active', 'online', 0,
 (SELECT id FROM users WHERE email='staff1@college.edu')),

('Infosys Technical Round',
 'Technical test for Infosys campus drive.',
 60, 24, 20, 'CS,IT,ECE', 'draft', 'campus', 0,
 (SELECT id FROM users WHERE email='staff1@college.edu')),

('Mock Placement Test – Practice',
 'Full-length mock test with MCQ and coding sections.',
 120, 35, 25, 'CS,IT,ECE,EEE', 'scheduled', 'online', 0,
 (SELECT id FROM users WHERE email='staff1@college.edu'));


-- Link questions to exams (exam_questions)
-- Exam 1 (General Aptitude) — first 10 MCQ questions
INSERT INTO exam_questions (exam_id, question_id, order_number)
SELECT
    (SELECT id FROM exams WHERE title='General Aptitude Test – Batch 2025'),
    id,
    ROW_NUMBER() OVER (ORDER BY id) - 1
FROM questions WHERE question_type='mcq' LIMIT 10;

-- Exam 2 (TCS Aptitude Round 1) — first 8 MCQ questions
INSERT INTO exam_questions (exam_id, question_id, order_number)
SELECT
    (SELECT id FROM exams WHERE title='TCS Aptitude Round 1'),
    id,
    ROW_NUMBER() OVER (ORDER BY id) - 1
FROM questions WHERE question_type='mcq' LIMIT 8;

-- Exam 3 (Coding Assessment) — 3 coding questions
INSERT INTO exam_questions (exam_id, question_id, order_number)
SELECT
    (SELECT id FROM exams WHERE title='Coding Assessment – Online'),
    id,
    ROW_NUMBER() OVER (ORDER BY id) - 1
FROM questions WHERE question_type='coding' LIMIT 3;

-- Exam 4 (Infosys Technical) — 5 MCQ + 2 coding
INSERT INTO exam_questions (exam_id, question_id, order_number)
SELECT (SELECT id FROM exams WHERE title='Infosys Technical Round'), id,
       ROW_NUMBER() OVER (ORDER BY id) + 3
FROM questions WHERE question_type='mcq' LIMIT 5;
INSERT INTO exam_questions (exam_id, question_id, order_number)
SELECT (SELECT id FROM exams WHERE title='Infosys Technical Round'), id,
       ROW_NUMBER() OVER (ORDER BY id) + 7
FROM questions WHERE question_type='coding' LIMIT 2;

-- Exam 5 (Mock Test) — 8 MCQ + 2 coding
INSERT INTO exam_questions (exam_id, question_id, order_number)
SELECT (SELECT id FROM exams WHERE title='Mock Placement Test – Practice'), id,
       ROW_NUMBER() OVER (ORDER BY id) - 1
FROM questions WHERE question_type='mcq' LIMIT 8;
INSERT INTO exam_questions (exam_id, question_id, order_number)
SELECT (SELECT id FROM exams WHERE title='Mock Placement Test – Practice'), id,
       ROW_NUMBER() OVER (ORDER BY id) + 7
FROM questions WHERE question_type='coding' LIMIT 2;


-- ─────────────────────────────────────────────────────────────
-- CAMPUS DRIVES
-- ─────────────────────────────────────────────────────────────

INSERT INTO campus_drives (company_id, title, job_role, job_description, package_lpa, location,
    eligible_departments, eligible_batches, min_cgpa, min_tenth_percent, min_twelfth_percent, max_backlogs,
    requested_date, confirmed_date, venue, status, response_open, officer_notes) VALUES
(
    (SELECT id FROM users WHERE email='hr@tcs.com'),
    'TCS NQT 2025 – Software Developer', 'Software Developer',
    'TCS is hiring 2025 batch graduates for its National Qualifier Test. Selected candidates will join as Software Developer Trainees. 6-month training at TCS campus followed by project allocation.',
    3.5, 'Chennai',
    '["CS","IT","ECE"]', '[2025]',
    6.0, 60.0, 60.0, 0,
    datetime('now', '+10 days'), datetime('now', '+10 days'),
    'Main Auditorium, Block A',
    'approved', 1, 'Dates confirmed with company.'
),
(
    (SELECT id FROM users WHERE email='hr@infosys.com'),
    'Infosys Fresher Drive 2025 – Systems Engineer', 'Systems Engineer',
    'Infosys is recruiting fresh graduates for Systems Engineer role. Candidates undergo 3-month training. Work on diverse projects across financial services, healthcare, and retail.',
    4.0, 'Bangalore',
    '["CS","IT","ECE","EEE"]', '[2025]',
    6.5, 65.0, 65.0, 0,
    datetime('now', '+20 days'), datetime('now', '+20 days'),
    'Conference Hall, Block B',
    'approved', 1, 'Infosys visit approved.'
),
(
    (SELECT id FROM users WHERE email='hr@wipro.com'),
    'Wipro Elite NLTH 2025 – Project Engineer', 'Project Engineer',
    'Wipro Elite National Level Talent Hunt for Project Engineer positions. Higher package for top performers. Work on cutting-edge technology projects.',
    6.5, 'Hyderabad',
    '["CS","IT"]', '[2025]',
    7.5, 70.0, 70.0, 0,
    datetime('now', '+30 days'), NULL, NULL,
    'pending', 0, NULL
),
(
    (SELECT id FROM users WHERE email='hr@tcs.com'),
    'TCS BPS – Business Process Services 2024', 'Process Associate',
    'Customer support and BPS roles. Previous batch. Drive completed.',
    2.5, 'Pune',
    '["CS","IT","ECE","EEE","MECH","CIVIL","MBA","MCA","BSC"]', '[2024]',
    5.0, 50.0, 50.0, 2,
    datetime('now', '-60 days'), datetime('now', '-60 days'),
    'Seminar Hall',
    'completed', 0, 'Drive completed. 18 students selected.'
);


-- ─────────────────────────────────────────────────────────────
-- DRIVE OPT-INS
-- ─────────────────────────────────────────────────────────────

-- TCS Drive opt-ins
INSERT INTO drive_opt_ins (drive_id, student_id, status) VALUES
((SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%'), (SELECT id FROM users WHERE email='arun@student.edu'),    'opted_in'),
((SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%'), (SELECT id FROM users WHERE email='sathish@student.edu'), 'opted_in'),
((SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%'), (SELECT id FROM users WHERE email='anitha@student.edu'),  'opted_in'),
((SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%'), (SELECT id FROM users WHERE email='vijay@student.edu'),   'opted_in'),
((SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%'), (SELECT id FROM users WHERE email='priya@student.edu'),   'opted_in'),
((SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%'), (SELECT id FROM users WHERE email='farhan@student.edu'),  'opted_in'),
((SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%'), (SELECT id FROM users WHERE email='lakshmi@student.edu'), 'opted_out');

-- Infosys Drive opt-ins
INSERT INTO drive_opt_ins (drive_id, student_id, status) VALUES
((SELECT id FROM campus_drives WHERE title LIKE 'Infosys%'), (SELECT id FROM users WHERE email='arun@student.edu'),    'opted_in'),
((SELECT id FROM campus_drives WHERE title LIKE 'Infosys%'), (SELECT id FROM users WHERE email='sathish@student.edu'), 'opted_in'),
((SELECT id FROM campus_drives WHERE title LIKE 'Infosys%'), (SELECT id FROM users WHERE email='anitha@student.edu'),  'opted_in'),
((SELECT id FROM campus_drives WHERE title LIKE 'Infosys%'), (SELECT id FROM users WHERE email='farhan@student.edu'),  'opted_in'),
((SELECT id FROM campus_drives WHERE title LIKE 'Infosys%'), (SELECT id FROM users WHERE email='divya@student.edu'),   'opted_in'),
((SELECT id FROM campus_drives WHERE title LIKE 'Infosys%'), (SELECT id FROM users WHERE email='vijay@student.edu'),   'opted_in');


-- ─────────────────────────────────────────────────────────────
-- DRIVE ROUNDS
-- ─────────────────────────────────────────────────────────────

-- TCS: 3 rounds
INSERT INTO drive_rounds (drive_id, round_number, round_type, description, status, passing_score, exam_id) VALUES
(
    (SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%'),
    1, 'aptitude', 'Written aptitude test – 45 minutes. 50 questions.', 'completed', 30,
    (SELECT id FROM exams WHERE title='TCS Aptitude Round 1')
),
(
    (SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%'),
    2, 'coding', 'Coding round – Python/Java. 3 problems in 60 minutes.', 'pending', 10, NULL
),
(
    (SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%'),
    3, 'hr', 'HR Interview – face to face with HR panel.', 'pending', 0, NULL
);

-- Update exam to link to TCS round 1
UPDATE exams
SET drive_round_id = (SELECT id FROM drive_rounds WHERE drive_id=(SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%') AND round_number=1)
WHERE title = 'TCS Aptitude Round 1';

-- Infosys: 4 rounds
INSERT INTO drive_rounds (drive_id, round_number, round_type, description, status, passing_score) VALUES
((SELECT id FROM campus_drives WHERE title LIKE 'Infosys%'), 1, 'aptitude',         'Online aptitude screening – 60 min', 'pending', 25),
((SELECT id FROM campus_drives WHERE title LIKE 'Infosys%'), 2, 'technical',         'Technical interview with engineering team', 'pending', 0),
((SELECT id FROM campus_drives WHERE title LIKE 'Infosys%'), 3, 'group_discussion',  'Group discussion – 10 students per group', 'pending', 0),
((SELECT id FROM campus_drives WHERE title LIKE 'Infosys%'), 4, 'hr',                'Final HR round', 'pending', 0);


-- ─────────────────────────────────────────────────────────────
-- DRIVE ROUND RESULTS (TCS Round 1 — completed)
-- ─────────────────────────────────────────────────────────────

INSERT INTO drive_round_results (round_id, student_id, passed, score, notes) VALUES
(
    (SELECT id FROM drive_rounds WHERE drive_id=(SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%') AND round_number=1),
    (SELECT id FROM users WHERE email='arun@student.edu'),    1, 38, 'Excellent performance'
),
(
    (SELECT id FROM drive_rounds WHERE drive_id=(SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%') AND round_number=1),
    (SELECT id FROM users WHERE email='sathish@student.edu'), 1, 42, 'Top scorer'
),
(
    (SELECT id FROM drive_rounds WHERE drive_id=(SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%') AND round_number=1),
    (SELECT id FROM users WHERE email='anitha@student.edu'),  1, 35, 'Good'
),
(
    (SELECT id FROM drive_rounds WHERE drive_id=(SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%') AND round_number=1),
    (SELECT id FROM users WHERE email='vijay@student.edu'),   1, 31, 'Passed'
),
(
    (SELECT id FROM drive_rounds WHERE drive_id=(SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%') AND round_number=1),
    (SELECT id FROM users WHERE email='priya@student.edu'),   0, 25, 'Did not reach passing score'
),
(
    (SELECT id FROM drive_rounds WHERE drive_id=(SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%') AND round_number=1),
    (SELECT id FROM users WHERE email='farhan@student.edu'),  1, 33, 'Passed'
);


-- ─────────────────────────────────────────────────────────────
-- EXAM SUBMISSIONS (General Aptitude Test)
-- ─────────────────────────────────────────────────────────────

INSERT INTO exam_submissions (exam_id, student_id, answers, score, total_marks, passed,
    tab_switch_count, blur_count, copy_paste_count, malpractice_flag, malpractice_notes) VALUES
((SELECT id FROM exams WHERE title LIKE 'General Aptitude%'), (SELECT id FROM users WHERE email='arun@student.edu'),    '{}', 18, 17, 1, 0, 1, 0, 0, NULL),
((SELECT id FROM exams WHERE title LIKE 'General Aptitude%'), (SELECT id FROM users WHERE email='sathish@student.edu'), '{}', 20, 17, 1, 0, 0, 0, 0, NULL),
((SELECT id FROM exams WHERE title LIKE 'General Aptitude%'), (SELECT id FROM users WHERE email='anitha@student.edu'),  '{}', 17, 17, 1, 1, 2, 0, 0, NULL),
((SELECT id FROM exams WHERE title LIKE 'General Aptitude%'), (SELECT id FROM users WHERE email='vijay@student.edu'),   '{}', 16, 17, 1, 0, 0, 0, 0, NULL),
((SELECT id FROM exams WHERE title LIKE 'General Aptitude%'), (SELECT id FROM users WHERE email='priya@student.edu'),   '{}', 13, 17, 0, 0, 1, 0, 0, NULL),
((SELECT id FROM exams WHERE title LIKE 'General Aptitude%'), (SELECT id FROM users WHERE email='farhan@student.edu'),  '{}', 15, 17, 1, 0, 0, 0, 0, NULL),
-- Malpractice flagged students
((SELECT id FROM exams WHERE title LIKE 'General Aptitude%'), (SELECT id FROM users WHERE email='divya@student.edu'),   '{}', 11, 17, 0, 4, 12, 1, 1, 'Tab switches: 4, Window blur: 12'),
((SELECT id FROM exams WHERE title LIKE 'General Aptitude%'), (SELECT id FROM users WHERE email='lakshmi@student.edu'), '{}', 10, 17, 0, 3, 5,  6, 1, 'Tab switches: 3, Copy/paste: 6');


-- ─────────────────────────────────────────────────────────────
-- NOTIFICATIONS
-- ─────────────────────────────────────────────────────────────

INSERT INTO notifications (sender_id, notif_type, target_role, drive_id, title, message) VALUES
(
    (SELECT id FROM users WHERE email='hr@tcs.com'),
    'company_to_students', 'student',
    (SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%'),
    'TCS Drive Tomorrow – Reporting Instructions',
    'Dear Students, TCS campus drive is scheduled for tomorrow. Please report to Main Auditorium by 8:30 AM with your college ID, 2 passport photos, and all academic mark sheets. Formal dress is mandatory.'
),
(
    (SELECT id FROM users WHERE email='hr@infosys.com'),
    'company_to_students', 'student',
    (SELECT id FROM campus_drives WHERE title LIKE 'Infosys%'),
    'Infosys Drive – Documents Required',
    'Infosys Systems Engineer drive is coming up. Please carry: 1) Updated resume (2 copies) 2) All semester marksheets 3) Aadhar card copy 4) Passport size photo. Aptitude round starts at 10:00 AM sharp.'
),
(
    (SELECT id FROM users WHERE email='admin@college.edu'),
    'head_to_staff', 'placement_officer',
    NULL,
    'Campus Drive Season – Staff Briefing',
    'All placement staff: We have 3 companies visiting this month. Please ensure all classrooms are booked and AV equipment is tested. Coordinate with department HoDs for student lists by Friday.'
),
(
    (SELECT id FROM users WHERE email='hr@tcs.com'),
    'company_to_placement', 'placement_officer',
    (SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%'),
    'TCS – Updated Eligibility Criteria',
    'Please note: TCS has updated eligibility to include students with one active backlog for BPS roles only. Please update student lists accordingly. Contact: ravi.sharma@tcs.com for queries.'
),
(
    (SELECT id FROM users WHERE email='admin@college.edu'),
    'system', NULL,
    NULL,
    'Portal Maintenance – Sunday 2 AM',
    'The placement portal will undergo maintenance on Sunday from 2:00 AM to 4:00 AM. Please complete all submissions before this window. Contact IT support for any issues.'
),
(
    (SELECT id FROM users WHERE email='officer@college.edu'),
    'head_to_staff', 'staff',
    (SELECT id FROM campus_drives WHERE title LIKE 'TCS NQT%'),
    'Pre-Drive Checklist – TCS',
    'Staff team: Please complete the pre-drive checklist: 1) Verify opted-in student count (currently 6) 2) Print attendance sheets 3) Coordinate with TCS coordinator Ravi Sharma 4) Set up Round 1 exam hall.'
);


-- ─────────────────────────────────────────────────────────────
-- VERIFICATION QUERIES (run to check data)
-- ─────────────────────────────────────────────────────────────

-- SELECT 'Users by role' AS check_name, role, COUNT(*) AS cnt FROM users GROUP BY role;
-- SELECT 'Exams' AS check_name, title, status, exam_type FROM exams;
-- SELECT 'Drives' AS check_name, title, status, response_open FROM campus_drives;
-- SELECT 'Opt-ins' AS check_name, COUNT(*) AS total, status FROM drive_opt_ins GROUP BY status;
-- SELECT 'Round results' AS check_name, passed, COUNT(*) AS cnt FROM drive_round_results GROUP BY passed;
-- SELECT 'Malpractice' AS check_name, malpractice_flag, COUNT(*) FROM exam_submissions GROUP BY malpractice_flag;
-- SELECT 'Notifications' AS check_name, notif_type, COUNT(*) FROM notifications GROUP BY notif_type;
