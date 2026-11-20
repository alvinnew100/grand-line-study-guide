import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nlt_gen import *  # noqa: E402,F401,F403

LN = '''# ListNode is pre-defined by the judge (no need to paste it):
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
'''

LL_FORMAT = ("\n\n**Judge input format:** a linked list is written as the Python list of its values from head to tail, "
             "e.g. `[1,2,3]`; `[]` is the empty list (`head = None`). The judge builds the `ListNode` chain for you "
             "and turns any returned list back into a Python list.\n")


def _rnd(seed):
    return random.Random(seed)


# --------------------------------------------------------------------------------------------
# Linked List Cycle adapter
CYCLE_ADAPTER = '''

# ---- judge adapter: do not edit -------------------------------------------
# Each test is (values, pos). The adapter builds the list, links the tail back
# to the node at index pos (pos = -1 means no cycle) and calls hasCycle(head).
def judge(values, pos):
    nodes = [ListNode(v) for v in values]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    if pos >= 0:
        nodes[-1].next = nodes[pos]
    return Solution().hasCycle(nodes[0] if nodes else None)
'''

INTERSECT_ADAPTER = '''

# ---- judge adapter: do not edit -------------------------------------------
# Each test is (prefixA, prefixB, common). List A = prefixA + common and
# list B = prefixB + common, where the `common` nodes are physically SHARED.
# The adapter reports the value of the node you return - but only if it really
# is the first shared node object (equal values are not enough).
def judge(prefixA, prefixB, common):
    def chain(vals, tail=None):
        head = tail
        for v in reversed(vals):
            head = ListNode(v, head)
        return head
    shared = chain(common)
    a, b = chain(prefixA, shared), chain(prefixB, shared)
    got = Solution().getIntersectionNode(a, b)
    if got is None:
        return None
    if got is not shared:
        return "wrong node object (val=%r)" % (got.val,)
    return got.val
'''

RANDOM_NODE = '''# For this problem the judge's node has a `random` pointer too. It is defined
# here for you (keep it):
class Node:
    def __init__(self, x: int, next: 'Node' = None, random: 'Node' = None):
        self.val = int(x)
        self.next = next
        self.random = random

'''

RANDOM_ADAPTER = '''

# ---- judge adapter: do not edit -------------------------------------------
# Each test is a list of [val, random_index] pairs (random_index None = null).
# The adapter builds the original list, calls copyRandomList(head) and then
# serialises YOUR copy back into the same [val, random_index] format. It also
# rejects copies that reuse original nodes or that damage the original list.
def judge(pairs):
    nodes = [Node(v) for v, _ in pairs]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    for node, (_, r) in zip(nodes, pairs):
        node.random = nodes[r] if r is not None else None
    original = {id(n) for n in nodes}
    head = Solution().copyRandomList(nodes[0] if nodes else None)
    copies, index, cur = [], {}, head
    while cur is not None and len(copies) <= len(nodes):
        if id(cur) in original:
            return "error: your list reuses a node from the original list"
        index[id(cur)] = len(copies)
        copies.append(cur)
        cur = cur.next
    out = []
    for c in copies:
        r = c.random
        if r is not None and id(r) not in index:
            return "error: a random pointer does not point into your copy"
        out.append([c.val, None if r is None else index[id(r)]])
    for i, (v, r) in enumerate(pairs):
        n = nodes[i]
        nxt = nodes[i + 1] if i + 1 < len(nodes) else None
        if n.val != v or n.next is not nxt or n.random is not (nodes[r] if r is not None else None):
            return "error: the original list was modified"
    return out
'''

MERGEK_ADAPTER = '''

# ---- judge adapter: do not edit -------------------------------------------
# Each test is a list of Python lists. The adapter turns every inner list into
# a ListNode chain and calls mergeKLists(lists) with a Python list of heads.
def judge(lists):
    heads = []
    for arr in lists:
        dummy = cur = ListNode()
        for v in arr:
            cur.next = ListNode(v)
            cur = cur.next
        heads.append(dummy.next)
    return Solution().mergeKLists(heads)
'''


def _sorted_list(rnd, n, lo=-100, hi=100):
    return sorted(rnd.randint(lo, hi) for _ in range(n))


r = _rnd(7)
_pal_big = [r.randint(0, 9) for _ in range(5000)]
_pal_big = _pal_big + _pal_big[::-1]
_pal_big_bad = _pal_big[:]
_pal_big_bad[4000] = (_pal_big_bad[4000] + 1) % 10

_lru_ops, _lru_args = ["LRUCache"], [[50]]
for _ in range(3000):
    if r.random() < 0.5:
        _lru_ops.append("put")
        _lru_args.append([r.randint(0, 120), r.randint(0, 10 ** 5)])
    else:
        _lru_ops.append("get")
        _lru_args.append([r.randint(0, 120)])

_dup_big = list(range(1, 10001)) + [r.randint(1, 10000)]
r.shuffle(_dup_big)
# make _dup_many a valid input: n+1 numbers in [1, n] with only one repeated value
_n = 10000
_dup_many = [7777] * 4001 + [x for x in range(1, _n + 1) if x != 7777][:6000]
r.shuffle(_dup_many)

