# Designing recursion and eliminating it

> **Before this lesson:** You should be able to read a recursive function and say what its base
> case is ([Thinking recursively](#/lesson/dsa-foundations/recursion-examples)), and know what a
> recurrence, the call stack and overlapping subproblems are
> ([Analysing recursive algorithms](#/lesson/dsa-foundations/recursion-analysis)).

## In plain words

The last two lessons read other people's recursive functions. This one is about writing your
own, and about knowing when to take the recursion back out.

Writing a recursion is like delegating. A good manager facing a big job asks one question: "if a
reliable assistant did everything except one small piece, what would be left for me to do?" You
do not need to know *how* the assistant does their part; you only need to hand over a smaller
job and finish off the result. The recipe in section 1 is that question, made precise.

Taking a recursion out is the reverse skill. Every recursive call leaves a sticky note on a pile
("when this comes back, multiply by 4"). Python's pile has a height limit. When the pile would
grow too tall, you can keep the notes yourself in an ordinary list, or notice that some
recursions never need notes at all and are loops in disguise.

Why it matters for a job: "now do it without recursion" is among the most common interview
follow-ups, and in production Python a recursion a few thousand levels deep crashes. Knowing the
three standard conversions (loop, explicit stack, table) covers almost every case.

## 1. A design recipe

Designing a recursion comes down to two activities:

1. **Test for base cases first.** There must be at least one input that is answered directly,
   with no recursive call. Every possible chain of calls has to end at one of them.
2. **Recur.** Otherwise, make one or more recursive calls, each on an input that is closer to a
   base case than the current one.

A practical way to find the recursion is the delegating question: *"if someone handed me the
answer for a smaller version of this problem, how would I finish the job?"* The table applies it
to five problems. (A **palindrome** is a word that reads the same backwards, such as "level"; the
last two rows preview later modules.)

| Problem | Smaller version | Finishing step |
|---|---|---|
| sum of `S[0:n]` | sum of `S[0:n-1]` | add `S[n-1]` |
| reverse `S[i:j]` | reverse `S[i+1:j-1]` | swap `S[i]`, `S[j-1]` |
| is `S[i:j]` a palindrome | is `S[i+1:j-1]` | compare the ends |
| height of a tree | height of each subtree | 1 + max |
| sorted merge of halves | sort each half | merge |

### 1.1 Parameterising a recursion

A function's **signature** is its name together with the list of parameters it accepts. Often
the signature a user wants is not the one the recursion needs. Callers want to write
`binary_search(data, target)`, but each recursive call has to know *which part of the list* it
is responsible for. The solution is to give the recursive function extra parameters, here `low`
and `high`, and to put a small function in front of it that supplies their starting values. That
front function is called a **wrapper**. (The leading underscore in `_bsearch` is a Python
convention meaning "internal helper, not for outside use", and `...` stands for the body shown
in the earlier lesson.)

```python
def binary_search(data, target):
    return _bsearch(data, target, 0, len(data) - 1)

def _bsearch(data, target, low, high):
    ...
```

Passing positions instead of slices is not only tidier. A slice copies its items, costing $O(n)$
per call, which would make binary search linear and `linear_sum` quadratic. The mirror-image
trick is to *return* extra information, as `good_fibonacci` did by returning two values instead
of one.

The palindrome checker below uses default values in place of a separate wrapper. A caller writes
`is_palindrome("racecar")`; the hidden parameters `lo` and `hi` mark the first and last
characters still to be compared and move inwards with each call.

```python-run
def is_palindrome(s, lo=0, hi=None):
    if hi is None:
        hi = len(s) - 1                 # public call: initialise the hidden parameters
    if lo >= hi:
        return True                     # empty or one character
    if s[lo] != s[hi]:
        return False
    return is_palindrome(s, lo + 1, hi - 1)

for w in ["racecar", "gohangasalamiimalasagnahog", "python", "", "a"]:
    print(repr(w), is_palindrome(w))
```

**Reading this code.** If `hi` was not supplied, this is the caller's first call, so `hi` is set
to the last position. `lo >= hi` means zero or one character remains: a palindrome by definition,
the base case. If the two end characters differ, the answer is `False` at once. Otherwise the
answer is whatever the inner stretch gives. `repr(w)` prints a string with its quotes, so the
empty string is visible. The output is `True`, `True`, `False`, `True`, `True`.

## 2. Recursion versus iteration

**Iteration** means repeating with a loop. The cost of recursion, compared with a loop, is the
call stack: every call that has started and not finished keeps a frame. For a recursion that
goes $n$ levels deep in one chain, that is $O(n)$ memory and, in Python, the risk of a
`RecursionError`. Any recursive algorithm *can* be rewritten without recursion by keeping your
own pile of unfinished subproblems; for some recursions it is easier still.

### 2.1 Tail recursion

A recursion is a **tail recursion** if every recursive call is the *very last* thing the
function does, and the value that comes back (if any) is returned unchanged. In that situation
the caller has nothing left to do when the call returns, so its frame holds no useful
information. Such a recursion can be turned into a loop that **assigns new values to the
parameters** and goes back to the top.

`binary_search` and `reverse` are tail-recursive: look for `return binary_search(...)` with
nothing wrapped around it. `factorial` is **not**: in `return n * factorial(n - 1)` the caller
still has a multiplication to do after the call comes back. Likewise `linear_sum` still has an
addition to do.

Compare the loop versions below with the recursive ones from the earlier lessons. The comments
mark where each recursive call turned into an assignment.

```python-run
def binary_search_iterative(data, target):
    low, high = 0, len(data) - 1
    while low <= high:                  # was: the base-case test
        mid = (low + high) // 2
        if target == data[mid]:
            return True
        elif target < data[mid]:
            high = mid - 1              # was: return binary_search(data, target, low, mid - 1)
        else:
            low = mid + 1               # was: return binary_search(data, target, mid + 1, high)
    return False

def reverse_iterative(S):
    start, stop = 0, len(S)
    while start < stop - 1:
        S[start], S[stop - 1] = S[stop - 1], S[start]
        start, stop = start + 1, stop - 1
    return S

print(binary_search_iterative(list(range(0, 100, 3)), 42), reverse_iterative([1, 2, 3, 4, 5]))
```

The base-case test `low > high` became the loop condition `low <= high` (its opposite: keep going
while the range is not empty). The demo searches the multiples of 3 below 100 for 42 and reverses
a five-item list; it prints `True [5, 4, 3, 2, 1]`.

> [!NOTE]
> Some languages (Scheme always, C compilers optionally) reuse the frame for a tail call
> automatically, a feature called *tail-call optimisation*. CPython, the standard Python
> interpreter, deliberately does not, because its designer preferred error reports that show
> every call. So in Python you must remove tail recursion yourself when depth matters.

### 2.2 Accumulators: making a recursion tail-recursive

A recursion that still has work to do after the call can often be converted by carrying that
unfinished work *forward* in an extra parameter, called an **accumulator**, instead of leaving it
behind on the stack. For factorial, the accumulator holds the product so far:

```python
def factorial_acc(n, acc=1):
    if n == 0:
        return acc
    return factorial_acc(n - 1, acc * n)   # tail call: nothing left to do afterwards
```

Trace `factorial_acc(3)`: it calls `factorial_acc(2, 3)`, which calls `factorial_acc(1, 6)`,
which calls `factorial_acc(0, 6)`, which returns 6. The multiplications happen on the way *down*,
and the answer is ready when the base case is reached. Now the call is a tail call, and the
recursion can be replaced by a loop:

```python
def factorial_iter(n):
    acc = 1
    while n > 0:
        n, acc = n - 1, acc * n
    return acc
```

The line `n, acc = n - 1, acc * n` computes both right-hand values first and then assigns them
together, so `acc * n` uses the old `n`.

### 2.3 Simulating the stack explicitly

When a function makes several recursive calls (binary or multiple recursion), reassigning
parameters is not enough, because after the first call returns there is still a second one to
make. The general method is to keep your own **stack** of work still to be done: a list where
you add to the end (`append`) and take from the end (`pop`). Here is the disk-usage computation
without recursion:

```python-run
fs = {"a": {"b": {"c.txt": 5, "d.txt": 7}, "e.txt": 11}, "f": {"g.txt": 2}, "h.txt": 1}

def total_size_iterative(root):
    total, stack = 0, [root]           # the stack replaces the call stack
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            stack.extend(node.values())   # "recursive calls" become pushes
            total += 1                    # directory overhead
        else:
            total += node
    return total

def total_size_recursive(node):
    if not isinstance(node, dict):
        return node
    return 1 + sum(total_size_recursive(c) for c in node.values())

print(total_size_iterative(fs), total_size_recursive(fs))
```

**Reading this code.** `stack` starts with one entry, the whole file system. `while stack:` keeps
going as long as the list is not empty. Each round takes one entry off the end. If it is a
directory (a `dict`), all of its contents are added to the stack with `extend`, and 1 is added
for the directory itself; if it is a file, its size is added. Where the recursive version would
have made a call, this version makes a note to come back later. Both functions print 30.

When something must happen *after* a directory's contents are finished (printing its total, for
example), push a marker such as `(node, "after")` underneath the children, so that the "return"
step is simulated too. Section 6 does exactly that.

## 3. Memoisation: keeping recursion, losing the waste

If the trouble with a recursion is *repeated subproblems* and not depth, store each result the
first time it is computed and look it up afterwards. Such a store is a **cache**, and the
technique is **memoisation**. Python provides it ready-made. The line `@lru_cache(maxsize=None)`
written above a function is a **decorator**: it wraps the function so that every call first
checks whether the same arguments have been seen before.

```python-run
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    return n if n <= 1 else fib(n - 1) + fib(n - 2)

def fib_bottom_up(n):            # the same idea, no recursion at all
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

print(fib(90), fib_bottom_up(90))
```

Both print `2880067194370816120`, the 90th Fibonacci number, instantly. Without the cache the
recursive version would need more than a million million million calls. Memoising turns
$\Theta(\phi^n)$ into $O(n)$, because each value from `fib(0)` to `fib(n)` is computed once. The
second function, `fib_bottom_up`, starts from the smallest cases and works upwards in a loop,
keeping only the last two values, so it uses $O(1)$ extra memory. The dynamic-programming lesson
in the text-processing module builds on this pattern.

## 4. When should you use recursion?

**Prefer recursion when:**

- the data is itself nested (trees, lists inside lists, file systems, arithmetic expressions
  with brackets);
- the algorithm splits the problem into parts and solves each part the same way, a strategy
  called *divide and conquer* (binary search, and the merge-sort and quick-sort of later
  lessons);
- you are exploring combinations of choices (backtracking).

**Prefer iteration when:**

- the recursion is a single deep chain (Python's depth limit, memory);
- the recursion is tail-recursive (the loop is equally clear);
- subproblems overlap and filling a table from the bottom up is natural.

> [!INTERVIEW]
> "Can you do this without recursion?" Answer in three steps: (1) is it tail-recursive? then reassign
> parameters in a loop; (2) otherwise, push pending subproblems on an explicit stack (or a queue for
> breadth-first order); (3) if subproblems overlap, fill a table bottom-up. Mention the Python
> recursion limit as the practical motivation.

## 5. Worked design example: the English ruler, iteratively?

The ruler recursion `draw_interval(c)` is binary, not tail recursive. An iterative version exists
but is far less clear — you would need to simulate both pending halves on a stack. Recursion's
depth here is only $c$ (a handful), and the output is exponential anyway, so recursion is the right
tool. The lesson: eliminate recursion **when depth or overhead is the problem**, not by reflex.

```python-run
# Iterative ruler interval via an explicit stack of (length, phase) frames - compare clarity!
def draw_interval_iter(c):
    lines, stack = [], [(c, 0)]
    while stack:
        length, phase = stack.pop()
        if length == 0:
            continue
        if phase == 0:                    # about to do top half
            stack.append((length, 1))
            stack.append((length - 1, 0))
        else:                             # top half done: print center, then bottom half
            lines.append('-' * length)
            stack.append((length - 1, 0))
    return lines
print("\n".join(draw_interval_iter(3)))
```

## 6. Worked design example: the Towers of Hanoi

A problem where the recursive design is short and the iterative one is genuinely harder. There are
three pegs and $n$ discs of different sizes stacked on peg A, largest at the bottom. Move the whole
stack to peg C, moving one disc at a time and never placing a larger disc on a smaller one.

**Apply the recipe.** *If someone handed me the solution for $n - 1$ discs, how would I finish?*
The largest disc can only move when the $n - 1$ smaller discs are all out of the way, stacked on the
spare peg. So:

1. move the top $n - 1$ discs from the source to the **spare** peg (recursively);
2. move the largest disc from the source to the target;
3. move the $n - 1$ discs from the spare peg to the target (recursively).

**Base case:** zero discs — nothing to do. **Progress:** each call has one disc fewer.
**Parameterisation:** the pegs must be parameters, because their roles (source, spare, target)
rotate from call to call.

```python-run
def hanoi(n, source, target, spare, moves):
    if n == 0:
        return                                    # base case: nothing to move
    hanoi(n - 1, source, spare, target, moves)    # clear the way
    moves.append((n, source, target))             # move the largest disc
    hanoi(n - 1, spare, target, source, moves)    # bring the rest back on top

def check(n, moves):
    """Replay the moves and verify the rules."""
    pegs = {"A": list(range(n, 0, -1)), "B": [], "C": []}
    for disc, src, dst in moves:
        assert pegs[src] and pegs[src][-1] == disc, "disc is not on top of its peg"
        assert not pegs[dst] or pegs[dst][-1] > disc, "larger disc placed on a smaller one"
        pegs[dst].append(pegs[src].pop())
    return pegs["C"] == list(range(n, 0, -1))

moves = []
hanoi(3, "A", "C", "B", moves)
for disc, src, dst in moves:
    print(f"move disc {disc}: {src} -> {dst}")
for n in [3, 10, 16]:
    moves = []
    hanoi(n, "A", "C", "B", moves)
    print(f"n = {n:2d}: {len(moves):6d} moves (2^n - 1 = {2**n - 1}), valid = {check(n, moves)}")
```

### Analysis

Let $T(n)$ be the number of moves: $T(0) = 0$ and $T(n) = 2T(n-1) + 1$ — the same recurrence as the
English ruler — so $T(n) = 2^n - 1$. This is optimal: the largest disc must move at least once, and
before and after that move the other $n - 1$ discs must be fully transferred, so any solution needs
at least $2T(n-1) + 1$ moves. The **recursion depth**, however, is only $n$: the stack holds one
frame per disc size, so memory is $O(n)$ even though time is $O(2^n)$. Depth and total work are
different quantities — a point worth internalising before the divide-and-conquer sorting lessons.

### Eliminating the recursion

`hanoi` makes **two** recursive calls, and only the second is a tail call. We can turn the tail call
into a loop by reassigning parameters, and simulate the first call with an explicit stack of pending
work. Each stack entry is either a subproblem to expand or a single move to perform:

```python-run
def hanoi_iterative(n, source="A", target="C", spare="B"):
    moves = []
    stack = [("solve", n, source, target, spare)]
    while stack:
        kind, k, src, dst, tmp = stack.pop()
        if kind == "move":
            moves.append((k, src, dst))
        elif k > 0:
            # push in REVERSE order of execution: the stack is last-in, first-out
            stack.append(("solve", k - 1, tmp, dst, src))     # step 3
            stack.append(("move", k, src, dst, tmp))          # step 2
            stack.append(("solve", k - 1, src, tmp, dst))     # step 1
    return moves

def hanoi_recursive(n, source="A", target="C", spare="B"):
    if n == 0: return []
    return (hanoi_recursive(n - 1, source, spare, target) + [(n, source, target)]
            + hanoi_recursive(n - 1, spare, target, source))

print(hanoi_iterative(4) == hanoi_recursive(4), len(hanoi_iterative(12)))
```

Two things to notice. First, the pending steps are pushed in **reverse** order, because a stack
returns them last-in, first-out — the commonest bug when hand-converting a recursion. Second, the
iterative version is neither shorter nor clearer than the recursive one, and it uses the same
$O(n)$ extra memory: the explicit stack *is* the call stack, written out by hand. That is the
general truth about removing recursion. It buys freedom from Python's depth limit and from the
small cost of each function call; it does not change the growth rate. Here, with depth only $n$
for a computation of $2^n$ steps, the recursive version is the right engineering choice.

## 7. Pitfalls

- **Believing Python will optimise tail calls.** It will not; a deep tail recursion still fails.
- **Replacing a non-tail recursion by a loop and losing the work that came after the call.** If
  the function did something after its recursive call returned, the loop version needs an
  accumulator or an explicit stack to do it.
- **Using a list as a default argument for an accumulator** (`def f(x, acc=[])`). Python creates
  that list once, when the function is defined, and every call shares it, so results from one
  call leak into the next. Write `acc=None` and create the list inside the function.
- **Memoising a function whose arguments are lists.** The cache looks arguments up in a
  dictionary, which only accepts values that cannot change (such values are called *hashable*).
  Convert lists to tuples first.
- **Pushing pending steps in the order you want them done.** A stack hands them back in reverse.

## 8. Summary

- Design: handle base cases first, then make recursive calls that move towards a base case.
  Give the recursive function the parameters it needs (positions, accumulators) and hide them
  behind a clean wrapper.
- A tail recursion becomes a loop by reassigning its parameters; other recursions need an
  explicit stack of pending work.
- When subproblems overlap, memoise or fill a table bottom-up.
- Removing recursion saves stack depth, not asymptotic time or space.

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 4.5–4.6.

## Glossary

- **Signature**: a function's name and the parameters it accepts.
- **Wrapper**: a small function that supplies starting values and calls the real worker.
- **Palindrome**: a sequence that reads the same forwards and backwards.
- **Iteration**: repetition using a loop.
- **Tail recursion**: recursion in which the recursive call is the last action of the function.
- **Tail-call optimisation**: a language feature that reuses the frame for a tail call; Python
  lacks it.
- **Accumulator**: an extra parameter that carries the result so far into the next call.
- **Explicit stack**: a list used last-in, first-out to hold work still to be done.
- **Cache**: a store of results already computed.
- **Memoisation**: caching a function's results by its arguments.
- **Decorator**: a line starting with `@` that wraps a function to change its behaviour.
- **Bottom-up**: solving the smallest subproblems first and building towards the answer.
- **Towers of Hanoi**: the three-peg disc puzzle; moving $n$ discs takes $2^n - 1$ moves.

## Check yourself

```quiz
[
  {"q": "Which function is tail-recursive?",
   "options": ["factorial: return n * factorial(n-1)", "binary_search: return binary_search(data, target, mid+1, high)", "linear_sum: return linear_sum(S, n-1) + S[n-1]", "bad_fibonacci"], "answer": 1,
   "explain": "Only binary search returns the recursive result directly with nothing left to do afterwards."},
  {"q": "Why does the book add low and high parameters to binary search?",
   "options": ["To make it faster than O(log n)", "So each recursive call can describe its subproblem without slicing the list", "Python requires default arguments", "To support unsorted data"], "answer": 1,
   "explain": "Indices identify the subrange in O(1); slicing would copy and make each call O(n)."},
  {"q": "Does CPython perform tail-call optimisation?",
   "options": ["Yes, always", "Only with -O", "No, deep tail recursion still raises RecursionError", "Only for lambdas"], "answer": 2,
   "explain": "CPython keeps every frame (for tracebacks), so tail recursion must be eliminated manually."},
  {"q": "To eliminate a binary (two-call) recursion like a tree traversal you typically...",
   "options": ["reassign parameters in a while loop", "maintain an explicit stack of pending subproblems", "use a for loop over range(n)", "cannot do it"], "answer": 1,
   "explain": "Parameter reassignment handles only the single tail call; multiple pending calls need a stack."},
  {"q": "What does an accumulator parameter achieve in factorial_acc(n, acc)?",
   "options": ["Memoisation", "It carries the pending multiplication forward so the recursive call becomes a tail call", "It reduces time to O(log n)", "It avoids the base case"], "answer": 1,
   "explain": "With the product passed down, nothing remains to do after the call returns."},
  {"q": "Memoising bad_fibonacci changes its running time from exponential to...",
   "options": ["O(log n)", "O(n)", "O(n^2)", "it stays exponential"], "answer": 1,
   "explain": "Each F(k) for k <= n is computed once, with O(1) work besides the (cached) calls."}
]
```
