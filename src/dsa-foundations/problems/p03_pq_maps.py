import random as _r

_r.seed(23)


def _pq_ops(n, seed):
    rnd = _r.Random(seed)
    ops, args = ["HeapPriorityQueue"], [[]]
    size = 0
    for _ in range(n):
        x = rnd.random()
        if x < 0.55 or size == 0:
            ops.append("add"); args.append([rnd.randint(0, 40), rnd.randint(0, 99)]); size += 1
        elif x < 0.85:
            ops.append("remove_min"); args.append([]); size -= 1
        elif x < 0.95:
            ops.append("min"); args.append([])
        else:
            ops.append("size"); args.append([])
    for _ in range(size + 1):
        ops.append("remove_min"); args.append([])
    return [ops, args]


def _map_ops(n, seed, keyrange):
    rnd = _r.Random(seed)
    ops, args = ["ChainHashMap"], [[]]
    for _ in range(n):
        x = rnd.random()
        k = rnd.randint(-keyrange, keyrange)
        if x < 0.45:
            ops.append("put"); args.append([k, rnd.randint(0, 999)])
        elif x < 0.75:
            ops.append("get"); args.append([k])
        elif x < 0.92:
            ops.append("remove"); args.append([k])
        else:
            ops.append("size"); args.append([])
    return [ops, args]


