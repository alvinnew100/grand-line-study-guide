# Access frequencies, move-to-front and link vs array

This lesson finishes the linked-list module with the book's case study — maintaining a list of
elements ordered by how often they are accessed — which introduces the elegant **move-to-front
heuristic** and its analysis. We close by systematically comparing link-based and array-based
sequences.

## 1. The favourites problem

Many applications keep track of the most popular items: a browser's most-visited pages, a music
player's most-played songs, a phone's frequently called contacts. We want a **favourites list**
supporting:

- `access(e)`: record an access of `e` (adding it if new);
- `remove(e)`: remove `e`;
- `top(k)`: report the $k$ most-accessed elements.

## 2. Approach 1: keep the list sorted by count

Store `(element, count)` items in a positional list kept in nondecreasing order... of *decreasing*
count. On `access(e)`:

1. find `e`'s position by walking the list — $O(n)$;
2. increment its count;
3. while the item before it has a smaller count, move it forward (like one pass of insertion sort).

`top(k)` is then just the first $k$ items: $O(k)$. The weak point is `access`, $O(n)$ for the search
in the worst case.

```python-run
class FavoritesList:
    """Elements kept in nonincreasing order of access count (plain-list version for clarity)."""
    def __init__(self):
        self._data = []                      # list of [element, count]
    def _find(self, e):
        for i, item in enumerate(self._data):
            if item[0] == e:
                return i
        return None
    def access(self, e):
        i = self._find(e)
        if i is None:
            self._data.append([e, 0])
            i = len(self._data) - 1
        self._data[i][1] += 1
        while i > 0 and self._data[i - 1][1] < self._data[i][1]:   # bubble forward
            self._data[i - 1], self._data[i] = self._data[i], self._data[i - 1]
            i -= 1
    def top(self, k):
        return [e for e, _ in self._data[:k]]

fav = FavoritesList()
for site in "a b c a b a d a c c c c".split():
    fav.access(site)
print(fav.top(3), fav._data)
```

## 3. Approach 2: the move-to-front heuristic

Access patterns often have **locality of reference**: an element that was just accessed is likely
to be accessed again soon. The **move-to-front (MTF)** heuristic exploits this: whenever an element
is accessed, move it to the *front* of the list. Recently used elements cluster near the front, so
their searches are fast.

- `access(e)`: find `e` ($O(\text{position})$), move it to the front ($O(1)$ with a positional list).
- `top(k)`: the list is no longer sorted by count, so we must compute it. The book's approach:
  copy the items to a temporary list and repeatedly extract the maximum count $k$ times — $O(kn)$.
  (With sorting it is $O(n \log n)$; with a heap, $O(n + k\log n)$.)

So MTF trades a slower `top(k)` for potentially much faster accesses.

### 3.1 When does MTF win — and lose?

**Favourable example.** Suppose there are $n$ elements and the access sequence is: access element 1
$n$ times, then element 2 $n$ times, … (blocks of repeated accesses). With MTF, the first access in
each block searches the list ($O(n)$) and the remaining $n - 1$ accesses find the element at the front
($O(1)$). Total $O(n^2)$ over $n^2$ accesses — $O(1)$ amortised each. The sorted-by-count list must
walk further and further as counts accumulate.

**Unfavourable example.** Access the $n$ elements in a repeating cycle $1, 2, \ldots, n, 1, 2,
\ldots$. MTF always moves the just-accessed element to the front, so the next element needed is
always at the **back**: every access costs $\Theta(n)$. A count-sorted list would do equally badly
here, but a static order would be no worse. MTF is a heuristic, not a guarantee.

