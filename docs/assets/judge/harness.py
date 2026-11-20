"""Judge harness shared by the in-browser runner (Pyodide) and the local build.

A problem spec (dict) looks like:
  kind:        "function" | "class"
  entry:       function / method name, or class name for kind="class"
  arg_types:   optional list, per argument: "list_node" | "tree" | None
  return_type: optional "list_node" | "tree" | None
  compare:     "exact" | "unordered" | "unordered_nested" | "float" | "set_of_sets"
  tolerance:   float tolerance for "float" (default 1e-6)
  inplace_arg: optional int; if set, result = that argument after the call
  checker:     optional python source defining check(args, got, expected) -> bool
"""
import copy
import io
import json
import math
import sys
import time
import traceback
from typing import *  # noqa: F401,F403  (lets user code use List, Optional, ...)
import collections  # noqa: F401
import heapq  # noqa: F401
import bisect  # noqa: F401
import itertools  # noqa: F401
import functools  # noqa: F401


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

    def __repr__(self):
        return f"ListNode({from_list_node(self)})"


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

    def __repr__(self):
        return f"TreeNode({from_tree(self)})"


class Node:
    """Generic node used by graph-clone style problems: Node(val, neighbors)."""

    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []


def to_list_node(arr):
    dummy = ListNode()
    cur = dummy
    for v in arr or []:
        cur.next = ListNode(v)
        cur = cur.next
    return dummy.next


def from_list_node(node, limit=100000):
    out = []
    while node is not None and len(out) < limit:
        out.append(node.val)
        node = node.next
    return out


def to_tree(arr):
    if not arr or arr[0] is None:
        return None
    it = iter(arr)
    root = TreeNode(next(it))
    q = collections.deque([root])
    while q:
        node = q.popleft()
        try:
            lv = next(it)
        except StopIteration:
            break
        if lv is not None:
            node.left = TreeNode(lv)
            q.append(node.left)
        try:
            rv = next(it)
        except StopIteration:
            break
        if rv is not None:
            node.right = TreeNode(rv)
            q.append(node.right)
    return root


def from_tree(root):
    if root is None:
        return []
    out, q = [], collections.deque([root])
    while q:
        n = q.popleft()
        if n is None:
            out.append(None)
            continue
        out.append(n.val)
        q.append(n.left)
        q.append(n.right)
    while out and out[-1] is None:
        out.pop()
    return out


def to_graph(adj):
    """adjacency list (1-indexed, LeetCode 133 style) -> Node"""
    if not adj:
        return None
    nodes = [Node(i + 1) for i in range(len(adj))]
    for i, nbrs in enumerate(adj):
        nodes[i].neighbors = [nodes[j - 1] for j in nbrs]
    return nodes[0]


def from_graph(node):
    if node is None:
        return []
    seen, order, q = {node.val: node}, [], collections.deque([node])
    while q:
        n = q.popleft()
        for nb in n.neighbors:
            if nb.val not in seen:
                seen[nb.val] = nb
                q.append(nb)
    out = []
    for v in sorted(seen):
        out.append([nb.val for nb in seen[v].neighbors])
    return out


CONVERT_IN = {"list_node": to_list_node, "tree": to_tree, "graph": to_graph}
CONVERT_OUT = {"list_node": from_list_node, "tree": from_tree, "graph": from_graph}


def normalize(x):
    """Turn results into JSON-friendly plain python values."""
    if hasattr(x, "tolist"):  # numpy arrays / scalars
        try:
            return normalize(x.tolist())
        except Exception:
            pass
    if isinstance(x, ListNode):
        return from_list_node(x)
    if isinstance(x, TreeNode):
        return from_tree(x)
    if isinstance(x, (list, tuple)):
        return [normalize(v) for v in x]
    if isinstance(x, (set, frozenset)):
        try:
            return sorted(normalize(v) for v in x)
        except TypeError:
            return [normalize(v) for v in x]
    if isinstance(x, dict):
        return {str(k): normalize(v) for k, v in x.items()}
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return str(x)
    return x


def _sort_key(v):
    return json.dumps(v, sort_keys=True)


def _float_eq(a, b, tol):
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=tol, abs_tol=tol)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_float_eq(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_float_eq(a[k], b[k], tol) for k in a)
    return a == b


def compare(spec, args, got, expected):
    if spec.get("checker"):
        ns = {}
        exec(spec["checker"], ns)
        return bool(ns["check"](copy.deepcopy(args), got, expected))
    mode = spec.get("compare", "exact")
    tol = spec.get("tolerance", 1e-6)
    if mode == "float":
        return _float_eq(got, expected, tol)
    if mode == "unordered":
        if not isinstance(got, list) or not isinstance(expected, list):
            return got == expected
        return sorted(got, key=_sort_key) == sorted(expected, key=_sort_key)
    if mode in ("unordered_nested", "set_of_sets"):
        if not isinstance(got, list) or not isinstance(expected, list):
            return got == expected

        def canon(lst):
            inner = [sorted(x, key=_sort_key) if isinstance(x, list) else x for x in lst]
            return sorted(inner, key=_sort_key)

        return canon(got) == canon(expected)
    return got == expected


