import random

_R = random.Random(31337)
INF = 2147483647


def _grid(rng, r, c, p, one="1", zero="0"):
    return [[one if rng.random() < p else zero for _ in range(c)] for _ in range(r)]


def _connected_adj(rng, n, extra):
    """random connected undirected simple graph as 1-indexed adjacency list"""
    edges = set()
    for v in range(2, n + 1):
        u = rng.randint(1, v - 1)
        edges.add((u, v))
    tries = 0
    while len(edges) < n - 1 + extra and tries < 10 * extra + 10:
        tries += 1
        a, b = rng.sample(range(1, n + 1), 2)
        edges.add((min(a, b), max(a, b)))
    adj = [[] for _ in range(n)]
    for a, b in sorted(edges):
        adj[a - 1].append(b)
        adj[b - 1].append(a)
    return adj


def _rooms(rng, r, c, pwall, pgate):
    g = []
    for _ in range(r):
        row = []
        for _ in range(c):
            x = rng.random()
            row.append(-1 if x < pwall else 0 if x < pwall + pgate else INF)
        g.append(row)
    return g


def _oranges(rng, r, c, p_empty, p_rot):
    g = []
    for _ in range(r):
        row = []
        for _ in range(c):
            x = rng.random()
            row.append(0 if x < p_empty else 2 if x < p_empty + p_rot else 1)
        g.append(row)
    return g


def _dag(rng, n, m):
    perm = list(range(n))
    rng.shuffle(perm)
    pairs = set()
    tries = 0
    while len(pairs) < m and tries < 20 * m:
        tries += 1
        i, j = sorted(rng.sample(range(n), 2))
        pairs.add((perm[j], perm[i]))  # perm[i] must come before perm[j]
    return [list(p) for p in sorted(pairs)]


def _tree_edges(rng, n, label_from=0):
    nodes = list(range(label_from, n + label_from))
    rng.shuffle(nodes)
    edges = []
    for i in range(1, n):
        edges.append([nodes[rng.randint(0, i - 1)], nodes[i]])
    rng.shuffle(edges)
    return edges


def _forest_edges(rng, n, m):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    edges = []
    tries = 0
    while len(edges) < m and tries < 50 * m + 50:
        tries += 1
        a, b = rng.sample(range(n), 2)
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
            edges.append([a, b])
    return edges


def _redundant(rng, n):
    edges = [[min(a, b), max(a, b)] for a, b in _tree_edges(rng, n, 1)]
    existing = {tuple(e) for e in edges}
    while True:
        a, b = sorted(rng.sample(range(1, n + 1), 2))
        if (a, b) not in existing:
            break
    pos = rng.randint(0, n - 1)
    edges.insert(pos, [a, b])
    return [edges]


def _ladder_case(rng, nwords, length, alphabet):
    words = set()
    while len(words) < nwords:
        words.add("".join(rng.choice(alphabet) for _ in range(length)))
    words = sorted(words)
    begin = "".join(rng.choice(alphabet) for _ in range(length))
    end = rng.choice(words)
    return [begin, end, words]


_COURSE2_CHECK = '''
def check(args, got, expected):
    n, pre = args
    if expected == []:
        return got == []
    if not isinstance(got, list) or sorted(got) != list(range(n)):
        return False
    pos = {c: i for i, c in enumerate(got)}
    return all(pos[b] < pos[a] for a, b in pre)
'''

