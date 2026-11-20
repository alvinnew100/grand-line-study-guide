import random

_R = random.Random(90210)


def _times(rng, n, m, wmax=100, connected=True):
    edges = {}
    if connected:
        order = list(range(1, n + 1))
        rng.shuffle(order)
        for i in range(1, n):
            u = order[rng.randint(0, i - 1)]
            edges[(u, order[i])] = rng.randint(0, wmax)
        k = order[0]
    else:
        k = rng.randint(1, n)
    tries = 0
    while len(edges) < m and tries < 20 * m:
        tries += 1
        u, v = rng.sample(range(1, n + 1), 2)
        if (u, v) not in edges:
            edges[(u, v)] = rng.randint(0, wmax)
    lst = [[u, v, w] for (u, v), w in edges.items()]
    rng.shuffle(lst)
    return [lst, n, k]


def _itinerary(rng, airports, legs):
    """tickets forming a walk from JFK, so a valid itinerary always exists"""
    cur, tickets = "JFK", []
    for _ in range(legs):
        nxt = rng.choice([a for a in airports if a != cur])
        tickets.append([cur, nxt])
        cur = nxt
    rng.shuffle(tickets)
    return [tickets]


def _points(rng, n, lim):
    pts = set()
    while len(pts) < n:
        pts.add((rng.randint(-lim, lim), rng.randint(-lim, lim)))
    pts = [list(p) for p in pts]
    rng.shuffle(pts)
    return [pts]


def _perm_grid(rng, n):
    vals = list(range(n * n))
    rng.shuffle(vals)
    return [[vals[r * n:(r + 1) * n] for r in range(n)]]


def _alien_words(rng, k, count, maxlen):
    letters = rng.sample("abcdefghijklmnopqrstuvwxyz", k)
    rank = {ch: i for i, ch in enumerate(letters)}
    words = set()
    while len(words) < count:
        words.add("".join(rng.choice(letters) for _ in range(rng.randint(1, maxlen))))
    return [sorted(words, key=lambda w: [rank[ch] for ch in w])]


def _flights(rng, n, m, pmax, k):
    edges = {}
    tries = 0
    while len(edges) < m and tries < 20 * m:
        tries += 1
        u, v = rng.sample(range(n), 2)
        if (u, v) not in edges:
            edges[(u, v)] = rng.randint(1, pmax)
    src, dst = rng.sample(range(n), 2)
    return [n, [[u, v, w] for (u, v), w in edges.items()], src, dst, k]


_ALIEN_CHECK = '''
def check(args, got, expected):
    words = args[0]
    if expected == "":
        return got == ""
    if not isinstance(got, str):
        return False
    letters = set("".join(words))
    if len(got) != len(letters) or set(got) != letters:
        return False
    pos = {ch: i for i, ch in enumerate(got)}
    for w1, w2 in zip(words, words[1:]):
        for a, b in zip(w1, w2):
            if a != b:
                if pos[a] > pos[b]:
                    return False
                break
    return True
'''

