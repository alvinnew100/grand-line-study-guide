# Measuring algorithms and the seven functions

> **Before this lesson:** Nothing beyond basic Python. You should be able to read a `for` loop, a
> function definition (`def`) and a list such as `[3, 1, 4]`. No earlier lesson is assumed, and no
> mathematics beyond multiplying and dividing whole numbers; every formula is explained when it
> first appears.

## In plain words

An **algorithm** is a list of exact steps for getting a job done, such as "to find a name in a
phone book, open it in the middle, decide which half the name is in, and repeat". A **data
structure** is a way of arranging information so that those steps are convenient, such as keeping
the phone book in alphabetical order. This lesson is about one question: *how much work does an
algorithm do as the amount of data grows?*

Think of two ways to find a friend's house on a long street. Method one: knock on every door from
the start of the street. Method two: read the house numbers and go straight there. On a street of
ten houses nobody cares which you use. On a street of ten million houses, method one takes weeks and
method two takes the same few seconds it always did. The methods do not differ by "a bit faster";
they *grow* differently, and growth is what this lesson teaches you to see.

Why it matters for a job: almost every coding interview ends with "what is the running time of your
solution?", and almost every slow page, report or data job at work is slow because some step grows
faster than its author expected. The seven growth shapes in this lesson are the vocabulary for both
conversations, and every later lesson in this track uses them.

## 1. Why analyse at all?

Every data structure in this track comes with a price tag: "this operation costs $O(1)$", "that one
costs $O(\log n)$". (Read $O(\ldots)$ as "grows no faster than"; the next lesson defines it
exactly.) Before we can read those price tags we need to agree on *what* is being measured and
*how*. We judge an algorithm mainly on two resources:

