import random as _r

_r.seed(67)


def _dag(n, m, seed):
    rnd = _r.Random(seed)
    perm = list(range(n))
    rnd.shuffle(perm)
    edges = set()
    while len(edges) < m:
        a, b = rnd.sample(range(n), 2)
        if a > b:
            a, b = b, a
        edges.add((perm[a], perm[b]))
    return [list(e) for e in sorted(edges)]


def _wgraph(n, m, seed, maxw=20, directed=True):
    rnd = _r.Random(seed)
    edges = []
    for _ in range(m):
        a, b = rnd.randrange(n), rnd.randrange(n)
        edges.append([a, b, rnd.randint(0 if directed else 1, maxw)])
    return edges


def _connected(n, extra, seed, maxw=50):
    rnd = _r.Random(seed)
    edges = [[rnd.randrange(i), i, rnd.randint(1, maxw)] for i in range(1, n)]
    for _ in range(extra):
        a, b = rnd.sample(range(n), 2)
        edges.append([a, b, rnd.randint(1, maxw)])
    rnd.shuffle(edges)
    return edges


def _uf_ops(n, k, seed):
    rnd = _r.Random(seed)
    ops, args = ["UnionFind"], [[n]]
    for _ in range(k):
        x = rnd.random()
        a, b = rnd.randrange(n), rnd.randrange(n)
        if x < 0.5:
            ops.append("union"); args.append([a, b])
        elif x < 0.8:
            ops.append("connected"); args.append([a, b])
        elif x < 0.9:
            ops.append("size_of"); args.append([a])
        else:
            ops.append("count"); args.append([])
    return [ops, args]


