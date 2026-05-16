"""
seed.py — Insert realistic sample data into the UCRS database.
Run AFTER executing schema.sql:
    python seed.py
"""

import mysql.connector
from werkzeug.security import generate_password_hash

# ── Database connection ──────────────────────────────────────────────────────
DB_CONFIG = dict(
    host='localhost',
    user='root',
    password='continue7x',        # change as needed
    database='ucrs',
    port=3306,
    autocommit=True,
)

conn = mysql.connector.connect(**DB_CONFIG)
cur = conn.cursor()

# ── Helpers ──────────────────────────────────────────────────────────────────

def insert(sql, params=()):
    cur.execute(sql, params)
    return cur.lastrowid


# ── 1. Departments ───────────────────────────────────────────────────────────
print("Inserting departments...")
cs_id = insert("INSERT INTO departments (dept_name, faculty_count) VALUES (%s, %s)", ('Computer Science', 3))
se_id = insert("INSERT INTO departments (dept_name, faculty_count) VALUES (%s, %s)", ('Software Engineering', 2))
ee_id = insert("INSERT INTO departments (dept_name, faculty_count) VALUES (%s, %s)", ('Electrical Engineering', 2))

# ── 2. Admin ─────────────────────────────────────────────────────────────────
print("Inserting admin...")
insert(
    "INSERT INTO admins (name, email, password_hash) VALUES (%s, %s, %s)",
    ('System Admin', 'admin@ucrs.edu', generate_password_hash('admin123'))
)

# ── 3. Faculty ───────────────────────────────────────────────────────────────
print("Inserting faculty...")
f_ahmed = insert(
    "INSERT INTO faculty (name, email, password_hash, dept_id, designation) VALUES (%s,%s,%s,%s,%s)",
    ('Dr. Ahmed Khan', 'ahmed@ucrs.edu', generate_password_hash('faculty123'), cs_id, 'Professor')
)
f_sara = insert(
    "INSERT INTO faculty (name, email, password_hash, dept_id, designation) VALUES (%s,%s,%s,%s,%s)",
    ('Dr. Sara Lee', 'sara@ucrs.edu', generate_password_hash('faculty123'), se_id, 'Associate Professor')
)
f_james = insert(
    "INSERT INTO faculty (name, email, password_hash, dept_id, designation) VALUES (%s,%s,%s,%s,%s)",
    ('Dr. James Wilson', 'james@ucrs.edu', generate_password_hash('faculty123'), ee_id, 'Assistant Professor')
)

# ── 4. Students ──────────────────────────────────────────────────────────────
print("Inserting students...")
s_alice = insert(
    "INSERT INTO students (name, email, password_hash, dob, dept_id) VALUES (%s,%s,%s,%s,%s)",
    ('Alice Johnson', 'alice@ucrs.edu', generate_password_hash('student123'), '2002-03-15', cs_id)
)
s_bob = insert(
    "INSERT INTO students (name, email, password_hash, dob, dept_id) VALUES (%s,%s,%s,%s,%s)",
    ('Bob Smith', 'bob@ucrs.edu', generate_password_hash('student123'), '2001-07-22', cs_id)
)
s_carol = insert(
    "INSERT INTO students (name, email, password_hash, dob, dept_id) VALUES (%s,%s,%s,%s,%s)",
    ('Carol Williams', 'carol@ucrs.edu', generate_password_hash('student123'), '2002-11-05', se_id)
)
s_david = insert(
    "INSERT INTO students (name, email, password_hash, dob, dept_id) VALUES (%s,%s,%s,%s,%s)",
    ('David Brown', 'david@ucrs.edu', generate_password_hash('student123'), '2003-01-30', ee_id)
)
s_eve = insert(
    "INSERT INTO students (name, email, password_hash, dob, dept_id) VALUES (%s,%s,%s,%s,%s)",
    ('Eve Davis', 'eve@ucrs.edu', generate_password_hash('student123'), '2002-06-18', se_id)
)

