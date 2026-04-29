from flask import Flask, render_template, request, redirect, session, jsonify, flash
from db import get_connection
from io import BytesIO
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64

app = Flask(__name__)
app.secret_key = "secret123"


# ---------------- GRAPH ----------------
def generate_graph(values, title):
    if not values:
        return None
    plt.figure()
    plt.bar(['CO1','CO2','CO3','CO4','CO5'], values)
    plt.title(title)
    img = BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()


# ---------------- LOGIN ----------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s AND role=%s",
            (username, password, role)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user'] = username
            session['role'] = role
            session['full_name'] = user.get('full_name') or username
            session['subject_id'] = user.get('subject_id')

            if role == "admin":
                return redirect('/admin_dashboard')
            else:
                return redirect('/faculty_dashboard')

        return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')


# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as cnt FROM students")
    total_students = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(DISTINCT subject_id) as cnt FROM marks")
    total_subjects = cursor.fetchone()['cnt']

    cursor.execute("SELECT AVG(percentage) as avg FROM marks")
    avg_percentage = cursor.fetchone()['avg'] or 0

    # Top 5 / Bottom 5 Performers (student-level avg)
    top_performers = []
    bottom_performers = []
    try:
        cursor.execute("""
            SELECT s.reg_no, s.name, ROUND(AVG(m.percentage), 2) as avg_pct
            FROM students s
            JOIN marks m ON s.student_id = m.student_id
            GROUP BY s.student_id, s.reg_no, s.name
            ORDER BY avg_pct DESC
            LIMIT 5
        """)
        top_performers = cursor.fetchall()

        cursor.execute("""
            SELECT s.reg_no, s.name, ROUND(AVG(m.percentage), 2) as avg_pct
            FROM students s
            JOIN marks m ON s.student_id = m.student_id
            GROUP BY s.student_id, s.reg_no, s.name
            ORDER BY avg_pct ASC
            LIMIT 5
        """)
        bottom_performers = cursor.fetchall()
    except Exception:
        pass

    # Attainment distribution
    cursor.execute("SELECT percentage FROM marks")
    data = cursor.fetchall()

    # Batch stacked bar: component avg per batch per subject
    batch_lollipop = []
    try:
        cursor.execute("""
            SELECT sub.subject_name,
                AVG(CASE WHEN s.pass_year=2027 THEN m.percentage END)       as avg_2027,
                AVG(CASE WHEN s.pass_year=2028 THEN m.percentage END)       as avg_2028,
                AVG(CASE WHEN s.pass_year=2027 THEN m.midsem_total END)     as mid_2027,
                AVG(CASE WHEN s.pass_year=2027 THEN m.quiz_total END)       as quiz_2027,
                AVG(CASE WHEN s.pass_year=2027 THEN m.assignment_total END) as assign_2027,
                AVG(CASE WHEN s.pass_year=2027 THEN m.attendance_total END) as att_2027,
                AVG(CASE WHEN s.pass_year=2028 THEN m.midsem_total END)     as mid_2028,
                AVG(CASE WHEN s.pass_year=2028 THEN m.quiz_total END)       as quiz_2028,
                AVG(CASE WHEN s.pass_year=2028 THEN m.assignment_total END) as assign_2028,
                AVG(CASE WHEN s.pass_year=2028 THEN m.attendance_total END) as att_2028
            FROM marks m
            JOIN students s ON s.student_id = m.student_id
            JOIN subjects sub ON sub.subject_id = m.subject_id
            GROUP BY sub.subject_name
            ORDER BY sub.subject_name
        """)
        batch_lollipop = cursor.fetchall()
    except Exception:
        pass

    conn.close()

    low = medium = high = 0
    for row in data:
        p = row['percentage']
        if p < 40: low += 1
        elif 40 <= p <= 70: medium += 1
        else: high += 1

    chart_data = {'low': low, 'medium': medium, 'high': high}

    return render_template(
        'admin_dashboard.html',
        total_students=total_students,
        total_subjects=total_subjects,
        avg_percentage=round(avg_percentage, 2),
        chart_data=chart_data,
        top_performers=top_performers,
        bottom_performers=bottom_performers,
        batch_lollipop=batch_lollipop,
        role=session.get('role')
    )



