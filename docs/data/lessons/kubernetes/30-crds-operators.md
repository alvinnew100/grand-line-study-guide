# Extending the API: CRDs and operators

## In plain words

Kubernetes ships with a fixed set of object kinds: Pod, Deployment, Service and a few dozen more. They describe generic building blocks. They do not describe *your* things: a PostgreSQL cluster with a primary and two replicas, a TLS certificate that must be renewed every ninety days, a machine-learning model to be served. You can assemble those from the built-in kinds, but then all the knowledge of how to operate them lives in a wiki page and in someone's head.

Kubernetes lets you teach it new kinds. A **CustomResourceDefinition (CRD)** adds a new type of object to the API, so that `kubectl get postgresclusters` works exactly like `kubectl get pods`. A new kind alone is only stored data, though. To make it *do* something you add a **controller** that watches objects of that kind and acts on them. A controller that carries the operational knowledge for running a particular piece of software is called an **operator**.

Imagine a company with a standard set of paper forms. One day the IT department needs a "new laptop request" form, so they design one and add it to the form cabinet: that is the CRD. A form sitting in an in-tray achieves nothing by itself. It needs a person whose job is to read each new request, order the laptop, install the software, hand it over, and later handle repairs and returns: that person is the operator. The form captures *what is wanted*; the operator knows *how to make it so, and keep it so*.

Why this matters for a job: most of what you install on a real cluster arrives as CRDs plus controllers: cert-manager, Prometheus, Argo CD, the Gateway API, database operators, KServe. You will read and write custom resources daily, debug them through their status and their controller's logs, and need to judge whether an operator is trustworthy. Interviewers ask "what is a CRD?" and "what is the operator pattern?".

