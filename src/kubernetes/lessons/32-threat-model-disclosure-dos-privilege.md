# Threat modelling II: disclosure, denial of service and privilege

## In plain words

The previous lesson worked through the first three letters of STRIDE: pretending to be someone else, changing things, and acting without leaving a record. This lesson finishes the model with the last three:

- **Information disclosure**: an attacker *reads* what they should not. Passwords, customer data, the layout of your systems.
- **Denial of service**: an attacker, or an accident, *stops the system working* for legitimate users.
- **Elevation of privilege**: an attacker starts with a little access and *turns it into a lot*. In Kubernetes the classic form is getting out of a container and onto the node, called a **container escape**.

Stay with the bank from last time. Disclosure is someone photographing the customer files. Denial of service is a crowd blocking the entrance so real customers cannot get in, or one customer occupying every teller with pointless requests. Elevation of privilege is the visitor who is allowed into the lobby finding an unlocked staff door and walking through to the vault. A well-run bank assumes each of these will be attempted and makes each one hard.

The lesson ends with the **Pod Security Standards**, the built-in mechanism that turns the most important container-hardening settings into rules a namespace can enforce.

Why this matters for a job: the settings here are what security reviews check first, and they are where real clusters are most often weak. "What is a privileged container and why is it dangerous?" and "how do you stop one tenant affecting another?" are common interview questions.

