# Measuring algorithms and the seven functions

Every data structure in this track will come with a price tag: "this operation costs $O(1)$", "that
one costs $O(\log n)$". Before we can read those price tags we need to agree on *what* we are
measuring and *how*. This lesson starts with the honest, empirical approach — timing code — shows
why it is not enough, and then introduces the small family of functions that describe almost every
running time you will meet.

## 1. Why analyse at all?

A data structure is a systematic way of organising data; an algorithm is a step-by-step procedure
for a task in finite time. We judge both mainly on two resources:

- **running time** — how long it takes, and
- **space** — how much memory it needs.

Running time almost always grows with the input size $n$, and the *shape* of that growth matters far
more than the constant in front. An algorithm that is twice as slow on a laptop as on a server is
the same algorithm; one whose time quadruples whenever the input doubles is a fundamentally
different beast from one whose time merely doubles.

## 2. Experimental studies

The most direct way to learn how fast an algorithm is: implement it, run it on inputs of various
sizes, and record the elapsed time. In Python you can use `time.time()` or, for better resolution,
`time.perf_counter()`; the `timeit` module repeats a measurement to average out noise.

```python-run
import time

def prefix_average_quadratic(S):
    n = len(S)
    A = [0] * n
    for j in range(n):
        total = 0
        for i in range(j + 1):      # re-add S[0..j] every time
            total += S[i]
        A[j] = total / (j + 1)
    return A

def prefix_average_linear(S):
    n = len(S)
    A = [0] * n
    total = 0
    for j in range(n):
        total += S[j]                # keep a running sum
        A[j] = total / (j + 1)
    return A

for n in [500, 1000, 2000, 4000]:
    data = list(range(n))
    t0 = time.perf_counter(); prefix_average_quadratic(data); t1 = time.perf_counter()
    prefix_average_linear(data); t2 = time.perf_counter()
    print(f"n={n:5d}  quadratic {1000*(t1-t0):8.2f} ms   linear {1000*(t2-t1):6.3f} ms")
```

Run it and look at the ratios: each time $n$ doubles, the quadratic version takes roughly **four**
times as long, while the linear version takes roughly **twice** as long. That ratio is the
fingerprint of the growth rate. Plotting time against $n$ on a log–log chart makes it vivid: a
polynomial $n^c$ becomes a straight line whose slope is $c$.

### 2.1 The limits of experiments

Goodrich et al. list three drawbacks of purely experimental analysis:

1. **Hardware and software must be identical** to compare two algorithms fairly — same machine,
   same interpreter, same background load.
2. **Only a limited set of inputs** can be tested; important inputs (the pathological ones) might
   be missed.
3. **The algorithm must be fully implemented** before you learn anything — expensive if it turns out
   to be a bad idea.

We want an approach that works directly on a high-level description of the algorithm, accounts for
*all* inputs, and is independent of the hardware.

## 3. Counting primitive operations

The trick is to count **primitive operations** — low-level steps whose cost is bounded by a
constant on any reasonable machine:

- assigning an identifier to an object,
- evaluating an arithmetic operation or a comparison,
- accessing a list element by index,
- calling a function or returning from one,
- following an object reference.

If an algorithm executes $t$ primitive operations, its running time is proportional to $t$ on any
machine. We then express $t$ as a function $f(n)$ of the input size.

### Worst case, average case, best case

For a fixed $n$ different inputs can take different numbers of steps. The **average case** is
attractive but requires a probability distribution over inputs, which is often unknowable and makes
the mathematics hard. The **worst case** is easier and, more importantly, *guarantees* behaviour:
an algorithm that is good in the worst case is good on every input. Unless stated otherwise, every
running time in this track is a worst-case bound.

> [!TIP]
> Designing for the worst case pushes you towards robust algorithms. "Usually fast" is a weaker
> promise than "always fast", and adversarial inputs (e.g. crafted hash collisions) do happen.

