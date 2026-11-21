"""Stage docs/data/index.json with ONLY the given tracks' entries updated (others as in HEAD).
Use when other tracks have uncommitted index changes. Keeps CRLF, indent=1, no trailing newline.
Usage (from study-guide/): python tools/qa/stage_index.py <track> [<track> ...]
A brand-new track is not in HEAD: add it by merging HEAD + the new entry sorted by src/order.py (see HANDOVER.md).
"""
import json, subprocess, sys
tracks = set(sys.argv[1:])
head = json.loads(subprocess.run(['git','show','HEAD:docs/data/index.json'],capture_output=True,text=True,encoding='utf-8').stdout)
work = {t['id']: t for t in json.load(open('docs/data/index.json',encoding='utf-8'))}
out = [work[t['id']] if t['id'] in tracks else t for t in head]
blob = (json.dumps(out, ensure_ascii=False, indent=1)).replace(chr(10), chr(13)+chr(10))
h = subprocess.run(['git','hash-object','-w','--stdin'],input=blob.encode('utf-8'),capture_output=True).stdout.decode().strip()
subprocess.run(['git','update-index','--cacheinfo','100644,'+h+',docs/data/index.json'],check=True)
print('staged index with', sorted(tracks))
