-- ============================================================
-- University Course Registration System (UCRS)
-- Full Database Schema: Tables, Procedures, Triggers, Views
-- MySQL 8.0
-- ============================================================

CREATE DATABASE IF NOT EXISTS ucrs
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE ucrs;

-- ============================================================
-- TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS departments (
  dept_id       INT AUTO_INCREMENT PRIMARY KEY,
  dept_name     VARCHAR(100) NOT NULL,
  faculty_count INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS students (
  student_id    INT AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(100) NOT NULL,
  email         VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  dob           DATE,
  dept_id       INT,
  cgpa          DECIMAL(3,2) DEFAULT 0.00,
  FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

CREATE TABLE IF NOT EXISTS faculty (
  faculty_id    INT AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(100) NOT NULL,
  email         VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  dept_id       INT,
  designation   VARCHAR(100),
  FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

CREATE TABLE IF NOT EXISTS admins (
  admin_id      INT AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(100) NOT NULL,
  email         VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
  course_id   INT AUTO_INCREMENT PRIMARY KEY,
  course_name VARCHAR(150) NOT NULL,
  credit_hours INT NOT NULL,
  dept_id     INT,
  FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

CREATE TABLE IF NOT EXISTS prerequisites (
  course_id  INT,
  prereq_id  INT,
  PRIMARY KEY (course_id, prereq_id),
  FOREIGN KEY (course_id) REFERENCES courses(course_id),
  FOREIGN KEY (prereq_id) REFERENCES courses(course_id)
);

CREATE TABLE IF NOT EXISTS semesters (
  semester_id INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(50) NOT NULL,
  year        INT NOT NULL,
  start_date  DATE,
  end_date    DATE
);

CREATE TABLE IF NOT EXISTS rooms (
  room_id   INT AUTO_INCREMENT PRIMARY KEY,
  building  VARCHAR(100),
  capacity  INT,
  room_type VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS course_offerings (
  offering_id     INT AUTO_INCREMENT PRIMARY KEY,
  course_id       INT,
  faculty_id      INT,
  semester_id     INT,
  seats_total     INT NOT NULL,
  seats_available INT NOT NULL,
  FOREIGN KEY (course_id)   REFERENCES courses(course_id),
  FOREIGN KEY (faculty_id)  REFERENCES faculty(faculty_id),
  FOREIGN KEY (semester_id) REFERENCES semesters(semester_id)
);

CREATE TABLE IF NOT EXISTS enrollments (
  enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
  student_id    INT,
  offering_id   INT,
  grade         CHAR(2) DEFAULT NULL,
  UNIQUE (student_id, offering_id),
  FOREIGN KEY (student_id)  REFERENCES students(student_id)  ON DELETE CASCADE,
  FOREIGN KEY (offering_id) REFERENCES course_offerings(offering_id)
);

CREATE TABLE IF NOT EXISTS timetable (
  slot_id     INT AUTO_INCREMENT PRIMARY KEY,
  offering_id INT,
  day         ENUM('Mon','Tue','Wed','Thu','Fri','Sat'),
  start_time  TIME,
  end_time    TIME,
  room_id     INT,
  FOREIGN KEY (offering_id) REFERENCES course_offerings(offering_id),
  FOREIGN KEY (room_id)     REFERENCES rooms(room_id)
);

-- ============================================================
-- TRIGGERS
-- ============================================================

DROP TRIGGER IF EXISTS trg_prevent_duplicate;
DROP TRIGGER IF EXISTS trg_update_seats;

DELIMITER $$

-- Trigger 1: Prevent duplicate enrollment before insert
CREATE TRIGGER trg_prevent_duplicate
BEFORE INSERT ON enrollments
FOR EACH ROW
BEGIN
  DECLARE v_count INT;
  SELECT COUNT(*) INTO v_count
  FROM enrollments
  WHERE student_id = NEW.student_id
    AND offering_id = NEW.offering_id;
  IF v_count > 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Student is already enrolled in this course offering';
  END IF;
END$$

-- Trigger 2: Decrement available seats after a successful enrollment
CREATE TRIGGER trg_update_seats
AFTER INSERT ON enrollments
FOR EACH ROW
BEGIN
  UPDATE course_offerings
  SET seats_available = seats_available - 1
  WHERE offering_id = NEW.offering_id;
END$$

DELIMITER ;

-- ============================================================
-- STORED PROCEDURES
-- ============================================================

DROP PROCEDURE IF EXISTS enroll_student;
DROP PROCEDURE IF EXISTS drop_course;
DROP PROCEDURE IF EXISTS calculate_gpa;

DELIMITER $$

-- Procedure 1: Enroll a student with full validation
CREATE PROCEDURE enroll_student(IN p_student_id INT, IN p_offering_id INT)
BEGIN
  DECLARE v_course_id       INT;
  DECLARE v_seats           INT;
  DECLARE v_conflict        INT DEFAULT 0;
  DECLARE v_unmet_prereqs   INT DEFAULT 0;

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  START TRANSACTION;

  -- Resolve the course for this offering
  SELECT course_id INTO v_course_id
  FROM course_offerings
  WHERE offering_id = p_offering_id;

  -- 1. Check all prerequisites are completed (grade IS NOT NULL)
  SELECT COUNT(*) INTO v_unmet_prereqs
  FROM prerequisites p
  WHERE p.course_id = v_course_id
    AND p.prereq_id NOT IN (
      SELECT co.course_id
      FROM enrollments e
      JOIN course_offerings co ON e.offering_id = co.offering_id
      WHERE e.student_id = p_student_id
        AND e.grade IS NOT NULL
    );

  IF v_unmet_prereqs > 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Prerequisites not completed for this course';
  END IF;

  -- 2. Check seats are available (lock the row to prevent race conditions)
  SELECT seats_available INTO v_seats
  FROM course_offerings
  WHERE offering_id = p_offering_id
  FOR UPDATE;

  IF v_seats <= 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'No seats available in this course offering';
  END IF;

  -- 3. Check for timetable conflicts with existing enrollments
  SELECT COUNT(*) INTO v_conflict
  FROM timetable t_new
  WHERE t_new.offering_id = p_offering_id
    AND EXISTS (
      SELECT 1
      FROM timetable t_existing
      JOIN enrollments e ON t_existing.offering_id = e.offering_id
      WHERE e.student_id = p_student_id
        AND t_existing.day = t_new.day
        AND t_existing.start_time < t_new.end_time
        AND t_existing.end_time   > t_new.start_time
    );

  IF v_conflict > 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Timetable conflict with an existing enrollment';
  END IF;

  -- All checks passed: insert enrollment (trg_update_seats will decrement seats)
  INSERT INTO enrollments (student_id, offering_id)
  VALUES (p_student_id, p_offering_id);

  COMMIT;
END$$


-- Procedure 2: Drop a course and restore the seat
CREATE PROCEDURE drop_course(IN p_student_id INT, IN p_offering_id INT)
BEGIN
  DECLARE v_count INT DEFAULT 0;

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  START TRANSACTION;

  SELECT COUNT(*) INTO v_count
  FROM enrollments
  WHERE student_id = p_student_id AND offering_id = p_offering_id;

  IF v_count = 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Enrollment not found';
  END IF;

  DELETE FROM enrollments
  WHERE student_id = p_student_id AND offering_id = p_offering_id;

  UPDATE course_offerings
  SET seats_available = seats_available + 1
  WHERE offering_id = p_offering_id;

  COMMIT;
END$$


-- Procedure 3: Compute weighted GPA for a semester and update the student record
CREATE PROCEDURE calculate_gpa(IN p_student_id INT, IN p_semester_id INT)
BEGIN
  DECLARE v_gpa DECIMAL(4,2) DEFAULT 0.00;

  SELECT COALESCE(
    SUM(
      CASE e.grade
        WHEN 'A'  THEN 4.0 * c.credit_hours
        WHEN 'A-' THEN 3.7 * c.credit_hours
        WHEN 'B+' THEN 3.3 * c.credit_hours
        WHEN 'B'  THEN 3.0 * c.credit_hours
        WHEN 'B-' THEN 2.7 * c.credit_hours
        WHEN 'C+' THEN 2.3 * c.credit_hours
        WHEN 'C'  THEN 2.0 * c.credit_hours
        WHEN 'D'  THEN 1.0 * c.credit_hours
        WHEN 'F'  THEN 0.0 * c.credit_hours
        ELSE 0
      END
    ) / NULLIF(
      SUM(CASE WHEN e.grade IS NOT NULL THEN c.credit_hours ELSE 0 END), 0
    ),
    0.00
  ) INTO v_gpa
  FROM enrollments e
  JOIN course_offerings co ON e.offering_id = co.offering_id
  JOIN courses c           ON co.course_id  = c.course_id
  WHERE e.student_id    = p_student_id
    AND co.semester_id  = p_semester_id
    AND e.grade IS NOT NULL;

  UPDATE students
  SET cgpa = v_gpa
  WHERE student_id = p_student_id;
END$$

DELIMITER ;

-- ============================================================
-- VIEWS
-- ============================================================

DROP VIEW IF EXISTS v_student_transcript;
DROP VIEW IF EXISTS v_enrollment_report;
DROP VIEW IF EXISTS v_gpa_distribution;

CREATE VIEW v_student_transcript AS
  SELECT
    e.student_id,
    c.course_name,
    c.credit_hours,
    sem.name  AS semester_name,
    sem.year,
    f.name    AS faculty_name,
    e.grade
  FROM enrollments e
  JOIN course_offerings co ON e.offering_id  = co.offering_id
  JOIN courses c           ON co.course_id   = c.course_id
  JOIN semesters sem       ON co.semester_id = sem.semester_id
  JOIN faculty f           ON co.faculty_id  = f.faculty_id;

CREATE VIEW v_enrollment_report AS
  SELECT
    c.course_name,
    sem.name            AS semester_name,
    sem.year,
    COUNT(e.enrollment_id) AS enrolled_count,
    co.seats_total
  FROM course_offerings co
  JOIN courses c     ON co.course_id   = c.course_id
  JOIN semesters sem ON co.semester_id = sem.semester_id
  LEFT JOIN enrollments e ON co.offering_id = e.offering_id
  GROUP BY co.offering_id, c.course_name, sem.name, sem.year, co.seats_total;

CREATE VIEW v_gpa_distribution AS
  SELECT
    d.dept_name,
    ROUND(AVG(s.cgpa), 2) AS avg_cgpa,
    COUNT(s.student_id)   AS student_count
  FROM departments d
  LEFT JOIN students s ON d.dept_id = s.dept_id
  GROUP BY d.dept_id, d.dept_name;