PROBLEMS = [
# ---------------------------------------------------------------------------------------------
dict(
    id="number-of-islands",
    title="Number of Islands",
    difficulty="Medium",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/number-of-islands/",
    neetcode="https://neetcode.io/problems/count-number-of-islands",
    entry="numIslands",
    description=r"""
A map is given as an `m × n` grid of strings: `"1"` is land and `"0"` is water. An **island** is a
maximal group of land cells connected **horizontally or vertically** (not diagonally). Everything
outside the grid is water. Return how many islands there are.

**Constraints:** `1 <= m, n <= 300`, each cell is `"0"` or `"1"`.

**Example 1:**
```
[["1","1","0","0"],
 ["1","1","0","0"],
 ["0","0","1","0"],
 ["0","0","0","1"]]   -> 3
```

**Example 2:** `[["1","1","1"],["0","1","0"],["1","1","1"]]` → `1`
""",
    starter='''class Solution:
    def numIslands(self, grid: List[List[str]]) -> int:
        pass
''',
    solution='''class Solution:
    def numIslands(self, grid):
        R, C = len(grid), len(grid[0])
        seen = [[False] * C for _ in range(R)]
        count = 0
        for sr in range(R):
            for sc in range(C):
                if grid[sr][sc] == "1" and not seen[sr][sc]:
                    count += 1
                    seen[sr][sc] = True
                    stack = [(sr, sc)]
                    while stack:
                        r, c = stack.pop()
                        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                            if 0 <= nr < R and 0 <= nc < C and grid[nr][nc] == "1" and not seen[nr][nc]:
                                seen[nr][nc] = True
                                stack.append((nr, nc))
        return count
''',
    tests=[
        [[["1", "1", "0", "0"], ["1", "1", "0", "0"], ["0", "0", "1", "0"], ["0", "0", "0", "1"]]],
        [[["1", "1", "1"], ["0", "1", "0"], ["1", "1", "1"]]],
        [[["0"]]],
        [[["1"]]],
        [[["1", "0", "1", "0", "1"]]],
        [[["1", "0"], ["0", "1"]]],
        [[["1", "1", "1", "1"], ["1", "0", "0", "1"], ["1", "0", "1", "1"], ["1", "1", "1", "0"]]],
        [[["1", "0", "1"], ["0", "1", "0"], ["1", "0", "1"]]],
        [[["0"] * 50 for _ in range(50)]],
        [[["1"] * 120 for _ in range(120)]],
        [_grid(_R, 150, 150, 0.45)],
        [_grid(_R, 100, 200, 0.6)],
        [[["1" if (r + c) % 2 == 0 else "0" for c in range(60)] for r in range(60)]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def numIslands(self, grid):
        return sum(row.count("1") for row in grid)
''',
        '''class Solution:
    def numIslands(self, grid):
        R, C = len(grid), len(grid[0]); seen = set(); count = 0
        for sr in range(R):
            for sc in range(C):
                if grid[sr][sc] == "1" and (sr, sc) not in seen:
                    count += 1; stack = [(sr, sc)]; seen.add((sr, sc))
                    while stack:
                        r, c = stack.pop()
                        for nr, nc in ((r+1,c),(r-1,c),(r,c+1),(r,c-1),(r+1,c+1),(r-1,c-1),(r+1,c-1),(r-1,c+1)):
                            if 0 <= nr < R and 0 <= nc < C and grid[nr][nc] == "1" and (nr, nc) not in seen:
                                seen.add((nr, nc)); stack.append((nr, nc))
        return count
''',
    ],
    guide=dict(
        prereqs="Grids as implicit graphs; DFS/BFS flood fill (lesson *DFS and BFS on grids and adjacency lists*).",
        intuition=r"""
Treat each land cell as a vertex with edges to its up/down/left/right land neighbours. Islands are
the **connected components** of this graph. Scan the grid; every time you meet unvisited land you
have found a new island — count it and flood-fill (DFS or BFS) to mark the whole island visited so
you don't count it again.
""",
        hints=[
            "Model the grid as a graph. What graph concept is an island?",
            "Scan every cell; when you find land you haven't visited, how do you make sure you never count any other cell of that island?",
            "count += 1, then DFS/BFS from that cell marking every reachable '1' as visited (or overwrite it with '0').",
        ],
        brute_force="Union-find over all land cells (union each land cell with its right and down neighbour, then count roots) is an equally efficient alternative. A truly naive approach would re-scan to merge labels repeatedly — O((mn)²).",
        approach=r"""
1. For each cell `(r, c)`: if it is `"1"` and unvisited, `count += 1` and flood-fill from it.
2. Flood fill (iterative DFS): push the start; pop a cell, push each in-bounds, unvisited land neighbour after marking it.

**Dry run** on Example 1: (0,0) is new → island 1 covers (0,0),(0,1),(1,0),(1,1). Next new land is (2,2) → island 2. Then (3,3) → island 3 (diagonal to (2,2), so separate). Answer 3.
""",
        complexity="O(m·n) time — every cell is pushed at most once and checks 4 neighbours. O(m·n) space for `seen` and the stack in the worst case.",
        pitfalls=r"""
- Counting diagonal neighbours (wrong solution #2).
- Comparing with the integer `1` — cells are the **strings** `"1"`/`"0"`.
- Recursive DFS on a 300×300 all-land grid exceeds Python's default recursion limit (1000). Use an explicit stack or BFS.
- Marking cells visited when *popped* rather than when *pushed* lets the same cell be pushed many times (still correct, but slower).
""",
        follow_up="*Number of Islands II* adds land one cell at a time and asks for the count after each addition — use union-find. *Max Area of Island* and *Surrounded Regions* reuse the same flood fill.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="max-area-of-island",
    title="Max Area of Island",
    difficulty="Medium",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/max-area-of-island/",
    neetcode="https://neetcode.io/problems/max-area-of-island",
    entry="maxAreaOfIsland",
    description=r"""
You get an `m × n` grid of integers where `1` is land and `0` is water. An island is a group of land
cells connected in the four cardinal directions. The **area** of an island is its number of cells.
Return the largest island area, or `0` if there is no land.

**Constraints:** `1 <= m, n <= 50`, cells are `0` or `1`.

**Example 1:**
```
[[0,1,1,0],
 [0,1,0,0],
 [1,0,0,1],
 [1,1,0,1]]  -> 3   (both the top island and the bottom-left island have 3 cells)
```

**Example 2:** `[[0,0,0]]` → `0`
""",
    starter='''class Solution:
    def maxAreaOfIsland(self, grid: List[List[int]]) -> int:
        pass
''',
    solution='''from collections import deque

class Solution:
    def maxAreaOfIsland(self, grid):
        R, C = len(grid), len(grid[0])
        seen = [[False] * C for _ in range(R)]
        best = 0
        for sr in range(R):
            for sc in range(C):
                if grid[sr][sc] == 1 and not seen[sr][sc]:
                    seen[sr][sc] = True
                    q, area = deque([(sr, sc)]), 0
                    while q:
                        r, c = q.popleft()
                        area += 1
                        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                            if 0 <= nr < R and 0 <= nc < C and grid[nr][nc] == 1 and not seen[nr][nc]:
                                seen[nr][nc] = True
                                q.append((nr, nc))
                    best = max(best, area)
        return best
''',
    tests=[
        [[[0, 1, 1, 0], [0, 1, 0, 0], [1, 0, 0, 1], [1, 1, 0, 1]]],
        [[[0, 0, 0]]],
        [[[1]]],
        [[[0]]],
        [[[1, 0, 1], [0, 1, 0], [1, 0, 1]]],
        [[[1, 1, 0, 0, 0], [1, 1, 0, 0, 0], [0, 0, 0, 1, 1], [0, 0, 0, 1, 1]]],
        [[[1, 1, 1, 1, 1], [0, 0, 0, 0, 1], [1, 1, 1, 0, 1], [1, 0, 1, 1, 1]]],
        [[[0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0],
          [0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0],
          [0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0]]],
        [[[1] * 50 for _ in range(50)]],
        [_grid(_R, 50, 50, 0.5, 1, 0)],
        [_grid(_R, 50, 50, 0.62, 1, 0)],
        [[[1 if c % 2 == 0 or (c % 4 == 1 and r == 0) or (c % 4 == 3 and r == 49) else 0 for c in range(50)] for r in range(50)]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def maxAreaOfIsland(self, grid):
        return sum(map(sum, grid))
''',
        '''class Solution:
    def maxAreaOfIsland(self, grid):
        R, C = len(grid), len(grid[0]); best = 0
        for r in range(R):
            run = 0
            for c in range(C):
                run = run + 1 if grid[r][c] else 0
                best = max(best, run)
        return best
''',
    ],
    guide=dict(
        prereqs="*Number of Islands*; BFS/DFS that returns a size.",
        intuition="Same flood fill as *Number of Islands*, but instead of only counting components, measure each one: the number of cells your traversal visits is the island's area. Keep the maximum.",
        hints=[
            "How would you find all cells of one island? Can the traversal also count them?",
            "Run BFS/DFS from each unvisited land cell and count the cells you pop.",
            "best = max(best, area) after each flood fill; return best (0 if no land).",
        ],
        brute_force="Flood-fill from every land cell without a shared visited set, computing that island's area each time — O((mn)²) in the worst case.",
        approach=r"""
For each unvisited land cell, BFS: mark on push, `area += 1` on pop, push four-way land neighbours. Update `best`.

**Dry run** Example 1: start (0,1) → visits (0,1),(0,2),(1,1) → area 3. Start (2,0) → (2,0),(3,0),(3,1) → 3. Start (2,3) → (2,3),(3,3) → 2. Max = 3.

Recursive form: `area(r, c) = 0` if out of bounds / water / seen, else mark and return `1 + sum(area of 4 neighbours)`.
""",
        complexity="O(m·n) time and space.",
        pitfalls=r"""
- Forgetting to mark visited → infinite loops or double counting.
- Returning `-inf`/`None` when there is no land — must be `0`.
- Recursion depth for a 50×50 snake-shaped island approaches 2,500 frames — beyond Python's default limit; use a stack/queue or raise the limit.
""",
        follow_up="*Making A Large Island* (LeetCode 827): label each island with its area first, then for each water cell sum the distinct neighbouring island areas + 1.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="clone-graph",
    title="Clone Graph",
    difficulty="Medium",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/clone-graph/",
    neetcode="https://neetcode.io/problems/clone-graph",
    entry="cloneGraph",
    arg_types=["graph"],
    return_type="graph",
    description=r"""
You receive a reference to one node of a **connected, undirected** graph. Each node has an integer
`val` and a list `neighbors`:

```python
class Node:
    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []
```

Return a **deep copy**: a brand-new set of `Node` objects with the same values and the same
connections (in the same neighbour order), sharing no node objects with the original. If the input is `None`, return `None`.

In the tests a graph is written as an adjacency list: entry `i` (0-based) lists the neighbour values
of the node with value `i + 1`; you receive the node with value `1`.

**Constraints:** `0 <= nodes <= 100`, values are `1..n` and unique, no self-loops or repeated edges.

**Example 1:** `[[2,4],[1,3],[2,4],[1,3]]` → `[[2,4],[1,3],[2,4],[1,3]]` (a square 1–2–3–4–1)

**Example 2:** `[[]]` → `[[]]` (one node, no edges). **Example 3:** `[]` → `[]` (no graph).
""",
    starter='''"""
# Definition for a Node (pre-defined in the judge).
class Node:
    def __init__(self, val = 0, neighbors = None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []
"""

class Solution:
    def cloneGraph(self, node: Optional['Node']) -> Optional['Node']:
        pass
''',
    solution='''from collections import deque

class Solution:
    def cloneGraph(self, node):
        if node is None:
            return None
        copies = {node: Node(node.val)}
        q = deque([node])
        while q:
            cur = q.popleft()
            for nb in cur.neighbors:
                if nb not in copies:
                    copies[nb] = Node(nb.val)
                    q.append(nb)
                copies[cur].neighbors.append(copies[nb])
        return copies[node]
''',
    tests=[
        [[[2, 4], [1, 3], [2, 4], [1, 3]]],
        [[[]]],
        [[]],
        [[[2], [1]]],
        [[[2, 3], [1, 3], [1, 2]]],
        [[[2], [1, 3], [2, 4], [3, 5], [4]]],
        [[[2, 3, 4, 5], [1], [1], [1], [1]]],
        [[[j for j in range(1, 11) if j != i] for i in range(1, 11)]],
        [_connected_adj(_R, 30, 20)],
        [_connected_adj(_R, 100, 0)],
        [_connected_adj(_R, 100, 300)],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def cloneGraph(self, node):
        return Node(node.val) if node else None
''',
        '''class Solution:
    def cloneGraph(self, node):
        if node is None: return None
        copies = {}
        def dfs(n):
            if n.val in copies: return copies[n.val]
            c = Node(n.val); copies[n.val] = c
            for nb in n.neighbors[:1]:
                c.neighbors.append(dfs(nb))
            return c
        return dfs(node)
''',
    ],
    guide=dict(
        prereqs="Graph traversal (BFS/DFS) with a visited map (lesson *DFS and BFS on grids and adjacency lists*).",
        intuition=r"""
Traverse the original graph, and keep a dictionary **old node → new node**. The dictionary doubles as
the visited set: the first time you see a node you create its copy; every later time (cycles!) you
reuse the existing copy. Each edge is then wired between copies.
""",
        hints=[
            "Why does a naive recursive copy loop forever on a graph with a cycle?",
            "Keep a hash map from each original node to its clone; it tells you whether a node has been copied already.",
            "BFS from the start node: for each neighbour, create its clone if missing (and enqueue it), then append the neighbour's clone to the current clone's neighbors.",
        ],
        brute_force="There is no meaningfully slower correct approach: any correct algorithm must visit every node and edge. The common *wrong* first attempt is recursion without a memo map (infinite recursion on cycles).",
        approach=r"""
1. If `node is None`, return `None`.
2. `copies = {node: Node(node.val)}`, queue = `[node]`.
3. Pop `cur`; for each neighbour `nb`: if not in `copies`, create and enqueue; append `copies[nb]` to `copies[cur].neighbors`.

**Dry run** square 1–2–3–4: pop 1 → create 2, 4; clone1.nbrs = [2', 4']. Pop 2 → 1 exists, create 3; clone2.nbrs = [1', 3']. Pop 4 → 1, 3 exist; clone4.nbrs = [1', 3']. Pop 3 → clone3.nbrs = [2', 4'].

DFS version: `def dfs(n): if n in copies: return copies[n]; c = copies[n] = Node(n.val); c.neighbors = [dfs(x) for x in n.neighbors]; return c` — register the copy **before** recursing.
""",
        complexity="O(V + E) time, O(V) space for the map and queue.",
        pitfalls=r"""
- Registering the clone in the map *after* recursing into neighbours → infinite recursion.
- Returning the original node or reusing original neighbour lists (shallow copy). The judge here compares structure; an interviewer will check identity too.
- Forgetting the `None` input.
""",
        follow_up="*Copy List with Random Pointer* is the same idea on a linked list. For a graph given as edge lists, cloning is just copying the adjacency structure.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="walls-and-gates",
    title="Walls and Gates",
    difficulty="Medium",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/walls-and-gates/",
    neetcode="https://neetcode.io/problems/islands-and-treasure",
    entry="wallsAndGates",
    inplace_arg=0,
    description=r"""
A building floor plan is an `m × n` grid `rooms` with three kinds of cells:

- `-1` — a wall;
- `0` — a gate;
- `2147483647` (call it `INF`) — an empty room.

**Modify `rooms` in place** so that every empty room holds the number of steps to its **nearest gate**,
moving up/down/left/right and never through walls. Rooms that cannot reach any gate stay `INF`.
Return nothing.

**Constraints:** `1 <= m, n <= 250`, cells are `-1`, `0` or `2147483647`.

**Example:**
```
INF  -1   0  INF          3  -1   0   1
INF INF INF   -1   --->   2   2   1  -1
INF  -1 INF   -1          1  -1   2  -1
  0  -1 INF INF           0  -1   3   4
```
""",
    starter='''class Solution:
    def wallsAndGates(self, rooms: List[List[int]]) -> None:
        """
        Do not return anything, modify rooms in-place instead.
        """
        pass
''',
    solution='''from collections import deque

class Solution:
    def wallsAndGates(self, rooms):
        INF = 2147483647
        R, C = len(rooms), len(rooms[0])
        q = deque((r, c) for r in range(R) for c in range(C) if rooms[r][c] == 0)
        while q:
            r, c = q.popleft()
            for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if 0 <= nr < R and 0 <= nc < C and rooms[nr][nc] == INF:
                    rooms[nr][nc] = rooms[r][c] + 1
                    q.append((nr, nc))
''',
    tests=[
        [[[INF, -1, 0, INF], [INF, INF, INF, -1], [INF, -1, INF, -1], [0, -1, INF, INF]]],
        [[[-1]]],
        [[[INF]]],
        [[[0]]],
        [[[0, INF, INF, INF, INF]]],
        [[[INF, INF, 0, INF, INF]]],
        [[[0, -1, INF]]],
        [[[INF, INF], [INF, INF]]],
        [[[0, INF, INF], [INF, -1, INF], [INF, INF, 0]]],
        [_rooms(_R, 60, 60, 0.25, 0.01)],
        [_rooms(_R, 100, 100, 0.2, 0.002)],
        [[[0] + [INF] * 149] + [[INF] * 150 for _ in range(149)]],
    ],
    examples=1,
    wrong_solutions=[
        '''from collections import deque
class Solution:
    def wallsAndGates(self, rooms):
        INF = 2147483647; R, C = len(rooms), len(rooms[0])
        gates = [(r, c) for r in range(R) for c in range(C) if rooms[r][c] == 0]
        if not gates: return
        q = deque([gates[0]])
        while q:
            r, c = q.popleft()
            for nr, nc in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)):
                if 0 <= nr < R and 0 <= nc < C and rooms[nr][nc] == INF:
                    rooms[nr][nc] = rooms[r][c] + 1; q.append((nr, nc))
''',
        '''class Solution:
    def wallsAndGates(self, rooms):
        INF = 2147483647; R, C = len(rooms), len(rooms[0])
        def dfs(r, c, d):
            if r < 0 or c < 0 or r == R or c == C or rooms[r][c] == -1: return
            if rooms[r][c] != INF and rooms[r][c] <= d and d > 0: return
            if d > 0 and rooms[r][c] == 0: return
            rooms[r][c] = d
            for nr, nc in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)):
                if 0 <= nr < R and 0 <= nc < C and rooms[nr][nc] == INF:
                    dfs(nr, nc, d + 1)
        for r in range(R):
            for c in range(C):
                if rooms[r][c] == 0: dfs(r, c, 0)
''',
    ],
    guide=dict(
        prereqs="BFS gives shortest paths in unweighted graphs; multi-source BFS (lesson *DFS and BFS on grids and adjacency lists*).",
        intuition=r"""
Running a BFS from each gate separately costs O(gates · m · n). Instead, put **all gates in the queue
at once** (distance 0). BFS then expands in rings: all cells at distance 1 from *some* gate, then
distance 2, ... The first time a room is reached is via its nearest gate, so its value is final —
which is why `rooms[nr][nc] == INF` doubles as the "unvisited" test.
""",
        hints=[
            "BFS from a single source finds shortest distances in an unweighted grid. What if there are many sources?",
            "Seed one queue with every gate at once. Why is the first visit to a room guaranteed to come from its nearest gate?",
            "Pop (r, c); for each in-bounds neighbour still equal to INF set it to rooms[r][c] + 1 and enqueue it.",
        ],
        brute_force="From every empty room, BFS until you hit a gate: O((m·n)²). Or BFS from each gate and keep the minimum: O(g·m·n).",
        approach=r"""
1. Enqueue every cell with value `0`.
2. Standard BFS: for each popped cell, any `INF` neighbour gets `dist + 1` and is enqueued.
3. Walls (`-1`) and already-set cells are never `INF`, so they're skipped automatically.

**Dry run** (example): queue starts with gates (0,2) and (3,0). Ring 1: (0,3)=1, (1,2)=1, (2,0)=1. Ring 2: (1,1)=2, (2,2)=2, (1,0)=2. Ring 3: (0,0)=3, (3,2)=3. Ring 4: (3,3)=4.
""",
        complexity="O(m·n) time — each cell enters the queue once. O(m·n) space for the queue.",
        pitfalls=r"""
- BFS from only one gate, or separate BFS per gate without taking minimums (wrong solution #1).
- DFS does **not** produce shortest distances unless you keep revisiting with smaller values (slow, and easy to get wrong — wrong solution #2 stops relaxing too early).
- Overwriting gates (`0`) when they're reached from another gate.
- Returning a new grid — the judge inspects the argument you were given.
""",
        follow_up="*Rotting Oranges* and *01 Matrix* use the identical multi-source BFS. *Shortest Distance from All Buildings* sums BFS distances from every source instead.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="rotting-oranges",
    title="Rotting Oranges",
    difficulty="Medium",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/rotting-oranges/",
    neetcode="https://neetcode.io/problems/rotting-fruit",
    entry="orangesRotting",
    description=r"""
A crate is an `m × n` grid: `0` is an empty slot, `1` a fresh orange, `2` a rotten orange. Every
minute, each fresh orange that is directly up/down/left/right of a rotten orange becomes rotten.

Return the number of minutes until **no fresh orange remains**, or `-1` if some fresh orange can
never rot. If there are no fresh oranges at the start, the answer is `0`.

**Constraints:** `1 <= m, n <= 10` on LeetCode (tests here go larger), cells are `0`, `1` or `2`.

**Example 1:** `[[2,1,1],[1,1,0],[0,1,1]]` → `4`

**Example 2:** `[[2,1,1],[0,1,1],[1,0,1]]` → `-1` (the bottom-left orange is isolated)

**Example 3:** `[[0,2]]` → `0`
""",
    starter='''class Solution:
    def orangesRotting(self, grid: List[List[int]]) -> int:
        pass
''',
    solution='''from collections import deque

class Solution:
    def orangesRotting(self, grid):
        R, C = len(grid), len(grid[0])
        g = [row[:] for row in grid]
        q = deque((r, c) for r in range(R) for c in range(C) if g[r][c] == 2)
        fresh = sum(row.count(1) for row in g)
        minutes = 0
        while q and fresh:
            for _ in range(len(q)):          # one BFS level = one minute
                r, c = q.popleft()
                for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                    if 0 <= nr < R and 0 <= nc < C and g[nr][nc] == 1:
                        g[nr][nc] = 2
                        fresh -= 1
                        q.append((nr, nc))
            minutes += 1
        return minutes if fresh == 0 else -1
''',
    tests=[
        [[[2, 1, 1], [1, 1, 0], [0, 1, 1]]],
        [[[2, 1, 1], [0, 1, 1], [1, 0, 1]]],
        [[[0, 2]]],
        [[[0]]],
        [[[1]]],
        [[[2]]],
        [[[2, 2], [1, 1], [0, 0], [2, 0]]],
        [[[2, 1, 1, 1, 1, 1, 1, 2]]],
        [[[1, 2, 1, 1, 2, 1, 1]]],
        [[[2, 0, 1]]],
        [_oranges(_R, 40, 40, 0.1, 0.01)],
        [_oranges(_R, 80, 80, 0.05, 0.002)],
        [[[2] + [1] * 99] + [[1] * 100 for _ in range(99)]],
    ],
    examples=3,
    wrong_solutions=[
        '''from collections import deque
class Solution:
    def orangesRotting(self, grid):
        R, C = len(grid), len(grid[0])
        q = deque((r, c, 0) for r in range(R) for c in range(C) if grid[r][c] == 2)
        t = 0
        while q:
            r, c, t = q.popleft()
            for nr, nc in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)):
                if 0 <= nr < R and 0 <= nc < C and grid[nr][nc] == 1:
                    grid[nr][nc] = 2; q.append((nr, nc, t + 1))
        return t
