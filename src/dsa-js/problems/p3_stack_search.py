"""DSA in JavaScript: Stack and Binary Search problems."""
import random


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


rng = random.Random(23)
TEMPS = [rng.randint(30, 100) for _ in range(10000)]
SORTED = sorted(rng.sample(range(-10**6, 10**6), 6000))
ROT = SORTED[2000:] + SORTED[:2000]

MIN_STACK_DRIVER = r'''
// --- driver used by the tests (provided, do not change) ---
function runMinStack(ops, args) {
  let st = null;
  const out = [];
  for (let i = 0; i < ops.length; i++) {
    if (ops[i] === "MinStack") { st = new MinStack(); out.push(null); }
    else { const r = st[ops[i]](...args[i]); out.push(r === undefined ? null : r); }
  }
  return out;
}
'''

def ms_ops(seq):
    ops, args = ["MinStack"], [[]]
    for s in seq:
        if isinstance(s, int):
            ops.append("push"); args.append([s])
        else:
            ops.append(s); args.append([])
    return [ops, args]

def ms_random(n, seed):
    r = random.Random(seed); seq = []; size = 0
    for _ in range(n):
        c = r.random()
        if size == 0 or c < 0.45:
            seq.append(r.randint(-1000, 1000)); size += 1
        elif c < 0.65:
            seq.append("pop"); size -= 1
        elif c < 0.8:
            seq.append("top")
        else:
            seq.append("getMin")
    return ms_ops(seq)

