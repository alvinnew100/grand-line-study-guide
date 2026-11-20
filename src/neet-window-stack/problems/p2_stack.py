import random

R = random.Random(6062026)

LC = "https://leetcode.com/problems/{}/"
NC = "https://neetcode.io/problems/{}"


# ---------- big inputs ----------
def _random_brackets(n, rng):
    """Valid bracket string of length 2n built with a stack."""
    pairs = {"(": ")", "[": "]", "{": "}"}
    out, st = [], []
    opened = 0
    while len(out) < 2 * n:
        if opened < n and (not st or rng.random() < 0.55):
            c = rng.choice("([{")
            st.append(c)
            out.append(c)
            opened += 1
        else:
            out.append(pairs[st.pop()])
    return "".join(out)


_vp_big = _random_brackets(30000, R)
_vp_deep = "(" * 30000 + ")" * 30000
_vp_bad = _vp_big[:-1] + "]" if _vp_big[-1] != "]" else _vp_big[:-1] + ")"


def _minstack_ops(n, rng):
    ops, args = ["MinStack"], [[]]
    size = 0
    for _ in range(n):
        r = rng.random()
        if size == 0 or r < 0.45:
            ops.append("push")
            args.append([rng.randint(-10 ** 6, 10 ** 6)])
            size += 1
        elif r < 0.65:
            ops.append("pop")
            args.append([])
            size -= 1
        elif r < 0.8:
            ops.append("top")
            args.append([])
        else:
            ops.append("getMin")
            args.append([])
    return [ops, args]


