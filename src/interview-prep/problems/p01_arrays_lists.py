import random

R = random.Random(11)
G = ("prereqs", "intuition", "hints", "brute_force", "approach", "complexity", "pitfalls", "follow_up")


def _starter(sol):
    out = []
    for ln in sol.splitlines():
        s = ln.strip()
        if ln.startswith("class "):
            out.append(ln)
        elif s.startswith("def ") and (ln.startswith("    def ") or ln.startswith("def ")) and (
                not s.startswith("def _") or s.startswith("def __init__")):
            out.append(ln)
            out.append(ln[:len(ln) - len(ln.lstrip())] + "    pass")
    return "\n".join(out) + "\n"


def P(id, title, diff, pattern, entry, desc, sol, tests, wrong, guide, **kw):
    if "class Solution" not in sol:
        kw.setdefault("kind", "class")
    return dict(id="ctci-" + id, title=title, difficulty=diff, pattern=pattern, entry=entry,
                description=desc.strip() + "\n", starter=_starter(sol), solution=sol, tests=tests,
                wrong_solutions=wrong, guide=dict(zip(G, guide)), **kw)


def _rs(n, alpha="abcdefghijklmnopqrstuvwxyz"):
    return "".join(R.choice(alpha) for _ in range(n))


_big_grid = [[R.randint(1, 9) for _ in range(60)] for _ in range(60)]
_zero_grid = [[R.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5])
               for _ in range(40)] for _ in range(50)]

