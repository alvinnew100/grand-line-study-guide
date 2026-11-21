PROBLEMS = [
dict(
    id="tf-plan-summary",
    title="Summarise a plan",
    difficulty="Easy",
    pattern="Plans",
    entry="planSummary",
    description=r"""
Terraform ends every plan with a one-line summary. Write `planSummary(actions)` that produces it.

`actions` is a list of strings, one per resource, each one of:
`"create"`, `"update"`, `"replace"`, `"delete"`, `"no-op"`.

Counting rules:

- `create` counts once under **add**.
- `update` counts once under **change**.
- `delete` counts once under **destroy**.
- `replace` counts once under **add** *and* once under **destroy** (the old object is destroyed and a new one created).
- `no-op` counts nowhere.

Return exactly `"Plan: A to add, C to change, D to destroy."`.
If all three numbers are zero (including an empty list), return
`"No changes. Your infrastructure matches the configuration."`.

**Example 1:** `["create", "update", "no-op"]` → `"Plan: 1 to add, 1 to change, 0 to destroy."`

**Example 2:** `["replace"]` → `"Plan: 1 to add, 0 to change, 1 to destroy."`
""",
    starter='''def planSummary(actions):
    pass
''',
    solution='''def planSummary(actions):
    add = change = destroy = 0
    for a in actions:
        if a == "create":
            add += 1
        elif a == "update":
            change += 1
        elif a == "delete":
            destroy += 1
        elif a == "replace":
            add += 1
            destroy += 1
    if add == change == destroy == 0:
        return "No changes. Your infrastructure matches the configuration."
    return f"Plan: {add} to add, {change} to change, {destroy} to destroy."
''',
    tests=[
        [["create", "update", "no-op"]],
        [["replace"]],
        [[]],
        [["no-op", "no-op"]],
        [["delete"]],
        [["create"] * 11],
        [["replace", "replace", "update"]],
        [["delete", "replace", "create", "update", "no-op", "update"]],
        [["update"] * 3],
        [["create", "delete"]],
        [["replace"] * 40 + ["no-op"] * 60],
        [["no-op", "replace", "no-op"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def planSummary(actions):
    add = actions.count("create") + actions.count("replace")
    change = actions.count("update")
    destroy = actions.count("delete")
    if add == change == destroy == 0:
        return "No changes. Your infrastructure matches the configuration."
    return f"Plan: {add} to add, {change} to change, {destroy} to destroy."
''',
        '''def planSummary(actions):
    add = actions.count("create")
    change = actions.count("update") + actions.count("replace")
    destroy = actions.count("delete")
    return f"Plan: {add} to add, {change} to change, {destroy} to destroy."
''',
    ],
    guide=dict(
        prereqs="Reading a plan: the lesson *How Terraform works, and how it compares with the alternatives*. Python loops and f-strings.",
        intuition="The summary is three counters. The only subtlety is that a replacement is two real operations, a destroy and a create, so it feeds two counters and never the *change* counter.",
        hints=[
            "Keep three integers and walk the list once.",
            "Which counters does `replace` touch? Think about what physically happens to the old and the new object.",
            "After the loop, check whether all three counters are zero before building the `Plan:` string.",
        ],
        brute_force="Call `list.count` once per action name: five passes over the list. Still O(n), but the single loop is clearer about `replace` contributing twice.",
        approach="""1. Start `add = change = destroy = 0`.
2. For each action: `create` → add; `update` → change; `delete` → destroy; `replace` → add **and** destroy; `no-op` → nothing.
3. If all are zero, return the "No changes" sentence; otherwise format the summary.

**Dry run** on `["delete", "replace", "create", "update", "no-op", "update"]`:

| action | add | change | destroy |
|---|---|---|---|
| delete | 0 | 0 | 1 |
| replace | 1 | 0 | 2 |
| create | 2 | 0 | 2 |
| update | 2 | 1 | 2 |
| no-op | 2 | 1 | 2 |
| update | 2 | 2 | 2 |

Result: `Plan: 2 to add, 2 to change, 2 to destroy.`""",
        complexity="Time O(n) for n actions, one pass. Space O(1): three counters.",
        pitfalls="Counting `replace` as a change. Forgetting the destroy half of a replacement, which hides data loss. Printing `Plan: 0 to add, 0 to change, 0 to destroy.` instead of the no-changes sentence. Missing the final full stop.",
        follow_up="Real Terraform adds a fourth number, `N to import`, when import blocks are present. Extend the function to accept an `import` action.",
    ),
),
dict(
    id="tf-compute-plan",
    title="Compute a plan from desired configuration and state",
    difficulty="Medium",
    pattern="Plans",
    entry="computePlan",
    description=r"""
Build the heart of `terraform plan`. Write `computePlan(desired, state, force_new)`.

- `desired` maps a resource address to its attributes as written in the configuration, e.g.
  `{"aws_instance.web": {"ami": "ami-2", "size": "small"}}`.
- `state` has the same shape and holds what Terraform recorded last time.
- `force_new` maps a **resource type** to a list of attribute names that cannot be changed in place.
  The resource type is the part of the address before the first dot (`aws_instance` for `aws_instance.web`).
  A type missing from `force_new` has no such attributes.

For every address that appears in `desired` or `state`, decide one action:

| Situation | Action |
|---|---|
| In `desired` only | `"create"` |
| In `state` only | `"delete"` |
| In both, all attributes equal | `"no-op"` |
| In both, at least one changed attribute is force-new for its type | `"replace"` |
| In both, something changed but nothing force-new | `"update"` |

An attribute counts as **changed** when its value differs between the two sides, or when it is present on
one side and absent on the other.

Return a list of `[address, action]` pairs sorted by address.

**Example:** desired `{"aws_instance.web": {"ami": "ami-2"}}`, state `{"aws_instance.web": {"ami": "ami-1"}, "aws_s3_bucket.logs": {"name": "l"}}`,
force_new `{"aws_instance": ["ami"]}` → `[["aws_instance.web", "replace"], ["aws_s3_bucket.logs", "delete"]]`
""",
    starter='''def computePlan(desired, state, force_new):
    pass
''',
    solution='''def computePlan(desired, state, force_new):
    plan = []
    for addr in sorted(set(desired) | set(state)):
        if addr not in state:
            plan.append([addr, "create"])
            continue
        if addr not in desired:
            plan.append([addr, "delete"])
            continue
        want, have = desired[addr], state[addr]
        missing = object()
        changed = [k for k in set(want) | set(have)
                   if want.get(k, missing) != have.get(k, missing)]
        if not changed:
            plan.append([addr, "no-op"])
            continue
        rtype = addr.split(".")[0]
        immutable = set(force_new.get(rtype, []))
        if any(k in immutable for k in changed):
            plan.append([addr, "replace"])
        else:
            plan.append([addr, "update"])
    return plan
''',
    tests=[
        [{"aws_instance.web": {"ami": "ami-2"}},
         {"aws_instance.web": {"ami": "ami-1"}, "aws_s3_bucket.logs": {"name": "l"}},
         {"aws_instance": ["ami"]}],
        [{"aws_instance.web": {"ami": "a", "size": "small"}}, {}, {}],
        [{}, {}, {}],
        [{}, {"aws_instance.web": {"ami": "a"}}, {"aws_instance": ["ami"]}],
        [{"aws_instance.web": {"ami": "a", "size": "large"}},
         {"aws_instance.web": {"ami": "a", "size": "small"}}, {"aws_instance": ["ami"]}],
        [{"aws_instance.web": {"ami": "a", "size": "small"}},
         {"aws_instance.web": {"ami": "a", "size": "small"}}, {"aws_instance": ["ami"]}],
        [{"aws_instance.web": {"ami": "a"}},
         {"aws_instance.web": {"ami": "a", "user_data": "x"}}, {"aws_instance": ["user_data"]}],
        [{"aws_instance.web": {"ami": "a", "tags": {"Team": "web"}}},
         {"aws_instance.web": {"ami": "a"}}, {"aws_instance": ["ami"]}],
        [{"aws_s3_bucket.b": {"name": "new"}, "aws_instance.b": {"name": "new"}},
         {"aws_s3_bucket.b": {"name": "old"}, "aws_instance.b": {"name": "old"}},
         {"aws_s3_bucket": ["name"]}],
        [{"aws_instance.web": {"ami": "b", "size": "large"}},
         {"aws_instance.web": {"ami": "a", "size": "small"}}, {"aws_instance": ["ami"]}],
        [{"z.z": {"a": 1}, "a.a": {"a": 1}, "m.m": {"a": 2}},
         {"m.m": {"a": 1}, "b.b": {"a": 1}}, {"m": []}],
        [{"aws_db_instance.db": {"encrypted": True, "class": "micro"}},
         {"aws_db_instance.db": {"encrypted": False, "class": "micro"}},
         {"aws_db_instance": ["encrypted"], "aws_instance": ["ami"]}],
        [{"aws_instance.web": {"count": None}}, {"aws_instance.web": {}}, {}],
        [{f"aws_instance.n{i:03d}": {"ami": "a" if i % 2 else "b"} for i in range(60)},
         {f"aws_instance.n{i:03d}": {"ami": "a"} for i in range(30, 90)},
         {"aws_instance": ["ami"]}],
    ],
    examples=2,
    wrong_solutions=[
        '''def computePlan(desired, state, force_new):
    plan = []
    for addr in sorted(set(desired) | set(state)):
        if addr not in state:
            plan.append([addr, "create"])
        elif addr not in desired:
            plan.append([addr, "delete"])
        else:
            want, have = desired[addr], state[addr]
            changed = [k for k in want if want[k] != have.get(k)]
            if not changed:
                plan.append([addr, "no-op"])
            elif set(changed) & set(force_new.get(addr.split(".")[0], [])):
                plan.append([addr, "replace"])
            else:
                plan.append([addr, "update"])
    return plan
''',
        '''def computePlan(desired, state, force_new):
    plan = []
    for addr in sorted(set(desired) | set(state)):
        if addr not in state:
            plan.append([addr, "create"])
        elif addr not in desired:
            plan.append([addr, "delete"])
        elif desired[addr] == state[addr]:
            plan.append([addr, "no-op"])
        else:
            plan.append([addr, "update"])
    return plan
''',
    ],
    guide=dict(
        prereqs="The plan table in *How Terraform works, and how it compares with the alternatives*. Python dicts and sets.",
        intuition="A plan is a diff between two dictionaries, taken twice: first over the set of addresses (who exists on which side), then, for addresses on both sides, over the set of attribute names. One extra question decides between update and replace: did any changed attribute belong to the type's force-new list?",
        hints=[
            "Take the union of the two key sets and sort it; handle 'only in desired' and 'only in state' first.",
            "For an address on both sides, collect the attribute names that differ. Remember an attribute can be missing on either side.",
            "Intersect the changed names with `force_new[type]`. Non-empty means replace.",
        ],
        brute_force="Compare every address in `desired` against every address in `state` with nested loops to find matches: O(n·m). Dictionary lookups make the match O(1) per address.",
        approach="""1. `addresses = sorted(set(desired) | set(state))`.
2. Not in state → `create`. Not in desired → `delete`.
3. Otherwise compute `changed`: for each key in the union of both attribute dicts, compare the two values, using a unique sentinel for "absent" so that a missing key differs even from `None`.
4. Empty `changed` → `no-op`. If `changed` intersects the type's force-new list → `replace`, else `update`.

**Dry run** with force_new `{"aws_instance": ["ami"]}`:

- `aws_instance.web`: desired `{ami: b, size: large}`, state `{ami: a, size: small}` → changed `{ami, size}`; `ami` is force-new → **replace**. One force-new attribute is enough, even if others could have been updated in place.
- `aws_s3_bucket.logs`: only in state → **delete**.""",
        complexity="Time O(R log R + A) where R is the number of addresses and A the total number of attributes; the sort dominates. Space O(R) for the result.",
        pitfalls="Iterating only over the desired attributes, which misses an attribute that was removed from the configuration. Using `dict.get(k)` on both sides, which treats a missing key and an explicit `None` as equal. Looking up `force_new` by full address instead of by type. Forgetting to sort.",
        follow_up="Real providers also have computed attributes that are unknown until apply. Extend the model with an `UNKNOWN` marker that never counts as a change.",
    ),
),
dict(
    id="tf-plan-review",
    title="Flag destructive actions in a plan",
    difficulty="Easy",
    pattern="Plans",
    entry="reviewPlan",
    description=r"""
A reviewer's first job is to find every line of a plan that destroys something. Write
`reviewPlan(changes, protected_types)`.

`changes` is a list of dicts shaped like entries of Terraform's plan JSON:

```
{"address": "aws_db_instance.orders", "type": "aws_db_instance", "actions": ["delete", "create"]}
```

`actions` is one of `["create"]`, `["update"]`, `["delete"]`, `["no-op"]`, `["delete", "create"]`
(replace, destroy first) or `["create", "delete"]` (replace, create first).

`protected_types` is a list of resource types that hold data (databases, buckets, disks).

Produce one flag for every change whose actions include `"delete"`:

- `"REPLACE <address>"` if the actions also include `"create"`, otherwise `"DESTROY <address>"`;
- append `" [PROTECTED]"` if the change's `type` is in `protected_types`.

Return the flags with all protected ones first, and within each group sorted by address.

**Example:** the change above with `protected_types = ["aws_db_instance"]` → `["REPLACE aws_db_instance.orders [PROTECTED]"]`
""",
    starter='''def reviewPlan(changes, protected_types):
    pass
''',
    solution='''def reviewPlan(changes, protected_types):
    protected = set(protected_types)
    rows = []
    for c in changes:
        actions = c["actions"]
        if "delete" not in actions:
            continue
        kind = "REPLACE" if "create" in actions else "DESTROY"
        is_protected = c["type"] in protected
        text = f"{kind} {c['address']}" + (" [PROTECTED]" if is_protected else "")
        rows.append((0 if is_protected else 1, c["address"], text))
    rows.sort()
    return [r[2] for r in rows]
''',
    tests=[
        [[{"address": "aws_db_instance.orders", "type": "aws_db_instance", "actions": ["delete", "create"]}],
         ["aws_db_instance"]],
        [[{"address": "aws_instance.web", "type": "aws_instance", "actions": ["update"]},
          {"address": "aws_instance.old", "type": "aws_instance", "actions": ["delete"]}], []],
        [[], ["aws_db_instance"]],
        [[{"address": "aws_lb.web", "type": "aws_lb", "actions": ["create"]},
          {"address": "aws_lb.api", "type": "aws_lb", "actions": ["no-op"]}], ["aws_lb"]],
        [[{"address": "aws_launch_template.web", "type": "aws_launch_template", "actions": ["create", "delete"]}], []],
        [[{"address": "b.x", "type": "b", "actions": ["delete"]},
          {"address": "a.x", "type": "a", "actions": ["delete"]},
          {"address": "c.x", "type": "c", "actions": ["delete", "create"]}], ["c"]],
        [[{"address": "aws_s3_bucket.z", "type": "aws_s3_bucket", "actions": ["delete"]},
          {"address": "aws_s3_bucket.a", "type": "aws_s3_bucket", "actions": ["create", "delete"]},
          {"address": "aws_instance.a", "type": "aws_instance", "actions": ["delete"]}],
         ["aws_s3_bucket", "aws_db_instance"]],
        [[{"address": "aws_db_instance.a", "type": "aws_db_instance", "actions": ["update"]}], ["aws_db_instance"]],
        [[{"address": "module.db.aws_db_instance.this", "type": "aws_db_instance", "actions": ["delete"]},
          {"address": "aws_ebs_volume.data[0]", "type": "aws_ebs_volume", "actions": ["delete", "create"]},
          {"address": "aws_iam_user.staff[\"ben\"]", "type": "aws_iam_user", "actions": ["delete"]}],
         ["aws_ebs_volume", "aws_db_instance"]],
        [[{"address": f"aws_instance.n{i}", "type": "aws_instance", "actions": ["delete"] if i % 3 == 0 else ["update"]}
          for i in range(30)], ["aws_instance"]],
        [[{"address": "x.b", "type": "x", "actions": ["create"]},
          {"address": "x.a", "type": "x", "actions": ["create", "delete"]}], ["y"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def reviewPlan(changes, protected_types):
    out = []
    for c in sorted(changes, key=lambda c: c["address"]):
        if c["actions"] == ["delete"]:
            out.append("DESTROY " + c["address"] + (" [PROTECTED]" if c["type"] in protected_types else ""))
    return out
''',
        '''def reviewPlan(changes, protected_types):
    out = []
    for c in changes:
        if "delete" in c["actions"]:
            kind = "REPLACE" if "create" in c["actions"] else "DESTROY"
            out.append(kind + " " + c["address"] + (" [PROTECTED]" if c["type"] in protected_types else ""))
    return sorted(out)
''',
    ],
    guide=dict(
        prereqs="Plan JSON and `resource_changes` from *Testing, part 1: manual tests, static analysis, policy and plan testing*.",
        intuition="Every destructive change has `delete` somewhere in its action list. A replacement is a delete that happens to come with a create, and it destroys data exactly like a plain delete does.",
        hints=[
            "Filter first: keep only the changes whose actions contain `delete`.",
            "Both `[\"delete\", \"create\"]` and `[\"create\", \"delete\"]` are replacements.",
            "Sort by a pair: (not protected, address). Sorting the finished strings would order by the words DESTROY and REPLACE instead.",
        ],
        brute_force="Build one list for protected flags and another for the others, sort each by address, and concatenate. Equivalent in cost; a tuple sort key does it in one pass.",
        approach="""For each change with `delete` in its actions, compute `kind` (REPLACE when `create` is also present), whether the type is protected, and the text. Collect `(0 or 1, address, text)` and sort.

**Dry run:** changes `b.x` delete, `a.x` delete, `c.x` replace, with `c` protected.

| tuple | text |
|---|---|
| (1, "b.x") | DESTROY b.x |
| (1, "a.x") | DESTROY a.x |
| (0, "c.x") | REPLACE c.x [PROTECTED] |

Sorted: `REPLACE c.x [PROTECTED]`, `DESTROY a.x`, `DESTROY b.x`.""",
        complexity="Time O(n log n) for the sort over n changes; space O(n).",
        pitfalls="Testing `actions == [\"delete\"]`, which lets replacements through unflagged: the most dangerous omission. Sorting the output strings, which groups by kind instead of by protection. Treating `update` on a protected type as destructive.",
        follow_up="Add a threshold: return an extra line `TOO MANY DELETIONS` when more than k resources are destroyed in one plan.",
    ),
),
dict(
    id="tf-policy-check",
    title="Check a plan against policy rules",
    difficulty="Medium",
    pattern="Testing & Policy",
    entry="checkPolicy",
    description=r"""
Policy-as-code tools read the plan JSON and fail the pipeline when a rule is broken. Write
`checkPolicy(changes, rules)`.

Each change is a dict: `{"address", "type", "actions", "after"}`. `after` is a dict of the resource's
planned attributes, or `None` for a pure delete.

**Which changes are checked.** Only changes whose `actions` include `"create"` or `"update"`.
Changes that are exactly `["no-op"]` or exactly `["delete"]` are skipped: existing, untouched
resources are not this plan's responsibility.

`rules` is a dict with three keys:

1. `"required_tags"`: a list of tag names. For every checked change and every listed tag (in the listed
   order), if `after.get("tags", {})` lacks the tag or maps it to an empty string, report
   `"<address>: missing tag <tag>"`.
2. `"allowed_instance_types"`: a list. For a checked change of type `aws_instance` whose
   `after["instance_type"]` is present and not in the list, report
   `"<address>: instance type <value> not allowed"`. An empty list means the rule is off.
3. `"forbid_public_buckets"`: a bool. When true, for a checked change of type `aws_s3_bucket` whose
   `after.get("acl")` is `"public-read"` or `"public-read-write"`, report `"<address>: public bucket"`.

Return all violation strings sorted alphabetically.

**Example:** creating `aws_instance.batch` with `{"instance_type": "m5.24xlarge", "tags": {}}` under rules
`{"required_tags": ["Team"], "allowed_instance_types": ["t3.micro"], "forbid_public_buckets": true}` →
`["aws_instance.batch: instance type m5.24xlarge not allowed", "aws_instance.batch: missing tag Team"]`
""",
    starter='''def checkPolicy(changes, rules):
    pass
''',
    solution='''def checkPolicy(changes, rules):
    required = rules.get("required_tags", [])
    allowed = rules.get("allowed_instance_types", [])
    forbid_public = rules.get("forbid_public_buckets", False)
    out = []
    for c in changes:
        actions = c["actions"]
        if "create" not in actions and "update" not in actions:
            continue
        after = c.get("after") or {}
        addr = c["address"]
        tags = after.get("tags") or {}
        for tag in required:
            if not tags.get(tag):
                out.append(f"{addr}: missing tag {tag}")
        if c["type"] == "aws_instance" and allowed:
            size = after.get("instance_type")
            if size is not None and size not in allowed:
                out.append(f"{addr}: instance type {size} not allowed")
        if forbid_public and c["type"] == "aws_s3_bucket":
            if after.get("acl") in ("public-read", "public-read-write"):
                out.append(f"{addr}: public bucket")
    return sorted(out)
''',
    tests=[
        [[{"address": "aws_instance.batch", "type": "aws_instance", "actions": ["create"],
           "after": {"instance_type": "m5.24xlarge", "tags": {}}}],
         {"required_tags": ["Team"], "allowed_instance_types": ["t3.micro"], "forbid_public_buckets": True}],
        [[{"address": "aws_s3_bucket.assets", "type": "aws_s3_bucket", "actions": ["create"],
           "after": {"acl": "public-read", "tags": {"Team": "web"}}}],
         {"required_tags": ["Team"], "allowed_instance_types": [], "forbid_public_buckets": True}],
        [[], {"required_tags": ["Team"], "allowed_instance_types": [], "forbid_public_buckets": True}],
        [[{"address": "aws_instance.old", "type": "aws_instance", "actions": ["no-op"],
           "after": {"instance_type": "m5.24xlarge", "tags": {}}},
          {"address": "aws_s3_bucket.gone", "type": "aws_s3_bucket", "actions": ["delete"], "after": None}],
         {"required_tags": ["Team"], "allowed_instance_types": ["t3.micro"], "forbid_public_buckets": True}],
        [[{"address": "aws_instance.web", "type": "aws_instance", "actions": ["update"],
           "after": {"instance_type": "t3.micro", "tags": {"Team": "web", "Env": ""}}}],
         {"required_tags": ["Team", "Env"], "allowed_instance_types": ["t3.micro"], "forbid_public_buckets": False}],
        [[{"address": "aws_s3_bucket.assets", "type": "aws_s3_bucket", "actions": ["create"],
           "after": {"acl": "public-read-write", "tags": {"Team": "web"}}}],
         {"required_tags": [], "allowed_instance_types": [], "forbid_public_buckets": False}],
        [[{"address": "aws_db_instance.db", "type": "aws_db_instance", "actions": ["delete", "create"],
           "after": {"instance_type": "huge"}}],
         {"required_tags": ["Team", "CostCentre"], "allowed_instance_types": ["t3.micro"], "forbid_public_buckets": True}],
        [[{"address": "aws_instance.a", "type": "aws_instance", "actions": ["create"],
           "after": {"tags": {"Team": "x"}}}],
         {"required_tags": ["Team"], "allowed_instance_types": ["t3.micro"], "forbid_public_buckets": True}],
        [[{"address": "aws_instance.z", "type": "aws_instance", "actions": ["create"],
           "after": {"instance_type": "c5.large", "tags": {"Team": "x"}}},
          {"address": "aws_instance.a", "type": "aws_instance", "actions": ["create", "delete"],
           "after": {"instance_type": "c5.large", "tags": None}}],
         {"required_tags": ["Team"], "allowed_instance_types": ["t3.micro", "t3.small"], "forbid_public_buckets": True}],
        [[{"address": "aws_s3_bucket.logs", "type": "aws_s3_bucket", "actions": ["update"],
           "after": {"acl": "private", "tags": {"Team": "ops"}}},
          {"address": "aws_s3_bucket.site", "type": "aws_s3_bucket", "actions": ["update"],
           "after": {"tags": {"Team": "web"}}}],
         {"required_tags": ["Team"], "allowed_instance_types": [], "forbid_public_buckets": True}],
        [[{"address": "aws_instance.x", "type": "aws_instance", "actions": ["create"],
           "after": {"instance_type": "x1.32xlarge", "tags": {"Team": "ml"}}}],
         {"required_tags": ["Team"], "allowed_instance_types": [], "forbid_public_buckets": True}],
        [[{"address": f"aws_instance.n{i:02d}", "type": "aws_instance",
           "actions": ["create"] if i % 2 else ["no-op"],
           "after": {"instance_type": "t3.micro" if i % 3 else "m5.large", "tags": {"Team": "a"} if i % 5 else {}}}
          for i in range(20)],
         {"required_tags": ["Team"], "allowed_instance_types": ["t3.micro"], "forbid_public_buckets": True}],
    ],
    examples=2,
    wrong_solutions=[
        '''def checkPolicy(changes, rules):
    out = []
    for c in changes:
        after = c.get("after") or {}
        addr = c["address"]
        tags = after.get("tags") or {}
        for tag in rules.get("required_tags", []):
            if not tags.get(tag):
                out.append(f"{addr}: missing tag {tag}")
        allowed = rules.get("allowed_instance_types", [])
        if c["type"] == "aws_instance" and allowed:
            size = after.get("instance_type")
            if size is not None and size not in allowed:
                out.append(f"{addr}: instance type {size} not allowed")
        if rules.get("forbid_public_buckets") and c["type"] == "aws_s3_bucket":
            if after.get("acl") in ("public-read", "public-read-write"):
                out.append(f"{addr}: public bucket")
    return sorted(out)
''',
        '''def checkPolicy(changes, rules):
    out = []
    for c in changes:
        if "create" not in c["actions"] and "update" not in c["actions"]:
            continue
        after = c.get("after") or {}
        addr = c["address"]
        tags = after.get("tags") or {}
        for tag in rules.get("required_tags", []):
            if tag not in tags:
                out.append(f"{addr}: missing tag {tag}")
        if c["type"] == "aws_instance":
            size = after.get("instance_type")
            if size is not None and size not in rules.get("allowed_instance_types", []):
                out.append(f"{addr}: instance type {size} not allowed")
        if rules.get("forbid_public_buckets") and c["type"] == "aws_s3_bucket":
            if after.get("acl") == "public-read":
                out.append(f"{addr}: public bucket")
    return sorted(out)
''',
    ],
    guide=dict(
        prereqs="Policy as code and the plan JSON in *Testing, part 1: manual tests, static analysis, policy and plan testing*.",
        intuition="A policy engine is a loop over `resource_changes` that applies each rule to the resources the plan is about to create or modify, and collects messages. Deciding *which resources are in scope* matters as much as the rules themselves.",
        hints=[
            "Start with the scope filter: is `create` or `update` in the actions?",
            "`after` may be `None`, and `tags` may be missing or `None`. Normalise both to empty dicts before checking.",
            "An empty tag value is as bad as a missing tag; an empty allowed list switches the instance rule off; two ACL values count as public.",
        ],
        brute_force="Run three separate passes over the changes, one per rule, and concatenate. Same O(n) cost; one pass keeps the scope filter in a single place.",
        approach="""For each change:

1. Skip unless `create` or `update` is among the actions. Replacements pass, because they contain `create`.
2. `after = change["after"] or {}` and `tags = after.get("tags") or {}`.
3. For each required tag: `if not tags.get(tag)` → message. This catches both absent and empty.
4. Instance rule: only type `aws_instance`, only when the allowed list is non-empty and the attribute exists.
5. Bucket rule: only when the flag is true.

Sort the collected messages.

**Dry run:** a `no-op` instance with a huge type and no tags, plus a deleted bucket → both skipped → `[]`. That is the correct result: the plan does not touch them.""",
        complexity="Time O(n·t + v log v) for n changes, t required tags and v violations; space O(v).",
        pitfalls="Checking `no-op` resources, which makes every unrelated pull request fail on old debt. Crashing on `after = None`. Using `tag not in tags`, which accepts an empty value. Applying the instance rule when the allowed list is empty. Forgetting `public-read-write`.",
        follow_up="Add a rule that forbids deleting resources of protected types, and a way to exempt a specific address with a recorded reason.",
    ),
),
dict(
    id="tf-cost-estimate",
    title="Estimate the cost change of a plan",
    difficulty="Medium",
    pattern="Plans",
    entry="costDelta",
    description=r"""
Cost tools read a plan and a price list and report how the monthly bill will move. Write
`costDelta(changes, prices)`.

Each change is a dict `{"type", "actions", "before", "after"}` where `before` and `after` are the
resource's **size** (a string such as `"t3.micro"`) or `None`.

`prices` maps `"<type>:<size>"` to a whole-number monthly price, for example
`{"aws_instance:t3.micro": 8}`. A type with no meaningful size uses an empty size: `"aws_lb:"`.
When `before` or `after` is `None` the size is the empty string for lookup purposes.
A key missing from `prices` costs `0`.

Rules per change:

- `["create"]`: the plan **adds** the price of `after`.
- `["delete"]`: the plan **removes** the price of `before`.
- `["update"]`, and both replacement orders: it removes the price of `before` and adds the price of `after`.
- `["no-op"]`: nothing.

Return `[added, removed, net]` where `added` and `removed` are the two totals and `net = added - removed`.

**Example:** one instance updated from `t3.micro` (8) to `t3.large` (60) and one load balancer created (18)
→ `[78, 8, 70]`
""",
    starter='''def costDelta(changes, prices):
    pass
''',
    solution='''def costDelta(changes, prices):
    def price(rtype, size):
        return prices.get(f"{rtype}:{size or ''}", 0)

    added = removed = 0
    for c in changes:
        actions = c["actions"]
        if actions == ["no-op"]:
            continue
        creates = "create" in actions or "update" in actions
        removes = "delete" in actions or "update" in actions
        if creates:
            added += price(c["type"], c.get("after"))
        if removes:
            removed += price(c["type"], c.get("before"))
    return [added, removed, added - removed]
''',
    tests=[
        [[{"type": "aws_instance", "actions": ["update"], "before": "t3.micro", "after": "t3.large"},
          {"type": "aws_lb", "actions": ["create"], "before": None, "after": None}],
         {"aws_instance:t3.micro": 8, "aws_instance:t3.large": 60, "aws_lb:": 18}],
        [[{"type": "aws_instance", "actions": ["delete"], "before": "t3.large", "after": None}],
         {"aws_instance:t3.large": 60}],
        [[], {"aws_instance:t3.large": 60}],
        [[{"type": "aws_instance", "actions": ["no-op"], "before": "t3.large", "after": "t3.large"}],
         {"aws_instance:t3.large": 60}],
        [[{"type": "aws_db_instance", "actions": ["delete", "create"], "before": "db.t4g.micro", "after": "db.r6g.large"}],
         {"aws_db_instance:db.t4g.micro": 13, "aws_db_instance:db.r6g.large": 165}],
        [[{"type": "aws_db_instance", "actions": ["create", "delete"], "before": "db.r6g.large", "after": "db.t4g.micro"}],
         {"aws_db_instance:db.t4g.micro": 13, "aws_db_instance:db.r6g.large": 165}],
        [[{"type": "aws_instance", "actions": ["create"], "before": None, "after": "x9.unknown"}],
         {"aws_instance:t3.micro": 8}],
        [[{"type": "aws_instance", "actions": ["update"], "before": "t3.micro", "after": "t3.micro"}],
         {"aws_instance:t3.micro": 8}],
        [[{"type": "aws_nat_gateway", "actions": ["create"], "before": None, "after": None},
          {"type": "aws_nat_gateway", "actions": ["create"], "before": None, "after": None},
          {"type": "aws_nat_gateway", "actions": ["delete"], "before": None, "after": None}],
         {"aws_nat_gateway:": 33}],
        [[{"type": "aws_instance", "actions": ["create"], "before": None, "after": "t3.micro"},
          {"type": "aws_db_instance", "actions": ["create"], "before": None, "after": "t3.micro"}],
         {"aws_instance:t3.micro": 8}],
        [[{"type": "aws_instance", "actions": ["update"], "before": "t3.large", "after": "t3.micro"}] * 5,
         {"aws_instance:t3.micro": 8, "aws_instance:t3.large": 60}],
        [[{"type": "aws_instance", "actions": ["create"] if i % 2 else ["delete"],
           "before": None if i % 2 else "t3.small", "after": "t3.small" if i % 2 else None}
          for i in range(41)],
         {"aws_instance:t3.small": 15}],
    ],
    examples=2,
    wrong_solutions=[
        '''def costDelta(changes, prices):
    added = removed = 0
    for c in changes:
        a = c["actions"]
        if "create" in a:
            added += prices.get(f"{c['type']}:{c.get('after') or ''}", 0)
        if "delete" in a:
            removed += prices.get(f"{c['type']}:{c.get('before') or ''}", 0)
    return [added, removed, added - removed]
''',
        '''def costDelta(changes, prices):
    added = removed = 0
    for c in changes:
        if c["actions"] == ["no-op"]:
            continue
        added += prices.get(f"{c['type']}:{c.get('after') or ''}", 0)
        removed += prices.get(f"{c['type']}:{c.get('before') or ''}", 0)
    return [added, removed, added - removed]
''',
    ],
    guide=dict(
        prereqs="Plan actions, and the review summary in *Terraform as a team, part 2: golden rules and a CI/CD pipeline*.",
        intuition="Think of each change as moving money between two piles: what the plan starts paying for and what it stops paying for. An in-place resize does both, exactly like a replacement, even though no resource is destroyed.",
        hints=[
            "Write a small `price(type, size)` helper that builds the key and defaults to 0.",
            "Decide two booleans per change: does it add the `after` price? does it remove the `before` price?",
            "`update` is true for both. `create` only adds, `delete` only removes.",
        ],
        brute_force="There is nothing slower that is natural here; the straightforward loop is already linear. The risk is in the case analysis, not the speed.",
        approach="""For each change that is not `no-op`:

- `adds = "create" in actions or "update" in actions`
- `removes = "delete" in actions or "update" in actions`

Add `price(type, after)` when `adds`, add `price(type, before)` to the removed total when `removes`.

**Dry run** with prices micro = 8, large = 60, load balancer = 18:

| change | added | removed |
|---|---|---|
| instance update micro → large | 60 | 8 |
| load balancer create (size None → key `aws_lb:`) | 78 | 8 |

Result `[78, 8, 70]`.""",
        complexity="Time O(n), one dictionary lookup or two per change. Space O(1).",
        pitfalls="Ignoring `update`, which hides the most common source of cost growth: resizing. Charging the `before` price on a pure create with a `None` size when a sizeless price such as `aws_lb:` exists. Looking up a size under the wrong resource type. Treating an unknown price as an error instead of zero.",
        follow_up="Return the three most expensive individual changes so a reviewer sees where the money goes.",
    ),
),
dict(
    id="tf-blast-radius",
    title="Rank changes by blast radius",
    difficulty="Hard",
    pattern="Dependency Graph",
    entry="blastRadius",
    description=r"""
The **blast radius** of a change is everything that could be affected if it goes wrong. For one resource,
define it as the resource itself plus every resource that depends on it, directly or through a chain.

Write `blastRadius(depends_on, changed)`.

- `depends_on` maps each resource address to the list of addresses it depends on. Every resource in the
  system appears as a key (possibly with an empty list). Dependencies on addresses that are not keys are ignored.
  The graph has no cycles.
- `changed` is a list of addresses being modified by a plan (all are keys of `depends_on`, no duplicates).

For each changed address compute the size of its blast radius. Return a list of `[address, size]` pairs
ordered by size descending, ties broken by address ascending.

**Example:** `{"vpc": [], "subnet": ["vpc"], "db": ["subnet"], "app": ["subnet", "db"], "dns": []}` with
`changed = ["db", "vpc", "dns"]` → `[["vpc", 4], ["db", 2], ["dns", 1]]`.
Changing the VPC can affect the subnet, the database and the app as well as itself.
""",
    starter='''def blastRadius(depends_on, changed):
    pass
''',
    solution='''def blastRadius(depends_on, changed):
    dependents = {addr: [] for addr in depends_on}
    for addr, deps in depends_on.items():
        for d in deps:
            if d in dependents and d != addr:
                dependents[d].append(addr)

    def radius(start):
        seen = {start}
        stack = [start]
        while stack:
            node = stack.pop()
            for nxt in dependents[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return len(seen)

    rows = [[addr, radius(addr)] for addr in changed]
    rows.sort(key=lambda r: (-r[1], r[0]))
    return rows
''',
    tests=[
        [{"vpc": [], "subnet": ["vpc"], "db": ["subnet"], "app": ["subnet", "db"], "dns": []}, ["db", "vpc", "dns"]],
        [{"a": [], "b": ["a"], "c": ["b"]}, ["c", "b", "a"]],
        [{"a": []}, ["a"]],
        [{"a": [], "b": []}, []],
        [{"a": ["ghost"], "b": ["a", "ghost"]}, ["a", "b"]],
        [{"root": [], "l": ["root"], "r": ["root"], "leaf": ["l", "r"]}, ["root", "l", "r", "leaf"]],
        [{"x": [], "y": [], "z": []}, ["z", "x", "y"]],
        [{"net": [], "sg": ["net"], "alb": ["net", "sg"], "asg": ["sg", "alb"], "dns": ["alb"], "alarm": ["asg"]},
         ["sg", "alb", "dns", "net"]],
        [{"a": [], "b": ["a"], "c": ["a"], "d": ["a"], "e": ["b", "c", "d"]}, ["b", "c", "a"]],
        [{"shared": [], **{f"svc{i}": ["shared"] for i in range(25)}}, ["shared", "svc3", "svc10"]],
        [{f"n{i:03d}": ([f"n{i-1:03d}"] if i else []) for i in range(300)}, ["n000", "n150", "n299"]],
        [{"a": [], "b": ["a"], "c": ["a", "b"], "d": ["c"], "e": ["c"], "f": ["e", "d"]}, ["c", "b", "e", "d"]],
    ],
    examples=2,
    wrong_solutions=[
        '''def blastRadius(depends_on, changed):
    rows = []
    for addr in changed:
        direct = [a for a, deps in depends_on.items() if addr in deps]
        rows.append([addr, 1 + len(direct)])
    rows.sort(key=lambda r: (-r[1], r[0]))
    return rows
''',
        '''def blastRadius(depends_on, changed):
    def count(addr):
        total = 1
        for a, deps in depends_on.items():
            if addr in deps:
                total += count(a)
        return total
    rows = [[a, count(a)] for a in changed]
    rows.sort(key=lambda r: (-r[1], r[0]))
    return rows
''',
    ],
    guide=dict(
        prereqs="The dependency graph in *Variables, outputs, references and a configurable web server*; blast radius in *Isolating state: workspaces, file layout and reading another state*. Graph traversal (depth-first or breadth-first search).",
        intuition="`depends_on` points from a resource to what it needs. Damage flows the other way: from a resource to whatever needs *it*. Reverse the arrows once, then the blast radius of a node is the number of nodes reachable from it.",
        hints=[
            "Build a reversed adjacency list: for each `a` depending on `b`, record that `a` is a dependent of `b`.",
            "From each changed address, traverse the reversed graph with a `seen` set. The answer is the size of the set.",
            "A diamond (two paths to the same node) must be counted once. That is what the `seen` set guarantees.",
        ],
        brute_force="For each changed address, scan the whole `depends_on` dict to find direct dependents, then scan again for each of those, and so on: O(V·E) per start. Precomputing the reversed graph makes each traversal O(V + E).",
        approach="""1. `dependents[b]` = list of addresses that list `b` among their dependencies (ignoring unknown addresses).
2. For each changed address run an iterative depth-first search over `dependents`, keeping a `seen` set that starts with the address itself.
3. Sort by `(-size, address)`.

**Dry run** on the example. Reversed graph: `vpc → [subnet]`, `subnet → [db, app]`, `db → [app]`.

- `vpc`: seen grows `{vpc}` → `{vpc, subnet}` → `{vpc, subnet, db, app}`; `app` is reached twice but counted once → 4.
- `db`: `{db, app}` → 2.
- `dns`: nothing depends on it → 1.

Sorted: `[["vpc", 4], ["db", 2], ["dns", 1]]`.""",
        complexity="Time O(V + E) to reverse, then O(V + E) per changed address: O(k·(V + E)) for k changes, plus O(k log k) to sort. Space O(V + E).",
        pitfalls="Counting only direct dependents. Recursively summing counts without a visited set, which double-counts diamonds (the second wrong solution). Traversing in the dependency direction, which measures what a resource needs instead of what it can break. Deep recursion on a long chain.",
        follow_up="Weight each resource (a database counts 10, a tag change 1) and rank by total weight. This is how some review tools decide which pull requests need a second approver.",
    ),
),
]
