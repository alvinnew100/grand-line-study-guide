_SCHEMA = {
    "type": "object",
    "required": ["city", "days"],
    "additionalProperties": False,
    "properties": {
        "city": {"type": "string", "minLength": 1, "maxLength": 20},
        "days": {"type": "integer", "minimum": 1, "maximum": 14},
        "units": {"type": "string", "enum": ["metric", "imperial"]},
        "alerts": {"type": "boolean"},
        "coords": {"type": "array", "items": {"type": "number"}},
        "contact": {"type": "object", "required": ["email"],
                    "properties": {"email": {"type": "string"}, "age": {"type": "integer", "minimum": 0}}},
        "note": {"type": "null"},
    },
}


def _m(role, tokens, content="x", **extra):
    return dict(role=role, tokens=tokens, content=content, **extra)


_CONV = [_m("system", 50, "sys"), _m("user", 20, "u1"), _m("assistant", 30, "a1"), _m("user", 10, "u2"),
         _m("assistant", 40, "a2"), _m("user", 15, "u3")]

_AGENT = [_m("system", 100, "sys"), _m("user", 20, "goal"), _m("assistant", 10, "call read"),
          _m("tool", 4000, "file A"), _m("assistant", 10, "call tests"), _m("tool", 2000, "log"),
          _m("assistant", 30, "found bug"), _m("assistant", 10, "call read"), _m("tool", 4100, "file A v2"),
          _m("assistant", 10, "call tests"), _m("tool", 600, "ok")]


def _ev_text(i, *parts):
    out = [{"type": "content_block_start", "index": i, "content_block": {"type": "text", "text": ""}}]
    out += [{"type": "content_block_delta", "index": i, "delta": {"type": "text_delta", "text": p}} for p in parts]
    return out + [{"type": "content_block_stop", "index": i}]


def _ev_tool(i, id_, name, *parts, stop=True):
    out = [{"type": "content_block_start", "index": i,
            "content_block": {"type": "tool_use", "id": id_, "name": name, "input": {}}}]
    out += [{"type": "content_block_delta", "index": i, "delta": {"type": "input_json_delta", "partial_json": p}}
            for p in parts]
    return out + ([{"type": "content_block_stop", "index": i}] if stop else [])


_START = [{"type": "message_start", "message": {"id": "msg_1", "role": "assistant", "usage": {"input_tokens": 25, "output_tokens": 1}}}]


def _end(reason, out_tokens):
    return [{"type": "message_delta", "delta": {"stop_reason": reason}, "usage": {"output_tokens": out_tokens}},
            {"type": "message_stop"}]


_DISPATCH_STARTER = r'''# The server's tools. Keep these definitions; implement handle() below.
TOOLS = {
    "add": {
        "description": "Add two integers.",
        "inputSchema": {"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                        "required": ["a", "b"]},
    },
    "divide": {
        "description": "Divide a by b.",
        "inputSchema": {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
                        "required": ["a", "b"]},
    },
    "echo": {
        "description": "Return the text unchanged.",
        "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    },
}
HANDLERS = {
    "add": lambda a, b: a + b,
    "divide": lambda a, b: a / b,
    "echo": lambda text: text,
}
'''

