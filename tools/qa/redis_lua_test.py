"""Run the Lua scripts from the Redis track against fakeredis (real Lua via lupa).

1. Every lua block in every redis lesson must compile (SCRIPT LOAD).
2. Lesson 24's sharded-list push/pop scripts are fuzzed against a Python deque.
Usage: python -I redis_lua_test.py <path to study-guide>
"""
import collections
import pathlib
import random
import re
import sys

import fakeredis

BT = chr(96) * 3
root = pathlib.Path(sys.argv[1])
r = fakeredis.FakeRedis(decode_responses=True)

# 1. compile every Lua block
total = bad = 0
blocks_24 = []
for p in sorted((root / "src" / "redis" / "lessons").glob("*.md")):
    for code in re.findall(BT + "lua\r?\n(.*?)" + BT, p.read_text(encoding="utf-8"), re.S):
        total += 1
        if p.name.startswith("24-"):
            blocks_24.append(code)
        try:
            r.script_load(code)
        except Exception as e:  # noqa: BLE001
            bad += 1
            print("COMPILE?", p.name, "|", str(e)[:120], "|", code.strip().splitlines()[0][:80])
print(f"compiled {total - bad}/{total} Lua blocks")

# 2. fuzz the sharded list scripts
push_src = next(b for b in blocks_24 if "lpush" in b and "rpush" in b and "unpack" in b)
pop_src = next(b for b in blocks_24 if "lpop" in b and "rpop" in b and "EXISTS" in b)
push, pop = r.register_script(push_src), r.register_script(pop_src)


def run(seed, cap, ops):
    r.flushall()
    rnd = random.Random(seed)
    model = collections.deque()
    keys = ["jobs:", "jobs:first", "jobs:last"]
    counter = 0
    for step in range(ops):
        op = rnd.choice(["rpush", "lpush", "rpop", "lpop", "rpush", "lpush"])
        if op.endswith("push"):
            items = [str(counter + i) for i in range(rnd.randint(1, 2 * cap + 1))]
            counter += len(items)
            pending = list(items)
            while pending:  # the caller loop from the lesson
                n = push(keys=keys, args=[op, cap] + pending[:64])
                assert 0 < n <= len(pending), (seed, step, op, n)
                for it in pending[:n]:
                    (model.appendleft if op == "lpush" else model.append)(it)
                del pending[:n]
        else:
            got = pop(keys=keys, args=[op])
            want = (model.popleft() if op == "lpop" else model.pop()) if model else None
            assert got == want, (seed, step, op, got, want)
        first = int(r.get("jobs:first") or 0)
        last = int(r.get("jobs:last") or 0)
        lens = [r.llen(f"jobs:{i}") for i in range(first, last + 1)]
        assert sum(lens) == len(model), (seed, step, lens, len(model))
        assert all(x == cap for x in lens[1:-1]), (seed, step, "middle shard not full", lens)
        assert all(x <= cap for x in lens), (seed, step, "over capacity", lens)
        flat = [v for i in range(first, last + 1) for v in r.lrange(f"jobs:{i}", 0, -1)]
        assert flat == list(model), (seed, step)


for seed in range(30):
    run(seed, cap=random.Random(seed).choice([1, 2, 3, 5]), ops=100)
print("sharded list scripts: 30 seeds x 100 ops agree with a deque; invariants hold")