```python-run
def mtf_cost(order, accesses):
    """Return total positions scanned (1-based) using move-to-front."""
    L, cost = list(order), 0
    for x in accesses:
        i = L.index(x)
        cost += i + 1
        L.insert(0, L.pop(i))              # move to front
    return cost

def static_cost(order, accesses):
    pos = {x: i for i, x in enumerate(order)}
    return sum(pos[x] + 1 for x in accesses)

n = 50
items = list(range(n))
blocks = [x for x in items for _ in range(n)]          # 0,0,...,0,1,1,...
cycle = items * n                                      # 0,1,...,n-1,0,1,...
print("blocks: MTF", mtf_cost(items[::-1], blocks), " static", static_cost(items[::-1], blocks))
print("cycle:  MTF", mtf_cost(items, cycle), " static", static_cost(items, cycle))
```

> [!NOTE]
> A celebrated result (Sleator and Tarjan, 1985) shows MTF is **2-competitive**: on any access
> sequence its total cost is at most about twice that of the best possible list-reordering strategy
> that knows the future. The same authors invented splay trees, which apply a "move-to-root" idea
> to binary search trees (search-trees module).

### 3.2 Where MTF is used

- **Self-organising lists** in symbol tables and caches.
- **Move-to-front transform** in compression: in bzip2, after the Burrows–Wheeler transform, MTF
  converts runs of repeated symbols into runs of small integers, which compress well.
- **LRU caching** is MTF with a capacity: on each access move to front; when full, evict the back.

## 4. Link-based versus array-based sequences

Neither representation dominates. Choosing well is about matching the operations you need.

### 4.1 Advantages of arrays

1. **$O(1)$ access by index.** `A[k]` is a single address computation; a linked list needs $k$ hops.
2. **Lower constant factors.** Operations with equal big-O typically run faster on arrays — e.g.
   appending to a list vs creating a node object, setting two or four references, and updating size.
3. **Less memory** — typically. An array of $n$ references uses at most about $2n$ cells even right
   after a doubling resize (and exactly $n$ for a tuple). A singly linked list uses $2n$ references
   (element + next) *plus* per-node object overhead; doubly linked uses $3n$ plus overhead.
4. **Cache locality**: contiguous memory is prefetched efficiently by hardware.

### 4.2 Advantages of linked lists

1. **Worst-case $O(1)$ bounds** for operations, not amortised. In real-time systems (an aircraft
   controller, an audio callback), an occasional $O(n)$ resize pause is unacceptable.
2. **$O(1)$ insertion and deletion at arbitrary positions** given a reference (position) to the
   location. Arrays must shift: inserting at index $k$ costs $O(n - k + 1)$.
3. **No over-allocation**: memory is proportional to the number of elements at all times.
4. **Stable references**: positions remain valid as other elements change; array indices shift.

### 4.3 Summary table

| Operation | Dynamic array | Singly linked | Doubly linked |
|---|---|---|---|
| access $k$-th | $O(1)$ | $O(k)$ | $O(\min(k, n-k))$ |
| insert/delete at front | $O(n)$ | $O(1)$ | $O(1)$ |
| insert at back | $O(1)$ amortised | $O(1)$ with tail | $O(1)$ |
| delete at back | $O(1)$ amortised | $O(n)$ | $O(1)$ |
| insert/delete at known position | $O(n)$ | $O(1)$ after / $O(n)$ at | $O(1)$ |
| search for value | $O(n)$ | $O(n)$ | $O(n)$ |
| memory | ~$n$ to $2n$ refs | $2n$ refs + node overhead | $3n$ refs + node overhead |

> [!INTERVIEW]
> "Array or linked list?" Interviewers want to hear about access patterns, not dogma: arrays for
> indexing, iteration and cache efficiency (the default in Python); linked structures when you hold
> references into the middle and splice frequently, or need worst-case $O(1)$. Note that in Python,
> `collections.deque` already gives $O(1)$ at both ends.

## 5. Building both favourites lists on a linked structure

The demo in section 2 used a Python list for clarity, which hides the point of the case study: with
a **positional (doubly linked) list**, relocating an item costs $O(1)$ once it has been found — no
shifting. The book's `FavoritesList` wraps a `PositionalList` (the *composition* pattern) and
`FavoritesListMTF` inherits from it, overriding just two methods: `_move_up` and `top`. The cell
below is a compact, self-contained version of both.