PROBLEMS = [
# ---------------------------------------------------------------------------------------------
dict(
    id="network-delay-time",
    title="Network Delay Time",
    difficulty="Medium",
    pattern="Advanced Graphs",
    leetcode="https://leetcode.com/problems/network-delay-time/",
    neetcode="https://neetcode.io/problems/network-delay-time",
    entry="networkDelayTime",
    description=r"""
A network has `n` nodes labelled `1..n`. Each entry `times[i] = [u, v, w]` is a **one-way** link:
a signal leaving `u` arrives at `v` after `w` time units.

A signal is sent from node `k` and is forwarded along every link the moment it arrives. Return the
time at which the **last** node receives it, or `-1` if some node never does.

**Constraints:** `1 <= k <= n <= 100`, `1 <= len(times) <= 6000`, `0 <= w <= 100`, at most one link per ordered pair `(u, v)`, `u != v`.

**Example 1:** `times = [[2,1,1],[2,3,1],[3,4,1]], n = 4, k = 2` → `2`

**Example 2:** `times = [[1,2,1]], n = 2, k = 2` → `-1` (node 1 is unreachable from 2)
""",
    starter='''class Solution:
    def networkDelayTime(self, times: List[List[int]], n: int, k: int) -> int:
        pass
''',
    solution='''import heapq

class Solution:
    def networkDelayTime(self, times, n, k):
        adj = [[] for _ in range(n + 1)]
        for u, v, w in times:
            adj[u].append((v, w))
        dist = {}
        heap = [(0, k)]
        while heap:
            d, u = heapq.heappop(heap)
            if u in dist:
                continue                 # stale entry
            dist[u] = d
            for v, w in adj[u]:
                if v not in dist:
                    heapq.heappush(heap, (d + w, v))
        return max(dist.values()) if len(dist) == n else -1
''',
    tests=[
        [[[2, 1, 1], [2, 3, 1], [3, 4, 1]], 4, 2],
        [[[1, 2, 1]], 2, 2],
        [[[1, 2, 1]], 2, 1],
        [[[1, 2, 5], [1, 3, 1], [3, 2, 1]], 3, 1],
        [[[1, 2, 1], [2, 3, 2], [1, 3, 4]], 3, 1],
        [[[1, 2, 1], [2, 1, 3]], 2, 2],
        [[[1, 2, 0], [2, 3, 0]], 3, 1],
        [[[1, 2, 1], [2, 3, 7], [1, 3, 4], [2, 1, 2]], 4, 1],
        [[[1, 2, 10], [1, 3, 1], [3, 4, 1], [4, 5, 1], [5, 2, 1]], 5, 1],
        _times(_R, 30, 120),
        _times(_R, 100, 6000),
        _times(_R, 100, 300),
        _times(_R, 100, 150, connected=False),
        [[[i, i + 1, 100] for i in range(1, 100)], 100, 1],
    ],
    examples=2,
    wrong_solutions=[
        '''from collections import deque
class Solution:
    def networkDelayTime(self, times, n, k):
        adj = [[] for _ in range(n + 1)]
        for u, v, w in times: adj[u].append((v, w))
        dist = {k: 0}; q = deque([k])
        while q:
            u = q.popleft()
            for v, w in adj[u]:
                if v not in dist:
                    dist[v] = dist[u] + w; q.append(v)
        return max(dist.values()) if len(dist) == n else -1
''',
        '''import heapq
class Solution:
    def networkDelayTime(self, times, n, k):
        adj = [[] for _ in range(n + 1)]
        for u, v, w in times: adj[u].append((v, w))
        dist = {}; heap = [(0, k)]
        while heap:
            d, u = heapq.heappop(heap)
            if u in dist: continue
            dist[u] = d
            for v, w in adj[u]: heapq.heappush(heap, (d + w, v))
        return max(dist.values())
''',
    ],
    guide=dict(
        prereqs="Weighted graphs and Dijkstra's algorithm (lesson *Shortest paths: Dijkstra and Bellman-Ford*); `heapq`.",
        intuition=r"""
The signal reaches each node at its **shortest-path distance** from `k`. The moment everyone has it
is the *largest* of those distances. Weights are non-negative, so Dijkstra applies: repeatedly
finalise the closest not-yet-finalised node, using a min-heap of `(distance, node)`.
""",
        hints=[
            "When does a single node first receive the signal? What well-known quantity is that?",
            "You need single-source shortest paths with non-negative weights, then one aggregate over all nodes.",
            "Dijkstra with a heap; answer = max(dist) if all n nodes were reached, else −1.",
        ],
        brute_force="Bellman-Ford: relax every edge n − 1 times — O(V·E) = 100 · 6000, which is perfectly fine here. A BFS that takes the first arrival ignores weights and is wrong.",
        approach=r"""
1. Adjacency list `adj[u] = [(v, w)]`.
2. Heap `[(0, k)]`, `dist = {}`.
3. Pop `(d, u)`; skip if `u` is already finalised (**lazy deletion** of stale entries); otherwise `dist[u] = d` and push `(d + w, v)` for each out-edge.
4. If `len(dist) < n` return −1, else `max(dist.values())`.

**Dry run** Example 1 from k = 2: pop (0,2) → push (1,1),(1,3). Pop (1,1). Pop (1,3) → push (2,4). Pop (2,4). dist = {2:0, 1:1, 3:1, 4:2} → 2.
""",
        complexity="O((V + E) log V) with a binary heap — O(E log E) with lazy deletion, same thing asymptotically. Space O(V + E).",
        pitfalls=r"""
- Plain BFS: the first path to arrive in hops isn't the cheapest in weight (wrong solution #1).
- Forgetting the unreachable case (wrong solution #2 returns a max over only the reached nodes).
- Finalising a node when it is *pushed* instead of when it is *popped*.
- Nodes are 1-indexed.
""",
        follow_up="With negative weights you'd need Bellman-Ford. For all-pairs delays, Floyd–Warshall in O(V³). Related: *Path With Minimum Effort*, *Swim in Rising Water* (Dijkstra with a different path cost).",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="reconstruct-itinerary",
    title="Reconstruct Itinerary",
    difficulty="Hard",
    pattern="Advanced Graphs",
    leetcode="https://leetcode.com/problems/reconstruct-itinerary/",
    neetcode="https://neetcode.io/problems/reconstruct-flight-path",
    entry="findItinerary",
    description=r"""
You have a pile of airline tickets, each `[from, to]` with three-letter airport codes. The traveller
starts at `"JFK"` and uses **every ticket exactly once**. Reconstruct the route as a list of
airports in visiting order.

If more than one route uses all tickets, return the one that is **smallest in lexicographic order**
when read as a list of strings (compare the first airport that differs). At least one valid route is guaranteed.
The same ticket may appear more than once.

**Constraints:** `1 <= len(tickets) <= 300`.

**Example 1:** `[["MUC","LHR"],["JFK","MUC"],["SFO","SJC"],["LHR","SFO"]]` → `["JFK","MUC","LHR","SFO","SJC"]`

**Example 2:** `[["JFK","SFO"],["JFK","ATL"],["SFO","ATL"],["ATL","JFK"],["ATL","SFO"]]` → `["JFK","ATL","JFK","SFO","ATL","SFO"]`

**Example 3:** `[["JFK","KUL"],["JFK","NRT"],["NRT","JFK"]]` → `["JFK","NRT","JFK","KUL"]`
(going to KUL first would be a dead end)
""",
    starter='''class Solution:
    def findItinerary(self, tickets: List[List[str]]) -> List[str]:
        pass
''',
    solution='''from collections import defaultdict

class Solution:
    def findItinerary(self, tickets):
        adj = defaultdict(list)
        for a, b in sorted(tickets, reverse=True):
            adj[a].append(b)              # smallest destination ends up last -> pop() is O(1)
        route, stack = [], ["JFK"]
        while stack:
            while adj[stack[-1]]:
                stack.append(adj[stack[-1]].pop())
            route.append(stack.pop())     # stuck: this airport is next from the END of the route
        return route[::-1]
''',
    tests=[
        [[["MUC", "LHR"], ["JFK", "MUC"], ["SFO", "SJC"], ["LHR", "SFO"]]],
        [[["JFK", "SFO"], ["JFK", "ATL"], ["SFO", "ATL"], ["ATL", "JFK"], ["ATL", "SFO"]]],
        [[["JFK", "KUL"], ["JFK", "NRT"], ["NRT", "JFK"]]],
        [[["JFK", "AAA"]]],
        [[["JFK", "AAA"], ["AAA", "JFK"], ["JFK", "AAA"], ["AAA", "JFK"]]],
        [[["JFK", "ATL"], ["ATL", "JFK"]]],
        [[["EZE", "AXA"], ["TIA", "ANU"], ["ANU", "JFK"], ["JFK", "ANU"], ["ANU", "EZE"], ["TIA", "ANU"],
          ["AXA", "TIA"], ["TIA", "JFK"], ["ANU", "TIA"], ["JFK", "TIA"]]],
        [[["JFK", "A"], ["JFK", "B"], ["B", "JFK"], ["A", "C"], ["C", "A"], ["A", "JFK"], ["JFK", "D"]]],
        _itinerary(random.Random(61), ["JFK", "AAA", "BBB"], 12),
        _itinerary(random.Random(62), ["JFK", "ATL", "SFO", "LAX", "ORD"], 40),
        _itinerary(random.Random(63), ["JFK"] + ["A%02d" % i for i in range(30)], 300),
        _itinerary(random.Random(64), ["JFK", "ZZZ", "YYY", "XXX"], 300),
        [[["JFK", "N%03d" % 1]] + [["N%03d" % i, "N%03d" % (i + 1)] for i in range(1, 299)]],
    ],
    examples=3,
    wrong_solutions=[
        '''from collections import defaultdict
class Solution:
    def findItinerary(self, tickets):
        adj = defaultdict(list)
        for a, b in sorted(tickets, reverse=True): adj[a].append(b)
        route, cur = ["JFK"], "JFK"
        while adj[cur]:
            cur = adj[cur].pop(); route.append(cur)
        return route
''',
        '''from collections import defaultdict
class Solution:
    def findItinerary(self, tickets):
        adj = defaultdict(list)
        for a, b in sorted(tickets): adj[a].append(b)
        route, stack = [], ["JFK"]
        while stack:
            while adj[stack[-1]]: stack.append(adj[stack[-1]].pop())
            route.append(stack.pop())
        return route[::-1]
''',
    ],
    guide=dict(
        prereqs="Eulerian paths and Hierholzer's algorithm (lesson *Eulerian paths and Hierholzer's algorithm*).",
        intuition=r"""
Airports are vertices, tickets are directed edges, and "use every ticket exactly once" is an
**Eulerian path** starting at JFK. Hierholzer's algorithm: walk greedily (always the smallest
destination) until you're stuck; the vertex where you get stuck must be the **end** of the route, so
record it and back up. Recording vertices in post-order and reversing yields the full path — and the
greedy smallest-first choice makes it the lexicographically smallest one.
""",
        hints=[
            "Every ticket once = every edge once. Which classic graph object is that?",
            "Greedily flying to the smallest destination can strand you (Example 3). What do you know about the airport where you get stuck?",
            "DFS that consumes edges; append the airport to the route AFTER all its outgoing tickets are used; reverse at the end.",
        ],
        brute_force="Backtracking: sort destinations, try each unused ticket, undo on dead ends, and stop at the first complete route. Correct, but exponential in the worst case (it can time out with many repeated tickets).",
        approach=r"""
1. Sort tickets in **reverse** and append to `adj[from]`, so `pop()` returns the smallest remaining destination in O(1).
2. Iterative Hierholzer: `stack = ["JFK"]`. While the top has unused tickets, push the next destination. When it has none, pop it onto `route`.
3. Return `route[::-1]`.

**Dry run** Example 3: adj JFK = [NRT, KUL] (pop gives KUL first), NRT = [JFK].
stack JFK → KUL (stuck) → route [KUL]. Back at JFK → NRT → JFK (stuck) → route [KUL, JFK] → NRT stuck → [KUL, JFK, NRT] → JFK stuck → [KUL, JFK, NRT, JFK]. Reversed: `JFK NRT JFK KUL` ✔.
""",
        complexity="O(E log E) for sorting, O(E) for the traversal; O(E) space.",
        pitfalls=r"""
- Pure greedy without post-order recording strands tickets (wrong solution #1).
- Popping the *largest* destination first (wrong solution #2) — sort order vs. pop end mismatch.
- Using `list.pop(0)` makes it O(E²); use reverse-sorted lists or a heap per airport.
- Deduplicating tickets with a set — duplicates are distinct tickets.
""",
        follow_up="*Valid Arrangement of Pairs* (LeetCode 2097) needs you to find the start vertex first (out-degree − in-degree = 1). *Cracking the Safe* is an Eulerian circuit on a de Bruijn graph.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="min-cost-to-connect-all-points",
    title="Min Cost to Connect All Points",
    difficulty="Medium",
    pattern="Advanced Graphs",
    leetcode="https://leetcode.com/problems/min-cost-to-connect-all-points/",
    neetcode="https://neetcode.io/problems/min-cost-to-connect-points",
    entry="minCostConnectPoints",
    description=r"""
You are given distinct points on a plane, `points[i] = [x, y]`. Connecting two points costs their
**Manhattan distance** `|x1 - x2| + |y1 - y2|`. Choose connections so that every point can reach
every other point (directly or through others) at the minimum total cost, and return that cost.

**Constraints:** `1 <= len(points) <= 1000`, `-10^6 <= x, y <= 10^6`, all points distinct.

**Example 1:** `[[0,0],[2,2],[3,10],[5,2],[7,0]]` → `20`

**Example 2:** `[[3,12],[-2,5],[-4,1]]` → `18`
""",
    starter='''class Solution:
    def minCostConnectPoints(self, points: List[List[int]]) -> int:
        pass
''',
    solution='''class Solution:
    def minCostConnectPoints(self, points):
        n = len(points)
        INF = float("inf")
        best = [INF] * n          # cheapest edge from the tree to each outside point
        best[0] = 0
        in_tree = [False] * n
        total = 0
        for _ in range(n):
            u, bu = -1, INF
            for i in range(n):
                if not in_tree[i] and best[i] < bu:
                    u, bu = i, best[i]
            in_tree[u] = True
            total += bu
            ux, uy = points[u]
            for v in range(n):
                if not in_tree[v]:
                    d = abs(ux - points[v][0]) + abs(uy - points[v][1])
                    if d < best[v]:
                        best[v] = d
        return total
''',
    tests=[
        [[[0, 0], [2, 2], [3, 10], [5, 2], [7, 0]]],
        [[[3, 12], [-2, 5], [-4, 1]]],
        [[[0, 0]]],
        [[[0, 0], [1, 1]]],
        [[[0, 0], [1, 1], [1, 0], [-1, 1]]],
        [[[-1000000, -1000000], [1000000, 1000000]]],
        [[[2, -3], [-17, -8], [13, 8], [-17, -15]]],
        [[[0, 0], [10, 0], [11, 0], [21, 0], [22, 0]]],
        [[[0, 0], [0, 3], [4, 0], [4, 3], [2, 1]]],
        _points(_R, 50, 100),
        _points(_R, 300, 1000000),
        _points(_R, 400, 30),
        [[[i, (i * i) % 97] for i in range(350)]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def minCostConnectPoints(self, points):
        n = len(points); used = [False] * n; used[0] = True; cur = 0; total = 0
        for _ in range(n - 1):
            b, bd = -1, float("inf")
            for j in range(n):
                if not used[j]:
                    d = abs(points[cur][0] - points[j][0]) + abs(points[cur][1] - points[j][1])
                    if d < bd: b, bd = j, d
            used[b] = True; total += bd; cur = b
        return total
''',
        '''class Solution:
    def minCostConnectPoints(self, points):
        n = len(points); total = 0
        for i in range(1, n):
            total += min(abs(points[i][0] - points[j][0]) + abs(points[i][1] - points[j][1]) for j in range(n) if j != i)
        return total
''',
    ],
    guide=dict(
        prereqs="Minimum spanning trees, Prim's and Kruskal's algorithms (lesson *Minimum spanning trees*).",
        intuition=r"""
"Connect everything at minimum total cost" is the definition of a **minimum spanning tree** on the
complete graph whose edge weights are Manhattan distances. The graph is dense (≈ n²/2 edges), which
is where the **array-based Prim** shines: grow a tree from point 0, always attaching the outside
point with the cheapest connection to the tree, in O(n²) with no heap at all.
""",
        hints=[
            "The cheapest set of connections that links all points and has no redundant connection is a well-known structure.",
            "The graph is complete: about n²/2 edges. Which MST algorithm is best for dense graphs?",
            "Prim: best[v] = cheapest distance from v to the tree. Repeat n times: take the outside point with the smallest best, add its cost, update best for the others.",
        ],
        brute_force="Enumerate all spanning trees — there are nⁿ⁻² of them (Cayley's formula). Kruskal with all n² edges sorted (O(n² log n)) is the simplest correct approach and is acceptable.",
        approach=r"""
**Prim, O(n²):**
1. `best[0] = 0`, others ∞; nothing in the tree.
2. Repeat n times: pick the outside vertex `u` with minimum `best[u]`; add `best[u]` to the total; for every outside `v` set `best[v] = min(best[v], dist(u, v))`.

**Dry run** Example 1, points A(0,0) B(2,2) C(3,10) D(5,2) E(7,0):
take A (0) → best: B4 C13 D7 E7. Take B (4) → C9 D3 E7. Take D (3) → C stays 9 (D offers 10); E improves to 4. Take E (4). Take C (9). Total 4 + 3 + 4 + 9 = **20**.

**Kruskal alternative:** generate all pairs, sort by distance, union-find; stop after n − 1 unions.
""",
        complexity="Array Prim: O(n²) time, O(n) space. Heap Prim / Kruskal on the complete graph: O(n² log n) time, O(n²) space.",
        pitfalls=r"""
- Nearest-neighbour *chain* (always extend from the last point added) builds a path, not an MST (wrong solution #1).
- Summing each point's nearest-neighbour distance double-counts or leaves the graph disconnected (wrong solution #2).
- Using Euclidean distance.
- In heap Prim, forgetting to skip vertices already in the tree when popped.
""",
        follow_up="For Manhattan MSTs with n up to 10⁵ there is an O(n log n) algorithm that only considers each point's nearest neighbour in 8 octants. Related: *Connecting Cities With Minimum Cost*, *Optimize Water Distribution in a Village*.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="swim-in-rising-water",
    title="Swim in Rising Water",
    difficulty="Hard",
    pattern="Advanced Graphs",
    leetcode="https://leetcode.com/problems/swim-in-rising-water/",
    neetcode="https://neetcode.io/problems/swim-in-rising-water",
    entry="swimInWater",
    description=r"""
An `n × n` grid holds elevations; `grid[r][c]` is the height of that cell, and all heights are
distinct. Rain raises the water level so that at time `t` the water depth everywhere is `t`. You can
swim between 4-directionally adjacent cells only if **both** cells have elevation at most `t`;
swimming itself takes no time.

Starting in the top-left cell, return the smallest `t` at which you can reach the bottom-right cell.

Equivalently: over all paths from `(0,0)` to `(n-1,n-1)`, minimise the **largest elevation on the path**.

**Constraints:** `1 <= n <= 50`, the grid is a permutation of `0 .. n²-1`.

**Example 1:** `[[0,2],[1,3]]` → `3`

**Example 2:**
```
[[ 0, 1, 2, 3, 4],
 [24,23,22,21, 5],
 [12,13,14,15,16],
 [11,17,18,19,20],
 [10, 9, 8, 7, 6]]   -> 16
```
""",
    starter='''class Solution:
    def swimInWater(self, grid: List[List[int]]) -> int:
        pass
''',
    solution='''import heapq

class Solution:
    def swimInWater(self, grid):
        n = len(grid)
        seen = [[False] * n for _ in range(n)]
        heap = [(grid[0][0], 0, 0)]       # (max elevation on the path so far, r, c)
        seen[0][0] = True
        while heap:
            t, r, c = heapq.heappop(heap)
            if r == n - 1 and c == n - 1:
                return t
            for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if 0 <= nr < n and 0 <= nc < n and not seen[nr][nc]:
                    seen[nr][nc] = True
                    heapq.heappush(heap, (max(t, grid[nr][nc]), nr, nc))
        return -1
''',
    tests=[
        [[[0, 2], [1, 3]]],
        [[[0, 1, 2, 3, 4], [24, 23, 22, 21, 5], [12, 13, 14, 15, 16], [11, 17, 18, 19, 20], [10, 9, 8, 7, 6]]],
        [[[0]]],
        [[[3, 2], [0, 1]]],
        [[[0, 3], [1, 2]]],
        [[[0, 1, 2], [5, 4, 3], [6, 7, 8]]],
        [[[8, 0, 1], [7, 6, 2], [5, 4, 3]]],
        [[[0, 8, 7], [1, 6, 5], [2, 3, 4]]],
        [[[0, 5, 6, 15], [1, 4, 7, 14], [2, 3, 8, 13], [11, 10, 9, 12]]],
        [[[0, 15, 14, 13], [1, 12, 5, 6], [2, 3, 4, 7], [11, 10, 9, 8]]],
        _perm_grid(_R, 10),
        _perm_grid(_R, 30),
        _perm_grid(_R, 50),
        [[[r * 50 + (c if r % 2 == 0 else 49 - c) for c in range(50)] for r in range(50)]],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def swimInWater(self, grid):
        n = len(grid)
        dp = [[0] * n for _ in range(n)]
        for r in range(n):
            for c in range(n):
                if r == 0 and c == 0: dp[r][c] = grid[0][0]
                else:
                    best = min(dp[r-1][c] if r else float("inf"), dp[r][c-1] if c else float("inf"))
                    dp[r][c] = max(best, grid[r][c])
        return dp[-1][-1]
''',
        '''class Solution:
    def swimInWater(self, grid):
        return max(grid[0][0], grid[-1][-1])
''',
    ],
    guide=dict(
        prereqs="Dijkstra's algorithm and why its greedy choice works (lesson *Shortest paths*). Optional: binary search on the answer, union-find.",
        intuition=r"""
The "cost" of a path is not the sum of its cells but the **maximum** cell on it — a *bottleneck* (minimax)
path. Dijkstra still works, because extending a path can never decrease its cost
(`max(t, next)` ≥ `t`), which is the only property the greedy proof needs. Use a min-heap keyed on the
max elevation so far; the first time you pop the destination, that key is the answer.
""",
        hints=[
            "Restate the goal without time: among all paths, minimise the highest cell you step on.",
            "Dijkstra finalises the cheapest frontier node. Does that argument still hold if path cost = max instead of sum?",
            "Heap of (max_so_far, r, c). Pop the smallest; push neighbours with max(max_so_far, grid[nr][nc]); return when you pop the bottom-right cell.",
        ],
        brute_force="For each `t` from 0 to n²−1, BFS using only cells ≤ t and stop when the corner is reachable: O(n⁴). Binary search on `t` improves this to O(n² log n).",
        approach=r"""
1. Push `(grid[0][0], 0, 0)`.
2. Pop `(t, r, c)`. If it's the target, return `t`.
3. For each unvisited neighbour push `(max(t, grid[nr][nc]), nr, nc)` and mark it visited.

Marking on push is safe here: the popped `t` values never decrease, so the first time a cell is discovered, it is discovered with the smallest possible key (the cell's own elevation is part of every path into it).

**Dry run** `[[0,2],[1,3]]`: pop (0,(0,0)) → push (2,(0,1)), (1,(1,0)). Pop (1,(1,0)) → push (3,(1,1)). Pop (2,(0,1)). Pop (3,(1,1)) → return 3.

Alternatives: **binary search + BFS**; or **Kruskal-style union-find** — add cells in increasing elevation, union with already-added neighbours, stop when the two corners are connected.
""",
        complexity="O(n² log n) time (n² cells, each pushed once), O(n²) space.",
        pitfalls=r"""
- DP over right/down moves only (wrong solution #1) — the best path may go up or left (Example 2 spirals).
- Summing elevations instead of taking the max.
- Forgetting that the start cell's own elevation counts (`[[3,2],[0,1]]` → 3).
""",
        follow_up="*Path With Minimum Effort* (max absolute height difference) and *Path with Maximum Minimum Value* are the same minimax pattern.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="alien-dictionary",
    title="Alien Dictionary",
    difficulty="Hard",
    pattern="Advanced Graphs",
    leetcode="https://leetcode.com/problems/alien-dictionary/",
    neetcode="https://neetcode.io/problems/foreign-dictionary",
    entry="alienOrder",
    checker=_ALIEN_CHECK,
    description=r"""
An alien language uses the lowercase English letters, but in an unknown alphabetical order. You are
given a list of `words` that is claimed to be **sorted according to the alien order** (dictionary
style: compare letter by letter; if one word is a prefix of the other, the shorter comes first).

Return a string containing **every distinct letter that appears in the words exactly once**, arranged
in an order consistent with the list. If several orders are consistent, return any (the judge
verifies yours). If the list cannot be sorted under any letter order, return `""`.

**Constraints:** `1 <= len(words) <= 100`, `1 <= len(words[i]) <= 100`, lowercase letters.

**Example 1:** `["wrt","wrf","er","ett","rftt"]` → `"wertf"`

**Example 2:** `["z","x"]` → `"zx"`

**Example 3:** `["z","x","z"]` → `""` (z before x and x before z)

**Example 4:** `["abc","ab"]` → `""` (a longer word can't precede its own prefix)
""",
    starter='''class Solution:
    def alienOrder(self, words: List[str]) -> str:
        pass
''',
    solution='''from collections import deque

class Solution:
    def alienOrder(self, words):
        adj = {ch: set() for w in words for ch in w}
        indeg = {ch: 0 for ch in adj}
        for w1, w2 in zip(words, words[1:]):
            for a, b in zip(w1, w2):
                if a != b:
                    if b not in adj[a]:
                        adj[a].add(b)
                        indeg[b] += 1
                    break
            else:
                if len(w1) > len(w2):
                    return ""             # "abc" before "ab" is impossible
        q = deque(sorted(ch for ch in adj if indeg[ch] == 0))
        out = []
        while q:
            ch = q.popleft()
            out.append(ch)
            for nb in sorted(adj[ch]):
                indeg[nb] -= 1
                if indeg[nb] == 0:
                    q.append(nb)
        return "".join(out) if len(out) == len(adj) else ""
''',
    tests=[
        [["wrt", "wrf", "er", "ett", "rftt"]],
        [["z", "x"]],
        [["z", "x", "z"]],
        [["abc", "ab"]],
        [["z"]],
        [["z", "z"]],
        [["ab", "abc"]],
        [["abc", "bcd", "qwert", "ab"]],
        [["ac", "ab", "zc", "zb"]],
        [["a", "b", "ca", "cc"]],
        [["hello", "leetcode"]],
        [["ri", "xz", "qxf", "jhsguaw", "dztqrbwbm", "dhdqfb", "jdv", "fcgfsilnb", "ooby"]],
        [["aa", "abb", "aba"]],
        _alien_words(random.Random(71), 5, 40, 6),
        _alien_words(random.Random(72), 26, 100, 100),
        _alien_words(random.Random(73), 12, 100, 4),
        [["x" * 99 + "a", "x" * 99 + "b", "x" * 99 + "c", "x" * 99 + "a"]],
    ],
    examples=4,
    wrong_solutions=[
        '''class Solution:
    def alienOrder(self, words):
        return "".join(sorted(set("".join(words))))
''',
        '''from collections import deque
class Solution:
    def alienOrder(self, words):
        adj = {ch: set() for w in words for ch in w}
        indeg = {ch: 0 for ch in adj}
        for w1, w2 in zip(words, words[1:]):
            for a, b in zip(w1, w2):
                if a != b:
                    if b not in adj[a]:
                        adj[a].add(b); indeg[b] += 1
                    break
        q = deque(ch for ch in adj if indeg[ch] == 0); out = []
        while q:
            ch = q.popleft(); out.append(ch)
            for nb in adj[ch]:
                indeg[nb] -= 1
                if indeg[nb] == 0: q.append(nb)
        return "".join(out) if len(out) == len(adj) else ""
''',
        '''from collections import deque
class Solution:
    def alienOrder(self, words):
        adj = {ch: set() for w in words for ch in w}
        indeg = {ch: 0 for ch in adj}
        for w1, w2 in zip(words, words[1:]):
            for a, b in zip(w1, w2):
                if a != b:
                    adj[a].add(b); indeg[b] += 1
        q = deque(ch for ch in adj if indeg[ch] == 0); out = []
        while q:
            ch = q.popleft(); out.append(ch)
            for nb in adj[ch]:
                indeg[nb] -= 1
                if indeg[nb] == 0: q.append(nb)
        return "".join(out) if len(out) == len(adj) else ""
''',
    ],
    guide=dict(
        prereqs="Topological sort (lesson *Cycle detection and topological sort*); how dictionary order compares two words.",
        intuition=r"""
In a sorted dictionary, two **adjacent** words tell you exactly one fact: at the first position where
they differ, the letter of the earlier word comes before the letter of the later word. Collect these
facts as directed edges between letters; any **topological order** of that graph is a valid alphabet.
A cycle means the list is inconsistent. One extra trap: if no position differs and the first word is
longer, the list is invalid on its own.
""",
        hints=[
            "Compare two neighbouring words. How much information about the letter order do they give you?",
            "Only the first differing position matters — letters after it tell you nothing. Build a graph of 'comes before' edges.",
            "Topologically sort all letters that appear (Kahn). Return '' on a cycle or when a word is followed by its own proper prefix.",
        ],
        brute_force="Try all permutations of the distinct letters (up to 26!) and test each against the list. Comparing *all* pairs of words instead of adjacent pairs is correct but adds only redundant edges at O(N²·L) cost.",
        approach=r"""
1. Create a node for **every** letter seen (letters with no constraints must still be output).
2. For each adjacent pair, find the first index with `a != b`; add edge `a → b` once (avoid double-counting in-degree). If there is no such index and `len(w1) > len(w2)`, return `""`.
3. Kahn's algorithm; if the output is shorter than the number of letters, there's a cycle → `""`.

**Dry run** Example 1: wrt/wrf → t→f; wrf/er → w→e; er/ett → r→t; ett/rftt → e→r.
Chain w → e → r → t → f → `"wertf"`.
""",
        complexity="O(C) time where C is the total number of characters (each adjacent pair is scanned once) plus O(V + E) with V ≤ 26, E ≤ 26². Space O(V + E).",
        pitfalls=r"""
- Missing the prefix rule (wrong solution #2 accepts `["abc","ab"]`).
- Adding edges for **every** differing position instead of only the first (wrong solution #3).
- Incrementing in-degree for a duplicate edge.
- Omitting letters that never appear in any constraint.
""",
        follow_up="How would you tell whether the order is *unique*? (Kahn's queue must never hold more than one letter.) Related: *Verifying an Alien Dictionary*, *Sequence Reconstruction*.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="cheapest-flights-within-k-stops",
    title="Cheapest Flights Within K Stops",
    difficulty="Medium",
    pattern="Advanced Graphs",
    leetcode="https://leetcode.com/problems/cheapest-flights-within-k-stops/",
    neetcode="https://neetcode.io/problems/cheapest-flight-path",
    entry="findCheapestPrice",
    description=r"""
There are `n` cities `0..n-1` and a list of one-way flights `[from, to, price]`. Find the cheapest
total price to travel from `src` to `dst` using **at most `k` intermediate stops** (so at most
`k + 1` flights). Return `-1` if no such route exists.

**Constraints:** `1 <= n <= 100`, `0 <= len(flights) <= n·(n-1)/2`, `1 <= price <= 10^4`, no duplicate
flights, `0 <= k < n`, `src != dst`.

**Example 1:** `n = 4, flights = [[0,1,100],[1,2,100],[2,0,100],[1,3,600],[2,3,200]], src = 0, dst = 3, k = 1` → `700`
(0 → 1 → 3; the cheaper 0 → 1 → 2 → 3 = 400 needs two stops)

**Example 2:** `n = 3, flights = [[0,1,100],[1,2,100],[0,2,500]], src = 0, dst = 2, k = 1` → `200`

**Example 3:** same flights, `k = 0` → `500`
""",
    starter='''class Solution:
    def findCheapestPrice(self, n: int, flights: List[List[int]], src: int, dst: int, k: int) -> int:
        pass
''',
    solution='''class Solution:
    def findCheapestPrice(self, n, flights, src, dst, k):
        INF = float("inf")
        dist = [INF] * n
        dist[src] = 0
        for _ in range(k + 1):               # allow one more flight per round
            nxt = dist[:]                    # read from last round, write to the copy
            for u, v, w in flights:
                if dist[u] + w < nxt[v]:
                    nxt[v] = dist[u] + w
            if nxt == dist:
                break
            dist = nxt
        return dist[dst] if dist[dst] < INF else -1
''',
    tests=[
        [4, [[0, 1, 100], [1, 2, 100], [2, 0, 100], [1, 3, 600], [2, 3, 200]], 0, 3, 1],
        [3, [[0, 1, 100], [1, 2, 100], [0, 2, 500]], 0, 2, 1],
        [3, [[0, 1, 100], [1, 2, 100], [0, 2, 500]], 0, 2, 0],
        [2, [], 0, 1, 0],
        [2, [[0, 1, 7]], 1, 0, 1],
        [4, [[0, 1, 1], [0, 2, 5], [1, 2, 1], [2, 3, 1]], 0, 3, 1],
        [5, [[0, 1, 5], [1, 2, 5], [0, 3, 2], [3, 1, 2], [1, 4, 1], [4, 2, 1]], 0, 2, 2],
        [5, [[0, 1, 1], [1, 2, 1], [2, 3, 1], [3, 4, 1]], 0, 4, 2],
        [5, [[0, 1, 1], [1, 2, 1], [2, 3, 1], [3, 4, 1]], 0, 4, 3],
        [4, [[0, 1, 1], [1, 2, 1], [2, 3, 1], [0, 3, 10]], 0, 3, 99 % 4],
        _flights(_R, 20, 100, 100, 2),
        _flights(_R, 100, 4950, 10000, 3),
        _flights(_R, 100, 2000, 10000, 10),
        _flights(_R, 100, 400, 50, 99),
        [100, [[i, i + 1, 1] for i in range(99)] + [[0, 99, 5000]], 0, 99, 97],
        [100, [[i, i + 1, 1] for i in range(99)] + [[0, 99, 5000]], 0, 99, 98],
    ],
    examples=3,
    wrong_solutions=[
        '''import heapq
class Solution:
    def findCheapestPrice(self, n, flights, src, dst, k):
        adj = [[] for _ in range(n)]
        for u, v, w in flights: adj[u].append((v, w))
        seen = set(); heap = [(0, src, 0)]
        while heap:
            d, u, used = heapq.heappop(heap)
            if u == dst: return d
            if u in seen or used > k: continue
            seen.add(u)
            for v, w in adj[u]: heapq.heappush(heap, (d + w, v, used + 1))
        return -1
''',
        '''class Solution:
    def findCheapestPrice(self, n, flights, src, dst, k):
        INF = float("inf"); dist = [INF] * n; dist[src] = 0
        for _ in range(k + 1):
            for u, v, w in flights:
                if dist[u] + w < dist[v]: dist[v] = dist[u] + w
        return dist[dst] if dist[dst] < INF else -1
''',
        '''class Solution:
    def findCheapestPrice(self, n, flights, src, dst, k):
        INF = float("inf"); dist = [INF] * n; dist[src] = 0
        for _ in range(k):
            nxt = dist[:]
            for u, v, w in flights:
                if dist[u] + w < nxt[v]: nxt[v] = dist[u] + w
            dist = nxt
        return dist[dst] if dist[dst] < INF else -1
''',
    ],
    guide=dict(
        prereqs="Bellman-Ford and its 'paths with at most i edges' invariant (lesson *Shortest paths: Dijkstra and Bellman-Ford*).",
        intuition=r"""
Bellman-Ford has a built-in notion of hop count: after round `i`, `dist[v]` is the cheapest price
using **at most `i` flights**. So run exactly `k + 1` rounds. The one subtlety: within a round you
must read prices from the *previous* round only (use a copy), otherwise a single round could chain
several flights together and break the hop limit.
""",
        hints=[
            "Plain Dijkstra finalises a city at its cheapest price — but the cheapest way there might use too many stops. What state is missing?",
            "Which shortest-path algorithm proceeds in rounds, where round i allows paths of at most i edges?",
            "Bellman-Ford for k + 1 rounds, relaxing from a snapshot: nxt = dist[:]; nxt[v] = min(nxt[v], dist[u] + w).",
        ],
        brute_force="DFS over all routes with at most k + 1 flights: O(branching^(k+1)) — exponential. BFS level-by-level with a best-price-per-city table is essentially the Bellman-Ford solution.",
        approach=r"""
1. `dist[src] = 0`, others ∞.
2. Repeat `k + 1` times: `nxt = dist[:]`; for each flight `(u, v, w)`: `nxt[v] = min(nxt[v], dist[u] + w)`; then `dist = nxt`.
3. Return `dist[dst]` or −1.

**Dry run** Example 1 (k = 1 → 2 rounds):

| round | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| start | 0 | ∞ | ∞ | ∞ |
| 1 | 0 | 100 | ∞ | ∞ |
| 2 | 0 | 100 | 200 | 700 |

City 3 = 700 (via 1). The 400 route would appear in round 3, which we never run.

**Dijkstra variant:** state `(cost, city, flights_used)`; allow revisiting a city if you arrive with fewer flights used than any previous visit.
""",
        complexity="O((k + 1) · E) time, O(n) space.",
        pitfalls=r"""
- Relaxing in place (wrong solution #2): `0→1→2→3` gets chained in one round, returning 400 for Example 1.
- Dijkstra with a plain visited set (wrong solution #1): it locks in the cheapest arrival even if it used too many stops.
- `k` stops means `k + 1` flights (wrong solution #3 runs one round too few).
""",
        follow_up="This is the DP `best[i][v] = min(best[i-1][v], min over (u,v,w) of best[i-1][u] + w)`. Related: *Network Delay Time* (no hop limit), *Minimum Cost to Reach Destination in Time*.",
    ),
),
]
