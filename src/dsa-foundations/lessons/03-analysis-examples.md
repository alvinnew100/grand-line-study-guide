# Analysing real code and proving it correct

With the notation in hand we can analyse real algorithms. This lesson works through the book's
running examples — finding a maximum, prefix averages, three-way set disjointness and element
uniqueness — and then covers the justification techniques you need to *prove* claims about
algorithms: counterexamples, contrapositive and contradiction, induction, and loop invariants.

## 1. Constant-time operations in Python

Before analysing code we must know the cost of its building blocks:

- `len(data)` is $O(1)$ — lists, tuples and strings store their length.
- `data[j]` is $O(1)$ — Python lists are arrays of references, so element $j$ is at a computable
  address (the arrays module explains why).
- Arithmetic on small ints, comparisons, assignments: $O(1)$.

## 2. Finding the maximum

```python
def find_max(data):
    biggest = data[0]          # O(1)
    for val in data:           # n iterations
        if val > biggest:      # O(1)
            biggest = val      # O(1)
    return biggest
```

The loop runs $n$ times with constant work, so the running time is $O(n)$ — and since every element
must be inspected, $\Theta(n)$.

**A subtler question:** how many times is `biggest` *updated*? In the worst case (increasing
input), $n$ times. But if the input is a random permutation, element $j$ is the largest of the first
$j$ with probability $1/j$, so the expected number of updates is the **harmonic number**

$$H_n = 1 + \tfrac12 + \tfrac13 + \cdots + \tfrac1n = O(\log n).$$

## 3. Prefix averages — three algorithms

