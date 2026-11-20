# Shrinking images and debugging containers that will not start

## In plain words

The previous lesson covered questions you answer by explaining. This one covers the two questions you answer by *doing*: "this image is far too big, make it smaller" and "this container will not start, find out why". Interviewers love them because they cannot be answered from a memorised list. They show how you approach a problem.

A good car mechanic does not start by replacing parts at random. They listen to the engine, read the warning lights, and test the most likely cause first. A doctor does the same: symptoms, simple tests, then a diagnosis. Both follow a **method**, a fixed order of checks that works even for a problem they have never met.

This lesson gives you such a method for each of the two tasks. Every step is a command you already know from earlier in the track, arranged so that each one narrows down the cause.

Why this matters for a job: these are not only interview exercises. A container that will not start is the most common thing a colleague will ask you to look at, and the difference between ten minutes and two hours is whether you follow a method or guess.

> **Before this lesson:** read [Core interview questions with worked answers](#/lesson/docker/interview-core) first. The shrinking part reviews [Optimising images for size, speed and security](#/lesson/docker/optimising-images); the debugging part uses the commands from [Running, inspecting and stopping containers](#/lesson/docker/running-containers) and ideas from [Restart policies](#/lesson/docker/restart-policies) and [Container networking and DNS](#/lesson/docker/compose-networking).

## Part 1: "How would you shrink this image?"

### The answer in one breath

"First I would measure which layers are large with `docker image history`. Then, in order of usual payoff: a smaller base image, a multi-stage build so that build tools are left out, a `.dockerignore`, clean-up in the same instruction as the install, and only the dependencies production needs."

Saying "measure first" is what marks an experienced answer.

### Worked example

You are handed this Dockerfile for a small Node.js web application and told the image is 1.4 GB.

```dockerfile
FROM node:22
WORKDIR /app
COPY . .
RUN npm install
RUN npm run build
EXPOSE 3000
CMD npm start
```

**Step 1: measure.**

```bash
docker image history harbour/storefront:big --format 'table {{.Size}}\t{{.CreatedBy}}'
```

`docker image history` lists the image's layers, newest first, with the size each instruction added.

```text
SIZE      CREATED BY
0B        CMD ["/bin/sh" "-c" "npm start"]
0B        EXPOSE map[3000/tcp:{}]
38MB      RUN /bin/sh -c npm run build
412MB     RUN /bin/sh -c npm install
96MB      COPY . . # buildkit
0B        WORKDIR /app
1.1GB     (base image node:22)
```

Now you know where the bytes are, and can say so:

| Finding | Likely cause |
|---|---|
| 1.1 GB base | The full `node:22` image includes compilers and many system packages |
| 96 MB `COPY . .` | The project folder contains things that should not be copied: `.git`, a local `node_modules`, logs |
| 412 MB `npm install` | Development tools (test runners, bundlers) are installed and kept |
| `CMD npm start` in shell form | Not a size problem, but worth fixing while you are there |

**Step 2: apply the fixes.**

```text
# .dockerignore
node_modules
.git
dist
*.log
.env*
coverage
```

Each line names files or folders that must not be sent to the build.

```dockerfile
# syntax=docker/dockerfile:1
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS prod-deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

FROM node:22-alpine
ENV NODE_ENV=production
WORKDIR /app
COPY --from=prod-deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json ./
USER node
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

What changed, and why:

- `node:22-alpine` is a much smaller variant of the base image.
- The Dockerfile now has three **stages**, each beginning with `FROM`. The `build` stage installs everything and produces the built application in `dist/`.
- `npm ci` installs exactly the versions in the lock file, which is more repeatable than `npm install`.
- Copying `package.json` and the lock file *before* the rest means the install step is reused from the cache when only source files change.
- The `prod-deps` stage installs only what the running application needs: `--omit=dev` leaves out development tools.
- The final stage copies in the two results (`COPY --from=...`) and nothing else. The source code, the development tools and the build cache stay behind.
- `USER node` runs the application as an unprivileged account that the base image provides.
- `CMD ["node", "dist/server.js"]` in bracketed form starts the program directly, so that it receives stop signals.

**Step 3: measure again.**

```bash
docker image ls harbour/storefront
```

```text
REPOSITORY           TAG     SIZE
harbour/storefront   big     1.41GB
harbour/storefront   small   168MB
```

About one eighth of the size, with faster rebuilds and far fewer packages for a security scan to complain about.

### The shrinking checklist

```mermaid
flowchart TD
  A["Measure: docker image history"] --> B{"Is the base image most of the size?"}
  B -- yes --> C["Use slim, alpine or distroless"]
  B -- no --> D{"Are build tools or dev dependencies in the image?"}
  C --> D
  D -- yes --> E["Multi-stage build; production-only dependencies"]
  D -- no --> F{"Is a COPY layer unexpectedly large?"}
  E --> F
  F -- yes --> G["Add .dockerignore; copy only what is needed"]
  F -- no --> H{"Files created and deleted in different layers?"}
  G --> H
  H -- yes --> I["Install and clean up in one RUN"]
  H -- no --> J["Measure again and stop when the gain is small"]
  I --> J
```

| Technique | Typical saving | One-line reason |
|---|---|---|
| Smaller base image | Hundreds of MB | The full images carry compilers and tools |
| Multi-stage build | Hundreds of MB | Build tools never reach the final image |
| Production-only dependencies | Tens to hundreds of MB | Test and build tools are not needed at run time |
| `.dockerignore` | Tens of MB and up | Keeps `.git`, local dependencies and data out |
| Clean up in the same `RUN` | Tens of MB | A later delete only hides files |
| Fewer, lighter dependencies | Varies | Each package brings others with it |

## Part 2: "My container will not start. How do you debug it?"

### The answer in one breath

"I check the container's state and exit code with `docker ps -a`, read its logs, inspect its configuration, and if that is not enough I start the image with a shell in place of its normal command and look around. Then I check the surroundings: ports, mounts, network and resources."

### The method

```mermaid
flowchart TD
  S["Container is not running"] --> A["1. docker ps -a: state and exit code"]
  A --> B["2. docker logs: what did it say?"]
  B --> C{"Logs explain it?"}
  C -- yes --> F["Fix the cause, recreate"]
  C -- no --> D["3. docker inspect: command, env, mounts, OOMKilled, State.Error"]
  D --> E["4. Run the image with a shell and look around"]
  E --> G["5. Check surroundings: ports, volumes, network, memory"]
  G --> F
```

### Step 1: what state is it in?

```bash
docker ps -a --filter name=api --format 'table {{.Names}}\t{{.Status}}'
```

`docker ps -a` lists all containers, including stopped ones. The `--filter` keeps those whose name contains `api`.

```text
NAMES   STATUS
api     Exited (1) 12 seconds ago
```

The status already narrows things down:

| Status | Meaning | Where to look next |
|---|---|---|
| `Created` | It was created but never started | The error printed by `docker run`; `State.Error` |
| `Exited (0)` | The main process finished normally | Was the command meant to keep running? |
| `Exited (1)` or another small number | The application reported an error | The logs |
| `Exited (126)` | The command exists but cannot be executed | File permissions; wrong file type |
| `Exited (127)` | The command was not found | Typing mistake in the command; wrong image |
| `Exited (137)` | The process was killed | Memory limit; check `OOMKilled` |
| `Restarting` | It keeps failing and the restart policy keeps trying | The logs; `RestartCount` |
| `Up` but not working | It started; the problem is elsewhere | Health status, ports, the application itself |

### Step 2: what did it say?

```bash
docker logs --tail 30 api
```

`docker logs` prints what the container's main process wrote; `--tail 30` limits it to the last thirty lines. Logs remain available after a container exits, until it is removed.

```text
Traceback (most recent call last):
  File "/app/main.py", line 9, in <module>
    DB_URL = os.environ["DATABASE_URL"]
KeyError: 'DATABASE_URL'
```

In perhaps three cases out of four the answer is here. A required environment variable was not supplied.

> [!TIP]
> If the container was started with `--rm`, it is deleted the moment it exits and its logs go with it. Remove `--rm` while investigating.

### Step 3: what was it actually given?

When the logs are empty or unclear, check what the container was configured with. `docker inspect` prints everything Docker knows about it; `--format` picks out parts.

```bash
docker inspect api --format 'exit={{.State.ExitCode}} oom={{.State.OOMKilled}} error={{.State.Error}}'
docker inspect api --format 'entrypoint={{.Config.Entrypoint}} cmd={{.Config.Cmd}}'
docker inspect api --format '{{json .Config.Env}}'
docker inspect api --format '{{json .Mounts}}'
```

```text
exit=137 oom=true error=
entrypoint=[python] cmd=[main.py]
["PATH=/usr/local/bin:/usr/bin","LOG_LEVEL=info"]
[]
```

Four questions answered: how it ended (killed for exceeding its memory limit), what command ran, which environment variables it received, and what storage was attached. Comparing these with what you *intended* often reveals the mistake: a missing variable, a volume that was never mounted, a command overridden by accident.

### Step 4: look inside the image

A container that has exited cannot be entered with `docker exec`, which only works on running containers. So start a **new** container from the same image, replacing its normal start-up program with a shell:

```bash
docker run --rm -it --entrypoint sh harbour/quotes-api:1.5
```

- `-it` gives you an interactive terminal.
- `--entrypoint sh` runs a shell in place of the image's own entrypoint.
- `--rm` cleans up when you leave.

Now you can investigate from inside:

```text
/app $ ls -l
/app $ cat config/settings.toml
/app $ which python
/app $ python main.py
```

`ls -l` lists files with their owners and permissions; `cat` shows a file; `which` shows where a program is; and running the real command by hand shows the error directly. Typical discoveries: a file that was never copied into the image, a script without execute permission, a missing program.

Add the same options the real container has (`-e`, `-v`, `--network`) to reproduce its situation exactly.

**When the image has no shell.** Minimal images (distroless, `scratch`) contain no shell at all, so `--entrypoint sh` fails with "executable file not found". Options:

| Technique | Command | Notes |
|---|---|---|
| Copy files out | `docker cp api:/app/config ./inspect` | Works on stopped containers |
| Export the filesystem | `docker export api -o rootfs.tar` | The container's whole filesystem as an archive |
| Attach a toolbox to the running container's network | `docker run --rm -it --network container:api nicolaka/netshoot` | For network problems |
| Docker's debug command | `docker debug api` | Brings its own tools into any container or image (a Docker Desktop feature) |
| A debug variant of the image | Build a `debug` target with a shell from the same Dockerfile | Keep it out of production |

### Step 5: check the surroundings

If the image is fine, the problem is in how the container meets the outside world.

**Ports.**

```text
Error response from daemon: Bind for 0.0.0.0:8080 failed: port is already allocated
```

Another process or container already uses that host port. `docker ps --format '{{.Names}}\t{{.Ports}}'` shows which container; choose a different host port or stop the other one.

A subtler case: the container is `Up`, the port is published, and requests still fail. The usual cause is an application listening on `127.0.0.1` inside the container. It must listen on `0.0.0.0`.

**Mounts.** A bind mount replaces the folder in the image. If you mount an empty or wrong host folder over the application's folder, its files vanish. A mistyped host path given with `-v` is silently created as an empty folder. Check `.Mounts` in `docker inspect` and look at the host path.

**Permissions.** A container running as a non-root user cannot write to a folder owned by root:

```text
PermissionError: [Errno 13] Permission denied: '/data/cache'
```

Compare `docker exec api id` (who the process is) with the owner of the folder.

**Network and dependencies.**

```text
could not translate host name "db" to address: Name or service not known
```

The name could not be found: the two containers are not on the same user-defined network, or the name is misspelled. `connection refused`, by contrast, means the name was found and nothing was listening yet: the dependency is still starting, or the port is wrong.

**Resources.** Exit code 137 with `OOMKilled=true` means the memory limit was reached. Raise the limit or reduce the application's use; `docker stats` shows current usage.

**Platform.** `exec format error` means the image was built for a different processor architecture than the host's (see the lesson on multi-architecture images).

### Error messages and what they mean

| Message | Cause | Fix |
|---|---|---|
| `Unable to find image ... pull access denied` | Wrong image name or tag, or not logged in to the registry | Check the name; `docker login` |
| `executable file not found in $PATH` | The command does not exist in the image | Fix the command, or a `CMD` written with single quotes |
| `permission denied` when starting | The script is not marked executable | `chmod +x` before copying, or `COPY --chmod=0755` |
| `exec format error` | Wrong architecture, or a script without a first line naming its interpreter | Build for the right platform; add `#!/bin/sh` |
| `no such file or directory` for a script that exists | Windows line endings in the script, or a missing interpreter | Convert the line endings; check the first line |
| `port is already allocated` | The host port is in use | Use another port |
| `address already in use` inside the container | Two processes in the container want the same port | Check the application's configuration |
| `Name or service not known` | Not on a shared user-defined network | Put both on the same network |
| `connection refused` | Nothing is listening there yet | Wait and retry; check the port and the bind address |
| `no space left on device` | The host's disk is full | `docker system df`, then `docker system prune` |
| `OOMKilled` / exit 137 | Memory limit exceeded | Raise the limit or fix the leak |

The small function below encodes the first branches of this method. Reading it is a good way to fix the order of the checks in memory.

```python-run
def diagnose(c):
    """c: a few facts about a container. Returns the most useful next step."""
    code, status = c.get("exit_code"), c.get("status")
    if status == "created":
        return "Never started: read the error from docker run and State.Error (port in use? bad mount?)"
    if status == "restarting":
        return "Crash loop: read docker logs; check RestartCount and the exit code"
    if status == "running":
        if c.get("health") == "unhealthy":
            return "Running but unhealthy: read the health check output in docker inspect"
        return "Running: check published ports, the bind address (0.0.0.0) and the app's own logs"
    if code == 0:
        return "Exited normally: the main command finished. Is it meant to stay in the foreground?"
    if code == 127:
        return "Command not found: check CMD/ENTRYPOINT spelling and that the program is in the image"
    if code == 126:
        return "Not executable: fix file permissions or the script's first line"
    if code == 137:
        return "Killed for memory: raise the limit" if c.get("oom") else "Killed: docker kill or a stop timeout"
    if c.get("logs"):
        return "Application error: the logs name the cause -> " + c["logs"]
    return "No logs: run the image with --entrypoint sh and start the command by hand"

cases = [
    {"status": "exited", "exit_code": 1, "logs": "KeyError: 'DATABASE_URL'"},
    {"status": "exited", "exit_code": 137, "oom": True},
    {"status": "exited", "exit_code": 127},
    {"status": "exited", "exit_code": 0},
    {"status": "running", "health": "unhealthy"},
    {"status": "created"},
    {"status": "exited", "exit_code": 2, "logs": ""},
]
for c in cases:
    print(f"{c} \n   -> {diagnose(c)}\n")
```

### A complete worked example

**The report:** "I ran `docker compose up -d` and the `api` service is not there."

```bash
docker compose ps -a
```

`docker compose ps -a` lists the project's containers, including stopped ones.

```text
NAME             SERVICE   STATUS
tasklane-api-1   api       Restarting (1) 4 seconds ago
tasklane-db-1    db        Up 2 minutes (healthy)
```

Step 1 result: a crash loop with exit code 1, an application error. The database is healthy.

```bash
docker compose logs --tail 5 api
```

```text
api-1  | psycopg.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
```

Step 2 result: the application is trying to reach the database at `localhost`. Inside the `api` container, `localhost` is the `api` container itself, where no database runs.

```bash
docker compose exec db env | grep POSTGRES_DB
docker compose config | grep DATABASE_URL
```

`docker compose config` prints the Compose file after all substitutions, which shows the value the container really receives.

```text
      DATABASE_URL: postgresql://postgres:devonly@localhost:5432/tasklane
```

Step 3 result: the configuration confirms it. The fix is to use the service name: `postgresql://postgres:devonly@db:5432/tasklane`. Then:

```bash
docker compose up -d
docker compose ps
```

```text
NAME             SERVICE   STATUS
tasklane-api-1   api       Up 6 seconds (healthy)
tasklane-db-1    db        Up 3 minutes (healthy)
```

Three commands, each chosen by what the previous one showed. That narrative, told aloud, is exactly what an interviewer wants to hear.

> [!INTERVIEW]
> Narrate your reasoning as you go: "the exit code is 1, so the application itself reported an error, so I read the logs next". Interviewers score the method. A candidate who reaches the wrong conclusion by a sound method usually does better than one who guesses right.

> [!WARNING]
> Do not "fix" a container by changing things inside it with `docker exec`. The change disappears when the container is replaced, and nobody else knows it was made. Use `exec` to investigate, then fix the image, the Compose file or the configuration and start a fresh container.

## Pitfalls

- **Skipping the measurement** and applying size tricks at random.
- **Deleting files in a later layer** and expecting a smaller image.
- **Changing several things at once** while debugging, so you cannot tell which one helped.
- **Using `docker exec` on a container that has exited.** It needs a running container; use `logs`, `inspect`, `cp`, or a new container with a shell.
- **Running with `--rm` during an investigation,** which deletes the evidence.
- **Reading only the last line of the logs.** The first error is usually the real one; later lines are consequences.
- **Assuming the image is at fault** when the cause is a port, a mount, a network or a limit.
- **Forgetting that `localhost` in a container means that container.**
- **Blaming Docker for an application error.** Exit code 1 with a stack trace is your program talking.
- **Leaving a restart policy on while debugging.** The container restarts every few seconds; `docker update --restart no NAME` holds it still.

## Cheat sheet

| Question | Command |
|---|---|
| Which layers are big? | `docker image history IMAGE` |
| What state and exit code? | `docker ps -a` |
| What did it print? | `docker logs --tail 50 NAME` |
| Why did it stop? | `docker inspect NAME --format '{{.State.ExitCode}} {{.State.OOMKilled}} {{.State.Error}}'` |
| What command ran? | `docker inspect NAME --format '{{.Config.Entrypoint}} {{.Config.Cmd}}'` |
| What environment did it get? | `docker inspect NAME --format '{{json .Config.Env}}'` |
| What is mounted? | `docker inspect NAME --format '{{json .Mounts}}'` |
| Look inside the image | `docker run --rm -it --entrypoint sh IMAGE` |
| Look inside a running container | `docker exec -it NAME sh` |
| Copy files from a stopped container | `docker cp NAME:/path ./local` |
| What did it change on disk? | `docker diff NAME` |
| Who uses that port? | `docker ps --format '{{.Names}}\t{{.Ports}}'` |
| Can it resolve and reach a dependency? | `docker exec NAME getent hosts db` and `nc -zv db 5432` |
| What will Compose really apply? | `docker compose config` |
| Is the disk full? | `docker system df` |
| Stop a crash loop to investigate | `docker update --restart no NAME` |

## Summary

- For "make it smaller": measure with `docker image history`, then apply the fixes in order of payoff: base image, multi-stage build, production-only dependencies, `.dockerignore`, same-layer clean-up. Measure again.
- For "it will not start": follow a fixed order. State and exit code, logs, configuration, a shell inside the image, then the surroundings.
- Exit codes point the way: 1 is the application, 127 a missing command, 126 a permission problem, 137 a kill (check `OOMKilled`), 0 a command that finished.
- An exited container still has its logs and files; use them before removing it.
- Many "container" problems are about the container's surroundings: ports, mounts, permissions, networks, memory and architecture.
- In an interview, say your reasoning aloud. The method is what is being assessed.

## Glossary

| Term | Meaning |
|---|---|
| Method | A fixed order of checks used to find the cause of a problem |
| Exit code | The number a process returns when it ends; 0 means success |
| Crash loop | A container that fails, is restarted and fails again, repeatedly |
| Stack trace (traceback) | The error report a program prints showing where it failed |
| Entrypoint override | Starting an image with a different program, such as a shell, to investigate |
| Stage | One `FROM` section of a multi-stage Dockerfile |
| Development dependencies | Packages needed to build or test, not to run |
| Lock file | A file recording exact dependency versions |
| Bind address | The network address a server listens on; `0.0.0.0` means all interfaces |
| OOM | Out of memory: the process was killed for exceeding its memory limit |
| Line endings | The invisible characters that end each line of a text file; Windows and Linux differ |
| Toolbox container | A helper container full of diagnostic tools attached to another container |

## Check yourself

```quiz
[
  {"q": "You are asked to shrink an image. What should you do first?",
   "options": ["Switch to Alpine immediately", "Measure which layers are large with docker image history", "Merge all RUN instructions", "Delete the Dockerfile's comments"],
   "answer": 1,
   "explain": "Measurement tells you where the bytes are, so you apply the fix with the biggest payoff instead of guessing."},
  {"q": "A Node image installs all dependencies and ships them. Which change removes build and test tools from the final image?",
   "options": ["Adding EXPOSE", "A multi-stage build with a production-only install (npm ci --omit=dev) copied into the final stage", "Using ADD instead of COPY", "Running npm cache clean in a later RUN"],
   "answer": 1,
   "explain": "Only what is copied from earlier stages reaches the final image, so development tools stay behind."},
  {"q": "A container shows `Exited (127)`. What is the most likely cause?",
   "options": ["Out of memory", "The command to run was not found in the image", "The port is in use", "The application threw an exception"],
   "answer": 1,
   "explain": "127 is the shell's code for command not found: a misspelt command or a program missing from the image."},
  {"q": "A container has exited. Which command still works on it?",
   "options": ["docker exec -it NAME sh", "docker logs NAME", "docker attach NAME", "docker top NAME"],
   "answer": 1,
   "explain": "Logs, inspect and cp work on stopped containers. exec, attach and top need a running one."},
  {"q": "How do you look around inside an image whose container exits immediately?",
   "options": ["docker exec into it quickly", "Start a new container from the image with --entrypoint sh", "Delete and pull the image again", "Restart Docker"],
   "answer": 1,
   "explain": "Overriding the entrypoint with a shell keeps the container alive so you can inspect files and run the real command by hand."},
  {"q": "An API container logs `connection refused` to `localhost:5432`, and the database runs in another container. What is wrong?",
   "options": ["The database port must be published", "localhost inside the API container is the API container itself; use the database's service name", "The database image is corrupt", "The API needs --privileged"],
   "answer": 1,
   "explain": "Each container has its own loopback. Containers on a shared network reach each other by service or container name."},
  {"q": "`docker inspect` shows exit code 137 and OOMKilled true. What happened?",
   "options": ["The command was not found", "The container exceeded its memory limit and was killed", "It was stopped normally", "The image has the wrong architecture"],
   "answer": 1,
   "explain": "137 means killed by signal 9, and OOMKilled identifies the memory limit as the reason."},
  {"q": "Why should you avoid fixing a problem by editing files inside a running container?",
   "options": ["It is not possible", "The change is lost when the container is replaced and is not recorded anywhere; fix the image or configuration instead", "It slows the container", "It corrupts the image"],
   "answer": 1,
   "explain": "Containers are disposable. Lasting fixes belong in the Dockerfile, Compose file or configuration, where they are versioned."}
]
```

> **Source:** review module drawing on Stoneman, *Learn Docker in a Month of Lunches*, ch. 2-4 and ch. 17 (topic coverage). Checked against <https://docs.docker.com/reference/cli/docker/container/inspect/>, <https://docs.docker.com/reference/cli/docker/debug/> and <https://docs.docker.com/build/building/best-practices/>. All wording and examples are original.
