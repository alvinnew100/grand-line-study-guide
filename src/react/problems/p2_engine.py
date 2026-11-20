"""React track problems, part 2: the machinery (virtual DOM, diffing, hooks, memoisation, events, context)."""


def G(prereqs, intuition, hints, brute_force, approach, complexity, pitfalls, follow_up=""):
    return dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute_force,
                approach=approach, complexity=complexity, pitfalls=pitfalls, follow_up=follow_up)


BUILD_DRIVER = r'''
// --- driver (provided, do not change) ---
// A spec is { t: type, p: props or null, c: [children] }; children may be strings, numbers,
// null, booleans, nested arrays or further specs. The driver turns specs into createElement calls.
function buildTree(spec) {
  const convert = (s) => {
    if (Array.isArray(s)) return s.map(convert);
    if (s !== null && typeof s === "object") {
      return createElement(s.t, s.p === undefined ? null : s.p, ...(s.c || []).map(convert));
    }
    return s;
  };
  return convert(spec);
}
'''

HOOKS_DRIVER = r'''
// --- driver (provided, do not change) ---
function runScript(actions) {
  const log = [];
  const rt = createRuntime();
  let api = null;
  function Counter(props) {
    const [count, setCount] = rt.useState(0);
    const [label, setLabel] = rt.useState("a");
    rt.useEffect(() => {
      log.push("effect:count=" + count);
      return () => log.push("cleanup:count=" + count);
    }, [count]);
    rt.useEffect(() => {
      log.push("effect:mount");
      return () => log.push("cleanup:unmount");
    }, []);
    rt.useEffect(() => { log.push("effect:always"); });
    api = { setCount, setLabel };
    log.push("render:" + props.tag + ":" + count + ":" + label);
  }
  for (const [name, arg] of actions) {
    if (name === "render") rt.render(Counter, { tag: arg });
    else if (name === "set") api.setCount(arg);
    else if (name === "inc") api.setCount((c) => c + 1);
    else if (name === "label") api.setLabel(arg);
    else if (name === "flush") log.push("flush:" + rt.flush());
    else if (name === "unmount") rt.unmount();
  }
  return log;
}
'''

DEPS_DRIVER = r'''
// --- driver (provided, do not change) ---
// JSON cannot carry NaN, -0 or shared references, so the tests use tokens:
// "$NaN" -> NaN, "$-0" -> -0, "$ref:x" -> one shared object per name.
function checkDeps(prev, next) {
  const shared = {};
  const revive = (v) => {
    if (v === "$NaN") return NaN;
    if (v === "$-0") return -0;
    if (typeof v === "string" && v.startsWith("$ref:")) return shared[v] || (shared[v] = { name: v });
    return v;
  };
  const fix = (deps) => (Array.isArray(deps) ? deps.map(revive) : deps);
  return depsChanged(fix(prev), fix(next));
}
'''

MEMO_DRIVER = r'''
// --- driver (provided, do not change) ---
// A prop value "$ref:x" stands for one shared object per name (the same reference every time).
function memoRenders(propsList) {
  const shared = {};
  const revive = (v) => (typeof v === "string" && v.startsWith("$ref:") ? shared[v] || (shared[v] = { name: v }) : v);
  let renders = 0;
  const Row = memo((props) => { renders++; return "render#" + renders; });
  return propsList.map((p) => {
    const props = {};
    for (const k of Object.keys(p)) props[k] = revive(p[k]);
    return Row(props);
  });
}
'''

HOOKS_SOLUTION = r'''function createRuntime() {
  let hooks = [];
  let cursor = 0;
  let dirty = false;
  let current = null;
  let pending = [];

  function useState(initial) {
    const i = cursor++;
    if (!hooks[i]) hooks[i] = { value: initial };
    const slot = hooks[i];
    const set = (next) => {
      const value = typeof next === "function" ? next(slot.value) : next;
      if (!Object.is(value, slot.value)) {
        slot.value = value;
        dirty = true;
      }
    };
    return [slot.value, set];
  }

  function useEffect(fn, deps) {
    const i = cursor++;
    const first = !hooks[i];
    if (first) hooks[i] = { deps: undefined, cleanup: undefined };
    const slot = hooks[i];
    const changed = first || !deps || !slot.deps || deps.length !== slot.deps.length ||
      deps.some((d, j) => !Object.is(d, slot.deps[j]));
    if (changed) pending.push({ slot, fn });
    slot.deps = deps;
  }

  function render(component, props) {
    current = { component, props };
    cursor = 0;
    pending = [];
    dirty = false;
    component(props);
    const toRun = pending;
    for (const { slot } of toRun) {
      if (typeof slot.cleanup === "function") slot.cleanup();
      slot.cleanup = undefined;
    }
    for (const { slot, fn } of toRun) {
      const result = fn();
      slot.cleanup = typeof result === "function" ? result : undefined;
    }
  }

  function flush() {
    if (!dirty || !current) return false;
    render(current.component, current.props);
    return true;
  }

  function unmount() {
    for (const slot of hooks) if (slot && typeof slot.cleanup === "function") slot.cleanup();
    hooks = [];
    current = null;
    dirty = false;
  }

  return { useState, useEffect, render, flush, unmount };
}
'''