PROBLEMS = [
P("distinct-badge-code", "Distinct Badge Code", "Easy", "Arrays & Strings", "allDistinct",
"""
A conference prints a short code on every badge. A code is **valid** only when no character appears in it more than once.
Upper-case and lower-case letters count as different characters, and a space is a character like any other.

Write `allDistinct(code)` that returns `True` when every character of `code` is different from all the others, and `False` otherwise.
The empty string is valid.

**Constraints:** `0 <= len(code) <= 10^5`; characters are printable ASCII.

**Example 1:** `code = "kiwi"` → `False` (the letter `i` appears twice)

**Example 2:** `code = "Aa1!"` → `True`
""",
'''class Solution:
    def allDistinct(self, code: str) -> bool:
        seen = set()
        for ch in code:
            if ch in seen:
                return False
            seen.add(ch)
        return True
''',
[["kiwi"], ["Aa1!"], [""], ["x"], ["aA"], ["  "], ["abcdefghijklmnopqrstuvwxyz"], ["abcdefghijklmnopqrstuvwxyza"],
 ["0123456789 9"], ["".join(chr(c) for c in range(32, 127))], ["".join(chr(c) for c in range(32, 127)) + "~"],
 [_rs(100000)], ["qwerty uiop"]],
['''class Solution:
    def allDistinct(self, code):
        return len(set(code.lower())) == len(code)
''', '''class Solution:
    def allDistinct(self, code):
        return all(code[i] != code[i + 1] for i in range(len(code) - 1))
'''],
("Python sets and the idea of a hash table: see [Hash maps and sets](#/lesson/neet-arrays/arrays-hashing-pattern).",
 "A repeat exists exactly when you meet a character you have already met. A set answers \"have I met this before?\" in constant time, so one pass is enough.",
 ["What would you do by hand? You would keep a list of the characters you have already read.",
  "Which data structure answers \"is this in my list?\" without scanning the list?",
  "Walk the string once; return False the moment a character is already in your set. If the loop ends, return True."],
 "Compare every character with every later character: two nested loops, O(n²) time, O(1) extra space. Fine for 20 characters, hopeless for 100,000.",
 "Keep an empty set. For each character: if it is in the set, stop with `False`; otherwise add it.\n\nDry run on `kiwi`: `k` → set {k}; `i` → {k,i}; `w` → {k,i,w}; `i` is already there → `False`.\n\nA useful observation to say aloud: with printable ASCII there are only 95 possible characters, so any string longer than 95 must contain a repeat.",
 "Time O(n), and in fact O(min(n, alphabet)) because the loop must stop once the alphabet is exhausted. Space O(alphabet) for the set.",
 "Lower-casing the input (the statement says case matters). Comparing only neighbouring characters. Forgetting the empty string.",
 "Do it with no extra data structure: sort the characters first (O(n log n)) and compare neighbours, or use one integer as a bit set when the alphabet is a-z. See [Bit tricks](#/lesson/neet-greedy-math/bit-tricks).")),

P("shuffled-twins", "Shuffled Twins", "Easy", "Arrays & Strings", "isShuffle",
"""
Two strings are **shuffled twins** when one can be turned into the other only by re-ordering its characters:
nothing is added, removed or changed. Case matters and spaces count.

Write `isShuffle(a, b)` that returns `True` when `a` and `b` are shuffled twins.

**Constraints:** `0 <= len(a), len(b) <= 10^5`.

**Example 1:** `a = "stream", b = "master"` → `True`

**Example 2:** `a = "aab", b = "abb"` → `False` (same letters, different counts)
""",
'''class Solution:
    def isShuffle(self, a: str, b: str) -> bool:
        if len(a) != len(b):
            return False
        count = {}
        for ch in a:
            count[ch] = count.get(ch, 0) + 1
        for ch in b:
            left = count.get(ch, 0)
            if left == 0:
                return False
            count[ch] = left - 1
        return True
''',
[["stream", "master"], ["aab", "abb"], ["", ""], ["a", ""], ["Dog", "god"], ["a b", "ba "], ["abc", "abcd"],
 ["aabbcc", "abcabc"], ["aaab", "abbb"], ["x" * 20000 + "y" * 20000, "yx" * 20000],
 ["x" * 20000 + "y" * 20000, "yx" * 19999 + "yy"], ["listen", "silent"], ["ab", "cd"]],
['''class Solution:
    def isShuffle(self, a, b):
        return set(a) == set(b) and len(a) == len(b)
'''],
("Counting with a dictionary: see [Hash maps and sets](#/lesson/neet-arrays/arrays-hashing-pattern).",
 "Re-ordering never changes how many times each character occurs. So two strings are twins exactly when their character counts match.",
 ["If the lengths differ, can they ever be twins?",
  "Count each character of the first string in a dictionary.",
  "Walk the second string and decrease the counts; a count that would go below zero proves a mismatch."],
 "Sort both strings and compare: O(n log n). Shorter to write and perfectly acceptable to mention first.",
 "1. Different lengths → `False`.\n2. Count the characters of `a`.\n3. For each character of `b`, take one away; if none is left, return `False`.\n4. Lengths were equal, so if nothing went negative every count is now zero.\n\nDry run `aab` vs `abb`: counts {a:2, b:1}. Read `a` → {a:1,b:1}; `b` → {a:1,b:0}; `b` again → nothing left → `False`.",
 "Time O(n), space O(k) where k is the number of distinct characters.",
 "Comparing sets instead of counts (`aab` and `abb` have the same set). Skipping the length check, which makes the final step wrong.",
 "Ask the interviewer whether case and whitespace matter; here they do. The same counting idea solves grouping problems: see [Group Anagrams](#/problem/group-anagrams).")),

P("run-length-shrink", "Run-Length Shrink", "Easy", "Arrays & Strings", "shrink",
"""
A sensor writes a log made only of letters. To save space we replace every run of the same letter by the letter followed by the run's length:
`"hhhhjjk"` becomes `"h4j2k1"`.

Write `shrink(log)` that returns the shrunk text, **unless** the shrunk text is not strictly shorter than the original, in which case return the original unchanged.

**Constraints:** `0 <= len(log) <= 10^5`; only letters `a-z`, `A-Z` (case matters).

**Example 1:** `"hhhhjjk"` → `"h4j2k1"`

**Example 2:** `"abc"` → `"abc"` (the shrunk form `a1b1c1` is longer)
""",
'''class Solution:
    def shrink(self, log: str) -> str:
        parts = []
        i, n = 0, len(log)
        while i < n:
            j = i
            while j < n and log[j] == log[i]:
                j += 1
            parts.append(log[i])
            parts.append(str(j - i))
            i = j
        packed = "".join(parts)
        return packed if len(packed) < len(log) else log
''',
[["hhhhjjk"], ["abc"], [""], ["a"], ["aa"], ["aaa"], ["aabb"], ["aAaA"], ["zzzzzzzzzzzz"], ["ppqrrrrrpp"],
 ["q" * 100000], ["ab" * 50000], ["aaabbbcccd"], ["wwwwwwwwwwX"]],
['''class Solution:
    def shrink(self, log):
        parts = []
        i, n = 0, len(log)
        while i < n:
            j = i
            while j < n and log[j] == log[i]:
                j += 1
            parts.append(log[i] + str(j - i))
            i = j
        return "".join(parts)
''', '''class Solution:
    def shrink(self, log):
        out = ""
        for ch in sorted(set(log)):
            out += ch + str(log.count(ch))
        return out if len(out) < len(log) else log
'''],
("String building and two indexes on one string: see [Two pointers](#/lesson/neet-arrays/two-pointers-pattern).",
 "A run is a stretch of equal neighbours. Find where each run starts and ends, write letter plus length, then compare lengths once at the end.",
 ["Use one index for the start of a run and a second that walks to its end.",
  "Collect the pieces in a list and join once; repeated `+=` on strings copies the text again and again.",
  "Only after building the packed text decide which of the two strings to return."],
 "Append to a string with `+=` for every character. In languages with immutable strings this copies the growing string each time and costs O(n²).",
 "`i` marks a run start. Move `j` forward while `log[j] == log[i]`. Emit `log[i]` and `j - i`, then set `i = j`.\n\nDry run `hhhhjjk`: run `h` from 0 to 4 → `h4`; run `j` from 4 to 6 → `j2`; run `k` from 6 to 7 → `k1`. Result `h4j2k1` (6 characters) is shorter than 7, so return it.",
 "Time O(n): each character is visited once by `j`. Space O(n) for the output.",
 "Returning the packed form when it has the *same* length (`aabb` → `a2b2` is not shorter). Counting letters globally instead of per run. Runs of 10 or more need two digits, which `str()` handles.",
 "Compute the packed length first without building it, so that you allocate nothing when the answer is the original. Then write a matching `expand` function.")),

P("one-typo-apart", "One Typo Apart", "Medium", "Arrays & Strings", "oneTypoApart",
"""
A spell checker treats two words as *close* when you can turn the first into the second with **at most one** of these typing slips:
insert one character, delete one character, or replace one character by another. Identical words are close (zero slips).

Write `oneTypoApart(a, b)` returning `True` when the words are close.

**Constraints:** `0 <= len(a), len(b) <= 10^5`.

**Example 1:** `a = "plane", b = "plan"` → `True` (delete `e`)

**Example 2:** `a = "plane", b = "blank"` → `False` (two replacements needed)
""",
'''class Solution:
    def oneTypoApart(self, a: str, b: str) -> bool:
        if len(a) > len(b):
            a, b = b, a
        if len(b) - len(a) > 1:
            return False
        i = j = 0
        used = False
        while i < len(a) and j < len(b):
            if a[i] == b[j]:
                i += 1
                j += 1
                continue
            if used:
                return False
            used = True
            if len(a) == len(b):
                i += 1
            j += 1
        return True
''',
[["plane", "plan"], ["plane", "blank"], ["", ""], ["", "a"], ["a", ""], ["ab", ""], ["cat", "cut"], ["cat", "cats"],
 ["cat", "scat"], ["cat", "coat"], ["cat", "act"], ["abcd", "abxy"], ["abc", "abcde"], ["a" * 30000, "a" * 29999],
 ["a" * 15000 + "b" + "a" * 15000, "a" * 15000 + "c" + "a" * 15000], ["ab" * 20000, "ba" * 20000], ["teh", "the"]],
['''class Solution:
    def oneTypoApart(self, a, b):
        if abs(len(a) - len(b)) > 1:
            return False
        return sum(x != y for x, y in zip(a, b)) <= 1
'''],
("Two pointers moving through two sequences: see [Two pointers](#/lesson/neet-arrays/two-pointers-pattern).",
 "Insert and delete are the same slip seen from the two sides, so only the length difference matters: equal lengths means \"at most one replacement\", lengths differing by one means \"the longer word has one extra character\".",
 ["If the lengths differ by two or more, the answer is immediate.",
  "Make `a` the shorter word so that you only handle one direction.",
  "Walk both words. At the first mismatch spend your single allowance: for equal lengths advance both indexes, otherwise advance only the index of the longer word."],
 "Generate every string one slip away from `a` and look for `b`: O(n · alphabet) candidates of length n, so O(n²) work or worse.",
 "Swap so `a` is not longer. If `len(b) - len(a) > 1` return `False`. Scan with `i` on `a`, `j` on `b`. On a mismatch: if a slip was already used, fail; otherwise mark it used and skip one character of `b` (and of `a` too when the lengths are equal).\n\nDry run `cat` / `coat`: `c=c`; `a≠o` → slip used, lengths differ so only `j` moves; `a=a`; `t=t`; end → `True`.",
 "Time O(n), space O(1).",
 "Counting positional mismatches with `zip` fails for inserts (`cat` vs `scat` mismatches at every position). A swap of neighbours (`teh`/`the`) is two replacements, so it is not close.",
 "The general version with any number of slips is edit distance: see [Edit Distance](#/problem/edit-distance) and the lesson [DP on strings](#/lesson/neet-dp/dp-strings).")),

P("quarter-turn-grid", "Quarter-Turn Grid", "Medium", "Arrays & Strings", "rotateGrid",
"""
A square photo is stored as an `n × n` grid of integers (one per pixel). Turn the photo **90 degrees clockwise, in place**:
change the grid you are given and return nothing. You may not build a second `n × n` grid.

**Constraints:** `1 <= n <= 200`.

**Example 1:** `[[1,2],[3,4]]` becomes `[[3,1],[4,2]]`

**Example 2:** `[[1,2,3],[4,5,6],[7,8,9]]` becomes `[[7,4,1],[8,5,2],[9,6,3]]`
""",
'''class Solution:
    def rotateGrid(self, grid: List[List[int]]) -> None:
        n = len(grid)
        for layer in range(n // 2):
            first, last = layer, n - 1 - layer
            for k in range(last - first):
                top = grid[first][first + k]
                grid[first][first + k] = grid[last - k][first]
                grid[last - k][first] = grid[last][last - k]
                grid[last][last - k] = grid[first + k][last]
                grid[first + k][last] = top
''',
[[[[1, 2], [3, 4]]], [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]], [[[5]]],
 [[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]], [[[0, 0], [0, 0]]], [[[1, 1], [2, 2]]],
 [[[i * 5 + j for j in range(5)] for i in range(5)]], [[[-1, 2], [3, -4]]], [[[i * 6 + j for j in range(6)] for i in range(6)]],
 [_big_grid], [[[R.randint(-99, 99) for _ in range(151)] for _ in range(151)]]],
['''class Solution:
    def rotateGrid(self, grid):
        n = len(grid)
        for i in range(n):
            for j in range(i + 1, n):
                grid[i][j], grid[j][i] = grid[j][i], grid[i][j]
''', '''class Solution:
    def rotateGrid(self, grid):
        grid.reverse()
        for row in grid:
            row.reverse()
'''],
("2-D lists and index arithmetic: see [Matrix tricks](#/lesson/neet-greedy-math/matrix-tricks).",
 "Think of the square as onion rings. In one ring every cell belongs to a group of four cells that trade places: top → right → bottom → left → top. Rotating a ring is a series of four-way swaps.",
 ["Where does the cell at row `r`, column `c` end up? At row `c`, column `n-1-r`.",
  "Handle the outer ring first, then the next ring inward. There are `n // 2` rings.",
  "Alternative that is easier to remember: transpose the grid (swap across the main diagonal), then reverse each row."],
 "Build a new grid with `new[c][n-1-r] = old[r][c]`. Correct and O(n²) time, but uses O(n²) extra memory, which the statement forbids.",
 "For each `layer` let `first = layer`, `last = n-1-layer`. For offset `k` from 0 to `last-first-1`, save the top cell, move left → top, bottom → left, right → bottom, saved top → right.\n\nDry run on the 2×2 example: one layer, `k = 0`. Save top `1`. Top gets left `3`. Left gets bottom `4`. Bottom gets right `2`. Right gets saved `1`. Grid: `[[3,1],[4,2]]`.",
 "Time O(n²) because every cell moves once; that is optimal since every cell must be touched. Space O(1).",
 "Looping `k` up to and including `last - first` rotates the corners twice. Transposing only (a mirror, not a turn). Reversing rows and columns gives 180 degrees.",
 "Rotate counter-clockwise, or rotate a non-square image (which cannot be done in place in the same way). See [Rotate Image](#/problem/rotate-image) for the transpose-and-reverse view.")),

