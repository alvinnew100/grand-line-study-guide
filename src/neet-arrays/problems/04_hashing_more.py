import random

_r = random.Random(2500)
_L = "abcdefghijklmnopqrstuvwxyz"


def _lc(slug):
    return f"https://leetcode.com/problems/{slug}/"


def _nc(slug):
    return f"https://neetcode.io/problems/{slug}"


# ---------- big inputs ----------
_lcp_prefix = "".join(_r.choice(_L) for _ in range(90))
_lcp_big = [_lcp_prefix + "".join(_r.choice(_L) for _ in range(_r.randint(1, 10))) for _ in range(1000)]
_lcp_big2 = ["a" * 200] * 400 + ["a" * 150 + "b"]

_names = ["".join(_r.choice("abc.") for _ in range(_r.randint(1, 6))).strip(".") or "x" for _ in range(4000)]
_emails_big = [f"{n}{'+' + n[::-1] if i % 3 == 0 else ''}@{_r.choice(['mail.com', 'm.ail.com', 'ex.org'])}"
               for i, n in enumerate(_names)]

_iso_s = "".join(_r.choice(_L[:20]) for _ in range(50000))
_perm = dict(zip(_L, random.Random(5).sample(_L, 26)))
_iso_t = "".join(_perm[c] for c in _iso_s)
_iso_t_bad = _iso_t[:-1] + ("a" if _iso_t[-1] != "a" else "b")

_wp_pat = "".join(_r.choice("abcdefgh") for _ in range(10000))
_wp_words = {c: w for c, w in zip("abcdefgh", ["dog", "cat", "fish", "bird", "ant", "owl", "bee", "fox"])}
_wp_s = " ".join(_wp_words[c] for c in _wp_pat)
_wp_s_bad = " ".join((_wp_words[c] if i != 9990 else "emu") for i, c in enumerate(_wp_pat))

_fb_big = []
while len(_fb_big) < 20000:
    _fb_big += [1] + [0] * _r.randint(1, 6)
_fb_big = _fb_big[:20000]


def _fb_cap(bed):
    bed = bed[:]
    c = 0
    for i in range(len(bed)):
        if bed[i] == 0 and (i == 0 or bed[i - 1] == 0) and (i == len(bed) - 1 or bed[i + 1] == 0):
            bed[i] = 1
            c += 1
    return c


_fb_cap_big = _fb_cap(_fb_big)

_ball_big = "".join(_r.choice("balonxyz") for _ in range(50000))

_piv_left = [_r.randint(-1000, 1000) for _ in range(10000)]
_piv_right = _piv_left[::-1]
_piv_big = _piv_left + [77] + _piv_right          # pivot exactly in the middle (maybe earlier too)
_piv_none = [_r.randint(1, 1000) for _ in range(20000)] + [10**8]

_na_big = [_r.randint(-10**5, 10**5) for _ in range(10000)]
_na_q = [sorted([_r.randint(0, 9999), _r.randint(0, 9999)]) for _ in range(4000)]

_dis_big = [_r.randint(1, 30000) for _ in range(30000)]

_maj2_big = [5] * 10100 + [-9] * 10050 + [_r.randint(100, 10**6) for _ in range(9850)]
random.Random(8).shuffle(_maj2_big)
_maj2_none = list(range(10000)) * 3

_css_big_no = [1] * 20000                    # k larger than total sum -> False
_css_big_yes = [_r.randint(1, 10**6) * 2 + 1 for _ in range(20000)]

_set_ops, _set_args = ["MyHashSet"], [[]]
for _ in range(6000):
    op = _r.choice(["add", "add", "remove", "contains", "contains"])
    _set_ops.append(op)
    _set_args.append([_r.randint(0, 3000) * 1009])
_map_ops, _map_args = ["MyHashMap"], [[]]
for _ in range(6000):
    op = _r.choice(["put", "put", "get", "get", "remove"])
    _map_ops.append(op)
    k = _r.randint(0, 3000) * 1009
    _map_args.append([k, _r.randint(0, 10**6)] if op == "put" else [k])

_sort_big = [_r.randint(-50000, 50000) for _ in range(15000)]

_np_big = list(range(1, 8001))
random.Random(13).shuffle(_np_big)
_np_desc = list(range(8000, 0, -1))