def _get_callable(ns, spec):
    entry = spec["entry"]
    if "Solution" in ns and isinstance(ns["Solution"], type):
        sol = ns["Solution"]()
        if hasattr(sol, entry):
            return getattr(sol, entry)
    if entry in ns and callable(ns[entry]):
        return ns[entry]
    raise NameError(
        f"Could not find '{entry}'. Define it as a method of class Solution or as a top-level function."
    )


def _base_namespace():
    ns = {"__name__": "__solution__"}
    exec(
        "from typing import *\nimport collections, heapq, bisect, itertools, functools, math, re, string\n"
        "from collections import *\nfrom heapq import *\nfrom functools import lru_cache, cache, reduce\n",
        ns,
    )
    ns.update(ListNode=ListNode, TreeNode=TreeNode, Node=Node)
    return ns


def _run_function(fn, spec, args):
    arg_types = spec.get("arg_types") or []
    call_args = copy.deepcopy(args)
    conv = []
    for i, a in enumerate(call_args):
        t = arg_types[i] if i < len(arg_types) else None
        conv.append(CONVERT_IN[t](a) if t in CONVERT_IN else a)
    res = fn(*conv)
    if spec.get("inplace_arg") is not None:
        res = conv[spec["inplace_arg"]]
    rt = spec.get("return_type")
    if rt in CONVERT_OUT and not isinstance(res, list):
        res = CONVERT_OUT[rt](res)
    return normalize(res)


def _run_class(ns, spec, test_args):
    ops, op_args = test_args
    cls = ns.get(spec["entry"])
    if cls is None:
        raise NameError(f"Could not find class '{spec['entry']}'.")
    out, obj = [], None
    for op, a in zip(ops, op_args):
        a = copy.deepcopy(a)
        if op == spec["entry"]:
            obj = cls(*a)
            out.append(None)
        else:
            out.append(normalize(getattr(obj, op)(*a)))
    return out


def execute(code, spec, args):
    """Run user code on one test. Returns (got, stdout, error, ms)."""
    ns = _base_namespace()
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    t0 = time.perf_counter()
    try:
        exec(compile(code, "solution.py", "exec"), ns)
        if spec.get("kind") == "class":
            got = _run_class(ns, spec, args)
        else:
            got = _run_function(_get_callable(ns, spec), spec, args)
        err = None
    except BaseException:  # noqa: BLE001 - report everything to the learner
        got = None
        tb = traceback.format_exc()
        # trim harness frames
        lines = tb.splitlines()
        keep = [l for l in lines if "harness.py" not in l]
        err = "\n".join(keep[-12:])
    finally:
        sys.stdout = old
    ms = (time.perf_counter() - t0) * 1000
    return got, buf.getvalue()[-4000:], err, ms


def run_tests(code, spec, tests, on_result=None):
    """tests: list of {"args": [...], "expected": ...}. Returns summary dict."""
    results = []
    for i, t in enumerate(tests):
        got, out, err, ms = execute(code, spec, t["args"])
        ok = err is None and compare(spec, t["args"], got, t.get("expected"))
        r = {"i": i, "ok": ok, "got": got, "stdout": out, "error": err, "ms": round(ms, 2)}
        results.append(r)
        if on_result:
            on_result(json.dumps(r, default=str))
        if err and "SyntaxError" in err:
            break
    passed = sum(r["ok"] for r in results)
    return {"passed": passed, "total": len(tests), "results": results}


def run_tests_json(code, spec_json, tests_json, on_result=None):
    return json.dumps(
        run_tests(code, json.loads(spec_json), json.loads(tests_json), on_result), default=str
    )


def _patch_asyncio_for_browser():
    """Pyodide's event loop cannot block, so asyncio.run() fails there.
    Replace it with a small blocking loop (timers and tasks only, no sockets)."""
    import asyncio
    from asyncio import events

    class _SyncLoop(asyncio.BaseEventLoop):
        def __init__(self):
            super().__init__()
            self._selector = self

        def select(self, timeout=None):
            if timeout and timeout > 0:
                time.sleep(timeout)
            return []

        def _process_events(self, event_list):
            pass

        def _write_to_self(self):
            pass

    def run(main, *, debug=None, loop_factory=None):
        outer = events._get_running_loop()
        events._set_running_loop(None)
        loop = _SyncLoop()
        try:
            return loop.run_until_complete(main)
        finally:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            finally:
                loop.close()
                events._set_running_loop(outer)

    asyncio.run = run


if sys.platform == "emscripten":
    _patch_asyncio_for_browser()
