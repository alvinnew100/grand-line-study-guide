_ADMIN = {"Sid": "Admin", "Effect": "Allow", "Action": ["*"], "Resource": ["*"]}
_READ_REPORTS = {"Sid": "Read", "Effect": "Allow", "Action": ["s3:Get*", "s3:List*"],
                 "Resource": ["arn:aws:s3:::reports", "arn:aws:s3:::reports/*"]}
_DENY_SECRET = {"Sid": "NoSecret", "Effect": "Deny", "Action": ["s3:*"], "Resource": ["arn:aws:s3:::reports/secret/*"]}
_MFA_DELETE = {"Sid": "MfaDelete", "Effect": "Allow", "Action": ["s3:DeleteObject"], "Resource": ["*"],
               "Condition": {"StringEquals": {"aws:MultiFactorAuthPresent": "true"}}}
_DENY_OUTSIDE_EU = {"Sid": "EuOnly", "Effect": "Deny", "Action": ["*"], "Resource": ["*"],
                    "Condition": {"StringNotEquals": {"aws:RequestedRegion": "eu-west-1"}}}
_BUCKET_ALLOW_ANA = {"Sid": "Bkt", "Effect": "Allow", "Principal": ["arn:aws:iam::111122223333:user/ana"],
                     "Action": ["s3:PutObject"], "Resource": ["arn:aws:s3:::uploads/*"]}
_SCP_ALL = [{"Effect": "Allow", "Action": ["*"], "Resource": ["*"]}]
_SCP_S3_ONLY = [{"Effect": "Allow", "Action": ["s3:*"], "Resource": ["*"]}]
_SCP_DENY_DELETE = [{"Effect": "Allow", "Action": ["*"], "Resource": ["*"]},
                    {"Effect": "Deny", "Action": ["s3:Delete*"], "Resource": ["*"]}]


def _req(action, resource, ctx=None, principal="arn:aws:iam::111122223333:user/ana"):
    return {"principal": principal, "action": action, "resource": resource, "context": ctx or {}}


