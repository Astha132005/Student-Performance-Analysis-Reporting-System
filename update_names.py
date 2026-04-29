import os

files_to_edit = [
    'templates/batch_analysis.html',
    'templates/faculty_batch_analysis.html',
    'templates/faculty.html',
    'templates/faculty_subject_analysis.html',
    'templates/subject_analysis.html'
]

link_str = '<a href="/student?search={{ s.reg_no }}" style="color: inherit; text-decoration: none; border-bottom: 1px dashed rgba(255,255,255,0.4);">{{ s.name }}</a>'

for file_path in files_to_edit:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # We only want to replace standalone {{ s.name }} that isn't inside our anchor
        if ">{{ s.name }}<" in content:
            content = content.replace(">{{ s.name }}<", f">{link_str}<")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {file_path}")
