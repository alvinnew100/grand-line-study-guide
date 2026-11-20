# Dockerfile instructions, one by one

## In plain words

A cake recipe lists ingredients and steps in order: take this base, add that, bake. Anyone who follows it gets the same cake. A **Dockerfile** is a recipe for an **image** (the packed, read-only bundle a container is started from). It is a plain text file. Each line is an **instruction**: start from this existing image, copy these files in, run this command, start the application like this.

The command `docker build` reads the recipe from top to bottom and produces the image. Because the recipe is a small text file kept beside the source code, anyone on the team, and any build machine, can produce the same image.

Why this matters for a job: writing and reviewing Dockerfiles is everyday work for developers, and several pairs of instructions that look alike behave differently (`CMD` and `ENTRYPOINT`, `COPY` and `ADD`, `ARG` and `ENV`). Those pairs are favourite interview questions precisely because the difference only shows when the container runs.

> **Before this lesson:** you should know what images and containers are ([What a container is](#/lesson/docker/what-is-a-container)) and be able to run and inspect a container ([Running, inspecting and stopping containers](#/lesson/docker/running-containers)).

## Why this matters

A Dockerfile is the recipe for an image: a plain text file of instructions that the builder executes from top to bottom. It is short, it lives in version control next to the code, and it replaces the wiki page titled "How to set up a server for this app". Anyone who can run `docker build` gets the same image.

There are fewer than twenty instructions and you will use about ten regularly. The trouble is that several of them look interchangeable and are not: `CMD` versus `ENTRYPOINT`, `COPY` versus `ADD`, `ARG` versus `ENV`, shell form versus exec form. Interviewers love these pairs precisely because the differences only show up at run time. This lesson walks through each instruction with a small example and says exactly what it changes: the image's **filesystem**, the image's **metadata**, or only the **build**.

## A first Dockerfile

Our example is `pagecount`, a tiny Python web service that counts visits. The project directory looks like this:

```text
pagecount/
  Dockerfile
  requirements.txt
  src/
    server.py
    templates/index.html
```

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim

LABEL org.opencontainers.image.title="pagecount" \
      org.opencontainers.image.source="https://git.example/harbour/pagecount"

ENV PYTHONUNBUFFERED=1 \
    PAGECOUNT_PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./

RUN useradd --system --uid 10001 --no-create-home pagecount
USER 10001

EXPOSE 8000
CMD ["python", "server.py"]
```

Build and run it:

Line by line:

- `# syntax=docker/dockerfile:1` selects the current version of the Dockerfile language. Lines starting with `#` are otherwise comments.
- `FROM python:3.12-slim` starts from an existing image that already contains Python.
- `LABEL ...` attaches descriptive notes to the image. The backslash `\` at the end of a line means the instruction continues on the next line.
- `ENV ...` sets two environment variables (named values the program can read) for every container started from the image.
- `WORKDIR /app` creates the folder `/app` inside the image and makes it the current folder for the lines that follow.
- `COPY requirements.txt .` copies that one file from your project into the current folder of the image (the `.`).
- `RUN pip install ...` executes a command while building: here, installing the Python libraries listed in the file.
- `COPY src/ ./` copies the application's source code.
- `RUN useradd ...` creates an unprivileged user account, and `USER 10001` makes the container run as that account instead of the administrator.
- `EXPOSE 8000` records that the application listens on port 8000.
- `CMD ["python", "server.py"]` is the command a container runs when it starts.


```bash
docker build -t harbour/pagecount:0.1 .
```

```text
[+] Building 14.2s (11/11) FINISHED
 => [internal] load build definition from Dockerfile                0.0s
 => [internal] load metadata for docker.io/library/python:3.12-slim 0.9s
 => [internal] load .dockerignore                                   0.0s
 => [internal] load build context                                   0.0s
 => => transferring context: 4.31kB                                 0.0s
 => [1/6] FROM docker.io/library/python:3.12-slim@sha256:5f0a...    3.1s
 => [2/6] WORKDIR /app                                              0.1s
 => [3/6] COPY requirements.txt .                                   0.0s
 => [4/6] RUN pip install --no-cache-dir -r requirements.txt        8.7s
 => [5/6] COPY src/ ./                                              0.0s
 => [6/6] RUN useradd --system --uid 10001 --no-create-home page... 0.3s
 => exporting to image                                              0.6s
 => => naming to docker.io/harbour/pagecount:0.1                    0.0s
```

The numbered steps `[1/6]` to `[6/6]` are the instructions that produce filesystem content. `LABEL`, `ENV`, `USER`, `EXPOSE` and `CMD` do not appear as numbered steps: they only edit the image's configuration.

```bash
docker run -d -p 8000:8000 --name pc harbour/pagecount:0.1
curl -s localhost:8000
```

```text
You are visitor number 1
```

`docker build -t harbour/pagecount:0.1 .` built the image: `-t` names it and the final `.` says "use the current folder as the source of files". `docker run -d -p 8000:8000 --name pc ...` started a container from it in the background, connecting port 8000 on your machine to port 8000 in the container. `curl -s localhost:8000` fetched the page.

## What each instruction changes

| Instruction | Adds a filesystem layer | Changes image config | Notes |
|---|---|---|---|
| `FROM` | starts from the base's layers | inherits base config | First instruction of every stage |
| `RUN` | yes | no | Executes a command at build time |
| `COPY` | yes | no | Files from context or another stage |
| `ADD` | yes | no | `COPY` plus URL download and tar extraction |
| `WORKDIR` | yes if it creates the directory | yes | Sets the directory for later steps and at run time |
| `ENV` | no | yes | Present at build time and run time |
| `ARG` | no | no | Build time only |
| `LABEL` | no | yes | Key-value metadata |
| `EXPOSE` | no | yes | Documentation of listening ports |
| `USER` | no | yes | Default UID for later `RUN` and for the container |
| `VOLUME` | no | yes | Declares a mount point |
| `CMD` | no | yes | Default command or default arguments |
| `ENTRYPOINT` | no | yes | The executable that always runs |
| `HEALTHCHECK` | no | yes | Command the engine runs to test health |
| `STOPSIGNAL` | no | yes | Signal `docker stop` sends |
| `SHELL` | no | yes | Shell used by shell-form instructions |
| `ONBUILD` | no | yes | Trigger for images built FROM this one |

## FROM: choosing the starting point

```dockerfile
FROM python:3.12-slim
FROM python:3.12-slim@sha256:5f0a...      # pinned to exact content
FROM node:22-alpine AS build              # a named stage
FROM scratch                              # an empty filesystem
```

Every image begins from another image, or from the special empty image `scratch`. The base decides the C library, the package manager, the shell and most of the size. Variants you will meet for nearly every official image:

| Variant | Typical size | Contents | Use when |
|---|---|---|---|
| `python:3.12` | ~1 GB | Debian + compilers + headers | You need to compile native extensions |
| `python:3.12-slim` | ~130 MB | Minimal Debian + Python | Default choice for services |
| `python:3.12-alpine` | ~55 MB | Alpine (musl libc) + Python | Small, but wheels may need compiling |
| distroless | ~50 MB | Runtime only, no shell | Hardened production images |
| `scratch` | 0 | Nothing | Static binaries (Go, Rust) |

> [!WARNING]
> `FROM python` with no tag means `python:latest`, which changes without notice. A build that worked on Monday can break on Tuesday with no change in your repository. Always give at least a minor version; pin a digest when reproducibility matters.

## RUN: executing commands at build time

`RUN` starts a temporary container from the layers so far, runs the command, and saves the filesystem difference as a new layer.

```dockerfile
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*
```

Three habits are packed into that one instruction:

1. **Chain with `&&`** so a failing step fails the build.
2. **Install and clean up in the same `RUN`.** A cleanup in a *later* `RUN` creates a new layer that hides the files but leaves them in the earlier layer, so the image does not shrink.
3. **Keep `apt-get update` and `install` together.** If they are separate instructions, the `update` layer is cached and a later change to the package list installs from a stale index.

For longer scripts a here-document reads better than a chain of backslashes:

```dockerfile
RUN <<EOF
set -eux
apt-get update
apt-get install -y --no-install-recommends curl
rm -rf /var/lib/apt/lists/*
EOF
```

## Shell form and exec form

`RUN`, `CMD` and `ENTRYPOINT` each accept two syntaxes, and the choice matters most for the last two.

```dockerfile
CMD python server.py --port 8000          # shell form
CMD ["python", "server.py", "--port", "8000"]   # exec form (a JSON array)
```

| | Shell form | Exec form |
|---|---|---|
| What runs | `/bin/sh -c "python server.py --port 8000"` | `python` directly |
| PID 1 | The shell | Your program |
| Variable expansion (`$PORT`) | Yes, by the shell | No |
| Signals from `docker stop` | Go to the shell, which does not forward them | Go to your program |
| Needs a shell in the image | Yes | No |

With shell form the engine's `SIGTERM` reaches `/bin/sh`, your server never hears it, and the container is killed after the ten-second grace period. **Use exec form for `CMD` and `ENTRYPOINT`.** If you need a variable expanded, do it in a small entrypoint script that ends with `exec "$@"` so the script replaces itself with the real process.

> [!WARNING]
> Exec form is JSON. It needs double quotes. `CMD ['python', 'server.py']` is not valid JSON, so Docker silently treats the whole line as shell form and tries to run a program literally named `[python,`.

## CMD and ENTRYPOINT

These two decide what process starts. The rules:

- `ENTRYPOINT` is the executable. `CMD` supplies default arguments to it.
- If only `CMD` is set, it is the whole command.
- Arguments given after the image name in `docker run` **replace `CMD`**. They never replace `ENTRYPOINT` (only `--entrypoint` does).
- If `ENTRYPOINT` is in shell form, `CMD` and run-time arguments are ignored entirely.

| Dockerfile | `docker run img` | `docker run img --debug` |
|---|---|---|
| `CMD ["serve"]` | `serve` | `--debug` (replaces the command) |
| `ENTRYPOINT ["pagecount"]` | `pagecount` | `pagecount --debug` |
| `ENTRYPOINT ["pagecount"]` + `CMD ["serve"]` | `pagecount serve` | `pagecount --debug` |
| `ENTRYPOINT pagecount` (shell) + `CMD ["serve"]` | `/bin/sh -c pagecount` | `/bin/sh -c pagecount` |

The third row is the idiom for an image that behaves like a command-line tool: a fixed executable plus overridable default arguments.

```dockerfile
ENTRYPOINT ["python", "-m", "pagecount"]
CMD ["serve", "--port", "8000"]
```

```bash
docker run harbour/pagecount:0.2                     # python -m pagecount serve --port 8000
docker run harbour/pagecount:0.2 migrate             # python -m pagecount migrate
docker run --entrypoint sh -it harbour/pagecount:0.2 # a shell, for debugging
```

The decision the engine makes can be written as a tiny function. Run it and try the combinations from the table.

```python-run
def resolve(entrypoint, cmd, run_args):
    """entrypoint/cmd: list (exec form), str (shell form) or None. run_args: list."""
    if isinstance(entrypoint, str):                      # shell-form entrypoint wins outright
        return ["/bin/sh", "-c", entrypoint]
    tail = run_args if run_args else cmd
    if isinstance(tail, str):                            # shell-form CMD
        tail = ["/bin/sh", "-c", tail]
    return (entrypoint or []) + (tail or [])

cases = [
    (None, ["serve"], []),
    (None, ["serve"], ["--debug"]),
    (["pagecount"], ["serve"], []),
    (["pagecount"], ["serve"], ["migrate", "--dry-run"]),
    (["pagecount"], "serve --port $PORT", []),
    ("pagecount serve", ["ignored"], ["also-ignored"]),
]
for ep, cmd, args in cases:
    print(f"ENTRYPOINT={ep!r:22} CMD={cmd!r:24} args={args!r:26} -> {resolve(ep, cmd, args)}")
```

Only the last `CMD` and the last `ENTRYPOINT` in a Dockerfile take effect, and setting `ENTRYPOINT` in a child image resets an inherited `CMD` to empty.

> [!INTERVIEW]
> "CMD vs ENTRYPOINT?" ENTRYPOINT fixes the program; CMD provides defaults that `docker run` arguments replace. Use ENTRYPOINT when the image *is* a tool, CMD alone when you want the whole command to be easy to override, and both together for "fixed binary, default flags". Mention exec form and signal handling for extra credit.

## COPY and ADD

```dockerfile
COPY requirements.txt .
COPY src/ ./
COPY --chown=10001:10001 config/defaults.toml /etc/pagecount/
COPY --from=build /out/pagecount /usr/local/bin/pagecount
COPY --chmod=0755 scripts/entrypoint.sh /entrypoint.sh
```

`COPY` takes files from the build context (or, with `--from`, from another stage or image) and adds them to the image. Things people trip over:

- Sources are relative to the **context**, not to the Dockerfile and not to your shell's current directory. You cannot `COPY ../secrets.txt`.
- Copying a directory copies its **contents**, not the directory itself. `COPY src/ ./` puts `server.py` directly in the working directory.
- If the destination ends with `/` or there are several sources, the destination is treated as a directory.
- Files are owned by root unless you pass `--chown`. Doing `RUN chown -R` afterwards duplicates every file into another layer.

`ADD` does everything `COPY` does plus two extras: if the source is a URL it downloads it, and if the source is a local tar archive it unpacks it. Those extras are surprising more often than they are helpful.

| Situation | Use |
|---|---|
| Local files and directories | `COPY` |
| Files from another build stage | `COPY --from` |
| Unpacking a local `.tar.gz` into the image | `ADD` (the one clear use) |
| Downloading from a URL | `RUN curl ... && verify checksum`, or `ADD --checksum=sha256:... URL dest` |

## WORKDIR, ENV and ARG

`WORKDIR /app` creates the directory if needed and makes it the current directory for the following `RUN`, `COPY`, `CMD` and `ENTRYPOINT`. Prefer it to `RUN cd /app`, which only affects that single `RUN`.

`ENV` and `ARG` both define variables. They differ in lifetime.

```dockerfile
ARG PY_VERSION=3.12
FROM python:${PY_VERSION}-slim

ARG GIT_SHA=unknown
ENV PAGECOUNT_BUILD=${GIT_SHA} \
    PAGECOUNT_PORT=8000
```

```bash
docker build --build-arg GIT_SHA=$(git rev-parse --short HEAD) -t harbour/pagecount:0.2 .
docker run --rm harbour/pagecount:0.2 env | grep PAGECOUNT
```

```text
PAGECOUNT_BUILD=4f2c9d1
PAGECOUNT_PORT=8000
```

| | `ARG` | `ENV` |
|---|---|---|
| Set with | `--build-arg NAME=value` | Dockerfile, overridable with `docker run -e` |
| Visible during build | Yes, after its declaration | Yes |
| Visible in the running container | No | Yes |
| Stored in image | Value appears in `docker history` | Stored in config |
| Scope | Until the end of the current stage | Until the end of the stage, inherited by children |

An `ARG` declared before the first `FROM` is usable only in `FROM` lines; redeclare it (without a value) inside a stage to use it there.

> [!WARNING]
> Neither `ARG` nor `ENV` is safe for secrets. `--build-arg NPM_TOKEN=...` is recorded in the image history and anyone who can pull the image can read it. Use `RUN --mount=type=secret` instead (covered in the CI lesson).

## USER, EXPOSE, VOLUME, LABEL and the rest

**`USER`** sets the UID (and optionally GID) for subsequent `RUN` instructions and for the container's main process. Images run as root unless you say otherwise. Create a user and switch to it near the end, after the steps that need root. A numeric UID is preferable to a name because orchestrators can verify "not zero" without reading `/etc/passwd`.

**`EXPOSE 8000`** records that the app listens on 8000. It does not publish anything; only `-p` does. It feeds `docker run -P` and serves as documentation.

**`VOLUME /var/lib/pagecount`** marks a path as a mount point. If the user does not mount something there, Docker creates an *anonymous* volume at run time. Changes made to that path by later build steps are discarded, which surprises people; most teams leave `VOLUME` out and declare volumes at run time or in Compose.

**`LABEL`** attaches metadata. The `org.opencontainers.image.*` keys (`source`, `revision`, `version`, `licenses`) are understood by registries and scanners.

**`HEALTHCHECK`** tells the engine how to test the app:

```dockerfile
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/healthz').status==200 else 1)"]
```

**`STOPSIGNAL SIGINT`** changes what `docker stop` sends, for programs that shut down cleanly on a signal other than `SIGTERM`.

**`SHELL ["/bin/bash", "-o", "pipefail", "-c"]`** changes the shell for shell-form instructions, commonly to make a failing command in a pipeline fail the build.

**`ONBUILD`** registers an instruction that runs when another image is built `FROM` this one. It is rare and makes builds harder to follow.

## A second pass: the improved Dockerfile

```dockerfile
# syntax=docker/dockerfile:1
ARG PY_VERSION=3.12
FROM python:${PY_VERSION}-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN useradd --system --uid 10001 --no-create-home pagecount

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=10001:10001 src/ ./

ARG GIT_SHA=unknown
LABEL org.opencontainers.image.revision=${GIT_SHA}

USER 10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s \
  CMD ["python", "healthcheck.py"]
ENTRYPOINT ["python", "server.py"]
CMD ["--port", "8000"]
```

Check the result rather than trusting the file:

```bash
docker image inspect harbour/pagecount:0.2 \
  --format 'user={{.Config.User}} entrypoint={{.Config.Entrypoint}} cmd={{.Config.Cmd}} ports={{.Config.ExposedPorts}}'
```

```text
user=10001 entrypoint=[python server.py] cmd=[--port 8000] ports=map[8000/tcp:{}]
```

Notice the placement of `ARG GIT_SHA`: it is declared *after* the dependency install. An `ARG` whose value changes on every commit invalidates the cache for every instruction after its first use, so it belongs as late as possible. The next lesson explains why.

## Pitfalls

- **Shell-form `CMD`** makes the shell PID 1 and breaks graceful shutdown.
- **Single quotes in exec form** silently turn it into shell form.
- **`RUN cd dir`** does not persist to the next instruction; use `WORKDIR`.
- **Cleanup in a separate `RUN`** hides files without removing them from the image.
- **`COPY . .` as the first step** drags in everything and ruins caching; copy dependency manifests first.
- **`EXPOSE` mistaken for publishing.** It is metadata.
- **Secrets in `ARG`/`ENV`** are readable from the image.
- **`USER` set before `RUN apt-get install`** makes the install fail with permission denied; switch user after the root-only steps.
- **`ADD` with a URL** re-downloads unpredictably and bypasses checksum verification unless you add `--checksum`.

## Cheat sheet

| Goal | Instruction |
|---|---|
| Choose a base | `FROM image:tag` (pin a version) |
| Install packages | `RUN install && cleanup` in one instruction |
| Add local files | `COPY --chown=uid:gid src dest` |
| Set working directory | `WORKDIR /app` |
| Run-time configuration default | `ENV NAME=value` |
| Build-time parameter | `ARG NAME=default` + `--build-arg` |
| Drop root | `USER 10001` |
| Document a port | `EXPOSE 8000` |
| Fixed executable | `ENTRYPOINT ["prog"]` (exec form) |
| Default arguments | `CMD ["arg1", "arg2"]` (exec form) |
| Liveness test | `HEALTHCHECK CMD [...]` |
| Metadata | `LABEL org.opencontainers.image.source=...` |

## Summary

- A Dockerfile is executed top to bottom; `RUN`, `COPY` and `ADD` create filesystem layers, everything else edits image configuration or build state.
- Pin the base image. Prefer `-slim` or smaller unless you need build tools.
- Use exec form for `CMD` and `ENTRYPOINT` so your program is PID 1 and receives signals.
- `ENTRYPOINT` is the program, `CMD` is its default arguments; `docker run` arguments replace `CMD`.
- Prefer `COPY`; reserve `ADD` for unpacking local archives.
- `ARG` exists only during the build; `ENV` persists into the container. Neither hides secrets.
- Create a non-root user and switch to it with `USER` after the privileged steps.

## Glossary

| Term | Meaning |
|---|---|
| Dockerfile | A text file of instructions for building an image |
| Instruction | One line of a Dockerfile, such as `FROM` or `RUN` |
| Base image | The image named in `FROM`, on which yours is built |
| Build | Running `docker build` to turn a Dockerfile into an image |
| Tag (`-t`) | The name and version given to the image being built |
| Shell form / exec form | A command written as plain text and run by a shell / written as a JSON list and run directly |
| JSON | A text format for data; a JSON list looks like `["a", "b"]` |
| ENTRYPOINT / CMD | The fixed program of a container / its default arguments or default command |
| ARG / ENV | A variable available only during the build / a variable stored in the image and present at run time |
| Working directory | The folder commands run in, set by `WORKDIR` |
| UID | User ID: the number identifying a user account |
| Metadata | Information about the image, such as labels and the default command, as opposed to its files |

## Check yourself

```quiz
[
  {"q": "An image has `ENTRYPOINT [\"backup\"]` and `CMD [\"--full\"]`. What runs for `docker run img --incremental /data`?",
   "options": ["backup --full --incremental /data", "backup --incremental /data", "--incremental /data", "/bin/sh -c backup --incremental /data"],
   "answer": 1,
   "explain": "Run-time arguments replace CMD entirely and are appended to the exec-form ENTRYPOINT."},
  {"q": "Why is `CMD python app.py` (shell form) a problem for graceful shutdown?",
   "options": ["Shell form cannot find python", "PID 1 becomes /bin/sh, which does not forward SIGTERM to the Python process", "Shell form disables stdout", "It prevents environment variables from being read"],
   "answer": 1,
   "explain": "docker stop signals PID 1. In shell form that is the shell; the app is a child that never receives the signal and is SIGKILLed after the grace period."},
  {"q": "Which instruction's value is available to the process in a running container?",
   "options": ["ARG only", "ENV only", "Both ARG and ENV", "Neither"],
   "answer": 1,
   "explain": "ARG values exist only while building. ENV values are stored in the image configuration and set in every container started from it."},
  {"q": "What does `EXPOSE 5432` do?",
   "options": ["Publishes port 5432 on the host", "Opens the port in the host firewall", "Records in image metadata that the app listens on 5432; nothing is published", "Makes the app listen on 5432"],
   "answer": 2,
   "explain": "EXPOSE is documentation plus input for `docker run -P`. Publishing requires -p or -P at run time."},
  {"q": "A Dockerfile has `RUN apt-get install -y build-essential` followed later by `RUN apt-get purge -y build-essential`. Effect on image size?",
   "options": ["The image shrinks by the size of build-essential", "No reduction: the files remain in the earlier layer and are only hidden", "The build fails", "The image shrinks only after docker image prune"],
   "answer": 1,
   "explain": "Layers are immutable. The purge layer adds whiteouts. To really avoid the bytes, install and remove within one RUN, or use a multi-stage build."},
  {"q": "When is ADD clearly the right choice over COPY?",
   "options": ["Always, it is the newer instruction", "When copying a directory", "When you want a local tar archive unpacked into the image", "When copying from another stage"],
   "answer": 2,
   "explain": "ADD auto-extracts local tar archives. For plain files COPY is more predictable, and --from is a COPY feature."},
  {"q": "`CMD ['node', 'server.js']` is written with single quotes. What happens?",
   "options": ["It works exactly like double quotes", "The build fails with a JSON error", "It is not valid JSON, so it is treated as shell form and the container fails to start a command named like `[node,`", "Docker converts the quotes automatically"],
   "answer": 2,
   "explain": "Exec form must be a valid JSON array. Anything else is interpreted as a shell-form string passed to /bin/sh -c."},
  {"q": "Where should `USER 10001` normally appear?",
   "options": ["Immediately after FROM", "After the steps that require root, such as package installation, and before CMD", "It must be the last line", "Before FROM"],
   "answer": 1,
   "explain": "USER affects subsequent RUN instructions too. Install system packages as root first, then switch so the container's main process is unprivileged."}
]
```

> **Source:** Stoneman, *Learn Docker in a Month of Lunches*, ch. 3 (topic coverage). Syntax checked against <https://docs.docker.com/reference/dockerfile/> and <https://docs.docker.com/build/building/best-practices/>. All wording and examples are original.
