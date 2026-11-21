"""DSA in JavaScript: Heap / Priority Queue and Graph problems."""
import random


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


HEAP = r'''class Heap {
  // less(a, b) === true means a should come out before b
  constructor(less) { this.a = []; this.less = less; }
  get size() { return this.a.length; }
  peek() { return this.a[0]; }
  push(x) {
    const a = this.a;
    a.push(x);
    let i = a.length - 1;
    while (i > 0) {                                // sift up
      const p = (i - 1) >> 1;
      if (!this.less(a[i], a[p])) break;
      [a[i], a[p]] = [a[p], a[i]];
      i = p;
    }
  }
  pop() {
    const a = this.a, top = a[0], last = a.pop();
    if (a.length) {
      a[0] = last;
      let i = 0;
      for (;;) {                                   // sift down
        const l = 2 * i + 1, r = l + 1;
        let m = i;
        if (l < a.length && this.less(a[l], a[m])) m = l;
        if (r < a.length && this.less(a[r], a[m])) m = r;
        if (m === i) break;
        [a[i], a[m]] = [a[m], a[i]];
        i = m;
      }
    }
    return top;
  }
}
'''

KTH_DRIVER = r'''
// --- driver used by the tests (provided, do not change) ---
function runKthLargest(ops, args) {
  let obj = null;
  const out = [];
  for (let i = 0; i < ops.length; i++) {
    if (ops[i] === "KthLargest") { obj = new KthLargest(...args[i]); out.push(null); }
    else { const r = obj[ops[i]](...args[i]); out.push(r === undefined ? null : r); }
  }
  return out;
}
'''

MEDIAN_DRIVER = r'''
// --- driver used by the tests (provided, do not change) ---
function runMedianFinder(ops, args) {
  let obj = null;
  const out = [];
  for (let i = 0; i < ops.length; i++) {
    if (ops[i] === "MedianFinder") { obj = new MedianFinder(); out.push(null); }
    else { const r = obj[ops[i]](...args[i]); out.push(r === undefined ? null : r); }
  }
  return out;
}
'''

r = random.Random(57)


def kth_case(k, init, adds, seed):
    rr = random.Random(seed)
    ops, args = ["KthLargest"], [[k, init]]
    for _ in range(adds):
        ops.append("add"); args.append([rr.randint(-10**4, 10**4)])
    return [ops, args]


def median_case(n, seed):
    rr = random.Random(seed)
    ops, args = ["MedianFinder"], [[]]
    for _ in range(n):
        if rr.random() < 0.6 or len(ops) == 1:
            ops.append("addNum"); args.append([rr.randint(-10**5, 10**5)])
        else:
            ops.append("findMedian"); args.append([])
    ops.append("findMedian"); args.append([])
    return [ops, args]


def unique_points(n, k, seed):
    rr = random.Random(seed)
    pts, seen = [], set()
    while len(pts) < n:
        p = (rr.randint(-1000, 1000), rr.randint(-1000, 1000))
        d = p[0] ** 2 + p[1] ** 2
        if d in seen:
            continue
        seen.add(d); pts.append(list(p))
    return [pts, k]


def island_grid(rows, cols, p, seed):
    rr = random.Random(seed)
    return [["1" if rr.random() < p else "0" for _ in range(cols)] for _ in range(rows)]


def orange_grid(rows, cols, seed):
    rr = random.Random(seed)
    g = [[1 if rr.random() < 0.85 else 0 for _ in range(cols)] for _ in range(rows)]
    g[0][0] = 2
    return g


def dag_prereqs(n, m, seed):
    rr = random.Random(seed)
    order = list(range(n)); rr.shuffle(order)
    pos = {v: i for i, v in enumerate(order)}
    edges = set()
    while len(edges) < m:
        a, b = rr.sample(range(n), 2)
        if pos[a] > pos[b]:
            edges.add((a, b))   # a requires b, b comes earlier
    return [n, [list(e) for e in sorted(edges)]]


def tree_plus_edge(n, seed):
    rr = random.Random(seed)
    edges = []
    for v in range(2, n + 1):
        edges.append([rr.randint(1, v - 1), v])
    while True:
        a, b = sorted(rr.sample(range(1, n + 1), 2))
        if [a, b] not in edges and [b, a] not in edges:
            break
    edges.insert(rr.randint(0, len(edges)), [a, b])
    return [edges]


def delay_case(n, m, seed):
    rr = random.Random(seed)
    edges = set()
    times = []
    for v in range(2, n + 1):                       # make everything reachable from 1
        u = rr.randint(1, v - 1)
        edges.add((u, v)); times.append([u, v, rr.randint(1, 100)])
    while len(times) < m:
        u, v = rr.sample(range(1, n + 1), 2)
        if (u, v) in edges:
            continue
        edges.add((u, v)); times.append([u, v, rr.randint(0, 100)])
    rr.shuffle(times)
    return [times, n, 1]


