import random as _r

_r.seed(7)

PROBLEMS = [
# ---------------------------------------------------------------- analysis
dict(
    id="dsaf-prefix-averages",
    title="Prefix Averages in Linear Time",
    difficulty="Easy",
    pattern="Algorithm Analysis",
    entry="prefix_averages",
    compare="float",
    description=r"""
Given a list `S` of $n$ numbers, return a list `A` of the same length where `A[j]` is the average of
`S[0], S[1], ..., S[j]` (Goodrich ch. 3.3.3).

The obvious double loop is $O(n^2)$; your solution must be $O(n)$ — the hidden tests include long inputs.
Return floats. An empty input returns `[]`.

**Example:** `S = [2, 4, 6, 8]` → `[2.0, 3.0, 4.0, 5.0]`

**Example:** `S = [10, -10, 5]` → `[10.0, 0.0, 1.6666666666666667]`
""",
    starter='''def prefix_averages(S):
    pass
''',
    solution='''def prefix_averages(S):
    A, total = [], 0
    for j, x in enumerate(S):
        total += x
        A.append(total / (j + 1))
    return A
''',
    tests=[
        [[2, 4, 6, 8]],
        [[10, -10, 5]],
        [[]],
        [[7]],
        [[1, 1, 1, 1, 1]],
        [[0, 0, 3]],
        [[-5, -5, -5, 15]],
        [[1.5, 2.5, 3.5]],
        [[_r.randint(-1000, 1000) for _ in range(1000)]],
        [[_r.randint(0, 1000) for _ in range(8000)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def prefix_averages(S):
    A, total = [], 0
    for j, x in enumerate(S):
        total += x
        A.append(total / max(j, 1))
    return A
''',
        '''def prefix_averages(S):
    A, total = [], 0
    for j, x in enumerate(S):
        total += x
        A.append(total // (j + 1))
    return A
''',
    ],
    guide=dict(
        prereqs="Lesson *Analysing real code and proving it correct* (prefix_average1/2/3).",
        intuition="The sum of the first j+1 elements is the sum of the first j elements plus one more. Keep a **running total** instead of re-adding everything.",
        hints=["How does sum(S[0..j]) relate to sum(S[0..j-1])?",
               "Maintain one variable `total` across iterations.",
               "Divide by j + 1, not j, and use true division `/`."],
        brute_force="For each j, loop i from 0 to j and add: 1 + 2 + ... + n = n(n+1)/2 additions, **O(n^2)**. Writing `sum(S[:j+1])` is the same cost hidden behind a slice.",
        approach="""
1. `total = 0`, `A = []`.
2. For each index `j` with value `x`: `total += x`; append `total / (j + 1)`.

Dry run on `[2, 4, 6, 8]`: totals 2, 6, 12, 20 → averages 2, 3, 4, 5.
""",
        complexity="Time O(n): one addition and one division per element. Space O(n) for the output (O(1) extra).",
        pitfalls="Dividing by `j` (off by one, and division by zero at j = 0); integer division `//`; using slicing + sum inside the loop (quadratic).",
        follow_up="Running/prefix sums power range-sum queries in O(1): sum(S[i..j]) = P[j+1] - P[i].",
    ),
),
# ---------------------------------------------------------------- recursion
dict(
    id="dsaf-english-ruler",
    title="Draw an English Ruler",
    difficulty="Easy",
    pattern="Recursion",
    entry="draw_ruler",
    description=r"""
Return the lines of an English ruler (Goodrich ch. 4.1.2) as a list of strings instead of printing.

`draw_ruler(num_inches, major_length)`:

- the ruler starts with a major tick labelled `0`: `'-' * major_length + ' 0'`;
- for each inch `j = 1 .. num_inches`, it draws an **interval** with central tick length
  `major_length - 1`, followed by a major tick labelled `j`.

An interval with central length `L > 0` is: an interval of central length `L - 1`, a tick
`'-' * L` (no label), then another interval of central length `L - 1`. An interval with `L = 0` is
empty.

`0 <= num_inches <= 6`, `1 <= major_length <= 7`.

**Example:** `draw_ruler(1, 3)` →
`['--- 0', '-', '--', '-', '--- 1']`
""",
    starter='''def draw_ruler(num_inches, major_length):
    lines = []
    # write a recursive helper that appends the lines of an interval
    return lines
''',
    solution='''def draw_ruler(num_inches, major_length):
    lines = []
    def tick(length, label=''):
        lines.append('-' * length + (' ' + label if label else ''))
    def interval(c):
        if c > 0:
            interval(c - 1)
            tick(c)
            interval(c - 1)
    tick(major_length, '0')
    for j in range(1, num_inches + 1):
        interval(major_length - 1)
        tick(major_length, str(j))
    return lines
''',
    tests=[[1, 3], [2, 4], [0, 5], [1, 1], [3, 1], [2, 2], [1, 5], [3, 3], [6, 7], [4, 6]],
    examples=2,
    wrong_solutions=[
        '''def draw_ruler(num_inches, major_length):
    lines = ['-' * major_length + ' 0']
    for j in range(1, num_inches + 1):
        for c in range(1, major_length):
            lines.append('-' * c)
        lines.append('-' * major_length + ' ' + str(j))
    return lines
''',
    ],
    guide=dict(
        prereqs="Lesson *Thinking recursively* (section 3).",
        intuition="Between two inch marks, the pattern is: a smaller ruler pattern, one tick of the central length, the same smaller pattern again. That self-similarity is the recursion.",
        hints=["Write `interval(c)` that appends the lines for central length c.",
               "Base case: c == 0 appends nothing.",
               "Recursive case: interval(c-1); tick(c); interval(c-1)."],
        brute_force="You could try to compute the tick length of each line directly (it is 1 + the number of trailing zero bits of the line index), but the recursive definition is simpler and exactly as fast.",
        approach="""
Use a nested helper that closes over `lines`. `draw_ruler` appends the `0` tick, then for each inch calls `interval(major_length - 1)` and appends the labelled major tick.

Dry run `interval(2)`: interval(1) → ['-']; tick '--'; interval(1) → ['-'] — giving `-`, `--`, `-`.
""",
        complexity="interval(c) produces 2^c - 1 lines, so the total is O(num_inches * 2^major_length) — proportional to the output, which is optimal. Recursion depth is major_length.",
        pitfalls="Labelled ticks need exactly one space before the label; unlabelled ticks have no trailing space. Remember the major tick for inch 0 even when num_inches is 0.",
        follow_up="Prove by induction that interval(c) emits 2^c - 1 lines. Can you write it without recursion using the trailing-zero-bits trick?",
    ),
),
dict(
    id="dsaf-recursive-binary-search",
    title="Recursive Binary Search",
    difficulty="Easy",
    pattern="Recursion",
    entry="binary_search",
    description=r"""
`data` is a list of **distinct** integers sorted in increasing order. Return the index of `target` in
`data`, or `-1` if it is absent.

Implement it **recursively** with a helper that takes `low` and `high` indices (Goodrich ch. 4.1.3) —
do not slice the list. Must run in $O(\log n)$.

**Example:** `data = [2, 4, 5, 7, 8, 9, 12, 14, 17, 19, 22, 25, 27, 28, 33, 37], target = 22` → `10`

**Example:** `data = [1, 3, 5], target = 4` → `-1`
""",
    starter='''def binary_search(data, target):
    pass
''',
    solution='''def binary_search(data, target):
    def search(low, high):
        if low > high:
            return -1
        mid = (low + high) // 2
        if data[mid] == target:
            return mid
        if target < data[mid]:
            return search(low, mid - 1)
        return search(mid + 1, high)
    return search(0, len(data) - 1)
''',
    tests=[
        [[2, 4, 5, 7, 8, 9, 12, 14, 17, 19, 22, 25, 27, 28, 33, 37], 22],
        [[1, 3, 5], 4],
        [[], 1],
        [[5], 5],
        [[5], 6],
        [[1, 2], 1],
        [[1, 2], 2],
        [[-10, -3, 0, 4, 9], -10],
        [[-10, -3, 0, 4, 9], 9],
        [[-10, -3, 0, 4, 9], 100],
        [list(range(0, 36000, 3)), 35997],
        [list(range(0, 36000, 3)), 18001],
    ],
    examples=2,
    wrong_solutions=[
        '''def binary_search(data, target):
    low, high = 0, len(data) - 1
    while low < high:
        mid = (low + high) // 2
        if data[mid] == target:
            return mid
        if target < data[mid]:
            high = mid - 1
        else:
            low = mid + 1
    return -1
''',
    ],
    guide=dict(
        prereqs="Lessons *Thinking recursively* and *Designing recursion* (parameterising a recursion).",
        intuition="Compare with the middle element; the answer can only lie in one half, so recurse there. Each call halves the candidate range.",
        hints=["Invariant: if target is present, it lies in data[low..high].",
               "Base case: low > high means the range is empty.",
               "Exclude mid from the next range (mid - 1 or mid + 1) to guarantee progress."],
        brute_force="Linear scan: O(n). It ignores the sortedness.",
        approach="""
`search(low, high)`: if `low > high` return -1. Compute `mid = (low + high) // 2`. Equal → return mid; smaller target → `search(low, mid - 1)`; larger → `search(mid + 1, high)`. Start with `search(0, len(data) - 1)`.
""",
        complexity="Time O(log n): at most floor(log2 n) + 1 calls. Space O(log n) recursion depth (O(1) if you eliminate the tail recursion).",
        pitfalls="Using `low < high` misses the single-element range. Recursing on `[low, mid]` can loop forever. Slicing `data[:mid]` makes each call O(n).",
        follow_up="Variants: first index >= target (bisect_left), last occurrence with duplicates, search in a rotated sorted array.",
    ),
),
# ---------------------------------------------------------------- arrays
dict(
    id="dsaf-dynamic-array",
    title="Implement a Dynamic Array",
    difficulty="Medium",
    pattern="Array-Based Sequences",
    kind="class",
    entry="DynamicArray",
    description=r"""
Implement a dynamic array (Goodrich ch. 5.3) **on top of a fixed-size storage list** that you only
ever replace, never `append` to. The grader inspects `capacity()`, so follow this exact policy:

- The initial capacity is **1** and the size is 0.
- `append(x)`: if the array is full, **double** the capacity first; then store `x` at the end.
- `insert(k, x)`: insert at index `0 <= k <= size` (shifting later items right); grow first if full
  (same doubling rule).
- `get(k)` → the element at index `k`, or `None` if `k` is not in `[0, size)`.
- `set(k, x)` → replace the element at `k`; returns `True`, or `False` for an invalid index.
- `pop()` → remove and return the last element (`None` if empty). After removing, if
  `capacity > 1` and `size < capacity // 4`, **halve** the capacity.
- `size()` and `capacity()`.

**Example:**
`["DynamicArray","append","append","append","capacity","pop","pop","capacity","get"]`,
`[[],[5],[6],[7],[],[],[],[],[0]]` → `[None,None,None,None,4,7,6,4,5]`

(After the second pop size is 1, and 1 < 4 // 4 is false, so the capacity stays 4.)
""",
    starter='''class DynamicArray:
    def __init__(self):
        self._n = 0
        self._cap = 1
        self._A = [None] * self._cap

    def append(self, x):
        pass

    def insert(self, k, x):
        pass

    def get(self, k):
        pass

    def set(self, k, x):
        pass

    def pop(self):
        pass

    def size(self):
        pass

    def capacity(self):
        pass
''',
    solution='''class DynamicArray:
    def __init__(self):
        self._n = 0
        self._cap = 1
        self._A = [None] * self._cap

    def _resize(self, c):
        B = [None] * c
        for i in range(self._n):
            B[i] = self._A[i]
        self._A, self._cap = B, c

    def append(self, x):
        if self._n == self._cap:
            self._resize(2 * self._cap)
        self._A[self._n] = x
        self._n += 1

    def insert(self, k, x):
        if self._n == self._cap:
            self._resize(2 * self._cap)
        for j in range(self._n, k, -1):
            self._A[j] = self._A[j - 1]
        self._A[k] = x
        self._n += 1

    def get(self, k):
        if 0 <= k < self._n:
            return self._A[k]
        return None

    def set(self, k, x):
        if 0 <= k < self._n:
            self._A[k] = x
            return True
        return False

    def pop(self):
        if self._n == 0:
            return None
        self._n -= 1
        x = self._A[self._n]
        self._A[self._n] = None
        if self._cap > 1 and self._n < self._cap // 4:
            self._resize(self._cap // 2)
        return x

    def size(self):
        return self._n

    def capacity(self):
        return self._cap
''',
    tests=[
        [["DynamicArray", "append", "append", "append", "capacity", "pop", "pop", "capacity", "get"],
         [[], [5], [6], [7], [], [], [], [], [0]]],
        [["DynamicArray", "capacity", "size", "pop", "get", "set"], [[], [], [], [], [0], [0, 1]]],
        [["DynamicArray", "append", "capacity", "append", "capacity", "append", "capacity", "append", "capacity", "append", "capacity"],
         [[], [1], [], [2], [], [3], [], [4], [], [5], []]],
        [["DynamicArray", "append", "append", "insert", "insert", "insert", "get", "get", "get", "get", "get", "size", "capacity"],
         [[], ["b"], ["d"], [0, "a"], [2, "c"], [4, "e"], [0], [1], [2], [3], [4], [], []]],
        [["DynamicArray", "append", "append", "set", "get", "set", "get", "get"],
         [[], [1], [2], [1, 20], [1], [5, 9], [5], [-1]]],
        [["DynamicArray"] + ["append"] * 9 + ["capacity"] + ["pop"] * 7 + ["capacity", "size", "get"],
         [[]] + [[i] for i in range(9)] + [[]] + [[]] * 7 + [[], [], [1]]],
        [["DynamicArray"] + ["append"] * 8 + ["pop"] * 8 + ["capacity", "pop", "capacity"],
         [[]] + [[i] for i in range(8)] + [[]] * 8 + [[], [], []]],
        [["DynamicArray", "insert", "insert", "insert", "get", "get", "get", "capacity"],
         [[], [0, 3], [0, 2], [0, 1], [0], [1], [2], []]],
        [["DynamicArray"] + ["append"] * 1000 + ["capacity", "size", "get"] + ["pop"] * 990 + ["capacity", "size", "get"],
         [[]] + [[i * i] for i in range(1000)] + [[], [], [999]] + [[]] * 990 + [[], [], [9]]],
        [["DynamicArray"] + ["append", "pop"] * 6 + ["capacity"],
         [[]] + [[1], []] * 6 + [[]]],
    ],
    examples=2,
    wrong_solutions=[
        '''class DynamicArray:
    def __init__(self):
        self._A = []
        self._cap = 1
    def append(self, x):
        self._A.append(x)
        if len(self._A) > self._cap:
            self._cap += 1
    def insert(self, k, x):
        self._A.insert(k, x)
        if len(self._A) > self._cap:
            self._cap += 1
    def get(self, k):
        return self._A[k] if 0 <= k < len(self._A) else None
    def set(self, k, x):
        if 0 <= k < len(self._A):
            self._A[k] = x
            return True
        return False
    def pop(self):
        return self._A.pop() if self._A else None
    def size(self):
        return len(self._A)
    def capacity(self):
        return self._cap
''',
        '''class DynamicArray:
    def __init__(self):
        self._A = []
        self._cap = 1
    def append(self, x):
        if len(self._A) == self._cap:
            self._cap *= 2
        self._A.append(x)
    def insert(self, k, x):
        if len(self._A) == self._cap:
            self._cap *= 2
        self._A.insert(k, x)
    def get(self, k):
        return self._A[k] if 0 <= k < len(self._A) else None
    def set(self, k, x):
        if 0 <= k < len(self._A):
            self._A[k] = x
            return True
        return False
    def pop(self):
        return self._A.pop() if self._A else None
    def size(self):
        return len(self._A)
    def capacity(self):
        return self._cap
''',
    ],
    guide=dict(
        prereqs="Lesson *Dynamic arrays and amortised analysis*.",
        intuition="Keep spare room. When it runs out, allocate an array twice as big and copy; the copies form a geometric series, so they average out to O(1) per append. Shrink only at one-quarter full to avoid thrashing.",
        hints=["Store `_n` (size), `_cap` (capacity) and `_A` (a list of length `_cap`).",
               "Write `_resize(c)` that allocates `[None] * c` and copies the first `_n` items.",
               "insert shifts from the end backwards: for j from n down to k+1, A[j] = A[j-1].",
               "pop: decrement size first, then test `size < cap // 4` and halve."],
        brute_force="Wrapping Python's own list hides the capacity logic entirely — and fails the capacity checks. The point is to implement the growth policy yourself.",
        approach="""
- `append`: grow if `_n == _cap`, write at `_A[_n]`, increment.
- `insert(k, x)`: grow if full, shift `_A[k.._n-1]` one right (rightmost first), write, increment.
- `pop`: if empty return None; decrement `_n`, take `_A[_n]`, clear the cell, maybe halve, return.

Trace: append 5,6,7 → capacities 1 → 2 → 4. pop → size 2 (2 < 1? no). pop → size 1 (1 < 1? no) → capacity 4.
""",
        complexity="append/insert-at-end/pop: O(1) amortised, O(n) worst case for a resizing call. insert(k): O(n - k + 1) amortised. get/set/size/capacity: O(1). Space O(n) — capacity is always at most 4 times the size (after the first append).",
        pitfalls="Shifting left-to-right in insert overwrites values. Halving when size < cap/2 instead of cap/4 causes thrashing. Forgetting to keep capacity at least 1.",
        follow_up="Prove with cyber-dollars that any mix of n appends and pops costs O(n) under this policy.",
    ),
),
dict(
    id="dsaf-insertion-sort",
    title="Insertion Sort and Counting Shifts",
    difficulty="Easy",
    pattern="Array-Based Sequences",
    entry="insertion_sort",
    description=r"""
Sort the list `A` **in place** into nondecreasing order using insertion sort (Goodrich ch. 5.5.2),
and **return the number of element shifts** performed — i.e. how many times an element was moved one
cell to the right to make room. (This equals the number of inversions in the input.)

Only shift elements strictly greater than the current value, so the sort is stable.

**Example:** `A = [5, 2, 4, 6, 1, 3]` → `9` (and `A` becomes `[1, 2, 3, 4, 5, 6]`)

**Example:** `A = [1, 2, 3]` → `0`
""",
    starter='''def insertion_sort(A):
    shifts = 0
    # sort A in place
    return shifts
''',
    solution='''def insertion_sort(A):
    shifts = 0
    for k in range(1, len(A)):
        cur = A[k]
        j = k
        while j > 0 and A[j - 1] > cur:
            A[j] = A[j - 1]
            j -= 1
            shifts += 1
        A[j] = cur
    return shifts
''',
    tests=[
        [[5, 2, 4, 6, 1, 3]],
        [[1, 2, 3]],
        [[]],
        [[42]],
        [[3, 2, 1]],
        [[2, 2, 2, 1]],
        [[1, 3, 2, 3, 1]],
        [[-1, -5, 0, -5]],
        [list(range(300, 0, -1))],
        [[_r.randint(0, 50) for _ in range(500)]],
        [list(range(1000)) + [-1]],
    ],
    examples=2,
    wrong_solutions=[
        '''def insertion_sort(A):
    shifts = 0
    for k in range(1, len(A)):
        cur = A[k]
        j = k
        while j > 0 and A[j - 1] >= cur:
            A[j] = A[j - 1]
            j -= 1
            shifts += 1
        A[j] = cur
    return shifts
''',
        '''def insertion_sort(A):
    A.sort()
    return 0
''',
    ],
    guide=dict(
        prereqs="Lesson *Using arrays* (insertion sort).",
        intuition="Grow a sorted prefix. Take the next element and slide it left past every larger element — each slide is one shift and fixes exactly one inversion.",
        hints=["Save `cur = A[k]` before shifting overwrites it.",
               "Loop while `j > 0 and A[j-1] > cur`: move A[j-1] to A[j].",
               "Count inside the while loop; place cur at A[j] afterwards."],
        brute_force="Counting inversions by checking all pairs is O(n^2) and does not sort. Merge sort can count inversions in O(n log n) (see the sorting module).",
        approach="""
For k = 1..n-1: `cur = A[k]`, `j = k`; while `j > 0 and A[j-1] > cur`: shift, decrement j, count. Then `A[j] = cur`.

Dry run `[5,2,4,6,1,3]`: shifts per k = 1,1,0,4,3 → 9.
""",
        complexity="Time O(n + I) where I is the number of inversions: O(n) for sorted input, O(n^2) worst case (reverse order). Space O(1).",
        pitfalls="Using `>=` moves equal elements (unstable, and counts too many shifts). Forgetting to save `cur`.",
        follow_up="Binary insertion sort finds the spot with binary search (fewer comparisons) but still O(n^2) shifts.",
    ),
),
dict(
    id="dsaf-caesar-cipher",
    title="Caesar Cipher",
    difficulty="Easy",
    pattern="Array-Based Sequences",
    entry="caesar",
    description=r"""
Implement the Caesar cipher (Goodrich ch. 5.5.3). `caesar(message, shift, mode)` returns the
transformed string, where `mode` is `"encrypt"` or `"decrypt"`.

- Each **letter** is rotated by `shift` positions through the alphabet (encrypt) or back (decrypt),
  wrapping around: with shift 3, `A→D`, `X→A`.
- **Case is preserved**: uppercase letters stay uppercase, lowercase stay lowercase.
- Any other character (digits, spaces, punctuation) is unchanged.
- `shift` may be any integer, including negative or larger than 26.

**Example:** `"THE EAGLE IS IN PLAY; MEET AT JOE'S.", 3, "encrypt"` → `"WKH HDJOH LV LQ SODB; PHHW DW MRH'V."`

**Example:** `"Khoor, Zruog!", 3, "decrypt"` → `"Hello, World!"`
""",
    starter='''def caesar(message, shift, mode):
    pass
''',
    solution='''def caesar(message, shift, mode):
    if mode == "decrypt":
        shift = -shift
    out = []
    for c in message:
        if 'A' <= c <= 'Z':
            out.append(chr((ord(c) - 65 + shift) % 26 + 65))
        elif 'a' <= c <= 'z':
            out.append(chr((ord(c) - 97 + shift) % 26 + 97))
        else:
            out.append(c)
    return ''.join(out)
''',
    tests=[
        ["THE EAGLE IS IN PLAY; MEET AT JOE'S.", 3, "encrypt"],
        ["Khoor, Zruog!", 3, "decrypt"],
        ["", 5, "encrypt"],
        ["xyz XYZ", 3, "encrypt"],
        ["abc", -1, "encrypt"],
        ["Hello", 26, "encrypt"],
        ["Hello", 52 + 1, "encrypt"],
        ["Ifmmp", 27, "decrypt"],
        ["123 !?", 10, "encrypt"],
        ["The quick brown fox jumps over the lazy dog", 13, "encrypt"],
        ["Gur dhvpx oebja sbk whzcf bire gur ynml qbt", 13, "decrypt"],
        ["MixedCase Zz Aa", -27, "decrypt"],
    ],
    examples=2,
    wrong_solutions=[
        '''def caesar(message, shift, mode):
    if mode == "decrypt":
        shift = -shift
    return ''.join(chr((ord(c) - 65 + shift) % 26 + 65) if c.isalpha() else c for c in message.upper())
''',
        '''def caesar(message, shift, mode):
    if mode == "decrypt":
        shift = -shift
    return ''.join(chr(ord(c) + shift) if c.isalpha() else c for c in message)
''',
    ],
    guide=dict(
        prereqs="Lesson *Using arrays* (Caesar cipher), `ord`/`chr`, the `%` operator.",
        intuition="Map a letter to 0..25, add the shift modulo 26, map back. Decryption is encryption with the negated shift.",
        hints=["`ord(c) - ord('A')` gives 0..25 for uppercase.",
               "Python's `%` with a positive modulus is always non-negative, even for negative left operands.",
               "Build a list of characters and `''.join` once."],
        brute_force="A big if/elif table per letter works but is error-prone; the arithmetic version is shorter and handles any shift.",
        approach="""
Negate the shift for decryption. For each character: uppercase → `chr((ord(c)-65+shift) % 26 + 65)`; lowercase → same with 97; else unchanged. Join.
""",
        complexity="Time O(n), space O(n) for the output.",
        pitfalls="Forgetting wrap-around (`chr(ord(c)+shift)` produces non-letters); upper-casing the whole message; repeated string `+=` (quadratic in the worst case).",
        follow_up="Break an unknown shift with letter-frequency analysis; generalise to the Vigenere cipher (a different shift per position).",
    ),
),
# ---------------------------------------------------------------- stacks & queues
dict(
    id="dsaf-array-stack",
    title="Array-Based Stack",
    difficulty="Easy",
    pattern="Stacks, Queues and Deques",
    kind="class",
    entry="ArrayStack",
    description=r"""
Implement the stack ADT (Goodrich ch. 6.1) as an adapter over a Python list:

- `push(e)` — add `e` on top.
- `pop()` — remove and return the top element, or `None` if the stack is empty.
- `top()` — return the top element without removing it, or `None` if empty.
- `is_empty()` — `True` iff there are no elements.
- `size()` — number of elements.

All operations must be $O(1)$ (amortised for push/pop).

**Example:** `["ArrayStack","push","push","size","pop","is_empty","pop","is_empty","pop"]`,
`[[],[5],[3],[],[],[],[],[],[]]` → `[None,None,None,2,3,false,5,true,null]`
""",
    starter='''class ArrayStack:
    def __init__(self):
        pass

    def push(self, e):
        pass

    def pop(self):
        pass

    def top(self):
        pass

    def is_empty(self):
        pass

    def size(self):
        pass
''',
    solution='''class ArrayStack:
    def __init__(self):
        self._data = []

    def push(self, e):
        self._data.append(e)

    def pop(self):
        return self._data.pop() if self._data else None

    def top(self):
        return self._data[-1] if self._data else None

    def is_empty(self):
        return not self._data

    def size(self):
        return len(self._data)
''',
    tests=[
        [["ArrayStack", "push", "push", "size", "pop", "is_empty", "pop", "is_empty", "pop"],
         [[], [5], [3], [], [], [], [], [], []]],
        [["ArrayStack", "pop", "top", "is_empty", "size"], [[], [], [], [], []]],
        [["ArrayStack", "push", "push", "push", "top", "pop", "push", "push", "top", "pop", "pop", "top"],
         [[], [7], [9], [4], [], [], [6], [8], [], [], [], []]],
        [["ArrayStack", "push", "top", "top", "size"], [[], ["x"], [], [], []]],
        [["ArrayStack", "push", "push", "pop", "pop", "push", "top", "size"], [[], [1], [2], [], [], [3], [], []]],
        [["ArrayStack"] + ["push"] * 50 + ["size"] + ["pop"] * 3 + ["top"],
         [[]] + [[i] for i in range(50)] + [[]] + [[]] * 3 + [[]]],
        [["ArrayStack", "push", "push", "push", "pop", "pop", "pop", "pop", "is_empty"],
         [[], [None], [0], [False], [], [], [], [], []]],
        [["ArrayStack"] + ["push"] * 4000 + ["pop"] * 3999 + ["top", "size"],
         [[]] + [[i] for i in range(4000)] + [[]] * 3999 + [[], []]],
    ],
    examples=2,
    wrong_solutions=[
        '''class ArrayStack:
    def __init__(self):
        self._data = []
    def push(self, e):
        self._data.insert(0, e)
    def pop(self):
        return self._data.pop() if self._data else None
    def top(self):
        return self._data[-1] if self._data else None
    def is_empty(self):
        return not self._data
    def size(self):
        return len(self._data)
''',
    ],
    guide=dict(
        prereqs="Lesson *Stacks and their applications* (adapter pattern).",
        intuition="The end of a Python list supports append and pop in O(1) amortised time, so make it the top.",
        hints=["push = append, pop = list.pop(), top = data[-1].",
               "Check emptiness before pop/top and return None.",
               "Do not use insert(0)/pop(0): that's O(n) and also the wrong end if mixed with pop()."],
        brute_force="Keeping the top at index 0 (insert(0, e) / pop(0)) is correct LIFO but O(n) per operation.",
        approach="Wrap a list `_data`. Each method is one line, guarded by an emptiness check where needed.",
        complexity="push/pop O(1) amortised (dynamic array resizing), top/is_empty/size O(1). Space O(n).",
        pitfalls="Returning `self._data[-1]` on an empty list raises IndexError; mixing ends (push at front, pop at back) silently makes a queue.",
        follow_up="Add `get_min()` in O(1) by storing (value, min_so_far) pairs; implement the stack with a singly linked list for worst-case O(1).",
    ),
),
dict(
    id="dsaf-circular-queue",
    title="Fixed-Capacity Circular Queue",
    difficulty="Medium",
    pattern="Stacks, Queues and Deques",
    kind="class",
    entry="CircularQueue",
    description=r"""
Implement a bounded FIFO queue in a **fixed-size circular array** (Goodrich ch. 6.2.2). Do not resize
and do not use `list.pop(0)`, `insert`, or `collections.deque` — use a front index and modular
arithmetic.

- `CircularQueue(k)` — capacity `k >= 1`.
- `enqueue(x)` → `True` if added at the back, `False` if the queue is full.
- `dequeue()` → remove and return the front element, or `None` if empty.
- `first()` / `last()` → peek at the front / back element, or `None` if empty.
- `is_empty()`, `is_full()`, `size()`.

Every operation must be $O(1)$ worst case.

**Example:** `["CircularQueue","enqueue","enqueue","enqueue","enqueue","last","is_full","dequeue","enqueue","last"]`,
`[[3],[1],[2],[3],[4],[],[],[],[4],[]]` → `[null,true,true,true,false,3,true,1,true,4]`
""",
    starter='''class CircularQueue:
    def __init__(self, k):
        self._data = [None] * k
        self._front = 0
        self._size = 0

    def enqueue(self, x):
        pass

    def dequeue(self):
        pass

    def first(self):
        pass

    def last(self):
        pass

    def is_empty(self):
        pass

    def is_full(self):
        pass

    def size(self):
        pass
''',
    solution='''class CircularQueue:
    def __init__(self, k):
        self._data = [None] * k
        self._front = 0
        self._size = 0

    def enqueue(self, x):
        if self._size == len(self._data):
            return False
        avail = (self._front + self._size) % len(self._data)
        self._data[avail] = x
        self._size += 1
        return True

    def dequeue(self):
        if self._size == 0:
            return None
        x = self._data[self._front]
        self._data[self._front] = None
        self._front = (self._front + 1) % len(self._data)
        self._size -= 1
        return x

    def first(self):
        return None if self._size == 0 else self._data[self._front]

    def last(self):
        if self._size == 0:
            return None
        return self._data[(self._front + self._size - 1) % len(self._data)]

    def is_empty(self):
        return self._size == 0

    def is_full(self):
        return self._size == len(self._data)

    def size(self):
        return self._size
''',
    tests=[
        [["CircularQueue", "enqueue", "enqueue", "enqueue", "enqueue", "last", "is_full", "dequeue", "enqueue", "last"],
         [[3], [1], [2], [3], [4], [], [], [], [4], []]],
        [["CircularQueue", "dequeue", "first", "last", "is_empty", "is_full", "size"], [[2], [], [], [], [], [], []]],
        [["CircularQueue", "enqueue", "is_full", "enqueue", "dequeue", "is_empty", "enqueue", "first", "last"],
         [[1], [10], [], [11], [], [], [12], [], []]],
        [["CircularQueue", "enqueue", "enqueue", "dequeue", "enqueue", "enqueue", "dequeue", "enqueue", "first", "last", "size"],
         [[3], [1], [2], [], [3], [4], [], [5], [], [], []]],
        [["CircularQueue"] + ["enqueue", "dequeue"] * 25 + ["is_empty", "enqueue", "first", "last"],
         [[4]] + [[7], []] * 25 + [[], [99], [], []]],
        [["CircularQueue", "enqueue", "enqueue", "enqueue", "dequeue", "dequeue", "enqueue", "enqueue", "enqueue", "is_full", "dequeue", "dequeue", "dequeue", "dequeue", "dequeue"],
         [[4], [1], [2], [3], [], [], [4], [5], [6], [], [], [], [], [], []]],
        [["CircularQueue", "enqueue", "enqueue", "dequeue", "dequeue", "dequeue", "enqueue", "size", "first"],
         [[2], ["a"], ["b"], [], [], [], ["c"], [], []]],
        [["CircularQueue"] + ["enqueue"] * 6 + ["size", "last"] + ["dequeue"] * 2 + ["enqueue"] * 3 + ["first", "last", "size"],
         [[5]] + [[i] for i in range(6)] + [[], []] + [[]] * 2 + [[10], [11], [12]] + [[], [], []]],
        [["CircularQueue"] + ["enqueue"] * 1000 + ["dequeue"] * 500 + ["enqueue"] * 600 + ["first", "last", "size", "is_full"],
         [[1000]] + [[i] for i in range(1000)] + [[]] * 500 + [[i] for i in range(1000, 1600)] + [[], [], [], []]],
    ],
    examples=2,
    wrong_solutions=[
        '''class CircularQueue:
    def __init__(self, k):
        self._data = [None] * k
        self._front = 0
        self._size = 0
    def enqueue(self, x):
        if self._size == len(self._data):
            return False
        self._data[self._front + self._size] = x if self._front + self._size < len(self._data) else None
        self._size += 1
        return True
    def dequeue(self):
        if self._size == 0:
            return None
        x = self._data[self._front]
        self._front += 1
        self._size -= 1
        return x
    def first(self):
        return None if self._size == 0 else self._data[self._front]
    def last(self):
        return None if self._size == 0 else self._data[self._front + self._size - 1]
    def is_empty(self):
        return self._size == 0
    def is_full(self):
        return self._size == len(self._data)
    def size(self):
        return self._size
''',
        '''class CircularQueue:
    def __init__(self, k):
        self._data = [None] * k
        self._front = 0
        self._size = 0
    def enqueue(self, x):
        if self._size == len(self._data):
            return False
        self._data[(self._front + self._size) % len(self._data)] = x
        self._size += 1
        return True
    def dequeue(self):
        if self._size == 0:
            return None
        x = self._data[self._front]
        self._front = (self._front + 1) % len(self._data)
        self._size -= 1
        return x
    def first(self):
        return None if self._size == 0 else self._data[self._front]
    def last(self):
        return None if self._size == 0 else self._data[(self._front + self._size) % len(self._data)]
    def is_empty(self):
        return self._size == 0
    def is_full(self):
        return self._size == len(self._data)
    def size(self):
        return self._size
''',
    ],
    guide=dict(
        prereqs="Lesson *Queues, circular arrays and deques*.",
        intuition="Treat the array as a ring: the front index moves forward on dequeue, and the next free slot is `(front + size) % capacity`.",
        hints=["Keep `front` and `size`; derive the back from them.",
               "enqueue writes at (front + size) % N; dequeue advances front = (front + 1) % N.",
               "The last element is at (front + size - 1) % N."],
        brute_force="A list with append/pop(0) is O(n) per dequeue; an ever-growing list with a moving front wastes unbounded memory.",
        approach="""
Store `_data` (length N), `_front`, `_size`.
- enqueue: if full return False; write at `(front+size)%N`; size += 1.
- dequeue: if empty None; read `data[front]`, clear it, `front = (front+1)%N`, size -= 1.

Trace with N = 3: enqueue 1,2,3 (full) → dequeue returns 1, front = 1 → enqueue 4 goes to (1+2)%3 = 0 → last = data[(1+3-1)%3] = data[0] = 4.
""",
        complexity="Every operation O(1) worst case, O(k) space — no resizing, no shifting.",
        pitfalls="Forgetting `% N` (index out of range after wrap-around); computing `last` as `(front+size)%N` (off by one); confusing full and empty if you track only front/back indices.",
        follow_up="Add resizing (copy in queue order to a new array of double size, resetting front to 0) to get the book's unbounded ArrayQueue.",
    ),
),
# ---------------------------------------------------------------- linked lists
dict(
    id="dsaf-linked-deque",
    title="Doubly Linked Deque with Sentinels",
    difficulty="Medium",
    pattern="Linked Lists",
    kind="class",
    entry="LinkedDeque",
    description=r"""
Implement a deque using a **doubly linked list with header and trailer sentinels** (Goodrich ch. 7.3).
Do not use a Python list or `collections.deque` for storage.

- `add_first(e)`, `add_last(e)`
- `delete_first()`, `delete_last()` → remove and return the element, or `None` if empty
- `first()`, `last()` → peek, or `None` if empty
- `size()`
- `to_list()` → the elements from front to back as a Python list (for checking)

All operations except `to_list` must be $O(1)$ worst case.

**Example:** `["LinkedDeque","add_last","add_first","add_first","add_last","to_list","delete_last","delete_first","to_list"]`,
`[[],[5],[3],[7],[9],[],[],[],[]]` → `[null,null,null,null,null,[7,3,5,9],9,7,[3,5]]`
""",
    starter='''class _Node:
    __slots__ = "elem", "prev", "next"
    def __init__(self, elem, prev, next):
        self.elem, self.prev, self.next = elem, prev, next


class LinkedDeque:
    def __init__(self):
        self._header = _Node(None, None, None)
        self._trailer = _Node(None, None, None)
        self._header.next = self._trailer
        self._trailer.prev = self._header
        self._size = 0

    def add_first(self, e):
        pass

    def add_last(self, e):
        pass

    def delete_first(self):
        pass

    def delete_last(self):
        pass

    def first(self):
        pass

    def last(self):
        pass

    def size(self):
        pass

    def to_list(self):
        pass
''',
    solution='''class _Node:
    __slots__ = "elem", "prev", "next"
    def __init__(self, elem, prev, next):
        self.elem, self.prev, self.next = elem, prev, next


class LinkedDeque:
    def __init__(self):
        self._header = _Node(None, None, None)
        self._trailer = _Node(None, None, None)
        self._header.next = self._trailer
        self._trailer.prev = self._header
        self._size = 0

    def _insert_between(self, e, a, b):
        node = _Node(e, a, b)
        a.next = node
        b.prev = node
        self._size += 1

    def _delete(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev
        self._size -= 1
        e = node.elem
        node.prev = node.next = node.elem = None
        return e

    def add_first(self, e):
        self._insert_between(e, self._header, self._header.next)

    def add_last(self, e):
        self._insert_between(e, self._trailer.prev, self._trailer)

    def delete_first(self):
        return None if self._size == 0 else self._delete(self._header.next)

    def delete_last(self):
        return None if self._size == 0 else self._delete(self._trailer.prev)

    def first(self):
        return None if self._size == 0 else self._header.next.elem

    def last(self):
        return None if self._size == 0 else self._trailer.prev.elem

    def size(self):
        return self._size

    def to_list(self):
        out, walk = [], self._header.next
        while walk is not self._trailer:
            out.append(walk.elem)
            walk = walk.next
        return out
''',
    tests=[
        [["LinkedDeque", "add_last", "add_first", "add_first", "add_last", "to_list", "delete_last", "delete_first", "to_list"],
         [[], [5], [3], [7], [9], [], [], [], []]],
        [["LinkedDeque", "delete_first", "delete_last", "first", "last", "size", "to_list"], [[], [], [], [], [], [], []]],
        [["LinkedDeque", "add_first", "delete_last", "size", "add_last", "delete_first", "to_list"],
         [[], [1], [], [], [2], [], []]],
        [["LinkedDeque", "add_last", "add_last", "add_last", "first", "last", "delete_last", "last", "size"],
         [[], ["a"], ["b"], ["c"], [], [], [], [], []]],
        [["LinkedDeque", "add_first", "add_first", "add_first", "delete_first", "first", "to_list"],
         [[], [1], [2], [3], [], [], []]],
        [["LinkedDeque", "add_last", "delete_first", "delete_first", "add_first", "first", "last", "to_list"],
         [[], [1], [], [], [9], [], [], []]],
        [["LinkedDeque"] + ["add_first", "add_last"] * 10 + ["to_list", "size"],
         [[]] + [[i] if j % 2 == 0 else [-i] for i in range(10) for j in range(2)] + [[], []]],
        [["LinkedDeque"] + ["add_last"] * 5 + ["delete_last"] * 6 + ["to_list", "add_first", "to_list"],
         [[]] + [[i] for i in range(5)] + [[]] * 6 + [[], [42], []]],
        [["LinkedDeque"] + ["add_last"] * 3000 + ["delete_first"] * 2990 + ["to_list", "first", "last", "size"],
         [[]] + [[i] for i in range(3000)] + [[]] * 2990 + [[], [], [], []]],
    ],
    examples=2,
    wrong_solutions=[
        '''class _Node:
    __slots__ = "elem", "prev", "next"
    def __init__(self, elem, prev, next):
        self.elem, self.prev, self.next = elem, prev, next
class LinkedDeque:
    def __init__(self):
        self._header = _Node(None, None, None)
        self._trailer = _Node(None, None, None)
        self._header.next = self._trailer
        self._trailer.prev = self._header
        self._size = 0
    def add_first(self, e):
        n = _Node(e, self._header, self._header.next)
        self._header.next = n
        self._size += 1
    def add_last(self, e):
        n = _Node(e, self._trailer.prev, self._trailer)
        self._trailer.prev.next = n
        self._trailer.prev = n
        self._size += 1
    def delete_first(self):
        if self._size == 0: return None
        n = self._header.next
        self._header.next = n.next
        n.next.prev = self._header
        self._size -= 1
        return n.elem
    def delete_last(self):
        if self._size == 0: return None
        n = self._trailer.prev
        self._trailer.prev = n.prev
        n.prev.next = self._trailer
        self._size -= 1
        return n.elem
    def first(self):
        return None if self._size == 0 else self._header.next.elem
    def last(self):
        return None if self._size == 0 else self._trailer.prev.elem
    def size(self):
        return self._size
    def to_list(self):
        out, w = [], self._header.next
        while w is not self._trailer:
            out.append(w.elem); w = w.next
        return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Doubly linked lists and positional lists*.",
        intuition="With sentinels every real node always has a real neighbour on both sides, so every insertion is 'between two nodes' and every deletion is 'unlink a node with two neighbours' — no special cases.",
        hints=["Write `_insert_between(e, a, b)` and `_delete(node)` once; every public method is a one-liner on top.",
               "Insertion needs FOUR links: new.prev, new.next, a.next, b.prev.",
               "First real node: header.next; last real node: trailer.prev."],
        brute_force="A Python list gives O(n) add_first/delete_first; a singly linked list gives O(n) delete_last.",
        approach="""
- `add_first(e)` = insert between header and header.next.
- `add_last(e)` = insert between trailer.prev and trailer.
- `delete_first` / `delete_last` = `_delete(header.next)` / `_delete(trailer.prev)` when non-empty.
- `_delete(node)`: `node.prev.next = node.next; node.next.prev = node.prev`.
""",
        complexity="All deque operations O(1) worst case; to_list O(n). Space O(n) with 3 references per element.",
        pitfalls="Forgetting `b.prev = new` in insertion — forward traversal still looks right but backward links are broken (the wrong solution fails exactly this way when you later delete from the other end).",
        follow_up="Extend to a positional list with add_before/add_after/delete(p); build an LRU cache by adding a dict from key to node.",
    ),
),
dict(
    id="dsaf-move-to-front",
    title="Move-to-Front Access Cost",
    difficulty="Easy",
    pattern="Linked Lists",
    entry="move_to_front",
    description=r"""
Simulate the **move-to-front heuristic** (Goodrich ch. 7.6.2). The list initially holds `initial`
(front first, all distinct). For each element `x` in `accesses`:

- If `x` is at 1-based position `p`, the access costs `p`; then move `x` to the front.
- If `x` is not in the list, the access costs `len(list) + 1` (a full unsuccessful scan) and `x` is
  inserted at the front.

Return `[total_cost, final_list]`.

**Example:** `initial = ["a","b","c"], accesses = ["c","c","b","d"]` →
cost 3 (c at 3) + 1 (c at front) + 3 (b) + 4 (d new) = 11, final `["d","b","c","a"]` →
`[11, ["d","b","c","a"]]`
""",
    starter='''def move_to_front(initial, accesses):
    pass
''',
    solution='''def move_to_front(initial, accesses):
    L = list(initial)
    total = 0
    for x in accesses:
        if x in L:
            i = L.index(x)
            total += i + 1
            L.pop(i)
        else:
            total += len(L) + 1
        L.insert(0, x)
    return [total, L]
''',
    tests=[
        [["a", "b", "c"], ["c", "c", "b", "d"]],
        [[], ["x", "y", "x"]],
        [[1, 2, 3], []],
        [[1, 2, 3, 4], [4, 3, 2, 1]],
        [[1, 2, 3, 4], [1, 1, 1, 1]],
        [[1, 2, 3], [1, 2, 3, 1, 2, 3]],
        [[1, 2, 3], [3, 2, 1, 3, 2, 1]],
        [list(range(20)), [x for x in range(20) for _ in range(20)]],
        [list(range(30)), list(range(30)) * 5],
        [["q"], ["q", "r", "q", "r", "s"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def move_to_front(initial, accesses):
    L = list(initial)
    total = 0
    for x in accesses:
        if x in L:
            total += L.index(x) + 1
        else:
            total += len(L) + 1
            L.append(x)
    return [total, L]
''',
        '''def move_to_front(initial, accesses):
    L = list(initial)
    total = 0
    for x in accesses:
        if x in L:
            i = L.index(x)
            total += i
            L.pop(i)
        else:
            total += len(L)
        L.insert(0, x)
    return [total, L]
''',
    ],
    guide=dict(
        prereqs="Lesson *Access frequencies, move-to-front and link vs array*.",
        intuition="Recently used items migrate to the front, so repeated accesses become cheap; cyclic access patterns are the worst case.",
        hints=["Cost of finding x is its 1-based index.",
               "Remove x from its position, then insert it at index 0.",
               "Unknown elements cost a full scan (len + 1) and are inserted at the front."],
        brute_force="This direct simulation is fine here: O(n) per access with a Python list. A positional list makes the move O(1) once x is found; a dict from element to node would make the find O(1) too (though then the 'cost' is only a model).",
        approach="Copy `initial`; for each access compute its cost, remove it (if present), insert at the front; accumulate the total.",
        complexity="Time O(m n) for m accesses on a list of size n with Python lists (find + shift). Space O(n).",
        pitfalls="0-based cost; forgetting to move the element; appending new elements at the back instead of the front; mutating `initial`.",
        follow_up="Compare with a static order sorted by final frequency on the same sequences — MTF is within a factor of about 2 of the optimum (Sleator and Tarjan).",
    ),
),
]