''',
        '''from collections import deque
class Solution:
    def orangesRotting(self, grid):
        R, C = len(grid), len(grid[0])
        g = [row[:] for row in grid]
        q = deque((r, c) for r in range(R) for c in range(C) if g[r][c] == 2)
        fresh = sum(row.count(1) for row in g); minutes = 0
        while q:
            for _ in range(len(q)):
                r, c = q.popleft()
                for nr, nc in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)):
                    if 0 <= nr < R and 0 <= nc < C and g[nr][nc] == 1:
                        g[nr][nc] = 2; fresh -= 1; q.append((nr, nc))
            minutes += 1
        return minutes if fresh == 0 else -1
''',
    ],
    guide=dict(
        prereqs="Multi-source BFS processed level by level (lesson *DFS and BFS on grids and adjacency lists*).",
        intuition=r"""
Rot spreads exactly like a BFS wavefront started from **all rotten oranges simultaneously**. Each
BFS level is one minute. Count the fresh oranges up front; decrement as they rot. When the
wave stops, any leftover fresh orange is unreachable → `-1`.
""",
        hints=[
            "Several oranges start rotten and spread at the same time — which traversal models 'spreading one step per minute'?",
            "Put all rotten oranges in the queue first. How do you know when one minute has passed?",
            "Process the queue in levels (for _ in range(len(q))), count minutes per level, stop when fresh == 0, and return −1 if fresh oranges remain.",
        ],
        brute_force="Simulate minute by minute: scan the whole grid, rot neighbours of rotten cells (using a copy so changes don't cascade within the minute). O((m·n)²) worst case.",
        approach=r"""
1. Queue all `2` cells; `fresh = count of 1`.
2. While the queue is non-empty **and** `fresh > 0`: process exactly `len(q)` cells (one level), rotting fresh neighbours; `minutes += 1`.
3. Return `minutes` if `fresh == 0` else `-1`.

**Dry run** `[[2,1,1],[1,1,0],[0,1,1]]`: fresh = 6. Min 1: (0,1),(1,0). Min 2: (0,2),(1,1). Min 3: (2,1). Min 4: (2,2). fresh = 0 → 4.

The `and fresh` condition matters: without it the loop runs one extra (empty) level and overcounts by one.
""",
        complexity="O(m·n) time and space.",
        pitfalls=r"""
- Counting the final empty level as a minute (wrong solution #2 returns 5 for Example 1).
- Forgetting the unreachable case (wrong solution #1 never returns −1).
- Returning `-1` when there are no fresh oranges at all — the answer is `0`.
- Rotting oranges in place during a sequential scan (changes cascade within one minute).
""",
        follow_up="Same template: *Walls and Gates*, *01 Matrix*, *As Far from Land as Possible*.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="pacific-atlantic-water-flow",
    title="Pacific Atlantic Water Flow",
    difficulty="Medium",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/pacific-atlantic-water-flow/",
    neetcode="https://neetcode.io/problems/pacific-atlantic-water-flow",
    entry="pacificAtlantic",
    compare="unordered",
    description=r"""
An island is described by an `m × n` grid `heights` of elevations. The **Pacific** touches the
island's top and left edges; the **Atlantic** touches the bottom and right edges.

Rain on a cell flows to an orthogonal neighbour whose height is **less than or equal to** the
current one, and from a border cell straight into the adjacent ocean. Return the coordinates
`[r, c]` of every cell from which water can reach **both** oceans, in any order.

**Constraints:** `1 <= m, n <= 200`, `0 <= heights[r][c] <= 10^5`.

**Example:**
```
heights = [[1,2,2,3,5],
           [3,2,3,4,4],
           [2,4,5,3,1],
           [6,7,1,4,5],
           [5,1,1,2,4]]
-> [[0,4],[1,3],[1,4],[2,2],[3,0],[3,1],[4,0]]
```

**Example 2:** `[[1]]` → `[[0,0]]`
""",
    starter='''class Solution:
    def pacificAtlantic(self, heights: List[List[int]]) -> List[List[int]]:
        pass
