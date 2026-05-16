from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import mysql.connector
import json
from db import get_db
from routes.utils import login_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@login_required(role='admin')
def dashboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute('SELECT COUNT(*) AS total FROM students')
    total_students = cursor.fetchone()['total']

    cursor.execute('SELECT COUNT(*) AS total FROM enrollments')
    total_enrollments = cursor.fetchone()['total']

    cursor.execute('SELECT COUNT(*) AS total FROM course_offerings WHERE seats_available > 0')
    active_courses = cursor.fetchone()['total']

    cursor.execute(
        '''SELECT course_name, semester_name, year, enrolled_count, seats_total
           FROM v_enrollment_report
           ORDER BY year DESC, semester_name, course_name
           LIMIT 10'''
    )
    enrollment_report = cursor.fetchall()

    cursor.execute(
        '''SELECT dept_name, avg_cgpa, student_count
           FROM v_gpa_distribution
           ORDER BY dept_name'''
    )
    gpa_dist = cursor.fetchall()

    chart_labels = json.dumps([r['course_name'] for r in enrollment_report])
    chart_data = json.dumps([r['enrolled_count'] for r in enrollment_report])

    cursor.close()
    return render_template(
        'admin/dashboard.html',
        total_students=total_students,
        total_enrollments=total_enrollments,
        active_courses=active_courses,
        enrollment_report=enrollment_report,
        gpa_dist=gpa_dist,
        chart_labels=chart_labels,
        chart_data=chart_data,
    )


@admin_bp.route('/courses')
@login_required(role='admin')
def courses():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        '''SELECT c.course_id, c.course_name, c.credit_hours,
                  d.dept_name,
                  GROUP_CONCAT(p.prereq_id ORDER BY p.prereq_id) AS prereq_ids,
                  (SELECT GROUP_CONCAT(c2.course_name ORDER BY c2.course_name SEPARATOR ', ')
                   FROM prerequisites pr
                   JOIN courses c2 ON pr.prereq_id = c2.course_id
                   WHERE pr.course_id = c.course_id) AS prerequisites
           FROM courses c
           LEFT JOIN departments d ON c.dept_id = d.dept_id
           LEFT JOIN prerequisites p ON p.course_id = c.course_id
           GROUP BY c.course_id
           ORDER BY d.dept_name, c.course_name'''
    )
    all_courses = cursor.fetchall()

    cursor.execute('SELECT dept_id, dept_name FROM departments ORDER BY dept_name')
    departments = cursor.fetchall()

    cursor.close()
    return render_template('admin/courses.html', courses=all_courses, departments=departments)


@admin_bp.route('/courses/add', methods=['POST'])
@login_required(role='admin')
def add_course():
    course_name = request.form.get('course_name', '').strip()
    credit_hours = request.form.get('credit_hours', type=int)
    dept_id = request.form.get('dept_id', type=int)
    prereq_ids = request.form.getlist('prereq_ids')

    if not course_name or not credit_hours or not dept_id:
        flash('Course name, credit hours, and department are required.', 'error')
        return redirect(url_for('admin.courses'))

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            'INSERT INTO courses (course_name, credit_hours, dept_id) VALUES (%s, %s, %s)',
            (course_name, credit_hours, dept_id)
        )
        new_course_id = cursor.lastrowid

        for pid in prereq_ids:
            if pid:
                cursor.execute(
                    'INSERT INTO prerequisites (course_id, prereq_id) VALUES (%s, %s)',
                    (new_course_id, int(pid))
                )

        flash(f'Course "{course_name}" added successfully.', 'success')
    except mysql.connector.Error as e:
        flash(f'Failed to add course: {e.msg}', 'error')
    finally:
        cursor.close()

    return redirect(url_for('admin.courses'))


@admin_bp.route('/reports')
@login_required(role='admin')
def reports():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        '''SELECT course_name, semester_name, year, enrolled_count, seats_total
           FROM v_enrollment_report
           ORDER BY year DESC, semester_name, enrolled_count DESC'''
    )
    enrollment_report = cursor.fetchall()

    cursor.execute(
        '''SELECT dept_name, avg_cgpa, student_count
           FROM v_gpa_distribution
           ORDER BY avg_cgpa DESC'''
    )
    gpa_dist = cursor.fetchall()

    chart_labels = json.dumps([r['course_name'] for r in enrollment_report])
    chart_data = json.dumps([r['enrolled_count'] for r in enrollment_report])

    cursor.close()
    return render_template(
        'admin/reports.html',
        enrollment_report=enrollment_report,
        gpa_dist=gpa_dist,
        chart_labels=chart_labels,
        chart_data=chart_data,
    )
