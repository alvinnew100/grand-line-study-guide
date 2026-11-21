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
  Inside quiz JSON strings write it as `\\$` (JSON needs the backslash doubled), or put the code in
  backticks: two bare dollars in one quiz string (`{$set: ...}`, `$uri $args`, `$5 and $10`) are
  rendered as broken math. Quiz explanations only appear after answering, so check them by reading.
- **Callouts**: blockquotes starting with `[!NOTE]`, `[!TIP]`, `[!WARNING]`, `[!INTERVIEW]`:
  ```
  > [!TIP]
  > Use a dict when you need O(1) lookup by key.
  ```
- **Diagrams**: a ```` ```mermaid ```` fence (flowchart, sequenceDiagram, classDiagram, graph LR…).
  Keep labels simple (avoid parentheses/quotes inside node labels; use `A["label (x)"]` if needed).
- **Runnable Python** (Pyodide, numpy / pandas / scikit-learn available): ```` ```python-run ````.
  The learner can edit and run it; stdout is shown. Use it generously for demos.
  Charts and FastAPI apps work too; see "Charts and FastAPI demos" below.
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

### Charts and FastAPI demos

**Charts in `python-run`.** Import matplotlib and draw as usual; end with `plt.show()` (optional).
After the run every open figure is saved as a PNG, shown below the text output, and closed, so the
next run starts clean. The backend is Agg (set for you; do not call `matplotlib.use`).

```python-run
import numpy as np
import matplotlib.pyplot as plt
x = np.random.default_rng(1).normal(size=500)
plt.hist(x, bins=30, color="#1f5f8b", edgecolor="white")
plt.xlabel("value"); plt.ylabel("count")
plt.show()
```

- matplotlib is Pyodide's 3.5.2: check that an API existed in 3.5 before using it. Up to 8 figures per run.
- Seaborn (`import seaborn as sns`, 0.13.2) and Plotly (`import plotly.express as px` or
  `plotly.graph_objects`, 6.0.1) are installed from PyPI on first use. Plotly figures appear as
  interactive charts in a sandboxed frame when you call `fig.show()` or leave the figure as the last
  expression (up to 4 per run); Plotly.js 3.0.1 loads from cdn.jsdelivr.net inside that frame.
- First use downloads the libraries and shows "Loading plotting library…": about 8 MB for
  matplotlib on top of numpy, about 4.5 MB more for seaborn (pandas), about 15 MB for Plotly (plus
  pandas for Plotly Express). Prefer
  matplotlib; use Plotly only when interactivity (hover, zoom) teaches something.
- Keep figures modest (`figsize` up to about (10, 4)); wide figures scroll sideways on phones. Pick
  colours that survive colour blindness (blue/orange, not red/green) and label both axes.
- The judge never loads plotting libraries; never import them in problems.

**FastAPI apps: ```` ```fastapi-run ````.** The block must define a FastAPI instance named `app`. Run
executes it in the browser and keeps the app alive; a request panel below the code (method, path with
query string, body, headers) sends requests to it and shows status, headers and the body, including
422 validation errors and 500s (the traceback is printed in the output pane). The panel lists the app's
routes as buttons (WebSocket routes as `WS`) and pre-fills the body from the OpenAPI schema. Optional
info-string options set the panel's starting request: `method=` (GET, POST, PUT, PATCH, DELETE or `WS`),
`path=`, and `body=form` or `body=file` (default JSON):

````
```fastapi-run method=POST path=/items/
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

app = FastAPI()

@app.post("/items/", status_code=201)
def create_item(item: Item):
    return item