# ── 5. Courses ───────────────────────────────────────────────────────────────
print("Inserting courses...")
c_intro  = insert("INSERT INTO courses (course_name, credit_hours, dept_id) VALUES (%s,%s,%s)", ('Introduction to Programming', 3, cs_id))
c_ds     = insert("INSERT INTO courses (course_name, credit_hours, dept_id) VALUES (%s,%s,%s)", ('Data Structures', 3, cs_id))
c_db     = insert("INSERT INTO courses (course_name, credit_hours, dept_id) VALUES (%s,%s,%s)", ('Database Systems', 3, cs_id))
c_algo   = insert("INSERT INTO courses (course_name, credit_hours, dept_id) VALUES (%s,%s,%s)", ('Algorithms', 3, cs_id))
c_sef    = insert("INSERT INTO courses (course_name, credit_hours, dept_id) VALUES (%s,%s,%s)", ('Software Engineering Fundamentals', 3, se_id))
c_sdp    = insert("INSERT INTO courses (course_name, credit_hours, dept_id) VALUES (%s,%s,%s)", ('Software Design Patterns', 3, se_id))
c_circ   = insert("INSERT INTO courses (course_name, credit_hours, dept_id) VALUES (%s,%s,%s)", ('Circuit Analysis', 4, ee_id))
c_dielec = insert("INSERT INTO courses (course_name, credit_hours, dept_id) VALUES (%s,%s,%s)", ('Digital Electronics', 3, ee_id))

# ── 6. Prerequisites ─────────────────────────────────────────────────────────
print("Inserting prerequisites...")
# Data Structures requires Intro to Programming
cur.execute("INSERT INTO prerequisites (course_id, prereq_id) VALUES (%s,%s)", (c_ds, c_intro))
# Database Systems requires Data Structures
cur.execute("INSERT INTO prerequisites (course_id, prereq_id) VALUES (%s,%s)", (c_db, c_ds))
# Algorithms requires Data Structures
cur.execute("INSERT INTO prerequisites (course_id, prereq_id) VALUES (%s,%s)", (c_algo, c_ds))
# Software Design Patterns requires SE Fundamentals
cur.execute("INSERT INTO prerequisites (course_id, prereq_id) VALUES (%s,%s)", (c_sdp, c_sef))
# Digital Electronics requires Circuit Analysis
cur.execute("INSERT INTO prerequisites (course_id, prereq_id) VALUES (%s,%s)", (c_dielec, c_circ))

# ── 7. Semesters ─────────────────────────────────────────────────────────────
print("Inserting semesters...")
sem_spring24 = insert(
    "INSERT INTO semesters (name, year, start_date, end_date) VALUES (%s,%s,%s,%s)",
    ('Spring', 2024, '2024-01-15', '2024-05-31')
)
sem_fall24 = insert(
    "INSERT INTO semesters (name, year, start_date, end_date) VALUES (%s,%s,%s,%s)",
    ('Fall', 2024, '2024-09-01', '2024-12-31')
)

# ── 8. Rooms ─────────────────────────────────────────────────────────────────
print("Inserting rooms...")
r_a101 = insert("INSERT INTO rooms (building, capacity, room_type) VALUES (%s,%s,%s)", ('Block A', 40, 'Lecture Hall'))
r_b202 = insert("INSERT INTO rooms (building, capacity, room_type) VALUES (%s,%s,%s)", ('Block B', 25, 'Computer Lab'))
r_c303 = insert("INSERT INTO rooms (building, capacity, room_type) VALUES (%s,%s,%s)", ('Block C', 20, 'Classroom'))

# ── 9. Course Offerings ──────────────────────────────────────────────────────
# Spring 2024 offerings (historical — already completed)
print("Inserting course offerings...")
off_intro_sp24 = insert(
    "INSERT INTO course_offerings (course_id,faculty_id,semester_id,seats_total,seats_available) VALUES (%s,%s,%s,%s,%s)",
    (c_intro, f_ahmed, sem_spring24, 30, 30)
)
off_sef_sp24 = insert(
    "INSERT INTO course_offerings (course_id,faculty_id,semester_id,seats_total,seats_available) VALUES (%s,%s,%s,%s,%s)",
    (c_sef, f_sara, sem_spring24, 30, 30)
)
off_circ_sp24 = insert(
    "INSERT INTO course_offerings (course_id,faculty_id,semester_id,seats_total,seats_available) VALUES (%s,%s,%s,%s,%s)",
    (c_circ, f_james, sem_spring24, 25, 25)
)