PROBLEMS = [
dict(
    id="js-valid-parentheses", title="Valid Parentheses", difficulty="Easy", pattern="Stack",
    leetcode="https://leetcode.com/problems/valid-parentheses/",
    neetcode="https://neetcode.io/problems/validate-parentheses",
    kind="js", entry="isValid",
    description=r"""
The string `s` contains only the characters `( ) [ ] { }`. It is **valid** when every opening bracket is closed
by a bracket of the same type, brackets close in the right order (the most recently opened one first), and no
closing bracket appears without a matching opener. Return `true` or `false`.

- `1 <= s.length <= 10^4`

**Example 1:** `"([{}])"` → `true`

**Example 2:** `"[(])"` → `false`
""",
    starter="function isValid(s) {\n  // your code\n}\n",
    solution=r'''function isValid(s) {
  const match = { ")": "(", "]": "[", "}": "{" };
  const stack = [];
  for (const c of s) {
    if (c === "(" || c === "[" || c === "{") stack.push(c);
    else if (stack.pop() !== match[c]) return false;   // pop() on empty gives undefined
  }
  return stack.length === 0;
}
''',
    tests=[["([{}])"], ["[(])"], ["()"], ["()[]{}"], ["(]"], ["("], [")"], ["(("], ["){"], ["{[]}"], ["([)]"],
           ["(" * 5000 + ")" * 5000], ["(" * 5000 + ")" * 4999 + "]"]],
    examples=2,
    wrong_solutions=[
        "function isValid(s) {\n  const c = {};\n  for (const ch of s) c[ch] = (c[ch] || 0) + 1;\n  return (c['('] || 0) === (c[')'] || 0) && (c['['] || 0) === (c[']'] || 0) && (c['{'] || 0) === (c['}'] || 0);\n}\n",
        "function isValid(s) {\n  const m = { ')': '(', ']': '[', '}': '{' }, st = [];\n  for (const ch of s) {\n    if ('([{'.includes(ch)) st.push(ch);\n    else if (st.length && st.pop() !== m[ch]) return false;\n  }\n  return st.length === 0;\n}\n",
    ],
    guide=G(
        prereqs="Arrays as stacks with `push` and `pop` (lesson *Stacks, queues and deques in JavaScript*); object literals as lookup tables.",
        intuition="The bracket that must close next is always the **most recently opened** one still open. A stack keeps exactly that order: push openers, and each closer must match the top.",
        hints=[
            "Which bracket has to be closed first?",
            "Push every opening bracket onto an array.",
            "For a closer, `pop()` and compare with the expected opener. At the end the stack must be empty.",
        ],
        brute_force="Repeatedly delete `\"()\"`, `\"[]\"` and `\"{}\"` with `replace` until nothing changes: O(n^2) and easy to get subtly wrong.",
        approach="1. `match` maps each closer to its opener.\n2. Push openers. For a closer: `stack.pop() !== match[c]` → `false`.\n3. Return `stack.length === 0`.\n\n**Dry run** `\"[(])\"`: push `[`, push `(`, closer `]` pops `(` → mismatch → `false`.",
        complexity="Time O(n), space O(n).",
        pitfalls="- `[].pop()` returns `undefined` rather than throwing. That is handy here (it never equals an opener), but in other problems it silently hides bugs.\n- Counting brackets ignores order (`\"([)]\"`).\n- Forgetting the final emptiness check accepts `\"((\"`.",
        follow_up="Minimum Remove to Make Valid Parentheses stores **indices** on the stack instead of characters.",
    ),
),
dict(
    id="js-min-stack", title="Min Stack", difficulty="Medium", pattern="Stack",
    leetcode="https://leetcode.com/problems/min-stack/",
    neetcode="https://neetcode.io/problems/minimum-stack",
    kind="js", entry="runMinStack",
    description=r"""
Design a class `MinStack` whose methods all run in **O(1)** time:

- `push(val)` puts `val` on top
- `pop()` removes the top element (returns nothing)
- `top()` returns the top element
- `getMin()` returns the smallest element currently in the stack

`pop`, `top` and `getMin` are only called on a non-empty stack.

**How the tests call your class.** Each test is a pair `[ops, args]` in LeetCode style, for example
`[["MinStack","push","push","getMin","pop","top"], [[],[5],[2],[],[],[]]]`. The provided driver
`runMinStack` creates the object, calls each method with its arguments, and returns the list of results
(`null` for the constructor and for methods that return nothing): `[null,null,null,2,null,5]`.
Leave the driver as it is and fill in the class.
""",
    starter="class MinStack {\n  constructor() {\n    // your fields\n  }\n  push(val) {}\n  pop() {}\n  top() {}\n  getMin() {}\n}\n" + MIN_STACK_DRIVER,
    solution=r'''class MinStack {
  constructor() {
    this.items = [];
    this.mins = [];          // mins[i] = minimum of items[0..i]
  }
  push(val) {
    this.items.push(val);
    const m = this.mins.length ? Math.min(val, this.mins[this.mins.length - 1]) : val;
    this.mins.push(m);
  }
  pop() {
    this.items.pop();
    this.mins.pop();
  }
  top() {
    return this.items[this.items.length - 1];
  }
  getMin() {
    return this.mins[this.mins.length - 1];
  }
}
''' + MIN_STACK_DRIVER,
    tests=[
        [["MinStack", "push", "push", "getMin", "pop", "top"], [[], [5], [2], [], [], []]],
        ms_ops([-2, 0, -3, "getMin", "pop", "top", "getMin"]),
        ms_ops([1, "top", "getMin"]),
        ms_ops([2, 2, 1, 1, "getMin", "pop", "getMin", "pop", "getMin", "pop", "getMin"]),
        ms_ops([0, 1, 0, "getMin", "pop", "getMin"]),
        ms_ops([5, 4, 3, 2, 1, "getMin", "pop", "pop", "getMin", "top"]),
        ms_ops([-1, "pop", 7, "getMin", "top"]),
        ms_ops([2147483647, -2147483648, "getMin", "pop", "getMin"]),
        ms_random(300, 1),
        ms_random(3000, 2),
    ],
    examples=2,
    wrong_solutions=[
        "class MinStack {\n  constructor() { this.a = []; this.min = Infinity; }\n  push(v) { this.a.push(v); this.min = Math.min(this.min, v); }\n  pop() { this.a.pop(); }\n  top() { return this.a[this.a.length - 1]; }\n  getMin() { return this.min; }\n}\n" + MIN_STACK_DRIVER,
        "class MinStack {\n  constructor() { this.a = []; }\n  push(v) { this.a.push(v); }\n  pop() { this.a.shift(); }\n  top() { return this.a[this.a.length - 1]; }\n  getMin() { return Math.min(...this.a); }\n}\n" + MIN_STACK_DRIVER,
    ],
    guide=G(
        prereqs="JavaScript classes with a `constructor` and methods (lesson *Linked lists and trees with classes* covers classes; this problem needs only fields and methods).",
        intuition="The minimum depends on what is **below** each element, and that never changes while the element sits in the stack. So store, next to every element, the minimum of the stack at the moment it was pushed.",
        hints=[
            "One running `min` field breaks after you pop the minimum. Why?",
            "Keep a second array `mins` that grows and shrinks with the main one.",
            "On push, `mins` gets `Math.min(val, previous min)`.",
        ],
        brute_force="Scan the whole array in `getMin`: O(n) per call.",
        approach="1. Two arrays, `items` and `mins`.\n2. `push(val)`: push `val`; push `Math.min(val, top of mins)` (or `val` if empty).\n3. `pop()`: pop both.\n4. `top()` and `getMin()` read the last entries.\n\n**Dry run** push 5, push 2: items `[5,2]`, mins `[5,2]`; getMin 2; pop → mins `[5]`; top 5.",
        complexity="Every operation O(1); space O(n).",
        pitfalls="- A single `min` variable cannot recover the previous minimum after a pop.\n- `arr.at(-1)` reads the last element in modern engines; `arr[arr.length - 1]` works everywhere.\n- Methods that return nothing give `undefined`; the driver turns it into `null` for you.",
        follow_up="Save space by pushing onto `mins` only when `val <= current min`, and popping it only when the popped value equals it.",
    ),
),
dict(
    id="js-evaluate-reverse-polish-notation", title="Evaluate Reverse Polish Notation", difficulty="Medium", pattern="Stack",
    leetcode="https://leetcode.com/problems/evaluate-reverse-polish-notation/",
    neetcode="https://neetcode.io/problems/evaluate-reverse-polish-notation",
    kind="js", entry="evalRPN",
    description=r"""
In **Reverse Polish Notation** (postfix), an operator comes after its two operands: `3 4 +` means `3 + 4`, and
`2 3 4 * +` means `2 + 3 * 4`. You get the tokens as an array of strings. Operators are `+`, `-`, `*` and `/`.
Division between integers **truncates toward zero** (`7 / -2` is `-3`, not `-4`). Return the value of the
expression. Every intermediate result fits in a 32-bit integer and there is no division by zero.

**Example 1:** `["1","2","+","3","*","4","-"]` → `5` (`(1 + 2) * 3 - 4`)

**Example 2:** `["7","-2","/"]` → `-3`
""",
    starter="function evalRPN(tokens) {\n  // your code\n}\n",
    solution=r'''function evalRPN(tokens) {
  const st = [];
  for (const tok of tokens) {
    if (tok === "+" || tok === "-" || tok === "*" || tok === "/") {
      const b = st.pop(), a = st.pop();      // b was pushed last: it is the RIGHT operand
      if (tok === "+") st.push(a + b);
      else if (tok === "-") st.push(a - b);
      else if (tok === "*") st.push(a * b);
      else st.push(Math.trunc(a / b));       // toward zero, unlike Math.floor
    } else {
      st.push(Number(tok));
    }
  }
  return st[0];
}
''',
    tests=[[["1", "2", "+", "3", "*", "4", "-"]], [["7", "-2", "/"]], [["2", "1", "+", "3", "*"]], [["4", "13", "5", "/", "+"]],
           [["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]], [["42"]], [["-7", "2", "/"]],
           [["3", "5", "-"]], [["0", "3", "/"]], [["-6", "3", "/"]], [["100", "200", "+", "2", "/", "5", "*", "7", "+"]]],
    examples=2,
    wrong_solutions=[
        "function evalRPN(tokens) {\n  const st = [];\n  for (const t of tokens) {\n    if ('+-*/'.includes(t) && t.length === 1) {\n      const b = st.pop(), a = st.pop();\n      st.push(t === '+' ? a + b : t === '-' ? a - b : t === '*' ? a * b : Math.floor(a / b));\n    } else st.push(Number(t));\n  }\n  return st[0];\n}\n",
        "function evalRPN(tokens) {\n  const st = [];\n  for (const t of tokens) {\n    if ('+-*/'.includes(t) && t.length === 1) {\n      const a = st.pop(), b = st.pop();\n      st.push(t === '+' ? a + b : t === '-' ? a - b : t === '*' ? a * b : Math.trunc(a / b));\n    } else st.push(Number(t));\n  }\n  return st[0];\n}\n",
        "function evalRPN(tokens) {\n  const st = [];\n  for (const t of tokens) {\n    if ('+-*/'.includes(t) && t.length === 1) {\n      const b = st.pop(), a = st.pop();\n      st.push(t === '+' ? a + b : t === '-' ? a - b : t === '*' ? a * b : a / b);\n    } else st.push(Number(t));\n  }\n  return st[0];\n}\n",
    ],
    guide=G(
        prereqs="Stacks; `Number()` conversion; the difference between `Math.trunc` and `Math.floor` (lesson *Numbers and sorting without surprises*).",
        intuition="Read left to right. Numbers wait on a stack. An operator takes the two most recent numbers, combines them, and pushes the result back. At the end exactly one number remains.",
        hints=[
            "Which two numbers does an operator act on?",
            "Pop twice: the first pop is the **right** operand.",
            "JavaScript `/` gives a fraction. Which `Math` function truncates toward zero?",
        ],
        brute_force="Convert to an expression string and `eval` it: forbidden in interviews, unsafe, and division would still be fractional.",
        approach="1. For each token: operator → `b = pop()`, `a = pop()`, push `a op b`; otherwise push `Number(tok)`.\n2. For `/` push `Math.trunc(a / b)`.\n3. Return the single remaining value.\n\n**Dry run** `[\"4\",\"13\",\"5\",\"/\",\"+\"]`: stack 4, 13, 5; `/` → 13/5 = 2.6 → trunc 2; `+` → 6.",
        complexity="Time O(n), space O(n).",
        pitfalls="- `Math.floor(-3.5)` is `-4` but truncation toward zero needs `-3`: use `Math.trunc` (or `(a / b) | 0`, valid here because results fit in 32 bits).\n- Popping in the wrong order flips `-` and `/`.\n- A token like `\"-11\"` starts with `-` but is a number: compare the whole token, not its first character.",
        follow_up="Basic Calculator problems turn infix into this form with an operator stack (shunting-yard).",
    ),
),
dict(
    id="js-daily-temperatures", title="Daily Temperatures", difficulty="Medium", pattern="Monotonic Stack",
    leetcode="https://leetcode.com/problems/daily-temperatures/",
    neetcode="https://neetcode.io/problems/daily-temperatures",
    kind="js", entry="dailyTemperatures",
    description=r"""
`temperatures[i]` is the temperature on day `i`. For every day, return how many days you have to wait until a
**strictly warmer** day. If no warmer day ever comes, use `0`.

- `1 <= temperatures.length <= 10^5`, `30 <= temperatures[i] <= 100`

**Example 1:** `[30, 38, 30, 36, 35, 40, 28]` → `[1, 4, 1, 2, 1, 0, 0]`

**Example 2:** `[22, 21, 20]` → `[0, 0, 0]`
""",
    starter="function dailyTemperatures(temperatures) {\n  // your code\n}\n",
    solution=r'''function dailyTemperatures(temperatures) {
  const n = temperatures.length;
  const ans = new Array(n).fill(0);
  const stack = [];                  // indices of days still waiting; temps decreasing
  for (let i = 0; i < n; i++) {
    while (stack.length && temperatures[stack[stack.length - 1]] < temperatures[i]) {
      const j = stack.pop();
      ans[j] = i - j;                 // day i is the first warmer day for j
    }
    stack.push(i);
  }
  return ans;
}
''',
    tests=[[[30, 38, 30, 36, 35, 40, 28]], [[22, 21, 20]], [[73, 74, 75, 71, 69, 72, 76, 73]], [[30, 40, 50, 60]],
           [[30, 60, 90]], [[50]], [[50, 50, 50]], [[89, 62, 70, 58, 47, 47, 46, 76, 100, 70]], [[100, 30, 30, 30, 31]],
           [TEMPS], [list(range(100, 50, -1)) * 100]],
    examples=2,
    wrong_solutions=[
        "function dailyTemperatures(t) {\n  const ans = new Array(t.length).fill(0), st = [];\n  for (let i = 0; i < t.length; i++) {\n    while (st.length && t[st[st.length - 1]] <= t[i]) { const j = st.pop(); ans[j] = i - j; }\n    st.push(i);\n  }\n  return ans;\n}\n",
        "function dailyTemperatures(t) {\n  return t.map((x, i) => (i + 1 < t.length && t[i + 1] > x ? 1 : 0));\n}\n",
    ],
    guide=G(
        prereqs="The monotonic stack (lesson *Pattern map I*, and the theory in the Python stack lessons).",
        intuition="Keep the days that are still waiting for a warmer day on a stack. Their temperatures are decreasing from bottom to top (otherwise the warmer one would already have answered the colder one). A new day answers every waiting day that is colder, starting from the top.",
        hints=[
            "Store **indices** on the stack so you can compute the distance.",
            "While today is warmer than the day on top, pop it and record `i - j`.",
            "Days left on the stack at the end keep their default `0`.",
        ],
        brute_force="For each day scan forward until a warmer day: O(n^2) for a strictly decreasing input.",
        approach="1. `ans = new Array(n).fill(0)`, empty stack.\n2. For each `i`: while the top index is colder, pop `j` and set `ans[j] = i - j`.\n3. Push `i`.\n\n**Dry run** `[30,38,30,36]`: push 0; 38 pops 0 (ans 1), push 1; push 2; 36 pops 2 (ans 1), 38 is warmer so stop; push 3.",
        complexity="Time O(n): every index is pushed and popped at most once. Space O(n).",
        pitfalls="- Use **strictly** warmer (`<`), so equal temperatures keep waiting.\n- `new Array(n)` without `.fill(0)` leaves holes that serialise as `null`.",
        follow_up="Next Greater Element, Online Stock Span and Largest Rectangle in Histogram all reuse this stack.",
    ),
),
dict(
    id="js-binary-search", title="Binary Search", difficulty="Easy", pattern="Binary Search",
    leetcode="https://leetcode.com/problems/binary-search/",
    neetcode="https://neetcode.io/problems/binary-search",
    kind="js", entry="search",
    description=r"""
`nums` holds distinct integers sorted in ascending order. Return the index of `target`, or `-1` if it is not
present. Your algorithm must run in O(log n).

**Example 1:** `nums = [-1, 0, 2, 4, 6, 8], target = 4` → `3`

**Example 2:** `nums = [-1, 0, 2, 4, 6, 8], target = 3` → `-1`
""",
    starter="function search(nums, target) {\n  // your code\n}\n",
    solution=r'''function search(nums, target) {
  let lo = 0, hi = nums.length - 1;
  while (lo <= hi) {
    const mid = lo + ((hi - lo) >> 1);    // integer midpoint
    if (nums[mid] === target) return mid;
    if (nums[mid] < target) lo = mid + 1;
    else hi = mid - 1;
  }
  return -1;
}
''',
    tests=[[[-1, 0, 2, 4, 6, 8], 4], [[-1, 0, 2, 4, 6, 8], 3], [[5], 5], [[5], -5], [[1, 3], 3], [[1, 3], 1], [[1, 3], 2],
           [[-9, -5, -2, 0, 3, 8, 12], -9], [[-9, -5, -2, 0, 3, 8, 12], 12], [[-9, -5, -2, 0, 3, 8, 12], 13],
           [SORTED, SORTED[4500]], [SORTED, SORTED[0] - 1]],
    examples=2,
    wrong_solutions=[
        "function search(nums, target) {\n  let lo = 0, hi = nums.length - 1;\n  while (lo < hi) {\n    const mid = (lo + hi) >> 1;\n    if (nums[mid] === target) return mid;\n    if (nums[mid] < target) lo = mid + 1; else hi = mid - 1;\n  }\n  return -1;\n}\n",
        "function search(nums, target) {\n  let lo = 0, hi = nums.length - 1;\n  while (lo <= hi) {\n    const mid = (lo + hi) / 2;\n    if (nums[mid] === target) return mid;\n    if (nums[mid] < target) lo = mid + 1; else hi = mid - 1;\n  }\n  return -1;\n}\n",
    ],
    guide=G(
        prereqs="Integer division in JavaScript: `Math.floor`, `>> 1` (lesson *Numbers and sorting without surprises*).",
        intuition="Look at the middle element. If it is too small, the target can only be to its right; if too big, only to its left. Each look halves the search range.",
        hints=[
            "Keep an inclusive range `[lo, hi]`.",
            "JavaScript `/` returns fractions. How do you get an integer midpoint?",
            "Loop while `lo <= hi`, and move past `mid` each time (`mid + 1` or `mid - 1`).",
        ],
        brute_force="`nums.indexOf(target)`: O(n).",
        approach="1. `lo = 0`, `hi = n - 1`.\n2. While `lo <= hi`: `mid = lo + ((hi - lo) >> 1)`; compare and move one side.\n3. Return `-1` when the range is empty.\n\n**Dry run** target 4 in `[-1,0,2,4,6,8]`: mid 2 (value 2) → lo 3; mid 4 (value 6) → hi 3; mid 3 → found.",
        complexity="Time O(log n), space O(1).",
        pitfalls="- `(lo + hi) / 2` is fractional (2.5): `nums[2.5]` is `undefined`, and the loop misbehaves.\n- `while (lo < hi)` with `hi = mid - 1` misses single-element ranges.\n- `>> 1` works for indices below 2^31; `Math.floor((lo + hi) / 2)` is the safe general form.",
        follow_up="Lower-bound search (first index with `nums[i] >= target`) uses a half-open range `[lo, hi)` and `hi = mid`.",
    ),
),
dict(
    id="js-koko-eating-bananas", title="Koko Eating Bananas", difficulty="Medium", pattern="Binary Search on Answer",
    leetcode="https://leetcode.com/problems/koko-eating-bananas/",
    neetcode="https://neetcode.io/problems/eating-bananas",
    kind="js", entry="minEatingSpeed",
    description=r"""
There are `piles.length` piles of bananas; pile `i` has `piles[i]` bananas. Each hour Koko picks one pile and eats
up to `k` bananas from it (if the pile has fewer, she finishes it and waits for the next hour). Return the
smallest integer speed `k` that lets her finish every pile within `h` hours.

- `1 <= piles.length <= 10^4`, `piles.length <= h <= 10^9`, `1 <= piles[i] <= 10^9`

**Example 1:** `piles = [1, 4, 3, 2], h = 9` → `2`

**Example 2:** `piles = [25, 10, 23, 4], h = 4` → `25`
""",
    starter="function minEatingSpeed(piles, h) {\n  // your code\n}\n",
    solution=r'''function minEatingSpeed(piles, h) {
  let lo = 1, hi = Math.max(...piles);      // speed hi always works
  while (lo < hi) {
    const k = Math.floor((lo + hi) / 2);
    let hours = 0;
    for (const p of piles) hours += Math.ceil(p / k);
    if (hours <= h) hi = k;                 // k works: try slower
    else lo = k + 1;                        // too slow
  }
  return lo;
}
''',
    tests=[[[1, 4, 3, 2], 9], [[25, 10, 23, 4], 4], [[3, 6, 7, 11], 8], [[30, 11, 23, 4, 20], 5], [[30, 11, 23, 4, 20], 6],
           [[1], 1], [[1000000000], 2], [[1000000000, 1000000000], 3], [[312884470], 968709470], [[5, 5, 5], 15],
           [[805306368, 805306368, 805306368], 1000000000], [[i * 37 % 10007 + 1 for i in range(5000)], 10000]],
    examples=2,
    wrong_solutions=[
        "function minEatingSpeed(piles, h) {\n  let lo = 1, hi = Math.max(...piles);\n  while (lo < hi) {\n    const k = Math.floor((lo + hi) / 2);\n    let hours = 0;\n    for (const p of piles) hours += Math.floor(p / k);\n    if (hours <= h) hi = k; else lo = k + 1;\n  }\n  return lo;\n}\n",
        "function minEatingSpeed(piles, h) {\n  const total = piles.reduce((a, b) => a + b, 0);\n  return Math.max(1, Math.ceil(total / h));\n}\n",
    ],
    guide=G(
        prereqs="Binary search on the answer (lesson *Pattern map I*); `Math.ceil`.",
        intuition="If Koko can finish at speed `k`, she can also finish at any faster speed. So the speeds split into \"too slow\" then \"fast enough\", and binary search finds the boundary.",
        hints=[
            "What are the smallest and largest speeds worth trying?",
            "Hours at speed `k` is the sum of `Math.ceil(p / k)`.",
            "Search for the first speed where hours `<= h`, using `lo < hi` and `hi = k`.",
        ],
        brute_force="Try every speed from 1 up to `max(piles)`: up to 10^9 speeds times n piles.",
        approach="1. `lo = 1`, `hi = Math.max(...piles)`.\n2. While `lo < hi`: `k = Math.floor((lo + hi) / 2)`; count hours.\n3. Fits → `hi = k`; otherwise `lo = k + 1`.\n4. Return `lo`.\n\n**Dry run** `[1,4,3,2]`, h 9: range 1..4; k=2 → 1+2+2+1 = 6 ≤ 9 → hi 2; k=1 → 10 > 9 → lo 2 → answer 2.",
        complexity="Time O(n log M) with M = max pile. Space O(1).",
        pitfalls="- `Math.floor(p / k)` under-counts partial hours: use `Math.ceil`.\n- Hours can exceed 2^31 (10^4 piles of 10^9 at speed 1), so do not use `| 0` on them; plain numbers are exact up to 2^53.\n- `Math.max(...piles)` is fine for 10^4 values but can throw `RangeError` for arrays in the hundreds of thousands: use a loop or `reduce` then.",
        follow_up="Capacity to Ship Packages and Split Array Largest Sum use the same \"search the answer\" template.",
    ),
),
dict(
    id="js-search-in-rotated-sorted-array", title="Search in Rotated Sorted Array", difficulty="Medium", pattern="Binary Search",
    leetcode="https://leetcode.com/problems/search-in-rotated-sorted-array/",
    neetcode="https://neetcode.io/problems/find-target-in-rotated-sorted-array",
    kind="js", entry="search",
    description=r"""
A sorted array of **distinct** integers was rotated at an unknown point: `[1,2,3,4,5,6]` might have become
`[4,5,6,1,2,3]`. Given the rotated array `nums` and a `target`, return the index of `target` or `-1`, in
O(log n) time.

**Example 1:** `nums = [3, 4, 5, 6, 1, 2], target = 1` → `4`

**Example 2:** `nums = [3, 5, 6, 0, 1, 2], target = 4` → `-1`
""",
    starter="function search(nums, target) {\n  // your code\n}\n",
    solution=r'''function search(nums, target) {
  let lo = 0, hi = nums.length - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (nums[mid] === target) return mid;
    if (nums[lo] <= nums[mid]) {                       // left half lo..mid is sorted
      if (nums[lo] <= target && target < nums[mid]) hi = mid - 1;
      else lo = mid + 1;
    } else {                                           // right half mid..hi is sorted
      if (nums[mid] < target && target <= nums[hi]) lo = mid + 1;
      else hi = mid - 1;
    }
  }
  return -1;
}
''',
    tests=[[[3, 4, 5, 6, 1, 2], 1], [[3, 5, 6, 0, 1, 2], 4], [[4, 5, 6, 7, 0, 1, 2], 0], [[4, 5, 6, 7, 0, 1, 2], 3], [[1], 0],
           [[1], 1], [[1, 3], 3], [[3, 1], 1], [[5, 1, 3], 5], [[1, 2, 3, 4, 5], 4], [[6, 7, 1, 2, 3, 4, 5], 7],
           [ROT, ROT[100]], [ROT, ROT[4500]], [ROT, 10**6 + 5]],
    examples=2,
    wrong_solutions=[
        "function search(nums, target) {\n  let lo = 0, hi = nums.length - 1;\n  while (lo <= hi) {\n    const mid = (lo + hi) >> 1;\n    if (nums[mid] === target) return mid;\n    if (nums[mid] < target) lo = mid + 1; else hi = mid - 1;\n  }\n  return -1;\n}\n",
        "function search(nums, target) {\n  let lo = 0, hi = nums.length - 1;\n  while (lo <= hi) {\n    const mid = (lo + hi) >> 1;\n    if (nums[mid] === target) return mid;\n    if (nums[lo] < nums[mid]) {\n      if (nums[lo] <= target && target < nums[mid]) hi = mid - 1; else lo = mid + 1;\n    } else {\n      if (nums[mid] < target && target <= nums[hi]) lo = mid + 1; else hi = mid - 1;\n    }\n  }\n  return -1;\n}\n",
    ],
    guide=G(
        prereqs="Classic binary search (*Binary Search* problem) and the rotated-array lesson in the Python binary search track.",
        intuition="Cut the range at `mid`: at least one of the two halves is perfectly sorted. Check whether the target lies inside the sorted half's value range; if it does, search there, otherwise search the other half.",
        hints=[
            "Compare `nums[lo]` with `nums[mid]` to learn which half is sorted.",
            "For a sorted half you can test `nums[lo] <= target < nums[mid]` directly.",
            "Use `<=` in `nums[lo] <= nums[mid]`, so a range of size one or two is handled.",
        ],
        brute_force="`nums.indexOf(target)`: O(n).",
        approach="1. Standard `lo <= hi` loop with `mid`.\n2. If `nums[lo] <= nums[mid]`, the left half is sorted: go left if the target is in `[nums[lo], nums[mid])`, else right.\n3. Otherwise the right half is sorted: go right if the target is in `(nums[mid], nums[hi]]`, else left.\n\n**Dry run** `[3,4,5,6,1,2]`, target 1: mid 2 (5); left sorted 3..5, 1 not inside → lo 3; mid 4 (1) → found.",
        complexity="Time O(log n), space O(1).",
        pitfalls="- Using `<` instead of `<=` when comparing `nums[lo]` and `nums[mid]` breaks when `lo === mid` (`[3, 1]`, target 1).\n- Plain binary search fails because the array is not globally sorted.",
        follow_up="With duplicates (Search in Rotated Sorted Array II) you sometimes cannot tell which half is sorted; shrink with `lo++` and accept O(n) worst case.",
    ),
),
dict(
    id="js-find-minimum-in-rotated-sorted-array", title="Find Minimum in Rotated Sorted Array", difficulty="Medium", pattern="Binary Search",
    leetcode="https://leetcode.com/problems/find-minimum-in-rotated-sorted-array/",
    neetcode="https://neetcode.io/problems/find-minimum-in-rotated-sorted-array",
    kind="js", entry="findMin",
    description=r"""
A sorted array of distinct integers was rotated between 1 and `n` times (rotating `n` times gives the original
array). Return the smallest element in O(log n).

**Example 1:** `[3, 4, 5, 6, 1, 2]` → `1`

**Example 2:** `[4, 5, 0, 1, 2, 3]` → `0`
""",
    starter="function findMin(nums) {\n  // your code\n}\n",
    solution=r'''function findMin(nums) {
  let lo = 0, hi = nums.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (nums[mid] > nums[hi]) lo = mid + 1;   // the drop is to the right of mid
    else hi = mid;                            // mid could be the minimum
  }
  return nums[lo];
}
''',
    tests=[[[3, 4, 5, 6, 1, 2]], [[4, 5, 0, 1, 2, 3]], [[4, 5, 6, 7]], [[1]], [[2, 1]], [[1, 2]], [[5, 1, 2, 3, 4]],
           [[2, 3, 4, 5, 1]], [[11, 13, 15, 17]], [[-3, -2, -1, -10]], [ROT], [SORTED]],
    examples=2,
    wrong_solutions=[
        "function findMin(nums) {\n  let lo = 0, hi = nums.length - 1;\n  while (lo < hi) {\n    const mid = (lo + hi) >> 1;\n    if (nums[mid] > nums[lo]) lo = mid + 1; else hi = mid;\n  }\n  return nums[lo];\n}\n",
        "function findMin(nums) {\n  return nums[0] < nums[nums.length - 1] ? nums[0] : nums[nums.length - 1];\n}\n",
    ],
    guide=G(
        prereqs="Binary search with `lo < hi` and `hi = mid` (the boundary-finding form).",
        intuition="Compare the middle with the **last** element. If the middle is bigger, the drop (and the minimum) must be to its right. Otherwise the stretch from `mid` to the end is sorted, so the minimum is at `mid` or to its left.",
        hints=[
            "The last element is a good reference point. Why?",
            "If `nums[mid] > nums[hi]`, can the minimum be at `mid`?",
            "Use `while (lo < hi)` and `hi = mid` so you never discard the answer.",
        ],
        brute_force="`Math.min(...nums)` or a linear scan: O(n).",
        approach="1. `lo = 0`, `hi = n - 1`.\n2. While `lo < hi`: `mid`; if `nums[mid] > nums[hi]` then `lo = mid + 1` else `hi = mid`.\n3. Return `nums[lo]`.\n\n**Dry run** `[3,4,5,6,1,2]`: mid 2 (5 > 2) → lo 3; mid 4 (1 < 2) → hi 4; mid 3 (6 > 1) → lo 4 → answer 1.",
        complexity="Time O(log n), space O(1).",
        pitfalls="- Comparing with `nums[lo]` instead of `nums[hi]` fails when the array is not rotated at all.\n- `hi = mid - 1` can skip the minimum.",
        follow_up="The index of the minimum is the rotation amount; it lets you run ordinary binary search on either side.",
    ),
),
]
