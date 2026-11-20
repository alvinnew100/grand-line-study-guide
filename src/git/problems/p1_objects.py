"""Git track problems, part 1: object ids and text formats."""

PROBLEMS = [
dict(
    id="git-blob-id",
    title="Compute a blob's object id",
    difficulty="Easy",
    pattern="Content-addressed storage",
    entry="blob_id",
    description=r"""
Git names every stored file by a hash of its content. For a file whose content is the byte string
`data`, the object id is the SHA-1 digest (40 lowercase hex characters) of

```
b"blob " + <decimal length of data in BYTES> + b"\0" + data
```

Write `blob_id(content)` that takes the file content as a Python `str`, encodes it as UTF-8 and returns
the object id. The length in the header counts **bytes after encoding**, not characters.

**Example:** `blob_id("")` → `"e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"` (the famous empty blob)

**Example:** `blob_id("hello\n")` → `"ce013625030ba8dba906f756967f9e9ca394464a"`
""",
    starter='''import hashlib

def blob_id(content: str) -> str:
    pass
''',
    solution='''import hashlib

def blob_id(content):
    data = content.encode("utf-8")
    header = b"blob " + str(len(data)).encode("ascii") + b"\\0"
    return hashlib.sha1(header + data).hexdigest()
''',
    tests=[
        [""],
        ["hello\n"],
        ["hello"],
        ["what is up, doc?"],
        ["naïve café\n"],
        ["日本語のテキスト\n"],
        ["a" * 10],
        ["line one\nline two\n"],
        ["x" * 5000],
        ["\n"],
        ["tab\tseparated\n"],
        ["🌿 branch\n"],
    ],
    examples=2,
    wrong_solutions=[
        '''import hashlib

def blob_id(content):
    return hashlib.sha1(content.encode("utf-8")).hexdigest()
''',
        '''import hashlib

def blob_id(content):
    data = content.encode("utf-8")
    header = ("blob %d\\0" % len(content)).encode()
    return hashlib.sha1(header + data).hexdigest()
''',
    ],
    guide=dict(
        prereqs="The lesson *Objects: blobs, trees, commits and tags*. Python `bytes` versus `str`, and `hashlib`.",
        intuition="Git does not hash the raw file. It first glues a tiny header in front that says what kind of object this is and how long it is, then hashes header and content together. Reproduce that byte sequence exactly and the standard SHA-1 function gives you the same id that `git hash-object` prints.",
        hints=[
            "Hash functions work on bytes. Convert the string with `.encode('utf-8')` before doing anything else.",
            "The header is the word `blob`, one space, the length written in decimal digits, and a single zero byte.",
            "Take `len()` of the encoded bytes, not of the original string: `'é'` is one character but two bytes.",
        ],
        brute_force="There is nothing to search here, so the 'naive' version is the common wrong one: hashing only the content. It gives a valid SHA-1, just not the one Git uses, so no object would ever be found under it.",
        approach="1. `data = content.encode('utf-8')`.\n2. Build `header = b'blob ' + str(len(data)).encode() + b'\\0'`.\n3. Return `hashlib.sha1(header + data).hexdigest()`.\n\n**Dry run** for `'hello\\n'`: the data is 6 bytes, so the header is `blob 6\\0` (7 bytes). The 13 bytes `blob 6\\0hello\\n` hash to `ce0136...`, which is what `echo hello | git hash-object --stdin` prints.",
        complexity="Time O(n) in the content size because SHA-1 reads each byte once; space O(n) for the encoded copy.",
        pitfalls="Using the character count instead of the byte count (breaks on any non-ASCII text). Writing the NUL as the two characters backslash-zero inside a raw string. Adding a newline the caller did not supply: `'hello'` and `'hello\\n'` are different blobs.",
        follow_up="Trees and commits use the same scheme with the words `tree` and `commit` in the header; the next problem builds on that.",
    ),
),
dict(
    id="git-tree-commit-id",
    title="Hash a tree and a commit (simplified format)",
    difficulty="Medium",
    pattern="Content-addressed storage",
    entry="commit_id",
    description=r"""
Real Git stores trees in a binary layout. This problem uses a **text-only simplified layout** so you can
focus on the idea: a commit names a tree, a tree names blobs, and every id is a hash of content.

Every object id is `sha1(f"{kind} {len(body)}\0".encode() + body)` as 40 hex characters, where `body`
is UTF-8 bytes and `len` is its length in bytes.

**Tree body.** You get `entries`, a list of `[mode, name, object_id]`. Sort the entries by `name`
(plain string order) and write one line per entry:

```
<mode> <name>\t<object_id>\n
```

The kind is `tree`. An empty entry list gives an empty body.

**Commit body.** Kind `commit`, built from these lines in this order:

```
tree <tree_id>\n
parent <parent_id>\n        (one line per parent, in the order given; none for a root commit)
author <author>\n
\n
<message>\n
```

Write `commit_id(entries, parents, author, message)` returning `[tree_id, commit_id]`.

**Example:** `commit_id([], [], "Ada", "init")` → the tree id is `sha1(b"tree 0\0")`, which is
`4b825dc642cb6eb9a060e54bf8d69288fbee4904` (the real empty-tree id, since an empty body is the same in both layouts).
""",
    starter='''import hashlib

def commit_id(entries, parents, author, message):
    pass
''',
    solution='''import hashlib

def _oid(kind, body):
    data = body.encode("utf-8")
    return hashlib.sha1(("%s %d" % (kind, len(data))).encode() + b"\\0" + data).hexdigest()

def commit_id(entries, parents, author, message):
    rows = sorted(entries, key=lambda e: e[1])
    tree_body = "".join("%s %s\\t%s\\n" % (m, n, o) for m, n, o in rows)
    tree = _oid("tree", tree_body)
    body = "tree %s\\n" % tree
    for p in parents:
        body += "parent %s\\n" % p
    body += "author %s\\n\\n%s\\n" % (author, message)
    return [tree, _oid("commit", body)]
''',
    tests=[
        [[], [], "Ada", "init"],
        [[["100644", "README.md", "ce013625030ba8dba906f756967f9e9ca394464a"]], [], "Ada <ada@example.com>", "add readme"],
        [[["100644", "b.txt", "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"], ["100644", "a.txt", "ce013625030ba8dba906f756967f9e9ca394464a"]], [], "Ada", "two files"],
        [[["100644", "a.txt", "ce013625030ba8dba906f756967f9e9ca394464a"], ["100644", "b.txt", "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"]], [], "Ada", "two files"],
        [[["100644", "a.txt", "ce013625030ba8dba906f756967f9e9ca394464a"]], ["1" * 40], "Ada", "child"],
        [[["100644", "a.txt", "ce013625030ba8dba906f756967f9e9ca394464a"]], ["1" * 40, "2" * 40], "Ada", "merge"],
        [[["100644", "a.txt", "ce013625030ba8dba906f756967f9e9ca394464a"]], ["2" * 40, "1" * 40], "Ada", "merge"],
        [[["040000", "src", "4b825dc642cb6eb9a060e54bf8d69288fbee4904"], ["100755", "run.sh", "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"]], ["3" * 40], "Grace", "add script\n\nlonger body"],
        [[["100644", "ünï.txt", "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"]], [], "Zoë", "non-ascii é"],
        [[["100644", "Z.txt", "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"], ["100644", "a.txt", "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"], ["100644", "B.txt", "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"]], [], "Ada", "case order"],
        [[], ["4" * 40], "Ada", ""],
    ],
    examples=2,
    wrong_solutions=[
        '''import hashlib

def _oid(kind, body):
    data = body.encode("utf-8")
    return hashlib.sha1(("%s %d" % (kind, len(data))).encode() + b"\\0" + data).hexdigest()

def commit_id(entries, parents, author, message):
    tree_body = "".join("%s %s\\t%s\\n" % (m, n, o) for m, n, o in entries)
    tree = _oid("tree", tree_body)
    body = "tree %s\\n" % tree
    for p in parents:
        body += "parent %s\\n" % p
    body += "author %s\\n\\n%s\\n" % (author, message)
    return [tree, _oid("commit", body)]
''',
        '''import hashlib

def _oid(kind, body):
    data = body.encode("utf-8")
    return hashlib.sha1(("%s %d" % (kind, len(body))).encode() + b"\\0" + data).hexdigest()

def commit_id(entries, parents, author, message):
    rows = sorted(entries, key=lambda e: e[1])
    tree_body = "".join("%s %s\\t%s\\n" % (m, n, o) for m, n, o in rows)
    tree = _oid("tree", tree_body)
    body = "tree %s\\n" % tree
    for p in sorted(parents):
        body += "parent %s\\n" % p
    body += "author %s\\n\\n%s\\n" % (author, message)
    return [tree, _oid("commit", body)]
''',
    ],
    guide=dict(
        prereqs="Problem *Compute a blob's object id* and the internals lesson on the four object types.",
        intuition="A commit id is a hash of text that contains the tree id, and the tree id is a hash of text that contains blob ids. Change one byte in one file and the blob id changes, so the tree body changes, so the tree id changes, so the commit body changes. That chain is why a commit id pins down the entire snapshot and all history behind it.",
        hints=[
            "Write one helper that takes a kind and a body string and returns the id. You will call it twice.",
            "Entries must be sorted so that the same set of files always produces the same tree id, no matter the input order.",
            "Parents are NOT sorted: the first parent is special in Git, so their order is part of the commit's identity.",
        ],
        brute_force="No search is involved. The straightforward construction is already optimal; the only way to go wrong is to assemble the bytes in a different shape from the specification.",
        approach="1. Sort entries by name and join `mode name<TAB>id<NEWLINE>` lines into the tree body.\n2. Hash it with kind `tree`.\n3. Build the commit body: `tree` line, one `parent` line each, `author` line, blank line, message, newline.\n4. Hash it with kind `commit` and return both ids.\n\n**Dry run** for no entries, no parents, author `Ada`, message `init`: tree body is empty, so the tree id is `sha1('tree 0\\0')` = `4b825d...`. The commit body is `tree 4b825d...\\nauthor Ada\\n\\ninit\\n`, 63 bytes, hashed behind the header `commit 63\\0`.",
        complexity="Time O(e log e + n) for e entries and n total bytes; space O(n).",
        pitfalls="Forgetting to sort entries, or sorting parents. Counting characters instead of bytes in the header (the non-ASCII test catches it). Dropping the blank line between the headers and the message.",
        follow_up="Real trees store the id as 20 raw bytes and sort directories as if their name ended in a slash. Try `git cat-file -p HEAD^{tree}` to see a real one decoded.",
    ),
),
dict(
    id="git-abbreviate-ids",
    title="Shortest unique object-id prefixes",
    difficulty="Medium",
    pattern="Sorting / prefixes",
    entry="abbreviate",
    description=r"""
`git log --oneline` shows short ids such as `3f9c2ab`. Git picks a prefix long enough to be unambiguous
among all objects in the repository, with a minimum length.

Write `abbreviate(ids, min_len)`. `ids` is a list of **distinct** lowercase hex strings, all of the same
length `L` (`min_len <= L`). For each id return the shortest prefix of length at least `min_len` that is
not a prefix of any other id in the list. Return the prefixes in the same order as the input.

**Example:** `abbreviate(["abcd12", "abcd34", "ffff00"], 4)` → `["abcd1", "abcd3", "ffff"]`

**Example:** `abbreviate(["a1b2c3"], 4)` → `["a1b2"]`

The list may hold tens of thousands of ids, so comparing every pair is too slow.
""",
    starter='''def abbreviate(ids, min_len):
    pass
''',
    solution='''def abbreviate(ids, min_len):
    order = sorted(range(len(ids)), key=lambda i: ids[i])
    def common(a, b):
        n = 0
        for x, y in zip(a, b):
            if x != y:
                break
            n += 1
        return n
    need = [min_len] * len(ids)
    for k in range(len(order) - 1):
        i, j = order[k], order[k + 1]
        c = common(ids[i], ids[j]) + 1
        if c > need[i]:
            need[i] = c
        if c > need[j]:
            need[j] = c
    return [ids[i][:need[i]] for i in range(len(ids))]
''',
    tests=[
        [["abcd12", "abcd34", "ffff00"], 4],
        [["a1b2c3"], 4],
        [[], 4],
        [["aaaaaa", "aaaaab"], 4],
        [["aaaaaa", "aaaaab"], 6],
        [["123456", "123499", "123999", "129999", "199999", "999999"], 1],
        [["ffff00", "abcd34", "abcd12"], 4],
        [["0a", "0b", "1a"], 1],
        [["abc000", "abd000", "abe000", "abc111"], 2],
        [["%040x" % (i * 7919 * 104729) for i in range(1, 400)], 7],
        [["%08x" % i for i in range(8000)], 4],
        [["deadbeef", "deadbeee", "deadbee0", "dead0000", "beef0000"], 4],
    ],
    examples=2,
    wrong_solutions=[
        '''def abbreviate(ids, min_len):
    return [x[:min_len] for x in ids]
''',
        '''def abbreviate(ids, min_len):
    out = []
    for x in ids:
        n = min_len
        while sum(1 for y in ids[:50] if y.startswith(x[:n])) > 1:
            n += 1
        out.append(x[:n])
    return out
''',
    ],
    guide=dict(
        prereqs="String prefixes and sorting. The lesson on revision selection explains why short ids work at all.",
        intuition="After sorting, the ids that share the longest prefix with a given id are its immediate neighbours in the sorted list. So each id only needs to be compared with the one before and the one after it, never with the whole list.",
        hints=[
            "A prefix is unique when it is one character longer than the longest prefix shared with any other id.",
            "Sort the ids. Why can the worst clash for an id only come from a sorted neighbour?",
            "Compute the common-prefix length for each adjacent pair once and update the requirement of both members of the pair.",
        ],
        brute_force="For each id, grow the prefix from `min_len` and scan all other ids with `startswith`. That is O(n^2 L) and takes far too long for many thousands of ids.",
        approach="1. Sort indices by id.\n2. For each adjacent pair compute `c = common_prefix_length + 1`.\n3. Each id needs `max(min_len, c_left, c_right)` characters.\n4. Slice and return in input order.\n\n**Dry run** on `abcd12, abcd34, ffff00` with minimum 4: sorted order is the same. Pair one shares `abcd` (4) so both need 5. Pair two shares nothing so needs 1, below the minimum. Result: `abcd1`, `abcd3`, `ffff`.",
        complexity="Time O(n log n * L) for the sort plus O(nL) for neighbour comparisons; space O(n).",
        pitfalls="Returning results in sorted order instead of input order. Forgetting the minimum length. Using only the left neighbour.",
        follow_up="Git uses the same neighbour idea inside its sorted pack index. A trie gives the answer too, at a higher memory cost.",
    ),
),
dict(
    id="git-gitignore-match",
    title="Match .gitignore patterns",
    difficulty="Hard",
    pattern="Pattern matching",
    entry="is_ignored",
    description=r"""
Implement a simplified `.gitignore` matcher: `is_ignored(patterns, path)` returns `True` when the **file**
at `path` (relative to the repository root, components separated by `/`, never ending in `/`) is ignored.

Process `patterns` top to bottom; the **last pattern that matches decides**. If none matches, the file is not ignored.

Rules for one pattern line:

1. Strip surrounding whitespace. Skip empty lines and lines starting with `#`.
2. A leading `!` negates the pattern: when it matches, the file becomes *not ignored*.
3. A trailing `/` means the pattern matches **directories only**. Remove it before matching.
4. If the remaining pattern contains a `/` (at the start or in the middle) it is **anchored**: it must
   match starting at the repository root. A leading `/` is then removed. A pattern with no `/` may match
   starting at **any depth**.
5. Split the pattern on `/` into segments. A segment that is exactly `**` matches zero or more whole
   path components. In any other segment `*` matches any run of characters except `/`, `?` matches
   exactly one character except `/`, and every other character (including `[` and `.`) matches itself.
6. A pattern matches the path when its segments match **the whole path**, or match **any leading
   directory of it** (for `a/b/c.txt` the leading directories are `a` and `a/b`); a matched directory
   takes everything inside with it. A directory-only pattern can only match a leading directory.

Simplification: unlike real Git, a `!` rule here *can* re-include a file inside an ignored directory.

**Example:** `is_ignored(["*.log", "!keep.log"], "logs/keep.log")` → `False`

**Example:** `is_ignored(["build/"], "app/build/out.o")` → `True`
""",
    starter='''def is_ignored(patterns, path):
    pass
''',
    solution='''import re

def _seg(seg, name):
    rx = ""
    for ch in seg:
        if ch == "*":
            rx += "[^/]*"
        elif ch == "?":
            rx += "[^/]"
        else:
            rx += re.escape(ch)
    return re.fullmatch(rx, name) is not None

def _match(psegs, parts):
    if not psegs:
        return not parts
    if psegs[0] == "**":
        return any(_match(psegs[1:], parts[k:]) for k in range(len(parts) + 1))
    if not parts:
        return False
    return _seg(psegs[0], parts[0]) and _match(psegs[1:], parts[1:])

def is_ignored(patterns, path):
    parts = path.split("/")
    ignored = False
    for raw in patterns:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        neg = line.startswith("!")
        if neg:
            line = line[1:]
        dir_only = line.endswith("/")
        if dir_only:
            line = line[:-1]
        anchored = "/" in line
        if line.startswith("/"):
            line = line[1:]
        psegs = line.split("/")
        if not anchored:
            psegs = ["**"] + psegs
        hit = False
        for k in range(1, len(parts) + 1):
            if k == len(parts) and dir_only:
                continue
            if _match(psegs, parts[:k]):
                hit = True
                break
        if hit:
            ignored = not neg
    return ignored
''',
    tests=[
        [["*.log", "!keep.log"], "logs/keep.log"],
        [["build/"], "app/build/out.o"],
        [["*.log"], "logs/debug.log"],
        [["build/"], "build"],
        [["/todo.txt"], "docs/todo.txt"],
        [["/todo.txt"], "todo.txt"],
        [["docs/*.pdf"], "docs/a.pdf"],
        [["docs/*.pdf"], "docs/sub/a.pdf"],
        [["docs/**/*.pdf"], "docs/sub/deep/a.pdf"],
        [["docs/**/*.pdf"], "docs/a.pdf"],
        [["# comment", "", "  node_modules/  "], "web/node_modules/x/index.js"],
        [["*.py[co]"], "a.pyc"],
        [["temp?"], "src/temp1/data.bin"],
        [["temp?"], "src/temp12/data.bin"],
        [["*", "!*.md"], "README.md"],
        [["!*.md", "*"], "README.md"],
        [["**/cache"], "a/b/cache/x"],
        [["src/gen"], "lib/src/gen/a.c"],
        [["a.b"], "aXb"],
        [[], "anything.txt"],
    ],
    examples=2,
    wrong_solutions=[
        '''import fnmatch

def is_ignored(patterns, path):
    ignored = False
    for p in patterns:
        p = p.strip()
        if not p or p.startswith("#"):
            continue
        neg = p.startswith("!")
        if neg:
            p = p[1:]
        if fnmatch.fnmatch(path, p) or fnmatch.fnmatch(path.split("/")[-1], p):
            ignored = not neg
    return ignored
''',
        '''import re

def is_ignored(patterns, path):
    for raw in patterns:
        line = raw.strip().rstrip("/").lstrip("/")
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        rx = re.escape(line).replace("\\\\*", "[^/]*").replace("\\\\?", "[^/]")
        if re.search("(^|/)" + rx + "(/|$)", path):
            return True
    return False
''',
    ],
    guide=dict(
        prereqs="The lesson on recording changes (the ignore-file section). Recursion over lists, and either regular expressions or a hand-written wildcard matcher.",
        intuition="Three independent ideas are stacked: (1) the last matching line wins, which is a simple loop with a variable; (2) ignoring a directory ignores everything under it, so you test every leading directory as well as the full path; (3) anchoring, which you can remove from the picture by turning an unanchored pattern into an anchored one that starts with `**`.",
        hints=[
            "Deal with the decorations first: comment, `!`, trailing `/`, leading `/`. What is left is a plain list of segments.",
            "An unanchored pattern `x` behaves exactly like the anchored pattern `**/x`. Rewrite it and you only need one matcher.",
            "Match segment lists recursively: a `**` segment tries to swallow 0, 1, 2, ... components; any other segment must match exactly one component.",
        ],
        brute_force="Translate the whole pattern into one giant regular expression. It works for simple cases but the interactions of anchoring, directory-only patterns and `**` make the single regex hard to get right; many attempts wrongly let `*` cross a `/`.",
        approach="For each pattern: strip, skip comments, record negation and directory-only flags, decide anchoring, split on `/`, and prepend `**` if unanchored. Then for `k = 1..len(parts)` test whether the segments match the first `k` components (skipping the full path when the pattern is directory-only). On a hit set `ignored = not negated`.\n\n**Dry run** `['build/']` against `app/build/out.o`: flags `dir_only=True`, unanchored, segments `['**','build']`. Prefix `app`: `**` takes zero then `build` vs `app` fails; `**` takes one and nothing is left, fails. Prefix `app/build`: `**` takes `app`, `build` matches `build`, hit. Result `True`.",
        complexity="With p pattern segments and d path components, the recursive match is O(p * d) per prefix in practice (exponential only with many `**`), so about O(lines * p * d^2). Paths are short, so this is fast.",
        pitfalls="Letting `*` match across `/`. Treating `.` as a regex wildcard (the `a.b` test). Forgetting that a directory-only pattern must not match the file itself (`build/` versus a file named `build`). Returning on the first match instead of the last.",
        follow_up="Real Git adds bracket classes like `[co]`, escaping with backslash, per-directory ignore files, and the rule that a file cannot be re-included when its parent directory is excluded. `git check-ignore -v path` tells you which line decided.",
    ),
),
dict(
    id="git-conventional-commit",
    title="Parse and validate a Conventional Commit message",
    difficulty="Medium",
    pattern="Parsing",
    entry="parse_commit",
    description=r"""
Many teams require commit messages in the *Conventional Commits* shape so that changelogs and version
bumps can be automated. Write `parse_commit(message)` that validates a message and returns a dict, or
`None` if the message is invalid.

The **header** is the first line and must look like

```
<type>[(<scope>)][!]: <description>
```

- `type` is one of `feat fix docs style refactor perf test build ci chore revert` (lowercase).
- `scope` is optional; when present it is inside parentheses and consists of one or more of `a-z`, `0-9`, `-`.
- `!` is optional and marks a breaking change.
- Then exactly a colon and **one space**.
- `description` is non-empty, does not start with a space and does not end with a period.
- The whole header is at most 72 characters long.

If the message has more than one line, the **second line must be empty** (it separates header and body).

The commit is **breaking** when the header has `!`, or when any line after the header starts with
`BREAKING CHANGE: ` or `BREAKING-CHANGE: `.

Return `{"type": ..., "scope": ... or None, "description": ..., "breaking": True/False}`.

**Example:** `parse_commit("feat(api)!: drop v1 endpoints")` →
`{"type": "feat", "scope": "api", "description": "drop v1 endpoints", "breaking": True}`

**Example:** `parse_commit("Fixed stuff")` → `None`
""",
    starter='''def parse_commit(message):
    pass
''',
    solution='''import re

_TYPES = "feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert"
_RX = re.compile(r"(" + _TYPES + r")(?:\\(([a-z0-9-]+)\\))?(!)?: (.+)")

def parse_commit(message):
    lines = message.split("\\n")
    header = lines[0]
    if len(header) > 72:
        return None
    m = _RX.fullmatch(header)
    if not m:
        return None
    desc = m.group(4)
    if desc.startswith(" ") or desc.endswith("."):
        return None
    if len(lines) > 1 and lines[1] != "":
        return None
    breaking = m.group(3) is not None
    for line in lines[1:]:
        if line.startswith("BREAKING CHANGE: ") or line.startswith("BREAKING-CHANGE: "):
            breaking = True
    return {"type": m.group(1), "scope": m.group(2), "description": desc, "breaking": breaking}
''',
    tests=[
        ["feat(api)!: drop v1 endpoints"],
        ["Fixed stuff"],
        ["fix: handle empty cart"],
        ["fix: handle empty cart."],
        ["feat(ui): add dark mode\n\nBREAKING CHANGE: theme tokens renamed"],
        ["feat(ui): add dark mode\nbody without blank line"],
        ["docs(read-me2): fix typo\n\nlonger explanation here"],
        ["Feat: capital type"],
        ["feat(UI): capital scope"],
        ["feat():empty scope"],
        ["chore:no space"],
        ["chore:  two spaces"],
        ["perf: " + "x" * 66],
        ["perf: " + "x" * 67],
        ["wip: not an allowed type"],
        ["refactor!: rename module\n\nBREAKING-CHANGE: import paths differ"],
        ["test: add cases\n\nthis mentions BREAKING CHANGE: but not at line start"],
        ["fix(core): "],
    ],
    examples=2,
    wrong_solutions=[
        '''def parse_commit(message):
    header = message.split("\\n")[0]
    if ": " not in header:
        return None
    left, desc = header.split(": ", 1)
    breaking = left.endswith("!")
    left = left.rstrip("!")
    scope = None
    if "(" in left:
        left, scope = left[:-1].split("(", 1)
    return {"type": left, "scope": scope, "description": desc, "breaking": breaking}
''',
        '''import re

def parse_commit(message):
    lines = message.split("\\n")
    m = re.fullmatch(r"(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(?:\\(([a-z0-9-]+)\\))?(!)?: (.+)", lines[0])
    if not m or m.group(4).endswith(".") or m.group(4).startswith(" "):
        return None
    if len(lines) > 1 and lines[1] != "":
        return None
    return {"type": m.group(1), "scope": m.group(2), "description": m.group(4), "breaking": m.group(3) is not None}
''',
    ],
    guide=dict(
        prereqs="The lesson on commit-message conventions in *Team workflows in practice*. Regular expressions with optional groups.",
        intuition="The header is a tiny formal language, which makes it a perfect fit for one anchored regular expression with optional groups. Everything the regex cannot express conveniently (length limit, trailing period, the blank second line, footers) is a handful of plain `if` statements around it.",
        hints=[
            "Split the message into lines first; almost every rule talks about a specific line.",
            "Use `re.fullmatch` so that leftovers at either end make the header invalid. Give the scope and the `!` their own optional groups.",
            "Breaking can come from two places. Compute it from the header, then scan the remaining lines for a footer that *starts* with the marker.",
        ],
        brute_force="Chop the header up with `split(':')`, `find('(')` and friends. It can be made to work, but every optional part doubles the cases, and loose versions accept garbage such as unknown types or uppercase scopes.",
        approach="1. `lines = message.split('\\n')`; reject a header longer than 72.\n2. Full-match `type (scope)? !? ': ' description`.\n3. Reject descriptions starting with a space or ending with `.`.\n4. If there is a second line it must be empty.\n5. `breaking = bang or any footer line starts with the marker`.\n\n**Dry run** `feat(api)!: drop v1 endpoints`: groups are `feat`, `api`, `!`, `drop v1 endpoints`; one line only, so no body checks; breaking is true from the bang.",
        complexity="Time and space O(n) in the message length.",
        pitfalls="Using `match` instead of `fullmatch`. Accepting `chore:no space`. Counting the 72 limit on the description instead of the whole header. Detecting the breaking marker in the middle of a sentence.",
        follow_up="Map the result to a semantic-version bump: breaking → major, `feat` → minor, `fix` → patch. Tools such as commitlint apply rules like these in a `commit-msg` hook.",
    ),
),
dict(
    id="git-sort-version-tags",
    title="Sort version tags",
    difficulty="Medium",
    pattern="Sorting with custom keys",
    entry="sort_tags",
    description=r"""
`git tag` lists tags alphabetically, which puts `v1.10.0` before `v1.9.0`. Write `sort_tags(tags)` that
returns the valid version tags in ascending **semantic version** order and silently drops everything else.

A valid tag is: an optional leading `v`, then `MAJOR.MINOR.PATCH` (three non-negative decimal integers),
then optionally `-` followed by a pre-release made of one or more dot-separated identifiers, each
consisting of one or more of `0-9 A-Z a-z -`.

Ordering:

1. Compare major, minor, patch numerically.
2. A version **with** a pre-release is lower than the same version without one (`1.0.0-rc.1 < 1.0.0`).
3. Two pre-releases are compared identifier by identifier: identifiers made only of digits compare
   numerically; a numeric identifier is lower than a non-numeric one; two non-numeric identifiers compare
   as plain strings; if all shared identifiers are equal, the one with fewer identifiers is lower.
4. Tags that compare equal (for example `v1.0.0` and `1.0.0`) keep their input order.

**Example:** `sort_tags(["v1.10.0", "v1.9.0", "v1.9.0-rc.1", "latest"])` → `["v1.9.0-rc.1", "v1.9.0", "v1.10.0"]`
""",
    starter='''def sort_tags(tags):
    pass
''',
    solution='''import re

_RX = re.compile(r"v?(\\d+)\\.(\\d+)\\.(\\d+)(?:-([0-9A-Za-z-]+(?:\\.[0-9A-Za-z-]+)*))?")

def sort_tags(tags):
    keyed = []
    for t in tags:
        m = _RX.fullmatch(t)
        if not m:
            continue
        core = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        pre = m.group(4)
        if pre is None:
            pk = (1, ())
        else:
            ids = []
            for part in pre.split("."):
                if part.isdigit():
                    ids.append((0, int(part), ""))
                else:
                    ids.append((1, 0, part))
            pk = (0, tuple(ids))
        keyed.append(((core, pk), t))
    keyed.sort(key=lambda kv: kv[0])
    return [t for _, t in keyed]
''',
    tests=[
        [["v1.10.0", "v1.9.0", "v1.9.0-rc.1", "latest"]],
        [["v2.0.0", "v1.0.0", "v1.2.0", "v1.10.0", "v1.9.9"]],
        [[]],
        [["nightly", "release", "v1", "v1.2", "1.2.3.4"]],
        [["1.0.0", "v1.0.0", "v0.9.9"]],
        [["v1.0.0", "1.0.0", "v0.9.9"]],
        [["1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-alpha.beta", "1.0.0-beta", "1.0.0-beta.2", "1.0.0-beta.11", "1.0.0-rc.1", "1.0.0"][::-1]],
        [["v1.0.0-rc.10", "v1.0.0-rc.9", "v1.0.0-rc.2"]],
        [["v1.0.0-1", "v1.0.0-a", "v1.0.0-10", "v1.0.0-2"]],
        [["v3.0.0-", "v3.0.0-a..b", "v3.0.0-ok", "V3.0.0"]],
        [["v0.0.1", "v0.0.10", "v0.0.2", "v0.1.0", "v0.0.9"]],
        [["v10.0.0", "v9.99.99", "v9.100.0"]],
        [["v1.2.3-x-y.1", "v1.2.3-x.1", "v1.2.3"]],
        [["v%d.%d.%d" % (i % 7, (i * 13) % 23, (i * 31) % 17) for i in range(300)]],
    ],
    examples=1,
    wrong_solutions=[
        '''def sort_tags(tags):
    return sorted(t for t in tags if t[:1] in "v0123456789" and t.count(".") >= 2)
''',
        '''import re

def sort_tags(tags):
    out = []
    for t in tags:
        m = re.fullmatch(r"v?(\\d+)\\.(\\d+)\\.(\\d+)(-[0-9A-Za-z.-]+)?", t)
        if m:
            out.append(((int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4) or ""), t))
    out.sort(key=lambda kv: kv[0])
    return [t for _, t in out]
''',
    ],
    guide=dict(
        prereqs="The tagging lesson. Python tuple comparison and `sort` with a `key` (and the fact that Python's sort is stable).",
        intuition="Sorting is easy once every tag is turned into a key whose natural tuple ordering equals the ordering you want. The art is in designing the key: numbers as ints, a flag that pushes releases after pre-releases, and a per-identifier triple that makes numeric identifiers sort before textual ones.",
        hints=[
            "Validate with one regular expression and capture the three numbers and the optional pre-release.",
            "Give a release the key `(1, ())` and a pre-release `(0, identifiers)`. Tuples compare element by element, so the flag settles rule 2.",
            "Encode a numeric identifier as `(0, number, '')` and a textual one as `(1, 0, text)`. Tuple comparison then implements rule 3, including the shorter-is-lower case.",
        ],
        brute_force="Write a `cmp(a, b)` function with nested ifs and use `functools.cmp_to_key`. It is correct if careful, but long and easy to get subtly wrong; plain string sorting, the really naive approach, fails as soon as a number reaches two digits.",
        approach="Parse, build `(core, pre_key)` for each valid tag, sort by key (stable, so equal versions keep input order), and return the tags.\n\n**Dry run** on `v1.10.0, v1.9.0, v1.9.0-rc.1, latest`: `latest` fails the regex. Keys: `((1,10,0),(1,()))`, `((1,9,0),(1,()))`, `((1,9,0),(0,((1,0,'rc'),(0,1,''))))`. Sorting puts the rc first (flag 0), then 1.9.0, then 1.10.0.",
        complexity="Time O(n log n) comparisons on short keys; space O(n).",
        pitfalls="Comparing numbers as strings. Treating the pre-release as one string so that `rc.10 < rc.9`. Mixing ints and strings in one tuple position, which raises `TypeError` in Python 3. Accepting a capital `V` or an empty identifier.",
        follow_up="Git can do this itself: `git tag --sort=version:refname` (alias `-v:refname`), with `versionsort.suffix` controlling pre-release suffixes.",
    ),
),
dict(
    id="git-parse-refspec",
    title="Parse a refspec",
    difficulty="Easy",
    pattern="Parsing",
    entry="parse_refspec",
    description=r"""
A refspec tells `git fetch` and `git push` which references to transfer and where to put them, for
example `+refs/heads/*:refs/remotes/origin/*`.

Write `parse_refspec(spec)` returning a dict
`{"force": bool, "src": str, "dst": str or None, "pattern": bool}` or `None` if the spec is invalid
under these simplified rules:

1. An optional leading `+` sets `force` and is removed.
2. If there is no `:`, the whole rest is `src` and `dst` is `None`. With exactly one `:`, the left side is
   `src` and the right side is `dst`. More than one `:` is invalid.
3. Whitespace anywhere is invalid. `src` and `dst` may not both be missing/empty.
4. An empty `dst` after a colon (`main:`) is invalid. An empty `src` before a colon (`:topic`) is valid and
   means "delete `dst`"; it cannot be combined with a `*`.
5. Each side may contain at most one `*`. When `dst` is present, either both sides contain a `*` or
   neither does. Without a `dst`, `src` may not contain a `*`.
6. `pattern` is `True` when the refspec uses `*`.

**Example:** `parse_refspec("+refs/heads/*:refs/remotes/origin/*")` →
`{"force": True, "src": "refs/heads/*", "dst": "refs/remotes/origin/*", "pattern": True}`

**Example:** `parse_refspec("main")` → `{"force": False, "src": "main", "dst": None, "pattern": False}`
""",
    starter='''def parse_refspec(spec):
    pass
''',
    solution='''def parse_refspec(spec):
    if any(ch.isspace() for ch in spec):
        return None
    force = spec.startswith("+")
    if force:
        spec = spec[1:]
    if spec.count(":") > 1:
        return None
    if ":" in spec:
        src, dst = spec.split(":")
        if dst == "":
            return None
    else:
        src, dst = spec, None
        if src == "":
            return None
    if src.count("*") > 1 or (dst is not None and dst.count("*") > 1):
        return None
    if dst is None:
        if "*" in src:
            return None
        pattern = False
    else:
        if ("*" in src) != ("*" in dst):
            return None
        pattern = "*" in dst
    return {"force": force, "src": src, "dst": dst, "pattern": pattern}
''',
    tests=[
        ["+refs/heads/*:refs/remotes/origin/*"],
        ["main"],
        ["main:main"],
        [":topic"],
        ["main:"],
        [""],
        ["+"],
        [":"],
        ["a:b:c"],
        ["refs/heads/*:refs/remotes/origin/main"],
        ["refs/heads/main:refs/remotes/origin/*"],
        ["refs/heads/*"],
        ["refs/heads/qa*:refs/remotes/origin/qa*"],
        ["refs/*/x/*:refs/y/*"],
        ["+HEAD:refs/heads/deploy"],
        ["main :main"],
        [":refs/heads/*"],
        ["refs/tags/v1.0:refs/tags/v1.0"],
    ],
    examples=2,
    wrong_solutions=[
        '''def parse_refspec(spec):
    force = spec.startswith("+")
    spec = spec.lstrip("+")
    if ":" in spec:
        src, dst = spec.split(":", 1)
    else:
        src, dst = spec, None
    return {"force": force, "src": src, "dst": dst, "pattern": "*" in spec}
''',
    ],
    guide=dict(
        prereqs="The internals lesson on the refspec. Basic string methods.",
        intuition="A refspec is `[+]source[:destination]`. Peel the pieces off from the outside in (plus sign, then the colon split), then run the consistency checks on the two halves. No clever algorithm is needed; the exercise is about being exhaustive with the rules.",
        hints=[
            "Handle the `+` first and remember it in a boolean; the rest of the logic should never see it.",
            "`str.count(':')` tells you which of the three shapes you have: no colon, one colon, or invalid.",
            "The wildcard rule is an equality of two booleans: `('*' in src) == ('*' in dst)`.",
        ],
        brute_force="A single regular expression can validate most of this, but the 'star on both sides or neither' rule needs a lookahead or a second check anyway, and the result is harder to read than straight-line code.",
        approach="Reject whitespace; strip `+`; count colons; split; reject empty destination or totally empty spec; check star counts; compute `pattern`.\n\n**Dry run** `:topic`: no plus, one colon, `src=''`, `dst='topic'`, no stars on either side, so the result is a delete refspec with `pattern` false. **Dry run** `refs/heads/*`: no colon so `dst=None`, but `src` has a star, invalid.",
        complexity="Time and space O(n) in the length of the string.",
        pitfalls="`lstrip('+')` removes several plus signs. `split(':', 1)` hides the three-part error. Forgetting that `:dst` is legal while `src:` is not (in this problem's rules).",
        follow_up="Write `map_ref(spec, name)` that returns the destination name for a concrete source ref by substituting what the `*` matched; that is exactly what fetch does to build remote-tracking names.",
    ),
),
]
