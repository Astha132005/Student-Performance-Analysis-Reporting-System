"""
SPARS Full Migration Script
- Adds DAA, OOPS, DAI subjects
- Expands users table with subject_id and full_name
- Replaces generic faculty user with 6 subject-specific teachers
- Imports OOPS, DAA, DAI marks from Excel
"""
import mysql.connector
import openpyxl
import sys

# Force UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

conn = mysql.connector.connect(
    host='localhost', user='root', password='A2s0t0h5@Dray', database='SPARS'
)
cursor = conn.cursor(dictionary=True)

print("=" * 60)
print("SPARS Full Migration")
print("=" * 60)

# STEP 1: Expand users table
print("\n[1] Expanding users table...")
try:
    cursor.execute("ALTER TABLE users ADD COLUMN subject_id INT NULL")
    print("  Added subject_id column")
except Exception as e:
    if "Duplicate column" in str(e):
        print("  subject_id already exists")
    else:
        print("  Warning: " + str(e))

try:
    cursor.execute("ALTER TABLE users ADD COLUMN full_name VARCHAR(100) NULL")
    print("  Added full_name column")
except Exception as e:
    if "Duplicate column" in str(e):
        print("  full_name already exists")
    else:
        print("  Warning: " + str(e))

conn.commit()

# STEP 2: Add new subjects
print("\n[2] Adding new subjects...")
new_subjects = [
    ('DAA', 3, 'AIML'),
    ('OOPS', 3, 'AIML'),
    ('DAI', 3, 'AIML'),
]
for subj_name, sem, branch in new_subjects:
    cursor.execute("SELECT subject_id FROM subjects WHERE subject_name=%s", (subj_name,))
    existing = cursor.fetchone()
    if existing:
        print("  " + subj_name + " already exists (id=" + str(existing['subject_id']) + ")")
    else:
        cursor.execute(
            "INSERT INTO subjects (subject_name, semester, branch) VALUES (%s, %s, %s)",
            (subj_name, sem, branch)
        )
        print("  Added subject: " + subj_name)

conn.commit()

# Get subject IDs
cursor.execute("SELECT subject_id, subject_name FROM subjects")
subjects_map = {r['subject_name']: r['subject_id'] for r in cursor.fetchall()}
print("  Subject map: " + str(subjects_map))

# STEP 3: Replace faculty users with 6 teachers
print("\n[3] Setting up faculty accounts...")
cursor.execute("DELETE FROM users WHERE role='faculty'")
print("  Removed old faculty users")

teachers = [
    ('daa_teacher', 'daa123', 'faculty', 'Chinmayee', 'DAA'),
    ('oops_teacher', 'oops123', 'faculty', 'Tapas', 'OOPS'),
    ('dai_teacher', 'dai123', 'faculty', 'Stitipragyan', 'DAI'),
    ('os_teacher', 'os123', 'faculty', 'Sanjit', 'OS'),
    ('ml_teacher', 'ml123', 'faculty', 'Swatilipsa', 'ML'),
    ('dva_teacher', 'dva123', 'faculty', 'Pranati', 'DVA'),
]

for username, password, role, full_name, subject_name in teachers:
    subject_id = subjects_map.get(subject_name)
    cursor.execute(
        "INSERT INTO users (username, password, role, full_name, subject_id) VALUES (%s, %s, %s, %s, %s)",
        (username, password, role, full_name, subject_id)
    )
    print("  Added: " + username + " (" + full_name + ") -> " + subject_name)

conn.commit()

# Helper: get student_id from reg_no
def get_student_id(reg_no):
    cursor.execute("SELECT student_id FROM students WHERE reg_no=%s", (str(reg_no),))
    row = cursor.fetchone()
    return row['student_id'] if row else None

