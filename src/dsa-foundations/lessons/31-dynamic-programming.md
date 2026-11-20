# Dynamic programming: matrix chain and LCS

Some problems look as if they require exponential time — there are exponentially many candidate
solutions — yet can be solved in polynomial time by a technique called **dynamic programming
(DP)**. The trick is to notice that the exponentially many candidates are built from a *small*
number of distinct subproblems, and to solve each subproblem **once**, storing its answer in a
table. The book introduces DP with two classics: the **matrix chain-product** and the **longest
common subsequence (LCS)** of two strings.

## 1. The dynamic programming recipe

DP applies to optimisation problems with these ingredients:

- **Simple subproblems.** The global problem can be broken into subproblems with a simple structure,
  parameterised by a few indices such as $i$, $j$, $k$.
- **Subproblem optimisation (optimal substructure).** An optimal solution to the global problem is
  composed of optimal solutions to subproblems.
- **Subproblem overlap.** Optimal solutions to unrelated subproblems share common sub-subproblems —
  so a naive recursion recomputes the same things over and over (as in `bad_fibonacci`).

The method: (1) define the subproblems, (2) write a recurrence relating a subproblem to smaller ones,
(3) compute the table **bottom-up** (or top-down with memoisation), (4) recover the actual solution
by tracing back through the table.

## 2. Matrix chain-product

We want to compute a product of $n$ matrices

$$A = A_0 \cdot A_1 \cdot A_2 \cdots A_{n-1},$$

where $A_i$ is a $d_i \times d_{i+1}$ matrix. Multiplying a $d \times e$ matrix by an $e \times f$
matrix with the standard algorithm takes $d \cdot e \cdot f$ scalar multiplications. Matrix
multiplication is **associative** — $B\cdot(C\cdot D) = (B\cdot C)\cdot D$ — so we may
parenthesise as we wish, and the choice can change the cost dramatically.

**Example.** $B$ is $2 \times 10$, $C$ is $10 \times 50$, $D$ is $50 \times 20$.

- $B \cdot (C \cdot D)$: $10\cdot50\cdot20 + 2\cdot10\cdot20 = 10000 + 400 = 10400$ multiplications.
- $(B \cdot C) \cdot D$: $2\cdot10\cdot50 + 2\cdot50\cdot20 = 1000 + 2000 = 3000$ multiplications.

The **matrix chain-product problem**: find the parenthesisation minimising the total number of
scalar multiplications.

### 2.1 Why brute force fails

Enumerating all parenthesisations means enumerating all binary trees with $n$ leaves — the Catalan
numbers, which grow as $\Omega(4^n / n^{3/2})$. Exponential.

### 2.2 Defining subproblems

Let $N_{i,j}$ be the minimum number of multiplications needed to compute the subproduct
$A_i \cdot A_{i+1} \cdots A_j$. The answer we want is $N_{0,n-1}$, and $N_{i,i} = 0$.

**Optimal substructure.** Any parenthesisation of $A_i \cdots A_j$ has a *final* multiplication that
splits it as $(A_i \cdots A_k) \cdot (A_{k+1} \cdots A_j)$ for some $i \le k < j$. If the whole is
optimal, each side must be parenthesised optimally too (otherwise swap in a better one and improve
the total). The final multiplication combines a $d_i \times d_{k+1}$ matrix with a
$d_{k+1} \times d_{j+1}$ matrix. Hence

$$N_{i,j} = \min_{i \le k < j} \left\{ N_{i,k} + N_{k+1,j} + d_i\, d_{k+1}\, d_{j+1} \right\}.$$

**Overlap.** $N_{i,j}$ depends only on subproblems for shorter chains, and there are only
$O(n^2)$ pairs $(i, j)$. Compute them in order of increasing chain length.

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

**Running time.** Three nested loops, each at most $n$ iterations: **$O(n^3)$** time and $O(n^2)$
space — polynomial instead of exponential. The table is filled diagonal by diagonal: first chains of
length 2, then 3, … so that when computing $N_{i,j}$ everything it needs (entries to its left in row
$i$ and below it in column $j$) is already there.

## 3. DNA and text sequence alignment: the LCS problem

