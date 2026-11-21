"""Extra practice for the analysis, recursion, stacks, linked-list and tree modules."""
import random as _r


def _mutate(src, old, new):
    """Derive a wrong solution from a reference one by replacing one exact snippet."""
    assert old in src, old
    return src.replace(old, new, 1)


# ---------------------------------------------------------------- generators

def _three_lists(seed, n):
    rnd = _r.Random(seed)
    span = 3 * n
    return [[x - span // 2 for x in rnd.sample(range(span), n)] for _ in range(3)]


def _rand_expr(rnd, depth):
    if depth == 0 or rnd.random() < 0.2:
        return str(rnd.randint(0, 999)) if rnd.random() < 0.75 else rnd.choice("abcxyz")
    s = _rand_expr(rnd, depth - 1) + rnd.choice(["+", "-", "*", "/", "^", " + ", " - ", "*"]) + _rand_expr(rnd, depth - 1)
    return "(" + s + ")" if rnd.random() < 0.3 else s


def _long_expr(seed, parts):
    rnd = _r.Random(seed)
    pieces = [_rand_expr(rnd, 4) for _ in range(parts)]
    out = pieces[0]
    for p in pieces[1:]:
        out += rnd.choice(["+", "-", "*", "/", "^"]) + p
    return out


def _pos_ops(n, seed):
    rnd = _r.Random(seed)
    ops, args = ["PositionalList"], [[]]
    live, live_set, issued, nxt = [], set(), [], 1

    def pick():
        r = rnd.random()
        if live and r < 0.85:
            return rnd.choice(live)
        if issued and r < 0.95:
            return rnd.choice(issued)
        return rnd.choice([0, -2, nxt + 7])

    def issue():
        nonlocal nxt
        live.append(nxt)
        live_set.add(nxt)
        issued.append(nxt)
        nxt += 1

    for i in range(n):
        x = rnd.random()
        e = "e%d" % i
        if x < 0.14 or not live:
            ops.append(rnd.choice(["add_first", "add_last"])); args.append([e]); issue()
        elif x < 0.32:
            h = pick()
            ops.append(rnd.choice(["add_before", "add_after"])); args.append([h, e])
            if h in live_set:
                issue()
        elif x < 0.47:
            h = pick()
            ops.append("delete"); args.append([h])
            if h in live_set:
                live_set.remove(h)
                live.remove(h)
        elif x < 0.57:
            ops.append("move_to_front"); args.append([pick()])
        elif x < 0.72:
            ops.append(rnd.choice(["element", "before", "after"])); args.append([pick()])
        elif x < 0.82:
            ops.append("replace"); args.append([pick(), "r%d" % i])
        else:
            ops.append(rnd.choice(["first", "last", "size"])); args.append([])
        if i % 1500 == 1499:
            ops.append("to_list"); args.append([])
    ops.append("to_list"); args.append([])
    return [ops, args]


def _rand_parent_tree(n, seed, window):
    """Random tree as (parent, labels); each node hangs below one of the `window` nodes created before it."""
    rnd = _r.Random(seed)
    perm = list(range(n))
    rnd.shuffle(perm)
    parent = [0] * n
    parent[perm[0]] = -1
    for i in range(1, n):
        parent[perm[i]] = perm[rnd.randrange(max(0, i - window), i)]
    labels = [rnd.choice("abcdefgh") + rnd.choice("xyz0123") for _ in range(n)]
    return [parent, labels]


def _caterpillar(spine, seed):
    rnd = _r.Random(seed)
    parent, labels = [-1], ["s"]
    for i in range(1, spine):
        parent.append(i - 1)
        labels.append("s")
    for _ in range(spine // 2):
        parent.append(rnd.randrange(spine))
        labels.append("L")
    return [parent, labels]


# ---------------------------------------------------------------- reference solutions used for mutations

_POS_SOL = '''class _Node:
    __slots__ = "elem", "prev", "next", "handle"

    def __init__(self, elem, prev, next, handle):
        self.elem, self.prev, self.next, self.handle = elem, prev, next, handle


class PositionalList:
    def __init__(self):
        self._header = _Node(None, None, None, None)
        self._trailer = _Node(None, None, None, None)
        self._header.next = self._trailer
        self._trailer.prev = self._header
        self._nodes = {}          # handle -> node, only for live elements
        self._next_handle = 1

    def _insert_between(self, e, a, b):
        node = _Node(e, a, b, self._next_handle)
        a.next = node
        b.prev = node
        self._nodes[node.handle] = node
        self._next_handle += 1
        return node.handle

    def _unlink(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _handle_of(self, node):
        if node is self._header or node is self._trailer:
            return None
        return node.handle

    def add_first(self, e):
        return self._insert_between(e, self._header, self._header.next)

    def add_last(self, e):
        return self._insert_between(e, self._trailer.prev, self._trailer)

    def add_before(self, h, e):
        node = self._nodes.get(h)
        if node is None:
            return -1
        return self._insert_between(e, node.prev, node)

    def add_after(self, h, e):
        node = self._nodes.get(h)
        if node is None:
            return -1
        return self._insert_between(e, node, node.next)

    def first(self):
        return self._handle_of(self._header.next)

    def last(self):
        return self._handle_of(self._trailer.prev)

    def before(self, h):
        node = self._nodes.get(h)
        return -1 if node is None else self._handle_of(node.prev)

    def after(self, h):
        node = self._nodes.get(h)
        return -1 if node is None else self._handle_of(node.next)

    def element(self, h):
        node = self._nodes.get(h)
        return -1 if node is None else node.elem

    def replace(self, h, e):
        node = self._nodes.get(h)
        if node is None:
            return -1
        old, node.elem = node.elem, e
        return old

    def delete(self, h):
        node = self._nodes.pop(h, None)
        if node is None:
            return -1
        self._unlink(node)
        node.prev = node.next = None
        return node.elem

    def move_to_front(self, h):
        node = self._nodes.get(h)
        if node is None:
            return -1
        if self._header.next is not node:
            self._unlink(node)
            first = self._header.next
            node.prev, node.next = self._header, first
            self._header.next = node
            first.prev = node
        return None

    def size(self):
        return len(self._nodes)

    def to_list(self):
        out, walk = [], self._header.next
        while walk is not self._trailer:
            out.append(walk.elem)
            walk = walk.next
        return out
'''

_PAREN_SOL = '''def parenthesize(parent, labels):
    n = len(parent)
    children = [[] for _ in range(n)]
    root = -1
    for v, p in enumerate(parent):
        if p == -1:
            root = v
        else:
            children[p].append(v)      # v grows, so each child list stays sorted
    out = []
    stack = [(root, 0)]                # (node, index of the next child to visit)
    while stack:
        v, i = stack.pop()
        kids = children[v]
        if i == 0:                     # pre visit
            out.append(labels[v])
            if kids:
                out.append(" (")
        if i < len(kids):
            if i > 0:
                out.append(", ")       # between two children
            stack.append((v, i + 1))   # come back for the next child later
            stack.append((kids[i], 0))
        elif kids:
            out.append(")")            # post visit
    return "".join(out)
'''


PROBLEMS = [
# ---------------------------------------------------------------- analysis
dict(
    id="dsaf-three-way-common",
    title="Values Shared by Three Lists",
    difficulty="Easy",
    pattern="Algorithm Analysis",
    entry="common_to_all",
    description=r"""
You receive three lists of integers `A`, `B` and `C`. Inside any one list no value is repeated, but
the same value may turn up in two or all three lists. Return, in **increasing order**, every value
that occurs in **all three** lists. (Goodrich ch. 3.3.3 only asks whether such a value exists; here
you report them all.)

The triple loop that compares every `a`, `b` and `c` costs $O(n^3)$, and the refinement that only
looks at `C` when `a == b` is still $O(n^2)$. Aim for $O(n \log n)$ (sort, then walk three
indices) or expected $O(n)$ (hash sets): the hidden tests contain lists with thousands of values.

Lists may be empty and values may be negative.

**Example:** `A = [4, 9, 1, 7], B = [7, 3, 4, 8], C = [2, 4, 7, 5]` → `[4, 7]`

**Example:** `A = [1, 2], B = [2, 3], C = [3, 1]` → `[]` (each pair of lists shares a value, yet no
value is in all three)
""",
    starter='''def common_to_all(A, B, C):
    pass
''',
    solution='''def common_to_all(A, B, C):
    a, b, c = sorted(A), sorted(B), sorted(C)
    i = j = k = 0
    out = []
    while i < len(a) and j < len(b) and k < len(c):
        x, y, z = a[i], b[j], c[k]
        if x == y == z:
            out.append(x)
            i += 1
            j += 1
            k += 1
        else:
            top = max(x, y, z)
            if x < top:
                i += 1
            if y < top:
                j += 1
            if z < top:
                k += 1
    return out
''',
    tests=[
        [[4, 9, 1, 7], [7, 3, 4, 8], [2, 4, 7, 5]],
        [[1, 2], [2, 3], [3, 1]],
        [[], [1, 2], [1, 2]],
        [[], [], []],
        [[5], [5], [5]],
        [[-3, 0, 3], [3, -3], [0, -3, 3, 6]],
        [[30, 20, 10], [10, 30, 20], [20, 10, 30]],
        [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        [[8, 6, 4, 2], [2, 4, 6, 8], [1, 2, 3]],
        [list(range(0, 3000, 2)), list(range(2997, -1, -3)), list(range(0, 3000, 5))],
        _three_lists(31, 3000),
        _three_lists(32, 7000),
    ],
    examples=2,
    wrong_solutions=[
        '''def common_to_all(A, B, C):
    return sorted(set(A) & set(B))
''',
        '''def common_to_all(A, B, C):
    rest = set(B) & set(C)
    return [x for x in A if x in rest]
''',
    ],
    guide=dict(
        prereqs="Lesson *Analysing real code and proving it correct*, sections 4 (three-way set disjointness) and 5 (element uniqueness).",
        intuition="Sort the three lists and look at their front values. If all three agree, that value is common. If not, any front value smaller than the largest of the three cannot occur in the list holding that largest value (everything left there is at least as big), so it can be thrown away. Each comparison retires at least one value.",
        hints=["Would the question be easier if all three lists were sorted?",
               "Keep one index per sorted list. When the three current values are equal, record the value and advance all three indices.",
               "Otherwise advance every index whose current value is smaller than the largest of the three current values."],
        brute_force="Compare every triple `(a, b, c)`: $n^3$ tests. Looking at `C` only when `a == b` brings it down to $O(n^2)$, which is still tens of millions of steps for $n$ in the thousands. Writing `x in B and x in C` on lists hides the same quadratic cost.",
        approach="""
1. `a, b, c = sorted(A), sorted(B), sorted(C)` and `i = j = k = 0`.
2. While no index has run off its list: if `a[i] == b[j] == c[k]`, append it and advance all three; otherwise let `top` be the largest of the three and advance each index whose value is below `top`.

Dry run on the first example: `a = [1,4,7,9]`, `b = [3,4,7,8]`, `c = [2,4,5,7]`.

| fronts | action |
|---|---|
| 1, 3, 2 | top 3: advance `i` and `k` |
| 4, 3, 4 | top 4: advance `j` |
| 4, 4, 4 | record 4, advance all |
| 7, 7, 5 | top 7: advance `k` |
| 7, 7, 7 | record 7, advance all |
| 9, 8, end | `c` exhausted: stop |

Result `[4, 7]`. A shorter alternative is `sorted(set(A) & set(B) & set(C))`, expected $O(n)$ for the intersections plus the sort of the answers.
""",
        complexity="Sorting costs O(n log n). In the walk, every step advances at least one index and no index ever moves back, so there are at most 3n steps: the 'pointer only moves forward' argument of the lesson. Total O(n log n) time and O(n) space for the sorted copies. The hash-set version is expected O(n), plus O(k log k) to sort the k answers.",
        pitfalls="Intersecting only two of the lists; returning the values in the order they appear in `A` instead of increasing order; advancing the index of the LARGEST value (it may still match later values in the other lists); calling `x in list` inside a loop, which is a hidden linear scan.",
        follow_up="If values could repeat inside a list and each common value had to be reported as often as it occurs in all three, how would the walk change? For k lists, keep the k front values in a heap: O(N log k) for N values in total.",
    ),
),
dict(
    id="dsaf-loop-step-count",
    title="Count the Steps Without Running the Loops",
    difficulty="Medium",
    pattern="Algorithm Analysis",
    entry="count_steps",
    description=r"""
Four loop shapes from the lesson *Analysing real code and proving it correct* (section 8). In each
one, count how many times the statement marked `# <- count` runs:

```python
def shape_A(n):
    for i in range(n):
        j = 1
        while j < n:
            j *= 2            # <- count

def shape_B(n):
    for i in range(1, n + 1):
        for j in range(0, n, i):
            pass              # <- count

def shape_C(n):
    i = 1
    while i < n:
        for j in range(i):
            pass              # <- count
        i *= 2

def shape_D(n):
    j = 0
    for i in range(n):
        while j < n and j < 2 * i:
            j += 1            # <- count
```

Write `count_steps(shape, n)` that returns this count for `shape` in `"A"`, `"B"`, `"C"`, `"D"`.
Running the loops is far too slow: `n` can be up to $10^{14}$ for shapes A, C and D, and up to
$3 \cdot 10^5$ for shape B. Derive the counts with exact integer arithmetic.

**Example:** `shape = "A", n = 5` → `15` (each of the 5 outer rounds doubles `j` from 1 to 8: 3 steps)

**Example:** `shape = "B", n = 5` → `13` (5 + 3 + 2 + 2 + 1)
""",
    starter='''def count_steps(shape, n):
    pass
''',
    solution='''from math import isqrt


def count_steps(shape, n):
    if shape == "A":
        # the while loop runs ceil(log2 n) times for every i; (n - 1).bit_length() is that, exactly
        return n * (n - 1).bit_length()
    if shape == "B":
        # sum of ceil(n / i) = n + sum of floor((n - 1) / i); add the floors in O(sqrt n)
        m = n - 1
        if m == 0:
            return n
        r = isqrt(m)
        return n + 2 * sum(m // i for i in range(1, r + 1)) - r * r
    if shape == "C":
        # 1 + 2 + 4 + ... over the powers of two below n
        return (1 << (n - 1).bit_length()) - 1
    # shape D: j only moves forward and stops at min(n, 2(n - 1))
    return min(n, 2 * n - 2)
''',
    tests=[
        ["A", 5],
        ["B", 5],
        ["C", 5],
        ["D", 5],
        ["A", 1],
        ["B", 1],
        ["C", 1],
        ["D", 1],
        ["A", 2],
        ["D", 2],
        ["A", 2 ** 29],
        ["C", 2 ** 39],
        ["C", 2 ** 49 + 1],
        ["A", 10 ** 14],
        ["B", 1000],
        ["B", 299999],
        ["D", 10 ** 14],
    ],
    examples=2,
    wrong_solutions=[
        '''import math
def count_steps(shape, n):
    if shape == "A":
        return n * math.ceil(math.log(n, 2)) if n > 1 else 0
    if shape == "B":
        return sum(-(-n // i) for i in range(1, n + 1))
    if shape == "C":
        return 2 ** math.ceil(math.log(n, 2)) - 1 if n > 1 else 0
    return min(n, 2 * n - 2)
''',
        '''def count_steps(shape, n):
    if shape == "A":
        return n * (n - 1).bit_length()
    if shape == "B":
        return sum(n // i for i in range(1, n + 1))
    if shape == "C":
        return (1 << (n - 1).bit_length()) - 1
    return min(n, 2 * n - 2)
''',
        '''def count_steps(shape, n):
    if shape == "A":
        return n * (n - 1).bit_length()
    if shape == "B":
        return sum(-(-n // i) for i in range(1, n + 1))
    if shape == "C":
        return (1 << (n - 1).bit_length()) - 1
    return max(0, 2 * n - 2)
''',
    ],
    guide=dict(
        prereqs="Lesson *Analysing real code and proving it correct*, section 8 (loops that are not what they seem), plus the logarithm, ceiling and the geometric and harmonic sums from *Measuring algorithms and the seven functions*.",
        intuition="Never multiply loop sizes blindly. Write the cost of the inner loop as a formula in the outer variable, then add the formula up; or find a quantity that only grows and bound how far it can go. Shape A costs the same in every round; B's inner loop shrinks like n / i; C's inner loop doubles; D's pointer never moves back.",
        hints=["Shape A: how many doublings take 1 to n or beyond? That is ceil(log2 n), and `(n - 1).bit_length()` computes it exactly for n >= 1, with no floating point.",
               "Shape C: the inner loop runs 1, 2, 4, ... times for each power of two below n. A sum of powers of two 1 + 2 + ... + 2^(k-1) is 2^k - 1. Shape D: `j` ends at min(n, 2(n - 1)) and each step adds 1.",
               "Shape B: `range(0, n, i)` has ceil(n / i) elements. Summing them is fine for n = 3*10^5; for much bigger n, note that floor(m / i) takes only about 2*sqrt(m) different values."],
        brute_force="Run the loops with a counter: shape A alone needs about n log n steps, which is hopeless for n = 10^14. Floating-point shortcuts such as `math.ceil(math.log(n, 2))` look right but are wrong for some exact powers of two (`math.log(2**29, 2)` is 29.000000000000004).",
        approach="""
- A: `n * (n - 1).bit_length()`.
- B: `sum(ceil(n / i))`, written with integers as `-(-n // i)`, or the O(sqrt n) identity used in the reference: with m = n - 1 and r = isqrt(m), the sum of floor(m / i) over i = 1..m equals 2 * (sum of floor(m / i) for i = 1..r) - r^2.
- C: `(1 << (n - 1).bit_length()) - 1`.
- D: `min(n, 2 * n - 2)`.

Dry run with n = 5. A: j goes 1 → 2 → 4 → 8, three steps, in each of 5 rounds: 15. B: ceil(5/1) + ceil(5/2) + ceil(5/3) + ceil(5/4) + ceil(5/5) = 5 + 3 + 2 + 2 + 1 = 13. C: i = 1, 2, 4 gives 1 + 2 + 4 = 7. D: j climbs to min(5, 8) = 5, so 5 steps (in rounds i = 1, 2, 3).
""",
        complexity="A, C and D: O(1) arithmetic on integers of O(log n) bits. B: O(n) with the direct sum, O(sqrt n) with the identity. Space O(1).",
        pitfalls="Floating-point logarithms (wrong by one at some powers of two, and for huge n); forgetting the edge case n = 1, where no loop body runs at all; counting floor(n / i) instead of ceil(n / i) in shape B; writing 2n - 2 for shape D without the cap at n.",
        follow_up="Why is shape B Theta(n log n)? Compare n + n/2 + n/3 + ... with the area under 1/x. Then count the steps of a sieve of Eratosthenes that, for each prime p, crosses off p^2, p^2 + p, ... up to n.",
    ),
),
# ---------------------------------------------------------------- recursion
dict(
    id="dsaf-hanoi-kth-move",
    title="The k-th Move of the Towers of Hanoi",
    difficulty="Medium",
    pattern="Recursion",
    entry="hanoi_move",
    description=r"""
The recursive solution of the Towers of Hanoi (lesson *Designing recursion and eliminating it*) moves
`n` discs from peg `"A"` to peg `"C"`, with `"B"` as the spare peg:

1. move the top `n - 1` discs from the source peg to the spare peg (recursively);
2. move disc `n`, the largest, from the source peg to the target peg;
3. move the `n - 1` discs from the spare peg to the target peg (recursively).

Discs are numbered from `1` (smallest) to `n` (largest), and the complete solution has $2^n - 1$
moves. Write `hanoi_move(n, k)` that returns the `k`-th move (counting from 1) of exactly this
solution, as `[disc, from_peg, to_peg]`.

Constraints: `1 <= n <= 50` and `1 <= k <= 2^n - 1`. Listing all the moves first is hopeless for
`n = 50` (about $10^{15}$ moves): find the answer in $O(n)$ steps.

**Example:** `n = 3, k = 4` → `[3, "A", "C"]` (the middle move always carries the largest disc)

**Example:** `n = 3, k = 6` → `[2, "B", "C"]`
""",
    starter='''def hanoi_move(n, k):
    pass
''',
    solution='''def hanoi_move(n, k):
    src, dst, spare = "A", "C", "B"
    while True:
        half = 1 << (n - 1)          # the move of disc n is move number 2^(n-1)
        if k == half:
            return [n, src, dst]
        if k < half:                 # first block: n-1 discs from src to spare
            dst, spare = spare, dst
        else:                        # last block: n-1 discs from spare to dst
            k -= half
            src, spare = spare, src
        n -= 1
''',
    tests=[
        [3, 4],
        [3, 6],
        [1, 1],
        [2, 1],
        [2, 3],
        [3, 1],
        [3, 7],
        [4, 5],
        [4, 12],
        [10, 512],
        [10, 1023],
        [20, 699051],
        [33, 2 ** 32 + 5],
        [50, 1],
        [50, 2 ** 50 - 1],
        [50, 987654321987654],
    ],
    examples=2,
    wrong_solutions=[
        '''def hanoi_move(n, k):
    src, dst, spare = "A", "C", "B"
    while True:
        half = 1 << (n - 1)
        if k == half:
            return [n, src, dst]
        if k < half:
            dst, spare = spare, dst
        else:
            src, spare = spare, src
        n -= 1
''',
        '''def hanoi_move(n, k):
    src, dst, spare = "A", "C", "B"
    while True:
        half = 1 << (n - 1)
        if k == half:
            return [n, src, dst]
        if k < half:
            dst, spare = spare, dst
        else:
            k -= half
            dst, spare = spare, dst
        n -= 1
''',
        '''def hanoi_move(n, k):
    src, dst, spare = "A", "C", "B"
    while n > 0:
        half = (1 << (n - 1)) - 1
        if k == half:
            return [n, src, dst]
        if k < half:
            dst, spare = spare, dst
        else:
            k -= half
            src, spare = spare, src
        n -= 1
    return [1, src, dst]
''',
    ],
    guide=dict(
        prereqs="Lessons *Designing recursion and eliminating it* (section 6, the Towers of Hanoi) and *Analysing recursive algorithms* (the recurrence T(n) = 2T(n-1) + 1).",
        intuition="The move list for n discs is three blocks: 2^(n-1) - 1 moves of the first sub-tower, ONE move of disc n, then 2^(n-1) - 1 moves of the second sub-tower. Because the block sizes are known in advance, you can tell which block move k falls into and descend into that block only, like a binary search down the recursion tree.",
        hints=["How many moves does the first recursive call make? Which move number therefore carries disc n?",
               "If k < 2^(n-1), the answer lies in the first sub-solution: n - 1 discs from the source to the spare peg. What are that sub-problem's source, target and spare?",
               "If k > 2^(n-1), subtract 2^(n-1) and continue in the second sub-solution: n - 1 discs from the spare peg to the target, with the source as the spare."],
        brute_force="Generate every move with the recursive procedure and index the list: O(2^n) time and memory. That is fine for n = 10 (1,023 moves) and impossible for n = 50.",
        approach="""
Keep the roles `(src, dst, spare)`, starting as `("A", "C", "B")`. Repeat:

1. `half = 2^(n-1)`. If `k == half`, the move is `[n, src, dst]`.
2. If `k < half`: the first block moves n-1 discs src → spare, so the roles become `(src, spare, dst)`.
3. If `k > half`: set `k -= half`; the last block moves n-1 discs spare → dst, so the roles become `(spare, dst, src)`.
4. `n -= 1`.

Dry run `n = 3, k = 6`: half = 4 and 6 > 4, so k = 2 and the roles become (B, C, A). Now n = 2, half = 2 = k: return `[2, "B", "C"]`.

The full list for n = 3 is A→C, A→B, C→B, **A→C (disc 3)**, B→A, B→C, A→C, which confirms it.
""",
        complexity="At most n rounds of O(1) work (Python integers hold 2^50 exactly): O(n) time and O(1) space. A recursive version with depth n is fine too, since n <= 50.",
        pitfalls="Forgetting to subtract 2^(n-1) when entering the last block; rotating the wrong pair of pegs (the first block swaps target and spare, the last block swaps source and spare); taking move 2^(n-1) - 1 as the middle (off by one); using floating-point powers, which lose precision for large n.",
        follow_up="Prove that the disc moved at step k is 1 plus the number of trailing zero bits of k, the same pattern as the tick lengths of the English ruler. Can you also report where every disc sits after k moves?",
    ),
),
# ---------------------------------------------------------------- stacks
dict(
    id="dsaf-infix-to-postfix",
    title="Infix to Postfix with Right-Associative Powers",
    difficulty="Medium",
    pattern="Stacks, Queues and Deques",
    entry="to_postfix",
    description=r"""
Convert an infix arithmetic expression to **postfix** (reverse Polish) notation using the
operator-stack method of the lesson *Stacks and their applications*.

The input string contains:

- operands: non-negative integer literals of one or more digits (`7`, `345`) or single lowercase
  letters (`x`);
- the binary operators `+ - * / ^` and parentheses `( )`;
- any number of spaces between tokens.

Precedence from loosest to tightest is `+ -`, then `* /`, then `^`. The operators `+ - * /` group
**left to right** (`8-3-2` means `(8-3)-2`), while `^` groups **right to left** (`2^3^2` means
`2^(3^2)`). The expression is always well formed and has no unary minus.

Return the postfix tokens joined by single spaces.

**Example:** `"6 + 2*(9 - 4)/5"` → `"6 2 9 4 - * 5 / +"`

**Example:** `"2^3^2"` → `"2 3 2 ^ ^"`

**Example:** `"a-b-c"` → `"a b - c -"`
""",
    starter='''def to_postfix(expr):
    pass
''',
    solution='''def to_postfix(expr):
    prec = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3}
    out, ops = [], []
    i, n = 0, len(expr)
    while i < n:
        ch = expr[i]
        if ch == " ":
            i += 1
            continue
        if ch.isdigit():                       # a whole run of digits is one number
            j = i
            while j < n and expr[j].isdigit():
                j += 1
            out.append(expr[i:j])
            i = j
            continue
        if ch.isalpha():
            out.append(ch)
        elif ch == "(":
            ops.append(ch)
        elif ch == ")":
            while ops[-1] != "(":
                out.append(ops.pop())
            ops.pop()
        else:
            while ops and ops[-1] != "(" and (
                    prec[ops[-1]] > prec[ch] or (prec[ops[-1]] == prec[ch] and ch != "^")):
                out.append(ops.pop())
            ops.append(ch)
        i += 1
    while ops:
        out.append(ops.pop())
    return " ".join(out)
''',
    tests=[
        ["6 + 2*(9 - 4)/5"],
        ["2^3^2"],
        ["a-b-c"],
        ["42"],
        ["(((7)))"],
        ["12+345*6"],
        ["  x * ( y + z )  "],
        ["100 / 25 / 2"],
        ["9-8+7-6"],
        ["2*3^2"],
        ["(1+2)*(3+4)-5"],
        ["a*(b+c*(d-e))^f/g"],
        ["2^(1+1)^3-x/y/z"],
        [_long_expr(41, 60)],
        [_long_expr(42, 400)],
    ],
    examples=3,
    wrong_solutions=[
        '''def to_postfix(expr):
    prec = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3}
    out, ops, i, n = [], [], 0, len(expr)
    while i < n:
        ch = expr[i]
        if ch == " ":
            i += 1
            continue
        if ch.isdigit():
            j = i
            while j < n and expr[j].isdigit():
                j += 1
            out.append(expr[i:j])
            i = j
            continue
        if ch.isalpha():
            out.append(ch)
        elif ch == "(":
            ops.append(ch)
        elif ch == ")":
            while ops[-1] != "(":
                out.append(ops.pop())
            ops.pop()
        else:
            while ops and ops[-1] != "(" and prec[ops[-1]] >= prec[ch]:
                out.append(ops.pop())
            ops.append(ch)
        i += 1
    while ops:
        out.append(ops.pop())
    return " ".join(out)
''',
        '''def to_postfix(expr):
    prec = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3}
    out, ops, i, n = [], [], 0, len(expr)
    while i < n:
        ch = expr[i]
        if ch == " ":
            i += 1
            continue
        if ch.isdigit():
            j = i
            while j < n and expr[j].isdigit():
                j += 1
            out.append(expr[i:j])
            i = j
            continue
        if ch.isalpha():
            out.append(ch)
        elif ch == "(":
            ops.append(ch)
        elif ch == ")":
            while ops[-1] != "(":
                out.append(ops.pop())
            ops.pop()
        else:
            while ops and ops[-1] != "(" and prec[ops[-1]] > prec[ch]:
                out.append(ops.pop())
            ops.append(ch)
        i += 1
    while ops:
        out.append(ops.pop())
    return " ".join(out)
''',
        '''def to_postfix(expr):
    prec = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3}
    out, ops = [], []
    for ch in expr.replace(" ", ""):
        if ch.isalnum():
            out.append(ch)
        elif ch == "(":
            ops.append(ch)
        elif ch == ")":
            while ops[-1] != "(":
                out.append(ops.pop())
            ops.pop()
        else:
            while ops and ops[-1] != "(" and (
                    prec[ops[-1]] > prec[ch] or (prec[ops[-1]] == prec[ch] and ch != "^")):
                out.append(ops.pop())
            ops.append(ch)
    while ops:
        out.append(ops.pop())
    return " ".join(out)
''',
    ],
    guide=dict(
        prereqs="Lesson *Stacks and their applications*, section 7 (from infix to postfix) and section 5 (evaluating postfix).",
        intuition="Operands already appear in the right order, so they go straight to the output. An operator must wait on a stack until its right operand has been written. It may leave when a newcomer arrives that binds less tightly (or equally tightly, if the operators group left to right), or when its enclosing parenthesis closes.",
        hints=["Tokenise first: a run of digits is one number, spaces are skipped, and every other character is a token of its own.",
               "On an operator `op`, pop to the output each stacked operator (stopping at `(`) whose precedence is higher than op's, or equal to it when op groups left to right; then push op.",
               "For `^`, equal precedence must NOT pop: in `2^3^2` the first `^` keeps waiting so that the second is applied first."],
        brute_force="Find the loosest operator outside all parentheses (the rightmost one for left-grouping operators, the leftmost `^`), split the string there and recurse on both sides. It is correct but rescans the string at every level: O(n^2) on long expressions, and deep recursion on long chains.",
        approach="""
Scan the string once, keeping an output list and an operator stack:

- number or letter → output;
- `(` → push;
- `)` → pop to the output until `(`, then discard the `(`;
- operator → pop while the rule of hint 2 allows, then push;
- end → pop everything that is left.

Dry run on `"6 + 2*(9 - 4)/5"`:

| token | action | stack | output |
|---|---|---|---|
| 6 | output | | 6 |
| + | push | + | 6 |
| 2 | output | + | 6 2 |
| * | `+` is looser, push | + * | 6 2 |
| ( | push | + * ( | 6 2 |
| 9 | output | + * ( | 6 2 9 |
| - | top is `(`, push | + * ( - | 6 2 9 |
| 4 | output | + * ( - | 6 2 9 4 |
| ) | pop until `(` | + * | 6 2 9 4 - |
| / | `*` is equal and groups left: pop it, push `/` | + / | 6 2 9 4 - * |
| 5 | output | + / | 6 2 9 4 - * 5 |
| end | pop all | | 6 2 9 4 - * 5 / + |
""",
        complexity="Each character is read once and each operator is pushed and popped at most once: O(n) time and O(n) extra space for an expression of n characters.",
        pitfalls="Popping on equal precedence for `^` (produces `2 3 ^ 2 ^`); not popping on equal precedence for `-` and `/` (produces `a b c - -`); splitting `12` into `1` and `2`; popping past a `(` when an operator arrives; forgetting to empty the stack at the end.",
        follow_up="Evaluate the postfix string with a second stack. Add unary minus by tokenising it as its own operator that binds tighter than `*` but looser than `^` (so that `-2^2` is -4).",
    ),
),
# ---------------------------------------------------------------- linked lists
dict(
    id="dsaf-positional-list",
    title="Positional List with Handles and Move-to-Front",
    difficulty="Medium",
    pattern="Linked Lists",
    kind="class",
    entry="PositionalList",
    description=r"""
Build a **positional list** (Goodrich ch. 7.4): a doubly linked list whose users keep *positions*
rather than indices. The grader can only pass plain values, so positions are integer **handles**:
the first successful insertion returns handle `1`, the next one `2`, and so on. A handle stays
attached to its element while other elements are inserted, deleted or moved around it, and becomes
invalid when its own element is deleted.

| Operation | Returns |
|---|---|
| `add_first(e)`, `add_last(e)` | the handle of the new element |
| `add_before(h, e)`, `add_after(h, e)` | the handle of the new element, placed next to `h` |
| `first()`, `last()` | the handle of the first / last element, or `None` if the list is empty |
| `before(h)`, `after(h)` | the handle of the neighbour, or `None` if `h` is at that end |
| `element(h)` | the element at `h` |
| `replace(h, e)` | the old element at `h` (which now holds `e`) |
| `delete(h)` | the removed element; `h` becomes invalid |
| `move_to_front(h)` | `None`; the element moves to the front and **keeps its handle** |
| `size()`, `to_list()` | the number of elements; the elements from front to back |

An operation given an **invalid handle** (never issued, or already deleted) changes nothing and
returns `-1`; in particular a failed `add_before` / `add_after` does not use up a handle number.
Elements are non-empty strings. Every operation except `to_list` must run in $O(1)$ time.

**Example:** `["PositionalList","add_last","add_last","add_first","add_after","to_list","before","after","after"]`,
`[[],["b"],["d"],["a"],[1,"c"],[],[1],[4],[2]]` → `[null,1,2,3,4,["a","b","c","d"],3,2,null]`

**Example:** `["PositionalList","add_first","add_first","delete","element","delete","replace","element","first","size"]`,
`[[],["x"],["y"],[1],[1],[1],[2,"z"],[2],[],[]]` → `[null,1,2,"x",-1,-1,"y","z",2,1]`
""",
    starter='''class _Node:
    __slots__ = "elem", "prev", "next", "handle"

    def __init__(self, elem, prev, next, handle):
        self.elem, self.prev, self.next, self.handle = elem, prev, next, handle


class PositionalList:
    def __init__(self):
        self._header = _Node(None, None, None, None)
        self._trailer = _Node(None, None, None, None)
        self._header.next = self._trailer
        self._trailer.prev = self._header
        # you will also need a dict from handle to node, and the next handle number

    def add_first(self, e):
        pass

    def add_last(self, e):
        pass

    def add_before(self, h, e):
        pass

    def add_after(self, h, e):
        pass

    def first(self):
        pass

    def last(self):
        pass

    def before(self, h):
        pass

    def after(self, h):
        pass

    def element(self, h):
        pass

    def replace(self, h, e):
        pass

    def delete(self, h):
        pass

    def move_to_front(self, h):
        pass

    def size(self):
        pass

    def to_list(self):
        pass
''',
    solution=_POS_SOL,
    tests=[
        [["PositionalList", "add_last", "add_last", "add_first", "add_after", "to_list", "before", "after", "after"],
         [[], ["b"], ["d"], ["a"], [1, "c"], [], [1], [4], [2]]],
        [["PositionalList", "add_first", "add_first", "delete", "element", "delete", "replace", "element", "first", "size"],
         [[], ["x"], ["y"], [1], [1], [1], [2, "z"], [2], [], []]],
        [["PositionalList", "first", "last", "size", "to_list", "after", "element", "delete", "move_to_front"],
         [[], [], [], [], [], [1], [0], [3], [1]]],
        [["PositionalList", "add_last", "add_last", "add_last", "move_to_front", "to_list", "move_to_front", "to_list",
          "move_to_front", "to_list", "first", "last", "before", "after", "element"],
         [[], ["a"], ["b"], ["c"], [3], [], [3], [], [2], [], [], [], [2], [1], [3]]],
        [["PositionalList", "add_first", "add_before", "add_before", "add_last", "to_list", "delete", "add_after",
          "add_first", "to_list", "size"],
         [[], ["m"], [1, "l"], [7, "q"], ["n"], [], [2], [2, "zz"], ["k"], [], []]],
        [["PositionalList", "add_first", "move_to_front", "before", "after", "delete", "first", "last", "size",
          "add_last", "first", "move_to_front", "replace"],
         [[], ["only"], [1], [1], [1], [1], [], [], [], ["again"], [], [1], [1, "nope"]]],
        [["PositionalList", "add_last", "add_last", "add_last", "add_last", "delete", "delete", "after", "before",
          "add_after", "add_before", "to_list", "move_to_front", "to_list", "last"],
         [[], ["p"], ["q"], ["r"], ["s"], [2], [3], [1], [4], [1, "t"], [4, "u"], [], [4], [], []]],
        [["PositionalList", "add_last", "add_last", "delete", "delete", "size", "to_list", "add_first", "add_after",
          "to_list", "element", "element"],
         [[], ["a"], ["b"], [1], [2], [], [], ["c"], [3, "d"], [], [3], [4]]],
        _pos_ops(1200, 51),
        _pos_ops(6000, 52),
    ],
    examples=2,
    wrong_solutions=[
        _mutate(_POS_SOL, "node = self._nodes.pop(h, None)", "node = self._nodes.get(h)"),
        _mutate(_POS_SOL,
                "        node = self._nodes.get(h)\n        if node is None:\n            return -1\n        return self._insert_between(e, node.prev, node)",
                "        node = self._nodes.get(h)\n        if node is None:\n            self._next_handle += 1\n            return -1\n        return self._insert_between(e, node.prev, node)"),
        _mutate(_POS_SOL,
                "        if self._header.next is not node:\n            self._unlink(node)",
                "        if True:\n            elem = self.delete(h)\n            return self.add_first(elem)\n        if self._header.next is not node:\n            self._unlink(node)"),
    ],
    guide=dict(
        prereqs="Lessons *Doubly linked lists and positional lists* (sentinels, the positional list ADT) and *Access frequencies, move-to-front and link vs array*.",
        intuition="A handle is a cloakroom ticket for one node. Keep a dictionary from ticket number to node: it turns a handle into its node in O(1), and the node's prev/next links do the rest. Sentinels at both ends mean every insertion is 'between two nodes' and every removal is 'join my two neighbours'.",
        hints=["Store `{handle: node}` for live elements only; deleting pops the entry, so a dead handle is simply 'not in the dictionary'.",
               "Write two helpers once: `_insert_between(e, a, b)` (issues the next handle) and `_unlink(node)`. Every update is built from them.",
               "move_to_front = unlink the node, then relink the SAME node right after the header. Do not create a new node, or the handle changes."],
        brute_force="A Python list of `[handle, element]` pairs works but every operation must first search for the handle: O(n) each, O(n^2) for a long sequence. It also makes insertions in the middle shift everything after them.",
        approach="""
- Fields: header and trailer sentinels, `_nodes = {}`, `_next_handle = 1`.
- `add_*`: find the two neighbours (validating `h` first for before/after), call `_insert_between`, return the new handle.
- `first/last/before/after`: follow one link; translate a sentinel into `None`.
- `delete(h)`: pop the node from the dictionary, unlink it, return its element.
- `move_to_front(h)`: if the node is not already first, unlink it and splice it in after the header.

Dry run of the first example: add_last b → 1, add_last d → 2, add_first a → 3, add_after(1, c) → 4. The list is a b c d. before(1) is the node of a, handle 3; after(4) is d, handle 2; after(2) reaches the trailer: `None`.
""",
        complexity="Every operation except to_list does a dictionary lookup and a constant number of link updates: O(1). to_list is O(n). Space O(n): one node (four fields) and one dictionary entry per element.",
        pitfalls="Leaving a deleted handle in the dictionary (it must answer -1 afterwards); spending a handle number on a failed insertion; implementing move_to_front as delete plus add_first, which hands out a new handle; returning -1 at the ends of the list where `None` is expected; forgetting to update both neighbours' links when splicing.",
        follow_up="Add a dictionary from element to handle and you have an LRU cache: access = move_to_front, eviction = delete(last()). Sort the list in place with insertion sort using only positions (lesson section 4).",
    ),
),
# ---------------------------------------------------------------- trees
dict(
    id="dsaf-parenthesize-tree",
    title="Parenthetic Representation of a Deep Tree",
    difficulty="Medium",
    pattern="Trees",
    entry="parenthesize",
    description=r"""
A general tree with `n` nodes numbered `0 .. n-1` is given as a **parent array**: `parent[v]` is the
parent of node `v`, and the one root has `parent[root] = -1` (the root need not be node 0). The
children of a node are ordered by increasing node number. `labels[v]` is the text of node `v`
(letters and digits; labels may repeat).

Return the tree's **parenthetic string representation** (Goodrich ch. 8.4.5):

- a leaf is written as its label;
- any other node is written as its label, a space, `(`, the representations of its children
  separated by `", "`, and `)`.

`1 <= n <= 8000`. The tree may be a single path thousands of levels deep, deeper than Python's
default recursion limit of 1000, so walk it with an explicit stack.

**Example:** `parent = [-1, 0, 0, 1, 1, 2]`, `labels = ["Q", "R", "S", "T", "U", "V"]` →
`"Q (R (T, U), S (V))"`

**Example:** `parent = [2, 2, -1, 1]`, `labels = ["x", "y", "top", "z"]` → `"top (x, y (z))"`
""",
    starter='''def parenthesize(parent, labels):
    pass
''',
    solution=_PAREN_SOL,
    tests=[
        [[-1, 0, 0, 1, 1, 2], ["Q", "R", "S", "T", "U", "V"]],
        [[2, 2, -1, 1], ["x", "y", "top", "z"]],
        [[-1], ["solo"]],
        [[-1, 0, 0, 0, 0], ["hub", "a", "b", "c", "d"]],
        [[-1, 0, 1, 2, 3], ["a", "b", "c", "d", "e"]],
        [[3, 3, 3, -1], ["p", "q", "s", "r"]],
        [[-1, 0, 0, 1], ["n", "n", "n", "n"]],
        [[4, 4, 0, 0, -1, 1, 1, 2], ["k1", "k2", "k3", "k4", "root", "k6", "k7", "k8"]],
        [[-1] + list(range(5999)), ["a"] * 6000],
        [list(range(1, 3000)) + [-1], ["b"] * 3000],
        _rand_parent_tree(2500, 61, 40),
        _rand_parent_tree(2000, 62, 2000),
        _caterpillar(1500, 63),
    ],
    examples=2,
    wrong_solutions=[
        '''def parenthesize(parent, labels):
    n = len(parent)
    kids = [[] for _ in range(n)]
    root = 0
    for v, p in enumerate(parent):
        if p == -1:
            root = v
        else:
            kids[p].append(v)
    def rec(v):
        if not kids[v]:
            return labels[v]
        return labels[v] + " (" + ", ".join(rec(c) for c in kids[v]) + ")"
    return rec(root)
''',
        '''def parenthesize(parent, labels):
    n = len(parent)
    kids = [[] for _ in range(n)]
    root = 0
    for v, p in enumerate(parent):
        if p == -1:
            root = v
        else:
            kids[p].append(v)
    out = []
    stack = [("node", root)]
    while stack:
        kind, v = stack.pop()
        if kind == "text":
            out.append(v)
            continue
        out.append(labels[v])
        if kids[v]:
            out.append(" (")
            stack.append(("text", ")"))
            for j, c in enumerate(kids[v]):
                if j:
                    stack.append(("text", ", "))
                stack.append(("node", c))
    return "".join(out)
''',
        _mutate(_PAREN_SOL, 'out.append(" (")', 'out.append("(")'),
    ],
    guide=dict(
        prereqs="Lessons *Traversals, Euler tours and expression trees* (sections 5, 6 and 8: the parenthetic representation, the Euler tour, traversals with an explicit stack) and *Tree terminology, ADTs and representations* (section 6: parent arrays).",
        intuition="The string is an Euler tour written down. Coming DOWN into a node (pre visit), write its label and, if it has children, ' ('. BETWEEN two children, write ', '. Going back UP (post visit), write ')'. An explicit stack remembers, for every node on the current path, which child to visit next.",
        hints=["First build child lists in one pass: append `v` to `children[parent[v]]`. Scanning `v` in increasing order keeps every list sorted.",
               "Push pairs `(node, next_child_index)`. When you pop `(v, i)`: if `i == 0`, write the label; if `i` is less than the number of children, push `(v, i + 1)` back and then `(child_i, 0)` on top of it.",
               "Write ', ' before every child except the first, and ')' when a node that has children has no child left to visit."],
        brute_force="The recursive one-liner `label + ' (' + ', '.join(rec(c) for c in kids) + ')'` gives the right string, but on a path of a few thousand nodes it raises RecursionError. Gluing strings bottom-up also copies long strings again at every level; collecting pieces in one list and joining once avoids that.",
        approach="""
Child lists for the first example: 0 → [1, 2], 1 → [3, 4], 2 → [5].

| pop | written | pushed back |
|---|---|---|
| (0,0) | `Q (` | (0,1), (1,0) |
| (1,0) | `R (` | (1,1), (3,0) |
| (3,0) | `T` | |
| (1,1) | `, ` | (1,2), (4,0) |
| (4,0) | `U` | |
| (1,2) | `)` | |
| (0,1) | `, ` | (0,2), (2,0) |
| (2,0) | `S (` | (2,1), (5,0) |
| (5,0) | `V` | |
| (2,1) | `)` | |
| (0,2) | `)` | |

Joined: `Q (R (T, U), S (V))`.
""",
        complexity="Building the child lists is O(n). A node is popped once more than it has children, so the loop runs sum(c_v + 1) = 2n - 1 times: O(n), and the output has O(n + total label length) characters. Extra space O(n) for the child lists; the stack holds one entry per level of the current path.",
        pitfalls="Recursing on a deep tree; assuming the root is node 0; pushing all children at once in index order (a stack hands them back in reverse); a missing space before `(` or after the comma; writing `()` after a leaf.",
        follow_up="Do the reverse: parse the parenthetic string back into a parent array. Print an indented outline with numbered headings (1, 1.1, 1.2, ...) using the same explicit-stack tour.",
    ),
),
]
