# Queues, circular arrays and deques

A **queue** is the stack's cousin: a collection whose elements are inserted and removed according
to the **first-in, first-out (FIFO)** principle. Elements enter at the **back** and leave from the
**front**, like people in a line at a ticket counter, calls waiting at a customer-service centre,
or jobs waiting for a printer. A **deque** ("deck", double-ended queue) generalises both: insert and
remove at either end.

## 1. The queue ADT

| Operation | Meaning |
|---|---|
| `Q.enqueue(e)` | add `e` to the back |
| `Q.dequeue()` | remove and return the first element; error if empty |
| `Q.first()` | return the first element without removing it; error if empty |
| `Q.is_empty()` | `True` if empty |
| `len(Q)` | number of elements |

| Operation | Return | front ← Q ← back |
|---|---|---|
| `enqueue(5)` | – | [5] |
| `enqueue(3)` | – | [5, 3] |
| `dequeue()` | 5 | [3] |
| `enqueue(7)` | – | [3, 7] |
| `first()` | 3 | [3, 7] |
| `dequeue()` | 3 | [7] |
| `dequeue()` | 7 | [] |
| `dequeue()` | error | [] |

## 2. Why a plain list is not good enough

Adapting a list as for the stack: `enqueue` = `append` ($O(1)$), `dequeue` = `pop(0)` — but
`pop(0)` shifts every remaining element: **$\Theta(n)$**.

A second idea: on dequeue, don't shift; just replace `data[f]` with `None` and advance a front index
`f`. Now dequeue is $O(1)$, but the list grows forever: after many enqueue/dequeue cycles a queue
holding 3 elements could occupy a list of millions of cells — the "dead" prefix is never reclaimed.

## 3. Using an array circularly

The fix: let the front index **wrap around**. Treat the underlying array of capacity $N$ as a
circle. The front is at index `f`; the queue's elements occupy the `size` cells starting at `f`,
wrapping past the end back to index 0. The next free cell for enqueue is

$$\text{avail} = (f + \text{size}) \bmod N,$$

and after a dequeue the front advances to $f = (f + 1) \bmod N$. The modulo operator makes the
array circular.

```mermaid
graph LR
  c0["0: E"] --> c1["1: F"] --> c2["2: empty"] --> c3["3: empty"] --> c4["4: empty"]
  c4 --> c5["5: empty"] --> c6["6: empty"] --> c7["7: B, front f=7"] --> c8["8: C"] --> c9["9: D"]
  c9 -->|wraps| c0
```

In the picture $N = 10$, $f = 7$, size $= 5$: elements B, C, D, E, F; the next enqueue goes to
$(7 + 5) \bmod 10 = 2$.

### 3.1 The ArrayQueue implementation

```python-run
class Empty(Exception):
    pass

class ArrayQueue:
    """FIFO queue implementation using a Python list as underlying storage."""
    DEFAULT_CAPACITY = 10

    def __init__(self):
        self._data = [None] * ArrayQueue.DEFAULT_CAPACITY
        self._size = 0
        self._front = 0

    def __len__(self):
        return self._size

    def is_empty(self):
        return self._size == 0

    def first(self):
        if self.is_empty():
            raise Empty('Queue is empty')
        return self._data[self._front]

    def dequeue(self):
        if self.is_empty():
            raise Empty('Queue is empty')
        answer = self._data[self._front]
        self._data[self._front] = None                  # help garbage collection
        self._front = (self._front + 1) % len(self._data)
        self._size -= 1
        if 0 < self._size < len(self._data) // 4:       # shrink when 1/4 full
            self._resize(len(self._data) // 2)
        return answer

    def enqueue(self, e):
        if self._size == len(self._data):
            self._resize(2 * len(self._data))           # double the array size
        avail = (self._front + self._size) % len(self._data)
        self._data[avail] = e
        self._size += 1

    def _resize(self, cap):
        old = self._data
        self._data = [None] * cap
        walk = self._front
        for k in range(self._size):                     # only consider existing elements
            self._data[k] = old[walk]                   # intentionally shift indices
            walk = (1 + walk) % len(old)                # use old size as modulus
        self._front = 0                                 # front has been realigned

Q = ArrayQueue()
for i in range(25):
    Q.enqueue(i)
    if i % 3 == 2:
        Q.dequeue()
print("size", len(Q), "capacity", len(Q._data), "front index", Q._front, "first", Q.first())
while len(Q) > 2:
    Q.dequeue()
print("after draining: size", len(Q), "capacity", len(Q._data), "contents", [Q._data[(Q._front + k) % len(Q._data)] for k in range(len(Q))])
```

