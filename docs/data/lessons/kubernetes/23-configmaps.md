# ConfigMaps

## In plain words

Every program has settings: which database to connect to, how much to log, which features are switched on. Those settings differ between your laptop, the test environment and production, while the program itself should be identical in all three. If the settings are baked into the container image, you need a different image for each environment, and you can no longer say "the thing we tested is the thing we shipped".

A **ConfigMap** is a Kubernetes object that holds configuration as plain key and value pairs, separately from the image. At start-up, Kubernetes hands the values to your container, either as environment variables or as files in a directory. The same image runs everywhere; only the ConfigMap differs.

A good comparison is a chef and a recipe card. The chef (the image) has the same skills in every restaurant of the chain. Each branch pins its own card to the wall (the ConfigMap): today's specials, the local spice level, the opening hours. Move the chef to another branch and the cooking adapts, without retraining the chef.

Why this matters for a job: every real deployment uses ConfigMaps. Knowing the two ways of consuming them, and in particular which one picks up changes without a restart, saves hours of confusion. "How do you manage configuration in Kubernetes, and what happens when a ConfigMap changes?" is a standard interview question.

> **Before this lesson:** you need Pod specs and volumes from [The Pod as the atomic unit](#/lesson/kubernetes/pod-basics) and [Volumes, PersistentVolumes and PersistentVolumeClaims](#/lesson/kubernetes/volumes-pv-pvc), and Deployments and rollouts from [Rolling updates](#/lesson/kubernetes/rolling-updates-rollbacks). The Docker track's [application configuration patterns](#/lesson/docker/app-config-patterns) covers the principle on one machine.

## Why configuration lives outside the image

The practice has a name: **externalised configuration**, one of the widely quoted "twelve-factor app" principles. Its benefits:

- **One image for all environments.** What passed tests is byte-for-byte what runs in production.
- **Changes without rebuilding.** Raising a log level is a configuration change, not a new build.
- **Separation of responsibilities.** Developers own the image; operators may own environment values.
- **Reviewable settings.** A ConfigMap is a small YAML file that lives in Git and shows up in diffs.

What does *not* belong in a ConfigMap is anything sensitive: passwords, tokens, private keys. Those go in Secrets, the subject of the [next lesson](#/lesson/kubernetes/secrets). ConfigMaps are stored and displayed in plain text.

## A ConfigMap, line by line

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: orders-config
  namespace: cafe
data:
  LOG_LEVEL: info
  ORDERS_DB_HOST: orders-db
  ORDERS_DB_PORT: "5432"
  FEATURE_LOYALTY_POINTS: "true"
  app.toml: |
    [server]
    listen = ":8080"
    read_timeout_seconds = 15

    [pricing]
    currency = "GBP"
    tax_rate = 0.20
```

- `apiVersion: v1`, `kind: ConfigMap` — a core object, namespaced.
- `data` — a map from keys to **string** values. There is no `spec`.
- The first four entries are short settings. Notice the quotes around `"5432"` and `"true"`: without them YAML would read a number and a boolean, and the API requires strings, so the apply would fail.
- `app.toml: |` — a key whose value is a whole file. The `|` begins a block of literal text: every indented line below becomes part of the value, line breaks included. A ConfigMap can therefore carry complete configuration files, with the key acting as the file name.

A ConfigMap also has a `binaryData` field for non-text content, and a total size limit of 1 MiB, because it is stored in etcd. It is for configuration, not for data files.

### Creating ConfigMaps

Declaratively, apply the manifest above. Imperatively, `kubectl` can build one from values or files:

```bash
$ kubectl create configmap orders-config -n cafe \
    --from-literal=LOG_LEVEL=info \
    --from-literal=ORDERS_DB_HOST=orders-db \
    --from-file=app.toml=./config/app.toml

$ kubectl create configmap orders-config -n cafe --from-env-file=orders.env \
    --dry-run=client -o yaml > orders-config.yaml

$ kubectl get configmap orders-config -n cafe -o yaml
$ kubectl describe configmap orders-config -n cafe
```

`--from-literal` adds one key and value. `--from-file=KEY=PATH` adds a key whose value is the file's contents; without `KEY=`, the file name is the key. `--from-env-file` reads `KEY=value` lines from a file. The second command combines this with a client-side dry run to generate YAML for Git. `kubectl get cm` is the short form.

## Way 1: environment variables

### One variable at a time

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders-api
  namespace: cafe
spec:
  replicas: 2
  selector:
    matchLabels:
      app: orders-api
  template:
    metadata:
      labels:
        app: orders-api
    spec:
      containers:
        - name: orders-api
          image: ghcr.io/harbour-coffee/orders-api:2.1.0
          env:
            - name: LOG_LEVEL
              valueFrom:
                configMapKeyRef:
                  name: orders-config
                  key: LOG_LEVEL
            - name: DB_HOST
              valueFrom:
                configMapKeyRef:
                  name: orders-config
                  key: ORDERS_DB_HOST
            - name: PAYMENTS_URL
              valueFrom:
                configMapKeyRef:
                  name: shared-endpoints
                  key: payments
                  optional: true
```

- `env` is the list of environment variables for the container.
- `valueFrom.configMapKeyRef` says "take the value from this ConfigMap and this key". `name` is the ConfigMap; `key` is the entry.
- The variable name seen by the program (`DB_HOST`) can differ from the key (`ORDERS_DB_HOST`). That lets one ConfigMap serve programs with different naming conventions.
- `optional: true` means "start anyway if the ConfigMap or key is missing"; the variable is then not set.

### All keys at once

```yaml
          envFrom:
            - configMapRef:
                name: orders-config
            - prefix: SHARED_
              configMapRef:
                name: shared-endpoints
```

`envFrom` turns every key of a ConfigMap into an environment variable of the same name. The optional `prefix` is added in front of each name. A key that is not a valid variable name, such as `app.toml`, is skipped, and an event records the fact.

### Which value wins

A container can receive the same variable name from several places. The rules:

1. A variable in **`env`** overrides the same name from **`envFrom`**.
2. Among several `envFrom` sources, the **later** one in the list overrides earlier ones.
3. Within `env`, if a name is listed twice, the later entry wins.

`env` entries can also refer to variables defined earlier in the same list with the syntax `$(NAME)`, for example `value: "postgres://$(DB_HOST):$(DB_PORT)/orders"`.

### The limitation of environment variables

Environment variables are read **once, when the container starts**. A process's environment cannot be changed from outside afterwards. If you edit the ConfigMap, running Pods keep the old values until they are replaced. Nothing warns you; the Pods carry on with stale settings.

## Way 2: files in a volume

```yaml
    spec:
      volumes:
        - name: config
          configMap:
            name: orders-config
            items:
              - key: app.toml
                path: app.toml
            defaultMode: 0444
      containers:
        - name: orders-api
          image: ghcr.io/harbour-coffee/orders-api:2.1.0
          args: ["--config", "/etc/orders/app.toml"]
          volumeMounts:
            - name: config
              mountPath: /etc/orders
              readOnly: true
```

- A volume of type `configMap` projects the ConfigMap's entries as files: each key becomes a file name, each value the file's contents.
- `items` selects which keys to include and what to call the files. Without `items`, every key becomes a file.
- `defaultMode: 0444` sets the file permissions (read-only for everyone). The leading zero marks an octal number.
- The container mounts the volume at `/etc/orders`, so the program finds `/etc/orders/app.toml`.

```bash
$ kubectl exec -n cafe deploy/orders-api -- ls -la /etc/orders
total 0
drwxrwxrwx 3 root root  77 Nov 21 11:02 .
drwxr-xr-x 1 root root  20 Nov 21 11:02 ..
drwxr-xr-x 2 root root  22 Nov 21 11:02 ..2026_11_21_11_02_17.2041967314
lrwxrwxrwx 1 root root  32 Nov 21 11:02 ..data -> ..2026_11_21_11_02_17.2041967314
lrwxrwxrwx 1 root root  15 Nov 21 11:02 app.toml -> ..data/app.toml
```

The listing reveals how updates work. `app.toml` is a symbolic link to `..data/app.toml`, and `..data` is a link to a timestamped directory holding the real files. When the ConfigMap changes, the kubelet writes a new timestamped directory and switches the `..data` link in one step, so all files change together and a program never sees half an update.

### Files update; variables do not

This is the most important practical difference between the two ways.

| | Environment variables | Volume files |
|---|---|---|
| Set when | Container start | Container start, then refreshed |
| After the ConfigMap changes | Unchanged until the Pod is replaced | Updated automatically, typically within about a minute |
| Suited to | Small individual settings | Whole configuration files |
| Program must | Read the environment | Read the file, and re-read it to notice changes |

Two cautions about the automatic refresh. First, the file changing does not mean the **application** notices. Unless the program watches the file or re-reads it periodically, it keeps using what it loaded at start-up. Second, a volume mounted with **`subPath`** is copied in once and is **never updated**.

Mounting a ConfigMap volume at a directory **hides whatever the image had in that directory**. Mounting at `/etc/orders` is fine if the image has nothing important there. To place a single file into a directory that has other files, `subPath` is the usual technique, at the cost of losing automatic updates.

## Projection and precedence, simulated

The program below computes the environment and files a container would get, following the rules above. Change the sources and press Run.

```python-run
configmaps = {
    "orders-config": {"LOG_LEVEL": "info", "ORDERS_DB_HOST": "orders-db", "app.toml": "[server]\nlisten=':8080'"},
    "shared-endpoints": {"LOG_LEVEL": "warn", "payments": "http://payments.finance"},
}

def is_env_name(key):
    return key.replace("_", "").isalnum() and not key[0].isdigit()

def build_env(env_from, env):
    result, notes = {}, []
    for src in env_from:                                  # later sources override earlier ones
        cm = configmaps.get(src["name"])
        if cm is None:
            if src.get("optional"):
                notes.append(f"envFrom {src['name']}: missing but optional, skipped")
                continue
            return None, [f"CreateContainerConfigError: configmap \"{src['name']}\" not found"]
        for key, value in cm.items():
            name = src.get("prefix", "") + key
            if not is_env_name(name):
                notes.append(f"envFrom {src['name']}: key '{key}' is not a valid variable name, skipped")
                continue
            result[name] = value
    for e in env:                                         # env always overrides envFrom
        if "value" in e:
            result[e["name"]] = e["value"]
            continue
        cm = configmaps.get(e["from"])
        if cm is None or e["key"] not in cm:
            if e.get("optional"):
                notes.append(f"env {e['name']}: source missing but optional, not set")
                continue
            return None, [f"CreateContainerConfigError: key '{e['key']}' not found in configmap '{e['from']}'"]
        result[e["name"]] = cm[e["key"]]
    return result, notes

def show(title, env_from, env):
    result, notes = build_env(env_from, env)
    print(f"\n{title}")
    for n in notes:
        print("   note:", n)
    if result is not None:
        for k in sorted(result):
            print(f"   {k}={result[k]!r}")

show("A. envFrom two ConfigMaps, later one wins on LOG_LEVEL",
     [{"name": "orders-config"}, {"name": "shared-endpoints"}], [])
show("B. explicit env overrides envFrom",
     [{"name": "orders-config"}, {"name": "shared-endpoints"}],
     [{"name": "LOG_LEVEL", "value": "debug"}, {"name": "DB_HOST", "from": "orders-config", "key": "ORDERS_DB_HOST"}])
show("C. a required key is missing",
     [], [{"name": "TIMEOUT", "from": "orders-config", "key": "TIMEOUT_SECONDS"}])
show("D. the same, marked optional",
     [], [{"name": "TIMEOUT", "from": "orders-config", "key": "TIMEOUT_SECONDS", "optional": True}])
```

Scenario A shows the later `envFrom` source winning (`LOG_LEVEL` becomes `warn`) and `app.toml` being skipped. Scenario B shows `env` beating both. Scenario C is the failure you will meet most often.

## When a reference is wrong

```bash
$ kubectl get pods -n cafe -l app=orders-api
NAME                          READY   STATUS                       RESTARTS   AGE
orders-api-6f7b8d9c5d-2kx9q   0/1     CreateContainerConfigError   0          40s

$ kubectl describe pod orders-api-6f7b8d9c5d-2kx9q -n cafe | tail -2
  Warning  Failed  12s (x4 over 40s)  kubelet  Error: configmap "orders-confg" not found
```

A Pod that refers to a missing ConfigMap, or a missing key, by environment variable is scheduled and then stuck in `CreateContainerConfigError`: the kubelet cannot build the container's configuration. The event names the object it could not find; here a typo, `orders-confg`. When the missing ConfigMap is used as a **volume**, the Pod instead stays in `ContainerCreating` with a `FailedMount` event. In both cases the kubelet keeps retrying, so creating the ConfigMap fixes the Pod without further action. Remember that the ConfigMap must be in the **same namespace** as the Pod.

## Rolling out a configuration change

Since environment variables do not update, and many programs do not re-read files, the dependable way to apply a change is to replace the Pods. Three approaches, from simplest to most robust:

**1. Restart by hand.**

```bash
$ kubectl apply -f orders-config.yaml
$ kubectl rollout restart deployment/orders-api -n cafe
```

Simple, and easy to forget.

**2. A checksum annotation.** Put a hash of the configuration in the Pod template:

```yaml
  template:
    metadata:
      annotations:
        checksum/config: 3c1f9a7e2b…
```

When the configuration changes, your tooling recomputes the hash, the Pod template changes, and the Deployment performs a normal rolling update. Helm charts commonly do this with a template function.

**3. Immutable, versioned ConfigMaps.** Give each version of the configuration a new name, such as `orders-config-7f2k9m`, and reference that name in the Deployment. A change creates a new ConfigMap and changes the reference, which triggers a rollout. Old Pods keep reading the old ConfigMap until they are replaced, and a rollback of the Deployment points back at the old one, which still exists. Kustomize's `configMapGenerator` does this automatically by appending a content hash to the name.

The third approach pairs with a field that enforces it:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: orders-config-7f2k9m
  namespace: cafe
immutable: true
data:
  LOG_LEVEL: info
```

`immutable: true` forbids any later change to the data; the only way to change it is to delete and recreate the object. It prevents accidental edits and, on large clusters, reduces load on the API server because kubelets no longer need to watch the object for changes.

> [!WARNING]
> Editing a ConfigMap in place changes configuration for running Pods on a schedule you do not control. File-mounted values update in Pods one by one over a minute or so, while environment variables update only as Pods happen to restart. For a while your replicas run with different settings, there is no rollout to watch and no revision to roll back to. For anything that matters, version the ConfigMap and let a Deployment rollout carry the change.

## The downward API: configuration from the Pod itself

Sometimes a program needs to know facts about its own Pod: its name, namespace, node or resource limits. The **downward API** exposes those through the same two mechanisms.

```yaml
          env:
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
            - name: POD_NAMESPACE
              valueFrom:
                fieldRef:
                  fieldPath: metadata.namespace
            - name: MEMORY_LIMIT_MB
              valueFrom:
                resourceFieldRef:
                  resource: limits.memory
                  divisor: 1Mi
```

`fieldRef` reads a field of the Pod object. `resourceFieldRef` reads a container's request or limit, divided by `divisor` to choose the unit. A common use is telling a runtime how much memory it really has, so that it sizes its internal buffers to the container's limit and not to the node's memory.

> [!TIP]
> After a change, verify what a container really received instead of trusting the manifest: `kubectl exec POD -- env | sort` for variables, and `kubectl exec POD -- cat /path/to/file` for mounted files. It settles "did the config reach the Pod?" in one command.

> [!INTERVIEW]
> **"How does a Pod consume a ConfigMap, and what happens when the ConfigMap is updated?"** Two ways: as environment variables, individually with `env[].valueFrom.configMapKeyRef` or in bulk with `envFrom`, and as files through a `configMap` volume. Environment variables are fixed when the container starts, so an updated ConfigMap has no effect until the Pod is replaced. Volume-mounted files are refreshed by the kubelet, atomically through a symlink swap, usually within a minute, except for `subPath` mounts, which never update; the application must still re-read the file. In practice teams trigger a rollout on configuration changes with `kubectl rollout restart`, a checksum annotation in the Pod template, or hash-named immutable ConfigMaps as Kustomize generates. Mention that a missing ConfigMap yields `CreateContainerConfigError`, and that ConfigMaps are not for secrets.

## Common pitfalls

- **Unquoted numbers and booleans in `data`.** Values must be strings.
- **Expecting environment variables to change.** They never do in a running container.
- **`subPath` mounts and stale files.**
- **Mounting over a directory that held files from the image.** They disappear from view.
- **ConfigMap in a different namespace from the Pod.** It is not found.
- **Putting credentials in a ConfigMap.** Anyone who can read the namespace's ConfigMaps can read them.
- **Large files.** The limit is 1 MiB per ConfigMap.
- **Editing in place with no rollout.** Replicas drift apart and there is nothing to roll back.

## Cheat sheet

| Goal | How |
|---|---|
| One variable from one key | `env[].valueFrom.configMapKeyRef` |
| All keys as variables | `envFrom[].configMapRef` (optional `prefix`) |
| Keys as files | `volumes[].configMap` + `volumeMounts` |
| Only some keys as files | `configMap.items[]` with `key` and `path` |
| Tolerate a missing source | `optional: true` |
| Forbid changes | `immutable: true` |
| Pod facts as variables | `fieldRef`, `resourceFieldRef` |
| Apply a change | `kubectl rollout restart`, checksum annotation, or hash-named ConfigMap |

| Precedence | Rule |
|---|---|
| `env` vs `envFrom` | `env` wins |
| Several `envFrom` | Later wins |
| Missing required source (env) | `CreateContainerConfigError` |
| Missing required source (volume) | `ContainerCreating`, `FailedMount` |

## Summary

A ConfigMap stores non-sensitive configuration as string key and value pairs outside the image, so one image can run in every environment. Containers receive the values as environment variables, which are fixed at start, or as files in a volume, which the kubelet refreshes when the ConfigMap changes. Explicit `env` entries override `envFrom`, and later `envFrom` sources override earlier ones. Because variables never update and programs may not re-read files, configuration changes are best delivered as rollouts, ideally with immutable, versioned ConfigMaps that make rollback meaningful. A missing ConfigMap or key leaves the Pod in `CreateContainerConfigError`. ConfigMaps are plain text and unsuitable for credentials, which need the object covered next.

## Glossary

- **ConfigMap**: an object holding non-sensitive configuration as key and value strings.
- **Externalised configuration**: keeping settings outside the application image.
- **Environment variable**: a named value in a process's environment, fixed at start.
- **configMapKeyRef**: a reference from one variable to one ConfigMap key.
- **envFrom**: importing all keys of a ConfigMap or Secret as variables.
- **ConfigMap volume**: a volume presenting keys as files.
- **items**: the selection and naming of keys projected into a volume.
- **subPath**: mounting a single entry of a volume; not refreshed on change.
- **Immutable ConfigMap**: a ConfigMap whose data cannot be modified.
- **Checksum annotation**: a hash in the Pod template that changes when configuration changes, triggering a rollout.
- **Downward API**: exposing a Pod's own fields to its containers.
- **CreateContainerConfigError**: the state of a container whose configuration sources cannot be resolved.
- **Symbolic link**: a filesystem entry that points to another path.

```quiz
[
  {"q": "A Deployment reads LOG_LEVEL from a ConfigMap as an environment variable. You change the value in the ConfigMap and apply it. What do the running Pods see?",
   "options": ["The new value within a minute", "The old value, until the Pods are replaced", "An empty value", "They restart automatically"],
   "answer": 1,
   "explain": "Environment variables are set once at container start. A ConfigMap update does not reach running containers through the environment."},
  {"q": "The same ConfigMap is also mounted as a volume at /etc/app (no subPath). After the update, what happens to the files?",
   "options": ["They never change", "The kubelet updates them automatically after a short delay", "The Pod is restarted", "The volume is unmounted"],
   "answer": 1,
   "explain": "Volume-projected ConfigMaps are refreshed atomically by the kubelet. The application must still re-read the file to use the new content."},
  {"q": "A container has envFrom listing ConfigMap A (LOG_LEVEL=info) then ConfigMap B (LOG_LEVEL=warn), and an env entry LOG_LEVEL=debug. What value does the process see?",
   "options": ["info", "warn", "debug", "The Pod fails to start"],
   "answer": 2,
   "explain": "Explicit env entries override envFrom. Without the env entry, the later envFrom source, warn, would win."},
  {"q": "A Pod shows STATUS CreateContainerConfigError. Why is this Pod not running?",
   "options": ["The image cannot be pulled", "A referenced ConfigMap or Secret, or a key within it, does not exist in the Pod's namespace", "The node is out of memory", "The readiness probe failed"],
   "answer": 1,
   "explain": "The kubelet cannot assemble the container's environment. kubectl describe pod names the missing object or key. Creating it lets the Pod start."},
  {"q": "A ConfigMap value is mounted as a single file using subPath. The ConfigMap is updated. What happens to the file in the running container?",
   "options": ["It updates within a minute", "It is not updated", "It is deleted", "The container restarts"],
   "answer": 1,
   "explain": "subPath mounts are resolved once at container start and do not receive later updates."},
  {"q": "Why do tools such as Kustomize append a content hash to generated ConfigMap names?",
   "options": ["To encrypt the data", "So a configuration change produces a new name, which changes the Pod template and triggers a rollout that can be rolled back", "To make names shorter", "To bypass the 1 MiB limit"],
   "answer": 1,
   "explain": "A new name means the Deployment's template changes, so Pods are replaced in a controlled rollout, and the old ConfigMap still exists for rollback."},
  {"q": "A manifest contains data: {MAX_ITEMS: 50}. kubectl apply fails. Why?",
   "options": ["Keys must be lowercase", "ConfigMap values must be strings; the number needs quotes", "ConfigMaps cannot hold numbers at all, even quoted", "The key is too long"],
   "answer": 1,
   "explain": "YAML parses 50 as an integer, but data is a map of string to string. Writing \"50\" fixes it."},
  {"q": "Which item does NOT belong in a ConfigMap?",
   "options": ["A log level", "A feature flag", "A database password", "A service host name"],
   "answer": 2,
   "explain": "ConfigMaps are plain text and broadly readable. Credentials belong in Secrets with tighter access control."}
]
```

> **Source:** Poulton, *The Kubernetes Book*, ch. 11 (topic coverage only). Official docs: https://kubernetes.io/docs/concepts/configuration/configmap/ , https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/ , https://kubernetes.io/docs/concepts/workloads/pods/downward-api/
