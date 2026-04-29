from db import get_connection


def auto_combine(subject_name):
    """
    Combine all 4 component COs into the marks table for the given subject.
    Returns dict with 'success', 'count', 'errors'.
    """

    conn = get_connection()
    cursor = conn.cursor(buffered=True)

    # ---- GET SUBJECT ----
    cursor.execute("SELECT subject_id FROM subjects WHERE subject_name=%s", (subject_name,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return {"success": False, "count": 0, "errors": [f"Subject '{subject_name}' not found"]}

    subject_id = result[0]

    # ---- GET STUDENTS WITH DATA FOR THIS SUBJECT ----
    cursor.execute("""
        SELECT DISTINCT s.student_id
        FROM students s
        WHERE EXISTS (SELECT 1 FROM midsem WHERE student_id=s.student_id AND subject_id=%s)
           OR EXISTS (SELECT 1 FROM quiz WHERE student_id=s.student_id AND subject_id=%s)
           OR EXISTS (SELECT 1 FROM assignment WHERE student_id=s.student_id AND subject_id=%s)
           OR EXISTS (SELECT 1 FROM attendance WHERE student_id=s.student_id AND subject_id=%s)
    """, (subject_id, subject_id, subject_id, subject_id))

    students = cursor.fetchall()
    count = 0
    errors = []

    def fetch(table, student_id):
        cursor.execute(f"""
            SELECT co1, co2, co3, co4, co5
            FROM {table}
            WHERE student_id=%s AND subject_id=%s
        """, (student_id, subject_id))

        res = cursor.fetchone()
        if not res:
            return (0, 0, 0, 0, 0)
        return tuple(x if x is not None else 0 for x in res)

    for s in students:
        student_id = s[0]

        try:
            mid = fetch("midsem", student_id)
            quiz = fetch("quiz", student_id)
            assign = fetch("assignment", student_id)
            att = fetch("attendance", student_id)

            midsem_total = sum(mid)
            quiz_total = sum(quiz)
            assignment_total = sum(assign)
            attendance_total = sum(att)

            co1 = mid[0] + quiz[0] + assign[0] + att[0]
            co2 = mid[1] + quiz[1] + assign[1] + att[1]
            co3 = mid[2] + quiz[2] + assign[2] + att[2]
            co4 = mid[3] + quiz[3] + assign[3] + att[3]
            co5 = mid[4] + quiz[4] + assign[4] + att[4]

            total = midsem_total + quiz_total + assignment_total + attendance_total
            percentage = round((total / 40) * 100, 2) if total else 0

            if percentage >= 70:
                attainment = "High"
            elif percentage >= 40:
                attainment = "Medium"
            else:
                attainment = "Low"

            cursor.execute("""
                INSERT INTO marks (
                    student_id, subject_id,
                    midsem_total, quiz_total, assignment_total, attendance_total,
                    total, percentage,
                    co1, co2, co3, co4, co5,
                    attainment
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                    midsem_total=VALUES(midsem_total),
                    quiz_total=VALUES(quiz_total),
                    assignment_total=VALUES(assignment_total),
                    attendance_total=VALUES(attendance_total),
                    total=VALUES(total),
                    percentage=VALUES(percentage),
                    co1=VALUES(co1), co2=VALUES(co2), co3=VALUES(co3),
                    co4=VALUES(co4), co5=VALUES(co5),
                    attainment=VALUES(attainment)
            """, (
                student_id, subject_id,
                midsem_total, quiz_total, assignment_total, attendance_total,
                total, percentage,
                co1, co2, co3, co4, co5,
                attainment
            ))

            count += 1

        except Exception as e:
            errors.append(f"Student {student_id}: {str(e)}")

    # Mark as combined in upload_status
    cursor.execute("""
        UPDATE upload_status SET combined=1
        WHERE subject_id=%s
    """, (subject_id,))

    conn.commit()
    conn.close()

    return {"success": True, "count": count, "errors": errors}
