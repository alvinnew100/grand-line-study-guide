"""Second batch: 25 more Linked List / Tree / Trie problems (NeetCode 250 and friends)."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nlt_gen import (balanced_bst, bst_from_keys, complete, inorder,  # noqa: E402
                     random_tree, relabel_distinct, skewed)

r = random.Random(4242)

LN = '''# ListNode is pre-defined by the judge (no need to paste it):
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
'''
TN = '''# TreeNode is pre-defined by the judge (no need to paste it):
# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right
'''
LL_FORMAT = ("\n\n**Judge input format:** a linked list is written as the Python list of its values from head to tail "
             "(`[]` = empty list). The judge builds the `ListNode` chain and converts a returned list back.\n")
TREE_FORMAT = ("\n\n**Judge input format:** a tree is a LeetCode level-order list (values level by level, `None` for a "
               "missing child, trailing `None`s dropped, `[]` = empty tree). The judge builds the `TreeNode`s for you.\n")

BIG = random_tree(5000, 21, -1000, 1000)
BIG_POS = random_tree(900, 22, 0, 9, depth_cap=11)
SKEW_R = skewed(list(range(1, 501)), "right")
SKEW_L = skewed(list(range(1, 501)), "left")
BST_BIG = bst_from_keys(r.sample(range(1, 10 ** 5), 5000))
DISTINCT = relabel_distinct(random_tree(3000, 23), 23)

LCA_ADAPTER = '''

# ---- judge adapter: do not edit -------------------------------------------
# Each test is (root, p, q) with p and q given as VALUES (all values in the tree
# are distinct). The adapter finds the two TreeNode objects, calls
# lowestCommonAncestor(root, p_node, q_node) and reports the returned node's value.
def judge(root, p, q):
    found, stack = {}, [root]
    while stack:
        n = stack.pop()
        if n:
            found[n.val] = n
            stack.append(n.left)
            stack.append(n.right)
    ans = Solution().lowestCommonAncestor(root, found[p], found[q])
    return None if ans is None else ans.val
'''

ITER_ADAPTER = '''

# ---- judge adapter: do not edit -------------------------------------------
# Each test is (root, ops). The adapter creates BSTIterator(root) and then calls
# the listed methods ("next" / "hasNext") in order, returning their results.
def judge(root, ops):
    it = BSTIterator(root)
    return [getattr(it, op)() for op in ops]
'''

BALANCED_BST_CHECKER = '''
def check(args, got, expected):
    import collections
    nums = args[0]
    if not isinstance(got, list):
        return False

    class N:
        __slots__ = ("val", "left", "right")

        def __init__(self, v):
            self.val, self.left, self.right = v, None, None

    if not got:
        return not nums
    it = iter(got)
    root = N(next(it))
    q = collections.deque([root])
    while q:
        node = q.popleft()
        stop = False
        for side in ("left", "right"):
            try:
                v = next(it)
            except StopIteration:
                stop = True
                break
            if v is not None:
                c = N(v)
                setattr(node, side, c)
                q.append(c)
        if stop:
            break
    out, st, cur = [], [], root
    while st or cur:
        while cur:
            st.append(cur)
            cur = cur.left
        cur = st.pop()
        out.append(cur.val)
        cur = cur.right
    if out != nums:
        return False

    height, stack = {None: 0}, [(root, False)]      # iterative post-order: safe on very deep trees
    while stack:
        n, done = stack.pop()
        if n is None:
            continue
        if done:
            a, b = height[n.left], height[n.right]
            if abs(a - b) > 1:
                return False
            height[n] = 1 + max(a, b)
        else:
            stack.append((n, True))
            stack.append((n.left, False))
            stack.append((n.right, False))
    return True
'''


def _iter_ops(n, seed):
    rr = random.Random(seed)
    ops, left = [], n
    while left:
        if rr.random() < 0.3:
            ops.append("hasNext")
        else:
            ops.append("next")
            left -= 1
    return ops + ["hasNext"]


def _mll_ops(n, seed):
    rr = random.Random(seed)
    ops, args, size = ["MyLinkedList"], [[]], 0
    for _ in range(n):
        c = rr.random()
        if c < 0.2:
            ops.append("addAtHead"); args.append([rr.randint(0, 99)]); size += 1
        elif c < 0.4:
            ops.append("addAtTail"); args.append([rr.randint(0, 99)]); size += 1
        elif c < 0.6:
            i = rr.randint(0, size + 1)
            ops.append("addAtIndex"); args.append([i, rr.randint(0, 99)])
            if i <= size:
                size += 1
        elif c < 0.75:
            i = rr.randint(0, size + 1)
            ops.append("deleteAtIndex"); args.append([i])
            if i < size:
                size -= 1
        else:
            ops.append("get"); args.append([rr.randint(0, size + 1)])
    return [ops, args]


def _words(n, lo, hi, alpha, seed):
    rr = random.Random(seed)
    return ["".join(rr.choice(alpha) for _ in range(rr.randint(lo, hi))) for _ in range(n)]


_ms_ops, _ms_args = ["MapSum"], [[]]
for _w in _words(600, 1, 5, "abc", 5):
    if r.random() < 0.6:
        _ms_ops.append("insert"); _ms_args.append([_w, r.randint(1, 1000)])
    else:
        _ms_ops.append("sum"); _ms_args.append([_w[:r.randint(1, len(_w))]])

_lw_chain = ["a" * k for k in range(1, 31)] + ["b" * k for k in range(2, 40)]
_lw_rand = sorted(set(_words(900, 1, 6, "abc", 8)))
r.shuffle(_lw_rand)

PROBLEMS = [
# ============================== LINKED LISTS ================================================
dict(
    id="remove-linked-list-elements",
    title="Remove Linked List Elements",
    difficulty="Easy",
    pattern="Linked List — Dummy Node",
    leetcode="https://leetcode.com/problems/remove-linked-list-elements/",
    entry="removeElements",
    arg_types=["list_node", None],
    return_type="list_node",
    description=r"""
Delete **every** node whose value equals `val` from a singly linked list and return the head of what is left.

**Constraints**

- 0 to $10^4$ nodes, `1 <= Node.val <= 50`, `0 <= val <= 50`.

**Arguments:** `head` (list format below) and the integer `val`.

**Example 1:** `head = [1,2,6,3,4,5,6], val = 6` → `[1,2,3,4,5]`

**Example 2:** `head = [7,7,7,7], val = 7` → `[]`

**Example 3:** `head = [], val = 1` → `[]`
""" + LL_FORMAT,
    starter=LN + '''class Solution:
    def removeElements(self, head: Optional[ListNode], val: int) -> Optional[ListNode]:
        pass
''',
    solution='''class Solution:
    def removeElements(self, head, val):
        dummy = ListNode(0, head)
        cur = dummy
        while cur.next:
            if cur.next.val == val:
                cur.next = cur.next.next
            else:
                cur = cur.next
        return dummy.next
''',
    tests=[[[1, 2, 6, 3, 4, 5, 6], 6], [[7, 7, 7, 7], 7], [[], 1], [[1], 1], [[1], 2], [[6, 6, 1, 6, 6, 2, 6], 6],
           [[1, 2, 3], 9], [[1, 2, 2, 1], 2], [[r.randint(1, 5) for _ in range(10000)], 3], [[4] * 5000 + [1], 4]],
    wrong_solutions=[
        '''class Solution:
    def removeElements(self, head, val):
        cur = head
        while cur and cur.next:           # never removes the head
            if cur.next.val == val:
                cur.next = cur.next.next
            else:
                cur = cur.next
        return head
''',
        '''class Solution:
    def removeElements(self, head, val):
        dummy = ListNode(0, head)
        cur = dummy
        while cur.next:
            if cur.next.val == val:
                cur.next = cur.next.next
            cur = cur.next if cur.next else cur     # always advances: skips consecutive matches
            if cur.next is None:
                break
        return dummy.next
''',
    ],
    guide=dict(
        prereqs="Dummy nodes — lesson *Nodes, pointers and the dummy-node trick*.",
        intuition="To unlink a node you must stand on the node **before** it. The head has nothing before it, so put a dummy node there; then every node is deleted the same way.",
        hints=["Create `dummy = ListNode(0, head)` and walk with `cur` starting at the dummy.",
               "Look one node ahead: if `cur.next.val == val`, bypass it with `cur.next = cur.next.next`.",
               "After deleting, do **not** advance `cur` — the new `cur.next` might also need deleting."],
        brute_force="Copy the values that are not `val` into a Python list and build a new linked list: O(n) time but O(n) extra memory.",
        approach="`[7,7,7]`, val 7: dummy→7→7→7. cur = dummy: next is 7 → bypass (dummy→7→7); still at dummy: bypass; bypass again; `cur.next` is None → stop. Return `dummy.next` = None, i.e. `[]`.",
        complexity="Time O(n), space O(1).",
        pitfalls="- Advancing after a deletion skips the node that slid into place.\n- Returning `head` (it may have been deleted) instead of `dummy.next`.",
        follow_up="Delete Node in a Linked List (237), Remove Duplicates from Sorted List II (82).",
    ),
),
dict(
    id="remove-duplicates-from-sorted-list",
    title="Remove Duplicates from Sorted List",
    difficulty="Easy",
    pattern="Linked List — Pointer Rewiring",
    leetcode="https://leetcode.com/problems/remove-duplicates-from-sorted-list/",
    entry="deleteDuplicates",
    arg_types=["list_node"],
    return_type="list_node",
    description=r"""
A linked list is sorted in non-decreasing order. Remove repeated values so that each value appears exactly
**once**, keeping the list sorted, and return the head.

**Constraints**

- 0 to 300 nodes classically (judge: up to 10,000), `-100 <= Node.val <= 100`, sorted ascending.

**Example 1:** `head = [1,1,2]` → `[1,2]`

**Example 2:** `head = [1,1,2,3,3]` → `[1,2,3]`
""" + LL_FORMAT,
    starter=LN + '''class Solution:
    def deleteDuplicates(self, head: Optional[ListNode]) -> Optional[ListNode]:
        pass
''',
    solution='''class Solution:
    def deleteDuplicates(self, head):
        cur = head
        while cur and cur.next:
            if cur.next.val == cur.val:
                cur.next = cur.next.next
            else:
                cur = cur.next
        return head
''',
    tests=[[[1, 1, 2]], [[1, 1, 2, 3, 3]], [[]], [[5]], [[2, 2, 2, 2]], [[1, 2, 3]], [[-3, -3, 0, 0, 0, 7]],
           [sorted(r.randint(-100, 100) for _ in range(10000))], [[0] * 3000 + [1] * 3000]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def deleteDuplicates(self, head):
        cur = head
        while cur and cur.next:
            if cur.next.val == cur.val:
                cur.next = cur.next.next
            cur = cur.next                 # always advances: leaves triples as pairs
        return head
''',
    ],
    guide=dict(
        prereqs="Deleting the node after a given node.",
        intuition="Because the list is sorted, equal values sit next to each other. Stand on a node and keep deleting its successor while the successor has the same value.",
        hints=["Compare `cur.val` with `cur.next.val`.", "If equal, bypass the next node; otherwise move forward.", "Only advance when you did not delete."],
        brute_force="Collect values into a set, sort, rebuild: O(n log n) and ignores the sortedness.",
        approach="`[1,1,1,2]`: at first 1, next is 1 → delete; next is 1 again → delete; next is 2 → advance; end. Result `[1,2]`. The head is never removed, so no dummy is needed.",
        complexity="Time O(n), space O(1).",
        pitfalls="Advancing after a deletion leaves one duplicate behind in runs of three or more.",
        follow_up="Remove Duplicates from Sorted List II (82): delete *all* copies of repeated values — needs a dummy node.",
    ),
),
dict(
    id="odd-even-linked-list",
    title="Odd Even Linked List",
    difficulty="Medium",
    pattern="Linked List — Two Chains",
    leetcode="https://leetcode.com/problems/odd-even-linked-list/",
    entry="oddEvenList",
    arg_types=["list_node"],
    return_type="list_node",
    description=r"""