PROBLEMS = [
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-tool-call-parser",
    title="Parse Tool Calls from Model Output",
    difficulty="Medium",
    pattern="Agents",
    entry="parse_tool_calls",
    description=r"""
Open-weight models emit tool calls as text. Write the parser an inference server would use for the
Hermes/Qwen format, where each call is a JSON object wrapped in `<tool_call>` ... `</tool_call>`.

Return a dict with three keys:

- `"content"`: the text with every complete `<tool_call>...</tool_call>` block removed, then stripped
  of leading/trailing whitespace;
- `"tool_calls"`: a list of `{"name": str, "arguments": dict}` for each **valid** block, in order;
- `"errors"`: the number of **invalid** blocks.

A block is valid if its body (after stripping whitespace) parses as a JSON **object** with a string
`"name"` and, if present, an `"arguments"` value that is an object. A missing `"arguments"` defaults to
`{}`. Anything else (broken JSON, a JSON array, missing or non-string name, non-object arguments) is
invalid. Extra keys are ignored.

Blocks are matched non-greedily and may span lines. An opening `<tool_call>` with no closing tag is not
a block: leave it in the content.

**Example**

```text
Let me check.
<tool_call>
{"name": "get_weather", "arguments": {"city": "Oslo"}}
</tool_call>
```

returns `{"content": "Let me check.", "tool_calls": [{"name": "get_weather", "arguments": {"city": "Oslo"}}], "errors": 0}`.
""",
    starter=r'''import json
import re

def parse_tool_calls(text):
    pass
''',
    solution=r'''import json
import re

_BLOCK = re.compile(r"<tool_call>(.*?)</tool_call>", re.S)

def parse_tool_calls(text):
    calls, errors = [], 0
    for body in _BLOCK.findall(text):
        try:
            obj = json.loads(body.strip())
        except json.JSONDecodeError:
            errors += 1
            continue
        if not isinstance(obj, dict) or not isinstance(obj.get("name"), str):
            errors += 1
            continue
        args = obj.get("arguments", {})
        if not isinstance(args, dict):
            errors += 1
            continue
        calls.append({"name": obj["name"], "arguments": args})
    return {"content": _BLOCK.sub("", text).strip(), "tool_calls": calls, "errors": errors}
''',
    tests=[
        ['Let me check.\n<tool_call>\n{"name": "get_weather", "arguments": {"city": "Oslo"}}\n</tool_call>'],
        ['<tool_call>{"name": "a", "arguments": {"x": 1}}</tool_call>\n<tool_call>{"name": "b", "arguments": {}}</tool_call>'],
        ["Just a normal answer with no tools."],
        [""],
        ['<tool_call>{"name": "get_weather", "arguments": {"city": "Bergen"}</tool_call>'],
        ['Before <tool_call>{"name": "ping"}</tool_call> after'],
        ['<tool_call>["not", "an", "object"]</tool_call>'],
        ['<tool_call>{"arguments": {"x": 1}}</tool_call><tool_call>{"name": 5, "arguments": {}}</tool_call>'],
        ['<tool_call>{"name": "f", "arguments": "city=Oslo"}</tool_call>'],
        ['I will call <tool_call>{"name": "search", "arguments": {"q": "a </b> c"}}</tool_call> now.\n\n<tool_call>\n  {"name": "open", "arguments": {"id": 3}, "extra": true}\n</tool_call>\n'],
        ['Thinking... <tool_call>{"name": "unfinished", "arguments": {'],
        ['<tool_call>{"name": "nested", "arguments": {"filters": {"tags": ["a", "b"], "range": {"lo": 1, "hi": 2}}}}</tool_call>'],
        ['<tool_call></tool_call>ok<tool_call>   </tool_call>'],
        ['A<tool_call>{"name": "x", "arguments": {}}</tool_call>B<tool_call>oops</tool_call>C'],
    ],
    examples=2,
    wrong_solutions=[
        # crashes / no error handling: treats malformed blocks as fatal
        r'''import json, re
def parse_tool_calls(text):
    calls = []
    for body in re.findall(r"<tool_call>(.*?)</tool_call>", text, re.S):
        obj = json.loads(body)
        calls.append({"name": obj["name"], "arguments": obj.get("arguments", {})})
    return {"content": re.sub(r"<tool_call>.*?</tool_call>", "", text, flags=re.S).strip(), "tool_calls": calls, "errors": 0}
''',
        # greedy regex merges several blocks into one
        r'''import json, re
def parse_tool_calls(text):
    calls, errors = [], 0
    for body in re.findall(r"<tool_call>(.*)</tool_call>", text, re.S):
        try:
            obj = json.loads(body.strip())
            if not isinstance(obj, dict) or not isinstance(obj.get("name"), str) or not isinstance(obj.get("arguments", {}), dict):
                raise ValueError
            calls.append({"name": obj["name"], "arguments": obj.get("arguments", {})})
        except ValueError:
            errors += 1
    return {"content": re.sub(r"<tool_call>.*</tool_call>", "", text, flags=re.S).strip(), "tool_calls": calls, "errors": errors}
''',
        # accepts anything that parses as JSON, without validating shape
        r'''import json, re
def parse_tool_calls(text):
    calls, errors = [], 0
    for body in re.findall(r"<tool_call>(.*?)</tool_call>", text, re.S):
        try:
            obj = json.loads(body.strip())
            calls.append({"name": obj.get("name"), "arguments": obj.get("arguments", {})})
        except Exception:
            errors += 1
    return {"content": re.sub(r"<tool_call>.*?</tool_call>", "", text, flags=re.S).strip(), "tool_calls": calls, "errors": errors}
''',
        # does not span newlines
        r'''import json, re
def parse_tool_calls(text):
    calls, errors = [], 0
    for body in re.findall(r"<tool_call>(.*?)</tool_call>", text):
        try:
            obj = json.loads(body.strip())
            if not isinstance(obj, dict) or not isinstance(obj.get("name"), str) or not isinstance(obj.get("arguments", {}), dict):
                raise ValueError
            calls.append({"name": obj["name"], "arguments": obj.get("arguments", {})})
        except ValueError:
            errors += 1
    return {"content": re.sub(r"<tool_call>.*?</tool_call>", "", text).strip(), "tool_calls": calls, "errors": errors}
''',
    ],
    guide=dict(
        prereqs="Lesson *Function calling: schemas, the tool loop and parsing*; `re` with the DOTALL flag; `json.loads`.",
        intuition="The model's output is untrusted text. Find the tagged blocks, try to parse each one, and keep careful count of what was valid and what was not, because a malformed call should be reported back to the model rather than silently dropped or allowed to crash the server.",
        hints=[
            "`re.findall(r'<tool_call>(.*?)</tool_call>', text, re.S)`: non-greedy and DOTALL.",
            "Wrap `json.loads` in `try/except json.JSONDecodeError`, then check `isinstance(obj, dict)`, the name's type and the arguments' type.",
            "Build the content with `re.sub` using the same pattern, then `.strip()`.",
        ],
        brute_force="Scan with `str.find` for each opening and closing tag in a loop. Equivalent to the regex and also $O(n)$; the regex is simply shorter.",
        approach="1. Compile one pattern for blocks.\n2. For each body: parse, validate shape, append or count an error.\n3. Remove all blocks from the text and strip.\n\n**Dry run** (test 5): the body lacks a closing brace, `json.loads` raises, so `errors = 1`, `tool_calls = []`, and the content is empty because the block itself is still removed.",
        complexity="$O(n)$ in the length of the text.",
        pitfalls="- A greedy `.*` swallows everything between the first opening and the last closing tag.\n- Forgetting `re.S`: real model output puts the JSON on its own lines.\n- Letting one malformed block raise and lose the valid calls.\n- Accepting JSON arrays or string arguments as calls.\n- Parsing with `eval` (never).",
        follow_up="Support Llama 3.1's bare-JSON format and Mistral's `[TOOL_CALLS]`; attach generated call ids; stream-parse partial output token by token.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-json-schema-validate",
    title="JSON-Schema-Lite Validator for Tool Arguments",
    difficulty="Medium",
    pattern="Agents",
    entry="validate",
    description=r"""
Before executing a tool call you must validate the model-supplied arguments. Implement a validator for a
useful subset of JSON Schema that returns **all** errors as a **sorted** list of strings (empty list =
valid).

`validate(value, schema, path="$")` checks, in this order:

1. **`type`** (if present): `object` (dict), `array` (list), `string`, `integer`, `number`
   (int or float), `boolean`, `null` (None). In JSON Schema a boolean is **not** an integer or number.
   On mismatch add `"{path}: expected {type}"` and stop checking this value.
2. **`enum`**: if the value is not in the list add `"{path}: not in enum"`.
3. Numbers: `minimum` gives `"{path}: below minimum"`, `maximum` gives `"{path}: above maximum"`.
4. Strings: `minLength` gives `"{path}: too short"`, `maxLength` gives `"{path}: too long"`.
5. Objects: every key in `required` that is absent adds `"{path}.{key}: missing"`; every present key
   that has a schema in `properties` is validated recursively with path `"{path}.{key}"`; if
   `additionalProperties` is `false`, every key not in `properties` adds `"{path}.{key}: unexpected"`.
6. Arrays: if `items` is present, each element is validated with path `"{path}[{i}]"`.

Rules 3-6 apply only when the value has the matching Python type (so they work even if `type` is
omitted). Return `sorted(errors)`.

**Example**

`schema = {"type": "object", "required": ["city", "days"], "properties": {"city": {"type": "string"},
"days": {"type": "integer", "minimum": 1}}}`

`validate({"days": 0}, schema)` returns `["$.city: missing", "$.days: below minimum"]`.
""",
    starter=r'''def validate(value, schema, path="$"):
    pass
''',
    solution=r'''def validate(value, schema, path="$"):
    return sorted(_check(value, schema, path))

def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)

def _check(value, schema, path):
    errs = []
    t = schema.get("type")
    if t is not None:
        ok = {
            "object": isinstance(value, dict),
            "array": isinstance(value, list),
            "string": isinstance(value, str),
            "integer": isinstance(value, int) and not isinstance(value, bool),
            "number": _is_num(value),
            "boolean": isinstance(value, bool),
            "null": value is None,
        }.get(t, True)
        if not ok:
            return [f"{path}: expected {t}"]
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: not in enum")
    if _is_num(value):
        if "minimum" in schema and value < schema["minimum"]:
            errs.append(f"{path}: below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            errs.append(f"{path}: above maximum")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errs.append(f"{path}: too short")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errs.append(f"{path}: too long")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errs.append(f"{path}.{key}: missing")
        for key, v in value.items():
            if key in props:
                errs.extend(_check(v, props[key], f"{path}.{key}"))
            elif schema.get("additionalProperties") is False:
                errs.append(f"{path}.{key}: unexpected")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            errs.extend(_check(item, schema["items"], f"{path}[{i}]"))
    return errs
''',
    tests=[
        [{"days": 0}, {"type": "object", "required": ["city", "days"],
                       "properties": {"city": {"type": "string"}, "days": {"type": "integer", "minimum": 1}}}],
        [{"city": "Oslo", "days": 3}, _SCHEMA],
        [{"city": "Oslo", "days": 30, "units": "kelvin", "debug": True}, _SCHEMA],
        [{"days": "3"}, _SCHEMA],
        ["not an object", _SCHEMA],
        [{"city": "", "days": True}, _SCHEMA],
        [{"city": "Oslo", "days": 2, "coords": [59.9, "10.7", 3, False]}, _SCHEMA],
        [{"city": "Oslo", "days": 2, "contact": {"age": -1}}, _SCHEMA],
        [{"city": "Oslo", "days": 2, "contact": {"email": "a@b.c", "age": 30, "nick": "al"}, "note": None, "alerts": False}, _SCHEMA],
        [{"city": "A very long city name indeed", "days": 2.0, "alerts": 1, "note": 0}, _SCHEMA],
        [[1, 2, "x"], {"type": "array", "items": {"type": "integer", "maximum": 1}}],
        [5, {"enum": [1, 2, 3]}],
        [{"a": {"b": {"c": [{"d": 1}, {"d": "x"}, {}]}}},
         {"type": "object", "properties": {"a": {"type": "object", "properties": {"b": {"type": "object", "properties": {
             "c": {"type": "array", "items": {"type": "object", "required": ["d"], "properties": {"d": {"type": "integer"}}}}}}}}}}],
        [3.5, {"type": "number", "minimum": 4, "maximum": 3}],
        [{}, {}],
    ],
    examples=2,
    wrong_solutions=[
        # treats booleans as integers/numbers
        r'''def validate(value, schema, path="$"):
    return sorted(_check(value, schema, path))
def _check(value, schema, path):
    errs = []; t = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "boolean": bool, "null": type(None)}
    if t in types and not isinstance(value, types[t]):
        return [f"{path}: expected {t}"]
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: not in enum")
    if isinstance(value, (int, float)):
        if "minimum" in schema and value < schema["minimum"]: errs.append(f"{path}: below minimum")
        if "maximum" in schema and value > schema["maximum"]: errs.append(f"{path}: above maximum")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]: errs.append(f"{path}: too short")
        if "maxLength" in schema and len(value) > schema["maxLength"]: errs.append(f"{path}: too long")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value: errs.append(f"{path}.{key}: missing")
        for key, v in value.items():
            if key in props: errs.extend(_check(v, props[key], f"{path}.{key}"))
            elif schema.get("additionalProperties") is False: errs.append(f"{path}.{key}: unexpected")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value): errs.extend(_check(item, schema["items"], f"{path}[{i}]"))
    return errs
''',
        # stops at the first error
        r'''def validate(value, schema, path="$"):
    e = _check(value, schema, path)
    return sorted(e)[:1]
def _is_num(v): return isinstance(v, (int, float)) and not isinstance(v, bool)
def _check(value, schema, path):
    errs = []; t = schema.get("type")
    ok = {"object": isinstance(value, dict), "array": isinstance(value, list), "string": isinstance(value, str),
          "integer": isinstance(value, int) and not isinstance(value, bool), "number": _is_num(value),
          "boolean": isinstance(value, bool), "null": value is None}.get(t, True)
    if not ok: return [f"{path}: expected {t}"]
    if "enum" in schema and value not in schema["enum"]: errs.append(f"{path}: not in enum")
    if _is_num(value):
        if "minimum" in schema and value < schema["minimum"]: errs.append(f"{path}: below minimum")
        if "maximum" in schema and value > schema["maximum"]: errs.append(f"{path}: above maximum")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value: errs.append(f"{path}.{key}: missing")
        for key, v in value.items():
            if key in props: errs.extend(_check(v, props[key], f"{path}.{key}"))
            elif schema.get("additionalProperties") is False: errs.append(f"{path}.{key}: unexpected")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value): errs.extend(_check(item, schema["items"], f"{path}[{i}]"))
    return errs
''',
        # no recursion into nested objects / arrays
        r'''def validate(value, schema, path="$"):
    errs = []; t = schema.get("type")
    def is_num(v): return isinstance(v, (int, float)) and not isinstance(v, bool)
    def type_ok(v, t):
        return {"object": isinstance(v, dict), "array": isinstance(v, list), "string": isinstance(v, str),
                "integer": isinstance(v, int) and not isinstance(v, bool), "number": is_num(v),
                "boolean": isinstance(v, bool), "null": v is None}.get(t, True)
    if not type_ok(value, t): return [f"{path}: expected {t}"]
    if "enum" in schema and value not in schema["enum"]: errs.append(f"{path}: not in enum")
    if is_num(value):
        if "minimum" in schema and value < schema["minimum"]: errs.append(f"{path}: below minimum")
        if "maximum" in schema and value > schema["maximum"]: errs.append(f"{path}: above maximum")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value: errs.append(f"{path}.{key}: missing")
        for key, v in value.items():
            if key in props:
                s = props[key]
                if not type_ok(v, s.get("type")): errs.append(f"{path}.{key}: expected {s.get('type')}")
                elif "enum" in s and v not in s["enum"]: errs.append(f"{path}.{key}: not in enum")
                elif is_num(v) and "minimum" in s and v < s["minimum"]: errs.append(f"{path}.{key}: below minimum")
                elif is_num(v) and "maximum" in s and v > s["maximum"]: errs.append(f"{path}.{key}: above maximum")
                elif isinstance(v, str) and "minLength" in s and len(v) < s["minLength"]: errs.append(f"{path}.{key}: too short")
                elif isinstance(v, str) and "maxLength" in s and len(v) > s["maxLength"]: errs.append(f"{path}.{key}: too long")
            elif schema.get("additionalProperties") is False: errs.append(f"{path}.{key}: unexpected")
    return sorted(errs)
''',
    ],
    guide=dict(
        prereqs="Lesson *Function calling*, section on validating before executing; recursion over nested data.",
        intuition="A schema is a tree that mirrors the shape of the data. Walk both trees together: at each node check the node-level rules, then recurse into children with a longer path. Collect every error so the model can fix them all in one retry.",
        hints=[
            "Write a helper `is_number(v)` that excludes `bool` (in Python `True` is an `int`).",
            "On a type mismatch return immediately with that single error; the other keywords are meaningless for the wrong type.",
            "Recurse with `f'{path}.{key}'` for properties and `f'{path}[{i}]'` for items, and sort only once at the top level.",
        ],
        brute_force="There is no cheaper alternative to visiting each value once; the 'brute force' mistake is to validate only the top level, which misses nested errors.",
        approach="1. Type check (early return on mismatch).\n2. `enum`.\n3. Numeric bounds, string lengths.\n4. Objects: required keys, recurse into known properties, flag unexpected keys when additional properties are disallowed.\n5. Arrays: recurse into items.\n6. Sort.\n\n**Dry run:** `{'days': 0}`: object OK; `city` missing; `days` is an integer below the minimum 1. Sorted: `['$.city: missing', '$.days: below minimum']`.",
        complexity="$O(n)$ in the number of values in the instance (times the size of any `enum` lists).",
        pitfalls="- `isinstance(True, int)` is `True` in Python: booleans must be rejected for `integer` and `number`.\n- `2.0` is a float: it is a valid `number` but, in this simplified validator, not an `integer`.\n- Continuing to check bounds after a type mismatch (comparison errors).\n- Returning at the first error.\n- Treating a missing `additionalProperties` as `false` (the default allows extra keys).",
        follow_up="Add `pattern`, `anyOf`, `$ref` with `$defs` and a depth limit; format the errors as a tool result the model can act on; compare with the `jsonschema` package.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-mcp-jsonrpc",
    title="MCP JSON-RPC: Build Requests, Validate Responses",
    difficulty="Easy",
    pattern="MCP",
    entry="jsonrpc",
    description=r"""
MCP messages are JSON-RPC 2.0. Implement one function with three actions (the second argument is a list
of that action's parameters).

**`jsonrpc("request", [id, method, params])`** builds a request dict
`{"jsonrpc": "2.0", "id": id, "method": method, "params": params}`.

- Omit the `"params"` key entirely when `params` is `None`.
- In MCP the id must be a string or an integer (not `None`, not a boolean, not a float) and the method a
  non-empty string. If either is invalid, return the string `"invalid"`.

**`jsonrpc("notification", [method, params])`** builds the same thing **without** an `id`.

**`jsonrpc("check", [request, response])`** classifies a response to a request and returns

- `"result"` for a valid success response,
- `"error:<code>"` (for example `"error:-32601"`) for a valid error response,
- `"invalid"` otherwise.

A response is valid when it is a dict with `"jsonrpc": "2.0"`, an `id` equal to the request's id **and
of the same type** (`1` does not match `"1"`), and **exactly one** of `result` / `error`. A `result`
must be a dict. An `error` must be a dict whose `code` is an integer (not a boolean) and whose
`message` is a string.

**Example**

`jsonrpc("request", [1, "tools/list", None])` returns `{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}`.

`jsonrpc("check", [{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, {"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "Method not found"}}])`
returns `"error:-32601"`.
""",
    starter=r'''def jsonrpc(action, args):
    pass
''',
    solution=r'''def _valid_id(i):
    return isinstance(i, (str, int)) and not isinstance(i, bool)

def jsonrpc(action, args):
    if action in ("request", "notification"):
        if action == "request":
            id_, method, params = args
            if not _valid_id(id_):
                return "invalid"
        else:
            method, params = args
        if not isinstance(method, str) or not method:
            return "invalid"
        msg = {"jsonrpc": "2.0"}
        if action == "request":
            msg["id"] = id_
        msg["method"] = method
        if params is not None:
            msg["params"] = params
        return msg
    request, resp = args
    if not isinstance(resp, dict) or resp.get("jsonrpc") != "2.0":
        return "invalid"
    rid = request.get("id")
    if "id" not in resp or type(resp["id"]) is not type(rid) or resp["id"] != rid:
        return "invalid"
    has_r, has_e = "result" in resp, "error" in resp
    if has_r == has_e:
        return "invalid"
    if has_r:
        return "result" if isinstance(resp["result"], dict) else "invalid"
    err = resp["error"]
    if (not isinstance(err, dict) or not isinstance(err.get("code"), int) or isinstance(err.get("code"), bool)
            or not isinstance(err.get("message"), str)):
        return "invalid"
    return "error:%d" % err["code"]
''',
    tests=[
        ["request", [1, "tools/list", None]],
        ["check", [{"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                   {"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "Method not found"}}]],
        ["request", ["abc-7", "tools/call", {"name": "add", "arguments": {"a": 1, "b": 2}}]],
        ["notification", ["notifications/initialized", None]],
        ["notification", ["notifications/progress", {"progressToken": "t", "progress": 5}]],
        ["request", [None, "ping", None]],
        ["request", [True, "ping", None]],
        ["request", [2.5, "ping", None]],
        ["request", [3, "", None]],
        ["request", [0, "initialize", {}]],
        ["check", [{"jsonrpc": "2.0", "id": 2, "method": "tools/call"},
                   {"jsonrpc": "2.0", "id": 2, "result": {"content": [{"type": "text", "text": "3"}], "isError": False}}]],
        ["check", [{"jsonrpc": "2.0", "id": 2, "method": "x"}, {"jsonrpc": "2.0", "id": "2", "result": {}}]],
        ["check", [{"jsonrpc": "2.0", "id": 2, "method": "x"}, {"jsonrpc": "2.0", "id": 3, "result": {}}]],
        ["check", [{"jsonrpc": "2.0", "id": 2, "method": "x"}, {"id": 2, "result": {}}]],
        ["check", [{"jsonrpc": "2.0", "id": 2, "method": "x"},
                   {"jsonrpc": "2.0", "id": 2, "result": {}, "error": {"code": 1, "message": "both"}}]],
        ["check", [{"jsonrpc": "2.0", "id": 2, "method": "x"}, {"jsonrpc": "2.0", "id": 2}]],
        ["check", [{"jsonrpc": "2.0", "id": 2, "method": "x"}, {"jsonrpc": "2.0", "id": 2, "result": "ok"}]],
        ["check", [{"jsonrpc": "2.0", "id": 2, "method": "x"},
                   {"jsonrpc": "2.0", "id": 2, "error": {"code": "-32602", "message": "bad"}}]],
        ["check", [{"jsonrpc": "2.0", "id": 2, "method": "x"}, {"jsonrpc": "2.0", "id": 2, "error": {"code": -32602}}]],
        ["check", [{"jsonrpc": "2.0", "id": "q", "method": "x"},
                   {"jsonrpc": "2.0", "id": "q", "error": {"code": -32022, "message": "Unsupported protocol version",
                                                             "data": {"supported": ["2026-07-28"]}}}]],
        ["check", [{"jsonrpc": "2.0", "id": 2, "method": "x"}, [1, 2, 3]]],
        ["check", [{"jsonrpc": "2.0", "id": 1, "method": "x"},
                   {"jsonrpc": "2.0", "id": 1, "error": {"code": True, "message": "bool code"}}]],
    ],
    examples=2,
    wrong_solutions=[
        # always includes params (null) and does not validate ids
        r'''def jsonrpc(action, args):
    if action == "request":
        return {"jsonrpc": "2.0", "id": args[0], "method": args[1], "params": args[2]}
    if action == "notification":
        return {"jsonrpc": "2.0", "method": args[0], "params": args[1]}
    request, resp = args
    if not isinstance(resp, dict) or resp.get("jsonrpc") != "2.0" or resp.get("id") != request.get("id"):
        return "invalid"
    if "error" in resp:
        return "error:%d" % resp["error"]["code"]
    return "result"
''',
        # loose id comparison and no exactly-one check
        r'''def _valid_id(i):
    return isinstance(i, (str, int)) and not isinstance(i, bool)
def jsonrpc(action, args):
    if action in ("request", "notification"):
        if action == "request":
            id_, method, params = args
            if not _valid_id(id_): return "invalid"
        else:
            method, params = args
        if not isinstance(method, str) or not method: return "invalid"
        msg = {"jsonrpc": "2.0"}
        if action == "request": msg["id"] = id_
        msg["method"] = method
        if params is not None: msg["params"] = params
        return msg
    request, resp = args
    if not isinstance(resp, dict) or resp.get("jsonrpc") != "2.0":
        return "invalid"
    if str(resp.get("id")) != str(request.get("id")):
        return "invalid"
    if "error" in resp:
        err = resp["error"]
        if not isinstance(err, dict) or not isinstance(err.get("code"), int) or not isinstance(err.get("message"), str):
            return "invalid"
        return "error:%d" % err["code"]
    if "result" in resp and isinstance(resp["result"], dict):
        return "result"
    return "invalid"
''',
        # adds an id to notifications
        r'''def _valid_id(i):
    return isinstance(i, (str, int)) and not isinstance(i, bool)
def jsonrpc(action, args):
    if action in ("request", "notification"):
        if action == "request":
            id_, method, params = args
            if not _valid_id(id_): return "invalid"
        else:
            method, params = args; id_ = None
        if not isinstance(method, str) or not method: return "invalid"
        msg = {"jsonrpc": "2.0", "id": id_, "method": method}
        if params is not None: msg["params"] = params
        return msg
    request, resp = args
    if not isinstance(resp, dict) or resp.get("jsonrpc") != "2.0": return "invalid"
    rid = request.get("id")
    if "id" not in resp or type(resp["id"]) is not type(rid) or resp["id"] != rid: return "invalid"
    if ("result" in resp) == ("error" in resp): return "invalid"
    if "result" in resp: return "result" if isinstance(resp["result"], dict) else "invalid"
    err = resp["error"]
    if not isinstance(err, dict) or not isinstance(err.get("code"), int) or isinstance(err.get("code"), bool) or not isinstance(err.get("message"), str):
        return "invalid"
    return "error:%d" % err["code"]
''',
    ],
    guide=dict(
        prereqs="Lesson *The wire protocol: JSON-RPC, lifecycle, transports*.",
        intuition="JSON-RPC has only four message shapes. A request has an id and expects exactly one reply with the same id; a notification has no id and gets no reply; a reply carries either `result` or `error`, never both.",
        hints=[
            "Build the dict incrementally and add `params` only when it is not `None`.",
            "Validate ids with `isinstance(i, (str, int)) and not isinstance(i, bool)`.",
            "For responses check, in order: dict and version, id type and value, exactly one of result/error, then the shape of that member.",
        ],
        brute_force="Not applicable: this is straightforward validation logic; the care is in the edge cases.",
        approach="**Builder:** validate, then assemble `jsonrpc`, optional `id`, `method`, optional `params`.\n\n**Checker:** reject non-dicts and wrong versions; compare ids with both `type(...) is type(...)` and `==`; use `has_result == has_error` to reject both-or-neither; validate the member.\n\n**Dry run:** request id `2`, response id `'2'`: types differ, so `invalid`, even though they print the same.",
        complexity="$O(1)$ per message (ignoring the size of params).",
        pitfalls="- Sending `\"params\": null`: some servers reject it; omit the key.\n- Giving notifications an id (the receiver would then owe a response).\n- `True == 1` in Python: booleans slip through naive integer checks.\n- Matching ids loosely (`1` vs `'1'`) can pair a response with the wrong request.\n- Treating a result that contains `isError: true` as a protocol error: it is still a *result*.",
        follow_up="Track in-flight requests in a dict keyed by id and dispatch responses to waiting futures; add the 2026-07-28 `_meta` fields and the `resultType` check.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-mcp-dispatcher",
    title="MCP Tool Dispatcher",
    difficulty="Hard",
    pattern="MCP",
    entry="handle",
    description=r"""
Write the request router at the heart of an MCP server. The starter code defines three tools (`TOOLS`
with JSON schemas and `HANDLERS` with their Python implementations); keep them and implement
`handle(message)`, which takes one already-parsed JSON-RPC message and returns the response dict, or
`None` when no response must be sent.

Rules, checked in this order:

1. If `message` is not a dict, or `message["jsonrpc"] != "2.0"`, or `method` is missing or not a string,
   or an `id` is present but is not a string/integer (booleans do not count): return an error with code
   `-32600` and message `"Invalid Request"`. Use the message's id if it is a valid id, else `None`.
2. If the message has **no `id`** it is a notification: return `None` (whatever the method).
3. `"ping"`: result `{}`.
4. `"tools/list"`: result `{"tools": [...]}` with one entry per tool, **sorted by name**, each
   `{"name", "description", "inputSchema"}`.
5. `"tools/call"`:
   - `params` must be a dict with a string `name`, otherwise error `-32602`, `"Invalid params"`;
   - unknown tool: error `-32602`, `"Unknown tool: <name>"`;
   - `arguments` (default `{}`) must be a dict, otherwise `-32602`, `"Invalid params"`;
   - a missing required argument: `-32602`, `"Missing required argument: <arg>"` (report the first
     missing one in the schema's `required` order);
   - otherwise call the handler with the arguments as keyword arguments. On success return the result
     `{"content": [{"type": "text", "text": str(value)}], "isError": False}`. If the handler raises
     **any** exception, return a *successful* response whose result is
     `{"content": [{"type": "text", "text": "<ExceptionClass>: <message>"}], "isError": True}`.
6. Any other method: error `-32601`, `"Method not found: <method>"`.

Responses have the form `{"jsonrpc": "2.0", "id": <id>, "result": {...}}` or
`{"jsonrpc": "2.0", "id": <id>, "error": {"code": <int>, "message": <str>}}`.

**Example**

`handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "divide", "arguments": {"a": 1, "b": 0}}})`

returns `{"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text", "text": "ZeroDivisionError: division by zero"}], "isError": True}}`:
a tool **execution** error is a result the model can read, not a protocol error.
""",
    starter=_DISPATCH_STARTER + r'''

def handle(message):
    pass
''',
    solution=_DISPATCH_STARTER + r'''

def _valid_id(i):
    return isinstance(i, (str, int)) and not isinstance(i, bool)

def _error(id_, code, message):
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}

def _result(id_, result):
    return {"jsonrpc": "2.0", "id": id_, "result": result}

def handle(message):
    if not isinstance(message, dict):
        return _error(None, -32600, "Invalid Request")
    has_id = "id" in message
    id_ = message.get("id") if has_id and _valid_id(message.get("id")) else None
    if (message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str)
            or (has_id and not _valid_id(message["id"]))):
        return _error(id_, -32600, "Invalid Request")
    if not has_id:
        return None
    method = message["method"]
    if method == "ping":
        return _result(id_, {})
    if method == "tools/list":
        tools = [{"name": n, "description": TOOLS[n]["description"], "inputSchema": TOOLS[n]["inputSchema"]}
                 for n in sorted(TOOLS)]
        return _result(id_, {"tools": tools})
    if method == "tools/call":
        params = message.get("params")
        if not isinstance(params, dict) or not isinstance(params.get("name"), str):
            return _error(id_, -32602, "Invalid params")
        name = params["name"]
        if name not in TOOLS:
            return _error(id_, -32602, "Unknown tool: " + name)
        args = params.get("arguments", {})
        if not isinstance(args, dict):
            return _error(id_, -32602, "Invalid params")
        for req in TOOLS[name]["inputSchema"].get("required", []):
            if req not in args:
                return _error(id_, -32602, "Missing required argument: " + req)
        try:
            text, is_error = str(HANDLERS[name](**args)), False
        except Exception as e:
            text, is_error = "%s: %s" % (type(e).__name__, e), True
        return _result(id_, {"content": [{"type": "text", "text": text}], "isError": is_error})
    return _error(id_, -32601, "Method not found: " + method)
''',
    tests=[
        [{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "divide", "arguments": {"a": 1, "b": 0}}}],
        [{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}],
        [{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "add", "arguments": {"a": 2, "b": 40}}}],
        [{"jsonrpc": "2.0", "id": "abc", "method": "tools/call", "params": {"name": "echo", "arguments": {"text": "hi"}}}],
        [{"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "mul", "arguments": {}}}],
        [{"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "add", "arguments": {"b": 1}}}],
        [{"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "add", "arguments": {"a": "x", "b": 1}}}],
        [{"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "add", "arguments": [1, 2]}}],
        [{"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": {"arguments": {"a": 1}}}],
        [{"jsonrpc": "2.0", "id": 9, "method": "tools/call"}],
        [{"jsonrpc": "2.0", "id": 10, "method": "resources/list"}],
        [{"jsonrpc": "2.0", "method": "notifications/initialized"}],
        [{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "add", "arguments": {"a": 1, "b": 2}}}],
        [{"jsonrpc": "1.0", "id": 11, "method": "ping"}],
        [{"jsonrpc": "2.0", "id": 12, "method": "ping"}],
        [{"jsonrpc": "2.0", "id": 13}],
        [{"jsonrpc": "2.0", "id": None, "method": "ping"}],
        [{"jsonrpc": "2.0", "id": True, "method": "ping"}],
        ["not a dict"],
        [{"jsonrpc": "2.0", "id": 15, "method": "tools/call", "params": {"name": "divide", "arguments": {"a": 7, "b": 2}}}],
        [{"jsonrpc": "2.0", "id": 16, "method": "tools/call", "params": {"name": "echo"}}],
    ],
    examples=2,
    wrong_solutions=[
        # reports tool execution failures as protocol errors (-32603)
        _DISPATCH_STARTER + r'''
def _valid_id(i): return isinstance(i, (str, int)) and not isinstance(i, bool)
def _error(i, c, m): return {"jsonrpc": "2.0", "id": i, "error": {"code": c, "message": m}}
def _result(i, r): return {"jsonrpc": "2.0", "id": i, "result": r}
def handle(message):
    if not isinstance(message, dict): return _error(None, -32600, "Invalid Request")
    has_id = "id" in message
    id_ = message.get("id") if has_id and _valid_id(message.get("id")) else None
    if message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str) or (has_id and not _valid_id(message["id"])):
        return _error(id_, -32600, "Invalid Request")
    if not has_id: return None
    method = message["method"]
    if method == "ping": return _result(id_, {})
    if method == "tools/list":
        return _result(id_, {"tools": [{"name": n, "description": TOOLS[n]["description"], "inputSchema": TOOLS[n]["inputSchema"]} for n in sorted(TOOLS)]})
    if method == "tools/call":
        params = message.get("params")
        if not isinstance(params, dict) or not isinstance(params.get("name"), str): return _error(id_, -32602, "Invalid params")
        name = params["name"]
        if name not in TOOLS: return _error(id_, -32602, "Unknown tool: " + name)
        args = params.get("arguments", {})
        if not isinstance(args, dict): return _error(id_, -32602, "Invalid params")
        for req in TOOLS[name]["inputSchema"].get("required", []):
            if req not in args: return _error(id_, -32602, "Missing required argument: " + req)
        try:
            return _result(id_, {"content": [{"type": "text", "text": str(HANDLERS[name](**args))}], "isError": False})
        except Exception as e:
            return _error(id_, -32603, "%s: %s" % (type(e).__name__, e))
    return _error(id_, -32601, "Method not found: " + method)
''',
        # answers notifications
        _DISPATCH_STARTER + r'''
def _valid_id(i): return isinstance(i, (str, int)) and not isinstance(i, bool)
def _error(i, c, m): return {"jsonrpc": "2.0", "id": i, "error": {"code": c, "message": m}}
def _result(i, r): return {"jsonrpc": "2.0", "id": i, "result": r}
def handle(message):
    if not isinstance(message, dict): return _error(None, -32600, "Invalid Request")
    has_id = "id" in message
    id_ = message.get("id") if has_id and _valid_id(message.get("id")) else None
    if message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str) or (has_id and not _valid_id(message["id"])):
        return _error(id_, -32600, "Invalid Request")
    method = message["method"]
    if method == "ping": return _result(id_, {})
    if method == "tools/list":
        return _result(id_, {"tools": [{"name": n, "description": TOOLS[n]["description"], "inputSchema": TOOLS[n]["inputSchema"]} for n in sorted(TOOLS)]})
    if method == "tools/call":
        params = message.get("params")
        if not isinstance(params, dict) or not isinstance(params.get("name"), str): return _error(id_, -32602, "Invalid params")
        name = params["name"]
        if name not in TOOLS: return _error(id_, -32602, "Unknown tool: " + name)
        args = params.get("arguments", {})
        if not isinstance(args, dict): return _error(id_, -32602, "Invalid params")
        for req in TOOLS[name]["inputSchema"].get("required", []):
            if req not in args: return _error(id_, -32602, "Missing required argument: " + req)
        try: text, bad = str(HANDLERS[name](**args)), False
        except Exception as e: text, bad = "%s: %s" % (type(e).__name__, e), True
        return _result(id_, {"content": [{"type": "text", "text": text}], "isError": bad})
    return _error(id_, -32601, "Method not found: " + method)
''',
        # unknown tool reported as method-not-found, unknown method as invalid params
        _DISPATCH_STARTER + r'''
def _valid_id(i): return isinstance(i, (str, int)) and not isinstance(i, bool)
def _error(i, c, m): return {"jsonrpc": "2.0", "id": i, "error": {"code": c, "message": m}}
def _result(i, r): return {"jsonrpc": "2.0", "id": i, "result": r}
def handle(message):
    if not isinstance(message, dict): return _error(None, -32600, "Invalid Request")
    has_id = "id" in message
    id_ = message.get("id") if has_id and _valid_id(message.get("id")) else None
    if message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str) or (has_id and not _valid_id(message["id"])):
        return _error(id_, -32600, "Invalid Request")
    if not has_id: return None
    method = message["method"]
    if method == "ping": return _result(id_, {})
    if method == "tools/list":
        return _result(id_, {"tools": [{"name": n, "description": TOOLS[n]["description"], "inputSchema": TOOLS[n]["inputSchema"]} for n in sorted(TOOLS)]})
    if method == "tools/call":
        params = message.get("params")
        if not isinstance(params, dict) or not isinstance(params.get("name"), str): return _error(id_, -32602, "Invalid params")
        name = params["name"]
        if name not in TOOLS: return _error(id_, -32601, "Unknown tool: " + name)
        args = params.get("arguments", {})
        if not isinstance(args, dict): return _error(id_, -32602, "Invalid params")
        for req in TOOLS[name]["inputSchema"].get("required", []):
            if req not in args: return _error(id_, -32602, "Missing required argument: " + req)
        try: text, bad = str(HANDLERS[name](**args)), False
        except Exception as e: text, bad = "%s: %s" % (type(e).__name__, e), True
        return _result(id_, {"content": [{"type": "text", "text": text}], "isError": bad})
    return _error(id_, -32602, "Method not found: " + method)
''',
    ],
    guide=dict(
        prereqs="Lessons *The wire protocol* and *Why MCP: architecture and primitives*; problem *MCP JSON-RPC: Build Requests, Validate Responses*.",
        intuition="A server is a function from one message to at most one message. Peel the onion from the outside in: is it valid JSON-RPC at all, is it a notification, which method, are the params well-formed, and only then run the tool. The layer at which something fails decides the error shape: protocol layers produce JSON-RPC errors, the tool layer produces an `isError` result.",
        hints=[
            "Write tiny helpers `_error(id, code, message)` and `_result(id, result)` first; the rest becomes a chain of early returns.",
            "Decide notification-or-not with `'id' in message` (not `message.get('id')`, since an explicit `null` id is an invalid request, not a notification).",
            "Wrap only the handler call in `try/except Exception` and convert failures into `{'content': [...], 'isError': True}`.",
        ],
        brute_force="A giant nested if/else works but is hard to get right; a dispatch table `{'ping': ..., 'tools/list': ..., 'tools/call': ...}` scales better when you add `resources/*` and `prompts/*`.",
        approach="1. Envelope validation (-32600).\n2. Notification: return `None`.\n3. Route: `ping`, `tools/list` (sorted), `tools/call`, otherwise -32601.\n4. For `tools/call`: params shape, tool lookup, arguments shape, required arguments (all -32602), then execute and wrap.\n\n**Dry run:** `add` with `{'a': 'x', 'b': 1}` passes every protocol check (this exercise only checks *presence* of required arguments); the handler raises `TypeError`, so the response is a result with `isError: True` and text `TypeError: can only concatenate str (not \"int\") to str`.",
        complexity="$O(1)$ routing; `tools/list` is $O(T \\log T)$ for $T$ tools; the tool call costs whatever the handler costs.",
        pitfalls="- Responding to notifications (the spec forbids it, even with an error).\n- Turning handler exceptions into `-32603` protocol errors: the model then cannot see or fix them.\n- `-32601` for an unknown **tool**: the method `tools/call` exists; the *parameter* is wrong, so it is `-32602`.\n- Unsorted `tools/list`: unstable ordering hurts client caching and LLM prompt caching.\n- Passing extra arguments straight to the handler: here that raises `TypeError` and becomes an `isError` result; a production server would validate against the schema first.",
        follow_up="Add `resources/list` and `resources/read`; validate arguments with your JSON-schema-lite validator and return the messages as an `isError` result; add the 2026-07-28 per-request `_meta` validation, `resultType: 'complete'` and `server/discover`.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-context-packer",
    title="Context-Window Packer",
    difficulty="Medium",
    pattern="Context Engineering",
    entry="pack_context",
    description=r"""
Fit a conversation into a token budget, keeping what matters most: the system prompt and the most recent
turns.

Each message is a dict `{"role": ..., "content": ..., "tokens": int}`. Implement
`pack_context(messages, budget)`:

1. **System messages are always kept** (all of them, in their original order, at the front of the
   output), even if they alone exceed the budget.
2. If everything fits (total tokens `<= budget`), return system messages followed by the other messages
   in order.
3. Otherwise some non-system messages must be dropped. Reserve **8 tokens** for a placeholder, then keep
   the **longest contiguous suffix** of the non-system messages that fits in the remaining budget
   (walk backwards from the newest message and stop at the first one that does not fit; do not skip it
   to squeeze in older ones).
4. Insert the placeholder message
   `{"role": "user", "content": "[N earlier messages omitted]", "tokens": 8}` right after the system
   messages, where `N` is the number of dropped messages.
5. If not even the placeholder fits next to the system messages (`budget - system_tokens < 8`), return
   only the system messages.

**Example:** system (50), user (20), assistant (30), user (10), assistant (40), user (15); `budget = 130`.

Total is 165 > 130. Available for history: `130 - 50 - 8 = 72`. From the end: 15 (ok), 40 (55, ok),
10 (65, ok), 30 (95, too big: stop). Two messages are dropped, so the output is
system, placeholder "[2 earlier messages omitted]", user (10), assistant (40), user (15).
""",
    starter=r'''def pack_context(messages, budget):
    pass
''',
    solution=r'''PLACEHOLDER_TOKENS = 8

def pack_context(messages, budget):
    system = [m for m in messages if m["role"] == "system"]
    rest = [m for m in messages if m["role"] != "system"]
    sys_tokens = sum(m["tokens"] for m in system)
    if sys_tokens + sum(m["tokens"] for m in rest) <= budget:
        return system + rest
    available = budget - sys_tokens - PLACEHOLDER_TOKENS
    if available < 0:
        return system
    kept, used = [], 0
    for m in reversed(rest):
        if used + m["tokens"] > available:
            break
        kept.append(m)
        used += m["tokens"]
    kept.reverse()
    dropped = len(rest) - len(kept)
    placeholder = {"role": "user", "content": "[%d earlier messages omitted]" % dropped, "tokens": PLACEHOLDER_TOKENS}
    return system + [placeholder] + kept
''',
    tests=[
        [_CONV, 130],
        [_CONV, 165],
        [_CONV, 164],
        [_CONV, 1000],
        [_CONV, 58],
        [_CONV, 57],
        [_CONV, 10],
        [_CONV, 73],
        [_CONV, 148],
        [[], 100],
        [[_m("user", 5, "hi")], 4],
        [[_m("user", 20, "old"), _m("system", 10, "late system"), _m("user", 5, "new")], 30],
        [[_m("system", 10), _m("user", 100, "huge"), _m("assistant", 5, "small"), _m("user", 5, "latest")], 60],
        [[_m("system", 10), _m("user", 5, "a"), _m("assistant", 100, "huge"), _m("user", 5, "latest")], 60],
        [[_m("system", 5, "s1"), _m("system", 5, "s2"), _m("user", 30, "q1"), _m("assistant", 30, "a1"), _m("user", 30, "q2")], 80],
        [[_m("user", 10, "m%d" % i) for i in range(50)], 108],
    ],
    examples=2,
    wrong_solutions=[
        # skips messages that do not fit and keeps squeezing in older ones (non-contiguous history)
        r'''def pack_context(messages, budget):
    system = [m for m in messages if m["role"] == "system"]
    rest = [m for m in messages if m["role"] != "system"]
    st = sum(m["tokens"] for m in system)
    if st + sum(m["tokens"] for m in rest) <= budget:
        return system + rest
    avail = budget - st - 8
    if avail < 0:
        return system
    kept, used = [], 0
    for m in reversed(rest):
        if used + m["tokens"] <= avail:
            kept.append(m); used += m["tokens"]
    kept.reverse()
    return system + [{"role": "user", "content": "[%d earlier messages omitted]" % (len(rest) - len(kept)), "tokens": 8}] + kept
''',
        # forgets to reserve tokens for the placeholder
        r'''def pack_context(messages, budget):
    system = [m for m in messages if m["role"] == "system"]
    rest = [m for m in messages if m["role"] != "system"]
    st = sum(m["tokens"] for m in system)
    if st + sum(m["tokens"] for m in rest) <= budget:
        return system + rest
    avail = budget - st
    if avail < 8:
        return system
    kept, used = [], 0
    for m in reversed(rest):
        if used + m["tokens"] > avail:
            break
        kept.append(m); used += m["tokens"]
    kept.reverse()
    return system + [{"role": "user", "content": "[%d earlier messages omitted]" % (len(rest) - len(kept)), "tokens": 8}] + kept
''',
        # keeps the oldest messages instead of the newest
        r'''def pack_context(messages, budget):
    system = [m for m in messages if m["role"] == "system"]
    rest = [m for m in messages if m["role"] != "system"]
    st = sum(m["tokens"] for m in system)
    if st + sum(m["tokens"] for m in rest) <= budget:
        return system + rest
    avail = budget - st - 8
    if avail < 0:
        return system
    kept, used = [], 0
    for m in rest:
        if used + m["tokens"] > avail:
            break
        kept.append(m); used += m["tokens"]
    return system + [{"role": "user", "content": "[%d earlier messages omitted]" % (len(rest) - len(kept)), "tokens": 8}] + kept
''',
        # leaves system messages in place instead of moving them to the front / drops them when over budget
        r'''def pack_context(messages, budget):
    if sum(m["tokens"] for m in messages) <= budget:
        return list(messages)
    kept, used = [], 0
    for m in reversed(messages):
        if used + m["tokens"] > budget - 8:
            break
        kept.append(m); used += m["tokens"]
    kept.reverse()
    return [{"role": "user", "content": "[%d earlier messages omitted]" % (len(messages) - len(kept)), "tokens": 8}] + kept
''',
    ],
    guide=dict(
        prereqs="Lesson *The context window as a budget*; lesson *Long-horizon agents*.",
        intuition="The system prompt defines the task, and the most recent turns define the current state, so they are the last things to give up. Older history is replaced by a small marker so the model knows something was cut. Keeping a *contiguous* suffix avoids confusing gaps in the dialogue.",
        hints=[
            "Partition into system and non-system messages first; compute the system token total.",
            "Check the everything-fits case before reserving placeholder tokens.",
            "Walk `reversed(rest)`, accumulate while it fits, `break` on the first miss, then reverse what you kept.",
        ],
        brute_force="Try every suffix length from longest to shortest and return the first that fits: $O(n^2)$ with repeated sums. A single backward pass with a running total is $O(n)$.",
        approach="1. Split by role, sum tokens.\n2. If the total fits, return `system + rest`.\n3. `available = budget - system_tokens - 8`; if negative return `system`.\n4. Greedy backward scan for the longest fitting suffix.\n5. Build the placeholder with the dropped count and assemble.\n\n**Dry run** (example): available 72; keep 15, 40, 10 (65); the next message (30) would make 95, stop. Dropped 2.",
        complexity="$O(n)$ time and space.",
        pitfalls="- Skipping an oversized message and continuing to older ones: the model would see a conversation with a hole in it.\n- Forgetting to budget for the placeholder, ending up over the limit.\n- Dropping or truncating the system prompt.\n- Emitting a placeholder when nothing was dropped.\n- In real APIs you must also keep tool-call/tool-result pairs together and make sure the first kept message has a valid role.",
        follow_up="Keep tool calls paired with their results; replace the placeholder by an LLM-written summary (see the compaction problem); pin the first user message that states the goal.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-compaction-policy",
    title="Conversation Compaction Policy",
    difficulty="Hard",
    pattern="Context Engineering",
    entry="compact",
    description=r"""
Implement the two-stage context-management policy of a long-running agent: first clear stale tool
results, and only if that is not enough, summarise old history.

Messages are dicts `{"role": "system"|"user"|"assistant"|"tool", "content": str, "tokens": int}`.
`compact(messages, limit, trigger_pct, keep_recent)` returns `{"action": ..., "messages": [...]}`.

Let `total` be the sum of tokens. Everything uses integer arithmetic: the context is "over the trigger"
when `total * 100 > trigger_pct * limit`.

**Stage 0.** If not over the trigger, return `{"action": "none", "messages": messages}` unchanged.

**Stage 1: clear tool results.** Among `tool` messages, protect the last `keep_recent` of them. Every
other tool message with more than 10 tokens becomes a copy with `content = "[cleared]"` and
`tokens = 10`. If the new total is no longer over the trigger, return `{"action": "clear", ...}`.

**Stage 2: summarise** (starting from the stage-1 result).

- System messages are kept, at the front, in order.
- From the non-system messages keep the last `keep_recent`. The kept window must **not start with a
  `tool` message** (a tool result without its call is invalid): while it does, extend the window one
  message further back.
- Replace all older non-system messages (if there are `n > 0` of them, totalling `t` tokens) with a
  single message `{"role": "user", "content": "[summary of n messages]", "tokens": max(20, t // 10)}`
  placed right after the system messages.
- Return `{"action": "summarize", "messages": system + [summary] + kept}`.

Never mutate the input messages.

**Example:** a 200-token system prompt, then alternating assistant calls and big tool results. With
`limit = 10000`, `trigger_pct = 80`, `keep_recent = 2`: if the total is 11,080, clearing the two oldest
tool results (4,000 and 2,000 tokens) brings it to 5,100, which is under 8,000, so the action is
`"clear"`.
""",
    starter=r'''def compact(messages, limit, trigger_pct=80, keep_recent=2):
    pass
''',
    solution=r'''def _total(msgs):
    return sum(m["tokens"] for m in msgs)

def compact(messages, limit, trigger_pct=80, keep_recent=2):
    def over(msgs):
        return _total(msgs) * 100 > trigger_pct * limit

    if not over(messages):
        return {"action": "none", "messages": messages}

    tool_idx = [i for i, m in enumerate(messages) if m["role"] == "tool"]
    protected = set(tool_idx[len(tool_idx) - keep_recent:]) if keep_recent > 0 else set()
    cleared = []
    for i, m in enumerate(messages):
        if m["role"] == "tool" and i not in protected and m["tokens"] > 10:
            m = dict(m, content="[cleared]", tokens=10)
        cleared.append(m)
    if not over(cleared):
        return {"action": "clear", "messages": cleared}

    system = [m for m in cleared if m["role"] == "system"]
    rest = [m for m in cleared if m["role"] != "system"]
    start = max(0, len(rest) - keep_recent)
    while start > 0 and start < len(rest) and rest[start]["role"] == "tool":
        start -= 1
    old, kept = rest[:start], rest[start:]
    out = list(system)
    if old:
        out.append({"role": "user", "content": "[summary of %d messages]" % len(old),
                    "tokens": max(20, _total(old) // 10)})
    return {"action": "summarize", "messages": out + kept}
''',
    tests=[
        [_AGENT, 10000, 80, 2],
        [_AGENT, 100000, 80, 2],
        [_AGENT, 5000, 80, 2],
        [_AGENT, 10000, 80, 0],
        [_AGENT, 4000, 50, 1],
        [_AGENT, 12000, 80, 10],
        [[], 100, 80, 2],
        [[_m("system", 50), _m("user", 500, "q1"), _m("assistant", 500, "a1"), _m("user", 500, "q2"),
          _m("assistant", 500, "a2")], 2000, 80, 2],
        [[_m("system", 50), _m("user", 500, "q1"), _m("assistant", 500, "a1"), _m("user", 500, "q2"),
          _m("assistant", 500, "a2")], 2000, 80, 0],
        [[_m("system", 900, "big system")], 1000, 80, 2],
        [[_m("user", 30, "goal"), _m("assistant", 5, "call"), _m("tool", 8, "tiny"), _m("assistant", 5, "call"),
          _m("tool", 500, "big"), _m("assistant", 5, "call"), _m("tool", 500, "big2")], 600, 80, 1],
        [[_m("user", 300, "goal"), _m("assistant", 300, "call"), _m("tool", 300, "r1"), _m("tool", 300, "r2"),
          _m("assistant", 300, "done")], 1000, 80, 2],
        [[_m("user", 2051, "a"), _m("assistant", 3000, "b"), _m("user", 3000, "c")], 10000, 80, 1],
        [[_m("user", 2000, "a"), _m("assistant", 3000, "b"), _m("user", 3000, "c")], 10000, 80, 1],
        [[_m("system", 10), _m("tool", 400, "orphan-ish"), _m("tool", 400, "second"), _m("assistant", 400, "x")], 500, 80, 2],
    ],
    examples=2,
    wrong_solutions=[
        # jumps straight to summarising (never tries the cheaper clearing stage) and ignores tool pairing
        r'''def compact(messages, limit, trigger_pct=80, keep_recent=2):
    total = sum(m["tokens"] for m in messages)
    if total * 100 <= trigger_pct * limit:
        return {"action": "none", "messages": messages}
    system = [m for m in messages if m["role"] == "system"]
    rest = [m for m in messages if m["role"] != "system"]
    start = max(0, len(rest) - keep_recent)
    old, kept = rest[:start], rest[start:]
    out = list(system)
    if old:
        out.append({"role": "user", "content": "[summary of %d messages]" % len(old), "tokens": max(20, sum(m["tokens"] for m in old) // 10)})
    return {"action": "summarize", "messages": out + kept}
''',
        # clears every tool result, including the protected recent ones
        r'''def compact(messages, limit, trigger_pct=80, keep_recent=2):
    def over(ms): return sum(m["tokens"] for m in ms) * 100 > trigger_pct * limit
    if not over(messages):
        return {"action": "none", "messages": messages}
    cleared = [dict(m, content="[cleared]", tokens=10) if m["role"] == "tool" and m["tokens"] > 10 else m for m in messages]
    if not over(cleared):
        return {"action": "clear", "messages": cleared}
    system = [m for m in cleared if m["role"] == "system"]
    rest = [m for m in cleared if m["role"] != "system"]
    start = max(0, len(rest) - keep_recent)
    while 0 < start < len(rest) and rest[start]["role"] == "tool":
        start -= 1
    old, kept = rest[:start], rest[start:]
    out = list(system)
    if old:
        out.append({"role": "user", "content": "[summary of %d messages]" % len(old), "tokens": max(20, sum(m["tokens"] for m in old) // 10)})
    return {"action": "summarize", "messages": out + kept}
''',
        # the kept window may start with an orphaned tool result
        r'''def compact(messages, limit, trigger_pct=80, keep_recent=2):
    def over(ms): return sum(m["tokens"] for m in ms) * 100 > trigger_pct * limit
    if not over(messages):
        return {"action": "none", "messages": messages}
    tool_idx = [i for i, m in enumerate(messages) if m["role"] == "tool"]
    protected = set(tool_idx[len(tool_idx) - keep_recent:]) if keep_recent > 0 else set()
    cleared = [dict(m, content="[cleared]", tokens=10) if m["role"] == "tool" and i not in protected and m["tokens"] > 10 else m
               for i, m in enumerate(messages)]
    if not over(cleared):
        return {"action": "clear", "messages": cleared}
    system = [m for m in cleared if m["role"] == "system"]
    rest = [m for m in cleared if m["role"] != "system"]
    start = max(0, len(rest) - keep_recent)
    old, kept = rest[:start], rest[start:]
    out = list(system)
    if old:
        out.append({"role": "user", "content": "[summary of %d messages]" % len(old), "tokens": max(20, sum(m["tokens"] for m in old) // 10)})
    return {"action": "summarize", "messages": out + kept}
''',
        # uses >= for the trigger and float maths
        r'''def compact(messages, limit, trigger_pct=80, keep_recent=2):
    def over(ms): return sum(m["tokens"] for m in ms) >= trigger_pct / 100 * limit
    if not over(messages):
        return {"action": "none", "messages": messages}
    tool_idx = [i for i, m in enumerate(messages) if m["role"] == "tool"]
    protected = set(tool_idx[len(tool_idx) - keep_recent:]) if keep_recent > 0 else set()
    cleared = [dict(m, content="[cleared]", tokens=10) if m["role"] == "tool" and i not in protected and m["tokens"] > 10 else m
               for i, m in enumerate(messages)]
    if not over(cleared):
        return {"action": "clear", "messages": cleared}
    system = [m for m in cleared if m["role"] == "system"]
    rest = [m for m in cleared if m["role"] != "system"]
    start = max(0, len(rest) - keep_recent)
    while 0 < start < len(rest) and rest[start]["role"] == "tool":
        start -= 1
    old, kept = rest[:start], rest[start:]
    out = list(system)
    if old:
        out.append({"role": "user", "content": "[summary of %d messages]" % len(old), "tokens": max(20, sum(m["tokens"] for m in old) // 10)})
    return {"action": "summarize", "messages": out + kept}
''',
    ],
    guide=dict(
        prereqs="Lesson *Long-horizon agents: compaction, notes, memory and sub-agents*; problem *Context-Window Packer*.",
        intuition="Escalate from the cheapest, safest intervention to the most lossy. Old tool outputs are bulky and rarely needed again, so blank them first. Only if the context is still too full do you replace old turns with a summary, and when you cut history you must cut at a point that leaves a well-formed conversation.",
        hints=[
            "Write `over(msgs)` once with integer maths: `total * 100 > trigger_pct * limit`.",
            "Find the indices of tool messages; the protected ones are the last `keep_recent` (careful: `lst[-0:]` is the whole list, so handle `keep_recent == 0`).",
            "For stage 2 compute `start = max(0, len(rest) - keep_recent)` and move it left while `rest[start]` is a tool message.",
        ],
        brute_force="Summarise whenever the trigger fires. It works, but throws away recent detail unnecessarily, costs an LLM call, and resets the prompt cache every time; the staged policy avoids all three in the common case.",
        approach="1. Stage 0: under the trigger, return unchanged.\n2. Stage 1: copy the list, clearing unprotected tool results over 10 tokens; re-check.\n3. Stage 2: split system/non-system; pick the kept window and repair its boundary; build the summary message from the rest.\n\n**Dry run** (`_AGENT`-style, limit 10,000, keep 2): total 11,080 > 8,000. Tool results are 4000, 2000, 4100, 600; the last two are protected; clearing the first two saves 5,980, new total 5,100, not over: action `clear`.",
        complexity="$O(n)$ time and space.",
        pitfalls="- `tool_idx[-keep_recent:]` with `keep_recent == 0` protects everything.\n- Mutating the caller's message dicts instead of copying.\n- Starting the kept window on a `tool` message (APIs reject a tool result whose call was removed).\n- Emitting a summary message when nothing was summarised.\n- Off-by-one at exactly the trigger (`>` versus `>=`), and float rounding when computing the threshold.",
        follow_up="Batch clearing to protect the prompt cache (only clear when it frees at least X tokens); always preserve the first user message verbatim; re-attach the most recently read files after summarising, as coding agents do.",
    ),
),
# ---------------------------------------------------------------------------------------------
dict(
    id="llm-stream-accumulate",
    title="Accumulate a Streaming Response",
    difficulty="Medium",
    pattern="LLM Applications",
    entry="accumulate",
    description=r"""
Rebuild a complete assistant message from a list of streaming events (Anthropic Messages API style).

Event types:

- `{"type": "message_start", "message": {...}}`: ignore.
- `{"type": "content_block_start", "index": i, "content_block": {"type": "text"}}` or
  `{"type": "tool_use", "id": ..., "name": ...}` or `{"type": "thinking"}`: opens block `i`.
- `{"type": "content_block_delta", "index": i, "delta": d}` where `d` is
  `{"type": "text_delta", "text": s}`, `{"type": "thinking_delta", "thinking": s}` or
  `{"type": "input_json_delta", "partial_json": s}`: append `s` to block `i`'s buffer.
- `{"type": "content_block_stop", "index": i}`: closes block `i`.
- `{"type": "message_delta", "delta": {"stop_reason": r}, "usage": {"output_tokens": n}}`: records the
  stop reason and output token count (either may be absent; keep the last values seen).
- `{"type": "ping"}`: ignore.
- `{"type": "error", ...}`: set the stop reason to `"error"` and **stop processing** further events.
- `{"type": "message_stop"}`: end of stream.

Return `{"content": [...], "stop_reason": r, "output_tokens": n}` where `content` lists the blocks in
ascending index order:

- text: `{"type": "text", "text": <joined text>}`
- thinking: `{"type": "thinking", "thinking": <joined text>}`
- tool use: `{"type": "tool_use", "id": ..., "name": ..., "input": <parsed JSON>}`. The input is the
  concatenation of all `partial_json` fragments parsed as JSON; an **empty** buffer means `{}`. If the
  block was never closed, or the buffer is not valid JSON, the input is `None`.

`stop_reason` and `output_tokens` default to `None` if never reported. Text and thinking blocks that
were never closed still return whatever was accumulated.

**Example:** a text block receiving `"Let me check "` then `"the weather."`, followed by a tool block
receiving `'{"city": "Os'` and `'lo"}'`, then a `message_delta` with stop reason `tool_use` produces

`{"content": [{"type": "text", "text": "Let me check the weather."}, {"type": "tool_use", "id": "toolu_1", "name": "get_weather", "input": {"city": "Oslo"}}], "stop_reason": "tool_use", "output_tokens": 42}`.
""",
    starter=r'''import json

def accumulate(events):
    pass
''',
    solution=r'''import json

def accumulate(events):
    blocks, buf, closed = {}, {}, set()
    stop_reason, output_tokens = None, None
    for e in events:
        t = e.get("type")
        if t == "content_block_start":
            i = e["index"]
            blocks[i] = e.get("content_block", {})
            buf[i] = ""
        elif t == "content_block_delta":
            i, d = e["index"], e.get("delta", {})
            if i in buf:
                buf[i] += d.get("text", "") + d.get("thinking", "") + d.get("partial_json", "")
        elif t == "content_block_stop":
            closed.add(e["index"])
        elif t == "message_delta":
            if "stop_reason" in e.get("delta", {}):
                stop_reason = e["delta"]["stop_reason"]
            if "output_tokens" in e.get("usage", {}):
                output_tokens = e["usage"]["output_tokens"]
        elif t == "error":
            stop_reason = "error"
            break
        elif t == "message_stop":
            break
    content = []
    for i in sorted(blocks):
        b = blocks[i]
        kind = b.get("type")
        if kind == "tool_use":
            value = None
            if i in closed:
                if buf[i] == "":
                    value = {}
                else:
                    try:
                        value = json.loads(buf[i])
                    except json.JSONDecodeError:
                        value = None
            content.append({"type": "tool_use", "id": b.get("id"), "name": b.get("name"), "input": value})
        elif kind == "thinking":
            content.append({"type": "thinking", "thinking": buf[i]})
        else:
            content.append({"type": "text", "text": buf[i]})
    return {"content": content, "stop_reason": stop_reason, "output_tokens": output_tokens}
''',
    tests=[
        [_START + _ev_text(0, "Let me check ", "the weather.") + _ev_tool(1, "toolu_1", "get_weather", '{"city": "Os', 'lo"}')
         + _end("tool_use", 42)],
        [_START + _ev_text(0, "Hello", ", ", "world", "!") + _end("end_turn", 6)],
        [[]],
        [_START + _ev_tool(0, "toolu_9", "get_time") + _end("tool_use", 12)],
        [_START + _ev_text(0, "Part") + [{"type": "ping"}] + _ev_tool(1, "t1", "a", '{"x"', ": [1, ", "2]}")
         + _ev_tool(2, "t2", "b", '{"y": {"z": null}}') + _end("tool_use", 30)],
        [_START + _ev_text(0, "Cut off mid")[:-1] + [{"type": "message_delta", "delta": {"stop_reason": "max_tokens"}, "usage": {"output_tokens": 4096}},
                                                    {"type": "message_stop"}]],
        [_START + _ev_tool(0, "t1", "search", '{"query": "kv ca', stop=False)
         + [{"type": "message_delta", "delta": {"stop_reason": "max_tokens"}, "usage": {"output_tokens": 100}}, {"type": "message_stop"}]],
        [_START + _ev_tool(0, "t1", "search", '{"query": "kv cache"', ) + _end("tool_use", 20)],
        [_START + _ev_text(0, "Partial ans") [:-1] + [{"type": "error", "error": {"type": "overloaded_error", "message": "Overloaded"}}]
         + _ev_text(1, "never seen") + _end("end_turn", 99)],
        [_START + [{"type": "content_block_start", "index": 0, "content_block": {"type": "thinking", "thinking": ""}},
                   {"type": "content_block_delta", "index": 0, "delta": {"type": "thinking_delta", "thinking": "Compare the "}},
                   {"type": "content_block_delta", "index": 0, "delta": {"type": "thinking_delta", "thinking": "two years."}},
                   {"type": "content_block_stop", "index": 0}] + _ev_text(1, "Four years.") + _end("end_turn", 15)],
        [_START + _ev_text(1, "second") + _ev_text(0, "first") + _end("end_turn", 3)],
        [_START + _ev_text(0, "x")
         + [{"type": "message_delta", "delta": {"stop_reason": "pause_turn"}, "usage": {"output_tokens": 5}},
            {"type": "message_delta", "delta": {}, "usage": {"output_tokens": 9}},
            {"type": "message_delta", "delta": {"stop_reason": "end_turn"}},
            {"type": "message_stop"}]],
        [_START + _ev_text(0, "naïve café ", "🤖") + _ev_tool(1, "t", "f", "[1, 2, 3]") + _end("tool_use", 8)],
        [_START + _ev_text(0, "done") + _end("end_turn", 2) + _ev_text(1, "after stop")],
    ],
    examples=2,
    wrong_solutions=[
        # parses each partial_json fragment separately instead of concatenating first
        r'''import json
def accumulate(events):
    blocks, stop, toks = {}, None, None
    for e in events:
        t = e.get("type")
        if t == "content_block_start":
            b = dict(e["content_block"]); k = b.get("type")
            blocks[e["index"]] = {"type": "tool_use", "id": b.get("id"), "name": b.get("name"), "input": {}} if k == "tool_use" else ({"type": "thinking", "thinking": ""} if k == "thinking" else {"type": "text", "text": ""})
        elif t == "content_block_delta":
            b, d = blocks[e["index"]], e["delta"]
            if b["type"] == "text": b["text"] += d.get("text", "")
            elif b["type"] == "thinking": b["thinking"] += d.get("thinking", "")
            else:
                try: b["input"] = json.loads(d.get("partial_json", ""))
                except Exception: b["input"] = None
        elif t == "message_delta":
            stop = e.get("delta", {}).get("stop_reason", stop); toks = e.get("usage", {}).get("output_tokens", toks)
        elif t == "error":
            stop = "error"; break
        elif t == "message_stop":
            break
    return {"content": [blocks[i] for i in sorted(blocks)], "stop_reason": stop, "output_tokens": toks}
''',
        # returns blocks in arrival order and keeps processing after an error
        r'''import json
def accumulate(events):
    blocks, buf, closed, order = {}, {}, set(), []
    stop, toks = None, None
    for e in events:
        t = e.get("type")
        if t == "content_block_start":
            blocks[e["index"]] = e["content_block"]; buf[e["index"]] = ""; order.append(e["index"])
        elif t == "content_block_delta":
            d = e["delta"]; buf[e["index"]] += d.get("text", "") + d.get("thinking", "") + d.get("partial_json", "")
        elif t == "content_block_stop":
            closed.add(e["index"])
        elif t == "message_delta":
            stop = e.get("delta", {}).get("stop_reason", stop); toks = e.get("usage", {}).get("output_tokens", toks)
        elif t == "error":
            stop = "error"
    out = []
    for i in order:
        b = blocks[i]
        if b.get("type") == "tool_use":
            v = None
            if i in closed:
                try: v = json.loads(buf[i]) if buf[i] else {}
                except Exception: v = None
            out.append({"type": "tool_use", "id": b.get("id"), "name": b.get("name"), "input": v})
        elif b.get("type") == "thinking":
            out.append({"type": "thinking", "thinking": buf[i]})
        else:
            out.append({"type": "text", "text": buf[i]})
    return {"content": out, "stop_reason": stop, "output_tokens": toks}
''',
        # treats unclosed / invalid tool JSON as {} and empty input as None
        r'''import json
def accumulate(events):
    blocks, buf = {}, {}
    stop, toks = None, None
    for e in events:
        t = e.get("type")
        if t == "content_block_start":
            blocks[e["index"]] = e["content_block"]; buf[e["index"]] = ""
        elif t == "content_block_delta":
            d = e["delta"]; buf[e["index"]] += d.get("text", "") + d.get("thinking", "") + d.get("partial_json", "")
        elif t == "message_delta":
            stop = e.get("delta", {}).get("stop_reason", stop); toks = e.get("usage", {}).get("output_tokens", toks)
        elif t == "error":
            stop = "error"; break
        elif t == "message_stop":
            break
    out = []
    for i in sorted(blocks):
        b = blocks[i]
        if b.get("type") == "tool_use":
            try: v = json.loads(buf[i])
            except Exception: v = {} if buf[i] else None
            out.append({"type": "tool_use", "id": b.get("id"), "name": b.get("name"), "input": v})
        elif b.get("type") == "thinking":
            out.append({"type": "thinking", "thinking": buf[i]})
        else:
            out.append({"type": "text", "text": buf[i]})
    return {"content": out, "stop_reason": stop, "output_tokens": toks}
''',
    ],
    guide=dict(
        prereqs="Lesson *Structured outputs and streaming*, section on accumulating a stream by hand.",
        intuition="A stream is the final message chopped into small edits addressed by block index. Keep a string buffer per block, append every delta, and only interpret a tool block's buffer as JSON once the block has been closed, because the fragments are arbitrary slices of a JSON string.",
        hints=[
            "Use three dicts/sets keyed by index: the block header from `content_block_start`, a string buffer, and the set of closed indices.",
            "Append `delta.get('text', '') + delta.get('thinking', '') + delta.get('partial_json', '')`: only one of them is present.",
            "After the loop, build the content in `sorted(blocks)` order; parse tool input only if the block is closed, with `''` meaning `{}` and a `try/except` for bad JSON.",
        ],
        brute_force="Concatenate all text deltas into one string and regex the tool JSON out of it. It loses block boundaries, breaks with several tool calls and cannot distinguish thinking from text; per-index buffers are both simpler and correct.",
        approach="1. Single pass over events with a small state machine.\n2. `error` and `message_stop` end processing; `ping` and `message_start` are ignored.\n3. Finalise blocks in index order.\n\n**Dry run** (example): buffer 0 becomes `Let me check the weather.`; buffer 1 becomes `{\"city\": \"Oslo\"}`, block 1 is closed, so it parses to `{'city': 'Oslo'}`; stop reason `tool_use`, 42 output tokens.",
        complexity="$O(n)$ in the number of events plus the total length of the deltas.",
        pitfalls="- Calling `json.loads` on each fragment: `'{\"city\": \"Os'` is not JSON.\n- A tool with no arguments streams no `partial_json` at all: the input is `{}`, not an error.\n- A stream cut by `max_tokens` leaves a tool block unclosed: its input is unusable (`None`), and the caller must check the stop reason.\n- Mid-stream `error` events arrive after an HTTP 200; do not keep processing.\n- Blocks can be listed out of order in tests; sort by index.",
        follow_up="Emit incremental UI updates (callbacks per delta); use a partial-JSON parser to show tool arguments while they stream; adapt the function to OpenAI's `chat.completion.chunk` format where tool-call fragments are keyed by `tool_calls[i].index`.",
    ),
),
]
