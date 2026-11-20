# Regular expressions

A **regular expression** (regex) is a tiny language for describing patterns in text: "three digits, a dash, four digits", "a word followed by an `@`", "everything between the brackets". Python's `re` module lets you search, extract, validate, split and replace with such patterns. Regexes are compact and powerful — and notoriously write-only, so this lesson focuses on a small core you can read fluently, plus the habits that keep patterns maintainable.

## First match

```python-run
import re

text = "Order #4521 shipped on 2026-01-15 to robin@ohara.org"
m = re.search(r"\d{4}-\d{2}-\d{2}", text)
print(m)                              # a Match object (or None)
print(m.group(), m.start(), m.end(), m.span())
print(re.search(r"refund", text))     # None: no match
```

Always write patterns as **raw strings** (`r"..."`). In a normal string, Python itself interprets backslashes (`"\b"` is a backspace character!); a raw string passes them through to the regex engine untouched.

## The pattern language

### Literals and metacharacters

Most characters match themselves. These are special and must be escaped with `\` to be literal: `. ^ $ * + ? { } [ ] \ | ( )`. `re.escape(s)` escapes a whole string for you.

### Character classes

| Pattern | Matches |
|---|---|
| `.` | any character except newline (any at all with `re.DOTALL`) |
| `\d` / `\D` | a digit / a non-digit |
| `\w` / `\W` | a "word" character (letter, digit, underscore) / anything else |
| `\s` / `\S` | whitespace / non-whitespace |
| `[abc]` | one of a, b, c |
| `[a-z0-9_]` | one character in the ranges |
| `[^abc]` | any character **except** a, b, c |

In Python 3, `\d`, `\w`, `\s` are Unicode-aware for `str` patterns (`\d` matches Arabic-Indic digits too); pass `re.ASCII` to restrict them.

### Quantifiers

| Pattern | Repetitions |
|---|---|
| `x*` | 0 or more |
| `x+` | 1 or more |
| `x?` | 0 or 1 |
| `x{3}` | exactly 3 |
| `x{2,5}` | 2 to 5 |
| `x{2,}` | 2 or more |

Quantifiers are **greedy**: they match as much as possible, then back off if the rest fails. Add `?` to make them **lazy** (as little as possible):

```python-run
import re
html = "<b>bold</b> and <i>italic</i>"
print(re.findall(r"<.+>", html))      # greedy: one giant match
print(re.findall(r"<.+?>", html))     # lazy: each tag
print(re.findall(r"<[^>]+>", html))   # better: a negated class, no backtracking surprises
```

### Anchors and boundaries

| Pattern | Position |
|---|---|
| `^` | start of string (or of each line with `re.MULTILINE`) |
| `$` | end of string (or just before a trailing newline; each line with `re.MULTILINE`) |
| `\A`, `\Z` | absolute start / end of string |
| `\b` | word boundary (between `\w` and `\W`) |
| `\B` | not a word boundary |

```python-run
import re
s = "cat concat cats category"
print(re.findall(r"cat", s))          # every occurrence, even inside words
print(re.findall(r"\bcat\b", s))      # the whole word only
print(re.findall(r"\bcat\w*", s))     # words starting with cat
```

### Alternation and groups

- `a|b` matches `a` or `b` (lowest precedence — wrap in a group to limit its scope: `gr(a|e)y`).
- `( ... )` is a **capturing group**: it groups for quantifiers/alternation *and* remembers the matched text.
- `(?: ... )` groups **without** capturing.
- `(?P<name> ... )` is a **named group**.
- `\1` or `(?P=name)` is a **backreference** to what a group matched.

```python-run
import re

m = re.search(r"(\d{4})-(\d{2})-(\d{2})", "due 2026-01-15, late")
print(m.group(0), m.group(1), m.groups(), m.group(2, 3))

m = re.search(r"(?P<user>[\w.+-]+)@(?P<domain>[\w-]+(?:\.[\w-]+)+)", "mail robin@ohara.org now")
print(m.group("user"), m["domain"], m.groupdict())

