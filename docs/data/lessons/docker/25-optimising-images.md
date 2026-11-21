# Optimising images for size, speed and security

## In plain words

Packing for a trip, you could take every item you own in a removal van, to be safe. You would arrive late, pay more, and spend the holiday searching for your toothbrush. A good traveller takes one small bag with exactly what the trip needs.

A container image is a packed bag for your application. A careless image contains compilers, documentation, caches and leftover files the running program never touches. It still works. It is also slow to download, slow to start on a new machine, costly to store, and full of extra software in which security flaws can hide.

**Optimising** an image means making three things better at once: its **size** (fewer bytes), its **build speed** (less waiting after each change) and its **security** (less software that could be attacked). The happy fact of this lesson is that the same handful of habits improves all three.

Why this matters for a job: image size and build time are things a team feels every day, in pipeline minutes and deployment delays. "How would you make this image smaller?" is one of the most frequent hands-on interview questions, often asked with a real Dockerfile to improve.

> **Before this lesson:** this lesson pulls together [Dockerfile instructions, one by one](#/lesson/docker/dockerfile-instructions), [Layers, the build cache, the context and .dockerignore](#/lesson/docker/layers-cache-context), [Multi-stage builds](#/lesson/docker/multi-stage-builds) and [Container security](#/lesson/docker/container-security). Read those first.

## Measure before you change anything

You cannot improve what you have not measured. Three commands tell you where the bytes are.

```bash
docker image ls harbour/reportly
```

```text
REPOSITORY         TAG   IMAGE ID       SIZE
harbour/reportly   v1    3c1f9a7e2b10   1.24GB
```

`docker image ls` shows the total size of the image when unpacked on disk.

```bash
docker image history harbour/reportly:v1 --format 'table {{.Size}}\t{{.CreatedBy}}'
```

```text
SIZE      CREATED BY
0B        CMD ["python" "main.py"]
312MB     RUN /bin/sh -c pip install -r requirements.txt
88MB      COPY . . # buildkit
395MB     RUN /bin/sh -c apt-get update && apt-get install -y build-essential git curl
0B        WORKDIR /app
...       (base image python:3.12, about 1.02GB before these steps are counted separately)
```

`docker image history` lists the image's **layers** (the stacked sets of file changes that make up an image, one per filesystem-changing instruction), newest first, with the size each one added. Read it like a bank statement: the large numbers are where to look. Here an 88 MB `COPY . .` is suspicious for a small Python project, and a 395 MB package installation is probably build tooling.

For a file-by-file view, the open-source tool `dive` shows the contents of each layer and marks files that were added in one layer and deleted in a later one, which is wasted space:

```bash
docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock wagoodman/dive harbour/reportly:v1
```

## The starting point

Here is the Dockerfile behind that 1.24 GB image. It works. Every line has something to improve.

```dockerfile
FROM python:3.12
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential git curl
COPY . .
RUN pip install -r requirements.txt
CMD python main.py
```

We will fix it in six steps, measuring after each.

## Step 1: choose a smaller base image

The **base image** is the image named after `FROM`, on which yours is built. `python:3.12` is the full variant: a complete Debian system with compilers and development files, about 1 GB. The `slim` variant has only what Python needs to run.

```dockerfile
FROM python:3.12-slim
```

| Base | Approximate size |
|---|---|
| `python:3.12` | 1.02 GB |
| `python:3.12-slim` | 130 MB |
| `python:3.12-alpine` | 55 MB |

One word changed, and about 900 MB is gone. Why not go straight to `alpine`? Alpine Linux uses a different C library (musl instead of the more common glibc). Many Python packages publish ready-made builds only for glibc, so on Alpine the installer has to compile them from source, which is slow and can fail. For Python, `slim` is the dependable choice. For a Go or Rust program that is a single self-contained binary, Alpine, distroless or `scratch` are excellent.

## Step 2: stop copying what you do not need

`COPY . .` copies the whole **build context**, the folder you gave to `docker build`. That 88 MB layer contains the `.git` history, a local virtual environment, test data and cached files.

Create a `.dockerignore` file beside the Dockerfile. It lists what must never be sent to the builder:

```text
.git
.venv
__pycache__/
**/*.pyc
tests/
docs/
data/
*.log
.env*
Dockerfile
.dockerignore
```

Each line is a pattern for files or folders to leave out. `**/*.pyc` means "files ending in `.pyc` at any depth".

The layer drops from 88 MB to about 400 kB. The build also starts faster, because less is transferred, and secrets in `.env` can no longer leak into the image.

## Step 3: order instructions so the cache works

Docker reuses the stored result of an instruction when nothing it depends on has changed; this is the **build cache**. Once one instruction has to run again, every instruction after it runs again too.

In the starting Dockerfile, `COPY . .` comes before `pip install`. Any change to any source file invalidates the copy, and therefore reinstalls every dependency: a 60-second wait for a one-character fix.

Copy the list of dependencies first, install, and copy the source last:

```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

Now an edit to the source reruns only the final `COPY`. The rule to remember: **things that change rarely go near the top; things that change often go near the bottom.**

```mermaid
flowchart TD
  A["FROM python 3.12-slim - changes monthly"] --> B["COPY requirements.txt - changes weekly"]
  B --> C["RUN pip install - reruns only when requirements change"]
  C --> D["COPY source - changes every commit"]
  D --> E["CMD - metadata"]
```

## Step 4: clean up in the same instruction

Every `RUN` creates a layer, and layers are permanent. Deleting a file in a *later* instruction hides it but does not remove its bytes from the earlier layer. So anything temporary must be removed in the **same** `RUN` that created it.

```dockerfile
# wasteful: the package lists stay in the first layer for ever
RUN apt-get update
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*

# better: one layer, with nothing left behind
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*
```

- `&&` runs the next command only if the previous one succeeded.
- `--no-install-recommends` tells the package manager to skip optional extras, often a large saving.
- `rm -rf /var/lib/apt/lists/*` deletes the downloaded package index, which is useless once installation is finished.

For Python, `pip install --no-cache-dir` stops pip keeping a copy of every downloaded package inside the layer.

The small model below shows why the split version is larger. It adds up layer sizes the way an image does.

```python-run
def image_size(layers):
    """Each layer is a list of (path, megabytes) changes; negative megabytes mean a delete."""
    total, files = 0, {}
    for i, layer in enumerate(layers, 1):
        added = sum(mb for _, mb in layer if mb > 0)       # deletes add (almost) nothing and remove nothing
        total += added
        for path, mb in layer:
            if mb > 0:
                files[path] = mb
            else:
                files.pop(path, None)
        print(f"  layer {i}: +{added:4d} MB")
    return total, sum(files.values())

split = [[("apt lists", 45)], [("build tools", 350)], [("app", 2)], [("apt lists", -45), ("build tools", -350)]]
single = [[("app", 2)]]          # install, build and clean up inside one RUN: nothing is left to store
for name, layers in [("four separate instructions", split), ("one combined instruction", single)]:
    print(name)
    stored, visible = image_size(layers)
    print(f"  stored in the image: {stored} MB, visible to the container: {visible} MB\n")
```

Both images *show* the container 2 MB of files. The first *ships* 397 MB, because the deleted files are still in its earlier layers.

## Step 5: keep build tools out with a multi-stage build

Some Python packages must be compiled during installation, which needs `build-essential` (a compiler and its companions). They are needed only while building, never while running. A **multi-stage build** uses one stage with the tools to do the work and a second, clean stage that receives only the result.

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim AS build
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

FROM python:3.12-slim
RUN useradd --system --uid 10001 --no-create-home app
COPY --from=build /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY --chown=10001:10001 . .
USER 10001
CMD ["python", "main.py"]
```

What each new part does:

- `FROM ... AS build` starts a stage named `build` that contains the compiler.
- `python -m venv /opt/venv` creates a **virtual environment**: a self-contained folder holding the installed Python packages. Having everything in one folder makes it easy to copy.
- `RUN --mount=type=cache,target=/root/.cache/pip` gives pip a download cache that persists between builds but is **not** stored in the image. It speeds up rebuilds without adding bytes.
- The second `FROM` starts the final stage from a clean base. `COPY --from=build /opt/venv /opt/venv` brings over only the installed packages. The compiler stays behind.
- `USER 10001` runs the app as an unprivileged user (from the security lesson).
- `CMD ["python", "main.py"]` uses the bracketed *exec form*, so the application receives stop signals directly.

## Step 6: remove what the application does not use

The last savings come from the dependency list itself.

- Split development dependencies (test tools, linters) into a separate file that the production image never installs.
- Check for heavyweight packages pulled in for one small function.
- Prefer the smaller variant when a library offers one, such as `opencv-python-headless`, or the CPU-only build of a machine-learning library when no graphics card is used.

## The results

| Version | Size | Rebuild after a source edit |
|---|---|---|
| Starting Dockerfile | 1.24 GB | about 75 s |
| + slim base | 520 MB | about 75 s |
| + `.dockerignore` | 430 MB | about 70 s |
| + dependency layer first | 430 MB | about 2 s |
| + clean-up and `--no-cache-dir` | 380 MB | about 2 s |
| + multi-stage, no build tools | 205 MB | about 2 s |
| + trimmed dependencies | 160 MB | about 2 s |

The image is about one eighth of its original size and rebuilds in two seconds. A vulnerability scan would also list far fewer findings, because roughly 400 packages that the application never used are gone.

## Why smaller is also safer and faster

| Habit | Size | Build speed | Security |
|---|---|---|---|
| Smaller base image | Much smaller | Faster pulls | Fewer packages to patch |
| `.dockerignore` | Smaller | Faster context transfer, fewer cache misses | No accidental secrets |
| Dependencies before source | Same | Much faster rebuilds | |
| Clean up in the same `RUN` | Smaller | | No leftover files |
| Multi-stage build | Much smaller | Stages can build in parallel | No compilers or tools for an intruder |
| Pinned versions | | Reproducible, stable cache | Known, reviewable contents |
| Non-root user | | | Limits damage |
| Cache mounts | Same | Faster dependency installs | |

Smaller images also mean shared layers are a larger fraction of each image, so pushes and pulls move less data: only the layers that changed travel.

## Layer count: a note on an old piece of advice

Older guides say to merge as many instructions as possible to reduce the number of layers. That mattered years ago. Today a few extra layers cost nothing measurable, and separate layers give better caching. Combine instructions when they belong together logically (install and clean up), not as a goal in itself. In particular, do not merge "install dependencies" with "copy source": that sacrifices the cache for no gain.

> [!WARNING]
> Do not optimise away the ability to diagnose problems. A distroless image has no shell, so `docker exec ... sh` will not work. That is a good trade for production, provided the team knows the alternatives (covered in the final lesson) before the first incident.

> [!INTERVIEW]
> "How would you shrink this image?" Measure with `docker image history`; switch to a slim or minimal base; add a `.dockerignore`; use a multi-stage build so build tools do not ship; clean up package caches in the same `RUN`; install only production dependencies. Then add the speed and security angle: order layers for the cache, pin versions, run as non-root. Naming the measurement step first is what separates a good answer from a list.

> [!TIP]
> Set a size budget in the pipeline, for example "fail if the image exceeds 250 MB". Sizes creep upward one dependency at a time, and a budget makes the creep visible when it happens instead of a year later.

## Golden images: one approved base for the whole organisation

Everything so far has been one team improving one Dockerfile. In a company with fifty services, fifty teams each choose a base image. One picks `python:3.12`, another `python:3.12-slim`, a third an image a stranger published under a convincing name. Each adds its own fixes for the same problems: the company's internal certificates, the time zone, a non-root user. When a serious flaw is announced in a system library, nobody can say quickly which services are affected, let alone patch them all.

The usual answer is a **golden image**: a base image that the organisation builds, approves and maintains itself, and that every application image must start from. Think of a restaurant chain's central kitchen. Each branch cooks its own dishes, but the stocks and sauces all come from one kitchen whose recipes are checked and whose ingredients are traced. If a supplier recalls a batch, the chain knows exactly which branches to call.

### Built on an official image, not from scratch

Anyone can push an image to Docker Hub, so the name alone proves nothing; an attacker can publish malware under an innocent-sounding name. Two kinds of image carry more trust. **Official images** (such as `python`, `nginx` and `postgres`) are curated by Docker together with the upstream project, follow published Dockerfile practices, are scanned and are rebuilt regularly; their Dockerfiles are public. **Verified publisher** images come from companies whose identity Docker has checked.

A golden image does not replace that work, it builds on it. It starts `FROM` an official image and adds only what the organisation needs everywhere:

```dockerfile
# syntax=docker/dockerfile:1
# golden/python/Dockerfile, owned by the platform team
FROM python:3.12-slim

LABEL org.opencontainers.image.vendor="Harbourline" \
      org.opencontainers.image.source="https://git.harbourline.example/platform/golden-images"

# Apply the latest security fixes and add the few packages every service needs
RUN apt-get update \
 && apt-get upgrade -y \
 && apt-get install -y --no-install-recommends ca-certificates tzdata \
 && rm -rf /var/lib/apt/lists/*

# Trust the company's internal certificate authority
COPY harbourline-root-ca.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates

# Shared defaults: internal package mirror, a standard unprivileged user
ENV PIP_INDEX_URL=https://pypi.internal.harbourline.example/simple \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=UTC
RUN useradd --uid 10001 --create-home app
```

- `FROM python:3.12-slim` keeps the official image's careful setup and its regular updates.
- `LABEL` records who owns the image and where its source lives, which scanners and people can read later.
- `apt-get upgrade` pulls in operating-system fixes released since the official image was last built.
- The CA certificate lets every service call internal HTTPS endpoints without each team repeating the same steps.
- The image creates the standard user but leaves the final `USER` line to each application, which may still need root for its own installs before switching.

It is published to the company's registry, for example as `registry.harbourline.example/base/python:3.12-slim`, and an application Dockerfile simply starts there:

```dockerfile
FROM registry.harbourline.example/base/python:3.12-slim AS base
# ... the multi-stage build from earlier in this lesson, unchanged ...
USER 10001
```

Golden images usually come in pairs that match multi-stage builds: a build image with compilers and SDKs, and a lean runtime image for the final stage.

### Kept patched

A golden image is only valuable if it stays current. A neglected one is worse than the official image it wraps, because it freezes old flaws into every service. The platform team that owns it typically:

- **Rebuilds on a schedule,** nightly or weekly, and whenever the official image changes, so new fixes flow in automatically.
- **Scans each rebuild before publishing,** acting as a quality gate: if a new version introduces a critical vulnerability or a forbidden software licence, it is not released.
- **Tags in two ways,** a moving tag such as `3.12-slim` that always points at the latest approved build, and a dated, never-reused tag such as `3.12-slim-2026.11.21` for teams that need to pin.
- **Triggers downstream rebuilds,** so application pipelines rebuild and redeploy on the new base without waiting for a code change.

Owning the base also lets you choose the update pace. Some organisations release feature changes to golden images only quarterly for stability, while still pushing security fixes immediately. Holding back security patches for a quarterly cycle defeats the point.

### Enforced in builds

A rule that "everyone should use the golden images" fades within months unless something checks it. Enforcement normally sits in three places:

- **In the pipeline:** a check reads each Dockerfile and fails the build if a `FROM` line names an image outside the approved registry path. The linter `hadolint` has a rule for exactly this (DL3026, configured with a list of trusted registries), and some scanners, Docker Scout among them, offer a ready-made approved-base-images policy.
- **At the registry:** the build network can only pull through the company registry, so unapproved images are simply unreachable.
- **At deployment:** a cluster can refuse to run images that do not come from the approved registry.

The check is less trivial than searching for `FROM`, because multi-stage builds also say `FROM base AS test`, where `base` is an earlier stage and not an image at all. This demo handles that:

```python-run
APPROVED_PREFIXES = ("registry.harbourline.example/base/",)
ALWAYS_ALLOWED = {"scratch"}      # the empty image has no contents to approve

def check_bases(dockerfile):
    stages, problems = set(), []
    for number, line in enumerate(dockerfile.splitlines(), start=1):
        words = line.split()
        if not words or words[0].upper() != "FROM":
            continue
        args = [w for w in words[1:] if not w.startswith("--")]   # skip --platform=...
        image = args[0]
        if image.lower() in stages:
            verdict = "ok (earlier stage)"
        elif image in ALWAYS_ALLOWED or image.startswith(APPROVED_PREFIXES):
            verdict = "ok (approved)"
        else:
            verdict = "NOT APPROVED"
            problems.append(number)
        if len(args) >= 3 and args[1].upper() == "AS":
            stages.add(args[2].lower())
        print(f"  line {number}: {image:55s} {verdict}")
    return problems

good = """FROM registry.harbourline.example/base/python-build:3.12 AS build
RUN pip wheel -r requirements.txt -w /wheels
FROM build AS test
RUN pytest
FROM registry.harbourline.example/base/python:3.12-slim
COPY --from=build /wheels /wheels"""

bad = """FROM python:3.12 AS build
FROM --platform=linux/amd64 someuser/python-fast:latest"""

for name, text in [("good", good), ("bad", bad)]:
    print(name)
    failed = check_bases(text)
    print("  ->", "build fails at lines " + str(failed) if failed else "build may continue")
```

A real check would also handle base images chosen through build arguments (`FROM ${BASE}`), for example by refusing them or resolving the argument first.

> [!INTERVIEW]
> "How do you keep base images secure across many teams?" Golden images: the platform team builds approved bases on official images, adds shared certificates, users and defaults, rebuilds and scans them on a schedule, publishes them to the internal registry with moving and dated tags, and triggers application rebuilds. Pipelines, the registry and the cluster all reject images that do not start from them.

## Pitfalls

- **Deleting files in a later layer** and expecting the image to shrink.
- **`COPY . .` before installing dependencies,** which reinstalls everything on each change.
- **No `.dockerignore`.**
- **Choosing Alpine for Python by reflex** and then fighting compile errors.
- **`apt-get update` in its own instruction.** The cached, stale package list is reused for later installs.
- **Using `--no-cache-dir` together with a cache mount.** They work against each other; with a cache mount, let pip use its cache.
- **Copying the virtual environment to a different path.** Paths inside it are fixed; keep the same location in both stages.
- **Unpinned `FROM` tags,** which make builds change without warning.
- **Squashing all layers into one.** Layer sharing between images and versions is lost, so every pull downloads everything.
- **Optimising a base image nobody else uses.** A slightly larger base that all your services share is downloaded once per machine.
- **A golden image nobody rebuilds.** An approved base that is months old spreads the same unpatched flaws into every service built on it.

## Cheat sheet

| Goal | Technique |
|---|---|
| Find the big layers | `docker image history IMAGE` or `dive` |
| Smaller base | `-slim`, distroless, Alpine or `scratch` as the language allows |
| Smaller context | `.dockerignore` |
| Fast rebuilds | Copy dependency lists, install, then copy source |
| No leftovers | Install and clean up in one `RUN`; `--no-install-recommends`; `--no-cache-dir` |
| No build tools shipped | Multi-stage build with `COPY --from` |
| Faster dependency installs | `RUN --mount=type=cache,target=...` |
| Reproducible builds | Pin base image tags (and digests) and dependency versions |
| Safer | `USER` non-root, minimal base, regular rebuilds and scans |
| Guard against growth | Size check in the pipeline |

## Summary

- Measure first: `docker image history` shows which instruction added which bytes.
- The largest single saving is usually the base image; the next is keeping build tools out with a multi-stage build.
- A `.dockerignore` shrinks the context, the image and the risk of leaking files.
- Order instructions from rarely changing to frequently changing so that the cache absorbs most rebuilds.
- Temporary files must be removed in the instruction that created them; later deletes only hide them.
- The same habits reduce size, speed up builds and shrink the attack surface, so optimisation is rarely a trade-off between them.
- Across an organisation, golden images give every team one approved base built on an official image, rebuilt and scanned on a schedule, and enforced by checks in the pipeline, the registry and the cluster.

## Glossary

| Term | Meaning |
|---|---|
| Optimise | Improve a chosen quality, here size, build speed and security |
| Base image | The image named in `FROM`, on which yours is built |
| Layer | The set of file changes produced by one instruction; layers stack to form the image |
| Build cache | Stored results of earlier build steps that are reused when inputs are unchanged |
| Build context | The folder whose files are available to the build |
| `.dockerignore` | A file listing patterns to exclude from the build context |
| Slim / Alpine / distroless / scratch | Progressively smaller kinds of base image |
| glibc / musl | Two implementations of the C library that programs depend on |
| Multi-stage build | A Dockerfile with several stages where only the last one is shipped |
| Virtual environment | A self-contained folder of installed Python packages |
| Cache mount | A build-time folder that persists between builds without being stored in the image |
| Attack surface | Everything in the image an attacker could try to use |
| Squash | Merging all layers of an image into one |
| Official image | A Docker Hub image curated by Docker with the upstream project, scanned and rebuilt regularly |
| Verified publisher | A company whose identity Docker has checked, publishing its own images |
| Golden image | An organisation-approved base image, built on an official image and maintained by a platform team |
| Platform team | The team that owns shared infrastructure such as golden images and pipelines |
| Quality gate | An automatic check a build must pass before it is released |

## Check yourself

```quiz
[
  {"q": "Which command shows how much each instruction added to an image?",
   "options": ["docker ps", "docker image history IMAGE", "docker logs IMAGE", "docker stats"],
   "answer": 1,
   "explain": "history lists the layers with their sizes and the instruction that created each, which is where optimisation starts."},
  {"q": "What is usually the largest single saving when shrinking a Python image built FROM python:3.12?",
   "options": ["Merging RUN instructions", "Switching to python:3.12-slim", "Deleting comments from the Dockerfile", "Using ADD instead of COPY"],
   "answer": 1,
   "explain": "The full base image is about 1 GB, mostly build tooling. The slim variant is around 130 MB."},
  {"q": "A Dockerfile has `RUN apt-get install -y gcc` and, three lines later, `RUN apt-get purge -y gcc`. How does the image size change because of the purge?",
   "options": ["It shrinks by the size of gcc", "It does not shrink; the earlier layer still contains gcc", "It doubles", "The build fails"],
   "answer": 1,
   "explain": "Layers are permanent. A later delete only hides files. Remove them in the same RUN or use a multi-stage build."},
  {"q": "Why copy requirements.txt and install before copying the rest of the source?",
   "options": ["pip requires it", "So that source edits do not invalidate the cached dependency layer", "It makes the image smaller", "COPY can only copy one file"],
   "answer": 1,
   "explain": "The cache is invalidated from the first changed instruction onward. Keeping the slow install above the frequently changing source avoids repeating it."},
  {"q": "What does a multi-stage build remove from the final image?",
   "options": ["The application code", "Compilers and other build-only tools, which stay in the earlier stage", "The base image", "Environment variables"],
   "answer": 1,
   "explain": "Only what is explicitly copied from the build stage reaches the final stage, so the toolchain is left behind."},
  {"q": "Why can python:3.12-alpine be a poor choice for a Python service?",
   "options": ["Alpine cannot run Python", "Many packages ship prebuilt only for glibc, so on Alpine's musl they must be compiled, which is slow and may fail", "Alpine images are larger", "Alpine has no package manager"],
   "answer": 1,
   "explain": "The different C library means prebuilt packages often do not apply. slim avoids the problem at a modest size cost."},
  {"q": "What does `RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt` do?",
   "options": ["Stores pip's cache inside the image", "Keeps pip's download cache between builds without adding it to the image", "Disables the layer cache", "Installs packages at run time"],
   "answer": 1,
   "explain": "A cache mount is managed by the builder and exists only during that instruction, so rebuilds are faster and the image is no larger."},
  {"q": "How does a smaller image improve security?",
   "options": ["Small files cannot contain flaws", "It contains fewer packages that can have vulnerabilities and fewer tools an intruder could use", "It is encrypted", "Scanners skip small images"],
   "answer": 1,
   "explain": "Less software means a smaller attack surface and shorter vulnerability reports."},
  {"q": "What is a golden image?",
   "options": ["The official image with the most downloads", "An organisation-approved base image, built on an official image with shared setup added, that application images must start from", "An image signed by Docker", "The final stage of a multi-stage build"],
   "answer": 1,
   "explain": "A platform team builds it FROM an official image, adds certificates, users and defaults, keeps it patched and publishes it to the internal registry."},
  {"q": "A pipeline check for golden images sees `FROM build AS test`. Why should it not fail the build?",
   "options": ["Lines with AS are never checked", "`build` is the name of an earlier stage in the same Dockerfile, not an image pulled from a registry", "Test stages are exempt from policy", "Docker ignores FROM lines in test stages"],
   "answer": 1,
   "explain": "Multi-stage builds reuse earlier stages by name. Only real image references must come from the approved registry."}
]
```

> **Source:** Stoneman, *Learn Docker in a Month of Lunches*, ch. 5 and ch. 17 (topic coverage). Checked against <https://docs.docker.com/build/building/best-practices/>, <https://docs.docker.com/build/cache/optimize/> <https://docs.docker.com/build/building/multi-stage/>, <https://docs.docker.com/trusted-content/official-images/> and <https://github.com/hadolint/hadolint/wiki/DL3026>. All wording and examples are original.
