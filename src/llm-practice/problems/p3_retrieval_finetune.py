import numpy as _np

_rng = _np.random.default_rng(2025)


def _r(*shape, scale=1.0):
    return _np.round(_rng.standard_normal(shape) * scale, 3).tolist()


def _knn_graph(X, m):
    X = _np.asarray(X)
    d = ((X[:, None, :] - X[None, :, :]) ** 2).sum(-1)
    _np.fill_diagonal(d, _np.inf)
    return _np.argsort(d, axis=1, kind="stable")[:, :m].tolist()


_GV = _r(40, 3)
_GN = _knn_graph(_GV, 4)
_GV2 = _r(120, 4)
_GN2 = _knn_graph(_GV2, 5)

# line graph 0-1-2-3-4-5 on the x axis, plus an isolated node 6 that is the true nearest to some queries
_LINE_V = [[0.0], [1.0], [2.0], [3.0], [4.0], [5.0], [10.0]]
_LINE_N = [[1], [0, 2], [1, 3], [2, 4], [3, 5], [4], []]
# a graph with a local minimum: from entry 0 the greedy path gets stuck at node 2 unless ef is large enough
_LM_V = [[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [2.0, 3.0], [3.0, 3.0], [4.0, 0.2], [0.0, 3.0]]
_LM_N = [[1, 6], [0, 2], [1], [6, 4], [3, 5], [4], [0, 3]]

_IVF_V = [[0, 0], [1, 0], [0, 1], [10, 10], [11, 10], [10, 11], [5, 5], [20, 0], [21, 1], [4, 4]]
_IVF_C = [[0, 0], [10, 10], [20, 0]]
_IVF_A = [0, 0, 0, 1, 1, 1, 1, 2, 2, 0]
_IVF_V2 = _r(60, 3, scale=3)
_IVF_C2 = _r(6, 3, scale=3)
_IVF_A2 = [int(_np.argmin(((_np.asarray(_IVF_C2) - _np.asarray(v)) ** 2).sum(1))) for v in _IVF_V2]

_LLAMA = []
for _i in range(2):
    _p = f"model.layers.{_i}."
    _LLAMA += [[_p + "self_attn.q_proj", 4096, 4096], [_p + "self_attn.k_proj", 1024, 4096],
               [_p + "self_attn.v_proj", 1024, 4096], [_p + "self_attn.o_proj", 4096, 4096],
               [_p + "mlp.gate_proj", 14336, 4096], [_p + "mlp.up_proj", 14336, 4096],
               [_p + "mlp.down_proj", 4096, 14336]]
_LLAMA += [["lm_head", 128256, 4096]]

PROBLEMS = [
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-cosine-topk",
    title="Cosine Similarity Top-k Search",
    difficulty="Easy",
    pattern="Vector Search",
    entry="cosine_topk",
    description=r"""
Implement exact (brute-force) semantic search.

Given a `query` vector, a list of document vectors `docs` and an integer `k`, return the **indices** of
the `k` documents with the highest cosine similarity to the query, best first.

$$\cos(a, b) = \frac{a \cdot b}{\|a\|\,\|b\|}$$

- A vector with zero norm has similarity `0` with everything.
- Break ties by the **lower index**.
- If `k` exceeds the number of documents, return all of them (ranked). `k = 0` returns `[]`.

**Example:** `query = [1, 0]`, `docs = [[0, 1], [2, 0], [1, 1], [-1, 0]]`, `k = 2`

Similarities are `[0, 1, 0.707, -1]`, so the answer is `[1, 2]`. Note that document 1 wins although a
raw dot product would also rank it first here; cosine ignores vector length.
""",
    starter=r'''import numpy as np

def cosine_topk(query, docs, k):
    pass
''',
    solution=r'''import numpy as np

def cosine_topk(query, docs, k):
    if not docs or k <= 0:
        return []
    q = np.asarray(query, dtype=float)
    D = np.asarray(docs, dtype=float)
    qn = np.linalg.norm(q)
    dn = np.linalg.norm(D, axis=1)
    denom = dn * qn
    dots = D @ q
    sims = np.where(denom > 0, dots / np.where(denom > 0, denom, 1.0), 0.0)
    order = sorted(range(len(docs)), key=lambda i: (-sims[i], i))
    return order[:k]
''',
    tests=[
        [[1, 0], [[0, 1], [2, 0], [1, 1], [-1, 0]], 2],
        [[1, 1], [[10, 0], [1, 1], [0.1, 0.1], [0, 3]], 4],
        [[1, 0], [[5, 0], [0, 0], [-1, 0]], 3],
        [[0, 0], [[1, 2], [3, 4], [5, 6]], 2],
        [[1, 2, 3], [], 3],
        [[1, 2, 3], [[1, 2, 3]], 0],
        [[1, 0, 0], [[0, 1, 0], [0, 0, 1], [0, 1, 1]], 5],
        [_r(8), _r(30, 8), 5],
        [_r(16), _r(200, 16), 10],
        [[3, 4], [[100, 0], [3, 4], [0, 0.001], [30, 40.5]], 2],
        [[1, 0], [[1, 0], [1, 0], [0, 1], [1, 0]], 3],
        [[-1, -1], [[1, 1], [-2, -2.1], [0, -1]], 3],
    ],
    examples=2,
    wrong_solutions=[
        r'''import numpy as np
def cosine_topk(query, docs, k):
    if not docs or k <= 0:
        return []
    s = np.asarray(docs, dtype=float) @ np.asarray(query, dtype=float)
    return sorted(range(len(docs)), key=lambda i: (-s[i], i))[:k]
''',
        r'''import numpy as np
def cosine_topk(query, docs, k):
    if not docs or k <= 0:
        return []
    q = np.asarray(query, dtype=float); D = np.asarray(docs, dtype=float)
    d = np.linalg.norm(D - q, axis=1)
    return sorted(range(len(docs)), key=lambda i: (d[i], i))[:k]
''',
        r'''import numpy as np
def cosine_topk(query, docs, k):
    if not docs or k <= 0:
        return []
    q = np.asarray(query, dtype=float); D = np.asarray(docs, dtype=float)
    den = np.linalg.norm(D, axis=1) * np.linalg.norm(q)
    s = np.where(den > 0, (D @ q) / np.where(den > 0, den, 1.0), 0.0)
    return sorted(range(len(docs)), key=lambda i: (s[i], i))[:k]
''',
    ],
    guide=dict(
        prereqs="Lesson *Embeddings and similarity*; vector norms and dot products.",
        intuition="Cosine similarity measures the angle between vectors and ignores their length. Normalise (or divide by the norms), take dot products with the query, and pick the largest.",
        hints=[
            "Compute all similarities at once: `(D @ q) / (norm(D, axis=1) * norm(q))`.",
            "Guard the division: where the denominator is 0 the similarity is defined as 0.",
            "For deterministic ties sort indices by the key `(-similarity, index)` and slice the first `k`.",
        ],
        brute_force="This *is* the brute-force (flat index) method: one pass over all documents, $O(Nd)$, then a sort. It is exact, and for up to roughly a million vectors it is often fast enough in production.",
        approach="1. Handle empty input and `k <= 0`.\n2. Vectorised dot products and norms.\n3. Similarity with zero-norm guard.\n4. Sort indices by `(-sim, idx)`; return the first `k`.\n\n**Dry run:** query `[1,0]`; docs `[0,1] -> 0`, `[2,0] -> 1`, `[1,1] -> 0.707`, `[-1,0] -> -1`. Top-2: `[1, 2]`.",
        complexity="$O(Nd)$ for similarities plus $O(N \\log N)$ for the sort (or $O(N + k \\log k)$ with `argpartition`); $O(N)$ space.",
        pitfalls="- Ranking by raw dot product: long vectors win unfairly.\n- Ranking by Euclidean distance on unnormalised vectors gives a different order.\n- Division by zero for zero vectors.\n- Sorting ascending, or non-deterministic tie order from `argsort` on negated scores.",
        follow_up="Pre-normalise the corpus once and use a plain dot product; use `np.argpartition` for $O(N)$ selection; batch many queries as a matrix product.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-ivf-search",
    title="IVF: Cluster-Then-Search",
    difficulty="Medium",
    pattern="Vector Search",
    entry="ivf_search",
    description=r"""
Implement the query side of an **inverted file (IVF)** index.

The index was built by assigning every vector to a k-means cell:

- `vectors`: list of `N` vectors
- `centroids`: list of `C` cell centroids
- `assignments`: `assignments[i]` is the cell id of `vectors[i]`

To search:

1. Find the `nprobe` centroids closest to `query` (squared Euclidean distance; ties: lower cell id). If
   `nprobe >= C`, probe every cell.
2. Collect the vectors assigned to those cells and rank them by squared Euclidean distance to the query
   (ties: lower vector index).
3. Return the indices of the `k` best (fewer if the probed cells hold fewer vectors).

**Example:** three cells around `(0,0)`, `(10,10)` and `(20,0)`. For `query = [6, 6]`, `nprobe = 1`,
only the `(10,10)` cell is searched, even if a vector in another cell (say `[4, 4]` assigned to cell 0)
is closer than some of the results: that is the approximation IVF makes. With `nprobe = 2` it would be
found.
""",
    starter=r'''import numpy as np

def ivf_search(vectors, centroids, assignments, query, nprobe, k):
    pass
''',
    solution=r'''import numpy as np

def ivf_search(vectors, centroids, assignments, query, nprobe, k):
    if not vectors or k <= 0 or nprobe <= 0:
        return []
    q = np.asarray(query, dtype=float)
    C = np.asarray(centroids, dtype=float)
    cd = ((C - q) ** 2).sum(axis=1)
    cells = set(sorted(range(len(centroids)), key=lambda c: (cd[c], c))[:nprobe])
    cand = [i for i, a in enumerate(assignments) if a in cells]
    if not cand:
        return []
    V = np.asarray(vectors, dtype=float)[cand]
    d = ((V - q) ** 2).sum(axis=1)
    order = sorted(range(len(cand)), key=lambda j: (d[j], cand[j]))
    return [cand[j] for j in order[:k]]
''',
    tests=[
        [_IVF_V, _IVF_C, _IVF_A, [6, 6], 1, 3],
        [_IVF_V, _IVF_C, _IVF_A, [6, 6], 2, 3],
        [_IVF_V, _IVF_C, _IVF_A, [0, 0], 1, 10],
        [_IVF_V, _IVF_C, _IVF_A, [19, 1], 1, 5],
        [_IVF_V, _IVF_C, _IVF_A, [10, 5], 3, 4],
        [_IVF_V, _IVF_C, _IVF_A, [10, 5], 99, 20],
        [_IVF_V, _IVF_C, _IVF_A, [5, 5], 1, 0],
        [[], [[0, 0]], [], [1, 1], 1, 3],
        [[[1, 1], [2, 2]], [[0, 0], [9, 9]], [0, 0], [9, 9], 1, 2],
        [_IVF_V2, _IVF_C2, _IVF_A2, _r(3, scale=3), 1, 5],
        [_IVF_V2, _IVF_C2, _IVF_A2, _r(3, scale=3), 2, 5],
        [_IVF_V2, _IVF_C2, _IVF_A2, _r(3, scale=3), 3, 8],
        [_IVF_V2, _IVF_C2, _IVF_A2, _r(3, scale=3), 6, 60],
        [[[0, 0], [0, 0], [1, 0], [-1, 0]], [[0, 0], [5, 5]], [0, 0, 0, 0], [0, 0], 1, 4],
    ],
    examples=2,
    wrong_solutions=[
        # ignores nprobe: exact search over everything
        r'''import numpy as np
def ivf_search(vectors, centroids, assignments, query, nprobe, k):
    if not vectors or k <= 0:
        return []
    d = ((np.asarray(vectors, dtype=float) - np.asarray(query, dtype=float)) ** 2).sum(1)
    return sorted(range(len(vectors)), key=lambda i: (d[i], i))[:k]
''',
        # always probes exactly one cell
        r'''import numpy as np
def ivf_search(vectors, centroids, assignments, query, nprobe, k):
    if not vectors or k <= 0 or nprobe <= 0:
        return []
    q = np.asarray(query, dtype=float)
    cd = ((np.asarray(centroids, dtype=float) - q) ** 2).sum(1)
    cell = int(np.argmin(cd))
    cand = [i for i, a in enumerate(assignments) if a == cell]
    d = {i: float(((np.asarray(vectors[i], dtype=float) - q) ** 2).sum()) for i in cand}
    return sorted(cand, key=lambda i: (d[i], i))[:k]
''',
        # returns candidates in index order instead of by distance
        r'''import numpy as np
def ivf_search(vectors, centroids, assignments, query, nprobe, k):
    if not vectors or k <= 0 or nprobe <= 0:
        return []
    q = np.asarray(query, dtype=float)
    cd = ((np.asarray(centroids, dtype=float) - q) ** 2).sum(1)
    cells = set(sorted(range(len(centroids)), key=lambda c: (cd[c], c))[:nprobe])
    return [i for i, a in enumerate(assignments) if a in cells][:k]
''',
    ],
    guide=dict(
        prereqs="Lesson *ANN indexes (HNSW, IVF, PQ) and vector databases*, section on IVF.",
        intuition="Instead of comparing the query with every vector, first compare it with a few hundred centroids, then search exhaustively only inside the closest cells. Vectors in unprobed cells are simply never seen, which is where the lost recall comes from.",
        hints=[
            "Rank centroids by squared distance with the key `(distance, cell_id)` and take the first `nprobe` into a set.",
            "Candidates are the indices `i` with `assignments[i]` in that set.",
            "Rank candidates by `(distance, index)` and return the first `k` original indices.",
        ],
        brute_force="Exact search over all `N` vectors: $O(Nd)$. IVF reduces this to about $O(Cd + \\frac{nprobe}{C} N d)$ when cells are balanced.",
        approach="1. Distances from the query to all centroids.\n2. Choose the `nprobe` nearest cells.\n3. Gather candidate indices.\n4. Exact distances for candidates, sort with tie-break, slice `k`.\n\n**Dry run** (example): query `[6,6]`: centroid distances are 72, 32, 232, so cell 1 is probed. Its vectors are 3, 4, 5, 6 with squared distances 32, 41, 41, 2. Result for `k = 3`: `[6, 3, 4]`. Vector 9 = `[4,4]` (distance 8) lives in cell 0 and is missed.",
        complexity="$O(Cd)$ to rank centroids plus $O(Md + M \\log M)$ for $M$ candidates.",
        pitfalls="- Ignoring `nprobe` (that is exact search, and gives *different* answers from a real IVF index).\n- Returning positions within the candidate list instead of original vector indices.\n- Not sorting candidates by distance.\n- Forgetting the cases `k = 0`, empty index and `nprobe` larger than the number of cells.",
        follow_up="Write the build side (k-means and assignment); measure recall@k versus `nprobe`; store residuals compressed with product quantisation (IVF-PQ).",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-greedy-graph-search",
    title="HNSW-Lite: Best-First Graph Search",
    difficulty="Hard",
    pattern="Vector Search",
    entry="graph_search",
    description=r"""
Implement the layer-0 search routine of HNSW (`SEARCH-LAYER` in the paper) on a given proximity graph.

Inputs: `vectors` (list of `N` vectors), `neighbors` (`neighbors[i]` = list of node ids linked from node
`i`), a `query` vector, an `entry` node id, the beam width `ef >= 1`, and `k`.

Use **squared Euclidean distance**. Algorithm:

1. `visited = {entry}`; `candidates` = min-heap containing `(dist(entry), entry)`; `results` = the best
   nodes found so far (at most `ef`), initially the entry.
2. Loop while `candidates` is not empty:
   - pop the closest candidate `(dc, c)` (ties: smaller id);
   - if `dc` is **greater** than the distance of the worst node in `results`, stop;
   - for each neighbour `n` of `c`, in listed order, that is not visited: mark it visited, compute
     `dn`; if `results` has fewer than `ef` nodes **or** `dn` is smaller than the worst distance in
     `results`, push `(dn, n)` to `candidates` and add it to `results`; if `results` now exceeds `ef`,
     evict its worst node (largest distance; ties: larger id).
3. Return the ids of the `k` closest nodes in `results`, sorted by `(distance, id)`.

Because the search only follows edges, it may miss the true nearest neighbour (for example an
unreachable node, or one hidden behind a local minimum when `ef` is small). That is expected.

**Example:** a path graph `0 - 1 - 2 - 3 - 4 - 5` with vectors `[0], [1], ..., [5]`, query `[3.2]`,
entry `0`, `ef = 2`, `k = 2` returns `[3, 4]`.
""",
    starter=r'''import heapq

def graph_search(vectors, neighbors, query, entry, ef, k):
    pass
''',
    solution=r'''import heapq

def graph_search(vectors, neighbors, query, entry, ef, k):
    def dist(i):
        return sum((a - b) ** 2 for a, b in zip(vectors[i], query))
    d0 = dist(entry)
    visited = {entry}
    candidates = [(d0, entry)]
    results = [(-d0, -entry)]          # max-heap: worst = largest distance, then largest id
    while candidates:
        dc, c = heapq.heappop(candidates)
        if dc > -results[0][0]:
            break
        for n in neighbors[c]:
            if n in visited:
                continue
            visited.add(n)
            dn = dist(n)
            if len(results) < ef or dn < -results[0][0]:
                heapq.heappush(candidates, (dn, n))
                heapq.heappush(results, (-dn, -n))
                if len(results) > ef:
                    heapq.heappop(results)
    ranked = sorted((-d, -i) for d, i in results)
    return [i for _, i in ranked[:k]]
''',
    tests=[
        [_LINE_V, _LINE_N, [3.2], 0, 2, 2],
        [_LINE_V, _LINE_N, [9.0], 0, 3, 1],
        [_LINE_V, _LINE_N, [9.0], 6, 3, 2],
        [_LM_V, _LM_N, [4.0, 0.0], 0, 1, 1],
        [_LM_V, _LM_N, [4.0, 0.0], 0, 4, 1],
        [_LM_V, _LM_N, [4.0, 0.0], 0, 4, 3],
        [_LINE_V, _LINE_N, [0.4], 5, 1, 1],
        [_LINE_V, _LINE_N, [2.5], 2, 4, 4],
        [[[1.0, 1.0]], [[]], [0.0, 0.0], 0, 5, 3],
        [_GV, _GN, _r(3), 0, 1, 1],
        [_GV, _GN, _r(3), 0, 5, 3],
        [_GV, _GN, _r(3), 17, 10, 5],
        [_GV2, _GN2, _r(4), 3, 8, 5],
        [_GV2, _GN2, _r(4), 99, 20, 10],
        [_GV2, _GN2, _r(4), 50, 2, 2],
    ],
    examples=2,
    wrong_solutions=[
        # brute force over all vectors (finds unreachable nodes, ignores the graph)
        r'''def graph_search(vectors, neighbors, query, entry, ef, k):
    d = [sum((a - b) ** 2 for a, b in zip(v, query)) for v in vectors]
    return sorted(range(len(vectors)), key=lambda i: (d[i], i))[:k]
''',
        # pure greedy walk (ignores ef)
        r'''def graph_search(vectors, neighbors, query, entry, ef, k):
    def dist(i):
        return sum((a - b) ** 2 for a, b in zip(vectors[i], query))
    cur, best = entry, dist(entry)
    improved = True
    while improved:
        improved = False
        for n in neighbors[cur]:
            dn = dist(n)
            if dn < best:
                cur, best, improved = n, dn, True
    return [cur][:k]
''',
        # full graph traversal (BFS over everything reachable), ignores the stopping rule and ef
        r'''def graph_search(vectors, neighbors, query, entry, ef, k):
    def dist(i):
        return sum((a - b) ** 2 for a, b in zip(vectors[i], query))
    seen, stack = {entry}, [entry]
    while stack:
        c = stack.pop()
        for n in neighbors[c]:
            if n not in seen:
                seen.add(n); stack.append(n)
    return sorted(seen, key=lambda i: (dist(i), i))[:k]
''',
    ],
    guide=dict(
        prereqs="Lesson *ANN indexes*, section on HNSW; `heapq`; best-first search.",
        intuition="Walk the graph towards the query, but instead of a single current node keep a beam of the `ef` best nodes seen. Always expand the closest unexpanded node; stop when even that one is worse than everything in the beam, because expanding it is unlikely to improve the beam.",
        hints=[
            "Use two heaps: a min-heap of candidates `(dist, id)` and a max-heap of results (store `(-dist, -id)` so the worst result is on top).",
            "Stop when the popped candidate's distance is greater than the worst result's distance.",
            "A neighbour enters both heaps if the beam is not full or it beats the worst result; pop the worst result when the beam exceeds `ef`.",
        ],
        brute_force="Compute the distance to every vector and sort: $O(Nd)$ and exact. Note it is **not** equivalent: it returns nodes the graph search cannot reach, so it fails the tests that include unreachable or hidden nodes.",
        approach="1. Initialise visited, candidates and results with the entry point.\n2. Pop the closest candidate; apply the stopping rule.\n3. Visit unvisited neighbours, pushing the promising ones and trimming the beam.\n4. Sort the beam by `(dist, id)` and return `k` ids.\n\n**Dry run** (path graph, query 3.2, entry 0, ef 2): results `{0}`; expand 0, add 1; expand 1, add 2 (evict 0); expand 2, add 3 (evict 1); expand 3, add 4 (evict 2); expand 4: node 5 (distance 3.24) is not better than the worst (0.64); next candidate... the heap is empty or worse, stop. Beam `{3, 4}`, sorted `[3, 4]`.",
        complexity="Roughly $O(ef \\cdot M \\cdot d + ef \\cdot M \\log ef)$ for graph degree $M$: independent of $N$ for a well-built graph, which is the whole point of HNSW.",
        pitfalls="- Marking nodes visited when popped instead of when first seen (distances get recomputed and duplicates enter the beam).\n- Using `>=` in the stopping rule (stops too early on ties).\n- Returning the true nearest neighbours by brute force.\n- Forgetting that `results` can hold fewer than `k` nodes.\n- Max-heap tie handling: evict the larger id among equal distances.",
        follow_up="Add the upper layers (greedy descent with `ef = 1` per layer); implement insertion with neighbour selection; plot recall@10 against `ef` on random data.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-chunk-overlap",
    title="Chunk Tokens with Overlap",
    difficulty="Easy",
    pattern="RAG",
    entry="chunk_tokens",
    description=r"""
Split a list of tokens into fixed-size chunks with overlap, the baseline RAG chunker.

- Each chunk has at most `size` tokens.
- Consecutive chunks share exactly `overlap` tokens: the window advances by `size - overlap`.
- The last chunk may be shorter. Stop as soon as a chunk reaches the end of the token list (do **not**
  emit an extra trailing chunk that only contains tokens already fully covered).
- If `size <= 0`, `overlap < 0` or `overlap >= size`, return `[]`. An empty token list gives `[]`.

**Example:** `tokens = [1,2,3,4,5,6,7,8,9,10]`, `size = 4`, `overlap = 1`

returns `[[1,2,3,4], [4,5,6,7], [7,8,9,10]]`.
""",
    starter=r'''def chunk_tokens(tokens, size, overlap):
    pass
''',
    solution=r'''def chunk_tokens(tokens, size, overlap):
    if size <= 0 or overlap < 0 or overlap >= size:
        return []
    chunks, start, step = [], 0, size - overlap
    while start < len(tokens):
        chunks.append(tokens[start:start + size])
        if start + size >= len(tokens):
            break
        start += step
    return chunks
''',
    tests=[
        [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 4, 1],
        [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5, 0],
        [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 4, 2],
        [[1, 2, 3], 10, 3],
        [[], 4, 1],
        [[1, 2, 3, 4, 5], 2, 2],
        [[1, 2, 3, 4, 5], 0, 0],
        [[1, 2, 3, 4, 5], 3, -1],
        [["a", "b", "c", "d", "e", "f", "g"], 3, 2],
        [list(range(11)), 4, 1],
        [[7], 1, 0],
        [list(range(1000)), 128, 16],
        [list(range(9)), 3, 0],
        [list(range(6)), 5, 4],
    ],
    examples=2,
    wrong_solutions=[
        r'''def chunk_tokens(tokens, size, overlap):
    if size <= 0 or overlap < 0 or overlap >= size:
        return []
    step = size - overlap
    return [tokens[i:i + size] for i in range(0, len(tokens), step)]
''',
        r'''def chunk_tokens(tokens, size, overlap):
    if size <= 0 or overlap < 0 or overlap >= size:
        return []
    return [tokens[i:i + size] for i in range(0, len(tokens), size)]
''',
        r'''def chunk_tokens(tokens, size, overlap):
    if size <= 0 or overlap < 0 or overlap >= size:
        return []
    chunks, start, step = [], 0, size - overlap
    while start + size <= len(tokens):
        chunks.append(tokens[start:start + size])
        start += step
    return chunks
''',
    ],
    guide=dict(
        prereqs="Lesson *Ingestion, parsing and chunking strategies*.",
        intuition="Slide a window of `size` tokens forward by `size - overlap` each time. The overlap gives content near a boundary a second chance to appear intact in one chunk.",
        hints=[
            "Validate parameters first; `overlap >= size` would make the step zero or negative (an infinite loop).",
            "Loop with `start`, append `tokens[start:start + size]`, advance by `size - overlap`.",
            "Break right after appending a chunk whose end `start + size` reaches or passes `len(tokens)`.",
        ],
        brute_force="A list comprehension over `range(0, n, step)` is nearly right but emits redundant tail chunks (e.g. for 10 tokens, size 4, overlap 2 it adds `[9, 10]` after `[7, 8, 9, 10]`).",
        approach="1. Guard invalid parameters.\n2. `step = size - overlap`, `start = 0`.\n3. Append the window; if it reached the end, stop; else advance.\n\n**Dry run** (10 tokens, size 4, overlap 1): starts 0, 3, 6. The window at 6 covers indices 6-9 and reaches the end, so we stop with three chunks.",
        complexity="$O(n \\cdot size / step)$ time and space: each token is copied into at most `ceil(size / step)` chunks.",
        pitfalls="- Infinite loop when `overlap >= size`.\n- A redundant final chunk that is a suffix of the previous one, which wastes index space and returns duplicate hits.\n- Dropping the short final chunk and losing the end of the document.\n- Counting characters or words while the embedding model's limit is in tokens.",
        follow_up="Return `(start, end)` offsets with each chunk for citations; snap boundaries to sentence ends; implement parent-child chunking.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-rrf",
    title="Reciprocal Rank Fusion",
    difficulty="Easy",
    pattern="RAG",
    entry="rrf",
    description=r"""
Fuse several ranked result lists (for example dense retrieval and BM25) with **Reciprocal Rank Fusion**.

Each ranking is a list of document ids (strings), best first. The fused score of a document is

$$\text{score}(d) = \sum_{\text{rankings containing } d} \frac{1}{k + \text{rank}(d)}$$

with ranks starting at **1**. If an id appears more than once in the same ranking, only its **first**
(best) position counts. Documents missing from a ranking get nothing from it.

Return the document ids sorted by score descending; break ties by id ascending. To make ties robust to
floating-point noise, round each score to 12 decimal places before sorting. If `top_n > 0`, return only
the first `top_n` ids.

**Example:** `rankings = [["a", "b", "c"], ["c", "a", "d"]]`, `k = 60`

`a = 1/61 + 1/62`, `c = 1/63 + 1/61`, `b = 1/62`, `d = 1/63`, so the result is `["a", "c", "b", "d"]`.
""",
    starter=r'''def rrf(rankings, k=60, top_n=0):
    pass
''',
    solution=r'''def rrf(rankings, k=60, top_n=0):
    score = {}
    for ranking in rankings:
        seen = set()
        for rank, doc in enumerate(ranking, start=1):
            if doc in seen:
                continue
            seen.add(doc)
            score[doc] = score.get(doc, 0.0) + 1.0 / (k + rank)
    order = sorted(score, key=lambda d: (-round(score[d], 12), d))
    return order[:top_n] if top_n > 0 else order
''',
    tests=[
        [[["a", "b", "c"], ["c", "a", "d"]], 60, 0],
        [[["d2", "d4", "d3", "d1"], ["d1", "d3", "d4"]], 60, 0],
        [[["a", "b"], ["b", "a"]], 60, 0],
        [[], 60, 0],
        [[[], ["x"]], 60, 0],
        [[["a", "a", "b"], ["b"]], 1, 0],
        [[["a", "b", "c", "d", "e"]], 60, 3],
        [[["x", "y", "z"], ["y", "z", "x"], ["z", "x", "y"]], 10, 0],
        [[["p", "q"], ["r", "s"], ["q", "r"]], 0, 2],
        [[["doc%d" % i for i in range(50)], ["doc%d" % i for i in range(49, -1, -1)]], 60, 5],
        [[["a", "b", "c"], ["c", "b", "a"], ["b"]], 2, 0],
        [[["m", "n", "m", "n", "o"], ["o", "o", "o"]], 5, 0],
        [[["a", "b"], ["c", "d"], ["e", "f"]], 60, 4],
    ],
    examples=2,
    wrong_solutions=[
        r'''def rrf(rankings, k=60, top_n=0):
    score = {}
    for ranking in rankings:
        seen = set()
        for rank, doc in enumerate(ranking):
            if doc in seen:
                continue
            seen.add(doc)
            score[doc] = score.get(doc, 0.0) + 1.0 / (k + rank) if k + rank else 1e9
    order = sorted(score, key=lambda d: (-round(score[d], 12), d))
    return order[:top_n] if top_n > 0 else order
''',
        r'''def rrf(rankings, k=60, top_n=0):
    score = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            score[doc] = score.get(doc, 0.0) + 1.0 / (k + rank)
    order = sorted(score, key=lambda d: (-round(score[d], 12), d))
    return order[:top_n] if top_n > 0 else order
''',
        r'''def rrf(rankings, k=60, top_n=0):
    score = {}
    for ranking in rankings:
        seen = set()
        for rank, doc in enumerate(ranking, start=1):
            if doc in seen:
                continue
            seen.add(doc)
            score[doc] = score.get(doc, 0.0) + 1.0 / (k + rank)
    order = sorted(score, key=lambda d: -round(score[d], 12))
    return order[:top_n] if top_n > 0 else order
''',
    ],
    guide=dict(
        prereqs="Lesson *Hybrid retrieval, fusion, reranking and grounded generation*.",
        intuition="Scores from different retrievers are not comparable, but ranks are. Give each document `1/(k + rank)` points per list and add them up: documents that several retrievers rank well float to the top, and `k` keeps a single first place from dominating.",
        hints=[
            "Use `enumerate(ranking, start=1)` so the best rank is 1.",
            "Track a per-ranking `seen` set to ignore repeated ids within one list.",
            "Sort ids with the key `(-round(score, 12), id)`, then apply `top_n` if positive.",
        ],
        brute_force="For each distinct document, scan every ranking for its position with `list.index`: $O(D \\cdot L)$. A single pass accumulating into a dict is $O(L)$ in the total list length.",
        approach="1. Accumulate `1/(k + rank)` per document, first occurrence per list only.\n2. Sort by rounded score descending, id ascending.\n3. Slice.\n\n**Dry run:** `a`: 1/61 + 1/62 = 0.03252; `c`: 1/63 + 1/61 = 0.03227; `b`: 1/62 = 0.01613; `d`: 1/63 = 0.01587. Order `a, c, b, d`.",
        complexity="$O(L + D \\log D)$ time for total list length $L$ and $D$ distinct documents; $O(D)$ space.",
        pitfalls="- Zero-based ranks (`1/(k + 0)`), which changes orderings and divides by zero when `k = 0`.\n- Counting duplicates inside one ranking twice.\n- Unstable tie order: always add the id as a secondary key.\n- Trying to average raw scores from different retrievers instead of ranks.",
        follow_up="Add per-retriever weights; fuse the results of multiple query rewrites; compare with min-max normalised score fusion on a labelled set.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-lora-params",
    title="LoRA Parameter Count",
    difficulty="Easy",
    pattern="Finetuning",
    entry="lora_stats",
    compare="float",
    description=r"""
Reproduce what `peft`'s `print_trainable_parameters()` reports for a LoRA configuration.

`layers` is a list of `[name, d_out, d_in]` describing every linear weight matrix in a model (biases are
ignored). `targets` is a list of name **suffixes** (like `target_modules` in `LoraConfig`): a layer gets
an adapter if its name ends with any of them. `r` is the LoRA rank.

A LoRA adapter on a `d_out x d_in` matrix adds $A \in \mathbb{R}^{r \times d_{in}}$ and
$B \in \mathbb{R}^{d_{out} \times r}$, that is $r\,(d_{in} + d_{out})$ trainable parameters.

Return a dict:

- `"trainable"`: total adapter parameters,
- `"total"`: base parameters (sum of `d_out * d_in` over **all** layers) **plus** the adapter parameters,
- `"percent"`: `100 * trainable / total` (use `0.0` if `total` is 0).

**Example:** `layers = [["attn.q_proj", 8, 8], ["attn.v_proj", 8, 8], ["mlp.fc", 32, 8]]`, `r = 2`,
`targets = ["q_proj", "v_proj"]`

Each targeted layer adds `2 * (8 + 8) = 32`, so `trainable = 64`; base = `64 + 64 + 256 = 384`;
`total = 448`; `percent = 14.2857...`.
""",
    starter=r'''def lora_stats(layers, r, targets):
    pass
''',
    solution=r'''def lora_stats(layers, r, targets):
    trainable = 0
    base = 0
    for name, d_out, d_in in layers:
        base += d_out * d_in
        if any(name.endswith(t) for t in targets):
            trainable += r * (d_in + d_out)
    total = base + trainable
    return {"trainable": trainable, "total": total, "percent": 100.0 * trainable / total if total else 0.0}
''',
    tests=[
        [[["attn.q_proj", 8, 8], ["attn.v_proj", 8, 8], ["mlp.fc", 32, 8]], 2, ["q_proj", "v_proj"]],
        [[["attn.q_proj", 8, 8], ["attn.v_proj", 8, 8], ["mlp.fc", 32, 8]], 2, []],
        [_LLAMA, 16, ["q_proj", "v_proj"]],
        [_LLAMA, 16, ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]],
        [_LLAMA, 64, ["proj"]],
        [[], 8, ["q_proj"]],
        [[["w", 100, 10]], 4, ["w"]],
        [[["w", 10, 100]], 4, ["w"]],
        [[["layer.q_proj", 16, 16], ["layer.q_proj_extra", 16, 16]], 1, ["q_proj"]],
        [[["a.dense", 768, 768], ["b.dense", 3072, 768], ["c.dense", 768, 3072], ["classifier", 2, 768]], 8, ["dense"]],
        [_LLAMA, 1, ["lm_head"]],
        [[["x", 5, 7], ["y", 7, 5]], 3, ["x", "y", "z"]],
    ],
    examples=2,
    wrong_solutions=[
        r'''def lora_stats(layers, r, targets):
    trainable = base = 0
    for name, d_out, d_in in layers:
        base += d_out * d_in
        if any(name.endswith(t) for t in targets):
            trainable += r * (d_in + d_out)
    return {"trainable": trainable, "total": base, "percent": 100.0 * trainable / base if base else 0.0}
''',
        r'''def lora_stats(layers, r, targets):
    trainable = base = 0
    for name, d_out, d_in in layers:
        base += d_out * d_in
        if any(t in name for t in targets):
            trainable += r * (d_in + d_out)
    total = base + trainable
    return {"trainable": trainable, "total": total, "percent": 100.0 * trainable / total if total else 0.0}
''',
        r'''def lora_stats(layers, r, targets):
    trainable = base = 0
    for name, d_out, d_in in layers:
        base += d_out * d_in
        if any(name.endswith(t) for t in targets):
            trainable += 2 * r * d_in
    total = base + trainable
    return {"trainable": trainable, "total": total, "percent": 100.0 * trainable / total if total else 0.0}
''',
    ],
    guide=dict(
        prereqs="Lesson *PEFT: LoRA, QLoRA and friends*.",
        intuition="LoRA replaces a full update of a $d_{out} \\times d_{in}$ matrix by two thin matrices. Their sizes are `r x d_in` and `d_out x r`, so the cost grows with the *sum* of the dimensions rather than the product.",
        hints=[
            "Base parameters are summed over every layer; adapters only over layers whose name ends with a target.",
            "Adapter size is `r * (d_in + d_out)`, not `r * d_in * d_out`.",
            "`peft` reports the percentage relative to all parameters *including* the adapters.",
        ],
        brute_force="No shortcut is needed: one pass over the layers, $O(L \\cdot |targets|)$.",
        approach="1. Loop over layers, adding `d_out * d_in` to the base.\n2. If the name matches a target suffix, add `r * (d_in + d_out)` to trainable.\n3. `total = base + trainable`, `percent = 100 * trainable / total`.\n\n**Dry run** (example): trainable 64, base 384, total 448, percent 14.29.",
        complexity="$O(L \\cdot T)$ for $L$ layers and $T$ target suffixes.",
        pitfalls="- Dividing by the base count instead of base plus adapters (differs from what `peft` prints).\n- Substring matching instead of suffix matching (`q_proj` would also match `q_proj_extra`).\n- Assuming square matrices: with GQA, `k_proj` and `v_proj` are `1024 x 4096` in Llama 3 8B.\n- Forgetting that non-targeted layers still count in the total.",
        follow_up="Add the adapter file size in bf16; support DoRA's extra magnitude vector (`d_out` more parameters per layer); compute the rank at which LoRA stops saving parameters (`r = d_in * d_out / (d_in + d_out)`).",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-dpo-loss",
    title="DPO Loss",
    difficulty="Medium",
    pattern="Finetuning",
    entry="dpo_loss",
    compare="float",
    description=r"""
Compute the **Direct Preference Optimization** loss for a batch of preference pairs.

For each pair you are given four numbers, each the **sum of token log-probabilities** of a response
given the prompt:

- `policy_chosen[i]`, `policy_rejected[i]`: under the model being trained,
- `ref_chosen[i]`, `ref_rejected[i]`: under the frozen reference model.

$$\text{margin}_i = \beta\left[(\pi_c - r_c) - (\pi_r - r_r)\right],\qquad
\mathcal{L}_i = -\log\sigma(\text{margin}_i)$$

Return a dict with

- `"loss"`: the mean of $\mathcal{L}_i$ over the batch,
- `"accuracy"`: the fraction of pairs with `margin > 0` (the "reward accuracy" TRL logs).

Your implementation must be numerically stable for margins of large magnitude (for example
$\pm 800$): `-log(sigmoid(m))` should be computed as `log(1 + exp(-m))` without overflow.

**Example:** `policy_chosen = [-10]`, `policy_rejected = [-18]`, `ref_chosen = [-12]`,
`ref_rejected = [-15]`, `beta = 0.1`: margin `= 0.1 * ((-10 + 12) - (-18 + 15)) = 0.5`,
loss `= log(1 + e^{-0.5}) = 0.4741`, accuracy `1.0`.
""",
    starter=r'''import numpy as np

def dpo_loss(policy_chosen, policy_rejected, ref_chosen, ref_rejected, beta=0.1):
    pass
''',
    solution=r'''import numpy as np

def dpo_loss(policy_chosen, policy_rejected, ref_chosen, ref_rejected, beta=0.1):
    pc, pr, rc, rr = (np.asarray(a, dtype=float) for a in (policy_chosen, policy_rejected, ref_chosen, ref_rejected))
    margin = beta * ((pc - rc) - (pr - rr))
    loss = np.logaddexp(0.0, -margin)
    return {"loss": float(loss.mean()), "accuracy": float((margin > 0).mean())}
''',
    tests=[
        [[-10], [-18], [-12], [-15], 0.1],
        [[-12, -30], [-15, -28], [-12, -30], [-15, -28], 0.1],
        [[-10, -27], [-18, -33], [-12, -30], [-15, -28], 0.1],
        [[-20, -5], [-10, -9], [-12, -6], [-15, -8], 0.5],
        [[0.0], [-8000.0], [0.0], [0.0], 0.1],
        [[-8000.0], [0.0], [0.0], [0.0], 0.1],
        [[-1, -2, -3, -4], [-4, -3, -2, -1], [-2, -2, -2, -2], [-2, -2, -2, -2], 1.0],
        [[-3.5], [-3.5], [-1.0], [-9.0], 0.2],
        [(_rng.standard_normal(16) * 5 - 20).round(3).tolist(), (_rng.standard_normal(16) * 5 - 22).round(3).tolist(),
         (_rng.standard_normal(16) * 5 - 21).round(3).tolist(), (_rng.standard_normal(16) * 5 - 21).round(3).tolist(), 0.1],
        [[-5, -5], [-6, -4], [-5, -5], [-5, -5], 2.0],
        [[-50.0, -40.0, -30.0], [-45.0, -60.0, -30.0], [-48.0, -41.0, -29.0], [-47.0, -55.0, -31.0], 0.05],
    ],
    examples=2,
    wrong_solutions=[
        # ignores the reference model
        r'''import numpy as np
def dpo_loss(policy_chosen, policy_rejected, ref_chosen, ref_rejected, beta=0.1):
    m = beta * (np.asarray(policy_chosen, dtype=float) - np.asarray(policy_rejected, dtype=float))
    return {"loss": float(np.logaddexp(0.0, -m).mean()), "accuracy": float((m > 0).mean())}
''',
        # sign error: rewards the rejected response
        r'''import numpy as np
def dpo_loss(policy_chosen, policy_rejected, ref_chosen, ref_rejected, beta=0.1):
    pc, pr, rc, rr = (np.asarray(a, dtype=float) for a in (policy_chosen, policy_rejected, ref_chosen, ref_rejected))
    m = beta * ((pr - rr) - (pc - rc))
    return {"loss": float(np.logaddexp(0.0, -m).mean()), "accuracy": float((m > 0).mean())}
''',
        # numerically unstable
        r'''import math
def dpo_loss(policy_chosen, policy_rejected, ref_chosen, ref_rejected, beta=0.1):
    losses, acc = [], 0
    for pc, pr, rc, rr in zip(policy_chosen, policy_rejected, ref_chosen, ref_rejected):
        m = beta * ((pc - rc) - (pr - rr))
        try:
            losses.append(-math.log(1.0 / (1.0 + math.exp(-m))))
        except (OverflowError, ValueError):
            losses.append(0.0)
        acc += m > 0
    return {"loss": sum(losses) / len(losses), "accuracy": acc / len(losses)}
''',
        # beta applied outside the sigmoid
        r'''import numpy as np
def dpo_loss(policy_chosen, policy_rejected, ref_chosen, ref_rejected, beta=0.1):
    pc, pr, rc, rr = (np.asarray(a, dtype=float) for a in (policy_chosen, policy_rejected, ref_chosen, ref_rejected))
    m = (pc - rc) - (pr - rr)
    return {"loss": float(beta * np.logaddexp(0.0, -m).mean()), "accuracy": float((m > 0).mean())}
''',
    ],
    guide=dict(
        prereqs="Lesson *SFT and DPO with TRL*; the logistic (sigmoid) function.",
        intuition="DPO treats `beta * log(pi / pi_ref)` as an implicit reward. The loss is a logistic regression that asks the chosen response's reward to exceed the rejected one's. Measuring against the reference keeps the policy from drifting just to win comparisons.",
        hints=[
            "Compute the two log-ratios first: `pc - rc` and `pr - rr`.",
            "`-log(sigmoid(m)) = log(1 + exp(-m))`, which is `np.logaddexp(0, -m)`: stable for any `m`.",
            "Accuracy is the mean of `margin > 0`.",
        ],
        brute_force="Loop over pairs and use `-math.log(1 / (1 + math.exp(-m)))`. Correct for small margins but overflows for `m = -800`; rewrite it as `max(-m, 0) + log1p(exp(-abs(m)))`.",
        approach="1. Convert to arrays.\n2. `margin = beta * ((pc - rc) - (pr - rr))`.\n3. `loss = logaddexp(0, -margin).mean()`.\n4. `accuracy = (margin > 0).mean()`.\n\n**Dry run:** when the policy equals the reference every margin is 0, the loss is `log 2 = 0.6931` and the accuracy is 0 (no margin is strictly positive).",
        complexity="$O(n)$ time and space for a batch of $n$ pairs.",
        pitfalls="- Dropping the reference terms (the loss then just maximises the chosen-vs-rejected gap and the model drifts).\n- Swapping chosen and rejected.\n- Multiplying the loss by `beta` instead of scaling the margin inside the sigmoid.\n- Overflow in `exp` for large negative margins.\n- Using mean token log-prob instead of the **sum** over the response.",
        follow_up="Add the IPO variant (`(margin/beta - 1/(2*tau))**2`); compute the implicit rewards TRL logs (`rewards/chosen`, `rewards/rejected`, `rewards/margins`); derive the gradient with respect to the policy log-probs.",
    ),
),
]