PROBLEMS = [
dict(
    id="dsaf-topological-order",
    title="Topological Ordering of a DAG",
    difficulty="Medium",
    pattern="Graph Algorithms",
    entry="topological_order",
    checker='''def check(args, got, expected):
    n, edges = args
    if not isinstance(got, list):
        return False
    if expected == [] and n > 0:
        return got == []
    if sorted(got) != list(range(n)):
        return False
    pos = {v: i for i, v in enumerate(got)}
    return all(pos[u] < pos[v] for u, v in edges)
''',
    description=r"""
A directed graph has vertices `0 .. n-1` and directed edges `[u, v]` meaning "u must come before v".

Return **any** topological ordering of the vertices — a list containing every vertex exactly once
such that for every edge `[u, v]`, `u` appears before `v` (Goodrich ch. 14.5). If the graph contains
a directed cycle, no such ordering exists: return `[]`.

Any valid ordering is accepted. Run in $O(n + m)$.

**Example:** `n = 4, edges = [[0,1],[0,2],[1,3],[2,3]]` → `[0, 1, 2, 3]` or `[0, 2, 1, 3]`

**Example:** `n = 3, edges = [[0,1],[1,2],[2,0]]` → `[]`
""",
    starter='''def topological_order(n, edges):
    pass
''',
    solution='''def topological_order(n, edges):
    adj = [[] for _ in range(n)]
    incount = [0] * n
    for u, v in edges:
        adj[u].append(v)
        incount[v] += 1
    ready = [u for u in range(n) if incount[u] == 0]
    topo = []
    while ready:
        u = ready.pop()
        topo.append(u)
        for v in adj[u]:
            incount[v] -= 1
            if incount[v] == 0:
                ready.append(v)
    return topo if len(topo) == n else []
''',
    tests=[
        [4, [[0, 1], [0, 2], [1, 3], [2, 3]]],
        [3, [[0, 1], [1, 2], [2, 0]]],
        [1, []],
        [5, []],
        [2, [[1, 0]]],
        [2, [[0, 1], [1, 0]]],
        [6, [[5, 2], [5, 0], [4, 0], [4, 1], [2, 3], [3, 1]]],
        [5, [[0, 1], [1, 2], [2, 3], [3, 1], [3, 4]]],
        [4, [[0, 1], [0, 1], [1, 2]]],
        [3, [[0, 0]]],
        [7, [[6, 5], [5, 4], [4, 3], [3, 2], [2, 1], [1, 0]]],
        [40, _dag(40, 120, 1)],
        [300, _dag(300, 1500, 2)],
        [300, _dag(300, 1500, 3) + [[7, 7]]],
        [2000, [[i, i + 1] for i in range(1999)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def topological_order(n, edges):
    return list(range(n))
''',
        '''def topological_order(n, edges):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
    seen, post = set(), []
    for s in range(n):
        if s in seen:
            continue
        stack = [(s, 0)]
        seen.add(s)
        while stack:
            u, i = stack.pop()
            if i < len(adj[u]):
                stack.append((u, i + 1))
                v = adj[u][i]
                if v not in seen:
                    seen.add(v)
                    stack.append((v, 0))
            else:
                post.append(u)
    return post[::-1]
''',
        '''def topological_order(n, edges):
    incount = [0] * n
    for u, v in edges:
        incount[v] += 1
    return sorted(range(n), key=lambda v: incount[v])
''',
    ],
    guide=dict(
        prereqs="Lesson *DFS, BFS, transitive closure and DAGs* (section 4).",
        intuition="A vertex with no incoming edges has no prerequisites, so it can go first. Remove it; this may free other vertices. Repeat. If you get stuck with vertices left over, they lie on (or behind) a cycle.",
        hints=["Build adjacency lists and an in-degree count for every vertex.",
               "Keep a list (stack or queue) of vertices whose in-degree is currently 0.",
               "Pop one, append it to the answer, decrement the in-degree of its out-neighbours; return [] if fewer than n vertices were output."],
        brute_force="Repeatedly scan all vertices for one with no remaining incoming edges and delete it: O(n) per round, O(n^2 + nm) overall. Trying permutations is O(n!).",
        approach="""
Kahn's algorithm. Example edges 5→2, 5→0, 4→0, 4→1, 2→3, 3→1: in-degrees = [2,2,1,1,0,0]; ready = [4,5].
Pop 5 → frees 2; pop 2 → frees 3; pop 3; pop 4 → frees 0 and 1; ... one valid result is `[5,2,3,4,1,0]`.
""",
        complexity="O(n + m) time — each vertex enters `ready` once and each edge is processed once. O(n + m) space.",
        pitfalls="Not detecting cycles (the DFS-based second wrong solution returns an order even for cyclic graphs); a self-loop is a cycle; duplicate edges must each be counted in the in-degree (and each decremented); sorting by initial in-degree is not a topological order.",
        follow_up="Return the lexicographically smallest order (use a min-heap for `ready`); count the number of distinct orders; longest path in a DAG by relaxing in topological order.",
    ),
),
dict(
    id="dsaf-dijkstra",
    title="Dijkstra's Shortest Paths",
    difficulty="Medium",
    pattern="Graph Algorithms",
    entry="dijkstra",
    description=r"""
A **directed** graph has vertices `0 .. n-1` and edges `[u, v, w]` with **non-negative** integer
weights `w`. Return a list `dist` of length `n` where `dist[v]` is the length of a shortest path
from `src` to `v`, or `-1` if `v` is unreachable (Goodrich ch. 14.6).

Use Dijkstra's algorithm with a priority queue: $O((n + m)\log n)$. Parallel edges and self-loops
may occur.

**Example:** `n = 5, edges = [[0,1,8],[0,2,2],[2,3,1],[3,1,2],[1,4,5]], src = 0` → `[0, 5, 2, 3, 10]`

**Example:** `n = 3, edges = [[0,1,4]], src = 0` → `[0, 4, -1]`
""",
    starter='''import heapq


def dijkstra(n, edges, src):
    pass
''',
    solution='''import heapq


def dijkstra(n, edges, src):
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
    INF = float("inf")
    dist = [INF] * n
    dist[src] = 0
    done = [False] * n
    heap = [(0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if done[u]:
            continue
        done[u] = True
        for v, w in adj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return [d if d != INF else -1 for d in dist]
''',
    tests=[
        [5, [[0, 1, 8], [0, 2, 2], [2, 3, 1], [3, 1, 2], [1, 4, 5]], 0],
        [3, [[0, 1, 4]], 0],
        [1, [], 0],
        [2, [[1, 0, 3]], 0],
        [2, [[0, 1, 7], [0, 1, 3], [0, 0, 1]], 0],
        [4, [[0, 1, 0], [1, 2, 0], [2, 3, 0]], 0],
        [4, [[0, 1, 1], [1, 2, 1], [2, 3, 1], [0, 3, 10]], 0],
        [4, [[0, 1, 1], [1, 2, 1], [2, 3, 1], [0, 3, 10]], 2],
        [6, [[0, 1, 7], [0, 2, 9], [0, 5, 14], [1, 2, 10], [1, 3, 15], [2, 3, 11], [2, 5, 2], [3, 4, 6], [5, 4, 9]], 0],
        [5, [[0, 1, 2], [0, 2, 2], [1, 3, 2], [2, 3, 1], [3, 4, 1], [1, 4, 4]], 0],
        [30, _wgraph(30, 90, 1), 0],
        [200, _wgraph(200, 900, 2), 17],
        [1500, _wgraph(1500, 6000, 3, maxw=1000), 3],
    ],
    examples=2,
    wrong_solutions=[
        '''from collections import deque
def dijkstra(n, edges, src):
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
    dist = [-1] * n
    dist[src] = 0
    q = deque([src])
    while q:
        u = q.popleft()
        for v, w in adj[u]:
            if dist[v] == -1:
                dist[v] = dist[u] + w
                q.append(v)
    return dist
''',
        '''import heapq
def dijkstra(n, edges, src):
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
    INF = float("inf")
    dist = [INF] * n
    dist[src] = 0
    seen = [False] * n
    seen[src] = True
    heap = [(0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        for v, w in adj[u]:
            if not seen[v]:
                seen[v] = True
                dist[v] = d + w
                heapq.heappush(heap, (dist[v], v))
    return [d if d != INF else -1 for d in dist]
''',
        '''import heapq
def dijkstra(n, edges, src):
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w)); adj[v].append((u, w))
    INF = float("inf")
    dist = [INF] * n
    dist[src] = 0
    heap = [(0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in adj[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                heapq.heappush(heap, (d + w, v))
    return [d if d != INF else -1 for d in dist]
''',
    ],
    guide=dict(
        prereqs="Lesson *Weighted graphs and Dijkstra's algorithm*; heaps.",
        intuition="Grow a cloud of finished vertices outward from the source, always finishing the closest unfinished vertex next. Because weights are non-negative, nothing discovered later can undercut it.",
        hints=["Build adjacency lists of (neighbour, weight).",
               "Heap of (distance, vertex) starting with (0, src); pop the smallest; skip it if that vertex is already finished.",
               "Relax each outgoing edge: if d + w < dist[v], update and push. Finalise on POP, not on push."],
        brute_force="Bellman-Ford relaxes every edge n - 1 times: O(nm). BFS (first wrong solution) only counts edges, ignoring weights.",
        approach="""
Trace of example 1 from 0: pop (0,0) → dist[1]=8, dist[2]=2. Pop (2,2) → dist[3]=3. Pop (3,3) → dist[1]=5. Pop (5,1) → dist[4]=10. Pop (8,1): stale, skip. Pop (10,4). Result [0,5,2,3,10].
""",
        complexity="O((n + m) log n) time with a binary heap and lazy deletion (the heap holds at most m entries); O(n + m) space.",
        pitfalls="Marking a vertex visited when first pushed (second wrong solution) freezes a non-optimal distance; treating the graph as undirected (third); using 0 or -1 as 'infinity' during the computation; forgetting unreachable vertices.",
        follow_up="Return the actual path with a parent array; stop early for a single target; handle negative edges with Bellman-Ford.",
    ),
),
dict(
    id="dsaf-mst-weight",
    title="Minimum Spanning Tree Weight",
    difficulty="Medium",
    pattern="Graph Algorithms",
    entry="mst_weight",
    description=r"""
An **undirected** weighted graph has vertices `0 .. n-1` and edges `[u, v, w]`. Return the total
weight of a **minimum spanning tree**, or `-1` if the graph is not connected (Goodrich ch. 14.7).

Use Kruskal's algorithm (sort edges + union-find) or Prim-Jarník (priority queue). Weights may be
negative or zero; parallel edges and self-loops may occur. `n >= 1`.

**Example:** `n = 4, edges = [[0,1,1],[1,2,2],[2,3,3],[3,0,4],[0,2,5]]` → `6`

**Example:** `n = 3, edges = [[0,1,5]]` → `-1`
""",
    starter='''def mst_weight(n, edges):
    pass
''',
    solution='''def mst_weight(n, edges):
    parent = list(range(n))
    size = [1] * n

    def find(p):
        root = p
        while parent[root] != root:
            root = parent[root]
        while parent[p] != root:
            parent[p], p = root, parent[p]
        return root

    total, used = 0, 0
    for w, u, v in sorted((w, u, v) for u, v, w in edges):
        a, b = find(u), find(v)
        if a != b:
            if size[a] < size[b]:
                a, b = b, a
            parent[b] = a
            size[a] += size[b]
            total += w
            used += 1
            if used == n - 1:
                break
    return total if used == n - 1 else -1
''',
    tests=[
        [4, [[0, 1, 1], [1, 2, 2], [2, 3, 3], [3, 0, 4], [0, 2, 5]]],
        [3, [[0, 1, 5]]],
        [1, []],
        [2, [[0, 1, 7]]],
        [2, [[0, 1, 7], [0, 1, 3], [1, 1, 0]]],
        [3, [[0, 1, -2], [1, 2, -3], [0, 2, 4]]],
        [4, [[0, 1, 1], [2, 3, 1]]],
        [9, [[0, 1, 4], [0, 7, 8], [1, 2, 8], [1, 7, 11], [2, 3, 7], [2, 5, 4], [2, 8, 2], [3, 4, 9], [3, 5, 14],
             [4, 5, 10], [5, 6, 2], [6, 7, 1], [6, 8, 6], [7, 8, 7]]],
        [5, [[0, 1, 2], [0, 2, 2], [0, 3, 2], [0, 4, 2], [1, 2, 2], [3, 4, 2]]],
        [4, [[0, 1, 1], [0, 2, 1], [0, 3, 10], [1, 3, 2], [2, 3, 2]]],
        [50, _connected(50, 150, 1)],
        [400, _connected(400, 2000, 2)],
        [400, _connected(399, 2000, 3)],
        [2000, _connected(2000, 5000, 4, maxw=1000)],
    ],
    examples=2,
    wrong_solutions=[
        '''import heapq
def mst_weight(n, edges):
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w)); adj[v].append((u, w))
    INF = float("inf")
    dist = [INF] * n; dist[0] = 0
    par_w = [0] * n
    done = [False] * n
    heap = [(0, 0)]
    while heap:
        d, u = heapq.heappop(heap)
        if done[u]: continue
        done[u] = True
        for v, w in adj[u]:
            if not done[v] and d + w < dist[v]:
                dist[v] = d + w; par_w[v] = w
                heapq.heappush(heap, (d + w, v))
    return sum(par_w) if all(done) else -1
''',
        '''def mst_weight(n, edges):
    total, seen = 0, {0}
    for u, v, w in sorted(edges, key=lambda e: e[2]):
        if (u in seen) != (v in seen):
            seen.add(u); seen.add(v)
            total += w
    return total if len(seen) == n else -1
''',
        '''def mst_weight(n, edges):
    return sum(sorted(w for _, _, w in edges)[:n - 1]) if len(edges) >= n - 1 else -1
''',
    ],
    guide=dict(
        prereqs="Lesson *Minimum spanning trees and union-find*.",
        intuition="Cut property: the cheapest edge leaving any group of vertices is safe to take. Kruskal applies it globally — scan edges from cheapest to most expensive and keep an edge whenever it joins two different components.",
        hints=["Sort edges by weight.",
               "Union-find: find(u) != find(v) means the edge connects two components — accept it and union them.",
               "Count accepted edges; you need exactly n - 1, otherwise the graph is disconnected."],
        brute_force="Enumerate all spanning trees (exponentially many), or check 'does this edge create a cycle?' with a DFS per edge: O(nm).",
        approach="""
Example 1: sorted edges (0,1,1), (1,2,2), (2,3,3), (3,0,4), (0,2,5). Accept 1, 2, 3 → three edges = n - 1 → total 6; the remaining edges would close cycles.

For the lesson's 9-vertex graph (test 8) the answer is 37.
""",
        complexity="O(m log m) for sorting plus near-linear union-find: O(m log n) overall. Space O(n + m).",
        pitfalls="Using Dijkstra's relaxation in Prim (first wrong solution builds a shortest-path tree); a single pass 'grow from vertex 0 over sorted edges' misses edges that become useful later (second); summing the n - 1 cheapest edges ignores cycles (third); self-loops are never useful; negative weights are fine.",
        follow_up="Return the edges; minimum spanning forest for disconnected graphs; second-best MST; maximum spanning tree (negate weights).",
    ),
),
dict(
    id="dsaf-union-find",
    title="Union-Find with Path Compression",
    difficulty="Medium",
    pattern="Graph Algorithms",
    kind="class",
    entry="UnionFind",
    description=r"""
Implement the disjoint-set (**union-find**) structure of Goodrich ch. 14.7.3 for elements
`0 .. n-1`, each initially in its own group.

- `UnionFind(n)`
- `union(a, b)` → merge the groups of `a` and `b`; return `True` if they were in different groups
  (a merge happened), `False` otherwise.
- `connected(a, b)` → `True` iff `a` and `b` are in the same group.
- `size_of(a)` → the number of elements in `a`'s group.
- `count()` → the current number of groups.

Use the tree-based representation with **union-by-size** and **path compression** so that
operations run in near-constant amortised time. (Leaders are an implementation detail and are not
exposed.)

**Example:** `["UnionFind","union","union","connected","connected","size_of","count","union","count"]`,
`[[5],[0,1],[1,2],[0,2],[0,3],[1],[],[2,0],[]]` → `[null,true,true,true,false,3,3,false,3]`
""",
    starter='''class UnionFind:
    def __init__(self, n):
        self._parent = list(range(n))
        self._size = [1] * n
        self._count = n

    def _find(self, p):
        pass

    def union(self, a, b):
        pass

    def connected(self, a, b):
        pass

    def size_of(self, a):
        pass

    def count(self):
        pass
''',
    solution='''class UnionFind:
    def __init__(self, n):
        self._parent = list(range(n))
        self._size = [1] * n
        self._count = n

    def _find(self, p):
        root = p
        while self._parent[root] != root:
            root = self._parent[root]
        while self._parent[p] != root:
            self._parent[p], p = root, self._parent[p]
        return root

    def union(self, a, b):
        ra, rb = self._find(a), self._find(b)
        if ra == rb:
            return False
        if self._size[ra] < self._size[rb]:
            ra, rb = rb, ra
        self._parent[rb] = ra
        self._size[ra] += self._size[rb]
        self._count -= 1
        return True

    def connected(self, a, b):
        return self._find(a) == self._find(b)

    def size_of(self, a):
        return self._size[self._find(a)]

    def count(self):
        return self._count
''',
    tests=[
        [["UnionFind", "union", "union", "connected", "connected", "size_of", "count", "union", "count"],
         [[5], [0, 1], [1, 2], [0, 2], [0, 3], [1], [], [2, 0], []]],
        [["UnionFind", "count", "connected", "size_of", "union", "count"], [[1], [], [0, 0], [0], [0, 0], []]],
        [["UnionFind", "union", "union", "union", "connected", "connected", "size_of", "size_of", "count"],
         [[6], [0, 1], [2, 3], [4, 5], [0, 3], [4, 5], [2], [1], []]],
        [["UnionFind", "union", "union", "union", "union", "connected", "size_of", "count"],
         [[6], [0, 1], [2, 3], [1, 3], [3, 0], [0, 2], [3], []]],
        [["UnionFind"] + ["union"] * 7 + ["count", "size_of", "connected", "union"],
         [[8]] + [[i, i + 1] for i in range(7)] + [[], [0], [0, 7], [7, 0]]],
        [["UnionFind"] + ["union"] * 4 + ["connected"] * 4 + ["count"],
         [[10]] + [[0, 9], [1, 8], [9, 8], [2, 7]] + [[0, 1], [0, 2], [7, 2], [3, 3]] + [[]]],
        _uf_ops(20, 80, 1),
        _uf_ops(200, 600, 2),
        _uf_ops(3000, 6000, 3),
        [["UnionFind"] + ["union"] * 4999 + ["connected", "size_of", "count"],
         [[5000]] + [[i, i + 1] for i in range(4999)] + [[0, 4999], [2500], []]],
    ],
    examples=2,
    wrong_solutions=[
        '''class UnionFind:
    def __init__(self, n):
        self._parent = list(range(n))
        self._size = [1] * n
        self._count = n
    def _find(self, p):
        while self._parent[p] != p:
            p = self._parent[p]
        return p
    def union(self, a, b):
        if self._find(a) == self._find(b):
            return False
        self._parent[a] = b
        self._size[b] += self._size[a]
        self._count -= 1
        return True
    def connected(self, a, b):
        return self._find(a) == self._find(b)
    def size_of(self, a):
        return self._size[self._find(a)]
    def count(self):
        return self._count
''',
        '''class UnionFind:
    def __init__(self, n):
        self._parent = list(range(n))
        self._size = [1] * n
        self._count = n
    def _find(self, p):
        while self._parent[p] != p:
            p = self._parent[p]
        return p
    def union(self, a, b):
        ra, rb = self._find(a), self._find(b)
        self._parent[rb] = ra
        self._size[ra] += self._size[rb]
        self._count -= 1
        return ra != rb
    def connected(self, a, b):
        return self._find(a) == self._find(b)
    def size_of(self, a):
        return self._size[self._find(a)]
    def count(self):
        return self._count
''',
    ],
    guide=dict(
        prereqs="Lesson *Minimum spanning trees and union-find* (section 5).",
        intuition="Each group is a tree of parent pointers whose root is the leader. Two elements are together iff they have the same root. Keep trees shallow: hang the smaller tree under the larger, and flatten every path you walk.",
        hints=["_find: walk to the root, then walk again re-pointing every node on the path to the root.",
               "union: find BOTH roots first; if equal return False; otherwise attach the smaller root under the larger and add the sizes.",
               "Sizes are only meaningful at roots."],
        brute_force="Store a group id per element and relabel a whole group on union: O(n) per union ('quick-find').",
        approach="""
Trace: union(0,1) → parent[1]=0, size[0]=2. union(1,2): roots 0 and 2 → parent[2]=0, size[0]=3. connected(0,2): both find 0 → True. union(2,0): same root → False; count stays 3 (groups {0,1,2}, {3}, {4}).
""",
        complexity="O(log* n) amortised per operation (effectively constant) with both heuristics; O(n) space.",
        pitfalls="Linking the elements instead of their roots (first wrong solution: `parent[a] = b` detaches a from its old tree's root and breaks sizes); updating counts/sizes even when the roots are already equal (second); recursive find overflowing the stack on a 5000-long chain.",
        follow_up="Use it for Kruskal, for counting connected components as edges arrive, and for detecting the first edge that closes a cycle.",
    ),
),
]
