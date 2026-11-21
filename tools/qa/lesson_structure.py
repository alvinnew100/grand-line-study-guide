"""List lessons missing the beginner sections or under 2,400 words.
Usage (from study-guide/): python tools/qa/lesson_structure.py <track> [<track> ...]
"""
import sys, pathlib, re
for t in sys.argv[1:]:
    files = sorted(pathlib.Path('src', t, 'lessons').glob('*.md'))
    todo = []
    for f in files:
        s = f.read_text(encoding='utf-8'); low = s.lower()
        miss = [k for k in ('before this lesson', '## in plain words', '## glossary') if k not in low]
        w = len(re.findall(r'\S+', s))
        if miss or w < 2400: todo.append(f"{f.name}({w}w{' missing:'+','.join(m.replace('## ','') for m in miss) if miss else ''})")
    print(f"{t}: {len(files)} lessons, {len(todo)} unfinished")
    for x in todo: print('   ', x)