# Fall 2024 offerings (current semester)
off_ds_fa24 = insert(
    "INSERT INTO course_offerings (course_id,faculty_id,semester_id,seats_total,seats_available) VALUES (%s,%s,%s,%s,%s)",
    (c_ds, f_ahmed, sem_fall24, 30, 30)
)
off_db_fa24 = insert(
    "INSERT INTO course_offerings (course_id,faculty_id,semester_id,seats_total,seats_available) VALUES (%s,%s,%s,%s,%s)",
    (c_db, f_ahmed, sem_fall24, 25, 25)
)
off_sdp_fa24 = insert(
    "INSERT INTO course_offerings (course_id,faculty_id,semester_id,seats_total,seats_available) VALUES (%s,%s,%s,%s,%s)",
    (c_sdp, f_sara, sem_fall24, 28, 28)
)
off_dielec_fa24 = insert(
    "INSERT INTO course_offerings (course_id,faculty_id,semester_id,seats_total,seats_available) VALUES (%s,%s,%s,%s,%s)",
    (c_dielec, f_james, sem_fall24, 20, 20)
)
off_intro_fa24 = insert(
    "INSERT INTO course_offerings (course_id,faculty_id,semester_id,seats_total,seats_available) VALUES (%s,%s,%s,%s,%s)",
    (c_intro, f_ahmed, sem_fall24, 30, 30)
)

# ── 10. Timetable ────────────────────────────────────────────────────────────
# Spring 2024 slots
print("Inserting timetable...")
cur.execute("INSERT INTO timetable (offering_id,day,start_time,end_time,room_id) VALUES (%s,%s,%s,%s,%s)", (off_intro_sp24, 'Mon', '09:00', '10:30', r_a101))
cur.execute("INSERT INTO timetable (offering_id,day,start_time,end_time,room_id) VALUES (%s,%s,%s,%s,%s)", (off_intro_sp24, 'Wed', '09:00', '10:30', r_a101))
cur.execute("INSERT INTO timetable (offering_id,day,start_time,end_time,room_id) VALUES (%s,%s,%s,%s,%s)", (off_sef_sp24,   'Tue', '11:00', '12:30', r_b202))
cur.execute("INSERT INTO timetable (offering_id,day,start_time,end_time,room_id) VALUES (%s,%s,%s,%s,%s)", (off_sef_sp24,   'Thu', '11:00', '12:30', r_b202))
cur.execute("INSERT INTO timetable (offering_id,day,start_time,end_time,room_id) VALUES (%s,%s,%s,%s,%s)", (off_circ_sp24,  'Mon', '14:00', '15:30', r_c303))
cur.execute("INSERT INTO timetable (offering_id,day,start_time,end_time,room_id) VALUES (%s,%s,%s,%s,%s)", (off_circ_sp24,  'Wed', '14:00', '15:30', r_c303))

