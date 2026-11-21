# Dynamic programming: matrix chain and LCS

> **Before this lesson:** You should know the two Fibonacci functions and the idea of overlapping
> subproblems ([Analysing recursive algorithms](#/lesson/dsa-foundations/recursion-analysis)),
> memoisation and bottom-up computation
> ([Designing recursion and eliminating it](#/lesson/dsa-foundations/recursion-design)), how to
> build a grid as a list of lists, and what a matrix and a matrix product are
> ([Using arrays](#/lesson/dsa-foundations/using-arrays)).

## In plain words

**Dynamic programming** is a way of solving a big problem by solving many small versions of it
first, writing each answer down in a table, and never working out the same answer twice. (The
name is historical and has nothing to do with programming being "dynamic"; think of it as
"careful table-filling".) It is usually shortened to **DP**.

Imagine planning the cheapest route across a country with many possible stops. If you tried
every complete route separately, you would recompute the cheapest way to reach each
intermediate town again and again. A sensible planner keeps a notebook: "the cheapest way to
reach town X costs this much". Each new entry is worked out from entries already in the
notebook, and each town is solved once. The notebook is the DP table.

The recursion module showed the idea in miniature: the slow Fibonacci function recomputed the
same values exponentially often, and remembering them made it linear. This lesson applies the
same cure to two realistic problems where the number of candidate answers is astronomically
large.

Why it matters for a job: dynamic programming is the topic interview candidates fear most,
and it appears often. It is also behind real tools: the `diff` command that compares two
versions of a file, spell-checkers that suggest the nearest word, and the alignment of DNA
sequences in biology all use the second algorithm of this lesson or a close relative.

## 1. The dynamic programming recipe

DP is used mostly for **optimisation problems**, which ask for the best of many possible
answers (cheapest, longest, fewest). It applies when a problem has three features:

- **Simple subproblems.** The problem can be broken into smaller problems of the same kind,
  each identified by a few numbers such as indices $i$, $j$, $k$.
- **Optimal substructure.** The best answer to the whole problem is assembled from best
  answers to subproblems. (The cheapest route to the coast that passes through town X includes
  a cheapest route to town X.)
- **Overlapping subproblems.** The same subproblem is needed in many places, so a plain
  recursion would recompute it over and over, as `bad_fibonacci` did.

The method has four steps: (1) define the subproblems precisely; (2) write a recurrence that
expresses a subproblem's answer in terms of smaller subproblems; (3) fill in a table of
answers, either **bottom-up**, smallest subproblems first, or top-down with memoisation; and
(4) if the answer itself is wanted and not only its value, recover it by walking back through
the table.

## 2. Matrix chain-product

The first example comes from numerical computing. Recall that a matrix is a rectangular table
of numbers; a $d \times e$ matrix has $d$ rows and $e$ columns. Two matrices can be multiplied
when the first has as many columns as the second has rows, and multiplying a $d \times e$
matrix by an $e \times f$ matrix in the standard way gives a $d \times f$ matrix at a cost of
$d \cdot e \cdot f$ multiplications of individual numbers. You do not need to know more about
matrices than that: for this problem only the *sizes* matter.

We want to compute a product of $n$ matrices

$$A = A_0 \cdot A_1 \cdot A_2 \cdots A_{n-1},$$

where $A_i$ is a $d_i \times d_{i+1}$ matrix. Matrix multiplication is **associative**:
$B\cdot(C\cdot D) = (B\cdot C)\cdot D$. The result is the same however the product is
bracketed, so we are free to choose which multiplications to do first. That choice can change
the cost enormously.

**Example.** $B$ is $2 \times 10$, $C$ is $10 \times 50$, $D$ is $50 \times 20$.

- $B \cdot (C \cdot D)$: $10\cdot50\cdot20 + 2\cdot10\cdot20 = 10000 + 400 = 10400$ multiplications.
- $(B \cdot C) \cdot D$: $2\cdot10\cdot50 + 2\cdot50\cdot20 = 1000 + 2000 = 3000$ multiplications.

Same three matrices, same answer, and one order of work is more than three times cheaper than
the other. The **matrix chain-product problem** is: find the way of bracketing the product
that minimises the total number of number-by-number multiplications.

### 2.1 Why brute force fails

Trying every bracketing is hopeless. The number of ways to bracket a product of $n$ factors
is given by a famous sequence called the Catalan numbers, which grows roughly like $4^n$. For
30 matrices there are already about a million billion bracketings.

### 2.2 Defining subproblems

Let $N_{i,j}$ be the smallest number of multiplications needed to compute the product of the
matrices from $A_i$ to $A_j$ inclusive. The answer we want is $N_{0,n-1}$, the whole chain. A
single matrix needs no multiplication, so $N_{i,i} = 0$.

**Optimal substructure.** However the chain $A_i \cdots A_j$ is bracketed, some multiplication
is done *last*, and it joins a left block to a right block:
$(A_i \cdots A_k) \cdot (A_{k+1} \cdots A_j)$ for some split position $k$ with $i \le k < j$.
If the overall bracketing is the best possible, then each block must itself be bracketed in
the best possible way; otherwise we could swap in a cheaper bracketing of that block and
lower the total. The left block produces a $d_i \times d_{k+1}$ matrix and the right block a
$d_{k+1} \times d_{j+1}$ matrix, so the last multiplication costs $d_i\, d_{k+1}\, d_{j+1}$.
We do not know the best $k$, so we try them all and keep the cheapest:

$$N_{i,j} = \min_{i \le k < j} \left\{ N_{i,k} + N_{k+1,j} + d_i\, d_{k+1}\, d_{j+1} \right\}.$$

Read it as: "the best cost for the chain from $i$ to $j$ is the best cost of the left part,
plus the best cost of the right part, plus the cost of the final multiplication, minimised
over where to split".

**Overlap.** There are only about $n^2/2$ pairs $(i, j)$, although there are exponentially
many bracketings; the same sub-chains occur inside vast numbers of them. And $N_{i,j}$ depends
only on *shorter* chains. So compute the $N_{i,j}$ in order of increasing chain length: all
chains of 2 matrices, then of 3, and so on.

**A hand computation.** Take four matrices with sizes given by $d = [5, 4, 6, 2, 7]$, so $A_0$
is $5 \times 4$, $A_1$ is $4 \times 6$, $A_2$ is $6 \times 2$ and $A_3$ is $2 \times 7$.

- Chains of length 2: $N_{0,1} = 5\cdot4\cdot6 = 120$, $N_{1,2} = 4\cdot6\cdot2 = 48$,
  $N_{2,3} = 6\cdot2\cdot7 = 84$.
- Chains of length 3. For $N_{0,2}$ there are two splits: $k = 0$ gives
  $0 + 48 + 5\cdot4\cdot2 = 88$, and $k = 1$ gives $120 + 0 + 5\cdot6\cdot2 = 180$; so
  $N_{0,2} = 88$. For $N_{1,3}$: $k = 1$ gives $0 + 84 + 4\cdot6\cdot7 = 252$ and $k = 2$
  gives $48 + 0 + 4\cdot2\cdot7 = 104$; so $N_{1,3} = 104$.
- The whole chain, $N_{0,3}$, has three splits: $k = 0$ gives $0 + 104 + 5\cdot4\cdot7 = 244$;
  $k = 1$ gives $120 + 84 + 5\cdot6\cdot7 = 414$; $k = 2$ gives $88 + 0 + 5\cdot2\cdot7 = 158$.
  The minimum is **158**, with the last multiplication after $A_2$: the bracketing
  $((A_0 (A_1 A_2)) A_3)$.

Each entry was obtained from entries already written down. That is the whole method.

```python-run
def matrix_chain(d):
    """d is a list of n+1 numbers such that the size of the kth matrix is d[k]-by-d[k+1].
    Return an n-by-n table such that N[i][j] represents the minimum number of
    multiplications needed to compute the product of Ai through Aj inclusive."""
    n = len(d) - 1                           # number of matrices
    N = [[0] * n for i in range(n)]          # initialize n-by-n result to zero
    split = [[None] * n for i in range(n)]
    for b in range(1, n):                    # number of products in subchain
        for i in range(n - b):               # start of subchain
            j = i + b                        # end of subchain
            best = None
            for k in range(i, j):
                cost = N[i][k] + N[k + 1][j] + d[i] * d[k + 1] * d[j + 1]
                if best is None or cost < best:
                    best, split[i][j] = cost, k
            N[i][j] = best
    return N, split

def parenthesize(split, i, j):
    if i == j: return f"A{i}"
    k = split[i][j]
    return "(" + parenthesize(split, i, k) + " " + parenthesize(split, k + 1, j) + ")"

d = [2, 10, 50, 20]
N, split = matrix_chain(d)
print(N[0][2], parenthesize(split, 0, 2))
d = [30, 35, 15, 5, 10, 20, 25]
N, split = matrix_chain(d)
print(N[0][5], parenthesize(split, 0, 5))
for row in N: print(row)
```

**Reading the code.** `d` lists the sizes, so there are `len(d) - 1` matrices. `N` is the table
of best costs and `split` remembers, for each chain, the split position `k` that achieved the
best cost. The outer loop variable `b` is the chain length minus one, so chains are processed
shortest first; `i` is where the chain starts and `j = i + b` where it ends; the innermost loop
tries every split. `parenthesize` then rebuilds the best bracketing by following the recorded
splits recursively. The first line of output is `3000 ((A0 A1) A2)`, the three-matrix example
above. The second is the best cost and bracketing for a chain of six matrices, followed by the
whole table `N`; its top-right entry is the answer.

**Running time.** Three nested loops, each running at most $n$ times: **$O(n^3)$** time and
$O(n^2)$ space. That is polynomial where brute force was exponential. Picture the table being
filled one diagonal at a time: first the chains of length 2 next to the main diagonal, then
the chains of length 3, and so on outwards, so that whenever $N_{i,j}$ is computed, everything
it needs is already in place.

## 3. DNA and text sequence alignment: the LCS problem

How similar are two strings? Biologists ask this of DNA strands, which are strings over the
four letters A, C, G and T. Programmers ask it of two versions of a file. Spell-checkers ask
it of a typed word and a dictionary word. One robust measure of similarity is the **longest
common subsequence**.

A **subsequence** of a string is what remains after deleting zero or more of its characters
and closing up the gaps: the surviving characters keep their order, but they **need not have
been next to each other**. (A *substring*, by contrast, must be a run of adjacent characters.)
`ACE` is a subsequence of `ABCDE` but not a substring; `AAAG` is a subsequence of
`CGATAATTGAGA`.

**The LCS problem:** given a string $X$ of length $n$ and a string $Y$ of length $m$, find the
longest string that is a subsequence of both. The more two strings have in common, the longer
it is.

Brute force would list all $2^n$ subsequences of $X$ (each character is either kept or
deleted) and test each against $Y$ in $O(m)$ time, for $O(2^n m)$ in all. Hopeless for
strings of any real length.

### 3.1 Subproblems and recurrence

The subproblems are the same question asked about beginnings of the two strings. Let
$L_{j,k}$ be the length of a longest common subsequence of the **prefixes** $X[0:j]$ (the
first $j$ characters of $X$) and $Y[0:k]$ (the first $k$ characters of $Y$). Look at the last
character of each prefix, $x_{j-1}$ and $y_{k-1}$. There are two cases.

- **They are the same character.** Then it is safe to match them with each other: a longest
  common subsequence can always be arranged to end with this shared character. What comes
  before it is a longest common subsequence of the two prefixes with that character removed:
  $$L_{j,k} = L_{j-1,k-1} + 1.$$
- **They differ.** A common subsequence cannot end with both of them, so at least one of the
  two last characters is not used. Either drop the last character of the $X$ prefix or drop
  the last character of the $Y$ prefix, and take whichever does better:
  $$L_{j,k} = \max(L_{j-1,k},\; L_{j,k-1}).$$

Base cases: an empty prefix has nothing in common with anything, so $L_{j,0} = L_{0,k} = 0$.
The answer to the original problem is $L_{n,m}$.

In the code the table has one more row and one more column than the strings have characters,
to hold those base cases; that is why string position `j` corresponds to table row `j + 1`.

```python-run
def LCS(X, Y):
    """Return table such that L[j][k] is length of LCS for X[0:j] and Y[0:k]."""
    n, m = len(X), len(Y)                        # introduce convenient notations
    L = [[0] * (m + 1) for k in range(n + 1)]    # (n+1) x (m+1) table
    for j in range(n):
        for k in range(m):
            if X[j] == Y[k]:                     # align this match
                L[j + 1][k + 1] = L[j][k] + 1
            else:                                # choose to ignore one character
                L[j + 1][k + 1] = max(L[j][k + 1], L[j + 1][k])
    return L

def LCS_solution(X, Y, L):
    """Return a longest common subsequence of X and Y, given LCS table L."""
    solution = []
    j, k = len(X), len(Y)
    while L[j][k] > 0:                           # common characters remain
        if X[j - 1] == Y[k - 1]:
            solution.append(X[j - 1])
            j -= 1
            k -= 1
        elif L[j - 1][k] >= L[j][k - 1]:
            j -= 1
        else:
            k -= 1
    return ''.join(reversed(solution))           # return left-to-right version

X, Y = "GTTCCTAATA", "CGATAATTGAGA"
L = LCS(X, Y)
print("length:", L[len(X)][len(Y)], " one LCS:", LCS_solution(X, Y, L))
print("     " + "  ".join(Y))
for j, row in enumerate(L):
    print((X[j - 1] if j else " ") + " " + " ".join(f"{v:2d}" for v in row))
```

**Running time:** the table has $(n+1)(m+1)$ entries, each computed in $O(1)$: **$O(nm)$** time and
space. Reconstruction walks from $L_{n,m}$ back to a zero entry in $O(n + m)$ steps.

### 3.2 Small dry run

$X = $ `ABCB`, $Y = $ `BDCAB`:

|   | "" | B | D | C | A | B |
|---|---|---|---|---|---|---|
| "" | 0 | 0 | 0 | 0 | 0 | 0 |
| A | 0 | 0 | 0 | 0 | 1 | 1 |
| B | 0 | 1 | 1 | 1 | 1 | 2 |
| C | 0 | 1 | 1 | 2 | 2 | 2 |
| B | 0 | 1 | 1 | 2 | 2 | 3 |

LCS length 3. Trace back from the bottom-right cell (row B, column B): the characters match, so
record `B` and move diagonally to (C, A). They differ; up is 1, left is 2, so move left to (C, C):
match — record `C`, move diagonally to (B, D). Differ; up is 0, left is 1, so move left to (B, B):
match — record `B`, and we land on a 0 entry. Reversing the recorded characters gives **`BCB`**.
LCS strings are not unique in general, but the length is.

### 3.3 Reconstructing the solution

Start at $L_{n,m}$. At $L_{j,k}$: if $x_{j-1} = y_{k-1}$, that character is part of the LCS — record
it and move diagonally to $L_{j-1,k-1}$. Otherwise move to whichever of $L_{j-1,k}$ and $L_{j,k-1}$
is larger (the one the value came from). Stop when the entry is 0. The characters are collected in
reverse.

### 3.4 Saving space

Row $j + 1$ depends only on row $j$. If only the **length** is needed, keep two rows (or one row
plus a saved diagonal value): $O(\min(n, m))$ space. Recovering the string in linear space is
possible too (Hirschberg's algorithm), using divide-and-conquer over the table.

```python-run
def lcs_length_two_rows(X, Y):
    if len(Y) > len(X): X, Y = Y, X
    prev = [0] * (len(Y) + 1)
    for x in X:
        cur = [0]
        for k, y in enumerate(Y):
            cur.append(prev[k] + 1 if x == y else max(prev[k + 1], cur[k]))
        prev = cur
    return prev[-1]
print(lcs_length_two_rows("GTTCCTAATA", "CGATAATTGAGA"), lcs_length_two_rows("ABCB", "BDCAB"))
```

## 4. Top-down versus bottom-up

There are two ways to turn a recurrence into a program.

**Memoisation**, the top-down way, writes the recurrence as a recursive function and caches
each result the first time it is computed. It is the quickest to write, and it computes only
the subproblems that are really needed, but it pays for the function calls and can run into
the recursion depth limit.

**Tabulation**, the bottom-up way, fills the table with loops, in an order that guarantees
each entry's ingredients are ready. It is somewhat faster and makes the space-saving tricks of
section 3.4 possible. Both have the same big-O running time.

Here is the LCS length computed top-down, with Python's `lru_cache` doing the remembering.
The inner function `L(j, k)` is the recurrence, word for word:

```python-run
from functools import lru_cache
def lcs_memo(X, Y):
    @lru_cache(maxsize=None)
    def L(j, k):
        if j == 0 or k == 0: return 0
        if X[j - 1] == Y[k - 1]: return L(j - 1, k - 1) + 1
        return max(L(j - 1, k), L(j, k - 1))
    return L(len(X), len(Y))
print(lcs_memo("GTTCCTAATA", "CGATAATTGAGA"))
```

## 5. Relatives of LCS

- **Edit distance** (also called Levenshtein distance): the smallest number of single-character
  insertions, deletions and substitutions that turn $X$ into $Y$. It uses a table of the same
  shape with a slightly different recurrence. If only insertions and deletions are allowed,
  the distance is $n + m - 2 \times (\text{LCS length})$, which is essentially what `diff`
  computes.
- **Sequence alignment** in biology, which scores matches, mismatches and gaps with different
  weights.
- **Longest increasing subsequence** of a list of numbers, which equals the LCS of the list
  and a sorted copy of it (faster special-purpose algorithms exist).

> [!INTERVIEW]
> For any DP problem, say four things in order. (1) The **state**: what one table entry means,
> in a full sentence ("$L[j][k]$ is the LCS length of the first $j$ characters of X and the
> first $k$ of Y"). (2) The **recurrence**. (3) The **base cases and the order of filling**.
> (4) The **time and space**, and how to recover the solution itself. For problems about a
> stretch of a sequence, such as matrix chain, the state is a pair $(i, j)$ marking the ends of
> the stretch, and the table is filled by increasing length.

## 6. Pitfalls

- **Confusing subsequence with substring.** A subsequence may have gaps; a substring may not.
  The longest common *substring* has a different recurrence, in which a mismatch resets the
  count to 0.
- **Index slips between strings and table.** The table has an extra row and column for the
  empty prefixes, so table row `j` goes with string character `j - 1`.
- **Filling the matrix-chain table row by row.** Entries would be read before they have been
  computed; fill by increasing chain length.
- **Building the table with `[[0] * m] * n`.** All the rows are then one and the same list
  (the trap from the arrays module).
- **Trusting a plausible shortcut.** "Always do the cheapest neighbouring multiplication
  first" sounds reasonable and does not give the best bracketing in general. DP is needed
  because local choices of that kind can be wrong.

## 7. Summary

| Problem | Subproblem | Recurrence | Time | Space |
|---|---|---|---|---|
| Matrix chain | $N_{i,j}$: best cost for $A_i..A_j$ | $\min_k N_{i,k} + N_{k+1,j} + d_i d_{k+1} d_{j+1}$ | $O(n^3)$ | $O(n^2)$ |
| LCS | $L_{j,k}$: LCS of prefixes | match: diag + 1; else max(up, left) | $O(nm)$ | $O(nm)$, or $O(\min(n,m))$ for length |

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 13.3.

## Glossary

- **Dynamic programming (DP)**: solving a problem by solving each of its subproblems once and
  storing the answers in a table.
- **Optimisation problem**: a problem that asks for the best among many possible answers.
- **Subproblem**: a smaller instance of the same problem.
- **Optimal substructure**: a best solution is built from best solutions of subproblems.
- **Overlapping subproblems**: the same subproblem is needed many times.
- **State**: the meaning of one entry of the DP table.
- **Recurrence**: the formula giving a table entry in terms of other entries.
- **Memoisation (top-down)**: recursion that caches each result.
- **Tabulation (bottom-up)**: filling the table with loops, smallest subproblems first.
- **Associative**: an operation whose result does not depend on how it is bracketed.
- **Matrix chain-product problem**: choosing the cheapest bracketing for a product of matrices.
- **Subsequence**: characters of a string taken in order, not necessarily adjacent.
- **Longest common subsequence (LCS)**: the longest string that is a subsequence of two given
  strings.
- **Edit distance**: the fewest single-character changes that turn one string into another.

## Check yourself

```quiz
[
  {"q": "Which three properties make a problem suitable for dynamic programming?",
   "options": ["Sorted input, unique keys, small alphabet", "Simple subproblems, optimal substructure, overlapping subproblems", "Greedy choice, matroid structure, monotonicity", "Randomness, independence, linearity"], "answer": 1,
   "explain": "Few distinct subproblems, optimal solutions built from optimal sub-solutions, and reuse of sub-subproblems."},
  {"q": "B is 2x10, C is 10x50, D is 50x20. Cost of (B C) D?",
   "options": ["10400", "3000", "2000", "1000"], "answer": 1,
   "explain": "2*10*50 = 1000 for BC (a 2x50 matrix), then 2*50*20 = 2000."},
  {"q": "Running time of the matrix chain DP for n matrices?",
   "options": ["O(n^2)", "O(n^3)", "O(2^n)", "O(n log n)"], "answer": 1,
   "explain": "O(n^2) subproblems, each minimising over O(n) split points."},
  {"q": "In the LCS recurrence, when X[j-1] == Y[k-1], L[j][k] equals...",
   "options": ["L[j-1][k-1] + 1", "max(L[j-1][k], L[j][k-1])", "L[j-1][k] + L[j][k-1]", "0"], "answer": 0,
   "explain": "The matching character extends an LCS of the two shorter prefixes."},
  {"q": "LCS length of 'ABCB' and 'BDCAB'?",
   "options": ["2", "3", "4", "5"], "answer": 1,
   "explain": "For example BCB."},
  {"q": "A subsequence differs from a substring in that...",
   "options": ["it must be sorted", "its characters need not be contiguous in the original", "it may reorder characters", "it must be a prefix"], "answer": 1,
   "explain": "Order is preserved, gaps are allowed."},
  {"q": "How much space is needed to compute only the LCS length?",
   "options": ["O(nm) necessarily", "O(min(n, m)) by keeping one or two rows", "O(1)", "O(2^n)"], "answer": 1,
   "explain": "Each row depends only on the previous row."}
]
```