PROBLEMS = [
dict(
    id="dsaf-heap-pq",
    title="Binary-Heap Priority Queue",
    difficulty="Medium",
    pattern="Priority Queues",
    kind="class",
    entry="HeapPriorityQueue",
    description=r"""
Implement a min-oriented priority queue with an **array-based binary heap** (Goodrich ch. 9.3).
Do not use `heapq`, `sorted`, `min` over the whole list, or `list.sort` — write up-heap and down-heap
bubbling yourself.

- `add(k, v)` — insert an entry with key `k` and value `v`.
- `min()` — return `[k, v]` for the smallest entry without removing it, or `None` if empty.
- `remove_min()` — remove and return `[k, v]` for the smallest entry, or `None` if empty.
- `size()`.

Entries are ordered by key; **ties are broken by the smaller value** (i.e. compare `(k, v)` pairs).

`add` and `remove_min` must be $O(\log n)$.

**Example:** `["HeapPriorityQueue","add","add","add","add","min","remove_min","remove_min","size"]`,
`[[],[5,"A"],[9,"C"],[3,"B"],[7,"D"],[],[],[],[]]` → `[null,null,null,null,null,[3,"B"],[3,"B"],[5,"A"],2]`
""",
    starter='''class HeapPriorityQueue:
    def __init__(self):
        self._data = []          # list of (key, value) tuples in heap order

    def add(self, k, v):
        pass

    def min(self):
        pass

    def remove_min(self):
        pass

    def size(self):
        pass
''',
    solution='''class HeapPriorityQueue:
    def __init__(self):
        self._data = []

    def _upheap(self, j):
        d = self._data
        while j > 0:
            p = (j - 1) // 2
            if d[j] < d[p]:
                d[j], d[p] = d[p], d[j]
                j = p
            else:
                break

    def _downheap(self, j):
        d = self._data
        n = len(d)
        while 2 * j + 1 < n:
            c = 2 * j + 1
            if c + 1 < n and d[c + 1] < d[c]:
                c += 1
            if d[c] < d[j]:
                d[j], d[c] = d[c], d[j]
                j = c
            else:
                break

    def add(self, k, v):
        self._data.append((k, v))
        self._upheap(len(self._data) - 1)

    def min(self):
        return list(self._data[0]) if self._data else None

    def remove_min(self):
        d = self._data
        if not d:
            return None
        d[0], d[-1] = d[-1], d[0]
        item = d.pop()
        self._downheap(0)
        return list(item)

    def size(self):
        return len(self._data)
''',
    tests=[
        [["HeapPriorityQueue", "add", "add", "add", "add", "min", "remove_min", "remove_min", "size"],
         [[], [5, "A"], [9, "C"], [3, "B"], [7, "D"], [], [], [], []]],
        [["HeapPriorityQueue", "min", "remove_min", "size"], [[], [], [], []]],
        [["HeapPriorityQueue", "add", "remove_min", "remove_min", "add", "min"], [[], [1, 1], [], [], [2, 2], []]],
        [["HeapPriorityQueue"] + ["add"] * 7 + ["remove_min"] * 7,
         [[]] + [[k, k * 10] for k in [4, 4, 1, 9, 1, 4, 0]] + [[]] * 7],
        [["HeapPriorityQueue"] + ["add"] * 4 + ["remove_min"] * 4,
         [[]] + [[2, "z"], [2, "a"], [2, "m"], [1, "q"]] + [[]] * 4],
        [["HeapPriorityQueue"] + ["add"] * 10 + ["remove_min"] * 10,
         [[]] + [[k, 0] for k in range(10, 0, -1)] + [[]] * 10],
        [["HeapPriorityQueue"] + ["add"] * 10 + ["remove_min"] * 10,
         [[]] + [[k, 0] for k in [1, 10, 2, 9, 3, 8, 4, 7, 5, 6]] + [[]] * 10],
        _pq_ops(60, 1),
        _pq_ops(300, 2),
        _pq_ops(2500, 3),
    ],
    examples=2,
    wrong_solutions=[
        '''class HeapPriorityQueue:
    def __init__(self):
        self._data = []
    def add(self, k, v):
        d = self._data
        d.append((k, v))
        j = len(d) - 1
        while j > 0 and d[j] < d[(j - 1) // 2]:
            d[j], d[(j - 1) // 2] = d[(j - 1) // 2], d[j]
            j = (j - 1) // 2
    def min(self):
        return list(self._data[0]) if self._data else None
    def remove_min(self):
        d = self._data
        if not d:
            return None
        d[0], d[-1] = d[-1], d[0]
        item = d.pop()
        j = 0
        while 2 * j + 1 < len(d):
            c = 2 * j + 1
            if d[c] < d[j]:
                d[j], d[c] = d[c], d[j]
                j = c
            else:
                break
        return list(item)
    def size(self):
        return len(self._data)
''',
        '''class HeapPriorityQueue:
    def __init__(self):
        self._data = []
    def add(self, k, v):
        self._data.append((k, v))
    def min(self):
        return list(self._data[0]) if self._data else None
    def remove_min(self):
        return list(self._data.pop(0)) if self._data else None
    def size(self):
        return len(self._data)
''',
    ],
    guide=dict(
        prereqs="Lesson *Priority queues and binary heaps*.",
        intuition="Keep a complete binary tree in an array where every parent is <= its children. Adding goes at the end and bubbles up; removing the min swaps the root with the last cell, pops it, and bubbles the new root down along the smaller child.",
        hints=["parent(j) = (j-1)//2, children 2j+1 and 2j+2.",
               "Store (k, v) tuples: Python compares tuples lexicographically, giving the tie-break for free.",
               "In down-heap, pick the SMALLER child before comparing with the parent."],
        brute_force="Unsorted list: add O(1), remove_min O(n). Sorted list: add O(n), remove_min O(1). Either makes n operations cost O(n^2).",
        approach="""
- `add`: append, then while j > 0 and data[j] < data[parent]: swap, j = parent.
- `remove_min`: swap data[0] with data[-1], pop, then sift down from 0.

Trace adds 5, 9, 3, 7: [5] → [5,9] → append 3 → swap with 5 → [3,9,5] → append 7 at index 3, parent 9 → swap → [3,7,5,9].
""",
        complexity="add and remove_min O(log n) (the heap's height is floor(log2 n)); min and size O(1). Space O(n).",
        pitfalls="Always swapping with the left child (the first wrong solution) breaks heap order when the right child is smaller; forgetting the empty case; returning tuples vs lists is fine (normalised), but return None when empty.",
        follow_up="Add bottom-up construction from a list in O(n); add locators for update/remove (adaptable PQ).",
    ),
),
dict(
    id="dsaf-heap-sort",
    title="In-Place Heap-Sort",
    difficulty="Medium",
    pattern="Priority Queues",
    entry="heap_sort",
    inplace_arg=0,
    description=r"""
Sort the list `A` **in place** into nondecreasing order using heap-sort (Goodrich ch. 9.4.2):

1. rearrange `A` into a **max-heap** (bottom-up construction is $O(n)$);
2. repeatedly swap the maximum `A[0]` with the last cell of the heap region, shrink the region by
   one, and restore the heap with down-heap bubbling.

Use $O(1)$ extra space — no second list, no `sorted`, no `heapq`. The function returns nothing; the
grader inspects `A`.

**Example:** `A = [7, 4, 8, 2, 5, 3]` → `A` becomes `[2, 3, 4, 5, 7, 8]`
""",
    starter='''def heap_sort(A):
    pass
''',
    solution='''def heap_sort(A):
    n = len(A)

    def down(j, size):
        while 2 * j + 1 < size:
            c = 2 * j + 1
            if c + 1 < size and A[c + 1] > A[c]:
                c += 1
            if A[c] > A[j]:
                A[j], A[c] = A[c], A[j]
                j = c
            else:
                break

    for j in range(n // 2 - 1, -1, -1):
        down(j, n)
    for end in range(n - 1, 0, -1):
        A[0], A[end] = A[end], A[0]
        down(0, end)
''',
    tests=[
        [[7, 4, 8, 2, 5, 3]],
        [[]],
        [[1]],
        [[2, 1]],
        [[1, 2, 3, 4, 5]],
        [[5, 4, 3, 2, 1]],
        [[3, 3, 3, 3]],
        [[0, -1, 5, -7, 2, 2, -1]],
        [[_r.randint(-100, 100) for _ in range(200)]],
        [[_r.randint(0, 10**6) for _ in range(5000)]],
        [[1, 3, 2, 7, 5, 4, 6, 9, 8, 0, 11, 10]],
    ],
    examples=2,
    wrong_solutions=[
        '''def heap_sort(A):
    n = len(A)
    def down(j, size):
        while 2 * j + 1 < size:
            c = 2 * j + 1
            if c + 1 < size and A[c + 1] < A[c]:
                c += 1
            if A[c] < A[j]:
                A[j], A[c] = A[c], A[j]
                j = c
            else:
                break
    for j in range(n // 2 - 1, -1, -1):
        down(j, n)
''',
        '''def heap_sort(A):
    n = len(A)
    def down(j, size):
        while 2 * j + 1 < size:
            c = 2 * j + 1
            if A[c] > A[j]:
                A[j], A[c] = A[c], A[j]
                j = c
            else:
                break
    for j in range(n // 2 - 1, -1, -1):
        down(j, n)
    for end in range(n - 1, 0, -1):
        A[0], A[end] = A[end], A[0]
        down(0, end)
''',
        '''def heap_sort(A):
    return sorted(A)
''',
    ],
    guide=dict(
        prereqs="Lessons *Priority queues and binary heaps* (down-heap, bottom-up construction) and *PQ sorting, heap-sort and adaptable priority queues*.",
        intuition="A max-heap keeps the largest element at index 0. Swap it to the end, where it belongs, and repair the smaller heap. The array is split into a heap prefix and a sorted suffix.",
        hints=["Write `down(j, size)` that sifts within A[0:size] toward the LARGER child.",
               "Heapify: for j from n//2 - 1 down to 0: down(j, n).",
               "Extraction: for end from n-1 down to 1: swap A[0], A[end]; down(0, end)."],
        brute_force="Selection sort also grows a sorted suffix by finding the maximum each round, but by scanning: O(n^2). The heap finds each maximum in O(log n).",
        approach="""
Dry run `[7,4,8,2,5,3]`: heapify → `[8,5,7,2,4,3]`. Then: swap 8↔3 → sift → `[7,5,3,2,4 | 8]`; swap 7↔4 → `[5,4,3,2 | 7,8]`; swap 5↔2 → `[4,2,3 | 5,7,8]`; swap 4↔3 → `[3,2 | 4,5,7,8]`; swap → `[2,3,4,5,7,8]`.
""",
        complexity="Time O(n log n) in the worst case: O(n) to heapify plus n - 1 sift-downs of O(log n). Extra space O(1). Not stable.",
        pitfalls="Using a min-heap (sorts descending / leaves just a heap); passing the full length to `down` during extraction (pulls sorted elements back into the heap); comparing only with the left child; returning a new list instead of mutating A.",
        follow_up="Why is heap-sort not stable? Construct a 3-element counterexample with equal keys.",
    ),
),
dict(
    id="dsaf-chain-hashmap",
    title="Hash Map with Separate Chaining",
    difficulty="Medium",
    pattern="Maps and Hash Tables",
    kind="class",
    entry="ChainHashMap",
    description=r"""
Implement a map from integer keys to values using a **hash table with separate chaining**
(Goodrich ch. 10.2). Do not use Python's `dict` or `set`.

- `put(k, v)` — insert the pair, or overwrite the value if `k` is already present.
- `get(k)` — return the value for `k`, or `-1` if absent.
- `remove(k)` — delete `k` if present; return `True` if something was removed, else `False`.
- `size()` — number of stored keys.

Requirements: keep an array of buckets (each a small list of `[key, value]` pairs), compress the key
with `k % N` (or a MAD function), and **rehash into a table of about double the size when the load
factor $n/N$ exceeds 0.5** (or another constant), so operations stay expected $O(1)$.

Keys may be negative. Values are in `[0, 999]`.

**Example:** `["ChainHashMap","put","put","get","get","put","get","remove","get","size"]`,
`[[],[1,10],[2,20],[1],[3],[2,25],[2],[2],[2],[]]` → `[null,null,null,10,-1,null,25,true,-1,1]`
""",
    starter='''class ChainHashMap:
    def __init__(self, cap=11):
        self._table = [None] * cap     # each slot: None or a list of [key, value]
        self._n = 0

    def put(self, k, v):
        pass

    def get(self, k):
        pass

    def remove(self, k):
        pass

    def size(self):
        pass
''',
    solution='''class ChainHashMap:
    def __init__(self, cap=11):
        self._table = [None] * cap
        self._n = 0

    def _bucket(self, k):
        return k % len(self._table)

    def _resize(self, cap):
        old = self._table
        self._table = [None] * cap
        self._n = 0
        for bucket in old:
            if bucket:
                for k, v in bucket:
                    self.put(k, v)

    def put(self, k, v):
        j = self._bucket(k)
        if self._table[j] is None:
            self._table[j] = []
        for item in self._table[j]:
            if item[0] == k:
                item[1] = v
                return
        self._table[j].append([k, v])
        self._n += 1
        if self._n > len(self._table) // 2:
            self._resize(2 * len(self._table) - 1)

    def get(self, k):
        bucket = self._table[self._bucket(k)]
        if bucket:
            for item in bucket:
                if item[0] == k:
                    return item[1]
        return -1

    def remove(self, k):
        bucket = self._table[self._bucket(k)]
        if bucket:
            for i, item in enumerate(bucket):
                if item[0] == k:
                    bucket.pop(i)
                    self._n -= 1
                    return True
        return False

    def size(self):
        return self._n
''',
    tests=[
        [["ChainHashMap", "put", "put", "get", "get", "put", "get", "remove", "get", "size"],
         [[], [1, 10], [2, 20], [1], [3], [2, 25], [2], [2], [2], []]],
        [["ChainHashMap", "get", "remove", "size"], [[], [5], [5], []]],
        [["ChainHashMap", "put", "put", "put", "get", "get", "get", "size"],
         [[], [0, 1], [11, 2], [22, 3], [0], [11], [22], []]],
        [["ChainHashMap", "put", "put", "remove", "get", "get", "remove", "size"],
         [[], [3, 30], [14, 40], [3], [3], [14], [3], []]],
        [["ChainHashMap", "put", "put", "get", "get", "remove", "remove", "size"],
         [[], [-1, 5], [-12, 6], [-1], [-12], [-1], [-1], []]],
        [["ChainHashMap", "put", "put", "put", "size", "get"], [[], [7, 1], [7, 2], [7, 3], [], [7]]],
        [["ChainHashMap"] + ["put"] * 100 + ["size"] + ["get"] * 5 + ["remove"] * 50 + ["size", "get", "get"],
         [[]] + [[i * 7, i] for i in range(100)] + [[]] + [[0], [7], [693], [700], [3]]
         + [[i * 14] for i in range(50)] + [[], [14], [21]]],
        _map_ops(200, 5, 12),
        _map_ops(1500, 6, 200),
        _map_ops(6000, 7, 100000),
    ],
    examples=2,
    wrong_solutions=[
        '''class ChainHashMap:
    def __init__(self, cap=11):
        self._table = [None] * cap
        self._n = 0
    def put(self, k, v):
        j = k % len(self._table)
        if self._table[j] is None:
            self._n += 1
        self._table[j] = [k, v]
    def get(self, k):
        item = self._table[k % len(self._table)]
        return item[1] if item and item[0] == k else -1
    def remove(self, k):
        j = k % len(self._table)
        item = self._table[j]
        if item and item[0] == k:
            self._table[j] = None
            self._n -= 1
            return True
        return False
    def size(self):
        return self._n
''',
        '''class ChainHashMap:
    def __init__(self, cap=11):
        self._table = [[] for _ in range(cap)]
        self._n = 0
    def put(self, k, v):
        self._table[k % len(self._table)].append([k, v])
        self._n += 1
    def get(self, k):
        for item in self._table[k % len(self._table)]:
            if item[0] == k:
                return item[1]
        return -1
    def remove(self, k):
        b = self._table[k % len(self._table)]
        for i, item in enumerate(b):
            if item[0] == k:
                b.pop(i)
                self._n -= 1
                return True
        return False
    def size(self):
        return self._n
''',
    ],
    guide=dict(
        prereqs="Lessons *Maps and hash functions* and *Collision handling, load factors and rehashing*.",
        intuition="A hash function sends each key to one of N buckets; colliding keys share a bucket, which is just a tiny unsorted list. If the table grows with the number of keys, buckets stay O(1) long on average.",
        hints=["bucket index = k % N — Python's % is non-negative for negative k.",
               "put must first scan the bucket for an existing key and overwrite its value.",
               "After inserting a NEW key, if n > N/2 build a table of size about 2N and re-insert every pair (indices change because N changed)."],
        brute_force="One unsorted list of pairs: every operation is O(n).",
        approach="""
- `put`: find bucket; scan for k (update in place) else append and count; maybe resize.
- `get`: scan the bucket.
- `remove`: scan, pop the pair, decrement.
- `_resize(cap)`: save the old table, allocate a new one, reset n, re-put everything.

With N = 11: keys 0, 11, 22 all land in bucket 0 — a chain of three; lookups still work by comparing keys.
""",
        complexity="Expected O(1) per operation with a good hash and bounded load factor (O(1 + n/N) per bucket scan); worst case O(n) if every key collides. Rehashing is O(n) but amortised O(1) per insertion. Space O(n + N).",
        pitfalls="Overwriting a bucket on collision (first wrong solution); appending duplicates instead of updating (second wrong solution: size and get go wrong); forgetting that indices must be recomputed when N changes; shrinking is optional.",
        follow_up="Re-implement with open addressing (linear probing) — deletion then needs a special AVAILABLE marker.",
    ),
),
]