Regroup a linked list so that all nodes at **odd positions** (1st, 3rd, 5th, …) come first, followed by all
nodes at **even positions** (2nd, 4th, …). Positions refer to the place in the list, not the values. Inside
each group the original relative order must be kept. Use O(1) extra space and O(n) time.

**Constraints**

- 0 to $10^4$ nodes, `-10^6 <= Node.val <= 10^6`.

**Example 1:** `head = [1,2,3,4,5]` → `[1,3,5,2,4]`

**Example 2:** `head = [2,1,3,5,6,4,7]` → `[2,3,6,7,1,5,4]`
""" + LL_FORMAT,
    starter=LN + '''class Solution:
    def oddEvenList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        pass
''',
    solution='''class Solution:
    def oddEvenList(self, head):
        if not head:
            return head
        odd, even = head, head.next
        even_head = even
        while even and even.next:
            odd.next = even.next
            odd = odd.next
            even.next = odd.next
            even = even.next
        odd.next = even_head
        return head
''',
    tests=[[[1, 2, 3, 4, 5]], [[2, 1, 3, 5, 6, 4, 7]], [[]], [[1]], [[1, 2]], [[1, 2, 3]], [[1, 2, 3, 4]],
           [[4, 4, 4, 4, 4, 4]], [list(range(10000))], [list(range(9999))]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def oddEvenList(self, head):
        # groups by VALUE parity instead of position
        vals = []
        while head:
            vals.append(head.val)
            head = head.next
        vals = [v for v in vals if v % 2] + [v for v in vals if v % 2 == 0]
        dummy = t = ListNode()
        for v in vals:
            t.next = ListNode(v)
            t = t.next
        return dummy.next
''',
    ],
    guide=dict(
        prereqs="Rewiring `next` pointers; keeping two tails.",
        intuition="Unzip the list into two chains — odd-position nodes and even-position nodes — by letting each node skip over its neighbour, then attach the even chain after the odd chain.",
        hints=["Keep `odd` and `even` pointers plus `even_head` to remember where the even chain starts.",
               "`odd.next = even.next` jumps the odd pointer over an even node; then `even.next = odd.next` does the same for even.",
               "Loop while `even and even.next`; finally `odd.next = even_head`."],
        brute_force="Collect nodes into two Python lists by index parity and relink: O(n) extra space.",
        approach="`[1,2,3,4,5]`: odd=1, even=2. Step 1: 1→3, odd=3; 2→4, even=4. Step 2: 3→5, odd=5; 4→None, even=None. Join: 5→2. Result `1,3,5,2,4`.",
        complexity="Time O(n), space O(1).",
        pitfalls="- Grouping by value parity.\n- Forgetting to save `even_head`.\n- Loop condition on `odd` instead of `even` (crashes on even lengths).",
        follow_up="Partition List (86) uses the same 'two chains, then join' idea.",
    ),
),
dict(
    id="swap-nodes-in-pairs",
    title="Swap Nodes in Pairs",
    difficulty="Medium",
    pattern="Linked List — Group Reversal",
    leetcode="https://leetcode.com/problems/swap-nodes-in-pairs/",
    entry="swapPairs",
    arg_types=["list_node"],
    return_type="list_node",
    description=r"""
Swap every two neighbouring nodes of a linked list and return the new head: the 1st and 2nd trade places,
the 3rd and 4th trade places, and so on. If the length is odd, the last node stays where it is. Rewire the
nodes; do not change their values.

**Constraints**

- 0 to 100 nodes classically (judge: up to 10,000), `0 <= Node.val <= 100`.

**Example 1:** `head = [1,2,3,4]` → `[2,1,4,3]`

**Example 2:** `head = [1,2,3]` → `[2,1,3]`
""" + LL_FORMAT,
    starter=LN + '''class Solution:
    def swapPairs(self, head: Optional[ListNode]) -> Optional[ListNode]:
        pass
''',
    solution='''class Solution:
    def swapPairs(self, head):
        dummy = ListNode(0, head)
        prev = dummy
        while prev.next and prev.next.next:
            a, b = prev.next, prev.next.next
            a.next = b.next
            b.next = a
            prev.next = b
            prev = a
        return dummy.next
''',
    tests=[[[1, 2, 3, 4]], [[1, 2, 3]], [[]], [[1]], [[1, 2]], [[5, 5, 6, 6, 7]], [list(range(10000))], [list(range(9999))]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def swapPairs(self, head):
        # swaps the first pair only
        if head and head.next:
            b = head.next
            head.next = b.next
            b.next = head
            return b
        return head
''',
    ],
    guide=dict(
        prereqs="Dummy node; *Reverse Nodes in k-Group* is the general version (k = 2).",
        intuition="For each pair `a → b`, three arrows change: the node before the pair must point to `b`, `b` must point to `a`, and `a` must point to whatever followed `b`.",
        hints=["Use a dummy so the first pair has a 'node before'.", "Name the nodes: `prev → a → b → rest`.", "Set `a.next = b.next; b.next = a; prev.next = b`, then `prev = a`."],
        brute_force="Swap the *values* of each pair — easy, but the problem asks you to move nodes.",
        approach="`D→1→2→3→4`: pair (1,2): 1→3, 2→1, D→2; prev = 1. Pair (3,4): 3→None, 4→3, 1→4. Result `2,1,4,3`.",
        complexity="Time O(n), space O(1).",
        pitfalls="Updating the arrows in an order that loses `b.next`; forgetting to reconnect the previous pair.",
        follow_up="Recursive version: `head.next = swap(second.next); second.next = head; return second`.",
    ),
),
dict(
    id="rotate-list",
    title="Rotate List",
    difficulty="Medium",
    pattern="Linked List — Make a Ring, Cut It",
    leetcode="https://leetcode.com/problems/rotate-list/",
    entry="rotateRight",
    arg_types=["list_node", None],
    return_type="list_node",
    description=r"""
Rotate a linked list to the right by `k` places: each rotation moves the last node to the front.

**Constraints**

- 0 to 500 nodes classically (judge: up to 10,000), `-100 <= Node.val <= 100`, `0 <= k <= 2 * 10^9`.

**Arguments:** `head` and the integer `k` (which can be far larger than the length).

**Example 1:** `head = [1,2,3,4,5], k = 2` → `[4,5,1,2,3]`

**Example 2:** `head = [0,1,2], k = 4` → `[2,0,1]`
""" + LL_FORMAT,
    starter=LN + '''class Solution:
    def rotateRight(self, head: Optional[ListNode], k: int) -> Optional[ListNode]:
        pass
''',
    solution='''class Solution:
    def rotateRight(self, head, k):
        if not head:
            return head
        n, tail = 1, head
        while tail.next:
            tail = tail.next
            n += 1
        k %= n
        if k == 0:
            return head
        tail.next = head                 # close the ring
        new_tail = head
        for _ in range(n - k - 1):
            new_tail = new_tail.next
        new_head = new_tail.next
        new_tail.next = None             # cut it
        return new_head
''',
    tests=[[[1, 2, 3, 4, 5], 2], [[0, 1, 2], 4], [[], 3], [[1], 99], [[1, 2], 0], [[1, 2], 2], [[1, 2, 3], 2000000000],
           [list(range(10000)), 1], [list(range(10000)), 12345], [[7, 7, 8], 1]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def rotateRight(self, head, k):
        # rotates LEFT by k
        if not head:
            return head
        n, tail = 1, head
        while tail.next:
            tail = tail.next
            n += 1
        k %= n
        if k == 0:
            return head
        tail.next = head
        new_tail = head
        for _ in range(k - 1):
            new_tail = new_tail.next
        new_head = new_tail.next
        new_tail.next = None
        return new_head
''',
    ],
    guide=dict(
        prereqs="Counting the length; gap pointers.",
        intuition="Rotating by the full length changes nothing, so only `k % n` matters. Join the tail to the head to make a ring, then cut the ring `k` nodes before the old tail.",
        hints=["Find the length `n` and the tail in one walk.", "Reduce `k %= n`; if 0, return the list unchanged.", "The new tail is node number `n - k` (1-based); the node after it is the new head."],
        brute_force="Perform k single rotations, each O(n): O(n·k) — hopeless for k = 2·10⁹.",
        approach="`[1,2,3,4,5], k=2`: n = 5, ring 5→1. New tail = 3rd node (5 − 2); new head = 4; cut 3→None. Result `4,5,1,2,3`.",
        complexity="Time O(n), space O(1).",
        pitfalls="- Not reducing k modulo n.\n- Empty list (modulo by zero).\n- Rotating left instead of right.",
        follow_up="Rotate Array (189) — the array analogue with three reversals.",
    ),
),
dict(
    id="partition-list",
    title="Partition List",
    difficulty="Medium",
    pattern="Linked List — Two Chains",
    leetcode="https://leetcode.com/problems/partition-list/",
    entry="partition",
    arg_types=["list_node", None],
    return_type="list_node",
    description=r"""
Rearrange a linked list around a value `x`: every node with a value **less than** `x` must come before every
node with a value **greater than or equal to** `x`. Within each of the two groups, nodes keep their original
relative order (a *stable* partition).

**Constraints**

- 0 to 200 nodes classically (judge: up to 10,000), `-100 <= Node.val <= 100`, `-200 <= x <= 200`.

**Example 1:** `head = [1,4,3,2,5,2], x = 3` → `[1,2,2,4,3,5]`

