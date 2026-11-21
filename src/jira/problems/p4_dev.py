def _patch(src, old, new):
    if old not in src:
        raise ValueError("patch target not found: " + old[:60])
    return src.replace(old, new, 1)


_SMART = r'''import re

KEY = re.compile(r"(?<![A-Za-z0-9])[A-Z]{2,}-[1-9][0-9]*(?![A-Za-z0-9])")
TIME = re.compile(r"^([0-9]+(?:\.[0-9]+)?)([wdhm])$")

def parse_smart_commit(message, transitions, hours_per_day, days_per_week):
    unit = {"m": 1, "h": 60, "d": 60 * hours_per_day, "w": 60 * hours_per_day * days_per_week}
    actions = []
    for line in message.split("\n"):
        parts = line.split("#")
        keys = []
        for k in KEY.findall(parts[0]):
            if k not in keys:
                keys.append(k)
        if not keys:
            continue
        for part in parts[1:]:
            words = part.split()
            if not words:
                continue
            cmd = words[0].lower()
            rest = part.strip()[len(words[0]):].strip()
            if cmd == "comment":
                if rest:
                    actions += [[k, "comment", rest] for k in keys]
            elif cmd == "time":
                minutes, used = 0.0, 0
                for tok in words[1:]:
                    m = TIME.match(tok)
                    if not m:
                        break
                    minutes += float(m.group(1)) * unit[m.group(2)]
                    used += 1
                if used:
                    actions += [[k, "time", int(round(minutes))] for k in keys]
                else:
                    actions += [[k, "error", "#time"] for k in keys]
            else:
                exact = [t for t in transitions if t.lower().replace(" ", "-") == cmd]
                first = [t for t in transitions if t.lower().split(" ")[0] == cmd]
                if exact:
                    result = ["transition", exact[0]]
                elif len(first) == 1:
                    result = ["transition", first[0]]
                elif first:
                    result = ["error", "ambiguous #" + cmd]
                else:
                    result = ["error", "unknown #" + cmd]
                actions += [[k] + result for k in keys]
    return actions
'''

_T = ["Start Progress", "Start Review", "Close", "Finish work", "Resolve"]

