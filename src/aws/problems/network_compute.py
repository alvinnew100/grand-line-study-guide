_RT = {
    "rtb-pub": [["10.0.0.0/16", "local"], ["0.0.0.0/0", "igw-0a1"]],
    "rtb-app": [["10.0.0.0/16", "local"], ["0.0.0.0/0", "nat-0b2"]],
    "rtb-db": [["10.0.0.0/16", "local"]],
    "rtb-hybrid": [["10.0.0.0/16", "local"], ["0.0.0.0/0", "tgw-0c3"], ["192.168.0.0/16", "vgw-0d4"]],
    "rtb-partial": [["10.0.0.0/16", "local"], ["8.8.8.0/24", "igw-0a1"]],
}
_NACL_OPEN = [[100, "-1", 0, 65535, "0.0.0.0/0", "allow"]]
_NACL_WEB_IN = [[100, "tcp", 443, 443, "0.0.0.0/0", "allow"], [110, "tcp", 22, 22, "203.0.113.0/24", "allow"]]
_NACL_EPHEMERAL_OUT = [[100, "tcp", 1024, 65535, "0.0.0.0/0", "allow"]]
_SG_WEB = [["tcp", 443, 443, "0.0.0.0/0"], ["tcp", 22, 22, "203.0.113.0/24"]]
_CATALOG = [["t3.small", 2, 2, 208], ["t3.medium", 2, 4, 416], ["t3.large", 2, 8, 832], ["m6i.large", 2, 8, 960],
            ["m6i.xlarge", 4, 16, 1920], ["m6i.2xlarge", 8, 32, 3840], ["c6i.xlarge", 4, 8, 1700], ["r6i.large", 2, 16, 1260]]


def _pkt(src, port, sport=50000, proto="tcp"):
    return {"src": src, "protocol": proto, "dst_port": port, "src_port": sport}