# ---------------- SUBJECT ANALYSIS (ADMIN) ----------------
@app.route('/subject_analysis')
def subject_analysis():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    year = request.args.get('year')
    branch = request.args.get('branch')
    semester = request.args.get('semester')
    subject = request.args.get('subject')

    students = []
    low_scorers = []
    avg = 0
    weakest_co = None
    total_students = 0
    midsem_data = quiz_data = assignment_data = attendance_data = None

    if year and branch and semester and subject:
        cursor.execute("""
            SELECT m.id as marks_id, s.student_id, s.reg_no, s.name,
                   m.midsem_total, m.quiz_total, m.assignment_total, m.attendance_total,
                   m.percentage, m.co1, m.co2, m.co3, m.co4, m.co5
            FROM students s
            JOIN marks m ON s.student_id = m.student_id
            JOIN subjects sub ON m.subject_id = sub.subject_id
            WHERE s.pass_year=%s AND s.branch=%s AND s.semester=%s AND sub.subject_name=%s
        """, (year, branch, semester, subject))
        students = cursor.fetchall()

        if students:
            total_students = len(students)
            avg = round(sum(s['percentage'] for s in students) / total_students, 2)
            low_scorers = [
                {"name": s['name'], "midsem": s['midsem_total'], "marks_id": s['marks_id'], "student_id": s['student_id']}
                for s in students if (s['midsem_total'] / 20) * 100 < 30
            ]
            co_avg = [sum(s['co'+str(i)] for s in students)/total_students for i in range(1,6)]
            weakest_co = f"CO{co_avg.index(min(co_avg)) + 1}"

            # Weights used to redistribute flat CO distributions in component tables
            _MID_W    = [0.60, 0.40, 0.10, 0.15, 0.00]
            _QUIZ_W   = [0.30, 0.00, 0.70, 0.00, 0.20]
            _ASSIGN_W = [0.00, 0.25, 0.00, 0.75, 0.25]
            _ATT_W    = [0.00, 0.00, 0.50, 0.00, 0.50]

            def _apply_w(total, weights):
                s = sum(weights)
                if s == 0: return [0.0] * 5
                return [round(total * w / s, 3) for w in weights]

            def get_co_avg(table, total_field, weights):
                cursor.execute(f"""
                    SELECT AVG(co1) as co1, AVG(co2) as co2, AVG(co3) as co3,
                           AVG(co4) as co4, AVG(co5) as co5
                    FROM {table} t JOIN students s ON s.student_id = t.student_id
                    JOIN subjects sub ON t.subject_id = sub.subject_id
                    WHERE s.pass_year=%s AND s.branch=%s AND s.semester=%s AND sub.subject_name=%s
                """, (year, branch, semester, subject))
                r = cursor.fetchone()
                raw = [r['co1'] or 0, r['co2'] or 0, r['co3'] or 0, r['co4'] or 0, r['co5'] or 0]
                # If all CO values are identical (flat distribution bug), use weighted totals
                if len(set(round(v, 3) for v in raw)) == 1:
                    cursor.execute(f"""
                        SELECT AVG({total_field}) as total FROM marks m
                        JOIN students s ON s.student_id = m.student_id
                        JOIN subjects sub ON m.subject_id = sub.subject_id
                        WHERE s.pass_year=%s AND s.branch=%s AND s.semester=%s AND sub.subject_name=%s
                    """, (year, branch, semester, subject))
                    t = cursor.fetchone()
                    return _apply_w(t['total'] or 0 if t else 0, weights)
                return raw

            midsem_data     = get_co_avg('midsem',     'midsem_total',     _MID_W)
            quiz_data       = get_co_avg('quiz',       'quiz_total',       _QUIZ_W)
            assignment_data = get_co_avg('assignment', 'assignment_total', _ASSIGN_W)
            attendance_data = get_co_avg('attendance', 'attendance_total', _ATT_W)

    cursor.execute("SELECT DISTINCT pass_year FROM students")
    years = cursor.fetchall()
    cursor.execute("SELECT DISTINCT branch FROM students")
    branches = cursor.fetchall()
    cursor.execute("SELECT DISTINCT semester FROM students")
    semesters = cursor.fetchall()
    if semester and branch:
        cursor.execute("SELECT DISTINCT subject_name FROM subjects WHERE semester=%s AND branch=%s ORDER BY subject_name", (semester, branch))
    else:
        cursor.execute("SELECT DISTINCT subject_name FROM subjects ORDER BY subject_name")
    subjects = cursor.fetchall()
    conn.close()

    return render_template("subject_analysis.html",
        total_students=total_students, low_scorers=low_scorers, avg=avg, weakest_co=weakest_co,
        midsem_data=midsem_data, quiz_data=quiz_data, assignment_data=assignment_data, attendance_data=attendance_data,
        years=years, branches=branches, semesters=semesters, subjects=subjects, students=students,
        role=session.get('role'))


# ---------------- BATCH ANALYSIS (ADMIN) ----------------
@app.route('/batch_analysis')
def batch_analysis():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/')

    branch = request.args.get('branch')
    semester = request.args.get('semester')
    pass_year = request.args.get('year')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    subjects_data = []

    if branch and semester and pass_year:
        cursor.execute("SELECT sub.subject_id, sub.subject_name FROM subjects sub WHERE sub.semester=%s AND sub.branch=%s", (semester, branch))
        subjects = cursor.fetchall()

        for sub in subjects:
            subject_id = sub['subject_id']
            subject_name = sub['subject_name']

            cursor.execute("""
                SELECT AVG(m.co1) as co1, AVG(m.co2) as co2, AVG(m.co3) as co3, AVG(m.co4) as co4, AVG(m.co5) as co5
                FROM marks m JOIN students s ON s.student_id = m.student_id
                WHERE m.subject_id=%s AND s.branch=%s AND s.semester=%s AND s.pass_year=%s
            """, (subject_id, branch, semester, pass_year))
            co = cursor.fetchone()
            co_vals = [co['co1'] or 0, co['co2'] or 0, co['co3'] or 0, co['co4'] or 0, co['co5'] or 0]

            cursor.execute("""
                SELECT m.percentage FROM marks m JOIN students s ON s.student_id = m.student_id
                WHERE m.subject_id=%s AND s.branch=%s AND s.semester=%s AND s.pass_year=%s
            """, (subject_id, branch, semester, pass_year))
            data = cursor.fetchall()
            low = medium = high = 0
            for row in data:
                p = row['percentage']
                if p < 40: low += 1
                elif 40 <= p <= 70: medium += 1
                else: high += 1

            cursor.execute("""
                SELECT m.id as marks_id, s.student_id, s.reg_no, s.name, m.midsem_total
                FROM students s JOIN marks m ON s.student_id = m.student_id
                WHERE m.subject_id=%s AND s.branch=%s AND s.semester=%s AND s.pass_year=%s
            """, (subject_id, branch, semester, pass_year))
            all_students = cursor.fetchall()
            low_scorers = [s for s in all_students if (s['midsem_total'] / 20) * 100 < 30]

            subjects_data.append({
                "subject_name": subject_name, "co_vals": co_vals,
                "pie_data": {'low': low, 'medium': medium, 'high': high},
                "low_scorers": low_scorers, "total_students": len(all_students),
                "co_avgs": co_vals, "overall_avg": round(sum(co_vals) / len(co_vals), 2) if co_vals else 0
            })

    cursor.execute("SELECT DISTINCT pass_year FROM students ORDER BY pass_year")
    years = cursor.fetchall()
    cursor.execute("SELECT DISTINCT branch FROM students ORDER BY branch")
    branches = cursor.fetchall()
    cursor.execute("SELECT DISTINCT semester FROM students ORDER BY semester")
    semesters = cursor.fetchall()
    conn.close()

    return render_template("batch_analysis.html",
        subjects_data=subjects_data, years=years, branches=branches, semesters=semesters,
        role=session.get('role'))