client = TestClient(app)                       # example requests, printed when the block runs
r = client.post("/items/", json={"name": "Saw", "price": "abc"})
print(r.status_code, r.json())
```
````

- End the block with example requests through `fastapi.testclient.TestClient`, exactly as in a real
  test: `client.get`, `client.post(json=...)`, forms with `data={...}`, uploads with
  `files={"file": ("a.csv", b"...", "text/csv")}`, `with client.stream("GET", ...) as r:`,
  `with TestClient(app) as client:` (runs lifespan startup/shutdown) and
  `with client.websocket_connect("/ws") as ws:` with `ws.send_text / receive_text / send_json /
  receive_json / close`. In the browser it is a thread-free stand-in with the same interface (see
  "How it runs" below). Middleware, background tasks, `StreamingResponse` and task groups all work.
  `asyncio.sleep` inside the app finishes **instantly** under the TestClient (it runs on a virtual
  clock), so do not print timings from TestClient calls; use the panel to show real timing.
- A test that would wait forever (for example `ws.receive_text()` when the handler is itself waiting
  for a message) raises a `RuntimeError` saying so, where the real TestClient would hang.
- Sync `def` endpoints and dependencies run inline (Pyodide has no threads), so `time.sleep` blocks the
  page; keep handlers fast. No network, databases or files outside memory: use a dict as the "database".
- A `python-run` block that imports fastapi also gets these packages and the same `TestClient`, but no
  request panel.

*Request panel modes.*

- **JSON / Form fields / File upload.** For POST, PUT, PATCH and DELETE a body switch appears. Form
  fields are name / value rows sent as `application/x-www-form-urlencoded`; File upload adds a file
  picker (field name editable, several files allowed when the parameter is `list[UploadFile]`) and
  sends `multipart/form-data`. The browser reads the chosen file (up to 5 MB) and hands the bytes to the
  app in the page; nothing is uploaded anywhere. Clicking a route whose OpenAPI body is a form or
  multipart switches the mode and fills the rows (file fields from `format: binary`).
- **Streaming.** When the app sends its body in several ASGI messages (`StreamingResponse`, SSE), the
  panel lists each chunk as it arrives, stamped with the time the app sent it (`+0.50 s`), and the
  Send button becomes **Stop** (it cancels the request like a closed tab, so generator `finally`
  blocks run). A one-chunk body (for example JSON passed through `@app.middleware`) is shown normally.
  Limits: 2,000 chunks or 2 MB, then the panel stops the stream; a stream that is silent for 15 s
  times out. Image responses are shown as images; other binary bodies as a byte count.
- **WebSocket** (`method=WS`, or click a `WS` route). Connect opens the socket, a log shows messages
  (→ sent, ← received, • status such as close codes or a refused handshake), a text box sends text
  frames, Close sends a 1000 close. The handler's prints go to the output pane. An open socket has no
  time limit; running the code again, or leaving the page, closes it. Text frames only from the panel
  (binary frames the app sends are shown as a hex preview).

*How it runs.* Two drivers, both on Pyodide's single thread, in `docs/assets/judge/worker.js`:

- The **panel** awaits the app on Pyodide's own event loop (real time) and calls it with raw ASGI
  messages: a request's `http.response.body` messages are forwarded to the page one by one, which is
  what makes chunks appear live (`httpx.ASGITransport` collects the whole body first, so it is only
  used to encode the request). WebSockets use an in-process driver: `websocket.connect` /
  `websocket.receive` / `websocket.disconnect` go in through a queue, `websocket.accept` / `send` /
  `close` come out as log entries.
- The **TestClient** runs the app on `VirtualLoop`, a private asyncio loop whose clock jumps straight
  to the next timer instead of waiting, driven to completion from sync code (`run_until_complete`
  with the page's loop set aside). WebSocket sessions keep their app task on that loop between calls.

*Packages.* Installed on first use (about 3.2 MB), and preloaded in the background as soon as a lesson
containing a `fastapi-run` block (or a `python-run` block importing fastapi) is opened: the wheels
fastapi 0.115.6, starlette 0.41.3, httpx 0.28.1, httpcore 1.0.7, anyio 4.7.0, sniffio 1.3.1,
h11 0.14.0 and python-multipart 0.0.20 (0.5 MB) are fetched in parallel straight from
files.pythonhosted.org with sha256 integrity checks (no micropip, no index lookups), while Pyodide's
pydantic 2.7.0 / pydantic-core 2.18.1, typing-extensions, idna, certifi and ssl (2.7 MB) load from
the Pyodide CDN. To bump a wheel, update the `WHEELS` list in worker.js (path and sha256 from
`https://pypi.org/pypi/<name>/<version>/json`), bump its `?v=` stamp in app.js, and update this list.

*Measured cold-load cost* (live site, empty browser cache, fast connection, 2026-11-21): the site opens
in 0.8 s (352 KB); the first Python demo of a visit takes about 2.2 s (Pyodide, 5.4 MB), re-runs about
0.35 s; the first matplotlib chart about 7 to 9 s (numpy + matplotlib, about 8 to 14 MB), re-runs about
0.55 s; the first FastAPI app about 3 s (about 4 MB). Slow mobile connections scale with the download
size, so use charts where they teach something, not as decoration.

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

## 5. JavaScript and HTML/CSS (web tracks)

Lesson blocks:

- **Runnable JavaScript**: a ```` ```js-run ```` fence. Runs in a Web Worker; `console.log` output is shown. No DOM, no network.
- **Live HTML/CSS/JS preview**: a ```` ```html-run ```` fence containing a complete small page (put CSS in `<style>` and JS in `<script>`). It renders in a sandboxed frame below the editor and re-renders on Run.
- Plain ```` ```javascript ````, ```` ```html ```` and ```` ```css ```` fences are static, highlighted code.

JavaScript problems (`kind="js"`): same fields as Python problems, except
`entry` is the name of a top-level function declared in the code (no `class Solution`),
`starter`/`solution`/`wrong_solutions` are JavaScript, and `tests` are lists of JSON arguments.
Expected outputs are computed by running `solution` in Node, so results must be JSON-serialisable
(return arrays/objects/numbers/strings/booleans/null; `undefined` becomes `null`).
`compare` supports `exact` (default; object key order ignored), `unordered`, `unordered_nested`, `float`.
No `arg_types`, `checker`, or `kind="class"` for JavaScript; to test a class, have `entry` be a function
that takes a list of operations and returns the list of results.

```python
dict(
    id="js-sum-range", title="Sum a range", difficulty="Easy", pattern="Functions", kind="js", entry="sumRange",
    description="...", starter="function sumRange(a, b) {\n  // your code\n}\n",
    solution="function sumRange(a, b) {\n  let s = 0;\n  for (let i = a; i <= b; i++) s += i;\n  return s;\n}\n",
    tests=[[1, 3], [5, 5], [3, 1]], wrong_solutions=["function sumRange(a, b) { return a + b; }\n"], guide=dict(...),
)
```

HTML/CSS problems (`kind="web"`): the learner edits one HTML document (CSS in `<style>`).
Give `starter` (a page with gaps), `solution` (a full page that meets every requirement) and
`checks`: at least 3 dicts `{"name": "...what the learner sees...", "test": "<JavaScript expression>"}`.
Each `test` is evaluated inside the rendered page after load and must be truthy, for example
`document.querySelectorAll('nav li').length === 3`,
`getComputedStyle(document.querySelector('h1')).textAlign === 'center'`,
`document.querySelector('img').alt.length > 0`. The frame is 1024x768. Keep tests robust
(compare computed values, not source text) and make sure the solution passes all of them and the
starter fails at least one. Web problems have no `tests`/`entry`; the build only checks their shape,
so double-check each expression by reasoning through it against your solution.

## 6. Write for a complete beginner

Assume the reader has never seen the topic before and has no computer-science background.

- Open every lesson with a short "In plain words" section: what this thing is, an everyday analogy, and why it matters for a job.
- Define every technical term the first time it appears, in one plain sentence, before using it. Spell out acronyms.
- Build up in small steps: the simplest possible example first, then one new idea at a time, then the realistic example.
- Explain what each line of a code example does the first few times a construct appears; show the output and say why.
- State what the reader should already know at the top ("Before this lesson") and link the earlier lesson that teaches it.
- Never say "simply", "obviously", "just" or "as you know". Anticipate the confusion a newcomer would have and answer it.
- Keep the depth: beginner-friendly means explained from zero, not shortened. Interview-level material still belongs, after the foundations.
- Add a short glossary of the lesson's new terms before the quiz.

## 7. Java and Go problems (judged on the server)

Java 21 and Go 1.23 run on a small judge server, not in the browser. Use `kind="java"` or `kind="go"`.

Fields: `id`, `title`, `difficulty`, `pattern`, `description`, `starter`, `solution`, `harness`, `cases`,
optional `wrong_solutions`, and the usual `guide`. No `tests` or `entry`.

- The learner edits ONE file: `Solution.java` (a class named `Solution`, not public is fine) or `solution.go`
  (`package main`, exported or unexported functions/types, no `main`).
- `harness` is the test driver you write: `Main.java` with `public class Main` and `main`, or `main.go`
  with `package main` and `func main()`. It calls the learner's code and prints exactly one line per test:
  `CASE <n> OK` or `CASE <n> FAIL <short reason>`, numbered from 1, then exits with status 0.
  Catch exceptions/panics per test so one failure does not stop the rest (Java: try/catch Throwable;
  Go: a helper with `defer recover()`).
- `cases` is the number of CASE lines the harness prints (at least 3; aim for 8–12 including edge cases).
- Standard library only. No network, no file system outside /tmp, 512 MB memory, 25 s wall time in total,
  so keep inputs modest and avoid long sleeps.
- Anything else the program prints is shown to the learner as "Your output", so do not print noise.
- In Go harness strings prefer `fmt.Println("CASE", n, "OK")` over format strings with escape sequences.

```python
dict(
    id="java-twice", title="Twice", difficulty="Easy", pattern="Methods", kind="java", cases=3,
    description="Write `static int twice(int x)` in class `Solution` that returns double its argument.",
    starter="class Solution {\n    static int twice(int x) {\n        // your code\n        return 0;\n    }\n}\n",
    solution="class Solution {\n    static int twice(int x) {\n        return 2 * x;\n    }\n}\n",
    wrong_solutions=["class Solution {\n    static int twice(int x) {\n        return x + 2;\n    }\n}\n"],
    harness='''public class Main {
    static int n = 0;
    static void check(int got, int want) {
        n++;
        System.out.println("CASE " + n + (got == want ? " OK" : " FAIL got " + got + " want " + want));
    }
    public static void main(String[] args) {
        try { check(Solution.twice(2), 4); } catch (Throwable t) { n++; System.out.println("CASE " + n + " FAIL " + t); }
        try { check(Solution.twice(0), 0); } catch (Throwable t) { n++; System.out.println("CASE " + n + " FAIL " + t); }
        try { check(Solution.twice(-5), -10); } catch (Throwable t) { n++; System.out.println("CASE " + n + " FAIL " + t); }
    }
}
''',
    guide=dict(...),
)
```

`python tools/build.py --track <id>` sends each reference `solution` (and each wrong solution) to the judge and
fails the build if the reference does not pass every case or a wrong solution passes them all. Results are cached,
and the judge allows about 30 runs a minute, so a first build of many problems takes a few minutes.
If the build prints "not verified on the judge", the credentials file is missing: tell the lead.
