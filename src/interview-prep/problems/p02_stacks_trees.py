import random
from collections import deque

R = random.Random(23)
G = ("prereqs", "intuition", "hints", "brute_force", "approach", "complexity", "pitfalls", "follow_up")


def _starter(sol):
    out = []
    for ln in sol.splitlines():
        s = ln.strip()
        if ln.startswith("class "):
            out.append(ln)
        elif s.startswith("def ") and (ln.startswith("    def ") or ln.startswith("def ")) and (
                not s.startswith("def _") or s.startswith("def __init__")):
            out.append(ln)
            out.append(ln[:len(ln) - len(ln.lstrip())] + "    pass")
    return "\n".join(out) + "\n"


def P(id, title, diff, pattern, entry, desc, sol, tests, wrong, guide, **kw):
    if "class Solution" not in sol:
        kw.setdefault("kind", "class")
    return dict(id="ctci-" + id, title=title, difficulty=diff, pattern=pattern, entry=entry,
                description=desc.strip() + "\n", starter=_starter(sol), solution=sol, tests=tests,
                wrong_solutions=wrong, guide=dict(zip(G, guide)), **kw)


def _ops(name, n, makers):
    """Random operation list for class problems: makers = list of (op, argfn)."""
    ops, args = [name[0]], [name[1]]
    for _ in range(n):
        op, fn = R.choice(makers)
        ops.append(op)
        args.append(fn())
    return [ops, args]


def _mk(lo, hi):
    if lo > hi:
        return None
    m = (lo + hi) // 2
    return (m, _mk(lo, m - 1), _mk(m + 1, hi))


def _lvl(t):
    out, q = [], deque([t])
    while q:
        x = q.popleft()
        if x is None:
            out.append(None)
            continue
        out.append(x[0])
        q.append(x[1])
        q.append(x[2])
    while out and out[-1] is None:
        out.pop()
    return out


def _skew(vals, side="r"):
    out = []
    for i, v in enumerate(vals):
        out.append(v)
        if i < len(vals) - 1 and side == "r":
            out.append(None)
        elif i < len(vals) - 1 and i > 0 and side == "l":
            out.append(None)
    return out


_BST = _lvl(_mk(1, 4000))
_BST_BAD = list(_BST)
_BST_BAD[3000] = 1
_RT = [R.randint(-9, 9) for _ in range(6000)]
_DAG_N = 3000
_DAG = [[a, b] for a in range(_DAG_N) for b in (a + 1, a + 7) if b < _DAG_N]
R.shuffle(_DAG)
_ri = lambda lo, hi: (lambda: [R.randint(lo, hi)])
_no = lambda: []

