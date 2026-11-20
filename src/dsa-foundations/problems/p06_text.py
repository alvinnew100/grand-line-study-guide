import random as _r

_r.seed(53)


def _rs(n, alphabet):
    return "".join(_r.choice(alphabet) for _ in range(n))


def _trie_ops(n, seed):
    rnd = _r.Random(seed)
    words = ["".join(rnd.choice("abc") for _ in range(rnd.randint(1, 6))) for _ in range(40)]
    ops, args = ["Trie"], [[]]
    for _ in range(n):
        x = rnd.random()
        w = rnd.choice(words)
        if x < 0.4:
            ops.append("insert"); args.append([w])
        elif x < 0.6:
            ops.append("search"); args.append([w])
        elif x < 0.8:
            ops.append("starts_with"); args.append([w[:rnd.randint(1, len(w))]])
        else:
            ops.append("count_prefix"); args.append([w[:rnd.randint(0, len(w))]])
    return [ops, args]


PROBLEMS = [
dict(
    id="dsaf-kmp-failure",
    title="KMP Failure Function",
    difficulty="Medium",
    pattern="Text Processing",
    entry="failure_function",
    description=r"""
Compute the **Knuth-Morris-Pratt failure function** of a pattern `P` (Goodrich ch. 13.2.3).

Return a list `fail` of length `len(P)` where `fail[k]` is the length of the longest **proper** prefix
of `P[0..k]` that is also a suffix of `P[0..k]`. ("Proper" means shorter than the whole string, so
`fail[0] = 0`.)

Must run in $O(m)$ — the last tests use patterns of length 20,000 (hidden) for which the naive
$O(m^2)$ / $O(m^3)$ definitions are far too slow.

**Example:** `P = "amalgamation"` → `[0, 0, 1, 0, 0, 1, 2, 3, 0, 0, 0, 0]`

**Example:** `P = "abacab"` → `[0, 0, 1, 0, 1, 2]`
""",
    starter='''def failure_function(P):
    pass
''',
    solution='''def failure_function(P):
    m = len(P)
    fail = [0] * m
    j, k = 1, 0
    while j < m:
        if P[j] == P[k]:
            fail[j] = k + 1
            j += 1
            k += 1
        elif k > 0:
            k = fail[k - 1]
        else:
            j += 1
    return fail
''',
    tests=[
        ["amalgamation"],
        ["abacab"],
        [""],
        ["a"],
        ["aaaaa"],
        ["abcabcabc"],
        ["aabaaab"],
        ["abcdef"],
        ["abababca"],
        ["aaabaaaab"],
        ["ab" * 10000],
        ["a" * 19999 + "b"],
        [_rs(5000, "ab")],
    ],
    examples=2,
    wrong_solutions=[
        '''def failure_function(P):
    m = len(P)
    fail = [0] * m
    k = 0
    for j in range(1, m):
        if P[j] == P[k]:
            k += 1
        else:
            k = 0
        fail[j] = k
    return fail
''',
        '''def failure_function(P):
    m = len(P)
    fail = [0] * m
    for j in range(1, m):
        k = fail[j - 1]
        if P[j] == P[k]:
            fail[j] = k + 1
        elif k > 0 and P[j] == P[fail[k - 1]]:
            fail[j] = fail[k - 1] + 1
    return fail
''',
    ],
    guide=dict(
        prereqs="Lesson *Pattern matching: brute force, Boyer-Moore, KMP*.",
        intuition="Slide the pattern against itself. If the current overlap of length k can be extended by one matching character, fail[j] = k + 1. If not, the next-best overlap to try is the overlap of the overlap: fail[k - 1].",
        hints=["Keep j (position being computed) and k (length of the current matching prefix).",
               "Match: fail[j] = k + 1, advance both.",
               "Mismatch with k > 0: k = fail[k - 1] and retry the same j. Mismatch with k == 0: fail[j] stays 0, advance j."],
        brute_force="For each k, try every proper prefix length from longest to shortest and compare slices: O(m^2) checks of O(m) each — O(m^3), or O(m^2) with care.",
        approach="""
Dry run on `aabaaab`:
- j=1: 'a'=='a' → fail[1]=1 (k=1)
- j=2: 'b' vs P[1]='a' ✗ → k=fail[0]=0; 'b' vs 'a' ✗ → fail[2]=0
- j=3: 'a'=='a' → 1; j=4: 'a'==P[1] → 2; j=5: 'a' vs P[2]='b' ✗ → k=fail[1]=1; 'a'==P[1] → fail[5]=2
- j=6: 'b'==P[2] → fail[6]=3

Result `[0,1,0,1,2,2,3]`.
""",
        complexity="O(m) time: each iteration increases j or the shift j - k, both bounded by m. O(m) space.",
        pitfalls="Resetting k to 0 on a mismatch (first wrong solution) misses shorter borders — it fails on `aabaaab`. Using fail[k] instead of fail[k - 1]. Forgetting the empty pattern.",
        follow_up="The smallest period of P is m - fail[m - 1]. Use the table to search a text in O(n + m) (next exercise).",
    ),
),
dict(
    id="dsaf-kmp-search",
    title="KMP Search: All Occurrences",
    difficulty="Medium",
    pattern="Text Processing",
    entry="find_all",
    description=r"""
Return the list of **all** starting indices (in increasing order) at which pattern `P` occurs in text
`T`, including **overlapping** occurrences. Use the Knuth-Morris-Pratt algorithm
(Goodrich ch. 13.2.3) so that the running time is $O(n + m)$ — do not use `str.find`, `in`, slicing
comparisons or regular expressions.

`P` is non-empty.

**Example:** `T = "abacaabaccabacabaabb", P = "abacab"` → `[10]`

**Example:** `T = "aaaaa", P = "aa"` → `[0, 1, 2, 3]`
""",
    starter='''def find_all(T, P):
    pass
''',
    solution='''def find_all(T, P):
    m = len(P)
    fail = [0] * m
    k = 0
    for j in range(1, m):
        while k > 0 and P[j] != P[k]:
            k = fail[k - 1]
        if P[j] == P[k]:
            k += 1
        fail[j] = k
    out = []
    k = 0
    for j, c in enumerate(T):
        while k > 0 and c != P[k]:
            k = fail[k - 1]
        if c == P[k]:
            k += 1
        if k == m:
            out.append(j - m + 1)
            k = fail[k - 1]
    return out
''',
    tests=[
        ["abacaabaccabacabaabb", "abacab"],
        ["aaaaa", "aa"],
        ["", "a"],
        ["abc", "abcd"],
        ["abc", "abc"],
        ["abababab", "abab"],
        ["mississippi", "issi"],
        ["mississippi", "x"],
        ["aabaaabaaab", "aab"],
        ["a" * 6000 + "b", "a" * 300 + "b"],
        ["ab" * 3000, "abab"],
        [_rs(20000, "ab"), "abba"],
    ],
    examples=2,
    wrong_solutions=[
        '''def find_all(T, P):
    m = len(P)
    fail = [0] * m
    k = 0
    for j in range(1, m):
        while k > 0 and P[j] != P[k]:
            k = fail[k - 1]
        if P[j] == P[k]:
            k += 1
        fail[j] = k
    out = []
    k = 0
    for j, c in enumerate(T):
        while k > 0 and c != P[k]:
            k = fail[k - 1]
        if c == P[k]:
            k += 1
        if k == m:
            out.append(j - m + 1)
            k = 0
    return out
''',
        '''def find_all(T, P):
    out, i = [], 0
    while i + len(P) <= len(T):
        k = 0
        while k < len(P) and T[i + k] == P[k]:
            k += 1
        if k == len(P):
            out.append(i)
            i += len(P)
        else:
            i += 1
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Pattern matching* and the failure-function exercise.",
        intuition="Scan the text once, maintaining k = how many pattern characters currently match. On a mismatch, do not move back in the text: shrink k to the next-longest border via the failure function and try again.",
        hints=["First compute the failure function of P.",
               "For each text character c: while k > 0 and c != P[k]: k = fail[k-1]; if c == P[k]: k += 1.",
               "On a full match (k == m) record j - m + 1 and continue with k = fail[m-1] so overlapping matches are found."],
        brute_force="Check every alignment: O(nm). On `a...ab` texts with `a...ab` patterns this is millions of comparisons.",
        approach="""
Two phases: build `fail` (O(m)), then scan T (O(n)).

Trace T = `aaaaa`, P = `aa` (fail = [0,1]): j=0 → k=1; j=1 → k=2 → match at 0, k=fail[1]=1; j=2 → k=2 → match at 1; ... → `[0,1,2,3]`.
""",
        complexity="O(n + m) time, O(m) extra space (plus the output).",
        pitfalls="Resetting k = 0 after a match loses overlapping matches (first wrong solution). Jumping i by len(P) after a match (second). Indexing P[k] when k == m — reduce k right after recording the match.",
        follow_up="Count occurrences in a stream without storing the text; Rabin-Karp rolling hash as an alternative; Aho-Corasick for many patterns at once.",
    ),
),
dict(
    id="dsaf-lcs",
    title="Longest Common Subsequence (with the String)",
    difficulty="Medium",
    pattern="Text Processing",
    entry="lcs",
    checker='''def check(args, got, expected):
    X, Y = args
    if not isinstance(got, str) or len(got) != len(expected):
        return False
    def is_subseq(s, t):
        it = iter(t)
        return all(c in it for c in s)
    return is_subseq(got, X) and is_subseq(got, Y)
''',
    description=r"""
Given strings `X` and `Y`, return **a longest common subsequence** — a longest string that can be
obtained from both `X` and `Y` by deleting zero or more characters (Goodrich ch. 13.3.2).

Fill the dynamic-programming table `L[j][k]` = LCS length of `X[:j]` and `Y[:k]`, then trace back
from `L[n][m]` to build the string. If several longest common subsequences exist, **any one** is
accepted (the grader checks that your answer is a common subsequence of maximum length).

**Example:** `X = "GTTCCTAATA", Y = "CGATAATTGAGA"` → e.g. `"GTTTAA"` (length 6)

**Example:** `X = "abc", Y = "def"` → `""`
""",
    starter='''def lcs(X, Y):
    pass
''',
    solution='''def lcs(X, Y):
    n, m = len(X), len(Y)
    L = [[0] * (m + 1) for _ in range(n + 1)]
    for j in range(n):
        row, nxt = L[j], L[j + 1]
        xj = X[j]
        for k in range(m):
            if xj == Y[k]:
                nxt[k + 1] = row[k] + 1
            else:
                a, b = row[k + 1], nxt[k]
                nxt[k + 1] = a if a >= b else b
    out = []
    j, k = n, m
    while L[j][k] > 0:
        if X[j - 1] == Y[k - 1]:
            out.append(X[j - 1])
            j -= 1
            k -= 1
        elif L[j - 1][k] >= L[j][k - 1]:
            j -= 1
        else:
            k -= 1
    return "".join(reversed(out))
''',
    tests=[
        ["GTTCCTAATA", "CGATAATTGAGA"],
        ["abc", "def"],
        ["", "abc"],
        ["abc", ""],
        ["abc", "abc"],
        ["ABCB", "BDCAB"],
        ["aaaa", "aa"],
        ["abcde", "ace"],
        ["XMJYAUZ", "MZJAWXU"],
        ["skullandbones", "lullabybabies"],
        [_rs(60, "ACGT"), _rs(70, "ACGT")],
        [_rs(300, "ab"), _rs(280, "abc")],
        [_rs(400, "ACGT"), _rs(400, "ACGT")],
    ],
    examples=2,
    wrong_solutions=[
        '''def lcs(X, Y):
    best = ""
    for i in range(len(X)):
        for j in range(i + 1, len(X) + 1):
            if X[i:j] in Y and j - i > len(best):
                best = X[i:j]
    return best
''',
        '''def lcs(X, Y):
    out, k = [], 0
    for c in X:
        p = Y.find(c, k)
        if p != -1:
            out.append(c)
            k = p + 1
    return "".join(out)
''',
    ],
    guide=dict(
        prereqs="Lesson *Dynamic programming: matrix chain and LCS*.",
        intuition="Look at the last characters of the two prefixes. If they match, that character can be the last character of an LCS (diagonal + 1). If not, one of them is useless: take the better of dropping either (max of up and left).",
        hints=["Use an (n+1) x (m+1) table with a zero row and column for empty prefixes.",
               "Match: L[j+1][k+1] = L[j][k] + 1; otherwise max(L[j][k+1], L[j+1][k]).",
               "Trace back from L[n][m]: on a match record the character and go diagonally; otherwise step toward the larger neighbour; reverse at the end."],
        brute_force="Enumerate all 2^n subsequences of X and test each against Y: O(2^n m). The greedy 'take the next matching character' (second wrong solution) is fast but not optimal.",
        approach="""
1. Fill the table row by row: O(nm).
2. Walk back from (n, m) until the entry is 0: O(n + m).

For `ABCB` / `BDCAB` the table's bottom-right entry is 3 and the walk yields `BCB`.
""",
        complexity="O(nm) time and space. (Length only: O(min(n, m)) space with two rows.)",
        pitfalls="Confusing subsequence with substring (first wrong solution returns the longest common *substring*); greedy matching; forgetting to reverse the collected characters; `[[0]*(m+1)]*(n+1)` aliasing all rows.",
        follow_up="Edit distance; shortest common supersequence (length n + m - LCS); Hirschberg's linear-space reconstruction.",
    ),
),
dict(
    id="dsaf-matrix-chain",
    title="Matrix Chain-Product",
    difficulty="Medium",
    pattern="Text Processing",
    entry="matrix_chain",
    description=r"""
You must multiply a chain of matrices $A_0 A_1 \cdots A_{n-1}$ where $A_i$ has dimensions
`d[i] × d[i+1]` (so `d` has `n + 1` entries). Multiplying a $p \times q$ matrix by a $q \times r$
matrix costs $p \cdot q \cdot r$ scalar multiplications.

Return the **minimum total number of scalar multiplications** over all ways to parenthesise the
product (Goodrich ch. 13.3.1). A chain of zero or one matrix costs 0.

**Example:** `d = [2, 10, 50, 20]` → `3000` — $(A_0 A_1) A_2$ costs $2\cdot10\cdot50 + 2\cdot50\cdot20$

**Example:** `d = [30, 35, 15, 5, 10, 20, 25]` → `15125`
""",
    starter='''def matrix_chain(d):
    pass
''',
    solution='''def matrix_chain(d):
    n = len(d) - 1
    if n < 2:
        return 0
    N = [[0] * n for _ in range(n)]
    for b in range(1, n):
        for i in range(n - b):
            j = i + b
            N[i][j] = min(N[i][k] + N[k + 1][j] + d[i] * d[k + 1] * d[j + 1] for k in range(i, j))
    return N[0][n - 1]
''',
    tests=[
        [[2, 10, 50, 20]],
        [[30, 35, 15, 5, 10, 20, 25]],
        [[5, 7]],
        [[]],
        [[9]],
        [[10, 20, 30]],
        [[10, 20, 30, 40, 30]],
        [[40, 20, 30, 10, 30]],
        [[1, 2, 3, 4, 5, 6]],
        [[5, 4, 3, 2, 1]],
        [[3, 3, 3, 3, 3, 3]],
        [[10, 1, 10, 1, 10, 1, 10]],
        [[_r.randint(1, 50) for _ in range(40)]],
        [[_r.randint(1, 100) for _ in range(90)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def matrix_chain(d):
    d = list(d)
    total = 0
    while len(d) > 2:
        best = min(range(1, len(d) - 1), key=lambda k: d[k - 1] * d[k] * d[k + 1])
        total += d[best - 1] * d[best] * d[best + 1]
        d.pop(best)
    return total
''',
        '''def matrix_chain(d):
    total = 0
    for k in range(1, len(d) - 1):
        total += d[0] * d[k] * d[k + 1]
    return total
''',
    ],
    guide=dict(
        prereqs="Lesson *Dynamic programming: matrix chain and LCS*.",
        intuition="Whatever the parenthesisation, there is a LAST multiplication that joins (A_i..A_k) with (A_{k+1}..A_j). Try every split point k, with each side solved optimally.",
        hints=["State: N[i][j] = minimum cost to compute A_i ... A_j; N[i][i] = 0.",
               "N[i][j] = min over k in [i, j) of N[i][k] + N[k+1][j] + d[i]*d[k+1]*d[j+1].",
               "Fill by increasing chain length b = j - i so the needed entries already exist."],
        brute_force="Recursively try all parenthesisations: Catalan-number many — exponential. The greedy 'do the cheapest multiplication first' (first wrong solution) is not optimal in general; left-to-right evaluation (second) is rarely optimal.",
        approach="""
For `d = [2, 10, 50, 20]`: N[0][1] = 2·10·50 = 1000, N[1][2] = 10·50·20 = 10000,
N[0][2] = min(k=0: 0 + 10000 + 2·10·20 = 10400, k=1: 1000 + 0 + 2·50·20 = 3000) = 3000.
""",
        complexity="O(n^3) time (O(n^2) intervals × O(n) split points), O(n^2) space.",
        pitfalls="Index slip in the dimension product (it is d[i] * d[k+1] * d[j+1]); filling rows in the wrong order; treating fewer than two matrices as an error instead of cost 0.",
        follow_up="Also return the optimal parenthesisation by storing the best k for each (i, j).",
    ),
),
dict(
    id="dsaf-huffman-cost",
    title="Huffman Encoded Length",
    difficulty="Medium",
    pattern="Text Processing",
    entry="huffman_bits",
    description=r"""
Return the number of bits needed to encode `text` with an optimal **Huffman code**
(Goodrich ch. 13.4): the sum over all distinct characters of `frequency × codeword length`.

Use the greedy algorithm with a priority queue: repeatedly remove the two least frequent trees and
merge them. (Different tie-breaking gives different codes but always the same total length.)

Conventions: the empty string needs `0` bits; a text with a single distinct character uses a 1-bit
code, i.e. `len(text)` bits.

**Example:** `"a fast runner need never be afraid of the dark"` → `165`

**Example:** `"aaaa"` → `4`;  `"abc"` → `5` (codes of lengths 1, 2, 2)
""",
    starter='''import heapq


def huffman_bits(text):
    pass
''',
    solution='''import heapq
from collections import Counter


def huffman_bits(text):
    freq = Counter(text)
    if not freq:
        return 0
    if len(freq) == 1:
        return len(text)
    heap = list(freq.values())
    heapq.heapify(heap)
    total = 0
    while len(heap) > 1:
        a = heapq.heappop(heap)
        b = heapq.heappop(heap)
        total += a + b
        heapq.heappush(heap, a + b)
    return total
''',
    tests=[
        ["a fast runner need never be afraid of the dark"],
        ["aaaa"],
        ["abc"],
        [""],
        ["z"],
        ["ab"],
        ["aab"],
        ["abcdefgh"],
        ["aaaaaaaabbbbccd"],
        ["mississippi river"],
        ["a" * 1 + "b" * 1 + "c" * 2 + "d" * 3 + "e" * 5 + "f" * 8 + "g" * 13 + "h" * 21],
        [_rs(5000, "abcdefghij")],
        [_rs(3000, "aaaaaaaabbbbccd ")],
    ],
    examples=2,
    wrong_solutions=[
        '''import math
from collections import Counter
def huffman_bits(text):
    freq = Counter(text)
    if not freq:
        return 0
    bits = max(1, math.ceil(math.log2(len(freq))))
    return bits * len(text)
''',
        '''from collections import Counter
def huffman_bits(text):
    freq = sorted(Counter(text).values(), reverse=True)
    if not freq:
        return 0
    if len(freq) == 1:
        return len(text)
    total = 0
    for depth, f in enumerate(freq, start=1):
        total += f * min(depth, len(freq) - 1)
    return total
''',
    ],
    guide=dict(
        prereqs="Lesson *Greedy compression and tries*; heaps (`heapq`).",
        intuition="Every merge of two trees pushes all characters beneath them one level deeper — one more bit each. So the total encoded length is just the sum of the weights of all merged (internal) nodes; you never need to build the tree.",
        hints=["Count frequencies; heapify the list of frequencies.",
               "While more than one item: pop a and b, add a + b to the answer, push a + b.",
               "Handle zero and one distinct characters separately."],
        brute_force="A fixed-length code uses ceil(log2 d) bits per character (first wrong solution) — never better than Huffman and usually worse. Trying all prefix-code trees is exponential.",
        approach="""
Example `abc` (1,1,1): merge 1+1 = 2 (total 2), merge 1+2 = 3 (total 5). Codes have lengths 1, 2, 2 → 1 + 2 + 2 = 5 bits.

Example `aab` (2,1): one merge of weight 3 → 3 bits.
""",
        complexity="O(n + d log d): counting is O(n); d - 1 merges with O(log d) heap operations. Space O(d).",
        pitfalls="Single distinct character (the loop never runs → 0, but the convention is 1 bit per character); assuming codes follow sorted rank like a unary code (second wrong solution); pushing tuples that compare trees on ties when you do build the tree.",
        follow_up="Produce the actual code table and a decoder; prove optimality with the exchange argument.",
    ),
),
dict(
    id="dsaf-trie",
    title="Standard Trie with Prefix Counts",
    difficulty="Medium",
    pattern="Text Processing",
    kind="class",
    entry="Trie",
    description=r"""
Implement a **standard trie** over lowercase strings (Goodrich ch. 13.5.1).

- `insert(word)` — add `word` (inserting the same word twice stores it twice).
- `search(word)` → `True` iff `word` was inserted as a complete word.
- `starts_with(prefix)` → `True` iff some inserted word has this prefix.
- `count_prefix(prefix)` → the number of inserted words (counting duplicates) that start with
  `prefix`. The empty prefix counts all words.

Each operation must take time proportional to the length of its argument, independent of how many
words are stored.

**Example:** `["Trie","insert","insert","insert","search","search","starts_with","count_prefix","count_prefix"]`,
`[[],["bear"],["bell"],["bid"],["bell"],["be"],["be"],["be"],["b"]]` →
`[null,null,null,null,true,false,true,2,3]`
""",
    starter='''class Trie:
    def __init__(self):
        pass

    def insert(self, word):
        pass

    def search(self, word):
        pass

    def starts_with(self, prefix):
        pass

    def count_prefix(self, prefix):
        pass
''',
    solution='''class _Node:
    __slots__ = "children", "words", "passing"
    def __init__(self):
        self.children = {}
        self.words = 0
        self.passing = 0


class Trie:
    def __init__(self):
        self._root = _Node()

    def insert(self, word):
        node = self._root
        node.passing += 1
        for ch in word:
            nxt = node.children.get(ch)
            if nxt is None:
                nxt = node.children[ch] = _Node()
            node = nxt
            node.passing += 1
        node.words += 1

    def _walk(self, s):
        node = self._root
        for ch in s:
            node = node.children.get(ch)
            if node is None:
                return None
        return node

    def search(self, word):
        node = self._walk(word)
        return node is not None and node.words > 0

    def starts_with(self, prefix):
        return self._walk(prefix) is not None

    def count_prefix(self, prefix):
        node = self._walk(prefix)
        return node.passing if node is not None else 0
''',
    tests=[
        [["Trie", "insert", "insert", "insert", "search", "search", "starts_with", "count_prefix", "count_prefix"],
         [[], ["bear"], ["bell"], ["bid"], ["bell"], ["be"], ["be"], ["be"], ["b"]]],
        [["Trie", "search", "starts_with", "count_prefix", "count_prefix"], [[], ["a"], ["a"], ["a"], [""]]],
        [["Trie", "insert", "insert", "search", "search", "count_prefix", "count_prefix"],
         [[], ["be"], ["bear"], ["be"], ["bea"], ["be"], ["bear"]]],
        [["Trie", "insert", "insert", "insert", "count_prefix", "count_prefix", "search"],
         [[], ["a"], ["a"], ["a"], ["a"], [""], ["a"]]],
        [["Trie", "insert", "starts_with", "starts_with", "starts_with", "search"],
         [[], ["stock"], ["sto"], ["stop"], ["stock"], ["stoc"]]],
        [["Trie"] + ["insert"] * 8 + ["count_prefix"] * 5 + ["search", "starts_with"],
         [[]] + [[w] for w in ["bear", "bell", "bid", "bull", "buy", "sell", "stock", "stop"]]
         + [["b"], ["bu"], ["s"], ["st"], ["x"]] + [["sel"], ["sel"]]],
        _trie_ops(150, 1),
        _trie_ops(800, 2),
        _trie_ops(3000, 3),
    ],
    examples=2,
    wrong_solutions=[
        '''class Trie:
    def __init__(self):
        self.root = {}
        self.n = 0
    def insert(self, word):
        node = self.root
        self.n += 1
        for ch in word:
            node = node.setdefault(ch, {})
    def _walk(self, s):
        node = self.root
        for ch in s:
            if ch not in node: return None
            node = node[ch]
        return node
    def search(self, word):
        return self._walk(word) is not None
    def starts_with(self, prefix):
        return self._walk(prefix) is not None
    def count_prefix(self, prefix):
        node = self._walk(prefix)
        if node is None: return 0
        def leaves(n):
            return 1 if not n else sum(leaves(c) for c in n.values())
        return leaves(node)
''',
        '''class Trie:
    def __init__(self):
        self.words = set()
    def insert(self, word):
        self.words.add(word)
    def search(self, word):
        return word in self.words
    def starts_with(self, prefix):
        return any(w.startswith(prefix) for w in self.words)
    def count_prefix(self, prefix):
        return sum(w.startswith(prefix) for w in self.words)
''',
    ],
    guide=dict(
        prereqs="Lesson *Greedy compression and tries* (standard tries).",
        intuition="Each node represents a prefix. Store in every node how many inserted words pass through it (for count_prefix) and how many end exactly there (the end-of-word marker for search).",
        hints=["A node holds a dict of children plus two counters: `passing` and `words`.",
               "insert: increment `passing` on the root and on each node along the path; increment `words` at the last node.",
               "search requires words > 0 at the final node; starts_with only requires that the path exists."],
        brute_force="A list or set of words: search is O(1) with a set but prefix queries scan every word — O(total length).",
        approach="""
Write one helper `_walk(s)` that follows s from the root and returns the node or None. Then:
- search → node exists and node.words > 0
- starts_with → node exists
- count_prefix → node.passing (0 if missing)

After inserting bear, bell, bid: node 'b' has passing 3, node 'be' has passing 2 and words 0 → search('be') is False but starts_with('be') is True.
""",
        complexity="O(m) per operation for an argument of length m (dict lookups are O(1) expected). Space O(total characters inserted) in the worst case.",
        pitfalls="No end-of-word marker (first wrong solution says 'be' is a word because 'bear' exists, and miscounts duplicates); counting distinct words instead of insertions (second); forgetting to count at the root, which makes count_prefix('') wrong.",
        follow_up="Add delete(word) (decrement counters, prune empty nodes) and autocomplete(prefix, k). Compress single-child chains to get a radix tree.",
    ),
),
]
