_NP_PODS = {
    "web": {"ns": "cafe", "labels": {"app": "web"}},
    "orders-api": {"ns": "cafe", "labels": {"app": "orders-api"}},
    "orders-db": {"ns": "cafe", "labels": {"app": "orders-db"}},
    "gateway": {"ns": "infra", "labels": {"app": "gateway"}},
    "coredns": {"ns": "kube-system", "labels": {"k8s-app": "kube-dns"}},
    "banner": {"ns": "marketing", "labels": {"app": "banner"}},
}
_NP_NS = {
    "cafe": {"name": "cafe", "team": "storefront"},
    "infra": {"name": "infra"},
    "kube-system": {"name": "kube-system"},
    "marketing": {"name": "marketing", "team": "storefront"},
}
_NP_POLICIES = [
    {"ns": "cafe", "podSelector": {}, "types": ["Ingress", "Egress"]},
    {"ns": "cafe", "podSelector": {}, "types": ["Egress"],
     "egress": [{"to": [{"namespaceSelector": {"name": "kube-system"}, "podSelector": {"k8s-app": "kube-dns"}}], "ports": [53]}]},
    {"ns": "cafe", "podSelector": {"app": "orders-api"}, "types": ["Ingress", "Egress"],
     "ingress": [{"from": [{"podSelector": {"app": "web"}},
                           {"namespaceSelector": {"name": "infra"}, "podSelector": {"app": "gateway"}}], "ports": [8080]}],
     "egress": [{"to": [{"podSelector": {"app": "orders-db"}}], "ports": [5432]}]},
    {"ns": "cafe", "podSelector": {"app": "orders-db"}, "types": ["Ingress"],
     "ingress": [{"from": [{"podSelector": {"app": "orders-api"}}], "ports": [5432]}]},
    {"ns": "cafe", "podSelector": {"app": "web"}, "types": ["Egress"],
     "egress": [{"to": [{"podSelector": {"app": "orders-api"}}], "ports": [8080]}]},
]
_NP_PODS_X = dict(
    _NP_PODS,
    **{"imposter-api": {"ns": "marketing", "labels": {"app": "orders-api"}},
       "imposter-web": {"ns": "marketing", "labels": {"app": "web"}}}
)
_NP_OPEN = [
    {"ns": "cafe", "podSelector": {"app": "orders-db"}, "types": ["Ingress"],
     "ingress": [{"from": [{"namespaceSelector": {"team": "storefront"}}]}]},
    {"ns": "cafe", "podSelector": {"app": "web"}, "types": ["Ingress"], "ingress": [{"ports": [8080]}]},
    {"ns": "marketing", "podSelector": {"app": "banner"}, "types": ["Egress"],
     "egress": [{"to": [{"namespaceSelector": {}}], "ports": [5432, 8080]}]},
]

_RBAC_ROLES = [
    {"kind": "Role", "namespace": "cafe", "name": "troubleshooter", "rules": [
        {"apiGroups": [""], "resources": ["pods", "pods/log"], "verbs": ["get", "list", "watch"]},
        {"apiGroups": ["apps"], "resources": ["deployments/scale"], "verbs": ["patch", "update"]},
        {"apiGroups": [""], "resources": ["secrets"], "resourceNames": ["flags"], "verbs": ["get"]}]},
    {"kind": "ClusterRole", "name": "edit", "rules": [
        {"apiGroups": ["", "apps"], "resources": ["*"], "verbs": ["*"]}]},
    {"kind": "ClusterRole", "name": "node-viewer", "rules": [
        {"apiGroups": [""], "resources": ["nodes"], "verbs": ["get", "list"]}]},
    {"kind": "Role", "namespace": "finance", "name": "troubleshooter", "rules": [
        {"apiGroups": ["*"], "resources": ["configmaps"], "verbs": ["get"]}]},
]
_RBAC_BINDINGS = [
    {"kind": "RoleBinding", "namespace": "cafe", "roleRef": {"kind": "Role", "name": "troubleshooter"},
     "subjects": [{"kind": "Group", "name": "cafe-devs"}, {"kind": "ServiceAccount", "name": "reporter", "namespace": "cafe"}]},
    {"kind": "RoleBinding", "namespace": "cafe", "roleRef": {"kind": "ClusterRole", "name": "edit"},
     "subjects": [{"kind": "Group", "name": "storefront"}]},
    {"kind": "ClusterRoleBinding", "roleRef": {"kind": "ClusterRole", "name": "node-viewer"},
     "subjects": [{"kind": "Group", "name": "system:authenticated"}]},
    {"kind": "RoleBinding", "namespace": "finance", "roleRef": {"kind": "ClusterRole", "name": "node-viewer"},
     "subjects": [{"kind": "User", "name": "lena"}]},
    {"kind": "RoleBinding", "namespace": "finance", "roleRef": {"kind": "Role", "name": "troubleshooter"},
     "subjects": [{"kind": "User", "name": "lena"}]},
    {"kind": "RoleBinding", "namespace": "shop", "roleRef": {"kind": "Role", "name": "missing"},
     "subjects": [{"kind": "User", "name": "lena"}]},
]

_ING_RULES = [
    ["shop.example", "/", "Prefix", "web"],
    ["api.example", "/menu", "Prefix", "menu-api"],
    ["api.example", "/orders", "Prefix", "orders-api"],
    ["api.example", "/orders/export", "Exact", "report-api"],
    ["*.partners.example", "/", "Prefix", "partner-portal"],
    ["acme.partners.example", "/", "Prefix", "acme-portal"],
    ["", "/healthz", "Exact", "health"],
    ["api.example", "/orders", "Exact", "orders-exact"],
]