# ---------------- STUDENT SEARCH ----------------
@app.route('/student')
def student_detail():
    if 'user' not in session:
        return redirect('/')
    if session.get('role') not in ('admin', 'faculty'):
        return "Unauthorized"

    search_query = request.args.get('search', '').strip()
    student_info = None
    subject_marks = []
    co_graph = None
    overall_percentage = 0
    error_msg = None
    co_data = None
    per_subject_intensity = []

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Faculty can only see their subject's marks
    faculty_subject_id = session.get('subject_id') if session.get('role') == 'faculty' else None

    if search_query:
        cursor.execute("SELECT student_id, reg_no, name, branch, semester, pass_year FROM students WHERE reg_no = %s", (search_query,))
        student_info = cursor.fetchone()

        if student_info:
            student_id = student_info['student_id']
            if faculty_subject_id:
                cursor.execute("""
                    SELECT m.id as marks_id, sub.subject_name,
                           m.co1, m.co2, m.co3, m.co4, m.co5, m.percentage, m.attainment,
                           m.midsem_total, m.quiz_total, m.assignment_total, m.attendance_total
                    FROM marks m JOIN subjects sub ON m.subject_id = sub.subject_id
                    WHERE m.student_id = %s AND m.subject_id = %s
                """, (student_id, faculty_subject_id))
            else:
                cursor.execute("""
                    SELECT m.id as marks_id, sub.subject_name,
                           m.co1, m.co2, m.co3, m.co4, m.co5, m.percentage, m.attainment,
                           m.midsem_total, m.quiz_total, m.assignment_total, m.attendance_total
                    FROM marks m JOIN subjects sub ON m.subject_id = sub.subject_id
                    WHERE m.student_id = %s
                """, (student_id,))
            subject_marks = cursor.fetchall()

            if subject_marks:
                avg_co = [
                    sum((s['co'+str(i)] or 0) for s in subject_marks) / len(subject_marks)
                    for i in range(1, 6)
                ]
                co_data = avg_co
                overall_percentage = round(sum((s['percentage'] or 0) for s in subject_marks) / len(subject_marks), 2)

                # Build per-subject intensity data using corrected marks-table CO values
                # The CO Attainment uses marks.co1-co5 (already properly distributed).
                # The Marks by Component stacked bar distributes each component's total
                # across CO1-CO5 using the same weighted scheme used in fix_co_distribution.py
                per_subject_intensity = []
                for sm in subject_marks:
                    sub_name = sm['subject_name']

                    # CO totals straight from the fixed marks table
                    co_totals = [round(sm['co'+str(i)] or 0, 2) for i in range(1, 6)]

                    mid   = sm['midsem_total']    or 0   # out of 20
                    quiz  = sm['quiz_total']       or 0   # out of 5
                    assign= sm['assignment_total'] or 0   # out of 10
                    att   = sm['attendance_total'] or 0   # out of 5

                    def _distribute(total, weights):
                        """Distribute `total` across 5 COs using weights (sum need not be 1)."""
                        s = sum(weights)
                        if s == 0:
                            return [round(total / 5, 2)] * 5
                        return [round(total * w / s, 2) for w in weights]

                    # Same weights as fix_co_distribution.py
                    # CO1 ← midsem-heavy, CO2 ← midsem+assign, CO3 ← quiz+att, CO4 ← assign, CO5 ← att
                    mid_w   = [0.60, 0.40, 0.10, 0.15, 0.00]  # midsem weights per CO
                    quiz_w  = [0.30, 0.00, 0.70, 0.00, 0.20]  # quiz weights per CO
                    assign_w= [0.00, 0.25, 0.00, 0.75, 0.25]  # assignment weights per CO
                    att_w   = [0.00, 0.00, 0.50, 0.00, 0.50]  # attendance weights per CO

                    comp_data = {
                        'Mid Sem':    {'values': _distribute(mid,    mid_w),    'max': 20},
                        'Quiz':       {'values': _distribute(quiz,   quiz_w),   'max': 5},
                        'Assignment': {'values': _distribute(assign, assign_w), 'max': 10},
                        'Attendance': {'values': _distribute(att,    att_w),    'max': 5},
                    }

                    per_subject_intensity.append({
                        'subject_name': sub_name,
                        'components':   comp_data,
                        'totals':       co_totals,   # from fixed marks table
                        'percentage':   sm['percentage'],
                        'attainment':   sm['attainment']
                    })
            else:
                error_msg = "No marks found for this student."
        else:
            error_msg = "No student found with that Registration Number."

    conn.close()

    return render_template("student.html",
        student=student_info, marks=subject_marks, co_data=co_data,
        overall_percentage=overall_percentage, error_msg=error_msg,
        search_query=search_query, role=session.get('role'),
        per_subject_intensity=per_subject_intensity)


