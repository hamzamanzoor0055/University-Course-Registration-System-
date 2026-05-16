# University Course Registration System (UCRS)

A full-stack web application for university course management, built as a Database Management Systems project. The database layer (stored procedures, triggers, views) is the primary demonstration.

## Tech Stack

| Layer      | Technology                                |
|------------|-------------------------------------------|
| Backend    | Python 3.x + Flask                        |
| Frontend   | Jinja2 + Tailwind CSS (CDN)              |
| Charts     | Chart.js (CDN)                            |
| Database   | MySQL 8.0                                 |
| DB Driver  | mysql-connector-python (raw SQL, no ORM)  |

---

## Project Structure

```
ucrs/
├── app.py               # Flask application factory
├── config.py            # Configuration (DB creds, secret key)
├── db.py                # MySQL connection helper (per-request)
├── seed.py              # Sample data loader (run once after schema)
├── schema.sql           # DDL: tables, stored procedures, triggers, views
├── requirements.txt
├── routes/
│   ├── utils.py         # login_required decorator
│   ├── auth.py          # /login, /logout
│   ├── student.py       # /student/*
│   ├── faculty.py       # /faculty/*
│   └── admin.py         # /admin/*
└── templates/
    ├── base.html
    ├── auth/login.html
    ├── student/         # dashboard, courses, timetable, transcript
    ├── faculty/         # dashboard, grades
    └── admin/           # dashboard, courses, reports
```

---

## Setup Instructions

### 1. Prerequisites

- Python 3.9+
- MySQL 8.0 running locally (or update `config.py` with your host/user/password)
- Git

### 2. Clone & Install Python Dependencies

```bash
git clone <repo-url>
cd Uni_Course_Reg_System

python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Database Connection

Edit `config.py` (or set environment variables) to match your MySQL credentials:

```python
MYSQL_USER     = 'root'
MYSQL_PASSWORD = 'your_password'
MYSQL_HOST     = 'localhost'
MYSQL_DB       = 'ucrs'
MYSQL_PORT     = 3306
```

Alternatively, set environment variables before running:

```bash
# Windows PowerShell
$env:MYSQL_PASSWORD = "your_password"

# macOS/Linux
export MYSQL_PASSWORD="your_password"
```

### 4. Create the Database Schema

Run `schema.sql` against your MySQL server. This creates the `ucrs` database, all tables, stored procedures, triggers, and views:

```bash
mysql -u root -p < schema.sql
```

Or from within the MySQL client:

```sql
source /full/path/to/schema.sql
```

### 5. Load Sample Data

```bash
python seed.py
```

This inserts departments, admin, faculty, students, courses, semesters, offerings, timetable slots, and historical enrollments with grades.

**Default login credentials after seeding:**

| Role    | Email               | Password    |
|---------|---------------------|-------------|
| Admin   | admin@ucrs.edu      | admin123    |
| Faculty | ahmed@ucrs.edu      | faculty123  |
| Faculty | sara@ucrs.edu       | faculty123  |
| Faculty | james@ucrs.edu      | faculty123  |
| Student | alice@ucrs.edu      | student123  |
| Student | bob@ucrs.edu        | student123  |
| Student | carol@ucrs.edu      | student123  |
| Student | david@ucrs.edu      | student123  |
| Student | eve@ucrs.edu        | student123  |

### 6. Start the Flask Development Server

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

---

## Database Design

### Schema (3NF)

11 tables: `departments`, `students`, `faculty`, `admins`, `courses`, `prerequisites`, `semesters`, `rooms`, `course_offerings`, `enrollments`, `timetable`

### Stored Procedures

| Procedure          | Purpose                                                       |
|--------------------|---------------------------------------------------------------|
| `enroll_student`   | Validates prereqs, seat count, timetable conflicts → INSERT   |
| `drop_course`      | DELETE enrollment + restore seat in one transaction           |
| `calculate_gpa`    | Weighted GPA from grades → UPDATE students.cgpa               |

### Triggers

| Trigger               | Event                     | Action                          |
|-----------------------|---------------------------|---------------------------------|
| `trg_update_seats`    | AFTER INSERT on enrollments | Decrements `seats_available`   |
| `trg_prevent_duplicate` | BEFORE INSERT on enrollments | SIGNALs on duplicate pair   |

### Views

| View                   | Purpose                                          |
|------------------------|--------------------------------------------------|
| `v_student_transcript` | Per-student course history with grades           |
| `v_enrollment_report`  | Enrollment counts per course per semester        |
| `v_gpa_distribution`   | Average CGPA and student count per department    |

---

## Application Features

### Student
- Browse available course offerings and enroll (calls `enroll_student` stored procedure)
- Drop an enrolled course (calls `drop_course` stored procedure)
- View weekly timetable
- View full academic transcript (`v_student_transcript` view)

### Faculty
- View assigned course offerings with enrollment counts
- Enter / update student grades; GPA is recalculated automatically (`calculate_gpa`)

### Admin
- Dashboard with metric cards and a Chart.js enrollment bar chart
- Manage course catalog (add courses with prerequisites)
- Full enrollment and GPA reports from database views

---

## Notes

- All enrollment logic is enforced inside the `enroll_student` stored procedure — Flask only calls `cursor.callproc()`.
- SIGNAL errors from stored procedures are caught in Python and displayed as flash messages.
- Passwords are hashed with `werkzeug.security.generate_password_hash` (PBKDF2-SHA256).
- No JavaScript fetch/AJAX — all form submissions are standard HTML POST.