PROBLEMS = [
dict(
    id="k8s-dns-resolve",
    title="Cluster DNS Name Resolution",
    difficulty="Medium",
    pattern="Service Discovery",
    entry="resolveName",
    description=r"""
Simulate how a Pod's resolver expands a name using its search list. Write
`resolveName(name, podNamespace, records, ndots)` returning `[answer, queries]`.

- `records` is the list of fully qualified names that exist, such as `"menu-api.cafe.svc.cluster.local"` or
  `"api.github.com"` (no trailing dots).
- The Pod's search list is, in order: `<podNamespace>.svc.cluster.local`, `svc.cluster.local`, `cluster.local`.
- Candidate names are tried in order until one is in `records`:
  - if `name` ends with a dot, it is fully qualified: the only candidate is `name` without the dot;
  - otherwise, if `name` contains **at least `ndots` dots**, try `name` first and then `name.<suffix>` for each suffix;
  - otherwise try `name.<suffix>` for each suffix first, and `name` last.
- `answer` is the candidate that was found, or `"NXDOMAIN"`. `queries` is the number of candidates tried, including the
  successful one.

**Examples** (namespace `cafe`, `ndots = 5`)

- `"menu-api"` → `["menu-api.cafe.svc.cluster.local", 1]`
- `"ledger.finance"` (exists in `finance`) → `["ledger.finance.svc.cluster.local", 2]`
- `"api.github.com"` → `["api.github.com", 4]`; with a trailing dot → `["api.github.com", 1]`
""",
    starter='''def resolveName(name, podNamespace, records, ndots):
    # return [answer, queries]
    pass
''',
    solution='''def resolveName(name, podNamespace, records, ndots):
    known = set(records)
    search = [podNamespace + ".svc.cluster.local", "svc.cluster.local", "cluster.local"]
    if name.endswith("."):
        candidates = [name[:-1]]
    elif name.count(".") >= ndots:
        candidates = [name] + [name + "." + s for s in search]
    else:
        candidates = [name + "." + s for s in search] + [name]
    for i, c in enumerate(candidates, 1):
        if c in known:
            return [c, i]
    return ["NXDOMAIN", len(candidates)]
''',
    tests=[
        ["menu-api", "cafe", ["menu-api.cafe.svc.cluster.local", "ledger.finance.svc.cluster.local", "api.github.com"], 5],
        ["ledger.finance", "cafe", ["menu-api.cafe.svc.cluster.local", "ledger.finance.svc.cluster.local", "api.github.com"], 5],
        ["api.github.com", "cafe", ["menu-api.cafe.svc.cluster.local", "ledger.finance.svc.cluster.local", "api.github.com"], 5],
        ["api.github.com.", "cafe", ["menu-api.cafe.svc.cluster.local", "ledger.finance.svc.cluster.local", "api.github.com"], 5],
        ["ledger", "cafe", ["menu-api.cafe.svc.cluster.local", "ledger.finance.svc.cluster.local"], 5],
        ["menu-api", "finance", ["menu-api.cafe.svc.cluster.local"], 5],
        ["menu-api.cafe.svc.cluster.local", "finance", ["menu-api.cafe.svc.cluster.local"], 5],
        ["menu-api.cafe.svc.cluster.local", "finance", ["menu-api.cafe.svc.cluster.local"], 4],
        ["api.github.com", "cafe", ["api.github.com"], 2],
        ["api.github.com", "cafe", ["api.github.com", "api.github.com.cafe.svc.cluster.local"], 5],
        ["db-0.db", "cafe", ["db-0.db.cafe.svc.cluster.local"], 5],
        ["missing.", "cafe", ["missing.cafe.svc.cluster.local"], 5],
        ["kubernetes.default.svc", "cafe", ["kubernetes.default.svc.cluster.local"], 5],
        ["a.b.c.d.e.f", "cafe", [], 5],
        ["localhost", "cafe", ["localhost"], 0],
    ],
    examples=3,
    wrong_solutions=[
        '''def resolveName(name, podNamespace, records, ndots):
    known = set(records)
    search = [podNamespace + ".svc.cluster.local", "svc.cluster.local", "cluster.local"]
    candidates = [name.rstrip(".") + "." + s for s in search] + [name.rstrip(".")]
    for i, c in enumerate(candidates, 1):
        if c in known:
            return [c, i]
    return ["NXDOMAIN", len(candidates)]
''',
        '''def resolveName(name, podNamespace, records, ndots):
    known = set(records)
    search = [podNamespace + ".svc.cluster.local", "svc.cluster.local", "cluster.local"]
    if name.endswith("."):
        candidates = [name[:-1]]
    elif name.count(".") > ndots:
        candidates = [name] + [name + "." + s for s in search]
    else:
        candidates = [name + "." + s for s in search] + [name]
    for i, c in enumerate(candidates, 1):
        if c in known:
            return [c, i]
    return ["NXDOMAIN", len(candidates)]
''',
    ],
    guide=dict(
        prereqs="The lesson *Service registration and cluster DNS*: `/etc/resolv.conf`, the search list and `ndots`.",
        intuition="The resolver does not know which names are complete. It builds an ordered list of guesses and asks about each in "
                  "turn. `ndots` and a trailing dot only change the order and length of that list.",
        hints=[
            "Build the list of candidates first, then loop over it with a counter.",
            "Three cases: trailing dot (one candidate), dots ≥ ndots (name first), otherwise (name last).",
            "Put `records` in a set so each lookup is O(1).",
        ],
        brute_force="Trying every candidate against a list is O(candidates × records). With a set it is O(candidates), and there are at most four.",
        approach="1. Build the search suffixes from the namespace.\n2. Choose the candidate order.\n3. Return the first hit with its 1-based position, "
                 "or `NXDOMAIN` with the total.\n\n"
                 "**Dry run:** `ledger.finance` from `cafe`, ndots 5. One dot < 5 → suffixes first: `ledger.finance.cafe.svc.cluster.local` (miss), "
                 "`ledger.finance.svc.cluster.local` (hit) → 2 queries.",
        complexity="O(len(records)) to build the set, then O(1).",
        pitfalls="- Ignoring the trailing dot and still applying the search list.\n- Using `>` instead of `>=` for the dot count.\n"
                 "- Counting only failed queries.\n- Forgetting that a full in-cluster name has four dots, which is still below the default of five.",
        follow_up="Each lookup is normally sent twice, for A and AAAA records. Return the total number of DNS packets, and add a per-Pod `dnsConfig` search list.",
    ),
),
dict(
    id="k8s-service-port-mapping",
    title="Service Type and Port Resolution",
    difficulty="Medium",
    pattern="Services",
    entry="resolvePort",
    description=r"""
A request arrives for a Service. Decide which Pod port it reaches, or why it fails. Write
`resolvePort(service, via, port, podPorts, nodeHasLocalPod)`.

- `service` is `{"type": T, "ports": [{"port": int, "targetPort": int or str (optional), "nodePort": int (optional)}],
  "externalTrafficPolicy": "Cluster" or "Local" (optional)}` with `T` in `ClusterIP`, `NodePort`, `LoadBalancer`,
  `ExternalName`.
- `via` says how the request arrives: `"cluster"` (to the ClusterIP from inside), `"node"` (to a node's IP),
  `"lb"` (to the external load balancer).
- `port` is the destination port of the request. `podPorts` maps port names to numbers on the Pods.
- `nodeHasLocalPod` says whether the receiving node runs a ready Pod of this Service.

Return an integer Pod port, or a string, by these rules in order:

1. Type `ExternalName` → `"alias"`.
2. The type does not expose that path → `"unreachable"`. `ClusterIP` accepts only `cluster`; `NodePort` accepts
   `cluster` and `node`; `LoadBalancer` accepts all three.
3. Find the first port entry that listens on `port`: via `node` it listens on its `nodePort` (entries without one do not
   listen); via `cluster` or `lb` it listens on `port`. If none → `"refused"`.
4. If `via` is `node` or `lb`, the policy is `"Local"` and `nodeHasLocalPod` is false → `"dropped"`.
5. The target is `targetPort`, or the entry's `port` if `targetPort` is missing. If it is a string, look it up in
   `podPorts`; if absent → `"no-endpoints"`.

**Example:** type `NodePort`, ports `[{port: 80, targetPort: "http", nodePort: 30080}]`, `podPorts = {http: 8080}`:
via `node` port `30080` → `8080`; via `node` port `80` → `"refused"`.
""",
    starter='''def resolvePort(service, via, port, podPorts, nodeHasLocalPod):
    # return the pod port (int) or a result string
    pass
''',
    solution='''def resolvePort(service, via, port, podPorts, nodeHasLocalPod):
    stype = service["type"]
    if stype == "ExternalName":
        return "alias"
    allowed = {"ClusterIP": ("cluster",), "NodePort": ("cluster", "node"),
               "LoadBalancer": ("cluster", "node", "lb")}[stype]
    if via not in allowed:
        return "unreachable"
    for entry in service.get("ports") or []:
        listen = entry.get("nodePort") if via == "node" else entry["port"]
        if listen is None or listen != port:
            continue
        if via in ("node", "lb") and service.get("externalTrafficPolicy") == "Local" and not nodeHasLocalPod:
            return "dropped"
        target = entry.get("targetPort", entry["port"])
        if isinstance(target, str):
            if target not in podPorts:
                return "no-endpoints"
            return podPorts[target]
        return target
    return "refused"
''',
    tests=[
        [{"type": "NodePort", "ports": [{"port": 80, "targetPort": "http", "nodePort": 30080}]}, "node", 30080, {"http": 8080}, True],
        [{"type": "NodePort", "ports": [{"port": 80, "targetPort": "http", "nodePort": 30080}]}, "node", 80, {"http": 8080}, True],
        [{"type": "ClusterIP", "ports": [{"port": 80, "targetPort": 8080}]}, "cluster", 80, {}, True],
        [{"type": "ClusterIP", "ports": [{"port": 80, "targetPort": 8080}]}, "node", 80, {}, True],
        [{"type": "ClusterIP", "ports": [{"port": 80}]}, "cluster", 80, {}, True],
        [{"type": "ClusterIP", "ports": [{"port": 80}]}, "cluster", 8080, {}, True],
        [{"type": "ExternalName", "ports": []}, "cluster", 443, {}, True],
        [{"type": "LoadBalancer", "externalTrafficPolicy": "Local",
          "ports": [{"port": 80, "targetPort": "http", "nodePort": 31544}, {"port": 443, "targetPort": 8443, "nodePort": 31545}]},
         "lb", 443, {"http": 8080}, True],
        [{"type": "LoadBalancer", "externalTrafficPolicy": "Local",
          "ports": [{"port": 80, "targetPort": "http", "nodePort": 31544}]}, "node", 31544, {"http": 8080}, False],
        [{"type": "LoadBalancer", "externalTrafficPolicy": "Local",
          "ports": [{"port": 80, "targetPort": "http", "nodePort": 31544}]}, "cluster", 80, {"http": 8080}, False],
        [{"type": "LoadBalancer", "externalTrafficPolicy": "Cluster",
          "ports": [{"port": 80, "targetPort": "http", "nodePort": 31544}]}, "lb", 80, {"http": 8080}, False],
        [{"type": "NodePort", "ports": [{"port": 80, "targetPort": "web", "nodePort": 30080}]}, "cluster", 80, {"http": 8080}, True],
        [{"type": "NodePort", "ports": [{"port": 9000}]}, "node", 9000, {}, True],
        [{"type": "NodePort", "ports": [{"port": 9000, "nodePort": 30900}]}, "lb", 9000, {}, True],
        [{"type": "LoadBalancer", "externalTrafficPolicy": "Local", "ports": [{"port": 80, "nodePort": 31000}]}, "lb", 81, {}, False],
    ],
    examples=2,
    wrong_solutions=[
        '''def resolvePort(service, via, port, podPorts, nodeHasLocalPod):
    stype = service["type"]
    if stype == "ExternalName":
        return "alias"
    for entry in service.get("ports") or []:
        if entry["port"] != port and entry.get("nodePort") != port:
            continue
        if service.get("externalTrafficPolicy") == "Local" and not nodeHasLocalPod:
            return "dropped"
        target = entry.get("targetPort", entry["port"])
        if isinstance(target, str):
            return podPorts.get(target, "no-endpoints")
        return target
    return "refused"
''',
    ],
    guide=dict(
        prereqs="The lesson *NodePort, LoadBalancer and other Service types*: the three port numbers and `externalTrafficPolicy`.",
        intuition="Three questions in sequence: can this kind of Service be reached this way at all; does anything listen on that port "
                  "on that path; and where does it forward to. Each question has its own failure word.",
        hints=[
            "Start with a table from Service type to the allowed `via` values.",
            "Which field an entry listens on depends on `via`: `nodePort` for `node`, `port` otherwise.",
            "Check the `Local` policy only after you have found the listening entry, so that a wrong port is still `refused`.",
        ],
        brute_force="The decision list is direct; scanning the port entries is O(number of ports).",
        approach="1. `ExternalName` → alias.\n2. Type/via table → unreachable.\n3. Scan entries for the listening port.\n"
                 "4. Apply the traffic policy.\n5. Resolve the target, by name if needed.\n\n"
                 "**Dry run:** LoadBalancer with policy Local, request via `cluster` on port 80, node without a Pod: allowed; entry found; "
                 "policy check applies only to `node` and `lb` → skip; target `http` → 8080.",
        complexity="O(p) for p port entries.",
        pitfalls="- Accepting `port` on a node, or `nodePort` on the ClusterIP.\n- Applying `externalTrafficPolicy` to in-cluster traffic.\n"
                 "- Forgetting that `targetPort` defaults to `port`.\n- Returning `dropped` for a port nobody listens on.",
        follow_up="Add `internalTrafficPolicy: Local` for in-cluster callers and `sessionAffinity: ClientIP` choosing a stable back end per client address.",
    ),
),
dict(
    id="k8s-ingress-match",
    title="Ingress Rule Matching with Precedence",
    difficulty="Medium",
    pattern="Ingress",
    entry="routeRequest",
    description=r"""
Route an HTTP request through Ingress rules. Write `routeRequest(rules, defaultBackend, host, path)` returning the name
of the Service that receives the request.

Each rule is `[ruleHost, rulePath, pathType, service]` with `pathType` either `"Exact"` or `"Prefix"`.

**Host matching**

- `""` matches every host.
- A host starting with `*.` is a wildcard: it matches a request host that ends with the rest (including the dot) and has
  **exactly one** extra label in front. `*.b.example` matches `a.b.example` but not `b.example` or `x.a.b.example`.
- Any other rule host must equal the request host.

**Path matching**

- `Exact`: the request path equals `rulePath`.
- `Prefix`: split both paths on `/`, ignoring empty pieces; the rule's pieces must be a prefix of the request's pieces.
  (`/orders` matches `/orders`, `/orders/` and `/orders/42`, but not `/ordersummary`. `/` matches everything.)

**Precedence** among matching rules, most important first:

1. host kind: exact host, then wildcard host, then `""`;
2. longer `rulePath` (number of characters);
3. `Exact` before `Prefix`;
4. the earlier rule in the list.

If nothing matches, return `defaultBackend`, or `"404"` if `defaultBackend` is `""`.

**Example:** with rules `/orders` (Prefix → `orders-api`) and `/orders/export` (Exact → `report-api`) on `api.example`:
`/orders/export` → `report-api`, `/orders/export/2026` → `orders-api`.
""",
    starter='''def routeRequest(rules, defaultBackend, host, path):
    # return the chosen service name
    pass
''',
    solution='''def routeRequest(rules, defaultBackend, host, path):
    def host_rank(rule_host):
        if rule_host == "":
            return 0
        if rule_host.startswith("*."):
            suffix = rule_host[1:]
            if host.endswith(suffix):
                first = host[:len(host) - len(suffix)]
                if first != "" and "." not in first:
                    return 1
            return -1
        return 2 if rule_host == host else -1

    def path_ok(rule_path, path_type):
        if path_type == "Exact":
            return path == rule_path
        want = [p for p in rule_path.split("/") if p]
        have = [p for p in path.split("/") if p]
        return have[:len(want)] == want

    best_key, best = None, None
    for i, (rule_host, rule_path, path_type, service) in enumerate(rules):
        rank = host_rank(rule_host)
        if rank < 0 or not path_ok(rule_path, path_type):
            continue
        key = (rank, len(rule_path), 1 if path_type == "Exact" else 0, -i)
        if best_key is None or key > best_key:
            best_key, best = key, service
    if best is not None:
        return best
    return defaultBackend if defaultBackend else "404"
''',
    tests=[
        [_ING_RULES, "not-found", "api.example", "/orders/export"],
        [_ING_RULES, "not-found", "api.example", "/orders/export/2026"],
        [_ING_RULES, "not-found", "shop.example", "/cart"],
        [_ING_RULES, "not-found", "api.example", "/menu/drinks"],
        [_ING_RULES, "not-found", "api.example", "/orders"],
        [_ING_RULES, "not-found", "api.example", "/orders/"],
        [_ING_RULES, "not-found", "api.example", "/ordersummary"],
        [_ING_RULES, "", "api.example", "/ordersummary"],
        [_ING_RULES, "not-found", "acme.partners.example", "/login"],
        [_ING_RULES, "not-found", "beta.partners.example", "/login"],
        [_ING_RULES, "not-found", "a.b.partners.example", "/login"],
        [_ING_RULES, "not-found", "partners.example", "/"],
        [_ING_RULES, "not-found", "unknown.example", "/healthz"],
        [_ING_RULES, "not-found", "shop.example", "/healthz"],
        [[], "", "x", "/"],
        [[["", "/a", "Prefix", "first"], ["", "/a", "Prefix", "second"], ["", "/a/", "Prefix", "third"]], "", "h", "/a/b"],
    ],
    examples=2,
    wrong_solutions=[
        '''def routeRequest(rules, defaultBackend, host, path):
    for rule_host, rule_path, path_type, service in rules:
        if rule_host not in ("", host) and not (rule_host.startswith("*.") and host.endswith(rule_host[1:])):
            continue
        if path_type == "Exact" and path == rule_path:
            return service
        if path_type == "Prefix" and path.startswith(rule_path):
            return service
    return defaultBackend if defaultBackend else "404"
''',
        '''def routeRequest(rules, defaultBackend, host, path):
    best_key, best = None, None
    for i, (rule_host, rule_path, path_type, service) in enumerate(rules):
        if rule_host == "":
            rank = 0
        elif rule_host.startswith("*.") and host.endswith(rule_host[1:]):
            rank = 1
        elif rule_host == host:
            rank = 2
        else:
            continue
        if path_type == "Exact":
            ok = path == rule_path
        else:
            ok = path.startswith(rule_path)
        if not ok:
            continue
        key = (rank, len(rule_path), 1 if path_type == "Exact" else 0, -i)
        if best_key is None or key > best_key:
            best_key, best = key, service
    return best if best is not None else (defaultBackend if defaultBackend else "404")
''',
    ],
    guide=dict(
        prereqs="The lesson *Ingress: host and path routing*: path types, wildcard hosts and the precedence rules.",
        intuition="Routing is filter-then-rank. First discard rules whose host or path does not match. Then pick the most specific "
                  "survivor, where specific is a tuple you can compare: host kind, path length, exactness, position.",
        hints=[
            "Write two helpers: one returning a host rank (or −1 for no match), one returning whether the path matches.",
            "Prefix matching compares lists of path elements, not characters. Split on `/` and drop empty strings.",
            "Build a tuple key such as `(hostRank, len(path), isExact, -index)` and keep the maximum.",
        ],
        brute_force="Evaluating every rule for each request is O(rules), which is what real controllers conceptually do before optimising "
                    "with tries. Nothing cheaper is needed here.",
        approach="1. For each rule compute the host rank; skip on −1.\n2. Check the path by type; skip on mismatch.\n"
                 "3. Compare keys and remember the best.\n4. Fall back to the default backend or `404`.\n\n"
                 "**Dry run:** host `api.example`, path `/orders`. Matching rules: `/orders` Prefix (key `(2, 7, 0, …)`) and `/orders` Exact "
                 "(key `(2, 7, 1, …)`). Same host rank and length; Exact wins → `orders-exact`.",
        complexity="O(R · L) for R rules and path length L.",
        pitfalls="- Using `startswith` for Prefix, which makes `/orders` match `/ordersummary`.\n- Letting a wildcard match zero or two labels.\n"
                 "- Returning the first matching rule instead of the most specific.\n- Preferring a wildcard host over an exact host because it has a longer path.",
        follow_up="Extend the matcher to Gateway API HTTPRoute matches: method, header and query-parameter conditions, with weighted backends.",
    ),
),
dict(
    id="k8s-network-policy",
    title="NetworkPolicy Evaluation",
    difficulty="Hard",
    pattern="Security",
    entry="isAllowed",
    description=r"""
Decide whether a connection between two Pods is allowed. Write `isAllowed(pods, namespaces, policies, src, dst, port)`.

- `pods` maps a Pod name to `{"ns": namespace, "labels": {...}}`. `namespaces` maps a namespace name to its labels.
- Each policy is `{"ns", "podSelector": {...}, "types": [...], "ingress": [rules], "egress": [rules]}`; `ingress` and
  `egress` may be missing (treated as no rules). `types` contains `"Ingress"` and/or `"Egress"`.
- A selector is a dict of labels that must all be present with equal values; `{}` matches everything.
- A policy **selects** a Pod when the Pod is in the policy's namespace and matches `podSelector`.
- An ingress rule is `{"from": [peers], "ports": [ints]}`; an egress rule is `{"to": [peers], "ports": [ints]}`.
  A missing or empty `ports` list means all ports. A missing or empty peer list means all peers.
- A peer is `{"podSelector": {...}}`, `{"namespaceSelector": {...}}`, or both:
  - only `podSelector`: Pods matching it **in the policy's own namespace**;
  - only `namespaceSelector`: every Pod in namespaces whose labels match;
  - both: Pods matching `podSelector` in namespaces matching `namespaceSelector`.

**Evaluation**

- Egress from `src` is permitted if no policy with type `Egress` selects `src`; otherwise it is permitted only if some
  egress rule of some such policy matches `dst` and `port`.
- Ingress to `dst` works the same way with type `Ingress`, ingress rules and `src`.

Return `"allowed"`, `"blocked-egress"`, `"blocked-ingress"` or `"blocked-both"`.

**Example:** a default-deny policy for both directions in `cafe` plus a policy letting `orders-api` reach `orders-db` on
5432 and a policy letting `orders-db` accept that: `orders-api → orders-db:5432` is `allowed`, `web → orders-db:5432` is
`blocked-both`.
""",
    starter='''def isAllowed(pods, namespaces, policies, src, dst, port):
    # return "allowed", "blocked-egress", "blocked-ingress" or "blocked-both"
    pass
''',
    solution='''def isAllowed(pods, namespaces, policies, src, dst, port):
    def sel(selector, labels):
        return all(labels.get(k) == v for k, v in (selector or {}).items())

    def peer_ok(peer, policy_ns, other):
        o = pods[other]
        if "namespaceSelector" in peer:
            if not sel(peer["namespaceSelector"], namespaces.get(o["ns"], {})):
                return False
        elif o["ns"] != policy_ns:
            return False
        return sel(peer.get("podSelector"), o["labels"])

    def permitted(pod, other, direction):
        me = pods[pod]
        chosen = [p for p in policies
                  if p["ns"] == me["ns"] and sel(p.get("podSelector"), me["labels"]) and direction in p["types"]]
        if not chosen:
            return True
        rules_key, peers_key = ("ingress", "from") if direction == "Ingress" else ("egress", "to")
        for p in chosen:
            for rule in p.get(rules_key) or []:
                ports = rule.get("ports") or []
                if ports and port not in ports:
                    continue
                peers = rule.get(peers_key) or []
                if not peers or any(peer_ok(peer, p["ns"], other) for peer in peers):
                    return True
        return False

    out = permitted(src, dst, "Egress")
    inn = permitted(dst, src, "Ingress")
    if out and inn:
        return "allowed"
    if not out and not inn:
        return "blocked-both"
    return "blocked-ingress" if out else "blocked-egress"
''',
    tests=[
        [_NP_PODS, _NP_NS, _NP_POLICIES, "orders-api", "orders-db", 5432],
        [_NP_PODS, _NP_NS, _NP_POLICIES, "web", "orders-db", 5432],
        [_NP_PODS, _NP_NS, _NP_POLICIES, "web", "orders-api", 8080],
        [_NP_PODS, _NP_NS, _NP_POLICIES, "web", "orders-api", 9090],
        [_NP_PODS, _NP_NS, _NP_POLICIES, "gateway", "orders-api", 8080],
        [_NP_PODS, _NP_NS, _NP_POLICIES, "banner", "orders-api", 8080],
        [_NP_PODS, _NP_NS, _NP_POLICIES, "web", "coredns", 53],
        [_NP_PODS, _NP_NS, _NP_POLICIES, "orders-api", "web", 8080],
        [_NP_PODS, _NP_NS, _NP_POLICIES, "banner", "gateway", 443],
        [_NP_PODS, _NP_NS, _NP_POLICIES, "gateway", "web", 8080],
        [_NP_PODS, _NP_NS, [], "banner", "orders-db", 5432],
        [_NP_PODS, _NP_NS, _NP_OPEN, "banner", "orders-db", 5432],
        [_NP_PODS, _NP_NS, _NP_OPEN, "gateway", "orders-db", 5432],
        [_NP_PODS, _NP_NS, _NP_OPEN, "gateway", "web", 8080],
        [_NP_PODS, _NP_NS, _NP_OPEN, "banner", "web", 443],
        [_NP_PODS, _NP_NS, _NP_OPEN, "banner", "gateway", 9999],
        [_NP_PODS_X, _NP_NS, _NP_POLICIES, "imposter-api", "orders-db", 5432],
        [_NP_PODS_X, _NP_NS, _NP_POLICIES, "imposter-web", "orders-api", 8080],
    ],
    examples=2,
    wrong_solutions=[
        '''def isAllowed(pods, namespaces, policies, src, dst, port):
    def sel(selector, labels):
        return all(labels.get(k) == v for k, v in (selector or {}).items())

    def peer_ok(peer, policy_ns, other):
        o = pods[other]
        if "namespaceSelector" in peer and not sel(peer["namespaceSelector"], namespaces.get(o["ns"], {})):
            return False
        return sel(peer.get("podSelector"), o["labels"])

    def permitted(pod, other, direction):
        me = pods[pod]
        chosen = [p for p in policies
                  if p["ns"] == me["ns"] and sel(p.get("podSelector"), me["labels"]) and direction in p["types"]]
        if not chosen:
            return True
        rules_key, peers_key = ("ingress", "from") if direction == "Ingress" else ("egress", "to")
        for p in chosen:
            for rule in p.get(rules_key) or []:
                ports = rule.get("ports") or []
                if ports and port not in ports:
                    continue
                peers = rule.get(peers_key) or []
                if not peers or any(peer_ok(peer, p["ns"], other) for peer in peers):
                    return True
        return False

    out = permitted(src, dst, "Egress")
    inn = permitted(dst, src, "Ingress")
    if out and inn:
        return "allowed"
    if not out and not inn:
        return "blocked-both"
    return "blocked-ingress" if out else "blocked-egress"
''',
        '''def isAllowed(pods, namespaces, policies, src, dst, port):
    def sel(selector, labels):
        return all(labels.get(k) == v for k, v in (selector or {}).items())
    d = pods[dst]
    chosen = [p for p in policies if p["ns"] == d["ns"] and sel(p.get("podSelector"), d["labels"]) and "Ingress" in p["types"]]
    if not chosen:
        return "allowed"
    for p in chosen:
        for rule in p.get("ingress") or []:
            if rule.get("ports") and port not in rule["ports"]:
                continue
            for peer in rule.get("from") or [{}]:
                o = pods[src]
                if "namespaceSelector" in peer:
                    if not sel(peer["namespaceSelector"], namespaces.get(o["ns"], {})):
                        continue
                elif o["ns"] != p["ns"]:
                    continue
                if sel(peer.get("podSelector"), o["labels"]):
                    return "allowed"
    return "blocked-ingress"
''',
    ],
    guide=dict(
        prereqs="The lesson *NetworkPolicies, isolation and auditing*: the four rules (default allow, isolation on selection, additive, both ends must agree) "
                "and the three kinds of peer.",
        intuition="Ask the same question twice, once for each end. For one Pod and one direction: is the Pod isolated at all, and if so, "
                  "does any rule of any selecting policy let this peer through on this port? The answer for the connection combines the two.",
        hints=[
            "Write `permitted(pod, other, direction)` and call it for `(src, dst, Egress)` and `(dst, src, Ingress)`.",
            "Inside it, first collect the policies that select `pod` for that direction. An empty collection means not isolated → permitted.",
            "A bare `podSelector` peer implies the policy's own namespace. Only a peer with a `namespaceSelector` can reach other namespaces.",
        ],
        brute_force="Checking every policy, rule and peer for both directions is O(policies × rules × peers), which is how a reference "
                    "evaluator works. Real data planes precompute per-Pod allow sets.",
        approach="1. `sel(selector, labels)` for label matching.\n2. `peer_ok` implementing the three peer forms.\n"
                 "3. `permitted` as described.\n4. Combine into the four results.\n\n"
                 "**Dry run:** `gateway → web:8080` with the lesson's policies. Egress of `gateway`: no policy in `infra` → permitted. "
                 "Ingress of `web`: the default-deny policy selects it for Ingress and has no ingress rules; no other policy with Ingress selects `web` "
                 "→ not permitted. Result `blocked-ingress`.",
        complexity="Time O(P · R · Q) for P policies, R rules and Q peers per rule; space O(P).",
        pitfalls="- Letting a bare `podSelector` match Pods in other namespaces.\n- Treating a policy with no rules as allow-all instead of deny-all.\n"
                 "- Checking only the destination's ingress and ignoring the source's egress.\n- Treating an empty `ports` list as no ports.\n"
                 "- Using a policy for a direction not listed in its `types`.",
        follow_up="Add `ipBlock` peers with `except` ranges, named ports, and report **which** policy allowed the connection.",
    ),
),
dict(
    id="k8s-rbac-check",
    title="RBAC Authorisation Check",
    difficulty="Medium",
    pattern="API Security",
    entry="canI",
    description=r"""
Implement the core of `kubectl auth can-i`. Write
`canI(roles, bindings, user, groups, verb, apiGroup, resource, namespace, name)` returning `True` or `False`.

- A role is `{"kind": "Role" | "ClusterRole", "namespace": ns (Role only), "name": str, "rules": [...]}`.
- A rule is `{"apiGroups": [...], "resources": [...], "verbs": [...], "resourceNames": [...] (optional)}`.
  The string `"*"` in any of the first three lists matches anything.
- A binding is `{"kind": "RoleBinding" | "ClusterRoleBinding", "namespace": ns (RoleBinding only),
  "roleRef": {"kind", "name"}, "subjects": [...]}`.
- A subject is `{"kind": "User" | "Group" | "ServiceAccount", "name", "namespace" (ServiceAccount only)}`.
  A `ServiceAccount` subject matches the user named `system:serviceaccount:<namespace>:<name>`.
- The request is for `verb` on `resource` in `apiGroup`; `namespace` is `""` for cluster-scoped resources and `name` is
  `""` when the request names no object.

The request is allowed if **some** binding grants it:

1. the binding has a subject matching the user or one of the groups;
2. a `RoleBinding` applies only when `namespace` is not `""` and equals the binding's namespace; a `ClusterRoleBinding`
   applies to every request;
3. the referenced role exists: a `roleRef` of kind `Role` refers to the Role with that name **in the binding's
   namespace**; kind `ClusterRole` refers to the ClusterRole with that name. A `ClusterRoleBinding` may only reference a
   `ClusterRole`;
4. some rule of that role matches the verb, API group and resource, and, if the rule has a non-empty `resourceNames`,
   `name` is not `""` and is in that list.

There are no deny rules: with no matching binding the answer is `False`.
""",
    starter='''def canI(roles, bindings, user, groups, verb, apiGroup, resource, namespace, name):
    # return True or False
    pass
''',
    solution='''def canI(roles, bindings, user, groups, verb, apiGroup, resource, namespace, name):
    index = {}
    for r in roles:
        if r["kind"] == "Role":
            index[("Role", r.get("namespace"), r["name"])] = r
        else:
            index[("ClusterRole", None, r["name"])] = r

    def subject_matches(s):
        if s["kind"] == "User":
            return s["name"] == user
        if s["kind"] == "Group":
            return s["name"] in groups
        if s["kind"] == "ServiceAccount":
            return user == "system:serviceaccount:%s:%s" % (s.get("namespace"), s["name"])
        return False

    def has(want, values):
        return "*" in values or want in values

    for b in bindings:
        if not any(subject_matches(s) for s in b.get("subjects") or []):
            continue
        ref = b["roleRef"]
        if b["kind"] == "RoleBinding":
            if namespace == "" or namespace != b.get("namespace"):
                continue
            key = ("Role", b.get("namespace"), ref["name"]) if ref["kind"] == "Role" else ("ClusterRole", None, ref["name"])
        else:
            if ref["kind"] != "ClusterRole":
                continue
            key = ("ClusterRole", None, ref["name"])
        role = index.get(key)
        if role is None:
            continue
        for rule in role.get("rules") or []:
            if not (has(verb, rule.get("verbs") or []) and has(apiGroup, rule.get("apiGroups") or [])
                    and has(resource, rule.get("resources") or [])):
                continue
            names = rule.get("resourceNames") or []
            if names and (name == "" or name not in names):
                continue
            return True
    return False
''',
    tests=[
        [_RBAC_ROLES, _RBAC_BINDINGS, "lena", ["cafe-devs", "system:authenticated"], "list", "", "pods", "cafe", ""],
        [_RBAC_ROLES, _RBAC_BINDINGS, "lena", ["cafe-devs", "system:authenticated"], "delete", "", "pods", "cafe", ""],
        [_RBAC_ROLES, _RBAC_BINDINGS, "lena", ["cafe-devs", "system:authenticated"], "list", "", "pods", "finance", ""],
        [_RBAC_ROLES, _RBAC_BINDINGS, "lena", ["cafe-devs", "system:authenticated"], "get", "", "secrets", "cafe", "flags"],
        [_RBAC_ROLES, _RBAC_BINDINGS, "lena", ["cafe-devs", "system:authenticated"], "get", "", "secrets", "cafe", "db-password"],
        [_RBAC_ROLES, _RBAC_BINDINGS, "lena", ["cafe-devs", "system:authenticated"], "get", "", "secrets", "cafe", ""],
        [_RBAC_ROLES, _RBAC_BINDINGS, "lena", ["cafe-devs", "system:authenticated"], "get", "", "pods/log", "cafe", "web-1"],
        [_RBAC_ROLES, _RBAC_BINDINGS, "lena", ["cafe-devs", "system:authenticated"], "patch", "apps", "deployments/scale", "cafe", "web"],
        [_RBAC_ROLES, _RBAC_BINDINGS, "lena", ["cafe-devs", "system:authenticated"], "patch", "", "deployments/scale", "cafe", "web"],
        [_RBAC_ROLES, _RBAC_BINDINGS, "omar", ["storefront", "system:authenticated"], "delete", "apps", "deployments", "cafe", "web"],
        [_RBAC_ROLES, _RBAC_BINDINGS, "omar", ["storefront", "system:authenticated"], "delete", "apps", "deployments", "shop", "web"],
        [_RBAC_ROLES, _RBAC_BINDINGS, "omar", ["storefront", "system:authenticated"], "delete", "batch", "jobs", "cafe", "j"],
        [_RBAC_ROLES, _RBAC_BINDINGS, "omar", ["storefront", "system:authenticated"], "list", "", "nodes", "", ""],
        [_RBAC_ROLES, _RBAC_BINDINGS, "anon", [], "list", "", "nodes", "", ""],
        [_RBAC_ROLES, _RBAC_BINDINGS, "system:serviceaccount:cafe:reporter", [], "watch", "", "pods", "cafe", ""],
        [_RBAC_ROLES, _RBAC_BINDINGS, "system:serviceaccount:finance:reporter", [], "watch", "", "pods", "cafe", ""],
        [_RBAC_ROLES, _RBAC_BINDINGS, "lena", [], "get", "", "configmaps", "finance", "x"],
        [_RBAC_ROLES, _RBAC_BINDINGS, "lena", [], "get", "", "configmaps", "shop", "x"],
        [_RBAC_ROLES, _RBAC_BINDINGS, "lena", [], "get", "", "nodes", "", "n1"],
    ],
    examples=2,
    wrong_solutions=[
        '''def canI(roles, bindings, user, groups, verb, apiGroup, resource, namespace, name):
    index = {r["name"]: r for r in roles}

    def subject_matches(s):
        if s["kind"] == "User":
            return s["name"] == user
        if s["kind"] == "Group":
            return s["name"] in groups
        return user == "system:serviceaccount:%s:%s" % (s.get("namespace"), s["name"])

    def has(want, values):
        return "*" in values or want in values

    for b in bindings:
        if not any(subject_matches(s) for s in b.get("subjects") or []):
            continue
        role = index.get(b["roleRef"]["name"])
        if role is None:
            continue
        for rule in role.get("rules") or []:
            if has(verb, rule.get("verbs") or []) and has(apiGroup, rule.get("apiGroups") or []) \\
                    and has(resource, rule.get("resources") or []):
                names = rule.get("resourceNames") or []
                if names and name not in names:
                    continue
                return True
    return False
''',
    ],
    guide=dict(
        prereqs="The lesson *RBAC authorisation and admission control*: Roles, ClusterRoles, the two binding kinds, subjects, and the rule that RBAC only grants.",
        intuition="Authorisation is a search for one path: subject → binding → role → rule → request. Each link has a condition. If "
                  "any complete path exists the answer is yes; otherwise no.",
        hints=[
            "Index roles by `(kind, namespace, name)` so that two Roles with the same name in different namespaces stay distinct.",
            "Handle the binding kind before looking at the role: a RoleBinding is useless for a request in another namespace or for a cluster-scoped resource.",
            "A `RoleBinding` may reference a `ClusterRole`; the namespace restriction still comes from the binding.",
        ],
        brute_force="Iterating over every binding and every rule is O(bindings × rules) and is the natural solution. Real API servers "
                    "do essentially this with caching.",
        approach="1. Build the role index.\n2. For each binding: subject check; scope check; resolve the role; scan the rules.\n"
                 "3. Return `True` at the first match; `False` at the end.\n\n"
                 "**Dry run:** `lena` lists `nodes` (cluster-scoped). The RoleBinding in `finance` to `node-viewer` is skipped because the request "
                 "namespace is empty. The ClusterRoleBinding grants `node-viewer` only to `system:authenticated`, and this request passes no groups → `False`.",
        complexity="Time O(B · S + B · R) for B bindings, S subjects and R rules per role; space O(number of roles).",
        pitfalls="- Looking up roles by name only.\n- Letting a RoleBinding grant access to cluster-scoped resources or other namespaces.\n"
                 "- Treating `resourceNames` as satisfied when the request names nothing (so `list` would pass).\n"
                 "- Forgetting that the core API group is the empty string.\n- Matching a ServiceAccount subject by name without its namespace.",
        follow_up="Return the list of `(verb, resource)` pairs a user holds in a namespace, as `kubectl auth can-i --list` does, and flag dangerous ones.",
    ),
),
dict(
    id="k8s-config-projection",
    title="ConfigMap and Secret Projection into the Environment",
    difficulty="Medium",
    pattern="Configuration",
    entry="buildEnv",
    description=r"""
Work out the environment variables a container receives. Write `buildEnv(sources, envFrom, env)`.

- `sources` maps the name of a ConfigMap or Secret to its `{key: value}` data.
- `envFrom` is a list of `{"name": source, "prefix": str (optional), "optional": bool (optional)}`.
- `env` is a list of entries, each either `{"name": N, "value": V}` or
  `{"name": N, "from": source, "key": K, "optional": bool (optional)}`.

Process `envFrom` in order, then `env` in order:

- **envFrom**: if the source does not exist: skip it when `optional` is true, otherwise return
  `"CreateContainerConfigError: <source>"`. For each key (in the source's own order) the variable name is
  `prefix + key`. Names that are not valid are skipped: a valid name matches `[A-Za-z_][A-Za-z0-9_]*`.
  A later source overwrites variables set by an earlier one.
- **env**: a literal `value` is set directly. For a reference, if the source or the key does not exist: skip the entry
  when `optional` is true, otherwise return `"CreateContainerConfigError: <source>/<key>"`. `env` entries overwrite
  variables from `envFrom`, and later `env` entries overwrite earlier ones.

Return the final dict of variables, or the error string of the **first** problem encountered.

**Example:** `sources = {"a": {"LOG": "info", "app.toml": "x"}, "b": {"LOG": "warn"}}`,
`envFrom = [{"name": "a"}, {"name": "b"}]`, `env = [{"name": "LOG", "value": "debug"}]` → `{"LOG": "debug"}`
(`app.toml` is not a valid variable name).
""",
    starter='''def buildEnv(sources, envFrom, env):
    # return the dict of environment variables or an error string
    pass
''',
    solution='''def buildEnv(sources, envFrom, env):
    def valid(name):
        if not name:
            return False
        if not (name[0].isascii() and (name[0].isalpha() or name[0] == "_")):
            return False
        return all(ch.isascii() and (ch.isalnum() or ch == "_") for ch in name)

    result = {}
    for src in envFrom:
        data = sources.get(src["name"])
        if data is None:
            if src.get("optional"):
                continue
            return "CreateContainerConfigError: " + src["name"]
        for key, value in data.items():
            name = (src.get("prefix") or "") + key
            if valid(name):
                result[name] = value
    for e in env:
        if "value" in e:
            result[e["name"]] = e["value"]
            continue
        data = sources.get(e["from"])
        if data is None or e["key"] not in data:
            if e.get("optional"):
                continue
            return "CreateContainerConfigError: %s/%s" % (e["from"], e["key"])
        result[e["name"]] = data[e["key"]]
    return result
''',
    tests=[
        [{"a": {"LOG": "info", "app.toml": "x"}, "b": {"LOG": "warn"}}, [{"name": "a"}, {"name": "b"}], [{"name": "LOG", "value": "debug"}]],
        [{"a": {"LOG": "info", "app.toml": "x"}, "b": {"LOG": "warn"}}, [{"name": "a"}, {"name": "b"}], []],
        [{"a": {"LOG": "info"}, "b": {"LOG": "warn"}}, [{"name": "b"}, {"name": "a"}], []],
        [{}, [], []],
        [{}, [{"name": "missing"}], []],
        [{}, [{"name": "missing", "optional": True}], [{"name": "X", "value": "1"}]],
        [{"a": {"HOST": "db"}}, [], [{"name": "DB_HOST", "from": "a", "key": "HOST"}]],
        [{"a": {"HOST": "db"}}, [], [{"name": "T", "from": "a", "key": "TIMEOUT"}]],
        [{"a": {"HOST": "db"}}, [], [{"name": "T", "from": "a", "key": "TIMEOUT", "optional": True}, {"name": "U", "from": "zzz", "key": "k", "optional": True}]],
        [{"a": {"HOST": "db"}}, [], [{"name": "T", "from": "zzz", "key": "k"}]],
        [{"a": {"HOST": "db", "PORT": "5432"}}, [{"name": "a", "prefix": "DB_"}], [{"name": "DB_PORT", "value": "6000"}, {"name": "DB_PORT", "value": "7000"}]],
        [{"a": {"9LIVES": "x", "ok_1": "y", "bad-key": "z", "_under": "u"}}, [{"name": "a"}], []],
        [{"a": {"9LIVES": "x", "bad-key": "z"}}, [{"name": "a", "prefix": "P_"}], []],
        [{"a": {"K": "1"}}, [{"name": "a"}, {"name": "gone"}], [{"name": "T", "from": "a", "key": "nope"}]],
        [{"a": {"K": "from-a"}, "s": {"K": "from-s", "TOKEN": "t"}}, [{"name": "a"}, {"name": "s"}],
         [{"name": "K", "from": "a", "key": "K"}, {"name": "EXTRA", "from": "s", "key": "TOKEN"}]],
    ],
    examples=2,
    wrong_solutions=[
        '''def buildEnv(sources, envFrom, env):
    result = {}
    for e in env:
        if "value" in e:
            result[e["name"]] = e["value"]
            continue
        data = sources.get(e["from"])
        if data is None or e["key"] not in data:
            if e.get("optional"):
                continue
            return "CreateContainerConfigError: %s/%s" % (e["from"], e["key"])
        result[e["name"]] = data[e["key"]]
    for src in envFrom:
        data = sources.get(src["name"])
        if data is None:
            if src.get("optional"):
                continue
            return "CreateContainerConfigError: " + src["name"]
        for key, value in data.items():
            result[(src.get("prefix") or "") + key] = value
    return result
''',
        '''def buildEnv(sources, envFrom, env):
    result = {}
    for src in envFrom:
        data = sources.get(src["name"]) or {}
        for key, value in data.items():
            name = (src.get("prefix") or "") + key
            if name.replace("_", "").isalnum() and not name[0].isdigit():
                result.setdefault(name, value)
    for e in env:
        if "value" in e:
            result[e["name"]] = e["value"]
        else:
            data = sources.get(e["from"]) or {}
            if e["key"] in data:
                result[e["name"]] = data[e["key"]]
    return result
''',
    ],
    guide=dict(
        prereqs="The lessons *ConfigMaps* and *Secrets*: `envFrom`, `configMapKeyRef`/`secretKeyRef`, `optional`, and the precedence rules.",
        intuition="The environment is a dictionary filled in a fixed order, where later writes overwrite earlier ones: bulk imports "
                  "first, explicit entries afterwards. A required source that is missing stops everything, which is what leaves a real Pod in "
                  "`CreateContainerConfigError`.",
        hints=[
            "Process `envFrom` completely before `env`; plain dictionary assignment then gives the right precedence for free.",
            "Validate the **prefixed** name, not the raw key.",
            "Return the error string immediately at the first required-but-missing source or key.",
        ],
        brute_force="A single pass over both lists is the direct solution.",
        approach="1. Helper `valid(name)`.\n2. For each `envFrom` source: handle missing; add valid prefixed names.\n"
                 "3. For each `env` entry: literal, or resolve the reference with the optional rule.\n4. Return the dict.\n\n"
                 "**Dry run** (example): after `a`: `LOG=info` (`app.toml` skipped). After `b`: `LOG=warn`. After `env`: `LOG=debug`.",
        complexity="Time O(total keys + len(env)), space O(number of variables).",
        pitfalls="- Applying `env` before `envFrom`.\n- First-wins instead of last-wins between `envFrom` sources.\n"
                 "- Silently ignoring a missing required source.\n- Accepting names such as `app.toml` or `9LIVES` as variables.\n"
                 "- A prefix can turn an invalid key into a valid name (`P_9LIVES`).",
        follow_up="Add `$(VAR)` expansion inside `env` values, which may only refer to variables defined earlier in the list, and volume projection with `items`.",
    ),
),
]
