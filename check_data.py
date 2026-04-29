from db import get_connection
conn = get_connection()
cursor = conn.cursor(dictionary=True)

cursor.execute('SELECT subject_id, subject_name, semester, branch FROM subjects')
subjects = cursor.fetchall()
print('SUBJECTS:')
for r in subjects:
    print(r['subject_id'], r['subject_name'], 'sem='+str(r['semester']), 'branch='+str(r['branch']))

cursor.execute('SELECT DISTINCT branch, semester, pass_year FROM students ORDER BY branch, semester, pass_year')
batches = cursor.fetchall()
print('STUDENT BATCHES:')
for r in batches:
    print(r['branch'], 'sem='+str(r['semester']), 'year='+str(r['pass_year']))

cursor.execute('SELECT s.branch, s.semester, s.pass_year, sub.subject_name, COUNT(*) as cnt FROM marks m JOIN students s ON s.student_id=m.student_id JOIN subjects sub ON sub.subject_id=m.subject_id GROUP BY s.branch, s.semester, s.pass_year, sub.subject_name ORDER BY s.semester, sub.subject_name')
print('MARKS DISTRIBUTION:')
for r in cursor.fetchall():
    print(r['branch'], 'sem='+str(r['semester']), 'year='+str(r['pass_year']), r['subject_name'], 'count='+str(r['cnt']))

conn.close()
