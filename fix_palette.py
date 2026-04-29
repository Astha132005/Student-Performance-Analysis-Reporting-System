f = r'e:\PPD\SPARS\templates\admin_dashboard.html'

# Read as bytes to find and replace the bad encoding
with open(f, 'rb') as fh:
    raw = fh.read()

# The garbled sequence â€" = UTF-8 bytes for â (0xC3 0xA2), € (0xE2 0x82 0xAC → but as latin1 misread: 0x80), " (0x93)
# More precisely the garbled â€" is the UTF-8 em-dash U+2013 (0xE2 0x80 0x93) misread as latin-1 then re-encoded
# In the file the raw bytes for the garbled text are: C3 A2 E2 80 93 or similar
# Let's just find the pattern directly

# Find the title line
bad  = 'Batch Score Comparison \u00e2\u20ac\u201c Stacked Bar Chart'.encode('utf-8')
good = 'Batch Score Comparison &mdash; Stacked Bar Chart'.encode('utf-8')
if bad in raw:
    raw = raw.replace(bad, good)
    print('Fixed em-dash (variant 1)')

# Also try the most common Windows double-encode pattern
bad2 = b'Batch Score Comparison \xc3\xa2\xe2\x82\xac\xe2\x80\x9c Stacked Bar Chart'
if bad2 in raw:
    raw = raw.replace(bad2, good)
    print('Fixed em-dash (variant 2)')

# Brute force: replace any run containing the garbled title
import re
# Work in decoded form with latin-1 to preserve bytes
text = raw.decode('latin-1')
text = re.sub(
    r'Batch Score Comparison [^\w<]+ Stacked Bar Chart',
    'Batch Score Comparison &mdash; Stacked Bar Chart',
    text
)
raw = text.encode('latin-1')

with open(f, 'wb') as fh:
    fh.write(raw)

# Verify
with open(f, encoding='utf-8', errors='replace') as fh:
    for i, line in enumerate(fh, 1):
        if 'Stacked Bar Chart' in line:
            print(f'L{i}: {line.strip()[:100]}')
            break