- **running time**: how long it takes to finish, and
- **space**: how much memory (the computer's working storage) it needs while it runs.

Both depend on how much data the algorithm is given. We call that amount the **input size** and
write it as the letter $n$. For a list, $n$ is the number of items in it; for a piece of text, the
number of characters. When you see $n$ in this track, read it as "however many items there are".

Running time almost always grows as $n$ grows, and the *shape* of that growth matters far more than
the raw speed of the machine. A program that takes twice as long on a laptop as on a server is
still the same algorithm. A program whose time quadruples whenever the input doubles is a different
kind of thing from one whose time doubles: give each ten times more data and the first takes a
hundred times longer while the second takes ten times longer.

## 2. Experimental studies

The most direct way to learn how fast an algorithm is: write it as a program, run it on inputs of
various sizes, and record how long each run took. Python has a stopwatch for this:
`time.perf_counter()` returns the current reading of a very fine clock, in seconds, so reading it
before and after a piece of code and subtracting gives the elapsed time. (The `timeit` module does
the same thing many times over and averages, which smooths out random noise.)

The demo below times two solutions to one small task. Given a list of numbers `S`, produce a list
`A` in which `A[j]` is the average of the first `j + 1` numbers of `S`. For `S = [10, 20, 30]` the
answer is `[10.0, 15.0, 20.0]`: the average of `10`, then of `10, 20`, then of `10, 20, 30`. These
are called **prefix averages**, because a *prefix* is a starting stretch of a list.

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

**Reading this code line by line**

- `import time` makes Python's clock functions available.
- `def prefix_average_quadratic(S):` defines the first solution. `n = len(S)` stores the number of
  items, and `A = [0] * n` builds a list of `n` zeros to hold the answers.
- `for j in range(n):` runs the indented block once for each position `j = 0, 1, ..., n - 1`.
- Inside it, `total = 0` starts a fresh sum, and the inner loop `for i in range(j + 1):` adds up
  `S[0]`, `S[1]`, ..., `S[j]` from scratch. `total += S[i]` means "add `S[i]` to `total`".
- `A[j] = total / (j + 1)` divides the sum by how many numbers went into it.
- `prefix_average_linear` does the same job with one loop. It never resets `total`; the sum of the
  first `j + 1` numbers is the previous sum plus one more number, so one addition per position is
  enough.
- The last block builds lists of 500, 1000, 2000 and 4000 numbers, reads the clock around each
  call, and prints the times in **milliseconds** (thousandths of a second, shortened to ms).

**What you should see.** The exact numbers depend on your machine, but the pattern does not. Each
time $n$ doubles, the first version takes roughly **four** times as long, while the second takes
roughly **twice** as long. Why four? The first version does about $n \times n / 2$ additions,
because for each of $n$ positions it re-adds up to $n$ numbers. Doubling $n$ doubles both factors,
and $2 \times 2 = 4$. The second version does $n$ additions, so doubling $n$ doubles the work. That
ratio, measured when the input doubles, is the fingerprint of a growth rate, and it is far more
reliable than any single timing.

The names in the code come from that arithmetic: work that grows like $n \times n$ is called
**quadratic**, and work that grows like $n$ is called **linear**. Section 4 gives both a proper
introduction.

### 2.1 The limits of experiments

Timing code is honest, and you should do it. On its own it has three weaknesses:

1. **The environment has to be identical.** To compare two algorithms fairly they must run on the
   same machine, with the same version of Python, while nothing else is hogging the computer.
   Otherwise you are measuring the machines, not the algorithms.
2. **You can only try a limited set of inputs.** The input that makes an algorithm slow may be a
   rare, awkward one that you never thought to test. Such an input is called **pathological**.
3. **The whole algorithm must be written first.** You learn nothing until the code exists, which
   is an expensive way to discover that the idea was poor.

We want a method that works on a description of the algorithm before any code is written, covers
*every* possible input, and gives the same answer whatever the hardware.

## 3. Counting primitive operations

The method is to count steps instead of seconds. A **primitive operation** is a low-level step
that takes a small, fixed amount of time no matter how large the input is. Examples:

- giving a value a name (`total = 0`),
- one arithmetic operation or comparison (`a + b`, `x < y`),
- reading or writing one list element by its position (`A[j]`),
- calling a function, or returning from one,
- following a reference from one object to another (how Python gets from a name to its value).

No two of these take exactly the same time, but each takes at most some fixed amount, perhaps a
few billionths of a second. So if an algorithm performs $t$ primitive operations, its running time
is roughly proportional to $t$ on any machine: a faster computer shrinks every step by about the
same factor and leaves the count unchanged.

The count depends on the input size, so we write it as a **function** of $n$. A function here means
a rule that turns one number into another; $f(n) = 3n + 2$ is the rule "multiply by three, then add
two". If an algorithm does $3n + 2$ steps on a list of $n$ items, then it does 32 steps on ten
items and 3,002 on a thousand.

**A tiny worked count.** Here is a function that finds the largest number in a list:

```python
def find_max(data):
    biggest = data[0]            # 2 steps: one read, one assignment
    for val in data:             # the loop body runs n times
        if val > biggest:        # 1 comparison each time
            biggest = val        # at most 1 assignment each time
    return biggest               # 1 step
```

The first line and the last line happen once: 3 steps. The loop body happens $n$ times and costs at
most 2 steps each time: $2n$ steps. In total, at most $2n + 3$. We do not care much whether the
true figure is $2n + 3$ or $4n + 7$ (that depends on how finely you slice a "step"). What matters is
that the count is some fixed number times $n$, plus a fixed extra. That is the linear shape.

### Worst case, average case, best case

For one fixed size $n$, different inputs can need different numbers of steps. In `find_max`, the
line `biggest = val` runs only when a new record is found: never for a list in descending order,
and $n - 1$ times for a list in strictly ascending order. So there are three questions one could ask:

- The **best case** is the smallest number of steps over all inputs of size $n$. It is rarely
  useful, because you cannot count on being lucky.
- The **average case** is the typical number of steps. It sounds ideal, but "typical" needs a
  precise statement of how likely each input is (a *probability distribution*), which is often
  unknown and makes the mathematics hard.
- The **worst case** is the largest number of steps over all inputs of size $n$. It is usually the
  easiest to work out and, more importantly, it is a *guarantee*: an algorithm that is fast in the
  worst case is fast on every input.

Unless a lesson says otherwise, every running time in this track is a worst-case figure.

> [!TIP]
> Designing for the worst case pushes you towards robust algorithms. "Usually fast" is a weaker
> promise than "always fast", and bad inputs are not only bad luck: attackers deliberately send a
> service the input that makes it slowest, in order to overload it.

## 4. The seven functions

Almost every step count you will meet in this track has one of only seven shapes. Learn the seven
and you can read any table of running times (often called a *complexity table*, where
**complexity** means "how the cost grows with the input size").

| # | Function | Name | Typical source |
|---|---|---|---|
| 1 | $f(n) = c$ | constant | one arithmetic step, reading one list element |
| 2 | $f(n) = \log_2 n$ | logarithmic | repeatedly halving what is left to search |
| 3 | $f(n) = n$ | linear | one pass over the input |
| 4 | $f(n) = n \log n$ | n-log-n | good sorting algorithms |
| 5 | $f(n) = n^2$ | quadratic | a loop inside a loop over the input |
| 6 | $f(n) = n^3$ (and $n^d$) | cubic / polynomial | three nested loops |
| 7 | $f(n) = b^n$ | exponential | trying every combination of choices |

The sections below take them one at a time. In each formula, $f(n)$ is read "f of n" and means
"the number of steps when the input size is $n$".

### 4.1 The constant function

$f(n) = c$, where $c$ is some fixed number, does not depend on $n$ at all. Ten items or ten
million, the cost is the same. Adding two numbers, giving a variable a value, or reading `A[i]`
from a Python list are constant-time steps. The most useful constant function is $g(n) = 1$,
because any other constant is that one multiplied by a fixed number.

### 4.2 The logarithm

The logarithm is the function newcomers find strangest, so start from a game. Think of a number
between 1 and 1,000,000 and let a friend guess it; after each guess you say "higher" or "lower".
A sensible friend always guesses the middle of what is left, which throws away half of the
remaining numbers each time. One million possibilities become 500,000, then 250,000, and so on.
After only 20 guesses a single number is left. The logarithm counts those halvings:

> $\log_2 n$ is, roughly, the number of times you can halve $n$ before you get down to 1.

The precise definition is the reverse of raising to a power: $\log_b n = x$ exactly when $b^x = n$.
The number $b$ is called the **base**. Since $2^{10} = 1024$, we have $\log_2 1024 = 10$; since
$2^{20} = 1{,}048{,}576$, $\log_2$ of a million is a little under 20. In computer science the base
is 2 unless stated otherwise, so this track writes $\log n$ for $\log_2 n$.

The point to take away is how slowly a logarithm grows. Multiply $n$ by a thousand and $\log n$
goes up by only about 10. An algorithm whose step count is logarithmic barely notices that its
input got bigger.

A handful of rules are worth having on hand (for positive $a$, $b$, $c$, with $b \ne 1$):

1. $\log_b(ac) = \log_b a + \log_b c$ (the log of a product is the sum of the logs)
2. $\log_b(a/c) = \log_b a - \log_b c$
3. $\log_b(a^c) = c \log_b a$
4. $\log_b a = \log_d a / \log_d b$ (change of base)
5. $b^{\log_d a} = a^{\log_d b}$

Rule 4 explains why nobody bothers to write the base when discussing growth:
$\log_{10} n = \log_2 n / \log_2 10$, and $\log_2 10 \approx 3.32$ is a fixed number. Changing the
base only multiplies the function by a constant, and constant multipliers do not change a growth
shape.

### 4.3 The linear function

$f(n) = n$ is what you pay to look at each of $n$ items once: reading the input, adding up a list,
comparing a value against every element. When an answer depends on every input item (as the
largest element of an unsorted list does), linear is the best any algorithm can achieve, since it
must at least look at them all.

### 4.4 The n-log-n function

$f(n) = n \log n$ is $n$ multiplied by the logarithm of $n$. It grows a little faster than linear
and far slower than quadratic: for a million items it is about 20 million, where $n^2$ would be a
million million. The fastest general-purpose sorting algorithms run in this time, and the sorting
module of this track proves that no method that works by comparing pairs of items can do better.

### 4.5 The quadratic function

$f(n) = n^2$ ($n$ times $n$) appears whenever one loop sits inside another and each runs about $n$
times: for every item, do something with every item.

A very common variant is an inner loop that runs once the first time, twice the second time, three
times the third time, and so on up to $n$. The first version of prefix averages was exactly this.
The total number of inner steps is $1 + 2 + 3 + \cdots + n$. To add that up, write the sum twice,
once forwards and once backwards, and add the two rows column by column:

```
  1  +   2   +   3   + ... +  n
  n  + (n-1) + (n-2) + ... +  1
-------------------------------
(n+1) + (n+1) + (n+1) + ... + (n+1)      n columns, each adding to n+1
```

Two copies of the sum come to $n(n+1)$, so one copy is half of that:

$$1 + 2 + 3 + \cdots + n = \frac{n(n+1)}{2}.$$

For $n = 100$ this gives $100 \times 101 / 2 = 5050$. Multiplied out, the formula is
$\tfrac{1}{2}n^2 + \tfrac{1}{2}n$. That is still quadratic: it is about half of $n^2$, and halving
a cost does not change how it grows.

The notation for "add up a list of terms" is the capital Greek letter sigma. A **summation**
$\sum_{i=a}^{b} f(i)$ means $f(a) + f(a+1) + \cdots + f(b)$: let $i$ take every whole value from
$a$ to $b$ and add the results. So the sum above is written $\sum_{i=1}^{n} i$. A loop in code
turns directly into a summation, which is why the symbol appears throughout this track.

### 4.6 The cubic function and other polynomials

$f(n) = n^3$ ($n \times n \times n$) comes from three nested loops. It appears less often; the
textbook example is multiplying two grids of numbers the direct way.

Constant, linear, quadratic and cubic all belong to one family. A **polynomial** is a sum of
powers of $n$, each multiplied by a fixed number:
$f(n) = a_0 + a_1 n + a_2 n^2 + \cdots + a_d n^d$ with $a_d \ne 0$. The highest power $d$ is its
**degree**. For example $5 + 2n + 3n^2$ is a polynomial of degree 2. When $n$ is large the
highest power dwarfs the rest, so the degree alone tells you the growth shape. In everyday
engineering talk, "polynomial time" means "usable", and the lower the degree the better.

### 4.7 The exponential function

$f(n) = b^n$ is the base $b$ multiplied by itself $n$ times; the base is larger than 1 and is
usually 2. Here $n$ sits in the exponent, the small raised position, and that changes everything:
adding **one** item to the input *doubles* the work. The standard source is trying every
combination. A set of $n$ light switches has $2^n$ on/off settings, so a program that tests each
setting of 30 switches does about a billion tests, and adding 10 more switches makes it a thousand
times worse.

Three exponent rules are used in this track: $(b^a)^c = b^{ac}$, $b^a b^c = b^{a+c}$, and
$b^a / b^c = b^{a-c}$.

Exponentials also come with a summation worth memorising. A **geometric sum** adds terms that each
multiply the previous one by the same number $a$:

$$\sum_{i=0}^{n} a^i = 1 + a + a^2 + \cdots + a^n = \frac{a^{n+1} - 1}{a - 1} \quad (a > 0, a \ne 1).$$

The case to remember is $a = 2$: $1 + 2 + 4 + \cdots + 2^{n-1} = 2^n - 1$. Check it with small
numbers: $1 + 2 + 4 = 7 = 8 - 1$. In words, a doubling series adds up to less than twice its last
term. This is also the largest whole number that fits in $n$ bits (a **bit** is a single 0 or 1),
and it comes back in the dynamic-arrays lesson: a list that doubles its storage whenever it fills
up spends, in total, less than twice its final size on copying.

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

Read the table one row at a time. Going from 8 items to 1,024 items (128 times more), $\log n$
went from 3 to 10, $n^2$ went from 64 to about a million, and $2^n$ went from 256 to a number with
309 digits. If one operation takes a microsecond (a millionth of a second), $2^{64}$ operations
take about 585,000 years. Exponential algorithms are usable only for tiny inputs.

The next demo prints the same kind of table for you. Change the list of sizes and run it again.

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

**Reading this code.** `funcs` is a list of pairs: a label and a small unnamed function. The word
`lambda` creates such a function in one line, so `lambda n: n**2` means "given `n`, return `n`
squared" (`**` is Python's power operator). `math.log2(n)` is the base-2 logarithm. The loop
computes every function for each `n` and prints one row. The format code `.3g` shows three
significant digits, switching to scientific notation for huge values: `1.34e+154` means 1.34
followed by 154 more digits' worth of size. Look at the last column racing away from the others.

### 5.1 Ceiling and floor

Step counts are whole numbers, but $n/2$ or $\log n$ often are not. Two rounding symbols fix that.
The **floor** $\lfloor x \rfloor$ rounds down to the nearest whole number, so
$\lfloor 3.7 \rfloor = 3$. The **ceiling** $\lceil x \rceil$ rounds up, so $\lceil 3.2 \rceil = 4$.
For example, the halving search from the guessing game needs at most
$\lfloor \log_2 1000 \rfloor + 1 = 9 + 1 = 10$ guesses for 1,000 items, because
$\log_2 1000 \approx 9.97$.

> [!INTERVIEW]
> "Rank these by growth: $n \log n$, $n^{1.5}$, $2^{\log n}$, $\log(n!)$." Two of them are
> disguises. By rule 5, $2^{\log_2 n} = n^{\log_2 2} = n$, so the third is plain linear. And $n!$
> (read "n factorial") is $1 \times 2 \times \cdots \times n$; its logarithm is
> $\log 1 + \log 2 + \cdots + \log n$, a sum of $n$ terms that are each at most $\log n$ and mostly
> not much smaller, so it grows like $n \log n$. The order is
> $2^{\log n} < n\log n \approx \log(n!) < n^{1.5}$. Interviewers like disguised versions of the
> seven functions; the first move is always to simplify each one to a familiar shape.

## 6. How the seven functions show up in code

With practice you can recognise the shape of a piece of code by looking at its loops. The table
uses the $O(\ldots)$ shorthand from section 1; read $O(n^2)$ as "grows no faster than $n^2$".

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

**Reading this code.** Neither function does useful work; each counts its own steps so that you
can compare the count with a formula.

- `count_steps_halving` keeps replacing `n` by `n // 2` (`//` is division that throws away the
  remainder, so `7 // 2` is `3`) and counts how many times it can do so before reaching 1. That
  count is $\lfloor \log_2 n \rfloor$.
- `count_steps_triangle` has an inner loop that runs 1 time, then 2 times, up to `n` times. Its
  count is $1 + 2 + \cdots + n$.

The output is:

```
10 halving: 3   triangle: 55   n(n+1)/2 = 55
100 halving: 6   triangle: 5050   n(n+1)/2 = 5050
1000 halving: 9   triangle: 500500   n(n+1)/2 = 500500
```

The halving count rises by 3 each time $n$ grows tenfold (because $2^3 = 8$ is close to 10), while
the triangle count grows a hundredfold. The last two columns agree, which confirms the formula
from section 4.5.

## 7. Pitfalls

- **Hidden loops.** One line of Python can contain a loop you cannot see. `x in some_list` checks
  the items one by one; `some_list.index(x)` does the same; a slice `S[a:b]` copies every item in
  the range; `some_list.insert(0, x)` moves every existing item one place along; and building a
  string with `s = s + piece` inside a loop recopies the whole string each time. All of these are
  linear, not constant.
- **Confusing $\log n$ with $n$.** A well-organised structure holding a million keys can be
  searched in about 20 steps, not a million. Mixing the two up is the difference between "instant"
  and "noticeably slow".
- **Trusting one timing.** Measurements are noisy. Repeat them, and look at the ratio when $n$
  doubles, not at any single number.
- **Forgetting what "input size" means for a number.** When the input is one number $N$ (not a
  list), its size is the number of digits needed to write it down, about $\log N$ bits. A loop
  that runs $N$ times is therefore *exponential* in the input size: adding one bit to $N$ doubles
  the loop. This is why testing whether a 300-digit number is prime by trying every smaller
  divisor is hopeless.
- **Dismissing the constant too early.** Growth shape decides what happens for large inputs. For
  small inputs a "slower-growing" method with heavy bookkeeping can lose to a plain one. The next
  lesson makes this precise.

## 8. Summary

- Timing experiments are useful but limited, so we also analyse algorithms by counting primitive
  operations as a function of the input size $n$, usually in the worst case.
- Seven functions (constant, logarithmic, linear, n-log-n, quadratic, cubic or polynomial, and
  exponential) describe almost every running time.
- $\log_2 n$ counts how many times $n$ can be halved; it grows extremely slowly.
- Two sums do most of the work: $1 + 2 + \cdots + n = n(n+1)/2$ and
  $1 + a + \cdots + a^n = (a^{n+1}-1)/(a-1)$.
- Logarithms in different bases differ only by a constant multiplier, so growth rates are written
  as $\log n$ with no base.

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 3.1–3.2.

## Glossary

- **Algorithm**: an exact, finite list of steps for carrying out a task.
- **Data structure**: a way of arranging data so that certain operations on it are convenient.
- **Input size ($n$)**: how much data an algorithm is given, such as the number of items in a list.
- **Running time**: how long an algorithm takes, usually stated as a step count that depends on $n$.
- **Space**: how much memory an algorithm uses while it runs.
- **Primitive operation**: a basic step, such as one addition or one comparison, whose cost does
  not depend on the input size.
- **Worst case / average case / best case**: the largest, typical and smallest step counts over
  all inputs of one size.
- **Growth rate**: how a step count changes as $n$ increases; the "shape" of the function.
- **Constant, linear, quadratic, cubic**: step counts proportional to 1, $n$, $n^2$ and $n^3$.
- **Logarithm ($\log n$)**: the number of times $n$ can be halved before reaching 1 (base 2).
- **Polynomial**: a sum of fixed multiples of powers of $n$; its degree is the highest power.
- **Exponential**: a function such as $2^n$, where adding one to $n$ multiplies the value.
- **Summation ($\sum$)**: shorthand for adding up a sequence of terms.
- **Geometric sum**: a sum in which each term is a fixed multiple of the one before.
- **Floor / ceiling**: rounding down / up to the nearest whole number.

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
