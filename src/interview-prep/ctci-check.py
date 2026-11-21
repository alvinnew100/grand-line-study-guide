"""Check internal links and lesson word counts for the interview-prep track. Run from the study-guide root."""
import glob, importlib.util, json, os, re
ids = set()
for f in glob.glob('docs/data/problems/*.json'):
    ids |= set(json.load(open(f, encoding='utf-8')).keys())
les, tracks = set(), set()
for t in os.listdir('src'):
    f = 'src/%s/track.py' % t
    if os.path.exists(f):
        try:
            s = importlib.util.spec_from_file_location('t', f); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
            tracks.add(t)
            for mo in m.TRACK['modules']:
                for l in mo['lessons']:
                    les.add(t + '/' + l['id'])
        except Exception as e:
            print('ERR', t, e)
bad = set()
for f in glob.glob('src/interview-prep/problems/*.py') + glob.glob('src/interview-prep/lessons/*.md'):
    for l in re.findall(r"#/(?:problem|lesson|track)/[a-z0-9/-]+", open(f, encoding='utf-8').read()):
        k, v = l[2:].split('/', 1)
        if (k == 'problem' and v not in ids) or (k == 'lesson' and v not in les) or (k == 'track' and v not in tracks):
            bad.add((os.path.basename(f), l))
for b in sorted(bad):
    print('BAD', b)
BANNED = re.compile(r"\b(simply|obviously|as you know)\b", re.I)
for f in sorted(glob.glob('src/interview-prep/lessons/*.md')):
    t = open(f, encoding='utf-8').read()
    n = len(t.split())
    flags = []
    if n < 2600: flags.append('SHORT')
    for need in ('## Before this lesson', '## In plain words', '## Glossary', '```quiz', '> **Source:**'):
        if need not in t: flags.append('missing ' + need)
    if BANNED.search(t): flags.append('banned word: ' + BANNED.search(t).group(0))
    if re.search(r"\bjust\b", re.sub(r"```.*?```", "", t, flags=re.S)): flags.append('just')
    print(os.path.basename(f), n, flags)