> **Before this lesson:** read [Resources, groups and versions](#/lesson/kubernetes/api-resources-versions) for API groups, versions and schemas, and [The declarative model and reconciliation loops](#/lesson/kubernetes/declarative-reconciliation) for controllers, owner references and finalizers.

## Custom resources and their definitions

Two terms, easily mixed up:

- A **CustomResourceDefinition (CRD)** defines a new kind: its name, its API group, its versions and the schema its objects must follow. It is itself a built-in, cluster-scoped object. You create it once.
- A **custom resource (CR)** is an object of that new kind. You create as many as you like.

The relationship is the same as between a class and its instances in programming, or a blank form and filled-in copies.

Once a CRD is created, the API server immediately serves a new REST endpoint for it, stores its objects in etcd, validates them against the schema, applies RBAC to them, and supports `kubectl get`, `describe`, `apply`, `delete`, watches and labels. You get all of that without writing or running any API code.

## A CRD, line by line

Harbour Coffee's marketing team runs short promotions: a banner on the website plus a discount. They want to declare one in a small object and have the cluster do the rest. Here is a CRD for a kind called `Promotion`.

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: promotions.marketing.harbour-coffee.example
spec:
  group: marketing.harbour-coffee.example
  scope: Namespaced
  names:
    kind: Promotion
    plural: promotions
    singular: promotion
    shortNames: ["promo"]
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          required: ["spec"]
          properties:
            spec:
              type: object
              required: ["drink", "discountPercent"]
              properties:
                drink:
                  type: string
                  minLength: 1
                discountPercent:
                  type: integer
                  minimum: 1
                  maximum: 50
                bannerReplicas:
                  type: integer
                  minimum: 1
                  default: 1
                endsAt:
                  type: string
                  format: date-time
              x-kubernetes-validations:
                - rule: "self.discountPercent <= 30 || self.bannerReplicas >= 2"
                  message: "discounts above 30% attract crowds: use at least 2 banner replicas"
            status:
              type: object
              properties:
                phase:
                  type: string
                readyReplicas:
                  type: integer
      subresources:
        status: {}
      additionalPrinterColumns:
        - name: Drink
          type: string
          jsonPath: .spec.drink
        - name: Discount
          type: integer
          jsonPath: .spec.discountPercent
        - name: Phase
          type: string
          jsonPath: .status.phase
```

- `apiVersion: apiextensions.k8s.io/v1`, `kind: CustomResourceDefinition` — the built-in kind for defining kinds.
- `metadata.name` **must** be `<plural>.<group>`.
- `spec.group` — the API group for the new kind. Use a domain you control so that it cannot clash with anyone else's.
- `spec.scope` — `Namespaced` or `Cluster`.
- `spec.names` — the kind, its plural (used in URLs and RBAC), singular, and short names for `kubectl`.
- `spec.versions` — a list, because a CRD can serve several versions.
  - `served: true` — this version is available through the API.
  - `storage: true` — objects are stored in etcd in this version. Exactly one version has this.
  - `schema.openAPIV3Schema` — the structure objects must have, in the OpenAPI schema language. It declares the types of `drink`, `discountPercent`, `bannerReplicas` and `endsAt`, which are required, numeric bounds, and a `default` that the API server fills in when the field is omitted.
  - `x-kubernetes-validations` — rules in CEL, the expression language introduced with admission policies. `self` is the object at this point in the schema, here the `spec`. This rule relates two fields to each other, which plain schema types cannot express.
  - `subresources.status: {}` — enables a separate `/status` endpoint, so that a controller updates status without touching spec, and users editing spec cannot overwrite status.
  - `additionalPrinterColumns` — extra columns for `kubectl get`, each taken from a field path.

Apply it and the kind exists:

```bash
$ kubectl apply -f promotion-crd.yaml
customresourcedefinition.apiextensions.k8s.io/promotions.marketing.harbour-coffee.example created

$ kubectl api-resources --api-group=marketing.harbour-coffee.example
NAME         SHORTNAMES   APIVERSION                            NAMESPACED   KIND
promotions   promo        marketing.harbour-coffee.example/v1   true         Promotion

$ kubectl explain promotion.spec.discountPercent
GROUP:      marketing.harbour-coffee.example
KIND:       Promotion
VERSION:    v1
FIELD: discountPercent <integer> -required-
```

The new resource shows up in discovery, and `kubectl explain` documents it from the schema you wrote.

## A custom resource

```yaml
apiVersion: marketing.harbour-coffee.example/v1
kind: Promotion
metadata:
  name: pumpkin-week
  namespace: cafe
spec:
  drink: pumpkin spice latte
  discountPercent: 20
  endsAt: "2026-11-30T23:59:59Z"
```

It looks like any other manifest: the group and version, the kind, metadata, and a spec shaped by the schema.

```bash
$ kubectl apply -f pumpkin-week.yaml
promotion.marketing.harbour-coffee.example/pumpkin-week created

$ kubectl get promo -n cafe
NAME           DRINK                 DISCOUNT   PHASE
pumpkin-week   pumpkin spice latte   20

$ kubectl get promo pumpkin-week -n cafe -o jsonpath='{.spec.bannerReplicas}{"\n"}'
1

$ kubectl apply -f - <<EOF
apiVersion: marketing.harbour-coffee.example/v1
kind: Promotion
metadata: {name: giveaway, namespace: cafe}
spec: {drink: espresso, discountPercent: 45}
EOF
The Promotion "giveaway" is invalid: spec: Invalid value: "object": discounts above 30% attract crowds: use at least 2 banner replicas
```

The short name works, the printer columns appear, the default of `bannerReplicas: 1` was filled in, and an object breaking the CEL rule is rejected by the API server with the message from the CRD. (`kubectl apply -f -` reads the manifest from standard input; `<<EOF ... EOF` is the shell's way of supplying those lines inline.)

Notice the empty `PHASE` column. **Nothing has happened.** No banner was deployed. The API server stored a valid object and that is all. A custom resource without a controller is a database record.

## Controllers: giving a kind behaviour

A **custom controller** is a program, usually running as a Deployment inside the cluster, that watches a kind and reconciles reality with each object's spec, in the loop you know well: observe, compare, act, report. For `Promotion`, the controller would, for each object:

1. make sure a Deployment of banner Pods exists with the right replica count and a ConfigMap holding the promotion text,
2. set owner references on them so they are garbage-collected when the Promotion is deleted,
3. after `endsAt`, scale the banner to zero,
4. write `status.phase` and `status.readyReplicas`.

The program below is that controller in miniature. The dictionaries stand in for the API server. Run it and follow how each pass through the loop moves the world towards the spec.

```python-run
cluster = {"promotions": {}, "deployments": {}, "configmaps": {}}

def reconcile(name, now):
    """One pass of the Promotion controller for one object. Returns a log of actions."""
    log = []
    promo = cluster["promotions"].get(name)
    child = f"promo-{name}"
    if promo is None:                                   # the Promotion was deleted
        for kind in ("deployments", "configmaps"):
            if child in cluster[kind]:
                del cluster[kind][child]
                log.append(f"garbage collect {kind[:-1]} {child} (owner gone)")
        return log or ["nothing to do"]
    spec = promo["spec"]
    expired = spec.get("endsAt") is not None and now >= spec["endsAt"]
    want_replicas = 0 if expired else spec.get("bannerReplicas", 1)
    want_text = f"{spec['discountPercent']}% off {spec['drink']}"

    cm = cluster["configmaps"].get(child)
    if cm is None or cm["text"] != want_text:
        cluster["configmaps"][child] = {"text": want_text, "owner": name}
        log.append(f"{'create' if cm is None else 'update'} configmap {child}: {want_text!r}")

    dep = cluster["deployments"].get(child)
    if dep is None:
        cluster["deployments"][child] = {"replicas": want_replicas, "ready": 0, "owner": name}
        log.append(f"create deployment {child} replicas={want_replicas}")
    elif dep["replicas"] != want_replicas:
        dep["replicas"] = want_replicas
        log.append(f"scale deployment {child} to {want_replicas}")

    dep = cluster["deployments"][child]
    phase = "Expired" if expired else ("Active" if dep["ready"] == want_replicas else "Progressing")
    new_status = {"phase": phase, "readyReplicas": dep["ready"]}
    if promo.get("status") != new_status:
        promo["status"] = new_status
        log.append(f"update status: {new_status}")
    return log or ["nothing to do"]

def pods_become_ready():
    for dep in cluster["deployments"].values():
        dep["ready"] = dep["replicas"]

def step(title, now, name="pumpkin-week"):
    print(f"\n{title}")
    for line in reconcile(name, now):
        print("   ", line)

cluster["promotions"]["pumpkin-week"] = {"spec": {"drink": "pumpkin spice latte", "discountPercent": 20, "endsAt": 100}}
step("1. Promotion created", now=1)
step("2. Reconcile again before Pods are ready", now=2)
pods_become_ready()
step("3. Pods became ready", now=3)
step("4. No change (idempotent)", now=4)
cluster["promotions"]["pumpkin-week"]["spec"]["discountPercent"] = 25
cluster["promotions"]["pumpkin-week"]["spec"]["bannerReplicas"] = 3
step("5. Someone edits the Promotion", now=5)
del cluster["deployments"]["promo-pumpkin-week"]
step("6. Someone deletes the Deployment by hand", now=6)
pods_become_ready()
step("7. The end date passes", now=100)
del cluster["promotions"]["pumpkin-week"]
step("8. The Promotion is deleted", now=101)
```

Each step is a situation real operators handle. Step 4 does nothing, because the world already matches. Step 6 shows self-healing of the operator's own children: a manually deleted Deployment is recreated. Step 7 is where an operator goes beyond what a static manifest can do, since it acts on the passage of time. In step 8, deleting the one custom resource cleans up everything it owned.

In real life controllers are written with a framework that supplies the plumbing (watches, caches, work queues, retries, leader election). The most used are **controller-runtime** and **Kubebuilder** and the **Operator SDK** for Go, and **kopf** for Python.

## The operator pattern

An **operator** is a controller plus one or more CRDs that together encode the knowledge of a human operations expert for one application. The term comes from the idea of capturing what an "operator" (a person) would do.

The difference from a simple controller is the depth of what is automated. Operators are often described by maturity level:

| Level | Capability | Example for a database operator |
|---|---|---|
| 1 | Install | Create the StatefulSet, Services, config and credentials from one object |
| 2 | Upgrade | Roll to a new version in the correct order, replicas before primary |
| 3 | Full lifecycle | Backups, restores, failure recovery, failover to a new primary |
| 4 | Insights | Metrics, alerts, dashboards |
| 5 | Auto-pilot | Automatic scaling, tuning and healing |

This is the answer to the caveat in the [StatefulSet lessons](#/lesson/kubernetes/statefulset-theory): a StatefulSet gives identity and storage, and an operator supplies the application-specific logic on top, such as replication setup and failover. With a PostgreSQL operator you write something like this:

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: orders-db
  namespace: cafe
spec:
  instances: 3
  storage:
    size: 20Gi
    storageClass: fast-ssd
  backup:
    barmanObjectStore:
      destinationPath: s3://harbour-coffee-backups/orders-db
```

One object asks for a three-instance cluster with storage and backups to object storage. The operator (here CloudNativePG, one of several) creates the Pods and volumes, configures replication, promotes a replica if the primary fails, and ships backups. You manage a database through a declarative object, the way you manage a web service through a Deployment.

Operators you are likely to meet:

| Operator / controller | Custom kinds | Does |
|---|---|---|
| cert-manager | `Certificate`, `Issuer`, `ClusterIssuer` | Obtains and renews TLS certificates |
| Prometheus Operator | `Prometheus`, `ServiceMonitor`, `PrometheusRule` | Runs monitoring and configures what is scraped |
| Argo CD | `Application`, `AppProject` | Syncs manifests from Git |
| External Secrets Operator | `ExternalSecret`, `SecretStore` | Syncs secrets from external managers |
| Gateway controllers | `Gateway`, `HTTPRoute` | Traffic routing |
| KServe | `InferenceService` | Serves ML models |
| Database operators | `Cluster`, `PostgresCluster`, and similar | Run databases with replication and backups |

## Working with custom resources day to day

A custom resource is debugged like any other object, plus one extra place to look: the controller.

```bash
$ kubectl get crds | grep -E "cert-manager|gateway" | head -4
certificates.cert-manager.io                2026-10-02T08:11:23Z
clusterissuers.cert-manager.io              2026-10-02T08:11:23Z
gateways.gateway.networking.k8s.io          2026-10-02T08:14:02Z
httproutes.gateway.networking.k8s.io        2026-10-02T08:14:02Z

$ kubectl get certificate -n cafe
NAME       READY   SECRET     AGE
shop-tls   False   shop-tls   6m

$ kubectl describe certificate shop-tls -n cafe | sed -n '/Status/,$p'
Status:
  Conditions:
    Last Transition Time:  2026-11-21T13:40:02Z
    Message:               Issuing certificate as Secret does not exist
    Reason:                DoesNotExist
    Status:                False
    Type:                  Ready
Events:
  Type     Reason     Age   From          Message
  Warning  Failed     2m    cert-manager  The certificate request has failed to complete: DNS record for "shop.harbour-coffee.example" not found

$ kubectl logs -n cert-manager deploy/cert-manager --tail=3
```

`kubectl get crds` lists installed definitions. The custom resource's **status conditions** and **events**, shown by `describe`, are where a well-written operator tells you what it is doing and why it is stuck. If they do not explain it, the controller's own logs will. The order to follow is always: the resource's status and events, then the controller's logs, then the objects the controller created (`kubectl get all -l` the relevant label, or follow owner references).

Access to custom resources is controlled by ordinary RBAC, using the CRD's group and plural:

```yaml
rules:
  - apiGroups: ["marketing.harbour-coffee.example"]
    resources: ["promotions"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
```

## Versions, conversion and the life of a CRD

Custom APIs evolve like built-in ones. A CRD can list several versions (`v1alpha1`, `v1beta1`, `v1`), each with its own schema, with one marked as the storage version. When the versions differ in structure, a **conversion webhook** translates objects between them on request. Changing a CRD's schema in an incompatible way with objects already stored is how upgrades of operators go wrong, which is why operator release notes need reading.

Two properties of CRDs deserve care:

- **Deleting a CRD deletes every custom resource of that kind**, in every namespace, and the controller then cleans up whatever those resources owned. Deleting the cert-manager CRDs deletes every `Certificate`; deleting a database operator's CRD can delete every database it manages.
- **CRDs are cluster-scoped and shared.** Two applications that each bundle a different version of the same CRD will conflict. This is a known pain point with Helm charts, which install CRDs but do not upgrade them.

> [!WARNING]
> Treat `kubectl delete crd` as one of the most destructive commands in Kubernetes. It cascades to every object of that kind across the whole cluster and, through owner references and finalizers, to the workloads and sometimes the data those objects stand for. When uninstalling an operator, read its documentation on the order of removal, and confirm what will be left behind before removing any CRD.

Finalizers, introduced in the declarative model lesson, are how operators clean up things outside the cluster. A database operator adds a finalizer to each custom resource so that when the resource is deleted, the controller gets a chance to remove cloud backups or DNS records before the object disappears. If the operator has already been uninstalled, nothing removes the finalizer and the resource stays in `Terminating`. The correct order is: delete the custom resources, let the operator finish, then remove the operator and its CRDs.

## Choosing and trusting an operator

An operator runs inside your cluster with whatever permissions it was given, often broad ones: creating Pods, reading Secrets, sometimes cluster-wide. Before installing one, check:

- **What RBAC does it request?** Read the ClusterRoles in its manifests. Cluster-wide Secret access or `*` verbs deserve a question.
- **Who maintains it, and how actively?** An operator for a database is a long-term dependency.
- **Is it scoped to one namespace or the whole cluster?**
- **What happens on upgrade and uninstall?** Especially to CRDs and data.
- **How does it behave when it is down?** A good operator's workloads keep running without it; only changes and healing pause.

### The aggregation layer

CRDs are one of two ways to extend the API. The other, **API aggregation**, registers a separate API server behind the main one for a whole group, using an `APIService` object. It suits APIs that need custom storage or behaviour CRDs cannot express. The metrics API behind `kubectl top` (`metrics.k8s.io`, served by metrics-server) is the example you are most likely to meet. For almost everything else, CRDs are the simpler choice.

> [!TIP]
> When you inherit a cluster, run `kubectl get crds` and `kubectl api-resources --api-group=<group>` for each unfamiliar group. The list of CRDs is the fastest inventory of what has been installed on top of plain Kubernetes, and each group name usually leads straight to the project's documentation.

> [!INTERVIEW]
> **"What is a CRD, and what is an operator?"** A CustomResourceDefinition registers a new kind with the API server: a group, versions, names, scope and an OpenAPI schema, optionally with CEL validation rules, a status subresource and printer columns. Once created, the API server serves, stores, validates and authorises objects of that kind like any built-in resource, but nothing acts on them. A controller that watches the custom resources and reconciles the cluster towards their spec supplies the behaviour. An operator is such a controller, with its CRDs, that encodes the operational knowledge for a specific application: installation, upgrades, backups, failover and scaling. It manages lower-level objects (StatefulSets, Services, Secrets), usually with owner references for cleanup and finalizers for external resources. Close with the risks: operators hold significant RBAC permissions, and deleting a CRD deletes all of its custom resources.

## Common pitfalls

- **Expecting a custom resource to do something without its controller running.** It is stored and ignored.
- **Applying a custom resource before its CRD exists.** `no matches for kind`. Install CRDs first, and wait until they are established.
- **Deleting a CRD to "clean up".** Every object of the kind goes with it.
- **Uninstalling an operator before its resources.** Objects with finalizers hang in `Terminating`.
- **Editing the objects an operator created.** The operator puts them back; change the custom resource instead.
- **Ignoring status conditions.** They usually state the problem outright.
- **Conflicting CRD versions between tools.** CRDs are cluster-wide singletons.
- **Granting an operator `cluster-admin` without reading what it needs.**

## Cheat sheet

| Term | Meaning |
|---|---|
| CRD | Definition of a new kind; cluster-scoped; named `plural.group` |
| CR | An object of a custom kind |
| Controller | Loop that reconciles objects of a kind |
| Operator | Controller + CRDs with application-specific operational logic |
| Status subresource | Separate endpoint for status, written by the controller |
| Finalizer | Blocks deletion until the controller has cleaned up |

| Task | Command |
|---|---|
| List installed CRDs | `kubectl get crds` |
| Resources in a custom group | `kubectl api-resources --api-group=GROUP` |
| Schema of a custom kind | `kubectl explain KIND.spec` |
| Why is my resource not ready? | `kubectl describe KIND NAME`, then the controller's logs |
| Wait for a CRD to be usable | `kubectl wait --for=condition=Established crd/NAME` |
| What did the operator create? | `kubectl get all -n NS -l LABEL` or follow `ownerReferences` |

## Summary

The Kubernetes API is extensible. A CustomResourceDefinition adds a new kind with its own group, versions and validated schema, and the API server then treats objects of that kind like any others. Behaviour comes from a controller that reconciles those objects, and an operator is a controller that packages the operational expertise for one application, from installation through upgrades, backups and failover. Most of the ecosystem, from certificate management to databases to the Gateway API, is delivered this way. Custom resources are debugged through their status conditions, their events and their controller's logs. The power comes with responsibilities: operators hold broad permissions, and removing a CRD removes everything defined by it. With the API and its access controls understood, the next module asks how all of this can be attacked, and defended.

## Glossary

- **CustomResourceDefinition (CRD)**: an object that defines a new kind in the API.
- **Custom resource (CR)**: an instance of a kind defined by a CRD.
- **Schema**: the declared structure and types an object must follow.
- **OpenAPI v3 schema**: the schema language used in CRDs.
- **CEL validation rule**: an expression in a CRD that an object must satisfy.
- **Storage version**: the version in which custom resources are persisted.
- **Conversion webhook**: a service that translates custom resources between versions.
- **Printer columns**: extra columns shown by `kubectl get` for a custom kind.
- **Custom controller**: a program that reconciles custom resources.
- **Operator**: a controller that automates the operation of a specific application.
- **Operator pattern**: capturing human operational knowledge in a controller.
- **controller-runtime / Kubebuilder / Operator SDK / kopf**: frameworks for writing controllers.
- **Status condition**: a typed true-or-false entry in status with a reason and message.
- **API aggregation**: extending the API with a separate API server registered through an APIService.
- **Established**: the CRD condition meaning its endpoint is ready to serve.

```quiz
[
  {"q": "You apply a CRD and then create a custom resource of the new kind. No controller for it is installed. What happens?",
   "options": ["The API server rejects the resource", "The resource is stored and can be listed, but nothing acts on it", "Kubernetes creates Pods for it automatically", "The CRD is deleted after a timeout"],
   "answer": 1,
   "explain": "A CRD gives storage, validation and an API endpoint. Behaviour requires a controller watching the kind."},
  {"q": "What must a CRD's metadata.name be?",
   "options": ["The kind in lowercase", "<plural>.<group>", "<group>/<version>", "Any unique string"],
   "answer": 1,
   "explain": "The name is the plural resource name followed by the API group, for example promotions.marketing.harbour-coffee.example."},
  {"q": "An administrator runs kubectl delete crd certificates.cert-manager.io to tidy up. What is the consequence?",
   "options": ["Only the definition is removed; existing Certificates stay", "Every Certificate object in every namespace is deleted", "cert-manager recreates the CRD and its objects", "Nothing until the next restart"],
   "answer": 1,
   "explain": "Deleting a CRD deletes all custom resources of that kind cluster-wide, with further cascading through owner references and finalizers."},
  {"q": "A Certificate custom resource shows READY False. Where should you look first?",
   "options": ["The kubelet logs on a random node", "kubectl describe on the Certificate for its status conditions and events, then the controller's logs", "The CRD's schema", "The scheduler"],
   "answer": 1,
   "explain": "Operators report progress and errors in the resource's status and events. The controller's logs are the next step."},
  {"q": "A database operator created a StatefulSet. You edit the StatefulSet's replicas directly from 3 to 5. What happens next?",
   "options": ["The change sticks", "The operator reconciles the StatefulSet back to what the custom resource specifies", "The custom resource is updated to 5", "The StatefulSet is deleted"],
   "answer": 1,
   "explain": "The custom resource is the source of truth. Objects the operator owns are restored to match it, so change the custom resource."},
  {"q": "An operator was uninstalled, and now its custom resources are stuck in Terminating. Why are they not deleted?",
   "options": ["The CRD is cluster-scoped", "They carry finalizers that only the now-absent controller would remove", "etcd is read-only", "RBAC forbids deletion"],
   "answer": 1,
   "explain": "Finalizers block deletion until their controller completes cleanup and removes them. Delete the resources before removing the operator."},
  {"q": "What distinguishes an operator from a plain custom controller?",
   "options": ["Operators do not use CRDs", "An operator encodes application-specific operational knowledge such as upgrades, backups and failover", "Operators run outside the cluster only", "Operators cannot use finalizers"],
   "answer": 1,
   "explain": "Every operator is a controller. The term implies automating the day-two operations a human expert would perform for a particular application."},
  {"q": "A custom resource is rejected with a message you recognise from the CRD's x-kubernetes-validations. Which component rejected it?",
   "options": ["The operator's controller", "The API server, while validating the object against the CRD", "The scheduler", "The kubelet"],
   "answer": 1,
   "explain": "Schema and CEL rules in a CRD are enforced by the API server at admission, before the object is stored and before any controller sees it."}
]
```

> **Source:** Poulton, *The Kubernetes Book*, ch. 14 (topic coverage only). Official docs: https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/ , https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/ , https://kubernetes.io/docs/concepts/extend-kubernetes/operator/ , https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/apiserver-aggregation/
