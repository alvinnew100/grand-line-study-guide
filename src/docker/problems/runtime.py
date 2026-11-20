PROBLEMS = [
dict(
    id="docker-port-mappings",
    title="Parse Port Mappings and Detect Conflicts",
    difficulty="Medium",
    pattern="Running Containers",
    entry="parsePorts",
    description=r"""
Several containers are about to be started on one host. Write `parsePorts(specs)` where `specs` is the list of all
their `-p` values, and return `[mappings, conflicts]`.

**Parsing.** Each spec has an optional protocol suffix `/tcp` or `/udp` (default `tcp`), and before it one of:

| Form | Meaning |
|---|---|
| `C` | container port `C`, host port chosen at random → host port `0`, host IP `0.0.0.0` |
| `H:C` | host port `H` on IP `0.0.0.0` |
| `IP:H:C` | host port `H` on that IPv4 address |
| `IP::C` | random host port (`0`) on that IP |

`mappings[i]` is `[ip, host_port, container_port, protocol]` for `specs[i]` (ports as integers).

**Conflicts.** Mappings `i < j` conflict when they have the same protocol, the same host port, that host port is not
`0`, and their IPs overlap: the IPs are equal, or at least one of them is `0.0.0.0` (which means every address).
`conflicts` is the list of `[i, j]` pairs sorted in increasing order.

**Example:** `["8080:80", "127.0.0.1:8080:8000", "8080:80/udp", "9000"]`
→ `[[["0.0.0.0", 8080, 80, "tcp"], ["127.0.0.1", 8080, 8000, "tcp"], ["0.0.0.0", 8080, 80, "udp"], ["0.0.0.0", 0, 9000, "tcp"]], [[0, 1]]]`
""",
    starter='''def parsePorts(specs):
    # return [mappings, conflicts]
    pass
''',
    solution='''def parsePorts(specs):
    mappings = []
    for spec in specs:
        proto = "tcp"
        if "/" in spec:
            spec, proto = spec.split("/", 1)
        parts = spec.split(":")
        if len(parts) == 1:
            ip, host, cont = "0.0.0.0", 0, int(parts[0])
        elif len(parts) == 2:
            ip, host, cont = "0.0.0.0", int(parts[0]), int(parts[1])
        else:
            ip, host, cont = parts[0], int(parts[1]) if parts[1] else 0, int(parts[2])
        mappings.append([ip, host, cont, proto])
    conflicts = []
    for i in range(len(mappings)):
        for j in range(i + 1, len(mappings)):
            a, b = mappings[i], mappings[j]
            if a[3] == b[3] and a[1] == b[1] and a[1] != 0:
                if a[0] == b[0] or "0.0.0.0" in (a[0], b[0]):
                    conflicts.append([i, j])
    return [mappings, conflicts]
''',
    tests=[
        [["8080:80", "127.0.0.1:8080:8000", "8080:80/udp", "9000"]],
        [[]],
        [["80"]],
        [["80", "80", "80/udp"]],
        [["5432:5432", "5433:5432"]],
        [["127.0.0.1:5432:5432", "10.0.0.5:5432:5432"]],
        [["127.0.0.1:5432:5432", "127.0.0.1:5432:5433"]],
        [["53:53/udp", "53:53/tcp", "53:5353/udp"]],
        [["127.0.0.1::8000", "127.0.0.1::8000"]],
        [["443:8443", "443:8443", "443:9443"]],
        [["10.0.0.1:80:80", "0.0.0.0:80:8080", "10.0.0.2:80:80"]],
        [["8000:8000/tcp", "8000:8000"]],
        [["%d:80" % (3000 + i % 40) for i in range(80)]],
    ],
    examples=1,
    wrong_solutions=[
        '''def parsePorts(specs):
    mappings = []
    for spec in specs:
        proto = "tcp"
        if "/" in spec:
            spec, proto = spec.split("/", 1)
        parts = spec.split(":")
        if len(parts) == 1:
            ip, host, cont = "0.0.0.0", 0, int(parts[0])
        elif len(parts) == 2:
            ip, host, cont = "0.0.0.0", int(parts[0]), int(parts[1])
        else:
            ip, host, cont = parts[0], int(parts[1]) if parts[1] else 0, int(parts[2])
        mappings.append([ip, host, cont, proto])
    conflicts = []
    for i in range(len(mappings)):
        for j in range(i + 1, len(mappings)):
            if mappings[i][1] == mappings[j][1]:
                conflicts.append([i, j])
    return [mappings, conflicts]
''',
        '''def parsePorts(specs):
    mappings = []
    for spec in specs:
        proto = "tcp"
        if "/" in spec:
            spec, proto = spec.split("/", 1)
        parts = spec.split(":")
        if len(parts) == 1:
            ip, host, cont = "0.0.0.0", 0, int(parts[0])
        elif len(parts) == 2:
            ip, host, cont = "0.0.0.0", int(parts[0]), int(parts[1])
        else:
            ip, host, cont = parts[0], int(parts[1]) if parts[1] else 0, int(parts[2])
        mappings.append([ip, host, cont, proto])
    conflicts = []
    for i in range(len(mappings)):
        for j in range(i + 1, len(mappings)):
            a, b = mappings[i], mappings[j]
            if a[3] == b[3] and a[1] == b[1] and a[1] != 0 and a[0] == b[0]:
                conflicts.append([i, j])
    return [mappings, conflicts]
''',
    ],
    guide=dict(
        prereqs="Lesson *Running, inspecting and stopping containers* (publishing ports). String splitting; nested loops over pairs.",
        intuition="Two containers may use the same port **inside** freely. The host has one set of ports per protocol and per address, so a clash "
                  "is 'same protocol, same host port, overlapping address'. `0.0.0.0` overlaps with everything; a random port (0) never clashes.",
        hints=[
            "Cut the `/protocol` suffix off first, then count the colon-separated fields.",
            "Three fields with an empty middle one (`IP::C`) means a random host port.",
            "Compare every pair `i < j`; write the overlap rule as `a == b or '0.0.0.0' in (a, b)`.",
        ],
        brute_force="The pairwise comparison *is* the brute force and is O(n^2). It is fine for the handful of ports on a real host.",
        approach="Parse each spec into four values, then test all pairs.\n\n**Dry run** (example): mapping 0 is `0.0.0.0:8080/tcp`, mapping 1 is `127.0.0.1:8080/tcp` → "
                 "same protocol and port, one side is `0.0.0.0` → conflict `[0, 1]`. Mapping 2 is UDP → different protocol. Mapping 3 has host port 0 → never conflicts.",
        complexity="Time O(n^2) for the pair check, O(n) to parse. Grouping by `(protocol, host_port)` first would make the common case near O(n).",
        pitfalls="- Comparing container ports instead of host ports.\n- Forgetting that TCP 53 and UDP 53 are different ports.\n"
                 "- Treating two random ports as a conflict.\n- Ignoring the `0.0.0.0` wildcard.",
        follow_up="Support ranges such as `9000-9002:9000-9002` and IPv6 addresses in brackets.",
    ),
),
dict(
    id="docker-mount-spec",
    title="Volume or Bind Mount?",
    difficulty="Easy",
    pattern="Storage",
    entry="classifyMounts",
    description=r"""
Interpret `-v` arguments the way Docker does. Write `classifyMounts(specs)` returning one result per spec.

Split the spec on `:`.

1. If there are at least two fields and the **last** field is `ro` or `rw`, that is the mode and is removed.
   Otherwise the mode is `rw`.
2. After that there must be one or two fields, otherwise the result is `["invalid", "", "", ""]`.
3. **One field** `T`: an anonymous volume → `["volume", "", T, mode]`.
4. **Two fields** `S` and `T`:
   - if `S` starts with `/`, `./`, `../` or `~`, or is exactly `.` or `..`, it is a host path → `["bind", S, T, mode]`;
   - otherwise `S` is a volume name → `["volume", S, T, mode]`. A volume name must start with a letter or digit and
     contain only letters, digits, `_`, `.` and `-`; if not, the result is invalid.
5. In every case the target `T` must start with `/`; if not, the result is invalid.

**Example:** `["pgdata:/var/lib/postgresql/data", "./src:/app/src:ro", "/cache", "data:relative"]`
→ `[["volume","pgdata","/var/lib/postgresql/data","rw"], ["bind","./src","/app/src","ro"], ["volume","","/cache","rw"], ["invalid","","",""]]`
""",
    starter='''def classifyMounts(specs):
    pass
''',
    solution='''import re

def classifyMounts(specs):
    bad = ["invalid", "", "", ""]
    out = []
    for spec in specs:
        parts = spec.split(":")
        mode = "rw"
        if len(parts) >= 2 and parts[-1] in ("ro", "rw"):
            mode = parts.pop()
        if len(parts) not in (1, 2):
            out.append(bad); continue
        target = parts[-1]
        if not target.startswith("/"):
            out.append(bad); continue
        if len(parts) == 1:
            out.append(["volume", "", target, mode]); continue
        src = parts[0]
        if src.startswith(("/", "./", "../", "~")) or src in (".", ".."):
            out.append(["bind", src, target, mode])
        elif re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", src):
            out.append(["volume", src, target, mode])
        else:
            out.append(bad)
    return out
''',
    tests=[
        [["pgdata:/var/lib/postgresql/data", "./src:/app/src:ro", "/cache", "data:relative"]],
        [[]],
        [["/srv/conf/app.toml:/etc/app/app.toml:ro"]],
        [["data:/app/data", "./data:/app/data"]],
        [["~/code:/work", "../shared:/shared:rw", ".:/here"]],
        [["a:b:c:d", "a:/b:ro:rw"]],
        [["/only:ro"]],
        [["my vol:/x", "-bad:/x", "ok_1.2-3:/x"]],
        [["relative"]],
        [["cache:/data:ro", "cache:/data:rw", "cache:/data:xx"]],
        [[":/data", "vol:"]],
        [["/a:/b", "/a:b"]],
        [["ro:/data", "rw"]],
    ],
    examples=1,
    wrong_solutions=[
        '''def classifyMounts(specs):
    out = []
    for spec in specs:
        parts = spec.split(":")
        mode = "rw"
        if parts[-1] in ("ro", "rw"):
            mode = parts.pop()
        if len(parts) == 1:
            out.append(["volume", "", parts[0], mode])
        elif len(parts) == 2:
            kind = "bind" if "/" in parts[0] else "volume"
            out.append([kind, parts[0], parts[1], mode])
        else:
            out.append(["invalid", "", "", ""])
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Volumes, bind mounts and tmpfs*. String splitting and a simple regular expression.",
        intuition="Docker decides by the **shape of the source**: something that looks like a path is a bind mount, a bare word is a volume name, "
                  "and no source at all is an anonymous volume. That is why `data:/x` and `./data:/x` do completely different things.",
        hints=[
            "Peel the optional mode off the end first, but only when at least two fields exist.",
            "Validate the target (must be absolute) before looking at the source.",
            "Check the path prefixes with `str.startswith` and a tuple; validate a volume name with `re.fullmatch`.",
        ],
        brute_force="There is nothing to search here; the only choice is between a careful rule-by-rule parse and an unmaintainable regular expression.",
        approach="Per spec: split, pop the mode, check the field count, check the target, then classify the source.\n\n**Dry run** `./src:/app/src:ro`: "
                 "fields `['./src', '/app/src', 'ro']`; last is a mode → `ro`. Two fields remain. Target starts with `/`. Source starts with `./` → "
                 "`['bind', './src', '/app/src', 'ro']`.",
        complexity="Time O(total length of the specs), space O(n) for the results.",
        pitfalls="- Classifying by 'contains a slash': `vol/name` is not a valid volume and not a path prefix.\n- Treating a single field `ro` as a mode.\n"
                 "- Accepting a relative target.\n- Forgetting `~` and `..`.",
        follow_up="Parse the long `--mount type=bind,source=...,target=...,readonly` syntax into the same four values.",
    ),
),
dict(
    id="docker-restart-policy",
    title="Simulate a Restart Policy",
    difficulty="Medium",
    pattern="Reliability",
    entry="simulateRestarts",
    description=r"""
Simulate how Docker restarts a crashing container. Write `simulateRestarts(policy, max_retries, runs)`.

- `policy` is `"no"`, `"on-failure"`, `"always"` or `"unless-stopped"`.
- `max_retries` applies only to `on-failure`: the maximum number of restarts, with `0` meaning unlimited.
- `runs` lists what happens each time the container runs: `[seconds_it_ran, exit_code]`. If the container is
  restarted more times than there are entries, the next run does not exit (it keeps running).

Process the runs in order. After a run exits:

1. **Should it restart?** `no`: never. `on-failure`: only if the exit code is not 0 **and** the number of restarts so
   far is below `max_retries` (when `max_retries > 0`). `always` and `unless-stopped`: always.
2. If not, stop: the final state is `"exited"`.
3. If yes: the back-off delay starts at 100 ms. If the run that exited lasted **10 seconds or more**, first reset the
   delay to 100. Wait the current delay, then double it for next time, capped at 60000 ms. Count one restart.

If every listed run has been used and a restart happened after the last one, the final state is `"running"`.
With an empty `runs` list the container never exits: state `"running"`.

Return `[restart_count, total_wait_ms, final_state]`.

**Example:** `("on-failure", 0, [[1, 1], [1, 1], [30, 1], [2, 0]])` → `[3, 400, "exited"]`
(waits 100, 200, then reset to 100; the last exit has code 0 so there is no further restart.)
""",
    starter='''def simulateRestarts(policy, max_retries, runs):
    pass
''',
    solution='''def simulateRestarts(policy, max_retries, runs):
    delay, restarts, waited = 100, 0, 0
    for ran, code in runs:
        if policy == "no":
            return [restarts, waited, "exited"]
        if policy == "on-failure":
            if code == 0 or (max_retries > 0 and restarts >= max_retries):
                return [restarts, waited, "exited"]
        if ran >= 10:
            delay = 100
        waited += delay
        delay = min(delay * 2, 60000)
        restarts += 1
    return [restarts, waited, "running"]
''',
    tests=[
        ["on-failure", 0, [[1, 1], [1, 1], [30, 1], [2, 0]]],
        ["no", 0, [[5, 1]]],
        ["always", 0, []],
        ["always", 0, [[3, 0], [3, 0]]],
        ["unless-stopped", 0, [[1, 137]]],
        ["on-failure", 3, [[1, 1]] * 10],
        ["on-failure", 1, [[1, 1], [1, 0]]],
        ["on-failure", 0, [[100, 0]]],
        ["always", 0, [[0, 1]] * 12],
        ["always", 0, [[0, 1]] * 5 + [[10, 1], [0, 1]]],
        ["always", 0, [[9, 1], [9, 1], [9, 1]]],
        ["on-failure", 5, [[1, 2], [1, 2], [1, 0], [1, 2]]],
        ["always", 5, [[1, 1]] * 8],
        ["on-failure", 2, [[20, 1], [20, 1], [20, 1]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def simulateRestarts(policy, max_retries, runs):
    delay, restarts, waited = 100, 0, 0
    for ran, code in runs:
        if policy == "no" or (policy == "on-failure" and code == 0):
            return [restarts, waited, "exited"]
        if max_retries > 0 and restarts >= max_retries:
            return [restarts, waited, "exited"]
        waited += delay
        delay = delay * 2
        restarts += 1
    return [restarts, waited, "running"]
''',
        '''def simulateRestarts(policy, max_retries, runs):
    delay, restarts, waited = 100, 0, 0
    for ran, code in runs:
        if policy == "no":
            return [restarts, waited, "exited"]
        if policy == "on-failure" and (code == 0 or (max_retries > 0 and restarts >= max_retries)):
            return [restarts, waited, "exited"]
        waited += delay
        delay = min(delay * 2, 60000)
        if ran >= 10:
            delay = 100
        restarts += 1
    return [restarts, waited, "exited"]
''',
    ],
    guide=dict(
        prereqs="Lesson *Restart policies and self-healing containers*. A loop that carries state between iterations.",
        intuition="It is a small state machine with three numbers to carry: the current delay, the restart count and the total time waited. "
                  "Each exit asks one question (restart or not?) and, if yes, performs one fixed update.",
        hints=[
            "Decide 'restart or stop' first and `return` at once when the answer is stop.",
            "Reset the delay **before** using it when the run lasted at least 10 seconds.",
            "If the loop finishes without returning, the last thing that happened was a restart, so the container is running.",
        ],
        brute_force="A real-time simulation ticking one millisecond at a time would work and be millions of times slower. Jump from event to event instead.",
        approach="Initialise `delay = 100`. For each run: apply the policy test; reset on long runs; add the delay to the total; double with a cap; count.\n\n"
                 "**Dry run** (example): run 1 exits 1 → wait 100, delay 200, restarts 1. Run 2 exits 1 → wait 200 (total 300), delay 400, restarts 2. "
                 "Run 3 lasted 30 s → reset to 100, wait 100 (total 400), delay 200, restarts 3. Run 4 exits 0 under `on-failure` → stop. `[3, 400, 'exited']`.",
        complexity="Time O(n) in the number of runs, space O(1).",
        pitfalls="- Applying `max_retries` to `always`.\n- Forgetting the 60000 ms cap (twelve quick crashes reach it).\n- Resetting the delay *after* waiting.\n"
                 "- Returning `exited` when the runs list is exhausted after a restart.",
        follow_up="Add a manual `docker stop` event and a daemon restart to distinguish `always` from `unless-stopped`.",
    ),
),
dict(
    id="docker-health-state",
    title="Health Check State Machine",
    difficulty="Medium",
    pattern="Reliability",
    entry="healthStates",
    description=r"""
Reproduce the health status Docker reports. Write `healthStates(checks, interval, timeout, retries, start_period)`.

`checks` is the list of health check runs in order; each is `[passed, duration]` where `passed` is a boolean and
`duration` is how many seconds the check took. Check number `k` (counting from 1) finishes at time `k * interval`
seconds after the container started.

A check **succeeds** only if `passed` is true **and** `duration <= timeout`.

The container starts in state `"starting"` with a failure streak of 0. After each check:

- **Success:** the state becomes `"healthy"` and the streak becomes 0.
- **Failure:** if the state is still `"starting"` **and** the check finished at a time `<= start_period`, the failure
  is ignored completely. Otherwise the streak increases by 1, and if the streak is now `>= retries` the state becomes
  `"unhealthy"`. (Below that threshold the state is unchanged.)

Return the list of states after each check.

**Example:** `checks = [[False,1],[False,1],[True,1],[False,1],[False,1],[False,1]]`, `interval=10`, `timeout=3`,
`retries=2`, `start_period=20` → `["starting","starting","healthy","healthy","unhealthy","unhealthy"]`
""",
    starter='''def healthStates(checks, interval, timeout, retries, start_period):
    pass
''',
    solution='''def healthStates(checks, interval, timeout, retries, start_period):
    state, streak, out = "starting", 0, []
    for k, (passed, duration) in enumerate(checks, start=1):
        ok = bool(passed) and duration <= timeout
        if ok:
            state, streak = "healthy", 0
        else:
            t = k * interval
            if not (state == "starting" and t <= start_period):
                streak += 1
                if streak >= retries:
                    state = "unhealthy"
        out.append(state)
    return out
''',
    tests=[
        [[[False, 1], [False, 1], [True, 1], [False, 1], [False, 1], [False, 1]], 10, 3, 2, 20],
        [[], 10, 3, 3, 0],
        [[[True, 1]], 30, 30, 3, 0],
        [[[False, 1], [False, 1], [False, 1], [False, 1]], 10, 3, 3, 0],
        [[[False, 1], [False, 1], [False, 1], [False, 1], [False, 1]], 10, 3, 3, 20],
        [[[True, 5], [True, 5], [True, 5]], 10, 3, 2, 0],
        [[[True, 3], [True, 4]], 10, 3, 1, 0],
        [[[True, 1], [False, 1], [True, 1], [False, 1], [False, 1], [True, 1]], 5, 2, 2, 0],
        [[[False, 1]] * 3 + [[True, 1]] + [[False, 1]] * 3, 10, 3, 3, 60],
        [[[False, 1], [False, 1], [False, 1]], 10, 3, 1, 10],
        [[[False, 1]] * 6, 10, 3, 2, 30],
        [[[True, 1], [False, 9], [False, 9], [False, 1], [True, 1], [False, 1]], 10, 3, 3, 100],
        [[[False, 1], [True, 1], [False, 1], [False, 1]], 10, 3, 2, 100],
    ],
    examples=1,
    wrong_solutions=[
        '''def healthStates(checks, interval, timeout, retries, start_period):
    state, streak, out = "starting", 0, []
    for k, (passed, duration) in enumerate(checks, start=1):
        if passed:
            state, streak = "healthy", 0
        else:
            streak += 1
            if streak >= retries:
                state = "unhealthy"
        out.append(state)
    return out
''',
        '''def healthStates(checks, interval, timeout, retries, start_period):
    state, streak, out = "starting", 0, []
    for k, (passed, duration) in enumerate(checks, start=1):
        ok = bool(passed) and duration <= timeout
        if ok:
            state, streak = "healthy", 0
        elif k * interval > start_period:
            streak += 1
            if streak >= retries:
                state = "unhealthy"
        out.append(state)
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Health checks and dependency checks*. Loops with state.",
        intuition="Three states and one counter. Success always wins outright. Failure only counts when it is 'real': outside the start-up grace, "
                  "or after the container has already been healthy once. `retries` real failures in a row tip it over.",
        hints=[
            "Work out 'did this check succeed?' as one boolean that includes the timeout.",
            "The grace period only protects a container that is still `starting`; once healthy, failures count even if the clock is inside the start period.",
            "Append the state after every check, including when nothing changed.",
        ],
        brute_force="Recompute from scratch for every prefix of the check list: O(n^2). The single pass carries the two pieces of state forward instead.",
        approach="Loop with a 1-based index to get the finish time `k * interval`. Update `(state, streak)` by the two rules, record the state.\n\n"
                 "**Dry run** (example, start period 20, retries 2): t=10 fail, starting and inside grace → ignored. t=20 fail → ignored (20 <= 20). "
                 "t=30 pass → healthy. t=40 fail → streak 1, still healthy. t=50 fail → streak 2 → unhealthy. t=60 fail → unhealthy.",
        complexity="Time O(n), space O(n) for the output.",
        pitfalls="- Ignoring the timeout.\n- Forgiving failures inside the start period even after the container became healthy.\n"
                 "- Not resetting the streak on success.\n- Using `<` instead of `<=` at the edge of the start period.",
        follow_up="Add Swarm's reaction: replace the task when it turns unhealthy, and count replacements.",
    ),
),
dict(
    id="docker-log-rotation",
    title="Simulate Log Rotation",
    difficulty="Easy",
    pattern="Observability",
    entry="rotateLogs",
    description=r"""
The `json-file` logging driver rotates files with `max-size` and `max-file`. Write
`rotateLogs(line_sizes, max_size, max_file)`.

Lines are written one at a time; `line_sizes[i]` is the size of line `i` in bytes. Files are kept in a list with the
**current file first** and the oldest last. Start with one empty current file.

For each line:

1. If the current file is **not empty** and adding the line would make its size **greater than** `max_size`, rotate:
   a new empty file becomes the current file and all others move one place back. If there are now more than
   `max_file` files, delete the oldest ones until there are `max_file`.
2. Append the line to the current file. (A single line larger than `max_size` is still written whole, into an empty file.)

Return `[sizes, lost]` where `sizes` is the list of file sizes, current file first, and `lost` is the total number of
bytes in deleted files. `max_file` is at least 1.

**Example:** `line_sizes = [4,4,4,4,4,4,4]`, `max_size = 10`, `max_file = 3` → `[[4, 8, 8], 8]`
""",
    starter='''def rotateLogs(line_sizes, max_size, max_file):
    # return [file_sizes_current_first, lost_bytes]
    pass
''',
    solution='''def rotateLogs(line_sizes, max_size, max_file):
    files, lost = [0], 0
    counts = [0]
    for size in line_sizes:
        if counts[0] > 0 and files[0] + size > max_size:
            files.insert(0, 0)
            counts.insert(0, 0)
            while len(files) > max_file:
                lost += files.pop()
                counts.pop()
        files[0] += size
        counts[0] += 1
    return [files, lost]
''',
    tests=[
        [[4, 4, 4, 4, 4, 4, 4], 10, 3],
        [[], 10, 3],
        [[5], 10, 1],
        [[5, 5], 10, 1],
        [[5, 5, 1], 10, 1],
        [[25, 1], 10, 2],
        [[25, 25, 25], 10, 2],
        [[3, 3, 3, 3], 100, 5],
        [[10, 10, 10, 10], 10, 2],
        [[0, 0, 0, 7, 7], 10, 2],
        [[1] * 1000, 64, 4],
        [[6, 5, 6, 5, 6, 5], 11, 10],
        [[7, 7, 7, 7, 7], 7, 1],
    ],
    examples=1,
    wrong_solutions=[
        '''def rotateLogs(line_sizes, max_size, max_file):
    files, lost = [0], 0
    for size in line_sizes:
        if files[0] + size >= max_size:
            files.insert(0, 0)
            while len(files) > max_file:
                lost += files.pop()
        files[0] += size
    return [files, lost]
''',
        '''def rotateLogs(line_sizes, max_size, max_file):
    files, lost, n = [0], 0, [0]
    for size in line_sizes:
        if n[0] > 0 and files[0] + size > max_size:
            files.insert(0, 0); n.insert(0, 0)
            if len(files) > max_file:
                files.pop(); n.pop()
        files[0] += size; n[0] += 1
    return [files, lost]
''',
    ],
    guide=dict(
        prereqs="Lesson *Container logs, logging drivers and logging patterns*. Lists used as a queue.",
        intuition="Keep a short list of file sizes. Before writing, ask whether the line still fits; if not, push a fresh file to the front and drop from the back. "
                  "The only subtle point is an *empty* file: it must accept any line, or an oversized line would rotate forever.",
        hints=[
            "Track whether the current file is empty separately from its size, because zero-length lines exist.",
            "Rotation happens **before** the write, and only when the result would be strictly greater than the limit.",
            "Add the size of every popped file to `lost`.",
        ],
        brute_force="Store every line in every file and recompute sizes with `sum` each time: O(n^2). Keeping a running size per file makes each line O(1).",
        approach="`files = [0]`, `counts = [0]`. For each line: rotate if needed, trim to `max_file`, then add.\n\n**Dry run** (example, limit 10, keep 3): "
                 "lines 1-2 → `[8]`. Line 3 would make 12 → rotate → `[4, 8]`. Line 4 → `[8, 8]`. Line 5 → rotate → `[4, 8, 8]`. Line 6 → `[8, 8, 8]`. "
                 "Line 7 → rotate → four files, delete the oldest (8 bytes lost) → `[4, 8, 8]`. Result `[[4, 8, 8], 8]`.",
        complexity="Time O(n) (each line causes at most one insert and one pop on a list of at most `max_file + 1` items), space O(max_file).",
        pitfalls="- Using `>=` so that a file can never be exactly full.\n- Rotating an empty file for an oversized line.\n- Forgetting to count lost bytes.\n"
                 "- Returning the files oldest-first.",
        follow_up="Given a line rate and size, compute how many hours of history a `max-size`/`max-file` setting retains.",
    ),
),
]