''',
    solution='''from collections import deque

class Solution:
    def pacificAtlantic(self, heights):
        R, C = len(heights), len(heights[0])

        def reach(starts):
            seen = set(starts)
            q = deque(starts)
            while q:
                r, c = q.popleft()
                for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                    if (0 <= nr < R and 0 <= nc < C and (nr, nc) not in seen
                            and heights[nr][nc] >= heights[r][c]):   # walk uphill from the ocean
                        seen.add((nr, nc))
                        q.append((nr, nc))
            return seen

        pac = reach([(0, c) for c in range(C)] + [(r, 0) for r in range(1, R)])
        atl = reach([(R - 1, c) for c in range(C)] + [(r, C - 1) for r in range(R - 1)])
        return [[r, c] for r, c in sorted(pac & atl)]
''',
    tests=[
        [[[1, 2, 2, 3, 5], [3, 2, 3, 4, 4], [2, 4, 5, 3, 1], [6, 7, 1, 4, 5], [5, 1, 1, 2, 4]]],
        [[[1]]],
        [[[1, 2, 3]]],
        [[[3], [2], [1]]],
        [[[2, 1], [1, 2]]],
        [[[1, 1], [1, 1]]],
        [[[10, 10, 10], [10, 1, 10], [10, 10, 10]]],
        [[[1, 2, 3], [8, 9, 4], [7, 6, 5]]],
        [[[3, 3, 3, 3, 3, 3], [3, 0, 3, 3, 0, 3], [3, 3, 3, 3, 3, 3]]],
        [[[_R.randint(0, 9) for _ in range(40)] for _ in range(40)]],
        [[[_R.randint(0, 100000) for _ in range(120)] for _ in range(120)]],
        [[[r + c for c in range(100)] for r in range(100)]],
    ],
    examples=2,
    wrong_solutions=[
        '''from collections import deque
class Solution:
    def pacificAtlantic(self, heights):
        R, C = len(heights), len(heights[0])
        def reach(starts):
            seen = set(starts); q = deque(starts)
            while q:
                r, c = q.popleft()
                for nr, nc in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)):
                    if 0 <= nr < R and 0 <= nc < C and (nr, nc) not in seen and heights[nr][nc] > heights[r][c]:
                        seen.add((nr, nc)); q.append((nr, nc))
            return seen
        pac = reach([(0, c) for c in range(C)] + [(r, 0) for r in range(R)])
        atl = reach([(R-1, c) for c in range(C)] + [(r, C-1) for r in range(R)])
        return [list(x) for x in pac & atl]
''',
        '''from collections import deque
class Solution:
    def pacificAtlantic(self, heights):
        R, C = len(heights), len(heights[0])
        def reach(starts):
            seen = set(starts); q = deque(starts)
            while q:
                r, c = q.popleft()
                for nr, nc in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)):
                    if 0 <= nr < R and 0 <= nc < C and (nr, nc) not in seen and heights[nr][nc] >= heights[r][c]:
                        seen.add((nr, nc)); q.append((nr, nc))
            return seen
        pac = reach([(0, c) for c in range(C)])
        atl = reach([(R-1, c) for c in range(C)])
        return [list(x) for x in pac & atl]
