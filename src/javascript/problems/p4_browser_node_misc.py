"""JavaScript problems: grids, parsing text formats, templates, serialisation, throttling and currying."""


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


QUERY_SOLUTION = r'''function parseQuery(query) {
  const out = {};
  if (query.startsWith("?")) query = query.slice(1);
  if (query === "") return out;
  const decode = (s) => decodeURIComponent(s.replace(/\+/g, " "));
  for (const part of query.split("&")) {
    if (part === "") continue;
    const eq = part.indexOf("=");
    const key = decode(eq === -1 ? part : part.slice(0, eq));
    const value = eq === -1 ? "" : decode(part.slice(eq + 1));
    if (!Object.hasOwn(out, key)) out[key] = value;
    else if (Array.isArray(out[key])) out[key].push(value);
    else out[key] = [out[key], value];
  }
  return out;
}
'''

FILL_SOLUTION = r'''function floodFill(grid, row, col, color) {
  const result = grid.map((line) => [...line]);
  const target = result[row][col];
  if (target === color) return result;
  const stack = [[row, col]];
  while (stack.length > 0) {
    const [r, c] = stack.pop();
    if (r < 0 || r >= result.length || c < 0 || c >= result[r].length) continue;
    if (result[r][c] !== target) continue;
    result[r][c] = color;
    stack.push([r + 1, c], [r - 1, c], [r, c + 1], [r, c - 1]);
  }
  return result;
}
'''

CSV_SOLUTION = r'''function parseCsv(text) {
  const rows = [];
  let row = [], field = "", inQuotes = false, i = 0, sawAnything = false;
  while (i < text.length) {
    const ch = text[i];
    if (inQuotes) {
      if (ch === '"' && text[i + 1] === '"') { field += '"'; i += 2; }
      else if (ch === '"') { inQuotes = false; i++; }
      else { field += ch; i++; }
      continue;
    }
    if (ch === '"') { inQuotes = true; sawAnything = true; i++; }
    else if (ch === ",") { row.push(field); field = ""; sawAnything = true; i++; }
    else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && text[i + 1] === "\n") i++;
      row.push(field); rows.push(row);
      row = []; field = ""; sawAnything = false; i++;
    }
    else { field += ch; sawAnything = true; i++; }
  }
  if (sawAnything) { row.push(field); rows.push(row); }
  return rows;
}
'''

TEMPLATE_SOLUTION = r'''function render(template, data) {
  const lookup = (path) => {
    let current = data;
    for (const key of path.split(".")) {
      if (current === null || typeof current !== "object" || !Object.hasOwn(current, key)) return "";
      current = current[key];
    }
    return current === null || typeof current === "object" ? "" : String(current);
  };
  const escapes = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  const escape = (s) => s.replace(/[&<>"']/g, (ch) => escapes[ch]);
  return template.replace(/\{\{\{\s*([\w.]+)\s*\}\}\}|\{\{\s*([\w.]+)\s*\}\}/g, (whole, raw, safe) =>
    raw !== undefined ? lookup(raw) : escape(lookup(safe)));
}
'''

STRINGIFY_SOLUTION = r'''function stringify(value) {
  if (value === null) return "null";
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : "null";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "string") return quote(value);
  if (Array.isArray(value)) return "[" + value.map((v) => (v === undefined ? "null" : stringify(v))).join(",") + "]";
  const parts = [];
  for (const key of Object.keys(value)) {
    if (value[key] === undefined) continue;
    parts.push(quote(key) + ":" + stringify(value[key]));
  }
  return "{" + parts.join(",") + "}";
}
function quote(text) {
  const named = { '"': '\\"', "\\": "\\\\", "\n": "\\n", "\r": "\\r", "\t": "\\t", "\b": "\\b", "\f": "\\f" };
  let out = '"';
  for (const ch of text) {
    if (named[ch]) out += named[ch];
    else if (ch < " ") out += "\\u" + ch.charCodeAt(0).toString(16).padStart(4, "0");
    else out += ch;
  }
  return out + '"';
}
'''

CURRY_DRIVER = r'''
// --- driver (provided, do not change) ---
function runCurry(arity, groups) {
  const table = {
    1: (a) => "f(" + a + ")",
    2: (a, b) => "f(" + a + "," + b + ")",
    3: (a, b, c) => "f(" + a + "," + b + "," + c + ")",
    4: (a, b, c, d) => "f(" + a + "," + b + "," + c + "," + d + ")",
  };
  let current = curry(table[arity]);
  const first = current;
  for (const group of groups) {
    if (typeof current !== "function") return "called too often";
    current = current(...group);
  }
  // a partially applied function must be reusable: applying it must not change it
  const reuse = typeof first(1) === typeof first(1);
  return [typeof current === "function" ? "function" : current, reuse];
}
'''

