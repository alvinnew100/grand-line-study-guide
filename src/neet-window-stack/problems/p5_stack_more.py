import random

R = random.Random(88002)
LC = "https://leetcode.com/problems/{}/"


def _queue_ops(n, rng):
    ops, args, size = ["MyQueue"], [[]], 0
    for _ in range(n):
        r = rng.random()
        if size == 0 or r < 0.5:
            ops.append("push"); args.append([rng.randint(1, 9)]); size += 1
        elif r < 0.75:
            ops.append("pop"); args.append([]); size -= 1
        elif r < 0.9:
            ops.append("peek"); args.append([])
        else:
            ops.append("empty"); args.append([])
    return [ops, args]


def _queue_fill_drain(n):
    ops = ["MyQueue"] + ["push"] * n + ["pop", "peek"] * (n // 2) + ["empty"]
    args = [[]] + [[i % 9 + 1] for i in range(n)] + [[], []] * (n // 2) + [[]]
    return [ops, args]


def _stack_ops(n, rng):
    ops, args, size = ["MyStack"], [[]], 0
    for _ in range(n):
        r = rng.random()
        if size == 0 or r < 0.5:
            ops.append("push"); args.append([rng.randint(1, 9)]); size += 1
        elif r < 0.75:
            ops.append("pop"); args.append([]); size -= 1
        elif r < 0.9:
            ops.append("top"); args.append([])
        else:
            ops.append("empty"); args.append([])
    return [ops, args]


def _path_big(n, rng):
    parts = []
    for _ in range(n):
        r = rng.random()
        if r < 0.5:
            parts.append(rng.choice(["a", "bb", "c_d", "...", "x.y", ".hidden"]))
        elif r < 0.7:
            parts.append("..")
        elif r < 0.85:
            parts.append(".")
        else:
            parts.append("")
    return "/" + "/".join(parts)


_digits_big = "".join(R.choice("0123456789") for _ in range(50000))
_digits_inc = "".join(str(i % 9 + 1) for i in range(1)) + "1" * 20000 + "9" * 20000
_p132_big = [R.randint(-10 ** 6, 10 ** 6) for _ in range(15000)]
_p132_inc = list(range(15000))
_nge2_big = [R.randint(-10 ** 4, 10 ** 4) for _ in range(15000)]
_nge2_desc = list(range(12000, 0, -1))
_dup_big = "".join(R.choice("ab") for _ in range(50000))
_dup_cascade = "a" * 20000 + "bb" + "a" * 20000 + "b"


def _rand_matrix(m, n, p, rng):
    return [["1" if rng.random() < p else "0" for _ in range(n)] for _ in range(m)]


_mat_big = _rand_matrix(120, 120, 0.85, R)
_mat_ones = [["1"] * 100 for _ in range(100)]
_ssm_big = [R.randint(1, 30000) for _ in range(20000)]

PROBLEMS = [
# ---------------------------------------------------------------- 232
dict(
    id="implement-queue-using-stacks",
    title="Implement Queue using Stacks",
    difficulty="Easy",
    pattern="Stack",
    leetcode=LC.format("implement-queue-using-stacks"),
    kind="class",
    entry="MyQueue",
    description=r"""
Build a first-in-first-out queue class `MyQueue` using **only stack operations** on Python lists (`append`,
`pop()` from the end, look at the last item, test for empty):

- `push(x)` — add `x` to the back of the queue;
- `pop()` — remove and return the item at the front;
- `peek()` — return the front item without removing it;
- `empty()` — return `True` if the queue holds nothing.

`pop` and `peek` are only called on a non-empty queue. Aim for **amortized O(1)** per operation.

**Constraints**

- `1 <= x <= 9`; up to 100 calls on LeetCode (far more in the tests here)

**Example:**

```
ops  = ["MyQueue","push","push","peek","pop","empty"]
args = [[],       [1],   [2],   [],    [],   []]
out  = [null,     null,  null,  1,     1,    false]
```
""",
    starter='''class MyQueue:

    def __init__(self):
        pass

    def push(self, x: int) -> None:
        pass

    def pop(self) -> int:
        pass

    def peek(self) -> int:
        pass

    def empty(self) -> bool:
        pass
''',
    solution='''class MyQueue:
    def __init__(self):
        self.inbox = []
        self.outbox = []

    def _shift(self):
        if not self.outbox:
            while self.inbox:
                self.outbox.append(self.inbox.pop())

    def push(self, x):
        self.inbox.append(x)

    def pop(self):
        self._shift()
        return self.outbox.pop()

    def peek(self):
        self._shift()
        return self.outbox[-1]

    def empty(self):
        return not self.inbox and not self.outbox
''',
    tests=[
        [["MyQueue", "push", "push", "peek", "pop", "empty"], [[], [1], [2], [], [], []]],
        [["MyQueue", "empty"], [[]]],
        [["MyQueue", "push", "pop", "empty"], [[], [7], [], []]],
        [["MyQueue", "push", "push", "push", "pop", "pop", "pop", "empty"], [[], [1], [2], [3], [], [], [], []]],
        [["MyQueue", "push", "push", "pop", "push", "pop", "pop"], [[], [1], [2], [], [3], [], []]],
        [["MyQueue", "push", "peek", "push", "peek", "pop", "peek"], [[], [4], [], [5], [], [], []]],
        [["MyQueue", "push", "push", "pop", "push", "push", "pop", "peek", "empty"], [[], [1], [2], [], [3], [4], [], [], []]],
        [["MyQueue", "push", "empty", "pop", "empty"], [[], [9], [], [], []]],
        _queue_ops(300, R),
        _queue_ops(10000, R),
        _queue_fill_drain(6000),
    ],
    wrong_solutions=[
        '''class MyQueue:
    def __init__(self):
        self.s = []
    def push(self, x):
        self.s.append(x)
    def pop(self):
        return self.s.pop()            # LIFO: this is still a stack
    def peek(self):
        return self.s[-1]
    def empty(self):
        return not self.s
''',
        '''class MyQueue:
    def __init__(self):
        self.inbox, self.outbox = [], []
    def push(self, x):
        self.inbox.append(x)
    def pop(self):
        while self.inbox:              # bug: refills even when outbox still has older items
            self.outbox.append(self.inbox.pop())
        return self.outbox.pop()
    def peek(self):
        while self.inbox:
            self.outbox.append(self.inbox.pop())
        return self.outbox[-1]
    def empty(self):
        return not self.inbox and not self.outbox
''',
    ],
    guide=dict(
        prereqs="Lesson *Stacks: the LIFO toolkit* (stack operations, amortized cost).",
        intuition="""
A stack reverses order. Reverse **twice** and you are back to the original order. Use two stacks: an *inbox*
that receives pushes and an *outbox* that serves pops. Pouring the inbox into the outbox flips the order, so the
oldest item ends up on top of the outbox — exactly where a queue needs it.

The crucial rule: pour **only when the outbox is empty**. Otherwise newer items would land on top of older ones.
""",
        hints=[
            "Pushing everything onto one stack and popping gives reverse order. What does reversing again give?",
            "Use two stacks: push onto one, pop from the other.",
            "Move all items from inbox to outbox only when outbox is empty; then pop/peek the outbox.",
        ],
        brute_force="One stack, and for every `pop` move everything to a temporary stack and back: **O(n)** per pop, O(n²) for n pops — the fill-then-drain test does about 3·10⁷ moves that way.",
        approach="""
**Dry run** push 1, push 2, peek, pop, push 3, pop, pop:

| op | inbox | outbox (top on right) | returns |
|---|---|---|---|
| push 1, push 2 | [1,2] | [] | |
| peek | [] | [2,1] | 1 |
| pop | [] | [2] | 1 |
| push 3 | [3] | [2] | |
| pop | [3] | [] | 2 |
| pop | [] → pour → [] | [3] → [] | 3 |
""",
        complexity="`push` O(1). `pop`/`peek` **amortized O(1)**: every item is moved from inbox to outbox at most once in its life. Space O(n).",
        pitfalls="""
- Pouring while the outbox is not empty scrambles the order.
- `empty()` must check **both** stacks.
- Using `list.pop(0)` breaks the "stack operations only" rule (and is O(n)).
""",
        follow_up="The same two-stack idea, with each stack also tracking its minimum, gives a queue with O(1) `getMin` — the basis of a sliding-window minimum without a deque.",
    ),
),
# ---------------------------------------------------------------- 225
dict(
    id="implement-stack-using-queues",
    title="Implement Stack using Queues",
    difficulty="Easy",
    pattern="Stack",
    leetcode=LC.format("implement-stack-using-queues"),
    kind="class",
    entry="MyStack",
    description=r"""
Build a last-in-first-out stack class `MyStack` using **only queue operations** (add to the back, remove from the
front, look at the front, size, test for empty) — for example on a `collections.deque` using just `append`,
`popleft` and `len`:

- `push(x)` — put `x` on top;
- `pop()` — remove and return the top item;
- `top()` — return the top item without removing it;
- `empty()` — return `True` if the stack holds nothing.

`pop` and `top` are only called on a non-empty stack.

**Constraints**

- `1 <= x <= 9`; up to 100 calls on LeetCode (more in the tests here)

**Example:**

```
ops  = ["MyStack","push","push","top","pop","empty"]
args = [[],       [1],   [2],   [],   [],   []]
out  = [null,     null,  null,  2,    2,    false]
```
""",
    starter='''class MyStack:

    def __init__(self):
        pass

    def push(self, x: int) -> None:
        pass

    def pop(self) -> int:
        pass

    def top(self) -> int:
        pass

    def empty(self) -> bool:
        pass
''',
    solution='''from collections import deque

class MyStack:
    def __init__(self):
        self.q = deque()

    def push(self, x):
        self.q.append(x)
        for _ in range(len(self.q) - 1):      # rotate so the newest item is at the front
            self.q.append(self.q.popleft())

    def pop(self):
        return self.q.popleft()

    def top(self):
        return self.q[0]

    def empty(self):
        return not self.q
''',
    tests=[
        [["MyStack", "push", "push", "top", "pop", "empty"], [[], [1], [2], [], [], []]],
        [["MyStack", "empty"], [[]]],
        [["MyStack", "push", "pop", "empty"], [[], [5], [], []]],
        [["MyStack", "push", "push", "push", "pop", "pop", "pop"], [[], [1], [2], [3], [], [], []]],
        [["MyStack", "push", "push", "pop", "push", "top", "pop", "pop", "empty"], [[], [1], [2], [], [3], [], [], [], []]],
        [["MyStack", "push", "top", "push", "top", "push", "top"], [[], [7], [], [8], [], [9], []]],
        [["MyStack", "push", "push", "pop", "top"], [[], [4], [6], [], []]],
        [["MyStack", "push", "empty", "pop", "empty"], [[], [3], [], [], []]],
        _stack_ops(300, R),
        _stack_ops(4000, R),
    ],
    wrong_solutions=[
        '''from collections import deque
class MyStack:
    def __init__(self):
        self.q = deque()
    def push(self, x):
        self.q.append(x)
    def pop(self):
        return self.q.popleft()        # FIFO: this is still a queue
    def top(self):
        return self.q[0]
    def empty(self):
        return not self.q
''',
        '''from collections import deque
class MyStack:
    def __init__(self):
        self.q = deque()
    def push(self, x):
        self.q.append(x)
        for _ in range(len(self.q)):   # bug: one rotation too many (full circle)
            self.q.append(self.q.popleft())
    def pop(self):
        return self.q.popleft()
    def top(self):
        return self.q[0]
    def empty(self):
        return not self.q
''',
    ],
    guide=dict(
        prereqs="Queues and `collections.deque` (lesson *The monotonic deque*, §1); stack ADT.",
        intuition="""
A queue only lets you take from the front, but a stack must hand back the **newest** item. So arrange for the
newest item to *be* at the front: after adding `x` at the back, take every older item from the front and re-add
it at the back. `x` is now first in line, followed by the older items in their previous order.
""",
        hints=[
            "After appending x, where is it in the queue, and where do you need it?",
            "You can move items from the front to the back one at a time.",
            "Rotate len(q) − 1 times after each push; then pop and top are the queue's front.",
        ],
        brute_force="There is no asymptotically better queue-only design: either `push` or `pop` must be O(n). (A two-queue version moves `n − 1` items on every `pop` instead.)",
        approach="""
**Dry run** push 1, push 2, push 3 (front on the left):

| op | queue after |
|---|---|
| push 1 | [1] |
| push 2 | [1,2] → rotate 1 → [2,1] |
| push 3 | [2,1,3] → rotate 2 → [3,2,1] |
| pop | returns 3, queue [2,1] |
""",
        complexity="`push` **O(n)**, `pop`/`top`/`empty` O(1). Space O(n).",
        pitfalls="""
- Rotating `len(q)` times instead of `len(q) − 1` brings the queue back to where it started.
- Using `deque.pop()` (from the back) is a stack operation — not allowed by the rules.
""",
        follow_up="Compare with *Implement Queue using Stacks*: there, two stacks give amortized O(1); here a linear-time operation is unavoidable.",
    ),
),
# ---------------------------------------------------------------- 71
dict(
    id="simplify-path",
    title="Simplify Path",
    difficulty="Medium",
    pattern="Stack",
    leetcode=LC.format("simplify-path"),
    entry="simplifyPath",
    description=r"""
You are given an absolute Unix-style file path (it starts with `/`). Return its shortest equivalent, the
*canonical* path, following these rules:

- `.` means "this directory" and can be dropped;
- `..` means "go up one directory" (at the root it does nothing);
- several slashes in a row count as one;
- any other name — including names like `...` or `.hidden` — is an ordinary directory or file name.

The result starts with a single `/`, separates names with a single `/`, and has no trailing `/` (unless it is
only the root `/`).

**Constraints**

- `1 <= len(path) <= 3000` (longer in the tests here)
- letters, digits, `.`, `_` and `/`

**Example 1:** `"/home/"` → `"/home"`.

**Example 2:** `"/home/user/Documents/../Pictures"` → `"/home/user/Pictures"`.

**Example 3:** `"/../"` → `"/"`.
""",
    starter='''class Solution:
    def simplifyPath(self, path: str) -> str:
        pass
''',
    solution='''class Solution:
    def simplifyPath(self, path):
        st = []
        for part in path.split("/"):
            if part == "" or part == ".":
                continue
            if part == "..":
                if st:
                    st.pop()
            else:
                st.append(part)
        return "/" + "/".join(st)
''',
    tests=[
        ["/home/"],
        ["/home/user/Documents/../Pictures"],
        ["/../"],
        ["/home//foo/"],
        ["/.../a/../b/c/../d/./"],
        ["/"],
        ["/a/./b/../../c/"],
        ["/a/../../b/../c//.//"],
        ["/a//b////c/d//././/.."],
        ["/.hidden/..hidden/x.."],
        ["/a/b/c/../../../../.."],
        [_path_big(20000, R)],
        ["/a" * 20000 + "/.." * 19990],
    ],
    wrong_solutions=[
        '''class Solution:
    def simplifyPath(self, path):
        st = []
        for part in path.split("/"):
            if part == "" or part == ".":
                continue
            if part == "..":
                st.pop()                      # bug: crashes when already at the root
            else:
                st.append(part)
        return "/" + "/".join(st)
''',
        '''class Solution:
    def simplifyPath(self, path):
        st = []
        for part in path.split("/"):
            if not part or set(part) == {"."}:   # bug: treats "..." as a special name
                if part == ".." and st:
                    st.pop()
                continue
            st.append(part)
        return "/" + "/".join(st)
''',
    ],
    guide=dict(
        prereqs="Stacks; `str.split` and `str.join`.",
        intuition="""
Walk through the names between slashes. A normal name takes you one level **deeper**; `..` **undoes** the most
recent step deeper. "Undo the most recent" is what a stack does: push names, pop on `..`.
""",
        hints=[
            "Split the path on '/'. What kinds of pieces can you get?",
            "Empty strings and '.' are ignored; '..' removes the last kept name (if any); everything else is kept.",
            "Keep the names in a list used as a stack and return '/' + '/'.join(stack).",
        ],
        brute_force="Repeatedly search the string for patterns such as `//`, `/./` and `/name/../` and rewrite it until nothing changes: each rewrite copies the string, **O(n²)** overall, and the pattern handling is error-prone.",
        approach="""
**Dry run** `"/a/./b/../../c/"` → pieces `["", "a", ".", "b", "..", "..", "c", ""]`:

| piece | stack after |
|---|---|
| a | [a] |
| . | [a] |
| b | [a, b] |
| .. | [a] |
| .. | [] |
| c | [c] |

Result `"/c"`.
""",
        complexity="Time **O(n)**, space **O(n)**.",
        pitfalls="""
- `..` at the root must do nothing (guard the pop).
- `...` and names starting with a dot are ordinary names.
- An empty stack must give `"/"`, which `"/" + "/".join([])` does.
""",
        follow_up="Resolving *relative* paths needs a starting directory stack; real systems must also handle symbolic links.",
    ),
),
# ---------------------------------------------------------------- 402
dict(
    id="remove-k-digits",
    title="Remove K Digits",
    difficulty="Medium",
    pattern="Monotonic Stack",
    leetcode=LC.format("remove-k-digits"),
    entry="removeKdigits",
    description=r"""
`num` is a string holding a non-negative integer (no leading zeros unless it is `"0"`). Delete exactly `k` of its
digits so that the remaining digits, kept in their original order, form the **smallest possible number**.
Return it as a string without leading zeros; return `"0"` if nothing is left.

**Constraints**

- `1 <= k <= len(num) <= 10^5`

**Example 1:** `num = "1432219", k = 3` → `"1219"`.

**Example 2:** `num = "10200", k = 1` → `"200"`.

**Example 3:** `num = "10", k = 2` → `"0"`.
""",
    starter='''class Solution:
    def removeKdigits(self, num: str, k: int) -> str:
        pass
''',
    solution='''class Solution:
    def removeKdigits(self, num, k):
        st = []
        for d in num:
            while k and st and st[-1] > d:
                st.pop()
                k -= 1
            st.append(d)
        if k:
            st = st[:len(st) - k]
        return "".join(st).lstrip("0") or "0"
''',
    tests=[
        ["1432219", 3],
        ["10200", 1],
        ["10", 2],
        ["9", 1],
        ["12345", 2],
        ["54321", 2],
        ["112", 1],
        ["100", 1],
        ["1234567890", 9],
        ["1111", 2],
        ["10001", 4],
        [_digits_big, 20000],
        [_digits_inc, 20000],
        [_digits_big, 49999],
    ],
    wrong_solutions=[
        '''class Solution:
    def removeKdigits(self, num, k):
        st = []
        for d in num:
            while k and st and st[-1] > d:
                st.pop(); k -= 1
            st.append(d)
        if k:
            st = st[:len(st) - k]
        return "".join(st) or "0"              # bug: leading zeros kept
''',
        '''class Solution:
    def removeKdigits(self, num, k):
        st = []
        for d in num:
            while k and st and st[-1] > d:
                st.pop(); k -= 1
            st.append(d)
        return "".join(st).lstrip("0") or "0"  # bug: unused removals are forgotten
''',
        '''class Solution:
    def removeKdigits(self, num, k):
        digits = sorted(num)[:len(num) - k]    # keeps the smallest digits but loses their order
        return "".join(digits).lstrip("0") or "0"
''',
    ],
    guide=dict(
        prereqs="Lesson *Monotonic stacks* (§8 shows this exact pattern).",
        intuition="""
The leftmost digits matter most. If a digit is **larger than the digit right after it**, deleting it makes the
number smaller at that position — the best possible use of a deletion. So scan left to right keeping a stack of
kept digits; while the top is larger than the incoming digit and deletions remain, pop it. The kept digits end
up non-decreasing. If deletions are left over at the end, remove them from the tail (the largest remaining digits).
""",
        hints=[
            "Which single digit would you delete from 1432219 to get the smallest result?",
            "The first digit that is bigger than its right neighbour (the 4).",
            "Monotonic stack: pop while top > current and k > 0. Afterwards cut k more from the end and strip leading zeros.",
        ],
        brute_force="Delete one digit at a time, each time scanning for the first 'drop': **O(n·k)** — 10⁹ for the big test. Trying all subsets is exponential.",
        approach="""
**Dry run** `"1432219"`, `k = 3`:

| digit | pops | stack | k left |
|---|---|---|---|
| 1 | | 1 | 3 |
| 4 | | 14 | 3 |
| 3 | 4 | 13 | 2 |
| 2 | 3 | 12 | 1 |
| 2 | | 122 | 1 |
| 1 | 2 | 121 | 0 |
| 9 | | 1219 | 0 |
""",
        complexity="Time **O(n)** (each digit pushed and popped at most once), space **O(n)**.",
        pitfalls="""
- Leftover `k` (e.g. `"12345"`): remove from the end.
- Leading zeros (`"10200"` → `"0200"` → `"200"`).
- Empty result must be `"0"`.
- Pop only on strictly greater; popping equal digits wastes deletions.
""",
        follow_up="*Create Maximum Number* (321) and *Smallest Subsequence of Distinct Characters* (1081) use the same greedy stack.",
    ),
),
# ---------------------------------------------------------------- 456
dict(
    id="132-pattern",
    title="132 Pattern",
    difficulty="Medium",
    pattern="Monotonic Stack",
    leetcode=LC.format("132-pattern"),
    entry="find132pattern",
    description=r"""
Decide whether the list `nums` contains three positions `i < j < k` (not necessarily adjacent) whose values
satisfy

`nums[i] < nums[k] < nums[j]`

— a small value, later a big value, later still a value strictly in between (the shape "1-3-2"). Return `True`
or `False`.

**Constraints**

- `1 <= len(nums) <= 2·10^5` (1.5·10^4 in the tests here)
- `-10^9 <= nums[i] <= 10^9`

**Example 1:** `nums = [1,2,3,4]` → `False`.

**Example 2:** `nums = [3,1,4,2]` → `True` (1, 4, 2).

**Example 3:** `nums = [-1,3,2,0]` → `True`.
""",
    starter='''class Solution:
    def find132pattern(self, nums: List[int]) -> bool:
        pass
''',
    solution='''class Solution:
    def find132pattern(self, nums):
        st = []                       # candidates for the "3", decreasing from bottom to top
        third = float("-inf")         # best (largest) "2" that has a bigger "3" to its left
        for x in reversed(nums):
            if x < third:
                return True
            while st and st[-1] < x:
                third = st.pop()
            st.append(x)
        return False
''',
    tests=[
        [[1, 2, 3, 4]],
        [[3, 1, 4, 2]],
        [[-1, 3, 2, 0]],
        [[1]],
        [[1, 2]],
        [[3, 5, 0, 3, 4]],
        [[1, 0, 1, -4, -3]],
        [[2, 2, 2]],
        [[1, 3, 3]],
        [[1, 3, 2]],
        [[4, 3, 2, 1]],
        [[1, 4, 0, -1, -2, -3, -1, -2]],
        [_p132_inc],
        [_p132_inc + [14998.5]],
        [_p132_big],
    ],
    wrong_solutions=[
        '''class Solution:
    def find132pattern(self, nums):
        for i in range(len(nums) - 2):            # only adjacent triples
            if nums[i] < nums[i + 2] < nums[i + 1]:
                return True
        return False
''',
        '''class Solution:
    def find132pattern(self, nums):
        st, third = [], float("-inf")
        for x in reversed(nums):
            if x <= third:                        # bug: needs strictly smaller
                return True
            while st and st[-1] <= x:
                third = st.pop()
            st.append(x)
        return False
''',
    ],
    guide=dict(
        prereqs="Monotonic stack (lesson 5); scanning from the right.",
        intuition="""
Scan from the **right** and treat the current value as the candidate "1". For it to work you need, somewhere to
its right, a "3" followed by a "2" with 2 < 3. Keep the **largest possible "2"** seen so far (`third`) — a larger
"2" makes it easier to find a "1" below it.

How do you know a value is a legitimate "2"? It must have a bigger value to its left. When the scan meets a
value `x` bigger than values on the stack, those popped values lie to the right of `x` and are smaller — each is
a valid "2" with `x` as its "3". Record the last (largest) one popped.
""",
        hints=[
            "Fix the middle element? The left one? Try scanning right-to-left and looking for the '1'.",
            "Maintain the best '2' value: the largest value that has something bigger to its left (within the scanned part).",
            "Decreasing stack from the right: while stack top < x, third = pop. If any later x < third, return True.",
        ],
        brute_force="All triples: O(n³). Fix `j`, keep the minimum to its left and scan right for a value in between: **O(n²)** — 10⁸ steps on an increasing list of 15 000.",
        approach="""
**Dry run** `[3,1,4,2]` from the right:

| x | check x < third | pops | third | stack |
|---|---|---|---|---|
| 2 | no (−∞) | | −∞ | [2] |
| 4 | no | 2 | 2 | [4] |
| 1 | **1 < 2 → True** | | | |

Here 4 is the "3", 2 the "2", 1 the "1".
""",
        complexity="Time **O(n)**, space **O(n)**.",
        pitfalls="""
- All inequalities are strict: `[1,3,3]` and `[2,2,2]` are False.
- The three values need not be adjacent.
- `third` only ever increases, because popped values are larger than previously popped ones.
""",
        follow_up="A left-to-right version keeps prefix minimums as the '1' and a stack of '2' candidates; both are O(n).",
    ),
),
# ---------------------------------------------------------------- 503
dict(
    id="next-greater-element-ii",
    title="Next Greater Element II",
    difficulty="Medium",
    pattern="Monotonic Stack",
    leetcode=LC.format("next-greater-element-ii"),
    entry="nextGreaterElements",
    description=r"""
`nums` is a **circular** list: after the last element comes the first again. For every element, find the first
strictly greater value you meet when walking forward (wrapping around at most once). If there is none, the
answer for that element is `-1`. Return the list of answers.

**Constraints**

- `1 <= len(nums) <= 10^4` (1.5·10^4 in the tests here)
- `-10^9 <= nums[i] <= 10^9`

**Example 1:** `nums = [1,2,1]` → `[2,-1,2]`.

**Example 2:** `nums = [1,2,3,4,3]` → `[2,3,4,-1,4]`.
""",
    starter='''class Solution:
    def nextGreaterElements(self, nums: List[int]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def nextGreaterElements(self, nums):
        n = len(nums)
        ans = [-1] * n
        st = []
        for i in range(2 * n):
            x = nums[i % n]
            while st and nums[st[-1]] < x:
                ans[st.pop()] = x
            if i < n:
                st.append(i)
        return ans
''',
    tests=[
        [[1, 2, 1]],
        [[1, 2, 3, 4, 3]],
        [[5]],
        [[5, 5, 5]],
        [[3, 2, 1]],
        [[1, 2, 3]],
        [[2, 1, 2, 4, 3]],
        [[-1, -2, -3, 0]],
        [[100, 1, 11, 1, 120, 111, 123, 1, -1, -100]],
        [[1, 1, 1, 2]],
        [_nge2_big],
        [_nge2_desc],
    ],
    wrong_solutions=[
        '''class Solution:
    def nextGreaterElements(self, nums):
        ans, st = [-1] * len(nums), []
        for i, x in enumerate(nums):               # bug: no wrap-around
            while st and nums[st[-1]] < x:
                ans[st.pop()] = x
            st.append(i)
        return ans
''',
        '''class Solution:
    def nextGreaterElements(self, nums):
        n = len(nums)
        ans, st = [-1] * n, []
        for i in range(2 * n):
            x = nums[i % n]
            while st and nums[st[-1]] <= x:        # bug: equal is not greater
                ans[st.pop()] = x
            if i < n:
                st.append(i)
        return ans
''',
    ],
    guide=dict(
        prereqs="*Next Greater Element I* / *Daily Temperatures* (lesson 5).",
        intuition="""
Solve the ordinary next-greater problem, then let the elements still waiting on the stack look at the list
**once more from the start**. Walking the indices `0 … 2n−1` and reading `nums[i % n]` simulates a second lap
without building a doubled list. Only push indices during the first lap — in the second lap elements only
*answer* the ones still waiting.
""",
        hints=[
            "What would the answer be if the list were written out twice in a row?",
            "Iterate i from 0 to 2n − 1 and use nums[i % n].",
            "Push an index only when i < n; pop and answer while the stack top's value is smaller than the current value.",
        ],
        brute_force="For each element scan up to `n − 1` positions forward with wrap-around: **O(n²)** — 1.4·10⁸ on a decreasing list of 12 000.",
        approach="""
**Dry run** `[1,2,1]`:

| i | x | pops → answer | stack (indices) |
|---|---|---|---|
| 0 | 1 | | [0] |
| 1 | 2 | 0 → 2 | [1] |
| 2 | 1 | | [1,2] |
| 3 | 1 | | [1,2] |
| 4 | 2 | 2 → 2 | [1] |
| 5 | 1 | | [1] |

Index 1 (the maximum) keeps `-1`. Result `[2,-1,2]`.
""",
        complexity="Time **O(n)** (2n steps, each index pushed once and popped at most once), space **O(n)**.",
        pitfalls="""
- Pushing during the second lap gives duplicates on the stack (harmless but wasteful) — or wrong answers if you store values instead of indices.
- Strictly greater: with equal values everywhere, all answers are `-1`.
""",
        follow_up="*Next Greater Element III* (556) is unrelated in technique (next permutation of digits) despite the name.",
    ),
),
# ---------------------------------------------------------------- 1209
dict(
    id="remove-all-adjacent-duplicates-in-string-ii",
    title="Remove All Adjacent Duplicates in String II",
    difficulty="Medium",
    pattern="Stack",
    leetcode=LC.format("remove-all-adjacent-duplicates-in-string-ii"),
    entry="removeDuplicates",
    description=r"""
Given a lowercase string `s` and an integer `k`, repeatedly do this until it is no longer possible: find `k`
**equal letters next to each other**, delete them, and close the gap (which may bring new equal letters
together). Return the final string — it is the same whatever order the deletions are made in.

**Constraints**

- `1 <= len(s) <= 10^5`, `2 <= k <= 10^4`

**Example 1:** `s = "abcd", k = 2` → `"abcd"`.

**Example 2:** `s = "deeedbbcccbdaa", k = 3` → `"aa"`.

**Example 3:** `s = "pbbcggttciiippooaais", k = 2` → `"ps"`.
""",
    starter='''class Solution:
    def removeDuplicates(self, s: str, k: int) -> str:
        pass
''',
    solution='''class Solution:
    def removeDuplicates(self, s, k):
        st = []                         # [letter, run length]
        for ch in s:
            if st and st[-1][0] == ch:
                st[-1][1] += 1
                if st[-1][1] == k:
                    st.pop()
            else:
                st.append([ch, 1])
        return "".join(c * n for c, n in st)
''',
    tests=[
        ["abcd", 2],
        ["deeedbbcccbdaa", 3],
        ["pbbcggttciiippooaais", 2],
        ["a", 2],
        ["aa", 2],
        ["aaa", 2],
        ["aaaa", 3],
        ["abba", 2],
        ["aabbccddeeffgghh", 2],
        ["yfttttfbbbbnnnnffbgffffgbbbbgssssgthyyyy", 4],
        [_dup_big, 2],
        [_dup_big, 3],
        [_dup_cascade, 3],
        ["ab" * 10000 + "ba" * 10000, 2],
    ],
    wrong_solutions=[
        '''class Solution:
    def removeDuplicates(self, s, k):
        from itertools import groupby
        out = []
        for ch, grp in groupby(s):               # one pass only: no cascading
            out.append(ch * (len(list(grp)) % k))
        return "".join(out)
''',
        '''class Solution:
    def removeDuplicates(self, s, k):
        st = []
        for ch in s:
            if st and st[-1][0] == ch:
                st[-1][1] += 1
                if st[-1][1] >= k:
                    st[-1][1] = 0                # bug: empty run stays and blocks merging
            else:
                st.append([ch, 1])
        return "".join(c * n for c, n in st)
''',
    ],
    guide=dict(
        prereqs="Stacks that store extra information per entry (*Min Stack*, *Online Stock Span*).",
        intuition="""
A deletion only affects what is **next to** the deleted block — the most recent surviving letters. Keep the
survivors on a stack, compressed as `(letter, run length)`. A new letter either extends the run on top or starts
a new run. When a run reaches length `k` it disappears, which automatically exposes the run below it to the next
letter — that is the "cascade".
""",
        hints=[
            "After deleting a block, which letters become neighbours?",
            "The run just before the block and whatever comes next. A stack of survivors models that.",
            "Stack of [letter, count]: same letter as top → count += 1 and pop when it hits k; otherwise push [letter, 1].",
        ],
        brute_force="Scan for a block of `k`, delete it, start again: each deletion is O(n) and there can be n/k of them — **O(n²/k)**. The cascade test (`\"a\"*20000 + \"bb\" + \"a\"*20000 + \"b\"`) hurts.",
        approach="""
**Dry run** `"deeedbbcccbdaa"`, `k = 3`:

`d` → [d1]; `eee` → e reaches 3, popped → [d1]; `d` → [d2]; `bb` → [d2,b2]; `ccc` → popped → [d2,b2];
`b` → b reaches 3, popped → [d2]; `d` → d reaches 3, popped → []; `aa` → [a2]. Result `"aa"`.
""",
        complexity="Time **O(n)**, space **O(n)**.",
        pitfalls="""
- A single pass with `groupby` misses blocks that form only after a deletion.
- Remove the run from the stack when it hits `k`; leaving a zero-length run prevents the neighbours from merging.
- A run longer than `k` keeps `length mod k` letters — the counter handles this naturally.
""",
        follow_up="*Remove All Adjacent Duplicates In String* (1047) is the `k = 2` special case; *Candy Crush 1D* style problems use the same stack.",
    ),
),
# ---------------------------------------------------------------- 85
dict(
    id="maximal-rectangle",
    title="Maximal Rectangle",
    difficulty="Hard",
    pattern="Monotonic Stack",
    leetcode=LC.format("maximal-rectangle"),
    entry="maximalRectangle",
    description=r"""
`matrix` is a grid of the **strings** `"0"` and `"1"`. Find the largest axis-aligned rectangle that contains only
`"1"`s and return its area (number of cells).

**Constraints**

- `1 <= rows, cols <= 200`

**Example 1:**

```
matrix = [["1","0","1","0","0"],
          ["1","0","1","1","1"],
          ["1","1","1","1","1"],
          ["1","0","0","1","0"]]   →  6
```

**Example 2:** `matrix = [["0"]]` → `0`.

**Example 3:** `matrix = [["1"]]` → `1`.
""",
    starter='''class Solution:
    def maximalRectangle(self, matrix: List[List[str]]) -> int:
        pass
''',
    solution='''class Solution:
    def maximalRectangle(self, matrix):
        if not matrix or not matrix[0]:
            return 0
        n = len(matrix[0])
        heights = [0] * (n + 1)          # last slot stays 0: the sentinel
        best = 0
        for row in matrix:
            for j in range(n):
                heights[j] = heights[j] + 1 if row[j] == "1" else 0
            st = []
            for i in range(n + 1):
                h = heights[i]
                while st and heights[st[-1]] >= h:
                    top = heights[st.pop()]
                    left = st[-1] if st else -1
                    area = top * (i - left - 1)
                    if area > best:
                        best = area
                st.append(i)
        return best
''',
    tests=[
        [[["1", "0", "1", "0", "0"], ["1", "0", "1", "1", "1"], ["1", "1", "1", "1", "1"], ["1", "0", "0", "1", "0"]]],
        [[["0"]]],
        [[["1"]]],
        [[["1", "1"], ["1", "1"]]],
        [[["0", "1"], ["1", "0"]]],
        [[["1", "1", "1", "1"]]],
        [[["1"], ["1"], ["0"], ["1"]]],
        [[["0", "0"], ["0", "0"]]],
        [[["1", "0", "1", "1", "1"], ["0", "1", "0", "1", "0"], ["1", "1", "0", "1", "1"], ["1", "1", "0", "1", "1"], ["0", "1", "1", "1", "1"]]],
        [[["1", "1", "0"], ["1", "1", "1"], ["0", "1", "1"]]],
        [_mat_big],
        [_mat_ones],
        [_rand_matrix(60, 150, 0.6, R)],
    ],
    wrong_solutions=[
        '''class Solution:
    def maximalRectangle(self, matrix):
        n = len(matrix[0])
        heights, best = [0] * n, 0
        for row in matrix:
            for j in range(n):
                heights[j] = heights[j] + 1 if row[j] == "1" else 0
            st = []
            for i in range(n):                       # bug: no sentinel, the stack is never flushed
                while st and heights[st[-1]] >= heights[i]:
                    top = heights[st.pop()]
                    left = st[-1] if st else -1
                    best = max(best, top * (i - left - 1))
                st.append(i)
        return best
''',
        '''class Solution:
    def maximalRectangle(self, matrix):
        m, n = len(matrix), len(matrix[0])
        dp = [[0] * (n + 1) for _ in range(m + 1)]   # this finds the largest SQUARE
        best = 0
        for i in range(m):
            for j in range(n):
                if matrix[i][j] == "1":
                    dp[i + 1][j + 1] = 1 + min(dp[i][j], dp[i][j + 1], dp[i + 1][j])
                    best = max(best, dp[i + 1][j + 1])
        return best * best
''',
        '''class Solution:
    def maximalRectangle(self, matrix):
        n = len(matrix[0])
        heights, best = [0] * (n + 1), 0
        for row in matrix:
            for j in range(n):
                if row[j] == "1":                    # bug: heights never reset on a "0"
                    heights[j] += 1
            st = []
            for i in range(n + 1):
                while st and heights[st[-1]] >= heights[i]:
                    top = heights[st.pop()]
                    left = st[-1] if st else -1
                    best = max(best, top * (i - left - 1))
                st.append(i)
        return best
''',
    ],
    guide=dict(
        prereqs="*Largest Rectangle in Histogram* — solve that first; this problem calls it once per row.",
        intuition="""
Stand on any row and look **up**: above each column there is a pile of consecutive `1`s ending at this row.
Those pile heights form a **histogram**, and every all-ones rectangle whose bottom edge lies on this row is a
rectangle under that histogram. So: update the heights row by row (a `1` adds one, a `0` resets to zero) and run
the histogram algorithm on each row. The best over all rows is the answer.
""",
        hints=[
            "Fix the bottom row of the rectangle. What do the columns above it look like?",
            "heights[j] = number of consecutive '1's ending at the current row in column j.",
            "For each row, update heights then compute the largest rectangle in that histogram with a monotonic stack.",
        ],
        brute_force="Enumerate every pair of corners and check that the rectangle is all ones: O((mn)³). Fixing the top-left corner and extending is O((mn)²) — hopeless at 120 × 120.",
        approach="""
**Dry run** on example 1 — heights after each row:

| row | heights | best rectangle in this histogram |
|---|---|---|
| 0 | 1 0 1 0 0 | 1 |
| 1 | 2 0 2 1 1 | 3 |
| 2 | 3 1 3 2 2 | **6** (columns 2–4, height 2) |
| 3 | 4 0 0 3 0 | 4 |

Answer 6.
""",
        complexity="Time **O(rows × cols)** — one O(cols) histogram pass per row. Space **O(cols)**.",
        pitfalls="""
- The cells are **strings**: compare with `"1"`, not `1`.
- Reset a column's height to 0 on a `"0"`.
- Keep the sentinel so rectangles touching the right edge are counted.
- The largest *square* DP is a different problem.
""",
        follow_up="*Maximal Square* (221) has a simpler DP. *Count Submatrices With All Ones* (1504) counts instead of maximising, with the same heights idea.",
    ),
),
# ---------------------------------------------------------------- 907
dict(
    id="sum-of-subarray-minimums",
    title="Sum of Subarray Minimums",
    difficulty="Medium",
    pattern="Monotonic Stack",
    leetcode=LC.format("sum-of-subarray-minimums"),
    entry="sumSubarrayMins",
    description=r"""
For every contiguous subarray of `arr`, take its minimum value. Return the **sum of all those minimums**, modulo
`10^9 + 7`.

**Constraints**

- `1 <= len(arr) <= 3·10^4`
- `1 <= arr[i] <= 3·10^4`

**Example 1:** `arr = [3,1,2,4]` → `17`
(minimums of the 10 subarrays: 3, 1, 2, 4, 1, 1, 2, 1, 1, 1).

**Example 2:** `arr = [11,81,94,43,3]` → `444`.
""",
    starter='''class Solution:
    def sumSubarrayMins(self, arr: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def sumSubarrayMins(self, arr):
        MOD = 10 ** 9 + 7
        st = []                 # indices, values increasing
        total = 0
        for i in range(len(arr) + 1):
            cur = arr[i] if i < len(arr) else 0     # sentinel smaller than everything
            while st and arr[st[-1]] >= cur:
                j = st.pop()
                left = st[-1] if st else -1
                total += arr[j] * (j - left) * (i - j)
            st.append(i)
        return total % MOD
''',
    tests=[
        [[3, 1, 2, 4]],
        [[11, 81, 94, 43, 3]],
        [[5]],
        [[2, 2]],
        [[71, 55, 82, 55]],
        [[1, 2, 3]],
        [[3, 2, 1]],
        [[1, 1, 1, 1]],
        [[2, 9, 7, 8, 3, 4, 6, 1]],
        [[30000] * 10],
        [_ssm_big],
        [list(range(1, 15001))],
        [[30000] * 20000],
    ],
    wrong_solutions=[
        '''class Solution:
    def sumSubarrayMins(self, arr):
        MOD, n = 10 ** 9 + 7, len(arr)
        left, right = [0] * n, [0] * n
        st = []
        for i in range(n):
            while st and arr[st[-1]] >= arr[i]: st.pop()
            left[i] = i - (st[-1] if st else -1)
            st.append(i)
        st = []
        for i in range(n - 1, -1, -1):
            while st and arr[st[-1]] >= arr[i]: st.pop()      # bug: both sides non-strict -> duplicates lost
            right[i] = (st[-1] if st else n) - i
            st.append(i)
        return sum(a * l * r for a, l, r in zip(arr, left, right)) % MOD
''',
        '''class Solution:
    def sumSubarrayMins(self, arr):
        st, total = [], 0
        for i in range(len(arr) + 1):
            cur = arr[i] if i < len(arr) else 0
            while st and arr[st[-1]] >= cur:
                j = st.pop()
                left = st[-1] if st else -1
                total += arr[j] * (j - left) * (i - j)
            st.append(i)
        return total                                           # bug: missing modulo
''',
    ],
    guide=dict(
        prereqs="Previous/next smaller element with a monotonic stack (lesson 5, histogram problem).",
        intuition="""
Instead of looking at each subarray and asking "what is your minimum?", look at each element and ask
"**for how many subarrays am I the minimum?**" (this switch is called the *contribution technique*).

Element `j` is the minimum of a subarray exactly when the subarray starts after the previous smaller element and
ends before the next smaller element. If there are `L` possible starts and `R` possible ends, that is `L × R`
subarrays, contributing `arr[j] × L × R` to the total.
""",
        hints=[
            "Count, for each element, the subarrays in which it is the minimum.",
            "Those subarrays start in (previous smaller, j] and end in [j, next smaller). Count = (j − left) × (right − j).",
            "To avoid double counting equal values, be strict on one side and non-strict on the other. A single increasing stack with pops on >= does this.",
        ],
        brute_force="For each start, extend while tracking the running minimum: **O(n²)** — 4.5·10⁸ for n = 30 000.",
        approach="""
**Dry run** `[3,1,2,4]` (plus sentinel 0 at index 4):

| popped j | value | left | right i | (j−left)(i−j) | contribution |
|---|---|---|---|---|---|
| 0 | 3 | −1 | 1 | 1·1 | 3 |
| 3 | 4 | 2 | 4 | 1·1 | 4 |
| 2 | 2 | 1 | 4 | 1·2 | 4 |
| 1 | 1 | −1 | 4 | 2·3 | 6 |

Total 17.

**Ties:** with `[2,2]`, popping on `>=` makes the second 2 the "next smaller-or-equal" of the first, while the
first is *not* the previous smaller of the second — so the subarray `[2,2]` is counted exactly once.
""",
        complexity="Time **O(n)**, space **O(n)**.",
        pitfalls="""
- Equal values: strict on both sides counts some subarrays twice; non-strict on both sides misses some.
- Take the result modulo `10^9 + 7`.
- Remember the sentinel (or flush the stack) at the end.
""",
        follow_up="*Sum of Subarray Ranges* (2104) = sum of maximums − sum of minimums. *Largest Rectangle in Histogram* uses the same left/right boundaries.",
    ),
),
]
