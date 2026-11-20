PROBLEMS = [
dict(
    id="fibonacci-number",
    title="Fibonacci Number",
    difficulty="Easy",
    pattern="DP Fundamentals",
    leetcode="https://leetcode.com/problems/fibonacci-number/",
    entry="fib",
    description=r"""
The Fibonacci sequence starts with `F(0) = 0` and `F(1) = 1`; every later term is the sum of the
two terms before it, so `F(n) = F(n-1) + F(n-2)` for `n >= 2`.

Given `n`, return `F(n)`.

**Constraints**

- `0 <= n <= 30`

**Example 1:** `n = 2` → `1` (0, 1, **1**)

**Example 2:** `n = 4` → `3` (0, 1, 1, 2, **3**)

**Example 3:** `n = 0` → `0`
""",
    starter='''class Solution:
    def fib(self, n: int) -> int:
        pass
''',
    solution='''class Solution:
    def fib(self, n):
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        return a
''',
    tests=[[2], [4], [0], [1], [3], [5], [10], [15], [20], [25], [29], [30]],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def fib(self, n):
        if n <= 2:
            return 1
        return self.fib(n - 1) + self.fib(n - 2)
''',
        '''class Solution:
    def fib(self, n):
        a, b = 0, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return b
''',
    ],
    guide=dict(
        prereqs="Basic recursion. Read the lesson *From recursion to dynamic programming* first — this problem is its running example.",
        intuition=r"""
The definition *is* the algorithm: `F(n) = F(n-1) + F(n-2)`. The only question is how many times
you recompute the same values. The naive recursion recomputes `F(n-2)` inside both branches, and the
waste compounds exponentially. If you instead compute the sequence **left to right** you only ever
need the last two numbers.
""",
        hints=[
            "Write the recursive definition directly. How many calls does `fib(30)` make?",
            "Each value `F(k)` only depends on `F(k-1)` and `F(k-2)`. Store results so each is computed once.",
            "You only need the previous two values: keep two variables `a, b` and slide them forward `n` times.",
        ],
        brute_force=r"""
```python
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
```
The call tree has roughly $\varphi^n$ nodes ($\varphi \approx 1.618$), so `fib(30)` makes about
2.7 million calls. Correct, but exponential: **O(φⁿ)** time, O(n) recursion depth.
""",
        approach=r"""
**State:** `F(i)` = the i-th Fibonacci number.
**Recurrence:** `F(i) = F(i-1) + F(i-2)`.
**Base cases:** `F(0) = 0`, `F(1) = 1`.
**Order:** increasing `i`.
**Answer:** `F(n)`.

Because each state looks back only two steps, keep a sliding window `(a, b) = (F(i), F(i+1))`:

| step | a | b |
|---|---|---|
| start | 0 | 1 |
| 1 | 1 | 1 |
| 2 | 1 | 2 |
| 3 | 2 | 3 |
| 4 | 3 | 5 |

After `n` steps `a = F(n)`. For `n = 4` the answer is `3`.

Top-down alternative: decorate the naive recursion with `@functools.cache`; each `n` is evaluated once.
""",
        complexity="Time O(n) — one addition per step. Space O(1) for the two-variable version (O(n) for memoization or a full table).",
        pitfalls=r"""
- Base cases: `F(0) = 0`, not 1. Off-by-one errors in the loop count are the classic bug.
- Using `if n <= 2: return 1` silently breaks `n = 0`.
- Memoizing with a mutable default argument (`memo={}`) shares state between calls — prefer `functools.cache`.
""",
        follow_up="Matrix exponentiation computes F(n) in O(log n) multiplications using [[1,1],[1,0]]ⁿ. Also try Climbing Stairs, which is the same recurrence in disguise.",
    ),
),
dict(
    id="n-th-tribonacci-number",
    title="N-th Tribonacci Number",
    difficulty="Easy",
    pattern="DP Fundamentals",
    leetcode="https://leetcode.com/problems/n-th-tribonacci-number/",
    entry="tribonacci",
    description=r"""
The Tribonacci sequence generalises Fibonacci by summing the **three** previous terms:
`T(0) = 0`, `T(1) = 1`, `T(2) = 1`, and `T(n) = T(n-1) + T(n-2) + T(n-3)` for `n >= 3`.

Return `T(n)`.

**Constraints**

- `0 <= n <= 37` (the answer fits in a 32-bit signed integer)

**Example 1:** `n = 4` → `4` (0, 1, 1, 2, **4**)

**Example 2:** `n = 25` → `1389537`
""",
    starter='''class Solution:
    def tribonacci(self, n: int) -> int:
        pass
''',
    solution='''class Solution:
    def tribonacci(self, n):
        a, b, c = 0, 1, 1
        for _ in range(n):
            a, b, c = b, c, a + b + c
        return a
''',
    tests=[[4], [25], [0], [1], [2], [3], [5], [10], [20], [30], [35], [37]],
    examples=2,
    wrong_solutions=[
        '''class Solution:
    def tribonacci(self, n):
        a, b, c = 0, 1, 2
        for _ in range(n):
            a, b, c = b, c, a + b + c
        return a
''',
        '''class Solution:
    def tribonacci(self, n):
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        return a
''',
    ],
    guide=dict(
        prereqs="Fibonacci Number (same idea, one more term).",
        intuition="Each term depends on a fixed window of the three previous terms, so you can slide a window of three variables forward — the textbook example of space-optimised tabulation.",
        hints=[
            "Write down T(0..5) by hand to make sure you have the base cases right.",
            "A table `t = [0, 1, 1]` extended with `t.append(t[-1] + t[-2] + t[-3])` works.",
            "Only three values are ever needed: rotate `a, b, c = b, c, a + b + c`.",
        ],
        brute_force="Plain recursion `T(n) = T(n-1)+T(n-2)+T(n-3)` branches three ways, roughly O(1.84ⁿ) calls — `n = 37` means billions of calls.",
        approach=r"""
**State:** `T(i)`. **Recurrence:** sum of previous three. **Base:** `T(0)=0, T(1)=1, T(2)=1`.
**Order:** increasing `i`. **Answer:** `T(n)`.

Keep `(a, b, c) = (T(i), T(i+1), T(i+2))`. After `n` rotations, `a = T(n)`.

| i | a | b | c |
|---|---|---|---|
| 0 | 0 | 1 | 1 |
| 1 | 1 | 1 | 2 |
| 2 | 1 | 2 | 4 |
| 3 | 2 | 4 | 7 |
| 4 | 4 | 7 | 13 |
""",
        complexity="Time O(n), space O(1).",
        pitfalls="- `T(2) = 1`, not 2.\n- Returning `c` instead of `a` shifts the answer by two positions.",
        follow_up="Generalise to k-bonacci with a deque of size k and a running sum, giving O(n) regardless of k.",
    ),
),
]
