# Designing recursion and eliminating it

The previous lessons showed what recursion looks like and how to analyse it. This lesson is about
*writing* recursive algorithms deliberately — the design recipe, the trick of parameterising a
recursion — and then about removing recursion when it costs too much: eliminating tail recursion
and simulating the call stack by hand.

## 1. A design recipe

Goodrich et al. summarise recursive design as two activities:

1. **Test for base cases.** Begin by testing for a set of base cases (there should be at least
   one). Every possible chain of recursive calls must eventually reach a base case, and each base
   case must be handled without recursion.
2. **Recur.** If not a base case, perform one or more recursive calls. Each call should make
   progress towards a base case.

A practical way to find the recursion: ask *"if someone handed me the answer for a smaller version
of this problem, how would I finish the job?"*

| Problem | Smaller version | Finishing step |
|---|---|---|
| sum of `S[0:n]` | sum of `S[0:n-1]` | add `S[n-1]` |
| reverse `S[i:j]` | reverse `S[i+1:j-1]` | swap `S[i]`, `S[j-1]` |
| is `S[i:j]` a palindrome | is `S[i+1:j-1]` | compare the ends |
| height of a tree | height of each subtree | 1 + max |
| sorted merge of halves | sort each half | merge |

### 1.1 Parameterising a recursion

Often the natural signature is not recursive-friendly. `binary_search(data, target)` is the public
interface users want, but each recursive call needs to know the *current range*. The solution is to
add parameters — `low` and `high` — and provide a clean public wrapper:

```python
def binary_search(data, target):
    return _bsearch(data, target, 0, len(data) - 1)

def _bsearch(data, target, low, high):
    ...
```

Passing indices rather than slices is not only cleaner — slicing costs $O(n)$ per call, which would
make binary search linear and `linear_sum` quadratic. The same trick returns *extra information*
(as in `good_fibonacci`, which returns two values instead of one).

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

## 2. Recursion versus iteration

Recursion's cost is the call stack: each pending activation stores its state. For a linear recursion
of depth $n$, that is $O(n)$ memory and a risk of `RecursionError`. Any recursive algorithm *can* be
made non-recursive by maintaining your own stack of pending subproblems; for some recursions it is
even simpler.

### 2.1 Tail recursion

A recursion is a **tail recursion** if every recursive call is the *very last* thing the function
does, and its return value (if any) is immediately returned. Then nothing remains to be done in the
caller after the call — so there is no need to keep the caller's frame. Such a recursion can be
turned into a loop that **reassigns the parameters** and jumps back to the top.

`binary_search` and `reverse` are tail-recursive. `factorial` is **not**: after
`factorial(n - 1)` returns, the caller still multiplies by `n`. Similarly `linear_sum` adds after
the call returns.

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

> [!NOTE]
> Some languages (Scheme, and optionally C compilers) perform tail-call optimisation automatically.
> CPython deliberately does not — Guido van Rossum preferred complete tracebacks — so in Python you
> must eliminate tail recursion yourself when depth matters.

### 2.2 Accumulators: making a recursion tail-recursive

A non-tail recursion can often be converted by passing the pending work along as an extra
**accumulator** parameter:

```python
def factorial_acc(n, acc=1):
    if n == 0:
        return acc
    return factorial_acc(n - 1, acc * n)   # tail call: nothing left to do afterwards
```

and then eliminated:

```python
def factorial_iter(n):
    acc = 1
    while n > 0:
        n, acc = n - 1, acc * n
    return acc
```

### 2.3 Simulating the stack explicitly

When there are several recursive calls (binary or multiple recursion), simple parameter
reassignment is not enough. Keep an explicit stack of pending work instead. Here is the
disk-usage-style traversal without recursion:

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

When the work after the recursive calls matters (postorder, e.g. printing a directory's total only
after its children are done), push a marker such as `(node, "after")` so the "return" step is
simulated too.

## 3. Memoisation: keeping recursion, losing the waste

If the problem with a recursion is *repeated subproblems* rather than depth, cache results. Python
makes it a one-liner:

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

Memoising turns $\Theta(\phi^n)$ into $O(n)$; the bottom-up version uses $O(1)$ space. This is the
pattern that the dynamic-programming lesson in the text-processing module builds on.

## 4. When should you use recursion?

**Prefer recursion when:**

- the data is recursive (trees, nested lists, file systems, expression grammars);
- the algorithm is divide-and-conquer (merge-sort, quick-sort, binary search);
- you are exploring a search space (backtracking).

**Prefer iteration when:**

- the recursion is linear with large depth (Python's limit, memory);
- the recursion is tail-recursive (the loop is just as clear);
- the recursion has overlapping subproblems and a bottom-up table is natural.

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
$O(n)$ auxiliary space: the explicit stack simply *is* the call stack, written out. That is the
general truth about recursion elimination — it buys freedom from Python's recursion limit and from
call overhead, not asymptotic savings. Here, with depth only $n$ for a $2^n$-step computation, the
recursive version is the right engineering choice.

## 7. Pitfalls

- Believing Python will optimise tail calls. It will not.
- Converting a non-tail recursion by "just using a loop" and losing the post-call work.
- Using a mutable default argument as an accumulator (`def f(x, acc=[])`) — it is shared across
  calls. Use `None` and initialise inside.
- Memoising a function whose arguments are unhashable (lists) — convert to tuples first.

## 8. Summary

- Design: base cases first, then recursive calls that make progress; parameterise with indices and
  wrap in a clean public function.
- Tail recursions become loops by reassigning parameters; others need an explicit stack.
- Overlapping subproblems → memoise or go bottom-up.

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 4.5–4.6.

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