## 4. The seven functions

Remarkably, almost all analyses in the book use just seven functions. Learn their shapes and you can
read any complexity table.

| # | Function | Name | Typical source |
|---|---|---|---|
| 1 | $f(n) = c$ | constant | one arithmetic step, indexing a list |
| 2 | $f(n) = \log_2 n$ | logarithmic | repeatedly halving the problem (binary search) |
| 3 | $f(n) = n$ | linear | one pass over the input |
| 4 | $f(n) = n \log n$ | n-log-n | divide-and-conquer sorting |
| 5 | $f(n) = n^2$ | quadratic | nested loops over the input |
| 6 | $f(n) = n^3$ (and $n^d$) | cubic / polynomial | triple loops, naive matrix multiply |
| 7 | $f(n) = b^n$ | exponential | trying every subset |

### 4.1 The constant function

$f(n) = c$ does not care about $n$ at all. The most important constant is $g(n) = 1$; any other
constant is $c \cdot g(n)$. Adding two numbers, assigning a variable, or reading `A[i]` from a Python
list are constant time.

### 4.2 The logarithm

$\log_b n = x$ exactly when $b^x = n$. In computer science the default base is 2, so we write
$\log n$ for $\log_2 n$. An informal but extremely useful reading: $\lceil \log n \rceil$ is the
number of times you can divide $n$ by 2 before you reach a number $\le 1$. For $n = 1{,}000{,}000$
that is only 20.

Rules you will use constantly (for $a, b, c > 0$, $b \ne 1$):

1. $\log_b(ac) = \log_b a + \log_b c$
2. $\log_b(a/c) = \log_b a - \log_b c$
3. $\log_b(a^c) = c \log_b a$
4. $\log_b a = \log_d a / \log_d b$ (change of base)
5. $b^{\log_d a} = a^{\log_d b}$

Rule 4 is why the base never matters inside big-O: $\log_{10} n = \log_2 n / \log_2 10$, which is
just a constant times $\log_2 n$.

### 4.3 The linear function

$f(n) = n$ is what you pay to look at each of $n$ items once — reading input, comparing a value
against every element. It is the best you can hope for when *every* input element must be examined.

### 4.4 The n-log-n function

$f(n) = n \log n$ grows a little faster than linear and much slower than quadratic. The fastest
general comparison-based sorting algorithms (merge-sort, heap-sort) run in this time, and we will
prove in the sorting module that you cannot do better by comparisons alone.

### 4.5 The quadratic function

$f(n) = n^2$ appears whenever there is a loop nested inside another loop, each running about $n$
times. A subtle and very common case is a nested loop whose inner loop runs $1, 2, 3, \ldots, n$
times. The total is

$$1 + 2 + 3 + \cdots + n = \frac{n(n+1)}{2},$$

a fact the young Gauss is said to have found by pairing the first and last terms. That is still
quadratic — only about half of $n^2$, but the constant factor does not change the growth rate.

### 4.6 The cubic function and other polynomials

$f(n) = n^3$ appears less often (naive matrix multiplication, some triple loops). More generally a
**polynomial** is $f(n) = a_0 + a_1 n + a_2 n^2 + \cdots + a_d n^d$ with $a_d \ne 0$; $d$ is its
degree. The constant, linear, quadratic and cubic functions are polynomials of degree 0–3.

A **summation** $\sum_{i=a}^{b} f(i)$ is the sum $f(a) + f(a+1) + \cdots + f(b)$; loops in code
translate naturally into summations, which is why they appear throughout the analysis.

### 4.7 The exponential function

$f(n) = b^n$ with base $b > 1$ (usually $b = 2$). If a loop doubles its work every iteration, the
work after $n$ iterations is $2^n$. Exponent rules: $(b^a)^c = b^{ac}$, $b^a b^c = b^{a+c}$, and
$b^a / b^c = b^{a-c}$. The **geometric sum** is the other summation you must know:

