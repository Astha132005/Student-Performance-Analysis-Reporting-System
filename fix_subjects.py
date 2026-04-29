from db import get_connection
import json

conn = get_connection()
cursor = conn.cursor(dictionary=True)

cursor.execute("SELECT subject_id, subject_name, semester, branch FROM subjects")
subjects = cursor.fetchall()

cursor.execute("""
    SELECT s.branch, s.semester, s.pass_year, sub.subject_name, COUNT(*) as cnt
    FROM marks m
    JOIN students s ON s.student_id=m.student_id
    JOIN subjects sub ON sub.subject_id=m.subject_id
    GROUP BY s.branch, s.semester, s.pass_year, sub.subject_name
    ORDER BY s.semester, sub.subject_name
""")
distribution = cursor.fetchall()

conn.close()

data = {'subjects': subjects, 'marks_distribution': distribution}
with open('audit_result.json', 'w') as f:
    json.dump(data, f, indent=2, default=str)
print("Done")