**Example 2:** `head = [2,1], x = 2` → `[1,2]`
""" + LL_FORMAT,
    starter=LN + '''class Solution:
    def partition(self, head: Optional[ListNode], x: int) -> Optional[ListNode]:
        pass
''',
    solution='''class Solution:
    def partition(self, head, x):
        small = s = ListNode()
        large = g = ListNode()
        while head:
            if head.val < x:
                s.next = head
                s = head
            else:
                g.next = head
                g = head
            head = head.next
        g.next = None
        s.next = large.next
        return small.next
''',
    tests=[[[1, 4, 3, 2, 5, 2], 3], [[2, 1], 2], [[], 0], [[1], 0], [[1], 2], [[3, 3, 3], 3], [[5, 4, 3, 2, 1], 3],
           [[r.randint(-100, 100) for _ in range(10000)], 0], [[1, 2, 3], 200]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def partition(self, head, x):
        vals = []
        while head:
            vals.append(head.val)
            head = head.next
        vals.sort()                       # sorting is not a stable partition
        dummy = t = ListNode()
        for v in vals:
            t.next = ListNode(v)
            t = t.next
        return dummy.next
''',
    ],
    guide=dict(
        prereqs="Dummy + tail building — lesson 1.",
        intuition="Deal the nodes into two piles as you walk: 'smaller than x' and 'the rest'. Each pile is a list built with its own dummy and tail. At the end, glue the second pile after the first.",
        hints=["Two dummy nodes, two tails.", "Append each node to the correct tail, in order.", "Terminate the second list with `None` before joining — otherwise you may leave a cycle."],
        brute_force="Collect values into two Python lists and rebuild: O(n) extra space.",
        approach="`[1,4,3,2,5,2], x=3`: small pile 1,2,2; large pile 4,3,5. Join → `1,2,2,4,3,5`.",
        complexity="Time O(n), space O(1).",
        pitfalls="Forgetting `g.next = None`: the last large node may still point at a node that moved to the small pile, creating a cycle.",
        follow_up="This is the partition step of quicksort on linked lists.",
    ),
),
dict(
    id="sort-list",
    title="Sort List",
    difficulty="Medium",
    pattern="Linked List — Merge Sort",
    leetcode="https://leetcode.com/problems/sort-list/",
    entry="sortList",
    arg_types=["list_node"],
    return_type="list_node",
    description=r"""
Sort a linked list in ascending order and return its head. Aim for O(n log n) time.

**Constraints**

- 0 to $5 \cdot 10^4$ nodes (judge: up to 10,000), `-10^5 <= Node.val <= 10^5`.

**Example 1:** `head = [4,2,1,3]` → `[1,2,3,4]`

**Example 2:** `head = [-1,5,3,4,0]` → `[-1,0,3,4,5]`
""" + LL_FORMAT,
    starter=LN + '''class Solution:
    def sortList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        pass
''',
    solution='''class Solution:
    def sortList(self, head):
        if not head or not head.next:
            return head
        slow, fast = head, head.next
        while fast and fast.next:
            slow, fast = slow.next, fast.next.next
        mid, slow.next = slow.next, None
        a, b = self.sortList(head), self.sortList(mid)
        dummy = tail = ListNode()
        while a and b:
            if a.val <= b.val:
                tail.next, a = a, a.next
            else:
                tail.next, b = b, b.next
            tail = tail.next
        tail.next = a or b
        return dummy.next
''',
    tests=[[[4, 2, 1, 3]], [[-1, 5, 3, 4, 0]], [[]], [[1]], [[2, 1]], [[3, 3, 3]], [[5, 4, 3, 2, 1]],
           [[r.randint(-10 ** 5, 10 ** 5) for _ in range(10000)]], [list(range(5000, 0, -1))]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def sortList(self, head):
        # one bubble pass only
        cur = head
        while cur and cur.next:
            if cur.val > cur.next.val:
                cur.val, cur.next.val = cur.next.val, cur.val
            cur = cur.next
        return head
''',
    ],
    guide=dict(
        prereqs="Middle of a list (fast/slow) and merging two sorted lists — lessons 2 and 3.",
        intuition="Merge sort fits linked lists perfectly: split at the middle, sort each half recursively, merge the two sorted halves by rewiring.",
        hints=["Base case: 0 or 1 nodes are already sorted.", "Use the first-middle variant (`fast = head.next`) and **cut** the list there.", "Merge with dummy + tail."],
        brute_force="Copy values to an array, sort, write back: O(n log n) time, O(n) space — or insertion sort on the list: O(n²).",
        approach="`[4,2,1,3]` → split `[4,2]` and `[1,3]` → `[2,4]` and `[1,3]` → merge `1,2,3,4`. Recursion depth is log₂ n (about 14 for 10,000 nodes).",
        complexity="Time O(n log n). Space O(log n) for the recursion (a bottom-up version reaches O(1)).",
        pitfalls="- Using `fast = head` for the split: a 2-node list never shrinks → infinite recursion.\n- Forgetting to cut the first half.",
        follow_up="Bottom-up merge sort (merge runs of size 1, 2, 4, …) for true O(1) extra space; Insertion Sort List (147).",
    ),
),
dict(
    id="reverse-linked-list-ii",
    title="Reverse Linked List II",
    difficulty="Medium",
    pattern="Linked List — Segment Reversal",
    leetcode="https://leetcode.com/problems/reverse-linked-list-ii/",
    entry="reverseBetween",
    arg_types=["list_node", None, None],
    return_type="list_node",
    description=r"""
Reverse only the part of a linked list between positions `left` and `right` (1-indexed, inclusive) and
return the head. Nodes outside that range stay where they are.

**Constraints**

- The list has `n` nodes, `1 <= n <= 500` classically (judge: up to 10,000); `1 <= left <= right <= n`.

**Example 1:** `head = [1,2,3,4,5], left = 2, right = 4` → `[1,4,3,2,5]`

**Example 2:** `head = [5], left = 1, right = 1` → `[5]`
""" + LL_FORMAT,
    starter=LN + '''class Solution:
    def reverseBetween(self, head: Optional[ListNode], left: int, right: int) -> Optional[ListNode]:
        pass
''',
    solution='''class Solution:
    def reverseBetween(self, head, left, right):
        dummy = ListNode(0, head)
        before = dummy
        for _ in range(left - 1):
            before = before.next
        prev, cur = None, before.next
        for _ in range(right - left + 1):
            cur.next, prev, cur = prev, cur, cur.next
        before.next.next = cur        # old first of segment -> node after segment
        before.next = prev            # node before segment -> old last of segment
        return dummy.next
''',
    tests=[[[1, 2, 3, 4, 5], 2, 4], [[5], 1, 1], [[1, 2], 1, 2], [[1, 2, 3], 1, 3], [[1, 2, 3], 1, 2], [[1, 2, 3], 2, 3],
           [[1, 2, 3, 4], 3, 3], [list(range(10000)), 1, 10000], [list(range(10000)), 2500, 7500]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def reverseBetween(self, head, left, right):
        # no dummy: breaks when left == 1
        before = head
        for _ in range(left - 2):
            before = before.next
        prev, cur = None, before.next
        for _ in range(right - left + 1):
            if cur is None:
                break
            cur.next, prev, cur = prev, cur, cur.next
        if before.next:
            before.next.next = cur
        before.next = prev
        return head
''',
    ],
    guide=dict(
        prereqs="*Reverse Linked List*; segment reversal — lesson 3.",
        intuition="Walk to the node just before the segment, reverse exactly `right - left + 1` nodes with the usual three-pointer loop, then reconnect the two ends.",
        hints=["A dummy node handles `left = 1`.", "After the loop, `prev` is the new first node of the segment and `cur` is the node after it.", "`before.next` still points at the segment's *old first* node, which is now its last: link it to `cur`, then set `before.next = prev`."],
        brute_force="Copy values to an array, reverse the slice, write back: O(n) extra space.",
        approach="`[1,2,3,4,5]`, 2..4: before = 1. Reverse 2,3,4 → prev = 4 (4→3→2), cur = 5. `2.next = 5`, `1.next = 4` → `1,4,3,2,5`.",
        complexity="Time O(n), space O(1), one pass.",
        pitfalls="Reconnecting in the wrong order (overwrite `before.next` first and you lose the old first node).",
        follow_up="Reverse Nodes in k-Group applies this to every block of k.",
    ),
),
dict(
    id="maximum-twin-sum-of-a-linked-list",
    title="Maximum Twin Sum of a Linked List",
    difficulty="Medium",
    pattern="Linked List — Middle + Reverse",
    leetcode="https://leetcode.com/problems/maximum-twin-sum-of-a-linked-list/",
    entry="pairSum",
    arg_types=["list_node"],
    description=r"""
In a linked list with an **even** number of nodes `n`, node `i` (0-indexed) and node `n - 1 - i` are *twins*:
first with last, second with second-to-last, and so on. The twin sum is the sum of the two values. Return
the largest twin sum.

**Constraints**

- `n` is even, `2 <= n <= 10^5` (judge: up to 10,000), `1 <= Node.val <= 10^5`.

**Example 1:** `head = [5,4,2,1]` → `6` (5+1 and 4+2 both give 6)

**Example 2:** `head = [4,2,2,3]` → `7`

**Example 3:** `head = [1,100000]` → `100001`
""" + LL_FORMAT,
    starter=LN + '''class Solution:
    def pairSum(self, head: Optional[ListNode]) -> int:
        pass
''',
    solution='''class Solution:
    def pairSum(self, head):
        slow = fast = head
        while fast and fast.next:
            slow, fast = slow.next, fast.next.next
        prev = None
        while slow:
            slow.next, prev, slow = prev, slow, slow.next
        best = 0
        while prev:
            best = max(best, head.val + prev.val)
            head, prev = head.next, prev.next
        return best
''',
    tests=[[[5, 4, 2, 1]], [[4, 2, 2, 3]], [[1, 100000]], [[1, 1]], [[1, 9, 9, 1]], [[10, 1, 1, 1, 1, 2]],
           [[r.randint(1, 10 ** 5) for _ in range(10000)]], [[3, 8, 1, 1, 1, 1]]],
    wrong_solutions=[
        '''class Solution:
    def pairSum(self, head):
        best = 0                      # adjacent pairs, not twins
        while head and head.next:
            best = max(best, head.val + head.next.val)
            head = head.next.next
        return best
''',
    ],
    guide=dict(
        prereqs="Middle (fast/slow) and reversal; same skeleton as *Palindrome Linked List*.",
        intuition="Twins are mirror images around the middle. Reverse the second half; then the first half and the reversed second half line up twin against twin.",
        hints=["Find the start of the second half with fast/slow.", "Reverse it in place.", "Walk both halves together, tracking the largest sum."],
        brute_force="Copy values to an array and use two indices from both ends: O(n) extra space — a perfectly good first answer.",
        approach="`[4,2,2,3]`: second half `2,3` reversed → `3,2`. Sums: 4+3 = 7, 2+2 = 4 → 7.",
        complexity="Time O(n), space O(1).",
        pitfalls="Pairing neighbours instead of mirror positions.",
        follow_up="Palindrome Linked List, Reorder List — same three-step composition.",
    ),
),
dict(
    id="design-linked-list",
    title="Design Linked List",
    difficulty="Medium",
    pattern="Linked List — Design",
    leetcode="https://leetcode.com/problems/design-linked-list/",
    kind="class",
    entry="MyLinkedList",
    description=r"""
Implement your own linked list class (singly or doubly linked — your choice) with 0-based indices:

- `MyLinkedList()` — empty list.
- `get(index)` — value of the node at `index`, or `-1` if the index is invalid.
- `addAtHead(val)` — insert a node before the first node.
- `addAtTail(val)` — append a node at the end.
- `addAtIndex(index, val)` — insert before the node currently at `index`. If `index` equals the length, append.
  If `index` is greater than the length, do nothing.
- `deleteAtIndex(index)` — delete the node at `index` if the index is valid.

**Constraints**

- `0 <= index, val <= 1000`, at most 2000 calls. Do not use a built-in list as the storage in spirit —
  the judge cannot check this, but the exercise is the pointer work.

**Judge input format:** two lists — operation names and argument lists; output is the list of return values
(`None` for everything except `get`).