# Fall 2024 slots
cur.execute("INSERT INTO timetable (offering_id,day,start_time,end_time,room_id) VALUES (%s,%s,%s,%s,%s)", (off_ds_fa24,     'Mon', '09:00', '10:30', r_a101))
cur.execute("INSERT INTO timetable (offering_id,day,start_time,end_time,room_id) VALUES (%s,%s,%s,%s,%s)", (off_ds_fa24,     'Wed', '09:00', '10:30', r_a101))
cur.execute("INSERT INTO timetable (offering_id,day,start_time,end_time,room_id) VALUES (%s,%s,%s,%s,%s)", (off_db_fa24,     'Tue', '11:00', '12:30', r_a101))
cur.execute("INSERT INTO timetable (offering_id,day,start_time,end_time,room_id) VALUES (%s,%s,%s,%s,%s)", (off_db_fa24,     'Thu', '11:00', '12:30', r_a101))
cur.execute("INSERT INTO timetable (offering_id,day,start_time,end_time,room_id) VALUES (%s,%s,%s,%s,%s)", (off_sdp_fa24,    'Mon', '14:00', '15:30', r_b202))
cur.execute("INSERT INTO timetable (offering_id,day,start_time,end_time,room_id) VALUES (%s,%s,%s,%s,%s)", (off_sdp_fa24,    'Wed', '14:00', '15:30', r_b202))
cur.execute("INSERT INTO timetable (offering_id,day,start_time,end_time,room_id) VALUES (%s,%s,%s,%s,%s)", (off_dielec_fa24, 'Tue', '09:00', '10:30', r_c303))
cur.execute("INSERT INTO timetable (offering_id,day,start_time,end_time,room_id) VALUES (%s,%s,%s,%s,%s)", (off_dielec_fa24, 'Thu', '09:00', '10:30', r_c303))
cur.execute("INSERT INTO timetable (offering_id,day,start_time,end_time,room_id) VALUES (%s,%s,%s,%s,%s)", (off_intro_fa24,  'Fri', '09:00', '10:30', r_a101))

# ── 11. Spring 2024 Enrollments (with grades) ────────────────────────────────
# These bypass stored procedures to seed historical completed data.
# The trigger trg_update_seats fires on each insert and decrements seats_available.
print("Inserting historical enrollments (Spring 2024)...")
cur.execute("INSERT INTO enrollments (student_id,offering_id,grade) VALUES (%s,%s,%s)", (s_alice, off_intro_sp24, 'A'))
cur.execute("INSERT INTO enrollments (student_id,offering_id,grade) VALUES (%s,%s,%s)", (s_bob,   off_intro_sp24, 'B'))
cur.execute("INSERT INTO enrollments (student_id,offering_id,grade) VALUES (%s,%s,%s)", (s_carol, off_sef_sp24,   'A'))
cur.execute("INSERT INTO enrollments (student_id,offering_id,grade) VALUES (%s,%s,%s)", (s_eve,   off_sef_sp24,   'B'))
cur.execute("INSERT INTO enrollments (student_id,offering_id,grade) VALUES (%s,%s,%s)", (s_david, off_circ_sp24,  'B'))

# Compute GPA for students who completed Spring 2024
for sid in (s_alice, s_bob, s_carol, s_eve, s_david):
    cur.callproc('calculate_gpa', [sid, sem_spring24])

# ── 12. Fall 2024 Enrollments (current — no grades yet) ──────────────────────
print("Inserting current enrollments (Fall 2024)...")
cur.execute("INSERT INTO enrollments (student_id,offering_id) VALUES (%s,%s)", (s_alice, off_ds_fa24))
cur.execute("INSERT INTO enrollments (student_id,offering_id) VALUES (%s,%s)", (s_bob,   off_ds_fa24))
cur.execute("INSERT INTO enrollments (student_id,offering_id) VALUES (%s,%s)", (s_carol, off_sdp_fa24))
cur.execute("INSERT INTO enrollments (student_id,offering_id) VALUES (%s,%s)", (s_eve,   off_sdp_fa24))
cur.execute("INSERT INTO enrollments (student_id,offering_id) VALUES (%s,%s)", (s_david, off_dielec_fa24))

cur.close()
conn.close()
print("\nSeed data inserted successfully!")
print("\nLogin credentials:")
print("  Admin   : admin@ucrs.edu  / admin123")
print("  Faculty : ahmed@ucrs.edu  / faculty123")
print("  Faculty : sara@ucrs.edu   / faculty123")
print("  Faculty : james@ucrs.edu  / faculty123")
print("  Student : alice@ucrs.edu  / student123  (CS, completed Intro → enrolled in Data Structures)")
print("  Student : bob@ucrs.edu    / student123  (CS, completed Intro → enrolled in Data Structures)")
print("  Student : carol@ucrs.edu  / student123  (SE, completed SEF  → enrolled in Design Patterns)")
print("  Student : eve@ucrs.edu    / student123  (SE, completed SEF  → enrolled in Design Patterns)")
print("  Student : david@ucrs.edu  / student123  (EE, completed Circ → enrolled in Digital Electronics)")