> **Before this lesson:** read [Threat modelling I](#/lesson/kubernetes/threat-model-identity-integrity) for STRIDE and security contexts. You also need [Secrets](#/lesson/kubernetes/secrets), [requests and limits](#/lesson/kubernetes/pod-lifecycle-resources), [ResourceQuotas and LimitRanges](#/lesson/kubernetes/namespace-quotas) and [RBAC and admission](#/lesson/kubernetes/rbac-admission).

## Information disclosure

What is worth reading in a cluster, and how is each protected?

| Asset | How it leaks | Defence |
|---|---|---|
| Secrets in etcd | Direct access to etcd or its backups | Encryption at rest with a KMS, isolated etcd, encrypted backups |
| Secrets through the API | Broad `get`/`list` on secrets; Pod-creation rights | Least-privilege RBAC, one namespace per trust boundary |
| Secrets in Git | Committed manifests | Sealed or externally managed secrets |
| Secrets in a container | Environment dumps, logs, a compromised process | File mounts, minimal keys, short-lived credentials |
| Data in transit | Sniffing Pod-to-Pod traffic | TLS, service mesh mTLS |
| Cloud credentials | The node's metadata service | Workload identity, block metadata access |
| Cluster layout | Open dashboards, anonymous API access, verbose errors | Authentication everywhere, no public control plane |

The [Secrets lesson](#/lesson/kubernetes/secrets) covered the first four rows. Three further points deserve attention.

### The cloud metadata service

Every cloud virtual machine can call a special local address, `169.254.169.254`, to learn about itself and to obtain **credentials for the machine's cloud identity**. Pods run on those machines, so unless something prevents it, any Pod can make the same call and receive the node's cloud credentials. If the node's role can read storage buckets or pull every image, so can an attacker who compromises one small container. This single path has featured in several well-known breaches.

Defences, in order of preference: use **workload identity** so that Pods get their own narrow cloud credentials and nodes need very few permissions; enable the provider's metadata protection (for example, requiring a session token and limiting the network hop count, or the provider's metadata concealment feature); and block the address with a NetworkPolicy for Pods that do not need it:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-cloud-metadata
  namespace: cafe
spec:
  podSelector: {}
  policyTypes: ["Egress"]
  egress:
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 169.254.169.254/32
```

- `podSelector: {}` — an empty selector means every Pod in the namespace.
- `policyTypes: ["Egress"]` — the policy governs outgoing traffic.
- The single egress rule allows traffic to all addresses (`0.0.0.0/0`) **except** the metadata address. `/32` means exactly one address.

The [NetworkPolicy lesson](#/lesson/kubernetes/network-policies-auditing) explains this object in full.

### What a Pod can see of the host

Certain Pod settings open windows onto the node, and each is a disclosure risk:

| Setting | Exposes |
|---|---|
| `hostNetwork: true` | The node's network interfaces; the Pod can listen on node ports and see traffic to local services |
| `hostPID: true` | Every process on the node, including their command lines and environment |
| `hostIPC: true` | The node's inter-process communication, including shared memory |
| `hostPath` volumes | Files on the node: logs, kubelet credentials, the container runtime's socket |

A `hostPath` mount of the container runtime's socket deserves special mention: a process that can talk to that socket can start any container with any settings, which is full control of the node.

### Exposure to the internet

A surprising number of incidents begin with something reachable that should not be: an API server with anonymous access, a dashboard with no login, etcd on a public address, the kubelet's port open to the world. Keep the control plane on a private network or restrict it to known address ranges, require authentication on every management interface, and check from outside what is visible.

## Denial of service

Denial of service attacks **availability**. In a cluster the cause is as often a mistake as an attacker, and the defences are the same.

### Exhausting a node

A container with no limits can consume all the CPU and memory of its node, starving every neighbour. A container that forks processes endlessly (a "fork bomb") can exhaust the node's process IDs. A container that fills the disk with logs or temporary files triggers disk pressure and evictions.

| Resource | Defence |
|---|---|
| CPU and memory | Requests and limits on every container; LimitRange defaults |
| Process IDs | The kubelet's per-Pod PID limit (`podPidsLimit`) |
| Local disk | `ephemeral-storage` requests and limits; `sizeLimit` on `emptyDir` |
| Too many Pods | ResourceQuota on `pods`; the per-node Pod maximum |

```yaml
resources:
  requests:
    cpu: 250m
    memory: 256Mi
    ephemeral-storage: 1Gi
  limits:
    memory: 256Mi
    ephemeral-storage: 2Gi
```

`ephemeral-storage` covers what a container writes to its own filesystem, to `emptyDir` volumes and to its logs. A Pod exceeding its limit is evicted, instead of filling the node's disk for everyone.

### Exhausting a namespace or the cluster

One team's runaway autoscaler or mistyped `replicas: 5000` can consume all capacity. **ResourceQuotas** per namespace, from the [quotas lesson](#/lesson/kubernetes/namespace-quotas), put a ceiling on each tenant.

### Overloading the control plane

The API server and etcd can be overwhelmed by a client listing every object in a loop, by a controller in a crash loop creating thousands of objects, or by very large objects. Defences:

- **API Priority and Fairness** queues requests by importance and by who is asking, so that system components keep working when one client misbehaves. It is on by default.
- **Object count quotas** (`count/secrets`, `count/configmaps`, and so on) stop etcd being filled.
- **Highly available control plane**: three or more API servers and etcd members across zones.
- **Do not expose the API server to the whole internet** if you can avoid it.

### Killing the application

The simplest denial of service is removing your Pods. Defences are the availability features from across this track:

- several replicas, never one;
- spread across nodes and zones with topology spread constraints or anti-affinity;
- **PodDisruptionBudgets** so that maintenance cannot remove too many at once;
- sensible probes, so that failing Pods are replaced and overloaded Pods are not restarted needlessly;
- autoscaling for load spikes;
- **PriorityClasses**, so that when capacity is short the scheduler keeps critical workloads and evicts less important ones first.

### Network floods

Traffic floods from the internet are absorbed, where possible, before they reach the cluster: by the cloud provider's DDoS protection, a content delivery network or a web application firewall in front of the ingress. Inside the cluster, rate limiting at the gateway and NetworkPolicies that stop Pods contacting services they have no business with both limit what a compromised Pod can flood.

A small model shows why limits matter. Three Pods share a node; one misbehaves.

```python-run
def simulate(node_memory_mi, pods):
    """pods: list of (name, request, limit or None, usage). Applies limits, then node pressure."""
    print(f"node memory: {node_memory_mi}Mi")
    running = []
    for name, request, limit, usage in pods:
        if limit is not None and usage > limit:
            print(f"  {name:10} uses {usage}Mi > limit {limit}Mi -> OOMKilled (only this container suffers)")
            continue
        running.append((name, request, usage))
    total = sum(u for _, _, u in running)
    print(f"  total usage of surviving Pods: {total}Mi")
    while total > node_memory_mi:
        # under node pressure, evict the Pod furthest above its own request
        victim = max(running, key=lambda p: (p[2] - p[1], p[0]))
        running.remove(victim)
        total -= victim[2]
        print(f"  node under memory pressure -> evict {victim[0]} ({victim[2] - victim[1]}Mi over its request)")
    print(f"  still running: {[n for n, _, _ in running]}\n")

print("A. No limits: a leak in 'reports' threatens the node")
simulate(4096, [("web", 512, None, 500), ("orders", 1024, None, 1000), ("reports", 256, None, 3500)])

print("B. Nobody set requests either: the innocent can be evicted first")
simulate(4096, [("web", 0, None, 900), ("orders", 0, None, 1000), ("reports", 0, None, 3500), ("cache", 0, None, 3600)])

print("C. With a limit: the faulty container is contained")
simulate(4096, [("web", 512, 512, 500), ("orders", 1024, 1024, 1000), ("reports", 256, 512, 3500)])
```

In scenario A the leak pushes the node past its capacity and the kubelet has to evict; the leaking Pod is furthest above its request, so it goes, but only after the whole node has been put under pressure. In scenario B, with no requests anywhere, the kubelet ranks Pods by raw overuse and a well-behaved but large Pod is evicted before the node recovers. In scenario C, the limit kills the faulty container the moment it crosses 512 MiB and the neighbours never notice.

## Elevation of privilege

This is the category where a small foothold becomes control of the cluster. There are two directions.

### Up through the API: RBAC escalation

Covered in the [RBAC lesson](#/lesson/kubernetes/rbac-admission): permissions such as reading Secrets, creating Pods, `pods/exec`, `bind`, `escalate` and `impersonate` each lead to more than they appear to grant. The defence is least privilege and regular review.

### Out through the node: container escape

A container is a process on the node, separated from it by kernel features: namespaces that limit what it sees, control groups that limit what it uses, and capability and system-call filters that limit what it may do. Several Pod settings **remove those walls**. An attacker who can run a Pod with them owns the node, and from the node can read every other Pod's Secrets and tokens.

| Setting | Why it is dangerous |
|---|---|
| `privileged: true` | Turns off almost all isolation: all capabilities, all devices, the host's kernel interfaces. Equivalent to root on the node |
| Running as root (UID 0) | Root inside the container is root on the node if any other barrier fails |
| `allowPrivilegeEscalation: true` (the default) | A process can gain privileges it did not start with |
| Added capabilities such as `SYS_ADMIN`, `NET_ADMIN`, `SYS_PTRACE` | Each restores a slice of root's power; `SYS_ADMIN` is nearly all of it |
| `hostPath` to sensitive paths | Read and write node files, including credentials and the runtime socket |
| `hostPID`, `hostNetwork`, `hostIPC` | Join the node's namespaces |
| No seccomp profile | Every system call is available to an exploit |

Compare a dangerous Pod with a hardened one.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: looks-harmless
  namespace: cafe
spec:
  hostPID: true
  hostNetwork: true
  containers:
    - name: tool
      image: busybox:1.37
      command: ["sleep", "infinity"]
      securityContext:
        privileged: true
      volumeMounts:
        - name: host-root
          mountPath: /host
  volumes:
    - name: host-root
      hostPath:
        path: /
```

Every line after `spec:` matters. `hostPID` shows all node processes. `hostNetwork` puts the Pod on the node's network. `privileged: true` removes isolation. The `hostPath` volume mounts the node's entire filesystem at `/host`. Anyone who can create this Pod can read the kubelet's credentials, every Secret mounted on the node and the node's cloud identity. This is why "can create Pods" is such a strong permission when nothing restricts *what kind* of Pod.

The hardened counterpart is the security context you saw last lesson:

```yaml
    spec:
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: menu-api
          image: ghcr.io/harbour-coffee/menu-api@sha256:9f2c1ab47d5e6f80a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
```

No host namespaces, no host paths, not privileged, not root, no escalation, no capabilities, default system-call filtering. If the application is compromised, the attacker holds an unprivileged process in a read-only box.

Further layers exist for stronger isolation: Linux security modules (**AppArmor** and **SELinux**, which confine what a process may touch); **user namespaces** (`hostUsers: false`), which map root inside the container to an unprivileged user on the node; and sandboxed runtimes such as gVisor or Kata Containers, selected with a RuntimeClass as described in the [worker nodes lesson](#/lesson/kubernetes/worker-nodes).

## Pod Security Standards

Asking every developer to remember those settings does not scale. Kubernetes defines three named policy levels, the **Pod Security Standards (PSS)**, and a built-in admission controller, **Pod Security Admission (PSA)**, that checks Pods against them.

> [!NOTE]
> An older mechanism called **PodSecurityPolicy** did this job until it was removed in version 1.25. You will still see it in older articles and books. Pod Security Admission, together with policy engines for custom rules, is its replacement.

| Level | Intent | Main rules |
|---|---|---|
| `privileged` | No restrictions | Anything is allowed. For trusted system components |
| `baseline` | Prevent known privilege escalations with minimal friction | No privileged containers; no host namespaces; no `hostPath`; no host ports; only a default set of capabilities may be added |
| `restricted` | Current hardening best practice | Everything in baseline, plus: must run as non-root; `allowPrivilegeEscalation: false`; drop `ALL` capabilities (only `NET_BIND_SERVICE` may be added back); seccomp `RuntimeDefault` or `Localhost`; only safe volume types |

The levels are applied per namespace with labels, in three **modes**:

| Mode | Effect on a violating Pod |
|---|---|
| `enforce` | Rejected |
| `audit` | Allowed; the violation is recorded in the audit log |
| `warn` | Allowed; the user sees a warning |

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cafe
  labels:
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/enforce-version: v1.37
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/audit: restricted
```

- `enforce: baseline` — Pods violating baseline are rejected.
- `enforce-version: v1.37` — pin the policy to the definition from that Kubernetes version, so that a cluster upgrade does not tighten the rules unexpectedly. `latest` follows the cluster.
- `warn: restricted` and `audit: restricted` — Pods that would fail the stricter level are allowed, but the person applying them is warned and the event is logged.

This combination is the standard way to adopt the standards: enforce the level you already meet, and warn about the one you are aiming for.

```bash
$ kubectl apply -f looks-harmless.yaml
Error from server (Forbidden): error when creating "looks-harmless.yaml": pods "looks-harmless" is forbidden:
violates PodSecurity "baseline:v1.37": host namespaces (hostNetwork=true, hostPID=true),
hostPath volumes (volume "host-root"), privileged (container "tool" must not set securityContext.privileged=true)

$ kubectl run test --image=nginx:1.29 -n cafe
Warning: would violate PodSecurity "restricted:v1.37": allowPrivilegeEscalation != false (container "test" must set
securityContext.allowPrivilegeEscalation=false), unrestricted capabilities (container "test" must set
securityContext.capabilities.drop=["ALL"]), runAsNonRoot != true (pod or container "test" must set
securityContext.runAsNonRoot=true), seccompProfile (pod or container "test" must set securityContext.seccompProfile.type
to "RuntimeDefault" or "Localhost")
pod/test created

$ kubectl label --dry-run=server --overwrite ns --all pod-security.kubernetes.io/enforce=restricted
namespace/cafe labeled (server dry run)
Warning: existing pods in namespace "finance" violate the new PodSecurity enforce level "restricted:latest"
Warning: ledger-7d9f8b6c5-x2x9p: allowPrivilegeEscalation != false, runAsNonRoot != true
```

The first command shows `enforce` rejecting the dangerous Pod and listing each violated rule. The second shows `warn`: a plain `nginx` Pod is created, with a precise list of what must change to meet `restricted`. The third is a planning tool: a server-side dry run of labelling every namespace `restricted` reports which existing Pods would violate it, without changing anything.

One behaviour to understand: the check applies to **Pods**. A Deployment whose template violates `enforce` is itself accepted, with a warning, and its Pods are then rejected when the ReplicaSet tries to create them. You see a Deployment at `0/3` and `FailedCreate` events on the ReplicaSet, as with quota.

### A checker for a subset of the rules

The logic of the standards can be written down directly. This checker implements a representative subset for both levels.

```python-run
ALLOWED_ADD_BASELINE = {"AUDIT_WRITE", "CHOWN", "DAC_OVERRIDE", "FOWNER", "FSETID", "KILL", "MKNOD",
                        "NET_BIND_SERVICE", "SETFCAP", "SETGID", "SETPCAP", "SETUID", "SYS_CHROOT"}

def check(pod, level):
    """Return a list of violations of the given Pod Security level (subset of the real rules)."""
    v = []
    if level == "privileged":
        return v
    for field in ("hostNetwork", "hostPID", "hostIPC"):
        if pod.get(field):
            v.append(f"host namespaces ({field}=true)")
    for vol in pod.get("volumes", []):
        if vol.get("type") == "hostPath":
            v.append(f"hostPath volume '{vol['name']}'")
    pod_sc = pod.get("securityContext", {})
    for c in pod["containers"]:
        sc = c.get("securityContext", {})
        if sc.get("privileged"):
            v.append(f"privileged container '{c['name']}'")
        added = set(sc.get("capabilities", {}).get("add", []))
        if added - ALLOWED_ADD_BASELINE:
            v.append(f"'{c['name']}' adds capabilities {sorted(added - ALLOWED_ADD_BASELINE)}")
        if level != "restricted":
            continue
        if sc.get("allowPrivilegeEscalation") is not False:
            v.append(f"'{c['name']}' must set allowPrivilegeEscalation=false")
        if "ALL" not in sc.get("capabilities", {}).get("drop", []):
            v.append(f"'{c['name']}' must drop ALL capabilities")
        if added - {"NET_BIND_SERVICE"}:
            v.append(f"'{c['name']}' may only add NET_BIND_SERVICE")
        if not (sc.get("runAsNonRoot", pod_sc.get("runAsNonRoot")) is True):
            v.append(f"'{c['name']}' must set runAsNonRoot=true")
        seccomp = sc.get("seccompProfile", pod_sc.get("seccompProfile"))
        if seccomp not in ("RuntimeDefault", "Localhost"):
            v.append(f"'{c['name']}' must set seccompProfile RuntimeDefault or Localhost")
    return v

pods = {
    "plain nginx": {"containers": [{"name": "nginx"}]},
    "looks-harmless": {"hostPID": True, "hostNetwork": True, "volumes": [{"name": "host-root", "type": "hostPath"}],
                       "containers": [{"name": "tool", "securityContext": {"privileged": True}}]},
    "hardened": {"securityContext": {"runAsNonRoot": True, "seccompProfile": "RuntimeDefault"},
                 "containers": [{"name": "api", "securityContext": {
                     "allowPrivilegeEscalation": False, "capabilities": {"drop": ["ALL"]}}}]},
    "net tool": {"securityContext": {"runAsNonRoot": True, "seccompProfile": "RuntimeDefault"},
                 "containers": [{"name": "sniffer", "securityContext": {
                     "allowPrivilegeEscalation": False, "capabilities": {"drop": ["ALL"], "add": ["NET_ADMIN"]}}}]},
}
for name, pod in pods.items():
    for level in ("baseline", "restricted"):
        violations = check(pod, level)
        print(f"{name:15} vs {level:10}: {'ALLOWED' if not violations else 'REJECTED'}")
        for item in violations:
            print(f"{'':30}- {item}")
```

A plain `nginx` Pod passes baseline and fails restricted on four counts. The "looks harmless" Pod fails both. The hardened Pod passes both. The network tool passes neither, because `NET_ADMIN` is outside the default capability set.

### Beyond the standards

Pod Security Admission is deliberately simple: three fixed levels, per namespace, with no exceptions for individual workloads beyond a small cluster-wide exemption list. For rules of your own ("images only from our registry", "every Pod must have resource limits", "no `latest` tag"), use ValidatingAdmissionPolicy or a policy engine such as Kyverno or Gatekeeper, as described in the [admission lesson](#/lesson/kubernetes/rbac-admission).

> [!WARNING]
> A namespace with no Pod Security labels enforces nothing, unless the cluster administrator has configured a cluster-wide default. On many clusters that means any user who can create a Pod in such a namespace can create a privileged one and take over the node it lands on. Label every namespace, system namespaces excepted, with at least `enforce: baseline`.

> [!TIP]
> To move a team to `restricted` without breaking anything: label the namespace `warn: restricted` and `audit: restricted` first; fix the warnings that appear during normal deployments (most applications need only the four `securityContext` settings and a non-root image); run the server-side dry run to confirm nothing would be rejected; then switch `enforce` to `restricted`.

> [!INTERVIEW]
> **"Why are privileged containers dangerous, and how do you prevent them?"** A privileged container has nearly all isolation removed: every capability, access to host devices and kernel interfaces. Its root user is effectively root on the node, from which an attacker can read all Pods' Secrets and tokens on that node and often move through the cluster. Related escape routes are host namespaces, `hostPath` mounts, added capabilities such as `SYS_ADMIN`, running as root and allowing privilege escalation. Prevention is layered: Pod Security Admission with `baseline` or `restricted` enforced per namespace via labels (with `warn` and `audit` for migration), hardened security contexts in every workload (non-root, no escalation, drop all capabilities, read-only root, seccomp default), custom admission policies for organisation rules, least-privilege RBAC so few identities can create Pods, and for untrusted code a sandboxed runtime or separate nodes. Mention that PodSecurityPolicy, the older mechanism, was removed in v1.25.

## Common pitfalls

- **Namespaces with no Pod Security labels.**
- **Jumping straight to `enforce: restricted`.** Use `warn` and `audit` first.
- **Looking for rejected Pods.** A Deployment is accepted; its ReplicaSet reports `FailedCreate`.
- **Images that only work as root.** Build images with a non-root user; the Docker track's [container security lesson](#/lesson/docker/container-security) shows how.
- **Granting node cloud roles broad permissions** and leaving the metadata service reachable.
- **No memory limits or ephemeral-storage limits.** One faulty Pod harms its node.
- **Single replicas and no PodDisruptionBudget** for services that must stay up.
- **Mounting the container runtime socket** into a Pod for convenience.
- **Believing `baseline` is hardening.** It blocks the worst settings only; root users are still allowed.

## Cheat sheet

| Threat | Main defences |
|---|---|
| Disclosure of Secrets | etcd encryption (KMS), RBAC, external secret managers, file mounts |
| Disclosure of cloud credentials | Workload identity, block `169.254.169.254` |
| Disclosure of host data | No host namespaces, no `hostPath` |
| DoS on a node | Requests and limits (CPU, memory, ephemeral-storage), PID limits |
| DoS on the cluster | ResourceQuota, object count quotas, API Priority and Fairness |
| DoS on an application | Replicas, spread, PodDisruptionBudgets, priorities, autoscaling |
| Privilege escalation via API | Least-privilege RBAC |
| Container escape | Pod Security Standards, hardened security contexts, sandboxed runtimes |

| PSA label | Meaning |
|---|---|
| `pod-security.kubernetes.io/enforce: LEVEL` | Reject violating Pods |
| `pod-security.kubernetes.io/audit: LEVEL` | Record violations in the audit log |
| `pod-security.kubernetes.io/warn: LEVEL` | Warn the user |
| `...-version: v1.NN` | Pin the rule set to a release |

## Summary

Information disclosure in a cluster centres on Secrets, cloud credentials reachable through the node's metadata service, and the host itself; the defences are encryption, least-privilege access, workload identity and keeping Pods out of the host's namespaces and files. Denial of service comes from exhausted nodes, namespaces and control planes as well as from deliberate attacks; requests, limits, quotas, replicas, spread and disruption budgets keep one failure from becoming everyone's. Elevation of privilege runs through over-broad RBAC and through Pod settings that dissolve container isolation, above all privileged mode, host access and running as root. The Pod Security Standards define `privileged`, `baseline` and `restricted` levels, and Pod Security Admission applies them per namespace with enforce, audit and warn modes. The next module moves from the threat model to practice across the whole delivery path.

## Glossary

- **Information disclosure**: unauthorised reading of data.
- **Denial of service (DoS)**: making a system unavailable to legitimate users.
- **Elevation of privilege**: gaining more access than was granted.
- **Container escape**: breaking out of a container to control the node.
- **Metadata service**: the cloud endpoint at `169.254.169.254` that gives a machine its identity and credentials.
- **Host namespaces**: the node's network, process and IPC namespaces, joined via `hostNetwork`, `hostPID`, `hostIPC`.
- **Privileged container**: a container with almost all isolation removed.
- **Capability**: a divisible piece of root's power, such as `NET_ADMIN`.
- **Ephemeral storage**: a container's writable layer, `emptyDir` volumes and logs.
- **PID limit**: the maximum number of processes a Pod may create.
- **AppArmor / SELinux**: Linux security modules that confine processes.
- **User namespace**: a mapping that makes root in a container unprivileged on the node.
- **Pod Security Standards (PSS)**: the `privileged`, `baseline` and `restricted` policy levels.
- **Pod Security Admission (PSA)**: the built-in admission controller enforcing them by namespace label.
- **enforce / audit / warn**: the three modes: reject, record, or warn.
- **PodSecurityPolicy**: the removed predecessor of Pod Security Admission.

```quiz
[
  {"q": "A Pod is created with privileged: true and a hostPath volume mounting / from the node. What can a process in it do?",
   "options": ["Only what any other Pod can do", "Read and modify the node's files, including credentials and other Pods' mounted Secrets", "Nothing; the kubelet ignores those settings", "Only read its own logs"],
   "answer": 1,
   "explain": "Privileged mode removes isolation and the hostPath exposes the node's filesystem. Together they amount to root on the node."},
  {"q": "A namespace is labelled pod-security.kubernetes.io/enforce: baseline. You apply a Deployment whose Pod template sets hostNetwork: true. What happens?",
   "options": ["The Deployment is rejected", "The Deployment is created with a warning, but its Pods are rejected, so the ReplicaSet shows FailedCreate", "The Pods run normally", "hostNetwork is silently removed"],
   "answer": 1,
   "explain": "Pod Security Admission enforces on Pods. The workload object is accepted with a warning; Pod creation fails and is reported on the ReplicaSet."},
  {"q": "Which requirement belongs to the restricted level but NOT to baseline?",
   "options": ["No privileged containers", "No hostPath volumes", "Containers must run as non-root", "No host network"],
   "answer": 2,
   "explain": "Baseline blocks known escalation paths such as privileged mode and host access. Restricted additionally demands non-root, no privilege escalation, dropped capabilities and a seccomp profile."},
  {"q": "A namespace has labels enforce: baseline and warn: restricted. A plain nginx Pod with no securityContext is applied. What is the result?",
   "options": ["Rejected", "Created, with a warning listing what would violate restricted", "Created silently", "Created but immediately evicted"],
   "answer": 1,
   "explain": "The Pod meets baseline, so it is admitted. The warn mode reports the restricted violations to the user without blocking."},
  {"q": "An attacker compromises a small container on a cloud node and requests http://169.254.169.254/. What are they after?",
   "options": ["The cluster DNS records", "The node's cloud identity credentials from the metadata service", "The container image", "The audit log"],
   "answer": 1,
   "explain": "The metadata service hands out credentials for the machine's cloud role. Workload identity and blocking that address remove this path."},
  {"q": "One Pod with no memory limit leaks memory until its node is under memory pressure. What happens next?",
   "options": ["Only that container is OOM-killed by its limit", "The kubelet evicts Pods to protect the node, and other workloads on the node may be affected", "The node adds more memory", "Nothing; memory is compressible"],
   "answer": 1,
   "explain": "With no limit there is nothing to stop the container at a boundary of its own, so the problem becomes node-wide and is resolved by eviction."},
  {"q": "Which control keeps the API server responsive for system components when one client floods it with requests?",
   "options": ["PodDisruptionBudget", "API Priority and Fairness", "A LimitRange", "A readiness probe"],
   "answer": 1,
   "explain": "API Priority and Fairness classifies and queues requests so that a noisy client is throttled and critical traffic keeps flowing."},
  {"q": "Why should a team migrating to the restricted level start with warn and audit modes instead of enforce?",
   "options": ["enforce is not supported for restricted", "To see which workloads would be rejected and fix them before any deployment is blocked", "warn mode is more secure", "audit mode fixes Pods automatically"],
   "answer": 1,
   "explain": "warn and audit reveal violations without rejecting Pods, allowing a safe, incremental migration."}
]
```

> **Source:** Poulton, *The Kubernetes Book*, ch. 15 (topic coverage only; the book's chapter discusses the since-removed PodSecurityPolicy, and this lesson uses its replacement). Official docs: https://kubernetes.io/docs/concepts/security/pod-security-standards/ , https://kubernetes.io/docs/concepts/security/pod-security-admission/ , https://kubernetes.io/docs/tasks/configure-pod-container/enforce-standards-namespace-labels/ , https://kubernetes.io/docs/concepts/security/security-checklist/
