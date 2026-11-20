PROBLEMS = [
dict(
    id="docker-parse-image-ref",
    title="Parse an Image Reference",
    difficulty="Medium",
    pattern="Images & Registries",
    entry="parseImageRef",
    description=r"""
Every `docker pull` starts by turning a short name such as `nginx` into a full address. Write
`parseImageRef(ref)` that returns `[registry, repository, tag, digest]` (four strings) using Docker's rules.

1. **Digest.** If `ref` contains `@`, everything after the first `@` is the digest. Remove it before the next steps.
   Otherwise the digest is `""`.
2. **Registry.** Look at the text before the first `/`. It is a registry host only if there *is* a `/` **and** that
   text contains a `.` or a `:` or is exactly `localhost`. Otherwise the registry is `docker.io` and the whole
   string is the path.
3. **Tag.** If the **last** path component (after the last `/`) contains `:`, the text after that `:` is the tag and
   is removed from the path. (A `:` in the registry host is a port, not a tag.)
4. **Repository.** The remaining path. If the registry is `docker.io` and the path has no `/`, prefix it with `library/`.
5. **Default tag.** If there is no tag **and no digest**, the tag is `latest`. If there is a digest and no tag, the tag is `""`.

The input is always a syntactically valid reference.

**Example 1:** `"nginx"` → `["docker.io", "library/nginx", "latest", ""]`

**Example 2:** `"localhost:5000/team/api:2.1"` → `["localhost:5000", "team/api", "2.1", ""]`

**Example 3:** `"python@sha256:abc"` → `["docker.io", "library/python", "", "sha256:abc"]`
""",
    starter='''def parseImageRef(ref):
    # return [registry, repository, tag, digest]
    pass
''',
    solution='''def parseImageRef(ref):
    digest = ""
    if "@" in ref:
        ref, digest = ref.split("@", 1)
    first, slash, rest = ref.partition("/")
    if slash and ("." in first or ":" in first or first == "localhost"):
        registry, path = first, rest
    else:
        registry, path = "docker.io", ref
    tag = ""
    last = path.rsplit("/", 1)[-1]
    if ":" in last:
        path, tag = path.rsplit(":", 1)
    if registry == "docker.io" and "/" not in path:
        path = "library/" + path
    if not tag and not digest:
        tag = "latest"
    return [registry, path, tag, digest]
''',
    tests=[
        ["nginx"],
        ["localhost:5000/team/api:2.1"],
        ["python@sha256:abc"],
        ["harbour/ledger"],
        ["harbour/ledger:1.8.0"],
        ["ghcr.io/harbour/tools/lint:2"],
        ["registry.example.com:5000/payments/ledger"],
        ["redis:7-alpine"],
        ["quay.io/prom/node-exporter:v1.8.2@sha256:def456"],
        ["localhost/ledger"],
        ["buildbox:5000/ledger"],
        ["my.registry/app@sha256:0011"],
        ["a/b/c/d:x"],
        ["docker.io/nginx"],
    ],
    examples=3,
    wrong_solutions=[
        '''def parseImageRef(ref):
    digest = ""
    if "@" in ref:
        ref, digest = ref.split("@", 1)
    tag = "latest"
    if ":" in ref:
        ref, tag = ref.rsplit(":", 1)
    first, slash, rest = ref.partition("/")
    if slash and "." in first:
        return [first, rest, tag, digest]
    if "/" not in ref:
        ref = "library/" + ref
    return ["docker.io", ref, tag, digest]
''',
        '''def parseImageRef(ref):
    digest = ""
    if "@" in ref:
        ref, digest = ref.split("@", 1)
    first, slash, rest = ref.partition("/")
    if slash and ("." in first or ":" in first or first == "localhost"):
        registry, path = first, rest
    else:
        registry, path = "docker.io", ref
    tag = "latest"
    if ":" in path.rsplit("/", 1)[-1]:
        path, tag = path.rsplit(":", 1)
    if registry == "docker.io" and "/" not in path:
        path = "library/" + path
    return [registry, path, tag, digest]
''',
    ],
    guide=dict(
        prereqs="Lesson *Registries, image references, tags and digests*. Python string methods `split`, `partition`, `rsplit`.",
        intuition="A reference is read **from the outside in**: peel the digest off the right end, decide whether the left end is a "
                  "host, and only then look for a tag, because a colon means *port* in the host and *tag* in the last component.",
        hints=[
            "Handle `@` first; after that the digest can never confuse the other steps.",
            "`s.partition('/')` gives you the text before the first slash and tells you whether a slash existed at all.",
            "Search for the tag colon only in `path.rsplit('/', 1)[-1]`, then apply the `library/` and `latest` defaults last.",
        ],
        brute_force="Trying to do it with one big regular expression is possible but fragile: the host/namespace ambiguity "
                    "(`harbour/ledger` vs `harbour.io/ledger`) needs a rule, not a pattern.",
        approach="1. Split on the first `@`.\n2. `first, slash, rest = ref.partition('/')`; host if `slash` and "
                 "(`.` or `:` in `first`, or `first == 'localhost'`).\n3. Take the last component; if it has `:`, `rsplit(':', 1)` the path.\n"
                 "4. Add `library/` for single-name Docker Hub repositories.\n5. Default the tag to `latest` only when there is no digest.\n\n"
                 "**Dry run** `buildbox:5000/ledger`: no `@`. `first='buildbox:5000'` contains `:` → registry. Path `ledger`, last component "
                 "has no `:` → no tag. Registry is not `docker.io` so no `library/`. No tag, no digest → `latest`. "
                 "Result `['buildbox:5000', 'ledger', 'latest', '']`.",
        complexity="Time O(n) in the length of the reference, space O(n) for the pieces.",
        pitfalls="- Splitting on the **first** colon treats a registry port as a tag.\n- Adding `latest` when a digest is present.\n"
                 "- Treating `localhost/ledger` as a Docker Hub namespace.\n- `docker.io/nginx` must still become `library/nginx`.",
        follow_up="Validate the pieces (lowercase repository, tag at most 128 characters), or render the canonical string back.",
    ),
),
dict(
    id="docker-semver-tags",
    title="Select a Tag by Version Constraint",
    difficulty="Medium",
    pattern="Images & Registries",
    entry="selectTag",
    description=r"""
A dependency-update bot must pick the newest image tag that satisfies a constraint. Write `selectTag(tags, constraint)`.

**Version tags.** A tag is a version only if it is `X.Y.Z` or `vX.Y.Z` where X, Y, Z are non-negative integers written
in digits. Every other tag (`latest`, `2.4`, `3.0.0-rc.1`, `1.2.3-alpine`) is ignored.

**Constraints** (the constraint never has a `v` prefix):

| Constraint | Matches versions `(X, Y, Z)` with |
|---|---|
| `*` | anything |
| `A.B.C` | exactly `(A, B, C)` |
| `~A.B.C` | `X == A`, `Y == B`, `Z >= C` |
| `^A.B.C` | `X == A` and `(Y, Z) >= (B, C)` |
| `A.B` | `X == A`, `Y == B` |
| `A` | `X == A` |

Return the **original tag string** of the highest matching version, comparing `(X, Y, Z)` as integers. If two tags
have the same version (`1.2.3` and `v1.2.3`) return the one that appears first in `tags`. Return `""` if nothing matches.

**Example 1:** `tags = ["2.9.3", "2.10.0", "latest"]`, `constraint = "^2.4.0"` → `"2.10.0"`

**Example 2:** `tags = ["1.4.0", "1.4.7", "1.5.0"]`, `constraint = "~1.4.2"` → `"1.4.7"`
""",
    starter='''def selectTag(tags, constraint):
    pass
''',
    solution='''import re

def selectTag(tags, constraint):
    def version(tag):
        m = re.fullmatch(r"v?(\\d+)\\.(\\d+)\\.(\\d+)", tag)
        return tuple(int(g) for g in m.groups()) if m else None

    if constraint == "*":
        ok = lambda v: True
    elif constraint[0] in "~^":
        a, b, c = (int(p) for p in constraint[1:].split("."))
        if constraint[0] == "~":
            ok = lambda v: v[0] == a and v[1] == b and v[2] >= c
        else:
            ok = lambda v: v[0] == a and (v[1], v[2]) >= (b, c)
    else:
        want = tuple(int(p) for p in constraint.split("."))
        ok = lambda v: v[:len(want)] == want
    best, best_v = "", None
    for tag in tags:
        v = version(tag)
        if v is not None and ok(v) and (best_v is None or v > best_v):
            best, best_v = tag, v
    return best
''',
    tests=[
        [["2.9.3", "2.10.0", "latest"], "^2.4.0"],
        [["1.4.0", "1.4.7", "1.5.0"], "~1.4.2"],
        [["1.9.7", "2.4.0", "2.4.1", "2.10.0", "3.0.0-rc.1"], "*"],
        [["1.9.7", "2.4.0", "2.4.1"], "2.4.0"],
        [["1.9.7", "2.4.0", "2.4.1"], "3.0.0"],
        [["v1.2.3", "1.2.3", "1.2.10", "1.2.9"], "1.2"],
        [["v1.2.3", "1.2.3"], "1"],
        [["1.2.3", "v1.2.3"], "~1.2.0"],
        [[], "*"],
        [["latest", "stable", "2.4", "1.2.3-alpine"], "*"],
        [["2.3.9", "2.4.0", "3.0.0"], "^2.4.1"],
        [["0.9.10", "0.10.2", "0.9.9"], "0"],
        [["10.0.0", "9.9.9", "2.0.0"], "*"],
        [["1.4.1", "1.4.2", "1.3.9"], "~1.4.2"],
        [["2.4.5", "2.5.0", "2.5.1"], "^2.5.1"],
    ],
    examples=2,
    wrong_solutions=[
        '''def selectTag(tags, constraint):
    import re
    c = constraint.lstrip("~^")
    good = [t for t in tags if re.fullmatch(r"v?\\d+\\.\\d+\\.\\d+", t)]
    if constraint == "*":
        return max(good) if good else ""
    major = c.split(".")[0]
    good = [t for t in good if t.lstrip("v").split(".")[0] == major]
    return max(good) if good else ""
''',
        '''import re

def selectTag(tags, constraint):
    best, best_v = "", None
    for tag in tags:
        m = re.fullmatch(r"v?(\\d+)\\.(\\d+)\\.(\\d+)", tag)
        if not m:
            continue
        v = tuple(int(g) for g in m.groups())
        if constraint == "*":
            ok = True
        elif constraint[0] in "~^":
            a, b, c = (int(p) for p in constraint[1:].split("."))
            ok = v[0] == a and v[1] == b and v[2] >= c
        else:
            want = tuple(int(p) for p in constraint.split("."))
            ok = v[:len(want)] == want
        if ok and (best_v is None or v >= best_v):
            best, best_v = tag, v
    return best
''',
    ],
    guide=dict(
        prereqs="Lesson *Tagging and versioning strategy*. Tuples compare element by element in Python.",
        intuition="Turn each tag into a tuple of three integers. Then every constraint is a small test on a tuple and "
                  "'newest' is the built-in tuple ordering. Never compare versions as text.",
        hints=[
            "`re.fullmatch(r'v?(\\d+)\\.(\\d+)\\.(\\d+)', tag)` both validates and extracts.",
            "Build one predicate function per constraint kind; `^` compares `(minor, patch) >= (B, C)` as a pair.",
            "Scan once keeping the best; use strict `>` so the earlier of two equal versions wins.",
        ],
        brute_force="Sort every tag as a string and walk backwards. It fails at once on `2.10.0` versus `2.9.3`, because `'1' < '9'`.",
        approach="1. Parse the constraint into a predicate.\n2. For each tag, parse to `(X, Y, Z)` or skip.\n3. Keep the tag whose tuple is "
                 "strictly greater than the best so far.\n\n**Dry run** `['2.3.9','2.4.0','3.0.0']`, `^2.4.1`: `(2,3,9)` → major ok, `(3,9) >= (4,1)` false. "
                 "`(2,4,0)` → `(4,0) >= (4,1)` false. `(3,0,0)` → major differs. Nothing matches → `\"\"`.",
        complexity="Time O(n) for n tags (each parse is O(length)), space O(1) beyond the input.",
        pitfalls="- String comparison of versions.\n- Treating `~` and `^` the same.\n- Accepting pre-release or suffixed tags.\n"
                 "- Using `>=` when updating the best, which returns the later duplicate.",
        follow_up="Add pre-release ordering (`3.0.0-rc.1 < 3.0.0`) or range constraints such as `>=2.0.0 <3.0.0`.",
    ),
),
dict(
    id="docker-image-size-dedup",
    title="Disk Usage with Shared Layers",
    difficulty="Easy",
    pattern="Images & Layers",
    entry="diskUsage",
    description=r"""
`docker image ls` shows each image's full size, but layers are stored once and shared. Write `diskUsage(images)`.

`images` is a dict: image name → list of layers, bottom first. Each layer is `[layer_id, size_in_bytes]`.
Two layers with the same `layer_id` are the same layer (and always have the same size).
If one image lists the same `layer_id` more than once, it counts once for that image.

Return `[virtual, actual, shared]` where

- `virtual` = the sum, over all images, of that image's size (each distinct layer of the image counted once);
- `actual` = bytes really on disk: every distinct layer across all images counted once;
- `shared` = total size of the distinct layers that are used by **two or more** images.

**Example:** `{"api": [["base", 100], ["deps", 50], ["a", 5]], "worker": [["base", 100], ["deps", 50], ["w", 7]]}`
→ `[312, 162, 150]`
""",
    starter='''def diskUsage(images):
    # return [virtual, actual, shared]
    pass
''',
    solution='''def diskUsage(images):
    size, users = {}, {}
    virtual = 0
    for layers in images.values():
        seen = set()
        for lid, sz in layers:
            if lid in seen:
                continue
            seen.add(lid)
            size[lid] = sz
            users[lid] = users.get(lid, 0) + 1
            virtual += sz
    actual = sum(size.values())
    shared = sum(size[l] for l in size if users[l] >= 2)
    return [virtual, actual, shared]
''',
    tests=[
        [{"api": [["base", 100], ["deps", 50], ["a", 5]], "worker": [["base", 100], ["deps", 50], ["w", 7]]}],
        [{}],
        [{"solo": [["x", 10], ["y", 20]]}],
        [{"a": [], "b": []}],
        [{"a": [["l", 9]], "b": [["l", 9]], "c": [["l", 9]]}],
        [{"a": [["dup", 40], ["dup", 40], ["top", 1]]}],
        [{"a": [["dup", 40], ["dup", 40]], "b": [["dup", 40]]}],
        [{"a": [["b1", 70], ["x", 3]], "b": [["b2", 70], ["x", 3]]}],
        [{"a": [["z", 0], ["q", 5]], "b": [["z", 0]]}],
        [{"img%d" % i: [["base", 1000], ["mid%d" % (i % 3), 200], ["top%d" % i, i]] for i in range(60)}],
        [{"a": [["1", 1], ["2", 2], ["3", 4]], "b": [["3", 4], ["2", 2]], "c": [["4", 8]]}],
    ],
    examples=1,
    wrong_solutions=[
        '''def diskUsage(images):
    size, users, virtual = {}, {}, 0
    for layers in images.values():
        for lid, sz in layers:
            size[lid] = sz
            users[lid] = users.get(lid, 0) + 1
            virtual += sz
    return [virtual, sum(size.values()), sum(size[l] for l in size if users[l] >= 2)]
''',
        '''def diskUsage(images):
    virtual = sum(sz for layers in images.values() for _, sz in {l[0]: l for l in layers}.values())
    sizes = set()
    for layers in images.values():
        for lid, sz in layers:
            sizes.add(sz)
    actual = sum(sizes)
    return [virtual, actual, virtual - actual]
''',
    ],
    guide=dict(
        prereqs="Lesson *What a container is* (layer sharing). Dictionaries and sets.",
        intuition="A layer is identified by its ID, not by which image mentions it. Count *per image* for the virtual total, "
                  "count *per distinct ID* for the real total, and remember how many images use each ID.",
        hints=[
            "Keep two dictionaries keyed by layer ID: its size and the number of images that use it.",
            "Use a per-image `set` so a repeated layer inside one image is counted once.",
            "`actual` is the sum of the size dictionary; `shared` is the same sum restricted to IDs with a user count of 2 or more.",
        ],
        brute_force="For each layer, scan every other image to see whether it also has it: O(L x L). Fine for tiny inputs, wasteful for many images.",
        approach="One pass over all images. For each image create an empty `seen` set; for each layer not yet in `seen`, add its size to "
                 "`virtual`, record its size and increase its user count. Afterwards sum.\n\n**Dry run** (the example): `api` adds 155 to virtual, "
                 "users base=1, deps=1, a=1. `worker` adds 157, users base=2, deps=2, w=1. virtual 312; actual 100+50+5+7 = 162; shared 100+50 = 150.",
        complexity="Time O(L) for L layer entries in total, space O(D) for D distinct layers.",
        pitfalls="- Counting a layer twice when one image lists it twice.\n- Computing `shared` as `virtual - actual` (that is the bytes *saved*, "
                 "a different number when three images share a layer).\n- Deduplicating by size instead of by ID.",
        follow_up="Report how many bytes would be freed by deleting one named image (only layers no other image uses).",
    ),
),
dict(
    id="docker-union-fs-lookup",
    title="Union Filesystem Lookup with Whiteouts",
    difficulty="Medium",
    pattern="Storage",
    entry="unionLookup",
    description=r"""
A container's filesystem is a stack of layers merged by a union filesystem. Write `unionLookup(layers, paths)`.

- `layers` is a list, **bottom layer first, top layer last**. Each layer is a dict mapping an absolute path
  (`"/app/main.py"`, never ending in `/`) to either a string (the file's content) or `None`, which is a **whiteout**.
- A whiteout at path `P` in a layer hides `P` itself **and every path below it** (every path starting with `P + "/"`)
  in all layers **underneath** that layer.
- To read a path, examine layers from the top down. In each layer:
  1. if the layer has an entry for the exact path, the answer is that entry (content, or "missing" if it is a whiteout);
  2. otherwise, if the layer has a whiteout for any ancestor directory of the path, the answer is "missing";
  3. otherwise continue with the next layer down.
- If no layer answers, the path is missing.

Return a list with one item per queried path: the content string, or `None` if missing.

**Example:** `layers = [{"/a/x": "1", "/b": "2"}, {"/a": None}, {"/a/y": "3"}]`, `paths = ["/a/x", "/a/y", "/b"]`
→ `[None, "3", "2"]`  (`/a/x` is hidden by the whiteout of `/a`; `/a/y` was created above the whiteout.)
""",
    starter='''def unionLookup(layers, paths):
    pass
''',
    solution='''def unionLookup(layers, paths):
    def lookup(path):
        parts = path.split("/")
        ancestors = ["/".join(parts[:i]) for i in range(2, len(parts))]
        for layer in reversed(layers):
            if path in layer:
                return layer[path]
            for a in ancestors:
                if a in layer and layer[a] is None:
                    return None
        return None
    return [lookup(p) for p in paths]
''',
    tests=[
        [[{"/a/x": "1", "/b": "2"}, {"/a": None}, {"/a/y": "3"}], ["/a/x", "/a/y", "/b"]],
        [[{"/etc/motd": "hi"}], ["/etc/motd", "/etc/none"]],
        [[], ["/x"]],
        [[{"/f": "low"}, {"/f": "mid"}, {"/f": "top"}], ["/f"]],
        [[{"/f": "low"}, {"/f": None}], ["/f"]],
        [[{"/f": "low"}, {"/f": None}, {"/f": "again"}], ["/f"]],
        [[{"/d/a": "1", "/d/b/c": "2"}, {"/d": None, "/d/a": "new"}], ["/d/a", "/d/b/c"]],
        [[{"/app/main.py": "v1", "/application/x": "keep"}, {"/app": None}], ["/app/main.py", "/application/x"]],
        [[{"/a/b/c/d": "deep"}, {"/a/b": None}, {}], ["/a/b/c/d", "/a/b"]],
        [[{"/a": "file"}, {"/a/b": "child"}], ["/a", "/a/b"]],
        [[{"/x": "1"}, {}, {}], ["/x", "/y"]],
        [[{"/k/v": "1"}, {"/k": None}, {"/k/v": "2"}, {"/k": None}], ["/k/v"]],
        [[{"/p%d" % i: str(i)} for i in range(200)], ["/p0", "/p199", "/p200"]],
    ],
    examples=1,
    wrong_solutions=[
        '''def unionLookup(layers, paths):
    out = []
    for p in paths:
        ans = None
        for layer in reversed(layers):
            if p in layer:
                ans = layer[p]
                break
        out.append(ans)
    return out
''',
        '''def unionLookup(layers, paths):
    def lookup(path):
        for layer in reversed(layers):
            if path in layer:
                return layer[path]
            for k, v in layer.items():
                if v is None and path.startswith(k):
                    return None
        return None
    return [lookup(p) for p in paths]
''',
    ],
    guide=dict(
        prereqs="Lessons *What a container is* and *The writable layer and copy-on-write*. Dictionaries; iterating a list in reverse.",
        intuition="The top layer speaks first. A layer can say three things about a path: 'here it is', 'it is deleted', or nothing. "
                  "A deleted directory also answers 'deleted' for everything inside it, but only for the layers below.",
        hints=[
            "Walk `reversed(layers)` and stop at the first layer that has an opinion.",
            "Check the exact path **before** the ancestors: a file recreated in the same layer as the directory whiteout must be visible.",
            "Ancestors of `/a/b/c` are `/a` and `/a/b`. Build them from `path.split('/')`; do not use `startswith` on raw strings.",
        ],
        brute_force="Materialise the merged tree: apply layers bottom-up into one dict, deleting keys under each whiteout. "
                    "Correct, but costs O(total entries x whiteouts) even when you only query one path.",
        approach="For each query: compute the ancestor list once, then for each layer from the top: exact hit → return its value; "
                 "ancestor whiteout → return `None`; else go lower.\n\n**Dry run** `/a/x` on the example: top layer `{'/a/y': '3'}` has no `/a/x` "
                 "and no whiteout of `/a` → continue. Middle `{'/a': None}`: no exact entry, ancestor `/a` is a whiteout → `None`.",
        complexity="Time O(Q x L x D) for Q queries, L layers and path depth D; space O(D).",
        pitfalls="- Ignoring directory whiteouts.\n- Prefix matching by string: a whiteout of `/app` must not hide `/application`.\n"
                 "- Checking ancestors before the exact path.\n- Iterating bottom-up and returning the first hit.",
        follow_up="Produce `docker diff` output (A, C, D) for the top layer relative to the layers below.",
    ),
),
dict(
    id="docker-multistage-stages",
    title="Which Build Stages Does a Target Need?",
    difficulty="Medium",
    pattern="Building Images",
    entry="stagesNeeded",
    description=r"""
BuildKit only builds the stages a target depends on. Write `stagesNeeded(stages, target)`.

`stages` lists the stages of a Dockerfile **in file order**. Each stage is `[name, base, copies]`:

- `name`: the stage's name (unique);
- `base`: what follows `FROM`;
- `copies`: the list of names used in `COPY --from=<name>` inside the stage (may contain duplicates).

A `base` or `copies` entry refers to a stage **only if a stage with that name appears earlier in the file**.
Otherwise it is an external image and is ignored.

`target` is a stage name, or `""` meaning the **last** stage. Return the names of every stage that must be built
(the target and everything it depends on, directly or indirectly) **in file order**. If `stages` is empty or the
target name does not exist, return `[]`.

**Example:** stages `[["base","python:3.12",[]], ["deps","base",[]], ["test","deps",[]], ["prod","base",["deps"]]]`,
target `""` → `["base", "deps", "prod"]`
""",
    starter='''def stagesNeeded(stages, target):
    pass
''',
    solution='''def stagesNeeded(stages, target):
    if not stages:
        return []
    index = {s[0]: i for i, s in enumerate(stages)}
    if target == "":
        target = stages[-1][0]
    if target not in index:
        return []
    needed = set()
    stack = [index[target]]
    while stack:
        i = stack.pop()
        if i in needed:
            continue
        needed.add(i)
        _, base, copies = stages[i]
        for ref in [base] + list(copies):
            j = index.get(ref)
            if j is not None and j < i:
                stack.append(j)
    return [stages[i][0] for i in sorted(needed)]
''',
    tests=[
        [[["base", "python:3.12", []], ["deps", "base", []], ["test", "deps", []], ["prod", "base", ["deps"]]], ""],
        [[["base", "python:3.12", []], ["deps", "base", []], ["test", "deps", []], ["prod", "base", ["deps"]]], "test"],
        [[], ""],
        [[["only", "alpine:3.20", []]], ""],
        [[["a", "alpine", []], ["b", "alpine", []]], "missing"],
        [[["build", "golang:1.23", []], ["final", "scratch", ["build", "build"]]], "final"],
        [[["a", "alpine", []], ["b", "a", []], ["c", "b", []], ["d", "c", []]], "c"],
        [[["a", "alpine", ["b"]], ["b", "alpine", []]], "a"],
        [[["nginx", "nginx:1.27", []], ["web", "node:22", ["nginx"]], ["x", "nginx", []]], "web"],
        [[["a", "alpine", []], ["b", "alpine", []], ["c", "alpine", ["a", "b"]], ["d", "alpine", ["c"]], ["e", "b", []]], "d"],
        [[["a", "alpine", []], ["b", "alpine", []], ["c", "alpine", ["a", "b"]], ["d", "alpine", ["c"]], ["e", "b", []]], "e"],
        [[["s%d" % i, ("s%d" % (i - 1)) if i else "alpine", []] for i in range(300)], ""],
        [[["a", "a", []]], "a"],
    ],
    examples=2,
    wrong_solutions=[
        '''def stagesNeeded(stages, target):
    if not stages:
        return []
    names = [s[0] for s in stages]
    if target == "":
        target = names[-1]
    if target not in names:
        return []
    return names[:names.index(target) + 1]
''',
        '''def stagesNeeded(stages, target):
    if not stages:
        return []
    index = {s[0]: i for i, s in enumerate(stages)}
    if target == "":
        target = stages[-1][0]
    if target not in index:
        return []
    needed, stack = set(), [index[target]]
    while stack:
        i = stack.pop()
        if i in needed:
            continue
        needed.add(i)
        base = stages[i][1]
        if base in index and index[base] < i:
            stack.append(index[base])
    return [stages[i][0] for i in sorted(needed)]
''',
    ],
    guide=dict(
        prereqs="Lesson *Multi-stage builds*. Graph traversal (depth-first search with a stack).",
        intuition="Stages form a graph: an edge from a stage to its `FROM` parent and to each `COPY --from` source. "
                  "The answer is everything reachable from the target, printed in the order the file lists it.",
        hints=[
            "Map each stage name to its index so you can test 'defined earlier' with `j < i`.",
            "Follow both kinds of edge: the base **and** every `copies` entry.",
            "Collect indices in a set during the search, then sort them to get file order.",
        ],
        brute_force="Return every stage up to and including the target. That is what the old builder did; it builds unrelated stages such as `test`.",
        approach="1. Resolve the target index (last stage if empty).\n2. Depth-first search with an explicit stack and a `needed` set.\n"
                 "3. For each reference of the current stage, push it if it names an earlier stage.\n4. Sort the indices.\n\n"
                 "**Dry run** (example, target `prod` at index 3): pop 3 → refs `base` (index 0), `deps` (index 1) pushed. Pop 1 → ref `base`. "
                 "Pop 0 → ref `python:3.12` is external. `needed = {0, 1, 3}` → `['base', 'deps', 'prod']`.",
        complexity="Time O(S + E) for S stages and E references, space O(S).",
        pitfalls="- Following only `FROM` and forgetting `COPY --from`.\n- Treating a name as a stage when the stage is defined **later** "
                 "(it is an external image then).\n- Returning search order instead of file order.\n- Recursion depth on a 300-stage chain: use a stack.",
        follow_up="Group the needed stages into waves that could be built in parallel.",
    ),
),
]