P("blackout-rows-cols", "Blackout Rows and Columns", "Medium", "Arrays & Strings", "blackout",
"""
A seating chart is an `m × n` grid of integers. A `0` marks a broken seat. For safety, every seat that shares a **row or a column with an originally broken seat** must also be set to `0`.

Change the grid **in place** and return nothing. Zeros that you write yourself must not trigger further blackouts.

**Constraints:** `1 <= m, n <= 200`.

**Example:** `[[4,1,7],[2,0,5],[3,9,6]]` becomes `[[4,0,7],[0,0,0],[3,0,6]]`
""",
'''class Solution:
    def blackout(self, grid: List[List[int]]) -> None:
        m, n = len(grid), len(grid[0])
        first_row = any(grid[0][c] == 0 for c in range(n))
        first_col = any(grid[r][0] == 0 for r in range(m))
        for r in range(1, m):
            for c in range(1, n):
                if grid[r][c] == 0:
                    grid[r][0] = 0
                    grid[0][c] = 0
        for r in range(1, m):
            for c in range(1, n):
                if grid[r][0] == 0 or grid[0][c] == 0:
                    grid[r][c] = 0
        if first_row:
            for c in range(n):
                grid[0][c] = 0
        if first_col:
            for r in range(m):
                grid[r][0] = 0
''',
[[[[4, 1, 7], [2, 0, 5], [3, 9, 6]]], [[[1, 2], [3, 4]]], [[[0]]], [[[7]]], [[[0, 1, 2], [3, 4, 5]]], [[[1, 2, 3], [4, 5, 0]]],
 [[[1, 0, 3]]], [[[1], [0], [3]]], [[[1, 2, 3, 4], [5, 0, 7, 8], [9, 10, 11, 0]]], [[[0, 1], [1, 1], [1, 0]]],
 [[[1, 1, 1], [1, 1, 1], [0, 1, 1]]], [_zero_grid], [[[1] * 200 for _ in range(199)] + [[1] * 199 + [0]]]],
['''class Solution:
    def blackout(self, grid):
        m, n = len(grid), len(grid[0])
        for r in range(m):
            for c in range(n):
                if grid[r][c] == 0:
                    for k in range(n):
                        grid[r][k] = 0
                    for k in range(m):
                        grid[k][c] = 0
''', '''class Solution:
    def blackout(self, grid):
        m, n = len(grid), len(grid[0])
        for r in range(1, m):
            for c in range(1, n):
                if grid[r][c] == 0:
                    grid[r][0] = 0
                    grid[0][c] = 0
        for r in range(m):
            for c in range(n):
                if grid[r][0] == 0 or grid[0][c] == 0:
                    grid[r][c] = 0
'''],
("Nested loops over a grid: see [Matrix tricks](#/lesson/neet-greedy-math/matrix-tricks).",
 "Separate *finding* from *writing*. First record which rows and columns contain an original zero, then write. The grid's own first row and first column can serve as the notebook, which removes the extra memory.",
 ["If you write zeros while scanning, you will later mistake your own zeros for original ones.",
  "A set of row numbers and a set of column numbers is a clean O(m + n) memory solution; present it first.",
  "To reach O(1) memory, store the marks in row 0 and column 0, after remembering in two booleans whether row 0 and column 0 themselves contain a zero."],
 "Copy the whole grid, scan the copy and write into the original: O(m·n) extra memory. Or, for each cell, scan its whole row and column: O(m·n·(m+n)) time.",
 "1. Booleans: does row 0 hold a zero? does column 0?\n2. For every other cell that is zero, mark `grid[r][0]` and `grid[0][c]`.\n3. For every other cell, zero it when its row mark or column mark is zero.\n4. Finally blank row 0 and column 0 if their booleans say so.\n\nDry run on the example: the zero at (1,1) sets marks `grid[1][0] = 0` and `grid[0][1] = 0`. Step 3 zeroes (1,2) and (2,1). Row 0 and column 0 had no original zero, so only the marks stay zero.",
 "Time O(m·n), space O(1).",
 "Cascading: the first wrong solution turns the whole grid to zeros. Using the marker row before saving whether it had a zero of its own. Processing row 0 and column 0 too early destroys the marks.",
 "Same problem as [Set Matrix Zeroes](#/problem/set-matrix-zeroes). Discuss what changes if the grid is too large for memory and arrives row by row.")),

