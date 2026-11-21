# Access frequencies, move-to-front and link vs array

> **Before this lesson:** You should know singly and doubly linked lists, positions, and the LRU
> cache from [Doubly linked lists and positional lists](#/lesson/dsa-foundations/doubly-positional),
> and the costs of list operations from
> [Low-level arrays](#/lesson/dsa-foundations/low-level-arrays). Amortised cost comes from
> [Dynamic arrays](#/lesson/dsa-foundations/dynamic-arrays).

## In plain words

This lesson asks a practical question: if you keep a list of things and look them up by walking
along the list, in what order should you keep them so that lookups are quick? It then steps back
and compares the two ways of storing a sequence that you now know, arrays and linked lists.

Think of the spices on a kitchen shelf. If you put each jar back at the *front* of the shelf
after using it, the jars you cook with most drift to the front on their own, and the saffron you
use once a year ends up at the back. You never planned an order; the habit produced one. That
habit is the **move-to-front heuristic**. (A **heuristic** is a rule of thumb that usually works
well but carries no guarantee of being best.)

Why it matters for a job: "should this be an array or a linked list?" is a question you will
answer in interviews and in code review, and a good answer talks about which operations are
frequent, not about which structure is "better". Move-to-front is also the idea underneath LRU
caches and part of the bzip2 compression program.

## 1. The favourites problem

Many applications track the most popular items: the pages you visit most in a browser, the
songs you play most, the contacts you call most. We want a **favourites list** with three
operations:

- `access(e)`: record one more use of item `e`, adding it to the list if it is new;
- `remove(e)`: take `e` off the list;
- `top(k)`: report the $k$ most-used items.

## 2. Approach 1: keep the list sorted by count

Store each item together with a count of how many times it has been accessed, and keep the list
ordered from the highest count to the lowest. On `access(e)`:

1. find `e` by walking along the list from the front, which is $O(n)$ in the worst case;
2. add one to its count;
3. while the item in front of it has a smaller count, move it one place forward (the same
   sliding step as insertion sort).

With the list in that order, `top(k)` is the first $k$ items, which costs $O(k)$. The weak
point is `access`: the search can take $O(n)$.

The first demo uses a plain Python list of `[element, count]` pairs so that the logic is easy to
follow; section 5 rebuilds it on a linked list.

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

**Reading this code.** `_find` walks the list and returns the index of `e`, or `None`.
`enumerate` supplies each item together with its index. `access` appends a new `[e, 0]` pair if
the item was not found, adds one to the count, and then swaps the pair forward while the pair in
front of it has a smaller count. The twelve accesses are a ×4, b ×2, c ×5, d ×1, so the output
is `['c', 'a', 'b'] [['c', 5], ['a', 4], ['b', 2], ['d', 1]]`.

## 3. Approach 2: the move-to-front heuristic

Real access patterns often show **locality of reference**: an item that was used a moment ago is
likely to be used again soon. (You open the same few files all morning, then a different few all
afternoon.) The **move-to-front (MTF)** heuristic exploits this. Whenever an item is accessed,
move it to the *front* of the list. Recently used items gather near the front, so finding them
again is quick.

- `access(e)`: find `e`, at a cost proportional to its position, then move it to the front,
  which is $O(1)$ in a doubly linked list.
- `top(k)`: the list is no longer in order of count, so the answer has to be computed. One
  direct way is to copy the items to a temporary list and pick out the largest count $k$ times,
  for $O(kn)$ in total. (Sorting the copy costs $O(n \log n)$; the heap of a later module does
  it in $O(n + k\log n)$.)

So MTF accepts a slower `top(k)` in exchange for accesses that may be much faster.

### 3.1 When does MTF win, and when does it lose?

**A favourable case.** Suppose there are $n$ items and the accesses come in blocks: item 1 is
accessed $n$ times, then item 2 is accessed $n$ times, and so on. With MTF, the first access of
each block has to search the list, costing up to $n$ steps, and the other $n - 1$ accesses find
the item at the very front, costing 1 step each. That is about $2n$ steps per block and $2n^2$
steps for all $n^2$ accesses: $O(1)$ amortised per access. The count-sorted list fares worse,
because the item now in demand has to climb past all the earlier favourites.

**An unfavourable case.** Access the $n$ items in an endless cycle $1, 2, \ldots, n, 1, 2,
\ldots$. MTF moves each item to the front as it is used, which pushes every other item one place
back, so the item needed next is always at the **back** of the list: every access costs
$\Theta(n)$. A list that never reordered itself would do no worse here. MTF is a heuristic, not
a guarantee.

The demo measures both cases. `mtf_cost` counts how many positions are scanned when the list
reorders itself by move-to-front; `static_cost` counts the same for a list that never changes.

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

With 50 items and 2,500 accesses, the block pattern costs MTF 4,950 positions (each block is one
scan of 50 followed by 49 hits at position 1) against 63,750 for a list that never reorders,
while the cycle pattern costs MTF 123,775 against 63,750 for the fixed list. One pattern rewards the heuristic and the other punishes it.

> [!NOTE]
> A celebrated result of Sleator and Tarjan (1985) shows that MTF is **2-competitive**: on *any*
> sequence of accesses, its total cost is at most about twice the cost of the best possible
> reordering strategy, even one that knows the whole future sequence in advance. So MTF can
> lose, but never by much. The same two researchers invented splay trees, which apply a
> "move to the top" idea to search trees (search-trees module).

### 3.2 Where MTF is used

- **Self-organising lists** inside compilers and caches, where a short list is searched often.
- **Compression.** The bzip2 program includes a move-to-front step that turns runs of repeated
  symbols into runs of small numbers, which then compress well.
- **LRU caching** is MTF with a size limit: on each access move the item to the front, and when
  the cache is full, evict the item at the back.

## 4. Link-based versus array-based sequences

Neither representation is better in general. Choosing well means matching the structure to the
operations you will perform most.

### 4.1 Advantages of arrays

1. **$O(1)$ access by index.** `A[k]` is one address calculation; a linked list needs $k$ hops.
2. **Smaller constant factors.** When both structures have the same big-O for an operation, the
   array version is usually quicker in practice. Appending to a list writes one cell; adding a
   node means creating an object, setting two or four references and updating a count.
3. **Less memory, usually.** An array of $n$ references has at most about $2n$ cells even
   immediately after doubling (and exactly $n$ for a tuple). A singly linked list needs $2n$
   references (element and next) *plus* the bookkeeping of $n$ separate node objects; a doubly
   linked list needs $3n$ plus that bookkeeping.
4. **Cache locality.** Processors keep recently used memory, and the memory next to it, in a
   small fast store called the **cache**. An array's cells are neighbours, so scanning it stays
   inside the cache; a list's nodes are scattered, so each hop may be a slow trip to main
   memory.

### 4.2 Advantages of linked lists

1. **Worst-case $O(1)$ bounds**, not amortised ones. In software that must respond within a
   fixed time (flight control, live audio), an occasional $O(n)$ pause for a resize is not
   acceptable.
2. **$O(1)$ insertion and deletion anywhere**, given a reference (a position) to the spot. An
   array must shift: inserting at index $k$ costs $O(n - k + 1)$.
3. **No spare capacity.** Memory use is proportional to the number of items at every moment.
4. **Stable handles.** A position stays valid while other items change; array indices shift.

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

In the table, "after / at" in the singly linked column means: $O(1)$ to insert or delete
*after* a node you hold, but $O(n)$ to delete that node itself, since its predecessor must be
found. In the doubly linked column, access to the $k$-th item can start from whichever end is
nearer.

> [!INTERVIEW]
> "Array or linked list?" Interviewers want reasoning about access patterns, not a slogan. Use
> an array for indexing, scanning and cache efficiency; it is the default in Python. Use a
> linked structure when you hold references into the middle and insert or remove there often, or
> when you need worst-case $O(1)$. Mention that Python's `collections.deque` already gives
> $O(1)$ at both ends.

## 5. Building both favourites lists on a linked structure

The demo in section 2 used a Python list for clarity, which hides the point of the case study.
On a **doubly linked list**, moving an item to a new place costs $O(1)$ once the item has been
found; nothing is shifted. The cell below builds both strategies on such a list. The second
class, `FavoritesListMTF`, inherits from the first and **overrides** (replaces) two of its
methods, `_move_up` and `top`; everything else is shared. Each list also counts in `steps` how
many nodes its searches examine, which is the cost we compare.

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

The experiment feeds both lists two streams of page visits. In the first, `random.choices` picks
pages with unequal probabilities given by `weights`: page $i$ is chosen in proportion to
$1/(i+1)$, so a few pages are very popular and most are rare. This shape is known as a *Zipf*
distribution and is typical of web traffic and word frequencies. In the second stream each
randomly chosen page is visited 50 times in a row.

There are two workloads and two different winners, which is the lesson of the case study.

- **Zipf-like popularity that does not change over time.** A handful of pages receive most of
  the hits and stay popular forever. Keeping the list sorted by count places exactly those pages at the front and *keeps* them
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

- **Assuming a linked list makes "insert in the middle" cheap.** The insertion itself is
  $O(1)$, but if you must first *search* for the spot, that search is $O(n)$.
- **Implementing MTF on a Python list with `insert(0, ...)`.** Each move then shifts the whole
  list, $O(n)$, which defeats the purpose. That is fine for a demo; for real use, take a linked
  list or `OrderedDict.move_to_end`.
- **Forgetting that `top(k)` under MTF needs a selection step.** The list order reflects
  recency, not popularity.
- **Reading "2-competitive" as "always within a factor of two of a fixed list".** The comparison
  is with the best strategy that is allowed to reorder; on the cycle pattern, MTF and that best
  strategy both do poorly.
- **Choosing a structure by reputation.** Measure or reason about the operations you perform.

## 7. Summary

- A favourites list sorted by count has `access` in $O(n)$ and `top(k)` in $O(k)$.
- Under move-to-front, the cost of `access` depends on how recently the item was used (fast when
  accesses have locality), `top(k)` costs $O(kn)$, and the total is never much worse than the
  best reordering strategy.
- Arrays win on access by index, constant factors, memory and cache behaviour. Linked lists win
  on worst-case bounds, insertion and removal at known positions, and handles that stay valid.

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 7.6–7.7.

## Glossary

- **Heuristic**: a rule of thumb that usually works well but has no guarantee of being best.
- **Favourites list**: a list that records how often each item is accessed and reports the top
  few.
- **Locality of reference**: the tendency for recently used items to be used again soon.
- **Move-to-front (MTF)**: moving each accessed item to the front of the list.
- **Self-organising list**: a list that reorders itself in response to accesses.
- **Competitive (2-competitive)**: never more than a fixed factor (here about 2) worse than the
  best strategy that knows the future.
- **Transpose heuristic**: swapping an accessed item with the one in front of it.
- **Zipf distribution**: a popularity pattern in which a few items account for most accesses.
- **Cache (processor)**: a small, fast memory holding recently used data and its neighbours.
- **Override**: to replace an inherited method with a new version in a subclass.
- **Splice**: to insert or remove a node by redirecting a few references.

## Check yourself

```quiz
[
  {"q": "What does the move-to-front heuristic do on each access?",
   "options": ["Swaps the element with its predecessor", "Moves the accessed element to the front of the list", "Sorts the list by count", "Moves the element to the back"], "answer": 1,
   "explain": "Recently accessed items cluster at the front, exploiting locality of reference."},
  {"q": "On the cyclic access sequence 1, 2, ..., n, 1, 2, ..., n, ..., each MTF access costs...",
   "options": ["O(1)", "Theta(n)", "O(log n)", "O(k)"], "answer": 1,
   "explain": "The element needed next is always at the back, because every other element has been moved in front of it since it was last used."},
  {"q": "In the book's MTF favourites list, top(k) costs...",
   "options": ["O(k)", "O(kn)", "O(1)", "O(n^2)"], "answer": 1,
   "explain": "The list is not sorted by count, so k rounds of finding the max over n items are needed."},
  {"q": "Which is an advantage of linked lists over arrays?",
   "options": ["O(1) access by index", "Better cache locality", "Worst-case O(1) insertion at a known position", "Less memory per element"], "answer": 2,
   "explain": "Arrays must shift elements; linked lists only update a few references."},
  {"q": "Which is an advantage of arrays over linked lists?",
   "options": ["Worst-case O(1) appends", "O(1) access to the k-th element", "O(1) deletion in the middle", "No over-allocation"], "answer": 1,
   "explain": "Address arithmetic gives direct indexing; appends are only amortised O(1)."},
  {"q": "MTF is called 2-competitive. This means...",
   "options": ["It is twice as fast as sorting", "Its total cost on any sequence is within about a factor 2 of the optimal offline strategy", "It uses two lists", "It needs two passes"], "answer": 1,
   "explain": "Sleator and Tarjan proved this bound, making MTF a robust choice when the access pattern is unknown."}
]
```