PROBLEMS = [
dict(
    id="js-spiral-matrix", title="Spiral order", difficulty="Medium", pattern="Matrices",
    kind="js", entry="spiralOrder",
    description=r"""
Given a rectangular grid (an array of equal-length rows), return its values in clockwise spiral order,
starting at the top-left corner and moving right first. The same traversal drives effects such as a
spiral wipe over the tiles of a game level.

**Examples:** `spiralOrder([[1,2,3],[4,5,6],[7,8,9]])` → `[1,2,3,6,9,8,7,4,5]` · `spiralOrder([[1,2,3,4]])` → `[1,2,3,4]` · `spiralOrder([])` → `[]`
""",
    starter="function spiralOrder(grid) {\n  // your code\n}\n",
    solution="function spiralOrder(grid) {\n  const out = [];\n  if (grid.length === 0) return out;\n  let top = 0, bottom = grid.length - 1, left = 0, right = grid[0].length - 1;\n  while (top <= bottom && left <= right) {\n    for (let c = left; c <= right; c++) out.push(grid[top][c]);\n    top++;\n    for (let r = top; r <= bottom; r++) out.push(grid[r][right]);\n    right--;\n    if (top <= bottom) {\n      for (let c = right; c >= left; c--) out.push(grid[bottom][c]);\n      bottom--;\n    }\n    if (left <= right) {\n      for (let r = bottom; r >= top; r--) out.push(grid[r][left]);\n      left++;\n    }\n  }\n  return out;\n}\n",
    tests=[
        [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]], [[[1, 2, 3, 4]]], [[]], [[[1], [2], [3]]], [[[7]]],
        [[[1, 2], [3, 4]]], [[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]], [[[1, 2], [3, 4], [5, 6], [7, 8]]],
        [[[1, 2, 3], [4, 5, 6]]], [[[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12, 13, 14, 15], [16, 17, 18, 19, 20], [21, 22, 23, 24, 25]]],
        [[["a", "b"], ["c", "d"], ["e", "f"]]],
        [[[r * 30 + c for c in range(30)] for r in range(20)]],
    ],
    wrong_solutions=[
        "function spiralOrder(grid) {\n  const out = [];\n  if (grid.length === 0) return out;\n  let top = 0, bottom = grid.length - 1, left = 0, right = grid[0].length - 1;\n  while (top <= bottom && left <= right) {\n    for (let c = left; c <= right; c++) out.push(grid[top][c]);\n    top++;\n    for (let r = top; r <= bottom; r++) out.push(grid[r][right]);\n    right--;\n    for (let c = right; c >= left; c--) out.push(grid[bottom][c]);\n    bottom--;\n    for (let r = bottom; r >= top; r--) out.push(grid[r][left]);\n    left++;\n  }\n  return out;\n}\n",
        "function spiralOrder(grid) { return grid.flat(); }\n",
        "function spiralOrder(grid) {\n  const out = [];\n  if (grid.length === 0) return out;\n  let top = 0, bottom = grid.length - 1, left = 0, right = grid.length - 1;\n  while (top <= bottom && left <= right) {\n    for (let c = left; c <= right; c++) out.push(grid[top][c]);\n    top++;\n    for (let r = top; r <= bottom; r++) out.push(grid[r][right]);\n    right--;\n    if (top <= bottom) { for (let c = right; c >= left; c--) out.push(grid[bottom][c]); bottom--; }\n    if (left <= right) { for (let r = bottom; r >= top; r--) out.push(grid[r][left]); left++; }\n  }\n  return out;\n}\n",
    ],
    guide=G(
        prereqs="Nested arrays and index loops (lesson *Objects, arrays and mutability*); grids as used by the platform game level.",
        intuition="Peel the grid like an onion. Four bindings (`top`, `bottom`, `left`, `right`) mark the unvisited rectangle; walk its border and shrink it.",
        hints=[
            "Walk the top row left→right, then the right column top→bottom, then the bottom row right→left, then the left column bottom→top.",
            "Move the corresponding boundary inwards right after each walk.",
            "Before the third and fourth walks, re-check that the rectangle still has a row / a column left, or a single row or column is emitted twice.",
        ],
        brute_force="Keep a `visited` grid and a direction; step forward, turning right when the next cell is outside or visited. Same O(rows·cols) time, extra O(rows·cols) memory.",
        approach="**Dry run** `[[1,2,3],[4,5,6]]`: top row → 1,2,3 (top=1); right column rows 1..1 → 6 (right=1); `top <= bottom` → bottom row from col 1 to 0 → 5,4 (bottom=0); `left <= right` → left column rows 0..1: none, since bottom < top. Loop ends. Result `1,2,3,6,5,4`.",
        complexity="O(rows × cols) time, O(1) extra space besides the output.",
        pitfalls="- Missing the two guards duplicates cells in single-row and single-column remainders.\n- Using the row count for the column bound only works for squares.\n- An empty grid has no `grid[0]`.",
        follow_up="Generate the inverse: fill an n × m grid with 1..n·m in spiral order. Or rotate a square matrix by 90° in place.",
    ),
),
dict(
    id="js-query-string", title="Parse a query string", difficulty="Medium", pattern="Parsing",
    kind="js", entry="parseQuery",
    description=r"""
The part of a URL after `?` encodes form fields as `name=value` pairs joined by `&`. Write
`parseQuery(query)` that turns such a string into an object **without using `URLSearchParams`**:

- a leading `?` is optional; an empty query gives `{}`; empty segments (`a=1&&b=2`) are skipped
- `+` means a space, and `%XX` sequences are percent-decoded (`decodeURIComponent`), in both names and values
- a name without `=` gets the value `""`; only the **first** `=` separates name from value
- a name that occurs several times collects its values in an array, in order

**Examples:** `parseQuery("?q=red+shoes&page=2")` → `{q: "red shoes", page: "2"}` · `parseQuery("tag=a&tag=b&tag=c")` → `{tag: ["a","b","c"]}`
""",
    starter="function parseQuery(query) {\n  // your code\n}\n",
    solution=QUERY_SOLUTION,
    tests=[["?q=red+shoes&page=2"], ["tag=a&tag=b&tag=c"], [""], ["?"], ["flag"], ["a=1&&b=2&"], ["eq=a=b=c"],
           ["name=J%C3%BCrgen&city=S%C3%A3o+Paulo"], ["a%20b=c%26d"], ["k="], ["=v"], ["x=1&y=2&x=3"],
           ["plus=1%2B1&space=1+1"], ["toString=1&constructor=2"], ["a=&a=&a=x"]],
    wrong_solutions=[
        "function parseQuery(query) {\n  const out = {};\n  if (query.startsWith('?')) query = query.slice(1);\n  for (const part of query.split('&')) { if (!part) continue; const [k, v] = part.split('='); out[k] = v ?? ''; }\n  return out;\n}\n",
        QUERY_SOLUTION.replace('const decode = (s) => decodeURIComponent(s.replace(/\\+/g, " "));', 'const decode = (s) => decodeURIComponent(s).replace(/\\+/g, " ");'),
        QUERY_SOLUTION.replace('if (!Object.hasOwn(out, key)) out[key] = value;\n    else if (Array.isArray(out[key])) out[key].push(value);\n    else out[key] = [out[key], value];', 'out[key] = value;'),
        QUERY_SOLUTION.replace('if (!Object.hasOwn(out, key)) out[key] = value;', 'if (!out[key]) out[key] = value;'),
    ],
    guide=G(
        prereqs="String methods `split`, `indexOf`, `slice`; URL encoding and how forms are submitted (lesson *HTTP, fetch, forms and client-side storage*).",
        intuition="Two levels of splitting: `&` separates pairs, the first `=` separates name from value. Decode *after* splitting, because an encoded `%26` or `%3D` must not be mistaken for a separator.",
        hints=[
            "Strip one leading `?`, then `split(\"&\")` and ignore empty pieces.",
            "Use `indexOf(\"=\")` and `slice` rather than `split(\"=\")`, so that values containing `=` stay intact.",
            "Replace `+` by a space **before** calling `decodeURIComponent`; afterwards you could not tell a real plus (`%2B`) from a space.",
        ],
        brute_force="A character-by-character state machine (reading name, reading value) is the manual alternative; splitting does the same in three lines.",
        approach="**Dry run** `?q=red+shoes&page=2`: strip `?`; parts `q=red+shoes`, `page=2`; first: key `q`, value `red+shoes` → `red shoes`; second: `page` → `\"2\"` (values are always strings).",
        complexity="O(n) in the length of the query.",
        pitfalls="- Decoding first and replacing `+` afterwards turns `1%2B1` into `1 1`.\n- `part.split(\"=\")` loses everything after a second `=`.\n- Overwriting repeated names instead of collecting them.\n- Checking `if (!out[key])` mistakes an existing empty-string value, or an inherited name like `toString`, for *absent*.",
        follow_up="Write the inverse `toQuery(obj)` with `encodeURIComponent`, and compare with the standard `URLSearchParams` class, which represents repeats through `getAll`.",
    ),
),
dict(
    id="js-flood-fill", title="Flood fill (paint bucket)", difficulty="Medium", pattern="Grid search",
    kind="js", entry="floodFill",
    description=r"""
The bucket tool of a pixel editor recolours the clicked pixel and every pixel of the **same colour** that is
connected to it through horizontal or vertical neighbours.

Write `floodFill(grid, row, col, color)`: `grid` is an array of rows of colour values (numbers or strings).
Return a **new** grid with the fill applied; do not modify the argument. `row` and `col` are always inside the grid.

**Example:** `floodFill([[1,1,0],[1,0,0],[1,1,1]], 0, 0, 7)` → `[[7,7,0],[7,0,0],[7,7,7]]`
""",
    starter="function floodFill(grid, row, col, color) {\n  // your code\n}\n",
    solution=FILL_SOLUTION,
    tests=[
        [[[1, 1, 0], [1, 0, 0], [1, 1, 1]], 0, 0, 7],
        [[[1, 1, 0], [1, 0, 0], [1, 1, 1]], 1, 1, 7],
        [[[5]], 0, 0, 5],
        [[[5]], 0, 0, 6],
        [[[0, 0], [0, 0]], 1, 1, 0],
        [[[1, 0, 1], [0, 1, 0], [1, 0, 1]], 1, 1, 9],
        [[[1, 0, 1], [0, 1, 0], [1, 0, 1]], 0, 1, 9],
        [[["r", "r", "g"], ["g", "r", "g"], ["g", "g", "g"]], 0, 2, "b"],
        [[[0, 0, 0, 0, 0]], 0, 2, 3],
        [[[0], [0], [1], [0]], 0, 0, 2],
        [[[1, 1, 1, 1], [1, 0, 0, 1], [1, 0, 0, 1], [1, 1, 1, 1]], 0, 0, 4],
        [[[2, 2, 2], [2, 3, 2], [2, 2, 2]], 1, 1, 2],
        [[[0] * 60 for _ in range(60)], 30, 30, 1],
        [[[(r // 3 + c // 3) % 2 for c in range(12)] for r in range(12)], 4, 4, 8],
    ],
    wrong_solutions=[
        "function floodFill(grid, row, col, color) {\n  const target = grid[row][col];\n  return grid.map((line) => line.map((v) => (v === target ? color : v)));\n}\n",
        FILL_SOLUTION.replace("stack.push([r + 1, c], [r - 1, c], [r, c + 1], [r, c - 1]);", "stack.push([r + 1, c], [r - 1, c], [r, c + 1], [r, c - 1], [r + 1, c + 1], [r - 1, c - 1], [r + 1, c - 1], [r - 1, c + 1]);"),
        FILL_SOLUTION.replace("stack.push([r + 1, c], [r - 1, c], [r, c + 1], [r, c - 1]);", "stack.push([r + 1, c], [r, c + 1]);"),
    ],
    guide=G(
        prereqs="2D arrays, copying arrays, a stack or queue for graph traversal (lesson *Project: a pixel art editor explained*).",
        intuition="The picture is a graph: pixels are nodes, touching pixels of equal colour are connected. Flood fill is a traversal from the clicked node that paints as it goes; painting doubles as the *visited* mark.",
        hints=[
            "Copy the grid first (`grid.map(row => [...row])`) and work on the copy.",
            "Remember the starting colour. If it equals the new colour, return immediately; otherwise painted cells would still look *unvisited* and the loop would never end.",
            "Use an explicit stack of `[r, c]` pairs: pop, skip if outside or of another colour, paint, push the four neighbours.",
        ],
        brute_force="Recolouring every pixel that has the target colour ignores connectivity and paints islands that are not attached to the clicked one.",
        approach="**Dry run** on the example from (0,0) with target 1 → paints (0,0), (1,0), (2,0), (2,1), (2,2), (0,1). The cell (2,2) is reached along the bottom row; the zeros are never entered.",
        complexity="O(rows × cols) time; the stack can hold O(rows × cols) entries in the worst case.",
        pitfalls="- Recursion overflows the call stack on large uniform areas (the 60 × 60 test fills 3,600 cells); use a loop.\n- Diagonal neighbours leak through corners.\n- Mutating the input breaks undo history in an editor that relies on immutable pictures.",
        follow_up="Scanline fill paints whole horizontal runs at once and pushes far fewer entries. Add a tolerance so that *similar* colours count as equal.",
    ),
),
dict(
    id="js-parse-csv", title="Parse CSV", difficulty="Hard", pattern="Parsing",
    kind="js", entry="parseCsv",
    description=r'''
Write `parseCsv(text)` returning an array of rows, each an array of string fields, for this common CSV dialect:

- fields are separated by commas, rows by `\n` or `\r\n`
- a field may be wrapped in double quotes; inside quotes, commas and line breaks are ordinary characters and
  a doubled quote `""` stands for one quote character
- unquoted fields are taken literally (no trimming)
- a line break at the very end of the text does not start an extra row, but an empty line in the middle is a
  row with one empty field
- the empty text has no rows

**Example:** `parseCsv('name,quote\n"Ada, Countess","said ""hi"""\n')` → `[["name","quote"],["Ada, Countess","said \"hi\""]]`
''',
    starter="function parseCsv(text) {\n  // your code\n}\n",
    solution=CSV_SOLUTION,
    tests=[['name,quote\n"Ada, Countess","said ""hi"""\n'], [""], ["a,b,c"], ["a,b,c\n"], ["a,b\n1,2\n3,4"],
           ["a,b\r\n1,2\r\n"], [",,"], ["a,\n,b"], ['"multi\nline",x\ny,z'], ['""'], ['"",""\n'], ["one\n\ntwo"],
           [" spaced , out "], ['a,"b,c",d\n"x""y",,"z"'], ["\n"], ['"a"\n"b"'], ["x,y\n1,"]],
    wrong_solutions=[
        "function parseCsv(text) {\n  if (text === '') return [];\n  return text.split('\\n').map((line) => line.split(','));\n}\n",
        "function parseCsv(text) {\n  if (text === '') return [];\n  return text.replace(/\\r?\\n$/, '').split(/\\r?\\n/).map((line) => line.split(',').map((f) => f.replace(/^\"|\"$/g, '').replace(/\"\"/g, '\"')));\n}\n",
        CSV_SOLUTION.replace("if (ch === '\"' && text[i + 1] === '\"') { field += '\"'; i += 2; }\n      else if", "if"),
        CSV_SOLUTION.replace("if (sawAnything) { row.push(field); rows.push(row); }", "row.push(field); rows.push(row);"),
    ],
    guide=G(
        prereqs="Character-by-character scanning with state; why a regular expression or `split` alone cannot handle nested quoting (lessons on regular expressions and on Node streams and files).",
        intuition="Whether a comma separates fields depends on *where you are*: inside quotes or not. That is one bit of state. Scan the text once, keep that bit, and build the current field, the current row and the list of rows as you go.",
        hints=[
            "Bindings: `rows`, `row`, `field`, `inQuotes`.",
            "Inside quotes only a quote is special: two in a row add one quote to the field; a single one ends the quoted section.",
            "Outside quotes: `,` closes the field; a line break closes the field **and** the row. At the end of the text, close the last row only if something was started on it.",
        ],
        brute_force="`text.split(\"\\n\").map(line => line.split(\",\"))` is the classic first attempt. It breaks on the first quoted comma or embedded newline.",
        approach="**Dry run** of `a,\"b,c\"`: `a` → field `a`; `,` → row `[a]`; `\"` → enter quotes; `b`, `,`, `c` appended (comma is literal); `\"` → leave quotes; end of text with something pending → row `[a, \"b,c\"]`.\n\nThe flag `sawAnything` distinguishes *text ended right after a line break* (no extra row) from *text ended after a comma or characters* (a final row).",
        complexity="O(n) time, O(n) space for the output.",
        pitfalls="- Treating `\\r\\n` as two line breaks creates phantom empty rows.\n- Stripping quotes with a regex after splitting cannot repair fields that were split at a quoted comma.\n- An empty quoted field `\"\"` at the end of the text is still a field.\n- `a,` ends with an empty second field; do not drop it.",
        follow_up="Turn rows into objects using the first row as headers; then make the parser incremental so it can consume a stream chunk by chunk.",
    ),
),
dict(
    id="js-template-engine", title="A tiny template engine", difficulty="Medium", pattern="String processing",
    kind="js", entry="render",
    description=r"""
Write `render(template, data)` that fills placeholders in a text:

- `{{ path }}` is replaced by the value found in `data` at the dotted path (`user.name`, `items.0.title`),
  converted to a string and **HTML-escaped**: `&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`, `"` → `&quot;`, `'` → `&#39;`
- `{{{ path }}}` inserts the value **without** escaping
- spaces around the path are optional; a path consists of letters, digits, `_` and dots
- a path that does not exist, or that leads to `null`, an object or an array, renders as the empty string
- anything else in the template is copied unchanged

**Example:** `render("Hi {{ user.name }}! {{{ badge }}}", {user: {name: "<Ada>"}, badge: "<b>new</b>"})` → `"Hi &lt;Ada&gt;! <b>new</b>"`
""",
    starter="function render(template, data) {\n  // your code\n}\n",
    solution=TEMPLATE_SOLUTION,
    tests=[
        ["Hi {{ user.name }}! {{{ badge }}}", {"user": {"name": "<Ada>"}, "badge": "<b>new</b>"}],
        ["no placeholders", {}],
        ["", {"a": 1}],
        ["{{a}}{{b}}{{a}}", {"a": "x", "b": "y"}],
        ["{{ missing }}|{{ a.b.c }}|{{ a.toString }}", {"a": {"b": 1}}],
        ["{{n}} items, {{ok}}, {{zero}}", {"n": 3, "ok": False, "zero": 0}],
        ["{{ items.1.title }}", {"items": [{"title": "first"}, {"title": "second"}]}],
        ["{{obj}}{{arr}}{{nil}}", {"obj": {"x": 1}, "arr": [1, 2], "nil": None}],
        ["<p title=\"{{t}}\">{{t}}</p>", {"t": "Tom & \"Jerry\" 's <show>"}],
        ["{{{ t }}} vs {{ t }}", {"t": "a < b && c > d"}],
        ["{ {a} } {{ a } } {{a}}", {"a": "v"}],
        ["{{  spaced.out  }}", {"spaced": {"out": "ok"}}],
        ["{{a}}", {"a": "{{b}}", "b": "nested"}],
        ["Total: {{ cart.total }} ({{cart.count}} items) {{{cart.note}}}", {"cart": {"total": 19.5, "count": 2, "note": "<i>gift</i>"}}],
    ],
    wrong_solutions=[
        TEMPLATE_SOLUTION.replace("raw !== undefined ? lookup(raw) : escape(lookup(safe)));", "raw !== undefined ? lookup(raw) : lookup(safe));"),
        "function render(template, data) {\n  return template.replace(/\\{\\{\\s*([\\w.]+)\\s*\\}\\}/g, (whole, key) => (data[key] === undefined ? '' : String(data[key])));\n}\n",
        TEMPLATE_SOLUTION.replace('return current === null || typeof current === "object" ? "" : String(current);', 'return current ? String(current) : "";'),
        TEMPLATE_SOLUTION.replace("/\\{\\{\\{\\s*([\\w.]+)\\s*\\}\\}\\}|\\{\\{\\s*([\\w.]+)\\s*\\}\\}/g", "/\\{\\{\\s*([\\w.]+)\\s*\\}\\}|\\{\\{\\{\\s*([\\w.]+)\\s*\\}\\}\\}/g"),
    ],
    guide=G(
        prereqs="`replace` with a callback, capture groups, alternation order (regular expression lessons); why untrusted text must be escaped before it becomes HTML (lesson *Changing the document*).",
        intuition="A template engine is *find the holes, look up a value for each, glue the text back together*. `String.replace` with a function argument does the finding and gluing; you supply lookup and escaping.",
        hints=[
            "One regular expression with two alternatives: triple braces first, then double. The engine tries alternatives left to right, so the longer form must come first.",
            "The replacement callback receives the whole match followed by the groups; exactly one of the two groups is defined.",
            "Write `lookup(path)` as a walk over `path.split(\".\")`, bailing out with `\"\"` when a step is impossible.",
        ],
        brute_force="Scan with `indexOf(\"{{\")` / `indexOf(\"}}\")` and build the output piece by piece. Works; the bookkeeping for the triple form is fiddly.",
        approach="**Dry run** of the example: match 1 `{{ user.name }}` → safe path `user.name` → `<Ada>` → escaped `&lt;Ada&gt;`. Match 2 `{{{ badge }}}` → raw → inserted as is.\n\nThe result of a replacement is not scanned again, so data containing `{{b}}` stays literal.",
        complexity="O(n + total size of inserted values).",
        pitfalls="- Not escaping lets data inject markup (cross-site scripting).\n- Putting the double-brace alternative first makes `{{{ x }}}` match as `{` + `{{ x }}` + `}`.\n- `current ? ... : \"\"` hides `0` and `false`.\n- Inherited members (`a.toString`) are not data.",
        follow_up="Add sections: `{{#each items}}...{{/each}}` and `{{#if flag}}...{{/if}}`. At that point a regex is no longer enough and you need the tokenizer-plus-parser structure from the Pebble project.",
    ),
),
dict(
    id="js-json-stringify", title="JSON.stringify, the essential subset", difficulty="Medium", pattern="Recursion & serialisation",
    kind="js", entry="stringify",
    description=r"""
Implement `stringify(value)` producing the same compact text as `JSON.stringify(value)` for JSON data,
**without calling `JSON.stringify`**:

- `null`, `true`, `false`, numbers → their literal text
- strings → wrapped in double quotes, with `"` and `\` escaped by a backslash, and newline, carriage return,
  tab, backspace and form feed written as `\n`, `\r`, `\t`, `\b`, `\f`; other control characters below
  U+0020 as `\u00XX` (lower-case hex)
- arrays → `[a,b,c]` and objects → `{"key":value,...}` in key order, with no spaces

**Examples:** `stringify({a: [1, "x", null]})` → `'{"a":[1,"x",null]}'` · `stringify('say "hi"\n')` → `'"say \\"hi\\"\\n"'`
""",
    starter="function stringify(value) {\n  // your code\n}\n",
    solution=STRINGIFY_SOLUTION,
    tests=[
        [{"a": [1, "x", None]}], ['say "hi"\n'], [None], [True], [False], [0], [-12.5], [1e21], [""], ["plain"],
        [[]], [{}], [[[], {}, [[]]]], ["back\\slash and \t tab"], ["line1\r\nline2"], ["\u0001\u001f"],
        [{"key with \"quote\"": 1, "": 2}], ["héllo ✓ 日本"], [{"users": [{"name": "Ada", "tags": ["a", "b"], "active": True, "score": 9.75}], "total": 1}],
        [[1, [2, [3, [4, [5]]]]]], [{"a": {"b": {"c": {}}}}], ["</script>"], [1e-7],
    ],
    wrong_solutions=[
        STRINGIFY_SOLUTION.replace("if (named[ch]) out += named[ch];\n    else if (ch < \" \") out += \"\\\\u\" + ch.charCodeAt(0).toString(16).padStart(4, \"0\");\n    else out += ch;", "out += ch;"),
        STRINGIFY_SOLUTION.replace('.join(",") + "]"', '.join(", ") + "]"'),
        STRINGIFY_SOLUTION.replace('parts.push(quote(key) + ":" + stringify(value[key]));', 'parts.push(key + ":" + stringify(value[key]));'),
        STRINGIFY_SOLUTION.replace('if (value === null) return "null";', 'if (!value) return "null";'),
    ],
    guide=G(
        prereqs="The JSON format (lesson *Destructuring, spread, rest and JSON*), recursion over nested data, string escapes.",
        intuition="Serialising is a recursion on the *type* of the value: four leaf cases that produce text directly and two container cases that join the serialisations of their parts.",
        hints=[
            "Order the checks: `null` first (because `typeof null` is `\"object\"`), then primitives by `typeof`, then `Array.isArray`, then objects.",
            "Write a separate `quote(text)` helper and use it for both string values and object keys.",
            "In `quote`, build the output character by character with a small lookup table for the named escapes.",
        ],
        brute_force="There is no meaningfully slower approach; the straightforward recursion is the standard algorithm.",
        approach="**Dry run** `{a:[1,\"x\",null]}`: object → key `a` → `\"a\":` + array → `1`, `\"x\"`, `null` joined by commas → `[1,\"x\",null]` → `{\"a\":[1,\"x\",null]}`.",
        complexity="O(n) in the size of the output; recursion depth equals nesting depth.",
        pitfalls="- Forgetting to escape the backslash itself produces text that parses to something else.\n- A raw newline inside the quotes is invalid JSON.\n- `if (!value)` catches `0`, `false` and `\"\"` along with `null`.\n- Keys need quotes; `{a:1}` is JavaScript, not JSON.\n- Numbers: let `String(n)` do the work (it matches JSON for finite numbers, including `1e+21`).",
        follow_up="Add the `indent` parameter for pretty-printing, call `toJSON()` when a value defines it, and detect cycles with a `Set` of ancestors.",
    ),
),
dict(
    id="js-throttle-sim", title="Throttle, simulated", difficulty="Easy", pattern="Timers",
    kind="js", entry="throttleCalls",
    description=r"""
A throttled function runs at most once per `interval` milliseconds: the first call runs immediately, and
further calls are ignored until `interval` ms have passed **since the last call that actually ran**.

`throttleCalls(times, interval)` receives the sorted timestamps of the attempted calls and returns the
timestamps of those that run.

**Example:** `throttleCalls([0, 30, 90, 100, 130, 260], 100)` → `[0, 100, 260]`
""",
    starter="function throttleCalls(times, interval) {\n  // your code\n}\n",
    solution="function throttleCalls(times, interval) {\n  const ran = [];\n  let last = -Infinity;\n  for (const t of times) {\n    if (t - last >= interval) {\n      ran.push(t);\n      last = t;\n    }\n  }\n  return ran;\n}\n",
    tests=[
        [[0, 30, 90, 100, 130, 260], 100], [[], 50], [[5], 50], [[0, 0, 0], 10], [[0, 10, 20, 30], 10],
        [[0, 9, 18, 27, 36], 10], [[0, 99, 100, 199, 200], 100], [[100, 150, 400, 420, 520], 100], [[1, 2, 3], 0],
        [[0, 60, 120, 180, 240], 100], [[i * 7 for i in range(200)], 50], [[0, 50, 99, 149, 198], 50],
    ],
    wrong_solutions=[
        "function throttleCalls(times, interval) {\n  const ran = []; let last = -Infinity;\n  for (const t of times) { if (t - last >= interval) ran.push(t); last = t; }\n  return ran;\n}\n",
        "function throttleCalls(times, interval) {\n  const ran = []; let last = -Infinity;\n  for (const t of times) { if (t - last > interval) { ran.push(t); last = t; } }\n  return ran;\n}\n",
        "function throttleCalls(times, interval) {\n  const ran = []; let slot = -1;\n  for (const t of times) { const s = Math.floor(t / (interval || 1)); if (s !== slot) { ran.push(t); slot = s; } }\n  return ran;\n}\n",
    ],
    guide=G(
        prereqs="The throttle pattern and how it differs from debounce (lessons *Keys, pointers, scrolling, timers and debouncing* and *Interview async and utilities*).",
        intuition="Remember one number: when the function last ran. A call is allowed exactly when enough time has passed since then.",
        hints=[
            "Initialise `last` to `-Infinity` so the very first call always passes.",
            "Compare `t - last >= interval`.",
            "Update `last` **only** when a call runs, not on every attempt.",
        ],
        brute_force="For each call, scan back through the calls that ran: O(n²). The single `last` binding carries the same information.",
        approach="**Dry run** interval 100: 0 runs (last 0); 30 and 90 are too early; 100 runs (last 100); 130 too early; 260 runs. Result `[0,100,260]`.",
        complexity="O(n) time, O(1) extra space.",
        pitfalls="- Updating `last` on ignored calls turns throttle into a kind of debounce: a steady stream faster than the interval would then run only once.\n- `>` instead of `>=` delays the next run by one tick.\n- Bucketing time into fixed slots lets two calls run 1 ms apart across a slot border.",
        follow_up="Real throttles often add a *trailing* call so the final state is not lost. Write `throttle(fn, interval)` with `Date.now()`, and a variant based on `requestAnimationFrame`.",
    ),
),
dict(
    id="js-curry", title="Curry a function", difficulty="Medium", pattern="Closures",
    kind="js", entry="runCurry",
    description=r"""
Write `curry(fn)` that converts a function of `fn.length` parameters into one that can receive its arguments
in any grouping: `curry(f)(1)(2)(3)`, `curry(f)(1, 2)(3)` and `curry(f)(1, 2, 3)` all compute `f(1, 2, 3)`.

- as long as fewer than `fn.length` arguments have been collected, the result is another function
- as soon as enough have been collected, `fn` is called and its result returned
- partially applied functions must be reusable: calling one must not alter it

The driver curries a function of the given arity that returns a string such as `"f(1,2,3)"`, feeds it the
argument groups one after another and reports `[finalResultOr"function", reusableFlag]`.

**Examples:** `runCurry(3, [[1], [2], [3]])` → `["f(1,2,3)", true]` · `runCurry(3, [[1, 2]])` → `["function", true]`
""",
    starter="function curry(fn) {\n  // your code\n}\n" + CURRY_DRIVER,
    solution="function curry(fn) {\n  return function curried(...args) {\n    if (args.length >= fn.length) return fn.apply(this, args);\n    return (...more) => curried.apply(this, [...args, ...more]);\n  };\n}\n" + CURRY_DRIVER,
    tests=[[3, [[1], [2], [3]]], [3, [[1, 2]]], [3, [[1, 2], [3]]], [3, [[1], [2, 3]]], [3, [[1, 2, 3]]], [1, [["x"]]],
           [2, [["a"], ["b"]]], [4, [[1], [2], [3], [4]]], [4, [[1, 2], [3, 4]]], [4, [[1], [2, 3]]], [2, []],
           [3, [[], [1], [], [2], [3]]], [2, [[9, 8]]], [4, [[1, 2, 3], ["z"]]]],
    wrong_solutions=[
        "function curry(fn) {\n  const collected = [];\n  return function curried(...args) {\n    collected.push(...args);\n    return collected.length >= fn.length ? fn(...collected) : curried;\n  };\n}\n" + CURRY_DRIVER,
        "function curry(fn) {\n  return function curried(...args) {\n    if (args.length >= fn.length) return fn(...args);\n    return (next) => curried(...args, next);\n  };\n}\n" + CURRY_DRIVER,
        "function curry(fn) {\n  return (a) => (b) => (c) => fn(a, b, c);\n}\n" + CURRY_DRIVER,
    ],
    guide=G(
        prereqs="Closures, rest and spread, `Function.prototype.length` (lessons *Closures and recursion*, *Interview core*).",
        intuition="Each call either has enough arguments to finish or returns a new function that remembers what has been collected so far. The memory is a closure over a **new** array for every step, which is what makes partial applications reusable.",
        hints=[
            "`fn.length` is the number of declared parameters.",
            "Inside `curried(...args)`: if `args.length >= fn.length`, call `fn`.",
            "Otherwise return `(...more) => curried(...args, ...more)`. Never push onto a shared array.",
        ],
        brute_force="Hard-coding `a => b => c => fn(a, b, c)` handles exactly one arity and exactly one grouping.",
        approach="**Dry run** `curry(f)(1, 2)(3)` for arity 3: `curried(1,2)` has 2 < 3 arguments → returns a function closing over `[1,2]`; calling it with `3` invokes `curried(1,2,3)` → 3 ≥ 3 → `f(1,2,3)`.",
        complexity="O(n) calls at most and O(n²) argument copying for n parameters, negligible in practice.",
        pitfalls="- A single shared `collected` array makes the second use of a partial function see stale arguments.\n- Accepting only one argument per call (`(next) => ...`) drops the rest of a group.\n- Functions with default or rest parameters report a smaller `length`; currying them needs an explicit arity.",
        follow_up="Add placeholder support (`curry(f)(_, 2)(1)`), or implement `partial(fn, ...preset)`, the simpler cousin that fixes the first arguments once.",
    ),
),
]