# ================================================================
# FACULTY ROUTES
# ================================================================

# ---------------- FACULTY DASHBOARD ----------------
@app.route('/faculty_dashboard')
def faculty_main_dashboard():
    if 'user' not in session or session.get('role') != 'faculty':
        return redirect('/')

    subject_id = session.get('subject_id')
    full_name = session.get('full_name', session.get('user'))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get subject name
    subject_name = 'Unknown'
    if subject_id:
        cursor.execute("SELECT subject_name FROM subjects WHERE subject_id=%s", (subject_id,))
        sub = cursor.fetchone()
        if sub:
            subject_name = sub['subject_name']

    # Stats for THIS subject only
    cursor.execute("""
        SELECT COUNT(DISTINCT m.student_id) as cnt FROM marks m WHERE m.subject_id=%s
    """, (subject_id,))
    total_students = cursor.fetchone()['cnt'] or 0

    cursor.execute("SELECT AVG(percentage) as avg FROM marks WHERE subject_id=%s", (subject_id,))
    avg_percentage = cursor.fetchone()['avg'] or 0

    # Top 5 for this subject
    cursor.execute("""
        SELECT s.reg_no, s.name, ROUND(m.percentage, 2) as avg_pct
        FROM students s JOIN marks m ON s.student_id = m.student_id
        WHERE m.subject_id=%s ORDER BY m.percentage DESC LIMIT 5
    """, (subject_id,))
    top_performers = cursor.fetchall()

    # Bottom 5 for this subject
    cursor.execute("""
        SELECT s.reg_no, s.name, ROUND(m.percentage, 2) as avg_pct
        FROM students s JOIN marks m ON s.student_id = m.student_id
        WHERE m.subject_id=%s ORDER BY m.percentage ASC LIMIT 5
    """, (subject_id,))
    bottom_performers = cursor.fetchall()

    # Attainment distribution for this subject
    cursor.execute("SELECT percentage FROM marks WHERE subject_id=%s", (subject_id,))
    data = cursor.fetchall()
    conn.close()

    low = medium = high = 0
    for row in data:
        p = row['percentage']
        if p < 40: low += 1
        elif 40 <= p <= 70: medium += 1
        else: high += 1

    chart_data = {'low': low, 'medium': medium, 'high': high}

    return render_template('faculty_dashboard.html',
        total_students=total_students,
        total_subjects=1,
        avg_percentage=round(avg_percentage, 2),
        chart_data=chart_data,
        top_performers=top_performers,
        bottom_performers=bottom_performers,
        subject_name=subject_name,
        full_name=full_name)


# ---------------- FACULTY OVERALL ANALYSIS ----------------
@app.route('/faculty/subject_analysis')
def faculty_subject_analysis():
    if 'user' not in session or session.get('role') != 'faculty':
        return redirect('/')

    subject_id = session.get('subject_id')
    full_name = session.get('full_name', session.get('user'))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Subject name
    cursor.execute("SELECT subject_name, semester, branch FROM subjects WHERE subject_id=%s", (subject_id,))
    sub = cursor.fetchone()
    subject_name = sub['subject_name'] if sub else ''
    semester = sub['semester'] if sub else ''
    branch = sub['branch'] if sub else ''

    # All students marks for this subject
    cursor.execute("""
        SELECT m.id as marks_id, s.student_id, s.reg_no, s.name,
               m.midsem_total, m.quiz_total, m.assignment_total, m.attendance_total,
               m.percentage, m.co1, m.co2, m.co3, m.co4, m.co5
        FROM students s JOIN marks m ON s.student_id = m.student_id
        WHERE m.subject_id=%s
        ORDER BY m.percentage DESC
    """, (subject_id,))
    students = cursor.fetchall()

    total_students = len(students)
    avg = round(sum(s['percentage'] for s in students) / total_students, 2) if students else 0
    weakest_co = None
    low_scorers = []
    midsem_data = quiz_data = assignment_data = attendance_data = None

    if students:
        co_avg = [sum(s['co'+str(i)] or 0 for s in students)/total_students for i in range(1,6)]
        weakest_co = f"CO{co_avg.index(min(co_avg)) + 1}"
        low_scorers = [
            {"name": s['name'], "midsem": s['midsem_total'], "marks_id": s['marks_id'], "student_id": s['student_id']}
            for s in students if (s['midsem_total'] / 20) * 100 < 30
        ]

        _MID_W    = [0.60, 0.40, 0.10, 0.15, 0.00]
        _QUIZ_W   = [0.30, 0.00, 0.70, 0.00, 0.20]
        _ASSIGN_W = [0.00, 0.25, 0.00, 0.75, 0.25]
        _ATT_W    = [0.00, 0.00, 0.50, 0.00, 0.50]

        def _apply_w(total, weights):
            s = sum(weights)
            if s == 0: return [0.0] * 5
            return [round(total * w / s, 3) for w in weights]

        def get_co(table, total_field, weights):
            cursor.execute(f"""
                SELECT AVG(co1) as co1, AVG(co2) as co2, AVG(co3) as co3,
                       AVG(co4) as co4, AVG(co5) as co5
                FROM {table} WHERE subject_id=%s
            """, (subject_id,))
            r = cursor.fetchone()
            raw = [r['co1'] or 0, r['co2'] or 0, r['co3'] or 0, r['co4'] or 0, r['co5'] or 0]
            if len(set(round(v, 3) for v in raw)) == 1:
                cursor.execute(f"""
                    SELECT AVG({total_field}) as total FROM marks WHERE subject_id=%s
                """, (subject_id,))
                t = cursor.fetchone()
                return _apply_w(t['total'] or 0 if t else 0, weights)
            return raw

        midsem_data     = get_co('midsem',     'midsem_total',     _MID_W)
        quiz_data       = get_co('quiz',       'quiz_total',       _QUIZ_W)
        assignment_data = get_co('assignment', 'assignment_total', _ASSIGN_W)
        attendance_data = get_co('attendance', 'attendance_total', _ATT_W)


    conn.close()

    return render_template("faculty_subject_analysis.html",
        total_students=total_students, low_scorers=low_scorers, avg=avg, weakest_co=weakest_co,
        midsem_data=midsem_data, quiz_data=quiz_data, assignment_data=assignment_data, attendance_data=attendance_data,
        students=students, subject_name=subject_name, full_name=full_name)


