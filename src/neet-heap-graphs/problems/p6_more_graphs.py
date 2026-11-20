import random

_R = random.Random(606)


def _bin(rng, r, c, p):
    return [[1 if rng.random() < p else 0 for _ in range(c)] for _ in range(r)]


def _digraph(rng, n, m, acyclic_part=0.5):
    g = [set() for _ in range(n)]
    for _ in range(m):
        a, b = rng.sample(range(n), 2)
        if rng.random() < acyclic_part and a > b:
            a, b = b, a
        g[a].add(b)
    return [[sorted(x) for x in g]]


def _bip(rng, n, m, spoil):
    side = [rng.randint(0, 1) for _ in range(n)]
    g = [set() for _ in range(n)]
    tries = 0
    while m > 0 and tries < 50 * m + 100:
        tries += 1
        a, b = rng.sample(range(n), 2)
        if side[a] != side[b] and b not in g[a]:
            g[a].add(b); g[b].add(a); m -= 1
    for _ in range(spoil):
        a, b = rng.sample(range(n), 2)
        g[a].add(b); g[b].add(a)
    return [[sorted(x) for x in g]]


def _tree(rng, n):
    edges = []
    for v in range(1, n):
        edges.append([rng.randint(max(0, v - 3), v - 1), v])
    rng.shuffle(edges)
    return [n, edges]


def _wgraph(rng, n, m, wmax):
    seen = {}
    for v in range(1, n):
        u = rng.randint(0, v - 1)
        seen[(u, v)] = rng.randint(1, wmax)
    tries = 0
    while len(seen) < m and tries < 20 * m:
        tries += 1
        a, b = sorted(rng.sample(range(n), 2))
        if (a, b) not in seen:
            seen[(a, b)] = rng.randint(1, wmax)
    return [[a, b, w] for (a, b), w in seen.items()]


def _prob(rng, n, m):
    es = _wgraph(rng, n, m, 1)
    edges = [[a, b] for a, b, _ in es]
    probs = [round(rng.uniform(0.05, 1.0), 3) for _ in es]
    s, t = rng.sample(range(n), 2)
    return [n, edges, probs, s, t]


def _diamonds(k, wa=1, wb=1):
    """chain of k diamonds: 2^k shortest paths when both branches cost the same"""
    roads, cur, nxt = [], 0, 1
    for _ in range(k):
        a, b, j = nxt, nxt + 1, nxt + 2
        roads += [[cur, a, wa], [a, j, wa], [cur, b, wb], [b, j, wb]]
        cur, nxt = j, nxt + 3
    return [cur + 1, roads]


