TRACK = dict(
    id="neet-linked-trees",
    title="Patterns III — Linked Lists, Trees & Tries",
    icon="🌳",
    color="#2e8b57",
    group="Data Structures & Algorithms",
    blurb=("Pointer surgery on linked lists, every flavour of tree traversal, binary search trees and tries — "
           "the node-based half of the NeetCode 150, with a judge that builds the lists and trees for you."),
    sources=[
        "Goodrich, Tamassia & Goldwasser, Data Structures and Algorithms in Python, ch. 7 (linked lists), "
        "ch. 8 (trees), ch. 11 (search trees), ch. 13.5 (tries)",
        "NeetCode 150 (Linked List, Trees, Tries)",
    ],
    modules=[
        dict(
            id="linked-list",
            title="Linked Lists",
            summary="Dummy nodes, pointer rewiring, fast/slow pointers, reversal and merging.",
            lessons=[
                dict(id="ll-pointers", title="Nodes, pointers and the dummy-node trick", file="01-pointers-dummy.md"),
                dict(id="ll-fast-slow", title="Fast and slow pointers (with Floyd's proof)", file="02-fast-slow.md"),
                dict(id="ll-reversal", title="Reversal, merging and in-place rearrangement", file="03-reversal-merge.md"),
            ],
            problems=[
                "reverse-linked-list", "merge-two-sorted-lists", "linked-list-cycle", "middle-of-the-linked-list",
                "palindrome-linked-list", "intersection-of-two-linked-lists", "reorder-list",
                "remove-nth-node-from-end-of-list", "copy-list-with-random-pointer", "add-two-numbers",
                "find-the-duplicate-number", "lru-cache", "merge-k-sorted-lists", "reverse-nodes-in-k-group",
            ],
        ),
        dict(
            id="trees",
            title="Trees",
            summary="Tree vocabulary, DFS and BFS, returning values up the tree, BSTs and tree construction.",
            lessons=[
                dict(id="tree-basics", title="Tree vocabulary, shapes and representations", file="04-tree-basics.md"),
                dict(id="tree-traversals", title="Traversals: DFS (pre/in/post) and BFS", file="05-traversals.md"),
                dict(id="tree-return-up", title="Returning values up the tree", file="06-return-up.md"),
                dict(id="tree-bst", title="Binary search trees, construction and serialization", file="07-bst-construction.md"),
            ],
            problems=[
                "invert-binary-tree", "maximum-depth-of-binary-tree", "binary-tree-inorder-traversal",
                "same-tree", "subtree-of-another-tree", "path-sum", "diameter-of-binary-tree",
                "balanced-binary-tree", "binary-tree-level-order-traversal", "binary-tree-right-side-view",
                "count-good-nodes-in-binary-tree", "lowest-common-ancestor-of-a-binary-search-tree",
                "insert-into-a-binary-search-tree", "delete-node-in-a-bst", "validate-binary-search-tree",
                "kth-smallest-element-in-a-bst", "construct-binary-tree-from-preorder-and-inorder-traversal",
                "binary-tree-maximum-path-sum", "serialize-and-deserialize-binary-tree",
            ],
        ),
        dict(
            id="tries",
            title="Tries",
            summary="Prefix trees: insert/search/prefix in O(length), wildcards, and trie-guided backtracking.",
            lessons=[
                dict(id="trie-basics", title="Tries: prefix trees from scratch", file="08-tries.md"),
                dict(id="trie-search", title="Wildcards and trie-guided grid search", file="09-trie-search.md"),
            ],
            problems=[
                "implement-trie-prefix-tree", "design-add-and-search-words-data-structure", "word-search-ii",
            ],
        ),
    ],
)