PROBLEMS = [
# ---------------------------------------------------------------------------------------------
dict(
    id="react-create-element", title="createElement: build a virtual DOM tree", difficulty="Easy", pattern="Virtual DOM",
    kind="js", entry="buildTree",
    description=r"""
JSX is syntax sugar for function calls that return plain objects. Write that function:
`createElement(type, props, ...children)` returns

```
{ type, key, props: { ...otherProps, children: [ ...normalised children ] } }
```

Rules:

- `props` may be `null`. `key` is taken **out of** props: `String(props.key)` when present, otherwise `null`
- children may be nested arrays (as produced by `list.map(...)`): flatten them completely
- `null`, `undefined`, `true` and `false` render nothing: drop them
- strings and numbers become text elements: `{ type: "TEXT", key: null, props: { nodeValue: String(value), children: [] } }`.
  Note that `0` and `""` are kept. Only the four values above are skipped
- anything else (an element object) is kept as it is
- `props.children` is always an array, possibly empty

The driver converts a JSON description into nested `createElement` calls.

**Example:** `createElement("p", {id: "x", key: 7}, "Hi ", null, 3)` →
`{type:"p", key:"7", props:{id:"x", children:[text("Hi "), text("3")]}}`
""",
    starter="function createElement(type, props, ...children) {\n  // return { type, key, props: { ..., children: [...] } }\n}\n" + BUILD_DRIVER,
    solution=r'''function createElement(type, props, ...children) {
  const { key, ...rest } = props || {};
  const flat = [];
  const add = (child) => {
    if (Array.isArray(child)) child.forEach(add);
    else if (child === null || child === undefined || typeof child === "boolean") return;
    else if (typeof child === "string" || typeof child === "number") {
      flat.push({ type: "TEXT", key: null, props: { nodeValue: String(child), children: [] } });
    } else flat.push(child);
  };
  children.forEach(add);
  return { type, key: key === undefined || key === null ? null : String(key), props: { ...rest, children: flat } };
}
''' + BUILD_DRIVER,
    tests=[
        [{"t": "p", "p": {"id": "x", "key": 7}, "c": ["Hi ", None, 3]}],
        [{"t": "br", "p": None, "c": []}],
        [{"t": "div", "p": {"className": "box"}}],
        [{"t": "ul", "p": None, "c": [[{"t": "li", "p": {"key": "a"}, "c": ["A"]}, {"t": "li", "p": {"key": "b"}, "c": ["B"]}]]}],
        [{"t": "span", "p": None, "c": [0]}],
        [{"t": "span", "p": None, "c": [False, True, None, ""]}],
        [{"t": "div", "p": None, "c": ["a", ["b", ["c", [None, "d"]]], "e"]}],
        [{"t": "h1", "p": {"key": 0, "title": "t"}, "c": ["zero key"]}],
        [{"t": "section", "p": {"key": None}, "c": [{"t": "p", "p": None, "c": ["x"]}, False, {"t": "p", "p": None, "c": [1.5]}]}],
        [{"t": "App", "p": {"user": {"name": "Ann"}, "count": 2}, "c": [{"t": "Header", "p": {"title": "Hi"}}]}],
        [{"t": "ol", "p": None, "c": [[], [[]], "only"]}],
        [{"t": "p", "p": {"children": "ignored?"}, "c": ["real"]}],
    ],
    wrong_solutions=[
        "function createElement(type, props, ...children) {\n  return { type, key: props && props.key ? String(props.key) : null, props: { ...props, children: children.flat().filter(Boolean) } };\n}\n" + BUILD_DRIVER,
        r'''function createElement(type, props, ...children) {
  const { key, ...rest } = props || {};
  const flat = children.flat(Infinity).filter((c) => c)
    .map((c) => (typeof c === "object" ? c : { type: "TEXT", key: null, props: { nodeValue: String(c), children: [] } }));
  return { type, key: key == null ? null : String(key), props: { ...rest, children: flat } };
}
''' + BUILD_DRIVER,
    ],
    guide=G(
        prereqs="Rest/spread syntax, recursion. Lesson *JSX, components and props*.",
        intuition="An element is a description, not a DOM node: a type, some props and its children. The only real work is "
                  "tidying the children so later stages can treat them uniformly.",
        hints=["Destructure `key` away from the rest of the props; remember `props` can be `null`.",
               "Write a small recursive `add(child)` that handles arrays by calling itself on each entry.",
               "Skip exactly four values: `null`, `undefined`, `true`, `false`. Test with `0`."],
        brute_force="`children.flat().filter(Boolean)` flattens one level only and throws away `0` and `\"\"`. The same mistake in JSX "
                    "(`{count && <Badge/>}`) is why a stray `0` shows up on screen: React itself keeps numbers.",
        approach="1. Split props into `key` and the rest.\n2. Walk the children depth-first, pushing text elements and element objects.\n"
                 "3. Return the element with `children` overriding any `children` that came in through props.\n\n"
                 "**Dry run** `(\"p\", {key:7}, \"Hi \", null, 3)`: key `\"7\"`; children → text `Hi `, skip `null`, text `3`.",
        complexity="O(number of children including nested arrays).",
        pitfalls="Treating key `0` as missing; dropping `0` children; leaving `key` inside props (React never passes it to the component).",
        follow_up="Real React also records `ref`, the owner and a `$$typeof` marker that blocks JSON-injected elements.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-render-to-string", title="Render a virtual tree to an HTML string", difficulty="Medium", pattern="Virtual DOM",
    kind="js", entry="renderToString",
    description=r"""
Server rendering turns the element tree into HTML text. Write `renderToString(node)`.

**Nodes**

- `null`, `true`, `false` → `""`
- a string or number → its text with `&`, `<`, `>` escaped as `&amp;`, `&lt;`, `&gt;`
- an array → the concatenation of its items
- `{ type, props }` → an element. `props.children` may be missing, a single node or an array
- type `"Fragment"` renders only its children

**Attributes**, in the order the props appear:

- skip `children`, `key`, `ref`, and any prop whose value is `null` or `false`
- `className` is written as `class`, `htmlFor` as `for`
- value `true` → the bare name (` disabled`)
- `style` given as an object → `style="font-size:12px;color:red"`: camelCase names become kebab-case, pairs are joined
  with `;`, values are used as they are
- everything else → ` name="value"` with `&`, `<`, `>` and `"` (`&quot;`) escaped

**Void elements** `br`, `hr`, `img`, `input`, `meta`, `link` are written as `<br/>` (attributes allowed, never children).
Other elements are `<type attrs>children</type>`.

**Example:** `{type:"a", props:{href:"/x?a=1&b=2", className:"link", children:["Tom & ", {type:"b", props:{children:"Jerry"}}]}}`
→ `<a href="/x?a=1&amp;b=2" class="link">Tom &amp; <b>Jerry</b></a>`
""",
    starter="function renderToString(node) {\n  // recursive: text, arrays, elements\n}\n",
    solution=r'''function renderToString(node) {
  const VOID = new Set(["br", "hr", "img", "input", "meta", "link"]);
  const text = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const attr = (s) => text(s).replace(/"/g, "&quot;");
  const kebab = (s) => s.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
  if (node === null || node === undefined || typeof node === "boolean") return "";
  if (typeof node === "string" || typeof node === "number") return text(node);
  if (Array.isArray(node)) return node.map(renderToString).join("");
  const props = node.props || {};
  const inner = renderToString(props.children === undefined ? null : props.children);
  if (node.type === "Fragment") return inner;
  let attrs = "";
  for (const name of Object.keys(props)) {
    const value = props[name];
    if (name === "children" || name === "key" || name === "ref" || value === null || value === false) continue;
    const out = name === "className" ? "class" : name === "htmlFor" ? "for" : name;
    if (value === true) attrs += " " + out;
    else if (name === "style" && typeof value === "object") {
      attrs += ' style="' + attr(Object.keys(value).map((k) => kebab(k) + ":" + value[k]).join(";")) + '"';
    } else attrs += " " + out + '="' + attr(value) + '"';
  }
  if (VOID.has(node.type)) return "<" + node.type + attrs + "/>";
  return "<" + node.type + attrs + ">" + inner + "</" + node.type + ">";
}
''',
    tests=[
        [{"type": "a", "props": {"href": "/x?a=1&b=2", "className": "link", "children": ["Tom & ", {"type": "b", "props": {"children": "Jerry"}}]}}],
        ["plain <text> & more"],
        [None],
        [42],
        [[1, " ", True, None, "two", False]],
        [{"type": "br", "props": {}}],
        [{"type": "img", "props": {"src": "a.png", "alt": "A \"quoted\" cat", "key": "k1"}}],
        [{"type": "input", "props": {"type": "checkbox", "checked": True, "disabled": False, "value": None, "id": "c"}}],
        [{"type": "label", "props": {"htmlFor": "c", "children": "Agree"}}],
        [{"type": "p", "props": {"style": {"fontSize": "12px", "color": "red", "backgroundColor": "#fff"}, "children": 0}}],
        [{"type": "Fragment", "props": {"children": [{"type": "h1", "props": {"children": "Title"}}, {"type": "p", "props": {}}]}}],
        [{"type": "ul", "props": {"children": [[{"type": "li", "props": {"key": "a", "children": "A"}}, {"type": "li", "props": {"key": "b", "children": ["B", 2]}}]]}}],
        [{"type": "div"}],
        [{"type": "div", "props": {"title": "a<b>c", "data-id": 7, "children": {"type": "span", "props": {"children": "<script>"}}}}],
    ],
    wrong_solutions=[
        r'''function renderToString(node) {
  if (node === null || node === undefined || typeof node === "boolean") return "";
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(renderToString).join("");
  const props = node.props || {};
  const inner = renderToString(props.children === undefined ? null : props.children);
  if (node.type === "Fragment") return inner;
  let attrs = "";
  for (const name of Object.keys(props)) {
    if (name === "children") continue;
    attrs += " " + name + '="' + props[name] + '"';
  }
  return "<" + node.type + attrs + ">" + inner + "</" + node.type + ">";
}
''',
        r'''function renderToString(node) {
  const text = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  if (!node) return "";
  if (typeof node !== "object") return text(node);
  if (Array.isArray(node)) return node.map(renderToString).join("");
  const props = node.props || {};
  const inner = renderToString(props.children);
  if (node.type === "Fragment") return inner;
  let attrs = "";
  for (const name of Object.keys(props)) {
    const v = props[name];
    if (["children", "key", "ref"].includes(name) || v === null || v === false) continue;
    const out = name === "className" ? "class" : name === "htmlFor" ? "for" : name;
    attrs += v === true ? " " + out : " " + out + '="' + text(v).replace(/"/g, "&quot;") + '"';
  }
  return "<" + node.type + attrs + ">" + inner + "</" + node.type + ">";
}
''',
    ],
    guide=G(
        prereqs="Recursion over trees; lesson *The virtual DOM and reconciliation*.",
        intuition="Rendering to a string is a post-order walk: render the children to text, then wrap that text in the element's "
                  "opening and closing tags. Escaping is what keeps data from becoming markup.",
        hints=["Handle the four non-element cases first (nothing, text, array, fragment).",
               "Build the attribute string in a loop over `Object.keys(props)` with a `continue` for the skipped names and values.",
               "Escape `&` before `<` and `>`, otherwise you double-escape your own entities."],
        brute_force="Concatenate values without escaping. It looks right until a user names themselves `<script>`, at which point "
                    "you have built a cross-site scripting hole.",
        approach="1. Leaf cases.\n2. Render children.\n3. Fragment → children only.\n4. Attributes with renames, booleans and style.\n"
                 "5. Void elements self-close.\n\n"
                 "**Dry run** `{type:\"p\", props:{style:{fontSize:\"12px\"}, children:0}}`: children `0` → `\"0\"`; style → `font-size:12px`; "
                 "result `<p style=\"font-size:12px\">0</p>`.",
        complexity="O(size of the tree + length of the output).",
        pitfalls="`if (!node) return \"\"` silently drops the number `0`. Booleans as attributes need the bare-name form. "
                 "Void elements must not get a closing tag.",
        follow_up="Hydration is the reverse trip: React walks existing HTML and attaches event handlers instead of creating nodes.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-keyed-list-diff", title="Keyed list diff: which children move?", difficulty="Medium", pattern="Reconciliation",
    kind="js", entry="diffKeys",
    description=r"""
When a list re-renders, React matches old and new children by `key` and works out the DOM operations. Implement the
same single-pass strategy React uses. `diffKeys(oldKeys, newKeys)` (both arrays of unique strings) returns

```
{ remove: [keys], insert: [{ key, index }], move: [{ key, index }] }
```

- `remove`: keys in the old list that are missing from the new one, in old order
- walk the new list from left to right keeping `lastPlacedIndex` (start at `-1`), the largest **old index** of any
  reused child so far:
  - a key that did not exist before → `insert` with its new index
  - a reused key whose old index is **less than** `lastPlacedIndex` → `move` with its new index
  - otherwise it stays where it is and `lastPlacedIndex` becomes its old index

**Examples**

`diffKeys(["a","b","c"], ["a","c","b"])` → `{remove:[], insert:[], move:[{key:"b", index:2}]}`

`diffKeys(["a","b","c","d"], ["d","a","b","c"])` → three moves (`a`, `b`, `c`): moving the last item to the front
is the worst case for this strategy, although a human would move only `d`.
""",
    starter="function diffKeys(oldKeys, newKeys) {\n  return { remove: [], insert: [], move: [] };\n}\n",
    solution=r'''function diffKeys(oldKeys, newKeys) {
  const oldIndex = new Map(oldKeys.map((k, i) => [k, i]));
  const kept = new Set(newKeys);
  const remove = oldKeys.filter((k) => !kept.has(k));
  const insert = [];
  const move = [];
  let lastPlacedIndex = -1;
  newKeys.forEach((key, index) => {
    if (!oldIndex.has(key)) insert.push({ key, index });
    else if (oldIndex.get(key) < lastPlacedIndex) move.push({ key, index });
    else lastPlacedIndex = oldIndex.get(key);
  });
  return { remove, insert, move };
}
''',
    tests=[
        [["a", "b", "c"], ["a", "c", "b"]],
        [["a", "b", "c", "d"], ["d", "a", "b", "c"]],
        [["a", "b", "c", "d"], ["b", "c", "d", "a"]],
        [[], []],
        [[], ["x", "y"]],
        [["x", "y"], []],
        [["a", "b", "c"], ["a", "b", "c"]],
        [["a", "b", "c"], ["c", "b", "a"]],
        [["a", "b", "c"], ["z", "a", "b", "c"]],
        [["a", "b", "c"], ["a", "b", "c", "z"]],
        [["a", "b", "c", "d", "e"], ["e", "x", "c", "a", "y"]],
        [["a", "b"], ["c", "d"]],
        [["a", "b", "c", "d"], ["a", "d"]],
        [[str(i) for i in range(200)], [str(i) for i in range(199, -1, -1)]],
    ],
    wrong_solutions=[
        r'''function diffKeys(oldKeys, newKeys) {
  const oldIndex = new Map(oldKeys.map((k, i) => [k, i]));
  const kept = new Set(newKeys);
  const insert = [], move = [];
  newKeys.forEach((key, index) => {
    if (!oldIndex.has(key)) insert.push({ key, index });
    else if (oldIndex.get(key) !== index) move.push({ key, index });
  });
  return { remove: oldKeys.filter((k) => !kept.has(k)), insert, move };
}
''',
        r'''function diffKeys(oldKeys, newKeys) {
  const oldIndex = new Map(oldKeys.map((k, i) => [k, i]));
  const kept = new Set(newKeys);
  const insert = [], move = [];
  let last = -1;
  newKeys.forEach((key, index) => {
    if (!oldIndex.has(key)) insert.push({ key, index });
    else { if (oldIndex.get(key) < last) move.push({ key, index }); last = oldIndex.get(key); }
  });
  return { remove: oldKeys.filter((k) => !kept.has(k)), insert, move };
}
''',
    ],
    guide=G(
        prereqs="`Map`/`Set`; lessons *Lists, keys and events* and *The virtual DOM and reconciliation*.",
        intuition="Reused children that already appear in increasing old-index order can stay put. `lastPlacedIndex` is the high-water "
                  "mark of that increasing run; anything that used to sit before the mark has been overtaken and must be moved after it.",
        hints=["Build `key → old index` once so lookups are O(1).",
               "Update `lastPlacedIndex` only when the child stays; a moved child does not raise the mark.",
               "Removals are independent of the walk: filter the old keys by membership in the new set."],
        brute_force="Flag every child whose index changed. Inserting one row at the top would then 'move' the entire list, the very "
                    "cost keys exist to avoid.",
        approach="**Dry run** old `[a,b,c,d]`, new `[d,a,b,c]`: `d` old 3 ≥ −1 → stays, mark 3. `a` old 0 < 3 → move. `b` 1 < 3 → move. "
                 "`c` 2 < 3 → move.\n\nReverse case new `[b,c,d,a]`: `b` stays (mark 1), `c` stays (2), `d` stays (3), `a` 0 < 3 → one move.",
        complexity="O(n + m) time, O(n) space.",
        pitfalls="Raising the mark for moved children (the second wrong solution) under-counts moves in reversals. "
                 "Comparing against the new index instead of old indices confuses 'shifted because of an insert' with 'moved'.",
        follow_up="Finding the *minimum* number of moves needs the longest increasing subsequence, which some other frameworks compute.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-vdom-diff", title="Diff two virtual trees into patches", difficulty="Hard", pattern="Reconciliation",
    kind="js", entry="diff",
    description=r"""
Write `diff(oldTree, newTree)` that returns the list of patches turning the old tree into the new one.

A node is either a **string** (text) or `{ type, props, children }` (`props` is an object of primitives, `children`
an array; either may be missing, meaning empty). Children are matched **by position** (no keys here).
A `path` is the list of child indexes from the root (`[]` is the root itself).

Compare two nodes at `path`:

1. both strings: if different emit `{op:"TEXT", path, value: newText}`
2. one is a string and the other is not, or the `type` differs: emit `{op:"REPLACE", path, node: newNode}` and do
   **not** look inside
3. same type:
   1. for each prop name of the new node in **alphabetical** order whose value differs from the old one (or is new):
      `{op:"SET_PROP", path, name, value}`
   2. for each prop name of the old node in alphabetical order that the new node lacks: `{op:"REMOVE_PROP", path, name}`
   3. recurse into the children present in both, in index order, at `[...path, i]`
   4. for each extra new child, in order: `{op:"APPEND", path, node}`
   5. for each extra old child, **from the last index down**: `{op:"REMOVE_CHILD", path, index}`

Return the patches in exactly the order they are produced.

**Example:** old `{type:"p", props:{id:"a"}, children:["hi"]}`, new `{type:"p", props:{id:"b"}, children:["yo", "!"]}` →
`[{op:"SET_PROP",path:[],name:"id",value:"b"}, {op:"TEXT",path:[0],value:"yo"}, {op:"APPEND",path:[],node:"!"}]`
""",
    starter="function diff(oldTree, newTree) {\n  const patches = [];\n  // walk both trees together\n  return patches;\n}\n",
    solution=r'''function diff(oldTree, newTree) {
  const patches = [];
  const walk = (a, b, path) => {
    const textA = typeof a === "string";
    const textB = typeof b === "string";
    if (textA && textB) {
      if (a !== b) patches.push({ op: "TEXT", path, value: b });
      return;
    }
    if (textA || textB || a.type !== b.type) {
      patches.push({ op: "REPLACE", path, node: b });
      return;
    }
    const pa = a.props || {};
    const pb = b.props || {};
    for (const name of Object.keys(pb).sort()) {
      if (!(name in pa) || pa[name] !== pb[name]) patches.push({ op: "SET_PROP", path, name, value: pb[name] });
    }
    for (const name of Object.keys(pa).sort()) {
      if (!(name in pb)) patches.push({ op: "REMOVE_PROP", path, name });
    }
    const ca = a.children || [];
    const cb = b.children || [];
    const common = Math.min(ca.length, cb.length);
    for (let i = 0; i < common; i++) walk(ca[i], cb[i], [...path, i]);
    for (let i = common; i < cb.length; i++) patches.push({ op: "APPEND", path, node: cb[i] });
    for (let i = ca.length - 1; i >= cb.length; i--) patches.push({ op: "REMOVE_CHILD", path, index: i });
  };
  walk(oldTree, newTree, []);
  return patches;
}
''',
    tests=[
        [{"type": "p", "props": {"id": "a"}, "children": ["hi"]}, {"type": "p", "props": {"id": "b"}, "children": ["yo", "!"]}],
        ["same", "same"],
        ["old", "new"],
        ["text", {"type": "b", "children": ["text"]}],
        [{"type": "div", "children": [{"type": "p", "children": ["deep"]}]}, {"type": "section", "children": [{"type": "p", "children": ["deep"]}]}],
        [{"type": "ul", "children": [{"type": "li", "children": ["a"]}, {"type": "li", "children": ["b"]}, {"type": "li", "children": ["c"]}]},
         {"type": "ul", "children": [{"type": "li", "children": ["a"]}]}],
        [{"type": "ul", "children": []}, {"type": "ul", "children": [{"type": "li", "children": ["a"]}, {"type": "li", "children": ["b"]}]}],
        [{"type": "a", "props": {"href": "/a", "title": "t", "target": "_blank"}}, {"type": "a", "props": {"href": "/a", "class": "x", "aria-label": "go"}}],
        [{"type": "div", "props": {"hidden": False}, "children": []}, {"type": "div", "props": {"hidden": False}}],
        [{"type": "div", "children": [{"type": "h1", "props": {"class": "t"}, "children": ["Title"]}, {"type": "p", "children": ["one", "two"]}, "tail"]},
         {"type": "div", "children": [{"type": "h1", "props": {"class": "big"}, "children": ["Title!"]}, {"type": "p", "children": ["one"]}, {"type": "i", "children": []}, "new"]}],
        [{"type": "ul", "children": [{"type": "li", "children": ["a"]}, {"type": "li", "children": ["b"]}]},
         {"type": "ul", "children": [{"type": "li", "children": ["z"]}, {"type": "li", "children": ["a"]}, {"type": "li", "children": ["b"]}]}],
        [{"type": "input", "props": {"value": "", "n": 0}}, {"type": "input", "props": {"value": "0", "n": None}}],
        [{"type": "x", "children": [{"type": "y", "children": [{"type": "z", "children": ["1", "2", "3"]}]}]},
         {"type": "x", "children": [{"type": "y", "children": [{"type": "z", "children": ["1", "9"]}]}]}],
    ],
    wrong_solutions=[
        r'''function diff(oldTree, newTree) {
  const patches = [];
  const walk = (a, b, path) => {
    if (typeof a === "string" || typeof b === "string") {
      if (a !== b) patches.push(typeof b === "string" && typeof a === "string" ? { op: "TEXT", path, value: b } : { op: "REPLACE", path, node: b });
      return;
    }
    if (a.type !== b.type) { patches.push({ op: "REPLACE", path, node: b }); return; }
    const pa = a.props || {}, pb = b.props || {};
    for (const name of Object.keys(pb).sort()) if (pa[name] !== pb[name]) patches.push({ op: "SET_PROP", path, name, value: pb[name] });
    const ca = a.children || [], cb = b.children || [];
    const common = Math.min(ca.length, cb.length);
    for (let i = 0; i < common; i++) walk(ca[i], cb[i], [...path, i]);
    for (let i = common; i < cb.length; i++) patches.push({ op: "APPEND", path, node: cb[i] });
    for (let i = cb.length; i < ca.length; i++) patches.push({ op: "REMOVE_CHILD", path, index: i });
  };
  walk(oldTree, newTree, []);
  return patches;
}
''',
        r'''function diff(oldTree, newTree) {
  return JSON.stringify(oldTree) === JSON.stringify(newTree) ? [] : [{ op: "REPLACE", path: [], node: newTree }];
}
''',
    ],
    guide=G(
        prereqs="Tree recursion; lesson *The virtual DOM and reconciliation*.",
        intuition="React's two heuristics in miniature: a different type means 'throw the subtree away', the same type means "
                  "'keep the node, update its attributes, then compare children pairwise'.",
        hints=["Decide the three cases (text/text, replace, same type) before touching props.",
               "Sort the prop names so the output order is deterministic.",
               "Removing children from the end means earlier indexes stay valid while the patches are applied."],
        brute_force="Replace the root whenever anything differs. Always correct, but it destroys input focus, scroll position and "
                    "every child's state, and does maximal DOM work.",
        approach="Recursive `walk(a, b, path)` pushing onto one shared array, following the numbered rules in order.\n\n"
                 "**Dry run** (example): same type `p`; prop `id` differs → SET_PROP. Children: index 0 `hi` vs `yo` → TEXT at `[0]`. "
                 "New has one extra child → APPEND `!`.",
        complexity="O(n) in the number of nodes compared; a replaced subtree is not visited.",
        pitfalls="Recursing into a replaced node emits patches for nodes that no longer exist. Removing children front-to-back shifts "
                 "the remaining indexes. The index-based matching makes a prepend rewrite every row (see the test with `z`), which "
                 "is the motivation for keys.",
        follow_up="Extend the node shape with `key` and reuse your `diffKeys` to emit MOVE patches.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-hooks-runtime", title="A tiny hooks runtime", difficulty="Hard", pattern="Hooks internals",
    kind="js", entry="runScript",
    description=r"""
Hooks are not magic: React keeps an array of slots per component and a cursor that advances on every hook call,
which is why hooks must be called in the same order on every render.

Write `createRuntime()` returning `{ useState, useEffect, render, flush, unmount }` for **one** component instance.

- `useState(initial)` → `[value, setValue]`. The slot is created on the first render only.
  `setValue(next)` accepts a value or an updater function `(previous) => next` (applied to the latest queued value).
  If the result differs from the stored value (`Object.is`) store it and mark the runtime **dirty**; it never renders
  by itself
- `useEffect(fn, deps)` registers an effect. It is **scheduled** for this render when it is the first render, when
  `deps` is not an array, or when any dependency differs from last time (`Object.is`, also when the length differs)
- `render(component, props)` resets the cursor, clears the dirty flag, calls `component(props)`, then (the "commit")
  first runs the previous cleanup of **every** scheduled effect, in hook order, then runs every scheduled effect in
  hook order, storing a returned function as its cleanup
- `flush()`: if dirty, render again with the same component and props and return `true`; otherwise return `false`
- `unmount()`: run all remaining cleanups in hook order and forget everything

The provided driver defines a `Counter` component with two state hooks and three effects (`[count]`, `[]`, no array),
runs a script of actions and returns the log. Read the driver carefully: it is the specification of what gets logged.

**Example:** `[["render","A"],["inc"],["inc"],["flush"]]` →
`["render:A:0:a","effect:count=0","effect:mount","effect:always","render:A:2:a","cleanup:count=0","effect:count=2","effect:always","flush:true"]`
""",
    starter="function createRuntime() {\n  let hooks = [];   // one slot per hook call\n  let cursor = 0;\n\n  function useState(initial) {}\n  function useEffect(fn, deps) {}\n  function render(component, props) {}\n  function flush() {}\n  function unmount() {}\n\n  return { useState, useEffect, render, flush, unmount };\n}\n" + HOOKS_DRIVER,
    solution=HOOKS_SOLUTION + HOOKS_DRIVER,
    tests=[
        [[["render", "A"], ["inc"], ["inc"], ["flush"]]],
        [[["render", "A"]]],
        [[["render", "A"], ["flush"]]],
        [[["render", "A"], ["set", 0], ["flush"]]],
        [[["render", "A"], ["label", "b"], ["flush"]]],
        [[["render", "A"], ["set", 5], ["set", 0], ["flush"]]],
        [[["render", "A"], ["set", 5], ["inc"], ["label", "z"], ["flush"], ["flush"]]],
        [[["render", "A"], ["render", "B"]]],
        [[["render", "A"], ["inc"], ["flush"], ["unmount"]]],
        [[["render", "A"], ["unmount"], ["render", "B"]]],
        [[["render", "A"], ["inc"], ["flush"], ["inc"], ["flush"], ["label", "q"], ["flush"], ["unmount"]]],
        [[["render", "A"], ["inc"], ["render", "C"], ["flush"]]],
        [[["render", "A"], ["unmount"], ["flush"]]],
    ],
    wrong_solutions=[
        HOOKS_SOLUTION.replace("const changed = first || !deps || !slot.deps || deps.length !== slot.deps.length ||\n      deps.some((d, j) => !Object.is(d, slot.deps[j]));", "const changed = true;") + HOOKS_DRIVER,
        HOOKS_SOLUTION.replace("if (!Object.is(value, slot.value)) {", "{") + HOOKS_DRIVER,
        HOOKS_SOLUTION.replace("if (typeof slot.cleanup === \"function\") slot.cleanup();\n      slot.cleanup = undefined;", "slot.cleanup = undefined;") + HOOKS_DRIVER,
        HOOKS_SOLUTION.replace("const value = typeof next === \"function\" ? next(slot.value) : next;", "const value = typeof next === \"function\" ? next(initial) : next;") + HOOKS_DRIVER,
    ],
    guide=G(
        prereqs="Closures; lessons *State with useState*, *useEffect* and *Render, commit and batching*.",
        intuition="State lives outside the component function in an array. Each render replays the hook calls in order, so call "
                  "number *i* always finds slot *i*. Effects are just callbacks remembered during render and executed after it.",
        hints=["Start with `useState` and `render` only; get `render:A:0:a` logged, then make `inc` + `flush` log `render:A:1:a`.",
               "In `useEffect`, do not run anything. Push `{ slot, fn }` onto a per-render list when the deps changed.",
               "`render` needs two loops over that list: all old cleanups first, then all new effects."],
        brute_force="Run every effect after every render and ignore dependencies. Correct for effects without an array, wrong for "
                    "`[]` (the 'mount' effect would resubscribe on every render).",
        approach="1. `hooks[]`, `cursor`, `dirty`, `current`, `pending`.\n2. `useState`: slot by cursor; setter resolves updater, compares, stores, sets dirty.\n"
                 "3. `useEffect`: compare deps, queue.\n4. `render`: reset, call, cleanups, effects.\n5. `flush`/`unmount`.\n\n"
                 "**Dry run** of the example: first render logs the render line, then three effects. `inc` twice → value 2, dirty. "
                 "`flush` renders (`render:A:2:a`); `[count]` changed 0→2 so its cleanup (captured `0`) runs, then `effect:count=2`; "
                 "`[]` is skipped; the array-less effect runs; finally the driver logs `flush:true`.",
        complexity="O(number of hooks) per render.",
        pitfalls="Applying the updater to the initial value instead of the latest one; running an effect's cleanup immediately before "
                 "its own effect instead of all cleanups first; forgetting that the cleanup closes over the *old* render's values; "
                 "not resetting the cursor.",
        follow_up="Calling a hook inside an `if` would shift every later slot. Try it in the driver and watch state swap places.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-deps-changed", title="Should the effect run again?", difficulty="Easy", pattern="Hooks internals",
    kind="js", entry="checkDeps",
    description=r"""
After every render React decides, per effect, whether to run it again. Write `depsChanged(prev, next)`:

- `next` is not an array (the effect was written without a dependency array) → `true`
- `prev` is not an array (first render) → `true`
- different lengths → `true`
- otherwise `true` when at least one position differs according to `Object.is`, else `false`

`Object.is` is like `===` except that `NaN` equals `NaN` and `0` does not equal `-0`. Objects, arrays and functions
are compared by reference, so two look-alike literals are different.

The driver lets the JSON tests express awkward values: `"$NaN"`, `"$-0"`, and `"$ref:name"` (the same object each
time the same name is used).

**Examples:** `([1,"a"], [1,"a"])` → `false` · `([{}], [{}])` → `true` · `(["$ref:u"], ["$ref:u"])` → `false`
""",
    starter="function depsChanged(prev, next) {\n  return true;\n}\n" + DEPS_DRIVER,
    solution=r'''function depsChanged(prev, next) {
  if (!Array.isArray(next) || !Array.isArray(prev)) return true;
  if (prev.length !== next.length) return true;
  return next.some((value, i) => !Object.is(value, prev[i]));
}
''' + DEPS_DRIVER,
    tests=[
        [[1, "a"], [1, "a"]],
        [[{}], [{}]],
        [["$ref:u"], ["$ref:u"]],
        [None, [1]],
        [[1], None],
        [None, None],
        [[], []],
        [["$NaN"], ["$NaN"]],
        [[0], ["$-0"]],
        [["$ref:a"], ["$ref:b"]],
        [[1, 2], [1, 2, 3]],
        [[1, "1"], [1, 1]],
        [["a", True, None], ["a", True, None]],
        [[[1]], [[1]]],
        [["$ref:a", 3, "x"], ["$ref:a", 3, "y"]],
        [[None], [False]],
    ],
    wrong_solutions=[
        "function depsChanged(prev, next) {\n  if (!Array.isArray(next) || !Array.isArray(prev)) return true;\n  if (prev.length !== next.length) return true;\n  return next.some((v, i) => v !== prev[i]);\n}\n" + DEPS_DRIVER,
        "function depsChanged(prev, next) {\n  if (!Array.isArray(next) || !Array.isArray(prev)) return true;\n  return JSON.stringify(prev) !== JSON.stringify(next);\n}\n" + DEPS_DRIVER,
        "function depsChanged(prev, next) {\n  if (!Array.isArray(prev)) return true;\n  if (!Array.isArray(next)) return false;\n  return prev.length !== next.length || next.some((v, i) => !Object.is(v, prev[i]));\n}\n" + DEPS_DRIVER,
    ],
    guide=G(
        prereqs="Lesson *useEffect and its dependency rules*.",
        intuition="The dependency array is compared slot by slot with identity semantics. Nothing looks inside objects.",
        hints=["Two early returns cover 'no array' and 'first render'.", "Use `Object.is`, not `===`.",
               "`some` returns `false` for an empty array, which is exactly the `[]` case: never changed."],
        brute_force="Stringify both arrays and compare. It claims `[{}]` equals `[{}]` (React says changed) and cannot represent functions at all.",
        approach="Guard, guard, length, `some`.\n\n**Dry run** `([0], [-0])`: arrays, same length, `Object.is(-0, 0)` is false → changed.",
        complexity="O(n) for n dependencies.",
        pitfalls="`===` reports `NaN` as changed forever, which would loop an effect whose dependency is `NaN`.",
        follow_up="The same comparison drives `useMemo` and `useCallback`.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-stale-closure", title="Predict the stale closure", difficulty="Medium", pattern="Closures",
    kind="js", entry="simulate",
    description=r"""
A component shows a counter that starts at `0`. A button increments it (`onClick={() => setCount(count + 1)}`,
always created fresh, so a click always sees the latest render). An effect with an **empty dependency array**
starts an interval once, at mount. The interval callback is written in one of three ways:

| `mode` | interval callback | what it sees |
|---|---|---|
| `"stale"` | `setCount(count + 1)` | `count` from the **first** render, forever `0` |
| `"updater"` | `setCount(c => c + 1)` | the latest state, supplied by React |
| `"ref"` | `setCount(latest.current + 1)` where `latest.current = count` is assigned on every render | the latest rendered value |

There is also a "remind me" button: `onClick={() => setTimeout(() => log(count), 3000)}`. In `"stale"` and
`"updater"` mode the timeout logs the `count` of the render in which the button was clicked. In `"ref"` mode it is
written as `log(latest.current)` and logs the value current when the timeout fires.

Write `simulate(mode, events)`. Each event is one of `"click"`, `"tick"` (the interval fires), `"snapshot"` (the
remind-me button is clicked) or `"fire"` (all pending timeouts run, oldest first). Assume a re-render completes
after every event.

Return `{ counts, logged }`: the counter after each event, and every value logged by the timeouts.

**Example:** `simulate("stale", ["click","click","tick","click"])` → `{ counts: [1,2,1,2], logged: [] }`
""",
    starter="function simulate(mode, events) {\n  const counts = [];\n  const logged = [];\n  // ...\n  return { counts, logged };\n}\n",
    solution=r'''function simulate(mode, events) {
  let count = 0;
  const firstRenderCount = 0;
  const latest = { current: 0 };
  const timeouts = [];
  const counts = [];
  const logged = [];
  for (const event of events) {
    if (event === "click") {
      count = count + 1;
    } else if (event === "tick") {
      if (mode === "stale") count = firstRenderCount + 1;
      else if (mode === "updater") count = count + 1;
      else count = latest.current + 1;
    } else if (event === "snapshot") {
      const seen = count;
      timeouts.push(mode === "ref" ? () => latest.current : () => seen);
    } else if (event === "fire") {
      while (timeouts.length > 0) logged.push(timeouts.shift()());
    }
    latest.current = count;
    counts.push(count);
  }
  return { counts, logged };
}
''',
    tests=[
        ["stale", ["click", "click", "tick", "click"]],
        ["updater", ["click", "click", "tick", "click"]],
        ["ref", ["click", "click", "tick", "click"]],
        ["stale", []],
        ["stale", ["tick", "tick", "tick"]],
        ["updater", ["tick", "tick", "tick"]],
        ["stale", ["snapshot", "click", "click", "fire"]],
        ["ref", ["snapshot", "click", "click", "fire"]],
        ["updater", ["click", "snapshot", "tick", "snapshot", "tick", "fire", "fire"]],
        ["stale", ["click", "click", "click", "snapshot", "tick", "fire", "snapshot", "click", "fire"]],
        ["ref", ["tick", "snapshot", "tick", "snapshot", "click", "fire", "tick"]],
        ["stale", ["fire", "tick", "click", "tick", "tick", "click", "click"]],
    ],
    wrong_solutions=[
        r'''function simulate(mode, events) {
  let count = 0; const timeouts = []; const counts = []; const logged = [];
  for (const e of events) {
    if (e === "click" || e === "tick") count++;
    else if (e === "snapshot") { const seen = count; timeouts.push(mode === "ref" ? () => count : () => seen); }
    else if (e === "fire") while (timeouts.length) logged.push(timeouts.shift()());
    counts.push(count);
  }
  return { counts, logged };
}
''',
        r'''function simulate(mode, events) {
  let count = 0; const timeouts = []; const counts = []; const logged = [];
  for (const e of events) {
    if (e === "click") count++;
    else if (e === "tick") count = mode === "stale" ? 1 : count + 1;
    else if (e === "snapshot") timeouts.push(() => count);
    else if (e === "fire") while (timeouts.length) logged.push(timeouts.shift()());
    counts.push(count);
  }
  return { counts, logged };
}
''',
    ],
    guide=G(
        prereqs="Closures; lessons *useEffect* and *React interview essentials: renders, keys and closures*.",
        intuition="Every render is a snapshot with its own `count` constant. A function keeps the snapshot it was created in. "
                  "The interval callback was created once, in the first snapshot; the click handler is recreated every render.",
        hints=["In stale mode a tick does not add one to the current count. It *sets* the count to `0 + 1`.",
               "A snapshot stores a function. Decide at creation time whether it captures a number or reads the ref later.",
               "Update `latest.current` after every event, mirroring the assignment during render."],
        brute_force="Assume every callback sees current state (first wrong solution). That is how the code *reads*, and it is exactly the bug.",
        approach="Track `count`, a ref object and a queue of timeout closures.\n\n"
                 "**Dry run** stale, `click, click, tick, click`: 1, 2, then tick sets `0 + 1 = 1`, then click sees 1 → 2.",
        complexity="O(number of events).",
        pitfalls="Forgetting that in updater mode the *timeout* is still a snapshot: the updater form fixes writes, not reads.",
        follow_up="The lint rule `react-hooks/exhaustive-deps` would flag the stale version: `count` is used but not listed.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-memo-shallow", title="memo: skip renders with shallow props", difficulty="Medium", pattern="Memoisation",
    kind="js", entry="memoRenders",
    description=r"""
`React.memo(Component)` returns a component that re-uses its **last** output when the new props are shallowly equal
to the previous props.

Write `memo(render)`. It returns a function `(props) => output` that

- calls `render(props)` the first time
- on later calls compares `props` with the props of the **previous call** (not all earlier calls): same set of own
  keys and `Object.is` for every value
- if equal, returns the remembered output without calling `render`; otherwise calls `render`, remembers the new
  props and output

The driver wraps a component that returns `"render#N"` (N counts real renders) and feeds it a list of props objects.
A prop value `"$ref:name"` stands for one shared object per name; any other object in the JSON is a brand-new
reference each time, like an inline `{}` or `() => {}` in JSX.

**Example:** `[{id:1},{id:1},{id:2},{id:1}]` → `["render#1","render#1","render#2","render#3"]`
""",
    starter="function memo(render) {\n  return function Memoised(props) {\n    return render(props);\n  };\n}\n" + MEMO_DRIVER,
    solution=r'''function memo(render) {
  let hasPrevious = false;
  let previousProps = null;
  let previousOutput = null;
  const shallowEqual = (a, b) => {
    const keysA = Object.keys(a);
    const keysB = Object.keys(b);
    if (keysA.length !== keysB.length) return false;
    return keysA.every((k) => Object.prototype.hasOwnProperty.call(b, k) && Object.is(a[k], b[k]));
  };
  return function Memoised(props) {
    if (hasPrevious && shallowEqual(previousProps, props)) return previousOutput;
    previousOutput = render(props);
    previousProps = props;
    hasPrevious = true;
    return previousOutput;
  };
}
''' + MEMO_DRIVER,
    tests=[
        [[{"id": 1}, {"id": 1}, {"id": 2}, {"id": 1}]],
        [[]],
        [[{}]],
        [[{}, {}, {}]],
        [[{"user": {"name": "Ann"}}, {"user": {"name": "Ann"}}]],
        [[{"user": "$ref:ann"}, {"user": "$ref:ann"}, {"user": "$ref:bob"}, {"user": "$ref:bob"}]],
        [[{"a": 1}, {"a": 1, "b": 2}, {"a": 1, "b": 2}, {"a": 1}]],
        [[{"a": 1, "b": 2}, {"b": 2, "a": 1}]],
        [[{"onClick": "$ref:handler", "label": "Save"}, {"onClick": "$ref:handler", "label": "Save"}, {"onClick": "$ref:handler", "label": "Saved"}]],
        [[{"style": {"color": "red"}, "n": 1}, {"style": {"color": "red"}, "n": 1}]],
        [[{"a": 1}, {"b": 1}]],
        [[{"items": [1, 2]}, {"items": [1, 2]}, {"items": "$ref:list"}, {"items": "$ref:list"}]],
        [[{"v": 0}, {"v": False}, {"v": None}, {"v": None}]],
    ],
    wrong_solutions=[
        r'''function memo(render) {
  let prev = null, out = null;
  return (props) => {
    if (prev !== null && JSON.stringify(prev) === JSON.stringify(props)) return out;
    out = render(props); prev = props; return out;
  };
}
''' + MEMO_DRIVER,
        r'''function memo(render) {
  const cache = new Map();
  return (props) => {
    const k = Object.keys(props).sort().map((x) => x + "=" + String(props[x])).join("&");
    if (!cache.has(k)) cache.set(k, render(props));
    return cache.get(k);
  };
}
''' + MEMO_DRIVER,
        r'''function memo(render) {
  let prev = null, out = null;
  return (props) => {
    if (prev !== null && Object.keys(prev).every((k) => Object.is(prev[k], props[k]))) return out;
    out = render(props); prev = props; return out;
  };
}
''' + MEMO_DRIVER,
    ],
    guide=G(
        prereqs="Problem *Shallow equal vs deep equal*; lesson *memo, useMemo and useCallback*.",
        intuition="A one-entry cache keyed by 'the props I saw last time'. The comparison is cheap on purpose: one pass over the "
                  "keys, identity per value.",
        hints=["Keep three variables in the closure: whether there is a previous call, its props, its output.",
               "Compare key counts first, then each key with `Object.is`.",
               "Only the previous call matters. `A, B, A` renders three times."],
        brute_force="A deep comparison (or JSON) on every call. It skips more renders but can cost more than the render it saves, "
                    "and it is wrong for functions.",
        approach="**Dry run** `[{user:{…}}, {user:{…}}]` with inline objects: second call has the same keys but "
                 "`Object.is(obj1, obj2)` is false → render again. With `$ref:ann` both calls hold the same reference → skipped.",
        complexity="O(k) per call for k props.",
        pitfalls="Iterating only the previous keys misses a newly added prop. A history cache is not what React does and would leak memory.",
        follow_up="`React.memo(Component, arePropsEqual)` lets you replace the comparison; `useMemo`/`useCallback` exist to keep "
                  "object and function props referentially stable so this check can succeed.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-event-delegation", title="Event delegation: capture and bubble", difficulty="Medium", pattern="Events",
    kind="js", entry="dispatchEvent",
    description=r"""
React attaches one native listener per event type at the root and then **simulates** propagation through the
component tree itself. Reproduce that.

`dispatchEvent(tree, targetId, type)`:

- a node is `{ id, on: { ... }, children: [ ... ] }` (`on` and `children` may be missing)
- handlers are stored under the event name: `on.click` for the bubble phase and `on.clickCapture` for the capture phase
- find the path from the root to the node whose id is `targetId` (ids are unique). If there is none return `[]`
- **capture phase:** from the root down to the target, call each `typeCapture` handler
- **bubble phase:** from the target back up to the root, call each `type` handler
- calling a handler appends `"id:capture"` or `"id:bubble"` to the log. A handler whose value is `"stop"` also calls
  `stopPropagation()`: nothing after it runs (in either phase). Any other truthy value just logs

Return the log.

**Example:** root `app` (`click: "log"`) → `list` (`clickCapture: "log"`) → `item` (`click: "log"`), target `item`,
type `"click"` → `["list:capture", "item:bubble", "app:bubble"]`
""",
    starter="function dispatchEvent(tree, targetId, type) {\n  const log = [];\n  // 1. find the path  2. capture  3. bubble\n  return log;\n}\n",
    solution=r'''function dispatchEvent(tree, targetId, type) {
  const path = [];
  const find = (node) => {
    path.push(node);
    if (node.id === targetId) return true;
    for (const child of node.children || []) if (find(child)) return true;
    path.pop();
    return false;
  };
  if (!find(tree)) return [];
  const log = [];
  const call = (node, name, phase) => {
    const handler = (node.on || {})[name];
    if (!handler) return false;
    log.push(node.id + ":" + phase);
    return handler === "stop";
  };
  for (const node of path) if (call(node, type + "Capture", "capture")) return log;
  for (let i = path.length - 1; i >= 0; i--) if (call(path[i], type, "bubble")) return log;
  return log;
}
''',
    tests=[
        [{"id": "app", "on": {"click": "log"}, "children": [{"id": "list", "on": {"clickCapture": "log"}, "children": [{"id": "item", "on": {"click": "log"}}]}]}, "item", "click"],
        [{"id": "app", "on": {"click": "log"}}, "app", "click"],
        [{"id": "app", "on": {"click": "log"}}, "missing", "click"],
        [{"id": "app", "on": {"click": "log", "clickCapture": "log"}, "children": [{"id": "btn", "on": {"click": "log", "clickCapture": "log"}}]}, "btn", "click"],
        [{"id": "app", "on": {"click": "log"}, "children": [{"id": "modal", "on": {"click": "stop"}, "children": [{"id": "ok", "on": {"click": "log"}}]}]}, "ok", "click"],
        [{"id": "app", "on": {"clickCapture": "stop", "click": "log"}, "children": [{"id": "btn", "on": {"click": "log"}}]}, "btn", "click"],
        [{"id": "app", "on": {"keydown": "log"}, "children": [{"id": "btn", "on": {"click": "log"}}]}, "btn", "click"],
        [{"id": "app", "on": {"click": "log"}, "children": [{"id": "a", "on": {"click": "log"}}, {"id": "b", "on": {"click": "log"}, "children": [{"id": "c"}]}]}, "c", "click"],
        [{"id": "r", "children": [{"id": "x", "children": [{"id": "y", "children": [{"id": "z"}]}]}]}, "z", "click"],
        [{"id": "r", "on": {"click": "log", "clickCapture": "log"}, "children": [
            {"id": "m", "on": {"clickCapture": "log", "click": "log"}, "children": [{"id": "t", "on": {"clickCapture": "stop", "click": "log"}}]}]}, "t", "click"],
        [{"id": "r", "on": {"focus": "log", "focusCapture": "log", "click": "log"}, "children": [{"id": "i", "on": {"focus": "stop"}}]}, "i", "focus"],
        [{"id": "r", "on": {"click": "log"}, "children": [{"id": "a", "on": {"click": "log"}, "children": [{"id": "deep", "on": {"click": "log"}}]},
                                                          {"id": "b", "on": {"click": "log"}}]}, "a", "click"],
    ],
    wrong_solutions=[
        r'''function dispatchEvent(tree, targetId, type) {
  const path = [];
  const find = (n) => { path.push(n); if (n.id === targetId) return true; for (const c of n.children || []) if (find(c)) return true; path.pop(); return false; };
  if (!find(tree)) return [];
  const log = [];
  for (const n of path) { const h = (n.on || {})[type + "Capture"]; if (h) log.push(n.id + ":capture"); }
  for (const n of path) { const h = (n.on || {})[type]; if (h) { log.push(n.id + ":bubble"); if (h === "stop") break; } }
  return log;
}
''',
        r'''function dispatchEvent(tree, targetId, type) {
  const log = [];
  const visit = (n) => {
    if ((n.on || {})[type]) log.push(n.id + ":bubble");
    (n.children || []).forEach(visit);
  };
  visit(tree);
  return log;
}
''',
    ],
    guide=G(
        prereqs="DOM event propagation; lesson *Lists, keys and events*.",
        intuition="Propagation is two walks over one list: the ancestors of the target, root first for capture and reversed for bubble.",
        hints=["A depth-first search that pushes on the way down and pops on failure leaves exactly the ancestor path in the array.",
               "Write one helper that looks up a handler, logs, and reports whether propagation should stop.",
               "Stopping in the capture phase must skip the entire bubble phase."],
        brute_force="Visit every node that has a handler. Siblings and descendants of the target must never fire.",
        approach="**Dry run** (example): path `[app, list, item]`. Capture: `app` none, `list` logs, `item` none. Bubble: `item` logs, "
                 "`list` none, `app` logs.",
        complexity="O(n) to find the target, O(depth) to dispatch.",
        pitfalls="Bubbling in root-to-target order; ignoring `stop` during capture; firing handlers of a different event type.",
        follow_up="Since React 17 the single native listener sits on the root container, not on `document`, so several React roots can coexist.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="react-context-lookup", title="Context: find the nearest provider", difficulty="Easy", pattern="Context",
    kind="js", entry="resolveContext",
    description=r"""
`useContext(SomeContext)` returns the value of the **closest provider above** the calling component, or the
context's default when there is none.

`resolveContext(tree, targetId, name, fallback)`:

- a node is `{ id, provides: { contextName: value }, children: [...] }` (`provides` and `children` optional)
- a node's `provides` applies to its **descendants only**, not to itself (a component that renders a provider does
  not read that provider's value)
- return `{ found: true, value }` for the node with id `targetId`: the value from the nearest ancestor that
  provides `name`, else `fallback`
- a provider may provide `null`; that still counts as provided
- unknown `targetId` → `{ found: false, value: null }`

**Example:** `app` provides `theme: "light"`; its child `sidebar` provides `theme: "dark"`; `sidebar`'s child `button`
→ `"dark"`; `app`'s other child `main` → `"light"`; `sidebar` itself → `"light"`; `app` itself → the fallback.
""",
    starter="function resolveContext(tree, targetId, name, fallback) {\n  // carry the current value down the tree\n}\n",
    solution=r'''function resolveContext(tree, targetId, name, fallback) {
  const visit = (node, inherited) => {
    if (node.id === targetId) return { found: true, value: inherited };
    const provides = node.provides || {};
    const forChildren = Object.prototype.hasOwnProperty.call(provides, name) ? provides[name] : inherited;
    for (const child of node.children || []) {
      const result = visit(child, forChildren);
      if (result) return result;
    }
    return null;
  };
  return visit(tree, fallback) || { found: false, value: null };
}
''',
    tests=[
        [{"id": "app", "provides": {"theme": "light"}, "children": [{"id": "sidebar", "provides": {"theme": "dark"}, "children": [{"id": "button"}]}, {"id": "main"}]}, "button", "theme", "system"],
        [{"id": "app", "provides": {"theme": "light"}, "children": [{"id": "sidebar", "provides": {"theme": "dark"}, "children": [{"id": "button"}]}, {"id": "main"}]}, "main", "theme", "system"],
        [{"id": "app", "provides": {"theme": "light"}, "children": [{"id": "sidebar", "provides": {"theme": "dark"}, "children": [{"id": "button"}]}, {"id": "main"}]}, "sidebar", "theme", "system"],
        [{"id": "app", "provides": {"theme": "light"}, "children": [{"id": "sidebar", "provides": {"theme": "dark"}, "children": [{"id": "button"}]}, {"id": "main"}]}, "app", "theme", "system"],
        [{"id": "app", "provides": {"theme": "light"}, "children": [{"id": "main"}]}, "main", "locale", "en"],
        [{"id": "app", "children": [{"id": "main"}]}, "ghost", "theme", "system"],
        [{"id": "app", "provides": {"user": {"name": "Ann"}}, "children": [{"id": "a", "provides": {"user": None}, "children": [{"id": "b"}]}]}, "b", "user", "guest"],
        [{"id": "app", "provides": {"user": {"name": "Ann"}, "theme": "dark"}, "children": [{"id": "a", "provides": {"theme": "light"}, "children": [{"id": "b"}]}]}, "b", "user", "guest"],
        [{"id": "only"}, "only", "theme", None],
        [{"id": "r", "provides": {"n": 1}, "children": [{"id": "x", "provides": {"n": 2}, "children": [{"id": "y", "provides": {"n": 3}, "children": [{"id": "z", "provides": {"n": 4}}]}]}]}, "z", "n", 0],
        [{"id": "r", "provides": {"n": 1}, "children": [{"id": "left", "provides": {"n": 2}, "children": [{"id": "l1"}]}, {"id": "right", "children": [{"id": "r1"}]}]}, "r1", "n", 0],
        [{"id": "r", "provides": {"flag": False}, "children": [{"id": "c"}]}, "c", "flag", True],
    ],
    wrong_solutions=[
        r'''function resolveContext(tree, targetId, name, fallback) {
  const visit = (node, inherited) => {
    const provides = node.provides || {};
    const here = name in provides ? provides[name] : inherited;
    if (node.id === targetId) return { found: true, value: here };
    for (const c of node.children || []) { const r = visit(c, here); if (r) return r; }
    return null;
  };
  return visit(tree, fallback) || { found: false, value: null };
}
''',
        r'''function resolveContext(tree, targetId, name, fallback) {
  const visit = (node, inherited) => {
    if (node.id === targetId) return { found: true, value: inherited };
    const v = (node.provides || {})[name] || inherited;
    for (const c of node.children || []) { const r = visit(c, v); if (r) return r; }
    return null;
  };
  return visit(tree, fallback) || { found: false, value: null };
}
''',
    ],
    guide=G(
        prereqs="Tree traversal; lesson *Context and global state*.",
        intuition="Pass the 'current value' down as a parameter while you walk the tree. Each provider swaps the value for its "
                  "subtree only; siblings never see it.",
        hints=["Give the recursive function a second parameter: the value inherited from above.",
               "Check for the target *before* applying the node's own `provides`.",
               "Use `hasOwnProperty` (or `in`), not truthiness, so `null` and `false` values count."],
        brute_force="Find the path to the target first, then scan the path backwards for a provider. Equally correct, two passes.",
        approach="**Dry run** target `button`: visit `app` with `system`; not the target; children inherit `light`. Visit `sidebar` "
                 "with `light`; children inherit `dark`. Visit `button` with `dark` → found.",
        complexity="O(n) time, O(depth) stack.",
        pitfalls="Using `||` drops falsy provided values; applying a node's provider to itself.",
        follow_up="When a provider's value changes, every consumer below it re-renders, which is why big frequently-changing objects make poor context values.",
    ),
),
]
