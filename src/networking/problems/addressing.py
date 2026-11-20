PROBLEMS = [
dict(
    id="net-ipv4-int",
    title="IPv4 Address and Integer Conversion",
    difficulty="Easy",
    pattern="Addressing",
    entry="ipv4_convert",
    description=r"""
An IPv4 address is just a 32-bit unsigned number. The dotted form `a.b.c.d` writes its four bytes in
decimal, most significant byte first (network byte order).

Write `ipv4_convert(value)` that converts in **both directions**:

- if `value` is a string such as `"192.168.1.10"`, return the integer `a*2^24 + b*2^16 + c*2^8 + d`;
- if `value` is an integer in `[0, 2^32 - 1]`, return the dotted string with no leading zeros.

All inputs are valid.

**Example:** `"10.0.0.1"` → `167772161`

**Example:** `3232235786` → `"192.168.1.10"`
""",
    starter='''def ipv4_convert(value):
    pass
''',
    solution='''def ipv4_convert(value):
    if isinstance(value, str):
        n = 0
        for part in value.split("."):
            n = (n << 8) | int(part)
        return n
    return ".".join(str((value >> s) & 255) for s in (24, 16, 8, 0))
''',
    tests=[
        ["10.0.0.1"], [3232235786], ["0.0.0.0"], [0], ["255.255.255.255"], [4294967295],
        ["1.2.3.4"], [16909060], ["127.0.0.1"], [2130706433], ["172.16.254.3"], [256], ["0.0.1.0"], [2886794753],
    ],
    examples=2,
    wrong_solutions=[
        '''def ipv4_convert(value):
    if isinstance(value, str):
        n = 0
        for i, part in enumerate(value.split(".")):
            n |= int(part) << (8 * i)
        return n
    return ".".join(str((value >> s) & 255) for s in (0, 8, 16, 24))
''',
        '''def ipv4_convert(value):
    if isinstance(value, str):
        return int("".join(value.split(".")))
    return str(value)
''',
    ],
    guide=dict(
        prereqs="Bit shifts and masks; the lesson *IPv4 addressing, subnets, CIDR and NAT*.",
        intuition="Treat the address as a base-256 number with four digits. Reading it is the same loop you would use to parse a decimal string, with 256 in place of 10; writing it peels the digits off with shifts and a `& 255` mask.",
        hints=[
            "Which of the four numbers is worth the most? The leftmost one is multiplied by 2^24.",
            "Accumulate with `n = n * 256 + part` (or `(n << 8) | part`) while walking the parts left to right.",
            "For the reverse direction, `(value >> 24) & 255` is the first octet, `(value >> 16) & 255` the second, and so on.",
        ],
        brute_force="Multiply each octet by an explicit power of 256 and add; for the reverse use repeated `divmod(value, 256)` and reverse the digits. Both are O(1), so there is nothing slower to improve on; the bit version is simply the idiomatic one.",
        approach="""1. If the input is a string, split on `.` and fold: start with `n = 0`, then for each part `n = (n << 8) | int(part)`.
2. Otherwise extract the bytes with shifts of 24, 16, 8 and 0, masking each with 255, and join with dots.

**Dry run** for `"10.0.0.1"`: `n=10` → `10*256+0 = 2560` → `2560*256+0 = 655360` → `655360*256+1 = 167772161`.
Reverse: `167772161 >> 24 = 10`, `(>>16)&255 = 0`, `(>>8)&255 = 0`, `&255 = 1` → `10.0.0.1`.""",
        complexity="Time O(1) and space O(1): always four octets.",
        pitfalls="Reversing the byte order (little-endian) gives a valid-looking but wrong number. Concatenating the decimal digits is not the same as base 256. Remember `0` must print as `0.0.0.0`, not an empty string.",
        follow_up="Add validation (exactly four parts, each 0–255, no leading zeros), or support IPv6 with eight 16-bit groups and `::` compression.",
    ),
),
dict(
    id="net-cidr-contains",
    title="Is an Address Inside a CIDR Block?",
    difficulty="Easy",
    pattern="Addressing",
    entry="in_cidr",
    description=r"""
A CIDR block `a.b.c.d/p` names every address whose first `p` bits equal the first `p` bits of `a.b.c.d`.

Write `in_cidr(ip, cidr)` returning `True` when the dotted IPv4 address `ip` belongs to the block.

- `p` is between 0 and 32. `/0` contains every address; `/32` contains exactly one.
- The block may be written with host bits set (`"10.9.8.7/8"` means the same as `"10.0.0.0/8"`).

**Example:** `ip = "192.168.5.130"`, `cidr = "192.168.5.128/25"` → `True`

**Example:** `ip = "192.168.5.127"`, `cidr = "192.168.5.128/25"` → `False`
""",
    starter='''def in_cidr(ip: str, cidr: str) -> bool:
    pass
''',
    solution='''def in_cidr(ip, cidr):
    def to_int(s):
        n = 0
        for part in s.split("."):
            n = (n << 8) | int(part)
        return n
    base, p = cidr.split("/")
    p = int(p)
    mask = ((1 << p) - 1) << (32 - p)
    return (to_int(ip) & mask) == (to_int(base) & mask)
''',
    tests=[
        ["192.168.5.130", "192.168.5.128/25"],
        ["192.168.5.127", "192.168.5.128/25"],
        ["8.8.8.8", "0.0.0.0/0"],
        ["10.200.3.4", "10.9.8.7/8"],
        ["11.0.0.0", "10.0.0.0/8"],
        ["172.16.0.1", "172.16.0.1/32"],
        ["172.16.0.2", "172.16.0.1/32"],
        ["172.31.255.255", "172.16.0.0/12"],
        ["172.32.0.0", "172.16.0.0/12"],
        ["192.168.100.1", "192.168.10.0/24"],
        ["10.1.19.200", "10.1.16.0/22"],
        ["10.1.20.0", "10.1.16.0/22"],
        ["255.255.255.255", "128.0.0.0/1"],
        ["127.255.255.255", "128.0.0.0/1"],
    ],
    examples=2,
    wrong_solutions=[
        '''def in_cidr(ip, cidr):
    base, p = cidr.split("/")
    k = int(p) // 8
    return ip.split(".")[:k] == base.split(".")[:k]
''',
        '''def in_cidr(ip, cidr):
    base, p = cidr.split("/")
    return ip.startswith(base.rsplit(".", 1)[0])
''',
    ],
    guide=dict(
        prereqs="Problem *IPv4 Address and Integer Conversion*; bitwise AND.",
        intuition="Membership is a comparison of the top `p` bits. Build a mask with `p` ones followed by `32 - p` zeros, AND it with both addresses and compare what is left.",
        hints=[
            "Convert both dotted strings to 32-bit integers first; strings cannot be compared bit by bit.",
            "The mask for `/p` is `((1 << p) - 1) << (32 - p)`. Check it by hand for `/24` and `/0`.",
            "Mask **both** sides: the block itself may have host bits set.",
        ],
        brute_force="Enumerate every address in the block and test for equality. A `/8` has 16 million addresses, so this is O(2^(32-p)) and useless for large blocks.",
        approach="""1. Parse the prefix length `p` and the base address.
2. `mask = ((1 << p) - 1) << (32 - p)`.
3. Return `(ip & mask) == (base & mask)`.

**Dry run:** `192.168.5.130` in `192.168.5.128/25`. The mask is `255.255.255.128`. Last octet of the address: `130 = 1000 0010`, AND `1000 0000` gives `128`. Last octet of the base: `128 & 128 = 128`. The first three octets are identical, so the masked values match → `True`. For `.127 = 0111 1111` the AND gives `0`, which differs from `128` → `False`.""",
        complexity="Time O(1), space O(1).",
        pitfalls="Comparing whole octets only works for /8, /16 and /24. In languages with 32-bit integers a shift by 32 is undefined, so `/0` needs care; Python integers are unbounded, which is why the mask is built by shifting left rather than by inverting.",
        follow_up="Given many blocks, find the most specific one containing an address (see *Longest-Prefix-Match Routing*).",
    ),
),
dict(
    id="net-subnet-info",
    title="Subnet Mask, Network, Broadcast and Host Count",
    difficulty="Easy",
    pattern="Addressing",
    entry="subnet_info",
    description=r"""
Given an interface address in CIDR form such as `"192.168.10.77/26"`, return a list
`[mask, network, broadcast, usable_hosts]`:

- `mask`: the dotted subnet mask (`p` one bits then zeros);
- `network`: the address with every host bit cleared;
- `broadcast`: the address with every host bit set;
- `usable_hosts`: for prefixes `/0`–`/30` this is `2^(32-p) - 2` (network and broadcast are reserved);
  for `/31` it is `2` (point-to-point links, RFC 3021); for `/32` it is `1`.

**Example:** `"192.168.10.77/26"` → `["255.255.255.192", "192.168.10.64", "192.168.10.127", 62]`
""",
    starter='''def subnet_info(cidr: str) -> list:
    pass
''',
    solution='''def subnet_info(cidr):
    addr, p = cidr.split("/")
    p = int(p)
    n = 0
    for part in addr.split("."):
        n = (n << 8) | int(part)
    mask = ((1 << p) - 1) << (32 - p)
    net = n & mask
    bcast = net | (mask ^ 0xFFFFFFFF)
    def dotted(v):
        return ".".join(str((v >> s) & 255) for s in (24, 16, 8, 0))
    if p == 32:
        hosts = 1
    elif p == 31:
        hosts = 2
    else:
        hosts = (1 << (32 - p)) - 2
    return [dotted(mask), dotted(net), dotted(bcast), hosts]
''',
    tests=[
        ["192.168.10.77/26"], ["10.0.0.1/8"], ["172.16.5.4/12"], ["192.168.1.1/24"], ["192.168.1.255/24"],
        ["10.1.2.3/30"], ["10.1.2.3/31"], ["10.1.2.3/32"], ["0.0.0.0/0"], ["203.0.113.200/29"],
        ["100.64.33.7/10"], ["10.20.30.40/22"], ["255.255.255.255/1"],
    ],
    examples=1,
    wrong_solutions=[
        '''def subnet_info(cidr):
    addr, p = cidr.split("/")
    p = int(p)
    n = 0
    for part in addr.split("."):
        n = (n << 8) | int(part)
    mask = ((1 << p) - 1) << (32 - p)
    net = n & mask
    bcast = net | (mask ^ 0xFFFFFFFF)
    def dotted(v):
        return ".".join(str((v >> s) & 255) for s in (24, 16, 8, 0))
    return [dotted(mask), dotted(net), dotted(bcast), (1 << (32 - p)) - 2]
''',
        '''def subnet_info(cidr):
    addr, p = cidr.split("/")
    p = int(p)
    n = 0
    for part in addr.split("."):
        n = (n << 8) | int(part)
    mask = ((1 << p) - 1) << (32 - p)
    net = n & mask
    bcast = net + 255
    def dotted(v):
        return ".".join(str((v >> s) & 255) for s in (24, 16, 8, 0))
    hosts = 1 if p == 32 else 2 if p == 31 else (1 << (32 - p)) - 2
    return [dotted(mask), dotted(net), dotted(bcast & 0xFFFFFFFF), hosts]
''',
    ],
    guide=dict(
        prereqs="Problems *IPv4 Address and Integer Conversion* and *Is an Address Inside a CIDR Block?*.",
        intuition="Everything falls out of one mask. AND with the mask clears the host bits (network); OR with the inverted mask sets them (broadcast); the number of host bits gives the block size.",
        hints=[
            "Compute the 32-bit mask first, exactly as in the CIDR membership problem.",
            "The inverted mask (`mask ^ 0xFFFFFFFF`) has ones precisely in the host positions.",
            "Handle `/31` and `/32` separately for the host count; the generic formula gives 0 and -1.",
        ],
        brute_force="Work octet by octet with special cases for where the prefix boundary lands. It works but needs fiddly branching; the integer approach removes all of it.",
        approach="""1. Convert the address to an integer `n` and build `mask`.
2. `network = n & mask`, `broadcast = network | ~mask` (restricted to 32 bits).
3. Hosts: `2^(32-p) - 2`, except 2 for `/31` and 1 for `/32`.
4. Convert the three integers back to dotted form.

**Dry run** `192.168.10.77/26`: host bits = 6, so the mask ends in `1100 0000 = 192`. `77 = 0100 1101`; AND `192` → `64`; OR `0011 1111` → `127`. Hosts `2^6 - 2 = 62`.""",
        complexity="Time O(1), space O(1).",
        pitfalls="`~mask` in Python is a negative number; XOR with `0xFFFFFFFF` instead. The broadcast is not always `.255`. Forgetting the `/31` and `/32` special cases is the most common interview slip.",
        follow_up="Return the first and last usable host, or decide whether two interface addresses are on the same subnet.",
    ),
),
dict(
    id="net-split-subnets",
    title="Split a Network into N Subnets",
    difficulty="Medium",
    pattern="Addressing",
    entry="split_network",
    description=r"""
You are given a block such as `"10.0.0.0/22"` and need at least `n` equal-sized subnets.

Borrow the **smallest** number of bits `k` such that `2^k >= n`, giving a new prefix length `p + k`,
and return **all** `2^k` resulting subnets in ascending address order as CIDR strings.

- Clear any host bits in the input block first (`"10.0.1.7/22"` is treated as `"10.0.0.0/22"`).
- `n >= 1`. For `n = 1` return the (normalised) block itself.
- If `p + k > 32` the split is impossible: return `[]`.

**Example:** `cidr = "192.168.0.0/24"`, `n = 3` → `["192.168.0.0/26", "192.168.0.64/26", "192.168.0.128/26", "192.168.0.192/26"]`
""",
    starter='''def split_network(cidr: str, n: int) -> list:
    pass
''',
    solution='''def split_network(cidr, n):
    addr, p = cidr.split("/")
    p = int(p)
    base = 0
    for part in addr.split("."):
        base = (base << 8) | int(part)
    base &= ((1 << p) - 1) << (32 - p)
    k = 0
    while (1 << k) < n:
        k += 1
    q = p + k
    if q > 32:
        return []
    step = 1 << (32 - q)
    out = []
    for i in range(1 << k):
        v = base + i * step
        out.append(".".join(str((v >> s) & 255) for s in (24, 16, 8, 0)) + "/" + str(q))
    return out
''',
    tests=[
        ["192.168.0.0/24", 3], ["10.0.0.0/22", 4], ["10.0.1.7/22", 2], ["172.16.0.0/16", 1],
        ["192.168.1.0/30", 4], ["192.168.1.0/30", 5], ["192.168.1.4/32", 1], ["192.168.1.4/32", 2],
        ["10.0.0.0/8", 5], ["10.10.0.0/20", 16], ["10.10.0.0/20", 17], ["0.0.0.0/0", 2], ["203.0.113.128/25", 7],
    ],
    examples=1,
    wrong_solutions=[
        '''def split_network(cidr, n):
    addr, p = cidr.split("/")
    p = int(p)
    base = 0
    for part in addr.split("."):
        base = (base << 8) | int(part)
    base &= ((1 << p) - 1) << (32 - p)
    k = n.bit_length()
    q = p + k
    if q > 32:
        return []
    step = 1 << (32 - q)
    return [".".join(str(((base + i * step) >> s) & 255) for s in (24, 16, 8, 0)) + "/" + str(q) for i in range(1 << k)]
''',
        '''def split_network(cidr, n):
    addr, p = cidr.split("/")
    p = int(p)
    base = 0
    for part in addr.split("."):
        base = (base << 8) | int(part)
    k = 0
    while (1 << k) < n:
        k += 1
    q = p + k
    if q > 32:
        return []
    step = 1 << (32 - q)
    return [".".join(str(((base + i * step) >> s) & 255) for s in (24, 16, 8, 0)) + "/" + str(q) for i in range(n)]
''',
    ],
    guide=dict(
        prereqs="Problem *Subnet Mask, Network, Broadcast and Host Count*; powers of two.",
        intuition="Each borrowed bit doubles the number of subnets and halves their size. Once you know the new prefix `q`, consecutive subnets are simply `2^(32-q)` addresses apart.",
        hints=[
            "How many bits do you need to count to `n` distinct values? That is `ceil(log2(n))`.",
            "Avoid floating-point logs: loop `k` upward until `1 << k >= n`.",
            "Subnet `i` starts at `base + i * 2^(32 - q)`; format each as dotted plus `/q`.",
        ],
        brute_force="Enumerate every address in the block and group them by their top `q` bits. That is O(2^(32-p)) work for something that only needs O(2^k) outputs.",
        approach="""1. Normalise the base address by masking with the original prefix.
2. Find the smallest `k` with `2^k >= n`; let `q = p + k`. If `q > 32`, return `[]`.
3. `step = 2^(32-q)`; emit `base + i*step` for `i = 0 .. 2^k - 1`.

**Dry run** `192.168.0.0/24`, `n = 3`: `k = 2` (4 ≥ 3), `q = 26`, `step = 64`. Subnets start at `.0`, `.64`, `.128`, `.192`.""",
        complexity="Time and space O(2^k), the size of the answer.",
        pitfalls="`n.bit_length()` is off by one for exact powers of two (4 needs 2 bits, not 3). Returning only `n` subnets instead of all `2^k` leaves part of the block unaccounted for. Forgetting to clear host bits yields misaligned subnets.",
        follow_up="Variable-length subnet masking: given a list of required host counts, allocate the smallest fitting block for each, largest first.",
    ),
),
dict(
    id="net-longest-prefix-match",
    title="Longest-Prefix-Match Routing",
    difficulty="Medium",
    pattern="Routing",
    entry="route_lookup",
    description=r"""
A router's forwarding table is a list of `[cidr, next_hop]` entries. To forward a packet it selects, among
all entries whose block contains the destination, the one with the **longest prefix** (the most specific).

Write `route_lookup(routes, destinations)` returning the chosen `next_hop` for every destination address.

- If no entry matches, the answer is `"unreachable"`.
- If two matching entries have the same prefix length, the one that appears **first** in `routes` wins.
- A `0.0.0.0/0` entry is a default route: it matches everything but loses to anything more specific.
- Entries may be written with host bits set; mask before comparing.

**Example:**
`routes = [["0.0.0.0/0","isp"], ["10.0.0.0/8","core"], ["10.1.0.0/16","dc1"], ["10.1.2.0/24","rack7"]]`,
`destinations = ["10.1.2.9", "10.1.9.9", "10.200.0.1", "8.8.8.8"]` → `["rack7", "dc1", "core", "isp"]`
""",
    starter='''def route_lookup(routes: list, destinations: list) -> list:
    pass
''',
    solution='''def route_lookup(routes, destinations):
    def to_int(s):
        n = 0
        for part in s.split("."):
            n = (n << 8) | int(part)
        return n
    table = {}
    for cidr, hop in routes:
        addr, p = cidr.split("/")
        p = int(p)
        mask = ((1 << p) - 1) << (32 - p)
        table.setdefault((p, to_int(addr) & mask), hop)
    lengths = sorted({p for p, _ in table}, reverse=True)
    out = []
    for d in destinations:
        n = to_int(d)
        ans = "unreachable"
        for p in lengths:
            mask = ((1 << p) - 1) << (32 - p)
            if (p, n & mask) in table:
                ans = table[(p, n & mask)]
                break
        out.append(ans)
    return out
''',
    tests=[
        [[["0.0.0.0/0", "isp"], ["10.0.0.0/8", "core"], ["10.1.0.0/16", "dc1"], ["10.1.2.0/24", "rack7"]],
         ["10.1.2.9", "10.1.9.9", "10.200.0.1", "8.8.8.8"]],
        [[["10.0.0.0/8", "a"]], ["11.0.0.1", "10.0.0.1"]],
        [[], ["1.2.3.4"]],
        [[["10.0.0.0/8", "a"]], []],
        [[["10.1.2.0/24", "rack"], ["10.0.0.0/8", "core"], ["0.0.0.0/0", "isp"]], ["10.1.2.3", "10.1.3.3", "9.9.9.9"]],
        [[["192.168.1.0/24", "first"], ["192.168.1.77/24", "second"]], ["192.168.1.5"]],
        [[["192.168.1.128/25", "hi"], ["192.168.1.0/25", "lo"], ["192.168.1.0/24", "all"]], ["192.168.1.127", "192.168.1.128", "192.168.2.1"]],
        [[["172.16.0.5/32", "host"], ["172.16.0.0/16", "net"]], ["172.16.0.5", "172.16.0.6"]],
        [[["0.0.0.0/0", "gw"]], ["255.255.255.255", "0.0.0.0"]],
        [[["10.0.0.0/9", "west"], ["10.128.0.0/9", "east"], ["10.64.0.0/10", "mid"]], ["10.63.255.255", "10.64.0.0", "10.127.9.9", "10.128.0.0"]],
        [[["10.%d.0.0/16" % i, "r%d" % i] for i in range(200)] + [["10.0.0.0/8", "agg"]],
         ["10.%d.3.4" % i for i in range(0, 256, 5)]],
        [[["100.64.0.0/10", "cgn"], ["100.64.0.0/11", "cgn-a"], ["100.96.0.0/11", "cgn-b"], ["100.100.100.0/24", "lab"]],
         ["100.100.100.100", "100.100.101.1", "100.65.1.1", "100.128.0.1"]],
    ],
    examples=1,
    wrong_solutions=[
        '''def route_lookup(routes, destinations):
    def to_int(s):
        n = 0
        for part in s.split("."):
            n = (n << 8) | int(part)
        return n
    out = []
    for d in destinations:
        n = to_int(d)
        ans = "unreachable"
        for cidr, hop in routes:
            addr, p = cidr.split("/")
            p = int(p)
            mask = ((1 << p) - 1) << (32 - p)
            if (n & mask) == (to_int(addr) & mask):
                ans = hop
                break
        out.append(ans)
    return out
''',
        '''def route_lookup(routes, destinations):
    def to_int(s):
        n = 0
        for part in s.split("."):
            n = (n << 8) | int(part)
        return n
    out = []
    for d in destinations:
        n = to_int(d)
        best, ans = -1, "unreachable"
        for cidr, hop in routes:
            addr, p = cidr.split("/")
            p = int(p)
            mask = ((1 << p) - 1) << (32 - p)
            if (n & mask) == (to_int(addr) & mask) and p >= best:
                best, ans = p, hop
        out.append(ans)
    return out
''',
    ],
    guide=dict(
        prereqs="Problem *Is an Address Inside a CIDR Block?*; hash maps; the lesson on routing.",
        intuition="Several routes can match; specificity decides. Either scan every route and keep the longest match, or index routes by `(prefix length, masked network)` and probe from /32 downward, stopping at the first hit.",
        hints=[
            "Start with the simple scan: for each destination, test every route and remember the best prefix length seen so far.",
            "Use a strict `>` when comparing prefix lengths so the earlier of two equal-length routes survives.",
            "To go faster, store routes in a dict keyed by `(p, network)` and try the distinct prefix lengths in descending order.",
        ],
        brute_force="For each destination test all `R` routes: O(D·R). Perfectly acceptable for small tables and a fine first answer in an interview.",
        approach="""1. Pre-process: for each route compute `(p, base & mask)` and store the first next hop seen for that key.
2. Collect the distinct prefix lengths, sorted longest first.
3. For each destination, mask it with each length in turn and look the pair up; the first hit is the longest match.

**Dry run:** destination `10.1.9.9`. Try /24 → `10.1.9.0` not present. Try /16 → `10.1.0.0` present → `dc1`. We never reach /8 or /0.""",
        complexity="Pre-processing O(R). Each lookup probes at most 33 prefix lengths, so O(1) per destination with respect to table size; space O(R). Real routers use tries or TCAM hardware for the same job.",
        pitfalls="Returning the first matching route (order-dependent, wrong). Using `>=` lets a later duplicate override an earlier one. Forgetting the default route must lose to every more specific entry.",
        follow_up="Implement the lookup with a binary trie so that a lookup walks at most 32 nodes and supports route insertion and deletion.",
    ),
),
dict(
    id="net-internet-checksum",
    title="Internet Checksum",
    difficulty="Easy",
    pattern="Error Detection",
    entry="internet_checksum",
    description=r"""
IPv4, ICMP, UDP and TCP all protect their headers with the same 16-bit ones' complement checksum (RFC 1071).

Given `data`, a list of byte values (0–255), compute it:

1. If the number of bytes is odd, append one zero byte.
2. Treat the bytes as big-endian 16-bit words and add them all.
3. While the sum does not fit in 16 bits, add the overflow (the bits above bit 15) back into the low 16 bits (end-around carry).
4. Return the bitwise complement of the result, as an integer in `[0, 65535]`.

An empty list returns `65535`.

**Example:** `[0x45, 0x00, 0x00, 0x1c]` → `0x4500 + 0x001c = 0x451c`, complement → `0xbae3 = 47843`
""",
    starter='''def internet_checksum(data: list) -> int:
    pass
''',
    solution='''def internet_checksum(data):
    if len(data) % 2:
        data = data + [0]
    total = 0
    for i in range(0, len(data), 2):
        total += (data[i] << 8) | data[i + 1]
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return total ^ 0xFFFF
''',
    tests=[
        [[0x45, 0x00, 0x00, 0x1c]],
        [[]],
        [[0xFF, 0xFF]],
        [[0x00, 0x01, 0xf2, 0x03, 0xf4, 0xf5, 0xf6, 0xf7]],
        [[0x45, 0x00, 0x00, 0x73, 0x00, 0x00, 0x40, 0x00, 0x40, 0x11, 0x00, 0x00, 0xc0, 0xa8, 0x00, 0x01, 0xc0, 0xa8, 0x00, 0xc7]],
        [[0x45, 0x00, 0x00, 0x73, 0x00, 0x00, 0x40, 0x00, 0x40, 0x11, 0xb8, 0x61, 0xc0, 0xa8, 0x00, 0x01, 0xc0, 0xa8, 0x00, 0xc7]],
        [[0xAB]],
        [[0x12, 0x34, 0x56]],
        [[0xFF] * 9],
        [[0xFF, 0xFF, 0x00, 0x01]],
        [[0x80, 0x00, 0x80, 0x00]],
        [[(i * 37 + 11) % 256 for i in range(1500)]],
        [[0xFF] * 4000],
    ],
    examples=1,
    wrong_solutions=[
        '''def internet_checksum(data):
    if len(data) % 2:
        data = data + [0]
    total = 0
    for i in range(0, len(data), 2):
        total += (data[i] << 8) | data[i + 1]
    return (total & 0xFFFF) ^ 0xFFFF
''',
        '''def internet_checksum(data):
    if len(data) % 2:
        data = [0] + data
    total = 0
    for i in range(0, len(data), 2):
        total += (data[i] << 8) | data[i + 1]
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return total ^ 0xFFFF
''',
    ],
    guide=dict(
        prereqs="Hexadecimal, shifts and masks; the lesson on IPv6, ICMP and routing (IPv4 header layout).",
        intuition="Ones' complement addition is ordinary addition where any carry out of the top bit wraps around and is added at the bottom. Sum the words in a big integer, fold the carries back, then flip the bits.",
        hints=[
            "Pair the bytes: word = `(high << 8) | low`. Pad a trailing odd byte with a zero **low** byte.",
            "Do not truncate to 16 bits: the bits that overflow must be added back in.",
            "One fold may itself overflow, so repeat `total = (total & 0xFFFF) + (total >> 16)` until nothing is left above bit 15.",
        ],
        brute_force="Fold after every single addition. It gives the same result because end-around carry is associative, but it does more work than folding once at the end.",
        approach="""1. Pad to an even length.
2. Add all 16-bit big-endian words into `total`.
3. Fold: while `total >> 16` is non-zero, `total = (total & 0xFFFF) + (total >> 16)`.
4. Return `total ^ 0xFFFF`.

**Dry run** `[0xFF,0xFF,0x00,0x01]`: sum `0xFFFF + 0x0001 = 0x10000`. Fold: `0x0000 + 0x1 = 0x0001`. Complement: `0xFFFE = 65534`. A receiver that sums the data **including** the checksum gets `0xFFFF`, which is how verification works (see the test where a correct IPv4 header returns 0).""",
        complexity="Time O(n) for n bytes, space O(1) extra.",
        pitfalls="Masking with `& 0xFFFF` instead of folding throws the carries away. Padding at the front instead of the end shifts every word. Using Python's `~` yields a negative number; XOR with `0xFFFF`.",
        follow_up="Incremental update (RFC 1624): when a router decrements the TTL it adjusts the checksum without re-summing the header. Why is this checksum weaker than a CRC?",
    ),
),
dict(
    id="net-mac-learning-switch",
    title="MAC Learning Switch",
    difficulty="Medium",
    pattern="Link Layer",
    entry="switch_sim",
    description=r"""
Simulate a transparent Ethernet switch with ports numbered `0 .. num_ports - 1` and an initially empty
MAC address table. Frames arrive one at a time as `[in_port, src_mac, dst_mac]`.

For each frame, in this order:

1. **Learn:** record that `src_mac` lives on `in_port` (overwriting any older entry: the host may have moved).
2. **Forward:**
   - if `dst_mac` is the broadcast address `"ff:ff:ff:ff:ff:ff"` or is not in the table, **flood**: send out of every port except `in_port`, in ascending order;
   - if `dst_mac` is in the table and its port equals `in_port`, **filter**: send nowhere (`[]`);
   - otherwise send out of the single learned port.

Return the list of output-port lists, one per frame. The broadcast address is never learned as a source.

**Example:** `num_ports = 3`, frames `[[0,"aa","bb"], [1,"bb","aa"], [0,"aa","bb"]]` → `[[1,2], [0], [1]]`
""",
    starter='''def switch_sim(num_ports: int, frames: list) -> list:
    pass
''',
    solution='''def switch_sim(num_ports, frames):
    BROADCAST = "ff:ff:ff:ff:ff:ff"
    table = {}
    out = []
    for port, src, dst in frames:
        if src != BROADCAST:
            table[src] = port
        if dst == BROADCAST or dst not in table:
            out.append([p for p in range(num_ports) if p != port])
        elif table[dst] == port:
            out.append([])
        else:
            out.append([table[dst]])
    return out
''',
    tests=[
        [3, [[0, "aa", "bb"], [1, "bb", "aa"], [0, "aa", "bb"]]],
        [4, [[2, "aa", "ff:ff:ff:ff:ff:ff"], [1, "bb", "aa"], [3, "cc", "ff:ff:ff:ff:ff:ff"]]],
        [4, []],
        [1, [[0, "aa", "bb"], [0, "bb", "aa"]]],
        [3, [[0, "aa", "bb"], [0, "bb", "aa"], [0, "aa", "bb"]]],
        [3, [[0, "aa", "bb"], [1, "bb", "aa"], [2, "aa", "bb"], [1, "bb", "aa"]]],
        [2, [[0, "aa", "aa"]]],
        [5, [[4, "h1", "h2"], [3, "h2", "h1"], [2, "h3", "h1"], [1, "h4", "h3"], [0, "h5", "h9"], [4, "h1", "h5"]]],
        [3, [[0, "aa", "bb"], [1, "bb", "cc"], [2, "cc", "aa"], [2, "cc", "bb"], [0, "aa", "cc"]]],
        [4, [[0, "aa", "bb"], [1, "bb", "aa"], [1, "aa", "bb"], [0, "cc", "aa"], [0, "cc", "bb"]]],
        [6, [[i % 6, "m%d" % (i % 9), "m%d" % ((i * 5 + 1) % 9)] for i in range(60)]],
        [3, [[1, "ff:ff:ff:ff:ff:ff", "aa"], [0, "bb", "ff:ff:ff:ff:ff:ff"]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def switch_sim(num_ports, frames):
    B = "ff:ff:ff:ff:ff:ff"
    table, out = {}, []
    for port, src, dst in frames:
        table.setdefault(src, port)
        if dst == B or dst not in table:
            out.append([p for p in range(num_ports) if p != port])
        elif table[dst] == port:
            out.append([])
        else:
            out.append([table[dst]])
    return out
''',
        '''def switch_sim(num_ports, frames):
    B = "ff:ff:ff:ff:ff:ff"
    table, out = {}, []
    for port, src, dst in frames:
        if src != B:
            table[src] = port
        if dst == B or dst not in table:
            out.append([p for p in range(num_ports) if p != port])
        else:
            out.append([table[dst]])
    return out
''',
    ],
    guide=dict(
        prereqs="The lesson *Ethernet, MAC addresses, ARP and switching*; dictionaries.",
        intuition="A switch never needs configuration: it learns where each station is by reading the **source** address of frames passing through, and uses that table to decide where frames for a **destination** go. Unknown means ask everyone.",
        hints=[
            "Keep a dict from MAC address to port. Which field of the frame updates it?",
            "Learn first, then look up the destination, so a frame addressed to its own sender is filtered.",
            "Three outcomes: flood (broadcast or unknown), filter (same port), forward (one port).",
        ],
        brute_force="Flood every frame like a hub. It delivers correctly but wastes bandwidth and is exactly what the table exists to avoid; it also fails the tests that expect a single port.",
        approach="""1. `table[src] = in_port` (skip the broadcast address).
2. If `dst` is broadcast or missing from the table, output all ports except `in_port`.
3. Else if `table[dst] == in_port`, output `[]`.
4. Else output `[table[dst]]`.

**Dry run** (3 ports): frame `[0,aa,bb]` learns aa→0; bb unknown → flood `[1,2]`. Frame `[1,bb,aa]` learns bb→1; aa known on 0 → `[0]`. Frame `[0,aa,bb]` → bb known on 1 → `[1]`.""",
        complexity="Time O(F·P) in the worst case (every frame floods to P ports); table operations are O(1) each. Space O(number of distinct MACs).",
        pitfalls="Using `setdefault` so that a host which moves to another port is never updated. Forgetting to exclude the ingress port when flooding (causes loops in real networks). Forgetting the filter case when source and destination sit behind the same port.",
        follow_up="Add an ageing timer so entries expire after 300 seconds, and VLAN tags so that flooding stays within one VLAN.",
    ),
),
dict(
    id="net-nat-table",
    title="NAT Translation Table",
    difficulty="Medium",
    pattern="Network Layer",
    entry="nat_sim",
    description=r"""
Simulate a home router performing port address translation (NAPT) with one public address.

`packets` is processed in order. Each packet is either

- `["out", src_ip, src_port, dst_ip, dst_port]`: a private host sends to the Internet, or
- `["in", src_ip, src_port, dst_port]`: an Internet host sends to the router's public address on `dst_port`.

**Outbound.** Each distinct private endpoint `(src_ip, src_port)` is given one public port, reused for every
destination. Ports are handed out in order: `first_port`, `first_port + 1`, … Mappings never expire.
The router also remembers that this private endpoint has contacted `(dst_ip, dst_port)`.
The result for the packet is the rewritten tuple `[public_ip, public_port, dst_ip, dst_port]`.

**Inbound.** If `dst_port` has a mapping **and** the mapped private endpoint has previously sent a packet to
exactly `(src_ip, src_port)`, the result is `[private_ip, private_port]` (where the packet is delivered).
Otherwise the result is the string `"drop"`.

Return the list of results.

**Example:** `public_ip = "203.0.113.5"`, `first_port = 40000`,
`packets = [["out","192.168.0.2",5555,"1.1.1.1",53], ["in","1.1.1.1",53,40000], ["in","9.9.9.9",53,40000]]`
→ `[["203.0.113.5",40000,"1.1.1.1",53], ["192.168.0.2",5555], "drop"]`
""",
    starter='''def nat_sim(public_ip: str, first_port: int, packets: list) -> list:
    pass
''',
    solution='''def nat_sim(public_ip, first_port, packets):
    out_map, in_map, allowed = {}, {}, set()
    next_port = first_port
    res = []
    for pkt in packets:
        if pkt[0] == "out":
            _, sip, sport, dip, dport = pkt
            key = (sip, sport)
            if key not in out_map:
                out_map[key] = next_port
                in_map[next_port] = key
                next_port += 1
            pub = out_map[key]
            allowed.add((pub, dip, dport))
            res.append([public_ip, pub, dip, dport])
        else:
            _, sip, sport, dport = pkt
            if dport in in_map and (dport, sip, sport) in allowed:
                res.append(list(in_map[dport]))
            else:
                res.append("drop")
    return res
''',
    tests=[
        ["203.0.113.5", 40000, [["out", "192.168.0.2", 5555, "1.1.1.1", 53], ["in", "1.1.1.1", 53, 40000], ["in", "9.9.9.9", 53, 40000]]],
        ["198.51.100.1", 1024, []],
        ["198.51.100.1", 1024, [["in", "8.8.8.8", 53, 1024]]],
        ["198.51.100.1", 1024, [["out", "10.0.0.2", 3000, "8.8.8.8", 53], ["out", "10.0.0.3", 3000, "8.8.8.8", 53], ["in", "8.8.8.8", 53, 1025], ["in", "8.8.8.8", 53, 1024]]],
        ["198.51.100.1", 1024, [["out", "10.0.0.2", 3000, "8.8.8.8", 53], ["out", "10.0.0.2", 3000, "9.9.9.9", 443], ["in", "9.9.9.9", 443, 1024], ["in", "9.9.9.9", 444, 1024], ["in", "8.8.8.8", 53, 1024]]],
        ["198.51.100.1", 1024, [["out", "10.0.0.2", 3000, "8.8.8.8", 53], ["out", "10.0.0.2", 3001, "8.8.8.8", 53], ["in", "8.8.8.8", 53, 1025]]],
        ["198.51.100.1", 6000, [["in", "8.8.8.8", 53, 6000], ["out", "10.0.0.2", 3000, "8.8.8.8", 53], ["in", "8.8.8.8", 53, 6000]]],
        ["198.51.100.1", 6000, [["out", "10.0.0.2", 3000, "8.8.8.8", 53], ["in", "8.8.8.8", 53, 6001], ["in", "8.8.4.4", 53, 6000]]],
        ["198.51.100.1", 6000, [["out", "10.0.0.2", 80, "1.1.1.1", 80], ["out", "10.0.0.3", 80, "1.1.1.1", 80], ["out", "10.0.0.2", 80, "1.1.1.1", 80], ["in", "1.1.1.1", 80, 6000], ["in", "1.1.1.1", 80, 6001], ["in", "1.1.1.1", 80, 6002]]],
        ["203.0.113.9", 50000, [["out", "192.168.1.%d" % (i % 7), 1000 + i % 11, "93.184.216.%d" % (i % 3), 443] for i in range(80)] + [["in", "93.184.216.%d" % (i % 4), 443, 50000 + i] for i in range(90)]],
        ["203.0.113.9", 50000, [["out", "192.168.1.2", 7, "5.5.5.5", 7], ["in", "5.5.5.5", 7, 50000], ["in", "5.5.5.5", 8, 50000], ["in", "5.5.5.6", 7, 50000], ["out", "192.168.1.2", 7, "5.5.5.6", 7], ["in", "5.5.5.6", 7, 50000]]],
    ],
    examples=1,
    wrong_solutions=[
        '''def nat_sim(public_ip, first_port, packets):
    out_map, in_map = {}, {}
    next_port = first_port
    res = []
    for pkt in packets:
        if pkt[0] == "out":
            _, sip, sport, dip, dport = pkt
            key = (sip, sport)
            if key not in out_map:
                out_map[key] = next_port
                in_map[next_port] = key
                next_port += 1
            res.append([public_ip, out_map[key], dip, dport])
        else:
            res.append(list(in_map[pkt[3]]) if pkt[3] in in_map else "drop")
    return res
''',
        '''def nat_sim(public_ip, first_port, packets):
    in_map, allowed = {}, set()
    next_port = first_port
    res = []
    for pkt in packets:
        if pkt[0] == "out":
            _, sip, sport, dip, dport = pkt
            in_map[next_port] = (sip, sport)
            allowed.add((next_port, dip, dport))
            res.append([public_ip, next_port, dip, dport])
            next_port += 1
        else:
            _, sip, sport, dport = pkt
            res.append(list(in_map[dport]) if (dport, sip, sport) in allowed else "drop")
    return res
''',
    ],
    guide=dict(
        prereqs="The lesson *IPv4 addressing, subnets, CIDR and NAT*; dictionaries and sets.",
        intuition="NAT is two dictionaries that are inverses of each other (private endpoint → public port, public port → private endpoint) plus a filter that only admits replies from peers the inside host has already spoken to.",
        hints=[
            "Key the outbound map by the pair `(private_ip, private_port)`, not by the IP alone.",
            "Allocate a new public port only the first time an endpoint is seen; reuse it afterwards.",
            "Store `(public_port, remote_ip, remote_port)` in a set on every outbound packet and consult it on every inbound one.",
        ],
        brute_force="Keep a plain list of mappings and scan it for every packet: O(P·M). Dictionaries make each packet O(1).",
        approach="""1. Outbound: look up or create the mapping, add the permitted remote endpoint, emit the rewritten 4-tuple.
2. Inbound: the packet is delivered only if the port maps to someone **and** the triple `(port, src_ip, src_port)` is permitted.

**Dry run:** `192.168.0.2:5555 → 1.1.1.1:53` allocates 40000 and permits `(40000, 1.1.1.1, 53)`. A reply from `1.1.1.1:53` to port 40000 is delivered to `192.168.0.2:5555`. A packet from `9.9.9.9:53` to the same port is dropped: nobody inside talked to it.""",
        complexity="Time O(P) for P packets, space O(number of mappings + permitted peers).",
        pitfalls="Allocating a fresh port per packet instead of per endpoint. Forwarding any inbound packet that hits a mapped port (that is a *full-cone* NAT, not the port-restricted behaviour specified here). Mixing up which port an inbound packet is addressed to.",
        follow_up="Add idle timeouts (e.g. 30 s for UDP, minutes for TCP) and explain why long-lived idle connections die behind NATs, and how keep-alives or STUN/TURN work around it.",
    ),
),
dict(
    id="net-traceroute-hops",
    title="Reconstruct a Traceroute Path",
    difficulty="Medium",
    pattern="Tools",
    entry="reconstruct_path",
    description=r"""
Traceroute sends probes with TTL 1, 2, 3, … Each router that decrements a probe's TTL to zero answers with an
ICMP *Time Exceeded* message, revealing its address; the destination itself answers the first probe that
reaches it.

You are given the collected `replies` in arbitrary order, each `[ttl, responder_ip, rtt_ms]`, and the
destination address `dest`. Several probes are sent per TTL; some get no reply; load balancing may make
different routers answer for the same TTL.

Build the path:

- Let `last` be the **smallest** TTL at which some reply came from `dest`; if `dest` never replied, `last` is the largest TTL present. With no replies at all, return `[]`.
- For each TTL from 1 to `last` output one hop `[ip, best_rtt]`:
  - `ip` is the responder seen most often at that TTL (ties → the lexicographically smallest string);
  - `best_rtt` is the minimum RTT among replies from that `ip` at that TTL;
  - a TTL with no replies yields `["*", -1]`.

**Example:** `replies = [[2,"10.0.0.1",9],[1,"192.168.1.1",2],[1,"192.168.1.1",1],[4,"93.184.216.34",30]]`, `dest = "93.184.216.34"`
→ `[["192.168.1.1",1], ["10.0.0.1",9], ["*",-1], ["93.184.216.34",30]]`
""",
    starter='''def reconstruct_path(replies: list, dest: str) -> list:
    pass
''',
    solution='''def reconstruct_path(replies, dest):
    if not replies:
        return []
    by_ttl = {}
    for ttl, ip, rtt in replies:
        by_ttl.setdefault(ttl, {}).setdefault(ip, []).append(rtt)
    reached = [t for t in by_ttl if dest in by_ttl[t]]
    last = min(reached) if reached else max(by_ttl)
    path = []
    for t in range(1, last + 1):
        if t not in by_ttl:
            path.append(["*", -1])
            continue
        ips = by_ttl[t]
        ip = min(ips, key=lambda k: (-len(ips[k]), k))
        path.append([ip, min(ips[ip])])
    return path
''',
    tests=[
        [[[2, "10.0.0.1", 9], [1, "192.168.1.1", 2], [1, "192.168.1.1", 1], [4, "93.184.216.34", 30]], "93.184.216.34"],
        [[], "1.1.1.1"],
        [[[1, "1.1.1.1", 5]], "1.1.1.1"],
        [[[3, "10.0.0.9", 12]], "1.1.1.1"],
        [[[1, "a", 3], [2, "b", 8], [3, "d", 20], [4, "d", 22], [5, "d", 21]], "d"],
        [[[1, "gw", 1], [2, "r2", 7], [2, "r1", 6], [2, "r2", 9], [3, "dst", 15]], "dst"],
        [[[1, "gw", 1], [2, "r2", 7], [2, "r1", 6], [3, "dst", 15]], "dst"],
        [[[1, "gw", 4], [1, "gw", 2], [1, "gw", 3], [2, "x", 50], [2, "y", 5], [2, "x", 40]], "dst"],
        [[[5, "e", 9], [2, "b", 3]], "zzz"],
        [[[1, "gw", 1], [2, "dst", 30], [2, "r1", 5], [2, "r1", 6], [3, "dst", 28]], "dst"],
        [[[t, "hop%02d" % t, t * 3 + (p % 2)] for t in range(1, 21) for p in range(3) if (t * 7 + p) % 5] + [[21, "target", 70]], "target"],
        [[[1, "10.1.1.1", 2], [1, "10.1.1.2", 1], [1, "10.1.1.2", 9], [1, "10.1.1.1", 3], [2, "t", 4]], "t"],
    ],
    examples=1,
    wrong_solutions=[
        '''def reconstruct_path(replies, dest):
    if not replies:
        return []
    by_ttl = {}
    for ttl, ip, rtt in replies:
        by_ttl.setdefault(ttl, {}).setdefault(ip, []).append(rtt)
    path = []
    for t in range(1, max(by_ttl) + 1):
        if t not in by_ttl:
            path.append(["*", -1])
            continue
        ips = by_ttl[t]
        ip = min(ips, key=lambda k: (-len(ips[k]), k))
        path.append([ip, min(ips[ip])])
    return path
''',
        '''def reconstruct_path(replies, dest):
    by_ttl = {}
    for ttl, ip, rtt in replies:
        by_ttl.setdefault(ttl, {}).setdefault(ip, []).append(rtt)
    path = []
    for t in sorted(by_ttl):
        ips = by_ttl[t]
        ip = min(ips, key=lambda k: (-len(ips[k]), k))
        path.append([ip, min(ips[ip])])
        if ip == dest:
            break
    return path
''',
    ],
    guide=dict(
        prereqs="The lesson on ping, traceroute, dig and curl; the IP TTL field and ICMP Time Exceeded; grouping with dictionaries.",
        intuition="The TTL of the probe *is* the hop number, so group replies by TTL. Inside each group take a majority vote for the address. The path ends at the first TTL where the destination itself answers.",
        hints=[
            "Build `ttl -> {ip -> [rtts]}`.",
            "Decide where the path stops before building it: the smallest TTL whose group contains `dest`, else the largest TTL seen.",
            "Walk TTL 1..last **including** the missing ones, which become `[\"*\", -1]`.",
        ],
        brute_force="For each TTL rescan the whole reply list to count addresses: O(T·R). Grouping once makes it O(R).",
        approach="""1. Group replies by TTL and then by responder.
2. `last = min(ttl where dest replied)` or `max(ttl)`.
3. For each TTL in `1..last`: missing → `["*", -1]`; otherwise pick the address with the most replies (ties by string order) and its minimum RTT.

**Dry run** (the example): TTL 1 → `192.168.1.1` twice, best RTT 1. TTL 2 → `10.0.0.1`, 9. TTL 3 → nothing → `*`. TTL 4 → the destination → stop.""",
        complexity="Time O(R + T) for R replies and T hops; space O(R).",
        pitfalls="Continuing past the destination (later probes also reach it and would repeat it). Skipping silent hops instead of emitting `*`, which shifts every later hop number. Taking the minimum RTT over all responders rather than the chosen one.",
        follow_up="Why can a later hop show a *lower* RTT than an earlier one? (ICMP generation is rate-limited and handled on a router's slow path; the return path may differ.)",
    ),
),
]