# ---------------- FACULTY MARKS ENTRY ----------------
@app.route('/faculty/marks_entry', methods=['GET', 'POST'])
def faculty_marks_entry():
    if 'user' not in session or session.get('role') != 'faculty':
        return redirect('/')

    subject_id = session.get('subject_id')
    full_name = session.get('full_name', session.get('user'))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT subject_name FROM subjects WHERE subject_id=%s", (subject_id,))
    sub = cursor.fetchone()
    subject_name = sub['subject_name'] if sub else ''

    message = None
    msg_type = None
    analysis_student = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'save_marks':
            student_id = request.form.get('student_id')
            try:
                midsem = min(float(request.form.get('midsem', 0) or 0), 20)
                quiz = min(float(request.form.get('quiz', 0) or 0), 5)
                assignment = min(float(request.form.get('assignment', 0) or 0), 10)
                attendance = min(float(request.form.get('attendance', 0) or 0), 5)
                total = midsem + quiz + assignment + attendance
                percentage = round((total / 40) * 100, 2)
                attainment = 'High' if percentage >= 70 else ('Medium' if percentage >= 40 else 'Low')
                co_each = round((midsem / 20) * 100 / 5, 2) if midsem > 0 else 0

                # Check existing
                cursor.execute("SELECT id FROM marks WHERE student_id=%s AND subject_id=%s", (student_id, subject_id))
                existing = cursor.fetchone()
                if existing:
                    cursor.execute("""
                        UPDATE marks SET midsem_total=%s, quiz_total=%s, assignment_total=%s,
                        attendance_total=%s, total=%s, percentage=%s, attainment=%s,
                        co1=%s, co2=%s, co3=%s, co4=%s, co5=%s
                        WHERE student_id=%s AND subject_id=%s
                    """, (midsem, quiz, assignment, attendance, total, percentage, attainment,
                          co_each, co_each, co_each, co_each, co_each, student_id, subject_id))
                else:
                    cursor.execute("""
                        INSERT INTO marks (student_id, subject_id, midsem_total, quiz_total,
                        assignment_total, attendance_total, total, percentage, attainment, co1, co2, co3, co4, co5)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (student_id, subject_id, midsem, quiz, assignment, attendance,
                          total, percentage, attainment, co_each, co_each, co_each, co_each, co_each))
                conn.commit()
                message = f"Marks saved for student. Total: {total}/40 ({percentage}%) - {attainment}"
                msg_type = 'success'

                # Return analysis for this student
                cursor.execute("""
                    SELECT s.name, s.reg_no, m.midsem_total, m.quiz_total, m.assignment_total,
                    m.attendance_total, m.total, m.percentage, m.attainment, m.co1, m.co2, m.co3, m.co4, m.co5
                    FROM students s JOIN marks m ON s.student_id = m.student_id
                    WHERE m.student_id=%s AND m.subject_id=%s
                """, (student_id, subject_id))
                analysis_student = cursor.fetchone()

            except Exception as e:
                message = f"Error saving marks: {str(e)}"
                msg_type = 'error'

    # Get search query
    search = request.args.get('search', '').strip()
    searched_student = None
    student_marks = None

    if search:
        cursor.execute("SELECT student_id, name, reg_no, branch, semester FROM students WHERE reg_no=%s OR name LIKE %s", (search, f'%{search}%'))
        searched_student = cursor.fetchone()
        if searched_student:
            cursor.execute("""
                SELECT midsem_total, quiz_total, assignment_total, attendance_total,
                       total, percentage, attainment, co1, co2, co3, co4, co5
                FROM marks WHERE student_id=%s AND subject_id=%s
            """, (searched_student['student_id'], subject_id))
            student_marks = cursor.fetchone()

    # All students for this subject (for table)
    cursor.execute("""
        SELECT s.student_id, s.name, s.reg_no,
               m.midsem_total, m.quiz_total, m.assignment_total, m.attendance_total,
               m.total, m.percentage, m.attainment
        FROM students s
        LEFT JOIN marks m ON s.student_id = m.student_id AND m.subject_id=%s
        WHERE s.semester = (SELECT semester FROM subjects WHERE subject_id=%s)
        AND s.branch = (SELECT branch FROM subjects WHERE subject_id=%s)
        ORDER BY s.name
    """, (subject_id, subject_id, subject_id))
    all_students = cursor.fetchall()

    conn.close()

    return render_template('faculty_marks_entry.html',
        subject_name=subject_name, subject_id=subject_id,
        all_students=all_students, search=search,
        searched_student=searched_student, student_marks=student_marks,
        analysis_student=analysis_student,
        message=message, msg_type=msg_type,
        full_name=full_name)


# ================================================================
# ADMIN CRUD — TEACHERS
# ================================================================
@app.route('/admin/teachers')
def admin_teachers():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.id, u.username, u.password, u.full_name, u.role, u.subject_id,
               s.subject_name
        FROM users u
        LEFT JOIN subjects s ON u.subject_id = s.subject_id
        WHERE u.role = 'faculty'
        ORDER BY u.full_name
    """)
    teachers = cursor.fetchall()

    cursor.execute("SELECT subject_id, subject_name FROM subjects ORDER BY subject_name")
    subjects = cursor.fetchall()

    conn.close()
    return render_template('admin_teachers.html', teachers=teachers, subjects=subjects, role='admin')