''',
    ],
    guide=dict(
        prereqs="Multi-source BFS/DFS; reversing the direction of a search (lesson *DFS and BFS on grids and adjacency lists*).",
        intuition=r"""
Asking "can water from this cell reach the ocean?" for every cell repeats a lot of work. Flip it:
start **from the ocean** and walk *uphill* (to neighbours with height ≥ current). Every cell you reach
can drain into that ocean. Do this once from the Pacific border and once from the Atlantic border;
the answer is the intersection of the two reachable sets.
""",
        hints=[
            "Searching downhill from every cell costs O((mn)²). Is there a direction of search that does the work once?",
            "Reverse the flow: from the ocean edges, which cells could have sent water here?",
            "Multi-source BFS from the top+left edges (moving to neighbours with height ≥ current) and from bottom+right edges; return the intersection.",
        ],
        brute_force="For each cell, DFS downhill (height ≤ current) and record whether you touch each ocean's border. O((m·n)²) time.",
        approach=r"""
1. `pac = reach(top row + left column)`, `atl = reach(bottom row + right column)`.
2. `reach` is multi-source BFS that moves from `(r,c)` to a neighbour with `heights[n] >= heights[r][c]`.
3. Return cells in both sets.

**Dry run** on Example 1: (2,2) with height 5 — the Pacific search climbs 1→2→... e.g. (0,2)=2 → (1,2)=3 → (2,2)=5 ✓; the Atlantic search climbs (4,2)=1 → (3,2)=1? no, from (2,4)=1 → (2,3)=3 → (2,2)=5 ✓. So (2,2) is in both.
""",
        complexity="O(m·n) time: each search visits each cell once. O(m·n) space.",
        pitfalls=r"""
- Using `>` instead of `>=` — water flows across equal heights (wrong solution #1).
- Seeding only the top row / bottom row and forgetting the side columns (wrong solution #2).
- Searching downhill from the ocean (the wrong direction).
""",
        follow_up="Any 'can X reach a target set' query over many starting points benefits from reversing the search from the targets. Related: *Surrounded Regions* (search from the border).",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="surrounded-regions",
    title="Surrounded Regions",
    difficulty="Medium",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/surrounded-regions/",
    neetcode="https://neetcode.io/problems/surrounded-regions",
    entry="solve",
    inplace_arg=0,
    description=r"""
You get an `m × n` board of `"X"` and `"O"` strings. A region is a 4-directionally connected group of
`"O"` cells. A region is **captured** when none of its cells lies on the board's border — it is
completely enclosed by `"X"`. Flip every cell of every captured region to `"X"`, **in place**.
Regions touching the border survive unchanged. Return nothing.

**Constraints:** `1 <= m, n <= 200`.

**Example:**
```
X X X X        X X X X
X O O X  --->  X X X X
X X O X        X X X X
X O X X        X O X X     (the bottom O touches the border)
```

**Example 2:** `[["X"]]` → `[["X"]]`
""",
    starter='''class Solution:
    def solve(self, board: List[List[str]]) -> None:
        """
        Do not return anything, modify board in-place instead.
        """
        pass
''',
    solution='''from collections import deque

class Solution:
    def solve(self, board):
        R, C = len(board), len(board[0])
        q = deque()
        for r in range(R):
            for c in range(C):
                if (r in (0, R - 1) or c in (0, C - 1)) and board[r][c] == "O":
                    board[r][c] = "S"          # safe: connected to the border
                    q.append((r, c))
        while q:
            r, c = q.popleft()
            for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if 0 <= nr < R and 0 <= nc < C and board[nr][nc] == "O":
                    board[nr][nc] = "S"
                    q.append((nr, nc))
        for r in range(R):
            for c in range(C):
                board[r][c] = "O" if board[r][c] == "S" else "X"
''',
    tests=[
        [[["X", "X", "X", "X"], ["X", "O", "O", "X"], ["X", "X", "O", "X"], ["X", "O", "X", "X"]]],
        [[["X"]]],
        [[["O"]]],
        [[["O", "O"], ["O", "O"]]],
        [[["X", "X", "X"], ["X", "O", "X"], ["X", "X", "X"]]],
        [[["O", "X", "X", "O", "X"], ["X", "O", "O", "X", "O"], ["X", "O", "X", "O", "X"], ["O", "X", "O", "O", "O"], ["X", "X", "O", "X", "O"]]],
        [[["X", "O", "X"], ["X", "O", "X"], ["X", "O", "X"]]],
        [[["X", "X", "X", "X", "X"], ["X", "O", "O", "O", "X"], ["X", "O", "X", "O", "X"], ["X", "O", "O", "O", "X"], ["X", "X", "X", "X", "X"]]],
        [_grid(_R, 60, 60, 0.55, "O", "X")],
        [_grid(_R, 120, 120, 0.45, "O", "X")],
        [[["X"] * 100] + [["X"] + ["O"] * 98 + ["X"] for _ in range(98)] + [["X"] * 100]],
        [[["O"] * 100] + [["X"] + ["O"] * 98 + ["X"] for _ in range(98)] + [["X"] * 100]],
    ],
    examples=1,
    wrong_solutions=[
        '''class Solution:
    def solve(self, board):
        R, C = len(board), len(board[0])
        for r in range(1, R - 1):
            for c in range(1, C - 1):
                if board[r][c] == "O": board[r][c] = "X"
''',
        '''class Solution:
    def solve(self, board):
        R, C = len(board), len(board[0])
        for r in range(1, R - 1):
            for c in range(1, C - 1):
                if board[r][c] == "O" and all(board[nr][nc] != "O" or not (nr in (0, R-1) or nc in (0, C-1))
                                               for nr, nc in ((r+1,c),(r-1,c),(r,c+1),(r,c-1))):
                    board[r][c] = "X"
''',
    ],
    guide=dict(
        prereqs="Flood fill; multi-source search from the border (lesson *DFS and BFS on grids and adjacency lists*).",
        intuition=r"""
Deciding whether a region is enclosed requires looking at the whole region. The complement is
easier: an `O` **survives** exactly when it is connected to a border `O`. So flood-fill from every
border `O`, tagging what you reach as safe. Afterwards every untagged `O` is captured.
""",
        hints=[
            "Instead of asking which O's are surrounded, ask which O's escape. What do they all have in common?",
            "Start a BFS/DFS from every 'O' on the border and mark everything you reach with a temporary symbol.",
            "Final pass: temporary symbol → 'O', every remaining 'O' → 'X'.",
        ],
        brute_force="For each `O` region, flood-fill it and check whether any cell touches the border; flip it if not. Also O(m·n) if done with a visited set, but more bookkeeping.",
        approach=r"""
1. Queue every border cell holding `"O"`, relabel it `"S"`.
2. BFS: neighbours that are `"O"` become `"S"`.
3. Sweep: `"S"` → `"O"`, everything else → `"X"`.

**Dry run** on the example: only (3,1) is a border `O`; it has no `O` neighbours. Sweep turns (1,1),(1,2),(2,2) into `X` and restores (3,1).
""",
        complexity="O(m·n) time and O(m·n) worst-case queue space.",
        pitfalls=r"""
- Flipping all interior `O`s without checking connectivity to the border (wrong solution #1).
- Checking only immediate neighbours instead of whole regions (wrong solution #2).
- Building a new board — the judge reads the board you were given.
- Recursive DFS from the border on a 200×200 board can blow the recursion limit; use a queue.
""",
        follow_up="Union-find variant: union all border `O`s with a virtual 'border' node, union adjacent `O`s, then flip every `O` not connected to the virtual node. Related: *Number of Enclaves*, *Pacific Atlantic Water Flow*.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="course-schedule",
    title="Course Schedule",
    difficulty="Medium",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/course-schedule/",
    neetcode="https://neetcode.io/problems/course-schedule",
    entry="canFinish",
    description=r"""
There are `numCourses` courses labelled `0 .. numCourses-1`. Each pair `prerequisites[i] = [a, b]`
means course `b` must be completed **before** course `a`. Return `True` if it is possible to take
every course, and `False` otherwise (i.e. when the requirements are circular).

**Constraints:** `1 <= numCourses <= 2000`, `0 <= len(prerequisites) <= 5000`, pairs are distinct.

**Example 1:** `numCourses = 2, prerequisites = [[1,0]]` → `True` (take 0, then 1)

**Example 2:** `numCourses = 2, prerequisites = [[1,0],[0,1]]` → `False`
""",
    starter='''class Solution:
    def canFinish(self, numCourses: int, prerequisites: List[List[int]]) -> bool:
        pass
''',
    solution='''from collections import deque

class Solution:
    def canFinish(self, numCourses, prerequisites):
        adj = [[] for _ in range(numCourses)]
        indeg = [0] * numCourses
        for a, b in prerequisites:
            adj[b].append(a)
            indeg[a] += 1
        q = deque(i for i in range(numCourses) if indeg[i] == 0)
        taken = 0
        while q:
            u = q.popleft()
            taken += 1
            for v in adj[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)
        return taken == numCourses