P("turned-word", "Turned Word", "Easy", "Arrays & Strings", "isTurned",
"""
Take a word written on a paper ring and cut the ring at some point: you get a **turn** of the word. For example the turns of `"tide"` are `"tide"`, `"idet"`, `"deti"` and `"etid"`.

Write `isTurned(word, other)` that returns `True` when `other` is a turn of `word`.

**Constraints:** `0 <= len(word), len(other) <= 10^5`.

**Example 1:** `word = "lantern", other = "ternlan"` → `True`

**Example 2:** `word = "lantern", other = "ternnal"` → `False`
""",
'''class Solution:
    def isTurned(self, word: str, other: str) -> bool:
        return len(word) == len(other) and other in word + word
''',
[["lantern", "ternlan"], ["lantern", "ternnal"], ["", ""], ["a", "a"], ["a", "b"], ["ab", "ba"], ["aab", "aba"],
 ["abc", "abcabc"], ["abcabc", "abc"], ["aaaa", "aaaa"], ["abab", "baba"], ["abcd", "acbd"],
 ["a" * 50000 + "b", "b" + "a" * 50000], ["xy" * 30000, "yx" * 30000], ["tide", "diet"]],
['''class Solution:
    def isTurned(self, word, other):
        return sorted(word) == sorted(other)
''', '''class Solution:
    def isTurned(self, word, other):
        return other in word + word
'''],
("Substring search and string concatenation. See [Pattern matching](#/lesson/dsa-foundations/pattern-matching) for how `in` can be fast.",
 "Cutting the ring splits the word into a front part `x` and a back part `y`, and the turn is `y + x`. Write the word twice: `x y x y`. The middle of that contains `y x`. So every turn is a substring of the doubled word.",
 ["Split the word as `x + y`. What does the turn look like in terms of `x` and `y`?",
  "Where does `y + x` appear inside `x + y + x + y`?",
  "Check equal lengths first, then one substring test on `word + word`."],
 "Try all n cut points and compare the n-character result each time: O(n²).",
 "Return `len(word) == len(other) and other in word + word`.\n\nDry run: `word + word = lanternlantern`. `ternlan` starts at index 3 → `True`. `ternnal` appears nowhere → `False`.",
 "Time O(n) with a linear-time substring search (O(n) typical for Python's `in`), space O(n) for the doubled string.",
 "Forgetting the length check (`abc` is a substring of `abcabcabcabc` but not a turn of `abcabc`). Comparing sorted letters, which accepts any shuffle.",
 "Find the cut position, or decide whether a list is a rotation of another list using [KMP](#/lesson/dsa-foundations/pattern-matching) on the values.")),

