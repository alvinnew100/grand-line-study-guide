# Regular expressions

> **Before this lesson:** you need strings and their methods (`split`, `replace`, `find`, slicing) from [Lists, tuples and strings](#/lesson/python/py-sequences), and lambdas from [Scope, closures and lambdas](#/lesson/python/py-scope-closures). Reading text line by line is covered in [Files, pathlib, JSON and CSV](#/lesson/python/py-files-json-csv).

## In plain words

String methods such as `find` and `replace` look for one exact piece of text. Often you need to look for a *kind* of text: "any date", "anything that looks like an email address", "every number in this line". A **regular expression**, usually shortened to **regex**, is a small language for describing such patterns. In Python it lives in the standard module `re`.

Think of the "find" box in a word processor, with superpowers. In that box you can type `2026` and find that exact text. With a regex you can describe a shape: "four digits, a dash, two digits, a dash, two digits", and it finds every date written that way, whichever date it is. You describe what the text *looks like*, and the regex engine (the machinery that carries out the search) finds everything that fits.

With a pattern you can do five things: **search** for it, **extract** the pieces that matched, **validate** that a whole string has the right shape, **split** text wherever the pattern occurs, and **replace** every match.

Why this matters for a job: cleaning messy text, reading log files and checking user input are everyday tasks, and regexes turn many of them into one line. Interviewers ask about the difference between `match`, `search` and `fullmatch`, and about greedy matching. Regexes also have a bad reputation, partly deserved: they are easy to write and hard to read. This lesson therefore teaches a small core you can read fluently, and the habits that keep patterns understandable.

## First match

```python-run
import re

text = "Order #4521 shipped on 2026-01-15 to robin@ohara.org"
m = re.search(r"\d{4}-\d{2}-\d{2}", text)
print(m)                              # a Match object (or None)
print(m.group(), m.start(), m.end(), m.span())
print(re.search(r"refund", text))     # None: no match
```

**Reading this code line by line**

- The pattern is `\d{4}-\d{2}-\d{2}`. `\d` means "any digit", `{4}` means "four of the preceding thing", and `-` is a plain dash. So: four digits, dash, two digits, dash, two digits.
- `re.search(pattern, text)` scans the text for the first place where the pattern fits. It returns a **match object** describing what was found, or `None` if nothing fits.
- `m.group()` is the text that matched, `2026-01-15`. `m.start()` and `m.end()` are the positions where it begins and ends, and `m.span()` gives both.
- The last line searches for `refund`, which does not occur, and prints `None`. In real code, always test for `None` before using a match.

Always write patterns as **raw strings**, with an `r` before the opening quote. In an ordinary string Python itself gives backslashes a meaning before the regex engine ever sees them (`"\b"` is a backspace character!). A raw string hands every backslash on untouched.

## The pattern language

### Literals and metacharacters

Most characters in a pattern stand for themselves: the pattern `cat` matches the text `cat`. A few characters have a special meaning and are called **metacharacters**: `. ^ $ * + ? { } [ ] \ | ( )`. To match one of them as an ordinary character, put a backslash in front (this is called **escaping**): `\.` matches a real full stop. `re.escape(s)` escapes a whole string for you.

### Character classes

A **character class** stands for "one character out of a set":

| Pattern | Matches |
|---|---|
| `.` | any character except newline (any at all with `re.DOTALL`) |
| `\d` / `\D` | a digit / a non-digit |
| `\w` / `\W` | a "word" character (letter, digit, underscore) / anything else |
| `\s` / `\S` | whitespace / non-whitespace |
| `[abc]` | one of a, b, c |
| `[a-z0-9_]` | one character in the ranges |
| `[^abc]` | any character **except** a, b, c |

In Python 3 the classes `\d`, `\w` and `\s` know about all the world's writing systems: `\d` also matches Arabic-Indic digits, and `\w` matches letters with accents. Pass the flag `re.ASCII` to limit them to the basic English set.

### Quantifiers

A **quantifier** says how many times the thing before it may be repeated:

| Pattern | Repetitions |
|---|---|
| `x*` | 0 or more |
| `x+` | 1 or more |
| `x?` | 0 or 1 |
| `x{3}` | exactly 3 |
| `x{2,5}` | 2 to 5 |
| `x{2,}` | 2 or more |

Quantifiers are **greedy**: they take as much text as they can, and give some back only if the remainder of the pattern would otherwise fail. Adding `?` after a quantifier makes it **lazy**: it takes as little as possible.

```python-run
import re
html = "<b>bold</b> and <i>italic</i>"
print(re.findall(r"<.+>", html))      # greedy: one giant match
print(re.findall(r"<.+?>", html))     # lazy: each tag
print(re.findall(r"<[^>]+>", html))   # better: a negated class, no backtracking surprises
```

The aim is to find each tag such as `<b>`. The pattern `<.+>` means "a `<`, then one or more of any character, then a `>`". Being greedy, `.+` runs to the end of the line and backs up only as far as the *last* `>`, so the result is one giant match containing the whole string. The lazy `<.+?>` stops at the first `>` it can and finds the four tags. The third pattern is the best habit: `[^>]+` means "one or more characters that are not `>`", which says exactly what is wanted and cannot run past the end of a tag.

### Anchors and boundaries

An **anchor** does not match a character. It matches a *position*:

| Pattern | Position |
|---|---|
| `^` | start of string (or of each line with `re.MULTILINE`) |
| `$` | end of string (or immediately before a final line break; each line with `re.MULTILINE`) |
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

Plain `cat` is found four times, including inside `concat` and `category`. `\bcat\b` requires a **word boundary** on both sides (a position between a word character and a non-word character, or the edge of the string) and finds only the standalone word. `\bcat\w*` finds the words that begin with `cat`: `cat`, `cats`, `category`.

### Alternation and groups

- `a|b` matches `a` or `b`. This "or" is called **alternation**, and it applies to everything on each side of the bar, so limit its reach with brackets: `gr(a|e)y` matches `gray` and `grey`.
- `( ... )` is a **capturing group**. It groups part of a pattern, so that a quantifier or an alternation applies to the whole group, *and* it remembers the text that part matched so you can get it out afterwards.
- `(?: ... )` groups **without** remembering.
- `(?P<name> ... )` is a **named group**: a capturing group you can refer to by name.
- `\1` (or `(?P=name)`) is a **backreference**: it matches the same text that group 1 matched earlier.

```python-run
import re

m = re.search(r"(\d{4})-(\d{2})-(\d{2})", "due 2026-01-15, late")
print(m.group(0), m.group(1), m.groups(), m.group(2, 3))

m = re.search(r"(?P<user>[\w.+-]+)@(?P<domain>[\w-]+(?:\.[\w-]+)+)", "mail robin@ohara.org now")
print(m.group("user"), m["domain"], m.groupdict())

print(re.findall(r"\b(\w+) \1\b", "it is is what it it was"))      # doubled words
print(re.fullmatch(r"gr(?:a|e)y", "grey") is not None)
```

- In the date pattern, the three pairs of brackets capture year, month and day. `m.group(0)` is the whole match, `m.group(1)` is the year, `m.groups()` is all three as a tuple, and `m.group(2, 3)` picks two of them.
- The second pattern names its groups. `(?P<user>[\w.+-]+)` captures the part before the `@`, and `(?P<domain>...)` the part after it; `m.group("user")`, `m["domain"]` and `m.groupdict()` read them by name.
- `\b(\w+) \1\b` finds a word followed by a space and *the same word again*, a doubled word such as `is is` or `it it`.
- `re.fullmatch(r"gr(?:a|e)y", "grey")` checks that the entire string is `gray` or `grey`.

### Lookarounds (zero-width assertions)

A **lookaround** checks what comes immediately after or immediately before the current position *without making it part of the match*. Lookarounds are for conditions like "a number, but only if the word EUR follows", where you want the number alone.

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

- `\d+(?= EUR)` matches digits only where ` EUR` follows; the result contains the digits alone: `['10', '30']`.
- `(?<=\$)\d+` matches digits only where a dollar sign comes before: `['45']`.
- The third pattern matches no characters at all, only positions: every place that has a digit before it and a multiple of three digits after it up to the end. Inserting a comma at each such position turns `1234567` into `1,234,567`.
- The last pattern states a password rule as three lookaheads from the start: somewhere there is a digit, somewhere a lowercase letter, somewhere a capital letter; and the whole thing has at least 8 characters.

## The functions

The `re` module offers a handful of functions that all take a pattern and a string:

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

The first line contrasts three functions on the same string: `match` finds no digit *at the start* and returns `None`; `search` finds the first digit anywhere; `fullmatch` confirms the entire string consists of allowed characters. `findall` returns all the numbers as strings; with two groups in the pattern it returns pairs. `finditer` gives match objects, from which positions can be read. `split` cuts the string at each comma or semicolon; with a capturing group in the pattern, the separators are kept in the result.

`findall` has a quirk that surprises everybody once. With **no** groups in the pattern it returns the whole matches; with **one** group it returns only that group's text; with **several** it returns tuples. Use a non-capturing `(?:...)` when you need brackets but want whole matches back, or use `finditer` for full control.

`match`, `search` and `fullmatch` are a classic trap. `re.match(r"\d+", "123abc")` succeeds, because the *beginning* of the string fits. To validate input, use `fullmatch`.

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

`re.sub(pattern, replacement, text)` replaces every match.

- Line 1 replaces each run of whitespace with a single space.
- Line 2 uses backreferences in the *replacement*: `\3/\2/\1` writes the three captured groups in reverse order, turning `2026-01-15` into `15/01/2026`.
- Line 3 does the same with named groups, written `\g<name>`.
- Line 4 passes a *function* as the replacement. It is called with each match object and returns the replacement text; here every number is doubled.
- `re.subn` also reports how many replacements were made.
- The two helper functions convert between `snake_case` and `camelCase` names, the second by inserting an underscore at every position that is followed by a capital letter and is not the start.

### Flags

A **flag** is an option that changes how a pattern is interpreted:

| Flag | Short | Effect |
|---|---|---|
| `re.IGNORECASE` | `re.I` | case-insensitive |
| `re.MULTILINE` | `re.M` | `^`/`$` match at each line |
| `re.DOTALL` | `re.S` | `.` matches newlines too |
| `re.VERBOSE` | `re.X` | ignore whitespace and allow `#` comments in the pattern |
| `re.ASCII` | `re.A` | `\w`, `\d`, `\s` ASCII-only |

Combine several flags with `|`. The most valuable one is **verbose mode**, which lets you spread a pattern over several lines and comment each part:

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

The pattern describes a line of a log file in five named parts, one per line, each with a comment. `LOG.match(line)` is tried on three lines; for the two that fit, `groupdict()` gives a ready-made dictionary of the parts, and the middle line is reported as not matching. The final line shows two more flags: with `re.M`, `^` matches at the start of every line, so the first word of each line is found; with `re.I`, upper and lower case are treated alike.

### Compiling

`re.compile` prepares a pattern once and gives you a pattern object with the same methods (`search`, `findall`, `sub` and so on). The module remembers recently used patterns anyway, so the main benefit is readability: define your patterns once, as named constants at the top of a module, and reuse them. There is also a small gain in speed inside loops.

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

Each line is a pattern for something that comes up again and again; the comment names what it finds. Try reading each one aloud ("one or more of: word character, dot, plus or dash; then an at-sign; ..."). Note the second-to-last line: removing extra spaces needs no regex at all, only `split` and `join`.

## When *not* to use regex

- For fixed pieces of text, the string tools `in`, `startswith`, `endswith`, `split`, `replace`, `partition` and `strip` are faster and clearer.
- For data in a defined format, use a real parser: `json`, `csv`, `html.parser` or BeautifulSoup, `urllib.parse`, `datetime.strptime`, `email`, `ipaddress`.
- Nested structures (matching brackets, HTML, programming languages) are beyond what regular expressions can describe.
- For complete validation of email addresses or web addresses according to the official standards, use a library, or a loose check followed by a confirmation step.

## Performance: catastrophic backtracking

Python's regex engine works by **backtracking**: it tries one way of fitting the pattern to the text and, if that fails further along, goes back and tries the next way. For most patterns that is quick. But a pattern with a quantifier inside a quantifier, where both can match the same characters, such as `(a+)+$`, `(\w+\s?)*$` or `(.*,)*`, offers an enormous number of ways to divide the text, and on input that *almost* matches the engine tries all of them before giving up. The time doubles with every extra character. If the input comes from users, an attacker can freeze your program with one short string; the attack is known as ReDoS (regular-expression denial of service).

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

The input is a row of `a` characters followed by `!`, which spoils the match at the very end. The times printed for 14, 18 and 22 letters grow about sixteen-fold from one line to the next. The equivalent pattern without the nested quantifier, `a+$`, deals with 5,000 letters in a tiny fraction of a second.

Defences: avoid nested quantifiers over the same characters; prefer precise classes (`[^,]*` in place of `.*`); anchor patterns; limit the length of the input; and from Python 3.11 use possessive quantifiers (`a++`) or atomic groups (`(?>...)`), which forbid backtracking.

## Worked example: a tiny tokenizer

A **tokenizer** (or lexer) cuts text into meaningful pieces called tokens, the first step in reading a formula or a programming language. Named groups combined with alternation make a compact one, a technique shown in the `re` documentation:

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

The pattern is five alternatives, each a named group: a number, a name, an operator, whitespace, or (as a catch-all) any other single character. `finditer` walks through the input, and `m.lastgroup` says *which* alternative matched. Whitespace is skipped, the catch-all raises an error giving the position, and everything else is yielded as a (kind, text) pair. The first input becomes a list of eleven tokens; the second fails at the `$`.

> [!INTERVIEW]
> Know: `match` (start only), `search` (anywhere) and `fullmatch` (whole string); greedy versus lazy quantifiers; capturing, non-capturing and named groups; what `findall` returns when the pattern has groups; why raw strings; `re.sub` with a function; and catastrophic backtracking. The practical skill being tested is whether you can read a pattern aloud ("one or more word characters, an at-sign, ...").

## Pitfalls recap

- Forgetting the `r` prefix: `"\b"` is a backspace, and `"\d"` produces a warning.
- Using `match` to validate (it accepts trailing junk) where `fullmatch` is needed.
- A greedy `.*` swallowing too much.
- `findall` returning the contents of groups when you expected whole matches.
- An unescaped `.` matching any character (`3.14` also matches `3x14`); write `\.` or `[.]` for a real dot.
- `$` also matching before a final line break; `\Z` is strict.
- Nested quantifiers, leading to exponential backtracking.

## Summary

A regex describes a text pattern with ordinary characters, classes, quantifiers, anchors, groups and lookarounds. Use `search`, `fullmatch`, `findall`, `finditer`, `sub` and `split`; write raw strings; use named groups and verbose mode for readability; compile the patterns you reuse. Prefer string methods and real parsers where they fit, and beware of backtracking blow-ups.

## Glossary

- **Regular expression (regex)** - a pattern, written in a small special language, that describes a set of strings.
- **Regex engine** - the machinery that tries to fit a pattern to text.
- **Raw string** - a string written `r"..."`, in which backslashes are left alone.
- **Metacharacter** - a character with a special meaning in a pattern, such as `.` or `*`.
- **Escaping** - putting `\` before a metacharacter to make it ordinary.
- **Character class** - a pattern for one character out of a set: `\d`, `\w`, `[a-z]`.
- **Quantifier** - how many repetitions are allowed: `*`, `+`, `?`, `{2,5}`.
- **Greedy / lazy** - taking as much / as little text as possible.
- **Anchor** - a pattern for a position, such as `^`, `$` or `\b`.
- **Word boundary** - the position between a word character and a non-word character.
- **Alternation** - "this or that", written `a|b`.
- **Capturing group** - a bracketed part of a pattern whose matched text is remembered.
- **Named group** - a capturing group referred to by name.
- **Backreference** - a reference to the text an earlier group matched.
- **Lookaround** - a check on what follows or precedes, which is not included in the match.
- **Match object** - the result of a successful search, holding the text, positions and groups.
- **Flag** - an option such as `re.IGNORECASE` or `re.VERBOSE`.
- **Backtracking** - undoing part of a match attempt to try another possibility.
- **ReDoS** - freezing a program with input that causes exponential backtracking.
- **Tokenizer (lexer)** - code that splits text into meaningful pieces.

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