Key details:

- **Resizing** cannot just copy the list: the elements may wrap around. `_resize` walks from the old
  front, copying in queue order, so in the new array the front is index 0. (Note that it uses the
  *old* length as the modulus.)
- **Shrinking** at one-quarter full keeps memory proportional to the number of elements, with the
  same amortised guarantees as the dynamic array.
- Setting the vacated cell to `None` lets the garbage collector reclaim the object.

### 3.2 Performance

| Operation | Running time |
|---|---|
| `enqueue(e)` | $O(1)$ amortised |
| `dequeue()` | $O(1)$ amortised |
| `first()`, `is_empty()`, `len(Q)` | $O(1)$ |

Space $O(n)$. The amortisation is due to resizing, exactly as with dynamic arrays.

### 3.3 A fixed-capacity ring buffer

Many systems (audio buffers, network packet queues, logging) use a **bounded** circular buffer
that never resizes: enqueue fails (or overwrites the oldest item) when full. Then every operation
is $O(1)$ *worst case*, with no allocation at all — important in real-time code. You will
implement this in the circular-queue exercise.

> [!WARNING]
> With only `front` and `back` indices (no `size` counter), "full" and "empty" both look like
> `front == back`. Either keep a size counter (as above) or deliberately leave one cell unused.

## 4. Double-ended queues

A **deque** supports insertion and deletion at both front and back:

| Operation | Meaning |
|---|---|
| `D.add_first(e)` / `D.add_last(e)` | insert at front / back |
| `D.delete_first()` / `D.delete_last()` | remove and return front / back |
| `D.first()` / `D.last()` | peek at front / back |
| `D.is_empty()`, `len(D)` | as usual |

A circular array implements it just as well. The only new arithmetic is moving the front
**backwards** for `add_first`:

$$f = (f - 1) \bmod N,$$

and the index of the last element, $(f + \text{size} - 1) \bmod N$. Python's `%` always returns a
non-negative result for positive $N$, so `(0 - 1) % 10 == 9` wraps correctly.

```python-run
class ArrayDeque:
    def __init__(self, cap=4):
        self._data, self._front, self._size = [None] * cap, 0, 0
    def __len__(self): return self._size
    def _grow(self):
        old, n = self._data, len(self._data)
        self._data = [old[(self._front + k) % n] for k in range(self._size)] + [None] * n
        self._front = 0
    def add_first(self, e):
        if self._size == len(self._data): self._grow()
        self._front = (self._front - 1) % len(self._data)
        self._data[self._front] = e
        self._size += 1
    def add_last(self, e):
        if self._size == len(self._data): self._grow()
        self._data[(self._front + self._size) % len(self._data)] = e
        self._size += 1
    def delete_first(self):
        e = self._data[self._front]; self._data[self._front] = None
        self._front = (self._front + 1) % len(self._data); self._size -= 1
        return e
    def delete_last(self):
        back = (self._front + self._size - 1) % len(self._data)
        e = self._data[back]; self._data[back] = None; self._size -= 1
        return e

D = ArrayDeque()
D.add_last(5); D.add_first(3); D.add_first(7); D.add_last(9); D.add_last(1)
print([D._data[(D._front + k) % len(D._data)] for k in range(len(D))])
print(D.delete_last(), D.delete_first(), len(D))
```

### 4.1 Python's `collections.deque`

The standard library's `deque` is implemented in C as a doubly linked list of fixed-size blocks
(a hybrid). All end operations are $O(1)$ worst case. Its method names differ from the ADT:

| ADT | `collections.deque` |
|---|---|
| `add_first` / `add_last` | `appendleft` / `append` |
| `delete_first` / `delete_last` | `popleft` / `pop` |
| `first` / `last` | `D[0]` / `D[-1]` |
| — | `rotate(k)`, `extend`, `extendleft`, `remove`, `maxlen=` bounded mode |

Indexing `D[j]` in the middle is $O(n)$ (it walks blocks), unlike a list. Creating
`deque(maxlen=k)` gives a bounded buffer that silently discards from the opposite end — perfect for
"last $k$ items" windows.

```python-run
from collections import deque
D = deque(maxlen=3)
for x in range(6):
    D.append(x)
    print(list(D))
D.rotate(1)
print("rotated:", list(D))
```

> [!INTERVIEW]
> "Implement a queue with two stacks": push onto an *in* stack; to dequeue, if the *out* stack is
> empty, pop everything from *in* onto *out*, then pop from *out*. Each element moves at most twice,
> so operations are $O(1)$ amortised. It is the same amortisation argument as dynamic arrays.