PROBLEMS = [
P("floor-stack", "Floor Stack", "Easy", "Stacks & Queues", "FloorStack",
"""
Design a stack of integers that can also report its **smallest element at any moment**, with every operation running in O(1) time.

Implement class `FloorStack`:

- `push(x)` puts `x` on top.
- `pop()` removes the top element and returns it, or returns `-1` if the stack is empty.
- `top()` returns the top element without removing it (`-1` if empty).
- `lowest()` returns the smallest element currently in the stack (`-1` if empty).

**Constraints:** values are in `[0, 10^9]`; up to `10^5` calls.

**Example:** `push(5), push(2), push(8), lowest() → 2, pop() → 8, pop() → 2, lowest() → 5`
""",
'''class FloorStack:
    def __init__(self):
        self.items = []

    def push(self, x: int) -> None:
        floor = x if not self.items else min(x, self.items[-1][1])
        self.items.append((x, floor))

    def pop(self) -> int:
        return self.items.pop()[0] if self.items else -1

    def top(self) -> int:
        return self.items[-1][0] if self.items else -1

    def lowest(self) -> int:
        return self.items[-1][1] if self.items else -1
''',
[[["FloorStack", "push", "push", "push", "lowest", "pop", "pop", "lowest"], [[], [5], [2], [8], [], [], [], []]],
 [["FloorStack", "pop", "top", "lowest"], [[], [], [], []]],
 [["FloorStack", "push", "push", "lowest", "pop", "lowest", "pop", "lowest"], [[], [3], [3], [], [], [], [], []]],
 [["FloorStack", "push", "push", "push", "pop", "lowest", "top"], [[], [1], [2], [3], [], [], []]],
 [["FloorStack", "push", "push", "push", "pop", "lowest", "pop", "lowest"], [[], [9], [4], [1], [], [], [], []]],
 [["FloorStack", "push", "pop", "push", "lowest"], [[], [7], [], [8], []]],
 [["FloorStack", "push", "push", "pop", "pop", "pop", "push", "lowest"], [[], [2], [1], [], [], [], [6], []]],
 [["FloorStack", "push", "push", "push", "push", "pop", "pop", "lowest"], [[], [2], [0], [3], [0], [], [], []]],
 _ops(("FloorStack", []), 3000, [("push", _ri(0, 50)), ("push", _ri(0, 50)), ("pop", _no), ("lowest", _no), ("top", _no)]),
 _ops(("FloorStack", []), 3000, [("push", _ri(0, 10 ** 9)), ("pop", _no), ("lowest", _no)])],
['''class FloorStack:
    def __init__(self):
        self.items = []
        self.low = None

    def push(self, x):
        self.items.append(x)
        if self.low is None or x < self.low:
            self.low = x

    def pop(self):
        return self.items.pop() if self.items else -1

    def top(self):
        return self.items[-1] if self.items else -1

    def lowest(self):
        return self.low if self.items else -1
'''],
("What a stack is (last in, first out): see [Stack basics](#/lesson/neet-window-stack/stack-basics).",
 "The minimum can only change when the stack changes, and a stack only changes at the top. So each element can remember \"the smallest value at or below me\". That note never becomes wrong while the element is in the stack, because nothing below it can change.",
 ["A single variable holding the minimum breaks on `pop`: after removing the minimum, what is the new one?",
  "Store extra information next to each pushed value.",
  "Push the pair (value, minimum so far). `lowest()` reads the pair on top."],
 "Scan the whole stack in `lowest()`: correct but O(n) per call.",
 "`push(x)`: floor = `min(x, floor of current top)`; append `(x, floor)`. `pop`/`top` use the first field, `lowest` the second.\n\nDry run: push 5 → (5,5); push 2 → (2,2); push 8 → (8,2); lowest 2; pop 8; pop 2; top pair is (5,5) so lowest 5.",
 "Every operation O(1) time. Space O(n): one extra number per element.",
 "Tracking the minimum in one variable (shown in the wrong solution). With a separate min-stack, pushing only on *strictly* smaller values loses duplicates of the minimum; use `<=`.",
 "Save memory with a second stack that stores a new minimum only when it changes. Compare with [Min Stack](#/problem/min-stack). Then design a queue with a `highest()` operation using a monotonic deque: see [Monotonic deque](#/lesson/neet-window-stack/monotonic-deque).")),

P("relay-queue", "Relay Queue From Two Stacks", "Easy", "Stacks & Queues", "RelayQueue",
"""
You are given only stacks (Python lists used with `append` and `pop()` at the end). Build a first-in, first-out queue from **two stacks**.

Implement class `RelayQueue`:

- `enqueue(x)` adds `x` at the back.
- `dequeue()` removes and returns the front element, or `-1` if the queue is empty.
- `front()` returns the front element without removing it (`-1` if empty).
- `size()` returns the number of stored elements.

Each operation must cost O(1) **amortised** time (averaged over any long sequence of calls).

**Example:** `enqueue(4), enqueue(6), front() → 4, dequeue() → 4, enqueue(9), dequeue() → 6, dequeue() → 9, dequeue() → -1`
""",
'''class RelayQueue:
    def __init__(self):
        self.inbox = []
        self.outbox = []

    def _shift(self):
        if not self.outbox:
            while self.inbox:
                self.outbox.append(self.inbox.pop())

    def enqueue(self, x: int) -> None:
        self.inbox.append(x)

    def dequeue(self) -> int:
        self._shift()
        return self.outbox.pop() if self.outbox else -1

    def front(self) -> int:
        self._shift()
        return self.outbox[-1] if self.outbox else -1

    def size(self) -> int:
        return len(self.inbox) + len(self.outbox)
''',
[[["RelayQueue", "enqueue", "enqueue", "front", "dequeue", "enqueue", "dequeue", "dequeue", "dequeue"],
  [[], [4], [6], [], [], [9], [], [], []]],
 [["RelayQueue", "dequeue", "front", "size"], [[], [], [], []]],
 [["RelayQueue", "enqueue", "size", "dequeue", "size"], [[], [1], [], [], []]],
 [["RelayQueue", "enqueue", "enqueue", "enqueue", "dequeue", "enqueue", "dequeue", "dequeue", "dequeue"],
  [[], [1], [2], [3], [], [4], [], [], []]],
 [["RelayQueue", "enqueue", "front", "enqueue", "front", "dequeue", "front"], [[], [5], [], [6], [], [], []]],
 [["RelayQueue", "enqueue", "dequeue", "enqueue", "dequeue", "dequeue"], [[], [1], [], [2], [], []]],
 [["RelayQueue", "enqueue", "enqueue", "dequeue", "enqueue", "enqueue", "dequeue", "dequeue", "size", "front"],
  [[], [7], [8], [], [9], [10], [], [], [], []]],
 _ops(("RelayQueue", []), 4000, [("enqueue", _ri(0, 99)), ("dequeue", _no), ("front", _no), ("size", _no)]),
 _ops(("RelayQueue", []), 4000, [("enqueue", _ri(0, 99)), ("enqueue", _ri(0, 99)), ("dequeue", _no)]),
 [["RelayQueue"] + ["enqueue"] * 3000 + ["dequeue"] * 3001, [[]] + [[i] for i in range(3000)] + [[]] * 3001]],
['''class RelayQueue:
    def __init__(self):
        self.inbox = []
        self.outbox = []

    def enqueue(self, x):
        self.inbox.append(x)

    def dequeue(self):
        while self.inbox:
            self.outbox.append(self.inbox.pop())
        return self.outbox.pop() if self.outbox else -1

    def front(self):
        while self.inbox:
            self.outbox.append(self.inbox.pop())
        return self.outbox[-1] if self.outbox else -1

    def size(self):
        return len(self.inbox) + len(self.outbox)
'''],
("Stacks, queues and amortised cost: see [Queues and deques](#/lesson/dsa-foundations/queues-deques) and [Dynamic arrays](#/lesson/dsa-foundations/dynamic-arrays).",
 "Pouring a stack into another stack reverses its order. Reversed last-in-first-out is first-in-first-out. So keep an *inbox* stack for arrivals and an *outbox* stack for departures, and pour only when the outbox is empty.",
 ["Pop everything from one stack onto another and look at the order.",
  "If you pour on every dequeue you do far too much work, and pouring while the outbox still holds items puts newer elements in front of older ones.",
  "Pour **only when the outbox is empty**. Then each element is pushed twice and popped twice in its whole life."],
 "Keep one stack; on each dequeue pour everything into a temporary stack, take the bottom item, pour everything back: O(n) per dequeue.",
 "`enqueue` appends to `inbox`. `dequeue`/`front` first call `_shift`, which moves all of `inbox` to `outbox` only if `outbox` is empty.\n\nDry run: enqueue 4, 6 → inbox [4,6]. front: shift → outbox [6,4], top is 4. dequeue → 4. enqueue 9 → inbox [9]. dequeue → outbox still has 6. dequeue → outbox empty, shift → [9] → 9.",
 "Amortised O(1) per operation: an element moves inbox → outbox once. A single dequeue can cost O(n). Space O(n).",
 "Pouring when the outbox is not empty breaks the order (the wrong solution returns 2 after 3 in the fourth test). Forgetting that `front` also needs the shift.",
 "Same idea as [Implement Queue using Stacks](#/problem/implement-queue-using-stacks). Try the mirror image: a stack from two queues, and explain why that one cannot be amortised O(1) for both push and pop with the simple approach.")),

P("book-piles", "Book Piles", "Medium", "Stacks & Queues", "BookPiles",
"""
A second-hand bookshop keeps returned books in piles along its counter. A pile is steady only up to `cap` books, so when the newest pile is full, the next book starts a fresh pile to its right. Books are identified by integer codes.

Implement class `BookPiles(cap)`:

- `push(x)` lays book `x` on the rightmost pile (starting a new pile if there is none or the rightmost one is full).
- `pop()` removes and returns the top book of the **rightmost** pile, or `-1` when the counter is empty.
- `popAt(i)` removes and returns the top book of pile number `i` (0 = leftmost), or `-1` if that pile does not exist. Books are **not** moved between piles afterwards, so a pile in the middle may stay shorter than `cap`.
- `count()` returns the current number of piles.

A pile that loses its last book disappears at once and the piles to its right are renumbered one position to the left.

**Constraints:** `1 <= cap <= 100`; up to `2·10^4` calls.

**Example (cap = 2):** `push 1, 2, 3, 4, 5` gives piles `[1,2] [3,4] [5]`. `popAt(0) → 2`, `pop() → 5`, `count() → 2`, `pop() → 4`.
""",
'''class BookPiles:
    def __init__(self, cap: int):
        self.cap = cap
        self.piles = []

    def push(self, x: int) -> None:
        if not self.piles or len(self.piles[-1]) == self.cap:
            self.piles.append([])
        self.piles[-1].append(x)

    def pop(self) -> int:
        return self.popAt(len(self.piles) - 1)

    def popAt(self, i: int) -> int:
        if i < 0 or i >= len(self.piles):
            return -1
        x = self.piles[i].pop()
        if not self.piles[i]:
            del self.piles[i]
        return x

    def count(self) -> int:
        return len(self.piles)
''',
[[["BookPiles", "push", "push", "push", "push", "push", "popAt", "pop", "count", "pop"], [[2], [1], [2], [3], [4], [5], [0], [], [], []]],
 [["BookPiles", "pop", "popAt", "count"], [[3], [], [0], []]],
 [["BookPiles", "push", "count", "pop", "count", "pop"], [[1], [7], [], [], [], []]],
 [["BookPiles", "push", "push", "push", "popAt", "popAt", "count", "pop"], [[2], [1], [2], [3], [0], [0], [], []]],
 [["BookPiles", "push", "push", "push", "popAt", "push", "count", "pop", "pop", "pop"], [[2], [1], [2], [3], [0], [4], [], [], [], []]],
 [["BookPiles", "push", "push", "popAt", "popAt", "popAt"], [[1], [5], [6], [1], [1], [0]]],
 [["BookPiles", "push", "push", "push", "push", "popAt", "popAt", "push", "push", "count"], [[2], [1], [2], [3], [4], [0], [0], [5], [6], []]],
 [["BookPiles", "push", "popAt", "popAt"], [[5], [9], [-1], [3]]],
 _ops(("BookPiles", [3]), 3000, [("push", _ri(0, 99)), ("push", _ri(0, 99)), ("pop", _no), ("popAt", _ri(0, 6)), ("count", _no)]),
 _ops(("BookPiles", [1]), 2000, [("push", _ri(0, 99)), ("pop", _no), ("popAt", _ri(0, 3)), ("count", _no)]),
 _ops(("BookPiles", [50]), 3000, [("push", _ri(0, 99)), ("push", _ri(0, 99)), ("popAt", _ri(0, 2)), ("count", _no)])],
['''class BookPiles:
    def __init__(self, cap):
        self.cap = cap
        self.piles = []

    def push(self, x):
        if not self.piles or len(self.piles[-1]) == self.cap:
            self.piles.append([])
        self.piles[-1].append(x)

    def pop(self):
        return self.popAt(len(self.piles) - 1)

    def popAt(self, i):
        if i < 0 or i >= len(self.piles) or not self.piles[i]:
            return -1
        return self.piles[i].pop()

    def count(self):
        return len(self.piles)
'''],
("A list of lists, and stack operations on each inner list: see [Stacks](#/lesson/dsa-foundations/stacks).",
 "The structure is a stack of stacks. All the difficulty is in the rules at the boundaries: when to open a new pile and what happens to an empty one. Write those rules down before coding.",
 ["Represent the row of piles as a list of lists.",
  "`pop()` is `popAt(last index)`: write one of them in terms of the other.",
  "After removing a book, delete the pile if it is now empty so that no empty pile is ever stored."],
 "One flat list plus arithmetic on indexes works for `push`/`pop` but `popAt` leaves holes that the arithmetic cannot describe.",
 "`push`: if there is no pile or the last is full, append a new empty pile; append the book to the last pile. `popAt(i)`: validate `i`, pop from pile `i`, delete the pile if empty.\n\nDry run (cap 2): piles `[1,2] [3,4] [5]`. `popAt(0)` → 2, piles `[1] [3,4] [5]`. `pop()` → 5 and the third pile vanishes. `count()` → 2. `pop()` → 4.",
 "`push`, `pop`, `count`: O(1). `popAt`: O(1) for the pop plus O(t) when a middle pile is deleted from a list of `t` piles.",
 "Leaving empty piles in the list, so that a later `pop` hits an empty list or `count` is too large. Accepting negative indexes, which Python happily interprets as counting from the end.",
 "Discuss the alternative rule where `popAt` *does* shift books left so every pile except the last stays full: each `popAt` then costs O(number of piles) and needs a remove-from-bottom operation, which suggests deques.")),

P("sort-with-spare-stack", "Sort With One Spare Stack", "Medium", "Stacks & Queues", "sortStack",
"""
A stack of numbered crates is given as a list whose **last element is the top**. Re-order it so that the **smallest crate is on top** (so the list ends up in descending order from bottom to top) and return it.

The exercise: use only **one additional stack** and a handful of variables. Treat both lists strictly as stacks (`append`, `pop()`, look at `[-1]`, test for empty). Calling `sort` defeats the purpose.

**Constraints:** `0 <= len(stack) <= 2000`.

**Example:** `[3, 1, 4, 1, 5]` → `[5, 4, 3, 1, 1]`
""",
'''class Solution:
    def sortStack(self, stack: List[int]) -> List[int]:
        spare = []
        while stack:
            crate = stack.pop()
            while spare and spare[-1] > crate:
                stack.append(spare.pop())
            spare.append(crate)
        while spare:
            stack.append(spare.pop())
        return stack
''',
[[[3, 1, 4, 1, 5]], [[]], [[7]], [[1, 2]], [[2, 1]], [[5, 5, 5]], [[1, 2, 3, 4]], [[4, 3, 2, 1]], [[-3, 0, -7, 2]],
 [[R.randint(0, 999) for _ in range(1500)]], [list(range(1200))], [list(range(1200, 0, -1))], [[2, 2, 1, 1, 3, 3]]],
['''class Solution:
    def sortStack(self, stack):
        return sorted(stack)
''', '''class Solution:
    def sortStack(self, stack):
        spare = []
        while stack:
            crate = stack.pop()
            if spare and spare[-1] > crate:
                stack.append(spare.pop())
            spare.append(crate)
        while spare:
            stack.append(spare.pop())
        return stack
'''],
("Stack operations and insertion sort: see [Stacks](#/lesson/dsa-foundations/stacks).",
 "Keep the spare stack sorted at all times (largest on top). To add a new crate, temporarily move the crates that are larger than it back onto the original stack, drop the new crate in, and the moved crates will be re-inserted by the same loop later. This is insertion sort, with the original stack doubling as the temporary storage.",
 ["Suppose the spare stack is already sorted. How do you insert one more value at the right depth?",
  "Hold the new crate in a variable; pop larger crates from the spare back onto the input stack.",
  "At the end the spare has the largest on top; pour it back once so the smallest ends on top."],
 "Repeatedly scan the stack for its minimum by pouring into the spare and back: also O(n²) but with more moving. Using three stacks allows merge sort in O(n log n).",
 "Loop while the input is non-empty: `crate = stack.pop()`; while the spare's top is greater than `crate`, move it back to the input; push `crate` on the spare. Finally pour the spare into the input.\n\nDry run `[3,1,4]` (top 4): spare [4]. crate 1: 4 > 1 → move 4 back, spare [1], input [3,4]. crate 4 → spare [1,4]. crate 3: 4 > 3 → back, spare [1,3], input [4]. crate 4 → spare [1,3,4]. Pour: `[4,3,1]`.",
 "Time O(n²) in the worst case (input already in the wrong order), space O(n) for the spare stack.",
 "Using `if` instead of `while` moves back only one crate, leaving the spare unsorted. Returning ascending order: read which end is the top.",
 "How would you sort if you had unlimited stacks? Split and merge (merge sort), or partition around a pivot (quick sort): see [Merge sort](#/lesson/dsa-foundations/merge-sort).")),

P("triple-stack-array", "Three Stacks, One Array", "Medium", "Stacks & Queues", "TripleStack",
"""
Memory is tight on a microcontroller: you get **one fixed array** and must run three independent stacks inside it. Each stack gets an equal slice of `cap` slots.

Implement class `TripleStack(cap)` where `s` is the stack number `0`, `1` or `2`:

- `push(s, x)` pushes `x` on stack `s`; returns `True`, or `False` (and stores nothing) if that stack already holds `cap` values.
- `pop(s)` removes and returns the top of stack `s`, or `-1` if it is empty.
- `peek(s)` returns the top of stack `s` without removing it, or `-1`.
- `sizes()` returns a list with the three current sizes.

Store all values in a single list of length `3 * cap`; do not create three lists.

**Constraints:** `1 <= cap <= 1000`; values in `[0, 10^9]`.

**Example (cap = 2):** `push(0,5) → True, push(0,6) → True, push(0,7) → False, push(2,9) → True, pop(0) → 6, peek(2) → 9, pop(1) → -1, sizes() → [1,0,1]`
""",
'''class TripleStack:
    def __init__(self, cap: int):
        self.cap = cap
        self.data = [0] * (3 * cap)
        self.used = [0, 0, 0]

    def push(self, s: int, x: int) -> bool:
        if self.used[s] == self.cap:
            return False
        self.data[s * self.cap + self.used[s]] = x
        self.used[s] += 1
        return True

    def pop(self, s: int) -> int:
        if self.used[s] == 0:
            return -1
        self.used[s] -= 1
        return self.data[s * self.cap + self.used[s]]

    def peek(self, s: int) -> int:
        if self.used[s] == 0:
            return -1
        return self.data[s * self.cap + self.used[s] - 1]

    def sizes(self) -> List[int]:
        return list(self.used)
''',
[[["TripleStack", "push", "push", "push", "push", "pop", "peek", "pop", "sizes"], [[2], [0, 5], [0, 6], [0, 7], [2, 9], [0], [2], [1], []]],
 [["TripleStack", "pop", "peek", "sizes"], [[1], [0], [1], []]],
 [["TripleStack", "push", "push", "push", "pop", "pop", "pop"], [[1], [0, 1], [1, 2], [2, 3], [0], [1], [2]]],
 [["TripleStack", "push", "push", "pop", "push", "peek"], [[1], [1, 4], [1, 5], [1], [1, 6], [1]]],
 [["TripleStack", "push", "push", "push", "push", "peek", "peek", "sizes"], [[2], [1, 1], [1, 2], [1, 3], [2, 4], [1], [0], []]],
 [["TripleStack", "push", "push", "pop", "pop", "pop", "sizes"], [[3], [2, 8], [2, 9], [2], [2], [2], []]],
 [["TripleStack", "push", "push", "push", "push", "pop", "peek", "peek"], [[2], [0, 1], [0, 2], [1, 3], [1, 4], [0], [0], [1]]],
 _ops(("TripleStack", [4]), 3000, [("push", lambda: [R.randint(0, 2), R.randint(0, 99)]), ("pop", _ri(0, 2)), ("peek", _ri(0, 2)), ("sizes", _no)]),
 _ops(("TripleStack", [1]), 2000, [("push", lambda: [R.randint(0, 2), R.randint(0, 99)]), ("pop", _ri(0, 2)), ("peek", _ri(0, 2))]),
 _ops(("TripleStack", [500]), 3000, [("push", lambda: [R.randint(0, 2), R.randint(0, 99)]), ("push", lambda: [R.randint(0, 2), R.randint(0, 99)]), ("pop", _ri(0, 2))])],
['''class TripleStack:
    def __init__(self, cap):
        self.cap = cap
        self.data = [0] * (3 * cap)
        self.used = [0, 0, 0]

    def push(self, s, x):
        if sum(self.used) == 3 * self.cap:
            return False
        self.data[s * self.cap + self.used[s]] = x
        self.used[s] += 1
        return True

    def pop(self, s):
        if self.used[s] == 0:
            return -1
        self.used[s] -= 1
        return self.data[s * self.cap + self.used[s]]

    def peek(self, s):
        if self.used[s] == 0:
            return -1
        return self.data[s * self.cap + self.used[s] - 1]

    def sizes(self):
        return list(self.used)
'''],
("Array indexing and how an array-backed stack keeps a size counter: see [Stacks](#/lesson/dsa-foundations/stacks).",
 "Cut the array into three equal regions. Stack `s` owns slots `s*cap … s*cap + cap - 1`. A stack needs only one number of bookkeeping, its size, because the top is always at `start + size - 1`.",
 ["Where does region `s` begin? At index `s * cap`.",
  "Keep a list of three sizes. The next free slot of stack `s` is `s * cap + size[s]`.",
  "`pop` only has to decrease the size and read the slot: the old value can stay in the array as garbage."],
 "Three separate Python lists: trivial but ignores the single-array requirement, which is the point of the exercise.",
 "`push(s, x)`: full if `used[s] == cap`; else write at `s*cap + used[s]` and increment. `pop(s)`: empty if `used[s] == 0`; else decrement and read.\n\nDry run (cap 2): push(0,5) writes index 0; push(0,6) writes index 1; push(0,7) refused; push(2,9) writes index 4; pop(0) reads index 1 → 6.",
 "All operations O(1) time; space is the fixed `3 * cap` array plus three counters.",
 "Checking total capacity instead of the per-stack capacity lets stack 0 overflow into stack 1's region. Reading before decrementing in `pop` returns the slot above the top.",
 "The harder design lets the regions have flexible sizes: when one stack is full but the array is not, shift a neighbouring region and treat the array as circular. Discuss the cost of shifting and why it is rarely worth it.")),

P("repair-counter", "Repair Counter", "Medium", "Stacks & Queues", "RepairCounter",
"""
A repair shop fixes two kinds of device, phones and laptops, strictly in the order in which they were handed in. A technician who becomes free asks either for "whichever device has waited longest" or, depending on their training, for the longest-waiting phone or the longest-waiting laptop.

Implement class `RepairCounter`:

- `dropOff(tag, kind)` registers a device; `tag` is the label stuck on it and `kind` is `"phone"` or `"laptop"`.
- `takeAny()` removes and returns the tag of the device that was handed in earliest.
- `takePhone()` / `takeLaptop()` remove and return the tag of the earliest device of that kind.

Each take method returns the empty string `""` when no suitable device is waiting. All operations must be O(1).

**Example:** `dropOff("P17","phone"), dropOff("L04","laptop"), dropOff("P18","phone"), takeLaptop() → "L04", takeAny() → "P17", takeAny() → "P18", takePhone() → ""`
""",
'''class RepairCounter:
    def __init__(self):
        self.phones = collections.deque()
        self.laptops = collections.deque()
        self.ticket = 0

    def dropOff(self, tag: str, kind: str) -> None:
        line = self.phones if kind == "phone" else self.laptops
        line.append((self.ticket, tag))
        self.ticket += 1

    def takeAny(self) -> str:
        if not self.phones:
            return self.takeLaptop()
        if not self.laptops:
            return self.takePhone()
        return self.takePhone() if self.phones[0][0] < self.laptops[0][0] else self.takeLaptop()

    def takePhone(self) -> str:
        return self.phones.popleft()[1] if self.phones else ""

    def takeLaptop(self) -> str:
        return self.laptops.popleft()[1] if self.laptops else ""
''',
[[["RepairCounter", "dropOff", "dropOff", "dropOff", "takeLaptop", "takeAny", "takeAny", "takePhone"],
  [[], ["P17", "phone"], ["L04", "laptop"], ["P18", "phone"], [], [], [], []]],
 [["RepairCounter", "takeAny", "takePhone", "takeLaptop"], [[], [], [], []]],
 [["RepairCounter", "dropOff", "takePhone", "takeAny"], [[], ["Bo", "laptop"], [], []]],
 [["RepairCounter", "dropOff", "dropOff", "takeAny", "takeAny"], [[], ["A", "laptop"], ["B", "phone"], [], []]],
 [["RepairCounter", "dropOff", "dropOff", "dropOff", "takePhone", "takeAny", "takeAny"], [[], ["A", "laptop"], ["B", "laptop"], ["C", "phone"], [], [], []]],
 [["RepairCounter", "dropOff", "dropOff", "takeLaptop", "dropOff", "takeAny", "takeAny"], [[], ["A", "phone"], ["B", "laptop"], [], ["C", "laptop"], [], []]],
 [["RepairCounter", "dropOff", "dropOff", "dropOff", "dropOff", "takeAny", "takeLaptop", "takeAny", "takeAny"],
  [[], ["Z", "phone"], ["Y", "phone"], ["X", "laptop"], ["W", "laptop"], [], [], [], []]],
 _ops(("RepairCounter", []), 3000, [("dropOff", lambda: ["n%d" % R.randint(0, 9999), R.choice(["phone", "laptop"])]), ("takeAny", _no), ("takePhone", _no), ("takeLaptop", _no)]),
 _ops(("RepairCounter", []), 3000, [("dropOff", lambda: ["n%d" % R.randint(0, 9999), R.choice(["phone", "laptop"])]), ("dropOff", lambda: ["m%d" % R.randint(0, 9999), "phone"]), ("takeAny", _no)]),
 _ops(("RepairCounter", []), 2000, [("dropOff", lambda: [R.choice("ABCDEFG"), R.choice(["phone", "laptop"])]), ("takeAny", _no), ("takeLaptop", _no)])],
['''class RepairCounter:
    def __init__(self):
        self.phones = collections.deque()
        self.laptops = collections.deque()

    def dropOff(self, tag, kind):
        (self.phones if kind == "phone" else self.laptops).append(tag)

    def takeAny(self):
        return self.takePhone() or self.takeLaptop()

    def takePhone(self):
        return self.phones.popleft() if self.phones else ""

    def takeLaptop(self):
        return self.laptops.popleft() if self.laptops else ""
'''],
("Queues and `collections.deque`: see [Queues and deques](#/lesson/dsa-foundations/queues-deques).",
 "One queue makes `takePhone` slow (you must dig past laptops). Two queues, one per kind, make the specific requests easy, and a ticket number stamped at drop-off tells you which of the two front devices has waited longer.",
 ["What goes wrong with a single queue when someone asks for a laptop and ten phones are in front?",
  "Keep a queue of phones and a queue of laptops. How will you compare the two fronts?",
  "Give every drop-off an increasing ticket number and store it with the tag."],
 "A single list, scanning from the front for the first device of the requested kind and deleting it: O(n) per request.",
 "`dropOff` appends `(ticket, tag)` to the right deque and increments the ticket. `takeAny` compares the tickets at the two fronts (handling an empty deque first) and delegates to `takePhone` or `takeLaptop`.\n\nDry run: P17(0,phone), L04(1,laptop), P18(2,phone). takeLaptop → L04. takeAny: only phones left → P17. takeAny → P18. takePhone → \"\".",
 "O(1) time per operation, O(n) space.",
 "Preferring phones whenever a phone is waiting (wrong solution) ignores the hand-in order. Using tags as the ordering key: tags are not ordered by time.",
 "Extend to k kinds of device: `takeAny` then needs the minimum over k queue fronts, which is a job for a heap. See [Binary heaps](#/lesson/neet-heap-graphs/binary-heaps).")),

P("route-exists", "Route Exists", "Easy", "Trees & Graphs", "hasRoute",
"""
A city has `n` crossings numbered `0 … n-1` joined by **one-way** streets. `streets[i] = [a, b]` means you can drive from `a` to `b` (not back).

Return `True` if a car can get from crossing `src` to crossing `dst` by following streets, `False` otherwise. A crossing can always reach itself.

**Constraints:** `1 <= n <= 10^4`; `0 <= len(streets) <= 2·10^4`.

**Example 1:** `n = 4, streets = [[0,1],[1,2],[3,2]], src = 0, dst = 2` → `True`

**Example 2:** same streets, `src = 2, dst = 0` → `False`
""",
'''class Solution:
    def hasRoute(self, n: int, streets: List[List[int]], src: int, dst: int) -> bool:
        out = [[] for _ in range(n)]
        for a, b in streets:
            out[a].append(b)
        seen = [False] * n
        seen[src] = True
        queue = collections.deque([src])
        while queue:
            node = queue.popleft()
            if node == dst:
                return True
            for nxt in out[node]:
                if not seen[nxt]:
                    seen[nxt] = True
                    queue.append(nxt)
        return False
''',
[[4, [[0, 1], [1, 2], [3, 2]], 0, 2], [4, [[0, 1], [1, 2], [3, 2]], 2, 0], [1, [], 0, 0], [2, [], 0, 1], [2, [[0, 1]], 1, 0],
 [3, [[0, 1], [1, 0]], 0, 2], [3, [[0, 1], [1, 2], [2, 0]], 2, 1], [5, [[0, 1], [0, 2], [2, 3], [3, 4], [4, 2]], 0, 4],
 [5, [[1, 0], [2, 1], [3, 2], [4, 3]], 0, 4], [5, [[1, 0], [2, 1], [3, 2], [4, 3]], 4, 0],
 [5000, [[i, i + 1] for i in range(4999)], 0, 4999], [5000, [[i, i + 1] for i in range(4999)], 4999, 0],
 [3000, [[R.randrange(3000), R.randrange(3000)] for _ in range(4000)], 5, 77]],
['''class Solution:
    def hasRoute(self, n, streets, src, dst):
        out = [[] for _ in range(n)]
        for a, b in streets:
            out[a].append(b)
            out[b].append(a)
        seen = {src}
        stack = [src]
        while stack:
            node = stack.pop()
            for nxt in out[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return dst in seen
'''],
("Adjacency lists and breadth-first search: see [Graph representations](#/lesson/neet-heap-graphs/graph-representations) and [DFS and BFS](#/lesson/neet-heap-graphs/dfs-bfs).",
 "\"Can I get there?\" is plain graph search. Start at `src`, repeatedly visit everything one street away from places you already reached, and never visit a crossing twice.",
 ["Turn the list of streets into, for each crossing, the list of crossings you can drive to.",
  "Use a queue (breadth-first) or a stack (depth-first); either works for a yes/no answer.",
  "Mark a crossing as seen when you put it in the queue, not when you take it out, so that it is never queued twice."],
 "Repeat n times: scan all streets and mark `b` reachable whenever `a` is. That is O(n·m), the idea behind Bellman-Ford.",
 "Build `out[a]`. BFS from `src` with a `seen` array. Return `True` when `dst` is dequeued; `False` when the queue empties.\n\nDry run example 1: queue [0] → visit 0, add 1 → visit 1, add 2 → visit 2 = dst → `True`. Example 2 starts at 2, which has no outgoing street → `False`.",
 "Time O(n + m), space O(n + m).",
 "Treating streets as two-way. Forgetting the `seen` marks, which loops forever on a cycle. Recursion-based DFS can exceed Python's recursion limit on a long chain; an explicit stack or queue avoids that.",
 "Find the shortest route (BFS gives it for free by recording distances), or search from both ends at once: see the problem [Friend Hops](#/problem/ctci-friend-hops).")),

P("balanced-bst-from-sorted", "Balanced Tree From Sorted Scores", "Easy", "Trees & Graphs", "buildBalanced",
"""
You receive exam scores **sorted in increasing order with no repeats**. Build a binary search tree of the smallest possible height that contains them and return its root.

So that everybody produces the same tree, always choose the element at index `(lo + hi) // 2` of the current range `lo … hi` as the root of that range.

**Constraints:** `0 <= len(scores) <= 10^4`.

**Example:** `[10, 20, 30, 40, 50]` → root 30; left subtree built from `[10, 20]` (root 10, right child 20); right subtree from `[40, 50]` (root 40, right child 50). Level order: `[30, 10, 40, null, 20, null, 50]`.
""",
'''class Solution:
    def buildBalanced(self, scores: List[int]) -> Optional[TreeNode]:
        def build(lo, hi):
            if lo > hi:
                return None
            mid = (lo + hi) // 2
            return TreeNode(scores[mid], build(lo, mid - 1), build(mid + 1, hi))
        return build(0, len(scores) - 1)
''',
[[[10, 20, 30, 40, 50]], [[]], [[7]], [[1, 2]], [[1, 2, 3]], [[1, 2, 3, 4]], [[-5, -1, 0, 3, 8, 9]], [list(range(7))],
 [list(range(15))], [list(range(0, 2000, 2))], [list(range(10000))], [[-10 ** 9, 10 ** 9]]],
['''class Solution:
    def buildBalanced(self, scores):
        root = None
        for s in reversed(scores):
            root = TreeNode(s, None, root)
        return root
''', '''class Solution:
    def buildBalanced(self, scores):
        def build(lo, hi):
            if lo > hi:
                return None
            mid = (lo + hi + 1) // 2
            return TreeNode(scores[mid], build(lo, mid - 1), build(mid + 1, hi))
        return build(0, len(scores) - 1)
'''],
("Binary search trees and recursion on index ranges: see [BST lesson](#/lesson/neet-linked-trees/tree-bst).",
 "A tree is shortest when each node splits its values as evenly as possible. In a sorted array, the middle element splits the rest into two equal halves that are themselves sorted, so the same idea applies to each half.",
 ["Which element should be the root so that the two sides have (almost) the same number of nodes?",
  "Everything left of the middle is smaller, everything right is larger: exactly the BST rule.",
  "Recurse on index ranges `(lo, mid-1)` and `(mid+1, hi)`; never slice the list."],
 "Insert the scores one by one with the ordinary BST insert. Inserting sorted data produces a chain of height n, the worst possible tree, and costs O(n²).",
 "`build(lo, hi)`: empty range → `None`; else `mid = (lo+hi)//2`, node = `scores[mid]`, children from the two sub-ranges.\n\nDry run `[10,20,30,40,50]`: mid 2 → 30. Left range (0,1): mid 0 → 10, its right child from (1,1) → 20. Right range (3,4): mid 3 → 40 with right child 50.",
 "Time O(n): one node per element, O(1) work each. Space O(n) for the tree plus O(log n) recursion depth.",
 "Slicing (`scores[:mid]`) copies data and makes the build O(n log n). Using the upper middle changes the shape; both are balanced but the checker here expects the lower middle.",
 "Same as [Convert Sorted Array to Binary Search Tree](#/problem/convert-sorted-array-to-binary-search-tree). Harder: build from a sorted *linked list* in O(n) by constructing in in-order.")),

P("level-headed-tree", "Level-Headed Tree", "Easy", "Trees & Graphs", "isLevelHeaded",
"""
Call a binary tree **level-headed** when, at *every* node, the heights of the left and right subtrees differ by at most one. (The height of an empty subtree is 0.)

Return `True` if the given tree is level-headed. Aim for a single traversal.

**Constraints:** up to `10^4` nodes; the tree's height is at most 500.

**Example 1:** `[1, 2, 3, 4]` → `True`

**Example 2:** `[1, 2, null, 3]` (a chain of three going left) → `False`
""",
'''class Solution:
    def isLevelHeaded(self, root: Optional[TreeNode]) -> bool:
        def height(node):
            if node is None:
                return 0
            left = height(node.left)
            if left < 0:
                return -1
            right = height(node.right)
            if right < 0 or abs(left - right) > 1:
                return -1
            return 1 + max(left, right)
        return height(root) >= 0
''',
[[[1, 2, 3, 4]], [[1, 2, None, 3]], [[]], [[1]], [[1, 2]], [[1, None, 2, None, 3]], [[1, 2, 3, 4, 5, 6, 7]],
 [[1, 2, 2, 3, 3, None, None, 4, 4]], [[1, 2, 2, 3, None, None, 3, 4, None, None, 4]], [list(range(8191))],
 [list(range(8191)) + [1, None, 1]], [_skew(list(range(300)))], [[1, 2, 3, 4, 5, None, None, 6]]],
['''class Solution:
    def isLevelHeaded(self, root):
        def height(node):
            return 0 if node is None else 1 + max(height(node.left), height(node.right))
        if root is None:
            return True
        return abs(height(root.left) - height(root.right)) <= 1
'''],
("Tree height and post-order recursion: see [Returning values up the tree](#/lesson/neet-linked-trees/tree-return-up).",
 "Each node needs two facts about each child: its height, and whether it is already unbalanced. One recursive function can return both if you reserve a special value (−1) for \"unbalanced below\".",
 ["Checking only the root's two children is not enough: the imbalance may be deep inside one side.",
  "Computing a fresh height at every node repeats work. Can the height function report a problem as well?",
  "Return −1 as soon as a subtree is unbalanced and pass that −1 straight up."],
 "For every node call a separate `height` function on both children, then recurse into the children: O(n log n) on balanced trees and O(n²) on a chain.",
 "`height(node)`: empty → 0. Get left; if −1 return −1. Get right; if −1 or the difference exceeds 1 return −1. Else `1 + max`.\n\nDry run `[1,2,null,3]`: node 3 → 1; node 2 → left 1, right 0 → 2; node 1 → left 2, right 0, difference 2 → −1 → `False`.",
 "Time O(n), space O(h) for the recursion where h is the height.",
 "Testing only the root (the ninth test is balanced at the root but not below). Mixing up height in nodes versus edges is harmless here as long as you are consistent.",
 "Same check as [Balanced Binary Tree](#/problem/balanced-binary-tree). Balanced search trees maintain this property automatically: see [AVL trees](#/lesson/dsa-foundations/avl).")),

P("valid-search-tree", "Valid Search Tree", "Medium", "Trees & Graphs", "isSearchTree",
"""
A library index is supposed to be a **binary search tree**: for every node, *all* values in its left subtree are strictly smaller and *all* values in its right subtree are strictly larger. Duplicates are therefore not allowed.

Return `True` if the given binary tree satisfies the rule.

**Constraints:** up to `10^4` nodes; height at most 500; values fit in 32-bit signed integers.

**Example 1:** `[8, 3, 10, 1, 6]` → `True`

**Example 2:** `[8, 3, 10, 1, 9]` → `False` (9 sits in the left subtree of 8)
""",
'''class Solution:
    def isSearchTree(self, root: Optional[TreeNode]) -> bool:
        def ok(node, low, high):
            if node is None:
                return True
            if (low is not None and node.val <= low) or (high is not None and node.val >= high):
                return False
            return ok(node.left, low, node.val) and ok(node.right, node.val, high)
        return ok(root, None, None)
''',
[[[8, 3, 10, 1, 6]], [[8, 3, 10, 1, 9]], [[]], [[5]], [[5, 5]], [[5, None, 5]], [[2, 1, 3]], [[2, 3, 1]],
 [[10, 5, 15, None, None, 6, 20]], [[-2147483648, None, 2147483647]], [[3, 1, 5, 0, 2, 4, 6]], [_BST], [_BST_BAD],
 [_skew(list(range(300)))], [[5, 3, 8, 2, 4, 6, 9, None, None, None, None, None, 7]]],
['''class Solution:
    def isSearchTree(self, root):
        def ok(node):
            if node is None:
                return True
            if node.left and node.left.val >= node.val:
                return False
            if node.right and node.right.val <= node.val:
                return False
            return ok(node.left) and ok(node.right)
        return ok(root)
'''],
("The BST property and in-order traversal: see [BST lesson](#/lesson/neet-linked-trees/tree-bst).",
 "The rule talks about whole subtrees, not only a node's two children. Carry a permitted range down the tree: going left tightens the upper limit to the parent's value, going right tightens the lower limit.",
 ["Comparing each node only with its children accepts example 2. Why?",
  "What range of values is allowed for the right child of the root's left child?",
  "Pass `(low, high)` down; use `None` for \"no limit\" rather than a magic number."],
 "For every node, compute the maximum of its left subtree and the minimum of its right subtree: O(n²) on a chain.",
 "`ok(node, low, high)`: empty → True; value outside the open interval → False; recurse left with `(low, val)` and right with `(val, high)`.\n\nDry run example 2: 8 with (None, None) fine; 3 with (None, 8) fine; 9 as right child of 3 has range (3, 8): 9 ≥ 8 → `False`.",
 "Time O(n), space O(h).",
 "Local parent-child comparison only. Using `<=`/`>=` the wrong way round and accepting duplicates. Using ±2³¹ as sentinels breaks when the tree contains those very values.",
 "Alternative: an in-order traversal of a BST must be strictly increasing; keep only the previous value. See [Validate Binary Search Tree](#/problem/validate-binary-search-tree).")),

P("inorder-next-value", "Next Larger Entry", "Medium", "Trees & Graphs", "nextLarger",
"""
A binary search tree stores distinct appointment times (integers). Given a number `t` (which may or may not be in the tree), return the **smallest stored value that is strictly greater than `t`**, or `-1` if no such value exists.

Do not visit the whole tree: the running time should depend on the tree's height.

**Constraints:** up to `10^4` nodes; values and `t` are in `[0, 10^9]`.

**Example:** tree `[20, 10, 30, 5, 15]`: `t = 10` → `15`; `t = 16` → `20`; `t = 30` → `-1`
""",
'''class Solution:
    def nextLarger(self, root: Optional[TreeNode], t: int) -> int:
        best = -1
        node = root
        while node:
            if node.val > t:
                best = node.val
                node = node.left
            else:
                node = node.right
        return best
''',
[[[20, 10, 30, 5, 15], 10], [[20, 10, 30, 5, 15], 16], [[20, 10, 30, 5, 15], 30], [[], 4], [[7], 7], [[7], 3], [[7], 9],
 [[20, 10, 30, 5, 15], 0], [[20, 10, 30, 5, 15], 15], [[20, 10, 30, 5, 15, 25, 35], 20], [[20, 10, 30, 5, 15, 25, 35], 29],
 [_BST, 1999], [_BST, 4000], [_BST, 0], [_skew(list(range(0, 600, 2))), 301]],
['''class Solution:
    def nextLarger(self, root, t):
        node = root
        while node and node.val != t:
            node = node.left if t < node.val else node.right
        if node is None or node.right is None:
            return -1
        node = node.right
        while node.left:
            node = node.left
        return node.val
'''],
("Searching in a BST: see [BST lesson](#/lesson/neet-linked-trees/tree-bst).",
 "Walk down as if searching for `t`. Every time you turn left you pass a node that is larger than `t`: it is a candidate, and each later candidate is smaller than the previous one. The last candidate you saw is the answer.",
 ["At a node with value > t, the answer is this node or something smaller on its left.",
  "At a node with value ≤ t, nothing on its left can be the answer.",
  "Keep one variable `best`; update it on every left turn."],
 "In-order traversal into a sorted list, then binary search: O(n) time and memory.",
 "Loop from the root: if `node.val > t`, record it and go left; else go right. Return the record.\n\nDry run `t = 16` on `[20,10,30,5,15]`: 20 > 16 → best 20, go left; 10 ≤ 16 → right; 15 ≤ 16 → right (empty). Answer 20.",
 "Time O(h), space O(1).",
 "The textbook rule \"leftmost node of the right subtree\" covers only half the cases: when the node has no right child the successor is an ancestor (the wrong solution returns −1 for `t = 15`). It also fails when `t` is not in the tree.",
 "With parent pointers you can start from the node itself and climb until you arrive from a left child. Related: [Kth Smallest Element in a BST](#/problem/kth-smallest-element-in-a-bst).")),

P("compile-order", "Compile Order", "Medium", "Trees & Graphs", "compileOrder",
"""
A software product has `n` modules numbered `0 … n-1`. `needs[i] = [a, b]` means module `a` **must be compiled before** module `b`.

Return any order of all `n` modules that respects every requirement. If the requirements contradict each other (a circular dependency), return an empty list.

**Constraints:** `1 <= n <= 10^4`; `0 <= len(needs) <= 2·10^4`. Any valid order is accepted.

**Example 1:** `n = 4, needs = [[0,1],[0,2],[1,3],[2,3]]` → `[0,1,2,3]` or `[0,2,1,3]`

**Example 2:** `n = 2, needs = [[0,1],[1,0]]` → `[]`
""",
'''class Solution:
    def compileOrder(self, n: int, needs: List[List[int]]) -> List[int]:
        after = [[] for _ in range(n)]
        waiting = [0] * n
        for a, b in needs:
            after[a].append(b)
            waiting[b] += 1
        ready = collections.deque(i for i in range(n) if waiting[i] == 0)
        order = []
        while ready:
            m = ready.popleft()
            order.append(m)
            for nxt in after[m]:
                waiting[nxt] -= 1
                if waiting[nxt] == 0:
                    ready.append(nxt)
        return order if len(order) == n else []
''',
[[4, [[0, 1], [0, 2], [1, 3], [2, 3]]], [2, [[0, 1], [1, 0]]], [1, []], [3, []], [3, [[2, 1], [1, 0]]], [3, [[0, 1], [1, 2], [2, 0]]],
 [5, [[0, 1], [1, 2], [3, 4]]], [4, [[0, 1], [1, 2], [2, 1]]], [2, [[0, 1], [0, 1]]], [6, [[5, 0], [5, 2], [4, 0], [4, 1], [2, 3], [3, 1]]],
 [1, [[0, 0]]], [_DAG_N, _DAG], [_DAG_N, _DAG + [[2999, 0]]], [5000, [[i + 1, i] for i in range(4999)]]],
['''class Solution:
    def compileOrder(self, n, needs):
        return list(range(n))
''', '''class Solution:
    def compileOrder(self, n, needs):
        after = [[] for _ in range(n)]
        waiting = [0] * n
        for a, b in needs:
            after[a].append(b)
            waiting[b] += 1
        ready = [i for i in range(n) if waiting[i] == 0]
        order = []
        while ready:
            m = ready.pop()
            order.append(m)
            for nxt in after[m]:
                waiting[nxt] -= 1
                if waiting[nxt] == 0:
                    ready.append(nxt)
        return order
'''],
("Directed graphs and topological sorting: see [Cycles and topological sort](#/lesson/neet-heap-graphs/cycles-toposort).",
 "A module can be compiled once everything it waits for is done. Start with the modules that wait for nothing; finishing a module may free others. If you run out of free modules before all are compiled, the remaining ones wait for each other in a circle.",
 ["For each module count how many requirements point *into* it (its in-degree).",
  "Put every module with count 0 in a queue. Removing a module lowers the counts of the modules that depend on it.",
  "At the end compare the length of your order with `n` to detect a cycle."],
 "Repeatedly scan all modules looking for one whose prerequisites are all done: O(n · (n + m)).",
 "This is Kahn's algorithm. Build `after[a]` lists and `waiting[b]` counts. Pop from the ready queue, append to the order, decrement the dependants.\n\nDry run example 1: waiting = [0,1,1,2]; ready [0]. Take 0 → waiting [_,0,0,2], ready [1,2]. Take 1 → 3 waits 1. Take 2 → 3 ready. Take 3. Order `[0,1,2,3]`.",
 "Time O(n + m), space O(n + m).",
 "Returning a partial order when there is a cycle. A repeated requirement must be counted twice in `waiting` (and is decremented twice), which the simple algorithm does naturally. A self-dependency `[0,0]` is a cycle.",
 "A depth-first version adds a node after all nodes reachable from it and reverses at the end. Compare with [Course Schedule II](#/problem/course-schedule-ii). The review lesson [Useful maths and graph algorithms](#/lesson/interview-prep/review-math-graphs) revisits both versions."),
checker='''def check(args, got, expected):
    n, needs = args
    if expected == []:
        return got == []
    if not isinstance(got, list) or sorted(got) != list(range(n)):
        return False
    pos = {m: i for i, m in enumerate(got)}
    return all(pos[a] < pos[b] for a, b in needs)
'''),

P("shared-ancestor", "Shared Ancestor", "Medium", "Trees & Graphs", "sharedAncestor",
"""
A company's reporting chart is a binary tree in which every node holds a distinct employee number. Given two employee numbers `p` and `q`, return the number of their **lowest shared manager**: the deepest node that has both of them in its subtree (a node counts as being in its own subtree).

The tree is **not** a search tree and nodes have no parent links. If either number does not appear in the tree, return `-1`.

**Constraints:** up to `10^4` nodes; height at most 500; `p != q`.

**Example:** tree `[1, 2, 3, 4, 5, null, 6]`: `p = 4, q = 5` → `2`; `p = 4, q = 6` → `1`; `p = 2, q = 4` → `2`; `p = 4, q = 99` → `-1`
""",
'''class Solution:
    def sharedAncestor(self, root: Optional[TreeNode], p: int, q: int) -> int:
        self.answer = -1

        def count(node):
            if node is None:
                return 0
            found = count(node.left) + count(node.right) + (1 if node.val in (p, q) else 0)
            if found == 2 and self.answer == -1:
                self.answer = node.val
            return found
        count(root)
        return self.answer
''',
[[[1, 2, 3, 4, 5, None, 6], 4, 5], [[1, 2, 3, 4, 5, None, 6], 4, 6], [[1, 2, 3, 4, 5, None, 6], 2, 4], [[1, 2, 3, 4, 5, None, 6], 4, 99],
 [[], 1, 2], [[1], 1, 2], [[1, 2], 2, 1], [[1, 2, 3], 2, 3], [[1, 2, 3, 4, 5, None, 6], 77, 88], [[1, 2, 3, 4, 5, None, 6], 6, 3],
 [list(range(8000)), 7998, 7999], [list(range(8000)), 4000, 7001], [list(range(8000)), 5, 9000], [_skew(list(range(300))), 250, 299]],
['''class Solution:
    def sharedAncestor(self, root, p, q):
        def go(node):
            if node is None or node.val == p or node.val == q:
                return node
            left, right = go(node.left), go(node.right)
            if left and right:
                return node
            return left or right
        res = go(root)
        return res.val if res else -1
'''],
("Post-order traversal that returns information to the parent: see [Returning values up the tree](#/lesson/neet-linked-trees/tree-return-up).",
 "Ask every subtree one question: \"how many of the two targets do you contain?\" The first node (deepest, because children report before parents) whose count reaches 2 is the lowest shared manager.",
 ["Each call should return 0, 1 or 2.",
  "A node's count is its children's counts plus one if the node itself is a target.",
  "Record the answer the first time a count equals 2; post-order guarantees that this is the deepest such node."],
 "Find the root-to-node path for `p` and for `q` (two traversals, O(n) memory each) and compare the paths from the top until they diverge.",
 "`count(node)` returns the number of targets below. When it first equals 2, store `node.val`.\n\nDry run `p=4, q=5`: node 4 → 1, node 5 → 1, node 2 → 0+1+1 = 2 → answer 2. Node 1 later also counts 2 but the answer is already set.",
 "Time O(n), space O(h).",
 "The classic short solution (shown as the wrong answer) stops descending when it meets `p`, so it never learns whether `q` exists at all: it returns 4 for `p = 4, q = 99`. Always ask whether both nodes are guaranteed to be present.",
 "With parent links the problem becomes \"intersection of two linked lists\". For a BST use the values to steer: see [Lowest Common Ancestor of a Binary Search Tree](#/problem/lowest-common-ancestor-of-a-binary-search-tree).")),

P("downward-path-count", "Downward Paths With a Given Total", "Medium", "Trees & Graphs", "countPaths",
"""
Each node of a binary tree holds an integer (possibly negative). Count the paths whose values add up to exactly `target`.

A path may start at **any node** and end at **any node below it (or at itself)**, always moving from parent to child.

**Constraints:** up to `6000` nodes; height at most 500; values in `[-1000, 1000]`.

**Example:** tree `[4, 3, -1, 1, 2]` (4 has children 3 and −1; 3 has children 1 and 2). With `target = 7` → `1` (the path 4 → 3). With `target = 3` → `2` (the single node 3, and the path 4 → −1).
""",
'''class Solution:
    def countPaths(self, root: Optional[TreeNode], target: int) -> int:
        seen = collections.defaultdict(int)
        seen[0] = 1

        def walk(node, running):
            if node is None:
                return 0
            running += node.val
            total = seen[running - target]
            seen[running] += 1
            total += walk(node.left, running) + walk(node.right, running)
            seen[running] -= 1
            return total
        return walk(root, 0)
''',
[[[4, 3, -1, 1, 2], 7], [[4, 3, -1, 1, 2], 3], [[], 0], [[5], 5], [[5], 0], [[0, 0, 0], 0], [[1, -1, 1, 1, -1], 0],
 [[1, 2, 3, 4, 5, 6, 7], 7], [[10, 5, -3, 3, 2, None, 11, 3, -2, None, 1], 8], [_RT, 5], [_RT, 0],
 [_skew([1] * 400), 20], [[1, None, 2, None, 3, None, 4, None, 5], 9]],
['''class Solution:
    def countPaths(self, root, target):
        def walk(node, remaining):
            if node is None:
                return 0
            remaining -= node.val
            return (1 if remaining == 0 else 0) + walk(node.left, remaining) + walk(node.right, remaining)
        return walk(root, target)
'''],
("Prefix sums with a hash map, and depth-first search: see [Prefix sums and counting](#/lesson/neet-arrays/prefix-counting).",
 "Along one root-to-node route, the tree is an array. In an array, a stretch sums to `target` exactly when two running totals differ by `target`. So carry the running total down the tree and keep a dictionary of how many times each earlier total occurred on the *current* route.",
 ["Solve the array version first: count subarrays with a given sum.",
  "At a node with running total `r`, the number of paths ending here is the number of ancestors (or the empty start) whose running total was `r - target`.",
  "When you leave a node, remove its running total from the dictionary: it must not be visible from other branches."],
 "From every node start a fresh downward search that counts paths beginning there: O(n·h), which is O(n²) for a chain.",
 "`seen = {0: 1}`. At each node: `running += val`; add `seen[running - target]`; increment `seen[running]`; recurse; decrement.\n\nDry run tree `[4,3,-1,1,2]`, target 3: at 4 running 4, need 1 → 0. At 3 running 7, need 4 → 1 (the path `3`). At 1 running 8, need 5 → 0. At 2 running 9, need 6 → 0. At −1 running 3, need 0 → 1 (path 4 → −1). Total 2.",
 "Time O(n), space O(h) for the dictionary and the recursion.",
 "Counting only paths that start at the root (wrong solution). Forgetting to undo the dictionary entry on the way back, which counts \"paths\" that jump between branches. Not seeding `seen[0] = 1`.",
 "Same technique as LeetCode's *Path Sum III* and [Subarray Sum Equals K](#/problem/subarray-sum-equals-k).")),

P("bst-arrival-orders", "Arrival Orders That Build the Same Tree", "Hard", "Trees & Graphs", "countOrders",
"""
A binary search tree was built by inserting distinct numbers one at a time into an empty tree, with no rebalancing. Many different insertion orders can lead to the same final tree: for the tree with root 2 and children 1 and 3, both `2,1,3` and `2,3,1` work.

Given the final tree, return **how many insertion orders produce exactly this tree**, modulo `1_000_000_007`. The empty tree has exactly one order (the empty one).

**Constraints:** up to `5000` nodes; height at most 500. The input is guaranteed to be a valid search tree.

**Example 1:** `[2, 1, 3]` → `2`

**Example 2:** `[5, 3, 8, 2, 4]` → `8`
""",
'''class Solution:
    def countOrders(self, root: Optional[TreeNode]) -> int:
        MOD = 1_000_000_007
        nodes, stack = [], [root] if root else []
        while stack:
            node = stack.pop()
            nodes.append(node)
            if node.left:
                stack.append(node.left)
            if node.right:
                stack.append(node.right)
        n = len(nodes)
        fact = [1] * (n + 1)
        for i in range(1, n + 1):
            fact[i] = fact[i - 1] * i % MOD
        inv = [pow(f, MOD - 2, MOD) for f in fact]
        size, ways = {None: 0}, {None: 1}
        for node in reversed(nodes):
            a, b = size[node.left], size[node.right]
            size[node] = a + b + 1
            choose = fact[a + b] * inv[a] % MOD * inv[b] % MOD
            ways[node] = choose * ways[node.left] % MOD * ways[node.right] % MOD
        return ways[root]
''',
[[[2, 1, 3]], [[5, 3, 8, 2, 4]], [[]], [[1]], [[1, None, 2]], [[4, 2, 6, 1, 3, 5, 7]], [[3, 1, None, None, 2]], [[5, 3, 8, 2, 4, 7, 9]],
 [_lvl(_mk(1, 15))], [_lvl(_mk(1, 1000))], [_lvl(_mk(1, 5000))], [_skew(list(range(400)))], [[10, 5, 20, 1, None, 15, 30, None, 2]]],
['''class Solution:
    def countOrders(self, root):
        def go(node):
            if node is None:
                return 1
            return go(node.left) * go(node.right) * (2 if node.left and node.right else 1) % 1_000_000_007
        return go(root)
'''],
("BST insertion, and counting with binomial coefficients $\\binom{n}{k}$: see [BST lesson](#/lesson/neet-linked-trees/tree-bst) and [Useful maths](#/lesson/interview-prep/review-math-graphs).",
 "The root must arrive first. After that, the left-subtree values and the right-subtree values never interact: each group must keep an order that builds its own subtree, but the two groups may be interleaved in any way. Counting interleavings of a sequence of length `a` with one of length `b` is choosing which `a` of the `a+b` positions belong to the first: $\\binom{a+b}{a}$.",
 ["Which value is forced to be first in every valid order?",
  "If the left subtree has `a` nodes and `W_L` valid orders, and the right has `b` and `W_R`, how many ways can one left order and one right order be merged while keeping each one's internal order?",
  "ways(node) = C(a+b, a) × ways(left) × ways(right). Compute sizes and ways bottom-up; precompute factorials modulo the prime."],
 "Generate all n! permutations, build a tree from each and compare: impossible beyond about 10 nodes.",
 "List nodes so that parents come before children, then process the list backwards so children are done first. Keep `size` and `ways` per node.\n\nDry run `[5,3,8,2,4]`: leaves 2, 4, 8 → size 1, ways 1. Node 3: a = b = 1 → C(2,1) = 2 → ways 2. Root: a = 3, b = 1 → C(4,3) = 4 → 4 × 2 × 1 = 8.",
 "Time O(n) after O(n) factorials (plus O(n log MOD) for the modular inverses), space O(n).",
 "Multiplying by 2 for each node with two children undercounts (it gives 4 for example 2). Forgetting the modulus on intermediate products. Recursing on a tall tree without care for the recursion limit: the reference uses an explicit stack.",
 "Print the actual orders for a small tree by \"weaving\" two lists recursively. Related counting: LeetCode's *Unique Binary Search Trees*.")),
]

_T = ["tree"]
_KW = {"balanced-bst-from-sorted": dict(return_type="tree"), "level-headed-tree": dict(arg_types=_T),
       "valid-search-tree": dict(arg_types=_T), "inorder-next-value": dict(arg_types=["tree", None]),
       "shared-ancestor": dict(arg_types=["tree", None, None]), "downward-path-count": dict(arg_types=["tree", None]),
       "bst-arrival-orders": dict(arg_types=_T)}
for _p in PROBLEMS:
    _p.update(_KW.get(_p["id"][5:], {}))
