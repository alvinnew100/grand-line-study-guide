"""DSA in JavaScript: Linked List problems.

Convention (documented in every description and in the lesson *Linked lists and trees with classes*):
tests pass plain arrays; a provided driver builds ListNode chains with buildList, calls the learner's
function, and converts the returned head back to an array with listToArray.
"""
import random


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


rng = random.Random(31)

LIST_HELPERS = r'''
// --- provided: ListNode and helpers (do not change) ---
class ListNode {
  constructor(val = 0, next = null) {
    this.val = val;
    this.next = next;
  }
}
function buildList(values) {            // [1, 2, 3] -> 1 -> 2 -> 3
  const dummy = new ListNode();
  let tail = dummy;
  for (const v of values) { tail.next = new ListNode(v); tail = tail.next; }
  return dummy.next;
}
function listToArray(head) {            // 1 -> 2 -> 3 -> [1, 2, 3]
  const out = [];
  for (let n = head; n && out.length < 100000; n = n.next) out.push(n.val);
  return out;
}
'''

CONVENTION = r"""

**How the tests talk to your code.** Lists are written as arrays: `[1, 2, 3]` means `1 -> 2 -> 3`, and `[]` is the
empty list (`null`). The provided `ListNode` class, `buildList` and `listToArray` helpers and the small driver at
the bottom convert between the two, so your function receives and returns real `ListNode` objects. Do not edit
the provided part.
"""

LRU_DRIVER = r'''
// --- driver used by the tests (provided, do not change) ---
function runLRUCache(ops, args) {
  let cache = null;
  const out = [];
  for (let i = 0; i < ops.length; i++) {
    if (ops[i] === "LRUCache") { cache = new LRUCache(...args[i]); out.push(null); }
    else { const r = cache[ops[i]](...args[i]); out.push(r === undefined ? null : r); }
  }
  return out;
}
'''

def lru_random(n, cap, keys, seed):
    r = random.Random(seed)
    ops, args = ["LRUCache"], [[cap]]
    for _ in range(n):
        if r.random() < 0.5:
            ops.append("put"); args.append([r.randint(0, keys), r.randint(0, 10**4)])
        else:
            ops.append("get"); args.append([r.randint(0, keys)])
    return [ops, args]

