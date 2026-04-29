from db import get_connection

conn = get_connection()
cursor = conn.cursor()

# USERS
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50),
    password VARCHAR(50),
    role VARCHAR(20)
)
""")

# STUDENTS (✅ FIXED pass_year)
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    reg_no VARCHAR(20) UNIQUE,
    name VARCHAR(100),
    branch VARCHAR(20),
    semester INT,
    pass_year INT
)
""")

# SUBJECTS
cursor.execute("""
CREATE TABLE IF NOT EXISTS subjects (
    subject_id INT AUTO_INCREMENT PRIMARY KEY,
    subject_name VARCHAR(50),
    branch VARCHAR(20),
    semester INT
)
""")

# MARKS
cursor.execute("""
CREATE TABLE IF NOT EXISTS marks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    subject_id INT,

    total FLOAT,
    percentage FLOAT,
    attainment VARCHAR(20),

    co1 FLOAT,
    co2 FLOAT,
    co3 FLOAT,
    co4 FLOAT,
    co5 FLOAT,

    UNIQUE(student_id, subject_id),

    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
)
""")

# DEFAULT USERS
cursor.execute("INSERT IGNORE INTO users VALUES (1,'admin','admin123','admin')")
cursor.execute("INSERT IGNORE INTO users VALUES (2,'faculty','faculty123','faculty')")

# MARKS PERMISSION (global time window)
cursor.execute("""
CREATE TABLE IF NOT EXISTS marks_permission (
    id INT PRIMARY KEY DEFAULT 1,
    start_time DATETIME,
    end_time DATETIME,
    is_active TINYINT DEFAULT 0
)
""")

# UPLOAD STATUS (track component uploads per subject)
cursor.execute("""
CREATE TABLE IF NOT EXISTS upload_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject_id INT,
    component VARCHAR(20),
    uploaded_at DATETIME,
    combined TINYINT DEFAULT 0,
    UNIQUE(subject_id, component),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
)
""")

conn.commit()
conn.close()

print("✅ DB Ready")