P("drop-repeat-nodes", "Drop Repeat Nodes", "Easy", "Linked Lists", "dropRepeats",
"""
A playlist is stored as a singly linked list of track numbers, in no particular order. Remove every node whose value has **already appeared earlier** in the list, keeping the first occurrence and the original order. Return the head.

**Constraints:** `0 <= length <= 10^5`; values fit in 32 bits.

**Example 1:** `4 → 9 → 4 → 2 → 9` → `4 → 9 → 2`

**Example 2:** `7 → 7 → 7` → `7`
""",
'''class Solution:
    def dropRepeats(self, head: Optional[ListNode]) -> Optional[ListNode]:
        seen = set()
        prev, cur = None, head
        while cur:
            if cur.val in seen:
                prev.next = cur.next
            else:
                seen.add(cur.val)
                prev = cur
            cur = cur.next
        return head
''',
[[[4, 9, 4, 2, 9]], [[7, 7, 7]], [[]], [[1]], [[1, 2, 3]], [[1, 1]], [[1, 2, 1, 2, 1, 2]], [[3, 3, 4, 4, 5, 5]],
 [[0, -1, 0, -1]], [[5, 4, 3, 2, 1, 1, 2, 3, 4, 5]], [[R.randint(0, 500) for _ in range(20000)]], [list(range(8000))],
 [[2, 1, 2]]],
['''class Solution:
    def dropRepeats(self, head):
        cur = head
        while cur and cur.next:
            if cur.next.val == cur.val:
                cur.next = cur.next.next
            else:
                cur = cur.next
        return head
'''],
("How a singly linked list is unlinked with a `prev` pointer: see [Linked-list pointers](#/lesson/neet-linked-trees/ll-pointers).",
 "Removing a node means making the node *before* it point past it. So walk with two references, `prev` and `cur`, and a set of the values met so far.",
 ["You need to know whether a value was seen before: which structure gives that in O(1)?",
  "To delete `cur` you must change `prev.next`. Only advance `prev` when you keep the node.",
  "The head is never deleted (it is always a first occurrence), so no dummy node is required here."],
 "For each node, run a second pointer through the rest of the list deleting equal values: O(n²) time, O(1) space. This is the answer when the interviewer forbids extra memory.",
 "Loop while `cur`: if `cur.val` is in `seen`, bypass it with `prev.next = cur.next`; else add the value and move `prev` to `cur`. Always move `cur` forward.\n\nDry run `4→9→4→2→9`: keep 4, keep 9, third node 4 is seen → 9 now points to 2, keep 2, last 9 is seen → 2 points to nothing. Result `4→9→2`.",
 "Time O(n), space O(n) for the set.",
 "Advancing `prev` after a deletion (it would then point at a removed node). Comparing only neighbours, which works only for sorted lists.",
 "No-buffer version with the runner technique (O(n²)). For a sorted list see [Remove Duplicates from Sorted List](#/problem/remove-duplicates-from-sorted-list).")),

