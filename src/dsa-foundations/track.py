TRACK = dict(
    id="dsa-foundations",
    title="DSA Foundations (Goodrich)",
    icon="📚",
    color="#2a6f97",
    group="Data Structures & Algorithms",
    blurb="The theory track: a chapter-by-chapter tour of Goodrich, Tamassia & Goldwasser - analysis, recursion, "
          "arrays, lists, trees, heaps, hashing, search trees, sorting, text, graphs and external memory - "
          "with runnable implementations and build-it-yourself exercises.",
    sources=["Goodrich, Tamassia & Goldwasser, Data Structures and Algorithms in Python (Wiley, 2013), ch. 3-15"],
    modules=[
        dict(
            id="analysis",
            title="Algorithm Analysis",
            summary="Experiments, the seven growth functions, big-O/Omega/Theta, and justification techniques.",
            lessons=[
                dict(id="seven-functions", title="Measuring algorithms and the seven functions", file="01-seven-functions.md"),
                dict(id="asymptotic-notation", title="Big-O, Big-Omega and Big-Theta", file="02-asymptotic-notation.md"),
                dict(id="analysis-examples", title="Analysing real code and proving it correct", file="03-analysis-examples.md"),
            ],
            problems=["dsaf-prefix-averages"],
        ),
        dict(
            id="recursion",
            title="Recursion",
            summary="Factorial, rulers, binary search, file systems; recursion traces, linear/binary/multiple recursion.",
            lessons=[
                dict(id="recursion-examples", title="Thinking recursively: four classic examples", file="04-recursion-examples.md"),
                dict(id="recursion-analysis", title="Analysing recursive algorithms", file="05-recursion-analysis.md"),
                dict(id="recursion-design", title="Designing recursion and eliminating it", file="06-recursion-design.md"),
            ],
            problems=["dsaf-english-ruler", "dsaf-recursive-binary-search"],
        ),
        dict(
            id="arrays",
            title="Array-Based Sequences",
            summary="Low-level arrays, dynamic arrays and amortised append, list/str costs, sorting, ciphers, 2-D data.",
            lessons=[
                dict(id="low-level-arrays", title="Low-level arrays and Python's sequence types", file="07-low-level-arrays.md"),
                dict(id="dynamic-arrays", title="Dynamic arrays and amortised analysis", file="08-dynamic-arrays.md"),
                dict(id="using-arrays", title="Using arrays: insertion sort, ciphers and 2-D data", file="09-using-arrays.md"),
            ],
            problems=["dsaf-dynamic-array", "dsaf-insertion-sort", "dsaf-caesar-cipher"],
        ),
        dict(
            id="stacks-queues",
            title="Stacks, Queues and Deques",
            summary="LIFO and FIFO ADTs, array implementations, circular buffers and delimiter matching.",
            lessons=[
                dict(id="stacks", title="Stacks and their applications", file="10-stacks.md"),
                dict(id="queues-deques", title="Queues, circular arrays and deques", file="11-queues-deques.md"),
            ],
            problems=["dsaf-array-stack", "dsaf-circular-queue"],
        ),
        dict(
            id="linked-lists",
            title="Linked Lists",
            summary="Singly, circular and doubly linked lists, the positional list ADT, move-to-front.",
            lessons=[
                dict(id="singly-circular", title="Singly and circularly linked lists", file="12-singly-circular.md"),
                dict(id="doubly-positional", title="Doubly linked lists and positional lists", file="13-doubly-positional.md"),
                dict(id="mtf-tradeoffs", title="Access frequencies, move-to-front and link vs array", file="14-mtf-tradeoffs.md"),
            ],
            problems=["dsaf-linked-deque", "dsaf-move-to-front"],
        ),
        dict(
            id="trees",
            title="Trees",
            summary="General and binary trees, properties, representations, traversals, Euler tours, expression trees.",
            lessons=[
                dict(id="tree-basics", title="Tree terminology, ADTs and representations", file="15-tree-basics.md"),
                dict(id="tree-traversals", title="Traversals, Euler tours and expression trees", file="16-tree-traversals.md"),
            ],
            problems=["dsaf-tree-traversals", "dsaf-expression-tree"],
        ),
        dict(
            id="priority-queues",
            title="Priority Queues and Heaps",
            summary="PQ ADT, list implementations, binary heaps, bottom-up construction, heap-sort, adaptable PQs.",
            lessons=[
                dict(id="heaps", title="Priority queues and binary heaps", file="17-heaps.md"),
                dict(id="heap-sort-adaptable", title="PQ sorting, heap-sort and adaptable priority queues", file="18-heap-sort-adaptable.md"),
            ],
            problems=["dsaf-heap-pq", "dsaf-heap-sort"],
        ),
        dict(
            id="maps-hashing",
            title="Maps, Hash Tables and Skip Lists",
            summary="Map ADT, hash codes and compression, chaining and open addressing, sorted maps, skip lists, sets.",
            lessons=[
                dict(id="maps-hash-functions", title="Maps and hash functions", file="19-maps-hash-functions.md"),
                dict(id="collisions", title="Collision handling, load factors and rehashing", file="20-collisions.md"),
                dict(id="sorted-maps-skip-lists", title="Sorted maps, skip lists, sets and multimaps", file="21-sorted-maps-skip-lists.md"),
            ],
            problems=["dsaf-chain-hashmap"],
        ),
        dict(
            id="search-trees",
            title="Search Trees",
            summary="Binary search trees, rotations, AVL, splay, (2,4) and red-black trees.",
            lessons=[
                dict(id="bst", title="Binary search trees", file="22-bst.md"),
                dict(id="avl", title="Rotations and AVL trees", file="23-avl.md"),
                dict(id="splay", title="Splay trees and amortised balance", file="24-splay.md"),
                dict(id="two-four-red-black", title="(2,4) trees and red-black trees", file="25-two-four-red-black.md"),
            ],
            problems=["dsaf-bst-class", "dsaf-avl-check", "dsaf-avl-insert"],
        ),
        dict(
            id="sorting",
            title="Sorting and Selection",
            summary="Merge-sort, quick-sort, the comparison lower bound, bucket/radix sort, quick-select.",
            lessons=[
                dict(id="merge-sort", title="Divide and conquer: merge-sort", file="26-merge-sort.md"),
                dict(id="quick-sort", title="Quick-sort and randomisation", file="27-quick-sort.md"),
                dict(id="lower-bound-linear", title="The sorting lower bound and linear-time sorts", file="28-lower-bound-linear.md"),
                dict(id="selection", title="Comparing sorts and selection", file="29-selection.md"),
            ],
            problems=["dsaf-merge-sort-inversions", "dsaf-quicksort-inplace", "dsaf-quickselect", "dsaf-radix-sort"],
        ),
        dict(
            id="text",
            title="Text Processing",
            summary="Brute force, Boyer-Moore, KMP; dynamic programming (matrix chain, LCS); Huffman; tries.",
            lessons=[
                dict(id="pattern-matching", title="Pattern matching: brute force, Boyer-Moore, KMP", file="30-pattern-matching.md"),
                dict(id="dynamic-programming", title="Dynamic programming: matrix chain and LCS", file="31-dynamic-programming.md"),
                dict(id="huffman-tries", title="Greedy compression and tries", file="32-huffman-tries.md"),
            ],
            problems=["dsaf-kmp-failure", "dsaf-kmp-search", "dsaf-lcs", "dsaf-matrix-chain", "dsaf-huffman-cost", "dsaf-trie"],
        ),
        dict(
            id="graphs",
            title="Graph Algorithms",
            summary="Graph ADT and representations, DFS/BFS, transitive closure, DAGs, Dijkstra, MSTs, union-find.",
            lessons=[
                dict(id="graph-representations", title="Graphs and their representations", file="33-graph-representations.md"),
                dict(id="graph-traversals", title="DFS, BFS, transitive closure and DAGs", file="34-graph-traversals.md"),
                dict(id="shortest-paths", title="Weighted graphs and Dijkstra's algorithm", file="35-shortest-paths.md"),
                dict(id="mst-union-find", title="Minimum spanning trees and union-find", file="36-mst-union-find.md"),
            ],
            problems=["dsaf-topological-order", "dsaf-dijkstra", "dsaf-mst-weight", "dsaf-union-find"],
        ),
        dict(
            id="memory",
            title="Memory Management and B-Trees",
            summary="Allocation, garbage collection, memory hierarchies, caching policies, B-trees, external sorting.",
            lessons=[
                dict(id="memory-management", title="Memory allocation, garbage collection and caching", file="37-memory-management.md"),
                dict(id="btrees", title="External searching: (a,b) trees and B-trees", file="38-btrees.md"),
            ],
            problems=["dsaf-btree-search"],
        ),
    ],
)
