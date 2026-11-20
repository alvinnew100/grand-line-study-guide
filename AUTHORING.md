# Authoring guide — Grand Line Study Guide

Everything you write goes in `src/<track-id>/`. Never edit `docs/data/` by hand; it is generated.

```
src/<track-id>/
  track.py              # TRACK manifest (modules -> lessons + problem ids)
  lessons/*.md          # one Markdown file per lesson
  problems/*.py         # PROBLEMS = [dict(...), ...]  (any number of files)
  datasets/*.sql        # SQL tracks only: schema + seed data (SQLite dialect)
```

Validate your track (must print `OK`, exit code 0):

```bash
python tools/build.py --track <track-id>
```

## 1. track.py

```python
TRACK = dict(
    id="dsa-arrays",                     # must equal the folder name
    title="DSA I — Arrays to Linked Lists",
    icon="🧭",                           # one emoji
    color="#e4572e",                     # accent colour for cards
    group="Data Structures & Algorithms", # home-page section (given in your brief)
    blurb="One or two sentences shown on the home page.",
    sources=["Goodrich, Data Structures & Algorithms in Python, ch. 5", "NeetCode 150"],
    modules=[
        dict(
            id="arrays-hashing",
            title="Arrays & Hashing",
            summary="One-line summary of the module.",
            lessons=[
                dict(id="hash-maps", title="Hash maps and sets", file="01-hash-maps.md"),
            ],
            problems=["contains-duplicate", "two-sum"],   # shown after the lessons, in order
        ),
    ],
)
```

Lesson ids must be unique within the track; problem ids must be unique across the WHOLE site, so
prefix non-LeetCode problems with the track (e.g. `ml-softmax`, `csapp-twos-complement`).

## 2. Lessons (Markdown)

GitHub-flavoured Markdown, rendered with marked + highlight.js. Write like a great textbook chapter:
motivation → core idea → worked examples → pitfalls → summary → check-yourself quiz.
Target **1,500–4,000 words per lesson**. Paraphrase the source books in your own words; never paste
long passages (short quotes < 15 words, attributed, are fine). Cite the source chapter at the end in a
`> **Source:** ...` line.

Special blocks:

- **Math**: `$inline$` and `$$display$$` (KaTeX). Escape a literal dollar as `\$`.
- **Callouts**: blockquotes starting with `[!NOTE]`, `[!TIP]`, `[!WARNING]`, `[!INTERVIEW]`:
  ```
  > [!TIP]
  > Use a dict when you need O(1) lookup by key.
  ```
- **Diagrams**: a ```` ```mermaid ```` fence (flowchart, sequenceDiagram, classDiagram, graph LR…).
  Keep labels simple (avoid parentheses/quotes inside node labels; use `A["label (x)"]` if needed).
- **Runnable Python** (Pyodide, numpy / pandas / scikit-learn available): ```` ```python-run ````.
  The learner can edit and run it; stdout is shown. Use it generously for demos.
- **Runnable SQL** against a dataset: ```` ```sql-run dataset=shop ```` (dataset = a file in `src/<track>/datasets/`).
- **Quiz**: a ```` ```quiz ```` fence containing a JSON array (strict JSON: double quotes, no trailing commas):
  ```quiz
  [
    {"q": "Average-case lookup in a Python dict?", "options": ["O(1)", "O(log n)", "O(n)"], "answer": 0,
     "explain": "Hashing jumps straight to the bucket; collisions are rare with a good hash and load factor."}
  ]
  ```
  `answer` is the 0-based index of the correct option. Always include `explain`. 4–8 questions per lesson.