$$\sum_{i=0}^{n} a^i = 1 + a + a^2 + \cdots + a^n = \frac{a^{n+1} - 1}{a - 1} \quad (a > 0, a \ne 1).$$

The special case $1 + 2 + 4 + \cdots + 2^{n-1} = 2^n - 1$ is the largest integer you can write in
$n$ bits, and it will reappear when we analyse dynamic arrays: doubling a capacity repeatedly costs,
in total, less than twice the final capacity.

## 5. Comparing growth rates

Ordered from slowest-growing to fastest:

$$1 \;<\; \log n \;<\; n \;<\; n \log n \;<\; n^2 \;<\; n^3 \;<\; 2^n$$

Use the interactive plot to feel how quickly these separate. Try toggling the curves and zooming the
$n$ axis.

<div class="widget" data-widget="bigo"></div>

Some concrete numbers make the point sharper:

| $n$ | $\log n$ | $n$ | $n \log n$ | $n^2$ | $n^3$ | $2^n$ |
|---|---|---|---|---|---|---|
| 8 | 3 | 8 | 24 | 64 | 512 | 256 |
| 64 | 6 | 64 | 384 | 4,096 | 262,144 | $1.8 \times 10^{19}$ |
| 1,024 | 10 | 1,024 | 10,240 | 1,048,576 | $1.1 \times 10^{9}$ | $1.8 \times 10^{308}$ |

If one operation takes a microsecond, $2^{64}$ operations take about 585,000 years. Exponential
algorithms are only usable for tiny inputs.

```python-run
import math
funcs = [("1", lambda n: 1), ("log n", lambda n: math.log2(n)), ("n", lambda n: n),
         ("n log n", lambda n: n * math.log2(n)), ("n^2", lambda n: n**2),
         ("n^3", lambda n: n**3), ("2^n", lambda n: 2**n)]
print(f"{'n':>6}" + "".join(f"{name:>14}" for name, _ in funcs))
for n in [2, 8, 32, 128, 512]:
    row = [f(n) for _, f in funcs]
    print(f"{n:>6}" + "".join(f"{v:>14.3g}" for v in row))
```

### 5.1 Ceiling and floor

Running times are counts, so they are integers, but $n/2$ or $\log n$ need not be. We use
$\lfloor x \rfloor$ (the largest integer $\le x$) and $\lceil x \rceil$ (the smallest integer
$\ge x$) to round. For example binary search on 1,000 items does at most
$\lfloor \log_2 1000 \rfloor + 1 = 10$ probes.

> [!INTERVIEW]
> "Rank these by growth: $n \log n$, $n^{1.5}$, $2^{\log n}$, $\log(n!)$." Answers: $2^{\log_2 n} = n$
> (rule 5), and $\log(n!) = \Theta(n \log n)$ by Stirling, so the order is
> $2^{\log n} < n\log n = \log(n!) < n^{1.5}$. Interviewers love disguised versions of the seven
> functions.

## 6. How the seven functions show up in code

| Code shape | Growth |
|---|---|
| a fixed number of statements, no loops over the input | $O(1)$ |
| `while n > 1: n //= 2` | $O(\log n)$ |
| `for x in data:` with $O(1)$ body | $O(n)$ |
| sort, then one pass | $O(n \log n)$ |
| `for i in range(n): for j in range(i):` | $O(n^2)$ |
| `for i...: for j...: for k...:` | $O(n^3)$ |
| recursion that branches twice and shrinks by 1, e.g. naive Fibonacci | exponential |

```python-run
def count_steps_halving(n):
    steps = 0
    while n > 1:
        n //= 2
        steps += 1
    return steps

def count_steps_triangle(n):
    steps = 0
    for i in range(n):
        for j in range(i + 1):
            steps += 1
    return steps

for n in [10, 100, 1000]:
    print(n, "halving:", count_steps_halving(n), "  triangle:", count_steps_triangle(n),
          "  n(n+1)/2 =", n * (n + 1) // 2)
```