print(re.findall(r"\b(\w+) \1\b", "it is is what it it was"))      # doubled words
print(re.fullmatch(r"gr(?:a|e)y", "grey") is not None)
```

### Lookarounds (zero-width assertions)

They check what comes next/before **without consuming** it:

| Pattern | Meaning |
|---|---|
| `x(?=y)` | x followed by y |
| `x(?!y)` | x **not** followed by y |
| `(?<=y)x` | x preceded by y |
| `(?<!y)x` | x **not** preceded by y |

```python-run
import re
print(re.findall(r"\d+(?= EUR)", "10 EUR, 20 USD, 30 EUR"))          # numbers before ' EUR'
print(re.findall(r"(?<=\$)\d+", "cost $45 or 45 units"))             # digits after a dollar sign
print(re.sub(r"(?<=\d)(?=(\d{3})+$)", ",", "1234567"))               # thousands separators
strong = re.compile(r"(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}")          # password rule via lookaheads
print(bool(strong.fullmatch("Passw0rdX")), bool(strong.fullmatch("password")))
```

## The functions

| Function | Does |
|---|---|
| `re.search(p, s)` | first match **anywhere**, or `None` |
| `re.match(p, s)` | match only at the **start** of the string |
| `re.fullmatch(p, s)` | the **entire** string must match — use this for validation |
| `re.findall(p, s)` | list of all matches (strings, or tuples of groups) |
| `re.finditer(p, s)` | iterator of Match objects (lazy, has positions) |
| `re.sub(p, repl, s, count=0)` | replace matches; `repl` is a string or a function |
| `re.split(p, s, maxsplit=0)` | split on matches |
| `re.compile(p, flags)` | precompile into a Pattern object with the same methods |

```python-run
import re
s = "a1, b22; c333"
print(re.match(r"\d", s), re.search(r"\d", s).group(), re.fullmatch(r"[a-c\d,; ]+", s) is not None)
print(re.findall(r"\d+", s))
print(re.findall(r"([a-z])(\d+)", s))               # groups -> list of tuples
print([(m.group(), m.start()) for m in re.finditer(r"\d+", s)])
print(re.split(r"[,;]\s*", s), re.split(r"\s*([,;])\s*", s))    # capturing group keeps separators
```

`findall` has a quirk: with **no** groups it returns whole matches; with **one** group, that group's text; with **several**, tuples. Use non-capturing `(?:...)` when you want grouping without changing the result, or `finditer` for full control.

`match` vs `search` vs `fullmatch` is a classic trap: `re.match(r"\d+", "123abc")` succeeds (prefix matches). For validation, use `fullmatch`.

### Substitution

```python-run
import re
print(re.sub(r"\s+", " ", "too    many \n spaces"))
print(re.sub(r"(\d{4})-(\d{2})-(\d{2})", r"\3/\2/\1", "2026-01-15"))           # reorder with backrefs
print(re.sub(r"(?P<first>\w+) (?P<last>\w+)", r"\g<last>, \g<first>", "Nico Robin"))
print(re.sub(r"\d+", lambda m: str(int(m.group()) * 2), "3 apples, 12 pears"))   # function replacement
print(re.subn(r"a", "A", "banana"))                                               # (result, count)

def snake_to_camel(name):
    return re.sub(r"_([a-z])", lambda m: m.group(1).upper(), name)
