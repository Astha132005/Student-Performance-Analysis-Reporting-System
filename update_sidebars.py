import os

admin_files = ['admin_dashboard.html', 'batch_analysis.html', 'subject_analysis.html', 'marks_entry.html']
faculty_files = ['faculty_dashboard.html', 'faculty_batch_analysis.html', 'faculty_subject_analysis.html', 'faculty.html']

for f_name in admin_files:
    path = os.path.join('templates', f_name)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '<a href="/student">Student Search</a>' not in content:
        if '<a href="/marks_entry">Mark\'s Entry</a>' in content:
            content = content.replace('<a href="/marks_entry">Mark\'s Entry</a>', '<a href="/marks_entry">Mark\'s Entry</a>\n        <a href="/student">Student Search</a>')
        elif '<a href="/marks_entry" class="active">Mark\'s Entry</a>' in content:
            content = content.replace('<a href="/marks_entry" class="active">Mark\'s Entry</a>', '<a href="/marks_entry" class="active">Mark\'s Entry</a>\n        <a href="/student">Student Search</a>')
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {f_name}')

for f_name in faculty_files:
    path = os.path.join('templates', f_name)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '<a href="/student">Student Search</a>' not in content:
        if '<a href="/faculty">My Subject</a>' in content:
            content = content.replace('<a href="/faculty\">My Subject</a>', '<a href="/faculty">My Subject</a>\n        <a href="/student">Student Search</a>')
        elif '<a href="/faculty" class="active">My Subject</a>' in content:
            content = content.replace('<a href="/faculty" class="active">My Subject</a>', '<a href="/faculty" class="active">My Subject</a>\n        <a href="/student\">Student Search</a>')
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {f_name}')