## 7. Pitfalls

- **Hidden loops.** In Python, `x in some_list`, `some_list.index(x)`, slicing `S[a:b]`,
  `list.insert(0, x)` and string concatenation in a loop are all linear, not constant. A single line
  can hide a loop.
- **Confusing $\log n$ with $n$.** A balanced tree of a million keys has height about 20, not a
  million.
- **Trusting one timing.** Measurements are noisy; repeat them and look at ratios when doubling $n$,
  not at absolute numbers.
- **Ignoring the input size definition.** For a number $N$ given as input, the "size" is the number
  of bits, about $\log N$. An algorithm that loops $N$ times is *exponential* in the input size
  (this is why naive primality testing is not polynomial).

## 8. Summary

- Experiments are useful but limited; we analyse algorithms by counting primitive operations as a
  function of input size, usually in the worst case.
- Seven functions — constant, logarithmic, linear, n-log-n, quadratic, cubic/polynomial,
  exponential — describe almost every running time.
- The arithmetic sum $\sum i = n(n+1)/2$ and the geometric sum $\sum a^i = (a^{n+1}-1)/(a-1)$ are the
  two workhorse identities.
- Logarithm bases differ only by a constant factor, so we simply write $\log n$.

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 3.1–3.2.

## Check yourself

```quiz
[
  {"q": "In the timing experiment, doubling n made one algorithm about 4x slower. What growth rate does that suggest?",
   "options": ["Linear", "Quadratic", "Logarithmic", "Exponential"], "answer": 1,
   "explain": "If T(n) = c n^2 then T(2n) = 4 c n^2, i.e. four times as much. Linear would double; exponential would square."},
  {"q": "Which is NOT one of the drawbacks of experimental analysis listed by Goodrich et al.?",
   "options": ["Only a limited set of inputs can be tested", "The algorithm must be implemented first", "Results depend on hardware and software environment", "It cannot measure Python programs"], "answer": 3,
   "explain": "Python programs can certainly be timed (time, timeit). The three real drawbacks are environment dependence, limited test inputs, and the need for a full implementation."},
  {"q": "Why do we write O(log n) without specifying a base?",
   "options": ["Because the base is always 10", "Because log_a n and log_b n differ only by a constant factor", "Because logarithms are always smaller than 1", "Because the base is always e"], "answer": 1,
   "explain": "Change of base: log_a n = log_b n / log_b a, and 1/log_b a is a constant, which big-O ignores."},
  {"q": "What is 1 + 2 + 3 + ... + n?",
   "options": ["n^2", "n(n+1)/2", "2^n - 1", "n log n"], "answer": 1,
   "explain": "Pair the first and last terms: each pair sums to n+1 and there are n/2 pairs. The result is quadratic."},
  {"q": "What is 1 + 2 + 4 + ... + 2^(n-1)?",
   "options": ["2^n", "2^n - 1", "n 2^n", "2^(n+1)"], "answer": 1,
   "explain": "Geometric sum with a = 2: (2^n - 1)/(2 - 1) = 2^n - 1. A doubling series sums to less than twice its last term."},
  {"q": "Which ordering by growth rate is correct?",
   "options": ["n log n < n < n^2", "log n < n < n log n < n^2 < 2^n", "2^n < n^3 < n^2", "n < log n < n^2"], "answer": 1,
   "explain": "The seven functions in increasing order: 1, log n, n, n log n, n^2, n^3, 2^n."},
  {"q": "A Python line `if x in my_list:` inside a loop over my_list makes the loop...",
   "options": ["O(n) overall", "O(n^2) overall", "O(log n) overall", "O(1) overall"], "answer": 1,
   "explain": "Membership testing in a list scans it, costing O(n). Doing it n times gives O(n^2): a hidden nested loop."}
]
```
