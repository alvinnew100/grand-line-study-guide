PROBLEMS = [
dict(
    id="fastapi-error-mapper",
    title="Map Exceptions to Responses through the Class Hierarchy",
    difficulty="Easy",
    pattern="Error Handling",
    entry="mapErrors",
    description=r"""
FastAPI's `@app.exception_handler(SomeError)` registers a handler for a class of exceptions. When an
exception escapes an endpoint, Starlette looks for a handler for its class, then its parent class,
then the grandparent, and so on up to `Exception`. If none is found, the client gets a plain
`500 Internal Server Error` that reveals nothing about the cause. Implement the lookup.

`mapErrors(handlers, parents, raised)`:

- `parents` maps a class name to its parent class name (single inheritance). The root is
  `"Exception"`. A class that appears nowhere in `parents` (and is not `"Exception"`) is a direct
  child of `"Exception"`.
- `handlers` maps a class name to `[status, template]`. In the template, every occurrence of
  `{msg}` is replaced by the exception's message; no other placeholder is special (any other braces
  stay as they are).
- `raised` is a list of `[class_name, message]`.
- For each raised exception, walk from its class up through its ancestors to `"Exception"`
  (inclusive) and use the first class that has a handler. If none does, the result is
  `[500, "Internal Server Error"]`; the message is **never** included in that fallback.

Return one `[status, detail]` per raised exception, in order.

**Example:** with `handlers = {"Missing": [404, "{msg} not found"]}` and
`parents = {"ExplorerMissing": "Missing", "Missing": "DomainError", "DomainError": "Exception"}`,
`raised = [["ExplorerMissing", "explorer ann"], ["KeyError", "x"]]` →
`[[404, "explorer ann not found"], [500, "Internal Server Error"]]`
""",
    starter='''def mapErrors(handlers: dict, parents: dict, raised: list) -> list:
    pass
''',
    solution='''def mapErrors(handlers, parents, raised):
    out = []
    for name, message in raised:
        cls, result = name, None
        while True:
            if cls in handlers:
                status, template = handlers[cls]
                result = [status, template.replace("{msg}", message)]
                break
            if cls == "Exception":
                break
            cls = parents.get(cls, "Exception")
        out.append(result or [500, "Internal Server Error"])
    return out
''',
    tests=[
        [{"Missing": [404, "{msg} not found"]},
         {"ExplorerMissing": "Missing", "Missing": "DomainError", "DomainError": "Exception"},
         [["ExplorerMissing", "explorer ann"], ["KeyError", "x"]]],
        [{"Missing": [404, "{msg} not found"], "Duplicate": [409, "{msg} already exists"], "DomainError": [400, "bad request: {msg}"]},
         {"Missing": "DomainError", "Duplicate": "DomainError", "RateLimited": "DomainError", "DomainError": "Exception"},
         [["Missing", "creature 7"], ["Duplicate", "yeti"], ["RateLimited", "too many"]]],
        [{"DomainError": [400, "{msg}"]},
         {"ZeroDivisionError": "ArithmeticError", "ArithmeticError": "Exception", "DomainError": "Exception"},
         [["ZeroDivisionError", "division by zero"]]],
        [{"DomainError": [400, "{msg}"], "Exception": [500, "internal error"]},
         {"ZeroDivisionError": "ArithmeticError", "ArithmeticError": "Exception", "DomainError": "Exception"},
         [["ZeroDivisionError", "division by zero"], ["DomainError", "nope"], ["Weird", "w"]]],
        [{"PermissionDenied": [403, "forbidden"]}, {"PermissionDenied": "DomainError"}, [["PermissionDenied", "user 5 on item 9"]]],
        [{"Missing": [404, "{msg} / {msg}"]}, {}, [["Missing", "a"]]],
        [{"Missing": [404, "x"]}, {}, []],
        [{"Exception": [500, "oops"], "DomainError": [400, "domain"], "Missing": [404, "missing"]},
         {"Missing": "DomainError", "DomainError": "Exception"}, [["Missing", ""], ["DomainError", ""], ["Exception", ""]]],
        [{"Missing": [404, "{msg} not found {detail}"]}, {}, [["Missing", "item {7}"]]],
        [{"Missing": [404, "{msg} not found"]}, {"Missing": "DomainError"}, [["Missing", "{msg}"]]],
        [{"Base": [418, "teapot: {msg}"]},
         {f"L{i}": (f"L{i - 1}" if i > 0 else "Base") for i in range(50)} | {"Base": "Exception"},
         [["L49", "deep"], ["L0", "shallow"], ["Other", "none"]]],
        [{"ValueError": [422, "invalid value"]}, {"UnicodeError": "ValueError", "ValueError": "Exception", "UnicodeDecodeError": "UnicodeError"},
         [["UnicodeDecodeError", "bad byte"], ["TypeError", "t"]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def mapErrors(handlers, parents, raised):
    out = []
    for name, message in raised:
        if name in handlers:
            s, t = handlers[name]
            out.append([s, t.replace("{msg}", message)])
        elif "Exception" in handlers:
            s, t = handlers["Exception"]
            out.append([s, t.replace("{msg}", message)])
        else:
            out.append([500, "Internal Server Error"])
    return out
''',
        '''def mapErrors(handlers, parents, raised):
    out = []
    for name, message in raised:
        cls = name
        while cls not in handlers and cls != "Exception":
            cls = parents.get(cls, "Exception")
        if cls in handlers:
            s, t = handlers[cls]
            out.append([s, t.replace("{msg}", message)])
        else:
            out.append([500, message])
    return out
''',
        '''def mapErrors(handlers, parents, raised):
    out = []
    for name, message in raised:
        cls = name
        while cls not in handlers and cls != "Exception":
            cls = parents.get(cls, "Exception")
        if cls in handlers:
            s, t = handlers[cls]
            out.append([s, t.format(msg=message)])
        else:
            out.append([500, "Internal Server Error"])
    return out
''',
    ],
    guide=dict(
        prereqs="Custom exception handlers and domain exceptions (lessons *Layered architecture: web, service, "
                "data* and *Errors, exception handlers and middleware*); class inheritance.",
        intuition="Handlers are registered per class, but exceptions arrive as instances of subclasses. "
                  "Walking up the inheritance chain until something claims the exception is exactly how "
                  "an `except DomainError:` clause catches a `Missing`. The fallback must be generic: a 500 "
                  "means *your* bug, and its message may contain SQL, file paths or secrets.",
        hints=["Loop: check `handlers` for the current class, then move to `parents.get(cls, 'Exception')`.",
               "Stop after checking `'Exception'` itself.",
               "Use `str.replace('{msg}', message)`, not `str.format`: other braces must survive."],
        brute_force="Looking up only the exact class name misses every subclass, which is the whole point "
                    "of a hierarchy of domain errors.",
        approach="For each raised exception, walk the chain checking for a handler; format the first one "
                 "found; otherwise return the generic 500.\n\nDry run of the example: `ExplorerMissing` has "
                 "no handler → parent `Missing` does → `[404, 'explorer ann not found']`. `KeyError` is not "
                 "in `parents` → parent is `Exception` → no handler → `[500, 'Internal Server Error']`.",
        complexity="O(d) per exception for an inheritance depth d.",
        pitfalls="- Leaking the exception message in the 500 fallback.\n- Using `template.format(msg=...)`: it "
                 "raises `KeyError` as soon as a template contains any other braces, such as `{detail}`.\n"
                 "- Forgetting that an unknown class still inherits from `Exception`, so a catch-all applies.",
        follow_up="Starlette walks the real `type(exc).__mro__`. FastAPI also installs default handlers for "
                  "`HTTPException` and `RequestValidationError`; overriding the latter is how you reshape "
                  "422 bodies into a uniform error envelope.",
    ),
),
dict(
    id="fastapi-sse-encode",
    title="Encode Server-Sent Events",
    difficulty="Easy",
    pattern="Streaming",
    entry="encodeSSE",
    description=r"""
A streaming endpoint has to turn each event into the `text/event-stream` wire format. Write the
encoder (the opposite direction of the problem *Parse a Server-Sent Events Stream*).

`encodeSSE(events)` takes a list of dicts and returns the whole stream as one string. Each dict may
contain `comment`, `event`, `id`, `retry` and `data`; a missing key or the value `None` means "not
set". For each event, produce these lines **in this order**:

1. `comment`: one line `": " + line` for each line of the comment.
2. `event`: `"event: " + value`, if it is a non-empty string (event names never contain line breaks).
3. `id`: `"id: " + value`, if set, **unless** it contains `\n`, `\r` or `\x00`, in which case the id
   is left out. An empty string id is allowed and produces `"id: "`.
4. `retry`: `"retry: " + str(value)`, if it is an integer `>= 0`; negative values are left out.
5. `data`: one line `"data: " + line` for each line of the data. The value is written exactly as
   given (no stripping), and an empty string produces one line `"data: "`.

"Lines" of a comment or data value: first turn `\r\n` and lone `\r` into `\n`, then split on `\n`.
Join the event's lines with `\n` and end the event with a blank line (`"\n\n"` after the last line).
An event that produces no lines at all contributes nothing.

**Example:** `encodeSSE([{"event": "token", "id": "1", "data": "Hi"}, {"comment": "ping"}])` →
`"event: token\nid: 1\ndata: Hi\n\n: ping\n\n"`
""",
    starter='''def encodeSSE(events: list[dict]) -> str:
    pass
''',
    solution=r'''def _lines(text):
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

def encodeSSE(events):
    out = []
    for ev in events:
        lines = []
        if ev.get("comment") is not None:
            lines += [": " + line for line in _lines(ev["comment"])]
        if ev.get("event"):
            lines.append("event: " + ev["event"])
        eid = ev.get("id")
        if eid is not None and not any(c in eid for c in ("\n", "\r", "\x00")):
            lines.append("id: " + eid)
        retry = ev.get("retry")
        if isinstance(retry, int) and not isinstance(retry, bool) and retry >= 0:
            lines.append("retry: " + str(retry))
        if ev.get("data") is not None:
            lines += ["data: " + line for line in _lines(ev["data"])]
        if lines:
            out.append("\n".join(lines) + "\n\n")
    return "".join(out)
''',
    tests=[
        [[{"event": "token", "id": "1", "data": "Hi"}, {"comment": "ping"}]],
        [[{"data": "hello"}]],
        [[{"event": "token", "id": "7", "data": "{\"text\": \" world\"}"}]],
        [[{"data": "line1\nline2"}]],
        [[{"data": "a\r\nb\rc"}]],
        [[{}, {"data": None}, {"event": ""}]],
        [[]],
        [[{"data": ""}]],
        [[{"data": " streams"}, {"data": "tail  "}]],
        [[{"id": "a\nb", "data": "x"}, {"id": "bad\x00id", "data": "y"}, {"id": "", "data": "z"}]],
        [[{"retry": 3000}, {"retry": -5}, {"retry": 0, "data": "r"}]],
        [[{"data": "payload", "retry": 1500, "id": "42", "event": "update", "comment": "first\nsecond"}]],
        [[{"event": "done"}]],
        [[{"event": "token", "id": str(i), "data": f" tok{i}"} for i in range(200)] + [{"data": "[DONE]"}]],
    ],
    examples=2,
    wrong_solutions=[
        '''def encodeSSE(events):
    out = ""
    for ev in events:
        lines = []
        if ev.get("comment") is not None: lines.append(": " + ev["comment"])
        if ev.get("event"): lines.append("event: " + ev["event"])
        if ev.get("id") is not None: lines.append("id: " + ev["id"])
        if isinstance(ev.get("retry"), int) and ev["retry"] >= 0: lines.append("retry: " + str(ev["retry"]))
        if ev.get("data") is not None: lines.append("data: " + ev["data"])
        if lines: out += "\\n".join(lines) + "\\n\\n"
    return out
''',
        '''def encodeSSE(events):
    out = ""
    for ev in events:
        lines = []
        norm = lambda t: t.replace("\\r\\n", "\\n").replace("\\r", "\\n").split("\\n")
        if ev.get("comment") is not None: lines += [": " + l.strip() for l in norm(ev["comment"])]
        if ev.get("event"): lines.append("event: " + ev["event"])
        eid = ev.get("id")
        if eid is not None and not any(c in eid for c in "\\n\\r\\x00"): lines.append("id: " + eid)
        if isinstance(ev.get("retry"), int) and ev["retry"] >= 0: lines.append("retry: " + str(ev["retry"]))
        if ev.get("data") is not None: lines += ["data: " + l.strip() for l in norm(ev["data"])]
        if lines: out += "\\n".join(lines) + "\\n\\n"
    return out
''',
    ],
    guide=dict(
        prereqs="The SSE format: fields, comments and the blank line that ends an event (lesson *WebSockets, "
                "streaming and Server-Sent Events*).",
        intuition="SSE is a line protocol, so a line break inside a value would end the field early and "
                  "corrupt the stream. Every multi-line value therefore becomes several lines with the same "
                  "field name, which the client joins back together. Everything else is careful string "
                  "building: the right order, nothing stripped, and a blank line after each event.",
        hints=["Write a helper that normalises `\\r\\n` and `\\r` to `\\n` and splits.",
               "Collect an event's lines in a list, then `'\\n'.join(lines) + '\\n\\n'`.",
               "Check for an empty `lines` list before adding anything for that event.",
               "Leave values untouched: LLM tokens often start with a space."],
        brute_force="Writing `'data: ' + value` directly works until a value contains a newline, at which "
                    "point the client sees a truncated field followed by garbage.",
        approach="For each event build lines in order: comment lines, `event:`, `id:` (only if safe), "
                 "`retry:` (only if a non-negative int), data lines. Skip events with no lines.\n\nDry run "
                 "of `{\"data\": \"a\\r\\nb\\rc\"}`: normalising gives `a\\nb\\nc` → three `data:` lines → "
                 "`data: a\\ndata: b\\ndata: c\\n\\n`.",
        complexity="O(total length of the input).",
        pitfalls="- Forgetting the final blank line, so the client never dispatches the event.\n- Stripping "
                 "values.\n- Writing an id containing a newline, which would inject a fake field.\n- Treating "
                 "`retry=0` as unset (0 is falsy but valid).",
        follow_up="FastAPI's `ServerSentEvent` does this for you, JSON-encoding `data` unless you pass "
                  "`raw_data`. Keep-alive pings are comment-only events, which is why an event with only a "
                  "comment must still be written.",
    ),
),
dict(
    id="fastapi-chat-rooms",
    title="Chat Rooms with Bounded Per-Client Queues",
    difficulty="Medium",
    pattern="WebSockets",
    kind="class",
    entry="ChatHub",
    description=r"""
A WebSocket chat server keeps track of who is connected, which rooms each person is in, and a queue
of messages waiting to be sent to each connection. Each queue is **bounded**: if a slow client's queue
is full, new messages for that client are dropped (and counted) instead of letting memory grow without
limit. Implement the bookkeeping.

`ChatHub(max_queue)`:

- `connect(user)` → `True`, or `False` if the user is already connected.
- `join(user, room)` → `True`; `False` if the user is not connected or is already in the room.
- `leave(user, room)` → `True`; `False` if the user is not connected or not in the room.
- `send(user, room, text)` → `-1` if the user is not connected or not in the room. Otherwise the
  message `room + "|" + user + ": " + text` is offered to every **other** member of the room: appended
  to their queue if it holds fewer than `max_queue` messages, otherwise dropped and that member's
  dropped count increases by one. Return the number of members whose queue accepted it.
- `receive(user)` → the list of queued messages for the user, oldest first, emptying the queue; `[]`
  for an unknown user.
- `disconnect(user)` → removes the user from every room and discards their queue and dropped count;
  returns the number of rooms they were in, or `-1` if they were not connected.
- `dropped(user)` → how many messages have been dropped for the user since they connected (`0` for an
  unknown user).

**Example:** `["ChatHub","connect","connect","join","join","send","receive","receive"]`,
`[[10],["ann"],["bob"],["ann","lobby"],["bob","lobby"],["ann","lobby","hi"],["bob"],["bob"]]` →
`[None,True,True,True,True,1,["lobby|ann: hi"],[]]`
""",
    starter='''class ChatHub:
    def __init__(self, max_queue: int):
        pass

    def connect(self, user: str) -> bool:
        pass

    def join(self, user: str, room: str) -> bool:
        pass

    def leave(self, user: str, room: str) -> bool:
        pass

    def send(self, user: str, room: str, text: str) -> int:
        pass

    def receive(self, user: str) -> list:
        pass

    def disconnect(self, user: str) -> int:
        pass

    def dropped(self, user: str) -> int:
        pass
''',
    solution='''class ChatHub:
    def __init__(self, max_queue):
        self.max_queue = max_queue
        self.queues = {}       # user -> list of pending messages
        self.rooms_of = {}     # user -> set of rooms
        self.members = {}      # room -> set of users
        self.drops = {}        # user -> dropped count

    def connect(self, user):
        if user in self.queues:
            return False
        self.queues[user], self.rooms_of[user], self.drops[user] = [], set(), 0
        return True

    def join(self, user, room):
        if user not in self.queues or room in self.rooms_of[user]:
            return False
        self.rooms_of[user].add(room)
        self.members.setdefault(room, set()).add(user)
        return True

    def leave(self, user, room):
        if user not in self.queues or room not in self.rooms_of[user]:
            return False
        self.rooms_of[user].discard(room)
        self.members[room].discard(user)
        return True

    def send(self, user, room, text):
        if user not in self.queues or room not in self.rooms_of[user]:
            return -1
        message = f"{room}|{user}: {text}"
        delivered = 0
        for other in self.members[room]:
            if other == user:
                continue
            queue = self.queues[other]
            if len(queue) < self.max_queue:
                queue.append(message)
                delivered += 1
            else:
                self.drops[other] += 1
        return delivered

    def receive(self, user):
        if user not in self.queues:
            return []
        pending, self.queues[user] = self.queues[user], []
        return pending

    def disconnect(self, user):
        if user not in self.queues:
            return -1
        rooms = self.rooms_of.pop(user)
        for room in rooms:
            self.members[room].discard(user)
        del self.queues[user], self.drops[user]
        return len(rooms)

    def dropped(self, user):
        return self.drops.get(user, 0)
''',
    tests=[
        [["ChatHub", "connect", "connect", "join", "join", "send", "receive", "receive"],
         [[10], ["ann"], ["bob"], ["ann", "lobby"], ["bob", "lobby"], ["ann", "lobby", "hi"], ["bob"], ["bob"]]],
        [["ChatHub", "connect", "connect", "connect", "join", "join", "join", "send", "receive", "receive", "receive"],
         [[10], ["ann"], ["bob"], ["cy"], ["ann", "r"], ["bob", "r"], ["cy", "r"], ["ann", "r", "hello"], ["ann"], ["bob"], ["cy"]]],
        [["ChatHub", "connect", "send", "join", "join", "send"],
         [[5], ["ann"], ["ann", "lobby", "x"], ["ann", "lobby"], ["ann", "lobby"], ["ann", "lobby", "alone"]]],
        [["ChatHub", "join", "leave", "receive", "disconnect", "dropped", "send"],
         [[5], ["ghost", "r"], ["ghost", "r"], ["ghost"], ["ghost"], ["ghost"], ["ghost", "r", "boo"]]],
        [["ChatHub", "connect", "connect", "join", "join", "send", "send", "send", "dropped", "receive", "send", "receive", "dropped"],
         [[2], ["a"], ["b"], ["a", "r"], ["b", "r"], ["a", "r", "m1"], ["a", "r", "m2"], ["a", "r", "m3"], ["b"], ["b"], ["a", "r", "m4"], ["b"], ["b"]]],
        [["ChatHub", "connect", "connect", "connect", "join", "join", "join", "join", "send", "send", "receive", "receive", "receive"],
         [[10], ["ann"], ["bob"], ["cy"], ["ann", "r1"], ["ann", "r2"], ["bob", "r1"], ["cy", "r2"],
          ["ann", "r1", "to r1"], ["ann", "r2", "to r2"], ["bob"], ["cy"], ["ann"]]],
        [["ChatHub", "connect", "connect", "join", "join", "leave", "leave", "send", "receive", "send"],
         [[10], ["ann"], ["bob"], ["ann", "r"], ["bob", "r"], ["bob", "r"], ["bob", "r"], ["ann", "r", "anyone?"], ["bob"], ["bob", "r", "late"]]],
        [["ChatHub", "connect", "connect", "join", "join", "join", "send", "send", "dropped", "disconnect", "send", "connect", "dropped", "receive"],
         [[1], ["ann"], ["bob"], ["ann", "r1"], ["bob", "r1"], ["bob", "r2"], ["ann", "r1", "one"], ["ann", "r1", "two"], ["bob"],
          ["bob"], ["ann", "r1", "three"], ["bob"], ["bob"], ["bob"]]],
        [["ChatHub", "connect", "connect", "disconnect", "connect"], [[3], ["ann"], ["ann"], ["ann"], ["ann"]]],
        [["ChatHub", "connect", "connect", "connect", "join", "join", "join", "send", "send", "send", "send", "receive"],
         [[10], ["a"], ["b"], ["c"], ["a", "r"], ["b", "r"], ["c", "r"], ["a", "r", "1"], ["b", "r", "2"], ["a", "r", "3"], ["c", "r", "4"], ["c"]]],
        [["ChatHub", "connect", "connect", "join", "join", "send", "send", "dropped", "receive"],
         [[0], ["a"], ["b"], ["a", "r"], ["b", "r"], ["a", "r", "x"], ["a", "r", "y"], ["b"], ["b"]]],
        [["ChatHub"] + ["connect"] * 20 + ["join"] * 20 + ["send"] * 5 + ["dropped", "receive"],
         [[3]] + [[f"u{i}"] for i in range(20)] + [[f"u{i}", "big"] for i in range(20)]
         + [["u0", "big", f"m{k}"] for k in range(5)] + [["u7"], ["u7"]]],
    ],
    examples=1,
    wrong_solutions=[
        '''class ChatHub:
    def __init__(self, max_queue):
        self.m, self.q, self.rooms, self.members, self.d = max_queue, {}, {}, {}, {}
    def connect(self, u):
        if u in self.q: return False
        self.q[u], self.rooms[u], self.d[u] = [], set(), 0; return True
    def join(self, u, r):
        if u not in self.q or r in self.rooms[u]: return False
        self.rooms[u].add(r); self.members.setdefault(r, set()).add(u); return True
    def leave(self, u, r):
        if u not in self.q or r not in self.rooms[u]: return False
        self.rooms[u].discard(r); self.members[r].discard(u); return True
    def send(self, u, r, t):
        if u not in self.q or r not in self.rooms[u]: return -1
        n = 0
        for o in self.members[r]:
            if len(self.q[o]) < self.m: self.q[o].append(f"{r}|{u}: {t}"); n += 1
            else: self.d[o] += 1
        return n
    def receive(self, u):
        if u not in self.q: return []
        out, self.q[u] = self.q[u], []; return out
    def disconnect(self, u):
        if u not in self.q: return -1
        rs = self.rooms.pop(u)
        for r in rs: self.members[r].discard(u)
        del self.q[u], self.d[u]; return len(rs)
    def dropped(self, u): return self.d.get(u, 0)
''',
        '''class ChatHub:
    def __init__(self, max_queue):
        self.m, self.q, self.rooms, self.members, self.d = max_queue, {}, {}, {}, {}
    def connect(self, u):
        if u in self.q: return False
        self.q[u], self.rooms[u], self.d[u] = [], set(), 0; return True
    def join(self, u, r):
        if u not in self.q or r in self.rooms[u]: return False
        self.rooms[u].add(r); self.members.setdefault(r, set()).add(u); return True
    def leave(self, u, r):
        if u not in self.q or r not in self.rooms[u]: return False
        self.rooms[u].discard(r); self.members[r].discard(u); return True
    def send(self, u, r, t):
        if u not in self.q or r not in self.rooms[u]: return -1
        n = 0
        for o in self.members[r]:
            if o == u: continue
            if len(self.q[o]) >= self.m:
                if self.q[o]: self.q[o].pop(0)
                self.d[o] += 1
            if self.m > 0: self.q[o].append(f"{r}|{u}: {t}"); n += 1
        return n
    def receive(self, u):
        if u not in self.q: return []
        out, self.q[u] = self.q[u], []; return out
    def disconnect(self, u):
        if u not in self.q: return -1
        rs = self.rooms.pop(u)
        for r in rs: self.members[r].discard(u)
        del self.q[u], self.d[u]; return len(rs)
    def dropped(self, u): return self.d.get(u, 0)
''',
        '''class ChatHub:
    def __init__(self, max_queue):
        self.m, self.q, self.rooms, self.members, self.d = max_queue, {}, {}, {}, {}
    def connect(self, u):
        if u in self.q: return False
        self.q[u], self.rooms[u], self.d[u] = [], set(), 0; return True
    def join(self, u, r):
        if u not in self.q or r in self.rooms[u]: return False
        self.rooms[u].add(r); self.members.setdefault(r, set()).add(u); return True
    def leave(self, u, r):
        if u not in self.q or r not in self.rooms[u]: return False
        self.rooms[u].discard(r); self.members[r].discard(u); return True
    def send(self, u, r, t):
        if u not in self.q or r not in self.rooms[u]: return -1
        n = 0
        for o in self.members[r]:
            if o == u: continue
            if o not in self.q: n += 1; continue
            if len(self.q[o]) < self.m: self.q[o].append(f"{r}|{u}: {t}"); n += 1
            else: self.d[o] += 1
        return n
    def receive(self, u):
        if u not in self.q: return []
        out, self.q[u] = self.q[u], []; return out
    def disconnect(self, u):
        if u not in self.q: return -1
        n = len(self.rooms.pop(u)); del self.q[u], self.d[u]; return n
    def dropped(self, u): return self.d.get(u, 0)
''',
    ],
    guide=dict(
        prereqs="WebSocket broadcasting, `ConnectionManager` and backpressure (lesson *WebSockets, streaming "
                "and Server-Sent Events*); dicts of sets.",
        intuition="Three mappings carry all the state: which rooms each user is in, which users each room "
                  "holds, and each user's pending messages. Keeping the first two in sync is the classic "
                  "source of bugs: forget one side on disconnect and messages get 'delivered' to a ghost. "
                  "The bounded queue is backpressure: one slow phone on a bad network must not make the "
                  "server's memory grow for ever.",
        hints=["Keep both `rooms_of[user]` and `members[room]`, and update both on join, leave and disconnect.",
               "Skip the sender when broadcasting.",
               "The drop policy here is 'refuse the newest': a full queue keeps its old messages.",
               "On disconnect also delete the dropped count, so a reconnect starts from zero."],
        brute_force="Scanning every user's room set for each `send` works but costs O(users) per message; "
                    "the reverse index `members[room]` makes it O(room size).",
        approach="`connect` creates the three per-user records. `join`/`leave` update both indexes. `send` "
                 "checks membership, then offers the message to every other member, counting acceptances. "
                 "`receive` swaps the queue for an empty one. `disconnect` removes the user from each room's "
                 "member set before deleting their records.\n\nDry run of test 5 (`max_queue=2`): m1 and m2 "
                 "fill b's queue → 1, 1; m3 is dropped → 0, dropped(b) = 1; receive gives [m1, m2]; m4 now "
                 "fits → 1.",
        complexity="O(room size) per `send`, O(rooms of user) per `disconnect`, O(1) otherwise.",
        pitfalls="- Delivering to the sender.\n- Leaving a disconnected user in `members[room]`.\n"
                 "- Evicting old messages instead of refusing new ones (a different policy from the one asked).\n"
                 "- `max_queue = 0` means every message is dropped.",
        follow_up="With several worker processes this state must be split: rooms and fan-out go through a "
                  "broker (Redis Pub/Sub), and each worker keeps only its own connections' queues. Real "
                  "servers often disconnect a client whose queue stays full instead of silently dropping.",
    ),
),
dict(
    id="fastapi-circuit-breaker",
    title="Circuit Breaker with an Injected Clock",
    difficulty="Medium",
    pattern="Reliability",
    kind="class",
    entry="CircuitBreaker",
    description=r"""
A circuit breaker protects a service from a failing dependency. After `threshold` **consecutive**
failures it *opens* and rejects calls immediately, without contacting the dependency. Once `cooldown`
seconds have passed since it opened, it is *half-open*: the next call is let through as a trial. A
successful trial closes the breaker; a failed one opens it again, starting a new cooldown. Times are
passed in, so behaviour is deterministic.

`CircuitBreaker(threshold, cooldown)`:

- `state(now)` → `"closed"`, `"open"` (opened less than `cooldown` seconds ago) or `"half-open"`
  (opened at least `cooldown` seconds ago and not yet tried). It changes nothing.
- `call(now, ok)` → what happens to a call at time `now`, where `ok` says whether the dependency would
  succeed:
  - state `"open"` → return `"rejected"` (the dependency is not called; nothing changes, the cooldown is
    not extended);
  - otherwise the dependency is called. If `ok`: reset the consecutive-failure count to 0, close the
    breaker, return `"success"`. If not `ok`: in `"half-open"` re-open at `now`; in `"closed"` add one
    to the count and open at `now` if it reaches `threshold`; return `"failure"`.

**Example:** `["CircuitBreaker","call","call","call","state","call","state","call","state"]`,
`[[3,10],[0,False],[1,False],[2,False],[2],[5,True],[12],[12,True],[12]]` →
`[None,"failure","failure","failure","open","rejected","half-open","success","closed"]`
""",
    starter='''class CircuitBreaker:
    def __init__(self, threshold: int, cooldown: int):
        pass

    def state(self, now: int) -> str:
        pass

    def call(self, now: int, ok: bool) -> str:
        pass
''',
    solution='''class CircuitBreaker:
    def __init__(self, threshold, cooldown):
        self.threshold, self.cooldown = threshold, cooldown
        self.failures = 0
        self.opened_at = None              # None means closed

    def state(self, now):
        if self.opened_at is None:
            return "closed"
        return "half-open" if now - self.opened_at >= self.cooldown else "open"

    def call(self, now, ok):
        current = self.state(now)
        if current == "open":
            return "rejected"
        if ok:
            self.failures, self.opened_at = 0, None
            return "success"
        if current == "half-open":
            self.opened_at = now
        else:
            self.failures += 1
            if self.failures >= self.threshold:
                self.opened_at = now
        return "failure"
''',
    tests=[
        [["CircuitBreaker", "call", "call", "call", "state", "call", "state", "call", "state"],
         [[3, 10], [0, False], [1, False], [2, False], [2], [5, True], [12], [12, True], [12]]],
        [["CircuitBreaker", "call", "call", "call", "call", "call", "state", "call", "state"],
         [[3, 10], [0, False], [1, False], [2, True], [3, False], [4, False], [4], [5, False], [5]]],
        [["CircuitBreaker", "call", "call", "call", "call", "state", "state", "call", "call"],
         [[3, 10], [0, False], [1, False], [2, False], [12, False], [15], [22], [21, True], [22, True]]],
        [["CircuitBreaker", "call", "state", "state", "state"], [[1, 10], [0, False], [9], [10], [11]]],
        [["CircuitBreaker", "call", "call", "call", "call", "state", "call"],
         [[1, 10], [0, False], [3, True], [5, True], [9, True], [10], [10, True]]],
        [["CircuitBreaker", "call", "state", "call", "state", "call", "call"],
         [[2, 0], [0, False], [0], [0, False], [0], [0, False], [0, True]]],
        [["CircuitBreaker", "call", "call", "call", "state"], [[2, 5], [0, True], [1, True], [2, True], [2]]],
        [["CircuitBreaker", "state", "state", "call", "state"], [[3, 10], [0], [100], [100, False], [100]]],
        [["CircuitBreaker", "call", "call", "call", "call", "call", "call", "state"],
         [[2, 4], [0, False], [1, False], [4, False], [8, False], [12, True], [13, False], [13]]],
        [["CircuitBreaker"] + ["call"] * 40 + ["state"],
         [[3, 5]] + [[t, (t % 7) in (0, 1)] for t in range(40)] + [[40]]],
        [["CircuitBreaker", "call", "call", "call", "call", "call", "call"],
         [[3, 10], [0, False], [1, False], [2, False], [9, True], [10, False], [19, True]]],
    ],
    examples=1,
    wrong_solutions=[
        '''class CircuitBreaker:
    def __init__(self, threshold, cooldown):
        self.t, self.c, self.f, self.at = threshold, cooldown, 0, None
    def state(self, now):
        if self.at is None: return "closed"
        return "half-open" if now - self.at >= self.c else "open"
    def call(self, now, ok):
        s = self.state(now)
        if s == "open": return "rejected"
        if ok:
            self.at = None; return "success"
        if s == "half-open": self.at = now
        else:
            self.f += 1
            if self.f >= self.t: self.at = now
        return "failure"
''',
        '''class CircuitBreaker:
    def __init__(self, threshold, cooldown):
        self.t, self.c, self.f, self.at = threshold, cooldown, 0, None
    def state(self, now):
        if self.at is None: return "closed"
        return "half-open" if now - self.at >= self.c else "open"
    def call(self, now, ok):
        s = self.state(now)
        if s == "open": return "rejected"
        if s == "half-open": self.at, self.f = None, 0
        if ok:
            self.f, self.at = 0, None; return "success"
        self.f += 1
        if self.f >= self.t: self.at = now
        return "failure"
''',
        '''class CircuitBreaker:
    def __init__(self, threshold, cooldown):
        self.t, self.c, self.f, self.at = threshold, cooldown, 0, None
    def state(self, now):
        if self.at is None: return "closed"
        return "half-open" if now - self.at > self.c else "open"
    def call(self, now, ok):
        s = self.state(now)
        if s == "open": return "rejected"
        if ok:
            self.f, self.at = 0, None; return "success"
        if s == "half-open": self.at = now
        else:
            self.f += 1
            if self.f >= self.t: self.at = now
        return "failure"
''',
    ],
    guide=dict(
        prereqs="Resilience patterns and the circuit-breaker demo (lesson *Health checks, logging and "
                "observability*); simple state machines.",
        intuition="The breaker is a three-state machine. *Closed*: count consecutive failures. *Open*: "
                  "refuse everything until the cooldown has passed, which saves your threads and gives the "
                  "dependency room to recover. *Half-open*: risk exactly one call to find out. Storing only "
                  "`opened_at` lets you *derive* open versus half-open from the clock instead of needing a "
                  "timer to flip the state.",
        hints=["Keep two fields: the consecutive-failure count and `opened_at` (`None` when closed).",
               "`state(now)` is a pure function of those fields and `now`.",
               "A failure in half-open re-opens immediately, whatever the count.",
               "Rejected calls must not touch `opened_at`."],
        brute_force="Not applicable; this is about getting every transition and boundary right.",
        approach="`state`: closed if `opened_at` is None; half-open if `now - opened_at >= cooldown`; else "
                 "open. `call`: if open → rejected. If ok → reset and close. Else if half-open → "
                 "`opened_at = now`; else count, and open at the threshold.\n\nDry run of test 3: three "
                 "failures open it at t=2. At t=12 (10 later) it is half-open; the trial fails → re-opened "
                 "at 12. t=15 open, t=22 half-open; a call at t=21 is still rejected (9 < 10); at t=22 it "
                 "succeeds and closes.",
        complexity="O(1) per operation.",
        pitfalls="- Not resetting the count on success (it must count *consecutive* failures).\n- Treating "
                 "the end of the cooldown as fully closed, so one failed trial does not re-open it.\n"
                 "- `>` instead of `>=` at the cooldown boundary.\n- Extending the cooldown on rejected calls.",
        follow_up="Production breakers (for example `pybreaker`, or Envoy and Istio outlier detection) "
                  "often count failures in a rolling time window or by error rate, allow several trial "
                  "calls in half-open, and treat timeouts and 5xx responses as failures but not 4xx.",
    ),
),
dict(
    id="fastapi-latency-histogram",
    title="Latency Histogram and Quantile Estimate",
    difficulty="Medium",
    pattern="Observability",
    entry="histogramQuantile",
    compare="float",
    description=r"""
Prometheus does not store every request duration. A histogram stores only **counts per bucket**, and
percentiles are *estimated* from those counts later. Implement both halves.

`histogramQuantile(bounds, observations, q)`:

- `bounds` are the bucket upper limits, strictly increasing and all positive; an implicit last bucket
  `+Inf` catches everything larger. An observation `x` belongs to the first bucket with
  `x <= bound` ("le" means *less than or equal*).
- Build the **cumulative** counts, one per bucket including `+Inf`: entry `i` is the number of
  observations `<= bounds[i]`; the last entry is the total.
- Estimate the `q` quantile (`0 < q <= 1`) the way Prometheus's `histogram_quantile` does:
  1. `rank = q * total`.
  2. Find the first bucket whose cumulative count is `>= rank`.
  3. If that is the `+Inf` bucket, the estimate is the largest finite bound, `bounds[-1]`.
  4. Otherwise interpolate linearly inside the bucket: with `lower` = the previous bucket's bound
     (`0` for the first bucket), `upper` = this bucket's bound, `prev` = the previous cumulative count
     (`0` for the first) and `n` = observations in this bucket,
     `estimate = lower + (upper - lower) * (rank - prev) / n`.
- Return `[cumulative_counts, estimate]`. There is at least one observation; observations are `>= 0`.

**Example:** `histogramQuantile([0.05, 0.1, 0.25, 0.5, 1.0], [0.03, 0.04, 0.08, 0.3, 0.04, 2.0], 0.75)` →
`[[3, 4, 4, 5, 5, 6], 0.375]`: rank 4.5 falls in the `0.5` bucket (cumulative 5), which holds 1
observation after the 4 below it, so the estimate is `0.25 + 0.25 * 0.5`.
""",
    starter='''def histogramQuantile(bounds: list[float], observations: list[float], q: float) -> list:
    pass
''',
    solution='''import bisect

def histogramQuantile(bounds, observations, q):
    counts = [0] * (len(bounds) + 1)
    for x in observations:
        counts[bisect.bisect_left(bounds, x)] += 1
    cumulative, running = [], 0
    for c in counts:
        running += c
        cumulative.append(running)
    rank = q * cumulative[-1]
    b = next(i for i, c in enumerate(cumulative) if c >= rank)
    if b == len(bounds):
        return [cumulative, bounds[-1]]
    lower = bounds[b - 1] if b > 0 else 0.0
    prev = cumulative[b - 1] if b > 0 else 0
    n = cumulative[b] - prev
    return [cumulative, lower + (bounds[b] - lower) * (rank - prev) / n]
''',
    tests=[
        [[0.05, 0.1, 0.25, 0.5, 1.0], [0.03, 0.04, 0.08, 0.3, 0.04, 2.0], 0.75],
        [[0.05, 0.1, 0.25, 0.5, 1.0], [0.03, 0.04, 0.08, 0.3, 0.04, 2.0], 0.5],
        [[0.05, 0.1, 0.25, 0.5, 1.0], [0.03, 0.04, 0.08, 0.3, 0.04, 2.0], 0.9],
        [[0.1, 1.0], [0.1], 1.0],
        [[1.0], [0.2, 0.4, 0.6, 0.8], 0.5],
        [[1.0, 2.0], [5.0, 6.0], 0.5],
        [[1.0, 2.0, 4.0], [0.5, 1.5, 3.0], 1.0],
        [[1.0, 2.0, 3.0, 4.0], [3.5, 3.5, 3.5, 3.5], 0.5],
        [[1.0, 2.0], [0.5, 0.5, 1.5, 1.5], 0.5],
        [[0.5, 1.0], [0.0, 0.0, 0.7], 0.5],
        [[0.1 * k for k in range(1, 11)], [i / 1000 for i in range(1000)], 0.95],
        [[0.1 * k for k in range(1, 11)], [i / 1000 for i in range(1000)], 0.01],
        [[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5], [0.04] * 980 + [1.8] * 20, 0.99],
    ],
    examples=2,
    wrong_solutions=[
        '''import bisect
def histogramQuantile(bounds, observations, q):
    counts = [0] * (len(bounds) + 1)
    for x in observations:
        counts[bisect.bisect_left(bounds, x)] += 1
    cum, r = [], 0
    for c in counts:
        r += c; cum.append(r)
    rank = q * cum[-1]
    b = next(i for i, c in enumerate(cum) if c >= rank)
    return [cum, bounds[min(b, len(bounds) - 1)]]
''',
        '''import bisect
def histogramQuantile(bounds, observations, q):
    counts = [0] * (len(bounds) + 1)
    for x in observations:
        counts[bisect.bisect_right(bounds, x)] += 1
    cum, r = [], 0
    for c in counts:
        r += c; cum.append(r)
    rank = q * cum[-1]
    b = next(i for i, c in enumerate(cum) if c >= rank)
    if b == len(bounds): return [cum, bounds[-1]]
    lo = bounds[b - 1] if b else 0.0
    prev = cum[b - 1] if b else 0
    return [cum, lo + (bounds[b] - lo) * (rank - prev) / (cum[b] - prev)]
''',
        '''import bisect
def histogramQuantile(bounds, observations, q):
    counts = [0] * (len(bounds) + 1)
    for x in observations:
        counts[bisect.bisect_left(bounds, x)] += 1
    rank = q * len(observations)
    run = 0
    for b, c in enumerate(counts):
        if run + c >= rank:
            if b == len(bounds): return [counts, bounds[-1]]
            lo = bounds[b - 1] if b else 0.0
            return [counts, lo + (bounds[b] - lo) * (rank - run) / c]
        run += c
''',
    ],
    guide=dict(
        prereqs="Metrics types, buckets and percentiles (lesson *Health checks, logging and observability*); "
                "`bisect`.",
        intuition="A histogram trades precision for size: whatever the traffic, it stores a dozen numbers. "
                  "To estimate the p95 you find the bucket in which the 95th-percent observation must lie, "
                  "then assume observations are spread evenly inside it. The estimate can only be as good "
                  "as the bucket boundaries, which is why bounds are chosen around your latency targets.",
        hints=["`bisect.bisect_left(bounds, x)` gives the first index with `bounds[i] >= x`, the `le` bucket.",
               "Turn per-bucket counts into running totals.",
               "Find the first running total `>= rank`; handle the `+Inf` bucket separately.",
               "The count *inside* the chosen bucket is `cumulative[b] - cumulative[b-1]`."],
        brute_force="Sorting the raw observations gives the exact percentile, but a real metrics system "
                    "never has the raw observations, only the bucket counts.",
        approach="1. Count observations per bucket with `bisect_left`.\n2. Accumulate.\n3. Locate the bucket "
                 "for `rank = q · total` and interpolate.\n\nDry run of the example with q = 0.5: rank 3; "
                 "the first cumulative count >= 3 is bucket 0 (count 3), so the estimate is "
                 "`0 + 0.05 · (3 − 0) / 3 = 0.05`. With q = 0.9, rank 5.4 exceeds every finite bucket "
                 "(5), so the answer is the largest finite bound, 1.0.",
        complexity="O(n log b) to bucket n observations into b buckets, then O(b).",
        pitfalls="- `bisect_right` puts a value equal to a bound in the wrong bucket.\n- Returning per-bucket "
                 "counts instead of cumulative ones.\n- Returning the bucket's upper bound without "
                 "interpolating.\n- Dividing by the cumulative count instead of the count inside the bucket.",
        follow_up="In PromQL this is `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))`. "
                  "Summing buckets across replicas is valid, while averaging per-replica percentiles is "
                  "not, which is the main reason histograms are preferred over client-side summaries.",
    ),
),
dict(
    id="fastapi-token-budget",
    title="LLM Token Budget with Reservations",
    difficulty="Medium",
    pattern="ML Serving",
    kind="class",
    entry="TokenBudget",
    description=r"""
An LLM endpoint must refuse a request **before** streaming starts if the user cannot afford it, but
the real cost is only known at the end. The usual answer: reserve the worst case (prompt tokens plus
`max_tokens`) up front, then refund the unused part when generation finishes. Implement a per-user
budget over **fixed windows**: window number `now // window`, so with `window = 60` the times 0 to 59
are window 0, 60 to 119 window 1, and so on.

`TokenBudget(limit, window)`:

- `reserve(user, request_id, prompt_tokens, max_tokens, now)`:
  - `"duplicate"` if `request_id` is already reserved and not yet settled (ids are global);
  - otherwise `cost = prompt_tokens + max_tokens`; if the user's usage in the current window plus
    `cost` exceeds `limit`, return `"429"` (nothing is reserved);
  - otherwise add `cost` to the user's usage for the current window, remember the reservation, and
    return `"ok"`.
- `settle(request_id, completion_tokens, now)`: `-1` if the id is not reserved. Otherwise the actual
  cost is `prompt_tokens + min(completion_tokens, max_tokens)`. If `now` is still in the window where
  the reservation was made, refund `reserved - actual` to the user's usage; if the window has changed,
  no refund is applied (the old window's usage has been discarded anyway). Forget the reservation and
  return the actual cost.
- `remaining(user, now)`: `limit` minus the user's usage in the window containing `now`.

Usage from an earlier window never counts in a later one. All times and counts are non-negative
integers.

**Example:** `["TokenBudget","reserve","remaining","settle","remaining","reserve","reserve","remaining"]`,
`[[1000,60],["ann","r1",100,400,0],["ann",1],["r1",150,5],["ann",6],["ann","r2",200,600,10],["ann","r3",200,500,10],["ann",11]]`
→ `[None,"ok",500,250,750,"429","ok",50]`
""",
    starter='''class TokenBudget:
    def __init__(self, limit: int, window: int):
        pass

    def reserve(self, user: str, request_id: str, prompt_tokens: int, max_tokens: int, now: int) -> str:
        pass

    def settle(self, request_id: str, completion_tokens: int, now: int) -> int:
        pass

    def remaining(self, user: str, now: int) -> int:
        pass
''',
    solution='''class TokenBudget:
    def __init__(self, limit, window):
        self.limit, self.window = limit, window
        self.usage = {}      # user -> [window_number, tokens]
        self.pending = {}    # request_id -> (user, window_number, prompt_tokens, max_tokens)

    def _current(self, user, now):
        w = now // self.window
        rec = self.usage.get(user)
        if rec is None or rec[0] != w:
            rec = [w, 0]
            self.usage[user] = rec
        return rec

    def reserve(self, user, request_id, prompt_tokens, max_tokens, now):
        if request_id in self.pending:
            return "duplicate"
        cost = prompt_tokens + max_tokens
        rec = self._current(user, now)
        if rec[1] + cost > self.limit:
            return "429"
        rec[1] += cost
        self.pending[request_id] = (user, rec[0], prompt_tokens, max_tokens)
        return "ok"

    def settle(self, request_id, completion_tokens, now):
        if request_id not in self.pending:
            return -1
        user, w, prompt, max_tokens = self.pending.pop(request_id)
        actual = prompt + min(completion_tokens, max_tokens)
        rec = self._current(user, now)
        if rec[0] == w:
            rec[1] -= (prompt + max_tokens) - actual
        return actual

    def remaining(self, user, now):
        return self.limit - self._current(user, now)[1]
''',
    tests=[
        [["TokenBudget", "reserve", "remaining", "settle", "remaining", "reserve", "reserve", "remaining"],
         [[1000, 60], ["ann", "r1", 100, 400, 0], ["ann", 1], ["r1", 150, 5], ["ann", 6], ["ann", "r2", 200, 600, 10], ["ann", "r3", 200, 500, 10], ["ann", 11]]],
        [["TokenBudget", "reserve", "remaining", "remaining"], [[1000, 60], ["ann", "r1", 500, 400, 10], ["ann", 59], ["ann", 60]]],
        [["TokenBudget", "reserve", "settle", "remaining"], [[1000, 60], ["ann", "r1", 100, 500, 50], ["r1", 10, 70], ["ann", 70]]],
        [["TokenBudget", "reserve", "settle", "remaining"], [[1000, 60], ["ann", "r1", 10, 50, 0], ["r1", 80, 1], ["ann", 2]]],
        [["TokenBudget", "settle", "reserve", "settle", "settle"], [[1000, 60], ["ghost", 5, 0], ["ann", "r1", 1, 1, 0], ["r1", 1, 0], ["r1", 1, 0]]],
        [["TokenBudget", "reserve", "reserve", "reserve", "settle", "reserve"],
         [[1000, 60], ["ann", "r1", 10, 10, 0], ["ann", "r1", 10, 10, 1], ["bob", "r1", 10, 10, 1], ["r1", 5, 2], ["bob", "r1", 10, 10, 3]]],
        [["TokenBudget", "reserve", "reserve", "reserve", "remaining", "remaining"],
         [[100, 60], ["ann", "a1", 50, 50, 0], ["ann", "a2", 1, 0, 0], ["bob", "b1", 60, 40, 0], ["ann", 0], ["bob", 0]]],
        [["TokenBudget", "reserve", "reserve", "reserve"], [[100, 10], ["ann", "x", 30, 30, 0], ["ann", "y", 20, 20, 0], ["ann", "z", 0, 1, 9]]],
        [["TokenBudget", "reserve", "remaining", "reserve", "remaining"], [[100, 60], ["ann", "big", 80, 30, 0], ["ann", 0], ["ann", "ok", 80, 20, 0], ["ann", 0]]],
        [["TokenBudget", "remaining", "remaining"], [[500, 60], ["nobody", 0], ["nobody", 1000]]],
        [["TokenBudget", "reserve", "settle", "remaining"], [[1000, 60], ["ann", "r1", 100, 300, 0], ["r1", 0, 30], ["ann", 31]]],
        [["TokenBudget", "reserve", "reserve", "settle", "settle", "remaining", "reserve", "remaining"],
         [[1000, 100], ["ann", "a", 100, 200, 0], ["ann", "b", 100, 200, 50], ["a", 50, 99], ["b", 999, 100], ["ann", 100], ["ann", "c", 900, 100, 150], ["ann", 199]]],
        [["TokenBudget"] + ["reserve"] * 30 + ["remaining"],
         [[1000, 60]] + [["ann", f"q{i}", 20, 20, i] for i in range(30)] + [["ann", 59]]],
    ],
    examples=1,
    wrong_solutions=[
        '''class TokenBudget:
    def __init__(self, limit, window):
        self.limit, self.window, self.usage, self.pending = limit, window, {}, {}
    def _cur(self, u, now):
        w = now // self.window
        r = self.usage.get(u)
        if r is None or r[0] != w:
            r = [w, 0]; self.usage[u] = r
        return r
    def reserve(self, u, rid, p, m, now):
        if rid in self.pending: return "duplicate"
        r = self._cur(u, now)
        if r[1] + p + m > self.limit: return "429"
        r[1] += p + m; self.pending[rid] = (u, r[0], p, m); return "ok"
    def settle(self, rid, c, now):
        if rid not in self.pending: return -1
        u, w, p, m = self.pending.pop(rid)
        return p + min(c, m)
    def remaining(self, u, now):
        return self.limit - self._cur(u, now)[1]
''',
        '''class TokenBudget:
    def __init__(self, limit, window):
        self.limit, self.window, self.usage, self.pending = limit, window, {}, {}
    def _cur(self, u, now):
        w = now // self.window
        r = self.usage.get(u)
        if r is None or r[0] != w:
            r = [w, 0]; self.usage[u] = r
        return r
    def reserve(self, u, rid, p, m, now):
        if rid in self.pending: return "duplicate"
        r = self._cur(u, now)
        if r[1] + p + m > self.limit: return "429"
        r[1] += p + m; self.pending[rid] = (u, r[0], p, m); return "ok"
    def settle(self, rid, c, now):
        if rid not in self.pending: return -1
        u, w, p, m = self.pending.pop(rid)
        actual = p + min(c, m)
        self._cur(u, now)[1] -= (p + m) - actual
        return actual
    def remaining(self, u, now):
        return self.limit - self._cur(u, now)[1]
''',
        '''class TokenBudget:
    def __init__(self, limit, window):
        self.limit, self.window, self.usage, self.pending = limit, window, {}, {}
    def _cur(self, u, now):
        w = now // self.window
        r = self.usage.get(u)
        if r is None or r[0] != w:
            r = [w, 0]; self.usage[u] = r
        return r
    def reserve(self, u, rid, p, m, now):
        if rid in self.pending: return "duplicate"
        r = self._cur(u, now)
        if r[1] + p + m > self.limit: return "429"
        r[1] += p + m; self.pending[rid] = (u, r[0], p, m); return "ok"
    def settle(self, rid, c, now):
        if rid not in self.pending: return -1
        u, w, p, m = self.pending.pop(rid)
        actual = p + c
        r = self._cur(u, now)
        if r[0] == w: r[1] -= (p + m) - actual
        return actual
    def remaining(self, u, now):
        return self.limit - self._cur(u, now)[1]
''',
    ],
    guide=dict(
        prereqs="Token-based rate limiting and validating before the first byte (lesson *Streaming LLM output "
                "and versioned endpoints*); fixed-window limiters (lesson *NoSQL and Redis caching*).",
        intuition="Once a stream has started, the response is already `200`, so the budget check must "
                  "happen first, using the worst case. Reserving `prompt + max_tokens` guarantees a user can "
                  "never overspend; settling afterwards gives back what the model did not use, so honest "
                  "short answers are not punished. The window number is the only clock state you need.",
        hints=["Store each user's usage as `[window_number, tokens]` and reset it when the window number changes.",
               "Remember for each pending request: user, window number, prompt tokens, max tokens.",
               "The model cannot produce more than `max_tokens`, so cap the completion count.",
               "Refund only if the settle happens in the same window as the reserve."],
        brute_force="Charging only after generation lets one user start many expensive streams at once "
                    "and overspend massively; charging `max_tokens` with no refund overcharges everyone.",
        approach="`reserve`: reject duplicates; compute the cost; check against the current window's usage; "
                 "record. `settle`: pop the reservation; compute the actual cost; refund the difference "
                 "if still in the same window.\n\nDry run of the example: r1 reserves 500 (remaining 500); "
                 "settling 150 completion tokens costs 250, refunding 250 (remaining 750); r2 needs 800 > 750 "
                 "→ 429; r3 needs 700 → ok, remaining 50.",
        complexity="O(1) per operation.",
        pitfalls="- Refunding into a new window, which can push `remaining` above `limit`.\n- Forgetting to "
                 "cap `completion_tokens` at `max_tokens`.\n- Letting a rejected (`429`) request consume budget.\n"
                 "- Allowing the same request id to be reserved twice while pending.",
        follow_up="Across several workers the counters live in Redis: `INCRBY` on a key such as "
                  "`budget:{user}:{window}` with an expiry, executed atomically in a Lua script that also "
                  "checks the limit. Daily and per-minute budgets are two such keys checked together.",
    ),
),
]