def camel_to_snake(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
print(snake_to_camel("user_first_name"), camel_to_snake("userFirstName"))
```

### Flags

| Flag | Short | Effect |
|---|---|---|
| `re.IGNORECASE` | `re.I` | case-insensitive |
| `re.MULTILINE` | `re.M` | `^`/`$` match at each line |
| `re.DOTALL` | `re.S` | `.` matches newlines too |
| `re.VERBOSE` | `re.X` | ignore whitespace and allow `#` comments in the pattern |
| `re.ASCII` | `re.A` | `\w`, `\d`, `\s` ASCII-only |

Combine with `|`. Use **verbose mode** to make non-trivial patterns readable:

```python-run
import re

LOG = re.compile(r"""
    ^(?P<date>\d{4}-\d{2}-\d{2})      # date
    \s+(?P<time>\d{2}:\d{2}:\d{2})    # time
    \s+\[(?P<level>[A-Z]+)\]          # [LEVEL]
    \s+(?P<module>\w+):               # module:
    \s+(?P<message>.*)$               # the rest
""", re.VERBOSE)

lines = """2026-01-02 10:00:01 [INFO] auth: login ok (user=17)
garbage line
2026-01-02 10:00:05 [ERROR] db: connection reset"""

for line in lines.splitlines():
    m = LOG.match(line)
    print(m.groupdict() if m else f"no match: {line!r}")

print(re.findall(r"^\w+", "one two\nthree four", re.M), re.findall(r"error", "Error ERROR error", re.I))
```

### Compiling

`re.compile` parses the pattern once and gives it a name. The module caches recent patterns anyway, so the main benefits are readability and reuse (define patterns as module-level constants), plus a small speed-up in tight loops.

## Common recipes

```python-run
import re
text = "Call +1 (555) 010-9999 or 555.010.8888; email a.b@x.io, c@y.co.uk; site https://ex.am/p?q=1; #tag1 #tag_2"
print(re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text))             # simple emails
print(re.findall(r"https?://[^\s;,]+", text))                        # URLs
print(re.findall(r"#(\w+)", text))                                   # hashtags
print(re.findall(r"\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}", text))          # US-style phones
print(re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", "x=-3.5, y=42, z=.5"))   # ints and floats
print(re.findall(r"[A-Za-z']+", "Don't panic, it's fine!"))          # words with apostrophes
print(" ".join("  trim   and  collapse ".split()))                   # no regex needed!
print(bool(re.fullmatch(r"[A-Za-z_]\w*", "valid_name1")), bool(re.fullmatch(r"\d{5}(-\d{4})?", "12345-678")))
```

## When *not* to use regex

- Simple fixed-string tasks: `in`, `startswith`, `endswith`, `split`, `replace`, `partition`, `strip` are faster and clearer.
- Structured formats: use a real parser — `json`, `csv`, `html.parser`/BeautifulSoup, `urllib.parse`, `datetime.strptime`, `email`, `ipaddress`.
- Nested/recursive structures (balanced parentheses, HTML, programming languages) are beyond what regular expressions can describe.
- Full e-mail or URL validation per the RFCs: use a library, or a loose check plus a confirmation step.

## Performance: catastrophic backtracking

Python's engine is a **backtracking** matcher. Patterns with nested or overlapping quantifiers — `(a+)+$`, `(\w+\s?)*$`, `(.*,)*` — can take **exponential** time on inputs that almost match, freezing your program. On user-supplied input this is a denial-of-service vector (ReDoS).

```python-run
import re, time
evil = re.compile(r"(a+)+$")
for n in (14, 18, 22):
    s = "a" * n + "!"
    t = time.perf_counter()
    evil.match(s)
    print(n, f"{time.perf_counter() - t:.4f}s")      # time roughly doubles per extra character
safe = re.compile(r"a+$")
t = time.perf_counter(); safe.match("a" * 5000 + "!"); print("safe:", f"{time.perf_counter() - t:.5f}s")
```

Defences: avoid nested quantifiers over the same characters; prefer specific classes (`[^,]*` instead of `.*`); anchor patterns; limit input length; from Python 3.11 use possessive quantifiers (`a++`) or atomic groups (`(?>...)`) to forbid backtracking.

## Worked example: a tiny tokenizer

Named groups plus alternation make a compact lexer — the technique shown in the `re` documentation:

```python-run
import re

TOKEN = re.compile(r"""
    (?P<NUMBER>\d+(?:\.\d+)?)
  | (?P<NAME>[A-Za-z_]\w*)
  | (?P<OP>[-+*/()=])
  | (?P<SKIP>\s+)
  | (?P<ERROR>.)
""", re.VERBOSE)

def tokenize(code):
    for m in TOKEN.finditer(code):
        kind = m.lastgroup
        if kind == "SKIP":
            continue
        if kind == "ERROR":
            raise SyntaxError(f"unexpected {m.group()!r} at position {m.start()}")
        yield kind, m.group()

print(list(tokenize("total = price * 3.5 + (tax - 2)")))
try:
    list(tokenize("x = 4 $ 2"))
except SyntaxError as e:
    print("SyntaxError:", e)
```

> [!INTERVIEW]
> Know: `match` (start only) vs `search` (anywhere) vs `fullmatch` (whole string); greedy vs lazy quantifiers; capturing vs non-capturing vs named groups; what `findall` returns with groups; why raw strings; `re.sub` with a function; and catastrophic backtracking. Being able to read a pattern aloud ("one or more word characters, an at-sign, ...") is the practical skill being tested.

## Pitfalls recap

- Forgetting the `r` prefix: `"\b"` is a backspace, `"\d"` a deprecation warning.
- Using `match` for validation (it accepts trailing junk) instead of `fullmatch`.
- Greedy `.*` swallowing too much.
- `findall` returning group contents instead of whole matches.
- Unescaped `.` matching any character (`3.14` matches `3x14`); `[.]` or `\.` for a literal dot.
- `$` matching before a trailing newline; `\Z` is strict.
- Nested quantifiers → exponential backtracking.

## Summary

Regexes describe text patterns with literals, classes, quantifiers, anchors, groups and lookarounds. Use `search`/`fullmatch`/`findall`/`finditer`/`sub`/`split`, raw strings, named groups and verbose mode for readability, and compile reusable patterns. Prefer string methods and real parsers when they fit, and beware backtracking blow-ups.

```quiz
[
  {"q": "Which function should validate that an ENTIRE string is a 5-digit code?", "options": ["re.match(r'\\d{5}', s)", "re.search(r'\\d{5}', s)", "re.fullmatch(r'\\d{5}', s)", "re.findall(r'\\d{5}', s)"], "answer": 2,
   "explain": "match only anchors at the start and search anywhere, so both accept '12345abc'. fullmatch requires the whole string to match."},
  {"q": "Why write patterns as raw strings (r'...')?", "options": ["They run faster", "So Python does not interpret backslashes before the regex engine sees them", "They are required by re", "To allow Unicode"], "answer": 1,
   "explain": "In a normal string '\\b' is a backspace; in a raw string it reaches the engine as the word-boundary escape."},
  {"q": "`re.findall(r'<.+>', '<a><b>')` returns:", "options": ["['<a>', '<b>']", "['<a><b>']", "['a', 'b']", "[]"], "answer": 1,
   "explain": "The greedy + grabs as much as possible. Use the lazy '<.+?>' or '<[^>]+>' to get each tag."},
  {"q": "What does `(?:...)` do?", "options": ["Creates a named group", "Groups without capturing", "Is a lookahead", "Matches a literal colon"], "answer": 1,
   "explain": "A non-capturing group applies quantifiers/alternation without adding to groups() or changing findall output."},
  {"q": "`re.findall(r'(\\w)(\\d)', 'a1 b2')` returns:", "options": ["['a1', 'b2']", "[('a', '1'), ('b', '2')]", "['a', '1', 'b', '2']", "[['a1'], ['b2']]"], "answer": 1,
   "explain": "With multiple capturing groups, findall returns a list of tuples of the groups."},
  {"q": "`\\bcat\\b` matches 'cat' in which string?", "options": ["'concatenate'", "'cats'", "'the cat sat'", "'category'"], "answer": 2,
   "explain": "Word boundaries require non-word characters (or string edges) on both sides."},
  {"q": "What is the danger of a pattern like `(a+)+$` on untrusted input?", "options": ["It never matches", "Catastrophic backtracking: exponential time on near-matches (ReDoS)", "It uses too much disk", "It is a syntax error"], "answer": 1,
   "explain": "Nested quantifiers create exponentially many ways to split the input, all tried before failing."},
  {"q": "In `re.sub(p, repl, s)`, what can `repl` be besides a string?", "options": ["A list", "A function taking a Match and returning the replacement string", "A dict", "A compiled pattern"], "answer": 1,
   "explain": "A callable replacement computes each replacement dynamically from the match."}
]
```

> **Source:** Python docs, *Library Reference* `re` — "Regular expression operations" and the *Regular Expression HOWTO*; Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, §1.11 (the `re` module) and ch. 13 (text processing).