PROBLEMS = [
# ---------------------------------------------------------------------------
dict(
    id="longest-common-prefix",
    title="Longest Common Prefix",
    difficulty="Easy",
    pattern="Arrays & Hashing",
    leetcode=_lc("longest-common-prefix"),
    neetcode=_nc("longest-common-prefix"),
    entry="longestCommonPrefix",
    description=r"""
A **prefix** of a string is any piece taken from its start (`"fl"` is a prefix of `"flower"`).
Given a list of strings `strs`, return the longest string that is a prefix of **every** string in the
list. If the strings share no starting characters, return the empty string `""`.

**Constraints**

- `1 <= len(strs) <= 200` on LeetCode (our judge also uses 1000 strings)
- `0 <= len(strs[i]) <= 200`, lowercase English letters

**Example 1:** `strs = ["flower", "flow", "flight"]` → `"fl"`

**Example 2:** `strs = ["dog", "racecar", "car"]` → `""`
""",
    starter='''class Solution:
    def longestCommonPrefix(self, strs: List[str]) -> str:
        pass
''',
    solution='''class Solution:
    def longestCommonPrefix(self, strs):
        first = strs[0]
        for i, ch in enumerate(first):
            for w in strs:
                if i == len(w) or w[i] != ch:
                    return first[:i]
        return first
''',
    tests=[
        [["flower", "flow", "flight"]],
        [["dog", "racecar", "car"]],
        [["alone"]],
        [[""]],
        [["", "b"]],
        [["ab", "a"]],
        [["a", "ab"]],
        [["same", "same", "same"]],
        [["interview", "internet", "interval", "into"]],
        [["cir", "car"]],
        [["abab", "aba", "abc"]],
        [["ab", "c", "ab"]],
        [_lcp_big],
        [_lcp_big2],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def longestCommonPrefix(self, strs):
        a, b = strs[0], strs[-1]          # compares only first and last WITHOUT sorting
        i = 0
        while i < min(len(a), len(b)) and a[i] == b[i]:
            i += 1
        return a[:i]
''',
        '''class Solution:
    def longestCommonPrefix(self, strs):
        first = strs[0]
        for i, ch in enumerate(first):
            for w in strs:
                if w[i] != ch:             # no length check: IndexError on a shorter word
                    return first[:i]
        return first
''',
    ],
    guide=dict(
        prereqs="String indexing and slicing (`s[i]`, `s[:i]`); nested loops.",
        intuition="Line the words up under each other and read **column by column**. The prefix continues as long as every word has the same character in the current column; it stops at the first column where a word differs or has run out.",
        hints=[
            "The answer can't be longer than the shortest word.",
            "Use the first word as a ruler: check its character i against character i of every other word.",
            "Stop and return first[:i] the moment a word is too short or has a different character.",
        ],
        brute_force="Try every prefix of the first word from longest to shortest and test `w.startswith(prefix)` for all words: O(m² · n) for word length m and n words. Column scanning does the same job in O(m · n).",
        approach="""
1. Take `first = strs[0]`.
2. For each index `i` and character `ch` of `first`, look at every word `w`:
   - if `i == len(w)` (word ended) or `w[i] != ch` → return `first[:i]`.
3. If the loop finishes, the whole first word is the prefix.

**Dry run** `["flower", "flow", "flight"]`:

| i | ch | flower | flow | flight | result |
|---|---|---|---|---|---|
| 0 | f | f | f | f | continue |
| 1 | l | l | l | l | continue |
| 2 | o | o | o | **i** | mismatch → return `"fl"` |

Alternative: sort the list; only the first and last words (alphabetically furthest apart) need comparing.
""",
        complexity="Time **O(S)** where S is the total number of characters (worst case every character is read once). Space **O(1)** besides the answer.",
        pitfalls="- Reading `w[i]` without checking the word's length (`['ab', 'a']`).\n- Comparing only the first and last word is valid **only after sorting**.\n- A list with one word: the answer is that word.",
        follow_up="A *trie* (prefix tree) answers many prefix queries on a fixed word list — see *Implement Trie* in the Tries pattern.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="pascals-triangle",
    title="Pascal's Triangle",
    difficulty="Easy",
    pattern="Arrays & Hashing",
    leetcode=_lc("pascals-triangle"),
    neetcode=_nc("pascals-triangle"),
    entry="generate",
    description=r"""
Pascal's triangle is a triangle of numbers in which every row starts and ends with `1`, and every other
number is the **sum of the two numbers directly above it** in the previous row.

Given `numRows`, return the first `numRows` rows as a list of lists.

**Constraints**

- `1 <= numRows <= 30` on LeetCode (our judge goes up to 100)

**Example 1:** `numRows = 5` → `[[1], [1,1], [1,2,1], [1,3,3,1], [1,4,6,4,1]]`

**Example 2:** `numRows = 1` → `[[1]]`
""",
    starter='''class Solution:
    def generate(self, numRows: int) -> List[List[int]]:
        pass
''',
    solution='''class Solution:
    def generate(self, numRows):
        rows = [[1]]
        for _ in range(numRows - 1):
            prev = rows[-1]
            row = [1]
            for i in range(1, len(prev)):
                row.append(prev[i - 1] + prev[i])
            row.append(1)
            rows.append(row)
        return rows
''',
    tests=[[5], [1], [2], [3], [4], [6], [10], [15], [30], [64], [100]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def generate(self, numRows):
        rows = [[1]]
        for _ in range(numRows):           # off by one: one row too many
            prev = rows[-1]
            rows.append([1] + [prev[i - 1] + prev[i] for i in range(1, len(prev))] + [1])
        return rows
''',
        '''class Solution:
    def generate(self, numRows):
        rows = []
        for n in range(1, numRows + 1):
            row = [1] * n
            for i in range(1, n - 1):
                row[i] = row[i - 1] + rows[-1][i]   # uses the NEW row's left neighbour
            rows.append(row)
        return rows
''',
    ],
    guide=dict(
        prereqs="Lists of lists; building a list with `append`.",
        intuition="Each row is completely determined by the row before it: put a `1` at both ends and fill the middle with sums of neighbouring pairs from the previous row.",
        hints=[
            "Row k has k numbers. What are the first and last?",
            "The value at position i of a row is prev[i-1] + prev[i].",
            "Start with [[1]] and build numRows - 1 more rows from rows[-1].",
        ],
        brute_force="Compute each entry independently as a binomial coefficient `C(row, i)` using factorials — correct, but it repeats huge multiplications. Building from the previous row needs one addition per entry.",
        approach="""
1. `rows = [[1]]`.
2. Repeat `numRows - 1` times: `prev = rows[-1]`; `row = [1]`; for `i` in `1..len(prev)-1` append
   `prev[i-1] + prev[i]`; append the closing `1`; add `row` to `rows`.

**Dry run** for `numRows = 4`:

- start `[[1]]`
- prev `[1]` → no middle values → `[1, 1]`
- prev `[1, 1]` → middle `1+1 = 2` → `[1, 2, 1]`
- prev `[1, 2, 1]` → middle `1+2 = 3`, `2+1 = 3` → `[1, 3, 3, 1]`
""",
        complexity="Time **O(numRows²)** — the triangle has 1 + 2 + … + n entries. Space O(numRows²) for the output.",
        pitfalls="- Looping `numRows` times after already placing the first row gives one row too many.\n- Reading the left neighbour from the row you're currently building instead of the previous row.",
        follow_up="*Pascal's Triangle II* (LC 119): return only row k using O(k) space — update one list from right to left.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="unique-email-addresses",
    title="Unique Email Addresses",
    difficulty="Easy",
    pattern="Arrays & Hashing",
    leetcode=_lc("unique-email-addresses"),
    neetcode=_nc("unique-email-addresses"),
    entry="numUniqueEmails",
    description=r"""
An email address has a **local name**, an `@`, and a **domain name**: `local@domain`. A mail provider
applies two rules to the **local name only**:

1. every `.` is ignored (`a.b.c@x.com` is delivered to `abc@x.com`);
2. everything from the first `+` onward is ignored (`abc+spam@x.com` is delivered to `abc@x.com`).

The domain name is never changed. Given a list `emails`, return how many **different mailboxes**
actually receive mail.

**Constraints**

- `1 <= len(emails) <= 100` on LeetCode (our judge uses 4000)
- each address contains exactly one `@`; local names don't start with `+`

**Example 1:** `["test.email+alex@leetcode.com", "test.e.mail+bob.cathy@leetcode.com", "testemail+david@lee.tcode.com"]` → `2`

**Example 2:** `["a@leetcode.com", "b@leetcode.com", "c@leetcode.com"]` → `3`
""",
    starter='''class Solution:
    def numUniqueEmails(self, emails: List[str]) -> int:
        pass
''',
    solution='''class Solution:
    def numUniqueEmails(self, emails):
        seen = set()
        for e in emails:
            local, domain = e.split("@")
            local = local.split("+")[0].replace(".", "")
            seen.add(local + "@" + domain)
        return len(seen)
''',
    tests=[
        [["test.email+alex@leetcode.com", "test.e.mail+bob.cathy@leetcode.com", "testemail+david@lee.tcode.com"]],
        [["a@leetcode.com", "b@leetcode.com", "c@leetcode.com"]],
        [["a@b.com"]],
        [["a.b@c.com", "ab@c.com", "a.b@c.co.m"]],
        [["x+y+z@d.com", "x@d.com", "x+@d.com"]],
        [["ab@c.d.com", "ab@cd.com"]],
        [["a+b.c@x.com", "a@x.com", "a.+.@x.com"]],
        [["same@x.com", "same@x.com"]],
        [["j.o.e@mail.com", "joe@mail.com", "joe@m.ail.com", "jo+e@mail.com"]],
        [["a@x+y.com", "a@x.com"]],
        [_emails_big],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def numUniqueEmails(self, emails):
        return len({e.split("+")[0].replace(".", "") + e[e.index("@"):].replace(".", "") for e in emails})
''',
        '''class Solution:
    def numUniqueEmails(self, emails):
        seen = set()
        for e in emails:
            local, domain = e.split("@")
            seen.add(local.replace(".", "") + "@" + domain)      # forgets the '+' rule
        return len(seen)
''',
    ],
    guide=dict(
        prereqs="String methods `split`, `replace`; sets for counting distinct values (*Contains Duplicate*).",
        intuition="Turn every address into its **canonical form** — the one true spelling of the mailbox — and count how many different canonical forms there are with a set.",
        hints=[
            "Split the address at '@' first; the rules only touch the left part.",
            "Cut the local name at the first '+', then delete the dots.",
            "Add `local + '@' + domain` to a set; the answer is the set's size.",
        ],
        brute_force="Normalise each address, then compare it against every address already kept in a list: O(n²) comparisons. A set does the 'already seen?' check in O(1).",
        approach="""
1. `seen = set()`.
2. For each email: `local, domain = e.split('@')`; `local = local.split('+')[0].replace('.', '')`; add `local@domain`.
3. Return `len(seen)`.

**Dry run** example 1:

| email | local after rules | canonical |
|---|---|---|
| test.email+alex@leetcode.com | testemail | testemail@leetcode.com |
| test.e.mail+bob.cathy@leetcode.com | testemail | testemail@leetcode.com |
| testemail+david@lee.tcode.com | testemail | testemail@lee.tcode.com |

Two different canonical forms → **2**.
""",
        complexity="Time **O(total characters)**, space O(total characters) for the set.",
        pitfalls="- Applying the rules to the **domain** (dots there matter: `lee.tcode.com` ≠ `leetcode.com`).\n- Removing dots before cutting at `+` is fine, but cutting at a `+` found in the whole address is not.",
        follow_up="Same 'canonical key + set/dict' idea as *Group Anagrams*.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="isomorphic-strings",
    title="Isomorphic Strings",
    difficulty="Easy",
    pattern="Arrays & Hashing",
    leetcode=_lc("isomorphic-strings"),
    neetcode=_nc("isomorphic-strings"),
    entry="isIsomorphic",
    description=r"""
Two strings `s` and `t` of equal length are **isomorphic** if you can turn `s` into `t` by replacing each
character with another character, following a fixed rule: the same character of `s` always becomes the
same character of `t`, and **two different characters of `s` never become the same character**. A
character may map to itself.

Return `True` if `s` and `t` are isomorphic.

**Constraints**

- `1 <= len(s) <= 5 * 10^4`, `len(t) == len(s)`, any ASCII characters

**Example 1:** `s = "egg", t = "add"` → `True` (e→a, g→d)

**Example 2:** `s = "foo", t = "bar"` → `False` (o would have to become both a and r)

**Example 3:** `s = "badc", t = "baba"` → `False` (b and d would both become b)
""",
    starter='''class Solution:
    def isIsomorphic(self, s: str, t: str) -> bool:
        pass
''',
    solution='''class Solution:
    def isIsomorphic(self, s, t):
        s_to_t, t_to_s = {}, {}
        for a, b in zip(s, t):
            if s_to_t.setdefault(a, b) != b or t_to_s.setdefault(b, a) != a:
                return False
        return True
''',
    tests=[
        ["egg", "add"],
        ["foo", "bar"],
        ["badc", "baba"],
        ["paper", "title"],
        ["a", "a"],
        ["ab", "aa"],
        ["aa", "ab"],
        ["13", "42"],
        ["abcabc", "xyzxyz"],
        ["abab", "baba"],
        ["abba", "abab"],
        [_iso_s, _iso_t],
        [_iso_s, _iso_t_bad],
    ],
    wrong_solutions=[
        '''class Solution:
    def isIsomorphic(self, s, t):
        m = {}
        for a, b in zip(s, t):
            if m.setdefault(a, b) != b:      # one direction only
                return False
        return True
''',
        '''class Solution:
    def isIsomorphic(self, s, t):
        return len(set(s)) == len(set(t))    # counts letters, ignores positions
''',
    ],
    guide=dict(
        prereqs="Dicts as lookup tables (*Two Sum*); `zip` to walk two strings together.",
        intuition="You need a **one-to-one** pairing between the characters of `s` and `t`. One dict checks 's-character always goes to the same t-character'; a second dict checks the reverse, which is what stops two different characters sharing a target.",
        hints=[
            "Record what each character of s maps to. What should happen when you meet it again?",
            "\"badc\" → \"baba\" passes a one-direction check. What extra rule is broken?",
            "Keep two dicts, s→t and t→s; every pair (a, b) must agree with both.",
        ],
        brute_force="For every pair of positions (i, j), check that `s[i] == s[j]` exactly when `t[i] == t[j]`: O(n²).",
        approach="""
1. `s_to_t = {}`, `t_to_s = {}`.
2. For each pair `(a, b)` from `zip(s, t)`:
   - `setdefault(a, b)` stores `b` for `a` if `a` is new, and returns whatever is stored. If that isn't `b` → `False`.
   - Do the same in the other direction with `t_to_s`.
3. Return `True`.

**Dry run** `s = "badc"`, `t = "baba"`:

| a | b | s_to_t | t_to_s | ok? |
|---|---|---|---|---|
| b | b | {b:b} | {b:b} | yes |
| a | a | {b:b, a:a} | {b:b, a:a} | yes |
| d | b | d→b stored | t_to_s[b] is **b**, not d | **False** |
""",
        complexity="Time **O(n)**, space **O(k)** where k is the number of distinct characters.",
        pitfalls="- Checking one direction only.\n- Comparing the number of distinct characters ignores *where* they are (`\"abba\"` vs `\"abab\"`).",
        follow_up="*Word Pattern* is the same problem with words instead of characters. Another trick: compare `[s.index(c) for c in s]` with the same for `t` (first-occurrence patterns).",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="word-pattern",
    title="Word Pattern",
    difficulty="Easy",
    pattern="Arrays & Hashing",
    leetcode=_lc("word-pattern"),
    neetcode=_nc("word-pattern"),
    entry="wordPattern",
    description=r"""
You are given a `pattern` made of lowercase letters and a string `s` of words separated by single spaces.
`s` **follows** the pattern if there is a one-to-one pairing between letters and words: each letter always
stands for the same word, and two different letters never stand for the same word. The number of words
must equal the number of letters.

Return `True` if `s` follows `pattern`.

**Constraints**

- `1 <= len(pattern) <= 300` on LeetCode (our judge uses 10^4)
- `s` has no leading/trailing spaces; words are lowercase

**Example 1:** `pattern = "abba", s = "dog cat cat dog"` → `True`

**Example 2:** `pattern = "abba", s = "dog cat cat fish"` → `False`

**Example 3:** `pattern = "aaaa", s = "dog cat cat dog"` → `False`
""",
    starter='''class Solution:
    def wordPattern(self, pattern: str, s: str) -> bool:
        pass
''',
    solution='''class Solution:
    def wordPattern(self, pattern, s):
        words = s.split()
        if len(words) != len(pattern):
            return False
        p_to_w, w_to_p = {}, {}
        for p, w in zip(pattern, words):
            if p_to_w.setdefault(p, w) != w or w_to_p.setdefault(w, p) != p:
                return False
        return True
''',
    tests=[
        ["abba", "dog cat cat dog"],
        ["abba", "dog cat cat fish"],
        ["aaaa", "dog cat cat dog"],
        ["abba", "dog dog dog dog"],
        ["a", "dog"],
        ["aaa", "dog dog dog dog"],
        ["abc", "dog cat"],
        ["ab", "a b"],
        ["abc", "b c a"],
        ["jquery", "jquery"],
        ["he", "unit"],
        [_wp_pat, _wp_s],
        [_wp_pat, _wp_s_bad],
    ],
    wrong_solutions=[
        '''class Solution:
    def wordPattern(self, pattern, s):
        words = s.split()
        if len(words) != len(pattern):
            return False
        m = {}
        for p, w in zip(pattern, words):
            if m.setdefault(p, w) != w:        # letter -> word only
                return False
        return True
''',
        '''class Solution:
    def wordPattern(self, pattern, s):
        p_to_w, w_to_p = {}, {}
        for p, w in zip(pattern, s.split()):   # zip silently drops extra words
            if p_to_w.setdefault(p, w) != w or w_to_p.setdefault(w, p) != p:
                return False
        return True
''',
    ],
    guide=dict(
        prereqs="*Isomorphic Strings*; `str.split()`.",
        intuition="Split the sentence into words; now it is *Isomorphic Strings* with letters on one side and whole words on the other. Two dicts enforce the one-to-one pairing.",
        hints=[
            "First make sure there are as many words as pattern letters.",
            "One dict letter → word is not enough: \"abba\" vs \"dog dog dog dog\".",
            "Add the reverse dict word → letter and check both for every pair.",
        ],
        brute_force="Compare every pair of positions: letters equal ⇔ words equal. O(n²) comparisons.",
        approach="""
1. `words = s.split()`; if the counts differ → `False`.
2. Walk `zip(pattern, words)` keeping `p_to_w` and `w_to_p`; any disagreement → `False`.

**Dry run** `"abba"`, `"dog dog dog dog"`:

| letter | word | check |
|---|---|---|
| a | dog | new pair, stored both ways |
| b | dog | `w_to_p['dog']` is `a`, not `b` → **False** |
""",
        complexity="Time **O(n + len(s))**, space O(number of distinct words).",
        pitfalls="- `zip` stops at the shorter input, so a missing length check lets extra words through.\n- One-direction mapping accepts two letters for one word.",
        follow_up="*Word Pattern II* (LC 291): no spaces in `s` → backtracking over possible word boundaries.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="can-place-flowers",
    title="Can Place Flowers",
    difficulty="Easy",
    pattern="Arrays & Hashing",
    leetcode=_lc("can-place-flowers"),
    neetcode=_nc("can-place-flowers"),
    entry="canPlaceFlowers",
    description=r"""
A flowerbed is a row of plots given as a list `flowerbed` of `0`s (empty) and `1`s (already planted).
Flowers may **never be in two neighbouring plots**. The existing bed already obeys that rule.

Given an integer `n`, return `True` if `n` **new** flowers can be planted without breaking the rule,
otherwise `False`.

**Constraints**

- `1 <= len(flowerbed) <= 2 * 10^4`
- `0 <= n <= len(flowerbed)`

**Example 1:** `flowerbed = [1,0,0,0,1], n = 1` → `True` (plant in the middle)

**Example 2:** `flowerbed = [1,0,0,0,1], n = 2` → `False`
""",
    starter='''class Solution:
    def canPlaceFlowers(self, flowerbed: List[int], n: int) -> bool:
        pass
''',
    solution='''class Solution:
    def canPlaceFlowers(self, flowerbed, n):
        bed = flowerbed[:]
        last = len(bed) - 1
        for i in range(len(bed)):
            if n <= 0:
                break
            left_free = i == 0 or bed[i - 1] == 0
            right_free = i == last or bed[i + 1] == 0
            if bed[i] == 0 and left_free and right_free:
                bed[i] = 1
                n -= 1
        return n <= 0
''',
    tests=[
        [[1, 0, 0, 0, 1], 1],
        [[1, 0, 0, 0, 1], 2],
        [[0], 1],
        [[1], 0],
        [[1], 1],
        [[0, 0], 1],
        [[0, 0], 2],
        [[0, 0, 0], 2],
        [[0, 0, 1, 0, 0], 2],
        [[1, 0, 0, 0, 0, 1], 2],
        [[0, 0, 0, 0, 0], 3],
        [[0, 1, 0], 1],
        [_fb_big, _fb_cap_big],
        [_fb_big, _fb_cap_big + 1],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def canPlaceFlowers(self, flowerbed, n):
        count = 0
        for i in range(1, len(flowerbed) - 1):      # never considers the two end plots
            if flowerbed[i - 1] == flowerbed[i] == flowerbed[i + 1] == 0:
                flowerbed[i] = 1
                count += 1
        return count >= n
''',
        '''class Solution:
    def canPlaceFlowers(self, flowerbed, n):
        last = len(flowerbed) - 1
        count = 0
        for i in range(len(flowerbed)):
            left_free = i == 0 or flowerbed[i - 1] == 0
            right_free = i == last or flowerbed[i + 1] == 0
            if flowerbed[i] == 0 and left_free and right_free:
                count += 1                            # never marks the plot as planted
        return count >= n
''',
    ],
    guide=dict(
        prereqs="Scanning a list by index and looking at neighbours `i - 1` and `i + 1` safely.",
        intuition="Go left to right and plant **greedily**: whenever a plot is empty and both neighbours are empty (or don't exist), plant there. Planting as early as possible never reduces how many flowers fit later.",
        hints=[
            "When exactly is plot i plantable?",
            "The first and last plots have only one neighbour — treat a missing neighbour as empty.",
            "After planting, mark the plot as 1 so the next plot sees it.",
        ],
        brute_force="Try every subset of empty plots and test the rule: exponential. The greedy scan is one pass.",
        approach="""
1. Copy the bed (so the input isn't changed).
2. For each `i`: if `bed[i] == 0`, the left plot is free (`i == 0` or `bed[i-1] == 0`) and the right plot is free, set `bed[i] = 1` and `n -= 1`.
3. Return `n <= 0`.

**Dry run** `[0, 0, 1, 0, 0]`, `n = 2`:

| i | bed[i] | left free? | right free? | action |
|---|---|---|---|---|
| 0 | 0 | yes (edge) | yes | plant → `[1,0,1,0,0]`, n=1 |
| 1 | 0 | no | – | skip |
| 2 | 1 | – | – | skip |
| 3 | 0 | no | – | skip |
| 4 | 0 | yes | yes (edge) | plant, n=0 |

`n <= 0` → **True**.
""",
        complexity="Time **O(len(flowerbed))**, space O(n) for the copy (O(1) if you may modify the input).",
        pitfalls="- Forgetting the end plots (`[0]`, `[0,0,1]`).\n- Not marking a planted plot, so two neighbours both get counted (`[0,0]` would allow 2).\n- `n = 0` is always `True`.",
        follow_up="Count runs of zeros instead: a run of z zeros between two flowers fits `(z - 1) // 2` new flowers.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="maximum-number-of-balloons",
    title="Maximum Number of Balloons",
    difficulty="Easy",
    pattern="Arrays & Hashing",
    leetcode=_lc("maximum-number-of-balloons"),
    neetcode=_nc("maximum-number-of-balloons"),
    entry="maxNumberOfBalloons",
    description=r"""
Using the letters of a string `text`, each **at most once**, how many copies of the word `"balloon"` can
you spell? Return that maximum number.

Note that `"balloon"` needs one `b`, one `a`, **two** `l`, **two** `o` and one `n`.

**Constraints**

- `1 <= len(text) <= 10^4` (our judge uses 5·10^4), lowercase English letters

**Example 1:** `text = "nlaebolko"` → `1`

**Example 2:** `text = "loonbalxballpoon"` → `2`

**Example 3:** `text = "leetcode"` → `0`
""",
    starter='''class Solution:
    def maxNumberOfBalloons(self, text: str) -> int:
        pass
''',
    solution='''class Solution:
    def maxNumberOfBalloons(self, text):
        have = collections.Counter(text)
        need = collections.Counter("balloon")
        return min(have[ch] // need[ch] for ch in need)
''',
    tests=[
        ["nlaebolko"],
        ["loonbalxballpoon"],
        ["leetcode"],
        ["balloon"],
        ["balon"],
        ["ballon"],
        ["bbaallnnoo"],
        ["balloonballoon"],
        ["b"],
        ["llllllloooooooobbbaaannn"],
        ["krhizmmgmcrecekgyljqkldocicziihtgpqwbticmvuyznragqoyrukzopfmjhjjxemsxmrsxuqmnkrzhgvtgdgtykhcglurvppvcwhrhrjoislonvvglhdciilduvuiebmffaagxerjeewmtcwmhmtwlxtvlbocczlrppmpjbpnifqtlninyzjtmazxdbzwxthpvrfulvrspycqcghuopjirzoeuqhetnbrcdakilzmklxwudxxhwilasbjjhhfgghogqoofsufysmcqeilaivtmfziumjloewbkjvaahsaaggteppqyuoylgpbdwqubaalfwcqrjeycjbbpifjbpigjdnnswocusuprydgrtxuaojeriigwumlovafxnpibjopjfqzrwemoinmptxddgcszmfprdrichjeqcvikynzigleaajcysusqasqadjemgnyvmzmbcfrttrzonwafrnedglhpudovigwvpimttiketopkvqw"],
        [_ball_big],
    ],
    wrong_solutions=[
        '''class Solution:
    def maxNumberOfBalloons(self, text):
        c = collections.Counter(text)
        return min(c[ch] for ch in "balon")        # l and o are needed twice
''',
        '''class Solution:
    def maxNumberOfBalloons(self, text):
        c = collections.Counter(text)
        return min(c["b"], c["a"], c["n"]) if c["l"] >= 2 and c["o"] >= 2 else 0
''',
    ],
    guide=dict(
        prereqs="Frequency counting with `collections.Counter` (*Valid Anagram*); integer division `//`.",
        intuition="Count how many of each letter you **have** and how many one word **needs**. Each needed letter limits the number of words to `have // need`; the scarcest letter decides — like a recipe limited by the ingredient you'll run out of first.",
        hints=[
            "Which letters matter? Only b, a, l, o, n.",
            "How many words can 5 l's support, when each word uses 2?",
            "Answer = min(have[ch] // need[ch]) over the letters of \"balloon\".",
        ],
        brute_force="Repeatedly remove the letters b-a-l-l-o-o-n from the text one copy at a time, searching the string for each letter: O(n²). Counting once is O(n).",
        approach="""
1. `have = Counter(text)`; `need = Counter('balloon')` → `{b:1, a:1, l:2, o:2, n:1}`.
2. Return the minimum of `have[ch] // need[ch]`.

**Dry run** `"loonbalxballpoon"`: have b=2, a=2, l=4, o=4, n=2 → quotients 2, 2, 2, 2, 2 → **2**.

`"ballon"`: o=1 → `1 // 2 = 0` → **0**.
""",
        complexity="Time **O(n)**, space **O(1)** (at most 26 counters).",
        pitfalls="- Treating `l` and `o` like the single letters.\n- A missing letter gives count 0 — `Counter` returns 0 for missing keys, a plain dict raises `KeyError`.",
        follow_up="Generalise: *Rearrange Characters to Make Target String* (LC 2287) — same code with any target word.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="find-pivot-index",
    title="Find Pivot Index",
    difficulty="Easy",
    pattern="Arrays & Hashing",
    leetcode=_lc("find-pivot-index"),
    neetcode=_nc("find-pivot-index"),
    entry="pivotIndex",
    description=r"""
The **pivot index** of a list is a position where the sum of all numbers strictly to its **left** equals
the sum of all numbers strictly to its **right**. (The sum of "nothing" — at either end — counts as 0.)

Return the **leftmost** pivot index of `nums`, or `-1` if there is none.

**Constraints**

- `1 <= len(nums) <= 10^4` (our judge uses 2·10^4)
- `-1000 <= nums[i] <= 1000`

**Example 1:** `nums = [1, 7, 3, 6, 5, 6]` → `3` (left `1+7+3 = 11`, right `5+6 = 11`)

**Example 2:** `nums = [1, 2, 3]` → `-1`

**Example 3:** `nums = [2, 1, -1]` → `0` (left is empty = 0, right `1 + -1 = 0`)
""",
    starter='''class Solution:
    def pivotIndex(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def pivotIndex(self, nums):
        total = sum(nums)
        left = 0
        for i, x in enumerate(nums):
            if left == total - left - x:
                return i
            left += x
        return -1
''',
    tests=[
        [[1, 7, 3, 6, 5, 6]],
        [[1, 2, 3]],
        [[2, 1, -1]],
        [[5]],
        [[0, 0, 0]],
        [[-1, -1, -1, 0, 1, 1]],
        [[1, -1, 4]],
        [[4, 1, -1]],
        [[1, 2, 3, 3]],
        [[-1, -1, 0, 1, 1, 0]],
        [[10, -10, 10, -10, 7]],
        [_piv_big],
        [_piv_none],
    ],
    wrong_solutions=[
        '''class Solution:
    def pivotIndex(self, nums):
        total = sum(nums)
        left = 0
        for i, x in enumerate(nums):
            left += x                       # pivot itself wrongly counted on the left
            if left == total - left:
                return i
        return -1
''',
        '''class Solution:
    def pivotIndex(self, nums):
        total = sum(nums)
        left, ans = 0, -1
        for i, x in enumerate(nums):
            if left == total - left - x:
                ans = i                     # keeps the RIGHTMOST pivot
            left += x
        return ans
''',
    ],
    guide=dict(
        prereqs="Running (prefix) sums — see *Prefix sums, counting and bucket tricks*.",
        intuition="If you know the total and the sum to the left of `i`, the right sum needs no loop: `right = total - left - nums[i]`. So one pass with a running left sum is enough.",
        hints=[
            "Recomputing both sums for each index is O(n²). What can you compute once?",
            "right = total − left − nums[i].",
            "Compare first, then add nums[i] to left before moving on.",
        ],
        brute_force="For each index compute `sum(nums[:i])` and `sum(nums[i+1:])`: **O(n²)**.",
        approach="""
1. `total = sum(nums)`, `left = 0`.
2. For each `i, x`: if `left == total - left - x` return `i`; then `left += x`.
3. Return `-1`.

**Dry run** `[1, 7, 3, 6, 5, 6]`, total 28:

| i | x | left | right = 28 − left − x | equal? |
|---|---|---|---|---|
| 0 | 1 | 0 | 27 | no |
| 1 | 7 | 1 | 20 | no |
| 2 | 3 | 8 | 17 | no |
| 3 | 6 | 11 | 11 | **yes → 3** |
""",
        complexity="Time **O(n)** (two passes), space **O(1)**.",
        pitfalls="- Adding `x` to `left` before comparing includes the pivot on one side.\n- Return the first match (leftmost).\n- Negative numbers mean you can't stop early when left exceeds right.",
        follow_up="*Find the Middle Index in Array* (LC 1991) is identical. *Product of Array Except Self* uses the same left/right split with multiplication.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="range-sum-query-immutable",
    title="Range Sum Query - Immutable",
    difficulty="Easy",
    pattern="Arrays & Hashing",
    leetcode=_lc("range-sum-query-immutable"),
    neetcode=_nc("range-sum-query-immutable"),
    kind="class",
    entry="NumArray",
    description=r"""
Design a class `NumArray` built from a fixed integer list `nums`. It must answer many calls of
`sumRange(left, right)`: the sum of the elements from index `left` to index `right`, **both included**.

Because there can be thousands of queries, each `sumRange` should take **O(1)** time.

**Constraints**

- `1 <= len(nums) <= 10^4`, `-10^5 <= nums[i] <= 10^5`
- `0 <= left <= right < len(nums)`; up to `10^4` calls

**Example:**

```
NumArray([-2, 0, 3, -5, 2, -1])
sumRange(0, 2) -> 1
sumRange(2, 5) -> -1
sumRange(0, 5) -> -3
```

Tests are `[operations, arguments]`; the output lists each call's return value (`None` for the constructor).
""",
    starter='''class NumArray:

    def __init__(self, nums: List[int]):
        pass

    def sumRange(self, left: int, right: int) -> int:
        pass
''',
    solution='''class NumArray:
    def __init__(self, nums):
        self.prefix = [0]                     # prefix[i] = sum of nums[:i]
        for x in nums:
            self.prefix.append(self.prefix[-1] + x)

    def sumRange(self, left, right):
        return self.prefix[right + 1] - self.prefix[left]
''',
    tests=[
        [["NumArray", "sumRange", "sumRange", "sumRange"], [[[-2, 0, 3, -5, 2, -1]], [0, 2], [2, 5], [0, 5]]],
        [["NumArray", "sumRange"], [[[7]], [0, 0]]],
        [["NumArray", "sumRange", "sumRange", "sumRange"], [[[1, 2, 3, 4]], [0, 0], [3, 3], [1, 2]]],
        [["NumArray", "sumRange", "sumRange"], [[[-1, -1, -1]], [0, 2], [1, 1]]],
        [["NumArray", "sumRange", "sumRange"], [[[0, 0, 0, 0]], [0, 3], [2, 3]]],
        [["NumArray", "sumRange", "sumRange", "sumRange"], [[[5, -5, 5, -5, 5]], [0, 4], [1, 4], [0, 3]]],
        [["NumArray", "sumRange", "sumRange"], [[[100000, -100000]], [0, 1], [1, 1]]],
        [["NumArray", "sumRange", "sumRange", "sumRange", "sumRange"], [[[3, 1, 4, 1, 5, 9, 2, 6]], [0, 7], [2, 2], [5, 7], [0, 1]]],
        [["NumArray", "sumRange", "sumRange"], [[[1, 2]], [0, 1], [0, 0]]],
        [["NumArray"] + ["sumRange"] * len(_na_q), [[_na_big]] + _na_q],
    ],
    examples=1,
    wrong_solutions=[
        '''class NumArray:
    def __init__(self, nums):
        self.prefix = []
        run = 0
        for x in nums:
            run += x
            self.prefix.append(run)           # no leading 0

    def sumRange(self, left, right):
        return self.prefix[right] - self.prefix[left]   # drops nums[left]
''',
        '''class NumArray:
    def __init__(self, nums):
        self.prefix = [0]
        for x in nums:
            self.prefix.append(self.prefix[-1] + x)

    def sumRange(self, left, right):
        return self.prefix[right] - self.prefix[left]   # right end excluded
''',
    ],
    guide=dict(
        prereqs="Prefix sums (see *Prefix sums, counting and bucket tricks*); how design problems are tested.",
        intuition="Do the adding **once**, in the constructor: store running totals. Any range sum is then 'total up to the right end' minus 'total before the left end'.",
        hints=[
            "Summing the slice on every call is O(n) per query. What could you precompute?",
            "Let prefix[i] be the sum of the first i numbers, with prefix[0] = 0.",
            "sumRange(l, r) = prefix[r + 1] − prefix[l].",
        ],
        brute_force="`return sum(self.nums[left:right + 1])` — O(n) per query, O(n·q) overall: 10⁴ × 10⁴ = 10⁸ additions.",
        approach="""
**Constructor:** `prefix = [0]`; for each `x` append `prefix[-1] + x`.

**Query:** `prefix[right + 1] - prefix[left]`.

**Dry run** `nums = [-2, 0, 3, -5, 2, -1]` → `prefix = [0, -2, -2, 1, -4, -2, -3]`.

- `sumRange(0, 2)` = `prefix[3] - prefix[0]` = 1 − 0 = **1**
- `sumRange(2, 5)` = `prefix[6] - prefix[2]` = −3 − (−2) = **−1**
""",
        complexity="Constructor **O(n)** time and space; each query **O(1)**.",
        pitfalls="- Without the leading 0 you need a special case for `left == 0`.\n- Inclusive right end → index `right + 1`.",
        follow_up="2-D version: *Range Sum Query 2D - Immutable*. With updates: Fenwick tree / segment tree (*Range Sum Query - Mutable*).",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="find-all-numbers-disappeared-in-an-array",
    title="Find All Numbers Disappeared in an Array",
    difficulty="Easy",
    pattern="Arrays & Hashing",
    leetcode=_lc("find-all-numbers-disappeared-in-an-array"),
    neetcode=_nc("find-all-numbers-disappeared-in-an-array"),
    entry="findDisappearedNumbers",
    compare="unordered",
    description=r"""
`nums` has `n` integers, each between `1` and `n` inclusive. Some values may appear more than once, which
means others are missing. Return every integer in the range `1..n` that does **not** appear in `nums`
(any order).

**Constraints**

- `1 <= n <= 10^5`, `1 <= nums[i] <= n`

**Example 1:** `nums = [4, 3, 2, 7, 8, 2, 3, 1]` → `[5, 6]`

**Example 2:** `nums = [1, 1]` → `[2]`

**Follow-up:** no extra space besides the returned list, O(n) time.
""",
    starter='''class Solution:
    def findDisappearedNumbers(self, nums: List[int]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def findDisappearedNumbers(self, nums):
        for x in nums:
            i = abs(x) - 1                 # value v "owns" index v - 1
            if nums[i] > 0:
                nums[i] = -nums[i]         # mark v as seen
        return [i + 1 for i, v in enumerate(nums) if v > 0]
''',
    tests=[
        [[4, 3, 2, 7, 8, 2, 3, 1]],
        [[1, 1]],
        [[1]],
        [[2, 2]],
        [[1, 2, 3]],
        [[3, 3, 3]],
        [[2, 1]],
        [[5, 4, 3, 2, 1]],
        [[1, 1, 1, 1, 1, 6]],
        [[2, 3, 4, 5, 6, 6]],
        [_dis_big],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def findDisappearedNumbers(self, nums):
        s = set(nums)
        return [v for v in range(1, max(nums) + 1) if v not in s]     # should go up to n
''',
        '''class Solution:
    def findDisappearedNumbers(self, nums):
        for x in nums:
            i = x - 1                       # forgot abs(): x may already be negated
            if nums[i] > 0:
                nums[i] = -nums[i]
        return [i + 1 for i, v in enumerate(nums) if v > 0]
''',
    ],
    guide=dict(
        prereqs="Sets (*Contains Duplicate*); the 'array as its own hash table' trick from *The Arrays & Hashing pattern*.",
        intuition="Values are `1..n` and there are exactly `n` slots, so value `v` can use slot `v - 1` as its personal checkbox. Tick the box by making the number there negative; unticked (still positive) boxes belong to missing values.",
        hints=[
            "With a set this is two lines. Which range must you check — up to max(nums) or up to n?",
            "For O(1) extra space, record 'v was seen' inside nums itself at index v − 1.",
            "Negate nums[abs(x) − 1]; afterwards the indices holding positive numbers are the answer (plus 1).",
        ],
        brute_force="For each `v` in `1..n`, scan the list for it: O(n²). With `set(nums)`: O(n) time, O(n) extra space.",
        approach="""
1. For each `x`: `i = abs(x) - 1` (abs because `x` may have been negated as someone's checkbox); if `nums[i] > 0`, negate it.
2. Collect `i + 1` for every index whose value is still positive.

**Dry run** `[4, 3, 2, 7, 8, 2, 3, 1]`:

after marking: `[-4, -3, -2, -7, 8, 2, -3, -1]` — indices 4 and 5 stayed positive → **[5, 6]**.
""",
        complexity="Time **O(n)**, extra space **O(1)** (the input is modified).",
        pitfalls="- Forgetting `abs()` → negative index, wrong slot.\n- Checking only up to `max(nums)` misses values above the maximum (`[1,1]` → 2).\n- Negating twice turns a mark back off — guard with `if nums[i] > 0`.",
        follow_up="*Find All Duplicates in an Array* (LC 442): a slot already negative means the value is a repeat. *First Missing Positive* uses the same idea with arbitrary values.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="majority-element-ii",
    title="Majority Element II",
    difficulty="Medium",
    pattern="Arrays & Hashing",
    leetcode=_lc("majority-element-ii"),
    neetcode=_nc("majority-element-ii"),
    entry="majorityElement",
    compare="unordered",
    description=r"""
Given an integer list `nums` of length `n`, return every value that appears **more than `n / 3` times**
(strictly more). There can be zero, one or two such values; return them in any order.

**Constraints**

- `1 <= n <= 5 * 10^4`, `-10^9 <= nums[i] <= 10^9`

**Example 1:** `nums = [3, 2, 3]` → `[3]`

**Example 2:** `nums = [1]` → `[1]`

**Example 3:** `nums = [1, 2]` → `[1, 2]`

**Follow-up:** O(n) time and O(1) extra space.
""",
    starter='''class Solution:
    def majorityElement(self, nums: List[int]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def majorityElement(self, nums):
        c1 = c2 = None
        n1 = n2 = 0
        for x in nums:
            if x == c1:
                n1 += 1
            elif x == c2:
                n2 += 1
            elif n1 == 0:
                c1, n1 = x, 1
            elif n2 == 0:
                c2, n2 = x, 1
            else:
                n1 -= 1
                n2 -= 1
        # second pass: the survivors are only candidates
        return [c for c in (c1, c2) if c is not None and nums.count(c) > len(nums) // 3]
''',
    tests=[
        [[3, 2, 3]],
        [[1]],
        [[1, 2]],
        [[1, 2, 3]],
        [[1, 1, 1, 3, 3, 2, 2, 2]],
        [[2, 2]],
        [[0, 0, 0]],
        [[1, 2, 3, 4, 5, 6]],
        [[4, 4, 4, 1, 2]],
        [[2, 1, 1, 3, 1, 4, 5, 6]],
        [[-1, -1, -1, 7, 7, 7, 9]],
        [_maj2_big],
        [_maj2_none],
    ],
    wrong_solutions=[
        '''class Solution:
    def majorityElement(self, nums):
        c1 = c2 = None
        n1 = n2 = 0
        for x in nums:
            if x == c1:
                n1 += 1
            elif x == c2:
                n2 += 1
            elif n1 == 0:
                c1, n1 = x, 1
            elif n2 == 0:
                c2, n2 = x, 1
            else:
                n1 -= 1
                n2 -= 1
        return [c for c in (c1, c2) if c is not None]      # no verification pass
''',
        '''class Solution:
    def majorityElement(self, nums):
        count = collections.Counter(nums)
        return [x for x, c in count.items() if c >= len(nums) / 3]    # >= instead of >
''',
    ],
    guide=dict(
        prereqs="*Majority Element* (Boyer–Moore voting); counting with a dict.",
        intuition="At most **two** values can each take more than a third of the slots. Extend the voting idea: keep two candidates with counters; a value matching neither cancels one vote from each. Whatever is truly frequent survives the cancelling — but survivors still need to be **checked**, because here a majority isn't guaranteed.",
        hints=[
            "How many different values can appear more than n/3 times?",
            "A Counter solves it in O(n) space. For O(1): two candidates, two counters.",
            "After the voting pass, count each candidate for real and keep those above n // 3.",
        ],
        brute_force="Count each distinct value by scanning: O(n²). `Counter` then filter: O(n) time, O(n) space — a perfectly good first answer.",
        approach="""
**Pass 1 (vote):** for each `x`: matches `c1` → `n1 += 1`; matches `c2` → `n2 += 1`; else if `n1 == 0` adopt as `c1`; else if `n2 == 0` adopt as `c2`; else decrement both.

**Pass 2 (verify):** keep a candidate only if its real count is `> n // 3`.

**Dry run** `[1, 1, 1, 3, 3, 2, 2, 2]` (n = 8, need > 2):

| x | c1:n1 | c2:n2 |
|---|---|---|
| 1,1,1 | 1:3 | –:0 |
| 3,3 | 1:3 | 3:2 |
| 2 | 1:2 | 3:1 |
| 2 | 1:1 | 3:0 |
| 2 | 1:1 | 2:1 |

Candidates 1 and 2; real counts 3 and 3 → **[1, 2]**.
""",
        complexity="Time **O(n)** (voting pass + at most two counting passes), space **O(1)**.",
        pitfalls="- Skipping verification (`[1,2,3]` leaves candidates that aren't majorities).\n- Checking the 'counter is zero' branches before the 'equals a candidate' branches can put the same value in both slots.\n- Strictly more than n/3.",
        follow_up="General rule: at most k − 1 values appear more than n/k times → k − 1 candidates (the Misra–Gries algorithm).",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="continuous-subarray-sum",
    title="Continuous Subarray Sum",
    difficulty="Medium",
    pattern="Arrays & Hashing",
    leetcode=_lc("continuous-subarray-sum"),
    neetcode=_nc("continuous-subarray-sum"),
    entry="checkSubarraySum",
    description=r"""
Given a list of **non-negative** integers `nums` and a positive integer `k`, return `True` if `nums`
contains a **contiguous** run of **at least two** elements whose sum is a multiple of `k` (that is,
`sum % k == 0`; a sum of `0` counts as a multiple). Otherwise return `False`.

**Constraints**

- `1 <= len(nums) <= 10^5` (our judge uses 2·10^4)
- `0 <= nums[i] <= 10^9`, `1 <= k <= 2^31 - 1`

**Example 1:** `nums = [23, 2, 4, 6, 7], k = 6` → `True` (`2 + 4 = 6`)

**Example 2:** `nums = [23, 2, 6, 4, 7], k = 6` → `True` (the whole list sums to 42)

**Example 3:** `nums = [23, 2, 6, 4, 7], k = 13` → `False`
""",
    starter='''class Solution:
    def checkSubarraySum(self, nums: List[int], k: int) -> bool:
        pass
''',
    solution='''class Solution:
    def checkSubarraySum(self, nums, k):
        first = {0: -1}                  # remainder -> earliest index where the prefix had it
        total = 0
        for i, x in enumerate(nums):
            total = (total + x) % k
            if total in first:
                if i - first[total] >= 2:
                    return True
            else:
                first[total] = i
        return False
''',
    tests=[
        [[23, 2, 4, 6, 7], 6],
        [[23, 2, 6, 4, 7], 6],
        [[23, 2, 6, 4, 7], 13],
        [[5], 5],
        [[0, 0], 1],
        [[0], 1],
        [[1, 0], 2],
        [[2, 5, 5], 5],
        [[5, 0, 0, 0], 3],
        [[1, 2, 3], 5],
        [[1, 2, 12], 6],
        [[6, 1, 1], 6],
        [_css_big_no, 10**9],
        [_css_big_yes, 2],
    ],
    wrong_solutions=[
        '''class Solution:
    def checkSubarraySum(self, nums, k):
        first = {0: -1}
        total = 0
        for i, x in enumerate(nums):
            total = (total + x) % k
            if total in first and i - first[total] >= 2:
                return True
            first[total] = i             # overwrites the EARLIEST index with a later one
        return False
''',
        '''class Solution:
    def checkSubarraySum(self, nums, k):
        seen = {0}
        total = 0
        for x in nums:
            total = (total + x) % k
            if total in seen:            # allows a "subarray" of length 1
                return True
            seen.add(total)
        return False
''',
    ],
    guide=dict(
        prereqs="*Subarray Sum Equals K* (prefix sum + dict); the remainder operator `%`.",
        intuition="If two prefix sums leave the **same remainder** when divided by `k`, the elements between them add up to a multiple of `k` (the remainders cancel in the subtraction). So remember the first index at which each remainder appeared, and look for a repeat at least two positions later.",
        hints=[
            "sum(i..j) = P[j+1] − P[i]. When is that divisible by k?",
            "Store prefix remainders in a dict: remainder → earliest index. Seed it with {0: -1}.",
            "Never overwrite an index: the earliest one gives the longest subarray, which you need for the length ≥ 2 rule.",
        ],
        brute_force="Try every start and extend with a running sum: **O(n²)** — 2·10⁸ steps for n = 2·10⁴.",
        approach="""
1. `first = {0: -1}` (empty prefix sits 'before index 0'); `total = 0`.
2. For each `i, x`: `total = (total + x) % k`.
   - If `total` was seen at index `j`: if `i - j >= 2` → `True` (do **not** update).
   - Else store `first[total] = i`.
3. Return `False`.

**Dry run** `[23, 2, 4, 6, 7]`, `k = 6`:

| i | x | total % 6 | first | result |
|---|---|---|---|---|
| 0 | 23 | 5 | {0:-1, 5:0} | – |
| 1 | 2 | 1 | + {1:1} | – |
| 2 | 4 | 5 | 5 seen at 0, 2 − 0 = 2 | **True** (`[2, 4]`) |
""",
        complexity="Time **O(n)**, space **O(min(n, k))** — at most k different remainders.",
        pitfalls="- Length must be ≥ 2: `[5], k=5` is `False`; a single `0` is not enough but `[0, 0]` is.\n- Overwriting the stored index breaks cases like `[2, 5, 5], k=5`.\n- Forgetting `{0: -1}` misses subarrays that start at index 0.",
        follow_up="*Subarray Sums Divisible by K* (LC 974) counts them: store remainder → count. *Make Sum Divisible by P* (LC 1590) removes the shortest subarray with a given remainder.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="design-hashset",
    title="Design HashSet",
    difficulty="Easy",
    pattern="Arrays & Hashing",
    leetcode=_lc("design-hashset"),
    neetcode=_nc("design-hashset"),
    kind="class",
    entry="MyHashSet",
    description=r"""
Build your own set of integers **without using Python's `set` or `dict`**. Implement the class `MyHashSet`:

- `add(key)` — insert `key` (inserting an existing key changes nothing);
- `remove(key)` — delete `key` if present (deleting a missing key changes nothing);
- `contains(key)` — return `True` if `key` is in the set, else `False`.

**Constraints**

- `0 <= key <= 10^6` on LeetCode (our judge uses keys up to about 3·10^6)
- up to `10^4` calls

**Example:**

```
MyHashSet()
add(1); add(2)
contains(1) -> True
contains(3) -> False
add(2)
contains(2) -> True
remove(2)
contains(2) -> False
```
""",
    starter='''class MyHashSet:

    def __init__(self):
        pass

    def add(self, key: int) -> None:
        pass

    def remove(self, key: int) -> None:
        pass

    def contains(self, key: int) -> bool:
        pass
''',
    solution='''class MyHashSet:
    def __init__(self):
        self.size = 1009                              # a prime number of buckets
        self.buckets = [[] for _ in range(self.size)]

    def _bucket(self, key):
        return self.buckets[key % self.size]

    def add(self, key):
        b = self._bucket(key)
        if key not in b:
            b.append(key)

    def remove(self, key):
        b = self._bucket(key)
        if key in b:
            b.remove(key)

    def contains(self, key):
        return key in self._bucket(key)
''',
    tests=[
        [["MyHashSet", "add", "add", "contains", "contains", "add", "contains", "remove", "contains"],
         [[], [1], [2], [1], [3], [2], [2], [2], [2]]],
        [["MyHashSet", "contains", "remove", "contains"], [[], [5], [5], [5]]],
        [["MyHashSet", "add", "add", "remove", "contains"], [[], [7], [7], [7], [7]]],
        [["MyHashSet", "add", "add", "contains", "contains", "remove", "contains", "contains"],
         [[], [0], [1009], [0], [1009], [0], [0], [1009]]],
        [["MyHashSet", "add", "contains", "contains"], [[], [1000000], [1000000], [0]]],
        [["MyHashSet", "add", "add", "add", "remove", "contains", "contains", "contains"],
         [[], [10], [1019], [2028], [1019], [10], [1019], [2028]]],
        [["MyHashSet", "add", "remove", "add", "contains"], [[], [3], [3], [3], [3]]],
        [["MyHashSet", "remove", "add", "remove", "remove", "contains"], [[], [9], [9], [9], [9], [9]]],
        [["MyHashSet", "add", "add", "add", "contains", "contains"], [[], [1], [10001], [20001], [10001], [30001]]],
        [_set_ops, _set_args],
    ],
    examples=1,
    wrong_solutions=[
        '''class MyHashSet:
    def __init__(self):
        self.items = []

    def add(self, key):
        self.items.append(key)              # duplicates pile up...

    def remove(self, key):
        if key in self.items:
            self.items.remove(key)          # ...and only one copy is removed

    def contains(self, key):
        return key in self.items
''',
        '''class MyHashSet:
    def __init__(self):
        self.size = 1009
        self.slots = [None] * self.size

    def add(self, key):
        self.slots[key % self.size] = key   # a colliding key overwrites the old one

    def remove(self, key):
        if self.slots[key % self.size] == key:
            self.slots[key % self.size] = None

    def contains(self, key):
        return self.slots[key % self.size] == key
''',
    ],
    guide=dict(
        prereqs="The lesson *Inside dict and set: hashing, collisions, resizing* — buckets, hash function, separate chaining.",
        intuition="A hash set is an array of **buckets**. A hash function (here `key % size`) decides which bucket a key lives in, so you only ever search one short bucket instead of everything. Keys that land in the same bucket (a *collision*) share a small list — separate chaining.",
        hints=[
            "A boolean list of size 10^6 + 1 works for the LeetCode limits, but wastes memory and isn't a hash table.",
            "Pick a number of buckets (a prime such as 1009) and send key to bucket key % 1009.",
            "Each bucket is a list: add only if absent, remove only if present.",
        ],
        brute_force="One plain list of all keys: every operation scans it — O(n) each. Or a direct-address table (`[False] * 1_000_001`): O(1) but memory proportional to the key range.",
        approach="""
1. `buckets = [[] for _ in range(1009)]`.
2. `add`: find the bucket; append if the key isn't already there.
3. `remove`: find the bucket; remove the key if present.
4. `contains`: `key in bucket`.

**Dry run** with keys 10, 1019, 2028 (all `% 1009 == 10`):

- add(10), add(1019), add(2028) → bucket 10 = `[10, 1019, 2028]`
- remove(1019) → bucket 10 = `[10, 2028]`
- contains(1019) → False; contains(2028) → True
""",
        complexity="Average **O(1 + n/buckets)** per operation — O(1) while the load factor stays small; worst case O(n) if everything collides. Space O(buckets + n).",
        pitfalls="- Overwriting on collision loses keys.\n- Appending without checking stores duplicates, so one `remove` leaves a copy behind.\n- `[[]] * size` makes every bucket the **same** list.",
        follow_up="Add resizing (double the bucket count and re-insert when load factor > 0.75). Try open addressing with tombstones. *Design HashMap* stores `(key, value)` pairs the same way.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="design-hashmap",
    title="Design HashMap",
    difficulty="Easy",
    pattern="Arrays & Hashing",
    leetcode=_lc("design-hashmap"),
    neetcode=_nc("design-hashmap"),
    kind="class",
    entry="MyHashMap",
    description=r"""
Build your own map from integer keys to integer values **without using Python's `dict`**. Implement
`MyHashMap`:

- `put(key, value)` — store the pair; if `key` already exists, **replace** its value;
- `get(key)` — return the value stored for `key`, or `-1` if the key is absent;
- `remove(key)` — delete the key and its value if present.

**Constraints**

- `0 <= key, value <= 10^6` on LeetCode (our judge uses keys up to about 3·10^6); up to `10^4` calls

**Example:**

```
MyHashMap()
put(1, 1); put(2, 2)
get(1) -> 1
get(3) -> -1
put(2, 1)          # overwrite
get(2) -> 1
remove(2)
get(2) -> -1
```
""",
    starter='''class MyHashMap:

    def __init__(self):
        pass

    def put(self, key: int, value: int) -> None:
        pass

    def get(self, key: int) -> int:
        pass

    def remove(self, key: int) -> None:
        pass
''',
    solution='''class MyHashMap:
    def __init__(self):
        self.size = 1009
        self.buckets = [[] for _ in range(self.size)]

    def put(self, key, value):
        b = self.buckets[key % self.size]
        for pair in b:
            if pair[0] == key:
                pair[1] = value                  # existing key: overwrite
                return
        b.append([key, value])

    def get(self, key):
        for k, v in self.buckets[key % self.size]:
            if k == key:
                return v
        return -1

    def remove(self, key):
        b = self.buckets[key % self.size]
        for i, pair in enumerate(b):
            if pair[0] == key:
                b.pop(i)
                return
''',
    tests=[
        [["MyHashMap", "put", "put", "get", "get", "put", "get", "remove", "get"],
         [[], [1, 1], [2, 2], [1], [3], [2, 1], [2], [2], [2]]],
        [["MyHashMap", "get", "remove", "get"], [[], [0], [0], [0]]],
        [["MyHashMap", "put", "get", "put", "get"], [[], [5, 0], [5], [5, 9], [5]]],
        [["MyHashMap", "put", "put", "get", "get", "remove", "get", "get"],
         [[], [0, 10], [1009, 20], [0], [1009], [0], [0], [1009]]],
        [["MyHashMap", "put", "put", "put", "remove", "get", "get", "get"],
         [[], [10, 1], [1019, 2], [2028, 3], [1019], [10], [1019], [2028]]],
        [["MyHashMap", "put", "remove", "put", "get"], [[], [7, 7], [7], [7, 8], [7]]],
        [["MyHashMap", "put", "get", "get"], [[], [1000000, 1000000], [1000000], [999999]]],
        [["MyHashMap", "put", "put", "put", "get"], [[], [4, 1], [4, 2], [4, 3], [4]]],
        [["MyHashMap", "put", "remove", "remove", "get"], [[], [2, 0], [2], [2], [2]]],
        [_map_ops, _map_args],
    ],
    examples=1,
    wrong_solutions=[
        '''class MyHashMap:
    def __init__(self):
        self.size = 1009
        self.buckets = [[] for _ in range(self.size)]

    def put(self, key, value):
        self.buckets[key % self.size].append([key, value])   # never overwrites: old value found first

    def get(self, key):
        for k, v in self.buckets[key % self.size]:
            if k == key:
                return v
        return -1

    def remove(self, key):
        b = self.buckets[key % self.size]
        for i, pair in enumerate(b):
            if pair[0] == key:
                b.pop(i)
                return
''',
        '''class MyHashMap:
    def __init__(self):
        self.size = 1009
        self.slots = [None] * self.size

    def put(self, key, value):
        self.slots[key % self.size] = (key, value)           # collisions overwrite each other

    def get(self, key):
        e = self.slots[key % self.size]
        return e[1] if e and e[0] == key else -1

    def remove(self, key):
        e = self.slots[key % self.size]
        if e and e[0] == key:
            self.slots[key % self.size] = None
''',
    ],
    guide=dict(
        prereqs="*Design HashSet*; the lesson *Inside dict and set*.",
        intuition="Exactly a hash set whose buckets hold `[key, value]` pairs. The key picks the bucket; inside the bucket you search for the pair with that key and read, replace or delete it.",
        hints=[
            "Reuse the HashSet design; what must each bucket store now?",
            "put has two cases: key already in the bucket (replace) or not (append).",
            "get returns -1 — not None — when the key is missing.",
        ],
        brute_force="A single list of pairs scanned on every call (O(n) each), or a direct-address list of size 10⁶ + 1 filled with −1 (O(1) but memory-hungry).",
        approach="""
1. `buckets = [[] for _ in range(1009)]`; bucket index = `key % 1009`.
2. `put`: scan the bucket; if a pair has this key set `pair[1] = value`, else append `[key, value]`.
3. `get`: scan; return the value or `-1`.
4. `remove`: scan; `pop` the pair if found.

**Dry run:** `put(1,1)`, `put(2,2)` → buckets 1 and 2 hold `[[1,1]]`, `[[2,2]]`. `put(2,1)` finds key 2 →
`[[2,1]]`. `get(2)` → 1. `remove(2)` → bucket 2 empty → `get(2)` → −1.
""",
        complexity="Average **O(1)** per operation with a bounded load factor; worst case O(n). Space O(buckets + n).",
        pitfalls="- Appending on every `put` leaves stale values that `get` finds first.\n- Storing pairs as tuples means you can't assign `pair[1]`; replace the whole entry instead.\n- A value of `0` is valid — don't test truthiness of the value.",
        follow_up="Resize when the load factor grows; implement open addressing; make it generic with Python's `hash()` for any hashable key. *LRU Cache* builds on a hash map plus a linked list.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="sort-an-array",
    title="Sort an Array",
    difficulty="Medium",
    pattern="Arrays & Hashing",
    leetcode=_lc("sort-an-array"),
    neetcode=_nc("sort-an-array"),
    entry="sortArray",
    description=r"""
Return the integers of `nums` in ascending (non-decreasing) order. You must **write the sorting algorithm
yourself** — no `sorted()` or `.sort()` — and it must run in **O(n log n)** time in the worst case with
as little extra space as you can manage.

**Constraints**

- `1 <= len(nums) <= 5 * 10^4`
- `-5 * 10^4 <= nums[i] <= 5 * 10^4`

**Example 1:** `nums = [5, 2, 3, 1]` → `[1, 2, 3, 5]`

**Example 2:** `nums = [5, 1, 1, 2, 0, 0]` → `[0, 0, 1, 1, 2, 5]`
""",
    starter='''class Solution:
    def sortArray(self, nums: List[int]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def sortArray(self, nums):
        if len(nums) <= 1:
            return nums
        mid = len(nums) // 2
        left = self.sortArray(nums[:mid])
        right = self.sortArray(nums[mid:])
        merged, i, j = [], 0, 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged
''',
    tests=[
        [[5, 2, 3, 1]],
        [[5, 1, 1, 2, 0, 0]],
        [[1]],
        [[2, 1]],
        [[1, 2, 3, 4, 5]],
        [[5, 4, 3, 2, 1]],
        [[3, 3, 3]],
        [[-1, -5, 0, 5, 1]],
        [[50000, -50000, 0]],
        [[2, 1, 2, 1, 2, 1, 2]],
        [_sort_big],
        [list(range(6000, 0, -1))],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def sortArray(self, nums):
        if len(nums) <= 1:
            return nums
        mid = len(nums) // 2
        left = self.sortArray(nums[:mid])
        right = self.sortArray(nums[mid:])
        merged, i, j = [], 0, 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
        return merged                       # forgot the leftovers of the longer half
''',
        '''class Solution:
    def sortArray(self, nums):
        count = {}
        for x in nums:
            count[x] = True                 # remembers presence, not how many
        return [v for v in range(-50000, 50001) if v in count]
''',
    ],
    guide=dict(
        prereqs="Merging two sorted lists (*Merge Sorted Array*); recursion — a function that calls itself on smaller inputs.",
        intuition="**Merge sort**: a list of length 0 or 1 is already sorted. For anything longer, split it in half, sort each half the same way, then *merge* the two sorted halves by repeatedly taking the smaller front element.",
        hints=[
            "Bubble/insertion sort are O(n²) — too slow for 5·10⁴ elements.",
            "Split in half, sort both halves recursively, merge.",
            "After the merge loop, one half still has elements left — append them.",
        ],
        brute_force="Insertion or selection sort: **O(n²)** — about 10⁹ steps for 5·10⁴ elements. Quick-sort with a bad pivot is also O(n²) in the worst case (LeetCode has tests for that).",
        approach="""
1. Base case: length ≤ 1 → return it.
2. `left = sort(first half)`, `right = sort(second half)`.
3. Merge with two indices `i`, `j`: append the smaller of `left[i]`, `right[j]` and advance that index.
4. Append the leftovers.

**Dry run** `[5, 2, 3, 1]`:

- split → `[5, 2]` and `[3, 1]`
- `[5, 2]` → `[5]`, `[2]` → merge → `[2, 5]`
- `[3, 1]` → `[3]`, `[1]` → merge → `[1, 3]`
- merge `[2, 5]` and `[1, 3]`: 1, 2, 3, then leftover 5 → `[1, 2, 3, 5]`

Since values are bounded by ±5·10⁴, **counting sort** (O(n + K)) is an alternative.
""",
        complexity="Time **O(n log n)** always: log n levels of splitting, O(n) merging per level. Space **O(n)** for the merged lists.",
        pitfalls="- Forgetting leftovers after the merge loop.\n- Using `<` instead of `<=` still sorts, but loses *stability* (equal items keeping their original order).\n- Counting-sort variants must store **counts**, not just presence.",
        follow_up="Heap sort gives O(n log n) with O(1) extra space. Quick-sort is O(n log n) on average; randomise the pivot. *Sort List* (LC 148) is merge sort on a linked list.",
    ),
),
# ---------------------------------------------------------------------------
dict(
    id="next-permutation",
    title="Next Permutation",
    difficulty="Medium",
    pattern="Arrays & Hashing",
    leetcode=_lc("next-permutation"),
    neetcode=_nc("next-permutation"),
    entry="nextPermutation",
    inplace_arg=0,
    description=r"""
A **permutation** of a list is one particular ordering of its elements. If you wrote all orderings of
`nums` in dictionary (lexicographic) order — like words in a dictionary, comparing position by position —
each ordering has a "next" one.

Rearrange `nums` **in place** into the next ordering. If `nums` is already the last ordering (sorted in
descending order), wrap around to the first one (sorted ascending). Use only O(1) extra memory; return nothing.

**Constraints**

- `1 <= len(nums) <= 100` on LeetCode (our judge uses 8000, with larger values)
- `0 <= nums[i] <= 100`

**Example 1:** `[1, 2, 3]` → `[1, 3, 2]`

**Example 2:** `[3, 2, 1]` → `[1, 2, 3]`

**Example 3:** `[1, 1, 5]` → `[1, 5, 1]`
""",
    starter='''class Solution:
    def nextPermutation(self, nums: List[int]) -> None:
        """
        Do not return anything, modify nums in-place instead.
        """
        pass
''',
    solution='''class Solution:
    def nextPermutation(self, nums):
        n = len(nums)
        i = n - 2
        while i >= 0 and nums[i] >= nums[i + 1]:     # 1. find the pivot from the right
            i -= 1
        if i >= 0:
            j = n - 1
            while nums[j] <= nums[i]:                # 2. rightmost value bigger than the pivot
                j -= 1
            nums[i], nums[j] = nums[j], nums[i]
        l, r = i + 1, n - 1                          # 3. reverse the tail
        while l < r:
            nums[l], nums[r] = nums[r], nums[l]
            l += 1
            r -= 1
''',
    tests=[
        [[1, 2, 3]],
        [[3, 2, 1]],
        [[1, 1, 5]],
        [[1]],
        [[1, 3, 2]],
        [[2, 3, 1]],
        [[1, 5, 1]],
        [[2, 2, 2]],
        [[1, 2, 4, 3, 3, 1]],
        [[5, 4, 7, 5, 3, 2]],
        [[2, 1, 2, 2, 2]],
        [[0, 1, 0]],
        [_np_big],
        [_np_desc],
    ],
    wrong_solutions=[
        '''class Solution:
    def nextPermutation(self, nums):
        n = len(nums)
        i = n - 2
        while i >= 0 and nums[i] >= nums[i + 1]:
            i -= 1
        if i >= 0:
            nums[i], nums[i + 1] = nums[i + 1], nums[i]     # swaps with the neighbour, not the right value
        l, r = i + 1, n - 1
        while l < r:
            nums[l], nums[r] = nums[r], nums[l]
            l += 1
            r -= 1
''',
        '''class Solution:
    def nextPermutation(self, nums):
        n = len(nums)
        i = n - 2
        while i >= 0 and nums[i] > nums[i + 1]:             # '>' instead of '>=': breaks on duplicates
            i -= 1
        if i >= 0:
            j = n - 1
            while nums[j] < nums[i]:
                j -= 1
            nums[i], nums[j] = nums[j], nums[i]
        l, r = i + 1, n - 1
        while l < r:
            nums[l], nums[r] = nums[r], nums[l]
            l += 1
            r -= 1
''',
    ],
    guide=dict(
        prereqs="In-place swaps and reversing a range with two indices (*Rotate Array*).",
        intuition="""
To get the *next* ordering you want the smallest possible increase, so change the list as far to the
**right** as you can. Scan from the right: as long as values keep rising (right to left), that tail is
already in its largest arrangement. The first value that is **smaller than its right neighbour** — the
*pivot* — is where an increase is possible. Swap it with the smallest tail value that is bigger than it,
then put the tail in its smallest arrangement (ascending), which is a reversal.
""",
        hints=[
            "Compare 1 2 4 3 3 1 with its successor 1 3 1 2 3 4. Which position changed, and why that one?",
            "From the right, find the first i with nums[i] < nums[i+1].",
            "Swap nums[i] with the rightmost element greater than it, then reverse everything after i.",
        ],
        brute_force="Generate all permutations in sorted order and pick the one after the current: O(n! · n) — impossible beyond ~10 elements.",
        approach="""
1. `i = n - 2`; move left while `nums[i] >= nums[i+1]`. Now `i` is the pivot, or `-1` if the list is fully descending.
2. If `i >= 0`: from the right end find `j` with `nums[j] > nums[i]`; swap them.
3. Reverse `nums[i+1:]` in place (the tail is descending, so reversing sorts it ascending).

**Dry run** `[1, 2, 4, 3, 3, 1]`:

- from the right: 3≥1, 3≥3, 4≥3, then `2 < 4` → pivot `i = 1` (value 2)
- rightmost value > 2 is the 3 at index 4 → swap → `[1, 3, 4, 3, 2, 1]`
- reverse the tail `[4, 3, 2, 1]` → `[1, 3, 1, 2, 3, 4]` ✓

For `[3, 2, 1]`: no pivot (`i = -1`) → reverse everything → `[1, 2, 3]`.
""",
        complexity="Time **O(n)** (three linear scans), space **O(1)**.",
        pitfalls="- Use `>=` / `<=` in the scans so duplicates are handled (`[1, 5, 1]`, `[2, 2, 2]`).\n- Swap with the *rightmost greater* element, not the neighbour.\n- Reverse the tail even when there is no pivot.",
        follow_up="*Previous Permutation*: mirror all comparisons. *Permutations* (LC 46) generates all orderings with backtracking; *Next Greater Element III* applies this algorithm to the digits of a number.",
    ),
),
]
