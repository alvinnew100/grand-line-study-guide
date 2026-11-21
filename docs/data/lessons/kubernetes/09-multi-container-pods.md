# Multi-container Pods: init, sidecar and adapter

## In plain words

Most Pods contain one container. Sometimes the main program needs help that does not belong inside its own image: something to prepare the ground before it starts, something to work beside it while it runs, or something to translate its output for another system. Kubernetes lets you put those helpers in the same Pod, where they share the main container's network address and can share its files.

Think of a restaurant kitchen station again. The head cook is the main container. Before service begins, a prep cook chops the vegetables and leaves; the head cook cannot start until that is done. This is an **init container**. During service, a runner stands beside the cook the whole shift, carrying plates to the pass; that is a **sidecar**. And when the cook writes tickets in personal shorthand, an assistant rewrites them in the format the cashier's system understands: an **adapter**. Each helper has one job, and the cook's own work stays the same.

Why this matters for a job: these patterns are everywhere in real clusters. Service meshes inject proxy sidecars into your Pods, log and metrics agents run as sidecars, and database migrations or "wait for the dependency" checks run as init containers. You will read such Pod specs in your first week, and "what is a sidecar?" is a standard interview question.

> **Before this lesson:** read [The Pod as the atomic unit](#/lesson/kubernetes/pod-basics). You need to know that containers in a Pod share an IP address and can share volumes, but have separate filesystems.

## The principle: one job per container

A container image should do one thing. Imagine `web`, an nginx server for Harbour Coffee's static pages. The pages change several times a day in a Git repository. You could build a custom image containing nginx plus a script that pulls from Git in a loop, but then:

- the image mixes two concerns and two release schedules,
- a crash in the sync script may take nginx down with it,
- the sync logic cannot be reused with a different web server.

The alternative is two small containers in one Pod: unmodified nginx, and a separate content-sync container. They cooperate through a shared folder. Each can be updated, given resource limits and restarted independently. This idea is called **separation of concerns**.

The cost of an extra container is not zero. It needs its own CPU and memory reservation, it adds an image to pull, and it adds a part that can fail. Use a helper container when it buys reuse or isolation, not by reflex.

## The sharing mechanism: an emptyDir volume

Containers have separate filesystems, so cooperation through files needs a **volume**: a directory that Kubernetes provides to the Pod and that containers mount at a path of their choosing. The simplest kind is **`emptyDir`**. It starts empty when the Pod is created, lives on the node as long as the Pod exists, survives container restarts, and is deleted when the Pod is removed.

Two steps are always needed: declare the volume once at Pod level under `spec.volumes`, then mount it in each container that needs it under `volumeMounts`. The mount paths may differ between containers.

## Pattern 1: init containers

An **init container** runs before the application containers start. If there are several, they run **one at a time, in the order listed**, and each must exit successfully (exit code 0) before the next begins. Only when all have succeeded does the kubelet start the main containers. Init containers run to completion; they are not long-lived.

Typical uses:

- wait until a dependency (a database, another service) is reachable,
- run a database schema migration,
- download or generate configuration or data into a shared volume,
- perform a setup step needing tools or permissions that the main image should not have.

Here is a Pod for `orders-api` with two init containers:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: orders-api
  namespace: cafe
  labels:
    app: orders-api
spec:
  volumes:
    - name: runtime-config
      emptyDir: {}
  initContainers:
    - name: wait-for-db
      image: busybox:1.37
      command:
        - sh
        - -c
        - |
          until nc -z orders-db 5432; do
            echo "database not reachable yet, retrying in 2s"
            sleep 2
          done
    - name: render-config
      image: ghcr.io/harbour-coffee/config-tool:1.2.0
      args: ["render", "--out", "/work/app.toml"]
      volumeMounts:
        - name: runtime-config
          mountPath: /work
  containers:
    - name: orders-api
      image: ghcr.io/harbour-coffee/orders-api:2.0.3
      args: ["--config", "/etc/orders/app.toml"]
      ports:
        - name: http
          containerPort: 8080
      volumeMounts:
        - name: runtime-config
          mountPath: /etc/orders
          readOnly: true
```

Line by line, for the new parts:

- `volumes:` declares one volume named `runtime-config` of type `emptyDir`. `{}` is YAML for "an empty set of options", meaning defaults.
- `initContainers:` is a list with the same shape as `containers`.
- `wait-for-db` uses the small `busybox` image. Its `command` is `sh -c` followed by a script. The `|` character starts a multi-line text block. The script loops: `nc -z orders-db 5432` tries to open a TCP connection to the host `orders-db` on port 5432 and succeeds only if something is listening. `until ... do ... done` repeats until that succeeds. When the loop ends, the shell exits with code 0 and the init container counts as successful.
- `render-config` runs a tool that writes `/work/app.toml`. Because `/work` is the mounted volume, the file lands in the shared `emptyDir`.
- The main container mounts the same volume at a different path, `/etc/orders`, marked `readOnly: true`, and is told to read its configuration there.

Watching it start:

```bash
$ kubectl get pod orders-api -n cafe --watch
NAME         READY   STATUS            RESTARTS   AGE
orders-api   0/1     Init:0/2          0          2s
orders-api   0/1     Init:1/2          0          9s
orders-api   0/1     PodInitializing   0          11s
orders-api   1/1     Running           0          13s

$ kubectl logs orders-api -n cafe -c wait-for-db
database not reachable yet, retrying in 2s
database not reachable yet, retrying in 2s
```

`--watch` keeps printing a new line each time the Pod changes. `Init:0/2` means zero of two init containers have finished. `Init:1/2` means the first has finished and the second is running. `PodInitializing` means all init containers are done and the main containers are starting. `kubectl logs ... -c wait-for-db` shows the output of a named container, which works for init containers too.

If an init container fails, the kubelet restarts it, with increasing delays, as long as the Pod's `restartPolicy` is `Always` or `OnFailure`. The Pod then shows `Init:Error` or `Init:CrashLoopBackOff`, and the main container never starts.

> [!WARNING]
> Init containers may run more than once: after a Pod sandbox restart, the whole sequence is repeated. Write them to be idempotent, meaning safe to run again. A migration step must cope with "already applied", and a download step must cope with the file already existing.

## Pattern 2: sidecars

A **sidecar** runs alongside the main container for the whole life of the Pod and adds a supporting capability. Common sidecars:

- a proxy that encrypts and controls network traffic (service meshes such as Istio and Linkerd inject one),
- a log shipper that reads log files and forwards them,
- a process that keeps content or credentials fresh,
- a metrics exporter.

### The modern way to declare a sidecar

For years, a sidecar was an ordinary entry in `containers`. That had two flaws. Nothing guaranteed the sidecar started before the app, so the app's first requests could fail if it needed the proxy. And in a Job, the sidecar kept running after the main container finished, so the Pod never completed.

Kubernetes fixed this with **native sidecar containers**, stable since version 1.33. A native sidecar is declared in the `initContainers` list with `restartPolicy: Always` on that container. That one field changes its behaviour:

- it starts in its listed order among the init containers, **before** the main containers,
- unlike a normal init container, the kubelet does not wait for it to exit; it moves on once the sidecar has started (and passed its startup probe, if it has one),
- it keeps running and is restarted if it stops,
- at shutdown it is stopped **after** the main containers, in reverse order, so the app can still use it while finishing work,
- it does not block a Job's Pod from completing.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web
  namespace: cafe
  labels:
    app: web
spec:
  volumes:
    - name: site
      emptyDir: {}
  initContainers:
    - name: content-sync
      image: registry.k8s.io/git-sync/git-sync:v4.4.0
      restartPolicy: Always
      args:
        - --repo=https://github.com/harbour-coffee/site-content
        - --root=/git
        - --link=current
        - --period=60s
      volumeMounts:
        - name: site
          mountPath: /git
      resources:
        requests:
          cpu: 20m
          memory: 32Mi
  containers:
    - name: nginx
      image: nginx:1.29
      ports:
        - name: http
          containerPort: 80
      volumeMounts:
        - name: site
          mountPath: /usr/share/nginx/html
          subPath: current
          readOnly: true
```

- `content-sync` is in `initContainers` and has `restartPolicy: Always`: that combination makes it a sidecar. Its arguments tell the git-sync tool which repository to clone, where to put it, to maintain a link named `current` pointing at the newest checkout, and to check for changes every 60 seconds.
- `resources.requests` reserves a small amount of CPU and memory for the sidecar. Sidecar requests are added to the Pod's total, so set them deliberately.
- `nginx` mounts the same volume. `subPath: current` mounts only the `current` entry inside the volume, so nginx serves the latest checkout.

Check the result:

```bash
$ kubectl get pod web -n cafe
NAME   READY   STATUS    RESTARTS   AGE
web    2/2     Running   0          40s

$ kubectl logs web -n cafe -c content-sync --tail=1
{"level":"info","msg":"updated successfully","ref":"HEAD","commit":"9f2c1ab"}

$ kubectl exec web -n cafe -c nginx -- ls /usr/share/nginx/html
index.html  menu.html  styles.css
```

`READY 2/2` counts the sidecar and the main container. The `exec` into the nginx container lists files that the other container downloaded: proof that the shared volume works.

## Pattern 3: adapters

An **adapter** is a sidecar with a specific purpose: it converts the main container's output into the form another system expects, so the main application does not have to change. The classic case is monitoring. Suppose `menu-api` exposes its statistics as JSON at `/stats`, and the company's monitoring system, Prometheus, wants a particular plain-text format at `/metrics`. An adapter reads one and serves the other.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: menu-api
  namespace: cafe
  labels:
    app: menu-api
spec:
  initContainers:
    - name: metrics-adapter
      image: ghcr.io/harbour-coffee/json-to-prom:0.4.1
      restartPolicy: Always
      args: ["--source=http://localhost:8080/stats", "--listen=:9102"]
      ports:
        - name: metrics
          containerPort: 9102
  containers:
    - name: menu-api
      image: ghcr.io/harbour-coffee/menu-api:1.1.0
      ports:
        - name: http
          containerPort: 8080
```

The adapter reaches the application at `localhost:8080` because both containers share the Pod's network namespace. It listens on a different port, 9102, since they also share the port space. The monitoring system collects from port 9102 and never needs to know about the JSON format.

A close relative is the **ambassador**: a sidecar that represents an *outside* service to the main container. The app connects to `localhost:5432`, and the ambassador forwards that to the real database, adding encryption, authentication or connection pooling. The difference is direction. An adapter standardises what goes *out* of your app to observers. An ambassador simplifies how your app reaches *other* systems.

## Start-up and shutdown order, simulated

The ordering rules are easier to trust once you have seen them run. This model takes a Pod definition and prints the sequence the kubelet follows.

```python-run
def run_pod(name, init, main):
    """init: list of (name, kind, succeeds) where kind is 'init' or 'sidecar'."""
    print(f"\n=== {name} ===")
    running_sidecars = []
    for cname, kind, ok in init:
        if kind == "sidecar":
            running_sidecars.append(cname)
            print(f"start sidecar   {cname:15} (kubelet continues once it has started)")
        else:
            print(f"run init        {cname:15} ", end="")
            if ok:
                print("exit 0 -> next")
            else:
                print("exit 1 -> restarted with backoff; main containers never start")
                print(f"status: Init:CrashLoopBackOff, still running: {running_sidecars}")
                return
    for cname in main:
        print(f"start main      {cname}")
    print(f"status: Running, containers up: {running_sidecars + main}")
    print("--- Pod deleted ---")
    for cname in main:
        print(f"stop main       {cname}")
    for cname in reversed(running_sidecars):
        print(f"stop sidecar    {cname:15} (after main, in reverse order)")

run_pod("orders-api",
        init=[("mesh-proxy", "sidecar", True), ("wait-for-db", "init", True), ("migrate", "init", True)],
        main=["orders-api"])

run_pod("orders-api with a failing migration",
        init=[("mesh-proxy", "sidecar", True), ("wait-for-db", "init", True), ("migrate", "init", False)],
        main=["orders-api"])
```

In the first run, the proxy sidecar is listed first, so the later init containers can use the network through it; then two ordinary init containers run in order; then the app starts; and on deletion the app stops before the proxy. In the second run the migration fails, the app never starts, and the status shows an init failure. The position of a sidecar within the `initContainers` list matters: anything listed before it runs without it.

## How resources add up

The scheduler needs one number per resource for the whole Pod. With init containers and sidecars the rule is a little subtle. Ordinary init containers run one at a time and finish, so they do not add together; what counts is the largest of them. Sidecars and main containers run at the same time, so they do add together. Simplified, the Pod's effective request is the larger of:

- the biggest request of any single init container (plus any sidecars already started before it), and
- the sum of all sidecars and all main containers.

For the `orders-api` example with a 50m proxy sidecar, a 500m migration init container and a 250m main container, the two figures are 550m (migration running beside the proxy) and 300m (proxy plus app), so the scheduler reserves 550m. A heavyweight init container can make a Pod much harder to place than its steady-state use suggests.

## Seeing and debugging multi-container Pods

```bash
$ kubectl get pod web -n cafe -o jsonpath='{.spec.initContainers[*].name}{"\n"}{.spec.containers[*].name}{"\n"}'
content-sync
nginx

$ kubectl logs web -n cafe --all-containers --prefix --tail=1
[pod/web/content-sync] {"level":"info","msg":"updated successfully"}
[pod/web/nginx] 10.244.2.1 - - [21/Nov/2026:10:40:02 +0000] "GET / HTTP/1.1" 200 4521

$ kubectl describe pod web -n cafe | grep -A3 "^Init Containers" 
Init Containers:
  content-sync:
    Container ID:  containerd://5b8e...
    Image:         registry.k8s.io/git-sync/git-sync:v4.4.0
```

The first command prints container names from both lists. `--all-containers --prefix` shows logs from every container with a label saying which one wrote each line. `kubectl describe pod` has separate sections for init containers and containers, each with its own state, restart count and last exit code.

When a container image has no shell (common for small, secure images), `kubectl exec` has nothing to run. An **ephemeral container** solves that: a temporary debugging container added to a running Pod.

```bash
$ kubectl debug -it web -n cafe --image=busybox:1.37 --target=nginx
Targeting container "nginx".
/ # wget -qO- localhost:80 | head -1
<!doctype html>
```

`kubectl debug` adds a `busybox` container to the existing Pod. `--target=nginx` makes it share that container's process namespace so you can inspect its processes. It shares the Pod's network, so `localhost:80` reaches nginx. Ephemeral containers are never restarted and vanish with the Pod.

> [!TIP]
> If a Pod is stuck in `Init:N/M`, the Nth-plus-one init container is the one running or failing. Read its logs with `kubectl logs POD -c NAME`. The main container's logs will be empty, because it has not started.

> [!INTERVIEW]
> **"What is the difference between an init container and a sidecar?"** Init containers run before the application containers, one at a time, in order, and each must finish successfully; they are for setup such as waiting on dependencies, migrations or fetching configuration. A sidecar runs for the Pod's whole life beside the main container and provides an ongoing service such as proxying, log shipping or syncing. Since v1.33 the supported way to declare a sidecar is an entry in `initContainers` with `restartPolicy: Always`, which guarantees it starts before and stops after the main containers and does not prevent a Job from completing. Add the sharing model: same network namespace, so `localhost`; files only through shared volumes.

## Common pitfalls

- **Init container that never exits.** A server process placed in `initContainers` without `restartPolicy: Always` blocks the Pod at `Init:0/1` indefinitely.
- **Waiting on a dependency with no timeout.** A typo in the host name leaves the Pod initialising silently. Log each attempt, as the example does.
- **Non-idempotent init steps.** They will run again.
- **Forgetting the volume mount in one of the containers.** A volume declared at Pod level is not visible to a container until that container mounts it.
- **Port clashes.** A sidecar and the app share ports; give each its own.
- **No resource requests on sidecars.** Hundreds of Pods each with an unbudgeted proxy add up to real capacity.
- **Legacy sidecars in Jobs.** A sidecar in the `containers` list keeps a Job's Pod from finishing; use the native form.

## Cheat sheet

| Pattern | Declared in | Runs | Purpose |
|---|---|---|---|
| Init container | `initContainers` | Before main, sequentially, to completion | Setup, waiting, migrations |
| Sidecar (native) | `initContainers` with `restartPolicy: Always` | Starts before main, runs throughout, stops after | Proxy, log shipping, syncing |
| Adapter | As a sidecar | Throughout | Convert the app's output to a standard format |
| Ambassador | As a sidecar | Throughout | Proxy the app's connections to outside services |
| Ephemeral container | `kubectl debug` | Temporarily | Troubleshooting |

| Status | Meaning |
|---|---|
| `Init:1/3` | One of three init containers finished |
| `Init:Error` | An init container exited with an error |
| `Init:CrashLoopBackOff` | An init container keeps failing; waiting before retry |
| `PodInitializing` | Init done; main containers starting |
| `READY 2/2` | Both long-running containers ready |

## Summary

Multi-container Pods keep each container to a single job while letting tightly coupled helpers share a network address and chosen files. Init containers prepare the ground: they run in order, each to completion, before the application starts. Sidecars work beside the application for the Pod's whole life; the native form, an init container with `restartPolicy: Always`, gives them a guaranteed start-before and stop-after order. Adapters and ambassadors are sidecars that translate output or front outside services. Sharing happens through `localhost` and through volumes such as `emptyDir`. With the structure of a Pod understood, the next lesson follows a Pod through time: its phases, restarts, health checks and resource limits.

## Glossary

- **Init container**: a container that runs to completion before the app containers start.
- **Sidecar**: a helper container that runs alongside the main container for the Pod's lifetime.
- **Native sidecar**: a sidecar declared as an init container with `restartPolicy: Always`.
- **Adapter**: a sidecar that converts the app's output to a format others expect.
- **Ambassador**: a sidecar that proxies the app's connections to outside services.
- **Separation of concerns**: giving each component one responsibility.
- **Volume**: a directory provided to a Pod that containers can mount.
- **emptyDir**: a volume that starts empty and lasts as long as the Pod.
- **volumeMounts / mountPath**: where a container attaches a volume in its filesystem.
- **subPath**: mounting one entry inside a volume instead of the whole volume.
- **Ephemeral container**: a temporary container added to a running Pod for debugging.
- **Service mesh**: infrastructure that manages traffic between services, usually through proxy sidecars.
- **Idempotent**: safe to run more than once.

```quiz
[
  {"q": "A Pod has init containers A, B and C in that order. B exits with code 1. What happens next?",
   "options": ["C runs, then the main container starts", "The main container starts without B", "B is retried with backoff; C and the main containers do not start", "The Pod is deleted"],
   "answer": 2,
   "explain": "Init containers run strictly in sequence and each must succeed. A failing one is restarted (unless restartPolicy is Never) and blocks everything after it."},
  {"q": "How do you declare a native sidecar container?",
   "options": ["In containers with sidecar: true", "In initContainers with restartPolicy: Always", "In a separate Sidecar object", "With the annotation sidecar.kubernetes.io/enabled"],
   "answer": 1,
   "explain": "An init container with container-level restartPolicy: Always is treated as a sidecar: it starts before the main containers and keeps running."},
  {"q": "A Pod shows STATUS Init:0/1 for twenty minutes. The single init container runs a web proxy. Why is this Pod not running?",
   "options": ["The proxy image is too large", "A long-running process in a plain init container never exits, so the main containers never start", "Init containers cannot use the network", "The Pod needs more replicas"],
   "answer": 1,
   "explain": "A normal init container must run to completion. A server never completes. It should be declared as a sidecar with restartPolicy: Always."},
  {"q": "An nginx container and a content-sync container are in one Pod. The sync container downloads files to /data in its own filesystem with no volumes defined. Can nginx serve them?",
   "options": ["Yes, containers in a Pod share a filesystem", "No, each container has its own filesystem; a shared volume is needed", "Yes, through localhost", "Only if both use the same image"],
   "answer": 1,
   "explain": "Containers in a Pod share the network, not their root filesystems. An emptyDir mounted in both is the usual way to share files."},
  {"q": "With native sidecars, in what order are containers stopped when the Pod is deleted?",
   "options": ["Sidecars first, then main containers", "All at the same instant, always", "Main containers first, then sidecars in reverse order", "In alphabetical order"],
   "answer": 2,
   "explain": "Sidecars are kept alive until the main containers have stopped, so the app can still use them while shutting down, then terminated in reverse start order."},
  {"q": "An app exposes statistics as JSON, but the monitoring system needs another format. You add a container that converts one to the other. Which pattern is this?",
   "options": ["Init container", "Adapter", "Ambassador", "DaemonSet"],
   "answer": 1,
   "explain": "An adapter standardises the main container's output for outside consumers without changing the application."},
  {"q": "A Pod has one sidecar requesting 100m, one init container requesting 800m, and one main container requesting 300m. Roughly how much CPU must a node have free to schedule it, if the sidecar is listed first?",
   "options": ["300m", "400m", "900m", "1200m"],
   "answer": 2,
   "explain": "The init container runs while the sidecar is already up: 800m + 100m = 900m. Steady state is 100m + 300m = 400m. The scheduler uses the larger figure."},
  {"q": "A container image has no shell, so kubectl exec fails. What is the supported way to investigate the running Pod?",
   "options": ["Rebuild the image with a shell and redeploy", "Add an ephemeral container with kubectl debug", "Delete the Pod", "SSH to the control plane"],
   "answer": 1,
   "explain": "kubectl debug attaches a temporary container with tools to the existing Pod, sharing its network and optionally a target container's processes."}
]
```

> **Source:** Poulton, *The Kubernetes Book*, ch. 4 (topic coverage only). Official docs: https://kubernetes.io/docs/concepts/workloads/pods/init-containers/ , https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/ , https://kubernetes.io/docs/concepts/workloads/pods/ephemeral-containers/ , https://kubernetes.io/docs/concepts/storage/volumes/#emptydir