PROBLEMS = [
dict(
    id="jira-smart-commit",
    title="Smart Commit Parser",
    difficulty="Hard",
    pattern="String Parsing",
    entry="parse_smart_commit",
    description=r"""
**Mirrors:** Jira smart commits as documented by Atlassian: `<KEY> <ignored text> #<command> <arguments>` with the
commands `#comment`, `#time` (values in `w`, `d`, `h`, `m`, decimals allowed) and `#<transition name>`; several
commands per line; several keys per line (separated by whitespace or commas); commands do not span lines, so a
line without a key is ignored; keys use the default format (two or more uppercase letters, a hyphen, a number);
and a transition is matched by the part of its name **before the first space**, so names sharing a first word are
ambiguous unless written with hyphens (`#start-review`).

Return the list of actions produced by `message`, in order. For each line (split on `\n`):

1. Split the line on `#`. The text before the first `#` holds the keys: every match of an uppercase key (not
   preceded or followed by a letter or digit, number without a leading zero), duplicates removed, in order. If there
   are none, skip the line.
2. Each later piece is one command. Its first word, lower-cased, is the command name (skip empty pieces). The rest
   of the piece, trimmed, is its text.
3. For each command, add one action **per key**, keys in order:
   - `comment`: `[key, "comment", text]`, or nothing if the text is empty.
   - `time`: read the text's words from the start while they look like `<number><unit>` (unit `w`, `d`, `h` or
     `m`); stop at the first word that does not. Minutes per unit: `m` 1, `h` 60, `d` `60 * hours_per_day`,
     `w` `60 * hours_per_day * days_per_week`. Action `[key, "time", int(round(total_minutes))]`, or
     `[key, "error", "#time"]` if no word matched.
   - anything else is a transition request for `cmd`, checked against `transitions` (the names available):
     - if some name, lower-cased with spaces replaced by `-`, equals `cmd`, use the first such name;
     - otherwise, if exactly one name's first word (lower-cased) equals `cmd`, use it;
     - otherwise, if several do: `[key, "error", "ambiguous #" + cmd]`;
     - otherwise: `[key, "error", "unknown #" + cmd]`.
     A successful match gives `[key, "transition", name]`.

**Example:**
```
message = "SHOP-7 SHOP-8 #time 1h 30m tidy up #start-review\nno key here #close\nSHOP-9 #start"
transitions = ["Start Progress", "Start Review", "Close"]; hours_per_day = 8; days_per_week = 5
```
→ `[["SHOP-7","time",90], ["SHOP-8","time",90], ["SHOP-7","transition","Start Review"],
["SHOP-8","transition","Start Review"], ["SHOP-9","error","ambiguous #start"]]`
""",
    starter='''def parse_smart_commit(message: str, transitions: List[str], hours_per_day: int, days_per_week: int) -> list:
    pass
''',
    solution=_SMART,
    tests=[
        ["SHOP-7 SHOP-8 #time 1h 30m tidy up #start-review\nno key here #close\nSHOP-9 #start", ["Start Progress", "Start Review", "Close"], 8, 5],
        ["JRA-34 #comment corrected indent issue", _T, 8, 5],
        ["JRA-34 #time 1w 2d 4h 30m Total work logged", _T, 8, 5],
        ["JRA-90 #close #comment Fixed this today", _T, 8, 5],
        ["JRA-123 #time 2d 5h #comment Task completed ahead of schedule #resolve", _T, 8, 5],
        ["JRA-123 JRA-234, JRA-345 #resolve", _T, 8, 5],
        ["no keys at all #comment hello", _T, 8, 5],
        ["", _T, 8, 5],
        ["jra-1 #comment lowercase key", _T, 8, 5],
        ["ABC-1 #finish", _T, 8, 5],
        ["ABC-1 #finish-work #FINISH-WORK #Close", _T, 8, 5],
        ["ABC-1 #deploy", _T, 8, 5],
        ["ABC-1 #time soon #time 1.5h #time 0.25d", _T, 8, 5],
        ["ABC-1 #time 1w", _T, 7.5, 4],
        ["ABC-1 #comment", _T, 8, 5],
        ["ABC-1 ABC-1 ABC-2 #comment twice", _T, 8, 5],
        ["ABC-1 ## # #comment spaced  out ", _T, 8, 5],
        ["ABC-1 #comment see #42", _T, 8, 5],
        ["ABC-1 #start\nABC-2 #start-progress\nABC-3 #START-review", _T, 8, 5],
        ["XABC-01 #close AB-0", _T, 8, 5],
        ["\n".join("K-%d KEY-%d #time %dh #comment line %d #close" % (i, i, i % 9 + 1, i) for i in range(1, 80)), _T, 8, 5],
    ],
    examples=1,
    wrong_solutions=[
        _patch(_SMART, "                elif len(first) == 1:\n                    result = [\"transition\", first[0]]\n                elif first:\n",
               "                elif first:\n                    result = [\"transition\", first[0]]\n                elif False:\n"),
        _patch(_SMART, "        if not keys:\n            continue\n",
               "        if not keys:\n            keys = last_keys\n        last_keys = keys\n        if not keys:\n            continue\n")
        .replace("    actions = []\n", "    actions = []\n    last_keys = []\n"),
        _patch(_SMART, "    unit = {\"m\": 1, \"h\": 60, \"d\": 60 * hours_per_day, \"w\": 60 * hours_per_day * days_per_week}",
               "    unit = {\"m\": 1, \"h\": 60, \"d\": 60 * 24, \"w\": 60 * 24 * 7}"),
        _patch(_SMART, "                    actions += [[k, \"comment\", rest] for k in keys]",
               "                    actions += [[keys[0], \"comment\", rest]]"),
    ],
    guide=dict(
        prereqs="String splitting, regular expressions and careful rule-following. See the lesson *Jira and your code: keys, smart commits and permissions*.",
        intuition="Treat each line on its own. Splitting on `#` separates the key area from the commands. Each command then produces the same action "
                  "for every key on the line. The only subtle part is transition matching: exact hyphenated name first, then a unique first word.",
        hints=[
            "Find keys only in `line.split('#')[0]`, and remove duplicates while keeping order.",
            "For each command piece, `words = piece.split()`; skip it if `words` is empty.",
            "For `#time`, stop at the first word that is not `<number><unit>`; the rest is the work log comment and is ignored.",
            "For transitions, compute `exact` and `first` lists separately; `len(first) > 1` is the ambiguous case.",
        ],
        brute_force="Matching transitions with `startswith` would make `#start` match anything beginning with 'start', and `#fin` would match 'Finish work', which Jira does not do.",
        approach="1. Loop over lines; extract keys; skip keyless lines.\n2. Loop over command pieces; branch on `comment`, `time` or a transition.\n"
                 "3. Append one action per key.\n\n**Dry run (example):** line 1 keys SHOP-7, SHOP-8; `time 1h 30m tidy up` → 90 minutes each; `start-review` "
                 "matches 'Start Review' exactly. Line 2 has no key. Line 3: `start` is the first word of two names → ambiguous.",
        complexity="Time O(L * T) for message length L and T transitions; space O(actions).",
        pitfalls="- Commands are case-insensitive (`#Close`), keys are not (`jra-1` is not a key).\n- A `#` inside comment text starts a new command.\n"
                 "- Working-day length is a parameter: Jira's time tracking can be configured, so do not hard-code 24-hour days.\n"
                 "- An empty `#comment` produces nothing.\n- A key repeated on a line acts once.",
        follow_up="Atlassian says a transition with required fields other than the comment silently fails. Extend the input with a set of transitions that "
                  "require extra fields and report them as errors instead of transitions.",
    ),
),
]