PROBLEMS = [
dict(
    id="js-kth-largest-element-in-a-stream", title="Kth Largest Element in a Stream", difficulty="Easy", pattern="Heap / Priority Queue",
    leetcode="https://leetcode.com/problems/kth-largest-element-in-a-stream/",
    neetcode="https://neetcode.io/problems/kth-largest-integer-in-a-stream",
    kind="js", entry="runKthLargest",
    description=r"""
Design class `KthLargest(k, nums)` that receives a starting array and then a stream of numbers. Each call
`add(val)` inserts `val` and returns the `k`-th largest value among everything seen so far (counting
duplicates). At least `k` values exist whenever `add` returns.

JavaScript has no built-in priority queue: write a small binary heap (lesson *A binary heap and priority queue
from scratch*).

**How the tests call your class.** `[ops, args]`, e.g.
`[["KthLargest","add","add","add"], [[3,[1,2,3,3]],[3],[5],[6]]]` → `[null,3,3,3]`. The provided driver makes the
calls.
""",
    starter="class KthLargest {\n  constructor(k, nums) {\n    // your fields\n  }\n  add(val) {}\n}\n" + KTH_DRIVER,
    solution=HEAP + r'''
class KthLargest {
  constructor(k, nums) {
    this.k = k;
    this.heap = new Heap((a, b) => a < b);   // min-heap of the k largest values
    for (const x of nums) this.add(x);
  }
  add(val) {
    this.heap.push(val);
    if (this.heap.size > this.k) this.heap.pop();   // drop the smallest
    return this.heap.peek();
  }
}
''' + KTH_DRIVER,
    tests=[
        [["KthLargest", "add", "add", "add"], [[3, [1, 2, 3, 3]], [3], [5], [6]]],
        [["KthLargest", "add", "add", "add", "add", "add"], [[3, [4, 5, 8, 2]], [3], [5], [10], [9], [4]]],
        [["KthLargest", "add", "add"], [[1, []], [-3], [-2]]],
        [["KthLargest", "add", "add", "add"], [[2, [0]], [-1], [1], [-2]]],
        [["KthLargest", "add", "add", "add", "add"], [[4, [7, 7, 7]], [7], [1], [8], [9]]],
        [["KthLargest", "add", "add"], [[1, [5, 4, 3]], [2], [10]]],
        kth_case(5, [3, 1, 4, 1, 5, 9, 2, 6], 300, 1),
        kth_case(100, [r.randint(-10**4, 10**4) for _ in range(200)], 3000, 2),
    ],
    examples=2,
    wrong_solutions=[
        HEAP + "\nclass KthLargest {\n  constructor(k, nums) { this.k = k; this.h = new Heap((a, b) => a > b); for (const x of nums) this.h.push(x); }\n  add(v) { this.h.push(v); return this.h.peek(); }\n}\n" + KTH_DRIVER,
        "class KthLargest {\n  constructor(k, nums) { this.k = k; this.a = [...nums]; }\n  add(v) { this.a.push(v); this.a.sort(); return this.a[this.a.length - this.k]; }\n}\n" + KTH_DRIVER,
    ],
    guide=G(
        prereqs="The lesson *A binary heap and priority queue from scratch*: `push`, `pop`, `peek` and the comparator function.",
        intuition="Keep only the `k` largest values, in a **min**-heap. Its smallest element (the root) is exactly the `k`-th largest overall. A new value goes in; if the heap grows past `k`, throw out the smallest.",
        hints=[
            "Which value do you need quick access to: the largest or the smallest of the top k?",
            "A min-heap of size k: root = k-th largest.",
            "After each push, pop while `size > k`.",
        ],
        brute_force="Push into an array and sort on each `add`: O(n log n) per call. Remember `sort()` without a comparator sorts numbers as strings.",
        approach="1. Min-heap with `less = (a, b) => a < b`.\n2. Constructor: `add` each initial value (the extra pops trim to k).\n3. `add(val)`: push; if `size > k` pop; return `peek()`.\n\n**Dry run** k=3, `[4,5,8,2]`: heap keeps 4, 5, 8. add 3 → push and pop 3 → root 4. add 5 → pop 4 → root 5.",
        complexity="Each `add` O(log k); constructor O(n log k). Space O(k).",
        pitfalls="- A max-heap returns the largest, not the k-th largest.\n- Default `sort()` puts `10` before `9`.\n- Off-by-one: the heap must hold exactly k values before you read the root.",
        follow_up="Kth Largest Element in an Array is the same heap over a fixed array, or Quickselect in O(n) average.",
    ),
),
dict(
    id="js-last-stone-weight", title="Last Stone Weight", difficulty="Easy", pattern="Heap / Priority Queue",
    leetcode="https://leetcode.com/problems/last-stone-weight/",
    neetcode="https://neetcode.io/problems/last-stone-weight",
    kind="js", entry="lastStoneWeight",
    description=r"""
You have stones with positive integer weights. Each turn, take the two heaviest stones `x <= y` and smash them:
if `x === y` both are destroyed; otherwise the lighter one is destroyed and the heavier one now weighs `y - x`.
Repeat until at most one stone is left. Return its weight, or `0` if none remain.

- `1 <= stones.length <= 1000`, `1 <= stones[i] <= 1000`

**Example 1:** `[2, 3, 6, 2, 4]` → `1`

**Example 2:** `[1, 2]` → `1`
""",
    starter="function lastStoneWeight(stones) {\n  // your code\n}\n",
    solution=HEAP + r'''
function lastStoneWeight(stones) {
  const heap = new Heap((a, b) => a > b);     // max-heap
  for (const s of stones) heap.push(s);
  while (heap.size > 1) {
    const y = heap.pop(), x = heap.pop();
    if (y !== x) heap.push(y - x);
  }
  return heap.size ? heap.pop() : 0;
}
''',
    tests=[[[2, 3, 6, 2, 4]], [[1, 2]], [[1]], [[2, 2]], [[2, 7, 4, 1, 8, 1]], [[10, 4, 2, 10]], [[3, 7, 2]], [[1, 1, 1]],
           [[1000, 1, 999]], [[r.randint(1, 1000) for _ in range(1000)]]],
    examples=2,
    wrong_solutions=[
        "function lastStoneWeight(stones) {\n  const a = [...stones].sort();\n  while (a.length > 1) { const y = a.pop(), x = a.pop(); if (y !== x) { a.push(y - x); a.sort(); } }\n  return a.length ? a[0] : 0;\n}\n",
        "function lastStoneWeight(stones) {\n  const a = [...stones].sort((p, q) => p - q);\n  while (a.length > 1) { const y = a.pop(), x = a.pop(); if (y !== x) a.push(y - x); }\n  return a.length ? a[0] : 0;\n}\n",
    ],
    guide=G(
        prereqs="A max-heap built from the generic `Heap` class with comparator `(a, b) => a > b`.",
        intuition="You repeatedly need the two largest items while new items keep arriving: that is exactly what a max-heap is for.",
        hints=[
            "Which structure gives you the maximum repeatedly while you insert new values?",
            "Flip the comparator of a min-heap to get a max-heap.",
            "Pop two, push the difference if it is non-zero.",
        ],
        brute_force="Sort with a numeric comparator after every smash: O(n^2 log n). Fine for n = 1000, but forgetting to re-sort (or using the default string sort) gives wrong answers.",
        approach="1. Push all stones into a max-heap.\n2. While at least two remain: `y = pop()`, `x = pop()`; if different, push `y - x`.\n3. Return the remaining stone or 0.\n\n**Dry run** `[2,3,6,2,4]`: 6,4 → 2; heap 3,2,2,2: 3,2 → 1; 2,2 → gone; left 1.",
        complexity="Time O(n log n), space O(n).",
        pitfalls="- Sorting once and never re-sorting after pushing `y - x` breaks the \"two heaviest\" rule.\n- `sort()` without a comparator orders `[10, 9, 100]` as `[10, 100, 9]`.",
        follow_up="Since weights are at most 1000, a counting array (bucket sort) gives O(n + W).",
    ),
),
dict(
    id="js-k-closest-points-to-origin", title="K Closest Points to Origin", difficulty="Medium", pattern="Heap / Priority Queue",
    leetcode="https://leetcode.com/problems/k-closest-points-to-origin/",
    neetcode="https://neetcode.io/problems/k-closest-points-to-origin",
    kind="js", entry="kClosest", compare="unordered",
    description=r"""
Given points `[x, y]` on a plane and an integer `k`, return the `k` points closest to the origin `(0, 0)` using
ordinary (Euclidean) distance. The answer is unique, and the points may be returned in any order.

- `1 <= k <= points.length <= 10^4`, `-10^4 <= x, y <= 10^4`

**Example 1:** `points = [[0, 2], [2, 2]], k = 1` → `[[0, 2]]`

**Example 2:** `points = [[0, 2], [2, 0], [2, 2]], k = 2` → `[[0, 2], [2, 0]]`
""",
    starter="function kClosest(points, k) {\n  // your code\n}\n",
    solution=HEAP + r'''
function kClosest(points, k) {
  const d = (p) => p[0] * p[0] + p[1] * p[1];        // squared distance: no sqrt needed
  const heap = new Heap((a, b) => d(a) > d(b));     // max-heap of the k best so far
  for (const p of points) {
    heap.push(p);
    if (heap.size > k) heap.pop();                  // drop the farthest
  }
  return heap.a;
}
''',
    tests=[[[[0, 2], [2, 2]], 1], [[[0, 2], [2, 0], [2, 2]], 2], [[[1, 3], [-2, 2]], 1], [[[3, 3], [5, -1], [-2, 4]], 2],
           [[[0, 0]], 1], [[[1, 1], [-1, -2], [3, 0]], 3], [[[10000, 10000], [-10000, -9999]], 1],
           [[[2, 9], [-1, 0], [7, -3], [0, 4], [-5, -5]], 3], unique_points(200, 17, 3), unique_points(5000, 600, 4)],
    examples=2,
    wrong_solutions=[
        "function kClosest(points, k) {\n  return [...points].sort((a, b) => (Math.abs(a[0]) + Math.abs(a[1])) - (Math.abs(b[0]) + Math.abs(b[1]))).slice(0, k);\n}\n",
        "function kClosest(points, k) {\n  return [...points].sort((a, b) => a[0] * a[0] + a[1] * a[1] - (b[0] * b[0] + b[1] * b[1])).slice(-k);\n}\n",
    ],
    guide=G(
        prereqs="The `Heap` class with a custom comparator; squared distances.",
        intuition="Keep the k best points seen so far in a **max**-heap keyed by distance. The root is the worst of the current best k, so when a new point arrives and the heap overflows, the root is the one to drop.",
        hints=[
            "You never need the square root: comparing `x*x + y*y` is enough.",
            "Sorting by distance and slicing gives an O(n log n) answer.",
            "A size-k max-heap gives O(n log k).",
        ],
        brute_force="`[...points].sort((a, b) => dist(a) - dist(b)).slice(0, k)`: O(n log n). Perfectly reasonable as a first answer.",
        approach="1. `d(p) = p[0]*p[0] + p[1]*p[1]`.\n2. Max-heap with `less = (a, b) => d(a) > d(b)`.\n3. Push every point; pop when size exceeds k.\n4. Return the heap's contents.",
        complexity="Time O(n log k), space O(k). Quickselect gives O(n) on average.",
        pitfalls="- Manhattan distance `|x| + |y|` is a different metric.\n- `Math.sqrt` is harmless but unnecessary; exact integer squares avoid floating-point ties.\n- The comparator of a max-heap is the reverse of a min-heap's: mixing them up keeps the farthest points.",
        follow_up="For a stream of points, the same heap answers \"k closest so far\" after each arrival.",
    ),
),
dict(
    id="js-find-median-from-data-stream", title="Find Median from Data Stream", difficulty="Hard", pattern="Heap / Priority Queue",
    leetcode="https://leetcode.com/problems/find-median-from-data-stream/",
    neetcode="https://neetcode.io/problems/find-median-in-a-data-stream",
    kind="js", entry="runMedianFinder",
    description=r"""
The **median** of a sorted list is its middle value; for an even count it is the average of the two middle values
(`[2, 3]` → `2.5`). Design class `MedianFinder` with:

- `addNum(num)` adds an integer from the stream
- `findMedian()` returns the median of all numbers added so far (at least one)

Aim for O(log n) per `addNum` and O(1) per `findMedian`.

**How the tests call your class.** `[ops, args]`, e.g.
`[["MedianFinder","addNum","addNum","findMedian","addNum","findMedian"], [[],[1],[2],[],[3],[]]]` →
`[null,null,null,1.5,null,2]`. The provided driver makes the calls.
""",
    starter="class MedianFinder {\n  constructor() {\n    // your fields\n  }\n  addNum(num) {}\n  findMedian() {}\n}\n" + MEDIAN_DRIVER,
    solution=HEAP + r'''
class MedianFinder {
  constructor() {
    this.low = new Heap((a, b) => a > b);    // max-heap: smaller half
    this.high = new Heap((a, b) => a < b);   // min-heap: larger half
  }
  addNum(num) {
    this.low.push(num);
    this.high.push(this.low.pop());          // move the largest of the low half up
    if (this.high.size > this.low.size) this.low.push(this.high.pop());   // keep low >= high
  }
  findMedian() {
    if (this.low.size > this.high.size) return this.low.peek();
    return (this.low.peek() + this.high.peek()) / 2;
  }
}
''' + MEDIAN_DRIVER,
    tests=[
        [["MedianFinder", "addNum", "addNum", "findMedian", "addNum", "findMedian"], [[], [1], [2], [], [3], []]],
        [["MedianFinder", "addNum", "findMedian"], [[], [-7], []]],
        [["MedianFinder", "addNum", "addNum", "addNum", "addNum", "findMedian"], [[], [5], [5], [5], [5], []]],
        [["MedianFinder", "addNum", "findMedian", "addNum", "findMedian", "addNum", "findMedian", "addNum", "findMedian"], [[], [10], [], [1], [], [7], [], [3], []]],
        [["MedianFinder", "addNum", "addNum", "findMedian"], [[], [-1], [-2], []]],
        [["MedianFinder", "addNum", "addNum", "addNum", "findMedian", "addNum", "findMedian"], [[], [6], [10], [2], [], [6], []]],
        median_case(300, 1),
        median_case(4000, 2),
    ],
    examples=2,
    wrong_solutions=[
        "class MedianFinder {\n  constructor() { this.a = []; }\n  addNum(n) { this.a.push(n); }\n  findMedian() { const s = [...this.a].sort(); const m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; }\n}\n" + MEDIAN_DRIVER,
        "class MedianFinder {\n  constructor() { this.a = []; }\n  addNum(n) { this.a.push(n); }\n  findMedian() { const s = [...this.a].sort((x, y) => x - y); return s[s.length >> 1]; }\n}\n" + MEDIAN_DRIVER,
    ],
    guide=G(
        prereqs="Two heaps built from one generic `Heap` class with opposite comparators.",
        intuition="Split the numbers into a smaller half and a larger half. Keep the smaller half in a max-heap and the larger half in a min-heap; then the middle values sit on the two roots. Balance the sizes so they differ by at most one.",
        hints=[
            "Which two values do you need to compute a median?",
            "Max-heap for the lower half, min-heap for the upper half.",
            "Insert into the low heap, move its max to the high heap, then rebalance so `low.size >= high.size`.",
        ],
        brute_force="Keep an array and sort it on every `findMedian`: O(n log n) per query (and the default `sort` is lexicographic). Binary-search insertion keeps it sorted in O(n) per add because of `splice`.",
        approach="1. `low` max-heap, `high` min-heap.\n2. `addNum`: push into `low`; push `low.pop()` into `high`; if `high` is larger, move its root back to `low`.\n3. `findMedian`: odd total → `low.peek()`; even → average of both roots.\n\n**Dry run** 1, 2: low [1], high [2] → 1.5. Add 3: low gets 3, moves 3 up, high [2,3] larger → move 2 down; low [2,1] → median 2.",
        complexity="`addNum` O(log n), `findMedian` O(1), space O(n).",
        pitfalls="- The default `sort()` puts `-1` after `-10` and `10` before `9`.\n- Forgetting to route the new number through `low` first can put a large value in the low half.\n- Averages like `1.5` are fine in JavaScript (all numbers are doubles), unlike integer division in other languages.",
        follow_up="Sliding Window Median adds deletions: use lazy deletion with a `Map` of pending removals.",
    ),
),
dict(
    id="js-number-of-islands", title="Number of Islands", difficulty="Medium", pattern="Graphs",
    leetcode="https://leetcode.com/problems/number-of-islands/",
    neetcode="https://neetcode.io/problems/count-number-of-islands",
    kind="js", entry="numIslands",
    description=r"""
`grid` is a 2-D array of strings `"1"` (land) and `"0"` (water). An **island** is a group of land cells joined
horizontally or vertically (not diagonally). Return the number of islands. Grids can be large
(one test is a 150 by 150 block of land), so an iterative search is safer than deep recursion.

**Example:**

```
[["1","1","0","0"],
 ["1","0","0","1"],
 ["0","0","1","1"]]   →   2
```
""",
    starter="function numIslands(grid) {\n  // your code\n}\n",
    solution=r'''function numIslands(grid) {
  const rows = grid.length, cols = rows ? grid[0].length : 0;
  const seen = Array.from({ length: rows }, () => new Array(cols).fill(false));
  let count = 0;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (grid[r][c] !== "1" || seen[r][c]) continue;
      count++;
      const stack = [[r, c]];          // iterative DFS: no call-stack limit
      seen[r][c] = true;
      while (stack.length) {
        const [i, j] = stack.pop();
        for (const [di, dj] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const a = i + di, b = j + dj;
          if (a >= 0 && a < rows && b >= 0 && b < cols && grid[a][b] === "1" && !seen[a][b]) {
            seen[a][b] = true;           // mark when pushing, not when popping
            stack.push([a, b]);
          }
        }
      }
    }
  }
  return count;
}
''',
    tests=[[[["1", "1", "0", "0"], ["1", "0", "0", "1"], ["0", "0", "1", "1"]]],
           [[["1", "1", "1", "1", "0"], ["1", "1", "0", "1", "0"], ["1", "1", "0", "0", "0"], ["0", "0", "0", "0", "0"]]],
           [[["1", "1", "0", "0", "0"], ["1", "1", "0", "0", "0"], ["0", "0", "1", "0", "0"], ["0", "0", "0", "1", "1"]]],
           [[["0"]]], [[["1"]]], [[["1", "0", "1", "0", "1"]]], [[["1"], ["0"], ["1"]]], [[["1", "0"], ["0", "1"]]],
           [[["1", "1", "1"], ["0", "1", "0"], ["1", "1", "1"]]], [island_grid(60, 60, 0.45, 5)], [[["1"] * 150 for _ in range(150)]],
           [island_grid(120, 120, 0.55, 6)]],
    examples=2,
    wrong_solutions=[
        "function numIslands(grid) {\n  let n = 0;\n  for (const row of grid) for (const c of row) if (c === '1') n++;\n  return n;\n}\n",
        "function numIslands(grid) {\n  let n = 0;\n  for (let r = 0; r < grid.length; r++) for (let c = 0; c < grid[0].length; c++) if (grid[r][c] === '1' && (r === 0 || grid[r - 1][c] !== '1') && (c === 0 || grid[r][c - 1] !== '1')) n++;\n  return n;\n}\n",
    ],
    guide=G(
        prereqs="The lesson *Graphs in JavaScript*: a grid as an implicit graph, iterative DFS with an array stack, `Array.from` for 2-D arrays.",
        intuition="Scan every cell. When you find land that no earlier search has reached, you found a new island: count it and flood its whole region (mark every connected land cell), so it is never counted again.",
        hints=[
            "Each unvisited `\"1\"` you meet during the scan starts a new island.",
            "Flood the island with DFS or BFS over the four neighbours.",
            "Mark a cell visited when you push it, so it is never pushed twice.",
        ],
        brute_force="Counting land cells, or counting cells with no land above or to the left, both fail on shapes like a U. Union-find over land cells is a correct alternative.",
        approach="1. `seen` grid of booleans (or overwrite `grid[r][c] = \"0\"` if mutation is allowed).\n2. For each unvisited land cell: `count++`, push it, and pop/push neighbours until the stack is empty.\n3. Return `count`.",
        complexity="Time O(R * C), space O(R * C) for `seen` and the stack.",
        pitfalls="- A recursive flood fill on a 200 x 200 all-land grid goes 40,000 calls deep and throws `RangeError: Maximum call stack size exceeded` in many engines. Use an explicit stack.\n- `new Array(rows).fill(new Array(cols).fill(false))` shares ONE row array across all rows.\n- Cells are strings: `grid[r][c] === 1` (number) is never true.",
        follow_up="Max Area of Island returns the largest flood size; Number of Islands II adds land online and needs union-find.",
    ),
),
dict(
    id="js-rotting-oranges", title="Rotting Oranges", difficulty="Medium", pattern="Graphs",
    leetcode="https://leetcode.com/problems/rotting-oranges/",
    neetcode="https://neetcode.io/problems/rotting-fruit",
    kind="js", entry="orangesRotting",
    description=r"""
Each cell of `grid` is `0` (empty), `1` (fresh orange) or `2` (rotten orange). Every minute, each fresh orange
next to a rotten one (up, down, left, right) becomes rotten. Return the number of minutes until no fresh orange is
left, or `-1` if some fresh orange can never rot.

**Example 1:** `[[2,1,1],[1,1,0],[0,1,1]]` → `4`

**Example 2:** `[[2,1,1],[0,1,1],[1,0,1]]` → `-1` (the bottom-left orange is cut off)
""",
    starter="function orangesRotting(grid) {\n  // your code\n}\n",
    solution=r'''function orangesRotting(grid) {
  const rows = grid.length, cols = grid[0].length;
  const g = grid.map((row) => [...row]);   // work on a copy
  let queue = [], fresh = 0;
  for (let r = 0; r < rows; r++)
    for (let c = 0; c < cols; c++) {
      if (g[r][c] === 2) queue.push([r, c]);
      else if (g[r][c] === 1) fresh++;
    }
  let minutes = 0;
  while (queue.length && fresh > 0) {      // multi-source BFS, one level per minute
    const next = [];
    for (const [r, c] of queue) {
      for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const a = r + dr, b = c + dc;
        if (a >= 0 && a < rows && b >= 0 && b < cols && g[a][b] === 1) {
          g[a][b] = 2;
          fresh--;
          next.push([a, b]);
        }
      }
    }
    queue = next;
    minutes++;
  }
  return fresh === 0 ? minutes : -1;
}
''',
    tests=[[[[2, 1, 1], [1, 1, 0], [0, 1, 1]]], [[[2, 1, 1], [0, 1, 1], [1, 0, 1]]], [[[0, 2]]], [[[0]]], [[[1]]], [[[2]]],
           [[[2, 1, 1, 1, 1, 1]]], [[[2, 1, 1], [1, 1, 1], [1, 1, 2]]], [[[1, 2, 1, 1, 2, 1, 1]]], [[[2, 0, 1]]],
           [orange_grid(40, 40, 3)], [[[1] * 120 for _ in range(120)][:119] + [[1] * 119 + [2]]]],
    examples=2,
    wrong_solutions=[
        "function orangesRotting(grid) {\n  let fresh = 0;\n  for (const row of grid) for (const x of row) if (x === 1) fresh++;\n  return fresh;\n}\n",
        "function orangesRotting(grid) {\n  const g = grid.map(r => [...r]);\n  let minutes = 0, changed = true;\n  while (changed) {\n    changed = false;\n    for (let r = 0; r < g.length; r++) for (let c = 0; c < g[0].length; c++) if (g[r][c] === 2) for (const [a, b] of [[r + 1, c], [r - 1, c], [r, c + 1], [r, c - 1]]) if (g[a] && g[a][b] === 1) { g[a][b] = 2; changed = true; }\n    if (changed) minutes++;\n  }\n  return g.some(row => row.includes(1)) ? -1 : minutes;\n}\n",
    ],
    guide=G(
        prereqs="Breadth-first search level by level (lesson *Graphs in JavaScript*).",
        intuition="Rot spreads like ripples from **all** rotten oranges at once. Start a BFS with every rotten cell in the first level; each BFS level is one minute. Count fresh oranges so you know at the end whether any were unreachable.",
        hints=[
            "Put every initially rotten orange in the starting queue.",
            "Process the queue one level at a time; each level is one minute.",
            "Track how many fresh oranges remain.",
        ],
        brute_force="Simulate minute by minute, scanning the whole grid each time: O((R * C)^2). Updating in place during the scan also lets rot spread several cells in one \"minute\", a classic bug.",
        approach="1. Copy the grid; enqueue rotten cells; count fresh.\n2. While the queue is non-empty and fresh > 0: build the next level from neighbours that are fresh (mark rotten, `fresh--`), then `minutes++`.\n3. Return `minutes` if `fresh === 0`, else `-1`.",
        complexity="Time O(R * C), space O(R * C).",
        pitfalls="- Without the `fresh > 0` loop guard you count one extra minute after the last orange rots.\n- A grid with no fresh oranges must return 0, even if there are no rotten ones.\n- Rotting cells during a full-grid scan mixes minutes; level-by-level BFS keeps them apart.",
        follow_up="Walls and Gates and 01 Matrix are the same multi-source BFS.",
    ),
),
dict(
    id="js-course-schedule", title="Course Schedule", difficulty="Medium", pattern="Graphs",
    leetcode="https://leetcode.com/problems/course-schedule/",
    neetcode="https://neetcode.io/problems/course-schedule",
    kind="js", entry="canFinish",
    description=r"""
There are `numCourses` courses labelled `0 .. numCourses - 1`. Each pair `[a, b]` in `prerequisites` means you
must finish course `b` before course `a`. Return `true` if it is possible to finish every course (that is, the
prerequisites contain no cycle).

- `1 <= numCourses <= 2000`, `0 <= prerequisites.length <= 5000`, pairs are distinct

**Example 1:** `numCourses = 2, prerequisites = [[1, 0]]` → `true`

**Example 2:** `numCourses = 2, prerequisites = [[1, 0], [0, 1]]` → `false`
""",
    starter="function canFinish(numCourses, prerequisites) {\n  // your code\n}\n",
    solution=r'''function canFinish(numCourses, prerequisites) {
  const next = Array.from({ length: numCourses }, () => []);   // b -> courses unlocked by b
  const indeg = new Array(numCourses).fill(0);
  for (const [a, b] of prerequisites) {
    next[b].push(a);
    indeg[a]++;
  }
  const queue = [];
  for (let i = 0; i < numCourses; i++) if (indeg[i] === 0) queue.push(i);
  let head = 0;                          // Kahn's algorithm with a head index
  while (head < queue.length) {
    const c = queue[head++];
    for (const d of next[c]) if (--indeg[d] === 0) queue.push(d);
  }
  return queue.length === numCourses;    // every course was taken
}
''',
    tests=[[2, [[1, 0]]], [2, [[1, 0], [0, 1]]], [1, []], [3, []], [3, [[0, 1], [1, 2], [2, 0]]], [4, [[1, 0], [2, 1], [3, 2]]],
           [3, [[1, 0], [1, 2], [0, 1]]], [5, [[1, 4], [2, 4], [3, 1], [3, 2]]], [2, [[0, 0]]],
           [2000, [[i + 1, i] for i in range(1999)]], [2000, [[i + 1, i] for i in range(1999)] + [[0, 1999]]],
           dag_prereqs(500, 3000, 7), [500, dag_prereqs(500, 2999, 8)[1] + [[0, 0]]]],
    examples=2,
    wrong_solutions=[
        "function canFinish(n, pre) {\n  for (const [a, b] of pre) if (pre.some(([c, d]) => c === b && d === a)) return false;\n  return true;\n}\n",
        "function canFinish(n, pre) {\n  const seen = new Set();\n  for (const [a, b] of pre) { if (seen.has(a)) return false; seen.add(b); }\n  return true;\n}\n",
    ],
    guide=G(
        prereqs="Adjacency lists as arrays of arrays, in-degrees, and topological order (lesson *Graphs in JavaScript*).",
        intuition="Courses with no remaining prerequisites can be taken now. Taking one may free others. If this process (Kahn's algorithm) takes every course, the graph has no cycle; if courses remain stuck, they are waiting on each other in a cycle.",
        hints=[
            "Model each prerequisite `[a, b]` as an edge `b -> a`.",
            "Count incoming edges (in-degree) for every course.",
            "Repeatedly take courses with in-degree 0 and lower their neighbours' in-degrees.",
        ],
        brute_force="Checking only for direct two-course loops (`[a,b]` and `[b,a]`) misses longer cycles like 0 → 1 → 2 → 0. A DFS with three colours (unvisited, in progress, done) is the other standard O(V + E) solution.",
        approach="1. Build `next` lists and `indeg` counts.\n2. Queue every course with in-degree 0.\n3. Pop with a head index; for each unlocked course decrement its in-degree and enqueue it at 0.\n4. Return whether all courses were dequeued.",
        complexity="Time O(V + E), space O(V + E).",
        pitfalls="- A recursive DFS on a 2000-course chain is about 2000 frames deep: fine in Node, but the iterative Kahn version has no depth risk at all.\n- A self-loop `[0, 0]` is a cycle.\n- `queue.shift()` makes Kahn's algorithm O(V^2) on long chains; use a head index.",
        follow_up="Course Schedule II returns the order itself: it is exactly the `queue` array when its length equals `numCourses`.",
    ),
),
dict(
    id="js-redundant-connection", title="Redundant Connection", difficulty="Medium", pattern="Graphs",
    leetcode="https://leetcode.com/problems/redundant-connection/",
    neetcode="https://neetcode.io/problems/redundant-connection",
    kind="js", entry="findRedundantConnection",
    description=r"""
A tree with nodes `1..n` had one extra edge added, so the undirected graph now has exactly one cycle. `edges`
lists all `n` edges in input order. Return an edge that can be removed so the result is a tree again; if several
edges qualify, return the one that appears **last** in `edges`.

- `3 <= n <= 1000`

**Example 1:** `[[1, 2], [1, 3], [3, 4], [2, 4]]` → `[2, 4]`

**Example 2:** `[[1, 2], [2, 3], [1, 3]]` → `[1, 3]`
""",
    starter="function findRedundantConnection(edges) {\n  // your code\n}\n",
    solution=r'''function findRedundantConnection(edges) {
  const parent = Array.from({ length: edges.length + 1 }, (_, i) => i);
  const rank = new Array(edges.length + 1).fill(0);
  const find = (x) => {
    while (parent[x] !== x) {
      parent[x] = parent[parent[x]];   // path halving
      x = parent[x];
    }
    return x;
  };
  for (const [a, b] of edges) {
    let ra = find(a), rb = find(b);
    if (ra === rb) return [a, b];      // already connected: this edge closes the cycle
    if (rank[ra] < rank[rb]) [ra, rb] = [rb, ra];
    parent[rb] = ra;
    if (rank[ra] === rank[rb]) rank[ra]++;
  }
  return [];
}
''',
    tests=[[[[1, 2], [1, 3], [3, 4], [2, 4]]], [[[1, 2], [2, 3], [1, 3]]], [[[1, 2], [2, 3], [3, 4], [1, 4], [1, 5]]],
           [[[3, 4], [1, 2], [2, 4], [3, 5], [2, 5]]], [[[1, 4], [3, 4], [1, 3], [1, 2], [4, 5]]], [[[2, 3], [1, 2], [1, 3]]],
           tree_plus_edge(50, 1), tree_plus_edge(1000, 2), [[[i, i + 1] for i in range(1, 1000)] + [[1, 1000]]]],
    examples=2,
    wrong_solutions=[
        "function findRedundantConnection(edges) {\n  return edges[edges.length - 1];\n}\n",
        "function findRedundantConnection(edges) {\n  const seen = new Set();\n  for (const [a, b] of edges) { if (seen.has(a) && seen.has(b)) return [a, b]; seen.add(a); seen.add(b); }\n  return [];\n}\n",
    ],
    guide=G(
        prereqs="Union-find (disjoint set union) with path compression (lesson *Graphs in JavaScript*).",
        intuition="Add edges one by one, keeping track of which nodes are already connected. The first edge whose two ends are **already** in the same component closes a cycle; because the graph has exactly one cycle, that edge is also the last cycle edge in the input.",
        hints=[
            "How can you test \"are a and b already connected?\" quickly while edges arrive?",
            "Union-find: `find` returns a component's representative, `union` merges two components.",
            "Return the first edge where `find(a) === find(b)`.",
        ],
        brute_force="For each edge, remove it and check with BFS whether the remaining graph is still connected; scan from the end. O(n^2).",
        approach="1. `parent[i] = i` for 1..n.\n2. `find` with path halving.\n3. For each edge: same root → return it; else union by rank.\n\n**Dry run** `[[1,2],[1,3],[3,4],[2,4]]`: union 1-2, 1-3, 3-4; edge 2-4: both have root 1 → `[2,4]`.",
        complexity="Time O(n * α(n)), effectively linear. Space O(n).",
        pitfalls="- \"Both endpoints seen before\" is not the same as \"connected\": two separate components can each contain one endpoint.\n- Nodes are 1-based; size the `parent` array `n + 1`.\n- A recursive `find` without compression can recurse deep on a chain; the loop version cannot.",
        follow_up="Number of Connected Components in an Undirected Graph counts successful unions: components = n - unions.",
    ),
),
dict(
    id="js-network-delay-time", title="Network Delay Time", difficulty="Medium", pattern="Advanced Graphs",
    leetcode="https://leetcode.com/problems/network-delay-time/",
    neetcode="https://neetcode.io/problems/network-delay-time",
    kind="js", entry="networkDelayTime",
    description=r"""
A network has `n` nodes labelled `1..n`. `times[i] = [u, v, w]` is a **directed** link: a signal sent from `u`
reaches `v` after `w` time units. A signal starts at node `k`. Return how long it takes until **every** node has
received it, or `-1` if some node is unreachable.

- `1 <= n <= 100`, `1 <= times.length <= 6000`, `0 <= w <= 100`

**Example 1:** `times = [[1,2,1],[2,3,1],[1,4,4],[3,4,1]], n = 4, k = 1` → `3`

**Example 2:** `times = [[1,2,1],[2,3,1]], n = 3, k = 2` → `-1`

Use Dijkstra's algorithm with a binary heap; JavaScript has no built-in priority queue.
""",
    starter="function networkDelayTime(times, n, k) {\n  // your code\n}\n",
    solution=HEAP + r'''
function networkDelayTime(times, n, k) {
  const adj = new Map();                          // u -> [[v, w], ...]
  for (const [u, v, w] of times) {
    if (!adj.has(u)) adj.set(u, []);
    adj.get(u).push([v, w]);
  }
  const dist = new Map();                         // finalised shortest times
  const heap = new Heap((a, b) => a[0] < b[0]);   // entries [time, node]
  heap.push([0, k]);
  while (heap.size) {
    const [t, u] = heap.pop();
    if (dist.has(u)) continue;                    // stale entry: already finalised
    dist.set(u, t);
    for (const [v, w] of adj.get(u) || []) if (!dist.has(v)) heap.push([t + w, v]);
  }
  if (dist.size < n) return -1;
  return Math.max(...dist.values());
}
''',
    tests=[[[[1, 2, 1], [2, 3, 1], [1, 4, 4], [3, 4, 1]], 4, 1], [[[1, 2, 1], [2, 3, 1]], 3, 2], [[[1, 2, 1]], 2, 1],
           [[[1, 2, 1]], 2, 2], [[], 1, 1], [[[2, 1, 1], [2, 3, 1], [3, 4, 1]], 4, 2], [[[1, 2, 0], [2, 3, 0]], 3, 1],
           [[[1, 2, 5], [1, 3, 1], [3, 2, 1], [2, 4, 1]], 4, 1], [[[1, 2, 1], [2, 1, 3]], 2, 2],
           delay_case(30, 200, 1), delay_case(100, 6000, 2), [delay_case(100, 3000, 3)[0], 100, 50]],
    examples=2,
    wrong_solutions=[
        "function networkDelayTime(times, n, k) {\n  const dist = new Map([[k, 0]]);\n  const q = [k];\n  for (let h = 0; h < q.length; h++) { const u = q[h]; for (const [a, b, w] of times) if (a === u && !dist.has(b)) { dist.set(b, dist.get(u) + w); q.push(b); } }\n  return dist.size < n ? -1 : Math.max(...dist.values());\n}\n",
        "function networkDelayTime(times, n, k) {\n  let s = 0;\n  for (const t of times) s = Math.max(s, t[2]);\n  return s;\n}\n",
    ],
    guide=G(
        prereqs="The `Heap` class (lesson *A binary heap and priority queue from scratch*) and adjacency `Map`s (lesson *Graphs in JavaScript*).",
        intuition="The answer is the largest shortest-path distance from `k`. Dijkstra's algorithm finalises nodes in order of distance: always expand the closest not-yet-finalised node, which a min-heap hands you in O(log n).",
        hints=[
            "Build an adjacency `Map` from each node to its outgoing `[v, w]` pairs.",
            "Push `[0, k]` into a min-heap ordered by time.",
            "Skip popped entries whose node is already finalised (lazy deletion). At the end, check that all n nodes were reached.",
        ],
        brute_force="Bellman-Ford relaxes every edge n - 1 times: O(n * E), which is 600,000 steps here and still acceptable. Plain BFS ignores weights and is wrong.",
        approach="1. Build `adj`.\n2. Heap of `[time, node]`; push `[0, k]`.\n3. Pop; if already in `dist`, skip; else record and push each neighbour with `t + w`.\n4. If fewer than n nodes are recorded return -1, else the maximum distance.\n\n**Dry run** example 1: pop (0,1) → push (1,2),(4,4); pop (1,2) → push (2,3); pop (2,3) → push (3,4); pop (3,4) finalises 4; stale (4,4) skipped → max 3.",
        complexity="Time O(E log E), space O(n + E).",
        pitfalls="- Without the \"already finalised\" check, stale heap entries overwrite correct distances.\n- BFS order is not distance order when edges have weights.\n- `Math.max(...dist.values())` is fine for 100 values; for huge maps reduce in a loop.",
        follow_up="Cheapest Flights Within K Stops limits the number of edges: use Bellman-Ford for k + 1 rounds or a BFS by stops.",
    ),
),
]