PROBLEMS = [
dict(
    id="aws-tag-compliance",
    title="Tag Compliance Audit",
    difficulty="Easy",
    pattern="Governance",
    entry="tagAudit",
    description=r"""
Companies attach **tags** (key/value labels such as `Environment=prod`) to every AWS resource so that the
bill can be split by team and so that automation can find resources. An audit checks each resource
against a tagging standard.

Write `tagAudit(resources, required)`:

- `resources`: list of `{"id": str, "tags": {key: value}}`.
- `required`: dict mapping a required tag key to a list of allowed values. An **empty list** means
  "any non-blank value is acceptable".
- Tag keys and values are **case-sensitive** (as they are on AWS): `environment` does not satisfy `Environment`.
- For each resource collect problems:
  - `"missing:<Key>"` when the key is absent;
  - `"invalid:<Key>"` when the key is present but its value is blank (empty or only spaces), or is not
    in the non-empty allowed list.
- Return a list of `[id, problems]` for the non-compliant resources only, sorted by `id`, with each
  `problems` list sorted alphabetically. Compliant resources are left out.

**Example:** `resources=[{"id":"i-1","tags":{"Environment":"prod"}}]`,
`required={"Environment":["prod","dev"],"Owner":[]}` → `[["i-1", ["missing:Owner"]]]`
""",
    starter='''def tagAudit(resources, required):
    pass
''',
    solution='''def tagAudit(resources, required):
    out = []
    for r in resources:
        tags = r.get("tags") or {}
        problems = []
        for key, allowed in required.items():
            if key not in tags:
                problems.append("missing:" + key)
            else:
                v = tags[key]
                if v.strip() == "" or (allowed and v not in allowed):
                    problems.append("invalid:" + key)
        if problems:
            out.append([r["id"], sorted(problems)])
    out.sort(key=lambda x: x[0])
    return out
''',
    tests=[
        [[{"id": "i-1", "tags": {"Environment": "prod"}}], {"Environment": ["prod", "dev"], "Owner": []}],
        [[{"id": "i-2", "tags": {"Environment": "prod", "Owner": "data"}}], {"Environment": ["prod", "dev"], "Owner": []}],
        [[{"id": "vol-9", "tags": {"environment": "prod", "Owner": " "}}, {"id": "i-3", "tags": {}}],
         {"Environment": ["prod", "dev"], "Owner": []}],
        [[], {"Owner": []}],
        [[{"id": "b-1", "tags": {"Environment": "Prod", "Owner": "x"}}], {"Environment": ["prod"], "Owner": []}],
        [[{"id": "b-2", "tags": {"CostCenter": "42"}}, {"id": "b-1", "tags": {"CostCenter": "7"}}], {"CostCenter": ["42"]}],
        [[{"id": "x", "tags": {"A": "1", "B": "2"}}], {}],
        [[{"id": "z", "tags": {"Owner": ""}}, {"id": "a", "tags": {"Owner": "ops", "Extra": "y"}}], {"Owner": []}],
        [[{"id": "db-1", "tags": {"Tier": "gold", "Zeta": "1"}}], {"Zeta": ["2"], "Tier": ["silver"], "Alpha": []}],
        [[{"id": "r%03d" % i, "tags": ({"Owner": "t"} if i % 3 else {})} for i in range(60)], {"Owner": []}],
    ],
    examples=2,
    wrong_solutions=[
        '''def tagAudit(resources, required):
    out = []
    for r in resources:
        tags = {k.lower(): v for k, v in r["tags"].items()}
        problems = []
        for key, allowed in required.items():
            if key.lower() not in tags:
                problems.append("missing:" + key)
            elif tags[key.lower()].strip() == "" or (allowed and tags[key.lower()] not in allowed):
                problems.append("invalid:" + key)
        if problems:
            out.append([r["id"], sorted(problems)])
    return sorted(out)
''',
        '''def tagAudit(resources, required):
    out = []
    for r in resources:
        problems = ["missing:" + k for k in required if k not in r["tags"]]
        if problems:
            out.append([r["id"], sorted(problems)])
    return sorted(out)
''',
    ],
    guide=dict(
        prereqs="Dictionaries and sorting. Tags are introduced in the account and billing lesson.",
        intuition="Loop over the standard, not over the resource's tags: for every required key ask two questions in order — is it there, and is its value acceptable?",
        hints=["Handle one resource at a time and build its list of problems.",
               "`value.strip() == ''` detects blank values; an empty allowed list means skip the membership check.",
               "Only append resources whose problem list is non-empty, then sort the outer list by id and each inner list alphabetically."],
        brute_force="There is no asymptotically worse sensible approach: a nested loop over resources and required keys is already the direct solution.",
        approach="For each resource, read its tag dict. For each required key: absent → `missing:Key`; present but blank or outside a non-empty allowed list → `invalid:Key`. Dry run with tags `{environment: prod, Owner: ' '}` and standard `{Environment: [prod, dev], Owner: []}`: `Environment` is absent because of case → `missing:Environment`; `Owner` is blank → `invalid:Owner`. Sorted: `[invalid:Owner, missing:Environment]`.",
        complexity="Time O(R × K) for R resources and K required keys, plus sorting; space O(output).",
        pitfalls="Lower-casing keys (AWS tag keys are case-sensitive); forgetting blank values; returning compliant resources with an empty list; forgetting to sort.",
    ),
),
dict(
    id="aws-bill-estimator",
    title="Monthly Bill Estimator",
    difficulty="Medium",
    pattern="Cost",
    entry="estimateBill",
    compare="float",
    description=r"""
An AWS bill is a long list of **usage lines**: a usage type (for example `ec2:t3.micro-hours`) and a
quantity. The price of a usage type is either flat or **tiered** (the first N units cost one price, the
next units a lower one). Some usage types have a monthly **free allowance**.

Write `estimateBill(usage, prices, free)`:

- `usage`: list of `[item, quantity]`. The same item may appear on several lines; add the quantities.
- `prices[item]` is either a number (USD per unit) or a list of tiers `[[upto, price], ...]`, where
  `upto` is the cumulative upper bound of the tier in units and the last tier has `upto = null`
  (unbounded). Example: `[[10, 0.09], [null, 0.05]]` means the first 10 billable units cost 0.09 each
  and every unit after that costs 0.05.
- `free[item]` (optional) is subtracted first: `billable = max(0, total - free)`. Tiers apply to the
  billable quantity.
- An item with no entry in `prices` costs 0.

Return a list of numbers: the cost of each distinct item **in alphabetical order of item name**, then
the grand total as the last element. Do not round.

**Example:** `usage=[["s3:gb",60],["s3:gb",40]]`, `prices={"s3:gb":[[50,0.023],[null,0.022]]}`,
`free={"s3:gb":5}` → billable 95 → `50*0.023 + 45*0.022 = 2.14` → `[2.14, 2.14]`
""",
    starter='''def estimateBill(usage, prices, free):
    pass
''',
    solution='''def estimateBill(usage, prices, free):
    totals = {}
    for item, qty in usage:
        totals[item] = totals.get(item, 0) + qty
    costs = []
    for item in sorted(totals):
        billable = max(0, totals[item] - free.get(item, 0))
        price = prices.get(item, 0)
        if isinstance(price, list):
            cost, prev = 0.0, 0
            for upto, p in price:
                if upto is None or billable <= upto:
                    cost += (billable - prev) * p
                    break
                cost += (upto - prev) * p
                prev = upto
        else:
            cost = billable * price
        costs.append(cost)
    return costs + [sum(costs)]
''',
    tests=[
        [[["s3:gb", 60], ["s3:gb", 40]], {"s3:gb": [[50, 0.023], [None, 0.022]]}, {"s3:gb": 5}],
        [[["ec2:t3.micro-hours", 730]], {"ec2:t3.micro-hours": 0.0104}, {}],
        [[], {"x": 1}, {}],
        [[["lambda:requests", 3000000], ["lambda:gb-seconds", 600000]],
         {"lambda:requests": 0.0000002, "lambda:gb-seconds": 0.0000166667},
         {"lambda:requests": 1000000, "lambda:gb-seconds": 400000}],
        [[["data-out:gb", 100]], {"data-out:gb": [[10, 0.09], [50, 0.085], [None, 0.07]]}, {"data-out:gb": 100}],
        [[["data-out:gb", 180]], {"data-out:gb": [[10, 0.09], [50, 0.085], [None, 0.07]]}, {"data-out:gb": 100}],
        [[["data-out:gb", 110]], {"data-out:gb": [[10, 0.09], [50, 0.085], [None, 0.07]]}, {"data-out:gb": 100}],
        [[["zeta", 3], ["alpha", 2], ["mid", 1]], {"zeta": 1, "alpha": 10}, {"mid": 5}],
        [[["nat:hours", 730], ["nat:gb", 200], ["eip:idle-hours", 730]],
         {"nat:hours": 0.045, "nat:gb": 0.045, "eip:idle-hours": 0.005}, {}],
        [[["a", 50]], {"a": [[50, 2], [None, 1]]}, {}],
        [[["a", 51]], {"a": [[50, 2], [None, 1]]}, {}],
        [[["k%d" % (i % 7), i] for i in range(200)], {"k%d" % j: [[100, 0.5], [None, 0.25]] for j in range(7)}, {"k3": 1000}],
    ],
    examples=2,
    wrong_solutions=[
        '''def estimateBill(usage, prices, free):
    totals = {}
    for item, qty in usage:
        totals[item] = totals.get(item, 0) + qty
    costs = []
    for item in sorted(totals):
        billable = max(0, totals[item] - free.get(item, 0))
        price = prices.get(item, 0)
        if isinstance(price, list):
            cost = 0
            for upto, p in price:
                if upto is None or billable <= upto:
                    cost = billable * p
                    break
        else:
            cost = billable * price
        costs.append(cost)
    return costs + [sum(costs)]
''',
        '''def estimateBill(usage, prices, free):
    costs = []
    for item, qty in sorted(usage):
        billable = max(0, qty - free.get(item, 0))
        price = prices.get(item, 0)
        if isinstance(price, list):
            cost, prev = 0.0, 0
            for upto, p in price:
                if upto is None or billable <= upto:
                    cost += (billable - prev) * p
                    break
                cost += (upto - prev) * p
                prev = upto
        else:
            cost = billable * price
        costs.append(cost)
    return costs + [sum(costs)]
''',
    ],
    guide=dict(
        prereqs="Dictionaries; the idea of tiered pricing from the billing lesson.",
        intuition="Three passes in a fixed order: add up quantities per item, subtract the free allowance, then walk the tiers charging each slice of the quantity at its own price. A common misreading is to charge the whole quantity at the price of the tier it ends in.",
        hints=["First build `totals[item]` — the free allowance applies once per item, not once per line.",
               "For tiers keep `prev`, the upper bound of the previous tier; the slice inside a tier is `min(billable, upto) - prev`.",
               "Stop at the first tier whose bound is `None` or at least `billable`; append the sum of all costs at the end."],
        brute_force="Charge unit by unit: for each billable unit find its tier and add that price. Correct but O(quantity), far too slow for millions of requests.",
        approach="Aggregate, then for each item in sorted order compute `billable`. Flat price: multiply. Tiered: accumulate slices. Dry run: 180 GB out, 100 free, tiers `[[10, .09], [50, .085], [None, .07]]`: billable 80 → 10×0.09 + 40×0.085 + 30×0.07 = 0.9 + 3.4 + 2.1 = 6.4.",
        complexity="O(L + I log I + I × T) for L usage lines, I items and T tiers; O(I) space.",
        pitfalls="Applying the free allowance per line; pricing the full quantity at the last tier's price; forgetting the `max(0, …)` when usage is below the allowance; not handling the exact tier boundary (50 units with a 50-unit tier stays in tier one).",
    ),
),
dict(
    id="aws-iam-least-privilege-audit",
    title="Least-Privilege Policy Audit",
    difficulty="Easy",
    pattern="IAM",
    entry="auditPolicy",
    description=r"""
**Least privilege** means a policy grants only what is used. A reviewer has the statements of an
identity policy and the list of actions the identity called in the last 90 days.

Write `auditPolicy(statements, used_actions)` returning a **sorted** list of finding strings.
Only statements with `"Effect": "Allow"` are audited. Each statement has `Sid`, `Action` (list) and
`Resource` (list).

For each Allow statement:

1. If `"*"` is in `Action` **and** `"*"` is in `Resource` → one finding `"ADMIN:<Sid>"` and nothing
   else for that statement.
2. Otherwise:
   - any action containing a `*` (such as `"*"`, `"s3:*"`, `"ec2:Describe*"`) → one finding
     `"WILDCARD_ACTION:<Sid>"` (once per statement);
   - `"*"` in `Resource` → `"WILDCARD_RESOURCE:<Sid>"`;
   - every action **without** a `*` that does not appear in `used_actions` (compare
     case-insensitively, because IAM action names are case-insensitive) → `"UNUSED:<Sid>:<action>"`
     using the action exactly as written in the policy.

**Example:** statement `{Sid:"S1", Effect:"Allow", Action:["s3:GetObject","s3:PutObject"], Resource:["*"]}`
with `used_actions=["s3:getobject"]` → `["UNUSED:S1:s3:PutObject", "WILDCARD_RESOURCE:S1"]`
""",
    starter='''def auditPolicy(statements, used_actions):
    pass
''',
    solution='''def auditPolicy(statements, used_actions):
    used = {a.lower() for a in used_actions}
    out = []
    for st in statements:
        if st["Effect"] != "Allow":
            continue
        sid, actions, resources = st["Sid"], st["Action"], st["Resource"]
        if "*" in actions and "*" in resources:
            out.append("ADMIN:" + sid)
            continue
        if any("*" in a for a in actions):
            out.append("WILDCARD_ACTION:" + sid)
        if "*" in resources:
            out.append("WILDCARD_RESOURCE:" + sid)
        for a in actions:
            if "*" not in a and a.lower() not in used:
                out.append("UNUSED:%s:%s" % (sid, a))
    return sorted(out)
''',
    tests=[
        [[{"Sid": "S1", "Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject"], "Resource": ["*"]}], ["s3:getobject"]],
        [[{"Sid": "Root", "Effect": "Allow", "Action": ["*"], "Resource": ["*"]}], []],
        [[{"Sid": "D", "Effect": "Deny", "Action": ["*"], "Resource": ["*"]}], []],
        [[{"Sid": "A", "Effect": "Allow", "Action": ["ec2:Describe*", "ec2:StartInstances"], "Resource": ["arn:aws:ec2:*:*:instance/i-1"]}],
         ["ec2:DescribeInstances"]],
        [[{"Sid": "B", "Effect": "Allow", "Action": ["*"], "Resource": ["arn:aws:s3:::logs/*"]}], ["s3:GetObject"]],
        [[], ["s3:GetObject"]],
        [[{"Sid": "Ok", "Effect": "Allow", "Action": ["sqs:SendMessage"], "Resource": ["arn:aws:sqs:eu-west-1:1:orders"]}], ["SQS:SENDMESSAGE"]],
        [[{"Sid": "Z", "Effect": "Allow", "Action": ["kms:Decrypt"], "Resource": ["*"]},
          {"Sid": "A", "Effect": "Allow", "Action": ["s3:*", "*"], "Resource": ["*"]},
          {"Sid": "M", "Effect": "Deny", "Action": ["iam:*"], "Resource": ["*"]}], ["kms:Decrypt"]],
        [[{"Sid": "Dup", "Effect": "Allow", "Action": ["s3:Get*", "s3:List*", "s3:DeleteObject"], "Resource": ["arn:aws:s3:::b/*", "*"]}], []],
        [[{"Sid": "S%d" % i, "Effect": "Allow", "Action": ["svc:Act%d" % i, "svc:Other%d" % i], "Resource": ["arn:x"]} for i in range(30)],
         ["svc:act%d" % i for i in range(0, 30, 2)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def auditPolicy(statements, used_actions):
    out = []
    for st in statements:
        if st["Effect"] != "Allow":
            continue
        sid, actions, resources = st["Sid"], st["Action"], st["Resource"]
        if "*" in actions and "*" in resources:
            out.append("ADMIN:" + sid)
            continue
        if any("*" in a for a in actions):
            out.append("WILDCARD_ACTION:" + sid)
        if "*" in resources:
            out.append("WILDCARD_RESOURCE:" + sid)
        for a in actions:
            if "*" not in a and a not in used_actions:
                out.append("UNUSED:%s:%s" % (sid, a))
    return sorted(out)
''',
        '''def auditPolicy(statements, used_actions):
    used = {a.lower() for a in used_actions}
    out = []
    for st in statements:
        sid, actions, resources = st["Sid"], st["Action"], st["Resource"]
        if "*" in actions:
            out.append("WILDCARD_ACTION:" + sid)
        if "*" in resources:
            out.append("WILDCARD_RESOURCE:" + sid)
        for a in actions:
            if "*" not in a and a.lower() not in used:
                out.append("UNUSED:%s:%s" % (sid, a))
    return sorted(out)
''',
    ],
    guide=dict(
        prereqs="The IAM identities lesson: what a statement, action and resource are.",
        intuition="Each statement is judged alone. The worst case (everything on everything) gets a single label; otherwise three independent checks run.",
        hints=["Skip Deny statements first.", "Put lower-cased used actions in a set for O(1) lookups.",
               "Emit `WILDCARD_ACTION` once per statement with `any(...)`, not once per wildcard action."],
        brute_force="Checking each action against the `used_actions` list with a linear scan and `.lower()` on every comparison is O(A × U); a set removes the inner loop.",
        approach="Dry run: `Action=[ec2:Describe*, ec2:StartInstances]`, resource a specific ARN, used `[ec2:DescribeInstances]`. Not admin. One action has `*` → `WILDCARD_ACTION:A`. Resource is specific → nothing. `ec2:StartInstances` has no `*` and is not used → `UNUSED:A:ec2:StartInstances`. Sort the findings.",
        complexity="O(total actions + U) time, O(U) space.",
        pitfalls="Case-sensitive comparison of action names; auditing Deny statements; reporting both wildcard findings as well as ADMIN; reporting a wildcard action as unused.",
    ),
),
dict(
    id="aws-iam-evaluate",
    title="IAM Policy Evaluation",
    difficulty="Hard",
    pattern="IAM",
    entry="evaluate",
    description=r"""
Implement the decision AWS makes for every API call inside **one account** (a simplified but faithful
version of the real evaluation logic).

`evaluate(request, identity, resource, scps)` returns `"Allow"`, `"ExplicitDeny"` or `"ImplicitDeny"`.

- `request`: `{"principal": arn, "action": "s3:GetObject", "resource": arn, "context": {key: value}}`.
- `identity`: list of statements attached to the caller (user, group or role policies, already merged).
- `resource`: list of statements of the resource-based policy (for example a bucket policy). These
  statements also carry `"Principal"`: a list of patterns; the statement applies only if one pattern
  matches `request["principal"]`.
- `scps`: list of service control policies (each one a list of statements) inherited from the
  organisation. An empty list means the account is not in an organisation.

A **statement** has `Effect` (`"Allow"`/`"Deny"`), `Action` (list of patterns), `Resource` (list of
patterns) and optionally `Condition`.

**Matching.** In patterns `*` matches any run of characters (including none) and `?` matches exactly
one character. Actions are compared **case-insensitively**; resources and principals are
case-sensitive. A statement matches when some action pattern matches, some resource pattern matches,
(for resource policies) some principal pattern matches, and every condition holds.

**Conditions.** `Condition` is `{operator: {key: value}}`. Every entry must hold:

- `StringEquals`: the context has the key and its value equals `value`.
- `StringNotEquals`: the context does **not** have the key, or its value differs.
- `StringLike`: the context has the key and it matches `value` as a `*`/`?` pattern.

**Decision, in this order:**

1. If any matching statement in `identity`, `resource` or any SCP has `Effect: Deny` → `"ExplicitDeny"`.
2. If `scps` is non-empty, **every** SCP must contain a matching Allow statement, otherwise
   `"ImplicitDeny"`. (SCPs never grant anything; they only limit.)
3. If a matching Allow exists in `identity` **or** in `resource` → `"Allow"`.
4. Otherwise → `"ImplicitDeny"`.

**Example:** identity allows `s3:Get*` on `arn:aws:s3:::reports/*` and denies `s3:*` on
`arn:aws:s3:::reports/secret/*`. Request `s3:GetObject` on `arn:aws:s3:::reports/secret/a.txt`
→ `"ExplicitDeny"`.
""",
    starter='''def evaluate(request, identity, resource, scps):
    pass
''',
    solution='''import re

def _like(pattern, text, ci=False):
    rx = "".join(".*" if c == "*" else "." if c == "?" else re.escape(c) for c in pattern)
    return re.fullmatch(rx, text, re.S | (re.I if ci else 0)) is not None

def _cond(st, ctx):
    for op, pairs in (st.get("Condition") or {}).items():
        for k, v in pairs.items():
            if op == "StringEquals":
                ok = k in ctx and ctx[k] == v
            elif op == "StringNotEquals":
                ok = k not in ctx or ctx[k] != v
            elif op == "StringLike":
                ok = k in ctx and _like(v, ctx[k])
            else:
                ok = False
            if not ok:
                return False
    return True

def _matches(st, req, need_principal):
    if not any(_like(a, req["action"], True) for a in st["Action"]):
        return False
    if not any(_like(r, req["resource"]) for r in st["Resource"]):
        return False
    if need_principal and not any(_like(p, req["principal"]) for p in st.get("Principal", [])):
        return False
    return _cond(st, req.get("context") or {})

def evaluate(request, identity, resource, scps):
    def effects(stmts, need_principal=False):
        return {s["Effect"] for s in stmts if _matches(s, request, need_principal)}
    ident, res = effects(identity), effects(resource, True)
    scp_effects = [effects(s) for s in scps]
    if "Deny" in ident or "Deny" in res or any("Deny" in e for e in scp_effects):
        return "ExplicitDeny"
    if any("Allow" not in e for e in scp_effects):
        return "ImplicitDeny"
    if "Allow" in ident or "Allow" in res:
        return "Allow"
    return "ImplicitDeny"
''',
    tests=[
        [_req("s3:GetObject", "arn:aws:s3:::reports/secret/a.txt"), [_READ_REPORTS, _DENY_SECRET], [], []],
        [_req("s3:GetObject", "arn:aws:s3:::reports/2026/q1.csv"), [_READ_REPORTS, _DENY_SECRET], [], []],
        [_req("s3:PutObject", "arn:aws:s3:::reports/2026/q1.csv"), [_READ_REPORTS], [], []],
        [_req("S3:getobject", "arn:aws:s3:::reports/x"), [_READ_REPORTS], [], []],
        [_req("s3:GetObject", "arn:aws:s3:::Reports/x"), [_READ_REPORTS], [], []],
        [_req("s3:PutObject", "arn:aws:s3:::uploads/a.png"), [], [_BUCKET_ALLOW_ANA], []],
        [_req("s3:PutObject", "arn:aws:s3:::uploads/a.png", principal="arn:aws:iam::111122223333:user/bo"), [], [_BUCKET_ALLOW_ANA], []],
        [_req("ec2:RunInstances", "arn:aws:ec2:eu-west-1:1:instance/*"), [_ADMIN], [], [_SCP_ALL, _SCP_S3_ONLY]],
        [_req("s3:ListBucket", "arn:aws:s3:::reports"), [_ADMIN], [], [_SCP_ALL, _SCP_S3_ONLY]],
        [_req("s3:DeleteObject", "arn:aws:s3:::reports/a"), [_ADMIN], [], [_SCP_DENY_DELETE]],
        [_req("s3:DeleteObject", "arn:aws:s3:::reports/a", {"aws:MultiFactorAuthPresent": "true"}), [_MFA_DELETE], [], []],
        [_req("s3:DeleteObject", "arn:aws:s3:::reports/a", {"aws:MultiFactorAuthPresent": "false"}), [_MFA_DELETE], [], []],
        [_req("s3:DeleteObject", "arn:aws:s3:::reports/a"), [_MFA_DELETE], [], []],
        [_req("s3:GetObject", "arn:aws:s3:::reports/a", {"aws:RequestedRegion": "us-east-1"}), [_ADMIN, _DENY_OUTSIDE_EU], [], []],
        [_req("s3:GetObject", "arn:aws:s3:::reports/a"), [_ADMIN, _DENY_OUTSIDE_EU], [], []],
        [_req("s3:GetObject", "arn:aws:s3:::reports/a", {"aws:RequestedRegion": "eu-west-1"}), [_ADMIN, _DENY_OUTSIDE_EU], [], [_SCP_ALL]],
        [_req("s3:PutObject", "arn:aws:s3:::uploads/a.png"), [], [_BUCKET_ALLOW_ANA], [[{"Effect": "Allow", "Action": ["ec2:*"], "Resource": ["*"]}]]],
        [_req("logs:PutLogEvents", "arn:aws:logs:eu-west-1:1:log-group:app-7", {"aws:PrincipalTag/team": "data-eu"}),
         [{"Effect": "Allow", "Action": ["logs:Put???Events"], "Resource": ["arn:aws:logs:*:*:log-group:app-?"],
           "Condition": {"StringLike": {"aws:PrincipalTag/team": "data-*"}}}], [], []],
    ],
    examples=3,
    wrong_solutions=[
        '''import fnmatch
def evaluate(request, identity, resource, scps):
    def m(st):
        return any(fnmatch.fnmatch(request["action"].lower(), a.lower()) for a in st["Action"]) and \\
               any(fnmatch.fnmatchcase(request["resource"], r) for r in st["Resource"])
    for st in identity + resource:
        if m(st) and st["Effect"] == "Allow":
            return "Allow"
    for st in identity + resource:
        if m(st) and st["Effect"] == "Deny":
            return "ExplicitDeny"
    return "ImplicitDeny"
''',
        '''import re
def _like(pattern, text, ci=False):
    rx = "".join(".*" if c == "*" else "." if c == "?" else re.escape(c) for c in pattern)
    return re.fullmatch(rx, text, re.S | (re.I if ci else 0)) is not None
def _cond(st, ctx):
    for op, pairs in (st.get("Condition") or {}).items():
        for k, v in pairs.items():
            if op == "StringEquals" and not (k in ctx and ctx[k] == v):
                return False
            if op == "StringNotEquals" and not (k in ctx and ctx[k] != v):
                return False
            if op == "StringLike" and not (k in ctx and _like(v, ctx[k])):
                return False
    return True
def evaluate(request, identity, resource, scps):
    def effects(stmts, pr=False):
        out = set()
        for s in stmts:
            if any(_like(a, request["action"], True) for a in s["Action"]) and any(_like(r, request["resource"]) for r in s["Resource"]) \\
               and (not pr or any(_like(p, request["principal"]) for p in s.get("Principal", []))) and _cond(s, request.get("context") or {}):
                out.add(s["Effect"])
        return out
    ident, res = effects(identity), effects(resource, True)
    sc = [effects(s) for s in scps]
    if "Deny" in ident or "Deny" in res or any("Deny" in e for e in sc):
        return "ExplicitDeny"
    if any("Allow" not in e for e in sc):
        return "ImplicitDeny"
    return "Allow" if ("Allow" in ident or "Allow" in res) else "ImplicitDeny"
''',
        '''import re
def _like(pattern, text, ci=False):
    rx = "".join(".*" if c == "*" else "." if c == "?" else re.escape(c) for c in pattern)
    return re.fullmatch(rx, text, re.S | (re.I if ci else 0)) is not None
def evaluate(request, identity, resource, scps):
    ctx = request.get("context") or {}
    def cond(st):
        for op, pairs in (st.get("Condition") or {}).items():
            for k, v in pairs.items():
                if op == "StringEquals" and not (k in ctx and ctx[k] == v): return False
                if op == "StringNotEquals" and not (k not in ctx or ctx[k] != v): return False
                if op == "StringLike" and not (k in ctx and _like(v, ctx[k])): return False
        return True
    def effects(stmts, pr=False):
        return {s["Effect"] for s in stmts if any(_like(a, request["action"], True) for a in s["Action"])
                and any(_like(r, request["resource"]) for r in s["Resource"])
                and (not pr or any(_like(p, request["principal"]) for p in s.get("Principal", []))) and cond(s)}
    ident, res = effects(identity), effects(resource, True)
    if "Deny" in ident or "Deny" in res:
        return "ExplicitDeny"
    for s in scps:
        e = effects(s)
        if "Deny" in e:
            return "ExplicitDeny"
    if any("Allow" in effects(s) for s in scps) or not scps:
        if "Allow" in ident or "Allow" in res:
            return "Allow"
    return "ImplicitDeny"
''',
    ],
    guide=dict(
        prereqs="The policy evaluation lesson (explicit deny, default deny, SCPs as guardrails). Regular expressions or a hand-written wildcard matcher.",
        intuition="Collect, for each policy source, the set of effects of the statements that match the request. The decision is then a fixed priority list: any Deny anywhere wins; SCPs must each say Allow; finally one Allow from the identity or the resource is enough. Order of statements never matters.",
        hints=["Write `matches(statement, request)` first and test it alone: action (case-insensitive), resource, optional principal, conditions.",
               "Translate a pattern to a regex: `*` → `.*`, `?` → `.`, escape everything else, and use `fullmatch`.",
               "A missing context key makes `StringEquals` false but `StringNotEquals` true — that asymmetry is what makes 'deny unless region is X' block requests with no region."],
        brute_force="Returning at the first matching statement in list order (allow-first) is the tempting approach and it is wrong: a later Deny must override an earlier Allow. A correct brute force scans all statements, which is already optimal.",
        approach="Compute `ident`, `res` and one effect set per SCP. Dry run: admin identity, SCPs `[allow all]` and `[allow s3:* only]`, request `ec2:RunInstances`. No Deny anywhere. The second SCP has no matching Allow → `ImplicitDeny`, even though the identity policy is `*:*`. With `s3:ListBucket` both SCPs allow and the identity allows → `Allow`.",
        complexity="O(S × P × L) for S statements, P patterns per statement and pattern/text length L (regex matching); O(1) extra space.",
        pitfalls="Stopping at the first Allow; letting an SCP Allow grant access by itself; requiring only one SCP to allow instead of all; comparing actions case-sensitively or resources case-insensitively; treating a missing key as a match for `StringNotEquals` the wrong way round; forgetting `Principal` on resource statements; using `fnmatch`, which gives `[` a special meaning.",
        follow_up="Real IAM adds permissions boundaries and session policies (each is another 'must also allow' layer) and cross-account rules, where the identity policy **and** the resource policy must both allow.",
    ),
),
dict(
    id="aws-s3-lifecycle-schedule",
    title="S3 Lifecycle Schedule",
    difficulty="Medium",
    pattern="S3",
    entry="lifecycleSchedule",
    description=r"""
An S3 **lifecycle configuration** is a list of rules. Each rule applies to the objects whose key starts
with the rule's prefix, moves them to colder storage classes when they reach given ages, and may
finally delete them.

Write `lifecycleSchedule(key, rules)` that returns the future of one object created on day 0 in class
`STANDARD`, as a list of `[day, state]` changes in chronological order.

- `rules`: list of `{"prefix": str, "transitions": [[days, storage_class], ...], "expire": days or null}`.
  A rule applies when `key.startswith(prefix)` (the empty prefix matches every key).
- Classes from warmest to coldest: `STANDARD`, `STANDARD_IA`, `GLACIER_IR`, `GLACIER`, `DEEP_ARCHIVE`.
- Merge the transitions of **all** applicable rules. Objects only ever move to a **colder** class:
  ignore a transition whose class is not colder than the class the object is in at that day. If
  several transitions fall on the same day, the coldest one wins (one change for that day).
- The object expires at the **smallest** `expire` among applicable rules. Expiration beats transition:
  transitions scheduled on or after the expiry day never happen. The last entry is then
  `[expiry_day, "EXPIRED"]`.
- If nothing applies, return `[]`.

**Example:** key `logs/app/1.gz`, rules `[{prefix:"logs/", transitions:[[30,"STANDARD_IA"],[90,"GLACIER"]], expire:365}]`
→ `[[30,"STANDARD_IA"],[90,"GLACIER"],[365,"EXPIRED"]]`
""",
    starter='''def lifecycleSchedule(key, rules):
    pass
''',
    solution='''def lifecycleSchedule(key, rules):
    order = ["STANDARD", "STANDARD_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE"]
    rank = {c: i for i, c in enumerate(order)}
    by_day, expiry = {}, None
    for r in rules:
        if not key.startswith(r["prefix"]):
            continue
        for days, cls in r.get("transitions") or []:
            by_day[days] = max(by_day.get(days, 0), rank[cls])
        e = r.get("expire")
        if e is not None and (expiry is None or e < expiry):
            expiry = e
    out, cur = [], 0
    for day in sorted(by_day):
        if expiry is not None and day >= expiry:
            break
        if by_day[day] > cur:
            cur = by_day[day]
            out.append([day, order[cur]])
    if expiry is not None:
        out.append([expiry, "EXPIRED"])
    return out
''',
    tests=[
        ["logs/app/1.gz", [{"prefix": "logs/", "transitions": [[30, "STANDARD_IA"], [90, "GLACIER"]], "expire": 365}]],
        ["images/cat.png", [{"prefix": "logs/", "transitions": [[30, "STANDARD_IA"]], "expire": 365}]],
        ["logs/a", [{"prefix": "", "transitions": [[60, "GLACIER"]], "expire": None},
                    {"prefix": "logs/", "transitions": [[30, "STANDARD_IA"], [90, "STANDARD_IA"]], "expire": None}]],
        ["tmp/x", [{"prefix": "tmp/", "transitions": [[30, "STANDARD_IA"]], "expire": 7}]],
        ["a", [{"prefix": "", "transitions": [[30, "GLACIER_IR"], [30, "STANDARD_IA"], [30, "DEEP_ARCHIVE"]], "expire": None}]],
        ["a", []],
        ["data/2026/01.parquet", [{"prefix": "data/", "transitions": [[180, "DEEP_ARCHIVE"]], "expire": 2555},
                                  {"prefix": "data/2026/", "transitions": [[30, "STANDARD_IA"], [200, "GLACIER"]], "expire": 3000}]],
        ["logs", [{"prefix": "logs/", "transitions": [[1, "GLACIER"]], "expire": 2}]],
        ["k", [{"prefix": "k", "transitions": [], "expire": 1}]],
        ["k", [{"prefix": "", "transitions": [[90, "GLACIER"]], "expire": 90}]],
        ["k", [{"prefix": "", "transitions": [[90, "GLACIER"], [30, "STANDARD_IA"], [60, "GLACIER_IR"], [365, "DEEP_ARCHIVE"]], "expire": None}]],
        ["p/q/r", [{"prefix": "p/", "transitions": [[10 * i, c]], "expire": None}
                   for i, c in enumerate(["DEEP_ARCHIVE", "GLACIER", "GLACIER_IR", "STANDARD_IA"], start=1)]],
    ],
    examples=2,
    wrong_solutions=[
        '''def lifecycleSchedule(key, rules):
    out, expiry = [], None
    for r in rules:
        if key.startswith(r["prefix"]):
            out += [list(t) for t in r["transitions"]]
            if r["expire"] is not None:
                expiry = r["expire"] if expiry is None else min(expiry, r["expire"])
    out.sort()
    if expiry is not None:
        out = [t for t in out if t[0] < expiry] + [[expiry, "EXPIRED"]]
    return out
''',
        '''def lifecycleSchedule(key, rules):
    order = ["STANDARD", "STANDARD_IA", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE"]
    rank = {c: i for i, c in enumerate(order)}
    for r in rules:
        if key.startswith(r["prefix"]):
            out, cur = [], 0
            for days, cls in sorted(r["transitions"]):
                if rank[cls] > cur and (r["expire"] is None or days < r["expire"]):
                    cur = rank[cls]
                    out.append([days, cls])
            if r["expire"] is not None:
                out.append([r["expire"], "EXPIRED"])
            return out
    return []
''',
    ],
    guide=dict(
        prereqs="The S3 basics lesson (storage classes and lifecycle rules); sorting; dictionaries.",
        intuition="Flatten everything into a timeline. Give each class a rank; walking the days in order, a transition is real only if it raises the rank. The earliest expiry cuts the timeline.",
        hints=["Filter rules with `key.startswith(prefix)` — the prefix is a plain string, not a folder.",
               "Group transitions by day keeping the coldest rank for that day.",
               "Walk days in ascending order with a `current_rank`; stop at the first day that is `>= expiry`."],
        brute_force="Simulate day by day from 0 to the largest day mentioned, asking each rule what applies today. Correct, but O(days × rules) instead of O(n log n).",
        approach="Dry run: rules `''→[60 GLACIER]` and `logs/→[30 IA, 90 IA]` for key `logs/a`. Days: 30→IA(1), 60→GLACIER(3), 90→IA(1). Walk: day 30 rank 1 > 0 → emit; day 60 rank 3 > 1 → emit; day 90 rank 1 < 3 → ignored (objects do not warm up). Result `[[30, STANDARD_IA], [60, GLACIER]]`.",
        complexity="O(T log T) for T transitions across matching rules; O(T) space.",
        pitfalls="Using only the first matching rule; letting an object move back to a warmer class; emitting two changes on the same day; keeping a transition on the expiry day; treating the prefix `logs/` as matching the key `logs`.",
    ),
),
dict(
    id="aws-s3-storage-cost",
    title="S3 Monthly Storage Cost",
    difficulty="Easy",
    pattern="S3",
    entry="storageCost",
    compare="float",
    description=r"""
Compute one month of S3 **storage** charges (requests and data transfer are ignored) for a set of
objects, using the prices passed in.

`storageCost(objects, prices)`:

- `objects`: list of `[size_kb, storage_class, count]` — `count` identical objects of `size_kb`
  kilobytes each.
- `prices`: dict `storage_class -> USD per GB-month`. 1 GB = 1,048,576 KB.
- **Minimum billable size.** In `STANDARD_IA`, `ONEZONE_IA` and `GLACIER_IR`, an object smaller than
  128 KB is billed as 128 KB.
- **Archive overhead.** In `GLACIER` and `DEEP_ARCHIVE`, every object carries 40 KB of extra
  metadata: 32 KB billed at the object's own class price and 8 KB billed at the `STANDARD` price.
- Other classes (`STANDARD`, `INTELLIGENT_TIERING`, …) bill the exact size.

Return the total in USD (a float; do not round).

**Example:** `[[10, "STANDARD_IA", 1000000]]` with `STANDARD_IA = 0.0125`: each 10 KB object is billed as
128 KB → `128,000,000 KB = 122.07 GB` → about `1.5259`.
""",
    starter='''def storageCost(objects, prices):
    pass
''',
    solution='''def storageCost(objects, prices):
    KB_PER_GB = 1024 * 1024
    total = 0.0
    for size_kb, cls, count in objects:
        if cls in ("STANDARD_IA", "ONEZONE_IA", "GLACIER_IR"):
            total += max(size_kb, 128) * count / KB_PER_GB * prices[cls]
        elif cls in ("GLACIER", "DEEP_ARCHIVE"):
            total += (size_kb + 32) * count / KB_PER_GB * prices[cls]
            total += 8 * count / KB_PER_GB * prices["STANDARD"]
        else:
            total += size_kb * count / KB_PER_GB * prices[cls]
    return total
''',
    tests=[
        [[[10, "STANDARD_IA", 1000000]], {"STANDARD_IA": 0.0125}],
        [[[1048576, "STANDARD", 100]], {"STANDARD": 0.023}],
        [[], {"STANDARD": 0.023}],
        [[[4, "DEEP_ARCHIVE", 5000000]], {"STANDARD": 0.023, "DEEP_ARCHIVE": 0.00099}],
        [[[4, "STANDARD", 5000000]], {"STANDARD": 0.023, "DEEP_ARCHIVE": 0.00099}],
        [[[128, "ONEZONE_IA", 10], [127, "ONEZONE_IA", 10], [129, "ONEZONE_IA", 10]], {"ONEZONE_IA": 0.01}],
        [[[500000, "GLACIER", 20], [50, "GLACIER_IR", 2000]], {"STANDARD": 0.023, "GLACIER": 0.0036, "GLACIER_IR": 0.004}],
        [[[64, "INTELLIGENT_TIERING", 1000]], {"INTELLIGENT_TIERING": 0.023}],
        [[[2048, "STANDARD", 3], [2048, "STANDARD_IA", 3], [2048, "GLACIER", 3], [2048, "DEEP_ARCHIVE", 3]],
         {"STANDARD": 0.023, "STANDARD_IA": 0.0125, "GLACIER": 0.0036, "DEEP_ARCHIVE": 0.00099}],
        [[[1, "GLACIER", 0]], {"STANDARD": 0.023, "GLACIER": 0.0036}],
        [[[i + 1, "STANDARD_IA", 10] for i in range(300)], {"STANDARD_IA": 0.0125}],
    ],
    examples=2,
    tolerance=1e-9,
    wrong_solutions=[
        '''def storageCost(objects, prices):
    return sum(s * c / (1024 * 1024) * prices[k] for s, k, c in objects)
''',
        '''def storageCost(objects, prices):
    total = 0.0
    for s, k, c in objects:
        if k in ("STANDARD_IA", "ONEZONE_IA", "GLACIER_IR"):
            s = max(s, 128)
        if k in ("GLACIER", "DEEP_ARCHIVE"):
            s += 40
        total += s * c / (1024 * 1024) * prices[k]
    return total
''',
    ],
    guide=dict(
        prereqs="The S3 basics lesson: storage classes, minimum billable object size and archive overhead.",
        intuition="Each class has its own way of turning an object's size into billable kilobytes. Convert first, price second.",
        hints=["Work in KB until the last moment, then divide by 1,048,576.",
               "For the infrequent-access family use `max(size, 128)`.",
               "The archive overhead is two separate charges: 32 KB at the archive price and 8 KB at the STANDARD price."],
        brute_force="Looping over every single object (`count` iterations) gives the same answer in O(total objects); multiplying by `count` makes it O(lines).",
        approach="Dry run: five million 4 KB objects in DEEP_ARCHIVE at 0.00099 with STANDARD at 0.023. Archive part: 36 KB × 5,000,000 = 171.66 GB × 0.00099 = 0.170. Standard part: 8 KB × 5,000,000 = 38.15 GB × 0.023 = 0.877. Total 1.047 — more than **twice** what the same objects cost in STANDARD (19.07 GB × 0.023 = 0.439). Tiny objects do not belong in archive classes.",
        complexity="O(n) time, O(1) space.",
        pitfalls="Using 1,000,000 KB per GB; adding all 40 KB at the archive price; applying the 128 KB minimum to STANDARD; forgetting to multiply by `count`.",
    ),
),
dict(
    id="aws-presigned-url-check",
    title="Presigned URL Expiry Check",
    difficulty="Easy",
    pattern="S3",
    entry="presignedStatus",
    description=r"""
A **presigned URL** lets someone without AWS credentials download or upload one S3 object for a limited
time. The signing time and lifetime travel in the query string:

`https://bucket.s3.eu-west-1.amazonaws.com/key?X-Amz-Date=20261121T101500Z&X-Amz-Expires=900&X-Amz-Signature=...`

Write `presignedStatus(url, now)` where `now` uses the same UTC format `YYYYMMDDTHHMMSSZ`:

- Return `"INVALID"` if `X-Amz-Date` or `X-Amz-Expires` is missing, if the date is not exactly in the
  format above, or if `X-Amz-Expires` is not an integer between 1 and 604800 (seven days, the maximum
  for Signature Version 4).
- Return `"NOT_YET_VALID"` if `now` is earlier than the signing time.
- Return `"VALID"` if `signing_time <= now < signing_time + expires`.
- Otherwise return `"EXPIRED"`.

Parameter names are case-sensitive. Other parameters may appear in any order. You may assume `now` is
well formed and that dates are real calendar dates.

**Example:** date `20261121T101500Z`, expires `900`, now `20261121T102959Z` → `"VALID"`; one second
later → `"EXPIRED"`.
""",
    starter='''def presignedStatus(url, now):
    pass
''',
    solution='''import re, calendar

def _epoch(s):
    m = re.fullmatch(r"(\\d{4})(\\d{2})(\\d{2})T(\\d{2})(\\d{2})(\\d{2})Z", s)
    if not m:
        return None
    y, mo, d, h, mi, sec = map(int, m.groups())
    return calendar.timegm((y, mo, d, h, mi, sec, 0, 0, 0))

def presignedStatus(url, now):
    query = url.split("?", 1)[1] if "?" in url else ""
    params = {}
    for part in query.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            params[k] = v
    if "X-Amz-Date" not in params or "X-Amz-Expires" not in params:
        return "INVALID"
    start = _epoch(params["X-Amz-Date"])
    exp = params["X-Amz-Expires"]
    if start is None or not re.fullmatch(r"\\d+", exp) or not (1 <= int(exp) <= 604800):
        return "INVALID"
    t = _epoch(now)
    if t < start:
        return "NOT_YET_VALID"
    return "VALID" if t < start + int(exp) else "EXPIRED"
''',
    tests=[
        ["https://b.s3.eu-west-1.amazonaws.com/k?X-Amz-Date=20261121T101500Z&X-Amz-Expires=900&X-Amz-Signature=ab", "20261121T102959Z"],
        ["https://b.s3.eu-west-1.amazonaws.com/k?X-Amz-Date=20261121T101500Z&X-Amz-Expires=900&X-Amz-Signature=ab", "20261121T103000Z"],
        ["https://b.s3.amazonaws.com/k?X-Amz-Expires=60&X-Amz-Date=20261121T101500Z", "20261121T101459Z"],
        ["https://b.s3.amazonaws.com/k?X-Amz-Expires=60", "20261121T101459Z"],
        ["https://b.s3.amazonaws.com/k", "20261121T101459Z"],
        ["https://b.s3.amazonaws.com/k?X-Amz-Date=20261121T101500Z&X-Amz-Expires=604801", "20261121T101500Z"],
        ["https://b.s3.amazonaws.com/k?X-Amz-Date=20261121T101500Z&X-Amz-Expires=604800", "20261128T101459Z"],
        ["https://b.s3.amazonaws.com/k?X-Amz-Date=20261121T101500Z&X-Amz-Expires=604800", "20261128T101500Z"],
        ["https://b.s3.amazonaws.com/k?X-Amz-Date=2026-11-21T10:15:00Z&X-Amz-Expires=60", "20261121T101500Z"],
        ["https://b.s3.amazonaws.com/k?X-Amz-Date=20261121T101500Z&X-Amz-Expires=0", "20261121T101500Z"],
        ["https://b.s3.amazonaws.com/k?X-Amz-Date=20261231T235950Z&X-Amz-Expires=30", "20270101T000010Z"],
        ["https://b.s3.amazonaws.com/k?X-Amz-Date=20240228T235950Z&X-Amz-Expires=86400", "20240229T235949Z"],
        ["https://b.s3.amazonaws.com/k?x-amz-date=20261121T101500Z&x-amz-expires=60", "20261121T101500Z"],
        ["https://b.s3.amazonaws.com/k?X-Amz-Date=20261121T101500Z&X-Amz-Expires=abc", "20261121T101500Z"],
        ["https://b.s3.amazonaws.com/k?X-Amz-Date=20261121T101500Z&X-Amz-Expires=3600", "20261121T101500Z"],
    ],
    examples=2,
    wrong_solutions=[
        '''def presignedStatus(url, now):
    params = dict(p.split("=", 1) for p in url.split("?", 1)[1].split("&")) if "?" in url else {}
    if "X-Amz-Date" not in params or "X-Amz-Expires" not in params:
        return "INVALID"
    try:
        exp = int(params["X-Amz-Expires"])
    except ValueError:
        return "INVALID"
    if not 1 <= exp <= 604800 or len(params["X-Amz-Date"]) != 16:
        return "INVALID"
    start = int(params["X-Amz-Date"][:8] + params["X-Amz-Date"][9:15])
    t = int(now[:8] + now[9:15])
    if t < start:
        return "NOT_YET_VALID"
    return "VALID" if t < start + exp else "EXPIRED"
''',
        '''import re, calendar
def _epoch(s):
    m = re.fullmatch(r"(\\d{4})(\\d{2})(\\d{2})T(\\d{2})(\\d{2})(\\d{2})Z", s)
    if not m:
        return None
    return calendar.timegm(tuple(map(int, m.groups())) + (0, 0, 0))
def presignedStatus(url, now):
    params = dict(p.split("=", 1) for p in url.split("?", 1)[1].split("&") if "=" in p) if "?" in url else {}
    if "X-Amz-Date" not in params or "X-Amz-Expires" not in params:
        return "INVALID"
    start = _epoch(params["X-Amz-Date"])
    if start is None or not params["X-Amz-Expires"].isdigit():
        return "INVALID"
    exp = int(params["X-Amz-Expires"])
    if exp > 604800:
        return "INVALID"
    t = _epoch(now)
    if t < start:
        return "NOT_YET_VALID"
    return "VALID" if t <= start + exp else "EXPIRED"
''',
    ],
    guide=dict(
        prereqs="The S3 protection lesson (presigned URLs). String splitting; converting a calendar time to seconds with `calendar.timegm` or `datetime`.",
        intuition="Turn both timestamps into seconds since 1970 so that the check becomes plain integer arithmetic on a half-open interval `[start, start + expires)`.",
        hints=["Split on the first `?`, then on `&`, then each pair on the first `=`.",
               "Validate before computing: missing keys, date format (a regex with six groups), integer range 1..604800.",
               "Do not compare the digit strings as numbers — `20261231235950 + 30` is not a time."],
        brute_force="There is no meaningful brute force; the mistake to avoid is arithmetic on concatenated digits instead of real time conversion.",
        approach="Dry run: date `20261231T235950Z`, expires 30, now `20270101T000010Z`. Epoch difference is 20 seconds (10 s to midnight plus 10 s) and 20 < 30 → `VALID`, although the year changed. With digit arithmetic the answer would wrongly be EXPIRED.",
        complexity="O(length of the URL) time and space.",
        pitfalls="Treating the end instant as valid (the interval is half-open); accepting `0` or more than seven days; case-insensitive parameter names; crashing on a URL without `?`.",
    ),
),
dict(
    id="aws-bucket-public-detector",
    title="Public Bucket Detector",
    difficulty="Medium",
    pattern="S3",
    entry="bucketExposure",
    description=r"""
Most S3 data leaks come from a bucket policy that grants access to **everyone**. Write a detector.

`bucketExposure(statements, restrict_public_buckets)` returns one of
`"PRIVATE"`, `"PUBLIC_READ"`, `"PUBLIC_WRITE"`, `"PUBLIC_READ_WRITE"`, `"BLOCKED"`.

A statement is **public** when all of these hold:

1. `Effect` is `"Allow"`.
2. `Principal` is the string `"*"`, or a dict `{"AWS": "*"}`, or a dict `{"AWS": [...]}` whose list
   contains `"*"`.
3. It has **no restricting condition**. A condition restricts when, under any operator, it uses one
   of the keys `aws:SourceIp`, `aws:SourceVpc`, `aws:SourceVpce`, `aws:PrincipalOrgID`,
   `aws:SourceArn`, `aws:SourceAccount`, `aws:PrincipalAccount` — except that `aws:SourceIp` with the
   value `"0.0.0.0/0"` restricts nothing. Any other condition key (for example `aws:SecureTransport`)
   does not make the statement private. Condition values are strings.

A public statement gives **read** if any of its `Action` patterns matches `s3:GetObject` or
`s3:ListBucket`, and **write** if any matches `s3:PutObject` or `s3:DeleteObject`. Patterns use `*` as
a wildcard for any run of characters and are case-insensitive (`"*"`, `"s3:*"`, `"s3:Get*"`, …).
`Action` may be a string or a list.

Combine all public statements: none (or none giving read or write) → `"PRIVATE"`. Otherwise, if
`restrict_public_buckets` is `True` (the Block Public Access setting that ignores public policies) →
`"BLOCKED"`. Otherwise report read, write or both.

**Example:** `[{Effect:"Allow", Principal:"*", Action:"s3:GetObject", Resource:"arn:aws:s3:::site/*"}]`,
`False` → `"PUBLIC_READ"`.
""",
    starter='''def bucketExposure(statements, restrict_public_buckets):
    pass
''',
    solution='''import re

RESTRICTING = {"aws:SourceIp", "aws:SourceVpc", "aws:SourceVpce", "aws:PrincipalOrgID",
               "aws:SourceArn", "aws:SourceAccount", "aws:PrincipalAccount"}

def _like(pattern, action):
    rx = "".join(".*" if c == "*" else re.escape(c) for c in pattern)
    return re.fullmatch(rx, action, re.I) is not None

def _public_principal(p):
    if p == "*":
        return True
    if isinstance(p, dict):
        aws = p.get("AWS")
        return aws == "*" or (isinstance(aws, list) and "*" in aws)
    return False

def _restricted(cond):
    for pairs in (cond or {}).values():
        for k, v in pairs.items():
            if k in RESTRICTING and not (k == "aws:SourceIp" and v == "0.0.0.0/0"):
                return True
    return False

def bucketExposure(statements, restrict_public_buckets):
    read = write = False
    for st in statements:
        if st.get("Effect") != "Allow" or not _public_principal(st.get("Principal")):
            continue
        if _restricted(st.get("Condition")):
            continue
        actions = st["Action"] if isinstance(st["Action"], list) else [st["Action"]]
        for a in actions:
            if _like(a, "s3:GetObject") or _like(a, "s3:ListBucket"):
                read = True
            if _like(a, "s3:PutObject") or _like(a, "s3:DeleteObject"):
                write = True
    if not (read or write):
        return "PRIVATE"
    if restrict_public_buckets:
        return "BLOCKED"
    return "PUBLIC_READ_WRITE" if read and write else "PUBLIC_READ" if read else "PUBLIC_WRITE"
''',
    tests=[
        [[{"Effect": "Allow", "Principal": "*", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::site/*"}], False],
        [[{"Effect": "Allow", "Principal": "*", "Action": "s3:GetObject", "Resource": "arn:aws:s3:::site/*"}], True],
        [[{"Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::111122223333:root"}, "Action": "s3:*", "Resource": "*"}], False],
        [[], False],
        [[{"Effect": "Allow", "Principal": {"AWS": "*"}, "Action": ["s3:Put*"], "Resource": "*"}], False],
        [[{"Effect": "Allow", "Principal": {"AWS": ["arn:aws:iam::1:root", "*"]}, "Action": ["S3:*"], "Resource": "*"}], False],
        [[{"Effect": "Allow", "Principal": "*", "Action": "s3:GetObject", "Resource": "*",
           "Condition": {"IpAddress": {"aws:SourceIp": "203.0.113.0/24"}}}], False],
        [[{"Effect": "Allow", "Principal": "*", "Action": "s3:GetObject", "Resource": "*",
           "Condition": {"IpAddress": {"aws:SourceIp": "0.0.0.0/0"}}}], False],
        [[{"Effect": "Allow", "Principal": "*", "Action": "*", "Resource": "*",
           "Condition": {"Bool": {"aws:SecureTransport": "true"}}}], False],
        [[{"Effect": "Deny", "Principal": "*", "Action": "s3:*", "Resource": "*",
           "Condition": {"Bool": {"aws:SecureTransport": "false"}}}], False],
        [[{"Effect": "Allow", "Principal": "*", "Action": "s3:GetBucketLocation", "Resource": "*"}], False],
        [[{"Effect": "Allow", "Principal": "*", "Action": "s3:List*", "Resource": "*",
           "Condition": {"StringEquals": {"aws:PrincipalOrgID": "o-abc123"}}},
          {"Effect": "Allow", "Principal": "*", "Action": ["s3:DeleteObject"], "Resource": "*"}], False],
        [[{"Effect": "Allow", "Principal": {"Service": "cloudfront.amazonaws.com"}, "Action": "s3:GetObject", "Resource": "*",
           "Condition": {"StringEquals": {"aws:SourceArn": "arn:aws:cloudfront::1:distribution/E1"}}}], False],
        [[{"Effect": "Allow", "Principal": "*", "Action": "s3:Get*", "Resource": "*"},
          {"Effect": "Allow", "Principal": {"AWS": "*"}, "Action": "s3:PutObject", "Resource": "*",
           "Condition": {"StringEquals": {"aws:SourceVpce": "vpce-1"}}}], False],
        [[{"Effect": "Allow", "Principal": "*", "Action": ["s3:PutObjectAcl", "s3:*Object"], "Resource": "*"}], True],
    ],
    examples=2,
    wrong_solutions=[
        '''def bucketExposure(statements, restrict_public_buckets):
    read = write = False
    for st in statements:
        if st.get("Effect") == "Allow" and st.get("Principal") == "*" and not st.get("Condition"):
            acts = st["Action"] if isinstance(st["Action"], list) else [st["Action"]]
            for a in acts:
                a = a.lower()
                if a in ("*", "s3:*") or a.startswith("s3:get") or a.startswith("s3:list"):
                    read = True
                if a in ("*", "s3:*") or a.startswith("s3:put") or a.startswith("s3:delete"):
                    write = True
    if not (read or write):
        return "PRIVATE"
    if restrict_public_buckets:
        return "BLOCKED"
    return "PUBLIC_READ_WRITE" if read and write else "PUBLIC_READ" if read else "PUBLIC_WRITE"
''',
        '''import re
def _like(p, a):
    return re.fullmatch("".join(".*" if c == "*" else re.escape(c) for c in p), a, re.I) is not None
def bucketExposure(statements, restrict_public_buckets):
    if restrict_public_buckets:
        return "BLOCKED"
    read = write = False
    for st in statements:
        p = st.get("Principal")
        pub = p == "*" or (isinstance(p, dict) and (p.get("AWS") == "*" or (isinstance(p.get("AWS"), list) and "*" in p["AWS"])))
        if st.get("Effect") != "Allow" or not pub:
            continue
        acts = st["Action"] if isinstance(st["Action"], list) else [st["Action"]]
        for a in acts:
            read = read or _like(a, "s3:GetObject") or _like(a, "s3:ListBucket")
            write = write or _like(a, "s3:PutObject") or _like(a, "s3:DeleteObject")
    if not (read or write):
        return "PRIVATE"
    return "PUBLIC_READ_WRITE" if read and write else "PUBLIC_READ" if read else "PUBLIC_WRITE"
''',
    ],
    guide=dict(
        prereqs="The S3 protection lesson: bucket policies, the `Principal` element, Block Public Access.",
        intuition="Three filters decide whether a statement is public (effect, principal, absence of a real restriction); then two probes decide what it exposes. Block Public Access is applied last, and only when something was actually exposed.",
        hints=["Write `is_public_principal` for the three accepted shapes.",
               "A condition restricts only if its key is in the given set, with the `0.0.0.0/0` exception.",
               "Test each action pattern against four probe actions with a wildcard matcher; do not try to enumerate prefixes."],
        brute_force="String-prefix tests such as `startswith('s3:get')` look simpler but miss patterns like `s3:*Object` and wrongly flag `s3:GetBucketLocation`.",
        approach="Dry run: statements `[List* with PrincipalOrgID condition, DeleteObject without condition]`. First statement: public principal but restricted → skipped. Second: public, no condition, matches `s3:DeleteObject` → write. Result `PUBLIC_WRITE`.",
        complexity="O(S × A) pattern matches; O(1) space.",
        pitfalls="Returning BLOCKED for a bucket that had nothing public; treating any condition as a restriction (`aws:SecureTransport` only forces HTTPS); forgetting the dict forms of `Principal`; flagging Deny statements; case-sensitive action matching.",
    ),
),
]
