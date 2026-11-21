PROBLEMS = [
dict(
    id="tf-workspace-key",
    title="Map workspaces to state objects in an S3 backend",
    difficulty="Easy",
    pattern="State",
    entry="statePaths",
    description=r"""
With an S3 backend, one configuration can keep several separate state files, one per **workspace**. Knowing
exactly where each one is stored matters when you need to inspect, back up or restore state. Write
`statePaths(backend, workspaces)`.

`backend` is a dict holding the backend settings:

- `"bucket"`: the bucket name;
- `"key"`: the path of the state object inside the bucket, as configured;
- `"workspace_key_prefix"`: optional, defaults to `"env:"`;
- `"use_lockfile"`: optional bool, defaults to false. When true, Terraform locks by writing a lock object
  beside the state, named like the state object with `.tflock` added.

Rules for the object key:

- workspace `default` → the configured `key` unchanged;
- any other workspace → `<workspace_key_prefix>/<workspace>/<key>`.

Return a dict from each workspace name in `workspaces` to `[state_url, lock_url]`, where
`state_url` is `s3://<bucket>/<object key>` and `lock_url` is the state URL plus `.tflock` when
`use_lockfile` is true, otherwise `None`.

**Example:** backend `{"bucket": "acme-tfstate", "key": "app/terraform.tfstate", "use_lockfile": True}` and
workspaces `["default", "stage"]` →

```
{"default": ["s3://acme-tfstate/app/terraform.tfstate", "s3://acme-tfstate/app/terraform.tfstate.tflock"],
 "stage":   ["s3://acme-tfstate/env:/stage/app/terraform.tfstate", "s3://acme-tfstate/env:/stage/app/terraform.tfstate.tflock"]}
```
""",
    starter='''def statePaths(backend, workspaces):
    pass
''',
    solution='''def statePaths(backend, workspaces):
    prefix = backend.get("workspace_key_prefix", "env:")
    locking = bool(backend.get("use_lockfile", False))
    result = {}
    for workspace in workspaces:
        if workspace == "default":
            key = backend["key"]
        else:
            key = prefix + "/" + workspace + "/" + backend["key"]
        url = "s3://" + backend["bucket"] + "/" + key
        result[workspace] = [url, url + ".tflock" if locking else None]
    return result
''',
    tests=[
        [{"bucket": "acme-tfstate", "key": "app/terraform.tfstate", "use_lockfile": True}, ["default", "stage"]],
        [{"bucket": "acme-tfstate", "key": "terraform.tfstate"}, ["default", "dev", "prod"]],
        [{"bucket": "b", "key": "k"}, []],
        [{"bucket": "b", "key": "k"}, ["default"]],
        [{"bucket": "b", "key": "k", "use_lockfile": False}, ["dev"]],
        [{"bucket": "acme-tfstate", "key": "live/prod/network/terraform.tfstate", "workspace_key_prefix": "workspaces",
          "use_lockfile": True}, ["default", "blue", "green"]],
        [{"bucket": "acme-tfstate", "key": "app.tfstate", "workspace_key_prefix": "team/app"}, ["feature-123"]],
        [{"bucket": "acme-tfstate", "key": "app/terraform.tfstate", "use_lockfile": True}, ["Default", "defaults"]],
        [{"bucket": "state", "key": "env:/dev/terraform.tfstate", "use_lockfile": True}, ["default", "dev"]],
        [{"bucket": "acme", "key": "a/b/c.tfstate", "workspace_key_prefix": "env:"}, ["default", "x"]],
        [{"bucket": "acme", "key": "terraform.tfstate", "use_lockfile": True}, [f"pr-{i}" for i in range(40)] + ["default"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def statePaths(backend, workspaces):
    prefix = backend.get("workspace_key_prefix", "env:")
    out = {}
    for w in workspaces:
        key = prefix + "/" + w + "/" + backend["key"]
        url = "s3://" + backend["bucket"] + "/" + key
        out[w] = [url, url + ".tflock" if backend.get("use_lockfile") else None]
    return out
''',
        '''def statePaths(backend, workspaces):
    out = {}
    for w in workspaces:
        key = backend["key"] if w == "default" else "env:/" + w + "/" + backend["key"]
        url = "s3://" + backend["bucket"] + "/" + key
        out[w] = [url, url + ".tflock"]
    return out
''',
        '''def statePaths(backend, workspaces):
    prefix = backend.get("workspace_key_prefix", "env:")
    out = {}
    for w in workspaces:
        key = backend["key"] if w == "default" else backend["key"] + "/" + prefix + "/" + w
        url = "s3://" + backend["bucket"] + "/" + key
        out[w] = [url, url + ".tflock" if backend.get("use_lockfile") else None]
    return out
''',
    ],
    guide=dict(
        prereqs="Backends and locking in *Terraform state, remote backends and locking*; workspaces in *Isolating state: workspaces, file layout and reading another state*. String building and `dict.get` with a default.",
        intuition="A bucket is a filing cabinet and the `key` is the label on one folder. The `default` workspace uses that folder directly. Every other workspace gets the same label filed one level deeper, inside a drawer named after the prefix and then the workspace. The lock, when S3 locking is on, is a sticky note placed next to whichever folder is being edited.",
        hints=[
            "Read the two optional settings once, with their defaults, before the loop.",
            "Only the exact name `default` is special. `Default` and `defaults` are ordinary workspaces.",
            "Build the state URL first; the lock URL is that string plus a suffix, or `None`.",
        ],
        brute_force="There is no meaningfully slower method; each workspace is one string concatenation. The work is in getting the three small rules right.",
        approach="""1. `prefix = backend.get("workspace_key_prefix", "env:")`, `locking = backend.get("use_lockfile", False)`.
2. For each workspace: `default` → `key`; otherwise `prefix/workspace/key`.
3. `url = "s3://" + bucket + "/" + key`; lock is `url + ".tflock"` when locking.

**Dry run:** bucket `acme-tfstate`, key `live/prod/network/terraform.tfstate`, prefix `workspaces`, locking on.

| workspace | object key |
|---|---|
| default | live/prod/network/terraform.tfstate |
| blue | workspaces/blue/live/prod/network/terraform.tfstate |

Note where `blue` ended up: at the top of the bucket under `workspaces/`, not beside the default state under `live/prod/network/`. Anyone browsing the `live/prod` folder will not see it, which is one reason workspaces are a weak way to separate environments.""",
        complexity="Time O(w·L) for w workspaces and key length L; space the same for the result.",
        pitfalls="Prefixing the `default` workspace too (first wrong solution). Hard-coding `env:` or always returning a lock path (second wrong solution): without `use_lockfile` there is no lock object. Appending the workspace after the key instead of before it (third wrong solution). Comparing workspace names case-insensitively.",
        follow_up="Write the inverse used by `terraform workspace list`: given every object key in the bucket and the backend settings, return the workspace names that have a state object, always including `default`.",
    ),
),
dict(
    id="tf-state-lock",
    title="Simulate state locking",
    difficulty="Easy",
    pattern="State",
    entry="lockLog",
    description=r"""
A state lock lets one run at a time write to a state file. Write `lockLog(events)` that replays a sequence
of lock operations against a single state and returns what each one printed.

Each event is a list:

- `["lock", who]`: a run started by `who` tries to take the lock.
  - Free → the lock is granted. Return its ID: `"lock-1"` for the first lock ever granted, `"lock-2"` for
    the second, and so on. Failed attempts do not use up a number.
  - Held (by anyone, **including the same person**) → `"Error: state locked by <holder> (<lock id>)"`.
- `["unlock", who]`: `who`'s run finishes and releases its lock.
  - Not locked → `"Error: state is not locked"`.
  - Held by someone else → `"Error: lock held by <holder>"`.
  - Held by `who` → release it and return `"unlocked"`.
- `["force-unlock", lock_id]`: someone runs `terraform force-unlock` with an ID.
  - Not locked → `"Error: state is not locked"`.
  - The ID differs from the current lock's ID → `"Error: lock ID <lock_id> does not match"`.
  - It matches → release the lock and return `"force-unlocked"`.

Return the list of results, one per event.

**Example:** `[["lock", "asha"], ["lock", "ben"], ["unlock", "asha"], ["lock", "ben"]]` →
`["lock-1", "Error: state locked by asha (lock-1)", "unlocked", "lock-2"]`
""",
    starter='''def lockLog(events):
    pass
''',
    solution='''def lockLog(events):
    holder = None
    lock_id = None
    granted = 0
    out = []
    for event in events:
        kind, arg = event[0], event[1]
        if kind == "lock":
            if holder is None:
                granted += 1
                holder, lock_id = arg, "lock-" + str(granted)
                out.append(lock_id)
            else:
                out.append("Error: state locked by " + holder + " (" + lock_id + ")")
        elif kind == "unlock":
            if holder is None:
                out.append("Error: state is not locked")
            elif holder != arg:
                out.append("Error: lock held by " + holder)
            else:
                holder = lock_id = None
                out.append("unlocked")
        else:
            if holder is None:
                out.append("Error: state is not locked")
            elif arg != lock_id:
                out.append("Error: lock ID " + arg + " does not match")
            else:
                holder = lock_id = None
                out.append("force-unlocked")
    return out
''',
    tests=[
        [[["lock", "asha"], ["lock", "ben"], ["unlock", "asha"], ["lock", "ben"]]],
        [[["lock", "ci"], ["force-unlock", "lock-9"], ["force-unlock", "lock-1"], ["lock", "ben"]]],
        [[]],
        [[["unlock", "asha"]]],
        [[["force-unlock", "lock-1"]]],
        [[["lock", "asha"], ["lock", "asha"], ["unlock", "asha"], ["unlock", "asha"]]],
        [[["lock", "asha"], ["unlock", "ben"], ["lock", "ben"], ["unlock", "asha"], ["lock", "ben"], ["unlock", "ben"]]],
        [[["lock", "a"], ["lock", "b"], ["lock", "c"], ["unlock", "a"], ["lock", "c"], ["lock", "b"], ["unlock", "c"],
          ["lock", "b"]]],
        [[["lock", "ci"], ["unlock", "ci"], ["force-unlock", "lock-1"], ["lock", "ci"], ["force-unlock", "lock-1"],
          ["force-unlock", "lock-2"], ["unlock", "ci"]]],
        [[["lock", "ben"], ["force-unlock", "ben"], ["force-unlock", "lock-1"], ["unlock", "ben"]]],
        [[["lock", "asha"], ["force-unlock", "lock-1"], ["lock", "ben"], ["unlock", "asha"], ["unlock", "ben"]]],
        [[e for i in range(60) for e in (["lock", f"run{i}"], ["lock", "late"], ["unlock", f"run{i}"])]],
    ],
    examples=2,
    wrong_solutions=[
        '''def lockLog(events):
    holder = lock_id = None
    n, out = 0, []
    for kind, arg in events:
        if kind == "lock":
            if holder is None or holder == arg:
                n += 1; holder, lock_id = arg, f"lock-{n}"; out.append(lock_id)
            else:
                out.append(f"Error: state locked by {holder} ({lock_id})")
        elif kind == "unlock":
            if holder is None:
                out.append("Error: state is not locked")
            elif holder != arg:
                out.append(f"Error: lock held by {holder}")
            else:
                holder = lock_id = None; out.append("unlocked")
        else:
            if holder is None:
                out.append("Error: state is not locked")
            elif arg != lock_id:
                out.append(f"Error: lock ID {arg} does not match")
            else:
                holder = lock_id = None; out.append("force-unlocked")
    return out
''',
        '''def lockLog(events):
    holder = lock_id = None
    n, out = 0, []
    for kind, arg in events:
        if kind == "lock":
            n += 1
            if holder is None:
                holder, lock_id = arg, f"lock-{n}"; out.append(lock_id)
            else:
                out.append(f"Error: state locked by {holder} ({lock_id})")
        elif kind == "unlock":
            if holder is None:
                out.append("Error: state is not locked")
            elif holder != arg:
                out.append(f"Error: lock held by {holder}")
            else:
                holder = lock_id = None; out.append("unlocked")
        else:
            if holder is None:
                out.append("Error: state is not locked")
            elif arg != lock_id:
                out.append(f"Error: lock ID {arg} does not match")
            else:
                holder = lock_id = None; out.append("force-unlocked")
    return out
''',
        '''def lockLog(events):
    holder = lock_id = None
    n, out = 0, []
    for kind, arg in events:
        if kind == "lock":
            if holder is None:
                n += 1; holder, lock_id = arg, f"lock-{n}"; out.append(lock_id)
            else:
                out.append(f"Error: state locked by {holder} ({lock_id})")
        elif kind == "unlock":
            if holder != arg:
                out.append("Error: state is not locked" if holder is None else f"Error: lock held by {holder}")
            else:
                holder = lock_id = None; out.append("unlocked")
        else:
            if holder is None:
                out.append("Error: state is not locked")
            else:
                holder = lock_id = None; out.append("force-unlocked")
    return out
''',
    ],
    guide=dict(
        prereqs="Locking and `force-unlock` in *Terraform state, remote backends and locking*. A loop with a few state variables.",
        intuition="The lock is a single key hanging on a hook. Whoever takes it writes their name and a ticket number on the hook. Anyone else who arrives reads the hook and waits. The key goes back either when its holder returns it or when somebody deliberately overrides the hook, and to override they must quote the ticket number, which proves they looked at *this* lock and not an older one.",
        hints=[
            "Three variables are enough: who holds the lock, its ID, and how many locks have been granted so far.",
            "Increase the counter only when a lock is granted.",
            "For each event kind, handle the 'not locked' case first, then the mismatch case, then the success case.",
        ],
        brute_force="Keep the full history of events and recompute the current holder from the start for every new event: O(n²). Carrying the current holder forward makes it O(n).",
        approach="""State: `holder`, `lock_id`, `granted`.

- **lock**: free → `granted += 1`, record holder and `lock-<granted>`; otherwise the error naming holder and ID.
- **unlock**: not locked → error; other holder → error; else clear.
- **force-unlock**: not locked → error; ID mismatch → error; else clear.

**Dry run** of the second example:

| event | holder before | result | holder after |
|---|---|---|---|
| lock ci | none | lock-1 | ci |
| force-unlock lock-9 | ci (lock-1) | Error: lock ID lock-9 does not match | ci |
| force-unlock lock-1 | ci (lock-1) | force-unlocked | none |
| lock ben | none | lock-2 | ben |""",
        complexity="Time O(n) for n events; space O(n) for the output and O(1) for the lock itself.",
        pitfalls="Letting the same person lock twice (first wrong solution): two terminals owned by one engineer are two separate runs and can corrupt state as easily as two people. Numbering failed attempts (second wrong solution). Force-unlocking without checking the ID (third wrong solution): the ID check is the safeguard against releasing a newer lock than the one you investigated.",
        follow_up="Real backends never expire a lock. Add timestamps to events and report locks held longer than a threshold as `possibly stale`, without releasing them automatically. Why is automatic release dangerous?",
    ),
),
dict(
    id="tf-stale-plan",
    title="Detect stale saved plans",
    difficulty="Easy",
    pattern="State",
    entry="replayRuns",
    description=r"""
A saved plan (`terraform plan -out=FILE`) remembers which version of the state it was computed from. State
carries a counter called the **serial** that goes up each time the state is rewritten. If the serial has moved
on by the time someone applies the file, the plan no longer describes reality and Terraform refuses it.

Write `replayRuns(start_serial, events)`. The state begins at `start_serial`. Each event is a list:

- `["plan", name, changes]`: save a plan called `name`, computed at the current serial, containing `changes`
  resource changes (a whole number ≥ 0). Saving under an existing name overwrites that plan.
  Result: `"Planned <name> at serial <serial>"`.
- `["apply", name]`: apply the saved plan `name`.
  - No such plan → `"Error: no plan <name>"`.
  - The plan's serial differs from the current serial → `"Error: Saved plan is stale"`.
  - Otherwise it is applied. If the plan had at least one change, the serial increases by 1; a plan with
    zero changes leaves the state untouched. Result: `"Applied <name>: serial <serial after>"`.
  - A plan file is not deleted by applying it.
- `["direct", changes]`: someone runs `terraform apply` with no plan file. It plans afresh, so it is never
  stale. The serial increases by 1 if `changes` > 0. Result: `"Applied directly: serial <serial after>"`.

Return the list of results.

**Example:** `replayRuns(7, [["plan", "a", 2], ["plan", "b", 1], ["apply", "a"], ["apply", "b"]])` →
`["Planned a at serial 7", "Planned b at serial 7", "Applied a: serial 8", "Error: Saved plan is stale"]`
""",
    starter='''def replayRuns(start_serial, events):
    pass
''',
    solution='''def replayRuns(start_serial, events):
    serial = start_serial
    plans = {}
    out = []
    for event in events:
        kind = event[0]
        if kind == "plan":
            name, changes = event[1], event[2]
            plans[name] = (serial, changes)
            out.append("Planned " + name + " at serial " + str(serial))
        elif kind == "apply":
            name = event[1]
            if name not in plans:
                out.append("Error: no plan " + name)
                continue
            planned_at, changes = plans[name]
            if planned_at != serial:
                out.append("Error: Saved plan is stale")
                continue
            if changes > 0:
                serial += 1
            out.append("Applied " + name + ": serial " + str(serial))
        else:
            if event[1] > 0:
                serial += 1
            out.append("Applied directly: serial " + str(serial))
    return out
''',
    tests=[
        [7, [["plan", "a", 2], ["plan", "b", 1], ["apply", "a"], ["apply", "b"]]],
        [1, [["plan", "pr-12", 3], ["direct", 1], ["apply", "pr-12"], ["plan", "pr-12", 3], ["apply", "pr-12"]]],
        [1, []],
        [5, [["apply", "ghost"]]],
        [5, [["plan", "a", 0], ["apply", "a"], ["apply", "a"]]],
        [5, [["plan", "a", 4], ["apply", "a"], ["apply", "a"]]],
        [5, [["plan", "a", 1], ["direct", 0], ["apply", "a"]]],
        [5, [["plan", "a", 0], ["plan", "b", 0], ["apply", "a"], ["apply", "b"]]],
        [0, [["direct", 2], ["direct", 0], ["direct", 5]]],
        [3, [["plan", "x", 1], ["plan", "x", 0], ["apply", "x"], ["plan", "y", 2], ["apply", "x"], ["apply", "y"],
             ["apply", "x"]]],
        [10, [["plan", "a", 1], ["plan", "b", 1], ["plan", "c", 1], ["apply", "c"], ["apply", "a"], ["plan", "a", 1],
              ["apply", "b"], ["apply", "a"]]],
        [100, [e for i in range(40) for e in (["plan", f"p{i}", i % 2], ["apply", f"p{i - 1}"], ["apply", f"p{i}"])]],
    ],
    examples=2,
    wrong_solutions=[
        '''def replayRuns(start_serial, events):
    serial, plans, out = start_serial, {}, []
    for e in events:
        if e[0] == "plan":
            plans[e[1]] = (serial, e[2]); out.append(f"Planned {e[1]} at serial {serial}")
        elif e[0] == "apply":
            if e[1] not in plans:
                out.append(f"Error: no plan {e[1]}"); continue
            if plans[e[1]][1] > 0:
                serial += 1
            out.append(f"Applied {e[1]}: serial {serial}")
        else:
            if e[1] > 0:
                serial += 1
            out.append(f"Applied directly: serial {serial}")
    return out
''',
        '''def replayRuns(start_serial, events):
    serial, plans, out = start_serial, {}, []
    for e in events:
        if e[0] == "plan":
            plans[e[1]] = (serial, e[2]); out.append(f"Planned {e[1]} at serial {serial}")
        elif e[0] == "apply":
            if e[1] not in plans:
                out.append(f"Error: no plan {e[1]}"); continue
            if plans[e[1]][0] != serial:
                out.append("Error: Saved plan is stale"); continue
            serial += 1
            out.append(f"Applied {e[1]}: serial {serial}")
        else:
            serial += 1
            out.append(f"Applied directly: serial {serial}")
    return out
''',
        '''def replayRuns(start_serial, events):
    serial, plans, out = start_serial, {}, []
    for e in events:
        if e[0] == "plan":
            plans[e[1]] = (serial, e[2]); out.append(f"Planned {e[1]} at serial {serial}")
        elif e[0] == "apply":
            if e[1] not in plans:
                out.append(f"Error: no plan {e[1]}"); continue
            at, changes = plans.pop(e[1])
            if at != serial:
                out.append("Error: Saved plan is stale"); continue
            if changes > 0:
                serial += 1
            out.append(f"Applied {e[1]}: serial {serial}")
        else:
            if e[1] > 0:
                serial += 1
            out.append(f"Applied directly: serial {serial}")
    return out
''',
    ],
    guide=dict(
        prereqs="Saved plans in *Installing Terraform, signing in safely and creating a first resource*; `serial` in *Terraform state, remote backends and locking*; plan-then-apply pipelines in *Terraform as a team, part 2: golden rules and a CI/CD pipeline*.",
        intuition="A saved plan is a set of driving directions written from a particular starting point. If the car has moved since they were written, following them blindly ends somewhere unintended. The serial is the starting point stamped on the directions; applying compares that stamp with where the state is now.",
        hints=[
            "Keep the current serial and a dict from plan name to the pair (serial when planned, number of changes).",
            "On apply, check for a missing plan first, then compare serials, and only then change anything.",
            "Whether the serial moves depends on whether the run changed anything, not on whether it ran.",
        ],
        brute_force="Store the whole event history and, for each apply, scan backwards to find the plan and count the state writes since: O(n²). One integer per plan gives the same answer in O(1) per event.",
        approach="""For each event:

- **plan** → `plans[name] = (serial, changes)`.
- **apply** → missing → error; `plans[name][0] != serial` → stale; else bump the serial when `changes > 0`.
- **direct** → bump the serial when `changes > 0`.

**Dry run** from serial 1: `plan pr-12 (3 changes)`, `direct (1 change)`, `apply pr-12`, `plan pr-12`, `apply pr-12`.

| event | serial before | result | serial after |
|---|---|---|---|
| plan pr-12 | 1 | Planned pr-12 at serial 1 | 1 |
| direct 1 | 1 | Applied directly: serial 2 | 2 |
| apply pr-12 | 2 | Error: Saved plan is stale | 2 |
| plan pr-12 | 2 | Planned pr-12 at serial 2 | 2 |
| apply pr-12 | 2 | Applied pr-12: serial 3 | 3 |

This is the everyday pipeline situation: two pull requests are planned, one merges and applies, and the other must be planned again before it can be applied.""",
        complexity="Time O(n) for n events; space O(p) for p saved plans.",
        pitfalls="Skipping the staleness check (first wrong solution): the second apply would then act on assumptions that are no longer true. Raising the serial for runs that changed nothing (second wrong solution), which makes harmless no-change applies invalidate everyone else's plans. Deleting a plan once applied (third wrong solution): the file is still on disk, and applying it again must report *stale*, not *missing*.",
        follow_up="Real state also carries a `lineage` identifier. Add it: a plan made against a state with a different lineage is rejected even if the serial numbers happen to match.",
    ),
),
dict(
    id="tf-detect-drift",
    title="Classify drift between configuration, state and reality",
    difficulty="Medium",
    pattern="State",
    entry="classifyDrift",
    description=r"""
**Drift** means the real infrastructure no longer matches what Terraform last recorded, usually because
someone changed it by hand. Deciding what to do needs three views of every attribute:

- `config`: what the code says it should be;
- `state`: what Terraform recorded after its last apply;
- `actual`: what the cloud provider reports right now.

Write `classifyDrift(config, state, actual, ignore_changes)`. The first three arguments map a resource
address to a dict of `attribute → value`. Every address in `state` is also in `config` with the same
attribute names. An address present in `actual` has the same attribute names too. Addresses that appear
only in `actual` are not managed by this configuration and are skipped.

`ignore_changes` maps an address to a list of attribute names the code has told Terraform not to manage
(the `lifecycle { ignore_changes = [...] }` setting). The list `["all"]` covers every attribute. An address
missing from the dict ignores nothing.

For each address in `state`:

- not in `actual` → one row `[address, "", "deleted"]` and nothing else for that address;
- otherwise, for each attribute, with `c`, `s`, `a` its three values:

| actual vs state | further test | label |
|---|---|---|
| `a == s` | `c == s` | *(no row)* |
| `a == s` | `c != s`, attribute ignored | *(no row)* |
| `a == s` | `c != s`, not ignored | `"pending"` (an ordinary code change waiting to be applied) |
| `a != s` | attribute ignored | `"drift-ignored"` |
| `a != s` | `c == a` | `"drift-adopted"` (the code was already updated to match) |
| `a != s` | `c == s` | `"drift-revert"` (the next apply undoes the manual change) |
| `a != s` | all three differ | `"drift-overwrite"` (the next apply replaces it with the code's value) |

Check the rows in the order shown. Return `[address, attribute, label]` rows sorted by address, then attribute.

**Example:** config and state both say `{"aws_instance.web": {"size": "small"}}` but actual says `"large"` →
`[["aws_instance.web", "size", "drift-revert"]]`
""",
    starter='''def classifyDrift(config, state, actual, ignore_changes):
    pass
''',
    solution='''def classifyDrift(config, state, actual, ignore_changes):
    rows = []
    for address in sorted(state):
        if address not in actual:
            rows.append([address, "", "deleted"])
            continue
        ignored = ignore_changes.get(address, [])
        ignore_all = "all" in ignored
        for attr in sorted(state[address]):
            s = state[address][attr]
            a = actual[address][attr]
            c = config[address][attr]
            skip = ignore_all or attr in ignored
            if a == s:
                if c != s and not skip:
                    rows.append([address, attr, "pending"])
            elif skip:
                rows.append([address, attr, "drift-ignored"])
            elif c == a:
                rows.append([address, attr, "drift-adopted"])
            elif c == s:
                rows.append([address, attr, "drift-revert"])
            else:
                rows.append([address, attr, "drift-overwrite"])
    return rows
''',
    tests=[
        [{"aws_instance.web": {"size": "small"}}, {"aws_instance.web": {"size": "small"}},
         {"aws_instance.web": {"size": "large"}}, {}],
        [{"aws_instance.web": {"size": "large", "ami": "ami-2"}}, {"aws_instance.web": {"size": "small", "ami": "ami-1"}},
         {"aws_instance.web": {"size": "large", "ami": "ami-1"}}, {}],
        [{}, {}, {}, {}],
        [{"aws_instance.web": {"size": "small"}}, {"aws_instance.web": {"size": "small"}},
         {"aws_instance.web": {"size": "small"}}, {}],
        [{"aws_instance.web": {"size": "small"}, "aws_s3_bucket.logs": {"acl": "private"}},
         {"aws_instance.web": {"size": "small"}, "aws_s3_bucket.logs": {"acl": "private"}},
         {"aws_s3_bucket.logs": {"acl": "private"}}, {}],
        [{"aws_instance.web": {"size": "medium"}}, {"aws_instance.web": {"size": "small"}},
         {"aws_instance.web": {"size": "large"}}, {}],
        [{"aws_autoscaling_group.web": {"desired_capacity": 2, "max_size": 6}},
         {"aws_autoscaling_group.web": {"desired_capacity": 2, "max_size": 6}},
         {"aws_autoscaling_group.web": {"desired_capacity": 5, "max_size": 8}},
         {"aws_autoscaling_group.web": ["desired_capacity"]}],
        [{"aws_autoscaling_group.web": {"desired_capacity": 3, "max_size": 9}},
         {"aws_autoscaling_group.web": {"desired_capacity": 2, "max_size": 6}},
         {"aws_autoscaling_group.web": {"desired_capacity": 2, "max_size": 6}},
         {"aws_autoscaling_group.web": ["desired_capacity"]}],
        [{"aws_instance.legacy": {"size": "small", "ami": "ami-1", "tags": {"Team": "web"}}},
         {"aws_instance.legacy": {"size": "small", "ami": "ami-1", "tags": {"Team": "web"}}},
         {"aws_instance.legacy": {"size": "large", "ami": "ami-9", "tags": {"Team": "web", "Owner": "ben"}}},
         {"aws_instance.legacy": ["all"]}],
        [{"aws_instance.web": {"size": "small"}}, {"aws_instance.web": {"size": "small"}},
         {"aws_instance.web": {"size": "small"}, "aws_instance.manual": {"size": "huge"}}, {}],
        [{"b.x": {"z": 1, "a": 1}, "a.x": {"k": 1}}, {"b.x": {"z": 1, "a": 1}, "a.x": {"k": 1}},
         {"b.x": {"z": 2, "a": 2}, "a.x": {"k": 2}}, {"a.x": ["other"], "c.x": ["all"]}],
        [{"aws_security_group.web": {"ingress": [443], "name": "web"}},
         {"aws_security_group.web": {"ingress": [443], "name": "web"}},
         {"aws_security_group.web": {"ingress": [443, 22], "name": "web"}}, {}],
        [{"r.gone": {"a": 1}}, {"r.gone": {"a": 1}}, {}, {"r.gone": ["all"]}],
        [{f"r.n{i:02d}": {"v": i % 4, "w": 0} for i in range(40)},
         {f"r.n{i:02d}": {"v": i % 3, "w": 0} for i in range(40)},
         {f"r.n{i:02d}": {"v": i % 2, "w": 0} for i in range(40) if i % 7},
         {f"r.n{i:02d}": ["v"] for i in range(0, 40, 5)}],
    ],
    examples=2,
    wrong_solutions=[
        '''def classifyDrift(config, state, actual, ignore_changes):
    rows = []
    for address in sorted(state):
        if address not in actual:
            rows.append([address, "", "deleted"]); continue
        for attr in sorted(state[address]):
            if actual[address][attr] != state[address][attr]:
                rows.append([address, attr, "drift-revert"])
            elif config[address][attr] != state[address][attr]:
                rows.append([address, attr, "pending"])
    return rows
''',
        '''def classifyDrift(config, state, actual, ignore_changes):
    rows = []
    for address in sorted(state):
        if address not in actual:
            rows.append([address, "", "deleted"]); continue
        for attr in sorted(state[address]):
            s, a, c = state[address][attr], actual[address][attr], config[address][attr]
            if a == s:
                if c != s:
                    rows.append([address, attr, "pending"])
            elif c == a:
                rows.append([address, attr, "drift-adopted"])
            elif c == s:
                rows.append([address, attr, "drift-revert"])
            else:
                rows.append([address, attr, "drift-overwrite"])
    return rows
''',
        '''def classifyDrift(config, state, actual, ignore_changes):
    rows = []
    for address in sorted(state):
        if address not in actual:
            rows.append([address, "", "deleted"]); continue
        ignored = ignore_changes.get(address, [])
        for attr in sorted(state[address]):
            s, a, c = state[address][attr], actual[address][attr], config[address][attr]
            skip = attr in ignored
            if a == s:
                if c != s and not skip:
                    rows.append([address, attr, "pending"])
            elif skip:
                rows.append([address, attr, "drift-ignored"])
            elif c == s:
                rows.append([address, attr, "drift-revert"])
            elif c == a:
                rows.append([address, attr, "drift-adopted"])
            else:
                rows.append([address, attr, "drift-overwrite"])
    return rows
''',
    ],
    guide=dict(
        prereqs="Drift, refresh and `ignore_changes` in *State surgery: moving, removing, importing and repairing* and *Interview essentials, part 1: state, plan and apply, count and for_each, drift and import*. Nested dicts.",
        intuition="State is a photograph taken after the last apply. Comparing reality with the photograph tells you *whether* something changed behind Terraform's back. Comparing the code with both tells you *what will happen next*: the code may still hold the old value (the manual change gets undone), may already hold the new value (nothing happens), or may hold a third value (the manual change is overwritten by something else).",
        hints=[
            "Handle a resource that has vanished from `actual` first, and skip its attributes.",
            "Ask the question 'did reality move?' (`a != s`) before any other. It splits the table in two.",
            "Work out once per attribute whether it is ignored: either listed by name or covered by `\"all\"`.",
        ],
        brute_force="Compare `state` with `actual` only and call every difference drift to be reverted (first wrong solution). That is what a quick script does, and it misreports every case where the code has also changed or the attribute is deliberately unmanaged.",
        approach="""For each address in sorted order, then each attribute in sorted order:

```
skip = "all" in ignored or attr in ignored
if a == s:
    pending if (c != s and not skip)
elif skip:        drift-ignored
elif c == a:      drift-adopted
elif c == s:      drift-revert
else:             drift-overwrite
```

**Dry run:** an auto scaling group whose `desired_capacity` is in `ignore_changes`.

| attribute | config | state | actual | reasoning | label |
|---|---|---|---|---|---|
| desired_capacity | 2 | 2 | 5 | moved, but ignored | drift-ignored |
| max_size | 6 | 6 | 8 | moved, code still says the old value | drift-revert |

The scaling policy changed the capacity, which is expected and left alone. Someone also raised the maximum by hand, and the next apply will put it back to 6.""",
        complexity="Time O(R log R + A log A) for R resources and A attributes in total, dominated by sorting. Space O(A) for the rows.",
        pitfalls="Ignoring the code's view (first wrong solution). Ignoring `ignore_changes` (second wrong solution), which turns every autoscaling event into a false alarm. Not supporting `all` (third wrong solution). Reporting attributes of a deleted resource. Treating unmanaged objects in `actual` as drift: Terraform cannot see what it does not manage.",
        follow_up="Turn each label into the command a reviewer would run: `terraform apply -refresh-only` to accept drift into state, a normal apply to revert, or a code change to adopt.",
    ),
),
]