How similar are two strings? Geneticists compare DNA strands (strings over $\{A, C, G, T\}$);
software engineers compare versions of a file (`diff`); spell checkers compare words. One robust
measure is the **longest common subsequence**.

A **subsequence** of a string $X = x_0 x_1 \cdots x_{n-1}$ is any string
$x_{i_1} x_{i_2} \cdots x_{i_k}$ with $i_1 < i_2 < \cdots < i_k$ — characters in order, but **not
necessarily contiguous** (unlike a substring). `AAAG` is a subsequence of `CGATAATTGAGA`.

**LCS problem:** given $X$ (length $n$) and $Y$ (length $m$), find a string $S$, as long as possible, that
is a subsequence of each of them.

Brute force — enumerate all $2^n$ subsequences of $X$ and test each against $Y$ in $O(m)$ — takes
$O(2^n m)$.

### 3.1 Subproblems and recurrence

Let $L_{j,k}$ be the length of a longest common subsequence of the **prefixes** $X[0:j]$ and
$Y[0:k]$. Consider the last characters $x_{j-1}$ and $y_{k-1}$:

- **They match.** Then some LCS of the prefixes ends with this character (if an LCS did not use it,
  we could swap its last character for this one), so
  $$L_{j,k} = L_{j-1,k-1} + 1.$$
- **They differ.** A common subsequence cannot end with both, so it ignores $x_{j-1}$ or ignores
  $y_{k-1}$:
  $$L_{j,k} = \max(L_{j-1,k},\; L_{j,k-1}).$$

Base cases: $L_{j,0} = L_{0,k} = 0$. The answer is $L_{n,m}$.

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

**Memoisation** (top-down) writes the recurrence as a recursive function and caches results; it
computes only the subproblems actually reached, but pays recursion overhead and depth.
**Tabulation** (bottom-up) fills the table iteratively in a safe order; it has smaller constants and
enables the space-saving tricks. They have the same asymptotic running time.

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

- **Edit distance** (Levenshtein): minimum insertions, deletions and substitutions to turn $X$ into
  $Y$; same table shape, slightly different recurrence. With only insertions and deletions, the
  distance is $n + m - 2\,\text{LCS}$ — which is what `diff` computes.
- **Sequence alignment** with scoring matrices and gap penalties (Needleman–Wunsch,
  Smith–Waterman) in bioinformatics.
- **Longest increasing subsequence** = LCS of the sequence and its sorted copy (though better
  algorithms exist).

> [!INTERVIEW]
> For any DP problem say these four things in order: (1) the **state** ("$L[j][k]$ = LCS of the
> first $j$ chars of X and first $k$ of Y"), (2) the **recurrence**, (3) **base cases and fill
> order**, (4) **time and space**, then how to recover the solution. For interval problems
> (matrix chain, burst balloons, optimal BST) the state is an interval $(i, j)$ and you iterate by
> increasing length.

## 6. Pitfalls

- Confusing sub**sequence** (gaps allowed) with sub**string** (contiguous). The longest common
  *substring* has a different recurrence (reset to 0 on mismatch).
- Off-by-one between string indices and table indices (the table has an extra row/column for empty
  prefixes).
- Filling the matrix-chain table row by row instead of by chain length — entries would be read
  before they are computed.
- Building the table with `[[0] * m] * n` — aliased rows!
- Greedy shortcuts ("always multiply the cheapest adjacent pair first") are not optimal for matrix
  chains.

## 7. Summary

| Problem | Subproblem | Recurrence | Time | Space |
|---|---|---|---|---|
| Matrix chain | $N_{i,j}$: best cost for $A_i..A_j$ | $\min_k N_{i,k} + N_{k+1,j} + d_i d_{k+1} d_{j+1}$ | $O(n^3)$ | $O(n^2)$ |
| LCS | $L_{j,k}$: LCS of prefixes | match: diag + 1; else max(up, left) | $O(nm)$ | $O(nm)$, or $O(\min(n,m))$ for length |

> **Source:** Goodrich, Tamassia & Goldwasser, *Data Structures and Algorithms in Python*, ch. 13.3.

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