Given $S$ of $n$ numbers, compute $A$ where $A[j]$ is the average of $S[0], \ldots, S[j]$. (Think of
a fund's average annual return over the last 1, 2, 3... years.)

### 3.1 Quadratic, explicit

```python
def prefix_average1(S):
    n = len(S)
    A = [0] * n                    # O(n)
    for j in range(n):
        total = 0
        for i in range(j + 1):     # j + 1 iterations
            total += S[i]
        A[j] = total / (j + 1)
    return A
```

The inner body runs $1 + 2 + \cdots + n = n(n+1)/2$ times: $O(n^2)$.

### 3.2 Quadratic, hidden

```python
def prefix_average2(S):
    n = len(S)
    A = [0] * n
    for j in range(n):
        A[j] = sum(S[0:j + 1]) / (j + 1)   # slicing AND sum are both O(j)
    return A
```

It looks like a single loop, but `S[0:j+1]` builds a new list of $j+1$ items and `sum` walks it.
Still $O(n^2)$. **Built-ins are not free.**

### 3.3 Linear

```python
def prefix_average3(S):
    n = len(S)
    A = [0] * n
    total = 0
    for j in range(n):
        total += S[j]              # running sum
        A[j] = total / (j + 1)
    return A
```

Each element is added once: $O(n)$. The key idea — **reuse work from the previous iteration** — is
the seed of dynamic programming.

## 4. Three-way set disjointness

Given three sequences $A$, $B$, $C$ (no duplicates inside each), decide whether some element is in
all three.

```python
def disjoint1(A, B, C):
    for a in A:
        for b in B:
            for c in C:
                if a == b == c:
                    return False
    return True
```

$O(n^3)$ if each has size $n$. Improvement: there is no point looping over $C$ unless $a = b$.

```python
def disjoint2(A, B, C):
    for a in A:
        for b in B:
            if a == b:             # only then look at C
                for c in C:
                    if a == c:
                        return False
    return True
```

The test `a == b` runs $n^2$ times. Because $A$ has no duplicates, at most $n$ pairs $(a, b)$ are
equal, so the innermost loop runs at most $n$ times, costing $O(n^2)$ in total. Overall
$O(n^2)$ — a real improvement that comes from **counting how often an inner loop can actually
execute**, not just multiplying loop bounds.

## 5. Element uniqueness

Are all elements of $S$ distinct?

```python
def unique1(S):
    for j in range(len(S)):
        for k in range(j + 1, len(S)):
            if S[j] == S[k]:
                return False
    return True
```

Pairs examined: $(n-1) + (n-2) + \cdots + 1 = n(n-1)/2$, so $O(n^2)$.

```python
def unique2(S):
    temp = sorted(S)                       # O(n log n)
    for j in range(1, len(temp)):          # O(n)
        if temp[j - 1] == temp[j]:
            return False
    return True
```

After sorting, duplicates are adjacent. Total $O(n \log n)$. (With a hash set it is $O(n)$
expected — see the hashing module.)

```python-run
import random, time
def unique1(S):
    for j in range(len(S)):
        for k in range(j + 1, len(S)):
            if S[j] == S[k]:
                return False
    return True
def unique2(S):
    temp = sorted(S)
    for j in range(1, len(temp)):
        if temp[j - 1] == temp[j]:
            return False
    return True
for n in [500, 1000, 2000]:
    S = random.sample(range(10 * n), n)         # all distinct: worst case
    t0 = time.perf_counter(); unique1(S); t1 = time.perf_counter(); unique2(S); t2 = time.perf_counter()
    print(f"n={n}: unique1 {1000*(t1-t0):7.1f} ms   unique2 {1000*(t2-t1):5.2f} ms")
```

> [!INTERVIEW]
> "Can you do better than $O(n^2)$?" is almost always answered by one of: sort first
> ($O(n\log n)$), hash ($O(n)$ expected), or keep a running aggregate (prefix sums). Element
> uniqueness is the archetype.

## 6. A note on amortisation

Some operations are usually cheap but occasionally expensive — appending to a Python list sometimes
triggers a resize that copies everything. **Amortised analysis** bounds the *total* cost of a
sequence of operations and divides by the number of operations. We do this carefully in the
dynamic-arrays lesson, where we prove that $n$ appends cost $O(n)$ total, i.e. $O(1)$ amortised each,
even though a single append can cost $\Theta(n)$.

## 7. Simple justification techniques

Claims like "this algorithm is correct" or "this runs in $O(n)$" need proofs. Four tools cover most
needs.

### 7.1 By example (and counterexample)

To prove "there exists an $x$ with property $P$", exhibit one. To *disprove* "every $x$ has $P$",
exhibit one counterexample. Example from the book: the claim "every number of the form $2^i - 1$ is
prime when $i > 1$" is false, since $2^4 - 1 = 15 = 3 \cdot 5$.

### 7.2 The "contra" attack

- **Contrapositive.** To prove "if $p$ then $q$", prove "if not $q$ then not $p$". Example: if $ab$
  is even then $a$ is even or $b$ is even. Contrapositive: if $a$ and $b$ are both odd, then
  $a = 2j+1$, $b = 2k+1$ and $ab = 4jk + 2j + 2k + 1$ is odd. Done.
- **De Morgan's laws** help form negations: not ($p$ or $q$) = (not $p$) and (not $q$).
- **Contradiction.** Assume the statement is false and derive something absurd. Example: if $ab$ is
  odd then $a$ and $b$ are both odd. Suppose not — say $a = 2j$ is even. Then $ab = 2(jb)$ is even,
  contradicting the assumption.

### 7.3 Induction

To prove $q(n)$ for all $n \ge 1$: show the **base case** $q(1)$ (perhaps a few base cases), then the
**inductive step**: assuming $q(j)$ for all $j < n$, show $q(n)$.

**Example.** $\sum_{i=1}^n i = n(n+1)/2$. Base: $n = 1$ gives $1 = 1 \cdot 2 / 2$. Step:
$\sum_{i=1}^{n} i = n + \sum_{i=1}^{n-1} i = n + \frac{(n-1)n}{2} = \frac{n(n+1)}{2}$.

**A second example (two base cases).** With $F(1) = 1$, $F(2) = 2$ and $F(n) = F(n-2) + F(n-1)$,
the book proves $F(n) < 2^n$. Base cases: $1 < 2$ and $2 < 4$. Step: for $n > 2$,
$F(n) = F(n-2) + F(n-1) < 2^{n-2} + 2^{n-1} < 2^{n-1} + 2^{n-1} = 2^n$. Two base cases are needed
because the step reaches back two values.

**A cautionary "proof".** An exercise in the book offers a bogus induction that $F(n)$ is $O(n)$:
"$F(n-2)$ is $O(n-2)$ and $F(n-1)$ is $O(n-1)$, so their sum is $O(n)$." The flaw is that big-O
hides a constant, and the induction silently lets that constant grow at every step — after $n$
steps it is no longer a constant at all. Never induct on a statement containing big-O; induct on
an explicit inequality with a fixed constant instead.

### 7.4 Loop invariants

To prove a loop correct, state a property $L$ that:

1. **Initialisation:** holds before the loop starts;
2. **Maintenance:** if it holds before an iteration, it holds after it;
3. **Termination:** when the loop ends, $L$ together with the exit condition implies the desired
   result.

**Example** — linear search:

```python
def find(S, val):
    n = len(S)
    j = 0
    while j < n:
        if S[j] == val:
            return j
        j += 1
    return -1
```

Invariant $L_j$: *`val` is not equal to any of the first $j$ elements of $S$.* Initially $j = 0$ and
the claim is vacuous. If the iteration does not return, $S[j] \ne$ `val`, so $L_{j+1}$ holds. If the
loop ends with $j = n$, $L_n$ says `val` is nowhere in $S$, so returning $-1$ is correct.

```python-run
# Check a loop invariant mechanically with assertions
def prefix_average3(S):
    A, total = [0] * len(S), 0
    for j in range(len(S)):
        # invariant: total == sum(S[0:j]) at the top of the loop
        assert total == sum(S[:j])
        total += S[j]
        A[j] = total / (j + 1)
    return A
print(prefix_average3([10, 20, 30, 40]))
```

Asserting invariants while developing is a cheap, powerful debugging habit.

## 8. Loops that are not what they seem

Most analysis mistakes come from assuming "a loop inside a loop is $n^2$". The inner loop's bound
often depends on the outer variable, and the total must be **summed**, not multiplied. Four
instructive shapes:

```python
def shape_a(n):                 # inner loop doubles
    for i in range(n):
        j = 1
        while j < n:
            j *= 2

def shape_b(n):                 # inner loop runs about n / i times
    for i in range(1, n + 1):
        for j in range(0, n, i):
            pass

def shape_c(n):                 # outer loop doubles, inner runs i times
    i = 1
    while i < n:
        for j in range(i):
            pass
        i *= 2

def shape_d(n):                 # two pointers that only move forward
    j = 0
    for i in range(n):
        while j < n and j < 2 * i:
            j += 1
```

- **Shape A:** the inner loop runs $\lceil \log_2 n \rceil$ times for *every* $i$:
  $n \log n$ in total.
- **Shape B:** the inner loop runs about $n/i$ times, so the total is
  $n(1 + \tfrac12 + \tfrac13 + \cdots + \tfrac1n) = n H_n = \Theta(n\log n)$ — the harmonic number
  again. This is the cost of any "visit every multiple of $i$" computation, such as a prime sieve.
- **Shape C:** the inner loop runs $1 + 2 + 4 + \cdots < 2n$ times in total — a geometric series —
  so the whole thing is $\Theta(n)$ despite the nesting.
- **Shape D:** the inner `while` can run several times for one value of $i$, but $j$ never decreases
  and never exceeds $n$, so across the **entire** execution it runs at most $n$ times:
  $\Theta(n)$. This "the pointer only moves forward" argument is the basis of two-pointer and
  sliding-window algorithms, and is an amortised argument in miniature.

```python-run
import math
def count_a(n):
    c = 0
    for i in range(n):
        j = 1
        while j < n: j *= 2; c += 1
    return c
def count_b(n):
    return sum(len(range(0, n, i)) for i in range(1, n + 1))
def count_c(n):
    c, i = 0, 1
    while i < n: c += i; i *= 2
    return c
def count_d(n):
    c, j = 0, 0
    for i in range(n):
        while j < n and j < 2 * i: j += 1; c += 1
    return c
print(f"{'n':>7} {'A':>9} {'n log2 n':>9} {'B':>9} {'n ln n':>9} {'C':>7} {'D':>7}")
for n in [1000, 10000, 100000]:
    print(f"{n:>7} {count_a(n):>9} {int(n*math.log2(n)):>9} {count_b(n):>9} {int(n*math.log(n)):>9} {count_c(n):>7} {count_d(n):>7}")
```

Multiply $n$ by 10 and columns A and B grow by a little more than 10 (the extra logarithmic
factor), while C and D grow by about 10: linear. **Method:** write the cost of the inner loop as a
function of the outer variable, then sum that function over the outer loop's range — using the
arithmetic, geometric or harmonic sum as appropriate — or find a quantity that only ever increases
and bound it.

## 9. Pitfalls

- Multiplying loop bounds blindly: `disjoint2` has three nested loops but is $O(n^2)$.
- Forgetting the cost of slicing, `sum`, `in`, `sorted`, string `+` in loops.
- Induction with too few base cases.
- Loop invariants that are true but too weak to imply the result at termination.

## 10. Summary

| Algorithm | Running time |
|---|---|
| `find_max` | $\Theta(n)$ |
| `prefix_average1`, `prefix_average2` | $\Theta(n^2)$ |
| `prefix_average3` | $\Theta(n)$ |
| `disjoint1` / `disjoint2` | $O(n^3)$ / $O(n^2)$ |
| `unique1` / `unique2` | $O(n^2)$ / $O(n\log n)$ |

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 3.3.3–3.4.

## Check yourself

```quiz
[
  {"q": "Why is prefix_average2 quadratic even though it has a single explicit loop?",
   "options": ["Division is O(n)", "The slice S[0:j+1] and sum() each take O(j) time", "range() is O(n) per iteration", "Lists are linked lists"], "answer": 1,
   "explain": "Slicing copies j+1 references and sum walks them, so iteration j costs O(j); total 1+2+...+n."},
  {"q": "In disjoint2, why does the innermost loop over C run at most n times in total?",
   "options": ["Because C is sorted", "Because a == b can be true for at most n pairs, as A has no duplicates", "Because of early return", "It actually runs n^2 times"], "answer": 1,
   "explain": "Each b equals at most one a (and vice versa), so at most n equal pairs reach the C loop, giving O(n^2) total."},
  {"q": "Expected number of times find_max updates `biggest` on a random permutation?",
   "options": ["n/2", "O(log n), the harmonic number", "1", "n"], "answer": 1,
   "explain": "Element j is a new maximum with probability 1/j, so the expectation is H_n = 1 + 1/2 + ... + 1/n = O(log n)."},
  {"q": "unique2 sorts first. Its running time is dominated by...",
   "options": ["the linear scan", "sorting, O(n log n)", "creating the copy, O(n^2)", "nothing; it is O(1)"], "answer": 1,
   "explain": "sorted() is O(n log n); the adjacent-pair scan is O(n)."},
  {"q": "To prove 'if ab is even then a or b is even' via contrapositive you prove...",
   "options": ["if a or b is even then ab is even", "if a and b are both odd then ab is odd", "if ab is odd then a is odd", "ab is even for all a, b"], "answer": 1,
   "explain": "The contrapositive of p => q is not q => not p; 'not (a even or b even)' is 'a odd and b odd' by De Morgan."},
  {"q": "Which three properties must a loop invariant argument establish?",
   "options": ["Base, step, conclusion of induction on n", "Initialisation, maintenance, termination", "Existence, uniqueness, minimality", "Upper bound, lower bound, tight bound"], "answer": 1,
   "explain": "The invariant holds initially, is preserved by each iteration, and at exit implies correctness."},
  {"q": "The bogus induction 'F(n-2) is O(n-2) and F(n-1) is O(n-1), so F(n) is O(n)' fails because...",
   "options": ["Fibonacci numbers are not integers", "The hidden big-O constant is allowed to grow at every inductive step", "Induction cannot be used on sequences", "It has too many base cases"], "answer": 1,
   "explain": "Big-O needs one fixed constant c for all n. Inducting on 'is O(...)' lets c double each step, which is how an exponential function 'becomes' O(n)."}
]
```