''',
    tests=[
        [2, [[1, 0]]],
        [2, [[1, 0], [0, 1]]],
        [1, []],
        [3, []],
        [3, [[0, 1], [1, 2], [2, 0]]],
        [4, [[1, 0], [2, 0], [3, 1], [3, 2]]],
        [5, [[1, 0], [2, 1], [3, 2], [1, 3]]],
        [5, [[1, 4], [2, 4], [3, 1], [3, 2]]],
        [3, [[1, 0], [1, 2], [0, 1]]],
        [2000, _dag(_R, 2000, 5000)],
        [2000, [[i + 1, i] for i in range(1999)]],
        [2000, [[i + 1, i] for i in range(1999)] + [[0, 1999]]],
        [1000, _dag(random.Random(9), 1000, 3000)],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def canFinish(self, numCourses, prerequisites):
        s = {(a, b) for a, b in prerequisites}
        return not any((b, a) in s for a, b in prerequisites)
''',
        '''class Solution:
    def canFinish(self, numCourses, prerequisites):
        return len(prerequisites) < numCourses
''',
    ],
    guide=dict(
        prereqs="Directed graphs, in-degrees and topological sort (lesson *Cycle detection and topological sort*).",
        intuition=r"""
Courses are vertices; a prerequisite `[a, b]` is a directed edge `b → a`. All courses can be taken
exactly when this graph has **no directed cycle**, i.e. it is a DAG and has a topological order.
Kahn's algorithm repeatedly takes a course with no remaining prerequisites; if it gets stuck before
taking all courses, the leftover courses lie on or behind a cycle.
""",
        hints=[
            "Model courses and prerequisites as a graph. When is it impossible to finish?",
            "Which courses can you take first? What happens to the other courses once you take one?",
            "Kahn's algorithm: in-degree array, queue of in-degree-0 courses; count how many you pop. Equal to numCourses ⇔ no cycle.",
        ],
        brute_force="For each course, DFS to see whether it can reach itself: O(V · (V + E)). Only checking 2-cycles (wrong solution #1) misses longer cycles.",
        approach=r"""
**Kahn (BFS)**: build `adj[b].append(a)`, `indeg[a] += 1`. Queue every course with in-degree 0. Pop, count, decrement neighbours' in-degree, enqueue those that hit 0. Return `count == numCourses`.

**DFS three-colour alternative**: state 0 = unvisited, 1 = on the current path, 2 = finished. Reaching a state-1 vertex means a back edge → cycle.

**Dry run** `5, [[1,0],[2,1],[3,2],[1,3]]`: indeg = [0,2,1,1,0]. Queue {0, 4}. Pop 0 → indeg[1] = 1. Pop 4. Queue empty, taken = 2 < 5 → `False` (cycle 1→2→3→1).
""",
        complexity="O(V + E) time and space.",
        pitfalls=r"""
- Reversing the edge direction (harmless for cycle detection, but it matters for *Course Schedule II*).
- Only detecting 2-cycles.
- Using a single `visited` set in DFS: a vertex visited in an *earlier* DFS is not a cycle — you need the "on current path" state.
- Recursive DFS on a 2,000-long chain overflows Python's default recursion limit; Kahn's algorithm is iterative.
""",
        follow_up="*Course Schedule II* returns the order itself; *Course Schedule IV* answers reachability queries (transitive closure).",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="course-schedule-ii",
    title="Course Schedule II",
    difficulty="Medium",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/course-schedule-ii/",
    neetcode="https://neetcode.io/problems/course-schedule-ii",
    entry="findOrder",
    checker=_COURSE2_CHECK,
    description=r"""
Same setting as *Course Schedule*: `numCourses` courses `0..n-1`, and `[a, b]` means `b` must be taken
before `a`. Return **an order** in which all courses can be taken. Many orders may be valid —
any one is accepted (the judge checks it). If it is impossible, return an empty list.

**Constraints:** `1 <= numCourses <= 2000`, `0 <= len(prerequisites) <= numCourses·(numCourses-1)`, pairs distinct, `a != b`.

**Example 1:** `2, [[1,0]]` → `[0,1]`

**Example 2:** `4, [[1,0],[2,0],[3,1],[3,2]]` → `[0,1,2,3]` or `[0,2,1,3]`

**Example 3:** `1, []` → `[0]`
""",
    starter='''class Solution:
    def findOrder(self, numCourses: int, prerequisites: List[List[int]]) -> List[int]:
        pass
''',
    solution='''from collections import deque

class Solution:
    def findOrder(self, numCourses, prerequisites):
        adj = [[] for _ in range(numCourses)]
        indeg = [0] * numCourses
        for a, b in prerequisites:
            adj[b].append(a)
            indeg[a] += 1
        q = deque(i for i in range(numCourses) if indeg[i] == 0)
        order = []
        while q:
            u = q.popleft()
            order.append(u)
            for v in adj[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)
        return order if len(order) == numCourses else []
''',
    tests=[
        [2, [[1, 0]]],
        [4, [[1, 0], [2, 0], [3, 1], [3, 2]]],
        [1, []],
        [2, [[0, 1], [1, 0]]],
        [3, []],
        [3, [[0, 1], [0, 2], [1, 2]]],
        [6, [[5, 4], [4, 3], [3, 2], [2, 1], [1, 0]]],
        [6, [[0, 5], [1, 5], [2, 4], [3, 4], [4, 0]]],
        [4, [[1, 0], [2, 1], [3, 2], [1, 3]]],
        [2000, _dag(random.Random(21), 2000, 6000)],
        [2000, [[i, i + 1] for i in range(1999)]],
        [500, _dag(random.Random(22), 500, 3000)],
        [300, [[i, i + 1] for i in range(299)] + [[299, 150]]],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def findOrder(self, numCourses, prerequisites):
        return list(range(numCourses))
''',
        '''from collections import deque
class Solution:
    def findOrder(self, numCourses, prerequisites):
        adj = [[] for _ in range(numCourses)]; indeg = [0] * numCourses
        for a, b in prerequisites:
            adj[a].append(b); indeg[b] += 1
        q = deque(i for i in range(numCourses) if indeg[i] == 0); order = []
        while q:
            u = q.popleft(); order.append(u)
            for v in adj[u]:
                indeg[v] -= 1
                if indeg[v] == 0: q.append(v)
        return order if len(order) == numCourses else []
''',
    ],
    guide=dict(
        prereqs="*Course Schedule*; topological sort (Kahn's algorithm and the DFS post-order method).",
        intuition=r"""
Kahn's algorithm doesn't just detect cycles — the order in which it pops vertices **is** a
topological order: a course is popped only after all its prerequisites have been popped. If the
order contains every course, return it; otherwise there is a cycle and you return `[]`.
""",
        hints=[
            "You already know how to detect a cycle with Kahn's algorithm. What does the sequence of popped vertices represent?",
            "Edge direction matters now: [a, b] means b → a (b first).",
            "Record each popped vertex; return the list if its length is numCourses, else [].",
        ],
        brute_force="Repeatedly scan all courses for one whose prerequisites are all taken: O(V · (V + E)).",
        approach=r"""
Kahn with `order.append(u)` at each pop.

**Dry run** `4, [[1,0],[2,0],[3,1],[3,2]]`: indeg = [0,1,1,2]. Queue [0]. Pop 0 → indeg 1:0, 2:0 → queue [1,2]. Pop 1 → indeg[3] = 1. Pop 2 → indeg[3] = 0 → queue [3]. Pop 3. Order `[0,1,2,3]`.

**DFS alternative**: three-colour DFS; append a vertex to a list when it **finishes** (post-order) — for edges `b → a` this produces reverse topological order, so reverse it at the end. A gray-to-gray edge means a cycle.
""",
        complexity="O(V + E) time and space.",
        pitfalls=r"""
- Building edges `a → b` gives a valid order of the *reversed* graph, which is backwards (wrong solution #2).
- Returning a partial order when a cycle exists — must return `[]`.
- Forgetting isolated courses (in-degree 0, no edges) — they still must appear.
""",
        follow_up="Need the lexicographically smallest order? Replace the queue with a min-heap. Need minimum number of semesters? Process Kahn's algorithm level by level (*Parallel Courses*).",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="graph-valid-tree",
    title="Graph Valid Tree",
    difficulty="Medium",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/graph-valid-tree/",
    neetcode="https://neetcode.io/problems/valid-tree",
    entry="validTree",
    description=r"""
You are given `n` nodes labelled `0..n-1` and a list of **undirected** edges. Return `True` if these
edges form a valid **tree** — the graph is connected and contains no cycle — and `False` otherwise.

**Constraints:** `1 <= n <= 2000`, `0 <= len(edges) <= 5000`, no repeated edges, no self-loops.

**Example 1:** `n = 5, edges = [[0,1],[0,2],[0,3],[1,4]]` → `True`

**Example 2:** `n = 5, edges = [[0,1],[1,2],[2,3],[1,3],[1,4]]` → `False` (cycle 1–2–3)
""",
    starter='''class Solution:
    def validTree(self, n: int, edges: List[List[int]]) -> bool:
        pass
''',
    solution='''class Solution:
    def validTree(self, n, edges):
        if len(edges) != n - 1:
            return False
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for a, b in edges:
            ra, rb = find(a), find(b)
            if ra == rb:
                return False          # this edge closes a cycle
            parent[ra] = rb
        return True                   # n-1 edges and acyclic => connected
''',
    tests=[
        [5, [[0, 1], [0, 2], [0, 3], [1, 4]]],
        [5, [[0, 1], [1, 2], [2, 3], [1, 3], [1, 4]]],
        [1, []],
        [2, []],
        [2, [[1, 0]]],
        [4, [[0, 1], [2, 3]]],
        [4, [[0, 1], [1, 2], [2, 0]]],
        [4, [[0, 1], [1, 2], [2, 0], [0, 3]]],
        [6, [[0, 1], [0, 2], [3, 4], [4, 5], [5, 3]]],
        [2000, _tree_edges(_R, 2000)],
        [1999, [[a - 1, b - 1] for a, b in _redundant(random.Random(5), 1999)[0][:-1]]],
        [1999, [[a - 1, b - 1] for a, b in _redundant(random.Random(6), 1999)[0]]],
        [2000, [[i, i + 1] for i in range(1999)]],
        [2000, [[i, i + 1] for i in range(1000)] + [[i, i + 1] for i in range(1001, 1999)] + [[0, 2]]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def validTree(self, n, edges):
        return len(edges) == n - 1
''',
        '''class Solution:
    def validTree(self, n, edges):
        parent = list(range(n))
        def find(x):
            while parent[x] != x: x = parent[x]
            return x
        for a, b in edges:
            ra, rb = find(a), find(b)
            if ra == rb: return False
            parent[ra] = rb
        return True
''',
    ],
    guide=dict(
        prereqs="Trees as graphs; union-find (lesson *Union-find*) or DFS with a parent pointer.",
        intuition=r"""
A graph on `n` vertices is a tree iff it has **exactly `n − 1` edges and no cycle** (equivalently,
`n − 1` edges and connected). Check the edge count first; then add edges one by one with union-find —
if an edge joins two vertices already in the same set, it closes a cycle.
""",
        hints=[
            "List the properties of a tree in graph terms. How many edges does a tree on n nodes have?",
            "If there are exactly n − 1 edges, one more property suffices. Which one is easy to check with union-find?",
            "Return False if len(edges) != n − 1; union each edge, returning False when find(a) == find(b); else True.",
        ],
        brute_force="DFS from node 0 with a parent pointer to detect cycles, then check every node was visited. Also O(V + E) — a fine alternative.",
        approach=r"""
1. `len(edges) != n - 1` → `False`.
2. Union-find over edges; a repeated root means a cycle → `False`.
3. Otherwise `True` (n−1 edges + no cycle forces connectivity: an acyclic forest with c components has n − c edges, so c = 1).

**Dry run** Example 2: 5 edges ≠ 4 → `False` immediately. For `4, [[0,1],[2,3]]`: 2 edges ≠ 3 → `False` (disconnected).
""",
        complexity="O(E · α(n)) ≈ O(E) with path compression; O(n) space.",
        pitfalls=r"""
- Only checking the edge count (wrong solution #1 accepts a cycle plus an isolated vertex).
- Only checking for cycles (wrong solution #2 accepts a disconnected forest).
- In DFS cycle detection on an undirected graph, the edge back to your parent is not a cycle.
""",
        follow_up="*Redundant Connection* finds the edge that creates the cycle; *Number of Connected Components* counts components with the same structure.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="number-of-connected-components-in-an-undirected-graph",
    title="Number of Connected Components in an Undirected Graph",
    difficulty="Medium",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/number-of-connected-components-in-an-undirected-graph/",
    neetcode="https://neetcode.io/problems/count-connected-components",
    entry="countComponents",
    description=r"""
Given `n` vertices labelled `0..n-1` and a list of undirected edges `[a, b]`, return the number of
**connected components** — maximal groups of vertices where every pair is joined by some path.
An isolated vertex is a component by itself.

**Constraints:** `1 <= n <= 2000`, `0 <= len(edges) <= 5000`, no duplicate edges, `a != b`.

**Example 1:** `n = 5, edges = [[0,1],[1,2],[3,4]]` → `2`

**Example 2:** `n = 5, edges = [[0,1],[1,2],[2,3],[3,4]]` → `1`
""",
    starter='''class Solution:
    def countComponents(self, n: int, edges: List[List[int]]) -> int:
        pass
''',
    solution='''class Solution:
    def countComponents(self, n, edges):
        parent = list(range(n))
        rank = [0] * n

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        comps = n
        for a, b in edges:
            ra, rb = find(a), find(b)
            if ra != rb:
                if rank[ra] < rank[rb]:
                    ra, rb = rb, ra
                parent[rb] = ra
                if rank[ra] == rank[rb]:
                    rank[ra] += 1
                comps -= 1
        return comps
''',
    tests=[
        [5, [[0, 1], [1, 2], [3, 4]]],
        [5, [[0, 1], [1, 2], [2, 3], [3, 4]]],
        [1, []],
        [4, []],
        [3, [[0, 1], [1, 2], [2, 0]]],
        [6, [[0, 1], [2, 3], [4, 5], [1, 2], [3, 0]]],
        [7, [[0, 6], [1, 5], [2, 4]]],
        [2000, _forest_edges(_R, 2000, 1500)],
        [2000, _forest_edges(_R, 2000, 1999)],
        [2000, [[i, (i * 7 + 3) % 2000] for i in range(2000) if i != (i * 7 + 3) % 2000][:1200]],
        [2000, [[i, j] for i in range(0, 60) for j in range(i + 1, 60)][:1700]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def countComponents(self, n, edges):
        return n - len(edges)
''',
        '''class Solution:
    def countComponents(self, n, edges):
        seen = set()
        for a, b in edges: seen.add(a); seen.add(b)
        return n - len(seen) + (1 if edges else 0)
''',
    ],
    guide=dict(
        prereqs="Union-find with path compression and union by rank (lesson *Union-find*); or DFS over an adjacency list.",
        intuition=r"""
Start with every vertex in its own component (`n` components). Each edge that connects two
**different** components merges them, reducing the count by one. Edges inside a component (which
would form a cycle) change nothing. Union-find answers "same component?" in near-constant time.
""",
        hints=[
            "How many components are there with zero edges? What can a single edge do to that number?",
            "An edge only reduces the count when its endpoints are currently in different components.",
            "Union-find: comps = n; for each edge, if find(a) != find(b): union and comps -= 1.",
        ],
        brute_force="Build an adjacency list and run DFS/BFS from every unvisited vertex, counting starts. Also O(V + E) — an equally good answer.",
        approach=r"""
Union-find with path compression (`parent[x] = parent[parent[x]]` while walking up) and union by rank.

**Dry run** `5, [[0,1],[1,2],[3,4]]`: comps 5 → union(0,1) 4 → union(1,2) 3 → union(3,4) 2. Answer 2.

With a cycle `3, [[0,1],[1,2],[2,0]]`: 3 → 2 → 1 → edge (2,0) has equal roots, no change → 1.
""",
        complexity="O(V + E · α(V)) time, O(V) space. α is the inverse Ackermann function (≤ 4 in practice).",
        pitfalls=r"""
- `n - len(edges)` ignores redundant (cycle) edges (wrong solution #1).
- Forgetting isolated vertices when counting via an adjacency map built from edges only.
- Union without `find` (setting `parent[a] = b` directly) corrupts the forest.
""",
        follow_up="*Number of Provinces* is the same problem with an adjacency matrix. *Accounts Merge* uses union-find over email strings.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="redundant-connection",
    title="Redundant Connection",
    difficulty="Medium",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/redundant-connection/",
    neetcode="https://neetcode.io/problems/redundant-connection",
    entry="findRedundantConnection",
    description=r"""
A tree with `n` nodes labelled `1..n` had **one extra edge** added between two different nodes, so
the undirected graph now has exactly `n` edges and exactly one cycle. The edges are given as a list.

Return an edge whose removal turns the graph back into a tree with `n` nodes. If several edges qualify
(all edges of the cycle do), return the one that appears **last** in the input.

**Constraints:** `3 <= n <= 1000`, `len(edges) == n`, `1 <= a < b <= n`, no repeated edges, the graph is connected.

**Example 1:** `[[1,2],[1,3],[2,3]]` → `[2,3]`

**Example 2:** `[[1,2],[2,3],[3,4],[1,4],[1,5]]` → `[1,4]`
""",
    starter='''class Solution:
    def findRedundantConnection(self, edges: List[List[int]]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def findRedundantConnection(self, edges):
        parent = list(range(len(edges) + 1))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for a, b in edges:
            ra, rb = find(a), find(b)
            if ra == rb:
                return [a, b]
            parent[ra] = rb
        return []
''',
    tests=[
        [[[1, 2], [1, 3], [2, 3]]],
        [[[1, 2], [2, 3], [3, 4], [1, 4], [1, 5]]],
        [[[1, 2], [2, 3], [1, 3], [3, 4]]],
        [[[3, 4], [1, 2], [2, 4], [3, 5], [2, 5]]],
        [[[1, 4], [3, 4], [1, 3], [1, 2], [4, 5]]],
        [[[1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [1, 6]]],
        [[[2, 3], [1, 2], [1, 3]]],
        _redundant(random.Random(41), 50),
        _redundant(random.Random(42), 1000),
        _redundant(random.Random(43), 1000),
        [[[i, i + 1] for i in range(1, 1000)] + [[1, 1000]]],
        [[[1, 1000]] + [[i, i + 1] for i in range(1, 1000)]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def findRedundantConnection(self, edges):
        return edges[-1]
''',
        '''class Solution:
    def findRedundantConnection(self, edges):
        seen = set()
        for a, b in edges:
            if a in seen and b in seen: return [a, b]
            seen.add(a); seen.add(b)
        return []
''',
    ],
    guide=dict(
        prereqs="Union-find (lesson *Union-find*).",
        intuition=r"""
Add edges one at a time with union-find. As long as each edge joins two separate components, the
edges so far form a forest. The **first** edge whose endpoints are already connected closes the one
and only cycle. Because the other cycle edges were all added earlier, this edge is also the cycle
edge that appears **last** — exactly what the problem asks for.
""",
        hints=[
            "Process edges in order. When does an edge create a cycle?",
            "You need a fast 'are u and v already connected?' check while edges are being added — union-find.",
            "Return the first edge [a, b] with find(a) == find(b).",
        ],
        brute_force="For each edge from last to first, remove it and check with DFS whether the remainder is a connected tree: O(n²).",
        approach=r"""
Union-find over `1..n`; for each `[a, b]`, if `find(a) == find(b)` return it, else union.

**Dry run** `[[1,2],[2,3],[3,4],[1,4],[1,5]]`: union 1–2, 2–3, 3–4 → {1,2,3,4}. Edge [1,4]: same root → return `[1,4]`.

Why it's the last cycle edge: the cycle's edges all must be present before it closes, and the closing edge is by definition processed after the others.
""",
        complexity="O(n · α(n)) time, O(n) space.",
        pitfalls=r"""
- Returning simply the last input edge (wrong solution #1) — the last edge may be a tree edge.
- "Both endpoints seen before" is not the same as "already connected" (wrong solution #2): the endpoints might be in different components.
- Labels are 1-based: size the parent array `n + 1`.
""",
        follow_up="*Redundant Connection II* makes the graph directed (a rooted tree plus one edge) — you must also handle a node with two parents.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="word-ladder",
    title="Word Ladder",
    difficulty="Hard",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/word-ladder/",
    neetcode="https://neetcode.io/problems/word-ladder",
    entry="ladderLength",
    description=r"""
A **transformation sequence** from `beginWord` to `endWord` is a list of words starting with
`beginWord` and ending with `endWord` where consecutive words differ in **exactly one letter**, and
every word after `beginWord` is in `wordList` (`beginWord` itself doesn't have to be).

Return the **number of words** in the shortest such sequence, or `0` if none exists.

**Constraints:** `1 <= len(beginWord) <= 10`; all words have that same length and are lowercase;
`1 <= len(wordList) <= 5000`; `wordList` has no duplicates; `beginWord != endWord`.

**Example 1:** `"hit", "cog", ["hot","dot","dog","lot","log","cog"]` → `5`
(`hit → hot → dot → dog → cog`)

**Example 2:** `"hit", "cog", ["hot","dot","dog","lot","log"]` → `0` (`cog` is not in the list)
""",
    starter='''class Solution:
    def ladderLength(self, beginWord: str, endWord: str, wordList: List[str]) -> int:
        pass
''',
    solution='''from collections import defaultdict, deque

class Solution:
    def ladderLength(self, beginWord, endWord, wordList):
        words = set(wordList)
        if endWord not in words:
            return 0
        L = len(beginWord)
        buckets = defaultdict(list)          # "h*t" -> ["hot", "hit", ...]
        for w in words | {beginWord}:
            for i in range(L):
                buckets[w[:i] + "*" + w[i + 1:]].append(w)
        seen = {beginWord}
        q = deque([(beginWord, 1)])
        while q:
            w, d = q.popleft()
            if w == endWord:
                return d
            for i in range(L):
                key = w[:i] + "*" + w[i + 1:]
                for nb in buckets[key]:
                    if nb not in seen:
                        seen.add(nb)
                        q.append((nb, d + 1))
                buckets[key] = []            # each bucket only needs expanding once
        return 0
''',
    tests=[
        ["hit", "cog", ["hot", "dot", "dog", "lot", "log", "cog"]],
        ["hit", "cog", ["hot", "dot", "dog", "lot", "log"]],
        ["a", "c", ["a", "b", "c"]],
        ["hot", "dog", ["hot", "dog"]],
        ["hot", "dog", ["hot", "dot", "dog"]],
        ["ab", "cd", ["ad", "cd"]],
        ["abc", "abd", ["abd"]],
        ["red", "tax", ["ted", "tex", "red", "tax", "tad", "den", "rex", "pee"]],
        ["lost", "cost", ["most", "fist", "lost", "cost", "fish"]],
        ["leet", "code", ["lest", "leet", "lose", "code", "lode", "robe", "lost"]],
        _ladder_case(random.Random(51), 2000, 4, "abcdefghij"),
        _ladder_case(random.Random(52), 3000, 5, "abcdef"),
        _ladder_case(random.Random(53), 5000, 6, "abcde"),
        ["aaaaaaaaaa", "bbbbbbbbbb", ["".join("b" if j < i else "a" for j in range(10)) for i in range(1, 11)]],
    ],
    examples=2,
    wrong_solutions=[
        '''from collections import deque
class Solution:
    def ladderLength(self, beginWord, endWord, wordList):
        words = set(wordList); q = deque([(beginWord, 1)]); seen = {beginWord}
        while q:
            w, d = q.popleft()
            if w == endWord: return d
            for i in range(len(w)):
                for ch in "abcdefghijklmnopqrstuvwxyz":
                    nb = w[:i] + ch + w[i+1:]
                    if nb in words and nb not in seen:
                        seen.add(nb); q.append((nb, d + 1))
        return 0
'''.replace("return d", "return d - 1"),
        '''class Solution:
    def ladderLength(self, beginWord, endWord, wordList):
        words = set(wordList)
        if endWord not in words: return 0
        seen = {beginWord}
        def dfs(w, d):
            if w == endWord: return d
            for i in range(len(w)):
                for ch in "abcdefghijklmnopqrstuvwxyz":
                    nb = w[:i] + ch + w[i+1:]
                    if nb in words and nb not in seen:
                        seen.add(nb)
                        r = dfs(nb, d + 1)
                        if r: return r
            return 0
        return dfs(beginWord, 1)
''',
    ],
    guide=dict(
        prereqs="BFS for shortest paths in unweighted graphs (lesson *DFS and BFS on grids and adjacency lists*); hashing wildcard patterns.",
        intuition=r"""
Words are vertices; two words are adjacent when they differ in one letter. The shortest
transformation is the **shortest path**, so use BFS. The challenge is finding neighbours quickly:
comparing every pair costs O(N²·L). Instead, generate neighbours on the fly — either try all
`26·L` one-letter edits and look them up in a set, or group words by **wildcard patterns** such as
`h*t`, where all words sharing a pattern are mutually adjacent.
""",
        hints=[
            "What graph are you searching, and why is BFS (not DFS) the right traversal?",
            "Building the full adjacency list pairwise is O(N²·L). How can you find a word's neighbours without comparing it to every other word?",
            "Map each pattern like 'h*t' to the words that match it. BFS from beginWord with depth starting at 1; return the depth when you pop endWord.",
        ],
        brute_force="Compare every pair of words to build edges (O(N²·L)), then BFS. Too slow when N = 5000 and L = 10 in a strict judge, though it's a valid first step to describe.",
        approach=r"""
1. If `endWord` isn't in the list, return 0.
2. Build `buckets[pattern] → words` for all words plus `beginWord`.
3. BFS from `(beginWord, 1)`. For each pattern of the popped word, enqueue unseen words in that bucket with depth + 1. Clearing a bucket after use avoids rescanning it.
4. Return the depth when `endWord` is popped; 0 if the queue empties.

**Dry run** Example 1: hit(1) → patterns `*it, h*t, hi*` → hot(2) → dot, lot (3) → dog, log (4) → cog (5).
""",
        complexity="O(N · L²) time: N words × L patterns × O(L) to build each pattern string; O(N · L²) space for the buckets.",
        pitfalls=r"""
- Counting edges instead of words (off by one — wrong solution #1).
- DFS finds *a* path, not the shortest (wrong solution #2).
- Forgetting that `endWord` must be in the list.
- Marking visited when popping instead of when pushing — the queue can blow up with duplicates.
""",
        follow_up="**Bidirectional BFS** from both ends (always expanding the smaller frontier) shrinks the search dramatically. *Word Ladder II* returns all shortest sequences (BFS to build a layered DAG, then backtrack).",
    ),
),
]