@app.route('/admin/teachers/add', methods=['POST'])
def admin_add_teacher():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/')

    username         = request.form.get('username', '').strip()
    password         = request.form.get('password', '').strip()
    full_name        = request.form.get('full_name', '').strip()
    subject_id       = request.form.get('subject_id') or None
    new_subject_name = request.form.get('new_subject_name', '').strip()

    if not username or not password:
        flash('Username and password are required.', 'error')
        return redirect('/admin/teachers')

    conn   = get_connection()
    cursor = conn.cursor()
    try:
        # If admin typed a brand-new subject name, create it first
        if new_subject_name:
            cursor.execute(
                "INSERT INTO subjects (subject_name) VALUES (%s)",
                (new_subject_name.upper(),)
            )
            subject_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO users (username, password, role, full_name, subject_id) VALUES (%s,%s,'faculty',%s,%s)",
            (username, password, full_name, subject_id)
        )
        conn.commit()
        if new_subject_name:
            flash(f'Subject "{new_subject_name.upper()}" created and teacher {full_name or username} added.', 'success')
        else:
            flash(f'Teacher {full_name or username} added successfully.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect('/admin/teachers')



@app.route('/admin/teachers/edit/<int:teacher_id>', methods=['POST'])
def admin_edit_teacher(teacher_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/')

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    full_name = request.form.get('full_name', '').strip()
    subject_id = request.form.get('subject_id') or None

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET username=%s, password=%s, full_name=%s, subject_id=%s WHERE id=%s AND role='faculty'",
            (username, password, full_name, subject_id, teacher_id)
        )
        conn.commit()
        flash('Teacher updated successfully.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect('/admin/teachers')


@app.route('/admin/teachers/delete/<int:teacher_id>', methods=['POST'])
def admin_delete_teacher(teacher_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id=%s AND role='faculty'", (teacher_id,))
        conn.commit()
        flash('Teacher deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect('/admin/teachers')


# ================================================================
# ADMIN CRUD — STUDENTS
# ================================================================
@app.route('/admin/students')
def admin_students():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/')

    search        = request.args.get('search', '').strip()
    filter_batch  = request.args.get('batch', '').strip()
    filter_att    = request.args.get('attainment', '').strip()
    filter_subj   = request.args.get('subject', '').strip()
    sort_by       = request.args.get('sort', 'name_az').strip()
    name_filter   = request.args.get('name_filter', '').strip()

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Base query enriched with avg score and subjects
    base_q = """
        SELECT s.student_id, s.name, s.reg_no, s.branch, s.semester, s.pass_year,
               ROUND(AVG(m.percentage), 1) as avg_score,
               GROUP_CONCAT(DISTINCT sub.subject_name ORDER BY sub.subject_name SEPARATOR ', ') as subjects
        FROM students s
        LEFT JOIN marks m ON s.student_id = m.student_id
        LEFT JOIN subjects sub ON m.subject_id = sub.subject_id
    """
    wheres = []
    params = []

    if search:
        wheres.append("(s.name LIKE %s OR s.reg_no LIKE %s)")
        params += [f'%{search}%', f'%{search}%']
    if name_filter:
        wheres.append("s.name LIKE %s")
        params.append(f'%{name_filter}%')
    if filter_batch:
        wheres.append("s.pass_year = %s")
        params.append(filter_batch)
    if filter_subj:
        wheres.append("EXISTS (SELECT 1 FROM marks mx JOIN subjects sx ON mx.subject_id=sx.subject_id WHERE mx.student_id=s.student_id AND sx.subject_name=%s)")
        params.append(filter_subj)

    if wheres:
        base_q += " WHERE " + " AND ".join(wheres)

    base_q += " GROUP BY s.student_id, s.name, s.reg_no, s.branch, s.semester, s.pass_year"

    # Apply attainment filter on the aggregated avg
    if filter_att == 'High':
        base_q += " HAVING avg_score >= 70"
    elif filter_att == 'Medium':
        base_q += " HAVING avg_score >= 40 AND avg_score < 70"
    elif filter_att == 'Low':
        base_q += " HAVING avg_score < 40 OR avg_score IS NULL"

    sort_map = {
        'name_az':    'ORDER BY s.name ASC',
        'name_za':    'ORDER BY s.name DESC',
        'batch_asc':  'ORDER BY s.pass_year ASC, s.name ASC',
        'batch_desc': 'ORDER BY s.pass_year DESC, s.name ASC',
        'score_high': 'ORDER BY avg_score DESC',
        'score_low':  'ORDER BY avg_score ASC',
    }
    base_q += " " + sort_map.get(sort_by, 'ORDER BY s.name ASC')
    base_q += " LIMIT 300"

    cursor.execute(base_q, params)
    students_raw = cursor.fetchall()

    # Attach computed attainment label
    students = []
    for s in students_raw:
        avg = s['avg_score']
        if avg is None:
            att = 'N/A'
        elif avg >= 70:
            att = 'High'
        elif avg >= 40:
            att = 'Medium'
        else:
            att = 'Low'
        s['attainment'] = att
        students.append(s)

    cursor.execute("SELECT COUNT(*) as cnt FROM students")
    total = cursor.fetchone()['cnt']

    cursor.execute("SELECT DISTINCT pass_year FROM students ORDER BY pass_year")
    all_batches = [r['pass_year'] for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT subject_name FROM subjects ORDER BY subject_name")
    all_subjects = [r['subject_name'] for r in cursor.fetchall()]

    conn.close()
    return render_template('admin_students.html',
        students=students, search=search, total=total, role='admin',
        filter_batch=filter_batch, filter_att=filter_att, filter_subj=filter_subj,
        sort_by=sort_by, name_filter=name_filter,
        all_batches=all_batches, all_subjects=all_subjects)


@app.route('/admin/students/add', methods=['POST'])
def admin_add_student():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/')

    name = request.form.get('name', '').strip().upper()
    reg_no = request.form.get('reg_no', '').strip()
    branch = request.form.get('branch', '').strip()
    semester = request.form.get('semester', '').strip()
    pass_year = request.form.get('pass_year', '').strip()

    if not (name and reg_no and branch and semester and pass_year):
        flash('All fields are required.', 'error')
        return redirect('/admin/students')

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO students (name, reg_no, branch, semester, pass_year) VALUES (%s,%s,%s,%s,%s)",
            (name, reg_no, branch, int(semester), int(pass_year))
        )
        conn.commit()
        flash(f'Student {name} ({reg_no}) added successfully.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect('/admin/students')


@app.route('/admin/students/edit/<int:student_id>', methods=['POST'])
def admin_edit_student(student_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/')

    name = request.form.get('name', '').strip().upper()
    reg_no = request.form.get('reg_no', '').strip()
    branch = request.form.get('branch', '').strip()
    semester = request.form.get('semester', '').strip()
    pass_year = request.form.get('pass_year', '').strip()

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE students SET name=%s, reg_no=%s, branch=%s, semester=%s, pass_year=%s WHERE student_id=%s",
            (name, reg_no, branch, int(semester), int(pass_year), student_id)
        )
        conn.commit()
        flash('Student updated successfully.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect('/admin/students')


@app.route('/admin/students/delete/<int:student_id>', methods=['POST'])
def admin_delete_student(student_id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Delete marks first (cascade)
        cursor.execute("DELETE FROM marks WHERE student_id=%s", (student_id,))
        cursor.execute("DELETE FROM midsem WHERE student_id=%s", (student_id,))
        cursor.execute("DELETE FROM quiz WHERE student_id=%s", (student_id,))
        cursor.execute("DELETE FROM assignment WHERE student_id=%s", (student_id,))
        cursor.execute("DELETE FROM attendance WHERE student_id=%s", (student_id,))
        cursor.execute("DELETE FROM students WHERE student_id=%s", (student_id,))
        conn.commit()
        flash('Student and all associated marks deleted.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect('/admin/students')


# ================================================================
# MARKS ENTRY (ADMIN — file upload based)
# ================================================================
@app.route('/marks_entry', methods=['GET', 'POST'])
def marks_entry():
    if 'user' not in session or session.get('role') not in ('admin', 'faculty'):
        return redirect('/')

    # Faculty goes to their own marks entry page
    if session.get('role') == 'faculty':
        return redirect('/faculty/marks_entry')

    branch_filter = request.args.get('branch')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    message = None
    msg_type = None

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'set_permission':
            start = request.form.get('start_time')
            end = request.form.get('end_time')
            try:
                start_dt = datetime.strptime(start, '%Y-%m-%dT%H:%M')
                end_dt = datetime.strptime(end, '%Y-%m-%dT%H:%M')
                if end_dt <= start_dt:
                    message = 'End time must be after start time'
                    msg_type = 'error'
                else:
                    cursor.execute("""
                        INSERT INTO marks_permission (id, start_time, end_time, is_active)
                        VALUES (1, %s, %s, 1)
                        ON DUPLICATE KEY UPDATE start_time=%s, end_time=%s, is_active=1
                    """, (start_dt, end_dt, start_dt, end_dt))
                    conn.commit()
                    message = f'Permission window set: {start} to {end}'
                    msg_type = 'success'
            except Exception as e:
                message = f'Error: {str(e)}'
                msg_type = 'error'
        elif action == 'deactivate':
            cursor.execute("UPDATE marks_permission SET is_active=0 WHERE id=1")
            conn.commit()
            message = 'Permission deactivated'
            msg_type = 'success'

    cursor.execute("SELECT * FROM marks_permission WHERE id=1")
    permission = cursor.fetchone()
    is_live = False
    if permission and permission['is_active']:
        now = datetime.now()
        if permission['start_time'] <= now <= permission['end_time']:
            is_live = True
        elif now > permission['end_time']:
            cursor.execute("UPDATE marks_permission SET is_active=0 WHERE id=1")
            conn.commit()
            permission['is_active'] = 0

    status_query = """
        SELECT sub.subject_name, sub.subject_id, sub.branch,
               us_mid.uploaded_at as midsem_at, us_quiz.uploaded_at as quiz_at,
               us_assign.uploaded_at as assignment_at, us_att.uploaded_at as attendance_at,
               COALESCE(us_mid.combined, 0) as combined
        FROM subjects sub
        LEFT JOIN upload_status us_mid ON sub.subject_id=us_mid.subject_id AND us_mid.component='midsem'
        LEFT JOIN upload_status us_quiz ON sub.subject_id=us_quiz.subject_id AND us_quiz.component='quiz'
        LEFT JOIN upload_status us_assign ON sub.subject_id=us_assign.subject_id AND us_assign.component='assignment'
        LEFT JOIN upload_status us_att ON sub.subject_id=us_att.subject_id AND us_att.component='attendance'
    """
    if branch_filter:
        status_query += " WHERE sub.branch = %s"
        cursor.execute(status_query, (branch_filter,))
    else:
        cursor.execute(status_query)
    subjects_status = cursor.fetchall()

    cursor.execute("SELECT DISTINCT branch FROM subjects WHERE branch IS NOT NULL ORDER BY branch")
    all_branches = cursor.fetchall()

    if branch_filter:
        cursor.execute("SELECT DISTINCT subject_name FROM subjects WHERE branch = %s ORDER BY subject_name", (branch_filter,))
    else:
        cursor.execute("SELECT DISTINCT subject_name FROM subjects ORDER BY subject_name")
    subject_list = cursor.fetchall()
    conn.close()

    return render_template('marks_entry.html',
        permission=permission, is_live=is_live,
        subjects_status=subjects_status, subject_list=subject_list,
        all_branches=all_branches, branch_filter=branch_filter,
        message=message, msg_type=msg_type, role=session.get('role'))


# ---------------- FACULTY UPLOAD ----------------
@app.route('/faculty_upload', methods=['POST'])
def faculty_upload():
    if 'user' not in session or session.get('role') != 'faculty':
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT start_time, end_time, is_active FROM marks_permission WHERE id=1")
    perm = cursor.fetchone()
    conn.close()

    if not perm or not perm['is_active']:
        flash('Upload permission is not active', 'error')
        return redirect('/faculty/marks_entry')

    now = datetime.now()
    if now < perm['start_time'] or now > perm['end_time']:
        flash('Upload window has expired', 'error')
        return redirect('/faculty/marks_entry')

    component = request.form.get('component')
    file = request.files.get('file')
    subject_name = request.form.get('subject_name')

    if not subject_name:
        flash('Please select a subject', 'error')
        return redirect('/faculty/marks_entry')
    if not file or not file.filename.endswith('.xlsx'):
        flash('Please upload a valid .xlsx file', 'error')
        return redirect('/faculty/marks_entry')
    if component not in ('midsem', 'quiz', 'assignment', 'attendance'):
        flash('Invalid component type', 'error')
        return redirect('/faculty/marks_entry')

    from upload_handler import upload_component
    result = upload_component(file, component, subject_name)

    if result['success']:
        msg = f"{component.upper()} uploaded: {result['count']} rows inserted"
        if result['skipped'] > 0:
            msg += f", {result['skipped']} skipped"
        flash(msg, 'success')
    else:
        flash(f"{component.upper()} upload failed: " + "; ".join(result['errors'][:5]), 'error')

    return redirect('/faculty/marks_entry')


# ---------------- API: UPDATE FIELD ----------------
@app.route('/api/update', methods=['POST'])
def api_update():
    if session.get('role') != 'admin':
        return jsonify(success=False, error="Unauthorized"), 403

    ALLOWED = {
        'marks': {'co1','co2','co3','co4','co5','midsem_total','quiz_total','assignment_total','attendance_total','percentage','attainment','total'},
        'students': {'name','reg_no','branch','semester','pass_year'},
        'midsem': {'co1','co2','co3','co4','co5'},
        'quiz': {'co1','co2','co3','co4','co5'},
        'assignment': {'co1','co2','co3','co4','co5'},
        'attendance': {'co1','co2','co3','co4','co5'},
        'subjects': {'subject_name','semester'},
    }
    PK = {'marks':'id','students':'student_id','midsem':'id','quiz':'id','assignment':'id','attendance':'id','subjects':'subject_id'}

    data = request.get_json()
    table = data.get('table')
    field = data.get('field')
    row_id = data.get('id')
    value = data.get('value')

    if table not in ALLOWED or field not in ALLOWED[table]:
        return jsonify(success=False, error="Invalid table or field"), 400

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        pk = PK[table]
        cursor.execute(f"UPDATE {table} SET {field} = %s WHERE {pk} = %s", (value, row_id))

        recalculated = None
        if table == 'marks' and field in ('midsem_total','quiz_total','assignment_total','attendance_total'):
            cursor.execute("SELECT midsem_total, quiz_total, assignment_total, attendance_total FROM marks WHERE id = %s", (row_id,))
            row = cursor.fetchone()
            total = sum((row[k] or 0) for k in ('midsem_total','quiz_total','assignment_total','attendance_total'))
            percentage = round((total / 40) * 100, 2)
            attainment = 'High' if percentage >= 70 else ('Medium' if percentage >= 40 else 'Low')
            cursor.execute("UPDATE marks SET total=%s, percentage=%s, attainment=%s WHERE id=%s", (total, percentage, attainment, row_id))
            recalculated = {'total': total, 'percentage': percentage, 'attainment': attainment}

        conn.commit()
        conn.close()
        return jsonify(success=True, recalculated=recalculated)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)