**Example:** `["MyLinkedList","addAtHead","addAtTail","addAtIndex","get","deleteAtIndex","get"]`,
`[[],[1],[3],[1,2],[1],[1],[1]]` → `[None,None,None,None,2,None,3]`
""",
    starter='''class MyLinkedList:

    def __init__(self):
        pass

    def get(self, index: int) -> int:
        pass

    def addAtHead(self, val: int) -> None:
        pass

    def addAtTail(self, val: int) -> None:
        pass

    def addAtIndex(self, index: int, val: int) -> None:
        pass

    def deleteAtIndex(self, index: int) -> None:
        pass
''',
    solution='''class _N:
    __slots__ = ("val", "next")

    def __init__(self, val=0, nxt=None):
        self.val, self.next = val, nxt


class MyLinkedList:
    def __init__(self):
        self.dummy = _N()
        self.size = 0

    def _before(self, index):            # node just before position index
        cur = self.dummy
        for _ in range(index):
            cur = cur.next
        return cur

    def get(self, index):
        if index < 0 or index >= self.size:
            return -1
        return self._before(index).next.val

    def addAtHead(self, val):
        self.addAtIndex(0, val)

    def addAtTail(self, val):
        self.addAtIndex(self.size, val)

    def addAtIndex(self, index, val):
        if index < 0 or index > self.size:
            return
        prev = self._before(index)
        prev.next = _N(val, prev.next)
        self.size += 1

    def deleteAtIndex(self, index):
        if index < 0 or index >= self.size:
            return
        prev = self._before(index)
        prev.next = prev.next.next
        self.size -= 1
''',
    tests=[
        [["MyLinkedList", "addAtHead", "addAtTail", "addAtIndex", "get", "deleteAtIndex", "get"], [[], [1], [3], [1, 2], [1], [1], [1]]],
        [["MyLinkedList", "get", "deleteAtIndex", "addAtIndex", "get"], [[], [0], [0], [1, 5], [0]]],
        [["MyLinkedList", "addAtIndex", "get", "get", "addAtIndex", "get"], [[], [0, 10], [0], [1], [1, 20], [1]]],
        [["MyLinkedList", "addAtHead", "addAtHead", "addAtHead", "get", "get", "get", "get"], [[], [1], [2], [3], [0], [1], [2], [3]]],
        [["MyLinkedList", "addAtTail", "addAtTail", "deleteAtIndex", "get", "deleteAtIndex", "get", "addAtTail", "get"],
         [[], [1], [2], [0], [0], [0], [0], [9], [0]]],
        [["MyLinkedList", "addAtHead", "deleteAtIndex", "deleteAtIndex", "get"], [[], [4], [1], [0], [0]]],
        [["MyLinkedList", "addAtHead", "addAtIndex", "addAtIndex", "get", "get", "get"], [[], [2], [0, 1], [2, 3], [0], [1], [2]]],
        _mll_ops(600, 1), _mll_ops(1500, 2),
    ],
    examples=1,
    wrong_solutions=[
        '''class MyLinkedList:
    def __init__(self):
        self.a = []

    def get(self, index):
        return self.a[index] if 0 <= index < len(self.a) else -1

    def addAtHead(self, val):
        self.a.insert(0, val)

    def addAtTail(self, val):
        self.a.append(val)

    def addAtIndex(self, index, val):
        self.a.insert(index, val)          # inserts even when index > length

    def deleteAtIndex(self, index):
        if 0 <= index < len(self.a):
            del self.a[index]
''',
        '''class MyLinkedList:
    def __init__(self):
        self.a = []

    def get(self, index):
        return self.a[index] if 0 <= index < len(self.a) else -1

    def addAtHead(self, val):
        self.a.insert(0, val)

    def addAtTail(self, val):
        self.a.append(val)

    def addAtIndex(self, index, val):
        if index < len(self.a):            # refuses index == length (should append)
            self.a.insert(index, val)

    def deleteAtIndex(self, index):
        if 0 <= index < len(self.a):
            del self.a[index]
''',
    ],
    guide=dict(
        prereqs="Insert-after and delete-after; dummy node — lesson 1.",
        intuition="Every operation is 'walk to the node just before position `index`, then insert or delete after it'. A dummy head makes position 0 ordinary, and a `size` counter makes index validation one comparison.",
        hints=["Keep `self.dummy` and `self.size`.", "Write one helper that returns the node before a position.", "`addAtHead` and `addAtTail` are `addAtIndex(0, …)` and `addAtIndex(size, …)`."],
        brute_force="Wrap a Python list — passes, but skips the point of the exercise.",
        approach="Example: addAtHead(1) → [1]; addAtTail(3) → [1,3]; addAtIndex(1,2) → [1,2,3]; get(1) = 2; deleteAtIndex(1) → [1,3]; get(1) = 3.",
        complexity="`get`, `addAtIndex`, `deleteAtIndex`, `addAtTail`: O(index) (O(n) worst). `addAtHead`: O(1). A doubly linked version with a tail sentinel makes `addAtTail` O(1) and halves the walk.",
        pitfalls="- `addAtIndex` with `index == size` must append; `index > size` must do nothing.\n- Forgetting to update `size`.\n- `get` on an invalid index returns -1, not an exception.",
        follow_up="Doubly linked version with header/trailer sentinels (Goodrich §7.3); it is the backbone of LRU Cache.",
    ),
),
# ================================== TREES ====================================================
dict(
    id="binary-tree-preorder-traversal",
    title="Binary Tree Preorder Traversal",
    difficulty="Easy",
    pattern="Trees — DFS (iterative)",
    leetcode="https://leetcode.com/problems/binary-tree-preorder-traversal/",
    entry="preorderTraversal",
    arg_types=["tree"],
    description=r"""
Return the node values of a binary tree in **preorder**: a node first, then its whole left subtree, then its
whole right subtree.

**Constraints**

- 0 to 100 nodes classically (judge: up to 5,000), `-100 <= Node.val <= 100`.
- Follow-up: do it without recursion.

**Example 1:** `root = [1,None,2,3]` → `[1,2,3]`