## 5. Applications

- **Round-robin scheduling**: dequeue a process, run it for a time slice, enqueue it again (the
  linked-lists module does this with a circular list).
- **Breadth-first search**: the frontier is a queue (graphs module, and level-order tree traversal).
- **Sliding windows**: a deque of indices gives the maximum of every window of size $k$ in $O(n)$.
- **Buffers** between producer and consumer threads (`queue.Queue` wraps a deque with locks).

## 6. Worked dry run: a circular queue of capacity 5

Index arithmetic is easiest to trust after tracing it once. Take a fixed-capacity circular queue
with $N = 5$, starting with `front = 0`, `size = 0`. Each row shows the array after the operation
(`.` is an empty cell) and the cell that the *next* enqueue would use,
`avail = (front + size) % 5`.

| operation | returns | cells 0–4 | front | size | avail |
|---|---|---|---|---|---|
| enqueue(A) | | A . . . . | 0 | 1 | 1 |
| enqueue(B) | | A B . . . | 0 | 2 | 2 |
| enqueue(C) | | A B C . . | 0 | 3 | 3 |
| dequeue() | A | . B C . . | 1 | 2 | 3 |
| dequeue() | B | . . C . . | 2 | 1 | 3 |
| enqueue(D) | | . . C D . | 2 | 2 | 4 |
| enqueue(E) | | . . C D E | 2 | 3 | 0 |
| enqueue(F) | | F . C D E | 2 | 4 | 1 |
| enqueue(G) | | F G C D E | 2 | 5 | 2 (= front: full) |
| dequeue() | C | F G . D E | 3 | 4 | 2 |

Points to notice. After `enqueue(E)`, `avail` wraps to $(2 + 3) \bmod 5 = 0$, so F is stored
**before** C in the array while being **after** it in the queue: array order and queue order are
different things, which is exactly why resizing must copy "from front, wrapping" rather than slice.
When the queue is full, `avail` equals `front` — the same relation that holds when it is empty —
which is why we track `size` instead of comparing indices. The cell below replays the trace.

```python-run
N = 5
data, front, size = [None] * N, 0, 0
def show(op, ret=""):
    cells = " ".join("." if x is None else x for x in data)
    print(f"{op:12s} {str(ret):3s} | {cells} | front={front} size={size} avail={(front + size) % N}")
def enqueue(x):
    global size
    assert size < N, "queue is full"
    data[(front + size) % N] = x
    size += 1
    show(f"enqueue({x})")
def dequeue():
    global front, size
    x, data[front] = data[front], None
    front = (front + 1) % N
    size -= 1
    show("dequeue()", x)
for step in ["A", "B", "C", None, None, "D", "E", "F", "G", None]:
    dequeue() if step is None else enqueue(step)
print("queue order:", [data[(front + k) % N] for k in range(size)])
```

## 7. Worked applications: level-by-level search and a sliding window

**Breadth-first search.** A queue processes items in the order they were discovered, which makes it
the engine of any "nearest first" exploration. Finding the fewest moves through a grid maze is the
standard example: every cell that is $d$ steps away is dequeued before any cell $d + 1$ steps away.

```python-run
from collections import deque
maze = ["S.#.....",
        ".##.###.",
        "....#...",
        ".##.#.#.",
        "...#..#E"]
def shortest_path_length(maze):
    R, C = len(maze), len(maze[0])
    start = next((r, c) for r in range(R) for c in range(C) if maze[r][c] == "S")
    dist = {start: 0}
    Q = deque([start])
    while Q:
        r, c = Q.popleft()                        # FIFO: closest unexplored cell first
        if maze[r][c] == "E":
            return dist[(r, c)]
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nr < R and 0 <= nc < C and maze[nr][nc] != "#" and (nr, nc) not in dist:
                dist[(nr, nc)] = dist[(r, c)] + 1     # mark when ENQUEUED, not when dequeued
                Q.append((nr, nc))
    return -1
print("fewest moves from S to E:", shortest_path_length(maze))
```

Each cell enters and leaves the queue at most once, so the search is $O(RC)$. Replace the deque by a
stack and the same code performs a depth-first search — which still finds *a* path, but not
necessarily a shortest one. Swap `popleft()` for `list.pop(0)` and it still works but each dequeue
becomes $O(n)$.

**Sliding-window maximum with a deque.** Given a sequence and a window width $k$, report the maximum
of every window of $k$ consecutive values. Recomputing each maximum costs $O(nk)$. A deque of
*indices* does it in $O(n)$, using both ends:

- keep the deque's values **decreasing** from front to back: before appending a new index, pop from
  the **back** every index whose value is $\le$ the new value — those elements can never be a
  maximum again, since the newcomer is at least as large and stays in the window longer;
- pop from the **front** when the front index has slid out of the window;
- the front is always the index of the current window's maximum.

```python-run
from collections import deque
def sliding_max(values, k):
    D, out = deque(), []                  # D holds indices; their values are decreasing
    for i, x in enumerate(values):
        while D and values[D[-1]] <= x:   # delete_last: dominated candidates
            D.pop()
        D.append(i)                       # add_last
        if D[0] <= i - k:                 # delete_first: fell out of the window
            D.popleft()
        if i >= k - 1:
            out.append(values[D[0]])      # first: the maximum
    return out
vals = [1, 3, -1, -3, 5, 3, 6, 7]
print(sliding_max(vals, 3))
print(sliding_max(vals, 3) == [max(vals[i:i + 3]) for i in range(len(vals) - 2)])
```

**Dry run** ($k = 3$): after reading 1, 3, −1 the deque holds the indices of `[3, −1]` (1 was popped
when 3 arrived) → maximum 3. Reading −3 appends it: `[3, −1, −3]` → 3. Reading 5 pops all three:
`[5]` → 5. Reading 3: `[5, 3]` → 5. Reading 6 pops both: `[6]` → 6. Reading 7: `[7]` → 7. Output
`[3, 3, 5, 5, 6, 7]`.

**Why $O(n)$:** each index is appended exactly once and removed at most once, so the total number of
deque operations is at most $2n$, even though a single step may pop many elements — the same
amortised accounting as the dynamic array. This algorithm needs **all four** deque operations, which
is why neither a stack nor a queue suffices.

## 8. Pitfalls

- `list.pop(0)` in a BFS loop: quadratic. Use `collections.deque.popleft`.
- Resizing a circular buffer with a plain slice copy: the wrapped elements end up out of order.
- Computing `avail` with the *new* length while copying from the old array.
- Off-by-one in `last`: it is `(f + size - 1) % N`, not `(f + size) % N`.

## 9. Summary

- Queue = FIFO; circular arrays make enqueue/dequeue $O(1)$ amortised with $O(n)$ space.
- Index arithmetic modulo the capacity is the whole trick: `avail = (f + size) % N`,
  `f = (f + 1) % N`, and for deques `f = (f - 1) % N`.
- Use `collections.deque` in real Python code.

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 6.2–6.3.

## Check yourself

```quiz
[
  {"q": "Why is `list.pop(0)` a poor dequeue?",
   "options": ["It returns the wrong element", "It shifts all remaining elements: Theta(n)", "It is not allowed on lists", "It is O(log n)"], "answer": 1,
   "explain": "Removing from the front of an array requires moving every later element left."},
  {"q": "A circular queue has capacity N = 8, front f = 6 and size 4. Where does the next enqueue go?",
   "options": ["index 2", "index 10", "index 7", "index 0"], "answer": 0,
   "explain": "(6 + 4) mod 8 = 2."},
  {"q": "In ArrayQueue._resize, why can't we just copy old[0:size]?",
   "options": ["Python forbids slicing", "The elements may wrap around, so queue order differs from index order", "It would be O(n^2)", "Because of garbage collection"], "answer": 1,
   "explain": "Walking from the old front with modular indexing copies elements in queue order and resets front to 0."},
  {"q": "For a circular deque with front f and capacity N, add_first places the new element at...",
   "options": ["(f + 1) mod N", "(f - 1) mod N", "f + size", "0"], "answer": 1,
   "explain": "The front moves one step backwards around the circle."},
  {"q": "In collections.deque, accessing D[len(D)//2] costs...",
   "options": ["O(1)", "O(n)", "O(log n)", "It is not supported"], "answer": 1,
   "explain": "deque is a linked structure of blocks; end operations are O(1) but middle indexing walks."},
  {"q": "With front and back indices but no size counter, what ambiguity arises?",
   "options": ["Cannot tell full from empty, since both have front == back", "Cannot dequeue", "Cannot resize", "None"], "answer": 0,
   "explain": "Keep a size counter or leave one slot permanently empty."},
  {"q": "Queue from two stacks: what is the amortised cost of dequeue?",
   "options": ["O(n)", "O(1)", "O(log n)", "O(n^2)"], "answer": 1,
   "explain": "Each element is pushed and popped at most twice in total."}
]
```