P("kth-from-tail", "Kth From the Tail", "Easy", "Linked Lists", "kthFromTail",
"""
A relay team is stored as a singly linked list of runner numbers. Return the number worn by the runner who is `k`-th counting **from the end**, where `k = 1` means the last runner. If the list has fewer than `k` nodes, return `-1`.

Do it in **one pass** without first counting the nodes.

**Constraints:** `0 <= length <= 10^5`, `1 <= k <= 10^5`, values are non-negative.

**Example 1:** list `10 → 20 → 30 → 40`, `k = 2` → `30`

**Example 2:** list `10 → 20`, `k = 5` → `-1`
""",
'''class Solution:
    def kthFromTail(self, head: Optional[ListNode], k: int) -> int:
        lead = head
        for _ in range(k):
            if lead is None:
                return -1
            lead = lead.next
        trail = head
        while lead:
            lead = lead.next
            trail = trail.next
        return trail.val
''',
[[[10, 20, 30, 40], 2], [[10, 20], 5], [[], 1], [[8], 1], [[8], 2], [[1, 2, 3], 3], [[1, 2, 3], 1], [[1, 2, 3], 4],
 [list(range(9000)), 1], [list(range(9000)), 9000], [list(range(9000)), 777], [[5, 5, 6, 5], 2]],
['''class Solution:
    def kthFromTail(self, head, k):
        lead = head
        for _ in range(k):
            if lead is None:
                return -1
            lead = lead.next
        trail = head
        while lead and lead.next:
            lead = lead.next
            trail = trail.next
        return trail.val
'''],
("Two pointers on one list: see [Fast and slow pointers](#/lesson/neet-linked-trees/ll-fast-slow).",
 "Two walkers kept exactly `k` nodes apart behave like a ruler: when the front one falls off the end, the back one is `k` nodes from the end.",
 ["If you knew the length `n`, the answer is at position `n - k` from the front. How can you avoid counting?",
  "Send one pointer `k` steps ahead. What does it mean if it runs out of nodes during those steps?",
  "Then move both one step at a time until the leader becomes `None`."],
 "Count the nodes in a first pass, then walk `n - k` steps in a second pass: O(n) time but two passes. Or copy the values into an array: O(n) space.",
 "Advance `lead` by `k` nodes, returning `-1` if it is `None` before a step. Then move `lead` and `trail` together until `lead` is `None`.\n\nDry run `10→20→30→40`, `k=2`: lead goes to 30. Step: lead 40, trail 20. Step: lead None, trail 30. Answer 30.",
 "Time O(n), space O(1).",
 "Off by one: stopping when `lead.next` is `None` returns the (k+1)-th from the end. Not handling `k` larger than the length.",
 "Delete that node instead of returning it: see [Remove Nth Node From End of List](#/problem/remove-nth-node-from-end-of-list). A recursive version counts on the way back up the call stack and uses O(n) stack space.")),

P("pivot-split-list", "Pivot Split", "Medium", "Linked Lists", "pivotSplit",
"""
Parcels move on a conveyor belt stored as a singly linked list of weights. Re-arrange the belt so that **every parcel lighter than `pivot` comes before every parcel that weighs `pivot` or more**. Inside each of the two groups the parcels must keep their original relative order. Return the new head.

**Constraints:** `0 <= length <= 10^5`.

**Example:** list `6 → 2 → 9 → 4 → 1`, `pivot = 4` → `2 → 1 → 6 → 9 → 4`
""",
'''class Solution:
    def pivotSplit(self, head: Optional[ListNode], pivot: int) -> Optional[ListNode]:
        small_head = small = ListNode()
        big_head = big = ListNode()
        cur = head
        while cur:
            if cur.val < pivot:
                small.next = cur
                small = cur
            else:
                big.next = cur
                big = cur
            cur = cur.next
        big.next = None
        small.next = big_head.next
        return small_head.next
''',
[[[6, 2, 9, 4, 1], 4], [[], 3], [[5], 5], [[5], 9], [[1, 2, 3], 0], [[1, 2, 3], 10], [[3, 3, 3], 3], [[9, 8, 7, 1, 2, 3], 5],
 [[4, 1, 4, 1], 4], [[-2, 5, -7, 0], 0], [[R.randint(0, 1000) for _ in range(15000)], 500], [[2, 1], 2], [[1, 2], 2]],
['''class Solution:
    def pivotSplit(self, head, pivot):
        vals = []
        while head:
            vals.append(head.val)
            head = head.next
        vals.sort()
        dummy = cur = ListNode()
        for v in vals:
            cur.next = ListNode(v)
            cur = cur.next
        return dummy.next
''', '''class Solution:
    def pivotSplit(self, head, pivot):
        new_head = tail = head
        cur = head.next if head else None
        if head:
            head.next = None
        while cur:
            nxt = cur.next
            if cur.val < pivot:
                cur.next = new_head
                new_head = cur
            else:
                tail.next = cur
                cur.next = None
                tail = cur
            cur = nxt
        return new_head
'''],
("Dummy head nodes: see [Linked-list pointers](#/lesson/neet-linked-trees/ll-pointers).",
 "Build two separate chains while walking once: a \"light\" chain and a \"heavy\" chain. Appending at the tail of each chain preserves order. At the end, hook the light tail to the heavy head.",
 ["Do not try to shuffle nodes inside one list; grow two lists instead.",
  "A dummy node in front of each chain removes the special case \"is this the first node of the chain?\".",
  "After the walk, the last heavy node may still point at an old neighbour: set its `next` to `None`."],
 "Copy values into two Python lists, concatenate and rebuild the linked list: O(n) time but O(n) extra memory and new nodes.",
 "Walk `cur`. `val < pivot` → append to `small`; else append to `big`. Then `big.next = None`, `small.next = big_head.next`, return `small_head.next`.\n\nDry run `6→2→9→4→1`, pivot 4: big: 6; small: 2; big: 6→9; big: 6→9→4; small: 2→1. Join: `2→1→6→9→4`.",
 "Time O(n), space O(1): nodes are re-linked, not copied.",
 "Leaving the old `next` of the final heavy node creates a cycle. Sorting changes the order inside the groups. Pushing light nodes at the front reverses them.",
 "Three-way version (less than, equal, greater), the linked-list form of the Dutch flag partition used by [Quick sort](#/lesson/dsa-foundations/quick-sort). Compare with [Partition List](#/problem/partition-list).")),