def _minstack_desc_then_queries(n):
    ops, args = ["MinStack"], [[]]
    for v in range(n, 0, -1):
        ops.append("push")
        args.append([v])
    for _ in range(n // 2):
        ops += ["getMin", "pop"]
        args += [[], []]
    return [ops, args]


def _rpn_big(n, rng):
    """Postfix expression whose intermediate values stay small (fits 32-bit)."""
    toks = [str(rng.randint(1, 9))]
    for i in range(n):
        toks.append(str(rng.randint(-9, 9) or 1))
        toks.append(rng.choice("+-"))
        if i % 5 == 0:
            toks += [str(rng.choice([2, 3, -2])), "*", str(rng.choice([3, 4, -3, 7])), "/"]
    return toks


_temps_big = [R.randint(30, 100) for _ in range(30000)]
_temps_flat = [70] * 15000 + [71]


def _fleet_big(n, rng):
    target = 10 ** 6
    pos = rng.sample(range(target), n)
    spd = [rng.randint(1, 10 ** 6) for _ in range(n)]
    return [target, pos, spd]


_hist_big = [R.randint(0, 10000) for _ in range(30000)]
_hist_inc = list(range(1, 8001))


def _baseball_big(n, rng):
    ops, size = [], 0
    for _ in range(n):
        r = rng.random()
        if size < 2 or r < 0.5:
            ops.append(str(rng.randint(-1000, 1000)))
            size += 1
        elif r < 0.65:
            ops.append("+")
            size += 1
        elif r < 0.8:
            ops.append("D")
            size += 1
        else:
            ops.append("C")
            size -= 1
    return ops


_nge_nums2 = list(range(10000))
R.shuffle(_nge_nums2)
_nge_nums1 = R.sample(_nge_nums2, 4000)
_nge_desc2 = list(range(10000, 0, -1))
_nge_desc1 = list(range(1, 10001, 2))


def _span_ops(prices):
    return [["StockSpanner"] + ["next"] * len(prices), [[]] + [[p] for p in prices]]


_ast_big = [R.choice([-1, 1]) * R.randint(1, 1000) for _ in range(30000)]
_ast_big2 = [R.randint(1, 1000) for _ in range(15000)] + [-1001] * 2 + [5, -3]


def _calc_big(n, rng):
    """Infix expression; '*' never chains twice so values stay within 32 bits."""
    parts = [str(rng.randint(0, 999))]
    prev = "+"
    for _ in range(n):
        op = rng.choice(["+", "-", "*", "/"] if prev != "*" else ["+", "-", "/"])
        parts.append(rng.choice([op, " " + op + " "]))
        parts.append(str(rng.randint(1, 999) if op == "/" else rng.randint(0, 999)))
        prev = op
    return "".join(parts)


PROBLEMS = [
# ---------------------------------------------------------------- 20
dict(
    id="valid-parentheses",
    title="Valid Parentheses",
    difficulty="Easy",
    pattern="Stack",
    leetcode=LC.format("valid-parentheses"),
    neetcode=NC.format("validate-parentheses"),
    entry="isValid",
    description=r"""
You get a string `s` made only of the six characters `( ) [ ] { }`. Decide whether it is **well formed**:

- every closing bracket closes an opening bracket **of the same kind**,
- brackets close in the reverse order in which they were opened (no crossing like `"([)]"`),
- nothing is left open at the end.

**Constraints**

- `1 <= len(s) <= 10^4` (big tests here go to 6·10^4)

**Example 1:** `s = "()[]{}"` → `True`.

**Example 2:** `s = "(]"` → `False`.

**Example 3:** `s = "([)]"` → `False` (the `[` is closed by `)`).
""",
    starter='''class Solution:
    def isValid(self, s: str) -> bool:
        pass
''',
    solution='''class Solution:
    def isValid(self, s):
        match = {")": "(", "]": "[", "}": "{"}
        st = []
        for ch in s:
            if ch in match:
                if not st or st[-1] != match[ch]:
                    return False
                st.pop()
            else:
                st.append(ch)
        return not st
''',
    tests=[
        ["()"],
        ["()[]{}"],
        ["(]"],
        ["([)]"],
        ["{[]}"],
        ["]"],
        ["(("],
        ["){"],
        ["(([]){})"],
        ["[({})](]"],
        [_vp_big],
        [_vp_deep],
        [_vp_bad],
    ],
    wrong_solutions=[
        '''class Solution:
    def isValid(self, s):
        return all(s.count(a) == s.count(b) for a, b in ["()", "[]", "{}"])
''',
        '''class Solution:
    def isValid(self, s):
        match = {")": "(", "]": "[", "}": "{"}
        st = []
        for ch in s:
            if ch in match:
                if st and st[-1] == match[ch]:
                    st.pop()
                else:
                    return False
            else:
                st.append(ch)
        return True                      # bug: ignores unclosed brackets
''',
    ],
    guide=dict(
        prereqs="The stack ADT (push / pop / top) — lesson *Stacks: the LIFO toolkit*.",
        intuition="""
The most recently opened bracket must be the first one closed — that is **last in, first out**, i.e. a stack.
Push every opener. When a closer arrives, the top of the stack must be its partner; pop it. At the end the
stack must be empty.
""",
        hints=[
            "Which opening bracket must a closing bracket match?",
            "The most recent unmatched opener. Keep openers on a stack.",
            "On a closer: fail if the stack is empty or the top is the wrong kind; otherwise pop. At the end, succeed only if the stack is empty.",
        ],
        brute_force="Repeatedly delete `\"()\"`, `\"[]\"`, `\"{}\"` until nothing changes: each pass is O(n) and there can be n/2 passes → **O(n²)**. Correct, but quadratic on deep nesting like `((((…))))`.",
        approach="""
```
for ch in s:
    if ch is a closer:
        if not st or st[-1] != partner(ch): return False
        st.pop()
    else:
        st.append(ch)
return not st
```

**Dry run** `"{[]}"`: push `{` → push `[` → `]` matches `[`, pop → `}` matches `{`, pop → empty → True.
`"([)]"`: push `(`, push `[`, then `)` sees top `[` → False.
""",
        complexity="Time **O(n)**, space **O(n)** in the worst case (all openers).",
        pitfalls="""
- Counting brackets is not enough — order matters (`"([)]"`).
- Popping from an empty stack (`"]"`) must return False, not crash.
- Forgetting the final emptiness check (`"(("`).
- Odd length can be rejected immediately — a nice early exit.
""",
        follow_up="*Minimum Remove to Make Valid Parentheses* (1249), *Longest Valid Parentheses* (32, Hard: push indices, not characters).",
    ),
),
# ---------------------------------------------------------------- 155
dict(
    id="min-stack",
    title="Min Stack",
    difficulty="Medium",
    pattern="Stack",
    leetcode=LC.format("min-stack"),
    neetcode=NC.format("minimum-stack"),
    kind="class",
    entry="MinStack",
    description=r"""
Design a stack class `MinStack` whose operations all run in **O(1)** time:

- `MinStack()` — create an empty stack.
- `push(val)` — put `val` on top.
- `pop()` — remove the top element (returns nothing).
- `top()` — return the top element.
- `getMin()` — return the smallest element currently in the stack.

`pop`, `top` and `getMin` are only called on a non-empty stack.

**Constraints**

- `-2^31 <= val <= 2^31 - 1`
- up to `3·10^4` calls

**Example:**

```
ops  = ["MinStack","push","push","push","getMin","pop","top","getMin"]
args = [[],        [-2],  [0],   [-3],  [],      [],   [],   []]
out  = [null,      null,  null,  null,  -3,      null, 0,    -2]
```
""",
    starter='''class MinStack:

    def __init__(self):
        pass

    def push(self, val: int) -> None:
        pass

    def pop(self) -> None:
        pass

    def top(self) -> int:
        pass

    def getMin(self) -> int:
        pass
''',
    solution='''class MinStack:
    def __init__(self):
        self.st = []      # pairs (value, min of stack up to here)

    def push(self, val):
        m = val if not self.st or val < self.st[-1][1] else self.st[-1][1]
        self.st.append((val, m))

    def pop(self):
        self.st.pop()

    def top(self):
        return self.st[-1][0]

    def getMin(self):
        return self.st[-1][1]
''',
    tests=[
        [["MinStack", "push", "push", "push", "getMin", "pop", "top", "getMin"], [[], [-2], [0], [-3], [], [], [], []]],
        [["MinStack", "push", "top", "getMin"], [[], [5], [], []]],
        [["MinStack", "push", "push", "push", "getMin", "pop", "getMin", "pop", "getMin"], [[], [1], [1], [2], [], [], [], [], []]],
        [["MinStack", "push", "push", "getMin", "pop", "getMin"], [[], [0], [0], [], [], []]],
        [["MinStack", "push", "push", "push", "pop", "pop", "getMin", "top"], [[], [3], [1], [2], [], [], [], []]],
        [["MinStack", "push", "pop", "push", "getMin"], [[], [-1], [], [7], []]],
        [["MinStack", "push", "push", "getMin", "top", "pop", "getMin"], [[], [2147483647], [-2147483648], [], [], [], []]],
        [["MinStack", "push", "push", "push", "push", "getMin", "pop", "getMin", "pop", "getMin", "pop", "getMin"],
         [[], [5], [3], [3], [4], [], [], [], [], [], [], []]],
        _minstack_ops(200, R),
        _minstack_ops(8000, R),
        _minstack_desc_then_queries(5000),
    ],
    wrong_solutions=[
        '''class MinStack:
    def __init__(self):
        self.st, self.mn = [], None
    def push(self, val):
        self.st.append(val)
        if self.mn is None or val < self.mn:
            self.mn = val
    def pop(self):
        self.st.pop()            # bug: min never restored
    def top(self):
        return self.st[-1]
    def getMin(self):
        return self.mn
''',
        '''class MinStack:
    def __init__(self):
        self.st, self.mins = [], []
    def push(self, val):
        self.st.append(val)
        if not self.mins or val < self.mins[-1]:   # bug: should be <=
            self.mins.append(val)
    def pop(self):
        if self.st.pop() == self.mins[-1]:
            self.mins.pop()
    def top(self):
        return self.st[-1]
    def getMin(self):
        return self.mins[-1]
''',
    ],
    guide=dict(
        prereqs="Stack ADT; the idea of storing *extra state per element*.",
        intuition="""
The minimum of a stack only changes at the top: pushing may lower it, popping may restore an older value.
So remember, **for each element, what the minimum was when it was pushed**. Store pairs
`(value, min_so_far)`; `getMin` is just the second half of the top pair. Popping automatically "rewinds"
the minimum to what it was before.
""",
        hints=[
            "A single `min` variable fails after you pop the current minimum. What would you need to know to restore it?",
            "The min after popping is the min of the stack *below* the popped element — a value you could have recorded at push time.",
            "Push (val, min(val, previous_min)); getMin returns st[-1][1].",
        ],
        brute_force="Keep a plain list and compute `min(self.st)` inside `getMin`: **O(n)** per call, O(n²) for a sequence of queries — the 10⁴-element test below makes this crawl.",
        approach="""
Each stack slot holds `(val, m)` where `m = min(val, m_below)`.

**Dry run** push −2, push 0, push −3:

| stack (bottom → top) | getMin |
|---|---|
| (−2,−2) | −2 |
| (−2,−2) (0,−2) | −2 |
| (−2,−2) (0,−2) (−3,−3) | **−3** |
| pop → (−2,−2) (0,−2) | **−2** |

Variant: two stacks — values and a *min stack* that pushes when `val <= current min` and pops when the popped
value equals the current min. Note the `<=`: duplicates of the minimum must be pushed too.
""",
        complexity="Every operation **O(1)**; space **O(n)**.",
        pitfalls="""
- One global min variable cannot be restored after `pop`.
- In the two-stack variant use `<=`, otherwise pushing the minimum twice and popping once loses it.
- `top()` returns the value, not the pair.
""",
        follow_up="*Max Stack* (716) adds `popMax` — needs a heap or a sorted structure plus lazy deletion. A *min queue* can be built from two min stacks (amortized O(1)).",
    ),
),
# ---------------------------------------------------------------- 150
dict(
    id="evaluate-reverse-polish-notation",
    title="Evaluate Reverse Polish Notation",
    difficulty="Medium",
    pattern="Stack",
    leetcode=LC.format("evaluate-reverse-polish-notation"),
    neetcode=NC.format("evaluate-reverse-polish-notation"),
    entry="evalRPN",
    description=r"""
An arithmetic expression is given in **postfix** (Reverse Polish) notation as a list of string tokens: each
token is an integer or one of `"+"`, `"-"`, `"*"`, `"/"`. An operator applies to the **two values
immediately before it** (left operand first). Return the integer value of the expression.

- Division between two integers **truncates toward zero** (`-7 / 2 = -3`, not `-4`).
- The input is always a valid expression; there is no division by zero; all intermediate results fit in 32 bits.

**Constraints**

- `1 <= len(tokens) <= 10^4` (big tests go somewhat further)

**Example 1:** `["2","1","+","3","*"]` → `9` (= (2 + 1) · 3).

**Example 2:** `["4","13","5","/","+"]` → `6` (= 4 + 13 / 5).
""",
    starter='''class Solution:
    def evalRPN(self, tokens: List[str]) -> int:
        pass
''',
    solution='''class Solution:
    def evalRPN(self, tokens):
        st = []
        for t in tokens:
            if t in ("+", "-", "*", "/"):
                b = st.pop()
                a = st.pop()
                if t == "+":
                    st.append(a + b)
                elif t == "-":
                    st.append(a - b)
                elif t == "*":
                    st.append(a * b)
                else:
                    st.append(int(a / b) if abs(a) < 2 ** 52 else (abs(a) // abs(b)) * (1 if (a < 0) == (b < 0) else -1))
            else:
                st.append(int(t))
        return st[-1]
''',
    tests=[
        [["2", "1", "+", "3", "*"]],
        [["4", "13", "5", "/", "+"]],
        [["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]],
        [["-7", "2", "/"]],
        [["7", "-2", "/"]],
        [["5"]],
        [["-42"]],
        [["3", "-4", "+"]],
        [["2", "3", "-"]],
        [["0", "3", "/"]],
        [["1", "2", "+", "3", "4", "+", "*", "5", "-"]],
        [_rpn_big(4000, R)],
        [["1"] + ["1", "+"] * 15000],
    ],
    wrong_solutions=[
        '''class Solution:
    def evalRPN(self, tokens):
        st = []
        for t in tokens:
            if t in "+-*/" and len(t) == 1:
                b, a = st.pop(), st.pop()
                st.append({"+": a + b, "-": a - b, "*": a * b, "/": a // b if b else 0}[t])  # floor, not truncation
            else:
                st.append(int(t))
        return st[-1]
''',
        '''class Solution:
    def evalRPN(self, tokens):
        st = []
        for t in tokens:
            if t in ("+", "-", "*", "/"):
                a, b = st.pop(), st.pop()      # operands swapped
                if t == "+": st.append(a + b)
                elif t == "-": st.append(a - b)
                elif t == "*": st.append(a * b)
                else: st.append(int(a / b))
            else:
                st.append(int(t))
        return st[-1]
''',
    ],
    guide=dict(
        prereqs="Stacks; Python integer division semantics.",
        intuition="""
In postfix notation an operator always consumes the **most recent** two values — exactly what a stack gives
you. Numbers are pushed; an operator pops two, combines them, and pushes the result. When the tokens run out,
the single value left is the answer.
""",
        hints=[
            "When you see an operator, where are its operands?",
            "They are the last two values produced. Pop b first, then a, and push a op b.",
            "Python's // floors (−7 // 2 == −4). For truncation toward zero use int(a / b) (fine for 32-bit ints) or math.trunc.",
        ],
        brute_force="Repeatedly scan for the first operator, replace `a b op` by its value, and rebuild the list: **O(n²)**. The stack does it in one pass.",
        approach="""
**Dry run** `["4","13","5","/","+"]`:

| token | stack after |
|---|---|
| 4 | [4] |
| 13 | [4, 13] |
| 5 | [4, 13, 5] |
| / | [4, 2] (13 / 5 → 2) |
| + | [6] |
""",
        complexity="Time **O(n)**, space **O(n)**.",
        pitfalls="""
- **Operand order**: for `-` and `/` the *second* pop is the left operand.
- **Floor vs truncation**: `-7 // 2 == -4` in Python but the task wants `-3`.
- Negative numbers like `"-11"` are operands, not operators — check `t in {"+","-","*","/"}`, not `t[0]`.
""",
        follow_up="Converting infix to postfix is Dijkstra's **shunting-yard** algorithm (two stacks). *Basic Calculator II* in this module evaluates infix directly.",
    ),
),
# ---------------------------------------------------------------- 22
dict(
    id="generate-parentheses",
    title="Generate Parentheses",
    difficulty="Medium",
    pattern="Stack",
    leetcode=LC.format("generate-parentheses"),
    neetcode=NC.format("generate-parentheses"),
    entry="generateParenthesis",
    compare="unordered",
    description=r"""
Given `n`, return **every** string of `n` pairs of round brackets that is well formed (every prefix has at least
as many `(` as `)`, and the totals are equal). The order of the list does not matter.

**Constraints**

- `1 <= n <= 8`

**Example 1:** `n = 3` → `["((()))","(()())","(())()","()(())","()()()"]`.

**Example 2:** `n = 1` → `["()"]`.
""",
    starter='''class Solution:
    def generateParenthesis(self, n: int) -> List[str]:
        pass
''',
    solution='''class Solution:
    def generateParenthesis(self, n):
        out, path = [], []

        def go(opened, closed):
            if closed == n:
                out.append("".join(path))
                return
            if opened < n:
                path.append("(")
                go(opened + 1, closed)
                path.pop()
            if closed < opened:
                path.append(")")
                go(opened, closed + 1)
                path.pop()

        go(0, 0)
        return out
''',
    tests=[[1], [2], [3], [4], [5], [6], [7], [8]],
    examples=3,
    wrong_solutions=[
        '''class Solution:
    def generateParenthesis(self, n):
        from itertools import permutations
        return sorted(set("".join(p) for p in permutations("(" * n + ")" * n))) if n < 5 else []
''',
        '''class Solution:
    def generateParenthesis(self, n):
        res = {"()"}
        for _ in range(n - 1):
            res = {"(" + s + ")" for s in res} | {"()" + s for s in res}   # misses (())(()) style
        return list(res)
''',
    ],
    guide=dict(
        prereqs="Recursion / backtracking; the 'balance' view of parentheses from *Valid Parentheses*.",
        intuition="""
Build the string left to right. At each step you have at most two choices, and you can tell immediately
whether each keeps the prefix **extendable** to a valid string:

- add `(` if you have not used all `n` openers,
- add `)` if there is an unmatched opener (`closed < opened`).

Never making an invalid move means every leaf of the recursion is a valid answer — no filtering needed.
The "stack" here is implicit: `opened - closed` is the height of the stack you would have in *Valid Parentheses*.
""",
        hints=[
            "Try generating strings character by character. When is adding '(' allowed? When is ')' allowed?",
            "'(' is allowed while opened < n; ')' is allowed while closed < opened.",
            "Backtrack with a shared list `path`: append, recurse, pop. Record the string when closed == n.",
        ],
        brute_force="Generate all $2^{2n}$ strings of brackets and keep the valid ones: **O(2^{2n} · n)** — 65 536 × 16 for n = 8, plus the validity check of each.",
        approach="""
**Dry run** `n = 2` (state = path, opened, closed):

```
"" (0,0)
└─ "(" (1,0)
   ├─ "((" (2,0) ── "(()" (2,1) ── "(())" ✓
   └─ "()" (1,1) ── "()(" (2,1) ── "()()" ✓
```
""",
        complexity="The number of answers is the Catalan number $C_n = \\frac{1}{n+1}\\binom{2n}{n} \\approx \\frac{4^n}{n^{3/2}\\sqrt\\pi}$; each costs O(n) to build, so time **O(n · C_n)** and output space the same; recursion depth O(n).",
        pitfalls="""
- Allowing `)` when `closed == opened` produces invalid prefixes.
- Building new strings at every level (`s + "("`) is fine for n ≤ 8, but a shared list with `pop()` is cleaner.
- Generating permutations of `"((()))"` repeats work enormously and still needs filtering.
""",
        follow_up="*Remove Invalid Parentheses* (301) — BFS/backtracking over deletions. Counting the answers (`C_n`) is a classic DP.",
    ),
),
# ---------------------------------------------------------------- 739
dict(
    id="daily-temperatures",
    title="Daily Temperatures",
    difficulty="Medium",
    pattern="Monotonic Stack",
    leetcode=LC.format("daily-temperatures"),
    neetcode=NC.format("daily-temperatures"),
    entry="dailyTemperatures",
    description=r"""
`temperatures[i]` is the temperature on day `i`. For every day, report how many days you must wait until a
**strictly warmer** day. If no warmer day ever comes, report `0` for that day.

**Constraints**

- `1 <= len(temperatures) <= 10^5`
- `30 <= temperatures[i] <= 100`

**Example 1:** `[73,74,75,71,69,72,76,73]` → `[1,1,4,2,1,1,0,0]`.

**Example 2:** `[30,60,90]` → `[1,1,0]`.
""",
    starter='''class Solution:
    def dailyTemperatures(self, temperatures: List[int]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def dailyTemperatures(self, temperatures):
        ans = [0] * len(temperatures)
        st = []                       # indices, temperatures non-increasing
        for i, t in enumerate(temperatures):
            while st and temperatures[st[-1]] < t:
                j = st.pop()
                ans[j] = i - j
            st.append(i)
        return ans
''',
    tests=[
        [[73, 74, 75, 71, 69, 72, 76, 73]],
        [[30, 40, 50, 60]],
        [[30, 60, 90]],
        [[90, 60, 30]],
        [[50]],
        [[70, 70, 70, 71]],
        [[55, 38, 53, 81, 61, 93, 97, 32, 43, 78]],
        [[89, 62, 70, 58, 47, 47, 46, 76, 100, 70]],
        [[100, 30, 100]],
        [_temps_big],
        [_temps_flat],
    ],
    wrong_solutions=[
        '''class Solution:
    def dailyTemperatures(self, temperatures):
        ans = [0] * len(temperatures)
        st = []
        for i, t in enumerate(temperatures):
            while st and temperatures[st[-1]] <= t:     # bug: equal is not warmer
                j = st.pop()
                ans[j] = i - j
            st.append(i)
        return ans
''',
        '''class Solution:
    def dailyTemperatures(self, temperatures):
        n = len(temperatures)
        return [1 if i + 1 < n and temperatures[i + 1] > temperatures[i] else 0 for i in range(n)]
''',
    ],
    guide=dict(
        prereqs="Stacks; the *monotonic stack* lesson (next-greater-element template).",
        intuition="""
Each day is a question waiting for an answer: "when is it warmer than me?". Keep the **unanswered** days on a
stack. Their temperatures are non-increasing from bottom to top (otherwise the lower one would have been
answered). When today's temperature beats the top of the stack, today is the answer for that day — pop it,
and keep popping while today beats the new top.
""",
        hints=[
            "Scanning forward from every day is O(n²). Can one day answer many earlier days at once?",
            "Keep indices of days still waiting for a warmer day. Which ones does a new warm day resolve?",
            "Monotonic stack of indices: while temps[stack top] < today, pop j and set ans[j] = i - j. Then push i.",
        ],
        brute_force="For each `i`, scan `j = i+1, i+2, …` until warmer: **O(n²)** worst case (e.g. a long flat stretch). The 15 000-day flat test makes this ~10⁸ steps.",
        approach="""
**Dry run** `[73,74,75,71,69,72,76,73]` (stack shows indices:temp):

| i | t | pops (ans) | stack after |
|---|---|---|---|
| 0 | 73 | | 0:73 |
| 1 | 74 | 0 → 1 | 1:74 |
| 2 | 75 | 1 → 1 | 2:75 |
| 3 | 71 | | 2:75 3:71 |
| 4 | 69 | | 2:75 3:71 4:69 |
| 5 | 72 | 4 → 1, 3 → 2 | 2:75 5:72 |
| 6 | 76 | 5 → 1, 2 → 4 | 6:76 |
| 7 | 73 | | 6:76 7:73 |

Days left on the stack keep the default `0`.
""",
        complexity="Time **O(n)** amortized — each index is pushed once and popped at most once. Space **O(n)**.",
        pitfalls="""
- *Strictly* warmer: pop on `<`, not `<=`.
- Store **indices** so you can compute distances.
- Initialise the answer with zeros so unresolved days are correct automatically.
""",
        follow_up="Because temperatures are in 30..100 there is also an O(n·71) backward scan with a `next[temp]` table. *Next Greater Element II* (503) adds circularity — loop twice.",
    ),
),
# ---------------------------------------------------------------- 853
dict(
    id="car-fleet",
    title="Car Fleet",
    difficulty="Medium",
    pattern="Monotonic Stack",
    leetcode=LC.format("car-fleet"),
    neetcode=NC.format("car-fleet"),
    entry="carFleet",
    description=r"""
`n` cars drive along a one-lane road toward mile `target`. Car `i` starts at `position[i]` (all distinct, all
less than `target`) and drives at constant `speed[i]`.

A car can never pass another one. If it catches up with a slower car ahead, it slows down and they continue
together as a **fleet** (a fleet moves at the speed of its slowest — i.e. front — car). A car that catches up
exactly at `target` still joins that fleet. A single car is also a fleet.

Return how many fleets arrive at `target`.

**Constraints**

- `1 <= n <= 10^5`
- `0 < target <= 10^6`, `0 <= position[i] < target`, `0 < speed[i] <= 10^6`

**Example 1:** `target = 12, position = [10,8,0,5,3], speed = [2,4,1,1,3]` → `3`.

**Example 2:** `target = 100, position = [0,2,4], speed = [4,2,1]` → `1`.
""",
    starter='''class Solution:
    def carFleet(self, target: int, position: List[int], speed: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def carFleet(self, target, position, speed):
        cars = sorted(zip(position, speed), reverse=True)   # closest to target first
        fleets = 0
        lead_d, lead_s = None, None    # remaining distance / speed of the current front fleet
        for p, s in cars:
            d = target - p
            # this car arrives later than the fleet ahead  <=>  d / s > lead_d / lead_s
            if lead_d is None or d * lead_s > lead_d * s:
                fleets += 1
                lead_d, lead_s = d, s
        return fleets
''',
    tests=[
        [12, [10, 8, 0, 5, 3], [2, 4, 1, 1, 3]],
        [10, [3], [3]],
        [100, [0, 2, 4], [4, 2, 1]],
        [10, [6, 8], [3, 2]],
        [10, [0, 4, 2], [2, 1, 3]],
        [10, [8, 3, 7, 4, 6, 5], [4, 4, 4, 4, 4, 4]],
        [10, [5, 0], [1, 2]],
        [20, [6, 2, 17], [3, 9, 2]],
        [13, [10, 2, 5, 7, 4, 6, 11], [7, 5, 10, 5, 9, 4, 1]],
        [1000000, [0, 999999], [1000000, 1]],
        _fleet_big(10000, R),
        [10 ** 6, list(range(0, 10000)), [1] * 10000],
    ],
    wrong_solutions=[
        '''class Solution:
    def carFleet(self, target, position, speed):
        return len(set((target - p) / s for p, s in zip(position, speed)))
''',
        '''class Solution:
    def carFleet(self, target, position, speed):
        cars = sorted(zip(position, speed))            # bug: processes from the back of the road
        st = []
        for p, s in cars:
            t = (target - p) / s
            if not st or t > st[-1]:
                st.append(t)
        return len(st)
''',
    ],
    guide=dict(
        prereqs="Sorting with tuples; monotonic stack reasoning.",
        intuition="""
Look at the cars **from the one closest to the target backwards**. Compute each car's arrival time *if it were
alone*: `(target - p) / s`. A car behind can only be slowed down by the fleet directly in front. If its solo time
is ≤ that fleet's time, it catches up and merges (it adopts the fleet's time). If its time is larger, it can
never catch up — it starts a new fleet, and becomes the new blocker for the cars behind it.

So the fleet times, scanned from the front, form a **strictly increasing** sequence — a monotonic stack where
we only need the top.
""",
        hints=[
            "Which car can possibly block a given car? Only cars ahead of it. Sort by position.",
            "Process from the car nearest the target. Compare each car's solo arrival time with the time of the fleet directly ahead.",
            "If time <= fleet ahead's time, it merges; otherwise it forms a new fleet whose time becomes the new reference. Count new fleets.",
        ],
        brute_force="Simulate time step by step (or event by event, merging cars): with real-valued meeting times this needs O(n²) pairwise catch-up checks and careful floating point.",
        approach="""
**Dry run** `target = 12`, cars (pos, speed) sorted by position descending: (10,2) (8,4) (5,1) (3,3) (0,1)

| car | time = (12−p)/s | fleet-ahead time | result |
|---|---|---|---|
| (10,2) | 1 | — | new fleet (1) |
| (8,4) | 1 | 1 | merges |
| (5,1) | 7 | 1 | new fleet (7) |
| (3,3) | 3 | 7 | merges |
| (0,1) | 12 | 7 | new fleet (12) |

3 fleets. The reference compares `d1/s1 > d2/s2` as `d1·s2 > d2·s1` to stay in exact integer arithmetic.
""",
        complexity="Time **O(n log n)** for the sort, then O(n). Space **O(n)** for the sorted pairs.",
        pitfalls="""
- Scanning from the back of the road: a slow car at the back says nothing about the cars in front.
- Counting distinct arrival times ignores who blocks whom.
- A car that catches the fleet *exactly* at the target merges — use `>` for "new fleet", not `>=`.
- Floating-point equality: cross-multiplying avoids surprises.
""",
        follow_up="*Car Fleet II* (1776) asks for each car's collision time — a genuine monotonic stack where you pop cars that would have already merged.",
    ),
),
# ---------------------------------------------------------------- 84
dict(
    id="largest-rectangle-in-histogram",
    title="Largest Rectangle in Histogram",
    difficulty="Hard",
    pattern="Monotonic Stack",
    leetcode=LC.format("largest-rectangle-in-histogram"),
    neetcode=NC.format("largest-rectangle-in-histogram"),
    entry="largestRectangleArea",
    description=r"""
`heights[i]` is the height of the `i`-th bar of a histogram; every bar has width 1 and they stand side by side.
Return the area of the largest axis-aligned rectangle that fits entirely inside the histogram.

**Constraints**

- `1 <= len(heights) <= 10^5`
- `0 <= heights[i] <= 10^4`

**Example 1:** `heights = [2,1,5,6,2,3]` → `10` (bars 5 and 6, height 5, width 2).

**Example 2:** `heights = [2,4]` → `4`.
""",
    starter='''class Solution:
    def largestRectangleArea(self, heights: List[int]) -> int:
        pass
''',
    solution='''class Solution:
    def largestRectangleArea(self, heights):
        st = []          # indices with increasing heights
        best = 0
        for i, h in enumerate(heights + [0]):
            start = i
            while st and heights[st[-1]] >= h:
                j = st.pop()
                left = st[-1] + 1 if st else 0
                area = heights[j] * (i - left)
                if area > best:
                    best = area
            st.append(i)
        return best
''',
    tests=[
        [[2, 1, 5, 6, 2, 3]],
        [[2, 4]],
        [[1]],
        [[0]],
        [[2, 2, 2]],
        [[6, 2, 5, 4, 5, 1, 6]],
        [[1, 2, 3, 4, 5]],
        [[5, 4, 3, 2, 1]],
        [[2, 1, 2]],
        [[4, 2, 0, 3, 2, 5]],
        [[0, 0, 0]],
        [[3, 6, 5, 7, 4, 8, 1, 0]],
        [_hist_big],
        [_hist_inc],
    ],
    wrong_solutions=[
        '''class Solution:
    def largestRectangleArea(self, heights):
        best = 0
        for i, h in enumerate(heights):
            j = i
            while j < len(heights) and heights[j] >= h:   # only extends to the right
                j += 1
            best = max(best, h * (j - i))
        return best
''',
        '''class Solution:
    def largestRectangleArea(self, heights):
        st, best = [], 0
        for i, h in enumerate(heights):                # bug: no sentinel, stack never flushed
            while st and heights[st[-1]] >= h:
                j = st.pop()
                left = st[-1] + 1 if st else 0
                best = max(best, heights[j] * (i - left))
            st.append(i)
        return best
''',
    ],
    guide=dict(
        prereqs="Monotonic stack (previous / next smaller element). *Daily Temperatures* first.",
        intuition="""
In the best rectangle, some bar `j` is the **shortest** one, and the rectangle stretches left and right until it
hits a bar shorter than `heights[j]`. So for every bar we need its **previous smaller** and **next smaller**
neighbours: area = `heights[j] × (next_smaller − prev_smaller − 1)`.

An increasing stack gives both at once: when bar `i` is shorter than the top `j`, `i` is `j`'s next-smaller,
and the element *below* `j` on the stack is `j`'s previous-smaller. Pop, compute the area, repeat. A sentinel
bar of height 0 at the end flushes everything left on the stack.
""",
        hints=[
            "Fix the bar that limits the height of the rectangle. How wide can the rectangle be?",
            "It extends to the nearest strictly lower bar on each side. That's the previous/next smaller element problem.",
            "Keep an increasing stack of indices. When height[i] < height[top], pop top: its width is i - (new top) - 1. Append a 0-height sentinel to flush the stack.",
        ],
        brute_force="For every pair `(i, j)` track the minimum height between them: **O(n²)**. The strictly increasing 8 000-bar test (≈3·10⁷ steps) shows the difference.",
        approach="""
**Dry run** `[2,1,5,6,2,3]` + sentinel `0` (stack shows `index:height`):

| i | h | popped → area | stack after |
|---|---|---|---|
| 0 | 2 | | 0:2 |
| 1 | 1 | 0:2 → 2×1 = 2 | 1:1 |
| 2 | 5 | | 1:1 2:5 |
| 3 | 6 | | 1:1 2:5 3:6 |
| 4 | 2 | 3:6 → 6×1 = 6; 2:5 → 5×2 = **10** | 1:1 4:2 |
| 5 | 3 | | 1:1 4:2 5:3 |
| 6 | 0 | 5:3 → 3; 4:2 → 2×4 = 8; 1:1 → 1×6 = 6 | 6:0 |

For a popped index `j`, width = `i − (st[-1] + 1)` where `st[-1]` is the new top (or `−1` if the stack is empty).
""",
        complexity="Time **O(n)** amortized (each index pushed and popped once). Space **O(n)**.",
        pitfalls="""
- Forgetting the final flush (sentinel) misses rectangles that reach the right edge — e.g. `[1,2,3,4,5]`.
- Width after popping uses the **new** top, not the popped index.
- Equal heights: popping on `>=` is fine; the last of the equal bars computes the full width.
""",
        follow_up="*Maximal Rectangle* (85) runs this per row of a 0/1 matrix. *Trapping Rain Water* (42) also has a monotonic-stack solution.",
    ),
),
# ---------------------------------------------------------------- 682
dict(
    id="baseball-game",
    title="Baseball Game",
    difficulty="Easy",
    pattern="Stack",
    leetcode=LC.format("baseball-game"),
    entry="calPoints",
    description=r"""
You keep score for a game with strange rules. The record starts empty, and you process a list of string
`operations`:

- an integer `x` — record a new score `x`;
- `"+"` — record the **sum of the previous two** scores;
- `"D"` — record **double the previous** score;
- `"C"` — delete the previous score from the record.

Operations are always valid (enough previous scores exist). Return the sum of all scores left in the record.

**Constraints**

- `1 <= len(operations) <= 1000` (big tests go further)
- integer scores are in `[-3·10^4, 3·10^4]`

**Example 1:** `["5","2","C","D","+"]` → `30` (record ends as `[5, 10, 15]`).

**Example 2:** `["1","C"]` → `0`.
""",
    starter='''class Solution:
    def calPoints(self, operations: List[str]) -> int:
        pass
''',
    solution='''class Solution:
    def calPoints(self, operations):
        st = []
        for op in operations:
            if op == "+":
                st.append(st[-1] + st[-2])
            elif op == "D":
                st.append(2 * st[-1])
            elif op == "C":
                st.pop()
            else:
                st.append(int(op))
        return sum(st)
''',
    tests=[
        [["5", "2", "C", "D", "+"]],
        [["5", "-2", "4", "C", "D", "9", "+", "+"]],
        [["1", "C"]],
        [["7"]],
        [["-3", "D"]],
        [["1", "2", "+", "+", "+"]],
        [["3", "D", "D", "C", "+"]],
        [["0", "0", "+"]],
        [["10", "-10", "+", "D", "C", "C"]],
        [_baseball_big(20000, R)],
    ],
    wrong_solutions=[
        '''class Solution:
    def calPoints(self, operations):
        st = []
        for op in operations:
            if op == "+":
                st.append(st[-1] + st[-2])
            elif op == "D":
                st.append(2 * st[-1])
            elif op == "C":
                st.pop()
            elif op.isdigit():           # bug: negative numbers are dropped
                st.append(int(op))
        return sum(st)
''',
    ],
    guide=dict(
        prereqs="Stack push / pop / peek.",
        intuition="Every rule refers only to the *most recent* scores, and `C` undoes the most recent one — a stack is the natural record.",
        hints=[
            "Which scores does each operation look at?",
            "Only the last one or two — the top of a stack.",
            "Push ints; '+' pushes st[-1]+st[-2]; 'D' pushes 2*st[-1]; 'C' pops. Return sum(st).",
        ],
        brute_force="There is no meaningful slower method — the stack *is* the simulation. (Recomputing the sum after every step would be O(n²).)",
        approach="**Dry run** `[\"5\",\"2\",\"C\",\"D\",\"+\"]`: [5] → [5,2] → [5] → [5,10] → [5,10,15] → sum 30.",
        complexity="Time **O(n)**, space **O(n)**.",
        pitfalls="- `\"-2\".isdigit()` is False — parse with `int()` in an `else` branch.\n- `C` after `+` removes only the `+` result, not its inputs.",
        follow_up="A running total can be kept alongside the stack to answer 'current sum' queries in O(1).",
    ),
),
# ---------------------------------------------------------------- 496
dict(
    id="next-greater-element-i",
    title="Next Greater Element I",
    difficulty="Easy",
    pattern="Monotonic Stack",
    leetcode=LC.format("next-greater-element-i"),
    entry="nextGreaterElement",
    description=r"""
You are given two lists of **distinct** integers, `nums1` and `nums2`, where every value of `nums1` also appears
in `nums2`.

For each `x` in `nums1`, find `x`'s position in `nums2` and look to its right: the answer is the **first value
greater than `x`** you meet, or `-1` if there is none. Return the answers in the order of `nums1`.

**Constraints**

- `1 <= len(nums1) <= len(nums2) <= 1000` (big tests go to 10^4)
- values are distinct, `0 <= value <= 10^4` in LeetCode (bigger here)

**Example 1:** `nums1 = [4,1,2], nums2 = [1,3,4,2]` → `[-1,3,-1]`.

**Example 2:** `nums1 = [2,4], nums2 = [1,2,3,4]` → `[3,-1]`.
""",
    starter='''class Solution:
    def nextGreaterElement(self, nums1: List[int], nums2: List[int]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def nextGreaterElement(self, nums1, nums2):
        nxt = {}
        st = []
        for x in nums2:
            while st and st[-1] < x:
                nxt[st.pop()] = x
            st.append(x)
        return [nxt.get(x, -1) for x in nums1]
''',
    tests=[
        [[4, 1, 2], [1, 3, 4, 2]],
        [[2, 4], [1, 2, 3, 4]],
        [[1], [1]],
        [[3, 1, 5, 7, 9, 2, 6], [1, 2, 3, 5, 6, 7, 9, 11]],
        [[1, 3, 5, 2, 4], [6, 5, 4, 3, 2, 1, 7]],
        [[5], [5, 4, 3]],
        [[2, 1], [2, 1, 3]],
        [[4], [4, 1, 2, 5]],
        [_nge_nums1, _nge_nums2],
        [_nge_desc1, _nge_desc2],
    ],
    wrong_solutions=[
        '''class Solution:
    def nextGreaterElement(self, nums1, nums2):
        pos = {x: i for i, x in enumerate(nums2)}
        out = []
        for x in nums1:
            i = pos[x]
            out.append(nums2[i + 1] if i + 1 < len(nums2) else -1)   # next element, not next greater
        return out
''',
        '''class Solution:
    def nextGreaterElement(self, nums1, nums2):
        out = []
        for x in nums1:
            bigger = [y for y in nums2 if y > x]
            out.append(min(bigger) if bigger else -1)   # smallest greater anywhere
        return out
''',
    ],
    guide=dict(
        prereqs="Monotonic stack lesson; dicts.",
        intuition="Precompute the next-greater value for **every** element of `nums2` with a decreasing stack, store it in a dict, then answer `nums1` by lookup.",
        hints=[
            "Solve the problem for every element of nums2 at once, then just look up nums1's values.",
            "Values waiting for a greater element sit on a stack in decreasing order.",
            "For x in nums2: while stack top < x, nxt[pop()] = x; push x. Answer with nxt.get(v, -1).",
        ],
        brute_force="For each `x` in `nums1`, find it in `nums2` and scan right: **O(|nums1| · |nums2|)** — 4·10⁷ for the big test.",
        approach="""
**Dry run** `nums2 = [1,3,4,2]`: push 1; 3 pops 1 (nxt[1]=3), push 3; 4 pops 3 (nxt[3]=4), push 4; push 2.
Left on stack: 4, 2 → no greater. `nums1 = [4,1,2]` → `[-1, 3, -1]`.
""",
        complexity="Time **O(|nums1| + |nums2|)**, space **O(|nums2|)**.",
        pitfalls="- 'Next greater' means first greater to the **right**, not the next element nor the smallest greater value.\n- Values are distinct, so a value-keyed dict is safe.",
        follow_up="*Next Greater Element II* (503, circular array: iterate 2n indices) and *Daily Temperatures* (distances instead of values).",
    ),
),
# ---------------------------------------------------------------- 901
dict(
    id="online-stock-span",
    title="Online Stock Span",
    difficulty="Medium",
    pattern="Monotonic Stack",
    leetcode=LC.format("online-stock-span"),
    kind="class",
    entry="StockSpanner",
    description=r"""
Design a class `StockSpanner` that receives daily stock prices one at a time.

- `StockSpanner()` — initialise.
- `next(price)` — record today's price and return today's **span**: the number of consecutive days, ending
  with today and going backwards, on which the price was **less than or equal to** today's price.

**Constraints**

- `1 <= price <= 10^5`
- up to `10^4` calls (big tests go further)

**Example:**

```
ops  = ["StockSpanner","next","next","next","next","next","next","next"]
args = [[],            [100], [80],  [60],  [70],  [60],  [75],  [85]]
out  = [null,          1,     1,     1,     2,     1,     4,     6]
```
""",
    starter='''class StockSpanner:

    def __init__(self):
        pass

    def next(self, price: int) -> int:
        pass
''',
    solution='''class StockSpanner:
    def __init__(self):
        self.st = []          # (price, span) with strictly decreasing prices

    def next(self, price):
        span = 1
        while self.st and self.st[-1][0] <= price:
            span += self.st.pop()[1]
        self.st.append((price, span))
        return span
''',
    tests=[
        _span_ops([100, 80, 60, 70, 60, 75, 85]),
        _span_ops([1]),
        _span_ops([5, 5, 5, 5]),
        _span_ops([1, 2, 3, 4, 5]),
        _span_ops([5, 4, 3, 2, 1]),
        _span_ops([31, 41, 48, 59, 79]),
        _span_ops([28, 14, 28, 35, 46, 53, 66, 80, 87, 88]),
        _span_ops([10, 1, 1, 1, 10, 1, 11]),
        _span_ops([R.randint(1, 100000) for _ in range(8000)]),
        _span_ops(list(range(1, 8001))),
    ],
    wrong_solutions=[
        '''class StockSpanner:
    def __init__(self):
        self.prev = None
        self.span = 0
    def next(self, price):
        if self.prev is not None and self.prev <= price:   # only compares with yesterday
            self.span += 1
        else:
            self.span = 1
        self.prev = price
        return self.span
''',
        '''class StockSpanner:
    def __init__(self):
        self.st = []
    def next(self, price):
        span = 1
        while self.st and self.st[-1][0] < price:    # bug: equal prices count too
            span += self.st.pop()[1]
        self.st.append((price, span))
        return span
''',
    ],
    guide=dict(
        prereqs="Monotonic stack; *Daily Temperatures* (this is its mirror image, online).",
        intuition="""
The span asks for the *previous strictly greater* price. Keep a stack of `(price, span)` with strictly
decreasing prices. A new price swallows every stack entry `<=` it — and since each swallowed entry already
knows how many days *it* covered, we just add their spans. The swallowed days can never matter again: today's
price is at least as large and more recent.
""",
        hints=[
            "Counting backwards day by day is O(n) per call. Can earlier work be reused?",
            "If yesterday's price <= today's, then everything yesterday covered is also covered today.",
            "Stack of (price, span). Pop while top price <= price, adding popped spans to 1; push (price, total).",
        ],
        brute_force="Store all prices and walk backwards each call: **O(n)** per call, O(n²) total — 10⁸ steps on the 8 000 increasing prices test.",
        approach="""
**Dry run** prices 100, 80, 60, 70, 60, 75, 85:

| price | popped | span | stack after |
|---|---|---|---|
| 100 | | 1 | (100,1) |
| 80 | | 1 | (100,1)(80,1) |
| 60 | | 1 | …(60,1) |
| 70 | (60,1) | 2 | (100,1)(80,1)(70,2) |
| 60 | | 1 | …(70,2)(60,1) |
| 75 | (60,1)(70,2) | 4 | (100,1)(80,1)(75,4) |
| 85 | (75,4)(80,1) | 6 | (100,1)(85,6) |
""",
        complexity="Each price is pushed once and popped at most once: **O(1) amortized** per call, O(n) space.",
        pitfalls="- The span includes days with **equal** price: pop on `<=`.\n- Comparing only with the previous day misses longer runs.",
        follow_up="Same 'merge with the previous block' trick appears in *Sum of Subarray Minimums* (907).",
    ),
),
# ---------------------------------------------------------------- 735
dict(
    id="asteroid-collision",
    title="Asteroid Collision",
    difficulty="Medium",
    pattern="Stack",
    leetcode=LC.format("asteroid-collision"),
    entry="asteroidCollision",
    description=r"""
A row of asteroids is given as non-zero integers: the absolute value is the size, the sign is the direction
(positive = moving right, negative = moving left). All move at the same speed.

When two asteroids meet, the smaller one explodes; if they are the same size, both explode. Asteroids moving in
the same direction never meet. Return the state of the row after all collisions, left to right.

**Constraints**

- `2 <= len(asteroids) <= 10^4` (big tests go further)
- `-1000 <= asteroids[i] <= 1000`, `asteroids[i] != 0`

**Example 1:** `[5,10,-5]` → `[5,10]` (`10` destroys `-5`).

**Example 2:** `[8,-8]` → `[]`.

**Example 3:** `[10,2,-5]` → `[10]` (`-5` destroys `2`, then `10` destroys `-5`).
""",
    starter='''class Solution:
    def asteroidCollision(self, asteroids: List[int]) -> List[int]:
        pass
''',
    solution='''class Solution:
    def asteroidCollision(self, asteroids):
        st = []
        for a in asteroids:
            alive = True
            while alive and a < 0 and st and st[-1] > 0:
                if st[-1] < -a:
                    st.pop()
                    continue
                if st[-1] == -a:
                    st.pop()
                alive = False
            if alive:
                st.append(a)
        return st
''',
    tests=[
        [[5, 10, -5]],
        [[8, -8]],
        [[10, 2, -5]],
        [[-2, -1, 1, 2]],
        [[1, -2, -2, -2]],
        [[-2, 1, -1, -2]],
        [[1, -1, -2, 2]],
        [[3, 5, -6, 2, -1, 4]],
        [[-5, 5]],
        [[1, 2, 3, -10]],
        [[10, -1, -2, -3]],
        [_ast_big],
        [_ast_big2],
    ],
    wrong_solutions=[
        '''class Solution:
    def asteroidCollision(self, asteroids):
        st = []
        for a in asteroids:
            if a < 0 and st and st[-1] > 0:      # bug: only one collision per asteroid
                if st[-1] < -a:
                    st.pop(); st.append(a)
                elif st[-1] == -a:
                    st.pop()
            else:
                st.append(a)
        return st
''',
        '''class Solution:
    def asteroidCollision(self, asteroids):
        st = []
        for a in asteroids:
            alive = True
            while alive and st and (st[-1] > 0) != (a > 0):   # bug: [-, +] pairs never meet
                if abs(st[-1]) < abs(a):
                    st.pop(); continue
                if abs(st[-1]) == abs(a):
                    st.pop()
                alive = False
            if alive:
                st.append(a)
        return st
''',
    ],
    guide=dict(
        prereqs="Stacks; careful case analysis.",
        intuition="""
Process asteroids left to right and keep the survivors on a stack. The only collision possible is a new
**left-mover** (`a < 0`) hitting a **right-mover** on top of the stack. It keeps smashing right-movers smaller
than itself, dies with an equal one, or dies against a bigger one. Everything else (left-mover with nothing
in front, right-movers) is simply pushed.
""",
        hints=[
            "Which pairs can collide? Note that a left-mover on the left and a right-mover on the right drift apart.",
            "Only (top > 0, new < 0) collides. The survivors so far form a stack.",
            "Loop while new < 0 and top > 0: pop smaller tops; on equal pop and stop; on bigger top stop. Push the new one if it survived.",
        ],
        brute_force="Repeatedly scan for an adjacent `(+, −)` pair and resolve it until none remain: **O(n²)** worst case.",
        approach="""
**Dry run** `[10, 2, -5]`: push 10, push 2; −5 meets 2 → 2 explodes; −5 meets 10 → −5 explodes. Result `[10]`.

`[-2, -1, 1, 2]`: nothing ever collides (left-movers first, right-movers after) → unchanged.
""",
        complexity="Time **O(n)** amortized — each asteroid is pushed and popped at most once. Space **O(n)**.",
        pitfalls="""
- `[-2, 2]`-style pairs never collide: only `top > 0` and `a < 0`.
- One left-mover can destroy many right-movers — use a `while`.
- Equal sizes destroy both: pop *and* do not push.
""",
        follow_up="Same 'process an element against the stack until stable' idea: *Remove All Adjacent Duplicates in String II* (1209).",
    ),
),
# ---------------------------------------------------------------- 394
dict(
    id="decode-string",
    title="Decode String",
    difficulty="Medium",
    pattern="Stack",
    leetcode=LC.format("decode-string"),
    entry="decodeString",
    description=r"""
An encoded string uses the rule `k[body]`, meaning `body` repeated exactly `k` times (`k` is a positive integer,
possibly with several digits). Bodies may themselves contain encoded parts. Return the fully decoded string.

The input is always valid: brackets are balanced, digits appear only as repeat counts, and the plain text is
lowercase letters.

**Constraints**

- `1 <= len(s) <= 30`, `1 <= k <= 300` in LeetCode; the decoded output is at most `10^5` characters.

**Example 1:** `"3[a]2[bc]"` → `"aaabcbc"`.

**Example 2:** `"3[a2[c]]"` → `"accaccacc"`.

**Example 3:** `"2[abc]3[cd]ef"` → `"abcabccdcdcdef"`.
""",
    starter='''class Solution:
    def decodeString(self, s: str) -> str:
        pass
''',
    solution='''class Solution:
    def decodeString(self, s):
        st = []              # (text before '[', repeat count)
        cur, num = [], 0
        for ch in s:
            if ch.isdigit():
                num = num * 10 + int(ch)
            elif ch == "[":
                st.append((cur, num))
                cur, num = [], 0
            elif ch == "]":
                prev, k = st.pop()
                prev.append("".join(cur) * k)
                cur = prev
            else:
                cur.append(ch)
        return "".join(cur)
''',
    tests=[
        ["3[a]2[bc]"],
        ["3[a2[c]]"],
        ["2[abc]3[cd]ef"],
        ["abc"],
        ["10[a]"],
        ["2[2[2[b]]]"],
        ["3[z]2[2[y]pq4[2[jk]e1[f]]]ef"],
        ["leet1[code]"],
        ["100[leetcode]"],
        ["a2[b3[c]]d"],
        ["300[ab]x"],
        ["5[4[3[2[10[ab]]]]]"],
        ["2[" * 10 + "x" + "]" * 10 + "y"],
    ],
    wrong_solutions=[
        '''class Solution:
    def decodeString(self, s):
        st, cur = [], ""
        for i, ch in enumerate(s):
            if ch == "[":
                st.append((cur[:-1], int(cur[-1])))   # bug: single-digit counts only
                cur = ""
            elif ch == "]":
                prev, k = st.pop()
                cur = prev + cur * k
            else:
                cur += ch
        return cur
''',
        '''class Solution:
    def decodeString(self, s):
        import re
        m = re.fullmatch(r"(\\d+)\\[([a-z]*)\\](.*)", s)   # bug: no nesting support
        if not m:
            return s
        return m.group(2) * int(m.group(1)) + self.decodeString(m.group(3))
''',
    ],
    guide=dict(
        prereqs="Stacks; parsing multi-digit numbers (`num = num*10 + d`).",
        intuition="""
`[` opens a new, nested context; `]` closes it and pastes the repeated result into the *enclosing* context.
Nesting + "resume where you were" = stack. On `[`, push the text built so far and the pending repeat count, then
start fresh. On `]`, pop them, and set `current = saved_text + current * k`.
""",
        hints=[
            "What must you remember when you dive into a '[' so you can continue afterwards?",
            "The text built before the '[' and the number in front of it. Push both.",
            "Accumulate digits into num; on '[' push (cur, num) and reset; on ']' pop (prev, k) and set cur = prev + cur*k; letters append to cur.",
        ],
        brute_force="Repeatedly find an innermost `k[letters]` with a regex and replace it by its expansion: each replacement rebuilds the string, so **O(output × nesting)**. Fine for small inputs but wasteful.",
        approach="""
**Dry run** `"3[a2[c]]"`:

| ch | action | stack | cur |
|---|---|---|---|
| 3 | num=3 | | "" |
| [ | push ("",3) | ("",3) | "" |
| a | | | "a" |
| 2 | num=2 | | "a" |
| [ | push ("a",2) | ("",3) ("a",2) | "" |
| c | | | "c" |
| ] | pop ("a",2) | ("",3) | "a"+"cc" = "acc" |
| ] | pop ("",3) | | "accaccacc" |
""",
        complexity="Time **O(output length)** (each output character is produced a bounded number of times by the joins — O(output × depth) in the worst case). Space O(output).",
        pitfalls="""
- Multi-digit counts: `"10[a]"`, `"100[leetcode]"`.
- Text *after* a closing bracket (`"2[a]bc"`) must be appended to the outer context.
- Repeated string concatenation in deep nesting can be slow — build lists and join.
""",
        follow_up="Recursive-descent parsing is the alternative: a function that parses until the matching `]` and returns `(string, next_index)`.",
    ),
),
# ---------------------------------------------------------------- 227
dict(
    id="basic-calculator-ii",
    title="Basic Calculator II",
    difficulty="Medium",
    pattern="Stack",
    leetcode=LC.format("basic-calculator-ii"),
    entry="calculate",
    description=r"""
Evaluate an arithmetic expression string `s` containing non-negative integers, the operators `+ - * /`, and
spaces. Use normal precedence (`*` and `/` before `+` and `-`, left to right within a level). Integer division
**truncates toward zero**. Do not use `eval`.

The expression is always valid; all intermediate results fit in a signed 32-bit integer. There are no
parentheses and no unary minus.

**Constraints**

- `1 <= len(s) <= 3·10^5`

**Example 1:** `"3+2*2"` → `7`.

**Example 2:** `" 3/2 "` → `1`.

**Example 3:** `" 3+5 / 2 "` → `5`.
""",
    starter='''class Solution:
    def calculate(self, s: str) -> int:
        pass
''',
    solution='''class Solution:
    def calculate(self, s):
        st = []
        num = 0
        op = "+"
        n = len(s)
        for i, ch in enumerate(s):
            if ch.isdigit():
                num = num * 10 + (ord(ch) - 48)
            if (not ch.isdigit() and ch != " ") or i == n - 1:
                if op == "+":
                    st.append(num)
                elif op == "-":
                    st.append(-num)
                elif op == "*":
                    st.append(st.pop() * num)
                else:
                    t = st.pop()
                    st.append(-(-t // num) if t < 0 else t // num)
                op = ch
                num = 0
        return sum(st)
''',
    tests=[
        ["3+2*2"],
        [" 3/2 "],
        [" 3+5 / 2 "],
        ["42"],
        ["1-1"],
        ["14-3/2"],
        ["0*7"],
        ["1+2*3-4/2"],
        ["2*3*4"],
        ["100/10/3"],
        ["1 - 2 * 3"],
        ["1-7/2"],
        [_calc_big(15000, R)],
    ],
    wrong_solutions=[
        '''class Solution:
    def calculate(self, s):
        st, num, op = [], 0, "+"
        s = s.replace(" ", "") + "+"
        for ch in s:
            if ch.isdigit():
                num = num * 10 + int(ch)
                continue
            if op == "+": st.append(num)
            elif op == "-": st.append(-num)
            elif op == "*": st.append(st.pop() * num)
            else: st.append(st.pop() // num)       # floor division bug
            op, num = ch, 0
        return sum(st)
''',
        '''class Solution:
    def calculate(self, s):
        s = s.replace(" ", "")
        total, num, op = 0, 0, "+"
        for ch in s + "+":                          # left-to-right, ignores precedence
            if ch.isdigit():
                num = num * 10 + int(ch)
                continue
            if op == "+": total += num
            elif op == "-": total -= num
            elif op == "*": total *= num
            else: total = int(total / num)
            op, num = ch, 0
        return total
''',
    ],
    guide=dict(
        prereqs="Stacks; parsing digits; truncating division.",
        intuition="""
Think of the expression as a **sum of terms**, where each term is a chain of `*` and `/`. Push each term's
value onto a stack with its sign (`+num` or `-num`). When a `*` or `/` arrives, it binds to the *previous* term,
so pop it, combine, and push back. At the end, add everything up.

The key implementation trick: remember the **previous operator**; act on it when the *next* operator (or the end
of the string) shows that the current number is complete.
""",
        hints=[
            "Addition and subtraction can be delayed; multiplication and division cannot.",
            "Push +num / -num for + and -; for * and / combine with the stack's top immediately.",
            "Keep `op` = the operator before the current number. When you hit a new operator or the end, apply `op` to num, then set op = this char. Truncate toward zero for negative tops.",
        ],
        brute_force="Two passes over a token list: first collapse every `*`/`/` (deleting from a Python list is O(n) each → **O(n²)**), then sum. The stack makes it one O(n) pass.",
        approach="""
**Dry run** `"14-3/2"`:

| ch | num | prev op | action | stack |
|---|---|---|---|---|
| 1,4 | 14 | + | | |
| - | | + | push 14 | [14] |
| 3 | 3 | - | | |
| / | | - | push −3 | [14, −3] |
| 2 (end) | 2 | / | pop −3, push trunc(−3/2) = −1 | [14, −1] |

Sum → **13**. (Floor division would give −2 and a wrong 12.)
""",
        complexity="Time **O(n)**, space **O(n)** (O(1) possible by keeping just the last term instead of a stack).",
        pitfalls="""
- Spaces: skip them, but still handle the last number at `i == n-1` even if it is followed by spaces.
- **Truncation toward zero** for negative terms (`"14-3/2"`).
- Multi-digit numbers.
- Do not reset `op` on spaces.
""",
        follow_up="*Basic Calculator* (224, parentheses and unary minus: push the sign context on `(`) and *Basic Calculator III* (772, everything).",
    ),
),
]
