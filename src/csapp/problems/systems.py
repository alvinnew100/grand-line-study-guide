PROBLEMS = [
dict(
    id="csapp-fork-count",
    title="Fork Output Counting",
    difficulty="Medium",
    pattern="Processes",
    entry="fork_count",
    description=r"""
Reason about `fork` the way you would on a CS:APP exam, but in code.

A straight-line "program" is a list of operations executed in order by **every live process**:

- `"fork"`: the process calls `fork()`. Both parent and child continue with the next operation.
  The new process is marked as a *child*; the calling process is marked as a *parent*
  (i.e. each process remembers the return value of its most recent `fork`; the initial process starts
  as a parent).
- `"print"`: the process prints one line.
- `"exit_if_child"`: the process exits if its most recent `fork` returned 0 (it is marked child).
  This models `if (fork() == 0) { ...; exit(0); }` when placed after the child's work.

Return `[lines, processes]`: the total number of lines printed and the total number of processes
that ever existed (including the original one).

**Example:** `["fork", "fork", "print"]` → `[4, 4]`

**Example:** `["fork", "print", "exit_if_child", "fork", "print"]` → `[4, 3]`
(parent and child print; the child exits; the parent forks again and both print)
""",
    starter='''def fork_count(ops: List[str]) -> List[int]:
    pass
''',
    solution='''def fork_count(ops):
    parents, children = 1, 0
    lines, created = 0, 1
    for op in ops:
        total = parents + children
        if op == "fork":
            parents, children = total, total
            created += total
        elif op == "print":
            lines += total
        elif op == "exit_if_child":
            children = 0
    return [lines, created]
''',
    tests=[
        [["fork", "fork", "print"]],
        [["fork", "print", "exit_if_child", "fork", "print"]],
        [[]],
        [["print"]],
        [["exit_if_child", "print"]],
        [["print", "fork", "print", "fork", "print"]],
        [["fork", "exit_if_child", "fork", "exit_if_child", "fork", "exit_if_child", "print"]],
        [["fork", "fork", "exit_if_child", "print"]],
        [["fork"] * 10 + ["print"]],
        [["fork", "print"] * 20],
        [["fork", "fork", "print", "exit_if_child", "exit_if_child", "print"]],
        [["fork", "exit_if_child"] * 50 + ["print"]],
        [["fork"] * 40],
    ],
    wrong_solutions=['''def fork_count(ops):
    n = ops.count("fork")
    return [ops.count("print") * 2 ** n, 2 ** n]
''', '''def fork_count(ops):
    procs, lines, created = 1, 0, 1
    for op in ops:
        if op == "fork":
            created += procs
            procs *= 2
        elif op == "print":
            lines += procs
        elif op == "exit_if_child":
            procs = max(1, procs // 2)
    return [lines, created]
'''],
    guide=dict(
        prereqs="Lesson *Processes: fork, exec, wait* (process graphs).",
        intuition="You never need to track individual processes: only how many live processes are currently 'parents' and how many are 'children' with respect to their latest fork. A fork turns every live process into one parent plus one child.",
        hints=["Keep two counters: live processes marked parent, live processes marked child.",
               "`fork`: with `t = parents + children`, afterwards there are `t` parents and `t` children, and `t` new processes were created.",
               "`exit_if_child` removes all children; `print` adds `parents + children` lines."],
        brute_force="Simulate each process explicitly as (program counter, is_child) on a work list. Exponential in the number of forks: 40 forks would need 2^40 processes.",
        approach="Counting simulation in one pass. Dry run of `fork, print, exit_if_child, fork, print`: (1,0) → fork (1,1) created 2 → print 2 lines → exit (1,0) → fork (1,1) created 3 → print 2 more: `[4, 3]`.",
        complexity="O(len(ops)) time with big-integer arithmetic, O(1) space.",
        pitfalls="- `2^forks` is only right when nobody exits.\n- After `exit_if_child`, *half* is not always what dies: after two forks without exits there are 2 parents and 2 children.\n- An `exit_if_child` before any fork kills nobody (the original process counts as a parent).",
        follow_up="Add `wait` and ask for the set of possible output orderings (topological sorts of the process graph).",
    ),
),
dict(
    id="csapp-page-translate",
    title="Virtual to Physical Address Translation",
    difficulty="Easy",
    pattern="Virtual Memory",
    entry="translate",
    description=r"""
Simulate the MMU with a single-level page table.

- `page_size` is a power of two (the page size in bytes).
- `page_table[vpn]` is the physical page number (PPN) for virtual page `vpn`, or `-1` if the page is
  not present (invalid). VPNs beyond the end of the table are also invalid.
- `addrs` is a list of virtual addresses.

For each virtual address return the physical address `PPN * page_size + VPO`, or `-1` for a page
fault. Remember: the page offset is unchanged by translation.

**Example:** `page_size = 64, page_table = [0x28, -1, 0x33], addrs = [0x20, 0x45, 0x83]`
→ `[0xA20, -1, 0xCC3]` = `[2592, -1, 3267]`
""",
    starter='''def translate(page_size: int, page_table: List[int], addrs: List[int]) -> List[int]:
    pass
''',
    solution='''def translate(page_size, page_table, addrs):
    p = page_size.bit_length() - 1
    out = []
    for va in addrs:
        vpn, vpo = va >> p, va & (page_size - 1)
        if vpn >= len(page_table) or page_table[vpn] < 0:
            out.append(-1)
        else:
            out.append((page_table[vpn] << p) | vpo)
    return out
''',
    tests=[
        [64, [0x28, -1, 0x33], [0x20, 0x45, 0x83]],
        [64, [0x28, -1, 0x33, 0x02, -1, 0x16, -1, -1, 0x13, 0x17, 0x09, -1, -1, 0x2D, 0x11, 0x0D], [0x03D4, 0x0B8F, 0x0020, 0x02C1, 0x03A9]],
        [4096, [5, 9, -1, 0], [0, 4095, 4096, 8191, 8192, 12288, 16383, 16384]],
        [4096, [], [0, 1]],
        [1, [7, 3, -1], [0, 1, 2, 3]],
        [16, [0], [0, 5, 15, 16]],
        [4096, [3], []],
        [1024, [10, 11, 12, 13], [1023, 1024, 2047, 3000, 4095]],
        [4096, list(range(100, 164)), [i * 3001 for i in range(200)]],
        [2 * 1024 * 1024, [1, -1, 0], [0x1FFFFF, 0x200000, 0x400123]],
    ],
    wrong_solutions=['''def translate(page_size, page_table, addrs):
    out = []
    for va in addrs:
        vpn = va // page_size
        if vpn >= len(page_table) or page_table[vpn] < 0:
            out.append(-1)
        else:
            out.append(page_table[vpn] * page_size)
    return out
''', '''def translate(page_size, page_table, addrs):
    out = []
    for va in addrs:
        vpn, vpo = va // page_size, va % page_size
        if page_table[vpn % max(1, len(page_table))] < 0 if page_table else True:
            out.append(-1)
        else:
            out.append(page_table[vpn % len(page_table)] * page_size + vpo)
    return out
'''],
    guide=dict(
        prereqs="Lesson *VM concepts and address translation*.",
        intuition="Split the virtual address into VPN (high bits) and VPO (low `p` bits). Look the VPN up in the page table; glue the PPN onto the unchanged offset.",
        hints=["`vpn = va // page_size`, `vpo = va % page_size`.", "Check bounds and the `-1` marker before using the entry.", "`pa = ppn * page_size + vpo`."],
        brute_force="This *is* the direct approach; there is nothing slower that is natural.",
        approach="One pass over the addresses. Dry run VA 0x83 with 64-byte pages: VPN 2, VPO 3, PPN 0x33 → 0x33*64 + 3 = 0xCC3.",
        complexity="O(len(addrs)).",
        pitfalls="- Dropping the offset.\n- Indexing past the end of the table (a fault, not a crash or wrap-around).\n- PPN 0 is a valid frame; only negative entries are invalid.",
        follow_up="Extend to a two-level table: the top bits index a directory whose entries point to second-level tables (or are null).",
    ),
),
dict(
    id="csapp-tlb-sim",
    title="TLB Simulator",
    difficulty="Medium",
    pattern="Virtual Memory",
    entry="tlb_sim",
    description=r"""
Simulate a set-associative **TLB** in front of a single-level page table.

- The TLB has `sets` sets (a power of two) and `ways` entries per set, with **LRU** replacement
  within a set. It starts empty.
- For a virtual address, `VPN = va // page_size`; the TLB index is `VPN % sets` and the tag is
  `VPN // sets`.
- **TLB hit:** the entry is present (it becomes most recently used).
- **TLB miss:** consult `page_table[VPN]`. If the VPN is beyond the table or the entry is `-1`,
  this is also a **page fault**: nothing is inserted into the TLB (assume the access is aborted and
  the page stays invalid). Otherwise insert the translation into the TLB, evicting the LRU entry of
  the set if it is full.

Return `[tlb_hits, tlb_misses, page_faults]` (every page fault is also counted as a TLB miss).

**Example:** `sets = 1, ways = 2, page_size = 4096, page_table = [1, 2, 3], addrs = [0, 100, 4096, 8192, 0]`
→ `[1, 4, 0]` (VPNs 0,0,1,2,0: miss, hit, miss, miss evicting VPN 0, miss)
""",
    starter='''def tlb_sim(sets: int, ways: int, page_size: int, page_table: List[int], addrs: List[int]) -> List[int]:
    pass
''',
    solution='''def tlb_sim(sets, ways, page_size, page_table, addrs):
    tlb = [collections.OrderedDict() for _ in range(sets)]
    hits = misses = faults = 0
    for va in addrs:
        vpn = va // page_size
        s, tag = tlb[vpn % sets], vpn // sets
        if tag in s:
            hits += 1
            s.move_to_end(tag)
            continue
        misses += 1
        if vpn >= len(page_table) or page_table[vpn] < 0:
            faults += 1
            continue
        if len(s) == ways:
            s.popitem(last=False)
        s[tag] = page_table[vpn]
    return [hits, misses, faults]
''',
    tests=[
        [1, 2, 4096, [1, 2, 3], [0, 100, 4096, 8192, 0]],
        [1, 2, 4096, [1, 2, 3], [0, 4096, 0, 8192, 0, 4096]],
        [4, 4, 64, [0x28, -1, 0x33, 0x02, -1, 0x16, -1, -1, 0x13, 0x17, 0x09, -1, -1, 0x2D, 0x11, 0x0D],
         [0x03D4, 0x03D7, 0x0B8F, 0x0020, 0x02C1, 0x0020, 0x03A9]],
        [2, 1, 4096, [5, 6, 7, 8], [0, 8192, 0, 8192, 4096, 12288, 4096]],
        [1, 1, 4096, [], [0, 0, 0]],
        [1, 1, 4096, [-1, 4], [0, 0, 4096, 4097]],
        [16, 4, 4096, list(range(1000)), [i * 4096 for i in range(64)] * 3],
        [16, 4, 4096, list(range(1000)), [i * 4096 for i in range(65)] * 3],
        [8, 2, 4096, list(range(64)), [(i * 7919) % (64 * 4096) for i in range(5000)]],
        [1, 4, 4096, list(range(8)), []],
        [1, 3, 1024, [9, 9, 9, 9, 9], [0, 1024, 2048, 0, 3072, 1024, 0, 2048]],
    ],
    wrong_solutions=['''def tlb_sim(sets, ways, page_size, page_table, addrs):
    tlb = [collections.OrderedDict() for _ in range(sets)]
    hits = misses = faults = 0
    for va in addrs:
        vpn = va // page_size
        s, tag = tlb[vpn % sets], vpn // sets
        if tag in s:
            hits += 1
            continue
        misses += 1
        if vpn >= len(page_table) or page_table[vpn] < 0:
            faults += 1
            continue
        if len(s) == ways:
            s.popitem(last=False)
        s[tag] = page_table[vpn]
    return [hits, misses, faults]
''', '''def tlb_sim(sets, ways, page_size, page_table, addrs):
    tlb = [collections.OrderedDict() for _ in range(sets)]
    hits = misses = faults = 0
    for va in addrs:
        vpn = va // page_size
        s, tag = tlb[vpn % sets], vpn // sets
        if tag in s:
            hits += 1
            s.move_to_end(tag)
            continue
        misses += 1
        if vpn >= len(page_table) or page_table[vpn] < 0:
            faults += 1
        if len(s) == ways:
            s.popitem(last=False)
        s[tag] = 0
    return [hits, misses, faults]
'''],
    guide=dict(
        prereqs="Lessons *VM concepts and address translation* (TLBI/TLBT) and *Cache memories* (LRU sets).",
        intuition="A TLB is just a small set-associative cache whose 'address' is the VPN and whose blocks are single page table entries. Reuse the cache-simulator pattern, with the page table as the next level.",
        hints=["Split the VPN, not the full address: index = VPN mod sets, tag = VPN div sets.", "Each set is an LRU of capacity `ways`.", "On a miss check the page table first; only valid translations are cached."],
        brute_force="Keep a list of (vpn, last_used_time) per set and scan it: O(ways) per access.",
        approach="OrderedDict per set. Hit → move to end. Miss → count; if invalid → fault, continue; else evict LRU if full and insert. Dry run of the first example gives `[1, 4, 0]`.",
        complexity="O(1) per access; O(sets × ways) space.",
        pitfalls="- Forgetting to refresh recency on hits.\n- Caching invalid translations after a page fault.\n- Using address bits instead of VPN bits for the index.",
        follow_up="Model a page fault handler that maps the page (allocating a frame) so that the retried access hits, and add a second-level TLB.",
    ),
),
dict(
    id="csapp-first-fit-malloc",
    title="First-Fit Allocator Simulator",
    difficulty="Hard",
    pattern="Dynamic Memory Allocation",
    entry="simulate_heap",
    description=r"""
Simulate the implicit-free-list allocator from CS:APP on a heap of `heap_size` bytes (a multiple
of 8) that initially is one free block starting at offset 0. The heap cannot grow.

`ops` is a list of requests:

- `["malloc", n]`: allocate a block for a payload of `n` bytes.
  - If `n <= 0`, the request fails.
  - The block size is `n + 8` (header + footer overhead) rounded up to a multiple of 8, with a
    minimum of 16 bytes.
  - **First fit:** scan blocks in address order and take the first free block that is large enough.
  - **Split** it if the remainder would be at least 16 bytes; otherwise use the whole block.
  - The result of the request is the **offset of the block's start**, or `-1` if no block fits.
- `["free", i]`: free the block returned by the malloc at index `i` of `ops` (0-based; it is
  guaranteed to be an earlier malloc that has not been freed before). If that malloc had failed, do
  nothing. **Coalesce immediately** with a free previous and/or next block.

Return the list of results of the malloc requests, in order.

**Example:** `heap_size = 64`, `ops = [["malloc",8],["malloc",8],["free",0],["malloc",20],["malloc",4]]`
→ `[0, 16, 32, 0]`
""",
    starter='''def simulate_heap(heap_size: int, ops: List[list]) -> List[int]:
    pass
''',
    solution='''def simulate_heap(heap_size, ops):
    blocks = [[0, heap_size, False]] if heap_size > 0 else []
    result_of = {}
    out = []
    for idx, (kind, arg) in enumerate(ops):
        if kind == "malloc":
            res = -1
            if arg > 0:
                asize = max(16, (arg + 8 + 7) // 8 * 8)
                for i, b in enumerate(blocks):
                    if not b[2] and b[1] >= asize:
                        if b[1] - asize >= 16:
                            blocks.insert(i + 1, [b[0] + asize, b[1] - asize, False])
                            b[1] = asize
                        b[2] = True
                        res = b[0]
                        break
            result_of[idx] = res
            out.append(res)
        else:
            start = result_of[arg]
            if start < 0:
                continue
            i = next(k for k, b in enumerate(blocks) if b[0] == start)
            blocks[i][2] = False
            if i + 1 < len(blocks) and not blocks[i + 1][2]:
                blocks[i][1] += blocks.pop(i + 1)[1]
            if i > 0 and not blocks[i - 1][2]:
                blocks[i - 1][1] += blocks.pop(i)[1]
    return out
''',
    tests=[
        [64, [["malloc", 8], ["malloc", 8], ["free", 0], ["malloc", 20], ["malloc", 4]]],
        [64, []],
        [16, [["malloc", 8], ["malloc", 1]]],
        [16, [["malloc", 9]]],
        [0, [["malloc", 1]]],
        [64, [["malloc", 0], ["malloc", -5], ["malloc", 1], ["free", 0], ["malloc", 56]]],
        [96, [["malloc", 8], ["malloc", 20], ["malloc", 8], ["free", 0], ["free", 2], ["malloc", 56], ["free", 1], ["malloc", 56]]],
        [64, [["malloc", 8], ["malloc", 8], ["malloc", 8], ["malloc", 8], ["free", 1], ["free", 2], ["malloc", 24], ["malloc", 1]]],
        [64, [["malloc", 8], ["malloc", 8], ["malloc", 8], ["malloc", 8], ["free", 0], ["free", 2], ["malloc", 24], ["free", 1], ["malloc", 24]]],
        [48, [["malloc", 30], ["malloc", 1], ["free", 0], ["malloc", 17], ["malloc", 1]]],
        [80, [["malloc", 24], ["malloc", 24], ["free", 0], ["malloc", 8], ["malloc", 8], ["malloc", 8]]],
        [128, [["malloc", 100], ["malloc", 100], ["free", 1], ["free", 0], ["malloc", 120], ["malloc", 1]]],
        [64, [["malloc", 8], ["malloc", 8], ["malloc", 8], ["free", 0], ["free", 1], ["malloc", 16], ["free", 2], ["malloc", 32]]],
        [8000, [["malloc", 8 + 8 * (i % 5)] for i in range(200)] + [["free", i] for i in range(0, 200, 2)]
         + [["malloc", 30] for _ in range(60)]],
    ],
    wrong_solutions=['''def simulate_heap(heap_size, ops):
    blocks = [[0, heap_size, False]] if heap_size > 0 else []
    result_of = {}
    out = []
    for idx, (kind, arg) in enumerate(ops):
        if kind == "malloc":
            res = -1
            if arg > 0:
                asize = max(16, (arg + 8 + 7) // 8 * 8)
                for i, b in enumerate(blocks):
                    if not b[2] and b[1] >= asize:
                        if b[1] - asize >= 16:
                            blocks.insert(i + 1, [b[0] + asize, b[1] - asize, False])
                            b[1] = asize
                        b[2] = True
                        res = b[0]
                        break
            result_of[idx] = res
            out.append(res)
        else:
            start = result_of[arg]
            if start < 0:
                continue
            i = next(k for k, b in enumerate(blocks) if b[0] == start)
            blocks[i][2] = False
    return out
''', '''def simulate_heap(heap_size, ops):
    blocks = [[0, heap_size, False]] if heap_size > 0 else []
    result_of = {}
    out = []
    for idx, (kind, arg) in enumerate(ops):
        if kind == "malloc":
            res = -1
            if arg > 0:
                asize = max(16, (arg + 8 + 7) // 8 * 8)
                for i, b in enumerate(blocks):
                    if not b[2] and b[1] >= asize:
                        if b[1] - asize > 0:
                            blocks.insert(i + 1, [b[0] + asize, b[1] - asize, False])
                            b[1] = asize
                        b[2] = True
                        res = b[0]
                        break
            result_of[idx] = res
            out.append(res)
        else:
            start = result_of[arg]
            if start < 0:
                continue
            i = next(k for k, b in enumerate(blocks) if b[0] == start)
            blocks[i][2] = False
            if i + 1 < len(blocks) and not blocks[i + 1][2]:
                blocks[i][1] += blocks.pop(i + 1)[1]
            if i > 0 and not blocks[i - 1][2]:
                blocks[i - 1][1] += blocks.pop(i)[1]
    return out
''', '''def simulate_heap(heap_size, ops):
    blocks = [[0, heap_size, False]] if heap_size > 0 else []
    result_of = {}
    out = []
    for idx, (kind, arg) in enumerate(ops):
        if kind == "malloc":
            res = -1
            if arg > 0:
                asize = max(16, (arg + 8 + 7) // 8 * 8)
                best = None
                for i, b in enumerate(blocks):
                    if not b[2] and b[1] >= asize and (best is None or b[1] < blocks[best][1]):
                        best = i
                if best is not None:
                    b = blocks[best]
                    if b[1] - asize >= 16:
                        blocks.insert(best + 1, [b[0] + asize, b[1] - asize, False])
                        b[1] = asize
                    b[2] = True
                    res = b[0]
            result_of[idx] = res
            out.append(res)
        else:
            start = result_of[arg]
            if start < 0:
                continue
            i = next(k for k, b in enumerate(blocks) if b[0] == start)
            blocks[i][2] = False
            if i + 1 < len(blocks) and not blocks[i + 1][2]:
                blocks[i][1] += blocks.pop(i + 1)[1]
            if i > 0 and not blocks[i - 1][2]:
                blocks[i - 1][1] += blocks.pop(i)[1]
    return out
'''],
    guide=dict(
        prereqs="Lesson *Dynamic memory allocation and garbage collection* (implicit free lists, splitting, coalescing).",
        intuition="Represent the heap as an address-ordered list of blocks `[start, size, allocated]`: exactly what the implicit free list encodes with headers. `malloc` scans for the first free block that fits and maybe splits it; `free` flips the bit and merges with free neighbours.",
        hints=["Adjusted size: `max(16, round_up(n + 8, 8))`.", "Split only when the leftover is at least 16 bytes (the minimum block); otherwise the whole block is used (internal fragmentation).", "On free, merge with the next block first, then with the previous one (the four boundary-tag cases)."],
        brute_force="Model the heap as an array of bytes marked free/used and search for runs. Much slower and it loses block boundaries (which matter: a 16-byte leftover rule depends on them).",
        approach="1. Keep `blocks` sorted by start. 2. malloc: compute `asize`, first-fit scan, split or not, record the result by op index. 3. free: locate by start offset, mark free, coalesce next then previous.\n\nDry run of the example (64 bytes): A=[0,16], B=[16,16], free A, malloc(20) needs 32 → first fit is the block at 32 (the hole at 0 is only 16) → 32; malloc(4) needs 16 → offset 0.",
        complexity="O(number of blocks) per operation, as with a real implicit free list. Space O(blocks).",
        pitfalls="- Splitting when the remainder is smaller than 16 bytes creates unusable blocks.\n- Forgetting to coalesce produces false fragmentation: later large requests fail.\n- Best fit gives different answers from first fit.\n- Failed mallocs can later be 'freed': that must be a no-op.",
        follow_up="Implement next fit and best fit and compare peak utilization on the same trace; add `realloc`.",
    ),
),
dict(
    id="csapp-fd-sharing",
    title="File Descriptor Tables",
    difficulty="Medium",
    pattern="System-Level I/O",
    entry="run_io",
    description=r"""
Model how the Unix kernel represents open files for a single process: a **descriptor table**
whose entries point to **open file table** entries (each with its own *file position*), which in
turn refer to files.

`files` maps file names to their contents (strings). `ops` is a list of operations; return the list
of their results:

- `["open", name]` → opens the file for reading: creates a **new** open file table entry with
  position 0 and returns the **smallest unused descriptor** (descriptors 0, 1, 2 are already taken
  by stdin/stdout/stderr, so the first open returns 3). If the file does not exist, returns `-1`.
- `["read", fd, n]` → reads up to `n` characters from the current position, advances the position,
  and returns the string read (`""` at end of file). Invalid `fd` → `-1`.
- `["dup2", oldfd, newfd]` → makes `newfd` refer to the **same open file table entry** as `oldfd`
  (silently closing `newfd` first if it was open). Returns `newfd`. If `oldfd` is not open, returns
  `-1` and changes nothing. If `oldfd == newfd`, returns `newfd`.
- `["dup", fd]` → like `dup2` onto the smallest unused descriptor; returns it (or `-1`).
- `["close", fd]` → closes the descriptor; returns `0`, or `-1` if it was not open.

Descriptors 0–2 are reserved: they are never returned by `open`/`dup`, reads on them return `-1`.

**Example:** with `files = {"foobar.txt": "foobar"}` and ops
`open, open, read(3,1), read(4,1)` → `[3, 4, "f", "f"]` (two opens = independent positions),
whereas `open, dup(3), read(3,1), read(4,1)` → `[3, 4, "f", "o"]` (shared position).
""",
    starter='''def run_io(files: dict, ops: List[list]) -> list:
    pass
''',
    solution='''def run_io(files, ops):
    fdt = {}
    out = []

    def lowest():
        fd = 3
        while fd in fdt:
            fd += 1
        return fd

    for op in ops:
        kind = op[0]
        if kind == "open":
            if op[1] not in files:
                out.append(-1)
                continue
            fd = lowest()
            fdt[fd] = {"name": op[1], "pos": 0}
            out.append(fd)
        elif kind == "read":
            fd, n = op[1], op[2]
            if fd not in fdt:
                out.append(-1)
                continue
            e = fdt[fd]
            data = files[e["name"]][e["pos"]:e["pos"] + max(0, n)]
            e["pos"] += len(data)
            out.append(data)
        elif kind == "dup2":
            old, new = op[1], op[2]
            if old not in fdt:
                out.append(-1)
            else:
                fdt[new] = fdt[old]
                out.append(new)
        elif kind == "dup":
            if op[1] not in fdt:
                out.append(-1)
            else:
                fd = lowest()
                fdt[fd] = fdt[op[1]]
                out.append(fd)
        elif kind == "close":
            if op[1] in fdt:
                del fdt[op[1]]
                out.append(0)
            else:
                out.append(-1)
    return out
''',
    tests=[
        [{"foobar.txt": "foobar"}, [["open", "foobar.txt"], ["open", "foobar.txt"], ["read", 3, 1], ["read", 4, 1]]],
        [{"foobar.txt": "foobar"}, [["open", "foobar.txt"], ["dup", 3], ["read", 3, 1], ["read", 4, 1]]],
        [{"foobar.txt": "foobar"}, [["open", "foobar.txt"], ["open", "foobar.txt"], ["read", 4, 1], ["dup2", 4, 3], ["read", 3, 1]]],
        [{}, [["open", "nope"], ["read", 3, 5], ["close", 3], ["dup", 3], ["dup2", 3, 4]]],
        [{"a": "hello", "b": "world"}, [["open", "a"], ["open", "b"], ["close", 3], ["open", "b"], ["read", 3, 2], ["read", 4, 3], ["read", 3, 10], ["read", 3, 1]]],
        [{"a": "abcdef"}, [["open", "a"], ["dup2", 3, 7], ["read", 7, 2], ["close", 3], ["read", 7, 2], ["read", 3, 2], ["open", "a"], ["read", 3, 2]]],
        [{"a": "abcdef"}, [["open", "a"], ["dup2", 3, 3], ["read", 3, 3], ["dup", 3], ["dup", 3], ["close", 4], ["read", 5, 3], ["read", 4, 1]]],
        [{"a": "xyz"}, [["read", 0, 1], ["read", 1, 1], ["close", 5], ["open", "a"], ["read", 3, 0], ["read", 3, 100], ["read", 3, 1]]],
        [{"a": "0123456789", "b": "ABCDEFGHIJ"}, [["open", "a"], ["open", "b"], ["dup2", 4, 3], ["read", 3, 2], ["read", 4, 2], ["open", "a"], ["read", 5, 3]]],
        [{}, []],
        [{"f": "abcdefghij" * 3}, [["open", "f"]] + [["dup", 3]] * 5 + [["read", fd, 2] for fd in (8, 3, 5, 4, 7, 6)] + [["close", 5], ["dup", 8], ["read", 5, 4]]],
    ],
    wrong_solutions=['''def run_io(files, ops):
    fdt = {}
    out = []

    def lowest():
        fd = 3
        while fd in fdt:
            fd += 1
        return fd

    for op in ops:
        kind = op[0]
        if kind == "open":
            if op[1] not in files:
                out.append(-1)
                continue
            fd = lowest()
            fdt[fd] = {"name": op[1], "pos": 0}
            out.append(fd)
        elif kind == "read":
            fd, n = op[1], op[2]
            if fd not in fdt:
                out.append(-1)
                continue
            e = fdt[fd]
            data = files[e["name"]][e["pos"]:e["pos"] + max(0, n)]
            e["pos"] += len(data)
            out.append(data)
        elif kind == "dup2":
            old, new = op[1], op[2]
            if old not in fdt:
                out.append(-1)
            else:
                fdt[new] = dict(fdt[old])
                out.append(new)
        elif kind == "dup":
            if op[1] not in fdt:
                out.append(-1)
            else:
                fd = lowest()
                fdt[fd] = dict(fdt[op[1]])
                out.append(fd)
        elif kind == "close":
            if op[1] in fdt:
                del fdt[op[1]]
                out.append(0)
            else:
                out.append(-1)
    return out
''', '''def run_io(files, ops):
    pos = {}
    fdt = {}
    out = []
    nxt = 3
    for op in ops:
        kind = op[0]
        if kind == "open":
            if op[1] not in files:
                out.append(-1)
                continue
            fdt[nxt] = op[1]
            pos.setdefault(op[1], 0)
            out.append(nxt)
            nxt += 1
        elif kind == "read":
            fd, n = op[1], op[2]
            if fd not in fdt:
                out.append(-1)
                continue
            name = fdt[fd]
            data = files[name][pos[name]:pos[name] + max(0, n)]
            pos[name] += len(data)
            out.append(data)
        elif kind == "dup2":
            if op[1] not in fdt:
                out.append(-1)
            else:
                fdt[op[2]] = fdt[op[1]]
                out.append(op[2])
        elif kind == "dup":
            if op[1] not in fdt:
                out.append(-1)
            else:
                fdt[nxt] = fdt[op[1]]
                out.append(nxt)
                nxt += 1
        elif kind == "close":
            if op[1] in fdt:
                del fdt[op[1]]
                out.append(0)
            else:
                out.append(-1)
    return out
'''],
    guide=dict(
        prereqs="Lesson *File sharing, redirection and standard I/O* (descriptor table, open file table, v-node table).",
        intuition="The file position lives in the *open file table entry*, not in the descriptor and not in the file. `open` creates a new entry; `dup`/`dup2` copy a *pointer* to an existing entry. So descriptors made by `dup` share a position; descriptors from separate `open`s do not.",
        hints=["Use a dict `fd -> entry` where `entry` is a mutable object `{name, pos}`.", "`dup2(old, new)`: `table[new] = table[old]` (same object, not a copy).", "Lowest unused descriptor starts at 3 and must reuse closed slots."],
        brute_force="Not applicable; the alternative designs (position per descriptor, or per file) are simply wrong models.",
        approach="Dictionary of descriptors to shared entry objects; implement each operation literally. Dry run: `open` → 3, `dup(3)` → 4 (same entry), `read(3,1)` → 'f' (pos 1), `read(4,1)` → 'o'.",
        complexity="O(1) per operation apart from the scan for the lowest free descriptor and string slicing.",
        pitfalls="- Copying the entry on `dup` (independent positions).\n- Keeping one position per *file* (two `open`s must be independent).\n- Not reusing the lowest closed descriptor.\n- Closing one alias must not affect the other: the entry lives until its last descriptor closes.",
        follow_up="Add `fork` (the child gets a copy of the descriptor table pointing to the *same* entries, with reference counts) and trace the book's fork/read puzzles.",
    ),
),
dict(
    id="csapp-dotted-decimal",
    title="Hex ↔ Dotted-Decimal IP Addresses",
    difficulty="Easy",
    pattern="Network Programming",
    entry="convert",
    description=r"""
An IPv4 address is a 32-bit unsigned integer, conventionally written in **dotted-decimal** notation:
each of the four bytes (most significant first, i.e. network byte order) in decimal, separated by
periods. CS:APP's practice problems ask for `hex2dd` and `dd2hex`; write both in one function.

- If `s` starts with `"0x"`, it is a hex number of at most 8 hex digits: return its dotted-decimal form.
- Otherwise `s` is dotted-decimal: return `"0x"` followed by the lowercase hex value **without leading
  zeros** (like C's `%x`; zero is `"0x0"`).
- Return `"error"` for a malformed dotted-decimal string (not exactly four parts, a non-numeric or
  empty part, or a part outside 0–255) or a hex value that does not fit in 32 bits.

**Example:** `"0x8002c2f2"` → `"128.2.194.242"`; `"205.188.160.121"` → `"0xcdbca079"`;
`"0.0.4.0"` → `"0x400"`
""",
    starter='''def convert(s: str) -> str:
    pass
''',
    solution='''def convert(s):
    if s.startswith("0x"):
        try:
            v = int(s, 16)
        except ValueError:
            return "error"
        if v >= 1 << 32:
            return "error"
        return ".".join(str((v >> sh) & 0xFF) for sh in (24, 16, 8, 0))
    parts = s.split(".")
    if len(parts) != 4:
        return "error"
    v = 0
    for p in parts:
        if not p.isdigit() or int(p) > 255:
            return "error"
        v = (v << 8) | int(p)
    return "0x%x" % v
''',
    tests=[["0x8002c2f2"], ["205.188.160.121"], ["0.0.4.0"], ["0x0"], ["0.0.0.0"], ["0xffffffff"], ["255.255.255.255"],
           ["0x7f000001"], ["127.0.0.1"], ["64.12.149.13"], ["0x400"], ["256.1.1.1"], ["1.2.3"], ["1.2.3.4.5"],
           ["1..2.3"], ["0x100000000"], ["a.b.c.d"], ["0xD1558868"]],
    wrong_solutions=['''def convert(s):
    if s.startswith("0x"):
        v = int(s, 16)
        return ".".join(str((v >> sh) & 0xFF) for sh in (0, 8, 16, 24))
    parts = s.split(".")
    v = 0
    for p in parts:
        v = (v << 8) | int(p)
    return "0x%x" % v
''', '''def convert(s):
    if s.startswith("0x"):
        v = int(s, 16)
        if v >= 1 << 32:
            return "error"
        return ".".join(str((v >> sh) & 0xFF) for sh in (24, 16, 8, 0))
    parts = s.split(".")
    if len(parts) != 4:
        return "error"
    v = 0
    for p in parts:
        if not p.isdigit():
            return "error"
        v = (v << 8) | int(p)
    return "0x%08x" % v
'''],
    guide=dict(
        prereqs="Lesson *Networks, IP addresses and DNS*; byte ordering from Module 2.",
        intuition="Dotted decimal is just the four bytes of the 32-bit value written in base 10, most significant byte first. Convert with shifts and masks in one direction, and shift-and-or in the other.",
        hints=["Byte k from the top is `(v >> (24 - 8k)) & 0xFF`.", "Build the integer with `v = (v << 8) | part`.", "Validate: exactly four parts, each all digits and at most 255."],
        brute_force="Format the number as 8 hex digits and convert each pair; same work.",
        approach="Branch on the `0x` prefix. Dry run `0x8002c2f2`: bytes 0x80=128, 0x02=2, 0xc2=194, 0xf2=242.",
        complexity="O(1).",
        pitfalls="- Emitting the bytes in little-endian order.\n- Padding the hex output with zeros (`0.0.4.0` is `0x400`).\n- Accepting octets above 255 or the wrong number of parts.",
        follow_up="In C these are `inet_ntop`/`inet_pton` plus `htonl`/`ntohl`; note that the conversion functions work on network-byte-order values.",
    ),
),
dict(
    id="csapp-race-outcomes",
    title="Race Condition Outcomes (badcnt)",
    difficulty="Medium",
    pattern="Concurrency",
    entry="race_outcomes",
    description=r"""
CS:APP's `badcnt.c` runs two threads that each execute `cnt++` in a loop without synchronization.
At the machine level each increment is three steps on a **private register**:

1. **L**oad: `reg = cnt`
2. **U**pdate: `reg = reg + 1`
3. **S**tore: `cnt = reg`

Thread 1 performs `n1` increments and thread 2 performs `n2`; `cnt` starts at 0. The scheduler may
interleave the steps of the two threads arbitrarily (each thread's own steps stay in order).

Return the **sorted list of all possible final values** of `cnt`.

Constraints: `0 <= n1, n2 <= 5`.

**Example:** `n1 = 1, n2 = 1` → `[1, 2]`

**Example:** `n1 = 2, n2 = 2` → `[2, 3, 4]`
""",
    starter='''def race_outcomes(n1: int, n2: int) -> List[int]:
    pass
''',
    solution='''def race_outcomes(n1, n2):
    end = (3 * n1, 3 * n2)
    start = (0, 0, 0, 0, 0)  # pc1, reg1, pc2, reg2, cnt
    seen = {start}
    stack = [start]
    finals = set()
    while stack:
        pc1, r1, pc2, r2, cnt = stack.pop()
        if pc1 == end[0] and pc2 == end[1]:
            finals.add(cnt)
            continue
        nxt = []
        if pc1 < end[0]:
            ph = pc1 % 3
            if ph == 0:
                nxt.append((pc1 + 1, cnt, pc2, r2, cnt))
            elif ph == 1:
                nxt.append((pc1 + 1, r1 + 1, pc2, r2, cnt))
            else:
                nxt.append((pc1 + 1, 0, pc2, r2, r1))
        if pc2 < end[1]:
            ph = pc2 % 3
            if ph == 0:
                nxt.append((pc1, r1, pc2 + 1, cnt, cnt))
            elif ph == 1:
                nxt.append((pc1, r1, pc2 + 1, r2 + 1, cnt))
            else:
                nxt.append((pc1, r1, pc2 + 1, 0, r2))
        for s in nxt:
            if s not in seen:
                seen.add(s)
                stack.append(s)
    return sorted(finals)
''',
    tests=[[1, 1], [2, 2], [0, 0], [0, 3], [3, 0], [1, 2], [1, 5], [3, 3], [2, 5], [4, 4], [5, 5], [5, 1]],
    wrong_solutions=['''def race_outcomes(n1, n2):
    return [n1 + n2]
''', '''def race_outcomes(n1, n2):
    if n1 == 0 or n2 == 0:
        return [n1 + n2]
    return list(range(max(n1, n2), n1 + n2 + 1))
''', '''def race_outcomes(n1, n2):
    if n1 == 0 or n2 == 0:
        return [n1 + n2]
    return list(range(2, n1 + n2 + 1))
'''],
    guide=dict(
        prereqs="Lesson *Synchronization with semaphores* (the `badcnt` example and progress graphs).",
        intuition="The program's state is tiny: each thread's position in its L/U/S sequence, each thread's register, and `cnt`. Explore every reachable state by trying both possible next steps: a graph search over the progress graph.",
        hints=["State = (pc1, reg1, pc2, reg2, cnt), with `pc % 3` telling you whether the next step is L, U or S.",
               "From each state there are at most two successors (advance thread 1 or thread 2).",
               "Collect `cnt` whenever both threads have finished; memoize visited states."],
        brute_force="Enumerate all interleavings explicitly: there are C(3(n1+n2), 3n1) of them (about 155 million for 5 and 5), far too many. The state-space search visits only a few thousand states.",
        approach="DFS/BFS with a visited set. Dry run n1=n2=1: orders like L1 U1 S1 L2 U2 S2 give 2; L1 L2 U1 U2 S1 S2 gives 1 (a lost update). Hence `[1, 2]`.",
        complexity="O(number of reachable states) = O(n1 · n2 · (n1+n2)^3) in the worst case, tiny for n ≤ 5.",
        pitfalls="- Assuming the minimum is `max(n1, n2)`: for n1 = n2 = 2 the value 2 is right, but with more iterations the minimum is **2**, not n (a thread can load early and store late, wiping out many of the other's increments, and vice versa).\n- When one thread does a single increment the minimum is 1.\n- With one thread idle there is no race.",
        follow_up="Add a mutex: wrap L-U-S in P(mutex)/V(mutex) steps and verify that only `n1 + n2` remains possible.",
    ),
),
dict(
    id="csapp-deadlock-check",
    title="Deadlock Detection via Progress Graph",
    difficulty="Hard",
    pattern="Concurrency",
    entry="can_deadlock",
    description=r"""
Each thread is a sequence of semaphore operations `["P", name]` or `["V", name]`. All semaphores are
**binary semaphores (mutexes) initialized to 1**.

- `P(s)`: if `s > 0`, decrement and continue; if `s == 0`, the thread **blocks** until another
  thread performs `V(s)`.
- `V(s)`: increment `s`.

`threads` is a list of threads (1 to 3 threads, each with at most 8 operations). The scheduler may
interleave them arbitrarily. Return `True` if **some** interleaving reaches a **deadlock**: a state
in which at least one thread has not finished and no unfinished thread can take its next step.
Otherwise return `False`.

This is the *progress graph* analysis from the lesson: a deadlock exists iff a trajectory can
enter a state from which no move is possible.

**Example:** thread 1 = `P(a) P(b) V(b) V(a)`, thread 2 = `P(b) P(a) V(a) V(b)` → `True`
(thread 1 holds `a` and waits for `b`; thread 2 holds `b` and waits for `a`).

**Example:** both threads `P(a) P(b) V(b) V(a)` → `False` (same lock order).
""",
    starter='''def can_deadlock(threads: List[List[List[str]]]) -> bool:
    pass
''',
    solution='''def can_deadlock(threads):
    n = len(threads)
    lens = [len(t) for t in threads]

    def sem_values(pcs):
        vals = collections.defaultdict(lambda: 1)
        for t, pc in zip(threads, pcs):
            for op, name in t[:pc]:
                vals[name] += -1 if op == "P" else 1
        return vals

    start = tuple([0] * n)
    seen = {start}
    stack = [start]
    while stack:
        pcs = stack.pop()
        if all(pcs[i] == lens[i] for i in range(n)):
            continue
        vals = sem_values(pcs)
        moved = False
        for i in range(n):
            if pcs[i] == lens[i]:
                continue
            op, name = threads[i][pcs[i]]
            if op == "P" and vals[name] <= 0:
                continue
            moved = True
            nxt = pcs[:i] + (pcs[i] + 1,) + pcs[i + 1:]
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
        if not moved:
            return True
    return False
''',
    tests=[
        [[[["P", "a"], ["P", "b"], ["V", "b"], ["V", "a"]], [["P", "b"], ["P", "a"], ["V", "a"], ["V", "b"]]]],
        [[[["P", "a"], ["P", "b"], ["V", "b"], ["V", "a"]], [["P", "a"], ["P", "b"], ["V", "b"], ["V", "a"]]]],
        [[[["P", "a"], ["V", "a"]]]],
        [[[["P", "a"], ["P", "a"]]]],
        [[[], []]],
        [[[["P", "a"], ["V", "a"], ["P", "b"], ["V", "b"]], [["P", "b"], ["V", "b"], ["P", "a"], ["V", "a"]]]],
        [[[["P", "a"], ["P", "b"], ["V", "a"], ["V", "b"]], [["P", "b"], ["P", "a"], ["V", "b"], ["V", "a"]]]],
        [[[["P", "a"], ["P", "b"], ["V", "b"], ["V", "a"]], [["P", "b"], ["P", "c"], ["V", "c"], ["V", "b"]],
          [["P", "c"], ["P", "a"], ["V", "a"], ["V", "c"]]]],
        [[[["P", "a"], ["P", "b"], ["V", "b"], ["V", "a"]], [["P", "b"], ["P", "c"], ["V", "c"], ["V", "b"]],
          [["P", "a"], ["P", "c"], ["V", "c"], ["V", "a"]]]],
        [[[["P", "a"]], [["P", "a"], ["V", "a"]]]],
        [[[["P", "a"], ["V", "a"]], [["V", "b"], ["P", "b"], ["P", "b"], ["P", "a"], ["V", "a"]]]],
        [[[["P", "g"], ["P", "a"], ["P", "b"], ["V", "b"], ["V", "a"], ["V", "g"]],
          [["P", "g"], ["P", "b"], ["P", "a"], ["V", "a"], ["V", "b"], ["V", "g"]]]],
        [[[["P", "a"], ["P", "b"], ["P", "c"], ["V", "c"], ["V", "b"], ["V", "a"]],
          [["P", "c"], ["P", "b"], ["P", "a"], ["V", "a"], ["V", "b"], ["V", "c"]]]],
    ],
    wrong_solutions=['''def can_deadlock(threads):
    orders = []
    for t in threads:
        held, pairs = [], set()
        for op, name in t:
            if op == "P":
                for h in held:
                    pairs.add((h, name))
                held.append(name)
            elif name in held:
                held.remove(name)
        orders.append(pairs)
    for i in range(len(orders)):
        for j in range(i + 1, len(orders)):
            for a, b in orders[i]:
                if (b, a) in orders[j]:
                    return True
    return False
''', '''def can_deadlock(threads):
    return False
'''],
    guide=dict(
        prereqs="Lesson *Parallelism, thread safety, races and deadlock* (progress graphs, mutex lock ordering rule).",
        intuition="The global state is just the tuple of program counters: semaphore values are determined by which P and V operations have executed. Search all reachable states; a deadlock is a reachable, unfinished state with no enabled move.",
        hints=["Compute each semaphore's value from the prefixes executed: 1 − (#P) + (#V).", "A thread's next op is enabled unless it is a P on a semaphore whose value is 0.", "DFS/BFS over pc tuples with a visited set; return True at the first stuck state."],
        brute_force="Enumerate every interleaving (a multinomial number of them). The state-space search collapses interleavings that reach the same state: at most 9³ states here.",
        approach="1. Start at all-zero pcs. 2. For each state compute semaphore values and the enabled threads. 3. No enabled thread and not all done → deadlock. 4. Otherwise push successors.\n\nDry run of the classic example: from (0,0) go to (1,0) [T1 holds a], then (1,1) [T2 holds b]. Now T1 needs b (0) and T2 needs a (0): stuck → True.",
        complexity="O(S · T · L) where S ≤ ∏(len_i + 1) states, T threads, L ops for recomputing values (can be made incremental).",
        pitfalls="- A pairwise lock-order check misses cycles through three threads (a→b, b→c, c→a) and falsely flags orders protected by an outer 'gate' lock.\n- A single thread can deadlock itself (`P(a) P(a)`).\n- A thread that ends while holding a lock can strand others forever: that is a deadlock under this definition.\n- Being *able* to deadlock does not mean every run deadlocks.",
        follow_up="Return a witness interleaving, or compute the lock-order graph and show that an acyclic order (the mutex lock ordering rule) implies no deadlock.",
    ),
),
]