P("digit-list-sum", "Digit List Sum (Forward Order)", "Medium", "Linked Lists", "addForward",
"""
Two non-negative whole numbers are stored as singly linked lists with **one decimal digit per node, most significant digit first**: `3 → 0 → 5` means 305. The lists may have different lengths and there are no leading zeros (except the number 0 itself, stored as a single node `0`).

Return their sum in the same format.

**Constraints:** each list has between 1 and `10^4` nodes. Do not convert the whole list to a Python integer: the point is the digit-by-digit technique.

**Example 1:** `4 → 8 → 3` plus `7 → 5 → 9` → `1 → 2 → 4 → 2` (483 + 759 = 1242)

**Example 2:** `9 → 9` plus `1` → `1 → 0 → 0`
""",
'''class Solution:
    def addForward(self, a: Optional[ListNode], b: Optional[ListNode]) -> Optional[ListNode]:
        sa, sb = [], []
        while a:
            sa.append(a.val)
            a = a.next
        while b:
            sb.append(b.val)
            b = b.next
        head, carry = None, 0
        while sa or sb or carry:
            total = carry + (sa.pop() if sa else 0) + (sb.pop() if sb else 0)
            carry = total // 10
            head = ListNode(total % 10, head)
        return head
''',
[[[4, 8, 3], [7, 5, 9]], [[9, 9], [1]], [[0], [0]], [[0], [7, 3]], [[5], [5]], [[1, 0, 0, 0], [1]], [[9, 9, 9, 9], [9, 9, 9]],
 [[1], [9, 9, 9, 9, 9]], [[4, 5, 6], [5, 4, 3]], [[9] * 10000, [1]], [[R.randint(1, 9)] + [R.randint(0, 9) for _ in range(9999)],
  [R.randint(1, 9)] + [R.randint(0, 9) for _ in range(7000)]], [[2, 5], [7, 5]]],
['''class Solution:
    def addForward(self, a, b):
        dummy = cur = ListNode()
        carry = 0
        while a or b or carry:
            total = carry + (a.val if a else 0) + (b.val if b else 0)
            carry = total // 10
            cur.next = ListNode(total % 10)
            cur = cur.next
            a = a.next if a else None
            b = b.next if b else None
        return dummy.next
'''],
("Stacks, and adding numbers column by column with a carry: see [Stack basics](#/lesson/neet-window-stack/stack-basics).",
 "School addition starts at the *last* digit, but a singly linked list only lets you walk forward. A stack reverses the order of arrival, so pushing the digits and popping them gives you the digits from least significant to most significant.",
 ["Why can you not add node by node from the heads? Think about `99 + 1`.",
  "Push each list's digits on its own stack, then pop from both.",
  "Create the answer by inserting each new digit in *front* of the result so far; keep going while either stack has digits or the carry is non-zero."],
 "Pad the shorter list with leading zero nodes and recurse to the end, returning the carry on the way back: also O(n) but needs O(n) call-stack depth, which fails for 10⁴ nodes in Python's default recursion limit.",
 "Fill `sa` and `sb`. Loop: `total = carry + pop(sa) + pop(sb)`; new head node holds `total % 10`; `carry = total // 10`.\n\nDry run 483 + 759: pops 3+9 = 12 → node 2, carry 1; 8+5+1 = 14 → node 4 in front, carry 1; 4+7+1 = 12 → node 2 in front, carry 1; stacks empty but carry 1 → node 1 in front. Result `1→2→4→2`.",
 "Time O(n + m), space O(n + m) for the stacks.",
 "Adding from the heads treats the lists as if digits were stored in reverse. Dropping the final carry (`99 + 1`).",
 "The reverse-order storage is easier and needs no stack: see [Add Two Numbers](#/problem/add-two-numbers). You can also reverse both lists in place, add, and reverse the result for O(1) extra memory.")),

P("mirror-list", "Mirror List", "Easy", "Linked Lists", "isMirror",
"""
A necklace of beads is stored as a singly linked list of colour numbers. Return `True` when the sequence of colours reads the same from the clasp end as from the far end.

Aim for **O(1) extra memory**. An empty list counts as a mirror.

**Constraints:** `0 <= length <= 10^5`.

**Example 1:** `3 → 8 → 8 → 3` → `True`

**Example 2:** `3 → 8 → 5` → `False`
""",
'''class Solution:
    def isMirror(self, head: Optional[ListNode]) -> bool:
        slow = fast = head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
        prev = None
        while slow:
            slow.next, prev, slow = prev, slow, slow.next
        left, right = head, prev
        while right:
            if left.val != right.val:
                return False
            left, right = left.next, right.next
        return True
''',
[[[3, 8, 8, 3]], [[3, 8, 5]], [[]], [[4]], [[4, 4]], [[4, 5]], [[1, 2, 1]], [[1, 2, 3, 2, 1]], [[1, 2, 3, 3, 2, 2]],
 [[1, 2, 2, 2]], [list(range(9000)) + list(range(8999, -1, -1))], [list(range(9000)) + [7] + list(range(8999, -1, -1))],
 [list(range(9000)) + list(range(9000))], [[1, 2, 1, 2]], [[1, 2, 3, 1]], [[5, 1, 2, 5]]],
['''class Solution:
    def isMirror(self, head):
        if not head:
            return True
        tail = head
        while tail.next:
            tail = tail.next
        return head.val == tail.val
'''],
("Finding the middle with fast and slow pointers and reversing a list: see [Fast and slow pointers](#/lesson/neet-linked-trees/ll-fast-slow) and [Reversal](#/lesson/neet-linked-trees/ll-reversal).",
 "A mirror sequence equals its own reverse, and you only need to compare the first half with the reversed second half. A list can be reversed by flipping its arrows, with no extra memory.",
 ["The easy version copies the values into an array and compares it with its reverse. Say that first.",
  "Find the middle: move one pointer by one node and another by two.",
  "Reverse the part from the middle onward, then walk from both ends toward the centre comparing values."],
 "Copy into a Python list and check `vals == vals[::-1]`: O(n) time, O(n) space.",
 "1. `slow` reaches the middle when `fast` reaches the end.\n2. Reverse from `slow` to the end; `prev` is the head of the reversed half.\n3. Compare `head...` with `prev...` until the reversed half ends.\n\nDry run `3→8→8→3`: slow stops at the second 8. Reversed half: `3→8`. Compare 3=3, 8=8 → `True`. With an odd length the middle node sits in the reversed half and is compared with itself, which is harmless.",
 "Time O(n), space O(1).",
 "Comparing only the first and last node. Looping on the *left* half instead of the reversed half walks past the middle. In production code, reverse the second half back before returning so the caller's list is intact.",
 "Same task as [Palindrome Linked List](#/problem/palindrome-linked-list). A stack-based variant pushes the first half while the slow pointer walks.")),