def import_marks(ws, subject_id, start_row, subj_name, has_quiz_assign=True, default_quiz=4, default_assign=9, default_attend=4):
    imported = 0
    skipped = 0
    for row in ws.iter_rows(min_row=start_row, values_only=True):
        # Expecting: col0=sl, col1=name, col2=reg_no, col3=subj_code, col4=midsem, col5=quiz, col6=assign, col7=attend
        reg_no_raw = row[2]
        midsem_raw = row[4]

        if reg_no_raw is None or not isinstance(reg_no_raw, (int, float)):
            continue

        reg_no = str(int(reg_no_raw))

        try:
            midsem = min(float(midsem_raw) if midsem_raw not in (None, 'absent', '') else 0, 20)
        except:
            midsem = 0

        if has_quiz_assign:
            try:
                quiz = min(float(row[5]) if row[5] not in (None, '') else 0, 5)
            except:
                quiz = 0
            try:
                assign = min(float(row[6]) if row[6] not in (None, '') else 0, 10)
            except:
                assign = 0
            try:
                attend = min(float(row[7]) if row[7] not in (None, '') else 0, 5)
            except:
                attend = 0
        else:
            quiz = default_quiz
            assign = default_assign
            attend = default_attend

        total = midsem + quiz + assign + attend
        percentage = round((total / 40) * 100, 2)
        attainment = 'High' if percentage >= 70 else ('Medium' if percentage >= 40 else 'Low')

        # CO approximation: distribute midsem equally across 5 COs
        co_each = round((midsem / 20) * 100 / 5, 2) if midsem > 0 else 0
        co1 = co2 = co3 = co4 = co5 = co_each

        student_id = get_student_id(reg_no)
        if not student_id:
            skipped += 1
            continue

        cursor.execute("SELECT id FROM marks WHERE student_id=%s AND subject_id=%s", (student_id, subject_id))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE marks SET midsem_total=%s, quiz_total=%s, assignment_total=%s,
                attendance_total=%s, total=%s, percentage=%s, attainment=%s,
                co1=%s, co2=%s, co3=%s, co4=%s, co5=%s
                WHERE student_id=%s AND subject_id=%s
            """, (midsem, quiz, assign, attend, total, percentage, attainment,
                  co1, co2, co3, co4, co5, student_id, subject_id))
        else:
            cursor.execute("""
                INSERT INTO marks (student_id, subject_id, midsem_total, quiz_total,
                assignment_total, attendance_total, total, percentage, attainment, co1, co2, co3, co4, co5)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (student_id, subject_id, midsem, quiz, assign, attend,
                  total, percentage, attainment, co1, co2, co3, co4, co5))
        imported += 1

    conn.commit()
    print("  " + subj_name + ": " + str(imported) + " imported, " + str(skipped) + " skipped")
    return imported, skipped

# Load workbook
wb = openpyxl.load_workbook(r'E:\PPD\SPARS\PPD_LAB.xlsx')

# STEP 4: Import OOPS
print("\n[4] Importing OOPS marks...")
oops_subject_id = subjects_map['OOPS']
ws_oops = wb['OOPS_3rdsem_midsem_analysis']
import_marks(ws_oops, oops_subject_id, 9, 'OOPS', has_quiz_assign=True)

# STEP 5: Import DAA
print("\n[5] Importing DAA marks...")
daa_subject_id = subjects_map['DAA']
ws_daa = wb['MIdsem_Total_AAD']
import_marks(ws_daa, daa_subject_id, 9, 'DAA', has_quiz_assign=True)

# STEP 6: Import DAI (midsem only, defaults for rest)
print("\n[6] Importing DAI marks...")
dai_subject_id = subjects_map['DAI']
ws_dai = wb['DAI-3RD-MID SEMESTER']
import_marks(ws_dai, dai_subject_id, 9, 'DAI', has_quiz_assign=False, default_quiz=4, default_assign=9, default_attend=4)

# STEP 7: Populate component tables (midsem/quiz/assignment/attendance) for CO charts
print("\n[7] Populating CO component tables...")

def upsert_component(table, student_id, subject_id, co1, co2, co3, co4, co5):
    cursor.execute("SELECT id FROM " + table + " WHERE student_id=%s AND subject_id=%s", (student_id, subject_id))
    if cursor.fetchone():
        cursor.execute(
            "UPDATE " + table + " SET co1=%s, co2=%s, co3=%s, co4=%s, co5=%s WHERE student_id=%s AND subject_id=%s",
            (co1, co2, co3, co4, co5, student_id, subject_id)
        )
    else:
        cursor.execute(
            "INSERT INTO " + table + " (student_id, subject_id, co1, co2, co3, co4, co5) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (student_id, subject_id, co1, co2, co3, co4, co5)
        )

for subj_name, subj_id in [('OOPS', oops_subject_id), ('DAA', daa_subject_id), ('DAI', dai_subject_id)]:
    cursor.execute("""
        SELECT student_id, midsem_total, quiz_total, assignment_total, attendance_total
        FROM marks WHERE subject_id=%s
    """, (subj_id,))
    rows = cursor.fetchall()
    for r in rows:
        sid = r['student_id']
        mid = r['midsem_total'] or 0
        co_mid = round(mid / 4.0, 2)
        upsert_component('midsem', sid, subj_id, co_mid, co_mid, co_mid, co_mid, co_mid)

        q = (r['quiz_total'] or 0) / 1.0
        co_q = round(q / 4.0, 2)
        upsert_component('quiz', sid, subj_id, co_q, co_q, co_q, co_q, co_q)

        a = (r['assignment_total'] or 0) / 2.0
        co_a = round(a / 4.0, 2)
        upsert_component('assignment', sid, subj_id, co_a, co_a, co_a, co_a, co_a)

        att = (r['attendance_total'] or 0) / 1.0
        co_att = round(att / 4.0, 2)
        upsert_component('attendance', sid, subj_id, co_att, co_att, co_att, co_att, co_att)

    conn.commit()
    print("  " + subj_name + ": component rows done for " + str(len(rows)) + " students")

conn.close()
print("\nMigration complete!")
print("  - DAA, OOPS, DAI subjects added")
print("  - 6 faculty users created")
print("  - OOPS marks imported from OOPS_3rdsem_midsem_analysis")
print("  - DAA marks imported from MIdsem_Total_AAD")
print("  - DAI marks imported from DAI-3RD-MID SEMESTER (defaults for quiz/assign/attend)")
