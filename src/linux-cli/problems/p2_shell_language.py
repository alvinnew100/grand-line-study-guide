"""Linux CLI problems, set 2: what the shell does to a line before a command ever runs."""

PROBLEMS = [
# ------------------------------------------------------------------ glob
dict(
    id="cli-glob-match",
    title="Shell Glob Matcher",
    difficulty="Medium",
    pattern="Expansion",
    entry="glob_match",
    description=r"""
When you type `ls *.log`, the shell — not `ls` — compares the pattern against every file name.
Implement that comparison for one name.

`glob_match(pattern, name)` returns `True` when the **whole** `name` matches `pattern`:

* `*` matches any run of characters, including an empty run.
* `?` matches exactly one character.
* `[abc]` matches one character from the set; `[a-z]` is a range (inclusive); sets and ranges can be
  mixed (`[a-cx0-9]`). A `-` that is first or last in the brackets is a literal dash.
* `[!abc]` or `[^abc]` matches one character **not** in the set.
* Every other character matches itself.

Brackets in the tests are always closed and non-empty. Ignore the real shell's special rule for
names that start with a dot.

**Example 1:** `pattern = "*.txt", name = "notes.txt"` → `True`

**Example 2:** `pattern = "data_??.csv", name = "data_07.csv"` → `True`

**Example 3:** `pattern = "[a-c]*", name = "delta"` → `False`
""",
    starter='''def glob_match(pattern: str, name: str) -> bool:
    pass
''',
    solution=r'''def glob_match(pattern, name):
    tokens = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            tokens.append(("star",))
            i += 1
        elif c == "?":
            tokens.append(("any",))
            i += 1
        elif c == "[":
            j = i + 1
            negate = pattern[j] in "!^"
            if negate:
                j += 1
            k = pattern.index("]", j)
            body = pattern[j:k]
            singles, ranges = set(), []
            m = 0
            while m < len(body):
                if m + 2 < len(body) and body[m + 1] == "-":
                    ranges.append((body[m], body[m + 2]))
                    m += 3
                else:
                    singles.add(body[m])
                    m += 1
            tokens.append(("set", negate, singles, ranges))
            i = k + 1
        else:
            tokens.append(("lit", c))
            i += 1

    def one(tok, ch):
        if tok[0] == "any":
            return True
        if tok[0] == "lit":
            return tok[1] == ch
        _, negate, singles, ranges = tok
        hit = ch in singles or any(lo <= ch <= hi for lo, hi in ranges)
        return hit != negate

    n = len(name)
    reach = [True] + [False] * n          # reach[j]: tokens so far can consume name[:j]
    for tok in tokens:
        nxt = [False] * (n + 1)
        if tok[0] == "star":
            seen = False
            for j in range(n + 1):
                seen = seen or reach[j]
                nxt[j] = seen
        else:
            for j in range(n):
                if reach[j] and one(tok, name[j]):
                    nxt[j + 1] = True
        reach = nxt
    return reach[n]
''',
    tests=[
        ["*.txt", "notes.txt"], ["data_??.csv", "data_07.csv"], ["[a-c]*", "delta"],
        ["*", ""], ["?", ""], ["*.txt", ".txt"], ["a*b*c", "aXbYbZc"], ["a*b*c", "aXbYbZ"],
        ["[!0-9]*", "9lives"], ["[^0-9]*", "nine"], ["log.[0-9][0-9]", "log.42"],
        ["log.[0-9][0-9]", "log.4"], ["*a*a*a*a*a*a*b", "a" * 40], ["img[_-]?.png", "img-1.png"],
        ["report", "reports"], ["[a-cx0-9]z", "xz"], ["**", "x"], ["?*", "q"],
    ],
    examples=3,
    wrong_solutions=[
        r'''def glob_match(pattern, name):
    import functools
    @functools.lru_cache(None)
    def go(i, j):
        if i == len(pattern):
            return j == len(name)
        c = pattern[i]
        if c == "*":
            return any(go(i + 1, k) for k in range(j + 1, len(name) + 1))
        if j == len(name):
            return False
        if c == "[":
            k = pattern.index("]", i + 2)
            body = pattern[i + 1:k]
            neg = body[0] in "!^"
            if neg:
                body = body[1:]
            hit = False
            m = 0
            while m < len(body):
                if m + 2 < len(body) and body[m + 1] == "-":
                    hit = hit or body[m] <= name[j] <= body[m + 2]
                    m += 3
                else:
                    hit = hit or body[m] == name[j]
                    m += 1
            return hit != neg and go(k + 1, j + 1)
        return (c == "?" or c == name[j]) and go(i + 1, j + 1)
    return go(0, 0)
''',
        r'''def glob_match(pattern, name):
    import re
    out = ""
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            out += ".*"
        elif c == "?":
            out += "."
        elif c == "[":
            k = pattern.index("]", i + 2)
            out += "[" + pattern[i + 1:k].lstrip("!^").replace("\\", "\\\\") + "]"
            i = k
        else:
            out += re.escape(c)
        i += 1
    return re.fullmatch(out, name, re.S) is not None
''',
    ],
    guide=dict(
        prereqs="The expansion lesson (pathname expansion and wildcards). Basic dynamic programming or recursion with memoisation.",
        intuition="Every pattern element except `*` eats exactly one character, so those are easy: line the pattern up with the name and compare. The star is the troublemaker because you do not know *how many* characters it should swallow. Instead of guessing, track **all** the positions in the name you could be at after each pattern element. A star simply says: from any reachable position, every later position is reachable too.",
        hints=[
            "Tokenise the pattern first so a bracket expression becomes one unit, just like a literal or a `?`.",
            "Keep a boolean list `reach` of length `len(name) + 1`; `reach[j]` means 'the tokens processed so far can match exactly the first j characters'.",
            "For a single-character token, `new[j+1] = reach[j] and token matches name[j]`. For `*`, `new[j]` is true if any `reach[i]` with `i <= j` is true — a running OR.",
        ],
        brute_force="Recursive backtracking: when you meet `*`, try letting it match 0, 1, 2, … characters and recurse on the rest. Simple and correct, but a pattern such as `*a*a*a*b` against a long string of `a`s explores an exponential number of splits before giving up.",
        approach="""1. Parse the pattern into tokens: `star`, `any`, `lit c`, or `set (negated?, singles, ranges)`.
2. `reach = [True, False, …]` — before any token, only the empty prefix is matched.
3. Fold over the tokens, building the next `reach` as described in the hints.
4. The answer is `reach[len(name)]`.

**Dry run, `a*c` vs `abc`:** start `[T,F,F,F]`. Token `a`: position 0 reachable and `name[0]=='a'` → `[F,T,F,F]`. Token `*`: running OR → `[F,T,T,T]`. Token `c`: from 1, `b` no; from 2, `c` yes → `[F,F,F,T]`. `reach[3]` is true.""",
        complexity="Time O(P × N) for P tokens and N characters; space O(N).",
        pitfalls="""* Forgetting that `*` can match nothing (`*.txt` matches `.txt` in this problem).
* Matching a prefix only. The pattern must consume the entire name.
* Ignoring negation, or treating a trailing `-` as the start of a range.
* Exponential backtracking on many stars.""",
        follow_up="Add the shell's dot-file rule (a leading `.` must be matched literally) and character classes such as `[[:digit:]]`. Compare with Python's `fnmatch.translate`.",
    ),
),
# ------------------------------------------------------------------ brace expansion
dict(
    id="cli-brace-expansion",
    title="Brace Expansion",
    difficulty="Medium",
    pattern="Expansion",
    entry="brace_expand",
    description=r"""
`mkdir -p project/{src,tests,docs}` creates three directories because the shell rewrites the word
into three words before `mkdir` starts. Unlike globs, brace expansion never looks at the disk: it is
pure text generation.

Return the list of words that the string `s` expands to, **in the order bash produces them**.

* `{x,y,z}` is a list of alternatives; alternatives may be empty (`{,s}`) and may contain further
  braces.
* `{m..n}` with integers is a range, counting up or down (`{3..1}` → `3 2 1`).
* Several groups in one word multiply; the **leftmost group varies slowest**.
* Text outside braces is copied to every result.

Every `{` in the tests has a matching `}` and is either a comma list or an integer range.

**Example 1:** `"file{1,2,3}.txt"` → `["file1.txt", "file2.txt", "file3.txt"]`

**Example 2:** `"{a,b}{1,2}"` → `["a1", "a2", "b1", "b2"]`

**Example 3:** `"a{b,c{d,e}}f"` → `["abf", "acdf", "acef"]`
""",
    starter='''def brace_expand(s: str) -> List[str]:
    pass
''',
    solution=r'''import re

def brace_expand(s):
    start = s.find("{")
    if start == -1:
        return [s]
    depth = 0
    for end in range(start, len(s)):
        if s[end] == "{":
            depth += 1
        elif s[end] == "}":
            depth -= 1
            if depth == 0:
                break
    prefix, body, rest = s[:start], s[start + 1:end], s[end + 1:]
    parts, cur, depth = [], "", 0
    for ch in body:
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        cur += ch
    parts.append(cur)
    if len(parts) == 1:
        m = re.fullmatch(r"(-?\d+)\.\.(-?\d+)", body)
        lo, hi = int(m.group(1)), int(m.group(2))
        step = 1 if lo <= hi else -1
        middles = [str(v) for v in range(lo, hi + step, step)]
    else:
        middles = []
        for part in parts:
            middles.extend(brace_expand(part))
    tails = brace_expand(rest)
    return [prefix + mid + tail for mid in middles for tail in tails]
''',
    tests=[
        ["file{1,2,3}.txt"], ["{a,b}{1,2}"], ["a{b,c{d,e}}f"], ["plain"], ["{1..5}"], ["v{3..1}"],
        ["{-1..1}"], ["{,un}do"], ["src/{lib,bin}/{a,b}.c"], ["x{1..3}{a,b}"], ["{a,{b,{c,d}}}"],
        [""], ["pre{x,}"], ["{a,b}-{1..2}-{y,z}"], ["{7..7}"],
    ],
    examples=3,
    wrong_solutions=[
        r'''import re

def brace_expand(s):
    m = re.search(r"\{([^{}]*)\}", s)
    if not m:
        return [s]
    body = m.group(1)
    r = re.fullmatch(r"(-?\d+)\.\.(-?\d+)", body)
    if r:
        lo, hi = int(r.group(1)), int(r.group(2))
        step = 1 if lo <= hi else -1
        alts = [str(v) for v in range(lo, hi + step, step)]
    else:
        alts = body.split(",")
    out = []
    for a in alts:
        out.extend(brace_expand(s[:m.start()] + a + s[m.end():]))
    return out
''',
        r'''import re

def brace_expand(s):
    start = s.find("{")
    if start == -1:
        return [s]
    depth = 0
    for end in range(start, len(s)):
        if s[end] == "{":
            depth += 1
        elif s[end] == "}":
            depth -= 1
            if depth == 0:
                break
    prefix, body, rest = s[:start], s[start + 1:end], s[end + 1:]
    parts, cur, depth = [], "", 0
    for ch in body:
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
            continue
        depth += ch == "{"
        depth -= ch == "}"
        cur += ch
    parts.append(cur)
    if len(parts) == 1:
        lo, hi = map(int, body.split(".."))
        middles = [str(v) for v in range(lo, hi + 1)]
    else:
        middles = [x for p in parts for x in brace_expand(p)]
    return [prefix + mid + tail for tail in brace_expand(rest) for mid in middles]
''',
    ],
    guide=dict(
        prereqs="The expansion lesson (brace expansion). Recursion; tracking nesting depth with a counter.",
        intuition="A word with braces is a little grammar: *prefix*, then *one of several alternatives*, then *the rest*. The rest may itself contain braces, and so may each alternative. That self-similarity is a recursion: expand the alternatives into a flat list of middles, expand the rest into a flat list of tails, and glue every middle to every tail. Because the middle loop is the outer one, the leftmost group changes slowest — the same order an odometer uses.",
        hints=[
            "Find the first `{` and then its *matching* `}` by counting depth; do not use the first `}` you see.",
            "Split the inside on commas, but only commas at depth zero.",
            "If there was no top-level comma, the body is a range `m..n`. Otherwise recursively expand each part and concatenate the lists. Then combine with the recursive expansion of everything after the closing brace.",
        ],
        brute_force="Repeatedly locate an innermost `{...}` (one with no braces inside), replace the word by one copy per alternative, and loop until no braces remain. It terminates, but working inside-out produces the results in the wrong order for nested groups, so you then need to re-sort them — which is harder than doing it properly.",
        approach="""1. No `{` → return `[s]`.
2. Locate the matching `}` using a depth counter. Split `s` into `prefix`, `body`, `rest`.
3. Split `body` on depth-0 commas into `parts`.
4. One part → integer range, counting in the right direction. Several parts → recursively expand each and concatenate.
5. `tails = brace_expand(rest)`; result is `prefix + mid + tail` for each `mid`, then each `tail`.

**Dry run, `a{b,c{d,e}}f`:** prefix `a`, body `b,c{d,e}`, rest `f`. Parts: `b` and `c{d,e}`. `b` → `[b]`; `c{d,e}` → `[cd, ce]`. Middles `[b, cd, ce]`, tails `[f]`. Output `abf acdf acef`.""",
        complexity="Time and space proportional to the total size of the output, which can be exponential in the number of groups — that is inherent, since every result must be produced.",
        pitfalls="""* Splitting on every comma breaks nested lists.
* Looping tails outside middles reverses the significance of the groups (`a1 b1 a2 b2`).
* Descending ranges need a step of −1 and an inclusive end.
* An empty alternative is valid and yields the bare prefix + suffix.""",
        follow_up="Bash also supports letter ranges (`{a..e}`), zero-padded ranges (`{01..10}`) and steps (`{0..20..5}`), and leaves `{single}` untouched. Add them.",
    ),
),
# ------------------------------------------------------------------ tokeniser
dict(
    id="cli-tokenize-command",
    title="Split a Command Line into Words",
    difficulty="Medium",
    pattern="Quoting",
    entry="shell_split",
    description=r"""
Before running anything, the shell chops the line you typed into **words**. Quoting decides where the
cuts go. Implement the quoting rules (no variable or glob expansion — just word boundaries and quote
removal).

* Outside quotes, spaces and tabs separate words; runs of them count as one separator.
* Inside **single quotes** every character is literal, up to the next single quote.
* Inside **double quotes** everything is literal except backslash, which escapes only the four
  characters `"`, `\`, `$` and the backtick (the backslash is dropped). Before any other character the
  backslash is kept as-is.
* Outside quotes, a backslash makes the next character literal and is itself removed.
* Quoted and unquoted pieces that touch form **one** word: `a'b c'd` is the single word `ab cd`.
* An empty pair of quotes still produces a word (the empty string).

The quote characters themselves are removed. Inputs are well formed (quotes are closed, no trailing
backslash).

**Example 1:** `ls -l /tmp` → `["ls", "-l", "/tmp"]`

**Example 2:** `echo 'two  spaces' "and more"` → `["echo", "two  spaces", "and more"]`

**Example 3:** `touch my\ file a'b c'd` → `["touch", "my file", "ab cd"]`
""",
    starter='''def shell_split(line: str) -> List[str]:
    pass
''',
    solution=r'''def shell_split(line):
    words, cur, in_word = [], [], False
    i, n = 0, len(line)
    while i < n:
        c = line[i]
        if c in " \t":
            if in_word:
                words.append("".join(cur))
                cur, in_word = [], False
            i += 1
        elif c == "'":
            j = line.index("'", i + 1)
            cur.append(line[i + 1:j])
            in_word = True
            i = j + 1
        elif c == '"':
            in_word = True
            i += 1
            while line[i] != '"':
                if line[i] == "\\" and line[i + 1] in '"\\$`':
                    cur.append(line[i + 1])
                    i += 2
                else:
                    cur.append(line[i])
                    i += 1
            i += 1
        elif c == "\\":
            cur.append(line[i + 1])
            in_word = True
            i += 2
        else:
            cur.append(c)
            in_word = True
            i += 1
    if in_word:
        words.append("".join(cur))
    return words
''',
    tests=[
        ["ls -l /tmp"],
        ["echo 'two  spaces' \"and more\""],
        ["touch my\\ file a'b c'd"],
        ["   echo   spaced\t\tout   "],
        [""],
        ["     "],
        ["touch ''"],
        ["echo \"\" x"],
        ["echo \"say \\\"hi\\\"\""],
        ["echo \"back\\slash and \\n stay\""],
        ["echo 'it'\\''s'"],
        ["grep \"it's here\" 'a \"b\" c'"],
        ["echo \"cost \\$5\" '\\$5'"],
        ["printf \"%s\\\\n\" \"a b\"c d"],
        ["echo \\\"quoted\\\" \\\\"],
    ],
    examples=3,
    wrong_solutions=[
        '''def shell_split(line):
    return line.split()
''',
        r'''def shell_split(line):
    words, cur, in_word = [], [], False
    i, n = 0, len(line)
    while i < n:
        c = line[i]
        if c in " \t":
            if in_word:
                words.append("".join(cur))
                cur, in_word = [], False
            i += 1
        elif c == "'":
            j = line.index("'", i + 1)
            cur.append(line[i + 1:j])
            in_word = True
            i = j + 1
        elif c == '"':
            in_word = True
            i += 1
            while line[i] != '"':
                if line[i] == "\\":
                    i += 1
                cur.append(line[i])
                i += 1
            i += 1
        elif c == "\\":
            cur.append(line[i + 1])
            in_word = True
            i += 2
        else:
            cur.append(c)
            in_word = True
            i += 1
    if in_word:
        words.append("".join(cur))
    return words
''',
        r'''def shell_split(line):
    words, cur = [], []
    i, n = 0, len(line)
    while i < n:
        c = line[i]
        if c in " \t":
            if cur:
                words.append("".join(cur))
                cur = []
            i += 1
        elif c == "'":
            j = line.index("'", i + 1)
            cur.append(line[i + 1:j])
            i = j + 1
        elif c == '"':
            i += 1
            while line[i] != '"':
                if line[i] == "\\" and line[i + 1] in '"\\$`':
                    i += 1
                cur.append(line[i])
                i += 1
            i += 1
        elif c == "\\":
            cur.append(line[i + 1])
            i += 2
        else:
            cur.append(c)
            i += 1
    if cur:
        words.append("".join(cur))
    return [w for w in words if w]
''',
    ],
    guide=dict(
        prereqs="The expansion-and-quoting lesson: what single quotes, double quotes and backslash each protect. A simple state machine over characters.",
        intuition="Read the line one character at a time and always know which of four situations you are in: between words, in a bare word, inside single quotes, inside double quotes. Whitespace ends a word only in the bare state. Quotes do not start a *new* word; they just switch how the following characters are read, which is why `a'b c'd` stays glued together. A separate flag for 'a word has started' is what lets `''` produce an empty word.",
        hints=[
            "Keep a buffer for the current word plus a boolean `in_word`; an empty buffer does not mean no word (think of `''`).",
            "Single quotes are the easy case: jump straight to the closing quote and append the slice.",
            "In double quotes, peek at the character after a backslash: drop the backslash only if that character is a double quote, a backslash, a dollar sign or a backtick.",
        ],
        brute_force="Call `line.split()`. It handles plain commands and nothing else: any quoted space is torn apart and the quote characters stay in the output. Patching it with regular expressions for quotes gets complicated fast because of adjacency and escapes.",
        approach="""Loop with an index `i`:

1. Space or tab → if `in_word`, flush the buffer to the result; advance.
2. `'` → append everything up to the next `'`; set `in_word`.
3. `"` → set `in_word`; copy characters until the closing `"`, applying the four-character escape rule.
4. `\\` → append the next character literally; set `in_word`.
5. Anything else → append; set `in_word`.

At the end flush once more.

**Dry run, `a'b c'd ""`:** `a` → buffer `a`. Quote: append `b c` → `ab c`. `d` → `ab cd`. Space: flush `["ab cd"]`. `""`: `in_word` becomes true with an empty buffer. End: flush `""`. Result `["ab cd", ""]`.""",
        complexity="Time O(n), space O(n).",
        pitfalls="""* Dropping every backslash inside double quotes — `"\\n"` keeps its backslash.
* Treating a backslash as special inside single quotes; nothing is special there, which is why `'it'\\''s'` is the idiom for an apostrophe.
* Losing empty arguments by testing whether the buffer is non-empty instead of using a flag.
* Starting a new word at a quote character.""",
        follow_up="Python's `shlex.split` implements nearly the same rules (it differs slightly on which characters backslash escapes in double quotes). Extend your tokenizer to recognise the operators `|`, `>`, `>>`, `&&` and `;` as separate tokens when unquoted.",
    ),
),
# ------------------------------------------------------------------ parameter expansion
dict(
    id="cli-parameter-expansion",
    title="Expand $1, $# and ${var:-default}",
    difficulty="Medium",
    pattern="Expansion",
    entry="expand_params",
    description=r"""
Implement the core of the shell's parameter expansion for one string.

`expand_params(template, args, env)` receives the text, the list of positional parameters
(`args[0]` is `$1`) and a dictionary of variables. Replace:

| Form | Meaning |
|---|---|
| `$1` … `$9` | one positional parameter (a **single** digit: `$10` is `$1` followed by `0`) |
| `${N}` | positional parameter N, any number of digits |
| `$#` | how many positional parameters there are |
| `$*`, `$@` | all positional parameters joined by single spaces |
| `$name`, `${name}` | variable; a name is letters, digits and `_`, not starting with a digit, taken as long as possible |
| `${p:-word}` | value of `p` if it is set **and non-empty**, otherwise `word` |
| `${p:+word}` | `word` if `p` is set and non-empty, otherwise nothing |
| `${#p}` | length of the value of `p` |

`p` can be a name or a number. Anything unset expands to the empty string. A `$` that starts none of
these forms is an ordinary character. `word` is plain text with no `}` in it.

**Example 1:** `template = "Hello $1, you have $# args", args = ["Ana", "x"], env = {}` → `"Hello Ana, you have 2 args"`

**Example 2:** `template = "${name:-guest}", args = [], env = {}` → `"guest"`

**Example 3:** `template = "$10", args = ["x"], env = {}` → `"x0"`
""",
    starter='''def expand_params(template: str, args: List[str], env: Dict[str, str]) -> str:
    pass
''',
    solution=r'''def expand_params(template, args, env):
    def lookup(key):
        if key.isdigit():
            k = int(key)
            return args[k - 1] if 1 <= k <= len(args) else ""
        return env.get(key, "")

    def is_name_char(ch):
        return ch == "_" or ("a" <= ch <= "z") or ("A" <= ch <= "Z") or ("0" <= ch <= "9")

    out, i, n = [], 0, len(template)
    while i < n:
        c = template[i]
        if c != "$" or i + 1 == n:
            out.append(c)
            i += 1
            continue
        d = template[i + 1]
        if d == "{":
            j = template.index("}", i)
            body = template[i + 2:j]
            i = j + 1
            if body.startswith("#"):
                out.append(str(len(lookup(body[1:]))))
            elif ":-" in body:
                key, word = body.split(":-", 1)
                out.append(lookup(key) or word)
            elif ":+" in body:
                key, word = body.split(":+", 1)
                out.append(word if lookup(key) else "")
            else:
                out.append(lookup(body))
        elif "1" <= d <= "9":
            out.append(lookup(d))
            i += 2
        elif d == "#":
            out.append(str(len(args)))
            i += 2
        elif d in "*@":
            out.append(" ".join(args))
            i += 2
        elif is_name_char(d) and not d.isdigit():
            j = i + 1
            while j < n and is_name_char(template[j]):
                j += 1
            out.append(lookup(template[i + 1:j]))
            i = j
        else:
            out.append("$")
            i += 1
    return "".join(out)
''',
    tests=[
        ["Hello $1, you have $# args", ["Ana", "x"], {}],
        ["${name:-guest}", [], {}],
        ["$10", ["x"], {}],
        ["${10}-${2}", list("abcdefghij"), {}],
        ["${name:-guest}", [], {"name": "kit"}],
        ["${name:-guest}", [], {"name": ""}],
        ["[${1:-none}] [${2:-none}]", ["only"], {}],
        ["run ${DEBUG:+--verbose} now", [], {"DEBUG": "1"}],
        ["run ${DEBUG:+--verbose} now", [], {}],
        ["${#name} ${#1} ${#missing}", ["abcd"], {"name": "hello"}],
        ["$user_name vs ${user}_name", [], {"user": "u", "user_name": "full"}],
        ["cost: $ 5, 100$ and $-", [], {}],
        ["<$*> <$@> <$#>", [], {}],
        ["$HOME/bin:$PATH", [], {"HOME": "/home/zed", "PATH": "/usr/bin"}],
        ["$1$2$3$4", ["a", "b"], {}],
        ["${greeting:-hi: there} $name!", [], {"name": "Bo"}],
    ],
    examples=3,
    wrong_solutions=[
        r'''import re

def expand_params(template, args, env):
    def lookup(key):
        if key.isdigit():
            k = int(key)
            return args[k - 1] if 1 <= k <= len(args) else ""
        return env.get(key, "")
    def repl(m):
        t = m.group(0)
        if t == "$#":
            return str(len(args))
        if t in ("$*", "$@"):
            return " ".join(args)
        if t.startswith("${"):
            body = t[2:-1]
            if body.startswith("#"):
                return str(len(lookup(body[1:])))
            if ":-" in body:
                k, w = body.split(":-", 1)
                return lookup(k) or w
            if ":+" in body:
                k, w = body.split(":+", 1)
                return w if lookup(k) else ""
            return lookup(body)
        return lookup(t[1:])
    return re.sub(r"\$\{[^}]*\}|\$\d+|\$[#*@]|\$[A-Za-z_][A-Za-z0-9_]*", repl, template)
''',
        r'''import re

def expand_params(template, args, env):
    def lookup(key, default=""):
        if key.isdigit():
            k = int(key)
            return args[k - 1] if 1 <= k <= len(args) else default
        return env.get(key, default)
    def repl(m):
        t = m.group(0)
        if t == "$#":
            return str(len(args))
        if t in ("$*", "$@"):
            return " ".join(args)
        if t.startswith("${"):
            body = t[2:-1]
            if body.startswith("#"):
                return str(len(lookup(body[1:])))
            if ":-" in body:
                k, w = body.split(":-", 1)
                return lookup(k, w)
            if ":+" in body:
                k, w = body.split(":+", 1)
                return w if lookup(k, None) is not None else ""
            return lookup(body)
        return lookup(t[1:])
    return re.sub(r"\$\{[^}]*\}|\$\d|\$[#*@]|\$[A-Za-z_][A-Za-z0-9_]*", repl, template)
''',
    ],
    guide=dict(
        prereqs="The positional-parameters and strings-and-numbers lessons. Scanning a string with an index.",
        intuition="Expansion is a left-to-right scan that copies ordinary characters and, whenever it meets a `$`, decides *how much* of what follows belongs to the reference. Braces make the extent explicit; without them the shell uses fixed rules — one digit for a positional parameter, the longest run of name characters for a variable. Once you know the extent, the lookup is trivial. The `:-` and `:+` forms are just an `if` on whether the value is empty.",
        hints=[
            "Write a helper `lookup(key)` that handles both numbers (index into `args`, 1-based) and names (dictionary), returning `''` when missing.",
            "After `$`, branch on the next character: `{`, a digit 1–9, `#`, `*`/`@`, a letter or underscore, or anything else (literal dollar).",
            "Inside braces: a leading `#` means length; otherwise look for `:-` or `:+` and split once.",
        ],
        brute_force="A chain of `str.replace` calls for each known variable. It breaks as soon as one name is a prefix of another (`$user` inside `$user_name`), cannot express `$#` or defaults, and may re-expand text that was itself the result of an expansion.",
        approach="""Single pass with index `i`:

1. Not a `$` (or `$` is the last character) → copy.
2. `${` → find `}`; interpret the body (`#p`, `p:-w`, `p:+w`, or plain `p`).
3. Digit 1–9 → that one positional parameter; consume two characters only.
4. `#` → count; `*` or `@` → joined arguments.
5. Letter/underscore → extend to the longest name; look it up.
6. Otherwise emit a literal `$`.

**Dry run, `"$10"` with args `["x"]`:** see `$`, next is `1` → append `x`, advance by 2. Remaining `0` is copied. Output `x0`. This is why scripts must write `${10}`.""",
        complexity="Time O(n + size of output), space the same.",
        pitfalls="""* Greedy digits: `$10` is not parameter ten.
* `:-` tests for *empty*, not merely unset — an empty string still triggers the default.
* Longest-match for names: `$user_name` is one variable, so use `${user}_name` to stop early.
* A lone `$` or `$` before punctuation is just a dollar sign.""",
        follow_up="Add `${p:=word}` (assign the default), `${p:?message}` (fail if unset), and the pattern forms `${p#prefix}` / `${p%suffix}` from the strings lesson.",
    ),
),
# ------------------------------------------------------------------ test / [ ]
dict(
    id="cli-test-expression",
    title="Evaluate a test Expression",
    difficulty="Medium",
    pattern="Scripting",
    entry="test_eval",
    description=r"""
`[ -f "$cfg" -a "$n" -gt 3 ]` is an ordinary command (`[` is a synonym of `test`) that receives its
expression as separate arguments and reports the answer through its **exit status**: `0` for true,
`1` for false. Implement it.

`test_eval(args, files)` gets the argument list (without the brackets) and a dictionary describing
a pretend file system: path → `"f"` (regular file) or `"d"` (directory). Return `0` or `1`.

Supported, in order of precedence from loosest to tightest:

* `e1 -o e2` — OR
* `e1 -a e2` — AND (binds tighter than `-o`)
* `! e` — NOT
* primaries:
  * `s1 = s2`, `s1 != s2` — string comparison
  * `n1 -eq n2`, `-ne`, `-lt`, `-le`, `-gt`, `-ge` — **integer** comparison
  * `-z s` (string is empty), `-n s` (string is not empty)
  * `-e p` (exists), `-f p` (regular file), `-d p` (directory)
  * a single string `s` — true when it is not empty

When three arguments are available and the middle one is a binary operator, treat them as a binary
primary (so `-n = -n` compares two strings). An empty argument list is false. There are no
parentheses.

**Example 1:** `args = ["5", "-gt", "3"]` → `0`

**Example 2:** `args = ["-f", "/etc/app.conf"], files = {"/etc/app.conf": "f"}` → `0`

**Example 3:** `args = ["10", "-lt", "9"]` → `1`
""",
    starter='''def test_eval(args: List[str], files: Dict[str, str]) -> int:
    pass
''',
    solution=r'''def test_eval(args, files):
    BIN = {"=", "!=", "-eq", "-ne", "-lt", "-le", "-gt", "-ge"}
    UN = {"-z", "-n", "-e", "-f", "-d"}
    pos = 0

    def primary():
        nonlocal pos
        if pos + 2 < len(args) and args[pos + 1] in BIN:
            a, op, b = args[pos], args[pos + 1], args[pos + 2]
            pos += 3
            if op == "=":
                return a == b
            if op == "!=":
                return a != b
            x, y = int(a), int(b)
            return {"-eq": x == y, "-ne": x != y, "-lt": x < y,
                    "-le": x <= y, "-gt": x > y, "-ge": x >= y}[op]
        if args[pos] in UN and pos + 1 < len(args):
            op, a = args[pos], args[pos + 1]
            pos += 2
            if op == "-z":
                return a == ""
            if op == "-n":
                return a != ""
            if op == "-e":
                return a in files
            if op == "-f":
                return files.get(a) == "f"
            return files.get(a) == "d"
        s = args[pos]
        pos += 1
        return s != ""

    def negation():
        nonlocal pos
        if pos < len(args) and args[pos] == "!" and pos + 1 < len(args):
            pos += 1
            return not negation()
        return primary()

    def conjunction():
        nonlocal pos
        value = negation()
        while pos < len(args) and args[pos] == "-a":
            pos += 1
            rhs = negation()
            value = value and rhs
        return value

    def disjunction():
        nonlocal pos
        value = conjunction()
        while pos < len(args) and args[pos] == "-o":
            pos += 1
            rhs = conjunction()
            value = value or rhs
        return value

    if not args:
        return 1
    return 0 if disjunction() else 1
''',
    tests=[
        [["5", "-gt", "3"], {}],
        [["-f", "/etc/app.conf"], {"/etc/app.conf": "f"}],
        [["10", "-lt", "9"], {}],
        [["-z", ""], {}],
        [["-n", ""], {}],
        [["abc"], {}],
        [[""], {}],
        [[], {}],
        [["a", "=", "a"], {}],
        [["a", "!=", "a"], {}],
        [["!", "-f", "/etc/x"], {"/etc/x": "f"}],
        [["-d", "/tmp"], {"/tmp": "d"}],
        [["-f", "/tmp"], {"/tmp": "d"}],
        [["-e", "/nope"], {"/tmp": "d"}],
        [["-f", "a", "-a", "-d", "b"], {"a": "f", "b": "d"}],
        [["1", "-eq", "1", "-o", "2", "-eq", "2", "-a", "-z", "x"], {}],
        [["!", "!", "x"], {}],
        [["-n", "=", "-n"], {}],
        [["007", "-eq", "7"], {}],
        [["-5", "-lt", "0", "-a", "!", "-e", "ghost"], {}],
        [["007", "=", "7"], {}],
    ],
    examples=3,
    wrong_solutions=[
        r'''def test_eval(args, files):
    BIN = {"=", "!=", "-eq", "-ne", "-lt", "-le", "-gt", "-ge"}
    UN = {"-z", "-n", "-e", "-f", "-d"}
    pos = 0
    def primary():
        nonlocal pos
        if pos + 2 < len(args) and args[pos + 1] in BIN:
            a, op, b = args[pos], args[pos + 1], args[pos + 2]
            pos += 3
            return {"=": a == b, "!=": a != b, "-eq": a == b, "-ne": a != b, "-lt": a < b,
                    "-le": a <= b, "-gt": a > b, "-ge": a >= b}[op]
        if args[pos] in UN and pos + 1 < len(args):
            op, a = args[pos], args[pos + 1]
            pos += 2
            return {"-z": a == "", "-n": a != "", "-e": a in files,
                    "-f": files.get(a) == "f", "-d": files.get(a) == "d"}[op]
        pos += 1
        return args[pos - 1] != ""
    def neg():
        nonlocal pos
        if args[pos] == "!" and pos + 1 < len(args):
            pos += 1
            return not neg()
        return primary()
    def conj():
        nonlocal pos
        v = neg()
        while pos < len(args) and args[pos] == "-a":
            pos += 1
            r = neg()
            v = v and r
        return v
    if not args:
        return 1
    v = conj()
    while pos < len(args) and args[pos] == "-o":
        pos += 1
        r = conj()
        v = v or r
    return 0 if v else 1
''',
        r'''def test_eval(args, files):
    BIN = {"=", "!=", "-eq", "-ne", "-lt", "-le", "-gt", "-ge"}
    UN = {"-z", "-n", "-e", "-f", "-d"}
    pos = 0
    def primary():
        nonlocal pos
        if pos + 2 < len(args) and args[pos + 1] in BIN:
            a, op, b = args[pos], args[pos + 1], args[pos + 2]
            pos += 3
            if op == "=":
                return a == b
            if op == "!=":
                return a != b
            x, y = int(a), int(b)
            return {"-eq": x == y, "-ne": x != y, "-lt": x < y,
                    "-le": x <= y, "-gt": x > y, "-ge": x >= y}[op]
        if args[pos] in UN and pos + 1 < len(args):
            op, a = args[pos], args[pos + 1]
            pos += 2
            return {"-z": a == "", "-n": a != "", "-e": a in files,
                    "-f": files.get(a) == "f", "-d": files.get(a) == "d"}[op]
        pos += 1
        return args[pos - 1] != ""
    def neg():
        nonlocal pos
        if args[pos] == "!" and pos + 1 < len(args):
            pos += 1
            return not neg()
        return primary()
    if not args:
        return 1
    v = neg()
    while pos < len(args) and args[pos] in ("-a", "-o"):
        op = args[pos]
        pos += 1
        r = neg()
        v = (v and r) if op == "-a" else (v or r)
    return 0 if v else 1
''',
        r'''def test_eval(args, files):
    if not args:
        return 0
    if len(args) == 1:
        return 1 if args[0] else 0
    return 1
''',
    ],
    guide=dict(
        prereqs="The flow-control lesson (`if`, exit status, `test`). Recursive-descent parsing: one function per precedence level.",
        intuition="`test` is a tiny expression language whose tokens are already separated for you — the shell did the splitting. Precedence is handled the classic way: a function for OR calls a function for AND, which calls one for NOT, which calls one for primaries. Each function consumes the tokens that belong to it and returns a boolean. The final twist is cultural, not technical: Unix success is **0**, so true maps to 0 and false to 1.",
        hints=[
            "Keep a shared index into `args`. `primary()` consumes 3, 2 or 1 tokens.",
            "Check the three-token binary form first, then the two-token unary form, then fall back to 'non-empty string'.",
            "`-eq` and friends must convert with `int()`; `=` and `!=` must not.",
        ],
        brute_force="Handle only the fixed shapes — one, two or three arguments — with a big `if` on `len(args)`. That covers most real scripts (and is how POSIX specifies the short cases) but cannot combine conditions with `-a`/`-o`.",
        approach="""1. `disjunction` → `conjunction` (`-o` `conjunction`)*
2. `conjunction` → `negation` (`-a` `negation`)*
3. `negation` → `!` `negation` | `primary`
4. `primary` → binary | unary | bare string
5. Return `0 if result else 1`.

**Dry run, `1 -eq 1 -o 2 -eq 2 -a -z x`:** `disjunction` calls `conjunction`, which parses `1 -eq 1` → true and stops at `-o`. Back in `disjunction`, consume `-o` and call `conjunction` again: `2 -eq 2` → true, sees `-a`, parses `-z x` → false, so this side is false. `true or false` → true → exit status `0`. Evaluating strictly left to right would have given false.""",
        complexity="Time O(number of arguments), space O(depth of `!` nesting).",
        pitfalls="""* Comparing numbers as strings: `"10" < "9"` is true alphabetically. Conversely `007 = 7` is **false** while `007 -eq 7` is true.
* Returning Python booleans instead of the inverted exit status.
* Giving `-a` and `-o` equal precedence.
* Not evaluating both sides before combining them — the parser must still *consume* the right-hand tokens even if the left side already decides the answer.""",
        follow_up="Bash's `[[ ... ]]` adds `&&`, `||`, parentheses, pattern matching with `==` and regex matching with `=~`, and does not word-split its operands. Extend the evaluator with parentheses.",
    ),
),
]