P("loop-entry-index", "Loop Entry Index", "Medium", "Linked Lists", "loopEntry",
"""
A treasure hunt has `n` clue cards numbered `0 … n-1`. Card `i` tells you which card to open next: `nxt[i]`, or `-1` when the hunt ends there. You start at card `0`.

A badly designed hunt can send you round in circles forever. Return the number of the **first card you would visit twice** (the entrance of the loop), or `-1` if the hunt ends normally.

Use **O(1) extra memory**: no set of visited cards and no changes to `nxt`.

**Constraints:** `1 <= n <= 10^5`; each `nxt[i]` is `-1` or in `[0, n-1]`.

**Example 1:** `nxt = [1, 2, 3, 1]` → `1` (path 0, 1, 2, 3, 1, …)

**Example 2:** `nxt = [1, 2, -1]` → `-1`
""",
'''class Solution:
    def loopEntry(self, nxt: List[int]) -> int:
        slow = fast = 0
        while True:
            if fast == -1 or nxt[fast] == -1:
                return -1
            slow = nxt[slow]
            fast = nxt[nxt[fast]]
            if slow == fast:
                break
        slow = 0
        while slow != fast:
            slow = nxt[slow]
            fast = nxt[fast]
        return slow
''',
[[[1, 2, 3, 1]], [[1, 2, -1]], [[-1]], [[0]], [[1, 0]], [[1, 1]], [[1, 2, 2]], [[3, 0, 1, 2]], [[2, 0, 1, -1]],
 [[1, 2, 3, 4, 5, 6, 3]], [list(range(1, 12000)) + [-1]], [list(range(1, 12000)) + [0]],
 [list(range(1, 12000)) + [7777]], [list(range(1, 12000)) + [11999]]],
['''class Solution:
    def loopEntry(self, nxt):
        slow = fast = 0
        while True:
            if fast == -1 or nxt[fast] == -1:
                return -1
            slow = nxt[slow]
            fast = nxt[nxt[fast]]
            if slow == fast:
                return slow
'''],
("Cycle detection with a slow and a fast pointer: see [Fast and slow pointers](#/lesson/neet-linked-trees/ll-fast-slow).",
 "The cards form a linked list where `nxt` is the `next` pointer. A walker moving two cards per step must catch a walker moving one card per step if both are trapped in a loop. Where they meet is as far from the loop entrance as the start is (counted modulo the loop length), so a second walk from the start finds the entrance.",
 ["First decide only *whether* a loop exists: fast and slow walkers.",
  "The meeting point is usually not the entrance. Draw a list with a tail of 3 cards and a loop of 5 and see where they meet.",
  "After they meet, put one walker back on card 0 and move both one card at a time. They meet at the entrance."],
 "Keep a set of visited cards and return the first card already in the set: O(n) time but O(n) memory.",
 "Let the tail (cards before the loop) have length `t` and the loop length `L`. When slow enters the loop, fast is `t mod L` cards ahead inside it and closes the gap by one per step, so they meet `L - (t mod L)` cards after the entrance. From there, `t` more steps lands exactly on the entrance, and `t` steps from card 0 also lands on the entrance.\n\nDry run `[1,2,3,1]`: slow 1, fast 2; slow 2, fast 1; slow 3, fast 3 → meet at 3. Reset slow to 0: slow 1, fast 1 → entrance 1.",
 "Time O(n), space O(1).",
 "Returning the meeting point itself. Reading `nxt[-1]`, which in Python silently wraps to the last element: test for `-1` before every jump.",
 "The pointer version is LeetCode's *Linked List Cycle II*; the same trick solves [Find the Duplicate Number](#/problem/find-the-duplicate-number).")),
]

_L = ["list_node"]
_KW = {"quarter-turn-grid": dict(inplace_arg=0), "blackout-rows-cols": dict(inplace_arg=0),
       "drop-repeat-nodes": dict(arg_types=_L, return_type="list_node"), "kth-from-tail": dict(arg_types=["list_node", None]),
       "pivot-split-list": dict(arg_types=["list_node", None], return_type="list_node"),
       "digit-list-sum": dict(arg_types=["list_node", "list_node"], return_type="list_node"),
       "mirror-list": dict(arg_types=_L)}
for _p in PROBLEMS:
    _p.update(_KW.get(_p["id"][5:], {}))