**Example 2:** `root = [1,2,3,4,5,None,8,None,None,6,7,9]` → `[1,2,4,5,6,7,3,8,9]`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def preorderTraversal(self, root: Optional[TreeNode]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def preorderTraversal(self, root):
        out, stack = [], [root]
        while stack:
            node = stack.pop()
            if node:
                out.append(node.val)
                stack.append(node.right)
                stack.append(node.left)
        return out
''',
    tests=[[[1, None, 2, 3]], [[1, 2, 3, 4, 5, None, 8, None, None, 6, 7, 9]], [[]], [[1]], [[1, 2]], [[1, None, 2]],
           [SKEW_L], [SKEW_R], [BIG], [complete(range(2000))]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def preorderTraversal(self, root):
        out, stack = [], [root]
        while stack:
            node = stack.pop()
            if node:
                out.append(node.val)
                stack.append(node.left)      # pushes left first -> right is visited first
                stack.append(node.right)
        return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Traversals: DFS (pre/in/post) and BFS*.",
        intuition="A stack hands back the most recently added item. Pop a node, record it, then push its right child and its left child — the left child is on top, so it is handled next, exactly as preorder demands.",
        hints=["Recursive: visit, recurse left, recurse right.", "Iterative: one stack, start with the root.", "Push **right before left**."],
        brute_force="The recursive version is already O(n); its only limit is recursion depth on very deep trees.",
        approach="`[1,None,2,3]`: pop 1 (out [1]); push its right child 2, then its left child None. Pop None (skip). Pop 2 (out [1,2]), push None, push 3. Pop 3 → `[1,2,3]`.",
        complexity="Time O(n), space O(h).",
        pitfalls="Pushing left before right reverses the sibling order.",
        follow_up="Inorder (94) and postorder (145); N-ary preorder (589).",
    ),
),
dict(
    id="binary-tree-postorder-traversal",
    title="Binary Tree Postorder Traversal",
    difficulty="Easy",
    pattern="Trees — DFS (iterative)",
    leetcode="https://leetcode.com/problems/binary-tree-postorder-traversal/",
    entry="postorderTraversal",
    arg_types=["tree"],
    description=r"""
Return the node values of a binary tree in **postorder**: the whole left subtree, then the whole right
subtree, then the node itself.

**Constraints**

- 0 to 100 nodes classically (judge: up to 5,000), `-100 <= Node.val <= 100`.
- Follow-up: do it without recursion.

**Example 1:** `root = [1,None,2,3]` → `[3,2,1]`

**Example 2:** `root = [1,2,3,4,5,None,8,None,None,6,7,9]` → `[4,6,7,5,2,9,8,3,1]`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def postorderTraversal(self, root: Optional[TreeNode]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def postorderTraversal(self, root):
        out, stack = [], [(root, False)]
        while stack:
            node, done = stack.pop()
            if not node:
                continue
            if done:
                out.append(node.val)
            else:
                stack.append((node, True))
                stack.append((node.right, False))
                stack.append((node.left, False))
        return out
''',
    tests=[[[1, None, 2, 3]], [[1, 2, 3, 4, 5, None, 8, None, None, 6, 7, 9]], [[]], [[1]], [[1, 2]], [[1, None, 2]],
           [SKEW_L], [SKEW_R], [BIG], [complete(range(2000))]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def postorderTraversal(self, root):
        out, stack = [], [root]
        while stack:
            node = stack.pop()
            if node:
                out.append(node.val)
                stack.append(node.right)
                stack.append(node.left)
        return out[::-1]                  # reverse of node-left-right = right-left-node (wrong)
''',
    ],
    guide=dict(
        prereqs="Lesson *Traversals*; iterative preorder.",
        intuition="A node may only be output after both subtrees are finished. Push each node twice: the first time you pop it, schedule 'me again, later' underneath its children; the second time, output it.",
        hints=["Recursive: left, right, visit.", "Trick: a 'node, right, left' traversal reversed is postorder.", "General: a stack of `(node, visited_flag)` pairs."],
        brute_force="Recursive version — already O(n).",
        approach="`[1,None,2,3]`: pop (1,F) → push (1,T),(2,F),(None). Pop None. Pop (2,F) → push (2,T),(None),(3,F). Pop (3,F) → push (3,T), Nones. Pop (3,T) out [3]; (2,T) out [3,2]; (1,T) out [3,2,1].",
        complexity="Time O(n) (each node pushed twice), space O(h).",
        pitfalls="Reversing the *ordinary* preorder gives right-left-node, which is not postorder; the preorder you reverse must visit right before left.",
        follow_up="Use the same flag template to compute bottom-up values (heights, sizes) without recursion.",
    ),
),
dict(
    id="symmetric-tree",
    title="Symmetric Tree",
    difficulty="Easy",
    pattern="Trees — Simultaneous DFS",
    leetcode="https://leetcode.com/problems/symmetric-tree/",
    entry="isSymmetric",
    arg_types=["tree"],
    description=r"""
Decide whether a binary tree is a mirror image of itself around its centre line: the left subtree of the
root must be the mirror reflection of the right subtree.

**Constraints**

- 1 to 1000 nodes (judge: up to 4,095), `-100 <= Node.val <= 100`.

**Example 1:** `root = [1,2,2,3,4,4,3]` → `True`

**Example 2:** `root = [1,2,2,None,3,None,3]` → `False`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def isSymmetric(self, root: Optional[TreeNode]) -> bool:
        pass
''',
    solution='''class Solution:
    def isSymmetric(self, root):
        stack = [(root.left, root.right)] if root else []
        while stack:
            a, b = stack.pop()
            if a is None and b is None:
                continue
            if a is None or b is None or a.val != b.val:
                return False
            stack.append((a.left, b.right))
            stack.append((a.right, b.left))
        return True
''',
    tests=[[[1, 2, 2, 3, 4, 4, 3]], [[1, 2, 2, None, 3, None, 3]], [[1]], [[1, 2, 2]], [[1, 2, 3]], [[1, 2, 2, 3, None, None, 3]],
           [[1, 2, 2, None, 3, 3]], [[2, 3, 3, 4, 5, 5, 4, None, None, 8, 9, None, None, 9, 8]], [[1] * 4095], [[1] * 4094 + [2]],
           [[1, 2, 2, 2, None, 2]]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def isSymmetric(self, root):
        def same(a, b):                   # checks the subtrees are IDENTICAL, not mirrored
            if not a and not b:
                return True
            if not a or not b or a.val != b.val:
                return False
            return same(a.left, b.left) and same(a.right, b.right)
        return same(root.left, root.right)
''',
        '''class Solution:
    def isSymmetric(self, root):
        def ino(n):
            return ino(n.left) + [n.val] + ino(n.right) if n else []
        v = ino(root)
        return v == v[::-1]               # palindromic inorder is not enough
''',
    ],
    guide=dict(
        prereqs="*Same Tree* — walking two trees together.",
        intuition="Two trees are mirrors when their roots match, and the **left** of one mirrors the **right** of the other (and vice versa). It is *Same Tree* with the children crossed.",
        hints=["Compare `root.left` and `root.right` as a pair.", "For a pair `(a, b)`: both None → fine; one None or different values → not symmetric.", "Next pairs: `(a.left, b.right)` and `(a.right, b.left)`."],
        brute_force="Build the mirrored copy (*Invert Binary Tree*) and compare with the original via *Same Tree*: O(n) time but O(n) extra space.",
        approach="Example 2: pair (2,2) ok → pairs (None, 3) → one is None → False.",
        complexity="Time O(n), space O(h).",
        pitfalls="- Pairing left with left.\n- Relying on a palindromic inorder: `[1,2,2,2,None,2]` has inorder 2,2,1,2,2 but is not symmetric.",
        follow_up="BFS version comparing each level against its reverse (with None markers).",
    ),
),
dict(
    id="merge-two-binary-trees",
    title="Merge Two Binary Trees",
    difficulty="Easy",
    pattern="Trees — Simultaneous DFS",
    leetcode="https://leetcode.com/problems/merge-two-binary-trees/",
    entry="mergeTrees",
    arg_types=["tree", "tree"],
    return_type="tree",
    description=r"""
Lay one binary tree on top of another. Where both trees have a node at the same position, the merged node's
value is the **sum** of the two; where only one tree has a node, that node is used as is. Return the merged
tree.

**Constraints**

- Each tree has 0 to 2000 nodes, `-10^4 <= Node.val <= 10^4`.

**Example 1:** `root1 = [1,3,2,5], root2 = [2,1,3,None,4,None,7]` → `[3,4,5,5,4,None,7]`

**Example 2:** `root1 = [1], root2 = [1,2]` → `[2,2]`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def mergeTrees(self, root1: Optional[TreeNode], root2: Optional[TreeNode]) -> Optional[TreeNode]:
        pass
''',
    solution='''class Solution:
    def mergeTrees(self, root1, root2):
        if not root1:
            return root2
        if not root2:
            return root1
        node = TreeNode(root1.val + root2.val)
        node.left = self.mergeTrees(root1.left, root2.left)
        node.right = self.mergeTrees(root1.right, root2.right)
        return node
''',
    tests=[[[1, 3, 2, 5], [2, 1, 3, None, 4, None, 7]], [[1], [1, 2]], [[], []], [[], [1]], [[1, 2, None, 3], [1, None, 2, None, 3]],
           [[5], [-5]], [random_tree(2000, 31), random_tree(2000, 32)], [skewed(list(range(400)), "left"), skewed(list(range(400)), "right")],
           [complete(range(1000)), complete(range(500))]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def mergeTrees(self, root1, root2):
        if not root1 or not root2:
            return None                    # drops nodes that exist in only one tree
        node = TreeNode(root1.val + root2.val)
        node.left = self.mergeTrees(root1.left, root2.left)
        node.right = self.mergeTrees(root1.right, root2.right)
        return node
''',
    ],
    guide=dict(
        prereqs="Recursion on two trees at once (*Same Tree*).",
        intuition="Merging two trees = merge the roots, then merge the two left subtrees and the two right subtrees. If one side is empty, the answer is the other side unchanged.",
        hints=["Base cases first: if one tree is `None`, return the other.", "Otherwise create a node with the sum.", "Its children are the merges of the corresponding children."],
        brute_force="There is nothing cheaper than visiting the overlapping nodes once.",
        approach="Example 1: roots 1+2 = 3. Left: 3+1 = 4 with children (5, None)→5 and (None, 4)→4. Right: 2+3 = 5 with right child (None, 7)→7.",
        complexity="Time O(min(n, m)) — only overlapping positions are visited. Space O(h).",
        pitfalls="Returning `None` when only one tree is missing a node.",
        follow_up="In-place variant that reuses `root1`'s nodes; iterative version with a stack of pairs.",
    ),
),
dict(
    id="minimum-depth-of-binary-tree",
    title="Minimum Depth of Binary Tree",
    difficulty="Easy",
    pattern="Trees — BFS",
    leetcode="https://leetcode.com/problems/minimum-depth-of-binary-tree/",
    entry="minDepth",
    arg_types=["tree"],
    description=r"""
Return the number of **nodes** on the shortest path from the root down to the nearest **leaf** (a node with
no children). The empty tree has minimum depth 0.

**Constraints**

- 0 to $10^5$ nodes (judge: up to 10,000), `-1000 <= Node.val <= 1000`.

**Example 1:** `root = [3,9,20,None,None,15,7]` → `2`

**Example 2:** `root = [2,None,3,None,4,None,5,None,6]` → `5` (a chain: the only leaf is at the bottom)
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def minDepth(self, root: Optional[TreeNode]) -> int:
        pass
''',
    solution='''class Solution:
    def minDepth(self, root):
        if not root:
            return 0
        q = collections.deque([(root, 1)])
        while q:
            node, d = q.popleft()
            if not node.left and not node.right:
                return d
            if node.left:
                q.append((node.left, d + 1))
            if node.right:
                q.append((node.right, d + 1))
''',
    tests=[[[3, 9, 20, None, None, 15, 7]], [[2, None, 3, None, 4, None, 5, None, 6]], [[]], [[1]], [[1, 2]], [[1, 2, 3, 4, 5]],
           [[1, 2, 3, 4, None, None, 5]], [SKEW_L], [BIG], [complete(range(10000))]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def minDepth(self, root):
        if not root:
            return 0                       # treats a missing child as a leaf at depth 0
        return 1 + min(self.minDepth(root.left), self.minDepth(root.right))
''',
    ],
    guide=dict(
        prereqs="BFS level order; what a leaf is.",
        intuition="BFS reaches nodes in order of depth, so the **first leaf** it meets is the nearest one — stop there.",
        hints=["A node with one child is not a leaf.", "BFS with `(node, depth)` pairs; return at the first node with no children.", "DFS also works: if one child is missing, you must take the other side."],
        brute_force="DFS over the whole tree computing the min over leaves: O(n) even when a leaf is right under the root.",
        approach="Example 2 (chain): BFS walks 2, 3, 4, 5 — none is a leaf — until 6 at depth 5. The buggy `1 + min(left, right)` would answer 1, because the missing left child reports 0.",
        complexity="Time O(n) worst case, but stops early; space O(w).",
        pitfalls="The one-child trap described above — the most famous bug of this problem.",
        follow_up="Maximum Depth (104).",
    ),
),
dict(
    id="path-sum-ii",
    title="Path Sum II",
    difficulty="Medium",
    pattern="Trees — Backtracking",
    leetcode="https://leetcode.com/problems/path-sum-ii/",
    entry="pathSum",
    arg_types=["tree", None],
    compare="unordered",
    description=r"""
List **every** root-to-leaf path whose values add up to `targetSum`. Each path is the list of node values
from the root to the leaf. The paths may be returned in any order.

**Constraints**

- 0 to 5000 nodes, `-1000 <= Node.val <= 1000`, `-1000 <= targetSum <= 1000`.

**Example 1:** `root = [5,4,8,11,None,13,4,7,2,None,None,5,1], targetSum = 22` → `[[5,4,11,2],[5,8,4,5]]`

**Example 2:** `root = [1,2,3], targetSum = 5` → `[]`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def pathSum(self, root: Optional[TreeNode], targetSum: int) -> List[List[int]]:
        pass
''',
    solution='''class Solution:
    def pathSum(self, root, targetSum):
        res, path = [], []
        def dfs(node, rem):
            if not node:
                return
            path.append(node.val)
            rem -= node.val
            if not node.left and not node.right and rem == 0:
                res.append(path[:])
            dfs(node.left, rem)
            dfs(node.right, rem)
            path.pop()
        dfs(root, targetSum)
        return res
''',
    tests=[[[5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1], 22], [[1, 2, 3], 5], [[], 0], [[1, 2], 1], [[1], 1],
           [[0, 0, 0, 0, 0, 0, 0], 0], [[-2, None, -3], -5], [[1, -1, -1, 1, 1, 1, 1], 1], [BIG_POS, 30], [complete([1] * 2047), 11]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def pathSum(self, root, targetSum):
        res, path = [], []
        def dfs(node, rem):
            if not node:
                return
            path.append(node.val)
            rem -= node.val
            if not node.left and not node.right and rem == 0:
                res.append(path)           # appends the SAME list object (no copy)
            dfs(node.left, rem)
            dfs(node.right, rem)
            path.pop()
        dfs(root, targetSum)
        return res
''',
        '''class Solution:
    def pathSum(self, root, targetSum):
        res = []
        def dfs(node, rem, path):
            if not node:
                return
            path = path + [node.val]
            rem -= node.val
            if rem == 0:                   # does not require a leaf
                res.append(path)
            dfs(node.left, rem, path)
            dfs(node.right, rem, path)
        dfs(root, targetSum, [])
        return res
''',
    ],
    guide=dict(
        prereqs="*Path Sum*; backtracking with a shared list — lesson *Returning values up the tree*, §1.",
        intuition="Same walk as *Path Sum*, but also remember the path taken. Keep one list: append on the way down, remove on the way back up. When a leaf completes the sum, save a **copy**.",
        hints=["Carry the remaining sum down.", "Append the node's value before recursing, pop it afterwards.", "`res.append(path[:])` — a copy, because `path` keeps changing."],
        brute_force="Generate every root-to-leaf path as a separate list, then filter by sum: O(n·h) memory even for paths that fail.",
        approach="Example 1: path 5,4,11,7 → sum 27 ✗, pop 7; 5,4,11,2 → 22 ✓ save copy; back up to 5; 5,8,13 ✗; 5,8,4,5 ✓; 5,8,4,1 ✗.",
        complexity="Time O(n) for the walk plus O(h) per saved path (O(n·h) worst case). Space O(h) besides the output.",
        pitfalls="- Saving `path` itself: every saved entry ends up as the same (finally empty) list.\n- Forgetting `path.pop()`.\n- Accepting a non-leaf.",
        follow_up="Path Sum III (437): paths may start and end anywhere going downward — prefix sums in a hash map.",
    ),
),
dict(
    id="sum-root-to-leaf-numbers",
    title="Sum Root to Leaf Numbers",
    difficulty="Medium",
    pattern="Trees — Passing State Down",
    leetcode="https://leetcode.com/problems/sum-root-to-leaf-numbers/",
    entry="sumNumbers",
    arg_types=["tree"],
    description=r"""
Every node holds one digit `0–9`. Reading the digits along a root-to-leaf path gives a decimal number (the
path 1 → 2 → 3 is the number 123). Return the sum of the numbers of **all** root-to-leaf paths.

**Constraints**

- 1 to 1000 nodes (judge: up to 1,023), `0 <= Node.val <= 9`, depth at most 12.

**Example 1:** `root = [1,2,3]` → `25` (12 + 13)

**Example 2:** `root = [4,9,0,5,1]` → `1026` (495 + 491 + 40)
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def sumNumbers(self, root: Optional[TreeNode]) -> int:
        pass
''',
    solution='''class Solution:
    def sumNumbers(self, root):
        total, stack = 0, [(root, 0)]
        while stack:
            node, cur = stack.pop()
            if not node:
                continue
            cur = cur * 10 + node.val
            if not node.left and not node.right:
                total += cur
            stack.append((node.left, cur))
            stack.append((node.right, cur))
        return total
''',
    tests=[[[1, 2, 3]], [[4, 9, 0, 5, 1]], [[0]], [[7]], [[1, 0]], [[1, None, 5]], [[0, 0, 0, 1]], [[9, 9, 9, 9, 9, 9, 9]],
           [BIG_POS], [complete([r.randint(0, 9) for _ in range(1023)])]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def sumNumbers(self, root):
        def dfs(node, cur):
            if not node:
                return cur                 # counts a missing child as a path end
            cur = cur * 10 + node.val
            return dfs(node.left, cur) + dfs(node.right, cur)
        return dfs(root, 0)
''',
    ],
    guide=dict(
        prereqs="Passing state down a DFS (*Path Sum*, *Count Good Nodes*).",
        intuition="Carry the number built so far down the tree: stepping onto a node appends its digit, i.e. `cur = cur * 10 + digit`. At a leaf the number is complete — add it to the total.",
        hints=["State passed down: the number formed by the path so far.", "Update with `cur * 10 + node.val`.", "Add to the answer only at leaves."],
        brute_force="Collect each path as a string, convert with `int`, sum: O(n·h).",
        approach="Example 2: 4 → 49 → 495 (leaf, +495), 491 (leaf, +491); 4 → 40 (leaf, +40). Total 1026.",
        complexity="Time O(n), space O(h).",
        pitfalls="Returning `cur` at `None`: a leaf would be counted twice and one-child nodes would count a phantom path.",
        follow_up="Binary Tree Paths (257), Sum of Root To Leaf Binary Numbers (1022).",
    ),
),
dict(
    id="binary-tree-zigzag-level-order-traversal",
    title="Binary Tree Zigzag Level Order Traversal",
    difficulty="Medium",
    pattern="Trees — BFS",
    leetcode="https://leetcode.com/problems/binary-tree-zigzag-level-order-traversal/",
    entry="zigzagLevelOrder",
    arg_types=["tree"],
    description=r"""
Return the values of a binary tree level by level, but alternate the direction: the first level left to
right, the second right to left, the third left to right again, and so on.

**Constraints**

- 0 to 2000 nodes (judge: up to 5,000), `-100 <= Node.val <= 100`.

**Example 1:** `root = [3,9,20,None,None,15,7]` → `[[3],[20,9],[15,7]]`

**Example 2:** `root = [1,2,3,4,None,None,5]` → `[[1],[3,2],[4,5]]`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def zigzagLevelOrder(self, root: Optional[TreeNode]) -> List[List[int]]:
        pass
''',
    solution='''class Solution:
    def zigzagLevelOrder(self, root):
        res = []
        q = collections.deque([root] if root else [])
        while q:
            level = []
            for _ in range(len(q)):
                node = q.popleft()
                level.append(node.val)
                if node.left:
                    q.append(node.left)
                if node.right:
                    q.append(node.right)
            if len(res) % 2:
                level.reverse()
            res.append(level)
        return res
''',
    tests=[[[3, 9, 20, None, None, 15, 7]], [[1, 2, 3, 4, None, None, 5]], [[]], [[1]], [[1, 2]], [[1, 2, 3, 4, 5, 6, 7, 8]],
           [SKEW_L], [BIG], [complete(range(3000))]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def zigzagLevelOrder(self, root):
        res = []
        q = collections.deque([root] if root else [])
        flip = False
        while q:
            level = []
            for _ in range(len(q)):
                node = q.popleft()
                level.append(node.val)
                kids = (node.right, node.left) if flip else (node.left, node.right)
                for c in kids:              # changing ENQUEUE order scrambles deeper levels
                    if c:
                        q.append(c)
            res.append(level)
            flip = not flip
        return res
''',
    ],
    guide=dict(
        prereqs="*Binary Tree Level Order Traversal*.",
        intuition="Do an ordinary level-order traversal and reverse every second level's list before storing it. Keep the queue itself in normal left-to-right order.",
        hints=["Start from your level-order solution.", "The level's index is `len(res)`.", "Reverse the list when that index is odd."],
        brute_force="Same thing — the reversal adds only O(level size).",
        approach="Example 2: levels `[1]`, `[2,3]`, `[4,5]` → reverse the middle one → `[[1],[3,2],[4,5]]`.",
        complexity="Time O(n), space O(w).",
        pitfalls="Trying to zigzag by changing the order children are enqueued: that changes which nodes are processed first on the *next* level and breaks the grouping (see the wrong solution on `[1,2,3,4,None,None,5]`).",
        follow_up="Use a `deque` per level and `appendleft` on odd levels to avoid the explicit reverse.",
    ),
),
dict(
    id="lowest-common-ancestor-of-a-binary-tree",
    title="Lowest Common Ancestor of a Binary Tree",
    difficulty="Medium",
    pattern="Trees — Return Values Up",
    leetcode="https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/",
    entry="judge",
    arg_types=["tree", None, None],
    description=r"""
In an ordinary binary tree (**not** a search tree — values are in no particular order), find the lowest
common ancestor of two nodes `p` and `q`: the deepest node that has both in its subtree, where a node
belongs to its own subtree.

**Constraints**

- 2 to $10^5$ nodes (judge: up to 3,000), all values **distinct**, `p != q`, both exist in the tree.

**Judge input format:** each test is `root, p, q` with `p` and `q` given as **values**. The adapter at the
bottom of the starter looks up the two `TreeNode` objects, calls your LeetCode-style
`lowestCommonAncestor(root, p, q)` with real nodes, and reports the **value** of the node you return.

**Example 1:** `root = [3,5,1,6,2,0,8,None,None,7,4], p = 5, q = 1` → `3`

**Example 2:** `root = [3,5,1,6,2,0,8,None,None,7,4], p = 5, q = 4` → `5`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def lowestCommonAncestor(self, root: 'TreeNode', p: 'TreeNode', q: 'TreeNode') -> 'TreeNode':
        pass
''' + LCA_ADAPTER,
    solution='''class Solution:
    def lowestCommonAncestor(self, root, p, q):
        if root is None or root is p or root is q:
            return root
        left = self.lowestCommonAncestor(root.left, p, q)
        right = self.lowestCommonAncestor(root.right, p, q)
        if left and right:
            return root
        return left or right
''' + LCA_ADAPTER,
    tests=[[[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 1], [[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 4], [[1, 2], 1, 2],
           [[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 7, 4], [[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 6, 4],
           [[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 7, 8], [[9, 1, 20, 30, 2], 30, 2], [SKEW_R, 100, 400],
           [DISTINCT, 17, 2900], [DISTINCT, 1500, 1501], [DISTINCT, DISTINCT[0], 77]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def lowestCommonAncestor(self, root, p, q):
        # BST shortcut on a tree that is not a BST
        cur = root
        while cur:
            if p.val < cur.val and q.val < cur.val and cur.left:
                cur = cur.left
            elif p.val > cur.val and q.val > cur.val and cur.right:
                cur = cur.right
            else:
                return cur
''' + LCA_ADAPTER,
        '''class Solution:
    def lowestCommonAncestor(self, root, p, q):
        return root
''' + LCA_ADAPTER,
    ],
    guide=dict(
        prereqs="Postorder 'return values up' — lesson *Returning values up the tree*, §6.",
        intuition="Ask each subtree: 'did you see p or q?' If the left subtree reports one and the right subtree reports the other, the current node is where their paths meet — the LCA. If only one side reports something, pass that report up.",
        hints=["Base case: `None`, `p` or `q` → return the node itself.", "Recurse on both children.", "Both non-None → return `root`; otherwise return whichever is non-None."],
        brute_force="Find the root-to-p and root-to-q paths as lists (two DFS passes) and return the last common node: O(n) time, O(h) extra space — a fine alternative answer.",
        approach="Example 2 (p = 5, q = 4): at 3, left call reaches 5 and returns it immediately (it is p) without looking below; right call (subtree of 1) returns None. So 3 returns 5. Correct, because q is guaranteed to exist and must be below 5.",
        complexity="Time O(n), space O(h).",
        pitfalls="- Comparing values with BST logic.\n- Using `==` on values when the tree could contain duplicates — compare nodes with `is`.",
        follow_up="LCA of a BST (235) in O(h); LCA with parent pointers (1650); LCA of deepest leaves (1123).",
    ),
),
dict(
    id="convert-sorted-array-to-binary-search-tree",
    title="Convert Sorted Array to Binary Search Tree",
    difficulty="Easy",
    pattern="Trees — Construction",
    leetcode="https://leetcode.com/problems/convert-sorted-array-to-binary-search-tree/",
    entry="sortedArrayToBST",
    return_type="tree",
    checker=BALANCED_BST_CHECKER,
    description=r"""
Given an integer array sorted in strictly increasing order, build a **height-balanced** binary search tree
containing exactly those values (height-balanced: at every node the two subtrees' heights differ by at most 1).
Several trees are valid; **the judge accepts any tree that is a BST over exactly these values and is
height-balanced.**

**Constraints**

- `1 <= len(nums) <= 10^4`, values strictly increasing, in `[-10^4, 10^4]`.

**Argument:** a plain Python list. The returned tree is checked structurally.

**Example 1:** `nums = [-10,-3,0,5,9]` → e.g. `[0,-10,5,None,-3,None,9]` (or `[0,-3,9,-10,None,5]`)

**Example 2:** `nums = [1,3]` → `[1,None,3]` or `[3,1]`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def sortedArrayToBST(self, nums: List[int]) -> Optional[TreeNode]:
        pass
''',
    solution='''class Solution:
    def sortedArrayToBST(self, nums):
        def build(lo, hi):
            if lo > hi:
                return None
            mid = (lo + hi) // 2
            return TreeNode(nums[mid], build(lo, mid - 1), build(mid + 1, hi))
        return build(0, len(nums) - 1)
''',
    tests=[[[-10, -3, 0, 5, 9]], [[1, 3]], [[1]], [[1, 2, 3]], [[1, 2, 3, 4]], [list(range(7))], [list(range(-50, 50))],
           [list(range(0, 20000, 2))], [list(range(-10000, -9000))]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def sortedArrayToBST(self, nums):
        root = None                        # a chain: valid BST, not balanced
        for v in reversed(nums):
            root = TreeNode(v, None, root)
        return root
''',
        '''class Solution:
    def sortedArrayToBST(self, nums):
        nodes = [TreeNode(v) for v in nums]     # complete tree in array order: balanced, not a BST
        for i, n in enumerate(nodes):
            if 2 * i + 1 < len(nodes):
                n.left = nodes[2 * i + 1]
            if 2 * i + 2 < len(nodes):
                n.right = nodes[2 * i + 2]
        return nodes[0]
''',
    ],
    guide=dict(
        prereqs="BST property; recursion on index ranges — lesson *Binary search trees, construction and serialization*.",
        intuition="Pick the **middle** element as the root: half the values go left, half go right, so the two sides differ in size by at most one. Do the same for each half.",
        hints=["Recurse on a range `(lo, hi)` of indices rather than slicing.", "`mid = (lo + hi) // 2` is the root of that range.", "Left child = build(lo, mid − 1), right child = build(mid + 1, hi)."],
        brute_force="Insert the values one by one into a BST: sorted input produces a chain of height n − 1 — a valid BST but not balanced.",
        approach="`[-10,-3,0,5,9]`: mid = 0 → root 0. Left range `[-10,-3]` → root -10 with right child -3. Right range `[5,9]` → root 5 with right child 9.",
        complexity="Time O(n), space O(log n) recursion.",
        pitfalls="Slicing (`nums[:mid]`) copies and makes it O(n log n); off-by-one in the ranges.",
        follow_up="Convert Sorted List to BST (109): find the middle with fast/slow, or build in inorder sequence.",
    ),
),
dict(
    id="range-sum-of-bst",
    title="Range Sum of BST",
    difficulty="Easy",
    pattern="Trees — BST Pruning",
    leetcode="https://leetcode.com/problems/range-sum-of-bst/",
    entry="rangeSumBST",
    arg_types=["tree", None, None],
    description=r"""
Given the root of a binary search tree and two integers `low <= high`, return the sum of all keys `k` in the
tree with `low <= k <= high`.

**Constraints**

- 1 to $2 \cdot 10^4$ nodes (judge: up to 5,000), keys distinct, `1 <= Node.val, low, high <= 10^5`.

**Example 1:** `root = [10,5,15,3,7,None,18], low = 7, high = 15` → `32` (7 + 10 + 15)

**Example 2:** `root = [10,5,15,3,7,13,18,1,None,6], low = 6, high = 10` → `23`
""" + TREE_FORMAT,
    starter=TN + '''class Solution:
    def rangeSumBST(self, root: Optional[TreeNode], low: int, high: int) -> int:
        pass
''',
    solution='''class Solution:
    def rangeSumBST(self, root, low, high):
        total, stack = 0, [root]
        while stack:
            node = stack.pop()
            if not node:
                continue
            if low <= node.val <= high:
                total += node.val
            if node.val > low:
                stack.append(node.left)
            if node.val < high:
                stack.append(node.right)
        return total
''',
    tests=[[[10, 5, 15, 3, 7, None, 18], 7, 15], [[10, 5, 15, 3, 7, 13, 18, 1, None, 6], 6, 10], [[5], 1, 4], [[5], 5, 5],
           [[10, 5, 15], 1, 100], [[10, 5, 15], 11, 14], [SKEW_R, 100, 200], [BST_BIG, 20000, 60000], [BST_BIG, 1, 10 ** 5],
           [balanced_bst(1, 4095), 1000, 1000]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def rangeSumBST(self, root, low, high):
        total, stack = 0, [root]
        while stack:
            node = stack.pop()
            if not node:
                continue
            if low < node.val < high:        # excludes the endpoints
                total += node.val
            stack.append(node.left)
            stack.append(node.right)
        return total
''',
        '''class Solution:
    def rangeSumBST(self, root, low, high):
        total, node = 0, root
        while node:                          # stops exploring once a node is out of range
            if node.val < low:
                node = node.right
            elif node.val > high:
                node = node.left
            else:
                total += node.val
                node = node.left
        return total
''',
    ],
    guide=dict(
        prereqs="BST ordering — lesson *Binary search trees*.",
        intuition="Visit nodes like any DFS, but use the ordering to skip whole subtrees: if a node's key is already ≤ `low`, nothing in its left subtree can be in range; if it is ≥ `high`, nothing in its right subtree can be.",
        hints=["Summing every node in range with a plain DFS is O(n) and correct.", "Only go left if `node.val > low`.", "Only go right if `node.val < high`."],
        brute_force="Inorder into a list and sum the in-range values: O(n) time and space.",
        approach="Example 1 (7..15): 10 in range (+10), go both ways. 5 < 7: skip its left (3), go right → 7 (+7). 15 (+15): not < 15, so skip 18. Total 32.",
        complexity="Time O(h + m) where m is the number of keys in range (O(n) worst case), space O(h).",
        pitfalls="Excluding the endpoints; abandoning the search at the first out-of-range node instead of pruning one side.",
        follow_up="Many range-sum queries on a changing set → augment nodes with subtree sums, or use a Fenwick tree.",
    ),
),
dict(
    id="binary-search-tree-iterator",
    title="Binary Search Tree Iterator",
    difficulty="Medium",
    pattern="Trees — Controlled Inorder",
    leetcode="https://leetcode.com/problems/binary-search-tree-iterator/",
    neetcode="https://neetcode.io/problems/binary-search-tree-iterator",
    entry="judge",
    arg_types=["tree", None],
    description=r"""
Implement `BSTIterator`, which walks a binary search tree in ascending key order one step at a time:

- `BSTIterator(root)` — set up the iterator (positioned *before* the smallest key).
- `next()` — move to the next key and return it.
- `hasNext()` — `True` if there is a next key.

`next()` is only called when a next key exists. Aim for O(1) **amortised** time per call and O(h) memory,
where h is the height — that rules out copying all keys into a list first.

**Constraints**

- 1 to $10^5$ nodes (judge: up to 5,000), `0 <= Node.val <= 10^6`.

**Judge input format:** the constructor needs a real tree, so each test is `root, ops`: a level-order list
and a list of method names (`"next"` / `"hasNext"`). The adapter at the bottom of the starter builds
`BSTIterator(root)`, calls the methods in order and returns the list of results.

**Example:** `root = [7,3,15,None,None,9,20]`,
`ops = ["next","next","hasNext","next","hasNext","next","hasNext","next","hasNext"]`
→ `[3,7,True,9,True,15,True,20,False]`
""" + TREE_FORMAT,
    starter=TN + '''class BSTIterator:

    def __init__(self, root: Optional[TreeNode]):
        pass

    def next(self) -> int:
        pass

    def hasNext(self) -> bool:
        pass
''' + ITER_ADAPTER,
    solution='''class BSTIterator:
    def __init__(self, root):
        self.stack = []
        self._push_left(root)

    def _push_left(self, node):
        while node:
            self.stack.append(node)
            node = node.left

    def next(self):
        node = self.stack.pop()
        self._push_left(node.right)
        return node.val

    def hasNext(self):
        return bool(self.stack)
''' + ITER_ADAPTER,
    tests=[[[7, 3, 15, None, None, 9, 20], ["next", "next", "hasNext", "next", "hasNext", "next", "hasNext", "next", "hasNext"]],
           [[1], ["hasNext", "next", "hasNext"]], [[2, 1], ["next", "next", "hasNext"]], [[1, None, 2], ["next", "hasNext", "next", "hasNext"]],
           [[5, 3, 8, 1, 4, 7, 9], _iter_ops(7, 1)], [SKEW_R, _iter_ops(500, 2)], [skewed(list(range(500, 0, -1)), "left"), ["hasNext", "next", "next"]],
           [BST_BIG, _iter_ops(5000, 3)], [balanced_bst(1, 2047), _iter_ops(2047, 4)]],
    examples=1,
    wrong_solutions=[
        '''class BSTIterator:
    # level order instead of sorted order
    def __init__(self, root):
        self.q = collections.deque([root] if root else [])

    def next(self):
        n = self.q.popleft()
        for c in (n.left, n.right):
            if c:
                self.q.append(c)
        return n.val

    def hasNext(self):
        return bool(self.q)
''' + ITER_ADAPTER,
        '''class BSTIterator:
    def __init__(self, root):
        self.stack = []
        while root:
            self.stack.append(root)
            root = root.left

    def next(self):
        node = self.stack.pop()            # forgets the right subtree
        return node.val

    def hasNext(self):
        return bool(self.stack)
''' + ITER_ADAPTER,
    ],
    guide=dict(
        prereqs="Iterative inorder traversal — lesson *Traversals*, §4.",
        intuition="This is the iterative inorder traversal, **paused** between pops. The stack holds the chain of nodes whose turn is still to come; `next()` pops one and prepares its right subtree by pushing that subtree's left spine.",
        hints=["Inorder of a BST is sorted.", "In the constructor push the root and all its left descendants.", "`next()`: pop a node, push the left spine of its right child, return its value. `hasNext()`: is the stack non-empty?"],
        brute_force="Run a full inorder in the constructor and keep an index into the list: O(1) per call but O(n) memory and O(n) set-up.",
        approach="`[7,3,15,None,None,9,20]`: constructor pushes 7, 3. next → pop 3 (no right) → 3. next → pop 7, push 15 then 9 → 7. next → pop 9 → 9. next → pop 15, push 20 → 15. next → 20. Stack empty → hasNext False.",
        complexity="Each node is pushed and popped once, so n calls cost O(n): O(1) amortised. Memory O(h).",
        pitfalls="Forgetting the right subtree; calling the tree's `left` spine push on the popped node instead of its right child.",
        follow_up="Two iterators (one ascending, one descending) solve Two Sum IV on a BST in O(h) space.",
    ),
),
# ================================== TRIES ====================================================
dict(
    id="replace-words",
    title="Replace Words",
    difficulty="Medium",
    pattern="Tries — Shortest Prefix",
    leetcode="https://leetcode.com/problems/replace-words/",
    entry="replaceWords",
    description=r"""
You have a dictionary of **roots** (short words) and a sentence of lowercase words separated by single
spaces. A longer word that begins with a root is a *derivative* of that root. Replace every derivative in
the sentence by its root; if several roots fit, use the **shortest** one. Words with no matching root stay
unchanged. Return the new sentence.

**Constraints**

- `1 <= len(dictionary) <= 1000`, roots have 1 to 100 lowercase letters.
- The sentence has up to $10^6$ characters classically (judge: about 30,000), words separated by exactly one space.

**Arguments:** `dictionary` (list of strings) and `sentence` (string).

**Example 1:** `dictionary = ["cat","bat","rat"], sentence = "the cattle was rattled by the battery"`
→ `"the cat was rat by the bat"`

**Example 2:** `dictionary = ["a","b","c"], sentence = "aadsfasf absbs bbab cadsfafs"` → `"a a b c"`
""",
    starter='''class Solution:
    def replaceWords(self, dictionary: List[str], sentence: str) -> str:
        pass
''',
    solution='''class Solution:
    def replaceWords(self, dictionary, sentence):
        root = {}
        for w in dictionary:
            node = root
            for ch in w:
                node = node.setdefault(ch, {})
            node["$"] = True
        out = []
        for word in sentence.split(" "):
            node, repl = root, word
            for i, ch in enumerate(word):
                node = node.get(ch)
                if node is None:
                    break
                if "$" in node:
                    repl = word[:i + 1]
                    break
            out.append(repl)
        return " ".join(out)
''',
    tests=[[["cat", "bat", "rat"], "the cattle was rattled by the battery"], [["a", "b", "c"], "aadsfasf absbs bbab cadsfafs"],
           [["a"], "b"], [["catt", "cat", "ca"], "cattle catalog car"], [["apple"], "app apple applepie"], [["x", "y"], "hello world"],
           [["ab", "abc", "b"], "abcd bcd abd a"], [_words(800, 1, 4, "abcd", 11), " ".join(_words(5000, 1, 8, "abcd", 12))],
           [["z" * 100], "z" * 99 + " " + "z" * 101]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def replaceWords(self, dictionary, sentence):
        out = []
        for word in sentence.split(" "):
            repl = word
            for root in dictionary:          # first matching root in list order, not the shortest
                if word.startswith(root):
                    repl = root
                    break
            out.append(repl)
        return " ".join(out)
''',
        '''class Solution:
    def replaceWords(self, dictionary, sentence):
        roots = set(dictionary)
        out = []
        for word in sentence.split(" "):
            repl = word
            for i in range(len(word), 0, -1):     # longest root instead of shortest
                if word[:i] in roots:
                    repl = word[:i]
                    break
            out.append(repl)
        return " ".join(out)
''',
    ],
    guide=dict(
        prereqs="*Implement Trie* — lesson *Tries: prefix trees from scratch*.",
        intuition="Put the roots in a trie. Walk each sentence word down the trie; the **first** end-of-word marker you pass is the shortest root that is a prefix of the word. If you fall off the trie first, there is no root.",
        hints=["Insert every root with an end marker.", "For each word walk character by character.", "Stop at the first end marker (→ replace) or at a missing child (→ keep the word)."],
        brute_force="For every word test every root with `startswith` and keep the shortest match: O(words × roots × length). A set of roots with prefix checks from shortest to longest is O(L²) per word.",
        approach="Roots cat/bat/rat. `cattle`: c → a → t (end marker) → replace by `cat`. `the`: no `t` child at the root → keep. `was`: no `w` → keep.",
        complexity="Building: O(total root letters). Each word of length L costs O(L). Overall linear in the input size.",
        pitfalls="- Returning the longest matching root or the first one in dictionary order.\n- Losing the single-space separators (use `split(' ')` / `' '.join`).",
        follow_up="Longest matching prefix instead of shortest (IP routing); Search Suggestions System (1268).",
    ),
),
dict(
    id="longest-word-in-dictionary",
    title="Longest Word in Dictionary",
    difficulty="Medium",
    pattern="Tries — DFS over Word Ends",
    leetcode="https://leetcode.com/problems/longest-word-in-dictionary/",
    entry="longestWord",
    description=r"""
Given a list of lowercase words, find the longest word that can be **built one letter at a time** using
other words of the list: every prefix of it (length 1, 2, … up to the word itself) must also be in the list.
If several such words have the same maximum length, return the alphabetically smallest. If none exists,
return the empty string.

**Constraints**

- `1 <= len(words) <= 1000`, each word has 1 to 30 lowercase letters.

**Example 1:** `words = ["w","wo","wor","worl","world"]` → `"world"`

**Example 2:** `words = ["a","banana","app","appl","ap","apply","apple"]` → `"apple"`
(`apple` and `apply` can both be built; `apple` is alphabetically smaller. `banana` cannot: `b` is missing.)
""",
    starter='''class Solution:
    def longestWord(self, words: List[str]) -> str:
        pass
''',
    solution='''class Solution:
    def longestWord(self, words):
        root = {}
        for w in words:
            node = root
            for ch in w:
                node = node.setdefault(ch, {})
            node["$"] = w
        best = ""
        stack = [root]
        while stack:
            node = stack.pop()
            for ch, child in node.items():
                if ch != "$" and "$" in child:       # only step onto complete words
                    w = child["$"]
                    if len(w) > len(best) or (len(w) == len(best) and w < best):
                        best = w
                    stack.append(child)
        return best
''',
    tests=[[["w", "wo", "wor", "worl", "world"]], [["a", "banana", "app", "appl", "ap", "apply", "apple"]], [["banana"]], [["b", "a"]],
           [["ab", "abc"]], [["a", "ab", "abc", "b", "bc", "bcd"]], [["yo", "ew", "fc", "zrc", "yodn", "fcm", "qm", "qmo", "fcmz", "z", "ewq", "yod", "ewqz", "y"]],
           [["m", "mo", "moc", "moch", "mocha", "l", "la", "lat", "latt", "latte", "c", "ca", "cat"]], [_lw_chain], [_lw_rand]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def longestWord(self, words):
        return min(words, key=lambda w: (-len(w), w))     # ignores the "buildable" rule
''',
        '''class Solution:
    def longestWord(self, words):
        s = set(words)
        best = ""
        for w in words:
            if all(w[:i] in s for i in range(1, len(w))) and len(w) > len(best):
                best = w                                   # no alphabetical tie-break
        return best
''',
    ],
    guide=dict(
        prereqs="Tries with end markers; DFS — lessons 8 and 9.",
        intuition="In a trie, 'every prefix is a word' means: every node on the path from the root to the word is marked as a word end. So explore the trie but only walk through marked nodes; the deepest node reached is the answer.",
        hints=["Insert all words; store the word at its end node.", "DFS/BFS from the root, stepping only into children that are word ends.", "Track the best by (longer length, then smaller alphabetically)."],
        brute_force="Put words in a set; for each word check all its prefixes: O(sum of L²). With L ≤ 30 that is also acceptable — sorting the words first makes it even shorter.",
        approach="Example 2: from the root only `a` is a word (b…banana is not marked at `b`). a → ap ✓ → app ✓ → appl ✓ → apple ✓ and apply ✓. Longest are both length 5; `apple` < `apply`.",
        complexity="Time O(total letters), space O(total letters).",
        pitfalls="- Forgetting the tie-break.\n- Checking only the prefix one shorter (must hold all the way down — the trie walk guarantees it).",
        follow_up="Longest Word With All Prefixes (1858); Word Squares (425).",
    ),
),
dict(
    id="map-sum-pairs",
    title="Map Sum Pairs",
    difficulty="Medium",
    pattern="Tries — Augmented Nodes",
    leetcode="https://leetcode.com/problems/map-sum-pairs/",
    kind="class",
    entry="MapSum",
    description=r"""
Design a map from string keys to integer values that can also add up values by prefix:

- `MapSum()` — empty map.
- `insert(key, val)` — store `val` under `key`. If the key already exists, its value is **replaced**.
- `sum(prefix)` — return the total of the values of all keys that start with `prefix`.

**Constraints**

- `1 <= len(key), len(prefix) <= 50`, lowercase letters, `1 <= val <= 1000`, at most 50 calls classically
  (judge: several hundred).

**Judge input format:** two lists — operation names and argument lists; output is the list of return values.

**Example:** `["MapSum","insert","sum","insert","sum"]`, `[[],["apple",3],["ap"],["app",2],["ap"]]`
→ `[None,None,3,None,5]`
""",
    starter='''class MapSum:

    def __init__(self):
        pass

    def insert(self, key: str, val: int) -> None:
        pass

    def sum(self, prefix: str) -> int:
        pass
''',
    solution='''class MapSum:
    def __init__(self):
        self.vals = {}
        self.root = {}

    def insert(self, key, val):
        delta = val - self.vals.get(key, 0)
        self.vals[key] = val
        node = self.root
        for ch in key:
            node = node.setdefault(ch, {})
            node["#"] = node.get("#", 0) + delta

    def sum(self, prefix):
        node = self.root
        for ch in prefix:
            node = node.get(ch)
            if node is None:
                return 0
        return node["#"]
''',
    tests=[
        [["MapSum", "insert", "sum", "insert", "sum"], [[], ["apple", 3], ["ap"], ["app", 2], ["ap"]]],
        [["MapSum", "sum", "insert", "sum", "sum"], [[], ["a"], ["a", 5], ["a"], ["aa"]]],
        [["MapSum", "insert", "insert", "sum", "sum"], [[], ["apple", 3], ["apple", 2], ["apple"], ["a"]]],
        [["MapSum", "insert", "insert", "insert", "sum", "sum", "sum"], [[], ["ab", 1], ["abc", 10], ["b", 100], ["ab"], ["b"], ["abcd"]]],
        [["MapSum", "insert", "sum", "insert", "sum", "insert", "sum"], [[], ["aa", 3], ["a"], ["aa", 2], ["a"], ["aaa", 3], ["aaa"]]],
        [["MapSum", "insert", "insert", "sum"], [[], ["x" * 50, 7], ["x" * 49, 1], ["x" * 49]]],
        [_ms_ops, _ms_args],
    ],
    examples=1,
    wrong_solutions=[
        '''class MapSum:
    # adds on re-insert instead of replacing
    def __init__(self):
        self.root = {}

    def insert(self, key, val):
        node = self.root
        for ch in key:
            node = node.setdefault(ch, {})
            node["#"] = node.get("#", 0) + val

    def sum(self, prefix):
        node = self.root
        for ch in prefix:
            node = node.get(ch)
            if node is None:
                return 0
        return node["#"]
''',
        '''class MapSum:
    def __init__(self):
        self.d = {}

    def insert(self, key, val):
        self.d[key] = val

    def sum(self, prefix):
        return self.d.get(prefix, 0)      # exact key only
''',
    ],
    guide=dict(
        prereqs="Tries with per-node counters — lesson *Tries: prefix trees from scratch*, §4.",
        intuition="Store at every trie node the **total value of all keys passing through it**. Then `sum(prefix)` is one walk to the prefix's node. Replacing a key means adding the *difference* between the new and old value along its path.",
        hints=["Keep an ordinary dict `key → value` to know the old value.", "On insert compute `delta = val - old` and add `delta` to every node on the key's path.", "`sum(prefix)`: walk the prefix; missing child → 0; otherwise return the node's total."],
        brute_force="A plain dict, and `sum` scans every key with `startswith`: O(N·L) per query — fine for 50 calls, poor at scale.",
        approach="insert(apple,3): nodes a,p,p,l,e all hold 3. sum(ap) = 3. insert(app,2): a,p,p become 5. sum(ap) = 5. Re-insert apple with 2: delta = −1 along a,p,p,l,e.",
        complexity="`insert` O(L), `sum` O(L). Space O(total letters).",
        pitfalls="Adding the full value again when a key is re-inserted (the classic bug).",
        follow_up="Support deletion (delta = −old); return the top-k keys under a prefix (autocomplete).",
    ),
),
]
