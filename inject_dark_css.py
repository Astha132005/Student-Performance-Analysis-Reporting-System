import glob

TARGET = "css/common.css') }}"
INSERT = '\n    <link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/dark-theme.css\') }}">'

for f in glob.glob('templates/*.html'):
    txt = open(f, encoding='utf-8').read()
    if 'dark-theme.css' not in txt and TARGET in txt:
        idx = txt.find(TARGET) + len(TARGET) + 1  # +1 for closing >
        # Find end of that line
        line_end = txt.find('\n', txt.find(TARGET))
        new_line = '\n    <link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/dark-theme.css\') }}">'
        txt = txt[:line_end] + new_line + txt[line_end:]
        open(f, 'w', encoding='utf-8').write(txt)
        print('Updated:', f)
    else:
        print('Skip:', f)
