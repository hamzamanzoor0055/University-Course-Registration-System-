from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import mysql.connector
from db import get_db
from routes.utils import login_required

student_bp = Blueprint('student', __name__, url_prefix='/student')


@student_bp.route('/dashboard')
@login_required(role='student')
def dashboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    student_id = session['user_id']

    cursor.execute(
        '''SELECT s.student_id, s.name, s.cgpa, s.email, d.dept_name
           FROM students s
           LEFT JOIN departments d ON s.dept_id = d.dept_id
           WHERE s.student_id = %s''',
        (student_id,)
    )
    student = cursor.fetchone()

    cursor.execute(
        '''SELECT e.enrollment_id, e.offering_id, e.grade,
                  c.course_name, c.credit_hours,
                  sem.name AS semester_name, sem.year,
                  f.name AS faculty_name
           FROM enrollments e
           JOIN course_offerings co ON e.offering_id = co.offering_id
           JOIN courses c ON co.course_id = c.course_id
           JOIN semesters sem ON co.semester_id = sem.semester_id
           JOIN faculty f ON co.faculty_id = f.faculty_id
           WHERE e.student_id = %s
           ORDER BY sem.year DESC, sem.name''',
        (student_id,)
    )
    enrollments = cursor.fetchall()
    cursor.close()

    return render_template('student/dashboard.html', student=student, enrollments=enrollments)


@student_bp.route('/courses')
@login_required(role='student')
def courses():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    student_id = session['user_id']

    cursor.execute(
        '''SELECT co.offering_id, c.course_name, c.credit_hours,
                  d.dept_name, f.name AS faculty_name,
                  sem.name AS semester_name, sem.year,
                  co.seats_available, co.seats_total,
                  (SELECT COUNT(*) FROM enrollments e
                   WHERE e.student_id = %s AND e.offering_id = co.offering_id) AS already_enrolled
           FROM course_offerings co
           JOIN courses c ON co.course_id = c.course_id
           JOIN departments d ON c.dept_id = d.dept_id
           JOIN faculty f ON co.faculty_id = f.faculty_id
           JOIN semesters sem ON co.semester_id = sem.semester_id
           ORDER BY sem.year DESC, c.course_name''',
        (student_id,)
    )
    offerings = cursor.fetchall()
    cursor.close()

    return render_template('student/courses.html', offerings=offerings)


@student_bp.route('/enroll', methods=['POST'])
@login_required(role='student')
def enroll():
    offering_id = request.form.get('offering_id')
    student_id = session['user_id']

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.callproc('enroll_student', [student_id, offering_id])
        flash('Successfully enrolled in the course!', 'success')
    except mysql.connector.Error as e:
        flash(f'Enrollment failed: {e.msg}', 'error')
    finally:
        cursor.close()

    return redirect(url_for('student.courses'))


@student_bp.route('/drop', methods=['POST'])
@login_required(role='student')
def drop():
    offering_id = request.form.get('offering_id')
    student_id = session['user_id']

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.callproc('drop_course', [student_id, offering_id])
        flash('Course dropped successfully.', 'success')
    except mysql.connector.Error as e:
        flash(f'Drop failed: {e.msg}', 'error')
    finally:
        cursor.close()

    return redirect(url_for('student.dashboard'))


@student_bp.route('/transcript')
@login_required(role='student')
def transcript():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    student_id = session['user_id']

    cursor.execute(
        '''SELECT course_name, credit_hours, semester_name, year, faculty_name, grade
           FROM v_student_transcript
           WHERE student_id = %s
           ORDER BY year DESC, semester_name''',
        (student_id,)
    )
    records = cursor.fetchall()
    cursor.close()

    return render_template('student/transcript.html', records=records)


@student_bp.route('/timetable')
@login_required(role='student')
def timetable():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    student_id = session['user_id']

    cursor.execute(
        '''SELECT t.day, t.start_time, t.end_time,
                  c.course_name, r.building, r.room_type, r.capacity
           FROM timetable t
           JOIN course_offerings co ON t.offering_id = co.offering_id
           JOIN courses c ON co.course_id = c.course_id
           JOIN rooms r ON t.room_id = r.room_id
           JOIN enrollments e ON e.offering_id = co.offering_id
           WHERE e.student_id = %s
           ORDER BY FIELD(t.day,'Mon','Tue','Wed','Thu','Fri','Sat'), t.start_time''',
        (student_id,)
    )
    slots = cursor.fetchall()
    cursor.close()

    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    timetable_by_day = {day: [] for day in days}
    for slot in slots:
        day = slot['day']
        start = slot['start_time']
        end = slot['end_time']
        if hasattr(start, 'seconds'):
            total = start.seconds
            slot['start_fmt'] = f"{total // 3600:02d}:{(total % 3600) // 60:02d}"
            total = end.seconds
            slot['end_fmt'] = f"{total // 3600:02d}:{(total % 3600) // 60:02d}"
        else:
            slot['start_fmt'] = str(start)
            slot['end_fmt'] = str(end)
        timetable_by_day[day].append(slot)

    return render_template('student/timetable.html',
                           timetable_by_day=timetable_by_day,
                           days=days)
