TRACK = dict(
    id="neet-heap-graphs",
    title="Patterns IV — Heaps, Backtracking & Graphs",
    icon="⚓",
    color="#2a7ab0",
    group="Data Structures & Algorithms",
    blurb="Priority queues and the top-k / two-heap patterns, the backtracking template with pruning, "
          "and the full graph toolkit: DFS/BFS, topological sort, union-find, Dijkstra, Bellman-Ford, MSTs "
          "and Eulerian paths — with 58 judged NeetCode problems.",
    sources=[
        "Goodrich, Tamassia & Goldwasser, Data Structures and Algorithms in Python, ch. 9 (Priority Queues)",
        "Goodrich, Tamassia & Goldwasser, Data Structures and Algorithms in Python, ch. 14 (Graph Algorithms)",
        "NeetCode 150 roadmap",
    ],
    modules=[
        dict(
            id="heap-priority-queue",
            title="Heap / Priority Queue",
            summary="Binary heaps, Python's heapq, the max-heap trick, top-k selection and the two-heap median pattern.",
            lessons=[
                dict(id="binary-heaps", title="Binary heaps and Python's heapq", file="01-binary-heaps.md"),
                dict(id="heap-patterns", title="Heap patterns: top-k, merging, scheduling and two heaps", file="02-heap-patterns.md"),
            ],
            problems=[
                "kth-largest-element-in-a-stream", "last-stone-weight", "k-closest-points-to-origin",
                "kth-largest-element-in-an-array", "task-scheduler", "design-twitter",
                "find-median-from-data-stream",
                "top-k-frequent-words", "reorganize-string", "single-threaded-cpu", "ipo",
                "seat-reservation-manager",
            ],
        ),
        dict(
            id="backtracking",
            title="Backtracking",
            summary="Choose, explore, un-choose: state-space trees for subsets, combinations, permutations and constraint search.",
            lessons=[
                dict(id="backtracking-template", title="The backtracking template and state-space trees", file="03-backtracking-template.md"),
                dict(id="backtracking-pruning", title="Duplicates, pruning and constraint search", file="04-backtracking-pruning.md"),
            ],
            problems=[
                "subsets", "combination-sum", "combination-sum-ii", "permutations", "subsets-ii",
                "word-search", "palindrome-partitioning", "letter-combinations-of-a-phone-number", "n-queens",
                "combinations", "permutations-ii", "restore-ip-addresses", "word-break-ii",
                "matchsticks-to-square", "sudoku-solver",
            ],
        ),
        dict(
            id="graphs",
            title="Graphs",
            summary="Representations, DFS and BFS on grids and adjacency lists, multi-source BFS, cycle detection, topological sort and union-find.",
            lessons=[
                dict(id="graph-representations", title="Graphs and how to store them", file="05-graph-representations.md"),
                dict(id="dfs-bfs", title="DFS and BFS on grids and adjacency lists", file="06-dfs-bfs.md"),
                dict(id="cycles-toposort", title="Cycle detection and topological sort", file="07-cycles-toposort.md"),
                dict(id="union-find", title="Union-find (disjoint sets)", file="08-union-find.md"),
            ],
            problems=[
                "number-of-islands", "max-area-of-island", "clone-graph", "walls-and-gates", "rotting-oranges",
                "pacific-atlantic-water-flow", "surrounded-regions", "course-schedule", "course-schedule-ii",
                "graph-valid-tree", "number-of-connected-components-in-an-undirected-graph",
                "redundant-connection", "word-ladder",
                "island-perimeter", "flood-fill", "shortest-path-in-binary-matrix", "01-matrix",
                "open-the-lock", "find-eventual-safe-states", "is-graph-bipartite", "minimum-height-trees",
            ],
        ),
        dict(
            id="advanced-graphs",
            title="Advanced Graphs",
            summary="Weighted shortest paths (Dijkstra, Bellman-Ford), minimum spanning trees (Prim, Kruskal) and Eulerian paths (Hierholzer).",
            lessons=[
                dict(id="shortest-paths", title="Shortest paths: Dijkstra and Bellman-Ford", file="09-shortest-paths.md"),
                dict(id="minimum-spanning-trees", title="Minimum spanning trees: Prim and Kruskal", file="10-minimum-spanning-trees.md"),
                dict(id="eulerian-paths", title="Eulerian paths and Hierholzer's algorithm", file="11-eulerian-paths.md"),
            ],
            problems=[
                "network-delay-time", "reconstruct-itinerary", "min-cost-to-connect-all-points",
                "swim-in-rising-water", "alien-dictionary", "cheapest-flights-within-k-stops",
                "path-with-minimum-effort", "path-with-maximum-probability",
                "find-the-city-with-the-smallest-number-of-neighbors-at-a-threshold-distance",
                "number-of-ways-to-arrive-at-destination",
            ],
        ),
    ],
)