PROBLEMS = [
# ============================================================================================
dict(
    id="reverse-linked-list",
    title="Reverse Linked List",
    difficulty="Easy",
    pattern="Linked List — Reversal",
    leetcode="https://leetcode.com/problems/reverse-linked-list/",
    neetcode="https://neetcode.io/problems/reverse-a-linked-list",
    entry="reverseList",
    arg_types=["list_node"],
    return_type="list_node",
    description=r"""
You receive the `head` of a singly linked list. Turn the list around so that the last node becomes
the first, and return the new head. Re-use the existing nodes — rewire their `next` pointers instead
of creating a new list.

**Constraints**

- The list has between 0 and 5000 nodes.
- `-5000 <= Node.val <= 5000`

**Example 1:** `head = [1,2,3,4,5]` → `[5,4,3,2,1]`

**Example 2:** `head = [1,2]` → `[2,1]`

**Example 3:** `head = []` → `[]`
""" + LL_FORMAT,
    starter=LN + '''class Solution:
    def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        pass
''',
    solution='''class Solution:
    def reverseList(self, head):
        prev = None
        cur = head
        while cur:
            nxt = cur.next
            cur.next = prev
            prev = cur
            cur = nxt
        return prev
''',
    tests=[
        [[1, 2, 3, 4, 5]], [[1, 2]], [[]], [[7]], [[1, 1, 2]], [[-5, 0, 5]], [[3, 3, 3]],
        [[5, 4, 3, 2, 1]], [[0, -1]], [list(range(5000))], [[r.randint(-5000, 5000) for _ in range(4999)]],
    ],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def reverseList(self, head):
        return head
''',
        '''class Solution:
    def reverseList(self, head):
        # swaps only the first two nodes
        if head and head.next:
            second = head.next
            head.next = second.next
            second.next = head
            return second
        return head
''',
    ],
    guide=dict(
        prereqs="Lesson *Nodes, pointers and the dummy-node trick* and the reversal section of *Reversal, merging and in-place rearrangement*.",
        intuition="Walk the list once. At every node, flip its arrow so it points **backwards** to the node you just left. "
                  "The only danger is losing the rest of the list when you overwrite `cur.next`, so save it first.",
        hints=[
            "You need to remember the node *before* the current one — call it `prev`, starting at `None`.",
            "Before changing `cur.next`, store it in a temporary variable, otherwise the rest of the list is unreachable.",
            "Loop: `nxt = cur.next; cur.next = prev; prev = cur; cur = nxt`. When `cur` is `None`, `prev` is the new head.",
        ],
        brute_force="Copy all values into a Python list, reverse it, and write the values back (or build new nodes). "
                    "O(n) time but O(n) extra space, and it dodges the pointer skill the problem is testing.",
        approach="""Three pointers: `prev`, `cur`, `nxt`.

Dry run on `1 → 2 → 3`:

| step | prev | cur | action |
|---|---|---|---|
| start | None | 1 | |
| 1 | 1 | 2 | `1.next = None` |
| 2 | 2 | 3 | `2.next = 1` |
| 3 | 3 | None | `3.next = 2` |

Return `prev` = 3, giving `3 → 2 → 1`.

**Recursive version:** `reverse(head)` reverses `head.next` onward, then sets `head.next.next = head; head.next = None`.
It is elegant but uses O(n) call stack — 5000 frames would exceed Python's default recursion limit.""",
        complexity="Time O(n) — each node is visited once. Space O(1) for the iterative version (O(n) stack for recursion).",
        pitfalls="- Forgetting to save `cur.next` before overwriting it.\n- Returning `head` (which is now the *tail*) instead of `prev`.\n"
                 "- Not setting the old head's `next` to `None` — creates a 2-node cycle (the iterative loop handles it because `prev` starts as `None`).",
        follow_up="Reverse only positions `left..right` (LeetCode 92), or reverse in groups of k (*Reverse Nodes in k-Group* in this module).",
    ),
),
# ============================================================================================
dict(
    id="merge-two-sorted-lists",
    title="Merge Two Sorted Lists",
    difficulty="Easy",
    pattern="Linked List — Dummy Node",
    leetcode="https://leetcode.com/problems/merge-two-sorted-lists/",
    neetcode="https://neetcode.io/problems/merge-two-sorted-linked-lists",
    entry="mergeTwoLists",
    arg_types=["list_node", "list_node"],
    return_type="list_node",
    description=r"""
Two singly linked lists are each sorted in non-decreasing order. Splice their nodes together into one
sorted list (re-using the nodes, not copying values) and return its head.

**Constraints**

- Each list has between 0 and 50 nodes in the classic version; the judge also tries a few thousand.
- `-100 <= Node.val <= 100`, both lists sorted ascending.

**Example 1:** `list1 = [1,2,4], list2 = [1,3,4]` → `[1,1,2,3,4,4]`

**Example 2:** `list1 = [], list2 = []` → `[]`

**Example 3:** `list1 = [], list2 = [0]` → `[0]`
""" + LL_FORMAT,
    starter=LN + '''class Solution:
    def mergeTwoLists(self, list1: Optional[ListNode], list2: Optional[ListNode]) -> Optional[ListNode]:
        pass
''',
    solution='''class Solution:
    def mergeTwoLists(self, list1, list2):
        dummy = tail = ListNode()
        while list1 and list2:
            if list1.val <= list2.val:
                tail.next, list1 = list1, list1.next
            else:
                tail.next, list2 = list2, list2.next
            tail = tail.next
        tail.next = list1 or list2
        return dummy.next
''',
    tests=[
        [[1, 2, 4], [1, 3, 4]], [[], []], [[], [0]], [[5], []], [[1, 2, 3], [4, 5, 6]], [[4, 5, 6], [1, 2, 3]],
        [[1, 1, 1], [1, 1]], [[-10, -3, 0], [-5, 2]], [[2], [1]], [[1, 3, 5, 7, 9], [2]],
        [_sorted_list(r, 3000), _sorted_list(r, 2500)],
    ],
    wrong_solutions=[
        '''class Solution:
    def mergeTwoLists(self, list1, list2):
        # just glues list2 after list1
        if not list1:
            return list2
        cur = list1
        while cur.next:
            cur = cur.next
        cur.next = list2
        return list1
''',
        '''class Solution:
    def mergeTwoLists(self, list1, list2):
        dummy = tail = ListNode()
        while list1 and list2:
            if list1.val <= list2.val:
                tail.next, list1 = list1, list1.next
            else:
                tail.next, list2 = list2, list2.next
            tail = tail.next
        return dummy.next   # forgets the leftover tail
''',
    ],
    guide=dict(
        prereqs="Dummy (sentinel) nodes — lesson *Nodes, pointers and the dummy-node trick*.",
        intuition="Like merging two sorted piles of cards: repeatedly take the smaller top card. A dummy node gives you a fixed "
                  "place to start attaching, so you never special-case 'which node is the head?'.",
        hints=[
            "Create `dummy = ListNode()` and a `tail` pointer that always sits on the last node of the merged list.",
            "While both lists are non-empty, attach the smaller head to `tail.next` and advance that list.",
            "When one list runs out, attach the *entire* remainder of the other in one step — it is already sorted.",
        ],
        brute_force="Collect all values, sort them (O((m+n) log(m+n))) and build a new list. Works, but ignores that the inputs are already sorted and allocates new nodes.",
        approach="""Dry run with `[1,2,4]` and `[1,3,4]` (ties go to `list1`):

1. 1 vs 1 → take list1's 1. merged: 1
2. 2 vs 1 → take list2's 1. merged: 1,1
3. 2 vs 3 → take 2. merged: 1,1,2
4. 4 vs 3 → take 3. merged: 1,1,2,3
5. 4 vs 4 → take list1's 4. list1 empty.
6. attach rest of list2 (`4`). Result `1,1,2,3,4,4`.

Return `dummy.next`. A recursive version (`if l1.val <= l2.val: l1.next = merge(l1.next, l2); return l1`) is shorter but uses O(m+n) stack.""",
        complexity="Time O(m + n): each node is attached exactly once. Space O(1) extra (iterative).",
        pitfalls="- Forgetting to attach the leftover list after the loop.\n- Returning `dummy` instead of `dummy.next`.\n- Forgetting to advance `tail`, which overwrites the same `next` field again and again.",
        follow_up="Merge **k** lists (*Merge k Sorted Lists*) and the merge step of merge sort on linked lists (LeetCode 148, Sort List).",
    ),
),
# ============================================================================================
dict(
    id="linked-list-cycle",
    title="Linked List Cycle",
    difficulty="Easy",
    pattern="Linked List — Fast & Slow Pointers",
    leetcode="https://leetcode.com/problems/linked-list-cycle/",
    neetcode="https://neetcode.io/problems/linked-list-cycle-detection",
    entry="judge",
    description=r"""
Decide whether a singly linked list contains a **cycle**: some node whose `next` pointer leads back to
a node seen earlier, so that following `next` forever never reaches `None`. Return `True` if there is a
cycle, otherwise `False`.

**Constraints**

- Up to $10^4$ nodes, `-10^5 <= Node.val <= 10^5` (values may repeat!).
- Follow-up: use O(1) extra memory.

**Judge input format (read this):** a cyclic list cannot be written as a plain Python list, so each test
gives two arguments `values, pos`. The judge builds the chain of `values` and, if `pos >= 0`, links the
**tail** back to the node at index `pos`. `pos = -1` means no cycle. You still only implement the
LeetCode method `hasCycle(head)`; the small `judge(values, pos)` adapter at the bottom of the starter
does the building — leave it in place.

**Example 1:** `values = [3,2,0,-4], pos = 1` → `True` (tail `-4` links back to `2`)

**Example 2:** `values = [1,2], pos = 0` → `True`

**Example 3:** `values = [1], pos = -1` → `False`
""",
    starter=LN + '''class Solution:
    def hasCycle(self, head: Optional[ListNode]) -> bool:
        pass
''' + CYCLE_ADAPTER,
    solution='''class Solution:
    def hasCycle(self, head):
        slow = fast = head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
            if slow is fast:
                return True
        return False
''' + CYCLE_ADAPTER,
    tests=[
        [[3, 2, 0, -4], 1], [[1, 2], 0], [[1], -1], [[], -1], [[1], 0], [[1, 1, 1, 1], -1],
        [[5, 5], -1], [list(range(10000)), -1], [list(range(10000)), 0], [list(range(10000)), 9999],
        [list(range(10000)), 5000], [[0] * 3000, 2999],
    ],
    wrong_solutions=[
        '''class Solution:
    def hasCycle(self, head):
        seen = set()
        while head:
            if head.val in seen:      # compares VALUES, not nodes
                return True
            seen.add(head.val)
            head = head.next
        return False
''' + CYCLE_ADAPTER,
        '''class Solution:
    def hasCycle(self, head):
        steps = 0
        while head:
            head = head.next
            steps += 1
            if steps > 1000:
                return True
        return False
''' + CYCLE_ADAPTER,
    ],
    guide=dict(
        prereqs="Floyd's tortoise-and-hare — lesson *Fast and slow pointers*.",
        intuition="Send two runners down the list, one moving 1 step and one moving 2 steps per turn. On a straight road the "
                  "fast one simply reaches the end. On a circular track the fast one laps the slow one and they meet.",
        hints=[
            "A set of *node objects* (not values) seen so far solves it in O(n) memory.",
            "For O(1) memory, use two pointers moving at different speeds.",
            "Loop while `fast and fast.next`; move `slow` 1 and `fast` 2; if `slow is fast`, there is a cycle.",
        ],
        brute_force="Store each visited node in a `set` (by identity — Python hashes objects by id by default). If you see a node twice, there is a cycle. O(n) time and O(n) space.",
        approach="""Floyd's algorithm. Once both pointers are inside the cycle (length $C$), the gap between them, measured in the
direction of travel, shrinks by exactly 1 every turn (fast gains 2, slow gains 1). A gap that shrinks by 1 must hit 0,
so they meet within $C$ turns of slow entering the loop.

Dry run, `[3,2,0,-4]`, tail → index 1:

| turn | slow | fast |
|---|---|---|
| 0 | 3 | 3 |
| 1 | 2 | 0 |
| 2 | 0 | 2 |
| 3 | -4 | -4 ✔ meet |""",
        complexity="Time O(n): slow takes at most (tail length + C) steps before meeting. Space O(1).",
        pitfalls="- Comparing `slow.val == fast.val` instead of `slow is fast` — duplicate values cause false positives.\n"
                 "- Checking `slow is fast` *before* moving: they are equal at the start.\n- Forgetting `fast.next` in the loop condition → `AttributeError` on `None.next`.",
        follow_up="Find the node where the cycle begins (LeetCode 142) — reset one pointer to `head` after meeting and move both at speed 1. That trick also solves *Find the Duplicate Number*.",
    ),
),
# ============================================================================================
dict(
    id="middle-of-the-linked-list",
    title="Middle of the Linked List",
    difficulty="Easy",
    pattern="Linked List — Fast & Slow Pointers",
    leetcode="https://leetcode.com/problems/middle-of-the-linked-list/",
    entry="middleNode",
    arg_types=["list_node"],
    return_type="list_node",
    description=r"""
Return the middle node of a non-empty singly linked list. When the list has an even number of nodes there
are two middles — return the **second** one. (Returning a node means the judge prints the list from that
node to the end.)

**Constraints**

- 1 to 100 nodes in the classic version (the judge also tests 9,999), `1 <= Node.val <= 100`.

**Example 1:** `head = [1,2,3,4,5]` → `[3,4,5]`

**Example 2:** `head = [1,2,3,4,5,6]` → `[4,5,6]`
""" + LL_FORMAT,
    starter=LN + '''class Solution:
    def middleNode(self, head: Optional[ListNode]) -> Optional[ListNode]:
        pass
''',
    solution='''class Solution:
    def middleNode(self, head):
        slow = fast = head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
        return slow
''',
    tests=[[[1, 2, 3, 4, 5]], [[1, 2, 3, 4, 5, 6]], [[1]], [[1, 2]], [[1, 2, 3]], [[9, 9, 9, 9]],
           [list(range(1, 10000))], [list(range(1, 10001))], [[5, 4, 3, 2, 1, 0, 7, 8]]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def middleNode(self, head):
        slow, fast = head, head.next
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
        return slow   # first middle for even lengths
''',
    ],
    guide=dict(
        prereqs="Fast/slow pointers.",
        intuition="If one pointer moves twice as fast, then when it falls off the end the slow pointer has covered half the distance.",
        hints=["Counting the length and walking `n // 2` steps works in two passes.",
               "With two pointers you can do it in one pass.",
               "`while fast and fast.next: slow = slow.next; fast = fast.next.next` — `slow` ends on the second middle."],
        brute_force="Copy nodes into an array and return `arr[len(arr)//2]` — O(n) space. Or two passes: count, then walk.",
        approach="Dry run `[1..6]`: (slow,fast) = (1,1) → (2,3) → (3,5) → (4,None). Stop, return node 4. For `[1..5]`: (1,1)→(2,3)→(3,5); `fast.next` is None so stop at 3.",
        complexity="Time O(n), space O(1).",
        pitfalls="Starting `fast` at `head.next` changes which middle you get — know which variant you need (palindrome and reorder problems often want the *first* middle).",
        follow_up="Used as a building block in *Palindrome Linked List*, *Reorder List* and merge sort on lists.",
    ),
),
# ============================================================================================
dict(
    id="palindrome-linked-list",
    title="Palindrome Linked List",
    difficulty="Easy",
    pattern="Linked List — Fast/Slow + Reversal",
    leetcode="https://leetcode.com/problems/palindrome-linked-list/",
    entry="isPalindrome",
    arg_types=["list_node"],
    description=r"""
Return `True` if the values of a singly linked list read the same forwards and backwards.

**Constraints**

- 1 to $10^5$ nodes (judge uses up to 10,000), `0 <= Node.val <= 9`.
- Follow-up: O(n) time and O(1) extra space.

**Example 1:** `head = [1,2,2,1]` → `True`

**Example 2:** `head = [1,2]` → `False`
""" + LL_FORMAT,
    starter=LN + '''class Solution:
    def isPalindrome(self, head: Optional[ListNode]) -> bool:
        pass
''',
    solution='''class Solution:
    def isPalindrome(self, head):
        slow = fast = head
        while fast and fast.next:
            slow, fast = slow.next, fast.next.next
        prev = None
        while slow:
            slow.next, prev, slow = prev, slow, slow.next
        left, right = head, prev
        while right:
            if left.val != right.val:
                return False
            left, right = left.next, right.next
        return True
''',
    tests=[[[1, 2, 2, 1]], [[1, 2]], [[1]], [[1, 2, 1]], [[1, 1]], [[1, 2, 3, 2, 2]], [[1, 0, 0]],
           [[9, 8, 7, 8, 9]], [[1, 2, 3, 1]], [_pal_big], [_pal_big_bad], [[3, 3, 3, 4, 3, 3]]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def isPalindrome(self, head):
        first, last = head, head
        while last.next:
            last = last.next
        return first.val == last.val
''',
    ],
    guide=dict(
        prereqs="Middle of the list and in-place reversal.",
        intuition="A palindrome's second half, reversed, equals its first half. Find the middle, reverse the second half in place, "
                  "then walk the two halves in lock-step.",
        hints=["Copying values to a Python list and comparing with its reverse is O(n) space — fine as a first answer.",
               "Use fast/slow pointers to reach the middle.",
               "Reverse from the middle to the end, then compare node by node from `head` and from the new reversed head."],
        brute_force="`vals = []` while walking, then `return vals == vals[::-1]`. O(n) time and space.",
        approach="For `[1,2,2,1]`: slow stops at the second `2`. Reversing from there gives `1 → 2`, while the first half is still `1 → 2 → (2)`. "
                 "Compare 1=1, 2=2, right half exhausted → `True`. For odd lengths the middle node ends up in the reversed half and compares with itself — harmless.",
        complexity="Time O(n), space O(1). (Polite code restores the second half afterwards by reversing it again.)",
        pitfalls="- Comparing until `left` is exhausted instead of `right`: the first half still points into the reversed part.\n- Mutating the input is acceptable on LeetCode, but mention it in interviews.",
        follow_up="Recursive solution with a pointer moving from the front while the recursion unwinds from the back (O(n) stack).",
    ),
),
# ============================================================================================
dict(
    id="intersection-of-two-linked-lists",
    title="Intersection of Two Linked Lists",
    difficulty="Easy",
    pattern="Linked List — Two Pointers",
    leetcode="https://leetcode.com/problems/intersection-of-two-linked-lists/",
    entry="judge",
    description=r"""
Two singly linked lists may merge at some node and share all nodes from there to the end (a "Y" shape).
Return the **first shared node**, or `None` if the lists never meet. Sharing means the *same node object*;
two different nodes holding equal values do not count. Do not modify the lists.

**Constraints**

- Up to $3 \cdot 10^4$ nodes per list; values can repeat across and within lists.
- Follow-up: O(m + n) time, O(1) memory.

**Judge input format:** each test is `prefixA, prefixB, common`. List A is `prefixA + common`, list B is
`prefixB + common`, and the `common` part is made of the very same node objects. The adapter at the bottom
of the starter builds this and calls your `getIntersectionNode(headA, headB)`. The expected output is the
value of the first shared node (or `None`). Returning a different node with an equal value is reported as wrong.

**Example 1:** `prefixA = [4,1], prefixB = [5,6,1], common = [8,4,5]` → `8`

**Example 2:** `prefixA = [2,6,4], prefixB = [1,5], common = []` → `None`
""",
    starter=LN + '''class Solution:
    def getIntersectionNode(self, headA: ListNode, headB: ListNode) -> Optional[ListNode]:
        pass
''' + INTERSECT_ADAPTER,
    solution='''class Solution:
    def getIntersectionNode(self, headA, headB):
        a, b = headA, headB
        while a is not b:
            a = a.next if a else headB
            b = b.next if b else headA
        return a
''' + INTERSECT_ADAPTER,
    tests=[
        [[4, 1], [5, 6, 1], [8, 4, 5]], [[2, 6, 4], [1, 5], []], [[], [], [1, 2, 3]], [[1, 9, 1], [2], [2, 4]],
        [[], [3], [3]], [[1], [], []], [[8, 8, 8], [8], [8, 8]], [[7, 7], [7, 7, 7, 7], [7]],
        [list(range(3000)), list(range(5000)), list(range(2000))], [[1] * 2000, [1] * 10, []],
    ],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def getIntersectionNode(self, headA, headB):
        vals = set()
        while headA:
            vals.add(headA.val)
            headA = headA.next
        while headB:
            if headB.val in vals:        # value equality, not identity
                return headB
            headB = headB.next
        return None
''' + INTERSECT_ADAPTER,
    ],
    guide=dict(
        prereqs="Pointer identity (`is`) vs value equality (`==`).",
        intuition="If pointer `a` walks A then B, and pointer `b` walks B then A, both travel exactly `len(A) + len(B)` steps. "
                  "Aligned that way, they arrive at the junction at the same moment — or both reach `None` together.",
        hints=["A set of node objects from list A lets you find the first B node in the set (O(m) memory).",
               "Alternative: compute both lengths and advance the longer list by the difference first.",
               "The elegant version: when a pointer falls off its list, restart it at the *other* list's head; loop until `a is b`."],
        brute_force="For every node of A, scan all of B: O(m·n). Or use a set of A's node objects: O(m+n) time, O(m) space.",
        approach="With A = `4,1,[8,4,5]`, B = `5,6,1,[8,4,5]`: `a` walks 5 nodes of A then switches to B; `b` walks 6 nodes of B then switches to A. "
                 "After `a` has done 2+3+3 = 8 steps and `b` 3+3+2 = 8 steps, both stand on the shared `8`. If there is no junction, both become `None` after m+n steps and `None is None` stops the loop.",
        complexity="Time O(m + n), space O(1).",
        pitfalls="- Using `==` on values instead of `is`.\n- Switching to the other head when `a.next` is None (instead of when `a` is None) — then the no-intersection case loops forever because pointers never equal `None` together.",
        follow_up="If the lists might contain cycles, first detect them with Floyd's algorithm.",
    ),
),
# ============================================================================================
dict(
    id="reorder-list",
    title="Reorder List",
    difficulty="Medium",
    pattern="Linked List — Middle + Reverse + Merge",
    leetcode="https://leetcode.com/problems/reorder-list/",
    neetcode="https://neetcode.io/problems/reorder-linked-list",
    entry="reorderList",
    arg_types=["list_node"],
    return_type="list_node",
    inplace_arg=0,
    description=r"""
A list $L_0 \to L_1 \to \dots \to L_{n-1}$ must be rearranged **in place** into
$L_0 \to L_{n-1} \to L_1 \to L_{n-2} \to L_2 \to \dots$ (first, last, second, second-to-last, ...).
Only rewire the `next` pointers; do not change node values. The method returns nothing.

**Constraints**

- 1 to $5 \cdot 10^4$ nodes, `1 <= Node.val <= 1000`.

**Judge input format:** the list of values head → tail. After your method returns, the judge reads the
list starting from the original `head` node, so the result is checked in place.

**Example 1:** `head = [1,2,3,4]` → `[1,4,2,3]`

**Example 2:** `head = [1,2,3,4,5]` → `[1,5,2,4,3]`
""",
    starter=LN + '''class Solution:
    def reorderList(self, head: Optional[ListNode]) -> None:
        """
        Do not return anything, modify head in-place instead.
        """
        pass
''',
    solution='''class Solution:
    def reorderList(self, head):
        if not head:
            return
        slow, fast = head, head.next
        while fast and fast.next:
            slow, fast = slow.next, fast.next.next
        second = slow.next
        slow.next = None
        prev = None
        while second:
            second.next, prev, second = prev, second, second.next
        first, second = head, prev
        while second:
            n1, n2 = first.next, second.next
            first.next = second
            second.next = n1
            first, second = n1, n2
''',
    tests=[[[1, 2, 3, 4]], [[1, 2, 3, 4, 5]], [[1]], [[1, 2]], [[1, 2, 3]], [[5, 5, 5, 5]], [[10, 20, 30, 40, 50, 60]],
           [list(range(1, 10001))], [list(range(1, 9998))], [[2, 1]]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def reorderList(self, head):
        vals = []
        cur = head
        while cur:
            vals.append(cur.val)
            cur = cur.next
        cur = head
        for v in reversed(vals):    # reverses instead of interleaving
            cur.val = v
            cur = cur.next
''',
        '''class Solution:
    def reorderList(self, head):
        if not head:
            return
        slow, fast = head, head.next
        while fast and fast.next:
            slow, fast = slow.next, fast.next.next
        second = slow.next          # forgot to cut: slow.next = None
        prev = None
        while second:
            second.next, prev, second = prev, second, second.next
        first, second = head, prev
        while second and first:
            n1, n2 = first.next, second.next
            first.next = second
            second.next = n1
            first, second = n1, n2
''',
    ],
    guide=dict(
        prereqs="Middle of list, in-place reversal, merging — all three lessons of this module.",
        intuition="The target order alternates between the front half and the *back half read backwards*. So: split at the middle, reverse the back half, then zip the two halves together.",
        hints=["Putting nodes into a Python list and using two indices i, j works in O(n) space.",
               "Find the end of the first half with fast/slow, cut the list there, reverse the second half.",
               "Interleave: save both `next`s, link `first → second → old first.next`, advance both."],
        brute_force="Store all nodes in an array `nodes`, then with `i = 0, j = n-1` link `nodes[i] → nodes[j] → nodes[i+1]` moving inward; finally set the last node's `next = None`. O(n) time and space.",
        approach="""`[1,2,3,4,5]`:

1. Middle: `slow` stops on 3 (first half `1,2,3`).
2. Cut: `3.next = None`; second half `4,5` reversed → `5,4`.
3. Merge: `1→5→2→4→3`.

Note the first half is always the same length as or one longer than the second half, so looping `while second` is enough.""",
        complexity="Time O(n), space O(1).",
        pitfalls="- Forgetting to cut the list (`slow.next = None`) creates a cycle.\n- Changing `val`s instead of links is not in the spirit of the problem.\n- With `fast = head` instead of `head.next` the split shifts for even lengths; both work if you are consistent, but verify on `[1,2]`.",
        follow_up="This 'split / reverse / merge' combo also appears in *Palindrome Linked List*.",
    ),
),
# ============================================================================================
dict(
    id="remove-nth-node-from-end-of-list",
    title="Remove Nth Node From End of List",
    difficulty="Medium",
    pattern="Linked List — Two Pointers with a Gap",
    leetcode="https://leetcode.com/problems/remove-nth-node-from-end-of-list/",
    neetcode="https://neetcode.io/problems/remove-node-from-end-of-linked-list",
    entry="removeNthFromEnd",
    arg_types=["list_node", None],
    return_type="list_node",
    description=r"""
Delete the `n`-th node counting from the **end** of a linked list (`n = 1` is the last node) and return
the head of the resulting list.

**Constraints**

- The list has `sz` nodes, `1 <= sz <= 30` classically (the judge also uses 10,000); `1 <= n <= sz`.
- Follow-up: one pass.

**Arguments:** `head` (list format below) and the integer `n`.

**Example 1:** `head = [1,2,3,4,5], n = 2` → `[1,2,3,5]`

**Example 2:** `head = [1], n = 1` → `[]`

**Example 3:** `head = [1,2], n = 2` → `[2]`
""" + LL_FORMAT,
    starter=LN + '''class Solution:
    def removeNthFromEnd(self, head: Optional[ListNode], n: int) -> Optional[ListNode]:
        pass
''',
    solution='''class Solution:
    def removeNthFromEnd(self, head, n):
        dummy = ListNode(0, head)
        left, right = dummy, head
        for _ in range(n):
            right = right.next
        while right:
            left, right = left.next, right.next
        left.next = left.next.next
        return dummy.next
''',
    tests=[[[1, 2, 3, 4, 5], 2], [[1], 1], [[1, 2], 2], [[1, 2], 1], [[1, 2, 3], 3], [[1, 2, 3], 1],
           [[7, 7, 7, 7], 2], [list(range(10000)), 10000], [list(range(10000)), 1], [list(range(10000)), 4321]],
    wrong_solutions=[
        '''class Solution:
    def removeNthFromEnd(self, head, n):
        # removes the n-th node from the START
        dummy = ListNode(0, head)
        cur = dummy
        for _ in range(n - 1):
            cur = cur.next
        cur.next = cur.next.next
        return dummy.next
''',
        '''class Solution:
    def removeNthFromEnd(self, head, n):
        left, right = head, head          # no dummy: cannot delete the head
        for _ in range(n):
            right = right.next
        if right is None:
            return head
        while right.next:
            left, right = left.next, right.next
        left.next = left.next.next
        return head
''',
    ],
    guide=dict(
        prereqs="Dummy node; two pointers kept a fixed distance apart.",
        intuition="Keep two pointers `n` nodes apart. When the front one falls off the end, the back one is right *before* the node to delete. A dummy in front of `head` makes deleting the head itself an ordinary case.",
        hints=["Two passes: count the length L, then delete node number L-n from the front.",
               "For one pass, advance a `right` pointer n steps first.",
               "Start `left` at a dummy node; move both until `right` is None; then `left.next = left.next.next`."],
        brute_force="Count the length L, then walk L - n - 1 steps and unlink. Two passes, O(L) time, O(1) space — perfectly acceptable, but interviewers usually ask for one pass.",
        approach="`[1,2,3,4,5], n=2`: `right` moves 2 → on node 3. `left` = dummy. Move both: (1,4),(2,5),(3,None). `left` = 3, unlink 4 → `1,2,3,5`.",
        complexity="Time O(L), space O(1).",
        pitfalls="- Without a dummy node, `n == length` (delete the head) needs special handling.\n- Off-by-one in the gap: `left` must stop at the node *before* the target.",
        follow_up="Same gap technique: find the k-th node from the end, rotate a list by k (LeetCode 61).",
    ),
),
# ============================================================================================
dict(
    id="copy-list-with-random-pointer",
    title="Copy List with Random Pointer",
    difficulty="Medium",
    pattern="Linked List — Hash Map / Interweaving",
    leetcode="https://leetcode.com/problems/copy-list-with-random-pointer/",
    neetcode="https://neetcode.io/problems/copy-linked-list-with-random-pointer",
    entry="judge",
    description=r"""
Every node of this linked list has, besides `next`, a pointer `random` that may point to **any** node of
the list or be `None`. Build a **deep copy**: brand-new nodes with the same values, whose `next` and
`random` pointers point into the copy in exactly the same pattern. No pointer of the copy may lead into the
original list, and the original must be left unchanged.

**Constraints**

- 0 to 1000 nodes, `-10^4 <= Node.val <= 10^4`.

**Judge input format:** each test is a list of pairs `[val, random_index]`, where `random_index` is the
position (0-based) of the node that `random` points to, or `None`. The starter defines the three-field
`Node` class for you, and the adapter at the bottom builds the original list, calls your
`copyRandomList(head)` and serialises your copy back into the same pair format. Reusing an original node
or modifying the original produces an error string.

**Example 1:** `[[7,None],[13,0],[11,4],[10,2],[1,0]]` → same list of pairs, but made of new nodes.

**Example 2:** `[[3,None],[3,0],[3,None]]` → `[[3,None],[3,0],[3,None]]`
""",
    starter=RANDOM_NODE + '''class Solution:
    def copyRandomList(self, head: 'Optional[Node]') -> 'Optional[Node]':
        pass
''' + RANDOM_ADAPTER,
    solution=RANDOM_NODE + '''class Solution:
    def copyRandomList(self, head):
        clone = {None: None}
        cur = head
        while cur:
            clone[cur] = Node(cur.val)
            cur = cur.next
        cur = head
        while cur:
            clone[cur].next = clone[cur.next]
            clone[cur].random = clone[cur.random]
            cur = cur.next
        return clone[head]
''' + RANDOM_ADAPTER,
    tests=[
        [[[7, None], [13, 0], [11, 4], [10, 2], [1, 0]]], [[[3, None], [3, 0], [3, None]]], [[[1, 1], [2, 1]]],
        [[]], [[[5, None]]], [[[5, 0]]], [[[1, 2], [2, 0], [3, 1]]], [[[i, None] for i in range(50)]],
        [[[i, 999 - i] for i in range(1000)]], [[[r.randint(-10 ** 4, 10 ** 4), r.choice([None, r.randrange(1000)])] for _ in range(1000)]],
    ],
    examples=2,
    wrong_solutions=[
        RANDOM_NODE + '''class Solution:
    def copyRandomList(self, head):
        return head          # not a copy at all
''' + RANDOM_ADAPTER,
        RANDOM_NODE + '''class Solution:
    def copyRandomList(self, head):
        dummy = tail = Node(0)
        while head:
            tail.next = Node(head.val, None, head.random)   # random points into the ORIGINAL
            tail, head = tail.next, head.next
        return dummy.next
''' + RANDOM_ADAPTER,
    ],
    guide=dict(
        prereqs="Hash maps keyed by object identity; two-pass algorithms.",
        intuition="The hard part is that `random` may point *forward* to a node you have not copied yet. Solve it by separating creation from wiring: first create every copy, recording `original → copy` in a dict; then wire `next` and `random` by looking up the dict.",
        hints=["Pass 1: walk the list and create `Node(cur.val)` for each node, storing it in `clone[cur]`.",
               "Pass 2: `clone[cur].next = clone[cur.next]` and `clone[cur].random = clone[cur.random]`.",
               "Seed the dict with `clone[None] = None` so null pointers need no special case."],
        brute_force="For each node, find the *index* of its random target by scanning from the head (O(n) each), build the copy, then translate indices to copy nodes by scanning again: O(n²) time.",
        approach="""Two passes with a dict. On Example 2 (`[[3,None],[3,0],[3,None]]`): pass 1 makes three new nodes A', B', C'. Pass 2:
A'.next = B', A'.random = None; B'.next = C', B'.random = A'; C'.next = None, C'.random = None.

**O(1)-extra-space variant (interweaving):** insert each copy right after its original (`A → A' → B → B' …`); then
`copy.random = orig.random.next`; finally unzip the two lists, restoring the original.""",
        complexity="Time O(n). Space O(n) for the dict (O(1) extra with interweaving, not counting the output).",
        pitfalls="- Copying `random` directly (`Node(v, None, cur.random)`) points into the original.\n- In the interweaving variant, forgetting to restore the original's `next` pointers.\n- Using values as dict keys — values can repeat.",
        follow_up="Clone Graph (LeetCode 133) uses the same 'old → new' map with DFS/BFS.",
    ),
),
# ============================================================================================
dict(
    id="add-two-numbers",
    title="Add Two Numbers",
    difficulty="Medium",
    pattern="Linked List — Dummy Node + Carry",
    leetcode="https://leetcode.com/problems/add-two-numbers/",
    neetcode="https://neetcode.io/problems/add-two-numbers",
    entry="addTwoNumbers",
    arg_types=["list_node", "list_node"],
    return_type="list_node",
    description=r"""
Two non-negative integers are stored as linked lists of decimal digits in **reverse** order: the head holds
the ones digit, the next node the tens digit, and so on. Return their sum in the same format.

**Constraints**

- Each list has 1 to 100 nodes, every value is a digit `0..9`.
- No leading zeros, except the number 0 itself (`[0]`).

**Example 1:** `l1 = [2,4,3], l2 = [5,6,4]` → `[7,0,8]` (342 + 465 = 807)

**Example 2:** `l1 = [9,9,9,9,9,9,9], l2 = [9,9,9,9]` → `[8,9,9,9,0,0,0,1]`
""" + LL_FORMAT,
    starter=LN + '''class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        pass
''',
    solution='''class Solution:
    def addTwoNumbers(self, l1, l2):
        dummy = tail = ListNode()
        carry = 0
        while l1 or l2 or carry:
            s = carry + (l1.val if l1 else 0) + (l2.val if l2 else 0)
            carry, digit = divmod(s, 10)
            tail.next = ListNode(digit)
            tail = tail.next
            l1 = l1.next if l1 else None
            l2 = l2.next if l2 else None
        return dummy.next
''',
    tests=[[[2, 4, 3], [5, 6, 4]], [[9, 9, 9, 9, 9, 9, 9], [9, 9, 9, 9]], [[0], [0]], [[5], [5]], [[1], [9, 9, 9]],
           [[1, 8], [0]], [[9], [1]], [[r.randint(0, 9) for _ in range(99)] + [7], [r.randint(0, 9) for _ in range(60)] + [3]],
           [[9] * 100, [1]], [[3, 2, 1], [6, 7, 8]]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def addTwoNumbers(self, l1, l2):
        dummy = tail = ListNode()
        carry = 0
        while l1 or l2:                         # drops the final carry
            s = carry + (l1.val if l1 else 0) + (l2.val if l2 else 0)
            carry, digit = divmod(s, 10)
            tail.next = ListNode(digit)
            tail = tail.next
            l1 = l1.next if l1 else None
            l2 = l2.next if l2 else None
        return dummy.next
''',
        '''class Solution:
    def addTwoNumbers(self, l1, l2):
        dummy = tail = ListNode()
        while l1 and l2:                        # ignores carries and unequal lengths
            tail.next = ListNode((l1.val + l2.val) % 10)
            tail, l1, l2 = tail.next, l1.next, l2.next
        return dummy.next
''',
    ],
    guide=dict(
        prereqs="Dummy node; grade-school addition.",
        intuition="Reverse order is a gift: the ones digits come first, exactly the order in which you add by hand, carrying to the left.",
        hints=["Walk both lists at once; a missing digit counts as 0.",
               "Keep a `carry`; each new digit is `(a + b + carry) % 10`, the new carry `(a + b + carry) // 10`.",
               "Keep looping while *either* list remains *or* carry is non-zero."],
        brute_force="Convert each list to a Python int, add, and convert back. It works in Python (big ints) but fails the spirit of the question and does not translate to fixed-width languages.",
        approach="342 + 465: (2+5)=7 c0 → (4+6)=10 → digit 0 c1 → (3+4+1)=8 → `[7,0,8]`. For `[9,9,9,9,9,9,9] + [9,9,9,9]` the final carry produces the extra `1` node.",
        complexity="Time O(max(m, n)), space O(max(m, n)) for the output (O(1) extra).",
        pitfalls="- Losing the last carry (`999 + 1`).\n- Stopping when the shorter list ends.",
        follow_up="Add Two Numbers II (LeetCode 445): digits in forward order — reverse both lists or use stacks.",
    ),
),
# ============================================================================================
dict(
    id="find-the-duplicate-number",
    title="Find the Duplicate Number",
    difficulty="Medium",
    pattern="Linked List — Floyd's Cycle Start",
    leetcode="https://leetcode.com/problems/find-the-duplicate-number/",
    neetcode="https://neetcode.io/problems/find-duplicate-integer",
    entry="findDuplicate",
    description=r"""
An array `nums` holds `n + 1` integers, each between `1` and `n` inclusive. By the pigeonhole principle at
least one value repeats; here exactly **one** value repeats (possibly many times). Return that value
**without modifying the array** and using only O(1) extra space.

**Constraints**

- `1 <= n <= 10^5`, `len(nums) == n + 1`, `1 <= nums[i] <= n`.
- Only one value appears more than once, but it may appear two or more times.

**Example 1:** `nums = [1,3,4,2,2]` → `2`

**Example 2:** `nums = [3,1,3,4,2]` → `3`

**Example 3:** `nums = [3,3,3,3,3]` → `3`

(This is an array problem in disguise — see the guide for why it lives in the linked-list module.)
""",
    starter='''class Solution:
    def findDuplicate(self, nums: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def findDuplicate(self, nums):
        slow = fast = 0
        while True:
            slow = nums[slow]
            fast = nums[nums[fast]]
            if slow == fast:
                break
        slow2 = 0
        while slow != slow2:
            slow = nums[slow]
            slow2 = nums[slow2]
        return slow
''',
    tests=[[[1, 3, 4, 2, 2]], [[3, 1, 3, 4, 2]], [[3, 3, 3, 3, 3]], [[1, 1]], [[2, 2, 2]], [[1, 1, 2]],
           [[2, 5, 9, 6, 9, 3, 8, 9, 7, 1]], [[4, 3, 1, 4, 2]], [_dup_big], [_dup_many], [[1, 4, 4, 2, 4]]],
    wrong_solutions=[
        '''class Solution:
    def findDuplicate(self, nums):
        n = len(nums) - 1
        return sum(nums) - n * (n + 1) // 2      # only right if the value repeats exactly twice
''',
        '''class Solution:
    def findDuplicate(self, nums):
        for i in range(1, len(nums)):
            if nums[i] == nums[i - 1]:           # assumes sorted input
                return nums[i]
        return nums[0]
''',
    ],
    guide=dict(
        prereqs="Floyd's cycle detection **and** finding the cycle start — lesson *Fast and slow pointers*.",
        intuition="Treat each index `i` as a node with an edge `i → nums[i]`. Every value is in `1..n`, so index 0 is never a target: starting from 0 you walk into a structure that must eventually loop. Two different indices pointing to the same value means that value is the node where the 'tail' joins the cycle — the duplicate is the **entrance of the cycle**.",
        hints=["Sorting or a set solves it but violates 'do not modify' or 'O(1) space'.",
               "Consider the functional graph `i → nums[i]` starting from index 0. Where does a cycle begin?",
               "Run Floyd: meet inside the cycle, then move one pointer back to 0 and step both by one; they meet at the duplicate."],
        brute_force="A `set` of seen values (O(n) space), sorting a copy (O(n log n), O(n) space), or binary search on the value range counting `<= mid` (O(n log n) time, O(1) space — a valid alternative!).",
        approach="""`nums = [1,3,4,2,2]`, edges: 0→1, 1→3, 3→2, 2→4, 4→2. Path from 0: 0,1,3,**2**,4,2,4,… The cycle is 2↔4 and its entrance is 2.

Phase 1: slow/fast from 0 until they meet (both at 4 here, say). Phase 2: `slow2 = 0`; step both by one: (4→2, 0→1), (2→4, 1→3), (4→2, 3→2) → meet at **2**.

Why phase 2 works: if the tail has length $a$ and the meeting point is $b$ steps into the cycle of length $C$, then $2(a+b) = a + b + kC$, so $a = kC - b$: walking $a$ more steps from the meeting point lands on the entrance.""",
        complexity="Time O(n), space O(1), array untouched.",
        pitfalls="- Starting the walk at an index other than 0 (0 is guaranteed outside every cycle).\n- Using the sum formula: fails when the duplicate appears 3+ times.\n- Swapping elements into place ('cyclic sort') modifies the array.",
        follow_up="LeetCode 142 (Linked List Cycle II) is the same phase-2 trick on real nodes.",
    ),
),
# ============================================================================================
dict(
    id="lru-cache",
    title="LRU Cache",
    difficulty="Medium",
    pattern="Linked List — Doubly Linked List + Hash Map",
    leetcode="https://leetcode.com/problems/lru-cache/",
    neetcode="https://neetcode.io/problems/lru-cache",
    kind="class",
    entry="LRUCache",
    description=r"""
Design a key-value cache with a fixed `capacity` that evicts the **least recently used** key when it gets full.

- `LRUCache(capacity)` — create the empty cache.
- `get(key)` — return the value for `key`, or `-1` if absent. A successful get counts as a *use*.
- `put(key, value)` — insert or overwrite `key`. This also counts as a use. If inserting a new key makes the
  cache exceed `capacity`, first remove the key that was used longest ago.

Both operations must run in **O(1) average time**.

**Constraints**

- `1 <= capacity <= 3000`, `0 <= key <= 10^4`, `0 <= value <= 10^5`, up to $2 \cdot 10^5$ calls.

**Judge input format:** each test is a pair of lists — operation names and their argument lists. The output
is the list of return values (`None` for the constructor and for `put`).

**Example:**
`["LRUCache","put","put","get","put","get","put","get","get","get"]`,
`[[2],[1,1],[2,2],[1],[3,3],[2],[4,4],[1],[3],[4]]`
→ `[None,None,None,1,None,-1,None,-1,3,4]`
""",
    starter='''class LRUCache:

    def __init__(self, capacity: int):
        pass

    def get(self, key: int) -> int:
        pass

    def put(self, key: int, value: int) -> None:
        pass
''',
    solution='''class _DNode:
    __slots__ = ("key", "val", "prev", "next")

    def __init__(self, key=0, val=0):
        self.key, self.val = key, val
        self.prev = self.next = None


class LRUCache:
    def __init__(self, capacity):
        self.cap = capacity
        self.map = {}
        self.left, self.right = _DNode(), _DNode()   # left = LRU side, right = MRU side
        self.left.next, self.right.prev = self.right, self.left

    def _remove(self, node):
        node.prev.next, node.next.prev = node.next, node.prev

    def _append(self, node):
        last = self.right.prev
        last.next = node
        node.prev, node.next = last, self.right
        self.right.prev = node

    def get(self, key):
        node = self.map.get(key)
        if node is None:
            return -1
        self._remove(node)
        self._append(node)
        return node.val

    def put(self, key, value):
        if key in self.map:
            self._remove(self.map[key])
        node = _DNode(key, value)
        self.map[key] = node
        self._append(node)
        if len(self.map) > self.cap:
            lru = self.left.next
            self._remove(lru)
            del self.map[lru.key]
''',
    tests=[
        [["LRUCache", "put", "put", "get", "put", "get", "put", "get", "get", "get"],
         [[2], [1, 1], [2, 2], [1], [3, 3], [2], [4, 4], [1], [3], [4]]],
        [["LRUCache", "put", "get", "put", "get", "get"], [[1], [2, 1], [2], [3, 2], [2], [3]]],
        [["LRUCache", "get"], [[1], [5]]],
        [["LRUCache", "put", "put", "put", "put", "get", "get"], [[2], [2, 1], [1, 1], [2, 3], [4, 1], [1], [2]]],
        [["LRUCache", "put", "put", "get", "put", "put", "get", "get"], [[2], [1, 1], [2, 2], [1], [1, 10], [3, 3], [2], [1]]],
        [["LRUCache", "put", "put", "put", "get", "get", "get"], [[3], [1, 1], [2, 2], [3, 3], [1], [2], [3]]],
        [["LRUCache", "put", "put", "put", "put", "get", "get", "get", "get"], [[3], [1, 1], [2, 2], [3, 3], [4, 4], [4], [3], [2], [1]]],
        [["LRUCache", "put", "put", "put", "put", "put", "get", "put", "get", "get", "put", "get", "put", "put", "put", "get", "put", "get", "get", "get", "get", "put", "put", "get", "get", "get", "put", "put", "get", "put", "get", "put", "get", "get", "get", "put", "put", "put", "get", "put", "get", "get", "put", "put", "get", "put", "put", "put", "put", "get", "put", "put", "get", "put", "put", "get", "put", "put", "put", "put", "put", "get", "put", "put", "get", "put", "get", "get", "get", "put", "get", "get", "put", "put", "put", "put", "get", "put", "put", "put", "put", "get", "get", "get", "put", "put", "put", "get", "put", "put", "put", "get", "put", "put", "put", "get", "get", "get", "put", "put", "put", "put", "get", "put", "put", "put", "put", "put", "put", "put"],
         [[10], [10, 13], [3, 17], [6, 11], [10, 5], [9, 10], [13], [2, 19], [2], [3], [5, 25], [8], [9, 22], [5, 5], [1, 30], [11], [9, 12], [7], [5], [8], [9], [4, 30], [9, 3], [9], [10], [10], [6, 14], [3, 1], [3], [10, 11], [8], [2, 14], [1], [5], [4], [11, 4], [12, 24], [5, 18], [13], [7, 23], [8], [12], [3, 27], [2, 12], [5], [2, 9], [13, 4], [8, 18], [1, 7], [6], [9, 29], [8, 21], [5], [6, 30], [1, 12], [10], [4, 15], [7, 22], [11, 26], [8, 17], [9, 29], [5], [3, 4], [11, 30], [12], [4, 29], [3], [9], [6], [3, 4], [1], [10], [3, 29], [10, 28], [1, 20], [11, 13], [3], [3, 12], [3, 8], [10, 9], [3, 26], [8], [7], [5], [13, 17], [2, 27], [11, 15], [12], [9, 19], [2, 15], [3, 16], [1], [12, 17], [9, 1], [6, 19], [4], [5], [5], [8, 1], [11, 7], [5, 2], [9, 28], [1], [2, 2], [7, 4], [4, 22], [7, 24], [9, 26], [13, 28], [11, 26]]],
        [_lru_ops, _lru_args],
    ],
    examples=1,
    wrong_solutions=[
        '''class LRUCache:
    # FIFO: get() does not refresh recency
    def __init__(self, capacity):
        self.cap = capacity
        self.d = {}

    def get(self, key):
        return self.d.get(key, -1)

    def put(self, key, value):
        if key in self.d:
            del self.d[key]
        self.d[key] = value
        if len(self.d) > self.cap:
            del self.d[next(iter(self.d))]
''',
        '''class LRUCache:
    # put() on an existing key does not refresh recency
    def __init__(self, capacity):
        self.cap = capacity
        self.d = {}

    def get(self, key):
        if key not in self.d:
            return -1
        v = self.d.pop(key)
        self.d[key] = v
        return v

    def put(self, key, value):
        if key in self.d:
            self.d[key] = value
            return
        self.d[key] = value
        if len(self.d) > self.cap:
            del self.d[next(iter(self.d))]
''',
    ],
    guide=dict(
        prereqs="Doubly linked lists with sentinels and hash maps — lesson *Nodes, pointers and the dummy-node trick*.",
        intuition="You need two things in O(1): find a key (hash map) and reorder by recency (a list where any node can be unlinked and moved to the end in O(1) — a **doubly** linked list). The map stores key → node; the list order is recency, LRU at the front.",
        hints=["A Python list for recency order is O(n) per removal — too slow.",
               "Use a doubly linked list with two sentinel nodes (`left` = least recent, `right` = most recent) so insert/remove never special-case empty lists.",
               "Every `get` hit and every `put` moves the node to the right end; on overflow remove `left.next` and delete its key from the map (store the key in the node!)."],
        brute_force="Store `(key, value, last_used_time)` and on eviction scan for the minimum time: O(capacity) per put.",
        approach="""Operations:

- `_remove(node)`: `node.prev.next = node.next; node.next.prev = node.prev`.
- `_append(node)`: insert just before the `right` sentinel.
- `get`: miss → -1; hit → remove + append, return value.
- `put`: if present remove old node; create node, map it, append; if `len(map) > cap`, evict `left.next`.

Dry run of the example (cap 2): put1, put2 → [1,2]; get1 → [2,1] returns 1; put3 overflows → evict 2 → [1,3]; get2 → -1; put4 evicts 1 → [3,4]; get1 -1, get3 3, get4 4.

Python shortcut: `collections.OrderedDict` with `move_to_end(key)` and `popitem(last=False)` — fine to mention, but interviewers usually want the hand-built version.""",
        complexity="O(1) average per operation (hash map + constant pointer updates). Space O(capacity).",
        pitfalls="- Forgetting to store the key inside the node, so you cannot delete it from the map on eviction.\n- Evicting *before* replacing an existing key (a put on an existing key never evicts).\n- Not refreshing recency on `get` or on `put` of an existing key.",
        follow_up="LFU Cache (LeetCode 460) — evict the least *frequently* used; needs a list per frequency.",
    ),
),
# ============================================================================================
dict(
    id="merge-k-sorted-lists",
    title="Merge k Sorted Lists",
    difficulty="Hard",
    pattern="Linked List — Heap / Divide & Conquer",
    leetcode="https://leetcode.com/problems/merge-k-sorted-lists/",
    neetcode="https://neetcode.io/problems/merge-k-sorted-linked-lists",
    entry="judge",
    return_type="list_node",
    description=r"""
You are given an array of `k` linked lists, each sorted ascending. Merge them all into one sorted linked list
and return its head.

**Constraints**

- `0 <= k <= 10^4`, each list has at most 500 nodes, total nodes $N \le 10^4$.
- `-10^4 <= Node.val <= 10^4`; any list may be empty.

**Judge input format:** the argument is a list of lists of values, e.g. `[[1,4,5],[1,3,4],[2,6]]`. The
adapter at the bottom of the starter converts each inner list into a `ListNode` chain (empty inner list →
`None`) and calls your `mergeKLists(lists)`. Your returned list is printed as a Python list.

**Example 1:** `lists = [[1,4,5],[1,3,4],[2,6]]` → `[1,1,2,3,4,4,5,6]`

**Example 2:** `lists = []` → `[]`

**Example 3:** `lists = [[]]` → `[]`
""",
    starter=LN + '''class Solution:
    def mergeKLists(self, lists: List[Optional[ListNode]]) -> Optional[ListNode]:
        pass
''' + MERGEK_ADAPTER,
    solution='''class Solution:
    def mergeKLists(self, lists):
        heap = [(node.val, i, node) for i, node in enumerate(lists) if node]
        heapq.heapify(heap)
        dummy = tail = ListNode()
        while heap:
            _, i, node = heapq.heappop(heap)
            tail.next = node
            tail = node
            if node.next:
                heapq.heappush(heap, (node.next.val, i, node.next))
        return dummy.next
''' + MERGEK_ADAPTER,
    tests=[
        [[[1, 4, 5], [1, 3, 4], [2, 6]]], [[]], [[[]]], [[[], [1]]], [[[2], [], [1]]], [[[1, 2, 3]]],
        [[[5, 5], [5], [5, 5, 5]]], [[[-3, 0, 9], [-10, 10], [], [1]]],
        [[_sorted_list(r, 100, -10 ** 4, 10 ** 4) for _ in range(100)]],
        [[[r.randint(-10 ** 4, 10 ** 4)] for _ in range(3000)]],
    ],
    wrong_solutions=[
        '''class Solution:
    def mergeKLists(self, lists):
        # merges only the first two lists
        def merge(a, b):
            dummy = tail = ListNode()
            while a and b:
                if a.val <= b.val:
                    tail.next, a = a, a.next
                else:
                    tail.next, b = b, b.next
                tail = tail.next
            tail.next = a or b
            return dummy.next
        if not lists:
            return None
        if len(lists) == 1:
            return lists[0]
        return merge(lists[0], lists[1])
''' + MERGEK_ADAPTER,
    ],
    guide=dict(
        prereqs="*Merge Two Sorted Lists*; heaps (`heapq`).",
        intuition="At every moment the next output node is the smallest among the k current heads. A min-heap of size k hands you that smallest head in O(log k).",
        hints=["Merging lists one at a time into an accumulator is O(k·N) — think about why.",
               "Put the head of every non-empty list in a min-heap; pop the smallest, attach it, push its successor.",
               "Python compares tuples element by element and cannot compare `ListNode`s: push `(val, index, node)` so ties break on the index."],
        brute_force="Collect all N values, sort, rebuild: O(N log N) time, O(N) space. Or merge sequentially: list 1 with 2, the result with 3, … — the accumulator keeps growing, giving O(k·N).",
        approach="""**Heap:** for `[[1,4,5],[1,3,4],[2,6]]` the heap starts with (1,0),(1,1),(2,2). Pop (1,0) → push 4; pop (1,1) → push 3; pop 2 → push 6; pop 3 → push 4; … producing `1,1,2,3,4,4,5,6`.

**Divide & conquer (no heap):** merge pairs (0,1), (2,3), … then pairs of results, like merge sort's merge tree. There are log k rounds, each touching all N nodes: O(N log k), O(1) extra space.""",
        complexity="Time O(N log k): every node passes through a heap of size ≤ k once. Space O(k) for the heap.",
        pitfalls="- Pushing `(val, node)` only — on equal values Python tries `node < node` and raises `TypeError`.\n- Forgetting empty lists (`None`) in the input.\n- Sequential merging times out for large k.",
        follow_up="K-way merge shows up in external sorting and in *Find K Pairs with Smallest Sums*, *Smallest Range Covering Elements from K Lists*.",
    ),
),
# ============================================================================================
dict(
    id="reverse-nodes-in-k-group",
    title="Reverse Nodes in k-Group",
    difficulty="Hard",
    pattern="Linked List — Group Reversal",
    leetcode="https://leetcode.com/problems/reverse-nodes-in-k-group/",
    neetcode="https://neetcode.io/problems/reverse-nodes-in-k-group",
    entry="reverseKGroup",
    arg_types=["list_node", None],
    return_type="list_node",
    description=r"""
Split a linked list into consecutive blocks of `k` nodes and reverse the order of nodes inside each full
block. If the final block has fewer than `k` nodes, leave it as it is. Change links only, not values, and
return the new head.

**Constraints**

- `1 <= k <= n <= 5000`, `0 <= Node.val <= 1000`.
- Follow-up: O(1) extra memory.

**Arguments:** `head` (list format below) and the integer `k`.

**Example 1:** `head = [1,2,3,4,5], k = 2` → `[2,1,4,3,5]`

**Example 2:** `head = [1,2,3,4,5], k = 3` → `[3,2,1,4,5]`
""" + LL_FORMAT,
    starter=LN + '''class Solution:
    def reverseKGroup(self, head: Optional[ListNode], k: int) -> Optional[ListNode]:
        pass
''',
    solution='''class Solution:
    def reverseKGroup(self, head, k):
        dummy = ListNode(0, head)
        group_prev = dummy
        while True:
            kth = group_prev
            for _ in range(k):
                kth = kth.next
                if kth is None:
                    return dummy.next
            group_next = kth.next
            prev, cur = group_next, group_prev.next
            while cur is not group_next:
                cur.next, prev, cur = prev, cur, cur.next
            first = group_prev.next
            group_prev.next = kth
            group_prev = first
''',
    tests=[[[1, 2, 3, 4, 5], 2], [[1, 2, 3, 4, 5], 3], [[1], 1], [[1, 2], 2], [[1, 2, 3, 4, 5], 1],
           [[1, 2, 3, 4, 5], 5], [[1, 2, 3, 4, 5, 6], 3], [[1, 2, 3, 4, 5, 6, 7], 3], [[4, 4, 1], 2],
           [list(range(5000)), 7], [list(range(5000)), 5000], [list(range(4999)), 2]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def reverseKGroup(self, head, k):
        # also reverses the incomplete last group
        vals = []
        while head:
            vals.append(head.val)
            head = head.next
        out = []
        for i in range(0, len(vals), k):
            out += vals[i:i + k][::-1]
        dummy = tail = ListNode()
        for v in out:
            tail.next = ListNode(v)
            tail = tail.next
        return dummy.next
''',
    ],
    guide=dict(
        prereqs="*Reverse Linked List* and dummy nodes; lesson *Reversal, merging and in-place rearrangement*.",
        intuition="Treat the list as a sequence of k-sized segments. For each full segment, reverse it with the usual three-pointer loop, then splice it back between the node before it (`group_prev`) and the node after it (`group_next`).",
        hints=["First check whether k nodes remain: walk k steps from `group_prev`; if you hit `None`, stop.",
               "Reverse the segment with `prev` initialised to `group_next` — then the segment's old first node automatically points to the rest of the list.",
               "After reversing, `group_prev.next` must become the old k-th node, and the next `group_prev` is the segment's old first node."],
        brute_force="Copy values into an array, reverse each full chunk, write values back: O(n) time and O(n) space, and it changes values rather than links.",
        approach="""`[1,2,3,4,5], k=2`, dummy D:

1. group_prev = D, kth = 2, group_next = 3. Reverse `1,2` with prev starting at 3 → `2→1→3`. D.next = 2; group_prev = 1.
2. kth = 4, group_next = 5. Reverse `3,4` → `4→3→5`; `1.next = 4`; group_prev = 3.
3. Walking 2 steps from 3 hits None → return D.next = `2,1,4,3,5`.""",
        complexity="Time O(n): each node is visited a constant number of times (once while counting, once while reversing). Space O(1).",
        pitfalls="- Reversing the final short group.\n- Losing the connection to the previous group (`group_prev.next` must be updated).\n- Updating `group_prev` to `kth` instead of to the old first node.",
        follow_up="Swap Nodes in Pairs (LeetCode 24) is the k = 2 special case; Reverse Linked List II reverses one segment.",
    ),
),
]
