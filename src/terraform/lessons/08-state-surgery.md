# State surgery: moving, removing, importing and repairing

## In plain words

Return to the library catalogue from the state lesson. Most days the catalogue updates itself as books are bought and discarded. Occasionally a librarian has to correct it by hand: a book was moved to another shelf, a donated book arrived without ever being ordered, a book is being given to another library and should come off the cards without being thrown in the bin. Each correction is small, and each is dangerous in the same way: a wrong card means a lost book or a duplicate purchase.

**State surgery** is the name engineers give to deliberately changing Terraform's state so that it matches reality again, without Terraform creating or destroying the real objects. The situations are the same as the librarian's:

- a resource was **renamed** in code, and state must follow;
- a resource **already exists** in the cloud and must be brought under Terraform's management (**import**);
- a resource should be **forgotten** by Terraform but kept running;
- reality has **drifted** from state, and you must decide which one is right.

Why this matters for a job: these are the moments when Terraform work goes wrong in production. Interviewers ask "how do you import an existing resource?" and "how do you rename a resource without recreating it?" because the answers show whether you understand state or only memorised commands.

> **Before this lesson:** read [Terraform state, remote backends and locking](#/lesson/terraform/state-and-backends) and [Isolating state: workspaces, file layout and reading another state](#/lesson/terraform/state-isolation). You should be comfortable reading a plan and know what a resource address is.

> [!WARNING]
> **Safety first.** Every command in this lesson that writes to state can cause real resources to be destroyed or duplicated on the next apply if it is done wrongly. Before any state operation: make sure the backend has versioning, take a copy with `terraform state pull > backup.tfstate`, make sure nobody else is applying, and afterwards run `terraform plan` and expect **no changes**. Practise in a sandbox first.

## The two ways to do surgery

Modern Terraform offers two styles for most operations:

1. **Declarative blocks in code** (`moved`, `import`, `removed`). You write the intention in a `.tf` file, it shows up in `plan`, a colleague reviews it, and `apply` performs it. This is the preferred style because it gets the same review as any other change and works for every environment that uses the code.
2. **Imperative commands** (`terraform state mv`, `terraform state rm`, `terraform import`). They act immediately on one state, with no plan and no review. They remain useful for one-off repairs and for older versions.

This lesson shows both, block first.

## Renaming and moving: the `moved` block

Suppose a security group was declared as `aws_security_group.sg` and you rename it to the clearer `aws_security_group.web`. Terraform identifies resources by address. To Terraform, the old address vanished and a new one appeared:

```bash
$ terraform plan
  # aws_security_group.sg will be destroyed
  # (because aws_security_group.sg is not in configuration)
  # aws_security_group.web will be created

Plan: 1 to add, 0 to change, 1 to destroy.
```

For a firewall attached to live servers that is an outage, and for a database it would be data loss. Nothing about the real object needs to change; only the label does. A `moved` block says so:

```hcl
moved {
  from = aws_security_group.sg
  to   = aws_security_group.web
}
```

- `from` is the address recorded in state.
- `to` is the address now used in the code.

```bash
$ terraform plan
  # aws_security_group.sg has moved to aws_security_group.web
    resource "aws_security_group" "web" {
        id   = "sg-0a1b2c3d4e5f67890"
        name = "bookshelf-web"
        # (8 unchanged attributes hidden)
    }

Plan: 0 to add, 0 to change, 0 to destroy.
```

The plan announces the move and proposes no changes to infrastructure. After `apply`, state uses the new address. The same block handles moving a resource into a module (`to = module.web.aws_security_group.this`), renaming a module, and switching between a single resource and one using `count` or `for_each` (`to = aws_instance.web["a"]`).

Keep `moved` blocks in the code for a while, at least until every environment and every consumer of a shared module has applied them. Removing one too early brings back the destroy-and-create plan for anyone who has not yet applied.

The older, imperative equivalent is:

```bash
terraform state mv aws_security_group.sg aws_security_group.web
```

It edits the state right away. It has to be repeated by hand for each environment's state, and nobody reviews it.

## Importing existing resources

Someone created a bucket by clicking in the console a year ago. It holds real data. You want Terraform to manage it from now on, without recreating it. That is an **import**: recording an existing object in state under an address.

### The `import` block

First write the resource block as you believe the object is configured, then add an `import` block:

```hcl
import {
  to = aws_s3_bucket.invoices
  id = "harbour-books-invoices"
}

resource "aws_s3_bucket" "invoices" {
  bucket = "harbour-books-invoices"
}
```

- `to` is the address the object should have.
- `id` is the provider's identifier for the real object. What counts as the ID differs by resource type (a bucket name, an instance ID, an ARN); each resource's documentation page has an "Import" section stating it.

```bash
$ terraform plan
  # aws_s3_bucket.invoices will be imported
    resource "aws_s3_bucket" "invoices" {
        arn    = "arn:aws:s3:::harbour-books-invoices"
        bucket = "harbour-books-invoices"
        ...
    }

Plan: 1 to import, 0 to add, 0 to change, 0 to destroy.
```

The summary gains a fourth number, "to import". The goal is a plan with an import and **nothing else**. If the plan also shows `~` changes, your resource block does not yet match reality; adjust the code until the differences disappear, unless a difference is a change you intend.

If you do not want to write the block by hand, Terraform can draft it:

```bash
terraform plan -generate-config-out=generated.tf
```

That writes a resource block for every `import` block that has no matching resource. Treat the result as a first draft: it is verbose, includes default values, and needs tidying before commit.

After a successful apply the `import` block has done its job and can be deleted.

### The `terraform import` command

The older form does the state half only:

```bash
terraform import aws_s3_bucket.invoices harbour-books-invoices
```

It writes straight to state with no plan. You must already have written the resource block, and you then run `plan` and edit the code until it shows no changes.

### Import pitfalls

- **One object, two addresses.** Importing the same real object under two addresses (or in two states) gives it two owners. Each will try to enforce its own configuration, and destroying either deletes the object.
- **Satellite resources.** Many objects are represented by several resources. An S3 bucket's versioning, encryption and public access settings are separate resource types, each needing its own import.
- **Wrong ID format.** The error message usually states the expected format.

## Forgetting a resource without destroying it

The opposite situation: Terraform manages something that it should stop managing, while the real object keeps running. Perhaps another team's configuration is taking it over, or it is being moved to a different state.

Deleting the resource block alone would plan a destroy. A `removed` block changes that:

```hcl
removed {
  from = aws_s3_bucket.invoices

  lifecycle {
    destroy = false
  }
}
```

- `from` is the address to drop from state. The resource block itself must be deleted from the code.
- `destroy = false` inside `lifecycle` means "forget it; do not delete the real object".

```bash
$ terraform plan
  # aws_s3_bucket.invoices will no longer be managed by Terraform, but will not be destroyed
  # (destroy = false is set in the configuration)

Plan: 0 to add, 0 to change, 0 to destroy.
```

The imperative equivalent:

```bash
terraform state rm aws_s3_bucket.invoices
```

After either one, the bucket is an ordinary unmanaged object again. If the resource block is still in the code after a `state rm`, the next plan will try to *create* a second one, which fails or duplicates depending on the resource type.

To move a resource from one state to another, combine the two ideas: `removed` (or `state rm`) in the source configuration and `import` in the destination.

## Drift: when reality and state disagree

**Drift** is any difference between what state records and what really exists. It appears when someone changes a setting in the console, when another tool modifies a resource, or when something is deleted outside Terraform.

Every `plan` begins with a **refresh**: for each resource in state, the provider reads the real object's current attributes. So an ordinary plan already detects drift, and it proposes to push reality back to what the code says:

```bash
$ terraform plan
aws_security_group.web: Refreshing state... [id=sg-0a1b2c3d4e5f67890]

Note: Objects have changed outside of Terraform

  # aws_instance.web will be updated in-place
  ~ resource "aws_instance" "web" {
      ~ instance_type = "t3.large" -> "t3.micro"
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```

Someone resized the server to `t3.large` by hand. The code still says `t3.micro`, so Terraform plans to shrink it back. You have two honest choices:

- **The code is right.** Apply, and the manual change is reverted.
- **The manual change is right.** Update the code to `t3.large`, and the plan becomes empty.

What you must not do is ignore it, because the next person to apply will revert the change without knowing it mattered.

To see drift without proposing any change to infrastructure, use refresh-only mode:

```bash
terraform plan -refresh-only     # show what changed outside Terraform
terraform apply -refresh-only    # accept those values into state; touches no infrastructure
```

`apply -refresh-only` updates state to match reality and nothing else. The code still disagrees until you edit it.

For attributes that are *supposed* to be changed by something else (an autoscaler adjusting a count, a deployment tool changing an image tag), tell Terraform to leave them alone:

```hcl
  lifecycle {
    ignore_changes = [desired_capacity]
  }
```

`ignore_changes` takes a list of attribute names whose differences Terraform should disregard after creation.

The simulation below models state, real attributes and the surgery operations on a toy scale. Follow each step and the plan that results.

```python-run
import copy

state = {
    "aws_security_group.sg": {"id": "sg-1", "name": "web"},
    "aws_instance.web":      {"id": "i-1", "size": "micro"},
}
real = {   # what the cloud really has, by id
    "sg-1": {"name": "web"},
    "i-1":  {"size": "large"},       # resized by hand: drift
    "b-9":  {"name": "invoices"},    # bucket created in the console, unmanaged
}
config = {
    "aws_security_group.web": {"name": "web"},        # renamed in code
    "aws_instance.web":       {"size": "micro"},
    "aws_s3_bucket.invoices": {"name": "invoices"},   # we want to adopt b-9
}

def plan(config, state, real):
    out = []
    for addr in sorted(set(config) | set(state)):
        if addr not in state:
            out.append(f"+ create  {addr}")
        elif addr not in config:
            out.append(f"- destroy {addr}")
        else:
            actual = real.get(state[addr]["id"], {})
            diff = {k: (actual.get(k), v) for k, v in config[addr].items() if actual.get(k) != v}
            if diff:
                out.append(f"~ update  {addr} {diff}")
    return out or ["No changes."]

def show(title, lines):
    print(title)
    for line in lines:
        print("   ", line)

show("1. Before any surgery:", plan(config, state, real))

s = copy.deepcopy(state)
s["aws_security_group.web"] = s.pop("aws_security_group.sg")      # moved / state mv
show("2. After moving sg -> web:", plan(config, s, real))

s["aws_s3_bucket.invoices"] = {"id": "b-9", **real["b-9"]}        # import
show("3. After importing the bucket:", plan(config, s, real))

config["aws_instance.web"]["size"] = "large"                       # accept the drift in code
show("4. After updating the code to match the manual resize:", plan(config, s, real))

del config["aws_s3_bucket.invoices"]                               # stop managing the bucket
show("5. Block deleted, nothing else done:", plan(config, s, real))
del s["aws_s3_bucket.invoices"]                                    # removed / state rm
show("6. After removing it from state too:", plan(config, s, real))
```

Step 1 shows the danger of doing nothing: a destroy and two creates. Each surgery removes one of them until the plan is empty. Step 5 shows why deleting a block alone is not "forgetting".

## Forcing a replacement

Sometimes a resource is technically unchanged but broken: a server whose startup script failed halfway, for example. To make Terraform rebuild it:

```bash
terraform apply -replace="aws_instance.web"
```

The plan shows `-/+` for that address even though the code did not change. This replaces the older `terraform taint` command, which marked a resource in state for replacement on the next apply. The `-replace` flag is preferred because the replacement appears in a plan you can review before it happens.

You may still see the word **tainted** in plan output. Terraform marks a resource as tainted on its own when creation succeeded but a later step (such as a provisioner script) failed, because the object may be half-configured. The next plan proposes replacing it.

## Other commands, and the ones to fear

```bash
terraform state list                      # all addresses
terraform state show ADDRESS              # one resource's recorded attributes
terraform state pull > backup.tfstate     # download raw state
terraform state push backup.tfstate       # upload a state file, overwriting the remote one
```

`state push` is the most dangerous command in this lesson. It replaces the remote state with a local file. Terraform refuses if the lineage differs or the serial is older, unless you add `-force`, and forcing is how teams erase their own records. Its legitimate use is restoring a known-good backup after corruption, and even then restoring a previous object version in the bucket is usually cleaner.

Editing the JSON by hand is off the table except as a last resort guided by the vendor's documentation.

## A safe procedure for any state change

1. Announce it. Make sure no pipeline or colleague will apply meanwhile.
2. Back up: `terraform state pull > backup.tfstate` (and confirm bucket versioning is on).
3. Run `terraform plan` and save the output, so you know the starting point.
4. Prefer a `moved`, `import` or `removed` block, so the change itself appears in a plan.
5. Apply.
6. Run `terraform plan` again. The target is **no changes**, or only the changes you intended.
7. Repeat per environment, starting with the least important one.
8. Delete the local backup; it contains secrets.

> [!INTERVIEW]
> "How do you rename a resource without recreating it?" Add a `moved` block from the old address to the new one, confirm the plan shows the move and zero infrastructure changes, apply, and keep the block until every environment has applied. Mention that `terraform state mv` does the same imperatively, per state, without review. For bonus credit, name the failure it prevents: a destroy-then-create of a stateful resource.

## Pitfalls

- **Renaming without `moved`.** The plan is a destroy and a create.
- **`state rm` while the block is still in the code.** The next plan creates a duplicate.
- **Importing and then applying a plan that still shows changes.** The result is a production resource changed to match a guess.
- **Importing one object into two states.** Two owners, eventual deletion.
- **Skipping the backup.** Surgery without a backup has no undo.
- **`state push -force`.** It bypasses the checks that protect you.
- **Using `ignore_changes` to hide drift you do not understand.** It silences the symptom and leaves the code describing something untrue.
- **Running surgery from a stale checkout.** The state may have moved on; pull the latest code first.

## Cheat sheet

| Goal | Declarative (preferred) | Imperative |
|---|---|---|
| Rename or move an address | `moved { from = A, to = B }` | `terraform state mv A B` |
| Adopt an existing object | `import { to = A, id = "..." }` | `terraform import A ID` |
| Draft code for an import | `terraform plan -generate-config-out=file.tf` | — |
| Stop managing, keep the object | `removed { from = A, lifecycle { destroy = false } }` | `terraform state rm A` |
| Rebuild one resource | — | `terraform apply -replace="A"` |
| See drift only | — | `terraform plan -refresh-only` |
| Accept drift into state | — | `terraform apply -refresh-only` |
| Ignore an attribute's drift | `lifecycle { ignore_changes = [attr] }` | — |
| Back up / restore state | — | `terraform state pull` / `terraform state push` |

## Summary

- State surgery changes Terraform's record without creating or destroying real objects, and a mistake causes exactly those effects on the next apply.
- Prefer the declarative blocks `moved`, `import` and `removed`: they appear in plans, get reviewed and apply to every environment.
- A rename needs a `moved` block; an existing object is adopted with `import` until the plan shows only the import; `removed` with `destroy = false` forgets a resource and keeps it running.
- Every plan refreshes and so detects drift. Decide whether code or reality is right, and make them agree.
- `-replace` rebuilds a broken resource through a reviewable plan.
- Back up first, expect "no changes" afterwards, and treat `state push` and `force` flags as last resorts.

## Glossary

- **State surgery:** deliberately modifying state to match reality.
- **`moved` block:** a declaration that an address was renamed or relocated.
- **Import:** recording an existing real object in state under an address.
- **`import` block:** the declarative way to import during plan and apply.
- **`removed` block:** a declaration that an address should leave state, optionally without destroying the object.
- **Drift:** a difference between recorded state and real infrastructure.
- **Refresh:** reading real attributes from the provider to update Terraform's view.
- **Refresh-only mode:** a plan or apply that only reconciles state with reality.
- **`ignore_changes`:** a lifecycle setting listing attributes whose drift is disregarded.
- **Tainted:** marked in state as needing replacement.
- **`-replace`:** a plan option forcing one resource to be rebuilt.

## Check yourself

```quiz
[
  {"q": "You rename `aws_db_instance.db` to `aws_db_instance.orders` in the code and add nothing else. What will the plan show?",
   "options": ["No changes", "Plan: 0 to add, 1 to change, 0 to destroy.", "Plan: 1 to add, 0 to change, 1 to destroy.", "An error about a missing resource"], "answer": 2,
   "explain": "Terraform tracks by address. The old address is in state but not in code (destroy) and the new address is in code but not in state (create). For a database that means data loss."},
  {"q": "You then add `moved { from = aws_db_instance.db, to = aws_db_instance.orders }`. What does the plan show now?",
   "options": ["Plan: 1 to add, 0 to change, 1 to destroy.", "The move is reported and Plan: 0 to add, 0 to change, 0 to destroy.", "Plan: 0 to add, 1 to change, 0 to destroy.", "Plan: 1 to import"], "answer": 1,
   "explain": "The moved block tells Terraform the existing object now has the new address, so only state is updated."},
  {"q": "After adding an `import` block and a hand-written resource block, the plan says `1 to import, 0 to add, 1 to change, 0 to destroy`. What should you do?",
   "options": ["Apply immediately", "Adjust the resource block until the change disappears, unless that change is intended", "Run state rm", "Delete the import block"], "answer": 1,
   "explain": "The pending change means the code does not match the real object. Applying would modify the live resource to match your guess."},
  {"q": "You run `terraform state rm aws_s3_bucket.logs` but leave the resource block in the code. What does the next plan show for it?",
   "options": ["No changes", "`-` destroy", "`+` create", "`~` update"], "answer": 2,
   "explain": "The address is now in the configuration but not in state, so Terraform plans to create it, colliding with or duplicating the real object."},
  {"q": "Someone changed an instance from t3.micro to t3.large in the console. The code says t3.micro. What does a normal `terraform plan` propose?",
   "options": ["Nothing; Terraform cannot see console changes", "An update changing t3.large back to t3.micro", "Destroying the instance", "Importing the instance"], "answer": 1,
   "explain": "Plan refreshes real attributes first, sees the difference from the configuration, and proposes to restore the configured value."},
  {"q": "Which command shows drift and can record it in state without changing any infrastructure?",
   "options": ["terraform apply -replace", "terraform plan -refresh-only followed by terraform apply -refresh-only", "terraform state push", "terraform destroy"], "answer": 1,
   "explain": "Refresh-only mode reconciles state with reality and proposes no infrastructure actions."},
  {"q": "What does this plan line mean: `# aws_s3_bucket.invoices will no longer be managed by Terraform, but will not be destroyed`?",
   "options": ["The bucket will be deleted on the next run", "A removed block with destroy = false drops it from state and leaves the real bucket alone", "The bucket was imported", "The bucket is tainted"], "answer": 1,
   "explain": "That is the plan output for a `removed` block whose lifecycle sets `destroy = false`."},
  {"q": "Why is a `moved` block usually better than `terraform state mv`?",
   "options": ["It is faster to type", "It appears in the plan, is reviewed with the code, and applies to every environment's state", "It works without a backend", "It also renames the real cloud object"], "answer": 1,
   "explain": "The declarative block travels with the code through review and through each environment. The command edits one state immediately with no review."}
]
```

> **Source:** Brikman, Terraform: Up & Running 3e, ch. 3 (state management) and ch. 5 (refactoring can be tricky, terraform import). Documentation: https://developer.hashicorp.com/terraform/language/moved, https://developer.hashicorp.com/terraform/language/import, https://developer.hashicorp.com/terraform/language/resources/syntax#removing-resources, https://developer.hashicorp.com/terraform/cli/commands/state and https://developer.hashicorp.com/terraform/cli/commands/plan#planning-modes