```python-run
class _Node:
    __slots__ = "item", "prev", "next"
    def __init__(self, item, prev=None, next=None):
        self.item, self.prev, self.next = item, prev, next

class FavoritesList:
    """Items kept in nonincreasing order of access count, in a doubly linked list with sentinels."""
    def __init__(self):
        self._head, self._tail = _Node(None), _Node(None)
        self._head.next, self._tail.prev = self._tail, self._head
        self.steps = 0                               # nodes examined so far (our cost measure)

    # ---- linked-list plumbing: all O(1) ----
    def _unlink(self, node):
        node.prev.next, node.next.prev = node.next, node.prev
    def _insert_before(self, node, successor):
        node.prev, node.next = successor.prev, successor
        successor.prev.next = node
        successor.prev = node

    def _find(self, e):
        walk = self._head.next
        while walk is not self._tail:
            self.steps += 1
            if walk.item[0] == e:
                return walk
            walk = walk.next
        return None

    def _move_up(self, node):
        """Move node toward the front while its count exceeds its predecessor's."""
        walk = node.prev
        if walk is self._head or walk.item[1] >= node.item[1]:
            return                                    # already in the right place
        while walk.prev is not self._head and walk.prev.item[1] < node.item[1]:
            walk = walk.prev
        self._unlink(node)
        self._insert_before(node, walk)

    def access(self, e):
        node = self._find(e)
        if node is None:
            node = _Node([e, 0])
            self._insert_before(node, self._tail)     # new items start at the back
        node.item[1] += 1
        self._move_up(node)

    def top(self, k):
        out, walk = [], self._head.next
        while walk is not self._tail and len(out) < k:
            out.append(tuple(walk.item)); walk = walk.next
        return out

class FavoritesListMTF(FavoritesList):
    """Same interface, but uses the move-to-front heuristic."""
    def _move_up(self, node):                         # override: straight to the front, O(1)
        if node.prev is not self._head:
            self._unlink(node)
            self._insert_before(node, self._head.next)
    def top(self, k):                                 # override: list is not sorted by count
        temp, walk = [], self._head.next
        while walk is not self._tail:
            temp.append(tuple(walk.item)); walk = walk.next
        out = []
        for _ in range(min(k, len(temp))):            # k rounds of 'find the max': O(kn)
            best = max(range(len(temp)), key=lambda i: temp[i][1])
            out.append(temp.pop(best))
        return out

import random
random.seed(3)
pages = [f"p{i}" for i in range(200)]
weights = [1 / (i + 1) for i in range(200)]           # Zipf-like popularity: a few pages dominate
stream = random.choices(pages, weights, k=20000)
bursty = [p for p in random.choices(pages, k=400) for _ in range(50)]   # 50 hits in a row per page
for name, seq in [("zipf", stream), ("bursty", bursty)]:
    a, b = FavoritesList(), FavoritesListMTF()
    for p in seq: a.access(p); b.access(p)
    print(f"{name:6s}: count-sorted scanned {a.steps:>9,} nodes; move-to-front scanned {b.steps:>9,}")
print("top 3 agree:", sorted(a.top(3)) == sorted(b.top(3)))
```

### 5.1 Reading the experiment

Two workloads, two different winners — which is exactly the lesson of the case study.

- **Zipf-like, stationary popularity.** A handful of pages receive most of the hits and stay popular
  forever. Keeping the list sorted by count places exactly those pages at the front and *keeps* them
  there, so its scans are short. Move-to-front does almost as well, but every access to a rare page
  drags that page to the very front, pushing the popular pages back by one position; MTF therefore
  scans somewhat more.
- **Bursty accesses (locality in time).** Each page is hit 50 times in a row and then abandoned. MTF
  pays one long scan for the first hit and then finds the page at position 1 for the remaining 49.
  The count-sorted list is hostage to history: pages that were popular long ago still occupy the
  front, so the currently hot page sits behind them until its count catches up.

