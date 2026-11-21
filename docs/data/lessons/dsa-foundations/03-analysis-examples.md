# Analysing real code and proving it correct

> **Before this lesson:** You should know the seven growth functions and the meaning of $O$,
> $\Omega$ and $\Theta$. Those are taught in
> [Measuring algorithms and the seven functions](#/lesson/dsa-foundations/seven-functions) and
> [Big-O, Big-Omega and Big-Theta](#/lesson/dsa-foundations/asymptotic-notation). You should also
> be comfortable reading Python loops and lists.

## In plain words

The last two lessons gave you a ruler for measuring algorithms. This lesson is where you pick up
the ruler and measure things. It does two jobs. First, it reads several short Python functions
and works out, loop by loop, how their cost grows. Second, it shows the standard ways to *argue
that a claim is true*, so that "I think this works" can become "here is why this must work".

An analogy: an accountant reading a restaurant bill does not time the kitchen. They look at each
line, ask "how many of these, at what price each?", and add up. Analysing code is the same
bookkeeping. For each line you ask "how many times does this run, and what does one run cost?",
then add the lines together and keep the biggest term.

Why it matters for a job: this is the exact skill an interviewer tests after you write a
solution, when they ask for its running time and whether it can be improved. It is also how
engineers find the one innocent-looking line that makes a nightly report take six hours.

## 1. Constant-time operations in Python

Before analysing code we must know the price of its building blocks. In Python these are all
$O(1)$, meaning their cost does not depend on how much data there is:

- `len(data)`: lists, tuples and strings keep a note of their own length, so nothing is counted.
- `data[j]`: a Python list stores its items in numbered slots next to each other in memory, so
  the computer can jump straight to slot `j` (the arrays module explains the mechanism).
- Arithmetic on ordinary-sized whole numbers, comparisons such as `a < b`, and assignments such
  as `x = 5`.

## 2. Finding the maximum

```python
def find_max(data):
    biggest = data[0]          # O(1)
    for val in data:           # n iterations
        if val > biggest:      # O(1)
            biggest = val      # O(1)
    return biggest
```

Go through it as the accountant would. The first and last lines run once and cost $O(1)$ each.
The loop body runs once per item, $n$ times, and each run does a comparison and perhaps an
assignment: $O(1)$. So the total is $n \times O(1) + O(1)$, which is $O(n)$. No algorithm can do
better, because skipping even one item risks missing the largest; so the running time is
$\Theta(n)$, exactly linear.

**A subtler question:** how many times is `biggest` *replaced*? If the numbers arrive in
increasing order, every item is a new record. But suppose the order is random; such a shuffled
arrangement is called a random **permutation**. The $j$-th item is a new record only if it is the
largest of the first $j$ items, and by symmetry each of those $j$ items is equally likely to be
the largest, so the chance is $1/j$. Adding the chances for $j = 1, 2, \ldots, n$ gives the
expected (long-run average) number of records, a famous sum called the **harmonic number**:

$$H_n = 1 + \tfrac12 + \tfrac13 + \cdots + \tfrac1n = O(\log n).$$

For a million shuffled numbers that is only about 14 updates. The harmonic number is the third
sum worth recognising, after the arithmetic sum $1 + 2 + \cdots + n$ and the geometric sum
$1 + 2 + 4 + \cdots$ from the first lesson.

## 3. Prefix averages: three algorithms

Given a list $S$ of $n$ numbers, compute a list $A$ in which $A[j]$ is the average of
$S[0], \ldots, S[j]$. (Think of an investment's average yearly return over its first 1, 2, 3...
years.) The first lesson timed two solutions; here we count their steps.

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

The outer loop runs $n$ times, but the inner loop does not run a fixed number of times: when
`j` is 0 it runs once, when `j` is 1 it runs twice, and so on up to $n$ times. The line
`total += S[i]` therefore runs $1 + 2 + \cdots + n = n(n+1)/2$ times in all. That is $O(n^2)$.

### 3.2 Quadratic, hidden

```python
def prefix_average2(S):
    n = len(S)
    A = [0] * n
    for j in range(n):
        A[j] = sum(S[0:j + 1]) / (j + 1)   # slicing AND sum are both O(j)
    return A
```

It looks like a single loop, so it is tempting to call it linear. But look inside the one line.
The expression `S[0:j + 1]` is a **slice**: it builds a brand-new list containing copies of the
first $j + 1$ entries, which takes $j + 1$ steps. Then `sum(...)` walks along that new list adding
as it goes, another $j + 1$ steps. The work per iteration is proportional to $j$, exactly as in
the first version, so the total is still $O(n^2)$. **Built-in functions are not free**: each one
is a loop written by somebody else.

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

Each element is added to `total` exactly once, and nothing else in the loop depends on $j$: $O(n)$.
The idea that made the difference is to **reuse the work of the previous iteration** instead of
starting again. The sum of the first five numbers is the sum of the first four plus one more.
That idea, grown up, becomes the technique called dynamic programming later in this track.

## 4. Three-way set disjointness

Given three lists $A$, $B$, $C$, each with no repeated values inside it, decide whether the three
are **disjoint**, meaning no single value appears in all three. The function returns `True` when
they are disjoint and `False` as soon as it finds a value common to all.

```python
def disjoint1(A, B, C):
    for a in A:
        for b in B:
            for c in C:
                if a == b == c:
                    return False
    return True
```

`a == b == c` is Python shorthand for "`a` equals `b` and `b` equals `c`". Three loops are nested,
each over $n$ items, and the test sits inside all three, so in the worst case (no common value)
it runs $n \times n \times n$ times: $O(n^3)$.

One observation improves it: there is no point looking through $C$ unless `a` and `b` already
match.

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

There are still three nested loops, so a quick glance says $n^3$. Count more carefully. The test
`a == b` runs $n^2$ times, once for each pair. How often is it true? Each value `b` can equal at
most one `a`, because $A$ contains no repeats, so at most $n$ of the $n^2$ pairs match. The loop
over $C$ therefore starts at most $n$ times, and each time costs at most $n$ steps: $n \times n =
n^2$ steps in total for the innermost loop, across the whole run. Adding the $n^2$ tests gives
$O(n^2)$ overall.

The improvement came from **counting how often an inner loop can really run**, which is different
from multiplying the sizes of the loops that surround it.

## 5. Element uniqueness

Are all elements of $S$ different from one another?

```python
def unique1(S):
    for j in range(len(S)):
        for k in range(j + 1, len(S)):
            if S[j] == S[k]:
                return False
    return True
```

This compares every element with every later element. `range(j + 1, len(S))` starts the inner
loop one place after `j`, so no pair is checked twice and nothing is compared with itself. The
first element is compared with $n - 1$ others, the second with $n - 2$, and so on:
$(n-1) + (n-2) + \cdots + 1 = n(n-1)/2$ pairs, so $O(n^2)$.

A different idea: if the list were in sorted order, any two equal values would end up side by
side, and one pass comparing neighbours would find them.

```python
def unique2(S):
    temp = sorted(S)                       # O(n log n)
    for j in range(1, len(temp)):          # O(n)
        if temp[j - 1] == temp[j]:
            return False
    return True
```

`sorted(S)` returns a new list with the same items in increasing order; Python's built-in sort
costs $O(n \log n)$. The loop then compares each item with the one before it, $O(n)$. By the sum
rule the total is $O(n \log n)$, the cost of the more expensive part. (A third approach, using a
*hash set* that remembers which values have been seen, brings this down to $O(n)$ on average; the
hashing module covers it.)

The demo times both versions on lists with no repeats, which is the worst case because neither
function can stop early.

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

**Reading the demo.** `random.sample(range(10 * n), n)` picks `n` different numbers at random, so
the list has no duplicates. The clock is read before, between and after the two calls. Each time
`n` doubles, `unique1` should take about four times as long (quadratic) and `unique2` only a
little more than twice as long (n-log-n). At `n = 2000` the gap is already a factor of several
hundred.

> [!INTERVIEW]
> "Can you do better than $O(n^2)$?" is almost always answered by one of three moves: sort first
> ($O(n\log n)$), remember what you have seen in a hash set or dictionary ($O(n)$ on average), or
> keep a running total instead of recomputing it (prefix sums). Element uniqueness shows the
> first two, prefix averages the third.

## 6. A note on amortisation

Some operations are cheap most of the time and expensive once in a while. Appending to a Python
list is the standard case: now and then the list has run out of room and must copy everything to
a larger block of memory. **Amortised analysis** handles this by bounding the *total* cost of a
long sequence of operations and then dividing by the number of operations, like spreading the
cost of an annual train pass over every journey of the year. The dynamic-arrays lesson does this
carefully and proves that $n$ appends cost $O(n)$ in total, which is $O(1)$ each *on average over
the sequence*, even though one unlucky append can cost $\Theta(n)$.

## 7. Simple justification techniques

A claim such as "this algorithm is correct" or "this runs in $O(n)$" needs an argument that leaves
no gaps. Such an argument is called a **proof**. Four tools cover most needs.

### 7.1 By example (and counterexample)

To prove "there exists an $x$ with property $P$", show one. To *disprove* "every $x$ has property
$P$", show one $x$ that lacks it; that single case is a **counterexample**. For instance, the
claim "every number of the form $2^i - 1$ is prime when $i > 1$" looks plausible for a while
($3, 7, \ldots$) and is false, since $2^4 - 1 = 15 = 3 \cdot 5$. (A **prime** is a whole number
greater than 1 that only 1 and itself divide evenly.) Note the asymmetry: one example can never
*prove* a claim about every case, however many you collect.

### 7.2 The "contra" attack

Two techniques prove a statement by attacking its opposite.

- **Contrapositive.** The statement "if $p$ then $q$" says exactly the same thing as "if not $q$
  then not $p$". ("If it is raining, the street is wet" matches "if the street is dry, it is not
  raining".) Sometimes the second form is easier. Example: *whenever a product $ab$ is even, at
  least one of $a$, $b$ is even.* The contrapositive is: if $a$ and $b$ are both odd then $ab$ is
  odd. An odd number is one more than an even number, so write $a = 2j+1$ and $b = 2k+1$; then
  $ab = 4jk + 2j + 2k + 1 = 2(2jk + j + k) + 1$, which is odd. Done.
- **De Morgan's laws** tell you how to negate "and" and "or": not ($p$ or $q$) is the same as
  (not $p$) and (not $q$). That is how "not (a even or b even)" became "a odd and b odd" above.
- **Contradiction.** Assume the statement is false and derive something impossible. Example: *if
  $ab$ is odd then $a$ and $b$ are both odd.* Suppose not, so at least one of them, say $a$, is
  even: $a = 2j$. Then $ab = 2(jb)$ is even, which clashes with $ab$ being odd. The assumption
  must have been wrong.

### 7.3 Induction

Induction proves that a statement $q(n)$ holds for every whole number $n \ge 1$ in two moves,
like knocking over a row of dominoes. Show that the first domino falls: the **base case** $q(1)$.
Then show that each domino knocks over the next: the **inductive step**, in which you assume the
statement for all values smaller than $n$ (the *inductive hypothesis*) and use that to prove it
for $n$. Together they cover every $n$.

**Example.** Claim: $\sum_{i=1}^n i = n(n+1)/2$. Base case: for $n = 1$ the left side is 1 and
the right side is $1 \cdot 2 / 2 = 1$. Step: split off the last term and apply the hypothesis to
the rest,
$\sum_{i=1}^{n} i = n + \sum_{i=1}^{n-1} i = n + \frac{(n-1)n}{2} = \frac{2n + n^2 - n}{2} = \frac{n(n+1)}{2}$.

**A second example (two base cases).** Define $G(1) = 1$, $G(2) = 3$ and, from then on, each term
as the sum of the previous two: $1, 3, 4, 7, 11, 18, \ldots$ Claim: $G(n) < 2^n$ for every
$n \ge 1$. Base cases: $1 < 2$ and $3 < 4$. Step: for $n > 2$,
$G(n) = G(n-1) + G(n-2) < 2^{n-1} + 2^{n-2} < 2^{n-1} + 2^{n-1} = 2^n$. Two base cases are needed
because the step reaches back two values; checking only $G(1)$ would leave $G(2)$ — and therefore
everything after it — unsupported.

**A cautionary "proof".** Here is a tempting but bogus induction claiming that the same sequence
grows only linearly, i.e. is $O(n)$: "by the hypothesis the two earlier terms are each linear, and
a sum of two linear quantities is linear." The flaw is that big-O hides a constant, and this
argument silently lets that constant grow at every step — after $n$ steps it is no longer a
constant at all. Never induct on a statement containing big-O; induct on an explicit inequality
with a fixed constant instead.

### 7.4 Loop invariants

A **loop invariant** is a statement about the program's variables that is true every time the
loop comes round to its top. It is induction applied to a loop, and it is the standard way to
prove a loop correct. You must show three things about your chosen statement $L$:

1. **Initialisation:** $L$ holds before the first iteration;
2. **Maintenance:** if $L$ holds before an iteration, it still holds after that iteration;
3. **Termination:** when the loop stops, $L$ combined with the reason for stopping gives the
   result you wanted.

**Example: linear search**, which returns the position of `val` in `S`, or `-1` if it is absent:

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

Invariant $L_j$: *none of $S[0], \ldots, S[j-1]$ equals `val`.*

- *Initialisation.* At the start $j = 0$, so the statement talks about no elements at all and is
  true automatically. (Mathematicians call a claim about an empty collection *vacuously* true.)
- *Maintenance.* If an iteration does not return, then $S[j] \ne$ `val`. Together with $L_j$,
  that gives $L_{j+1}$, and `j += 1` makes the names line up again.
- *Termination.* If the loop ends because $j = n$, then $L_n$ says `val` is nowhere in $S$, so
  returning $-1$ is correct. If it ends early, it returned a `j` with `S[j] == val`, also correct.

Python can check an invariant for you while the program runs. An `assert` statement stops the
program with an error if the condition after it is false, and does nothing otherwise:

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

The output is `[10.0, 15.0, 20.0, 25.0]` and no assertion fires, so the invariant "`total` equals
the sum of the first `j` items" held at the top of every iteration. Change `total += S[j]` to
`total += S[j] + 1` and run it again: the assertion fails on the second iteration and points
straight at the bug. (The check itself costs $O(j)$, so remove such assertions from finished
code.) Writing invariants as assertions while developing is a cheap and effective habit.

## 8. Loops that are not what they seem

Most analysis mistakes come from the reflex "a loop inside a loop is $n^2$". The number of times
an inner loop runs often depends on the outer loop's variable, and then the total has to be
**added up** term by term; multiplying the two loop sizes gives the wrong answer. Four shapes
are worth studying. In the code, `j *= 2` doubles `j`, `range(0, n, i)` counts from 0 up to `n`
in steps of `i`, and `pass` is a placeholder statement that does nothing.

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

Each `count_` function mirrors one shape and counts how many times its innermost statement runs.
The columns `n log2 n` and `n ln n` are formulas to compare against (`ln` is the *natural*
logarithm, which differs from $\log_2$ only by a constant factor). Multiply $n$ by 10 and columns
A and B grow by a little more than 10 (the extra logarithmic factor), while C and D grow by about
10: linear.

**The method, in two sentences.** Write the cost of the inner loop as a formula in the outer
loop's variable, then add that formula up over the outer loop's range, using the arithmetic,
geometric or harmonic sum as appropriate. Or find a quantity that only ever increases, and bound
how far it can go.

## 9. Pitfalls

- **Multiplying loop sizes without thinking.** `disjoint2` has three nested loops and is still
  $O(n^2)$; shape C has two and is $O(n)$.
- **Forgetting the cost of built-ins.** Slicing, `sum`, `in` on a list, `sorted`, and joining
  strings with `+` inside a loop all contain loops of their own.
- **Induction with too few base cases.** If the step reaches back two values, two base cases are
  needed.
- **Invariants that are true but too weak.** "`j` is not negative" holds throughout linear
  search and proves nothing. The invariant has to be strong enough that, at the end, it gives
  you the result.
- **Confusing evidence with proof.** A hundred passing tests show that those hundred inputs
  work. Only an argument covers the inputs you did not try.

## 10. Summary

| Algorithm | Running time |
|---|---|
| `find_max` | $\Theta(n)$ |
| `prefix_average1`, `prefix_average2` | $\Theta(n^2)$ |
| `prefix_average3` | $\Theta(n)$ |
| `disjoint1` / `disjoint2` | $O(n^3)$ / $O(n^2)$ |
| `unique1` / `unique2` | $O(n^2)$ / $O(n\log n)$ |

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 3.3.3–3.4.

## Glossary

- **Slice**: an expression such as `S[a:b]` that copies part of a list into a new list.
- **Permutation**: one particular ordering of a collection of items.
- **Harmonic number $H_n$**: the sum $1 + 1/2 + \cdots + 1/n$, which grows like $\log n$.
- **Disjoint**: having no element in common.
- **Amortised cost**: the average cost per operation over a long sequence of operations.
- **Proof**: an argument that establishes a claim for every case, leaving no gaps.
- **Counterexample**: a single case that shows a general claim is false.
- **Contrapositive**: the equivalent form "if not $q$ then not $p$" of "if $p$ then $q$".
- **Proof by contradiction**: assuming a claim is false and deriving an impossibility.
- **Induction**: proving a base case and a step from smaller cases to the next one.
- **Loop invariant**: a statement that is true at the start of every iteration of a loop.
- **Assertion**: a check (`assert`) that halts the program if a condition is false.

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
