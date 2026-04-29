"""
Fix CO distribution for 2028 batch subjects (OOPS, DAA, DAI)
where all CO1-CO5 currently have identical values.

New distribution strategy:
  CO1 = midsem contribution (scale to 10)
  CO2 = midsem contribution scaled differently (slightly different weight)
  CO3 = quiz contribution (scale to 5)
  CO4 = assignment contribution (scale to 10)
  CO5 = attendance contribution (scale to 5)

This preserves the total marks while making each CO represent
a distinct aspect of student performance.
"""

import sys
sys.path.insert(0, 'e:/PPD/SPARS')
from db import get_connection

SUBJECTS_TO_FIX = ['OOPS', 'DAA', 'DAI']

# CO distribution weights (sum = 40 total marks)
# midsem=20, quiz=5, assignment=10, attendance=5
# CO1: primarily midsem (first half)
# CO2: midsem (second half, slightly different scaling)
# CO3: quiz-heavy + some midsem
# CO4: assignment
# CO5: attendance + quiz

def fix_co_distribution():
    conn = get_connection()
    cursor = conn.cursor(buffered=True)
    cursor2 = conn.cursor(dictionary=True)

    for subj_name in SUBJECTS_TO_FIX:
        cursor.execute("SELECT subject_id FROM subjects WHERE subject_name=%s", (subj_name,))
        res = cursor.fetchone()
        if not res:
            print(f"Subject {subj_name} not found, skipping.")
            continue
        subject_id = res[0]

        # Fetch all marks rows for this subject 2028
        cursor2.execute("""
            SELECT m.id, m.student_id, 
                   m.midsem_total, m.quiz_total, m.assignment_total, m.attendance_total
            FROM marks m
            JOIN students s ON s.student_id = m.student_id
            WHERE m.subject_id = %s AND s.pass_year = 2028
        """, (subject_id,))
        rows = cursor2.fetchall()

        count = 0
        for row in rows:
            mid = row['midsem_total'] or 0      # out of 20
            quiz = row['quiz_total'] or 0        # out of 5
            assign = row['assignment_total'] or 0 # out of 10
            att = row['attendance_total'] or 0   # out of 5

            # Allocate each CO differently:
            # CO1: heavy midsem (60% midsem + 10% quiz)
            co1 = round(mid * 0.60 + quiz * 0.30, 3)

            # CO2: midsem (remaining 40% midsem + some assignment)
            co2 = round(mid * 0.40 + assign * 0.25, 3)

            # CO3: quiz dominant + some attendance
            co3 = round(quiz * 0.70 + att * 0.50 + mid * 0.10, 3)

            # CO4: assignment dominant
            co4 = round(assign * 0.75 + mid * 0.15, 3)

            # CO5: attendance + rest
            co5 = round(att * 0.50 + assign * 0.25 + quiz * 0.20, 3)

            # Scale to match max possible: CO1 max ~ 0.6*20+0.3*5=13.5, etc.
            # Normalize so sum(co1..co5) ~= total
            total = mid + quiz + assign + att
            co_sum = co1 + co2 + co3 + co4 + co5
            if co_sum > 0:
                scale = total / co_sum
                co1 = round(co1 * scale, 3)
                co2 = round(co2 * scale, 3)
                co3 = round(co3 * scale, 3)
                co4 = round(co4 * scale, 3)
                co5 = round(co5 * scale, 3)

            cursor.execute("""
                UPDATE marks SET co1=%s, co2=%s, co3=%s, co4=%s, co5=%s
                WHERE id=%s
            """, (co1, co2, co3, co4, co5, row['id']))
            count += 1

        conn.commit()
        print(f"[OK] Fixed {count} rows for {subj_name}")

    conn.close()
    print("Done!")

if __name__ == "__main__":
    fix_co_distribution()