PROBLEMS = [
# ---------------------------------------------------------------------------------------------
dict(
    id="island-perimeter",
    title="Island Perimeter",
    difficulty="Easy",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/island-perimeter/",
    neetcode="https://neetcode.io/problems/island-perimeter",
    entry="islandPerimeter",
    description=r"""
A map is a grid of `1`s (land) and `0`s (water). The land cells form **exactly one island**
(connected up/down/left/right) with no lakes inside it, and the grid is surrounded by water. Every
cell is a square with side length 1.

Return the length of the island's outline (its perimeter).

**Constraints:** `1 <= rows, cols <= 100`.

**Example 1:**
```
[[0,1,0,0],
 [1,1,1,0],
 [0,1,0,0],
 [1,1,0,0]]   -> 16
```

**Example 2:** `[[1]]` → `4`. **Example 3:** `[[1,0]]` → `4`.
""",
    starter='''class Solution:
    def islandPerimeter(self, grid: List[List[int]]) -> int:
        pass
''',
    solution='''class Solution:
    def islandPerimeter(self, grid):
        R, C = len(grid), len(grid[0])
        total = 0
        for r in range(R):
            for c in range(C):
                if grid[r][c] == 1:
                    for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                        # an edge is on the outline when the other side is water or off the map
                        if not (0 <= nr < R and 0 <= nc < C) or grid[nr][nc] == 0:
                            total += 1
        return total
''',
    tests=[
        [[[0, 1, 0, 0], [1, 1, 1, 0], [0, 1, 0, 0], [1, 1, 0, 0]]],
        [[[1]]],
        [[[1, 0]]],
        [[[1, 1]]],
        [[[1], [1], [1]]],
        [[[1, 1], [1, 1]]],
        [[[0, 0, 0], [0, 1, 0], [0, 0, 0]]],
        [[[1, 1, 1], [1, 0, 0], [1, 1, 1]]],
        [[[0, 1, 1, 1], [1, 1, 0, 0]]],
        [[[1] * 100 for _ in range(100)]],
        [[[1] * 100] + [[1] + [0] * 99 for _ in range(99)]],
        [[[1 if (c % 2 == 0 or r == 0) else 0 for c in range(99)] for r in range(100)]],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def islandPerimeter(self, grid):
        return 4 * sum(map(sum, grid))
''',
        '''class Solution:
    def islandPerimeter(self, grid):
        R, C = len(grid), len(grid[0]); total = 0
        for r in range(R):
            for c in range(C):
                if grid[r][c]:
                    total += 4
                    if r and grid[r-1][c]: total -= 1
                    if c and grid[r][c-1]: total -= 1
        return total
''',
    ],
    guide=dict(
        prereqs="Grids as graphs and the four-neighbour loop (lesson *Graphs and how to store them*).",
        intuition=r"""
Look at one land cell. It has four edges. An edge belongs to the outline exactly when the cell on the
other side of it is **water or outside the grid**. So no traversal is needed — visit every land cell
and count such edges.
""",
        hints=[
            "Think about a single square of land: which of its four sides are part of the coastline?",
            "A side is coastline if the neighbouring cell in that direction is water or does not exist.",
            "Alternative count: 4 per land cell, minus 2 for every pair of adjacent land cells (the shared side disappears from both).",
        ],
        brute_force="This problem's direct solution is already linear. A heavier alternative is a DFS from the first land cell that adds 1 each time it steps to water or off the grid — same O(R·C).",
        approach=r"""
For each land cell, for each of the 4 directions: if the neighbour is out of bounds or `0`, add 1.

**Dry run** `[[1,1]]`: left cell — up, down, left are outside (3), right is land (0). Right cell — up, down, right are outside (3). Total 6.

**Formula view:** `4 · land − 2 · (adjacent land pairs)`. For `[[1,1]]`: 4·2 − 2·1 = 6.
""",
        complexity="O(R·C) time, O(1) extra space.",
        pitfalls=r"""
- Returning `4 × land cells` (wrong solution #1) ignores shared sides.
- Subtracting only **1** per shared side (wrong solution #2): a shared side removes one edge from *each* of the two cells, so subtract 2.
- Index errors on the border — test bounds before reading the neighbour.
""",
        follow_up="If lakes were allowed and only the *outer* coastline counted, you would flood-fill the water from outside first. Related: *Number of Islands*, *Max Area of Island*.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="flood-fill",
    title="Flood Fill",
    difficulty="Easy",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/flood-fill/",
    entry="floodFill",
    description=r"""
An image is a grid of integers, each a pixel colour. Implement the "paint bucket" tool: starting from
pixel `(sr, sc)`, repaint with `color` the starting pixel and every pixel that can be reached from it
by moving up/down/left/right **through pixels that have the starting pixel's original colour**.

Return the modified image.

**Constraints:** `1 <= rows, cols <= 50` (tests go to 150), `0 <= image[r][c], color < 2^16`.

**Example 1:** `image = [[1,1,1],[1,1,0],[1,0,1]], sr = 1, sc = 1, color = 2` → `[[2,2,2],[2,2,0],[2,0,1]]`
(the bottom-right `1` touches the region only diagonally, so it stays)

**Example 2:** `image = [[0,0,0],[0,0,0]], sr = 0, sc = 0, color = 0` → unchanged
""",
    starter='''class Solution:
    def floodFill(self, image: List[List[int]], sr: int, sc: int, color: int) -> List[List[int]]:
        pass
''',
    solution='''class Solution:
    def floodFill(self, image, sr, sc, color):
        old = image[sr][sc]
        if old == color:
            return image                  # nothing to do, and avoids an endless loop
        R, C = len(image), len(image[0])
        image[sr][sc] = color
        stack = [(sr, sc)]
        while stack:
            r, c = stack.pop()
            for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if 0 <= nr < R and 0 <= nc < C and image[nr][nc] == old:
                    image[nr][nc] = color     # repainting doubles as "visited"
                    stack.append((nr, nc))
        return image
''',
    tests=[
        [[[1, 1, 1], [1, 1, 0], [1, 0, 1]], 1, 1, 2],
        [[[0, 0, 0], [0, 0, 0]], 0, 0, 0],
        [[[5]], 0, 0, 7],
        [[[1, 2], [2, 1]], 0, 0, 3],
        [[[1, 1], [1, 1]], 1, 1, 9],
        [[[0, 1, 0], [1, 0, 1], [0, 1, 0]], 1, 1, 4],
        [[[2, 2, 2], [2, 3, 2], [2, 2, 2]], 0, 0, 3],
        [[[1, 1, 1], [0, 0, 1], [1, 1, 1]], 2, 0, 6],
        [[[7] * 150 for _ in range(150)], 75, 75, 8],
        [[[_R.randint(0, 1) for _ in range(60)] for _ in range(60)], 30, 30, 5],
        [[[_R.randint(0, 2) for _ in range(120)] for _ in range(120)], 0, 0, 65535],
        [[[1 if (r % 2 == 0 or (r % 4 == 1 and c == 99) or (r % 4 == 3 and c == 0)) else 0 for c in range(100)] for r in range(100)], 0, 0, 2],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def floodFill(self, image, sr, sc, color):
        old = image[sr][sc]
        return [[color if v == old else v for v in row] for row in image]
''',
        '''class Solution:
    def floodFill(self, image, sr, sc, color):
        old = image[sr][sc]
        if old == color: return image
        R, C = len(image), len(image[0]); image[sr][sc] = color; stack = [(sr, sc)]
        while stack:
            r, c = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < R and 0 <= nc < C and image[nr][nc] == old:
                        image[nr][nc] = color; stack.append((nr, nc))
        return image
''',
    ],
    guide=dict(
        prereqs="DFS/BFS on a grid (lesson *DFS and BFS on grids and adjacency lists*).",
        intuition=r"""
The pixels to repaint are exactly the **connected component** of the start pixel in the graph whose
edges join neighbouring pixels of the original colour. Traverse that component and repaint as you go.
Repainting a pixel also marks it as visited, because it no longer has the old colour — provided the
new colour differs from the old one.
""",
        hints=[
            "Which pixels change? Describe them as 'reachable from the start by steps of a certain kind'.",
            "Use DFS or BFS from (sr, sc), stepping only onto pixels that still have the original colour.",
            "Handle the case new colour == original colour first: return immediately, otherwise nothing ever looks 'visited'.",
        ],
        brute_force="Repeatedly scan the whole image, repainting any old-colour pixel that touches a repainted one, until nothing changes: O((R·C)²).",
        approach=r"""
1. `old = image[sr][sc]`; if `old == color` return.
2. Paint the start; push it on a stack.
3. Pop a pixel; for each in-bounds neighbour still coloured `old`: paint and push.

**Dry run** Example 1 from (1,1): paint (1,1); neighbours (0,1), (1,0) are 1 → paint; from those reach (0,0), (0,2), (2,0). (1,2) and (2,1) are 0 → skipped. (2,2) is only diagonal → untouched.
""",
        complexity="O(R·C) time; O(R·C) stack space in the worst case.",
        pitfalls=r"""
- Repainting every pixel of that colour in the image, connected or not (wrong solution #1).
- Including diagonal neighbours (wrong solution #2).
- Infinite loop when the new colour equals the old colour.
- Recursive DFS on a 150 × 150 single-colour image exceeds Python's recursion limit — use a stack.
""",
        follow_up="*Number of Islands* runs this fill from every unvisited land cell. *Coloring a Border* repaints only the component's boundary.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="shortest-path-in-binary-matrix",
    title="Shortest Path in Binary Matrix",
    difficulty="Medium",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/shortest-path-in-binary-matrix/",
    neetcode="https://neetcode.io/problems/shortest-path-in-binary-matrix",
    entry="shortestPathBinaryMatrix",
    description=r"""
In an `n × n` grid of `0`s (open) and `1`s (blocked), find the shortest path from the top-left cell
to the bottom-right cell that walks only on open cells. From a cell you may move to any of its
**eight** neighbours (including diagonals).

Return the number of **cells** on the shortest such path (both ends included), or `-1` if there is none.

**Constraints:** `1 <= n <= 100`.

**Example 1:** `[[0,1],[1,0]]` → `2` (one diagonal step)

**Example 2:** `[[0,0,0],[1,1,0],[1,1,0]]` → `4`

**Example 3:** `[[1,0,0],[1,1,0],[1,1,0]]` → `-1` (the start is blocked)
""",
    starter='''class Solution:
    def shortestPathBinaryMatrix(self, grid: List[List[int]]) -> int:
        pass
''',
    solution='''from collections import deque

class Solution:
    def shortestPathBinaryMatrix(self, grid):
        n = len(grid)
        if grid[0][0] or grid[n - 1][n - 1]:
            return -1
        seen = [[False] * n for _ in range(n)]
        seen[0][0] = True
        q = deque([(0, 0, 1)])                     # (row, col, cells on the path so far)
        while q:
            r, c, d = q.popleft()
            if r == n - 1 and c == n - 1:
                return d
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n and not seen[nr][nc] and grid[nr][nc] == 0:
                        seen[nr][nc] = True
                        q.append((nr, nc, d + 1))
        return -1
''',
    tests=[
        [[[0, 1], [1, 0]]],
        [[[0, 0, 0], [1, 1, 0], [1, 1, 0]]],
        [[[1, 0, 0], [1, 1, 0], [1, 1, 0]]],
        [[[0]]],
        [[[1]]],
        [[[0, 0], [0, 1]]],
        [[[0, 1, 0], [1, 1, 1], [0, 1, 0]]],
        [[[0, 1, 1, 0], [0, 1, 0, 0], [0, 1, 0, 1], [0, 0, 0, 0]]],
        [[[0, 0, 0, 0], [1, 1, 1, 0], [0, 0, 0, 0], [0, 1, 1, 1]]],
        [[[0] * 100 for _ in range(100)]],
        [[[0 if (r % 2 == 0 or (r % 4 == 1 and c == 99) or (r % 4 == 3 and c == 0)) else 1 for c in range(100)] for r in range(99)] + [[1] * 99 + [0]]],
        [[[0 if (r in (0, 99) or c in (0, 99) or _R.random() < 0.6) else 1 for c in range(100)] for r in range(100)]],
        [[[0 if (r == c or _R.random() < 0.3) else 1 for c in range(60)] for r in range(60)]],
    ],
    examples=3,
    wrong_solutions=[
        '''from collections import deque
class Solution:
    def shortestPathBinaryMatrix(self, grid):
        n = len(grid)
        if grid[0][0] or grid[n-1][n-1]: return -1
        seen = {(0, 0)}; q = deque([(0, 0, 1)])
        while q:
            r, c, d = q.popleft()
            if r == n - 1 and c == n - 1: return d
            for nr, nc in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)):
                if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in seen and grid[nr][nc] == 0:
                    seen.add((nr, nc)); q.append((nr, nc, d + 1))
        return -1
''',
        '''from collections import deque
class Solution:
    def shortestPathBinaryMatrix(self, grid):
        n = len(grid); seen = {(0, 0)}; q = deque([(0, 0, 0)])
        while q:
            r, c, d = q.popleft()
            if r == n - 1 and c == n - 1: return d
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in seen and grid[nr][nc] == 0:
                        seen.add((nr, nc)); q.append((nr, nc, d + 1))
        return -1
''',
    ],
    guide=dict(
        prereqs="BFS shortest paths in unweighted graphs (lesson *DFS and BFS on grids and adjacency lists*).",
        intuition=r"""
Every step costs the same, so the shortest path in number of cells is found by **breadth-first
search**: it reaches cells in rings of increasing distance, and the first time it reaches the target
is via a shortest path. The only twists are the eight directions and counting cells instead of steps
(start the count at 1).
""",
        hints=[
            "All moves cost the same. Which traversal guarantees the first arrival is the shortest?",
            "Neighbours: all (dr, dc) with dr, dc in {−1, 0, 1} except (0, 0).",
            "Start with distance 1 at (0,0); return −1 early if the start or the end cell is blocked.",
        ],
        brute_force="DFS over all simple paths keeping the best length — exponential. DFS with a visited set is fast but returns *a* path, not the shortest.",
        approach=r"""
1. If `grid[0][0]` or `grid[n-1][n-1]` is 1 → −1.
2. BFS from `(0, 0, 1)`; mark cells when enqueued.
3. Return the stored length when the target is dequeued; −1 if the queue empties.

**Dry run** Example 2: (0,0,1) → (0,1,2) → (0,2,3) and (1,2,3) [diagonal from (0,1)] → (2,2,4). Answer 4.
""",
        complexity="O(n²) time and space: each cell is enqueued once and inspects 8 neighbours.",
        pitfalls=r"""
- Only four directions (wrong solution #1 returns −1 for Example 1).
- Counting steps instead of cells, or not checking a blocked start (wrong solution #2).
- Marking visited on dequeue — the queue fills with duplicates.
- `n = 1`: the single open cell is both start and end → answer 1.
""",
        follow_up="A* with the Chebyshev distance `max(|dr|, |dc|)` as heuristic explores fewer cells. If moves had different costs you would switch to Dijkstra (*Path With Minimum Effort*).",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="01-matrix",
    title="01 Matrix",
    difficulty="Medium",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/01-matrix/",
    entry="updateMatrix",
    description=r"""
Given a grid `mat` of `0`s and `1`s that contains **at least one `0`**, return a grid of the same
shape in which each cell holds the distance from that cell to the **nearest `0`**. Distance is the
number of up/down/left/right steps; a cell containing `0` has distance `0`.

**Constraints:** `1 <= rows, cols`, `rows * cols <= 10^4`.

**Example 1:** `[[0,0,0],[0,1,0],[0,0,0]]` → `[[0,0,0],[0,1,0],[0,0,0]]`

**Example 2:** `[[0,0,0],[0,1,0],[1,1,1]]` → `[[0,0,0],[0,1,0],[1,2,1]]`
""",
    starter='''class Solution:
    def updateMatrix(self, mat: List[List[int]]) -> List[List[int]]:
        pass
''',
    solution='''from collections import deque

class Solution:
    def updateMatrix(self, mat):
        R, C = len(mat), len(mat[0])
        dist = [[-1] * C for _ in range(R)]
        q = deque()
        for r in range(R):
            for c in range(C):
                if mat[r][c] == 0:
                    dist[r][c] = 0
                    q.append((r, c))             # every zero is a starting point
        while q:
            r, c = q.popleft()
            for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if 0 <= nr < R and 0 <= nc < C and dist[nr][nc] == -1:
                    dist[nr][nc] = dist[r][c] + 1
                    q.append((nr, nc))
        return dist
''',
    tests=[
        [[[0, 0, 0], [0, 1, 0], [0, 0, 0]]],
        [[[0, 0, 0], [0, 1, 0], [1, 1, 1]]],
        [[[0]]],
        [[[1, 0]]],
        [[[1, 1, 1, 1, 0]]],
        [[[0], [1], [1], [1]]],
        [[[1, 1, 1], [1, 1, 1], [1, 1, 0]]],
        [[[0, 1, 1], [1, 1, 1], [1, 1, 1]]],
        [[[1, 1, 0, 1, 1], [1, 1, 1, 1, 1], [0, 1, 1, 1, 1]]],
        [[[1] * 100 for _ in range(99)] + [[1] * 99 + [0]]],
        [_bin(_R, 100, 100, 0.97)[:-1] + [[0] * 100]],
        [[[0] + [1] * 99] + _bin(_R, 99, 100, 0.9)],
        [[[0 if (r, c) == (50, 50) else 1 for c in range(100)] for r in range(100)]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def updateMatrix(self, mat):
        R, C = len(mat), len(mat[0]); INF = 10**9
        d = [[0 if mat[r][c] == 0 else INF for c in range(C)] for r in range(R)]
        for r in range(R):
            for c in range(C):
                if r: d[r][c] = min(d[r][c], d[r-1][c] + 1)
                if c: d[r][c] = min(d[r][c], d[r][c-1] + 1)
        return [[min(v, R + C) for v in row] for row in d]
''',
        '''class Solution:
    def updateMatrix(self, mat):
        R, C = len(mat), len(mat[0])
        out = [row[:] for row in mat]
        for r in range(R):
            for c in range(C):
                if mat[r][c] == 1:
                    near = [mat[nr][nc] for nr, nc in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)) if 0 <= nr < R and 0 <= nc < C]
                    out[r][c] = 1 if 0 in near else 2
        return out
''',
    ],
    guide=dict(
        prereqs="Multi-source BFS (lesson *DFS and BFS on grids and adjacency lists*; see also *Walls and Gates*).",
        intuition=r"""
Searching outward from every `1` until it meets a `0` repeats enormous amounts of work. Turn it
around: start a single BFS **from all the zeros at once**. The wave reaches every cell for the first
time from its nearest zero, so the distance written on first arrival is the answer.
""",
        hints=[
            "Running a BFS from each 1 is O((R·C)²). Could one search answer the question for all cells?",
            "Put every 0 in the queue with distance 0 before the BFS starts.",
            "dist = −1 means unvisited; set dist[neighbour] = dist[current] + 1 the first time you reach it.",
        ],
        brute_force="BFS from each `1` until a `0` is found: O((R·C)²) in the worst case (one zero in a corner).",
        approach=r"""
1. `dist` grid of −1; enqueue all zeros with distance 0.
2. BFS: unvisited neighbours get `dist + 1`.

**Dry run** Example 2: ring 0 = all zeros. Ring 1: (1,1), (2,0), (2,2). Ring 2: (2,1). Result `[[0,0,0],[0,1,0],[1,2,1]]`.

**DP alternative (two sweeps):** top-left to bottom-right using the up and left neighbours, then bottom-right to top-left using down and right. Both sweeps are needed.
""",
        complexity="O(R·C) time and space.",
        pitfalls=r"""
- A single DP sweep sees only zeros above/left of a cell (wrong solution #1).
- Looking only at immediate neighbours (wrong solution #2 caps distances at 2).
- BFS from one zero only.
- Using the input grid's `1`s as the visited marker: a computed distance of 1 is indistinguishable from an unvisited `1`.
""",
        follow_up="Identical technique: *Walls and Gates*, *Rotting Oranges*, *As Far from Land as Possible*, *Map of Highest Peak*.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="open-the-lock",
    title="Open the Lock",
    difficulty="Medium",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/open-the-lock/",
    neetcode="https://neetcode.io/problems/open-the-lock",
    entry="openLock",
    description=r"""
A lock has four wheels, each showing a digit `0`–`9`. One **move** turns a single wheel one notch
forward or backward; the wheels wrap around (`9` forward becomes `0`, `0` backward becomes `9`).

The lock starts at `"0000"`. Some combinations are `deadends`: if the lock ever shows one of them it
jams and can no longer be turned. Return the minimum number of moves needed to show `target`, or `-1`
if it cannot be reached.

**Constraints:** `1 <= len(deadends) <= 500`; `target` is not a deadend and is not `"0000"`... except
that `"0000"` itself may appear among the deadends.

**Example 1:** `deadends = ["0201","0101","0102","1212","2002"], target = "0202"` → `6`

**Example 2:** `deadends = ["8888"], target = "0009"` → `1` (turn the last wheel backward)

**Example 3:** `deadends = ["8887","8889","8878","8898","8788","8988","7888","9888"], target = "8888"` → `-1`
""",
    starter='''class Solution:
    def openLock(self, deadends: List[str], target: str) -> int:
        pass
''',
    solution='''from collections import deque

class Solution:
    def openLock(self, deadends, target):
        seen = set(deadends)                 # never step onto a deadend
        if "0000" in seen:
            return -1
        seen.add("0000")
        q = deque([("0000", 0)])
        while q:
            state, moves = q.popleft()
            if state == target:
                return moves
            for i in range(4):
                d = int(state[i])
                for nd in ((d + 1) % 10, (d - 1) % 10):
                    nxt = state[:i] + str(nd) + state[i + 1:]
                    if nxt not in seen:
                        seen.add(nxt)
                        q.append((nxt, moves + 1))
        return -1
''',
    tests=[
        [["0201", "0101", "0102", "1212", "2002"], "0202"],
        [["8888"], "0009"],
        [["8887", "8889", "8878", "8898", "8788", "8988", "7888", "9888"], "8888"],
        [["0000"], "8888"],
        [["1111"], "0001"],
        [["1000", "9000", "0100", "0900", "0010", "0090", "0001", "0009"], "5555"],
        [["1000", "9000", "0100", "0900", "0010", "0090", "0009"], "5555"],
        [["5557", "5553", "5575", "5535", "5755", "5355", "7555", "3555", "6555", "4555", "5655", "5455", "5565", "5545", "5566", "5544", "5556"], "5555"],
        [["0001"], "0002"],
        [["1234"], "9999"],
        [["%04d" % _R.randrange(1, 10000) for _ in range(500)], "5050"],
        [["%04d" % x for x in range(1000, 1500)], "2000"],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def openLock(self, deadends, target):
        return sum(min(int(ch), 10 - int(ch)) for ch in target)
''',
        '''from collections import deque
class Solution:
    def openLock(self, deadends, target):
        seen = set(deadends) | {"0000"}; q = deque([("0000", 0)])
        while q:
            state, moves = q.popleft()
            if state == target: return moves
            for i in range(4):
                d = int(state[i])
                for nd in (d + 1, d - 1):
                    if 0 <= nd <= 9:
                        nxt = state[:i] + str(nd) + state[i+1:]
                        if nxt not in seen:
                            seen.add(nxt); q.append((nxt, moves + 1))
        return -1
''',
    ],
    guide=dict(
        prereqs="BFS on an implicit state graph (lessons *Graphs and how to store them* — state graphs — and *DFS and BFS*).",
        intuition=r"""
Treat each of the 10,000 combinations as a vertex. Two combinations are joined by an edge when one
move turns one into the other, so every vertex has 8 neighbours. "Fewest moves" is then a shortest
path in an unweighted graph → BFS from `"0000"`. Deadends are vertices you may not enter: put them in
the visited set before starting.
""",
        hints=[
            "What are the 'states' and what does one move do to a state? How many states exist?",
            "Minimum number of equal-cost moves → breadth-first search over states.",
            "Pre-load the visited set with the deadends; handle '0000' being a deadend; generate 8 neighbours with (d ± 1) % 10.",
        ],
        brute_force="DFS over move sequences has no natural stopping point and does not find the minimum. Without deadends the answer is the sum over wheels of `min(d, 10 − d)`, but deadends can force detours.",
        approach=r"""
1. `seen = set(deadends)`; if `"0000"` is in it return −1; add `"0000"`.
2. BFS with `(state, moves)`; for each wheel and each direction build the neighbour string; enqueue it if unseen.
3. Return `moves` when the target is dequeued, −1 if the queue empties.

**Dry run** Example 2: `"0000"` → its neighbours include `"0009"` (last wheel backward) at 1 move → answer 1.
""",
        complexity="At most 10⁴ states × 8 neighbours, each built in O(4): effectively constant, about 3·10⁵ string operations. In general O(bᵈ · d) for d wheels with base b.",
        pitfalls=r"""
- Ignoring deadends and using the wheel-distance formula (wrong solution #1).
- No wrap-around between 9 and 0 (wrong solution #2).
- Not checking whether the start itself is a deadend.
- `-1 % 10` is 9 in Python (handy), but in many other languages it is −1.
""",
        follow_up="Bidirectional BFS from both `\"0000\"` and the target meets in the middle and visits far fewer states. Same pattern: *Word Ladder*, *Minimum Genetic Mutation*, *Sliding Puzzle*.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="find-eventual-safe-states",
    title="Find Eventual Safe States",
    difficulty="Medium",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/find-eventual-safe-states/",
    neetcode="https://neetcode.io/problems/find-eventual-safe-states",
    entry="eventualSafeNodes",
    description=r"""
A directed graph has nodes `0..n-1`; `graph[i]` lists the nodes that `i` has an edge to. A node with
no outgoing edges is a **terminal** node. A node is **safe** if *every* path that starts there
eventually stops at a terminal node — in other words, no walk from it can go on forever.

Return all safe nodes in **ascending order**.

**Constraints:** `1 <= n <= 10^4` (tests go to 3000), up to `4 * 10^4` edges, self-loops allowed, each `graph[i]` sorted.

**Example 1:** `graph = [[1,2],[2,3],[5],[0],[5],[],[]]` → `[2,4,5,6]`
(0 → 1 → 3 → 0 is a cycle, so 0, 1 and 3 are unsafe)

**Example 2:** `graph = [[1,2,3,4],[1,2],[3,4],[0,4],[]]` → `[4]`
""",
    starter='''class Solution:
    def eventualSafeNodes(self, graph: List[List[int]]) -> List[int]:
        pass
''',
    solution='''from collections import deque

class Solution:
    def eventualSafeNodes(self, graph):
        n = len(graph)
        rev = [[] for _ in range(n)]          # reversed edges
        out = [len(g) for g in graph]         # remaining out-degree
        for u, nbrs in enumerate(graph):
            for v in nbrs:
                rev[v].append(u)
        q = deque(i for i in range(n) if out[i] == 0)     # terminal nodes are safe
        safe = [False] * n
        while q:
            v = q.popleft()
            safe[v] = True
            for u in rev[v]:
                out[u] -= 1                   # one more of u's edges leads to a safe node
                if out[u] == 0:
                    q.append(u)
        return [i for i in range(n) if safe[i]]
''',
    tests=[
        [[[1, 2], [2, 3], [5], [0], [5], [], []]],
        [[[1, 2, 3, 4], [1, 2], [3, 4], [0, 4], []]],
        [[[]]],
        [[[0]]],
        [[[1], [0]]],
        [[[1], [2], []]],
        [[[], [0, 2, 3, 4], [3], [4], []]],
        [[[1, 2], [3], [3], []]],
        [[[1], [2], [0], [0], [], [4], [5, 3]]],
        _digraph(_R, 30, 40, 0.9),
        _digraph(_R, 3000, 6000, 0.97),
        _digraph(_R, 3000, 3000, 1.0),
        [[[i + 1] for i in range(2999)] + [[]]],
        [[[i + 1] for i in range(2999)] + [[1500]]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def eventualSafeNodes(self, graph):
        return [i for i, g in enumerate(graph) if not g]
''',
        '''class Solution:
    def eventualSafeNodes(self, graph):
        term = {i for i, g in enumerate(graph) if not g}
        return [i for i, g in enumerate(graph) if i in term or all(v in term for v in g)]
''',
    ],
    guide=dict(
        prereqs="Directed cycles and Kahn's algorithm (lesson *Cycle detection and topological sort*).",
        intuition=r"""
A node is unsafe exactly when it can reach a **cycle**. Work backwards from what is certainly safe:
terminal nodes. A node becomes safe once **all** of its outgoing edges lead to safe nodes. That is
Kahn's topological-sort peeling, run on the **reversed** graph with out-degrees playing the role of
in-degrees: repeatedly take a node whose remaining out-degree is 0 and "remove" it, lowering the
out-degree of every node that points to it.
""",
        hints=[
            "Which nodes are obviously safe? What makes some other node safe?",
            "A node is safe when every one of its out-edges goes to a safe node. Process nodes in the order they become safe.",
            "Reverse the edges; count out-degrees; queue nodes with out-degree 0; when a node is declared safe, decrement the out-degree of its predecessors.",
        ],
        brute_force="From each node, DFS to see whether a cycle is reachable: O(n · (n + m)).",
        approach=r"""
1. Build reversed adjacency lists and `out[i] = len(graph[i])`.
2. Queue all terminal nodes.
3. Pop `v`, mark safe; for each predecessor `u`: `out[u] -= 1`; if it reaches 0, enqueue.
4. Return marked nodes in index order.

**Dry run** Example 1: terminals 5, 6. Pop 5 → predecessors 2 and 4 drop to 0 → safe. Pop 6. Pop 2 → predecessors 0 (out 2→1) and 1 (2→1). Pop 4. Nodes 0, 1, 3 never reach 0 (they feed the cycle). Answer `[2,4,5,6]`.

**DFS alternative:** three colours; a node is safe iff its DFS finishes without meeting a gray node; memoise the result per node.
""",
        complexity="O(n + m) time and space.",
        pitfalls=r"""
- Returning only terminal nodes (wrong solution #1) or looking just one step ahead (wrong solution #2).
- Declaring a node safe when *some* edge leads to safety — it must be *all* edges.
- Self-loops: a node pointing to itself is a cycle and unsafe.
- Forgetting to sort the output (collecting by index order does this for free).
""",
        follow_up="This is the same peeling as *Course Schedule* on the reversed graph. Related: *Loud and Rich*, *Minimum Height Trees* (peeling leaves of an undirected tree).",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="is-graph-bipartite",
    title="Is Graph Bipartite?",
    difficulty="Medium",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/is-graph-bipartite/",
    entry="isBipartite",
    description=r"""
An undirected graph has nodes `0..n-1`; `graph[u]` lists the neighbours of `u` (if `v` is in
`graph[u]` then `u` is in `graph[v]`). The graph may be disconnected.

A graph is **bipartite** if its nodes can be split into two groups so that **every edge joins a node
of one group to a node of the other** — no edge stays inside a group. Return `True` if the graph is
bipartite, `False` otherwise.

**Constraints:** `1 <= n <= 100` (tests go to 2000), no self-loops, no repeated edges.

**Example 1:** `[[1,2,3],[0,2],[0,1,3],[0,2]]` → `False` (0, 1, 2 form a triangle)

**Example 2:** `[[1,3],[0,2],[1,3],[0,2]]` → `True` (groups {0, 2} and {1, 3})
""",
    starter='''class Solution:
    def isBipartite(self, graph: List[List[int]]) -> bool:
        pass
''',
    solution='''from collections import deque

class Solution:
    def isBipartite(self, graph):
        n = len(graph)
        color = [-1] * n                      # -1 = not coloured yet, otherwise 0 or 1
        for s in range(n):                    # the graph may have several components
            if color[s] != -1:
                continue
            color[s] = 0
            q = deque([s])
            while q:
                u = q.popleft()
                for v in graph[u]:
                    if color[v] == -1:
                        color[v] = 1 - color[u]     # neighbours get the opposite colour
                        q.append(v)
                    elif color[v] == color[u]:
                        return False                # an edge inside one group
        return True
''',
    tests=[
        [[[1, 2, 3], [0, 2], [0, 1, 3], [0, 2]]],
        [[[1, 3], [0, 2], [1, 3], [0, 2]]],
        [[[]]],
        [[[1], [0]]],
        [[[], [2], [1]]],
        [[[1], [0], [3, 4], [2, 4], [2, 3]]],
        [[[1, 4], [0, 2], [1, 3], [2, 4], [3, 0]]],
        [[[1, 5], [0, 2], [1, 3], [2, 4], [3, 5], [4, 0]]],
        [[[], [], []]],
        _bip(_R, 50, 120, 0),
        _bip(_R, 2000, 6000, 0),
        _bip(_R, 2000, 6000, 1),
        [[[1, 1998]] + [[i - 1, i + 1] for i in range(1, 1998)] + [[1997, 0]]],
        [[[1, 1999]] + [[i - 1, i + 1] for i in range(1, 1999)] + [[1998, 0]]],
    ],
    examples=2,
    wrong_solutions=[
        '''from collections import deque
class Solution:
    def isBipartite(self, graph):
        color = {0: 0}; q = deque([0])
        while q:
            u = q.popleft()
            for v in graph[u]:
                if v not in color:
                    color[v] = 1 - color[u]; q.append(v)
                elif color[v] == color[u]:
                    return False
        return True
''',
        '''class Solution:
    def isBipartite(self, graph):
        for u in range(len(graph)):
            s = set(graph[u])
            for v in graph[u]:
                if s & set(graph[v]): return False
        return True
''',
    ],
    guide=dict(
        prereqs="BFS/DFS over all components (lesson *DFS and BFS on grids and adjacency lists*).",
        intuition=r"""
Try to paint the nodes with two colours so that neighbours always differ. Once you choose a colour
for one node, everything in its connected component is **forced**: its neighbours must take the other
colour, their neighbours the first colour again, and so on. So traverse, colouring as you go; if you
ever find an edge whose two ends already have the same colour, no valid split exists. A graph is
bipartite exactly when it has no cycle of odd length.
""",
        hints=[
            "Give node 0 a colour. What colour must its neighbours have? And theirs?",
            "Traverse with BFS or DFS, assigning the opposite colour to each newly reached neighbour.",
            "If a neighbour is already coloured the same as the current node, return False. Start a new traversal from every uncoloured node.",
        ],
        brute_force="Try all 2ⁿ ways to split the nodes into two groups and check every edge: exponential.",
        approach=r"""
`color` array of −1. For each uncoloured start: colour it 0, BFS; uncoloured neighbour → opposite colour and enqueue; same-coloured neighbour → `False`.

**Dry run** Example 1: 0 = A. Neighbours 1, 2, 3 = B. Processing 1: neighbour 2 is also B → conflict → `False`.

Example 2 (a 4-cycle): 0 = A; 1, 3 = B; 2 = A; all edges join A to B → `True`.
""",
        complexity="O(n + m) time, O(n) space.",
        pitfalls=r"""
- Colouring only the component containing node 0 (wrong solution #1 misses an odd cycle elsewhere).
- Testing only for triangles (wrong solution #2 accepts a 5-cycle).
- Treating "already visited" as a conflict — it is a conflict only when the colours are equal.
""",
        follow_up="*Possible Bipartition* is the same test on a 'dislikes' graph. A union-find variant unions each node's neighbours together and checks the node is not in their set.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="minimum-height-trees",
    title="Minimum Height Trees",
    difficulty="Medium",
    pattern="Graphs",
    leetcode="https://leetcode.com/problems/minimum-height-trees/",
    neetcode="https://neetcode.io/problems/minimum-height-trees",
    entry="findMinHeightTrees",
    compare="unordered",
    description=r"""
A tree with `n` nodes labelled `0..n-1` is given as a list of `n - 1` undirected edges. You may pick
any node as the **root**; the *height* of the rooted tree is the number of edges on the longest
downward path from the root to a leaf.

Return the labels of all roots that give the **smallest possible height**, in any order. (There are
always one or two such nodes.)

**Constraints:** `1 <= n <= 2 * 10^4` (tests go to 5000), the edges form a valid tree.

**Example 1:** `n = 4, edges = [[1,0],[1,2],[1,3]]` → `[1]`

**Example 2:** `n = 6, edges = [[3,0],[3,1],[3,2],[3,4],[5,4]]` → `[3,4]`

**Example 3:** `n = 1, edges = []` → `[0]`
""",
    starter='''class Solution:
    def findMinHeightTrees(self, n: int, edges: List[List[int]]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def findMinHeightTrees(self, n, edges):
        if n <= 2:
            return list(range(n))
        adj = [set() for _ in range(n)]
        for a, b in edges:
            adj[a].add(b)
            adj[b].add(a)
        leaves = [i for i in range(n) if len(adj[i]) == 1]
        remaining = n
        while remaining > 2:
            remaining -= len(leaves)
            new_leaves = []
            for leaf in leaves:                  # peel one whole layer of leaves
                nb = adj[leaf].pop()
                adj[nb].discard(leaf)
                if len(adj[nb]) == 1:
                    new_leaves.append(nb)
            leaves = new_leaves
        return leaves
''',
    tests=[
        [4, [[1, 0], [1, 2], [1, 3]]],
        [6, [[3, 0], [3, 1], [3, 2], [3, 4], [5, 4]]],
        [1, []],
        [2, [[0, 1]]],
        [3, [[0, 1], [1, 2]]],
        [4, [[0, 1], [1, 2], [2, 3]]],
        [7, [[0, 1], [1, 2], [1, 3], [2, 4], [3, 5], [4, 6]]],
        [6, [[0, 1], [0, 2], [0, 3], [3, 4], [4, 5]]],
        [5, [[0, 1], [0, 2], [0, 3], [0, 4]]],
        _tree(_R, 50),
        _tree(_R, 5000),
        [5000, [[i, i + 1] for i in range(4999)]],
        [4999, [[i, i + 1] for i in range(4998)]],
        [5000, [[0, i] for i in range(1, 4999)] + [[4998, 4999]]],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def findMinHeightTrees(self, n, edges):
        deg = [0] * n
        for a, b in edges: deg[a] += 1; deg[b] += 1
        m = max(deg)
        return [i for i in range(n) if deg[i] == m]
''',
        '''class Solution:
    def findMinHeightTrees(self, n, edges):
        if n == 1: return [0]
        adj = [set() for _ in range(n)]
        for a, b in edges: adj[a].add(b); adj[b].add(a)
        leaves = [i for i in range(n) if len(adj[i]) == 1]; remaining = n
        while remaining > 2:
            remaining -= len(leaves); new = []
            for leaf in leaves:
                nb = adj[leaf].pop(); adj[nb].discard(leaf)
                if len(adj[nb]) == 1: new.append(nb)
            leaves = new
        return leaves[:1]
''',
    ],
    guide=dict(
        prereqs="Trees as undirected graphs; degree; layer-by-layer peeling as in Kahn's algorithm (lesson *Cycle detection and topological sort*).",
        intuition=r"""
The best roots are the **middle** of the tree's longest path — a root far from the middle has a long
branch on one side. You can find the middle without finding that path: repeatedly strip off **all
current leaves** at once, like peeling an onion. Each round shortens every long path by one node at
each end. When one or two nodes are left, they are the centre.
""",
        hints=[
            "On a simple path graph 0–1–2–3–4, which root gives the smallest height? What about a path with an even number of nodes?",
            "A leaf is never a better root than its neighbour (unless n ≤ 2). Remove all leaves and ask the question again.",
            "Keep degrees; peel leaf layers until at most 2 nodes remain; those are the answer.",
        ],
        brute_force="Run a BFS from every node to compute its height and keep the minima: O(n²) — too slow for n = 2·10⁴.",
        approach=r"""
1. `n ≤ 2` → all nodes.
2. Adjacency sets; `leaves` = nodes of degree 1.
3. While more than 2 nodes remain: subtract the number of leaves; detach each leaf from its neighbour; neighbours that drop to degree 1 form the next layer.
4. The last layer is the answer.

**Dry run** Example 2: leaves 0, 1, 2, 5 (remaining 6 → 2). Removing them leaves 3 and 4, joined by an edge → `[3,4]`.

**Alternative:** two BFS passes find the longest path (the *diameter*); its middle node(s) are the answer.
""",
        complexity="O(n) time and space — every node and edge is removed once.",
        pitfalls=r"""
- Picking the highest-degree node (wrong solution #1 fails on a star attached to a long tail).
- Returning only one node when two are left (wrong solution #2): a tree whose longest path has an even number of nodes has **two** centres. Stop peeling when `remaining <= 2` and return everything that is left.
- Forgetting `n == 1` (no leaves of degree 1 exist) and `n == 2`.
- Removing leaves one at a time while also adding new leaves to the same list mixes layers.
""",
        follow_up="The answer nodes are called the tree's *centre*; the related *centroid* minimises the largest remaining subtree instead. Related: *Tree Diameter*, *Sum of Distances in Tree*.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="path-with-minimum-effort",
    title="Path With Minimum Effort",
    difficulty="Medium",
    pattern="Advanced Graphs",
    leetcode="https://leetcode.com/problems/path-with-minimum-effort/",
    neetcode="https://neetcode.io/problems/path-with-minimum-effort",
    entry="minimumEffortPath",
    description=r"""
A hiker crosses a grid of `heights` from the top-left cell to the bottom-right cell, moving
up/down/left/right. The **effort** of a route is the **largest absolute height difference between two
consecutive cells** on it (not the sum of differences).

Return the minimum effort needed.

**Constraints:** `1 <= rows, cols <= 100` (tests go to 60), `1 <= heights[r][c] <= 10^6`.

**Example 1:** `[[1,2,2],[3,8,2],[5,3,5]]` → `2` (route 1 → 3 → 5 → 3 → 5 has steps of size 2, 2, 2, 2)

**Example 2:** `[[1,2,3],[3,8,4],[5,3,5]]` → `1` (route 1 → 2 → 3 → 4 → 5)

**Example 3:** `[[7]]` → `0`
""",
    starter='''class Solution:
    def minimumEffortPath(self, heights: List[List[int]]) -> int:
        pass
''',
    solution='''import heapq

class Solution:
    def minimumEffortPath(self, heights):
        R, C = len(heights), len(heights[0])
        best = [[float("inf")] * C for _ in range(R)]
        best[0][0] = 0
        heap = [(0, 0, 0)]                        # (effort so far, row, col)
        while heap:
            e, r, c = heapq.heappop(heap)
            if r == R - 1 and c == C - 1:
                return e
            if e > best[r][c]:
                continue                          # stale entry
            for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if 0 <= nr < R and 0 <= nc < C:
                    ne = max(e, abs(heights[nr][nc] - heights[r][c]))
                    if ne < best[nr][nc]:
                        best[nr][nc] = ne
                        heapq.heappush(heap, (ne, nr, nc))
        return 0
''',
    tests=[
        [[[1, 2, 2], [3, 8, 2], [5, 3, 5]]],
        [[[1, 2, 3], [3, 8, 4], [5, 3, 5]]],
        [[[7]]],
        [[[1, 10]]],
        [[[1], [4], [2]]],
        [[[1, 2, 1, 1, 1], [1, 2, 1, 2, 1], [1, 2, 1, 2, 1], [1, 2, 1, 2, 1], [1, 1, 1, 2, 1]]],
        [[[1, 100, 1], [1, 100, 1], [1, 1, 1]]],
        [[[4, 3, 4, 10, 5, 5, 9, 2], [10, 8, 2, 10, 9, 7, 5, 6], [5, 8, 10, 10, 10, 7, 4, 2], [5, 1, 3, 1, 1, 3, 1, 9], [6, 4, 10, 6, 10, 9, 4, 6]]],
        [[[1, 1000000], [1000000, 1]]],
        [[[10, 8], [10, 8], [1, 2], [10, 3], [1, 3], [6, 3], [5, 2]]],
        [[[_R.randint(1, 20) for _ in range(30)] for _ in range(30)]],
        [[[_R.randint(1, 10**6) for _ in range(60)] for _ in range(60)]],
        [[[5] * 60 for _ in range(60)]],
        [[[1 if (r % 2 == 0 or (r % 4 == 1 and c == 49) or (r % 4 == 3 and c == 0)) else 500 for c in range(50)] for r in range(49)]],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def minimumEffortPath(self, heights):
        R, C = len(heights), len(heights[0]); INF = float("inf")
        dp = [[INF] * C for _ in range(R)]; dp[0][0] = 0
        for r in range(R):
            for c in range(C):
                if r: dp[r][c] = min(dp[r][c], max(dp[r-1][c], abs(heights[r][c] - heights[r-1][c])))
                if c: dp[r][c] = min(dp[r][c], max(dp[r][c-1], abs(heights[r][c] - heights[r][c-1])))
        return dp[-1][-1]
''',
        '''import heapq
class Solution:
    def minimumEffortPath(self, heights):
        R, C = len(heights), len(heights[0])
        best = {(0, 0): (0, 0)}; heap = [(0, 0, 0, 0)]
        while heap:
            s, e, r, c = heapq.heappop(heap)
            if (r, c) == (R - 1, C - 1): return e
            for nr, nc in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)):
                if 0 <= nr < R and 0 <= nc < C:
                    d = abs(heights[nr][nc] - heights[r][c])
                    if (nr, nc) not in best or s + d < best[(nr, nc)][0]:
                        best[(nr, nc)] = (s + d, max(e, d))
                        heapq.heappush(heap, (s + d, max(e, d), nr, nc))
        return 0
''',
    ],
    guide=dict(
        prereqs="Dijkstra's algorithm and its minimax variant (lesson *Shortest paths: Dijkstra and Bellman-Ford*; compare *Swim in Rising Water*).",
        intuition=r"""
This is a shortest-path problem with an unusual way of measuring a path: by its **worst single
step** instead of the sum of its steps. Dijkstra's algorithm still applies, because the property it
relies on still holds — extending a route can never make its cost smaller (`max(e, step) >= e`).
So keep the best known effort for each cell, always expand the cell with the smallest effort, and
combine with `max` where ordinary Dijkstra uses `+`.
""",
        hints=[
            "The cost of a route is its largest step. If you extend a route by one more cell, can its cost go down?",
            "Run Dijkstra with a heap of (effort, row, col); the new effort to a neighbour is max(current effort, |height difference|).",
            "Stop when the bottom-right cell is popped. Skip heap entries that are worse than the best recorded effort for that cell.",
        ],
        brute_force="Try every simple path with DFS — exponential. A good intermediate answer: binary-search the effort limit `k` and BFS using only steps ≤ k: O(R·C·log(maxHeight)).",
        approach=r"""
1. `best[0][0] = 0`; heap `[(0, 0, 0)]`.
2. Pop `(e, r, c)`. Target → return `e`. Stale → skip.
3. For each neighbour: `ne = max(e, |Δheight|)`; if smaller than its recorded best, record and push.

**Dry run** Example 1: from (0,0)=1: right to 2 (effort 1), down to 3 (effort 2). The cheap route through the top row must eventually take a big step (2 → 8 is avoided, but 2 → 5 at the end costs 3), while the left column 1 → 3 → 5 → 3 → 5 never exceeds 2. The target is popped with effort 2.

**Other approaches:** binary search + BFS; or Kruskal — sort all neighbouring-cell edges by difference and union until the two corners connect.
""",
        complexity="O(R·C·log(R·C)) time, O(R·C) space.",
        pitfalls=r"""
- A right/down-only DP (wrong solution #1) — the best route may go up or left.
- Minimising the *sum* of differences and reporting that route's maximum (wrong solution #2).
- Returning early when the target is *pushed* rather than popped.
- A 1 × 1 grid has effort 0.
""",
        follow_up="*Swim in Rising Water* (max cell value) and *Path With Maximum Minimum Value* are the same minimax idea.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="path-with-maximum-probability",
    title="Path with Maximum Probability",
    difficulty="Medium",
    pattern="Advanced Graphs",
    leetcode="https://leetcode.com/problems/path-with-maximum-probability/",
    neetcode="https://neetcode.io/problems/path-with-maximum-probability",
    entry="maxProbability",
    compare="float",
    tolerance=1e-5,
    description=r"""
An undirected graph has `n` nodes `0..n-1`. Edge `edges[i] = [a, b]` can be crossed successfully with
probability `succProb[i]`. The probability of completing a whole path is the **product** of the
probabilities of its edges.

Return the highest success probability of any path from `start_node` to `end_node`, or `0` if no path
exists. Answers within `1e-5` of the correct value are accepted.

**Constraints:** `2 <= n <= 10^4` (tests go to 2000), `0 <= len(edges) <= 2 * 10^4`, `0 <= succProb[i] <= 1`,
at most one edge per pair, `start_node != end_node`.

**Example 1:** `n = 3, edges = [[0,1],[1,2],[0,2]], succProb = [0.5,0.5,0.2], start = 0, end = 2` → `0.25`
(0 → 1 → 2 gives 0.5 × 0.5, better than the direct edge 0.2)

**Example 2:** same graph with `succProb = [0.5,0.5,0.3]` → `0.3`

**Example 3:** `n = 3, edges = [[0,1]], succProb = [0.5], start = 0, end = 2` → `0`
""",
    starter='''class Solution:
    def maxProbability(self, n: int, edges: List[List[int]], succProb: List[float], start_node: int, end_node: int) -> float:
        pass
''',
    solution='''import heapq

class Solution:
    def maxProbability(self, n, edges, succProb, start_node, end_node):
        adj = [[] for _ in range(n)]
        for (a, b), p in zip(edges, succProb):
            adj[a].append((b, p))
            adj[b].append((a, p))
        best = [0.0] * n
        best[start_node] = 1.0
        heap = [(-1.0, start_node)]               # max-heap on probability via negation
        while heap:
            p, u = heapq.heappop(heap)
            p = -p
            if u == end_node:
                return p
            if p < best[u]:
                continue
            for v, w in adj[u]:
                np_ = p * w
                if np_ > best[v]:
                    best[v] = np_
                    heapq.heappush(heap, (-np_, v))
        return 0.0
''',
    tests=[
        [3, [[0, 1], [1, 2], [0, 2]], [0.5, 0.5, 0.2], 0, 2],
        [3, [[0, 1], [1, 2], [0, 2]], [0.5, 0.5, 0.3], 0, 2],
        [3, [[0, 1]], [0.5], 0, 2],
        [2, [[0, 1]], [1.0], 0, 1],
        [2, [], [], 0, 1],
        [4, [[0, 1], [1, 2], [2, 3], [0, 3]], [0.9, 0.9, 0.9, 0.7], 0, 3],
        [4, [[0, 1], [1, 2], [2, 3], [0, 3]], [0.9, 0.9, 0.9, 0.75], 3, 0],
        [5, [[0, 1], [1, 2], [2, 3], [3, 4], [0, 4]], [1.0, 1.0, 1.0, 1.0, 0.99], 0, 4],
        [3, [[0, 1], [1, 2]], [0.0, 0.5], 0, 2],
        [5, [[1, 4], [2, 4], [0, 4], [0, 3], [0, 2], [2, 3]], [0.37, 0.17, 0.93, 0.23, 0.39, 0.04], 3, 4],
        _prob(_R, 30, 80),
        _prob(_R, 2000, 6000),
        _prob(_R, 2000, 2500),
        [300, [[i, i + 1] for i in range(299)], [0.99] * 299, 0, 299],
    ],
    examples=3,
    wrong_solutions=[
        '''from collections import deque
class Solution:
    def maxProbability(self, n, edges, succProb, start_node, end_node):
        adj = [[] for _ in range(n)]
        for (a, b), p in zip(edges, succProb):
            adj[a].append((b, p)); adj[b].append((a, p))
        best = {start_node: 1.0}; q = deque([start_node])
        while q:
            u = q.popleft()
            for v, w in adj[u]:
                if v not in best:
                    best[v] = best[u] * w; q.append(v)
        return best.get(end_node, 0.0)
''',
        '''import heapq
class Solution:
    def maxProbability(self, n, edges, succProb, start_node, end_node):
        adj = [[] for _ in range(n)]
        for (a, b), p in zip(edges, succProb):
            adj[a].append((b, p)); adj[b].append((a, p))
        seen = set(); heap = [(-1.0, start_node, 1.0)]
        while heap:
            k, u, p = heapq.heappop(heap)
            if u == end_node: return p
            if u in seen: continue
            seen.add(u)
            for v, w in adj[u]:
                heapq.heappush(heap, (-w, v, p * w))
        return 0.0
''',
    ],
    guide=dict(
        prereqs="Dijkstra with a heap, the max-heap negation trick, and the condition 'extending a path never improves it' (lesson *Shortest paths: Dijkstra and Bellman-Ford*).",
        intuition=r"""
Replace "shortest" by "most probable" and "sum of weights" by "product of probabilities". Since every
probability is at most 1, multiplying by another edge can only keep the value the same or make it
**smaller** — the mirror image of "adding a non-negative weight can only make a distance larger". So
Dijkstra's greedy rule works with a **max**-heap: the unfinished node with the highest probability is
final, because no detour through less likely nodes can beat it.
""",
        hints=[
            "How does the value of a path change when you append one more edge? Can it increase?",
            "Use Dijkstra, but always expand the node with the LARGEST probability so far; combine with multiplication.",
            "Max-heap of (−probability, node); best[start] = 1.0; return when the end node is popped; return 0 if it never is.",
        ],
        brute_force="Bellman-Ford style: repeat n − 1 times 'for each edge, improve the better endpoint's product' — O(n·m), simple and correct. Enumerating all paths is exponential.",
        approach=r"""
1. Adjacency list with `(neighbour, probability)` in both directions.
2. `best[start] = 1`; heap `[(-1, start)]`.
3. Pop the most probable node; if it is the end, return; skip stale entries; for each neighbour compute `p · w` and push when it improves `best`.

**Dry run** Example 1: pop (1.0, node 0) → best[1] = 0.5, best[2] = 0.2. Pop (0.5, node 1) → 0.5 · 0.5 = 0.25 > 0.2 → best[2] = 0.25. Pop (0.25, node 2) → return 0.25.

**Log trick:** maximising a product of probabilities equals minimising the sum of `−log(p)`, which are non-negative weights — ordinary Dijkstra.
""",
        complexity="O((n + m) log n) time, O(n + m) space.",
        pitfalls=r"""
- BFS takes the path with the fewest edges, not the most probable (wrong solution #1).
- Ordering the heap by the last edge's probability instead of the whole path's (wrong solution #2).
- Using a min-heap without negating.
- Initialising `best` with 1 or ∞ — the neutral "nothing found" value for a maximum is 0.
""",
        follow_up="With a limit on the number of edges, use Bellman-Ford rounds (*Cheapest Flights Within K Stops*). Currency-arbitrage detection is the same product-of-rates idea with negative-cycle detection.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="find-the-city-with-the-smallest-number-of-neighbors-at-a-threshold-distance",
    title="Find the City With the Smallest Number of Neighbors at a Threshold Distance",
    difficulty="Medium",
    pattern="Advanced Graphs",
    leetcode="https://leetcode.com/problems/find-the-city-with-the-smallest-number-of-neighbors-at-a-threshold-distance/",
    entry="findTheCity",
    description=r"""
There are `n` cities `0..n-1` joined by two-way roads `edges[i] = [from, to, weight]`. A city `b` is
*within reach* of city `a` if the shortest road distance between them is at most `distanceThreshold`.

Return the city that has the **fewest other cities within reach**. If several cities tie, return the
one with the **largest number**.

**Constraints:** `2 <= n <= 100`, `1 <= len(edges) <= n(n-1)/2`, `1 <= weight, distanceThreshold <= 10^4`, at most one road per pair.

**Example 1:** `n = 4, edges = [[0,1,3],[1,2,1],[1,3,4],[2,3,1]], distanceThreshold = 4` → `3`
(reach: city 0 → {1,2}; 1 → {0,2,3}; 2 → {0,1,3}; 3 → {1,2}. Cities 0 and 3 tie with two; return 3.)

**Example 2:** `n = 5, edges = [[0,1,2],[0,4,8],[1,2,3],[1,4,2],[2,3,1],[3,4,1]], distanceThreshold = 2` → `0`
""",
    starter='''class Solution:
    def findTheCity(self, n: int, edges: List[List[int]], distanceThreshold: int) -> int:
        pass
''',
    solution='''class Solution:
    def findTheCity(self, n, edges, distanceThreshold):
        INF = float("inf")
        d = [[INF] * n for _ in range(n)]
        for i in range(n):
            d[i][i] = 0
        for a, b, w in edges:
            d[a][b] = d[b][a] = w
        for k in range(n):                       # Floyd-Warshall: allow k as an intermediate stop
            dk = d[k]
            for i in range(n):
                dik = d[i][k]
                if dik == INF:
                    continue
                di = d[i]
                for j in range(n):
                    if dik + dk[j] < di[j]:
                        di[j] = dik + dk[j]
        best_city, best_count = -1, n + 1
        for i in range(n):
            count = sum(1 for j in range(n) if j != i and d[i][j] <= distanceThreshold)
            if count <= best_count:              # <= keeps the largest index on ties
                best_city, best_count = i, count
        return best_city
''',
    tests=[
        [4, [[0, 1, 3], [1, 2, 1], [1, 3, 4], [2, 3, 1]], 4],
        [5, [[0, 1, 2], [0, 4, 8], [1, 2, 3], [1, 4, 2], [2, 3, 1], [3, 4, 1]], 2],
        [2, [[0, 1, 1]], 1],
        [2, [[0, 1, 5]], 4],
        [3, [[0, 1, 1], [1, 2, 1]], 1],
        [3, [[0, 1, 1], [1, 2, 1]], 2],
        [4, [[0, 1, 1], [2, 3, 1]], 10],
        [5, [[0, 1, 1], [1, 2, 1], [2, 3, 1], [3, 4, 1], [0, 4, 10]], 2],
        [6, [[0, 1, 10], [0, 2, 1], [2, 4, 10], [4, 5, 10], [1, 3, 10], [3, 5, 10]], 20],
        [30, _wgraph(_R, 30, 60, 20), 15],
        [100, _wgraph(_R, 100, 300, 10000), 9000],
        [100, _wgraph(_R, 100, 4950, 100), 12],
        [100, [[i, i + 1, 100] for i in range(99)], 350],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def findTheCity(self, n, edges, distanceThreshold):
        INF = float("inf"); d = [[INF] * n for _ in range(n)]
        for i in range(n): d[i][i] = 0
        for a, b, w in edges: d[a][b] = d[b][a] = w
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if d[i][k] + d[k][j] < d[i][j]: d[i][j] = d[i][k] + d[k][j]
        best, cnt = -1, n + 1
        for i in range(n):
            c = sum(1 for j in range(n) if j != i and d[i][j] <= distanceThreshold)
            if c < cnt: best, cnt = i, c
        return best
''',
        '''class Solution:
    def findTheCity(self, n, edges, distanceThreshold):
        cnt = [0] * n
        for a, b, w in edges:
            if w <= distanceThreshold: cnt[a] += 1; cnt[b] += 1
        best = 0
        for i in range(n):
            if cnt[i] <= cnt[best]: best = i
        return best
''',
    ],
    guide=dict(
        prereqs="Shortest paths (lesson *Shortest paths: Dijkstra and Bellman-Ford*). New here: the all-pairs algorithm of Floyd and Warshall.",
        intuition=r"""
You need the shortest distance between **every pair** of cities, then a count per city. With only 100
cities the simplest tool is the **Floyd–Warshall** algorithm: start with the direct road lengths and,
for each city `k` in turn, ask for every pair `(i, j)` whether going `i → k → j` beats the best route
known so far. After all `k` have been considered, the table holds true shortest distances. Three
nested loops, n³ = 10⁶ steps.
""",
        hints=[
            "For one city, which algorithm gives the distance to all others? You need that for every city.",
            "n ≤ 100 allows O(n³): dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j]) for k in the OUTER loop.",
            "Count cities within the threshold for each i; use <= when comparing counts so the larger index wins ties.",
        ],
        brute_force="Counting only direct roads within the threshold ignores multi-road routes. A correct slower-to-write alternative is Dijkstra from each city: O(n · m log n).",
        approach=r"""
1. `d[i][i] = 0`, `d[a][b] = d[b][a] = w`, everything else ∞.
2. For `k`, `i`, `j`: relax through `k`.
3. For each city count `j ≠ i` with `d[i][j] <= threshold`; keep the city with the smallest count, preferring later indices.

**Dry run** Example 1, threshold 4: d(0,2) = 3 + 1 = 4 ✔ reachable; d(0,3) = 3 + 1 + 1 = 5 ✘. Counts: 0 → 2, 1 → 3, 2 → 3, 3 → 2. Tie between 0 and 3 → 3.
""",
        complexity="O(n³) time, O(n²) space.",
        pitfalls=r"""
- Tie-break: strict `<` keeps the smallest index (wrong solution #1); the problem wants the largest.
- Considering only direct roads (wrong solution #2).
- Putting `k` in an inner loop — the intermediate city must be the **outermost** loop.
- Counting the city itself.
""",
        follow_up="Floyd–Warshall also handles negative edges (no negative cycles) and gives *transitive closure* with booleans (*Course Schedule IV*). For large sparse graphs use Dijkstra from each source.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="number-of-ways-to-arrive-at-destination",
    title="Number of Ways to Arrive at Destination",
    difficulty="Medium",
    pattern="Advanced Graphs",
    leetcode="https://leetcode.com/problems/number-of-ways-to-arrive-at-destination/",
    entry="countPaths",
    description=r"""
A city has `n` intersections `0..n-1` and two-way roads `roads[i] = [u, v, time]`. You want to drive
from intersection `0` to intersection `n - 1` in the **shortest possible total time**.

Return **how many different routes** achieve that shortest time. Because the count can be huge,
return it modulo `10^9 + 7`.

**Constraints:** `1 <= n <= 200`, the road network is connected, at most one road per pair, `1 <= time <= 10^9`.

**Example 1:** `n = 7, roads = [[0,6,7],[0,1,2],[1,2,3],[1,3,3],[6,3,3],[3,5,1],[6,5,1],[2,5,1],[0,4,5],[4,6,2]]` → `4`
(the shortest time is 7; the four routes are 0→6, 0→4→6, 0→1→2→5→6 and 0→1→3→5→6)

**Example 2:** `n = 2, roads = [[1,0,10]]` → `1`
""",
    starter='''class Solution:
    def countPaths(self, n: int, roads: List[List[int]]) -> int:
        pass
''',
    solution='''import heapq

class Solution:
    def countPaths(self, n, roads):
        MOD = 10**9 + 7
        adj = [[] for _ in range(n)]
        for u, v, t in roads:
            adj[u].append((v, t))
            adj[v].append((u, t))
        dist = [float("inf")] * n
        ways = [0] * n
        dist[0], ways[0] = 0, 1
        heap = [(0, 0)]
        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue
            for v, t in adj[u]:
                nd = d + t
                if nd < dist[v]:                 # strictly better: start counting afresh
                    dist[v] = nd
                    ways[v] = ways[u]
                    heapq.heappush(heap, (nd, v))
                elif nd == dist[v]:              # another equally short way in
                    ways[v] = (ways[v] + ways[u]) % MOD
        return ways[n - 1] % MOD
''',
    tests=[
        [7, [[0, 6, 7], [0, 1, 2], [1, 2, 3], [1, 3, 3], [6, 3, 3], [3, 5, 1], [6, 5, 1], [2, 5, 1], [0, 4, 5], [4, 6, 2]]],
        [2, [[1, 0, 10]]],
        [1, []],
        [3, [[0, 1, 1], [1, 2, 1], [0, 2, 2]]],
        [3, [[0, 1, 1], [1, 2, 1], [0, 2, 3]]],
        [4, [[0, 1, 1], [0, 2, 1], [1, 3, 1], [2, 3, 1]]],
        [4, [[0, 1, 1], [0, 2, 1], [1, 3, 1], [2, 3, 2]]],
        [5, [[0, 1, 1], [1, 2, 4], [0, 4, 3], [3, 2, 5], [3, 4, 1], [3, 0, 5], [1, 3, 1]]],
        [4, [[0, 1, 1000000000], [1, 2, 1000000000], [2, 3, 1000000000], [0, 2, 1000000000], [1, 3, 1000000000]]],
        _diamonds(10),
        _diamonds(40),
        _diamonds(66),
        _diamonds(30, 3, 4),
        [200, _wgraph(_R, 200, 3000, 3)],
        [200, _wgraph(_R, 200, 19900, 1000)],
    ],
    examples=2,
    wrong_solutions=[
        '''import heapq
class Solution:
    def countPaths(self, n, roads):
        adj = [[] for _ in range(n)]
        for u, v, t in roads: adj[u].append((v, t)); adj[v].append((u, t))
        dist = [float("inf")] * n; ways = [0] * n; dist[0], ways[0] = 0, 1; heap = [(0, 0)]
        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]: continue
            for v, t in adj[u]:
                nd = d + t
                if nd < dist[v]:
                    dist[v] = nd; ways[v] = ways[u]; heapq.heappush(heap, (nd, v))
                elif nd == dist[v]:
                    ways[v] += ways[u]
        return ways[n - 1]
''',
        '''from collections import deque
class Solution:
    def countPaths(self, n, roads):
        MOD = 10**9 + 7
        adj = [[] for _ in range(n)]
        for u, v, t in roads: adj[u].append(v); adj[v].append(u)
        dist = [-1] * n; ways = [0] * n; dist[0], ways[0] = 0, 1; q = deque([0])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if dist[v] == -1:
                    dist[v] = dist[u] + 1; ways[v] = ways[u]; q.append(v)
                elif dist[v] == dist[u] + 1:
                    ways[v] = (ways[v] + ways[u]) % MOD
        return ways[n - 1]
''',
    ],
    guide=dict(
        prereqs="Dijkstra's algorithm with a distance array (lesson *Shortest paths: Dijkstra and Bellman-Ford*); counting paths by adding up predecessors.",
        intuition=r"""
Run Dijkstra, and carry a second number for each intersection: `ways[v]`, the number of shortest
routes from 0 to `v` found so far. When an edge `u → v` gives a **strictly shorter** time, every
earlier route to `v` is obsolete, so `ways[v]` is reset to `ways[u]`. When it gives **exactly the
same** time, the routes through `u` are additional shortest routes, so add `ways[u]`. Dijkstra
finalises `u` before any node farther away, so `ways[u]` is complete by the time it is used
(road times are positive).
""",
        hints=[
            "First find the shortest time. What extra information per node would let you count the routes?",
            "ways[v] = sum of ways[u] over all neighbours u that lie on a shortest route into v.",
            "During relaxation: nd < dist[v] → dist[v] = nd, ways[v] = ways[u], push. nd == dist[v] → ways[v] += ways[u] (mod 1e9+7).",
        ],
        brute_force="Enumerate every route with DFS and count those whose total equals the minimum — exponential (2⁶⁶ routes in one of the tests).",
        approach=r"""
1. Adjacency list; `dist[0] = 0`, `ways[0] = 1`.
2. Dijkstra with lazy deletion. For each edge out of the popped node apply the two rules above.
3. Return `ways[n-1] % (10⁹ + 7)`.

**Dry run** `n = 4`, roads 0–1, 0–2, 1–3, 2–3 all of time 1: pop 0 → dist[1] = dist[2] = 1, ways 1 each. Pop 1 → dist[3] = 2, ways[3] = 1. Pop 2 → 1 + 1 == dist[3] → ways[3] = 2. Answer 2.
""",
        complexity="O((n + m) log n) time, O(n + m) space.",
        pitfalls=r"""
- Forgetting the modulo (wrong solution #1) — counts exceed 10⁹ + 7 quickly.
- Using BFS / hop counts when roads have different times (wrong solution #2).
- Adding on `<=` without resetting the count on a strict improvement.
- Using 32-bit style sentinels: total times reach about 2·10¹¹, so "infinity" must be larger (`float('inf')` is safe).
- Pushing a node again on an equal distance — unnecessary, and with naive handling it double-counts.
""",
        follow_up="The same 'distance + count' pair works with BFS on unweighted graphs (*Number of Shortest Paths*) and with DP on DAGs. *Second Minimum Time to Reach Destination* tracks two distances per node.",
    ),
),
]