PROBLEMS = [
dict(
    id="aws-subnet-public-private",
    title="Public, Private or Isolated Subnet?",
    difficulty="Easy",
    pattern="VPC",
    entry="classifySubnets",
    description=r"""
Nothing in a subnet's own settings says "public". A subnet is public **only because of its route
table**: its default route (`0.0.0.0/0`) points at an internet gateway.

Write `classifySubnets(subnets, route_tables, main_table)`:

- `subnets`: dict `subnet_id -> route_table_id`, or `null` when the subnet has no explicit association
  and therefore uses the VPC's **main route table** `main_table`.
- `route_tables`: dict `route_table_id -> list of [destination_cidr, target]`.
- Look only at the route whose destination is exactly `"0.0.0.0/0"`:
  - target starts with `"igw-"` → `"public"`
  - target starts with `"nat-"` → `"private"`
  - no such route → `"isolated"`
  - any other target (`tgw-`, `vgw-`, `eni-`, …) → `"private-custom"`

Return a dict `subnet_id -> classification`.

**Example:** `{"subnet-a": "rtb-1", "subnet-b": null}` with `rtb-1 = [["10.0.0.0/16","local"],["0.0.0.0/0","igw-1"]]`,
main `rtb-0 = [["10.0.0.0/16","local"]]` → `{"subnet-a": "public", "subnet-b": "isolated"}`
""",
    starter='''def classifySubnets(subnets, route_tables, main_table):
    pass
''',
    solution='''def classifySubnets(subnets, route_tables, main_table):
    out = {}
    for sid, rt in subnets.items():
        routes = route_tables[rt if rt is not None else main_table]
        target = None
        for dest, tgt in routes:
            if dest == "0.0.0.0/0":
                target = tgt
        if target is None:
            out[sid] = "isolated"
        elif target.startswith("igw-"):
            out[sid] = "public"
        elif target.startswith("nat-"):
            out[sid] = "private"
        else:
            out[sid] = "private-custom"
    return out
''',
    tests=[
        [{"subnet-a": "rtb-1", "subnet-b": None}, {"rtb-1": [["10.0.0.0/16", "local"], ["0.0.0.0/0", "igw-1"]], "rtb-0": [["10.0.0.0/16", "local"]]}, "rtb-0"],
        [{"s1": "rtb-pub", "s2": "rtb-app", "s3": "rtb-db"}, _RT, "rtb-db"],
        [{"s1": None, "s2": None}, _RT, "rtb-pub"],
        [{}, _RT, "rtb-db"],
        [{"s1": "rtb-hybrid"}, _RT, "rtb-db"],
        [{"s1": "rtb-partial"}, _RT, "rtb-pub"],
        [{"s1": None, "s2": "rtb-app"}, _RT, "rtb-hybrid"],
        [{"a": "r"}, {"r": []}, "r"],
        [{"a": "r"}, {"r": [["0.0.0.0/0", "eni-0123"], ["10.1.0.0/16", "local"]]}, "r"],
        [{"sub%d" % i: (None if i % 4 == 0 else ["rtb-pub", "rtb-app", "rtb-db"][i % 3]) for i in range(40)}, _RT, "rtb-app"],
    ],
    examples=2,
    wrong_solutions=[
        '''def classifySubnets(subnets, route_tables, main_table):
    out = {}
    for sid, rt in subnets.items():
        routes = route_tables[rt if rt is not None else main_table]
        if any(t.startswith("igw-") for d, t in routes):
            out[sid] = "public"
        elif any(t.startswith("nat-") for d, t in routes):
            out[sid] = "private"
        elif any(d == "0.0.0.0/0" for d, t in routes):
            out[sid] = "private-custom"
        else:
            out[sid] = "isolated"
    return out
''',
        '''def classifySubnets(subnets, route_tables, main_table):
    out = {}
    for sid, rt in subnets.items():
        if rt is None:
            out[sid] = "isolated"
            continue
        target = dict(route_tables[rt]).get("0.0.0.0/0")
        out[sid] = "isolated" if target is None else "public" if target.startswith("igw-") else "private" if target.startswith("nat-") else "private-custom"
    return out
''',
    ],
    guide=dict(
        prereqs="The VPC basics lesson: route tables, the main route table, internet and NAT gateways.",
        intuition="Follow the pointer: subnet → its route table (or the main one) → the default route → the kind of target.",
        hints=["Resolve `None` to `main_table` before anything else.",
               "Only the destination `0.0.0.0/0` matters; an `igw-` target on a narrower route does not make the subnet public.",
               "Use `startswith` on the target id."],
        brute_force="Not applicable — the direct lookup is linear in the number of routes.",
        approach="Dry run: subnet `s1` uses `rtb-partial` = `[10.0.0.0/16 → local, 8.8.8.0/24 → igw]`. There is no `0.0.0.0/0` entry, so the subnet is `isolated` for our purposes even though one narrow range goes to the internet gateway.",
        complexity="O(total routes examined) time, O(subnets) space.",
        pitfalls="Declaring a subnet public because an `igw-` target appears anywhere in the table; forgetting the main route table fallback; assuming the main table is private.",
    ),
),
dict(
    id="aws-route-longest-prefix",
    title="Route Table Longest-Prefix Match",
    difficulty="Easy",
    pattern="VPC",
    entry="routeTarget",
    description=r"""
When a packet leaves a subnet, the VPC router picks the route whose destination range contains the
packet's destination address **and is the most specific** (the longest prefix, i.e. the largest number
after the slash). The order of the routes in the table does not matter.

Write `routeTarget(routes, ip)`:

- `routes`: list of `[cidr, target]`, with distinct CIDR blocks such as `"10.0.0.0/16"` or `"0.0.0.0/0"`.
- `ip`: a dotted IPv4 address.
- Return the target of the most specific matching route, or `"no-route"` if none matches.

A CIDR block `a.b.c.d/n` contains an address when their first `n` bits are equal.

**Example:** routes `[["10.0.0.0/16","local"],["0.0.0.0/0","nat-1"],["10.20.0.0/16","pcx-9"]]`:
`10.0.3.7` → `"local"`, `10.20.1.1` → `"pcx-9"`, `52.1.2.3` → `"nat-1"`.
""",
    starter='''def routeTarget(routes, ip):
    pass
''',
    solution='''def _to_int(addr):
    a, b, c, d = (int(x) for x in addr.split("."))
    return (a << 24) | (b << 16) | (c << 8) | d

def routeTarget(routes, ip):
    x = _to_int(ip)
    best_len, best = -1, "no-route"
    for cidr, target in routes:
        net, n = cidr.split("/")
        n = int(n)
        mask = 0 if n == 0 else (0xFFFFFFFF << (32 - n)) & 0xFFFFFFFF
        if (x & mask) == (_to_int(net) & mask) and n > best_len:
            best_len, best = n, target
    return best
''',
    tests=[
        [[["10.0.0.0/16", "local"], ["0.0.0.0/0", "nat-1"], ["10.20.0.0/16", "pcx-9"]], "10.0.3.7"],
        [[["10.0.0.0/16", "local"], ["0.0.0.0/0", "nat-1"], ["10.20.0.0/16", "pcx-9"]], "10.20.1.1"],
        [[["10.0.0.0/16", "local"], ["0.0.0.0/0", "nat-1"], ["10.20.0.0/16", "pcx-9"]], "52.1.2.3"],
        [[["10.0.0.0/16", "local"]], "8.8.8.8"],
        [[], "10.0.0.1"],
        [[["0.0.0.0/0", "igw-1"], ["10.0.0.0/8", "tgw-1"], ["10.1.0.0/16", "pcx-1"], ["10.1.2.0/24", "eni-1"], ["10.1.2.3/32", "eni-2"]], "10.1.2.3"],
        [[["0.0.0.0/0", "igw-1"], ["10.0.0.0/8", "tgw-1"], ["10.1.0.0/16", "pcx-1"], ["10.1.2.0/24", "eni-1"], ["10.1.2.3/32", "eni-2"]], "10.1.2.4"],
        [[["0.0.0.0/0", "igw-1"], ["10.0.0.0/8", "tgw-1"], ["10.1.0.0/16", "pcx-1"], ["10.1.2.0/24", "eni-1"]], "10.1.3.4"],
        [[["0.0.0.0/0", "igw-1"], ["10.0.0.0/8", "tgw-1"], ["10.1.0.0/16", "pcx-1"]], "10.200.3.4"],
        [[["172.16.0.0/12", "vgw-1"], ["172.31.0.0/16", "local"]], "172.32.0.1"],
        [[["172.16.0.0/12", "vgw-1"], ["172.31.0.0/16", "local"]], "172.20.9.9"],
        [[["10.0.0.128/25", "a"], ["10.0.0.0/25", "b"], ["10.0.0.0/24", "c"]], "10.0.0.127"],
        [[["10.0.0.128/25", "a"], ["10.0.0.0/25", "b"], ["10.0.0.0/24", "c"]], "10.0.0.128"],
        [[["192.168.1.0/24", "x"], ["192.168.10.0/24", "y"]], "192.168.10.5"],
    ],
    examples=3,
    wrong_solutions=[
        '''def routeTarget(routes, ip):
    def to_int(a):
        p = [int(x) for x in a.split(".")]
        return (p[0] << 24) | (p[1] << 16) | (p[2] << 8) | p[3]
    x = to_int(ip)
    for cidr, target in routes:
        net, n = cidr.split("/")
        n = int(n)
        mask = 0 if n == 0 else (0xFFFFFFFF << (32 - n)) & 0xFFFFFFFF
        if (x & mask) == (to_int(net) & mask):
            return target
    return "no-route"
''',
        '''def routeTarget(routes, ip):
    best, best_len = "no-route", -1
    for cidr, target in routes:
        net, n = cidr.split("/")
        n = int(n)
        prefix = ".".join(net.split(".")[: n // 8])
        if ip.startswith(prefix) and n > best_len:
            best, best_len = target, n
    return best
''',
    ],
    guide=dict(
        prereqs="The VPC basics lesson (CIDR notation, route tables). Bit operations: shift and mask.",
        intuition="Convert addresses to 32-bit integers. A route matches when the top `n` bits agree; among matches keep the largest `n`.",
        hints=["`(a << 24) | (b << 16) | (c << 8) | d` turns four octets into one integer.",
               "The mask for `/n` has `n` one-bits at the top: `(0xFFFFFFFF << (32 - n)) & 0xFFFFFFFF`; treat `/0` separately or note that it yields 0.",
               "Track `best_len` starting at -1 so that a `/0` route can win when nothing else matches."],
        brute_force="Scanning every route is already optimal for a list (real routers use a trie for millions of prefixes).",
        approach="Dry run for `10.1.2.4` with routes `/0 igw`, `10.0.0.0/8 tgw`, `10.1.0.0/16 pcx`, `10.1.2.0/24 eni-1`, `10.1.2.3/32 eni-2`: the first four match, the `/32` does not (last bit pattern differs). The longest match is `/24` → `eni-1`.",
        complexity="O(R) time for R routes, O(1) space.",
        pitfalls="Returning the first match instead of the most specific; comparing dotted strings with `startswith` (breaks for prefixes that are not multiples of 8 and for `192.168.1` vs `192.168.10`); a mask that overflows 32 bits in Python.",
    ),
),
dict(
    id="aws-vpc-subnet-planner",
    title="VPC Subnet Planner",
    difficulty="Medium",
    pattern="VPC",
    entry="planSubnets",
    description=r"""
Carve a VPC's address range into non-overlapping subnets: one subnet per **tier** (public, app, data…)
in each **Availability Zone**.

Write `planSubnets(vpc_cidr, azs, tiers)`:

- `vpc_cidr`: for example `"10.0.0.0/16"` (always a valid, aligned block).
- `azs`: list of AZ names, e.g. `["a", "b", "c"]`.
- `tiers`: list of `[tier_name, prefix_length]`, e.g. `[["public", 24], ["app", 22]]`.
- Allocate in this order: tiers in the given order, and for each tier the AZs in the given order.
  Each request takes the **lowest-addressed** block of the requested size that is correctly aligned
  (its start address is a multiple of its size), lies inside the VPC and does not overlap any block
  allocated so far.
- AWS reserves 5 addresses in every subnet (network, router, DNS, future use, broadcast), so the
  usable host count is `2^(32 - prefix) - 5`.
- Return a list of `[tier_name, az, subnet_cidr, usable_hosts]` in allocation order.
- Return `[]` if any prefix is smaller than the VPC's prefix or larger than 28 (the AWS subnet size
  limits are /16 to /28), or if some request cannot be satisfied.

**Example:** `planSubnets("10.0.0.0/24", ["a","b"], [["web", 26]])`
→ `[["web","a","10.0.0.0/26",59], ["web","b","10.0.0.64/26",59]]`
""",
    starter='''def planSubnets(vpc_cidr, azs, tiers):
    pass
''',
    solution='''def planSubnets(vpc_cidr, azs, tiers):
    def to_int(a):
        p = [int(x) for x in a.split(".")]
        return (p[0] << 24) | (p[1] << 16) | (p[2] << 8) | p[3]
    def to_str(x):
        return ".".join(str((x >> s) & 255) for s in (24, 16, 8, 0))
    net, vp = vpc_cidr.split("/")
    vp = int(vp)
    base = to_int(net)
    end = base + (1 << (32 - vp))
    taken, out = [], []
    for name, p in tiers:
        if p < vp or p > 28:
            return []
        size = 1 << (32 - p)
        for az in azs:
            start = base
            while start + size <= end:
                clash = None
                for s, e in taken:
                    if start < e and s < start + size:
                        clash = e
                        break
                if clash is None:
                    break
                start = ((clash + size - 1) // size) * size
            else:
                return []
            taken.append((start, start + size))
            out.append([name, az, "%s/%d" % (to_str(start), p), size - 5])
    return out
''',
    tests=[
        ["10.0.0.0/24", ["a", "b"], [["web", 26]]],
        ["10.0.0.0/16", ["a", "b", "c"], [["public", 24], ["app", 22], ["data", 24]]],
        ["10.0.0.0/24", ["a", "b", "c"], [["web", 25]]],
        ["10.0.0.0/24", ["a"], [["web", 23]]],
        ["10.0.0.0/24", ["a"], [["tiny", 29]]],
        ["10.0.0.0/24", ["a", "b"], [["small", 28], ["big", 25]]],
        ["10.0.0.0/24", ["a", "b"], [["small", 28], ["mid", 26], ["tiny", 28]]],
        ["172.31.0.0/16", ["a"], [["all", 16]]],
        ["172.31.0.0/16", ["a", "b"], [["all", 16]]],
        ["192.168.4.0/22", ["x", "y"], [["a", 24], ["b", 23]]],
        ["10.0.0.0/16", [], [["public", 24]]],
        ["10.0.0.0/16", ["a", "b"], []],
        ["10.10.0.0/20", ["a", "b", "c"], [["pub", 26], ["app", 23], ["db", 26], ["spare", 22]]],
        ["10.0.0.0/22", ["a", "b"], [["s", 28], ["m", 25], ["l", 24], ["s2", 27]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def planSubnets(vpc_cidr, azs, tiers):
    def to_int(a):
        p = [int(x) for x in a.split(".")]
        return (p[0] << 24) | (p[1] << 16) | (p[2] << 8) | p[3]
    def to_str(x):
        return ".".join(str((x >> s) & 255) for s in (24, 16, 8, 0))
    net, vp = vpc_cidr.split("/")
    vp = int(vp)
    cur = to_int(net)
    end = cur + (1 << (32 - vp))
    out = []
    for name, p in tiers:
        if p < vp or p > 28:
            return []
        size = 1 << (32 - p)
        for az in azs:
            if cur + size > end:
                return []
            out.append([name, az, "%s/%d" % (to_str(cur), p), size - 5])
            cur += size
    return out
''',
        '''def planSubnets(vpc_cidr, azs, tiers):
    def to_int(a):
        p = [int(x) for x in a.split(".")]
        return (p[0] << 24) | (p[1] << 16) | (p[2] << 8) | p[3]
    def to_str(x):
        return ".".join(str((x >> s) & 255) for s in (24, 16, 8, 0))
    net, vp = vpc_cidr.split("/")
    vp = int(vp)
    base = to_int(net)
    end = base + (1 << (32 - vp))
    cur, out = base, []
    for name, p in tiers:
        if p < vp or p > 28:
            return []
        size = 1 << (32 - p)
        for az in azs:
            cur = ((cur + size - 1) // size) * size
            if cur + size > end:
                return []
            out.append([name, az, "%s/%d" % (to_str(cur), p), size - 2])
            cur += size
    return out
''',
    ],
    guide=dict(
        prereqs="The VPC basics lesson (CIDR arithmetic, the five reserved addresses). Integer representation of IPv4 addresses.",
        intuition="A block of prefix `p` has size `2^(32-p)` and can only start at a multiple of that size. For each request, slide along the aligned positions until the block overlaps nothing taken — a first-fit allocator.",
        hints=["Convert the VPC to `[base, end)` as integers; keep a list of taken `(start, end)` intervals.",
               "Two half-open intervals overlap when `a_start < b_end and b_start < a_end`.",
               "When a candidate clashes with a taken block, jump to the next aligned start at or after that block's end instead of stepping one block at a time."],
        brute_force="A moving cursor that never looks back is the tempting approach; it wastes or mis-aligns space when a large block follows a small one and it can never reuse the gap left behind. Trying every aligned position one by one is correct but can test thousands of positions.",
        approach="Dry run: VPC `10.0.0.0/24`, AZs a,b, tiers `small /28`, `mid /26`, `tiny /28`. small-a → .0/28, small-b → .16/28. mid (size 64): .0 clashes → jump past .16 block's end (32) aligned up to 64 → `.64/26`, then `.128/26`. tiny: .0 and .16 taken, `.32/28` is free and aligned → tiny-a, then `.48/28`. The gap left by alignment is reused.",
        complexity="O(N²) in the number of subnets N in the worst case (each request scans the taken list a few times); O(N) space.",
        pitfalls="Unaligned subnets (10.0.0.32/26 is not a valid block); subtracting 2 instead of 5; accepting /29 or a prefix shorter than the VPC's; returning a partial plan instead of `[]`.",
    ),
),
dict(
    id="aws-sg-nacl-evaluate",
    title="Security Group and Network ACL Evaluation",
    difficulty="Hard",
    pattern="VPC",
    entry="packetVerdict",
    description=r"""
A client opens a connection to an EC2 instance. Two firewalls stand in the way:

- the subnet's **network ACL** — *stateless*, numbered rules, allow **and** deny;
- the instance's **security group** — *stateful*, allow rules only.

Write `packetVerdict(packet, sg_inbound, nacl_inbound, nacl_outbound)`.

`packet = {"src": client_ip, "protocol": "tcp"|"udp", "dst_port": int, "src_port": int}` describes the
request. The reply travels back to `src` on port `src_port` (the client's ephemeral port).

**Network ACL rule**: `[number, protocol, port_from, port_to, cidr, "allow"|"deny"]`. Protocol `"-1"`
means all protocols and its port range is ignored. Rules are evaluated in **ascending rule number**
(the list may be unsorted); the **first** rule that matches decides. If no rule matches, the packet is
denied (the implicit `*` rule).

**Security group rule**: `[protocol, port_from, port_to, cidr]` (protocol `"-1"` = everything). If
**any** rule matches the packet is allowed; otherwise it is denied.

A rule matches when the protocol matches, the relevant port is within `[port_from, port_to]`, and the
relevant address is inside `cidr`.

Evaluate in this order and return the first failure:

1. Inbound NACL against the request (`src` address, `dst_port`) → else `"NACL_INBOUND_DENY"`.
2. Security group inbound against the request → else `"SG_DENY"`.
3. The reply: the security group is stateful, so the reply is allowed automatically. The outbound
   NACL is stateless and must allow the reply (address `src`, port `src_port`) → else
   `"NACL_OUTBOUND_DENY"`.
4. Otherwise `"ALLOWED"`.

**Example:** inbound NACL allows tcp 443 from anywhere, SG allows tcp 443, outbound NACL allows only
tcp 443 → a request from port 50000 gets `"NACL_OUTBOUND_DENY"`: the reply to port 50000 is dropped.
""",
    starter='''def packetVerdict(packet, sg_inbound, nacl_inbound, nacl_outbound):
    pass
''',
    solution='''def _to_int(a):
    p = [int(x) for x in a.split(".")]
    return (p[0] << 24) | (p[1] << 16) | (p[2] << 8) | p[3]

def _in_cidr(ip, cidr):
    net, n = cidr.split("/")
    n = int(n)
    mask = 0 if n == 0 else (0xFFFFFFFF << (32 - n)) & 0xFFFFFFFF
    return (_to_int(ip) & mask) == (_to_int(net) & mask)

def _match(proto, lo, hi, cidr, pkt_proto, port, ip):
    if proto != "-1" and (proto != pkt_proto or not (lo <= port <= hi)):
        return False
    return _in_cidr(ip, cidr)

def _nacl(rules, pkt_proto, port, ip):
    for num, proto, lo, hi, cidr, action in sorted(rules, key=lambda r: r[0]):
        if _match(proto, lo, hi, cidr, pkt_proto, port, ip):
            return action == "allow"
    return False

def packetVerdict(packet, sg_inbound, nacl_inbound, nacl_outbound):
    src, proto = packet["src"], packet["protocol"]
    if not _nacl(nacl_inbound, proto, packet["dst_port"], src):
        return "NACL_INBOUND_DENY"
    if not any(_match(p, lo, hi, c, proto, packet["dst_port"], src) for p, lo, hi, c in sg_inbound):
        return "SG_DENY"
    if not _nacl(nacl_outbound, proto, packet["src_port"], src):
        return "NACL_OUTBOUND_DENY"
    return "ALLOWED"
''',
    tests=[
        [_pkt("198.51.100.7", 443), [["tcp", 443, 443, "0.0.0.0/0"]], [[100, "tcp", 443, 443, "0.0.0.0/0", "allow"]], [[100, "tcp", 443, 443, "0.0.0.0/0", "allow"]]],
        [_pkt("198.51.100.7", 443), _SG_WEB, _NACL_WEB_IN, _NACL_EPHEMERAL_OUT],
        [_pkt("198.51.100.7", 22), _SG_WEB, _NACL_WEB_IN, _NACL_EPHEMERAL_OUT],
        [_pkt("203.0.113.9", 22), _SG_WEB, _NACL_WEB_IN, _NACL_EPHEMERAL_OUT],
        [_pkt("203.0.113.9", 22), [["tcp", 443, 443, "0.0.0.0/0"]], _NACL_OPEN, _NACL_OPEN],
        [_pkt("198.51.100.7", 443), _SG_WEB, [[200, "tcp", 443, 443, "0.0.0.0/0", "allow"], [100, "tcp", 0, 65535, "198.51.100.0/24", "deny"]], _NACL_OPEN],
        [_pkt("198.51.100.7", 443), _SG_WEB, [[100, "tcp", 443, 443, "0.0.0.0/0", "allow"], [200, "tcp", 0, 65535, "198.51.100.0/24", "deny"]], _NACL_OPEN],
        [_pkt("198.51.100.7", 443), _SG_WEB, [], _NACL_OPEN],
        [_pkt("198.51.100.7", 443), [], _NACL_OPEN, _NACL_OPEN],
        [_pkt("198.51.100.7", 443, 1023), _SG_WEB, _NACL_WEB_IN, _NACL_EPHEMERAL_OUT],
        [_pkt("198.51.100.7", 53, 40000, "udp"), [["-1", 0, 0, "0.0.0.0/0"]], [[100, "-1", 0, 0, "0.0.0.0/0", "allow"]], [[100, "tcp", 1024, 65535, "0.0.0.0/0", "allow"]]],
        [_pkt("198.51.100.7", 53, 40000, "udp"), [["udp", 53, 53, "198.51.100.0/24"]], [[100, "-1", 0, 0, "0.0.0.0/0", "allow"]], [[90, "udp", 1024, 65535, "198.51.100.7/32", "allow"]]],
        [_pkt("10.0.1.5", 5432), [["tcp", 5432, 5432, "10.0.1.0/24"]], _NACL_OPEN, [[50, "-1", 0, 0, "10.0.1.5/32", "deny"], [100, "-1", 0, 0, "0.0.0.0/0", "allow"]]],
        [_pkt("10.0.2.5", 5432), [["tcp", 5432, 5432, "10.0.1.0/24"]], _NACL_OPEN, _NACL_OPEN],
        [_pkt("198.51.100.7", 8080), [["tcp", 8000, 8100, "0.0.0.0/0"]], [[100, "tcp", 8000, 8100, "0.0.0.0/0", "allow"]], [[100, "tcp", 32768, 65535, "0.0.0.0/0", "allow"]]],
    ],
    examples=2,
    wrong_solutions=[
        '''def _to_int(a):
    p = [int(x) for x in a.split(".")]
    return (p[0] << 24) | (p[1] << 16) | (p[2] << 8) | p[3]
def _in(ip, cidr):
    net, n = cidr.split("/"); n = int(n)
    mask = 0 if n == 0 else (0xFFFFFFFF << (32 - n)) & 0xFFFFFFFF
    return (_to_int(ip) & mask) == (_to_int(net) & mask)
def _m(proto, lo, hi, cidr, pp, port, ip):
    return (proto == "-1" or (proto == pp and lo <= port <= hi)) and _in(ip, cidr)
def packetVerdict(packet, sg_inbound, nacl_inbound, nacl_outbound):
    src, proto, port = packet["src"], packet["protocol"], packet["dst_port"]
    ok = False
    for num, p, lo, hi, c, act in sorted(nacl_inbound):
        if _m(p, lo, hi, c, proto, port, src):
            ok = act == "allow"; break
    if not ok:
        return "NACL_INBOUND_DENY"
    if not any(_m(p, lo, hi, c, proto, port, src) for p, lo, hi, c in sg_inbound):
        return "SG_DENY"
    return "ALLOWED"
''',
        '''def _to_int(a):
    p = [int(x) for x in a.split(".")]
    return (p[0] << 24) | (p[1] << 16) | (p[2] << 8) | p[3]
def _in(ip, cidr):
    net, n = cidr.split("/"); n = int(n)
    mask = 0 if n == 0 else (0xFFFFFFFF << (32 - n)) & 0xFFFFFFFF
    return (_to_int(ip) & mask) == (_to_int(net) & mask)
def _m(proto, lo, hi, cidr, pp, port, ip):
    return (proto == "-1" or (proto == pp and lo <= port <= hi)) and _in(ip, cidr)
def _nacl(rules, pp, port, ip):
    if any(_m(p, lo, hi, c, pp, port, ip) and act == "deny" for n, p, lo, hi, c, act in rules):
        return False
    return any(_m(p, lo, hi, c, pp, port, ip) and act == "allow" for n, p, lo, hi, c, act in rules)
def packetVerdict(packet, sg_inbound, nacl_inbound, nacl_outbound):
    src, proto = packet["src"], packet["protocol"]
    if not _nacl(nacl_inbound, proto, packet["dst_port"], src):
        return "NACL_INBOUND_DENY"
    if not any(_m(p, lo, hi, c, proto, packet["dst_port"], src) for p, lo, hi, c in sg_inbound):
        return "SG_DENY"
    if not _nacl(nacl_outbound, proto, packet["src_port"], src):
        return "NACL_OUTBOUND_DENY"
    return "ALLOWED"
''',
    ],
    guide=dict(
        prereqs="The security groups versus network ACLs lesson; CIDR membership from the longest-prefix problem.",
        intuition="Three checkpoints in sequence. The ACL is a sorted first-match list and is consulted twice — once per direction — because it has no memory. The security group is an any-match list and is consulted once because it remembers the connection.",
        hints=["Write one `match(rule fields, protocol, port, ip)` helper and reuse it for both firewalls.",
               "For the ACL, sort by rule number and return at the first matching rule, whether it says allow or deny.",
               "For the reply, the port to test is the client's `src_port` and the address is still the client's address."],
        brute_force="Treating the ACL like IAM ('any deny wins, otherwise any allow') ignores rule numbers and gives wrong answers when an allow rule has a lower number than a deny rule.",
        approach="Dry run: request from 198.51.100.7:50000 to port 443; inbound ACL `[200 allow 443 from all, 100 deny all tcp from 198.51.100.0/24]`. Sorted: rule 100 matches first → deny → `NACL_INBOUND_DENY`. Swap the numbers and rule 100 (allow 443) matches first → continue to the security group.",
        complexity="O(R log R) for sorting the ACL rules plus O(R) matching; O(R) space for the sorted copy.",
        pitfalls="Skipping the outbound ACL check; checking the reply against `dst_port`; assuming the ACL list is already sorted; forgetting that protocol `-1` ignores ports; adding a security-group outbound check for the reply (stateful firewalls do not need one).",
    ),
),
dict(
    id="aws-ec2-purchase-cost",
    title="On-Demand vs Reserved vs Spot",
    difficulty="Medium",
    pattern="EC2",
    entry="cheapestPlan",
    description=r"""
Choose the cheapest way to pay for one instance during a 730-hour month. All money is in **integer
cents** so that no rounding is needed.

`cheapestPlan(job)` where `job` is a dict:

- `hours`: hours of work the instance must complete this month (0–730).
- `od_rate`: On-Demand price, cents per hour. Cost = `hours × od_rate`.
- `ri_monthly`: fixed monthly fee of a reservation, in cents (the amortised upfront part), and
  `ri_rate`: its hourly rate. A reservation is billed for **all 730 hours** whether the instance runs
  or not: cost = `ri_monthly + 730 × ri_rate`.
- `spot_rate`: Spot price, cents per hour. `interruptions`: how many times the instance is reclaimed
  during the month. Each interruption wastes `rework_hours` of progress that must be run again:
  cost = `(hours + interruptions × rework_hours) × spot_rate`.
- `interruptible`: if `False` the workload cannot tolerate interruption and Spot is not an option.
- Spot is also not an option if the total Spot hours `hours + interruptions × rework_hours` exceed 730.

Return `[plan, cost_in_cents]` with `plan` in `"on-demand"`, `"reserved"`, `"spot"`. On a tie prefer
on-demand, then reserved, then spot (the least commitment and the least risk first).

**Example:** 200 hours, On-Demand 10 c/h, reservation 0 + 6 c/h, Spot 3 c/h with 4 interruptions of 5
hours, interruptible → on-demand 2000, reserved 4380, spot 660 → `["spot", 660]`.
""",
    starter='''def cheapestPlan(job):
    pass
''',
    solution='''def cheapestPlan(job):
    options = [("on-demand", job["hours"] * job["od_rate"]),
               ("reserved", job["ri_monthly"] + 730 * job["ri_rate"])]
    spot_hours = job["hours"] + job["interruptions"] * job["rework_hours"]
    if job["interruptible"] and spot_hours <= 730:
        options.append(("spot", spot_hours * job["spot_rate"]))
    best = options[0]
    for o in options[1:]:
        if o[1] < best[1]:
            best = o
    return [best[0], best[1]]
''',
    tests=[
        [{"hours": 200, "od_rate": 10, "ri_monthly": 0, "ri_rate": 6, "spot_rate": 3, "interruptions": 4, "rework_hours": 5, "interruptible": True}],
        [{"hours": 730, "od_rate": 10, "ri_monthly": 0, "ri_rate": 6, "spot_rate": 3, "interruptions": 0, "rework_hours": 0, "interruptible": False}],
        [{"hours": 200, "od_rate": 10, "ri_monthly": 0, "ri_rate": 6, "spot_rate": 3, "interruptions": 4, "rework_hours": 5, "interruptible": False}],
        [{"hours": 0, "od_rate": 10, "ri_monthly": 0, "ri_rate": 0, "spot_rate": 0, "interruptions": 0, "rework_hours": 0, "interruptible": True}],
        [{"hours": 438, "od_rate": 10, "ri_monthly": 0, "ri_rate": 6, "spot_rate": 9, "interruptions": 30, "rework_hours": 2, "interruptible": True}],
        [{"hours": 439, "od_rate": 10, "ri_monthly": 0, "ri_rate": 6, "spot_rate": 9, "interruptions": 30, "rework_hours": 2, "interruptible": True}],
        [{"hours": 700, "od_rate": 10, "ri_monthly": 0, "ri_rate": 9, "spot_rate": 3, "interruptions": 10, "rework_hours": 4, "interruptible": True}],
        [{"hours": 700, "od_rate": 10, "ri_monthly": 0, "ri_rate": 9, "spot_rate": 3, "interruptions": 10, "rework_hours": 3, "interruptible": True}],
        [{"hours": 600, "od_rate": 20, "ri_monthly": 5000, "ri_rate": 8, "spot_rate": 7, "interruptions": 50, "rework_hours": 20, "interruptible": True}],
        [{"hours": 100, "od_rate": 50, "ri_monthly": 1000, "ri_rate": 5, "spot_rate": 10, "interruptions": 20, "rework_hours": 20, "interruptible": True}],
        [{"hours": 100, "od_rate": 5, "ri_monthly": 0, "ri_rate": 1, "spot_rate": 5, "interruptions": 0, "rework_hours": 9, "interruptible": True}],
        [{"hours": 365, "od_rate": 8, "ri_monthly": 0, "ri_rate": 4, "spot_rate": 8, "interruptions": 0, "rework_hours": 0, "interruptible": True}],
    ],
    examples=2,
    wrong_solutions=[
        '''def cheapestPlan(job):
    options = [("on-demand", job["hours"] * job["od_rate"]),
               ("reserved", job["ri_monthly"] + job["hours"] * job["ri_rate"])]
    spot_hours = job["hours"] + job["interruptions"] * job["rework_hours"]
    if job["interruptible"] and spot_hours <= 730:
        options.append(("spot", spot_hours * job["spot_rate"]))
    best = min(options, key=lambda o: o[1])
    return [best[0], best[1]]
''',
        '''def cheapestPlan(job):
    options = [("spot", job["hours"] * job["spot_rate"]),
               ("reserved", job["ri_monthly"] + 730 * job["ri_rate"]),
               ("on-demand", job["hours"] * job["od_rate"])]
    best = min(options, key=lambda o: o[1])
    return [best[0], best[1]]
''',
    ],
    guide=dict(
        prereqs="The EC2 purchasing lesson: how each option is billed and what an interruption costs.",
        intuition="Write the three cost formulas exactly as the billing rules state them, drop the options that are not allowed, and take the minimum with a stable tie-break.",
        hints=["A reservation's cost does not depend on `hours` at all.",
               "Compute the Spot hours first; they decide both eligibility and cost.",
               "Build the option list in tie-break order and replace the best only on a strictly smaller cost."],
        brute_force="Not applicable; the pitfall is modelling, not speed.",
        approach="Dry run: 438 hours, OD 10, RI 0 + 6/h, Spot 9 with 30 interruptions × 2 h. On-demand 4380; reserved 730 × 6 = 4380; spot (438 + 60) × 9 = 4482. Tie between on-demand and reserved → on-demand. At 439 hours on-demand becomes 4390 and reserved wins: the break-even utilisation is `ri_rate / od_rate` = 60 % of the month.",
        complexity="O(1).",
        pitfalls="Charging the reservation only for the hours used; ignoring rework after interruptions; offering Spot to a workload that cannot be interrupted; an unstable tie-break from `min` over a differently ordered list.",
    ),
),
dict(
    id="aws-right-size",
    title="Right-Size an Instance",
    difficulty="Medium",
    pattern="EC2",
    entry="rightSize",
    description=r"""
Right-sizing means replacing an instance with the cheapest type that still fits the measured load plus
a safety margin.

`rightSize(current, catalog, cpu_p95, mem_p95, headroom)`:

- `catalog`: list of `[name, vcpus, memory_gib, price_cents_per_hour]` (all integers). `current` is the
  name of one of them.
- `cpu_p95`, `mem_p95`: the 95th-percentile utilisation over the last two weeks, as integer
  percentages **of the current instance's** vCPUs and memory.
- `headroom`: integer percentage of extra capacity to keep free.
- Required capacity: `needed_vcpu = current_vcpus × cpu_p95/100 × (1 + headroom/100)` and likewise for
  memory. A candidate fits when its vCPUs **and** memory are both at least the needed amounts
  (fractions matter: 2.1 needed vCPUs do not fit on 2).
- Return the name of the cheapest fitting instance; break price ties by the alphabetically smallest
  name. If nothing fits (the instance is overloaded and no bigger type exists), return `current`.

Use integer arithmetic to avoid floating-point surprises:
`candidate_vcpus × 10000 >= current_vcpus × cpu_p95 × (100 + headroom)`.

**Example:** current `m6i.xlarge` (4 vCPU, 16 GiB), CPU p95 20 %, memory p95 40 %, headroom 20 % →
needs 0.96 vCPU and 7.68 GiB → the cheapest type with at least 8 GiB.
""",
    starter='''def rightSize(current, catalog, cpu_p95, mem_p95, headroom):
    pass
''',
    solution='''def rightSize(current, catalog, cpu_p95, mem_p95, headroom):
    cur = next(c for c in catalog if c[0] == current)
    need_cpu = cur[1] * cpu_p95 * (100 + headroom)
    need_mem = cur[2] * mem_p95 * (100 + headroom)
    best = None
    for name, vcpu, mem, price in catalog:
        if vcpu * 10000 >= need_cpu and mem * 10000 >= need_mem:
            if best is None or (price, name) < best:
                best = (price, name)
    return best[1] if best else current
''',
    tests=[
        ["m6i.xlarge", _CATALOG, 20, 40, 20],
        ["m6i.2xlarge", _CATALOG, 90, 90, 20],
        ["m6i.xlarge", _CATALOG, 45, 20, 10],
        ["m6i.xlarge", _CATALOG, 50, 20, 0],
        ["m6i.xlarge", _CATALOG, 51, 20, 0],
        ["t3.small", _CATALOG, 5, 5, 50],
        ["m6i.2xlarge", _CATALOG, 10, 45, 10],
        ["m6i.2xlarge", _CATALOG, 10, 46, 10],
        ["t3.large", _CATALOG, 100, 100, 0],
        ["c6i.xlarge", _CATALOG, 60, 30, 25],
        ["a", [["a", 4, 8, 100], ["c", 2, 4, 50], ["b", 2, 4, 50]], 30, 30, 20],
        ["a", [["a", 4, 8, 100]], 0, 0, 0],
        ["r6i.large", _CATALOG, 20, 80, 30],
    ],
    examples=2,
    wrong_solutions=[
        '''def rightSize(current, catalog, cpu_p95, mem_p95, headroom):
    cur = next(c for c in catalog if c[0] == current)
    need_cpu = cur[1] * cpu_p95 // 100
    need_mem = cur[2] * mem_p95 // 100
    fits = [(p, n) for n, v, m, p in catalog if v >= need_cpu and m >= need_mem]
    return min(fits)[1] if fits else current
''',
        '''def rightSize(current, catalog, cpu_p95, mem_p95, headroom):
    cur = next(c for c in catalog if c[0] == current)
    need_cpu = cur[1] * cpu_p95 * (100 + headroom)
    need_mem = cur[2] * mem_p95 * (100 + headroom)
    best = None
    for name, vcpu, mem, price in catalog:
        if vcpu * 10000 >= need_cpu and mem * 10000 >= need_mem and price < cur[3]:
            if best is None or price < best[0]:
                best = (price, name)
    return best[1] if best else current
''',
    ],
    guide=dict(
        prereqs="The EC2 purchasing and right-sizing lesson; tuples compare element by element in Python.",
        intuition="Translate percentages of the current machine into absolute needs, inflate by the headroom, then run a filtered minimum over the catalogue.",
        hints=["Find the current row first — every percentage is relative to it.",
               "Multiply everything out to avoid division: compare `vcpu × 10000` with `cur_vcpu × p95 × (100 + headroom)`.",
               "Use the tuple `(price, name)` as the sort key so that the tie-break comes for free."],
        brute_force="Sorting the whole catalogue by price and scanning is O(n log n); a single pass with a running best is O(n).",
        approach="Dry run: current m6i.2xlarge (8 vCPU, 32 GiB), CPU 10 %, memory 45 %, headroom 10 %. Needs 0.88 vCPU and 15.84 GiB. Types with ≥ 16 GiB: r6i.large (1260), m6i.xlarge (1920), m6i.2xlarge (3840) → `r6i.large`. At 46 % memory the need is 16.19 GiB, so only m6i.2xlarge fits → stay.",
        complexity="O(n) time over the catalogue, O(1) space.",
        pitfalls="Integer division that floors the requirement; forgetting headroom; only considering cheaper types (an overloaded instance should be allowed to grow — but here, when nothing fits we keep the current one); ignoring the name tie-break.",
    ),
),
dict(
    id="aws-ebs-performance",
    title="EBS Volume IOPS and Throughput",
    difficulty="Medium",
    pattern="EBS",
    entry="ebsPerformance",
    description=r"""
Each EBS volume type has its own rules linking size, **IOPS** (input/output operations per second) and
**throughput** (MiB per second). Implement the rules below (a simplified version of the published
limits) and reject impossible configurations.

`ebsPerformance(volume_type, size_gib, iops, throughput)` returns `[iops, throughput_mib_s]`, or `[]`
when the configuration is invalid. `iops` and `throughput` are the provisioned values or `null` for
"use the default".

| type | size (GiB) | IOPS | throughput (MiB/s) |
|---|---|---|---|
| `gp2` | 1–16384 | `min(16000, max(100, 3 × size))`; provisioned values are ignored | 128 if size ≤ 170, otherwise 250 |
| `gp3` | 1–65536 | default 3000; valid 3000–80000 and at most `500 × size` | default 125; valid 125–2000 and at most `0.25 × IOPS` |
| `io2` | 4–65536 | **required**; valid 100–256000 and at most `1000 × size` | `min(4000, IOPS × 256 // 1024)`; provisioned value ignored |
| `st1` | 125–16384 | always 500 (provisioned value ignored) | `min(500, 40 × size // 1024)` |

For `gp3`, the default IOPS of 3000 is always valid, whatever the size. Any other volume type, or a
size outside the range, or an invalid provisioned value → `[]`.

**Example:** `ebsPerformance("gp3", 100, 12000, 500)` → `[12000, 500]`;
`ebsPerformance("gp3", 10, 6000, null)` → `[]` (10 GiB allows at most 5000 IOPS).
""",
    starter='''def ebsPerformance(volume_type, size_gib, iops, throughput):
    pass
''',
    solution='''def ebsPerformance(volume_type, size_gib, iops, throughput):
    if volume_type == "gp2":
        if not 1 <= size_gib <= 16384:
            return []
        return [min(16000, max(100, 3 * size_gib)), 128 if size_gib <= 170 else 250]
    if volume_type == "gp3":
        if not 1 <= size_gib <= 65536:
            return []
        if iops is None:
            iops = 3000
        elif not 3000 <= iops <= 80000 or (iops > 3000 and iops > 500 * size_gib):
            return []
        if throughput is None:
            throughput = 125
        elif not 125 <= throughput <= 2000 or throughput * 4 > iops:
            return []
        return [iops, throughput]
    if volume_type == "io2":
        if not 4 <= size_gib <= 65536 or iops is None:
            return []
        if not 100 <= iops <= 256000 or iops > 1000 * size_gib:
            return []
        return [iops, min(4000, iops * 256 // 1024)]
    if volume_type == "st1":
        if not 125 <= size_gib <= 16384:
            return []
        return [500, min(500, 40 * size_gib // 1024)]
    return []
''',
    tests=[
        ["gp3", 100, 12000, 500],
        ["gp3", 10, 6000, None],
        ["gp2", 20, None, None],
        ["gp2", 500, None, None],
        ["gp2", 8000, 99999, 99999],
        ["gp2", 170, None, None],
        ["gp2", 171, None, None],
        ["gp3", 1, None, None],
        ["gp3", 160, 80000, 2000],
        ["gp3", 159, 80000, 2000],
        ["gp3", 100, 3000, 751],
        ["gp3", 100, 3000, 750],
        ["gp3", 100, 2999, None],
        ["gp3", 100, None, 124],
        ["gp3", 70000, None, None],
        ["io2", 100, None, None],
        ["io2", 100, 100000, None],
        ["io2", 100, 100001, None],
        ["io2", 4, 400, 9999],
        ["io2", 3, 100, None],
        ["io2", 1000, 64000, None],
        ["st1", 124, None, None],
        ["st1", 2048, None, None],
        ["st1", 16384, 7, 7],
        ["sc9", 100, None, None],
        ["gp2", 0, None, None],
    ],
    examples=3,
    wrong_solutions=[
        '''def ebsPerformance(volume_type, size_gib, iops, throughput):
    if volume_type == "gp2":
        return [min(16000, 3 * size_gib), 250]
    if volume_type == "gp3":
        return [iops or 3000, throughput or 125]
    if volume_type == "io2":
        return [iops, min(4000, iops * 256 // 1024)] if iops else []
    if volume_type == "st1":
        return [500, min(500, 40 * size_gib // 1024)]
    return []
''',
        '''def ebsPerformance(volume_type, size_gib, iops, throughput):
    if volume_type == "gp2":
        if not 1 <= size_gib <= 16384:
            return []
        return [min(16000, max(100, 3 * size_gib)), 128 if size_gib <= 170 else 250]
    if volume_type == "gp3":
        if not 1 <= size_gib <= 65536:
            return []
        iops = 3000 if iops is None else iops
        if not 3000 <= iops <= 80000 or iops > 500 * size_gib:
            return []
        throughput = 125 if throughput is None else throughput
        if not 125 <= throughput <= 2000:
            return []
        return [iops, throughput]
    if volume_type == "io2":
        if not 4 <= size_gib <= 65536 or iops is None:
            return []
        if not 100 <= iops <= 256000 or iops > 1000 * size_gib:
            return []
        return [iops, min(4000, iops * 256 // 1024)]
    if volume_type == "st1":
        if not 125 <= size_gib <= 16384:
            return []
        return [500, min(500, 40 * size_gib // 1024)]
    return []
''',
    ],
    guide=dict(
        prereqs="The EBS lesson: what IOPS and throughput mean and how gp2, gp3, io2 and st1 differ.",
        intuition="One branch per volume type. In each branch validate the size, then the provisioned numbers, then compute what the volume delivers. gp2 and st1 derive performance from size; gp3 and io2 let you buy it, within ratios.",
        hints=["Handle `None` defaults before range checks.",
               "The gp3 throughput rule `≤ 0.25 × IOPS` is safest as `throughput × 4 <= iops`.",
               "A 1 GiB gp3 volume still gets 3000 IOPS — the `500 × size` ratio only limits IOPS provisioned above the baseline."],
        brute_force="Not applicable — this is rule transcription; the risk is missing a boundary.",
        approach="Dry run `gp3, 100 GiB, iops 3000, throughput 751`: size fine; IOPS at baseline; throughput in range but 751 × 4 = 3004 > 3000 → invalid → `[]`. With 750 the product equals 3000 → `[3000, 750]`.",
        complexity="O(1).",
        pitfalls="Rejecting small gp3 volumes at the default 3000 IOPS; forgetting the gp2 floor of 100 IOPS and cap of 16000; letting io2 run without provisioned IOPS; not rejecting unknown types.",
    ),
),
]
