import random
import string

r = random.Random(99)


def _word(lo=1, hi=8, alpha="abcde"):
    return "".join(r.choice(alpha) for _ in range(r.randint(lo, hi)))


_trie_ops, _trie_args = ["Trie"], [[]]
for _ in range(2500):
    op = r.choice(["insert", "insert", "search", "startsWith"])
    _trie_ops.append(op)
    _trie_args.append([_word()])

_wd_ops, _wd_args = ["WordDictionary"], [[]]
for _ in range(1500):
    if r.random() < 0.45:
        _wd_ops.append("addWord")
        _wd_args.append([_word(1, 6, "abc")])
    else:
        w = list(_word(1, 6, "abc"))
        for i in range(len(w)):
            if r.random() < 0.3:
                w[i] = "."
        _wd_ops.append("search")
        _wd_args.append(["".join(w)])

_board_big = [[r.choice("abcd") for _ in range(12)] for _ in range(12)]
_words_big = list({_word(1, 10, "abcd") for _ in range(1500)})
_words_big.sort()
_board_a = [["a"] * 4 for _ in range(4)]
_words_a = ["a" * k for k in range(1, 9)] + ["a" * 7 + "b", "b"]

PROBLEMS = [
# ============================================================================================
dict(
    id="implement-trie-prefix-tree",
    title="Implement Trie (Prefix Tree)",
    difficulty="Medium",
    pattern="Tries",
    leetcode="https://leetcode.com/problems/implement-trie-prefix-tree/",
    neetcode="https://neetcode.io/problems/implement-prefix-tree",
    kind="class",
    entry="Trie",
    description=r"""
Build a **trie** (prefix tree) that stores lowercase words:

- `Trie()` — create an empty trie.
- `insert(word)` — add `word`.
- `search(word)` — `True` if `word` was inserted before (as a whole word).
- `startsWith(prefix)` — `True` if some inserted word begins with `prefix`.

**Constraints**

- `1 <= len(word), len(prefix) <= 2000`, lowercase English letters only.
- Up to $3 \cdot 10^4$ calls in total.

**Judge input format:** two lists — operation names and argument lists. The output is the list of return
values (`None` for the constructor and for `insert`).

**Example:**
`["Trie","insert","search","search","startsWith","insert","search"]`,
`[[],["apple"],["apple"],["app"],["app"],["app"],["app"]]`
→ `[None,None,True,False,True,None,True]`
""",
    starter='''class Trie:

    def __init__(self):
        pass

    def insert(self, word: str) -> None:
        pass

    def search(self, word: str) -> bool:
        pass

    def startsWith(self, prefix: str) -> bool:
        pass
''',
    solution='''class TrieNode:
    __slots__ = ("children", "end")

    def __init__(self):
        self.children = {}
        self.end = False


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for ch in word:
            node = node.children.setdefault(ch, TrieNode())
        node.end = True

    def _walk(self, s):
        node = self.root
        for ch in s:
            node = node.children.get(ch)
            if node is None:
                return None
        return node

    def search(self, word):
        node = self._walk(word)
        return node is not None and node.end

    def startsWith(self, prefix):
        return self._walk(prefix) is not None
''',
    tests=[
        [["Trie", "insert", "search", "search", "startsWith", "insert", "search"],
         [[], ["apple"], ["apple"], ["app"], ["app"], ["app"], ["app"]]],
        [["Trie", "search", "startsWith"], [[], ["a"], ["a"]]],
        [["Trie", "insert", "search", "startsWith", "search"], [[], ["a"], ["a"], ["a"], ["aa"]]],
        [["Trie", "insert", "insert", "search", "search", "startsWith", "startsWith"],
         [[], ["car"], ["cart"], ["car"], ["ca"], ["cart"], ["carts"]]],
        [["Trie", "insert", "insert", "search", "search", "search"], [[], ["ab"], ["abc"], ["ab"], ["abc"], ["a"]]],
        [["Trie", "insert", "startsWith", "search", "insert", "search"], [[], ["hello"], ["hell"], ["hell"], ["hell"], ["hell"]]],
        [["Trie", "insert", "insert", "startsWith", "search"], [[], ["xyz"], ["xya"], ["xy"], ["xy"]]],
        [["Trie", "insert", "search", "startsWith"], [[], ["z" * 2000], ["z" * 1999], ["z" * 2000]]],
        [_trie_ops, _trie_args],
    ],
    examples=1,
    wrong_solutions=[
        '''class Trie:
    # treats every prefix as a stored word
    def __init__(self):
        self.prefixes = set()

    def insert(self, word):
        for i in range(1, len(word) + 1):
            self.prefixes.add(word[:i])

    def search(self, word):
        return word in self.prefixes

    def startsWith(self, prefix):
        return prefix in self.prefixes
''',
        '''class Trie:
    def __init__(self):
        self.words = set()

    def insert(self, word):
        self.words.add(word)

    def search(self, word):
        return word in self.words

    def startsWith(self, prefix):
        return any(w.startswith(prefix[:-1]) for w in self.words)   # off by one
''',
    ],
    guide=dict(
        prereqs="Lesson *Tries: prefix trees from scratch*.",
        intuition="Store words character by character along a path from the root. Words that share a prefix share the nodes of that prefix. A boolean flag on a node marks 'a word ends here', which is what separates `search` from `startsWith`.",
        hints=["Each node holds a dict `children: char -> node` and a flag `end`.",
               "`insert`: walk the characters, creating missing children; set `end = True` on the last node.",
               "`search` and `startsWith` share one helper that walks a string and returns the final node (or None); they differ only in whether they check `end`."],
        brute_force="A Python `set` of words handles `search` in O(L); `startsWith` then needs scanning all words — O(N·L) per query. Storing every prefix in a second set makes `startsWith` fast but costs O(sum of L²) memory.",
        approach="""After inserting `apple`: root → a → p → p → l → e(end).

- `search("apple")`: path exists and `e.end` → True.
- `search("app")`: path exists but the second `p` has `end = False` → False.
- `startsWith("app")`: the path exists → True.
- `insert("app")` sets `end` on the second `p`; now `search("app")` → True.""",
        complexity="Each operation is O(L) for a word of length L. Space O(total characters inserted) in the worst case (no shared prefixes).",
        pitfalls="- Forgetting the `end` flag (then every prefix looks like a word).\n- Creating nodes during `search` (using `setdefault` there pollutes the trie).\n- Using a 26-slot array per node in Python wastes memory; a dict is idiomatic.",
        follow_up="Count words with a prefix (store a counter per node), delete words, or autocomplete (DFS from the prefix node).",
    ),
),
# ============================================================================================
dict(
    id="design-add-and-search-words-data-structure",
    title="Design Add and Search Words Data Structure",
    difficulty="Medium",
    pattern="Tries — Wildcard DFS",
    leetcode="https://leetcode.com/problems/design-add-and-search-words-data-structure/",
    neetcode="https://neetcode.io/problems/design-word-search-data-structure",
    kind="class",
    entry="WordDictionary",
    description=r"""
Design a dictionary of lowercase words that supports wildcard lookups:

- `WordDictionary()` — create an empty dictionary.
- `addWord(word)` — store `word`.
- `search(pattern)` — `True` if some stored word has exactly the pattern's length and matches it, where
  a `.` in the pattern matches **any single letter**.

**Constraints**

- `1 <= len(word) <= 25`; `addWord` words are lowercase; search patterns are lowercase letters or `.`, with at most 2 dots on LeetCode (the judge's random test allows more).
- Up to $10^4$ calls.

**Judge input format:** two lists — operation names and argument lists; output is the list of return values.

**Example:**
`["WordDictionary","addWord","addWord","addWord","search","search","search","search"]`,
`[[],["bad"],["dad"],["mad"],["pad"],["bad"],[".ad"],["b.."]]`
→ `[None,None,None,None,False,True,True,True]`
""",
    starter='''class WordDictionary:

    def __init__(self):
        pass

    def addWord(self, word: str) -> None:
        pass

    def search(self, word: str) -> bool:
        pass
''',
    solution='''class WordDictionary:
    def __init__(self):
        self.root = {}

    def addWord(self, word):
        node = self.root
        for ch in word:
            node = node.setdefault(ch, {})
        node["$"] = True

    def search(self, word):
        def dfs(node, i):
            if i == len(word):
                return "$" in node
            ch = word[i]
            if ch == ".":
                return any(k != "$" and dfs(child, i + 1) for k, child in node.items())
            child = node.get(ch)
            return child is not None and dfs(child, i + 1)
        return dfs(self.root, 0)
''',
    tests=[
        [["WordDictionary", "addWord", "addWord", "addWord", "search", "search", "search", "search"],
         [[], ["bad"], ["dad"], ["mad"], ["pad"], ["bad"], [".ad"], ["b.."]]],
        [["WordDictionary", "search", "addWord", "search", "search"], [[], ["."], ["a"], ["."], [".."]]],
        [["WordDictionary", "addWord", "addWord", "search", "search", "search", "search"],
         [[], ["a"], ["ab"], ["a"], ["a."], ["ab"], [".b"]]],
        [["WordDictionary", "addWord", "search", "search", "search"], [[], ["abc"], ["ab"], ["abcd"], ["..."]]],
        [["WordDictionary", "addWord", "addWord", "search", "search"], [[], ["at"], ["and"], ["a.d."], ["an."]]],
        [["WordDictionary", "addWord", "addWord", "search", "search", "search"],
         [[], ["xyzzy"], ["xyz"], ["x...y"], ["xy..."], ["....."]]],
        [["WordDictionary", "addWord", "search", "search"], [[], ["a" * 25], ["." * 25], ["." * 24]]],
        [["WordDictionary", "addWord", "addWord", "search"], [[], ["ba"], ["ab"], ["a."]]],
        [_wd_ops, _wd_args],
    ],
    examples=1,
    wrong_solutions=[
        '''class WordDictionary:
    # treats "." as a literal character
    def __init__(self):
        self.words = set()

    def addWord(self, word):
        self.words.add(word)

    def search(self, word):
        return word in self.words
''',
        '''class WordDictionary:
    # prefix match instead of whole-word match
    def __init__(self):
        self.words = []

    def addWord(self, word):
        self.words.append(word)

    def search(self, word):
        for w in self.words:
            if len(w) >= len(word) and all(p == "." or p == c for p, c in zip(word, w)):
                return True
        return False
''',
    ],
    guide=dict(
        prereqs="*Implement Trie*; DFS/backtracking — lesson *Wildcards and trie-guided grid search*.",
        intuition="Without wildcards this is a normal trie lookup. A `.` means 'try every child here', which turns the single path walk into a DFS that branches only at the dots.",
        hints=["Store words in a trie with an end marker.",
               "Search recursively with `(node, index)`.",
               "On `.`, return True if *any* child succeeds for `index + 1`; at the end of the pattern, check the end marker."],
        brute_force="Keep a list of words and compare the pattern against each word of the same length: O(N·L) per search. Bucketing words by length helps but stays linear in N.",
        approach="Example: trie has b-a-d, d-a-d, m-a-d. `.ad`: branch into b, d, m; under b, `a` then `d` with end marker → True immediately. `pad`: root has no `p` child → False.",
        complexity="`addWord` O(L). `search` O(L) without dots; with d dots, worst case O(26^d · L) — with LeetCode's 2-dot limit that is O(26² · L).",
        pitfalls="- Accepting a match at a node without the end marker (prefixes are not words).\n- Iterating over the end-marker key as if it were a child (the reference skips `$`).",
        follow_up="Support `*` (any sequence) — becomes DP/backtracking on the trie, similar to wildcard matching (44).",
    ),
),
# ============================================================================================
dict(
    id="word-search-ii",
    title="Word Search II",
    difficulty="Hard",
    pattern="Tries — Backtracking on a Grid",
    leetcode="https://leetcode.com/problems/word-search-ii/",
    neetcode="https://neetcode.io/problems/search-for-word-ii",
    entry="findWords",
    compare="unordered",
    description=r"""
Given an `m x n` grid of lowercase letters and a list of distinct `words`, return every word that can be
traced in the grid. A word is traced by starting on some cell and moving to **horizontally or vertically
adjacent** cells, one letter per cell, never reusing a cell within the same word. Each found word is
reported once; the order of the answer does not matter.

**Constraints**

- `1 <= m, n <= 12`, `1 <= len(words) <= 3 * 10^4`, `1 <= len(words[i]) <= 10`, all words distinct.

**Arguments:** `board` (list of lists of single characters) and `words` (list of strings). The judge
compares your result as an unordered list.

**Example 1:** `board = [["o","a","a","n"],["e","t","a","e"],["i","h","k","r"],["i","f","l","v"]]`,
`words = ["oath","pea","eat","rain"]` → `["eat","oath"]`

**Example 2:** `board = [["a","b"],["c","d"]], words = ["abcb"]` → `[]`
""",
    starter='''class Solution:
    def findWords(self, board: List[List[str]], words: List[str]) -> List[str]:
        pass
''',
    solution='''class Solution:
    def findWords(self, board, words):
        root = {}
        for w in words:
            node = root
            for ch in w:
                node = node.setdefault(ch, {})
            node["$"] = w
        rows, cols = len(board), len(board[0])
        found = []

        def dfs(r, c, parent):
            ch = board[r][c]
            node = parent[ch]
            word = node.pop("$", None)
            if word is not None:
                found.append(word)
            board[r][c] = "#"
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] in node:
                    dfs(nr, nc, node)
            board[r][c] = ch
            if not node:                 # prune exhausted branches
                parent.pop(ch)

        for r in range(rows):
            for c in range(cols):
                if board[r][c] in root:
                    dfs(r, c, root)
        return found
''',
    tests=[
        [[["o", "a", "a", "n"], ["e", "t", "a", "e"], ["i", "h", "k", "r"], ["i", "f", "l", "v"]], ["oath", "pea", "eat", "rain"]],
        [[["a", "b"], ["c", "d"]], ["abcb"]],
        [[["a"]], ["a"]],
        [[["a"]], ["b", "aa"]],
        [[["a", "a"]], ["aaa", "aa", "a"]],
        [[["a", "b"], ["c", "d"]], ["abdc", "acdb", "abcd", "ba", "dc", "db"]],
        [[["o", "a", "b", "n"], ["o", "t", "a", "e"], ["a", "h", "k", "r"], ["a", "f", "l", "v"]], ["oa", "oaa"]],
        [[["a", "b", "c"], ["a", "e", "d"], ["a", "f", "g"]], ["abcdefg", "gfedcbaaa", "eaabcdgfa", "befa", "dgc", "ade"]],
        [_board_a, _words_a],
        [_board_big, _words_big],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def findWords(self, board, words):
        # allows re-using the same cell
        rows, cols = len(board), len(board[0])
        def can(w, i, r, c):
            if board[r][c] != w[i]:
                return False
            if i == len(w) - 1:
                return True
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and can(w, i + 1, nr, nc):
                    return True
            return False
        return [w for w in words if any(can(w, 0, r, c) for r in range(rows) for c in range(cols))]
''',
        '''class Solution:
    def findWords(self, board, words):
        # only checks that all letters exist somewhere
        letters = {ch for row in board for ch in row}
        return [w for w in words if set(w) <= letters]
''',
    ],
    guide=dict(
        prereqs="*Implement Trie*; grid backtracking (Word Search I, LeetCode 79) — lesson *Wildcards and trie-guided grid search*.",
        intuition="Running a separate grid search per word repeats the same work for shared prefixes. Put all the words into a trie and run **one** backtracking search from every cell, walking the trie in parallel with the grid. The moment the current path is not a prefix of any word, stop.",
        hints=["Build a trie of all words; store the complete word at its end node.",
               "DFS from each cell with the trie node for the path so far; only step to a neighbour whose letter is a child of the current trie node. Mark cells as visited by overwriting them temporarily.",
               "Optimisations: remove the word from the trie once found (avoids duplicates), and delete trie nodes that become empty so later searches skip dead branches."],
        brute_force="For each word, run Word Search I (DFS from every cell): O(W · m·n · 4·3^(L-1)). With 3·10^4 words this times out.",
        approach="""Example 1: trie holds oath, pea, eat, rain. From the `o` at (0,0): o → a (0,1) → t (1,1) → h (2,1) → word `oath` found. From `e` at (1,0): no child `e→...` path continues in the board for `pea`; from (1,3) `e` → a (1,2) → t (1,1) → `eat`. `rain` fails because no `r` neighbour leads to `a`.

Pruning: after `oath` is found its end marker is removed; nodes left empty are popped from their parents, so the trie shrinks as the search proceeds.""",
        complexity="Time O(m·n · 4·3^(L-1)) in the worst case (L ≤ 10 is the longest word) — but in practice the trie prunes almost every path. Space O(total letters in words) for the trie plus O(L) recursion.",
        pitfalls="- Reporting a word twice when it can be traced along two paths (remove it from the trie on first find, or use a set).\n- Forgetting to restore the cell after backtracking.\n- Checking bounds/visited after indexing the board.",
        follow_up="Boggle solvers; Concatenated Words (472) and Word Break II also combine a trie with search.",
    ),
),
]