So the count-sorted list answers "which items are popular **overall**?", and MTF answers "which
items are popular **right now**?". When you cannot predict which regime you are in, MTF's
2-competitiveness makes it the safer default.

### 5.2 Cost summary for the two classes

| Operation | `FavoritesList` (sorted by count) | `FavoritesListMTF` |
|---|---|---|
| find the element | $O(p)$ for position $p$; $O(n)$ worst case | $O(p)$; small when accesses have locality |
| relocate after access | walk up past lower counts, then $O(1)$ splice | $O(1)$ splice to the front |
| `top(k)` | $O(k)$ | $O(kn)$ as written; $O(n + k\log n)$ with a heap |
| `remove(e)` | $O(n)$ to find, $O(1)$ to unlink | the same |

Two other self-organising heuristics are worth knowing: **transpose** (swap the accessed item with
its predecessor — cautious, converges slowly, but less disturbed by one-off accesses) and
**frequency count** (which is exactly the count-sorted list). And if the *search* itself must be
fast, pair the linked list with a hash map from element to node: the find drops to expected
$O(1)$, and the list is used purely for ordering — the design of every LRU cache.

## 6. Pitfalls

- Assuming linked lists make "insert in the middle" cheap when you must first *search* for the
  spot ($O(n)$).
- Implementing MTF on a Python list with `insert(0, ...)`: that is $O(n)$ per move, defeating the
  purpose (fine for demos; use a linked/positional list or `OrderedDict.move_to_end` for real).
- Forgetting that `top(k)` with MTF requires a selection step.

## 7. Summary

- Sorted-by-count favourites: `access` $O(n)$, `top(k)` $O(k)$.
- Move-to-front: `access` cost depends on recency (fast with locality), `top(k)` $O(kn)$; 2-competitive.
- Arrays win on indexing, constants and memory; linked lists win on worst-case bounds, splicing at
  known positions, and stable references.

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 7.6–7.7.

## Check yourself

```quiz
[
  {"q": "What does the move-to-front heuristic do on each access?",
   "options": ["Swaps the element with its predecessor", "Moves the accessed element to the front of the list", "Sorts the list by count", "Moves the element to the back"], "answer": 1,
   "explain": "Recently accessed items cluster at the front, exploiting locality of reference."},
  {"q": "On the cyclic access sequence 1, 2, ..., n, 1, 2, ..., n, ..., each MTF access costs...",
   "options": ["O(1)", "Theta(n)", "O(log n)", "O(k)"], "answer": 1,
   "explain": "The element needed next is always at the back, because everything after it was just moved forward."},
  {"q": "In the book's MTF favourites list, top(k) costs...",
   "options": ["O(k)", "O(kn)", "O(1)", "O(n^2)"], "answer": 1,
   "explain": "The list is not sorted by count, so k rounds of finding the max over n items are needed."},
  {"q": "Which is an advantage of linked lists over arrays?",
   "options": ["O(1) access by index", "Better cache locality", "Worst-case O(1) insertion at a known position", "Less memory per element"], "answer": 2,
   "explain": "Arrays must shift elements; linked lists just update references."},
  {"q": "Which is an advantage of arrays over linked lists?",
   "options": ["Worst-case O(1) appends", "O(1) access to the k-th element", "O(1) deletion in the middle", "No over-allocation"], "answer": 1,
   "explain": "Address arithmetic gives direct indexing; appends are only amortised O(1)."},
  {"q": "MTF is called 2-competitive. This means...",
   "options": ["It is twice as fast as sorting", "Its total cost on any sequence is within about a factor 2 of the optimal offline strategy", "It uses two lists", "It needs two passes"], "answer": 1,
   "explain": "Sleator and Tarjan proved this bound, making MTF a robust choice when the access pattern is unknown."}
]
```