- **Interactive widgets** (built in, optional): `<div class="widget" data-widget="bits"></div>`
  (integer/two's-complement/bit explorer), `data-widget="float"` (IEEE-754 float explorer),
  `data-widget="cache"` (direct-mapped/set-associative cache simulator),
  `data-widget="bigo"` (growth-rate plot).

## 3. Code problems (`problems/*.py`)

```python
PROBLEMS = [
dict(
    id="two-sum",                     # LeetCode slug when it is a LeetCode problem
    title="Two Sum",
    difficulty="Easy",                # Easy | Medium | Hard
    pattern="Arrays & Hashing",
    leetcode="https://leetcode.com/problems/two-sum/",      # optional
    neetcode="https://neetcode.io/problems/two-integer-sum", # optional
    kind="function",                  # function (default) | class | sql
    entry="twoSum",                   # method of class Solution, or a top-level function
    compare="unordered",              # exact (default) | unordered | unordered_nested | float
    description=r"""
Write the problem statement IN YOUR OWN WORDS (do not copy LeetCode text).
Include constraints and 1–2 examples in Markdown:

**Example:** `nums = [2,7,11,15], target = 9` → `[0,1]`
""",
    starter='''class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        pass
''',
    solution='''class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, x in enumerate(nums):
            if target - x in seen:
                return [seen[target - x], i]
            seen[x] = i
''',
    tests=[                           # each entry = the list of positional args
        [[2, 7, 11, 15], 9],
        [[3, 2, 4], 6],
        [[3, 3], 6],
        [list(range(10000)), 19997],  # it's real Python: generate big cases
    ],
    examples=2,                       # first N tests are shown as examples (default 3)
    wrong_solutions=[                 # optional but encouraged: must FAIL >= 1 test
        '''class Solution:
    def twoSum(self, nums, target):
        return [0, 1]
''',
    ],
    guide=dict(
        prereqs="Hash maps (see lesson). Markdown.",
        intuition="Markdown: the key insight in plain words.",
        hints=["Hint 1 (gentle)", "Hint 2", "Hint 3 (almost the answer)"],
        brute_force="Markdown: the naive approach and its complexity.",
        approach="Markdown: step-by-step walkthrough of the optimal approach, with a dry run.",
        complexity="Time O(n), space O(n) — and why.",
        pitfalls="Markdown: common bugs / edge cases.",
        follow_up="Optional: variants, related problems.",
    ),
),
]
```

Expected outputs are computed by running `solution` — you never write them. So the reference
solution must be correct. Results are normalised to plain JSON (tuples → lists, numpy → lists).

Spec options:

| key | meaning |
|---|---|
| `arg_types` | per-argument converter: `"list_node"` (list → linked list), `"tree"` (level-order list with `None` → TreeNode), `"graph"` (adjacency list → Node), or `None` |
| `return_type` | `"list_node"` / `"tree"` / `"graph"` to convert the returned object back |
| `compare` | `exact`, `unordered` (order of outer list ignored), `unordered_nested` (outer and inner order ignored), `float` (tolerance `tolerance`, default 1e-6, works on nested lists) |
| `inplace_arg` | index of the argument to compare after the call (for "modify in place, return nothing" problems) |
| `checker` | Python source defining `check(args, got, expected) -> bool` for problems with many valid answers |

`ListNode(val, next)`, `TreeNode(val, left, right)`, `Node(val, neighbors)`, `typing.*`,
`collections`, `heapq`, `bisect`, `itertools`, `functools`, `math` are pre-imported for learners.

**Design problems** (`kind="class"`, LeetCode style): `entry` is the class name and each test is
`[ops, args]`, e.g. `[["MinStack","push","push","getMin","pop","top"], [[],[-2],[0],[],[],[]]]`.
Output is the list of return values (`None` for the constructor).

**SQL problems** (`kind="sql"`): `dataset="shop"`, `solution="SELECT ..."` (reference query),
`ordered=True` if row order matters (i.e. the task says ORDER BY). No `tests`/`entry`/`starter` code
logic needed, but still give `starter="-- write your query\nSELECT "`.

Aim for **8–15 tests** per problem including edge cases (empty input, single element, duplicates,
negatives, large input for complexity). Keep each problem's tests under 400 KB of JSON and the
reference run fast (< 1 s total locally).

Numeric/ML problems: numpy is available in the browser; return lists or numpy arrays and use
`compare="float"`. scikit-learn and pandas are available too but load slowly — prefer numpy.

## 4. Quality bar

- Thorough: a learner with no prior exposure should be able to learn the topic from your lessons alone.
- Accurate: double-check facts against the source PDF text and official docs.
- Original wording; cite sources.
- Every lesson ends with a quiz; every module that teaches an algorithmic or coding skill has problems.
