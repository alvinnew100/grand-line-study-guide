# Loops: count, for_each and the index-shifting trap

## In plain words

A teacher has thirty pupils and thirty pegs for coats. One way to assign pegs is by position in the register: first pupil gets peg 1, second gets peg 2, and so on. It works until the third pupil leaves the school. Now everyone after them moves up one line in the register, and twenty-seven children are told their coat belongs on a different peg.

The other way is to write each child's name on a peg. When a pupil leaves, one peg loses its label and nobody else is affected.

Terraform has two ways to create several copies of a resource, and they differ in exactly this way. `count` assigns by position. `for_each` assigns by name. This lesson teaches both, shows the damage the first can do, and gives you a rule for choosing.

Why this matters for a job: "what is the difference between count and for_each?" is one of the most frequently asked Terraform interview questions, and the index-shifting problem behind it has caused real outages when servers or user accounts were recreated by accident.

> **Before this lesson:** complete [Reusable modules: inputs, outputs and locals](#/lesson/terraform/module-basics). You should know the collection types from the variables lesson: a list is an ordered sequence, a map is a set of key and value pairs.

> [!WARNING]
> **Cost and safety.** A loop multiplies resources. A typing mistake that turns 3 into 30 creates thirty billable servers. The examples use IAM users, which cost nothing, so you can try them freely in a sandbox account. Read the "to add" number in every plan before approving.

## Why loops are needed

HCL is declarative, so there is no `for` statement that repeats a block. Without a looping feature, three users means writing three nearly identical blocks, and a list of users supplied as a variable could not be handled at all. Terraform's answer is a pair of **meta-arguments**, settings that work on any resource and are handled by Terraform itself: `count` and `for_each`.

## `count`: a number of copies

```hcl
resource "aws_iam_user" "staff" {
  count = 3
  name  = "staff-${count.index}"
}
```

- `count = 3` asks for three copies of this resource.
- Inside the block, `count.index` is the number of the current copy, starting at 0. So the users are named `staff-0`, `staff-1` and `staff-2`.

An **IAM user** is an identity in AWS that a person or program signs in as. The AWS track covers them in [IAM users, groups, roles and policies](#/lesson/aws/iam-identities).

Numbered names are rarely what you want. Combine `count` with a list variable to get real names:

```hcl
variable "staff_names" {
  description = "People who need an account"
  type        = list(string)
  default     = ["asha", "ben", "chidi"]
}

resource "aws_iam_user" "staff" {
  count = length(var.staff_names)
  name  = var.staff_names[count.index]
}
```

- `length(list)` is a built-in function returning the number of elements, here 3.
- `var.staff_names[count.index]` picks the element at the current position. Square brackets after a list select by position, starting from 0.

With `count`, the resource is no longer one object; it is a **list** of objects. Each has an address with its position in square brackets:

```bash
$ terraform plan
  # aws_iam_user.staff[0] will be created
  + resource "aws_iam_user" "staff" { + name = "asha"  ... }
  # aws_iam_user.staff[1] will be created
  + resource "aws_iam_user" "staff" { + name = "ben"   ... }
  # aws_iam_user.staff[2] will be created
  + resource "aws_iam_user" "staff" { + name = "chidi" ... }

Plan: 3 to add, 0 to change, 0 to destroy.
```

To refer to them elsewhere:

```hcl
output "first_arn" {
  value = aws_iam_user.staff[0].arn
}

output "all_arns" {
  value = aws_iam_user.staff[*].arn
}
```

- `aws_iam_user.staff[0].arn` reads one copy's attribute.
- `aws_iam_user.staff[*].arn` is a **splat expression**: the `[*]` means "for every element, take this attribute", giving a list of all three ARNs.

## The trap: removing an item from the middle

Ben leaves the company. You remove his name:

```hcl
  default = ["asha", "chidi"]
```

You expect one user to be deleted. Here is the plan:

```bash
$ terraform plan

  # aws_iam_user.staff[1] will be updated in-place
  ~ resource "aws_iam_user" "staff" {
      ~ name = "ben" -> "chidi"
    }

  # aws_iam_user.staff[2] will be destroyed
  # (because index [2] is out of range for count)
  - resource "aws_iam_user" "staff" {
      - name = "chidi" -> null
    }

Plan: 0 to add, 1 to change, 1 to destroy.
```

Terraform does not know about names. It knows positions. Before, position 1 was "ben" and position 2 was "chidi". Now position 1 should be "chidi" and position 2 should not exist. So it proposes to rename Ben's account to "chidi" and delete Chidi's real account.

The outcome is wrong in several ways at once. Chidi's original account, with its access keys, permissions and history, is destroyed. Ben's account lives on under a new name. And depending on the resource type the apply may fail halfway, because for a moment two users would both be called "chidi".

With servers instead of users the effect is worse: for a resource whose changed attribute forces replacement, every element after the removed one is destroyed and recreated. Remove the first item from a list of fifty and forty-nine resources are rebuilt.

This is the **index-shifting problem**, and it is the main reason to prefer `for_each`.

## `for_each`: one copy per key

```hcl
variable "staff_names" {
  type    = list(string)
  default = ["asha", "ben", "chidi"]
}

resource "aws_iam_user" "staff" {
  for_each = toset(var.staff_names)
  name     = each.value
}
```

- `for_each` takes a **map** or a **set of strings** and creates one copy for each element.
- A **set** is a collection of unique values with no order. `toset(list)` converts a list into a set, removing duplicates. `for_each` does not accept a plain list, precisely because a list has positions and `for_each` exists to avoid them.
- Inside the block, `each.key` is the current element's key and `each.value` is its value. For a set the two are the same; for a map they are the key and the value.

Now the resource is a **map** of objects, and each address carries its key as a quoted string:

```bash
$ terraform plan
  # aws_iam_user.staff["asha"] will be created
  # aws_iam_user.staff["ben"] will be created
  # aws_iam_user.staff["chidi"] will be created

Plan: 3 to add, 0 to change, 0 to destroy.
```

Remove "ben" from the list and plan again:

```bash
$ terraform plan
  # aws_iam_user.staff["ben"] will be destroyed
  # (because key ["ben"] is not in for_each map)
  - resource "aws_iam_user" "staff" {
      - name = "ben" -> null
    }

Plan: 0 to add, 0 to change, 1 to destroy.
```

One destroy, and it is the right one. Asha and Chidi are identified by their names, so nothing about them changed.

Referring to the copies:

```hcl
output "chidi_arn" {
  value = aws_iam_user.staff["chidi"].arn
}

output "all_arns" {
  value = values(aws_iam_user.staff)[*].arn
}
```

- `aws_iam_user.staff["chidi"]` selects one copy by key.
- The splat `[*]` works on lists, not maps, so `values(map)` first turns the map's values into a list.

### `for_each` with a map

A map lets each copy carry several settings:

```hcl
variable "buckets" {
  description = "Buckets to create, keyed by purpose"
  type = map(object({
    versioned = bool
    team      = string
  }))
  default = {
    invoices = { versioned = true, team = "finance" }
    uploads  = { versioned = false, team = "web" }
  }
}

resource "aws_s3_bucket" "this" {
  for_each = var.buckets
  bucket   = "harbour-books-${each.key}"

  tags = {
    Team = each.value.team
  }
}
```

- The type `map(object({ ... }))` reads as "a map whose values are objects with these two fields".
- `each.key` is `invoices` or `uploads`; `each.value.team` reaches into the object for one field.
- The addresses are `aws_s3_bucket.this["invoices"]` and `aws_s3_bucket.this["uploads"]`.

## See the difference for yourself

The simulation compares the two addressing schemes when one name is removed. It treats `name` as an attribute that can be updated in place, as it is for IAM users, and then as a force-new attribute, as an AMI would be for servers.

```python-run
def plan_count(old, new, force_new):
    actions = []
    for i in range(max(len(old), len(new))):
        addr = f"res[{i}]"
        if i >= len(old):
            actions.append((addr, "create", new[i]))
        elif i >= len(new):
            actions.append((addr, "destroy", old[i]))
        elif old[i] != new[i]:
            actions.append((addr, "replace" if force_new else "update", f"{old[i]} -> {new[i]}"))
    return actions

def plan_for_each(old, new):
    actions = []
    for k in sorted(set(old) | set(new)):
        if k not in old:
            actions.append((f'res["{k}"]', "create", k))
        elif k not in new:
            actions.append((f'res["{k}"]', "destroy", k))
    return actions

def summarise(actions):
    add = sum(a in ("create", "replace") for _, a, _ in actions)
    chg = sum(a == "update" for _, a, _ in actions)
    des = sum(a in ("destroy", "replace") for _, a, _ in actions)
    return f"Plan: {add} to add, {chg} to change, {des} to destroy."

old = ["asha", "ben", "chidi", "dana", "eli"]
new = ["asha", "chidi", "dana", "eli"]          # ben removed from the middle

for title, acts in [
    ("count, name updatable in place", plan_count(old, new, False)),
    ("count, attribute forces replacement", plan_count(old, new, True)),
    ("for_each", plan_for_each(old, new)),
]:
    print(title)
    for addr, act, detail in acts:
        print(f"   {act:8} {addr:14} {detail}")
    print("  ", summarise(acts), "\n")
```

Try removing the *last* name instead of a middle one. With `count` that case happens to behave, which is why the bug often hides until the day someone removes an early element.

## Loops on modules

Both meta-arguments work on `module` blocks too:

```hcl
module "site" {
  source   = "../../modules/web-fleet"
  for_each = toset(["bookshelf", "checkout"])

  name     = "${each.key}-dev"
  min_size = 1
  max_size = 2
}

output "urls" {
  value = { for name, m in module.site : name => m.alb_dns_name }
}
```

- This creates two complete copies of everything in the module, addressed as `module.site["bookshelf"]` and `module.site["checkout"]`.
- The output uses a `for` expression, taught in the next lesson, to build a map from site name to DNS name.

## Looping inside a resource: `dynamic` blocks

`count` and `for_each` repeat whole resources. To repeat a *nested block* inside one resource, use a **`dynamic` block**:

```hcl
variable "group_tags" {
  type    = map(string)
  default = { Team = "web", CostCentre = "retail" }
}

resource "aws_autoscaling_group" "web" {
  # ...other arguments...

  dynamic "tag" {
    for_each = var.group_tags

    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }
}
```

- `dynamic "tag"` says "generate `tag` blocks".
- `for_each` gives the collection to loop over.
- `content { ... }` is the body of each generated block. Inside it, the iterator is named after the block (`tag`), with `tag.key` and `tag.value`.

The result is the same as writing two `tag` blocks by hand. Use `dynamic` when the number of nested blocks comes from input; when the blocks are fixed, writing them out is easier to read.

## Limits of count and for_each

Three restrictions catch people out.

**1. The count or the keys must be known at plan time.** Terraform must decide *how many* resources exist and what their addresses are before it creates anything. So `count` and the keys of `for_each` cannot depend on a value that only exists after apply:

```hcl
# Fails if aws_instance.web is created in the same run
resource "aws_eip" "web" {
  for_each = toset(aws_instance.web[*].id)
}
```

```bash
Error: Invalid for_each argument

The "for_each" set includes values derived from resource attributes that cannot
be determined until apply, and so Terraform cannot determine the full set of
keys that will identify the instances of this resource.
```

The fix is to key by something you know in advance, such as names from a variable, and let unknown values appear only in the *values*.

**2. `for_each` keys cannot be sensitive.** The keys become part of resource addresses, which are printed in plans, so a value marked sensitive is rejected as a key.

**3. `count` and `for_each` cannot be used together** on the same block.

## Converting from count to for_each

Switching an existing resource changes every address from `staff[0]` to `staff["asha"]`. Without help, the plan would destroy all the old copies and create new ones. Add `moved` blocks to tell Terraform which is which:

```hcl
moved {
  from = aws_iam_user.staff[0]
  to   = aws_iam_user.staff["asha"]
}

moved {
  from = aws_iam_user.staff[1]
  to   = aws_iam_user.staff["ben"]
}

moved {
  from = aws_iam_user.staff[2]
  to   = aws_iam_user.staff["chidi"]
}
```

The plan should then report three moves and no infrastructure changes.

## Choosing between them

| | `count` | `for_each` |
|---|---|---|
| Input | A whole number | A map or a set of strings |
| Identity of each copy | Position: `[0]`, `[1]` | Key: `["asha"]` |
| Inside the block | `count.index` | `each.key`, `each.value` |
| Removing a middle item | Shifts every later copy | Affects only that copy |
| Resource becomes | A list | A map |
| Good for | "This thing, or not" (0 or 1); N truly identical copies | Anything with a natural name |

A working rule: **use `for_each` for collections, and keep `count` for switching a single resource on or off**, which the next lesson covers.

> [!INTERVIEW]
> "count versus for_each?" Both create multiple instances. `count` identifies them by index, so removing an element from the middle of the source list shifts the others and causes unwanted updates or replacements. `for_each` identifies them by a stable key from a map or set, so only the removed key is destroyed. Add the constraints: keys must be known at plan time and cannot be sensitive, and converting needs `moved` blocks.

## Pitfalls

- **`count` over a list of named things.** It works until someone deletes or reorders an entry.
- **Passing a list to `for_each`.** The error says a map or set of strings is required; wrap it in `toset()`.
- **Duplicates in the list.** `toset` silently merges them, giving fewer resources than list entries.
- **Keys derived from unknown values.** Use static keys from variables.
- **Forgetting the index or key when referencing.** After adding `count`, `aws_iam_user.staff.arn` no longer works; write `[0]` or `[*]`.
- **Sorting or reordering a list used with `count`.** Every position changes meaning.
- **Converting without `moved` blocks.** Everything is recreated.

## Cheat sheet

| Task | Syntax |
|---|---|
| N copies | `count = 3`, `count.index` |
| One per list element (by position) | `count = length(var.xs)`, `var.xs[count.index]` |
| One per set element | `for_each = toset(var.xs)`, `each.value` |
| One per map entry | `for_each = var.m`, `each.key`, `each.value.field` |
| Address with count | `aws_x.y[0]` |
| Address with for_each | `aws_x.y["key"]` |
| All attributes (count) | `aws_x.y[*].arn` |
| All attributes (for_each) | `values(aws_x.y)[*].arn` |
| Repeat a nested block | `dynamic "block" { for_each = ...  content { ... } }` |
| Loop over a module | `for_each` or `count` in the `module` block |

## Summary

- `count` creates copies identified by position; `for_each` creates copies identified by key.
- Removing an element from the middle of a list used with `count` shifts all later positions, causing wrong updates or mass replacement.
- `for_each` takes a map or set of strings; convert lists with `toset`.
- With `count` a resource is a list (`[0]`, `[*]`); with `for_each` it is a map (`["key"]`, `values(...)`).
- `dynamic` blocks repeat nested blocks inside a resource.
- Counts and keys must be known at plan time, and keys cannot be sensitive.
- Convert between the two with `moved` blocks so nothing is recreated.

## Glossary

- **Meta-argument:** an argument handled by Terraform core on any resource or module.
- **`count`:** a meta-argument that creates a numbered list of copies.
- **`count.index`:** the position of the current copy, from 0.
- **`for_each`:** a meta-argument that creates one copy per map entry or set element.
- **`each.key` / `each.value`:** the current element's key and value.
- **Set:** an unordered collection of unique values.
- **`toset`:** a function converting a list to a set.
- **Splat expression:** `[*]`, which collects one attribute from every element of a list.
- **Index shifting:** positions changing meaning when a list element is removed or reordered.
- **`dynamic` block:** a construct that generates repeated nested blocks.
- **Known at plan time:** a value Terraform can determine before creating anything.

## Check yourself

```quiz
[
  {"q": "`count = length(var.names)` with names `[\"a\", \"b\", \"c\", \"d\"]` creates four resources whose `name` can be updated in place. You remove \"a\". What does the plan show?",
   "options": ["Plan: 0 to add, 0 to change, 1 to destroy.", "Plan: 0 to add, 3 to change, 1 to destroy.", "Plan: 3 to add, 0 to change, 4 to destroy.", "No changes."], "answer": 1,
   "explain": "Positions 0, 1 and 2 now hold b, c and d, so three resources are renamed, and position 3 no longer exists, so it is destroyed. The destroyed object is the one that was d."},
  {"q": "Same change, but the resource uses `for_each = toset(var.names)`. What does the plan show?",
   "options": ["Plan: 0 to add, 0 to change, 1 to destroy.", "Plan: 0 to add, 3 to change, 1 to destroy.", "Plan: 3 to add, 0 to change, 3 to destroy.", "No changes."], "answer": 0,
   "explain": "Each resource is identified by its key. Only the key \"a\" disappeared, so only that resource is destroyed."},
  {"q": "With `count` over five servers where the differing attribute forces replacement, the first list element is removed. How many servers are destroyed?",
   "options": ["1", "4", "5", "0"], "answer": 2,
   "explain": "Positions 0 to 3 each get a different value and are replaced (4 destroys plus 4 creates), and position 4 is destroyed outright: five destroys and four creates."},
  {"q": "What is the address of the copy created for key `uploads` in `resource \"aws_s3_bucket\" \"this\" { for_each = var.buckets }`?",
   "options": ["`aws_s3_bucket.this[uploads]`", "`aws_s3_bucket.this.uploads`", "`aws_s3_bucket.this[\"uploads\"]`", "`aws_s3_bucket.uploads`"], "answer": 2,
   "explain": "for_each instances are addressed with the key as a quoted string in square brackets."},
  {"q": "`for_each = [\"a\", \"b\"]` is written directly with a list. What happens?",
   "options": ["Two resources keyed 0 and 1", "An error: for_each needs a map or a set of strings", "One resource", "Two resources keyed a and b"], "answer": 1,
   "explain": "Lists are rejected because they are positional. Convert with `toset([...])`."},
  {"q": "`for_each = toset(aws_instance.web[*].id)` where the instances are created in the same apply. What is the result?",
   "options": ["It works; Terraform waits for the IDs", "An 'Invalid for_each argument' error because the keys are not known until apply", "The resource is skipped", "Keys default to indexes"], "answer": 1,
   "explain": "Terraform must know every instance address during planning. IDs assigned at creation are unknown then, so they cannot be keys."},
  {"q": "You switch a resource from count to for_each without moved blocks. Three instances exist. What does the plan show?",
   "options": ["Three moves and no changes", "Plan: 3 to add, 0 to change, 3 to destroy.", "No changes", "Plan: 0 to add, 3 to change, 0 to destroy."], "answer": 1,
   "explain": "The addresses `[0]`, `[1]`, `[2]` are in state but not in configuration, and the keyed addresses are new, so all three are destroyed and recreated."},
  {"q": "Which expression returns a list of ARNs from a resource that uses for_each?",
   "options": ["`aws_iam_user.staff[*].arn`", "`values(aws_iam_user.staff)[*].arn`", "`aws_iam_user.staff.arn`", "`aws_iam_user.staff[0].arn`"], "answer": 1,
   "explain": "A for_each resource is a map. `values()` turns its values into a list, on which the splat then works."}
]
```

> **Source:** Brikman, Terraform: Up & Running 3e, ch. 5 (loops with the count parameter, loops with for_each expressions, count and for_each limitations). Documentation: https://developer.hashicorp.com/terraform/language/meta-arguments/count, https://developer.hashicorp.com/terraform/language/meta-arguments/for_each and https://developer.hashicorp.com/terraform/language/expressions/dynamic-blocks
