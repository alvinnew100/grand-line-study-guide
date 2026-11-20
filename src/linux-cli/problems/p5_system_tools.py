"""Linux CLI problems, set 5: parsing ls and ps, cron schedules, du roll-ups and find filters."""

PS_SAMPLE = """USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1 167812 11520 ?        Ss   09:01   0:02 /sbin/init splash
mira      2231 87.5 12.4 9123456 2031616 pts/0 Rl   09:40  12:31 python train.py --epochs 40
mira      2250  3.1  0.4 412312  65536 pts/1   Sl   09:41   0:09 tmux new -s work
postgres   812  9.5  2.0 2212345 327680 ?      Ss   09:01   1:15 postgres: checkpointer
www-data  1410 10.0  1.1 1456789 180224 ?      S    09:02   0:44 nginx: worker process
root       433  0.0  0.0      0     0 ?        I<   09:01   0:00 [kworker/0:1H]
"""

PS_CUSTOM = """%CPU   PID COMMAND
 2.0   500 worker --queue high priority
100.0   77 stress -c 1
 9.9  1200 worker --queue low

 0.0     2 [kthreadd]
"""

PROBLEMS = [
# ------------------------------------------------------------------ parse ls -l
dict(
    id="cli-parse-ls-line",
    title="Parse a Line of ls -l",
    difficulty="Medium",
    pattern="Parsing",
    entry="parse_ls_line",
    description=r"""
A long listing packs seven facts about a file into one line:

```
-rw-r--r-- 1 mira staff  4096 Nov 20 09:15 notes.txt
```

Parse one such line into a dictionary with these keys:

| key | value |
|---|---|
| `type` | from the first character: `-` → `"file"`, `d` → `"dir"`, `l` → `"link"`, anything else → `"other"` |
| `perms` | the nine permission characters after the type character |
| `links` | hard-link count (int) |
| `owner`, `group` | strings |
| `size` | bytes (int) |
| `name` | the file name — it **may contain spaces** |
| `target` | for a symbolic link shown as `name -> target`, the target; otherwise `None` |

Fields are separated by one or more spaces. The timestamp always occupies exactly three fields
(month, day, then either a time or a year). Everything after the timestamp is the name.

**Example 1:** `"-rw-r--r-- 1 mira staff  4096 Nov 20 09:15 notes.txt"` →
`{"type": "file", "perms": "rw-r--r--", "links": 1, "owner": "mira", "group": "staff", "size": 4096, "name": "notes.txt", "target": None}`

**Example 2:** `"lrwxrwxrwx 1 root root 7 Jan  3  2025 python -> python3"` → type `"link"`, name `"python"`, target `"python3"`
""",
    starter='''def parse_ls_line(line: str) -> dict:
    pass
''',
    solution='''def parse_ls_line(line):
    parts = line.split(None, 8)
    mode, links, owner, group, size = parts[:5]
    name = parts[8]
    kind = {"-": "file", "d": "dir", "l": "link"}.get(mode[0], "other")
    target = None
    if kind == "link" and " -> " in name:
        name, target = name.split(" -> ", 1)
    return {
        "type": kind,
        "perms": mode[1:10],
        "links": int(links),
        "owner": owner,
        "group": group,
        "size": int(size),
        "name": name,
        "target": target,
    }
''',
    tests=[
        ["-rw-r--r-- 1 mira staff  4096 Nov 20 09:15 notes.txt"],
        ["lrwxrwxrwx 1 root root 7 Jan  3  2025 python -> python3"],
        ["drwxr-xr-x 12 mira staff 4096 Oct  2 18:40 Holiday Photos 2026"],
        ["-rwxr-xr-x 1 root root 1183448 Mar 14  2024 bash"],
        ["crw-rw-rw- 1 root tty 0 Nov 20 08:00 tty"],
        ["-rw------- 1 svc-backup backup 0 Nov  1 00:00 .lock"],
        ["drwxrwxrwt 18 root root 4096 Nov 20 10:02 tmp"],
        ["-rw-r--r-- 3 ana ana 52 Feb 29  2024 a -> b.txt"],
        ["lrwxrwxrwx 1 ana ana 21 Nov 19 23:59 current release -> releases/v2 final"],
        ["-rwsr-xr-x 1 root root 68208 Apr  9  2025 passwd"],
        ["-rw-r--r--  1 mira  staff  1048576000 Nov 20 09:15 model  weights.bin"],
        ["brw-rw---- 1 root disk 0 Nov 20 08:00 sda"],
    ],
    examples=2,
    wrong_solutions=[
        '''def parse_ls_line(line):
    p = line.split()
    kind = {"-": "file", "d": "dir", "l": "link"}.get(p[0][0], "other")
    name, target = p[8], None
    if kind == "link" and "->" in p:
        target = p[-1]
    return {"type": kind, "perms": p[0][1:10], "links": int(p[1]), "owner": p[2], "group": p[3],
            "size": int(p[4]), "name": name, "target": target}
''',
        '''def parse_ls_line(line):
    parts = line.split(None, 8)
    mode = parts[0]
    kind = {"-": "file", "d": "dir", "l": "link"}.get(mode[0], "other")
    name, target = parts[8], None
    if " -> " in name:
        name, target = name.split(" -> ", 1)
    return {"type": kind, "perms": mode[1:10], "links": int(parts[1]), "owner": parts[2],
            "group": parts[3], "size": int(parts[4]), "name": name, "target": target}
''',
        '''def parse_ls_line(line):
    parts = line.split(None, 8)
    mode = parts[0]
    kind = "dir" if mode[0] == "d" else "link" if mode[0] == "l" else "file"
    name, target = parts[8], None
    if kind == "link" and " -> " in name:
        name, target = name.split(" -> ", 1)
    return {"type": kind, "perms": mode[1:10], "links": int(parts[1]), "owner": parts[2],
            "group": parts[3], "size": int(parts[4]), "name": name, "target": target}
''',
    ],
    guide=dict(
        prereqs="The exploring-the-system lesson (anatomy of `ls -l`). `str.split` with `maxsplit`.",
        intuition="The line is a fixed number of whitespace-separated columns followed by one free-form column. The trick is to stop splitting once the fixed columns are done, so spaces inside the name survive. Count them: mode, links, owner, group, size, month, day, time — eight fields — then the remainder.",
        hints=[
            "`line.split(None, 8)` splits on runs of whitespace at most eight times, leaving the ninth piece intact.",
            "Map the first character of the mode through a small dictionary with a default.",
            "Only split on `' -> '` when the entry really is a link; a regular file can legally be called `a -> b.txt`.",
        ],
        brute_force="Split on every space and re-join pieces 8 onward with single spaces. This looks equivalent but silently changes names that contain two consecutive spaces, and still needs the link logic.",
        approach="""1. `parts = line.split(None, 8)`.
2. Take `mode, links, owner, group, size` from the first five; skip three timestamp fields; `name = parts[8]`.
3. Derive `type` from `mode[0]`, `perms` from `mode[1:10]`.
4. For links, split the name once on `' -> '`.

**Dry run, example 2:** parts = `lrwxrwxrwx`, `1`, `root`, `root`, `7`, `Jan`, `3`, `2025`, `python -> python3`. Type `link`; name `python`, target `python3`.""",
        complexity="O(length of the line) time and space.",
        pitfalls="""* Taking the last whitespace-separated token as the name.
* Treating ` -> ` inside a non-link name as a link target.
* Forgetting device files (`c`, `b`), sockets and pipes — they are neither file, dir nor link.
* In real life: do not parse `ls` in scripts at all. Its format varies with locale and options; use `stat --format` or `find -printf` instead. Doing it by hand here is how you learn why.""",
        follow_up="Produce the same dictionary from `stat -c '%A %h %U %G %s %n'` output, which has no ambiguous date columns.",
    ),
),
# ------------------------------------------------------------------ top CPU from ps
dict(
    id="cli-top-cpu-processes",
    title="Top CPU Processes from ps Output",
    difficulty="Medium",
    pattern="Parsing",
    entry="top_cpu",
    description=r"""
During an incident the first question is often "what is eating the CPU?". `ps aux --sort=-%cpu | head`
answers it; here you do the same from the raw text.

`top_cpu(text, k)` receives the full output of a `ps` command and returns the `k` busiest processes
as `[pid, cpu, command]` lists (`pid` an int, `cpu` a float, `command` a string), ordered by CPU
descending and, for equal CPU, by PID ascending.

* The first line is a header naming the columns. It always contains `PID`, `%CPU` and `COMMAND`,
  but the **column order and the other columns vary** (ps output is configurable with `-o`).
* `COMMAND` is always the last column and may contain spaces; every other column is a single token.
* Blank lines should be ignored. If there are fewer than `k` processes, return them all.

**Example:** for the text

```
%CPU   PID COMMAND
 2.0   500 worker --queue high priority
100.0   77 stress -c 1
```

`top_cpu(text, 1)` → `[[77, 100.0, "stress -c 1"]]`
""",
    starter='''def top_cpu(text: str, k: int) -> List[list]:
    pass
''',
    solution='''def top_cpu(text, k):
    rows = [ln for ln in text.split("\\n") if ln.strip()]
    if not rows:
        return []
    header = rows[0].split()
    pid_col, cpu_col = header.index("PID"), header.index("%CPU")
    last = len(header) - 1
    procs = []
    for ln in rows[1:]:
        parts = ln.split(None, last)
        procs.append([int(parts[pid_col]), float(parts[cpu_col]), parts[last].rstrip()])
    procs.sort(key=lambda p: (-p[1], p[0]))
    return procs[:k]
''',
    tests=[
        [PS_CUSTOM, 1],
        [PS_SAMPLE, 3],
        [PS_SAMPLE, 1],
        [PS_SAMPLE, 100],
        [PS_CUSTOM, 2],
        [PS_CUSTOM, 0],
        ["USER PID %CPU COMMAND\n", 3],
        ["", 2],
        ["PID %CPU COMMAND\n9 5.0 b\n3 5.0 a\n7 5.0 c\n", 2],
        ["PID %CPU COMMAND\n1 9.5 nine\n2 10.0 ten\n3 100.0 hundred\n", 3],
        ["USER PID %CPU %MEM COMMAND\nana 42 0.5 1.0 vim my notes.txt\nana 43 0.7 1.0 less  -S  wide file\n", 2],
        ["PID TTY %CPU COMMAND\n12 pts/0 1.0 bash\n13 pts/0 33.3 make -j8\n14 ? 33.3 cc1 -O2 main.c\n", 2],
    ],
    examples=1,
    wrong_solutions=[
        '''def top_cpu(text, k):
    rows = [ln for ln in text.split("\\n") if ln.strip()]
    procs = []
    for ln in rows[1:]:
        p = ln.split(None, 10)
        procs.append([int(p[1]), float(p[2]), p[10].rstrip()])
    procs.sort(key=lambda p: (-p[1], p[0]))
    return procs[:k]
''',
        '''def top_cpu(text, k):
    rows = [ln for ln in text.split("\\n") if ln.strip()]
    if not rows:
        return []
    header = rows[0].split()
    pc, cc, last = header.index("PID"), header.index("%CPU"), len(header) - 1
    procs = []
    for ln in rows[1:]:
        parts = ln.split(None, last)
        procs.append((parts[cc], int(parts[pc]), parts[last].rstrip()))
    procs.sort(key=lambda p: p[0], reverse=True)
    return [[pid, float(cpu), cmd] for cpu, pid, cmd in procs[:k]]
''',
        '''def top_cpu(text, k):
    rows = [ln for ln in text.split("\\n") if ln.strip()]
    if not rows:
        return []
    header = rows[0].split()
    pc, cc, last = header.index("PID"), header.index("%CPU"), len(header) - 1
    procs = []
    for ln in rows[1:]:
        parts = ln.split()
        procs.append([int(parts[pc]), float(parts[cc]), parts[last]])
    procs.sort(key=lambda p: (-p[1], p[0]))
    return procs[:k]
''',
    ],
    guide=dict(
        prereqs="The processes lesson (`ps`, `top`). Splitting with `maxsplit`; sorting with a tuple key.",
        intuition="Tabular command output is a contract between the header and the rows: the header tells you which position holds which fact. Read the header first, find the positions you care about by *name*, and only then touch the data. The last column is free text, so split each row into exactly as many pieces as there are header names and let the final piece keep its spaces.",
        hints=[
            "Find `PID` and `%CPU` with `header.index(...)` instead of hard-coding positions.",
            "`row.split(None, len(header) - 1)` yields exactly `len(header)` parts.",
            "Sort numerically: key `(-cpu, pid)`.",
        ],
        brute_force="Hard-code the `ps aux` layout (PID is column 2, %CPU column 3, COMMAND column 11). It works for that one invocation and breaks as soon as someone uses `ps -eo pid,pcpu,comm` — which is what careful scripts do.",
        approach="""1. Drop blank lines. No lines → `[]`.
2. Split the header; record the indices of `PID` and `%CPU` and the index of the last column.
3. For each row split with `maxsplit = last`; convert PID to `int`, CPU to `float`, keep the command.
4. Sort by `(-cpu, pid)` and slice `k`.

**Dry run, the three-column example:** header `[%CPU, PID, COMMAND]` → cpu_col 0, pid_col 1, last 2. Row 2 splits into `100.0`, `77`, `stress -c 1`. After sorting, 100.0 comes first.""",
        complexity="Time O(n log n) for n processes, space O(n). A heap of size k would give O(n log k).",
        pitfalls="""* Sorting CPU values as strings puts `9.5` above `10.0` and `100.0`.
* Splitting the command on spaces and keeping only the program name.
* Assuming a fixed layout.
* Remember what `%CPU` means in `ps`: CPU time divided by the process's lifetime, not an instantaneous reading like `top` shows.""",
        follow_up="Group by `USER` and report total CPU per user; or aggregate by the first word of the command to find which program, across many worker processes, uses the most.",
    ),
),
# ------------------------------------------------------------------ cron
dict(
    id="cli-cron-match",
    title="Does This Cron Expression Fire Now?",
    difficulty="Medium",
    pattern="Scheduling",
    entry="cron_match",
    description=r"""
A crontab line starts with five fields — **minute, hour, day-of-month, month, day-of-week** — that
say when the job runs. Decide whether a schedule fires at a given moment.

`cron_match(expr, minute, hour, dom, month, dow)`; `dow` is 0–6 with 0 = Sunday.

Each field is a comma-separated list of items. An item is

* `*` — every value in the field's range;
* `N` — one value;
* `A-B` — an inclusive range;
* any of the first or third form followed by `/S` — every S-th value **counting from the start of
  the range** (`*/15` in the minute field is 0, 15, 30, 45; `10-50/20` is 10, 30, 50).

Field ranges: minute 0–59, hour 0–23, day-of-month 1–31, month 1–12, day-of-week 0–7 where **both 0
and 7 mean Sunday**.

The job fires when minute, hour and month all match **and** the day matches, where "the day
matches" has a famous quirk:

* if either day field is exactly `*`, both day fields must match (the `*` one trivially does);
* if **both** day-of-month and day-of-week are restricted, the day matches when **either** matches.

**Example 1:** `"*/15 * * * *"` at minute 30 → `True`

**Example 2:** `"0 9-17 * * 1-5"` on Saturday (dow 6) at 10:00 → `False`

**Example 3:** `"0 0 13 * 5"` at 00:00 on the 6th, a Friday → `True` (13th **or** Friday)
""",
    starter='''def cron_match(expr: str, minute: int, hour: int, dom: int, month: int, dow: int) -> bool:
    pass
''',
    solution='''def cron_match(expr, minute, hour, dom, month, dow):
    bounds = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]
    fields = expr.split()

    def values(field, lo, hi):
        allowed = set()
        for item in field.split(","):
            step = 1
            if "/" in item:
                item, s = item.split("/")
                step = int(s)
            if item == "*":
                a, b = lo, hi
            elif "-" in item:
                x, y = item.split("-")
                a, b = int(x), int(y)
            else:
                a = b = int(item)
            allowed.update(range(a, b + 1, step))
        return allowed

    sets = [values(f, lo, hi) for f, (lo, hi) in zip(fields, bounds)]
    if 7 in sets[4]:
        sets[4].add(0)
    if not (minute in sets[0] and hour in sets[1] and month in sets[3]):
        return False
    dom_ok, dow_ok = dom in sets[2], dow in sets[4]
    if fields[2] == "*" or fields[4] == "*":
        return dom_ok and dow_ok
    return dom_ok or dow_ok
''',
    tests=[
        ["*/15 * * * *", 30, 4, 9, 6, 2],
        ["0 9-17 * * 1-5", 0, 10, 14, 11, 6],
        ["0 0 13 * 5", 0, 0, 6, 11, 5],
        ["*/15 * * * *", 31, 4, 9, 6, 2],
        ["* * * * *", 59, 23, 31, 12, 0],
        ["0 9-17 * * 1-5", 0, 17, 14, 11, 3],
        ["0 0 13 * 5", 0, 0, 13, 11, 2],
        ["0 0 13 * 5", 0, 0, 6, 11, 2],
        ["0 0 * * 7", 0, 0, 22, 11, 0],
        ["5,35 * * * *", 35, 8, 1, 1, 1],
        ["10-50/20 * * * *", 30, 8, 1, 1, 1],
        ["10-50/20 * * * *", 20, 8, 1, 1, 1],
        ["0 0 1 1 *", 0, 0, 1, 1, 4],
        ["0 0 1 1 *", 0, 0, 1, 2, 4],
        ["0 */6 * * *", 0, 12, 5, 5, 5],
        ["0 */6 * * *", 0, 13, 5, 5, 5],
        ["30 2 * * 0", 30, 2, 9, 3, 0],
        ["0 4 1 * *", 0, 4, 2, 7, 1],
        ["0 22 * * 1-5", 0, 22, 20, 11, 5],
        ["15 3 1,15 * 1", 15, 3, 15, 4, 3],
        ["15 3 1,15 * 1", 15, 3, 16, 4, 3],
    ],
    examples=3,
    wrong_solutions=[
        '''def cron_match(expr, minute, hour, dom, month, dow):
    bounds = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]
    def values(field, lo, hi):
        allowed = set()
        for item in field.split(","):
            step = 1
            if "/" in item:
                item, s = item.split("/")
                step = int(s)
            if item == "*":
                a, b = lo, hi
            elif "-" in item:
                a, b = map(int, item.split("-"))
            else:
                a = b = int(item)
            allowed.update(range(a, b + 1, step))
        return allowed
    sets = [values(f, lo, hi) for f, (lo, hi) in zip(expr.split(), bounds)]
    if 7 in sets[4]:
        sets[4].add(0)
    now = [minute, hour, dom, month, dow]
    return all(v in s for v, s in zip(now, sets))
''',
        '''def cron_match(expr, minute, hour, dom, month, dow):
    bounds = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]
    fields = expr.split()
    def values(field, lo, hi):
        allowed = set()
        for item in field.split(","):
            step = 1
            if "/" in item:
                item, s = item.split("/")
                step = int(s)
            if item == "*":
                a, b = lo, hi
            elif "-" in item:
                a, b = map(int, item.split("-"))
            else:
                a = b = int(item)
            allowed.update(v for v in range(a, b + 1) if v % step == 0)
        return allowed
    sets = [values(f, lo, hi) for f, (lo, hi) in zip(fields, bounds)]
    if 7 in sets[4]:
        sets[4].add(0)
    if not (minute in sets[0] and hour in sets[1] and month in sets[3]):
        return False
    a, b = dom in sets[2], dow in sets[4]
    return (a and b) if "*" in (fields[2], fields[4]) else (a or b)
''',
        '''def cron_match(expr, minute, hour, dom, month, dow):
    bounds = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 6)]
    fields = expr.split()
    def values(field, lo, hi):
        allowed = set()
        for item in field.split(","):
            step = 1
            if "/" in item:
                item, s = item.split("/")
                step = int(s)
            if item == "*":
                a, b = lo, hi
            elif "-" in item:
                a, b = map(int, item.split("-"))
            else:
                a = b = int(item)
            allowed.update(range(a, b + 1, step))
        return allowed
    sets = [values(f, lo, hi) for f, (lo, hi) in zip(fields, bounds)]
    if not (minute in sets[0] and hour in sets[1] and month in sets[3]):
        return False
    a, b = dom in sets[2], dow in sets[4]
    return (a and b) if "*" in (fields[2], fields[4]) else (a or b)
''',
    ],
    guide=dict(
        prereqs="The cron section of the ML-and-backend module. Sets and `range` with a step.",
        intuition="Each field is shorthand for a *set of allowed numbers*. Once the five sets exist, matching is membership testing. So spend the effort on a single helper that turns a field such as `1,15,20-30/5` into a set, and then apply the one irregular rule in cron — day-of-month and day-of-week combine with OR when both are restricted.",
        hints=[
            "Split the expression on whitespace, then each field on commas.",
            "For an item, peel off an optional `/step`, then resolve `*`, `A-B` or `N` to a `(start, end)` pair and add `range(start, end + 1, step)`.",
            "Normalise Sunday (7 → 0), check minute/hour/month, then choose AND or OR for the two day fields depending on whether either is a bare `*`.",
        ],
        brute_force="Expand the expression into every (minute, hour, day, month) of a whole year and check whether the given moment is in that list. Around half a million combinations — workable for one query but wasteful, and you still have to implement the field parser.",
        approach="""1. `values(field, lo, hi)` → set of ints.
2. Build five sets with the bounds for each position; add 0 if 7 is present in the weekday set.
3. Return False unless minute, hour and month are members.
4. `dom_ok`, `dow_ok`; if either field is `*` → AND, else → OR.

**Dry run, `0 0 13 * 5` on Friday the 6th at 00:00:** minute {0} ✓, hour {0} ✓, month all ✓. `dom_ok` = 6 in {13} = False; `dow_ok` = 5 in {5} = True. Both fields restricted → OR → True.""",
        complexity="Time O(size of the expanded sets) ≤ a few hundred operations; space the same.",
        pitfalls="""* ANDing the two day fields — the single most common cron misunderstanding. `0 0 13 * 5` is *not* 'Friday the 13th'.
* Steps count from the range start: `10-50/20` gives 10, 30, 50, not the multiples of 20.
* Forgetting that 7 is also Sunday.
* Cron uses the system time zone and knows nothing about 'every 90 minutes' — `*/90` is not valid.""",
        follow_up="Add month and weekday names (`jan`, `mon`), the `@daily`/`@hourly` shortcuts, and write `next_run(expr, now)` that finds the next matching minute.",
    ),
),
# ------------------------------------------------------------------ du
dict(
    id="cli-du-rollup",
    title="du: Roll Up Directory Sizes",
    difficulty="Medium",
    pattern="File System",
    entry="du_rollup",
    description=r"""
"The disk is full — which directory is responsible?" `du` answers by charging every file's size to
**all** of its ancestor directories.

`du_rollup(files)` receives a list of `[path, size]` pairs. Paths are relative, use `/` as the
separator and name **files** (for example `"proj/data/train.csv"`). Return a list of
`[total_size, directory]` pairs containing

* every directory that appears as an ancestor of at least one file, and
* `"."` standing for the top level, whose total is the sum of everything,

sorted by total size descending and then by directory name ascending — the order you get from
`du | sort -rn`.

**Example:**

```
files = [["proj/a.py", 10], ["proj/data/x.csv", 300], ["proj/data/y.csv", 200], ["notes.txt", 5]]
→ [[515, "."], [510, "proj"], [500, "proj/data"]]
```
""",
    starter='''def du_rollup(files: List[list]) -> List[list]:
    pass
''',
    solution='''def du_rollup(files):
    totals = {".": 0}
    for path, size in files:
        totals["."] += size
        parts = path.split("/")[:-1]
        for depth in range(1, len(parts) + 1):
            d = "/".join(parts[:depth])
            totals[d] = totals.get(d, 0) + size
    return sorted(([t, d] for d, t in totals.items()), key=lambda p: (-p[0], p[1]))
''',
    tests=[
        [[["proj/a.py", 10], ["proj/data/x.csv", 300], ["proj/data/y.csv", 200], ["notes.txt", 5]]],
        [[]],
        [[["solo.txt", 42]]],
        [[["a/b/c/d/e.bin", 7]]],
        [[["a/x", 1], ["b/x", 1], ["c/x", 1]]],
        [[["logs/app.log", 900], ["logs/old/app.1.gz", 120], ["logs/old/app.2.gz", 110], ["cache/blob", 2000], ["cache/tmp/t1", 1], ["cache/tmp/t2", 1]]],
        [[["a/empty", 0], ["b/also", 0]]],
        [[["data/data/data.csv", 9], ["data/readme", 1]]],
        [[["x/y/f1", 5], ["x/yz/f2", 6], ["xy/f3", 7]]],
        [[["d%d/sub%d/f%d" % (i % 5, i % 3, i), i] for i in range(200)]],
        [[["home/ana/models/big.pt", 4000000000], ["home/ana/.cache/pip/wheel", 250000000], ["home/bo/tiny", 12], ["var/log/syslog", 730000]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def du_rollup(files):
    totals = {".": 0}
    for path, size in files:
        totals["."] += size
        parts = path.split("/")[:-1]
        if parts:
            d = "/".join(parts)
            totals[d] = totals.get(d, 0) + size
    return sorted(([t, d] for d, t in totals.items()), key=lambda p: (-p[0], p[1]))
''',
        '''def du_rollup(files):
    totals = {".": 0}
    for path, size in files:
        totals["."] += size
        for d in path.split("/")[:-1]:
            totals[d] = totals.get(d, 0) + size
    return sorted(([t, d] for d, t in totals.items()), key=lambda p: (-p[0], p[1]))
''',
        '''def du_rollup(files):
    totals = {".": 0}
    for path, size in files:
        totals["."] += size
        parts = path.split("/")[:-1]
        for depth in range(1, len(parts) + 1):
            d = "/".join(parts[:depth])
            totals[d] = totals.get(d, 0) + size
    return sorted(([t, d] for d, t in totals.items()), reverse=True)
''',
    ],
    guide=dict(
        prereqs="The storage and on-call lessons (`df` versus `du`). Dictionaries; building path prefixes.",
        intuition="A directory's size is the sum of everything beneath it, at any depth. Rather than building a tree and summing bottom-up, flip the viewpoint: each file knows its chain of ancestors, so let every file *donate* its size to each of them. A file three levels deep makes three donations (plus one to the grand total).",
        hints=[
            "Drop the last path component (the file name); what remains are the directory names.",
            "The ancestors are the prefixes: `a`, `a/b`, `a/b/c`. Use the full prefix as the dictionary key, not the bare directory name.",
            "Sort the final pairs with key `(-total, name)`.",
        ],
        brute_force="First collect the set of all directories; then, for each directory, loop over all files and add those whose path starts with `dir + '/'`. That is O(directories × files) and has a subtle trap: testing `startswith(dir)` without the slash makes `x/y` swallow `x/yz`.",
        approach="""1. `totals = {'.': 0}`.
2. For each `(path, size)`: add to `'.'`; split the path, drop the file name, and add `size` to every prefix.
3. Emit `[total, dir]` sorted by descending total then name.

**Dry run, `proj/data/x.csv` (300):** `.` += 300; prefixes `proj` += 300 and `proj/data` += 300. After all four files: `.` = 515, `proj` = 510, `proj/data` = 500.""",
        complexity="Time O(total number of path components + d log d) for d directories; space O(d).",
        pitfalls="""* Charging only the immediate parent — then `proj` would show 10 instead of 510.
* Keying by bare directory name merges unrelated directories that share a name (`data/data`).
* Reverse-sorting the pairs as a whole puts ties in descending name order.
* Real `du` reports **disk blocks used**, not byte lengths, so sparse files and tiny files can differ from `ls -l` sizes.""",
        follow_up="Add a `max_depth` argument like `du -d 1`: directories deeper than the limit are still counted in their ancestors but not listed.",
    ),
),
# ------------------------------------------------------------------ find
dict(
    id="cli-find-filter",
    title="find: Filter by Name, Type, Size and Age",
    difficulty="Hard",
    pattern="File System",
    entry="find_filter",
    description=r"""
`find` walks a directory tree and prints the entries that pass **all** of the tests you give it.
Implement the tests over a pre-walked list.

`find_filter(entries, criteria)`:

* `entries` — list of dictionaries with keys `path` (string), `type` (`"f"` file, `"d"` directory,
  `"l"` symlink), `size` (bytes) and `age_hours` (hours since last modification, a float).
* `criteria` — dictionary with any subset of these keys (missing key = no restriction):

| key | like | meaning |
|---|---|---|
| `name` | `-name '*.log'` | shell glob (`*`, `?`, `[...]`) matched against the **base name** (the part after the last `/`), case-sensitively |
| `type` | `-type f` | exact type letter |
| `size` | `-size +10k` | see below |
| `mtime` | `-mtime +7` | see below |

Return the matching paths in input order.

**Size.** The value is an optional sign, a number N and a unit: `c` = bytes, `k` = 1024 bytes,
`M` = 1048576 bytes. The file size is first **rounded up** to a whole number of units, then compared:
`+N` means more than N units, `-N` fewer than N units, plain `N` exactly N units. (So a 1-byte file
counts as 1M, and `-size -1M` only matches empty files.)

**mtime.** The age is first converted to whole days, **discarding the fraction**
(`age_hours // 24`); then `+N` means more than N days, `-N` fewer than N, `N` exactly N. (So
`-mtime +7` needs an age of at least 8 full days.)

**Example:** entries `a.log` (file, 2048 bytes, 30 h old) and `b.txt` (file, 10 bytes, 500 h old):
`{"name": "*.log"}` → `["a.log"]`; `{"mtime": "+7"}` → `["b.txt"]`; `{"size": "+1k"}` → `["a.log"]`.
""",
    starter='''def find_filter(entries: List[dict], criteria: dict) -> List[str]:
    pass
''',
    solution='''import fnmatch
import math

def find_filter(entries, criteria):
    def compare(value, spec):
        if spec[0] == "+":
            return value > int(spec[1:])
        if spec[0] == "-":
            return value < int(spec[1:])
        return value == int(spec)

    out = []
    for e in entries:
        if "name" in criteria:
            base = e["path"].rsplit("/", 1)[-1]
            if not fnmatch.fnmatchcase(base, criteria["name"]):
                continue
        if "type" in criteria and e["type"] != criteria["type"]:
            continue
        if "size" in criteria:
            spec = criteria["size"]
            unit = {"c": 1, "k": 1024, "M": 1048576}[spec[-1]]
            units = math.ceil(e["size"] / unit)
            if not compare(units, spec[:-1]):
                continue
        if "mtime" in criteria:
            days = int(e["age_hours"] // 24)
            if not compare(days, criteria["mtime"]):
                continue
        out.append(e["path"])
    return out
''',
    tests=[
        [[{"path": "a.log", "type": "f", "size": 2048, "age_hours": 30.0}, {"path": "b.txt", "type": "f", "size": 10, "age_hours": 500.0}], {"name": "*.log"}],
        [[{"path": "a.log", "type": "f", "size": 2048, "age_hours": 30.0}, {"path": "b.txt", "type": "f", "size": 10, "age_hours": 500.0}], {"mtime": "+7"}],
        [[{"path": "a.log", "type": "f", "size": 2048, "age_hours": 30.0}, {"path": "b.txt", "type": "f", "size": 10, "age_hours": 500.0}], {"size": "+1k"}],
        [[{"path": "a.log", "type": "f", "size": 2048, "age_hours": 30.0}], {}],
        [[], {"type": "f"}],
        [[{"path": "logs", "type": "d", "size": 4096, "age_hours": 1.0}, {"path": "logs/app.log", "type": "f", "size": 1, "age_hours": 1.0}, {"path": "latest", "type": "l", "size": 4, "age_hours": 1.0}], {"type": "d"}],
        [[{"path": "logs.d/readme", "type": "f", "size": 1, "age_hours": 1.0}, {"path": "x/logs.d", "type": "d", "size": 1, "age_hours": 1.0}], {"name": "logs*"}],
        [[{"path": "e", "type": "f", "size": 0, "age_hours": 0.0}, {"path": "one", "type": "f", "size": 1, "age_hours": 0.0}, {"path": "meg", "type": "f", "size": 1048576, "age_hours": 0.0}, {"path": "meg1", "type": "f", "size": 1048577, "age_hours": 0.0}], {"size": "-1M"}],
        [[{"path": "e", "type": "f", "size": 0, "age_hours": 0.0}, {"path": "one", "type": "f", "size": 1, "age_hours": 0.0}, {"path": "meg", "type": "f", "size": 1048576, "age_hours": 0.0}, {"path": "meg1", "type": "f", "size": 1048577, "age_hours": 0.0}], {"size": "1M"}],
        [[{"path": "e", "type": "f", "size": 0, "age_hours": 0.0}, {"path": "one", "type": "f", "size": 1, "age_hours": 0.0}, {"path": "meg", "type": "f", "size": 1048576, "age_hours": 0.0}, {"path": "meg1", "type": "f", "size": 1048577, "age_hours": 0.0}], {"size": "+1M"}],
        [[{"path": "d7", "type": "f", "size": 5, "age_hours": 168.0}, {"path": "d7h", "type": "f", "size": 5, "age_hours": 191.9}, {"path": "d8", "type": "f", "size": 5, "age_hours": 192.0}, {"path": "new", "type": "f", "size": 5, "age_hours": 23.9}], {"mtime": "+7"}],
        [[{"path": "d7", "type": "f", "size": 5, "age_hours": 168.0}, {"path": "d7h", "type": "f", "size": 5, "age_hours": 191.9}, {"path": "d8", "type": "f", "size": 5, "age_hours": 192.0}, {"path": "new", "type": "f", "size": 5, "age_hours": 23.9}], {"mtime": "7"}],
        [[{"path": "d7", "type": "f", "size": 5, "age_hours": 168.0}, {"path": "d1", "type": "f", "size": 5, "age_hours": 24.0}, {"path": "new", "type": "f", "size": 5, "age_hours": 23.9}], {"mtime": "-1"}],
        [[{"path": "run/ckpt_01.pt", "type": "f", "size": 900000000, "age_hours": 400.0}, {"path": "run/ckpt_02.pt", "type": "f", "size": 900000000, "age_hours": 20.0}, {"path": "run/ckpt_old", "type": "d", "size": 4096, "age_hours": 900.0}, {"path": "run/notes.PT", "type": "f", "size": 200, "age_hours": 900.0}, {"path": "run/small.pt", "type": "f", "size": 100, "age_hours": 900.0}], {"name": "*.pt", "type": "f", "size": "+100M", "mtime": "+14"}],
        [[{"path": "a/img_1.png", "type": "f", "size": 3, "age_hours": 2.0}, {"path": "a/img_12.png", "type": "f", "size": 3, "age_hours": 2.0}, {"path": "a/img_x.png", "type": "f", "size": 3, "age_hours": 2.0}], {"name": "img_[0-9].png"}],
        [[{"path": "k1", "type": "f", "size": 1024, "age_hours": 0.5}, {"path": "k1b", "type": "f", "size": 1025, "age_hours": 0.5}, {"path": "c", "type": "f", "size": 512, "age_hours": 0.5}], {"size": "1k"}],
        [[{"path": "k1", "type": "f", "size": 1024, "age_hours": 0.5}, {"path": "c", "type": "f", "size": 512, "age_hours": 0.5}], {"size": "512c"}],
    ],
    examples=3,
    wrong_solutions=[
        '''import fnmatch

def find_filter(entries, criteria):
    def compare(value, spec):
        if spec[0] == "+":
            return value > int(spec[1:])
        if spec[0] == "-":
            return value < int(spec[1:])
        return value == int(spec)
    out = []
    for e in entries:
        if "name" in criteria and not fnmatch.fnmatchcase(e["path"].rsplit("/", 1)[-1], criteria["name"]):
            continue
        if "type" in criteria and e["type"] != criteria["type"]:
            continue
        if "size" in criteria:
            spec = criteria["size"]
            unit = {"c": 1, "k": 1024, "M": 1048576}[spec[-1]]
            if not compare(e["size"] / unit, spec[:-1]):
                continue
        if "mtime" in criteria and not compare(int(e["age_hours"] // 24), criteria["mtime"]):
            continue
        out.append(e["path"])
    return out
''',
        '''import fnmatch, math

def find_filter(entries, criteria):
    def compare(value, spec):
        if spec[0] == "+":
            return value > float(spec[1:])
        if spec[0] == "-":
            return value < float(spec[1:])
        return value == float(spec)
    out = []
    for e in entries:
        if "name" in criteria and not fnmatch.fnmatchcase(e["path"].rsplit("/", 1)[-1], criteria["name"]):
            continue
        if "type" in criteria and e["type"] != criteria["type"]:
            continue
        if "size" in criteria:
            spec = criteria["size"]
            unit = {"c": 1, "k": 1024, "M": 1048576}[spec[-1]]
            if not compare(math.ceil(e["size"] / unit), spec[:-1]):
                continue
        if "mtime" in criteria and not compare(e["age_hours"] / 24, criteria["mtime"]):
            continue
        out.append(e["path"])
    return out
''',
        '''import fnmatch, math

def find_filter(entries, criteria):
    def compare(value, spec):
        if spec[0] == "+":
            return value > int(spec[1:])
        if spec[0] == "-":
            return value < int(spec[1:])
        return value == int(spec)
    out = []
    for e in entries:
        if "name" in criteria and not fnmatch.fnmatchcase(e["path"], criteria["name"]):
            continue
        if "type" in criteria and e["type"] != criteria["type"]:
            continue
        if "size" in criteria:
            spec = criteria["size"]
            unit = {"c": 1, "k": 1024, "M": 1048576}[spec[-1]]
            if not compare(math.ceil(e["size"] / unit), spec[:-1]):
                continue
        if "mtime" in criteria and not compare(int(e["age_hours"] // 24), criteria["mtime"]):
            continue
        out.append(e["path"])
    return out
''',
    ],
    guide=dict(
        prereqs="The searching-for-files lesson (`find` tests and their numeric arguments) and the glob problem. `math.ceil`, integer division.",
        intuition="`find` evaluates an AND-chain of tests per entry and stops at the first failure. Each test is easy on its own; the difficulty is entirely in two rounding rules that surprise almost everyone. Sizes are rounded **up** to whole units before comparing, and ages are rounded **down** to whole days. Once the value is rounded, `+N`, `-N` and `N` are plain greater-than, less-than and equals on integers.",
        hints=[
            "Write one helper `compare(value, spec)` for the `+N` / `-N` / `N` logic and reuse it for size and mtime.",
            "Size: `units = ceil(size / unit)`. mtime: `days = age_hours // 24`.",
            "Match the glob against the base name only; `fnmatch.fnmatchcase` implements `*`, `?` and `[...]` (or reuse your own matcher).",
        ],
        brute_force="There is no asymptotically worse approach — each entry must be examined once — but the 'obvious' implementation compares raw bytes against `N × unit` and fractional days against N. It is the natural reading of the options and it is wrong at the boundaries, which is exactly what the tests probe.",
        approach="""For each entry, apply the present criteria in turn and `continue` on the first failure:

1. `name` → base name vs glob.
2. `type` → equality.
3. `size` → parse unit, `ceil`, compare.
4. `mtime` → floor to days, compare.

**Dry run, `-size -1M`:** sizes 0, 1, 1048576, 1048577 bytes become 0, 1, 1, 2 units. 'Fewer than 1' keeps only the empty file. With `1M` exactly: the 1-byte and the 1 MiB files. With `+1M`: only the 1048577-byte file.

**Dry run, `-mtime +7`:** ages 168 h, 191.9 h, 192 h → 7, 7, 8 days. Only the 192-hour file is 'more than 7'.""",
        complexity="Time O(n × p) for n entries and glob length p; space O(output).",
        pitfalls="""* `-size -1M` does not mean 'smaller than a megabyte'. Use `-size -1048576c` for that.
* `-mtime +7` means 'at least 8 days ago'; `-mtime 7` is the window from 7 to just under 8 days.
* `-name` never sees directory components; `-path` does.
* On a real shell, quote the pattern (`-name '*.log'`) or the shell expands it before `find` sees it.""",
        follow_up="Add `-maxdepth`, `-newer file`, the `-o` (OR) operator and `!` negation, then an action list such as `-delete` — and think about why `-delete` should come last.",
    ),
),
]
