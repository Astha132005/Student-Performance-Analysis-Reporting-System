from db import get_connection


def combine():

    conn = get_connection()
    cursor = conn.cursor(buffered=True)

    # ------------------------------
    # GET SUBJECT
    # ------------------------------
    cursor.execute(
        "SELECT subject_id FROM subjects WHERE subject_name=%s",
        ("OS",)
    )
    result = cursor.fetchone()

    if not result:
        print("❌ Subject not found")
        return

    subject_id = result[0]

    # ------------------------------
    # GET STUDENTS
    # ------------------------------
    cursor.execute("SELECT student_id FROM students")
    students = cursor.fetchall()

    count = 0

    # ------------------------------
    # FETCH FUNCTION (SAFE)
    # ------------------------------
    def fetch(table, student_id, subject_id):
        cursor.execute(f"""
            SELECT co1, co2, co3, co4, co5
            FROM {table}
            WHERE student_id=%s AND subject_id=%s
        """, (student_id, subject_id))

        res = cursor.fetchone()

        if not res:
            return (0, 0, 0, 0, 0)

        return tuple(x if x is not None else 0 for x in res)

    # ------------------------------
    # MAIN LOOP
    # ------------------------------
    for s in students:
        student_id = s[0]

        try:
            # ------------------------------
            # FETCH ALL COMPONENT DATA
            # ------------------------------
            mid = fetch("midsem", student_id, subject_id)
            quiz = fetch("quiz", student_id, subject_id)
            assign = fetch("assignment", student_id, subject_id)
            att = fetch("attendance", student_id, subject_id)

            # ------------------------------
            # COMPONENT TOTALS
            # ------------------------------
            midsem_total = sum(mid)          # out of 20
            quiz_total = sum(quiz)           # out of 5
            assignment_total = sum(assign)   # out of 10
            attendance_total = sum(att)      # out of 5

            # ------------------------------
            # FINAL COs (REAL AGGREGATION)
            # ------------------------------
            co1 = mid[0] + quiz[0] + assign[0] + att[0]
            co2 = mid[1] + quiz[1] + assign[1] + att[1]
            co3 = mid[2] + quiz[2] + assign[2] + att[2]
            co4 = mid[3] + quiz[3] + assign[3] + att[3]
            co5 = mid[4] + quiz[4] + assign[4] + att[4]

            # ------------------------------
            # TOTAL + PERCENTAGE
            # ------------------------------
            total = midsem_total + quiz_total + assignment_total + attendance_total
            percentage = (total / 40) * 100 if total else 0

            # ------------------------------
            # ATTAINMENT
            # ------------------------------
            if percentage >= 70:
                attainment = "High"
            elif percentage >= 40:
                attainment = "Medium"
            else:
                attainment = "Low"

            # ------------------------------
            # INSERT INTO MARKS
            # ------------------------------
            cursor.execute("""
                INSERT INTO marks (
                    student_id, subject_id,
                    midsem_total, quiz_total, assignment_total, attendance_total,
                    total, percentage,
                    co1, co2, co3, co4, co5,
                    attainment
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                student_id, subject_id,
                midsem_total, quiz_total, assignment_total, attendance_total,
                total, percentage,
                co1, co2, co3, co4, co5,
                attainment
            ))

            count += 1

        except Exception as e:
            print(f"⚠️ Error for student {student_id}: {e}")

    conn.commit()
    conn.close()

    print(f"✅ DONE: {count} rows inserted")


if __name__ == "__main__":
    combine()
