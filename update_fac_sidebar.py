import os

files_to_edit = [
    'templates/faculty_dashboard.html',
    'templates/faculty_batch_analysis.html',
    'templates/faculty_subject_analysis.html'
]

for file_path in files_to_edit:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace My Subject with Mark's Entry
        if '<a href="/faculty">My Subject</a>' in content:
            content = content.replace('<a href="/faculty">My Subject</a>', '<a href="/marks_entry">Mark\'s Entry</a>')
        elif '<a href="/faculty" class="active">My Subject</a>' in content:
            content = content.replace('<a href="/faculty" class="active">My Subject</a>', '<a href="/marks_entry" class="active">Mark\'s Entry</a>')

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated sidebar in {file_path}")