PROBLEMS = [
dict(
    id="js-reverse-linked-list", title="Reverse Linked List", difficulty="Easy", pattern="Linked List",
    leetcode="https://leetcode.com/problems/reverse-linked-list/",
    neetcode="https://neetcode.io/problems/reverse-a-linked-list",
    kind="js", entry="runReverseList",
    description=r"""
Given the `head` of a singly linked list, reverse the list and return the new head.

- `0 <=` number of nodes `<= 5000`

**Example 1:** `[0, 1, 2, 3]` → `[3, 2, 1, 0]`

**Example 2:** `[]` → `[]`
""" + CONVENTION,
    starter="function reverseList(head) {\n  // your code\n}\n" + LIST_HELPERS + "\nfunction runReverseList(values) {\n  return listToArray(reverseList(buildList(values)));\n}\n",
    solution=r'''function reverseList(head) {
  let prev = null, cur = head;
  while (cur) {
    const next = cur.next;   // remember the rest before cutting the link
    cur.next = prev;         // turn the arrow around
    prev = cur;
    cur = next;
  }
  return prev;
}
''' + LIST_HELPERS + "\nfunction runReverseList(values) {\n  return listToArray(reverseList(buildList(values)));\n}\n",
    tests=[[[0, 1, 2, 3]], [[]], [[7]], [[1, 2]], [[1, 2, 3, 4, 5]], [[5, 5, 5]], [[-1, 0, 1]], [list(range(5000))]],
    examples=2,
    wrong_solutions=[
        "function reverseList(head) {\n  return head;\n}\n" + LIST_HELPERS + "\nfunction runReverseList(values) {\n  return listToArray(reverseList(buildList(values)));\n}\n",
        "function reverseList(head) {\n  if (!head || !head.next) return head;\n  const second = head.next;\n  head.next = null;\n  second.next = head;\n  return second;\n}\n" + LIST_HELPERS + "\nfunction runReverseList(values) {\n  return listToArray(reverseList(buildList(values)));\n}\n",
    ],
    guide=G(
        prereqs="The lesson *Linked lists and trees with classes*: `ListNode`, `null` as the end of a list, walking with `cur = cur.next`.",
        intuition="Walk the list once and turn every arrow around. Keep three references: the node before (`prev`), the current node, and the next node, which you must save **before** you overwrite `cur.next`.",
        hints=[
            "Start with `prev = null`: the old head becomes the new tail.",
            "Save `cur.next` in a variable before changing it.",
            "When `cur` becomes `null`, `prev` is the new head.",
        ],
        brute_force="Copy the values into an array, reverse it, and rebuild nodes: O(n) time but O(n) extra space and new nodes instead of re-linking the existing ones.",
        approach="1. `prev = null`, `cur = head`.\n2. Loop: `next = cur.next`; `cur.next = prev`; `prev = cur`; `cur = next`.\n3. Return `prev`.\n\n**Dry run** `0 -> 1 -> 2`: 0 points to null; 1 points to 0; 2 points to 1; return 2.",
        complexity="Time O(n), space O(1).",
        pitfalls="- Losing the rest of the list by assigning `cur.next = prev` before saving `next`.\n- Returning `head` (now the tail) instead of `prev`.\n- A recursive version uses one stack frame per node; with 5000 nodes it is fine, but very long lists can exceed the engine's call-stack limit (lesson *Recursion depth limits and backtracking*).",
        follow_up="Reverse Linked List II reverses only positions `left..right`; Reverse Nodes in k-Group repeats the same loop per block.",
    ),
),
dict(
    id="js-merge-two-sorted-lists", title="Merge Two Sorted Lists", difficulty="Easy", pattern="Linked List",
    leetcode="https://leetcode.com/problems/merge-two-sorted-lists/",
    neetcode="https://neetcode.io/problems/merge-two-sorted-linked-lists",
    kind="js", entry="runMerge",
    description=r"""
You are given the heads of two linked lists sorted in non-decreasing order. Splice their nodes together into
one sorted list and return its head.

- each list has `0..100` nodes, values in `-100..100`

**Example 1:** `[1, 2, 4]` and `[1, 3, 5]` → `[1, 1, 2, 3, 4, 5]`

**Example 2:** `[]` and `[1, 2]` → `[1, 2]`
""" + CONVENTION,
    starter="function mergeTwoLists(list1, list2) {\n  // your code\n}\n" + LIST_HELPERS + "\nfunction runMerge(a, b) {\n  return listToArray(mergeTwoLists(buildList(a), buildList(b)));\n}\n",
    solution=r'''function mergeTwoLists(list1, list2) {
  const dummy = new ListNode();     // placeholder in front of the answer
  let tail = dummy;
  while (list1 && list2) {
    if (list1.val <= list2.val) { tail.next = list1; list1 = list1.next; }
    else { tail.next = list2; list2 = list2.next; }
    tail = tail.next;
  }
  tail.next = list1 || list2;       // attach whatever is left
  return dummy.next;
}
''' + LIST_HELPERS + "\nfunction runMerge(a, b) {\n  return listToArray(mergeTwoLists(buildList(a), buildList(b)));\n}\n",
    tests=[[[1, 2, 4], [1, 3, 5]], [[], [1, 2]], [[], []], [[5], []], [[1, 1, 1], [1, 1]], [[-100, 0, 100], [-50, 50]],
           [[1, 2, 3], [4, 5, 6]], [[4, 5, 6], [1, 2, 3]], [[2], [1]], [sorted(rng.randint(-100, 100) for _ in range(100)), sorted(rng.randint(-100, 100) for _ in range(100))]],
    examples=2,
    wrong_solutions=[
        "function mergeTwoLists(a, b) {\n  const d = new ListNode(); let t = d;\n  while (a && b) {\n    if (a.val <= b.val) { t.next = a; a = a.next; } else { t.next = b; b = b.next; }\n    t = t.next;\n  }\n  return d.next;\n}\n" + LIST_HELPERS + "\nfunction runMerge(a, b) {\n  return listToArray(mergeTwoLists(buildList(a), buildList(b)));\n}\n",
        "function mergeTwoLists(a, b) {\n  if (!a) return b;\n  let t = a;\n  while (t.next) t = t.next;\n  t.next = b;\n  return a;\n}\n" + LIST_HELPERS + "\nfunction runMerge(a, b) {\n  return listToArray(mergeTwoLists(buildList(a), buildList(b)));\n}\n",
    ],
    guide=G(
        prereqs="The dummy-node trick (lesson *Linked lists and trees with classes*).",
        intuition="Like merging two sorted piles of cards: always take the smaller front card. A dummy node in front of the result means you never have to special-case the first node.",
        hints=[
            "Create `const dummy = new ListNode()` and a `tail` pointer.",
            "While both lists are non-empty, link the smaller head and advance it.",
            "When one list runs out, link the rest of the other in one step.",
        ],
        brute_force="Collect all values in an array, sort with `(a, b) => a - b`, and build a new list: O((m + n) log(m + n)) and allocates new nodes.",
        approach="1. `dummy`, `tail = dummy`.\n2. While both exist: attach the smaller (`<=` keeps the merge stable), advance that list and `tail`.\n3. `tail.next = list1 || list2`.\n4. Return `dummy.next`.",
        complexity="Time O(m + n), space O(1) (nodes are reused).",
        pitfalls="- Forgetting to attach the leftover list drops its tail.\n- Returning `dummy` instead of `dummy.next` adds a stray 0 at the front.",
        follow_up="Merge k Sorted Lists: merge in pairs (O(N log k)) or keep the k heads in a min-heap.",
    ),
),
dict(
    id="js-linked-list-cycle", title="Linked List Cycle", difficulty="Easy", pattern="Linked List",
    leetcode="https://leetcode.com/problems/linked-list-cycle/",
    neetcode="https://neetcode.io/problems/linked-list-cycle-detection",
    kind="js", entry="runHasCycle",
    description=r"""
Given the `head` of a linked list, return `true` if following `next` pointers ever brings you back to a node you
already visited (a **cycle**), and `false` if the list ends with `null`. Try to use O(1) extra memory.

**How the tests build the list.** Each test is `[values, pos]`. The driver builds the list from `values`, and if
`pos >= 0` it connects the last node's `next` to the node at index `pos`. Your function only receives `head`.

**Example 1:** `values = [3, 2, 0, -4], pos = 1` → `true` (the tail links back to the node holding 2)

**Example 2:** `values = [1, 2], pos = -1` → `false`
""",
    starter="function hasCycle(head) {\n  // your code\n}\n" + LIST_HELPERS + r'''
function runHasCycle(values, pos) {
  const head = buildList(values), nodes = [];
  for (let n = head; n; n = n.next) nodes.push(n);
  if (pos >= 0) nodes[nodes.length - 1].next = nodes[pos];
  return hasCycle(head);
}
''',
    solution=r'''function hasCycle(head) {
  let slow = head, fast = head;
  while (fast && fast.next) {
    slow = slow.next;          // one step
    fast = fast.next.next;     // two steps
    if (slow === fast) return true;   // same node object: they met inside a cycle
  }
  return false;
}
''' + LIST_HELPERS + r'''
function runHasCycle(values, pos) {
  const head = buildList(values), nodes = [];
  for (let n = head; n; n = n.next) nodes.push(n);
  if (pos >= 0) nodes[nodes.length - 1].next = nodes[pos];
  return hasCycle(head);
}
''',
    tests=[[[3, 2, 0, -4], 1], [[1, 2], -1], [[1, 2], 0], [[1], -1], [[1], 0], [[], -1], [[1, 1, 1, 1], -1], [[1, 1, 1, 1], 3],
           [list(range(5000)), 2500], [list(range(5000)), -1]],
    examples=2,
    wrong_solutions=[
        "function hasCycle(head) {\n  const seen = new Set();\n  for (let n = head; n; n = n.next) {\n    if (seen.has(n.val)) return true;\n    seen.add(n.val);\n  }\n  return false;\n}\n" + LIST_HELPERS + r'''
function runHasCycle(values, pos) {
  const head = buildList(values), nodes = [];
  for (let n = head; n; n = n.next) nodes.push(n);
  if (pos >= 0) nodes[nodes.length - 1].next = nodes[pos];
  return hasCycle(head);
}
''',
        "function hasCycle(head) {\n  return !!(head && head.next && head.next.next);\n}\n" + LIST_HELPERS + r'''
function runHasCycle(values, pos) {
  const head = buildList(values), nodes = [];
  for (let n = head; n; n = n.next) nodes.push(n);
  if (pos >= 0) nodes[nodes.length - 1].next = nodes[pos];
  return hasCycle(head);
}
''',
    ],
    guide=G(
        prereqs="Object identity with `===` (two references to the same node), and the fast/slow pointer idea.",
        intuition="Send two runners down the list, one twice as fast. If the list ends, the fast runner reaches `null`. If there is a loop, the fast runner laps the slow one and they land on the **same node object**.",
        hints=[
            "A `Set` of visited **nodes** (not values) works in O(n) space.",
            "For O(1) space: `slow` moves one step, `fast` moves two.",
            "Loop while `fast && fast.next`; compare nodes with `===`.",
        ],
        brute_force="Store every visited node in a `Set` and stop when you see one again: O(n) time and space. Storing **values** is wrong because different nodes can hold equal values.",
        approach="1. `slow = fast = head`.\n2. While `fast && fast.next`: advance `slow` by one, `fast` by two; if `slow === fast` return `true`.\n3. Return `false`.\n\nInside the cycle the gap between them shrinks by one each step, so they must meet.",
        complexity="Time O(n), space O(1).",
        pitfalls="- Checking `slow === fast` before moving returns `true` at the start.\n- Guarding only `fast` (not `fast.next`) throws `TypeError: Cannot read properties of null`.\n- Comparing `slow.val === fast.val` gives false positives on repeated values.",
        follow_up="Linked List Cycle II: after they meet, restart one pointer at the head and move both one step at a time; they meet at the cycle entrance.",
    ),
),
dict(
    id="js-remove-nth-node-from-end-of-list", title="Remove Nth Node From End of List", difficulty="Medium", pattern="Linked List",
    leetcode="https://leetcode.com/problems/remove-nth-node-from-end-of-list/",
    neetcode="https://neetcode.io/problems/remove-node-from-end-of-linked-list",
    kind="js", entry="runRemoveNth",
    description=r"""
Given the `head` of a linked list and an integer `n`, remove the `n`-th node counting from the end (the last
node is `n = 1`) and return the head of the changed list. `1 <= n <=` list length. Try a single pass.

**Example 1:** `[1, 2, 3, 4]`, `n = 2` → `[1, 2, 4]`

**Example 2:** `[5]`, `n = 1` → `[]`
""" + CONVENTION,
    starter="function removeNthFromEnd(head, n) {\n  // your code\n}\n" + LIST_HELPERS + "\nfunction runRemoveNth(values, n) {\n  return listToArray(removeNthFromEnd(buildList(values), n));\n}\n",
    solution=r'''function removeNthFromEnd(head, n) {
  const dummy = new ListNode(0, head);
  let lead = dummy, trail = dummy;
  for (let i = 0; i < n; i++) lead = lead.next;   // open a gap of n nodes
  while (lead.next) { lead = lead.next; trail = trail.next; }
  trail.next = trail.next.next;                   // trail sits just before the target
  return dummy.next;
}
''' + LIST_HELPERS + "\nfunction runRemoveNth(values, n) {\n  return listToArray(removeNthFromEnd(buildList(values), n));\n}\n",
    tests=[[[1, 2, 3, 4], 2], [[5], 1], [[1, 2, 3, 4, 5], 2], [[1, 2], 1], [[1, 2], 2], [[1, 2, 3], 3], [[1, 2, 3], 1],
           [[7, 7, 7, 7], 4], [list(range(1000)), 1000], [list(range(1000)), 500]],
    examples=2,
    wrong_solutions=[
        "function removeNthFromEnd(head, n) {\n  let lead = head, trail = head;\n  for (let i = 0; i < n; i++) lead = lead.next;\n  if (!lead) return head;\n  while (lead.next) { lead = lead.next; trail = trail.next; }\n  trail.next = trail.next.next;\n  return head;\n}\n" + LIST_HELPERS + "\nfunction runRemoveNth(values, n) {\n  return listToArray(removeNthFromEnd(buildList(values), n));\n}\n",
        "function removeNthFromEnd(head, n) {\n  const d = new ListNode(0, head);\n  let p = d;\n  for (let i = 0; i < n - 1 && p.next; i++) p = p.next;\n  if (p.next) p.next = p.next.next;\n  return d.next;\n}\n" + LIST_HELPERS + "\nfunction runRemoveNth(values, n) {\n  return listToArray(removeNthFromEnd(buildList(values), n));\n}\n",
    ],
    guide=G(
        prereqs="Dummy nodes and two pointers moving at the same speed with a fixed gap.",
        intuition="Move a `lead` pointer `n` steps ahead, then move `lead` and `trail` together. When `lead` reaches the last node, `trail` is exactly one node before the one to delete. A dummy node in front handles deleting the head.",
        hints=[
            "Two passes work: count the length L, then unlink node `L - n`.",
            "For one pass, keep a gap of `n` nodes between two pointers.",
            "Start both at a dummy node so `trail` can stop **before** the head.",
        ],
        brute_force="Two passes: count the nodes, then walk `length - n` steps from a dummy and unlink. Also O(n); the one-pass version is the usual follow-up.",
        approach="1. `dummy = new ListNode(0, head)`; `lead = trail = dummy`.\n2. Move `lead` forward `n` times.\n3. While `lead.next`: move both.\n4. `trail.next = trail.next.next`; return `dummy.next`.\n\n**Dry run** `[1,2,3,4]`, n 2: lead at 2; move both until lead is 4 → trail at 2; unlink 3.",
        complexity="Time O(L), space O(1).",
        pitfalls="- Without a dummy, removing the head (`n` equal to the length) needs a special case.\n- Returning `head` after removing the head node returns the deleted node.",
        follow_up="The same fixed gap finds the middle (fast/slow) or the k-th node from the end.",
    ),
),
dict(
    id="js-lru-cache-design", title="LRU Cache", difficulty="Medium", pattern="Linked List",
    leetcode="https://leetcode.com/problems/lru-cache/",
    neetcode="https://neetcode.io/problems/lru-cache",
    kind="js", entry="runLRUCache",
    description=r"""
Design a **least recently used (LRU)** cache with a fixed `capacity`:

- `get(key)` returns the value stored for `key`, or `-1` if absent. A successful `get` counts as a use.
- `put(key, value)` inserts or updates the key (also a use). If this makes the cache hold more than
  `capacity` keys, evict the key that was used **least recently**.

Both operations must run in O(1) on average.

**How the tests call your class.** Each test is `[ops, args]`, e.g.
`[["LRUCache","put","put","get","put","get"], [[2],[1,10],[2,20],[1],[3,30],[2]]]` → `[null,null,null,10,null,-1]`
(putting 3 evicts key 2, because key 1 was used more recently). The provided `runLRUCache` driver does the
calls. Please build it with a hash map plus a doubly linked list; the guide also shows a shortcut with `Map`.
""",
    starter="class LRUCache {\n  constructor(capacity) {\n    // your fields\n  }\n  get(key) {}\n  put(key, value) {}\n}\n" + LRU_DRIVER,
    solution=r'''class DNode {
  constructor(key, val) { this.key = key; this.val = val; this.prev = null; this.next = null; }
}
class LRUCache {
  constructor(capacity) {
    this.cap = capacity;
    this.map = new Map();                 // key -> DNode
    this.head = new DNode(0, 0);          // sentinel: most recent side
    this.tail = new DNode(0, 0);          // sentinel: least recent side
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }
  unlink(node) {
    node.prev.next = node.next;
    node.next.prev = node.prev;
  }
  pushFront(node) {
    node.next = this.head.next;
    node.prev = this.head;
    this.head.next.prev = node;
    this.head.next = node;
  }
  get(key) {
    const node = this.map.get(key);
    if (!node) return -1;
    this.unlink(node);
    this.pushFront(node);
    return node.val;
  }
  put(key, value) {
    let node = this.map.get(key);
    if (node) {
      node.val = value;
      this.unlink(node);
    } else {
      node = new DNode(key, value);
      this.map.set(key, node);
      if (this.map.size > this.cap) {
        const lru = this.tail.prev;       // least recently used real node
        this.unlink(lru);
        this.map.delete(lru.key);
      }
    }
    this.pushFront(node);
  }
}
''' + LRU_DRIVER,
    tests=[
        [["LRUCache", "put", "put", "get", "put", "get"], [[2], [1, 10], [2, 20], [1], [3, 30], [2]]],
        [["LRUCache", "put", "put", "get", "put", "get", "put", "get", "get", "get"], [[2], [1, 1], [2, 2], [1], [3, 3], [2], [4, 4], [1], [3], [4]]],
        [["LRUCache", "put", "get", "put", "get", "get"], [[1], [2, 1], [2], [3, 2], [2], [3]]],
        [["LRUCache", "get"], [[1], [5]]],
        [["LRUCache", "put", "put", "put", "get", "put", "get", "get"], [[2], [1, 1], [2, 2], [1, 5], [1], [3, 3], [2], [1]]],
        [["LRUCache", "put", "put", "get", "get", "put", "get", "get"], [[2], [2, 1], [1, 1], [2], [1], [4, 1], [1], [2]]],
        [["LRUCache", "put", "put", "put", "put", "get", "get"], [[2], [0, 0], [0, 1], [0, 2], [3, 3], [0], [3]]],
        lru_random(200, 3, 8, 5),
        lru_random(3000, 50, 120, 6),
    ],
    examples=2,
    wrong_solutions=[
        "class LRUCache {\n  constructor(c) { this.c = c; this.m = new Map(); }\n  get(k) { return this.m.has(k) ? this.m.get(k) : -1; }\n  put(k, v) {\n    if (!this.m.has(k) && this.m.size === this.c) this.m.delete(this.m.keys().next().value);\n    this.m.set(k, v);\n  }\n}\n" + LRU_DRIVER,
        "class LRUCache {\n  constructor(c) { this.c = c; this.m = new Map(); }\n  get(k) { if (!this.m.has(k)) return -1; const v = this.m.get(k); this.m.delete(k); this.m.set(k, v); return v; }\n  put(k, v) {\n    if (this.m.size === this.c) this.m.delete(this.m.keys().next().value);\n    this.m.delete(k);\n    this.m.set(k, v);\n  }\n}\n" + LRU_DRIVER,
    ],
    guide=G(
        prereqs="`Map`, classes, and doubly linked lists with sentinel nodes (lesson *Pattern map II*).",
        intuition="You need two things at once: find a key in O(1) (a hash map) and keep keys in order of last use with O(1) moves (a doubly linked list). The map stores pointers to list nodes; a use moves the node to the front, and eviction removes the node at the back.",
        hints=[
            "Which structure removes a node from the middle in O(1) if you already hold the node?",
            "Two sentinel nodes `head` and `tail` remove all null checks.",
            "Store the key inside each node so eviction can delete it from the map.",
        ],
        brute_force="Keep an array of keys in use order and `splice` on each access: O(capacity) per operation.",
        approach="1. `map: key -> node`; sentinel `head` (most recent) and `tail` (least recent).\n2. `get`: missing → -1; else unlink the node, push it to the front, return its value.\n3. `put`: existing → update and move to front; new → create, insert into map, push front; if size exceeds capacity, unlink `tail.prev` and delete its key.\n\n**Shortcut in JavaScript:** a `Map` remembers insertion order, so `delete` then `set` moves a key to the newest end, and `map.keys().next().value` is the oldest key. That gives a five-line LRU; know both versions.",
        complexity="O(1) average for both operations; O(capacity) space.",
        pitfalls="- Evicting before checking whether the key already exists (an update must not evict).\n- Forgetting that `get` counts as a use.\n- With the `Map` shortcut, a plain `set` on an existing key does **not** move it to the end; you must `delete` first.",
        follow_up="LFU Cache adds frequency buckets: a map from frequency to its own ordered list.",
    ),
),
]
