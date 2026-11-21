# For expressions, string directives and conditionals

## In plain words

A mail-merge takes a spreadsheet of customers and produces a stack of letters. Three small abilities make it useful. It can *transform* each row ("write the surname in capitals"). It can *filter* rows ("only customers in Dublin"). And it can make parts of the letter *conditional* ("if the customer is a member, add the discount paragraph").

Terraform's language has the same three abilities for values:

- a **`for` expression** transforms and filters a list or map into a new list or map;
- **string directives** put loops and if-statements inside a piece of text;
- **conditionals** choose between two values, and, combined with `count` or `for_each`, decide whether a resource exists at all.

The previous lesson's `count` and `for_each` decide *how many resources* exist. The tools in this lesson work on *values*.

Why this matters for a job: real modules are full of these expressions, usually on one dense line. Being able to read `{ for k, v in var.x : k => v.id if v.enabled }` at a glance is the difference between reviewing a change and nodding at it. "How do you create a resource conditionally?" is a standard interview question.

> **Before this lesson:** complete [Loops: count, for_each and the index-shifting trap](#/lesson/terraform/loops-count-for-each). You should know lists, maps, sets and how `count` and `for_each` address their copies.

## A place to experiment: `terraform console`

Everything in this lesson is an expression, and expressions can be tried without creating anything. `terraform console` opens an interactive prompt that evaluates whatever you type:

```bash
$ terraform console
> upper("harbour")
"HARBOUR"
> length(["a", "b", "c"])
3
> 2 + 3 * 4
14
> exit
```

It reads the variables and state of the current folder, so `var.names` works if the folder declares it. It never changes infrastructure. Use it alongside this lesson.

## `for` expressions on lists

The basic form produces a new **list**:

```hcl
[for <item> in <collection> : <result>]
```

```hcl
variable "names" {
  type    = list(string)
  default = ["asha", "ben", "chidi"]
}

output "shouted" {
  value = [for n in var.names : upper(n)]
}
```

- The square brackets say the result is a list.
- `for n in var.names` visits each element, calling it `n`.
- After the colon comes the expression computed for each element. `upper()` converts text to capitals.
- The result is `["ASHA", "BEN", "CHIDI"]`.

Add an `if` clause at the end to **filter**:

```hcl
output "short_names" {
  value = [for n in var.names : upper(n) if length(n) < 5]
}
```

Only elements for which the condition is true are kept. Here `length(n)` is the number of characters, so the result is `["ASHA", "BEN"]`.

When you need the position as well, name two variables. The first receives the index:

```hcl
output "numbered" {
  value = [for i, n in var.names : "${i + 1}. ${n}"]
}
```

The result is `["1. asha", "2. ben", "3. chidi"]`.

## `for` expressions on maps

Looping over a map gives a key and a value:

```hcl
variable "teams" {
  type = map(string)
  default = {
    asha  = "finance"
    ben   = "web"
    chidi = "web"
  }
}

output "sentences" {
  value = [for person, team in var.teams : "${person} works in ${team}"]
}
```

The result is a list of three strings. Maps are visited in alphabetical order of their keys, so the output order is predictable.

To produce a **map** instead of a list, use curly braces and the arrow `=>` between key and value:

```hcl
{for <item> in <collection> : <key> => <value>}
```

```hcl
output "upper_teams" {
  value = { for person, team in var.teams : person => upper(team) }
}
```

The result is `{ asha = "FINANCE", ben = "WEB", chidi = "WEB" }`.

Two things can go wrong when building a map:

- **Duplicate keys are an error.** If you invert the map above, making the team the key, "web" appears twice and Terraform stops with "Duplicate object key".
- To collect duplicates into lists, add three dots after the value. This is **grouping mode**:

```hcl
output "people_by_team" {
  value = { for person, team in var.teams : team => person... }
}
```

The result is `{ finance = ["asha"], web = ["ben", "chidi"] }`.

### The pattern you will use most

`for_each` wants a map, but inputs often arrive as a list of objects. A `for` expression converts one into the other by choosing a key:

```hcl
variable "queues" {
  type = list(object({
    name      = string
    retention = number
    enabled   = bool
  }))
  default = [
    { name = "orders", retention = 86400, enabled = true },
    { name = "emails", retention = 3600, enabled = true },
    { name = "legacy", retention = 3600, enabled = false },
  ]
}

resource "aws_sqs_queue" "this" {
  for_each = { for q in var.queues : q.name => q if q.enabled }

  name                      = "harbour-${each.key}"
  message_retention_seconds = each.value.retention
}
```

- The expression builds a map keyed by each queue's `name`, keeping only enabled ones.
- The resource then has stable addresses, `aws_sqs_queue.this["orders"]` and `aws_sqs_queue.this["emails"]`, and the disabled queue is not created.

An SQS queue is a managed message queue; see [SQS and SNS: queues, topics and fan-out](#/lesson/aws/messaging).

The simulation mirrors these forms in Python so you can compare the syntax side by side and check your predictions.

```python-run
names = ["asha", "ben", "chidi"]
teams = {"asha": "finance", "ben": "web", "chidi": "web"}
queues = [
    {"name": "orders", "retention": 86400, "enabled": True},
    {"name": "emails", "retention": 3600,  "enabled": True},
    {"name": "legacy", "retention": 3600,  "enabled": False},
]

# [for n in var.names : upper(n) if length(n) < 5]
print([n.upper() for n in names if len(n) < 5])

# [for i, n in var.names : "${i + 1}. ${n}"]
print([f"{i + 1}. {n}" for i, n in enumerate(names)])

# { for person, team in var.teams : person => upper(team) }   (maps iterate in key order)
print({person: team.upper() for person, team in sorted(teams.items())})

# { for person, team in var.teams : team => person... }        (grouping mode)
grouped = {}
for person, team in sorted(teams.items()):
    grouped.setdefault(team, []).append(person)
print(grouped)

# { for q in var.queues : q.name => q if q.enabled }
print(sorted({q["name"]: q for q in queues if q["enabled"]}))

# Duplicate keys without grouping are an error in Terraform:
inverted = {}
for person, team in sorted(teams.items()):
    if team in inverted:
        print(f'Error: Duplicate object key "{team}" (use ... to group)')
        break
    inverted[team] = person
```

## String directives

Interpolation, `${ ... }`, inserts one value into a string. A **string directive**, written `%{ ... }`, adds control flow inside a string: a loop or an if-statement. Directives are mainly used in heredocs and in template files, where you are generating a configuration file or a script.

### The `for` directive

```hcl
variable "upstreams" {
  type    = list(string)
  default = ["10.0.1.10", "10.0.2.10", "10.0.3.10"]
}

output "upstream_block" {
  value = <<-EOT
    upstream bookshelf {
    %{ for ip in var.upstreams ~}
      server ${ip}:8080;
    %{ endfor ~}
    }
  EOT
}
```

- `%{ for ip in var.upstreams }` starts a loop and `%{ endfor }` ends it. The lines between are repeated once per element.
- `${ip}` inside the loop is ordinary interpolation.
- The `~` immediately inside a closing brace is a **strip marker**. It removes the whitespace and line break that follow the directive. Without it, each directive line would leave an empty line in the output. A `~` immediately inside an opening brace, `%{~`, strips whitespace before the directive instead.

The result:

```bash
upstream bookshelf {
  server 10.0.1.10:8080;
  server 10.0.2.10:8080;
  server 10.0.3.10:8080;
}
```

### The `if` directive

```hcl
variable "motto" {
  type    = string
  default = ""
}

output "banner" {
  value = "Harbour Books%{ if var.motto != "" }: ${var.motto}%{ else } (no motto set)%{ endif }"
}
```

- `%{ if condition }` ... `%{ else }` ... `%{ endif }` includes one piece of text or the other. The `else` part is optional.
- With the default, the output is `Harbour Books (no motto set)`. With `motto = "read more"`, it is `Harbour Books: read more`.

A common use is printing a comma between items but not after the last one:

```hcl
output "csv" {
  value = "%{ for i, n in var.names }${n}%{ if i < length(var.names) - 1 }, %{ endif }%{ endfor }"
}
```

The result is `asha, ben, chidi`. For this particular job the built-in function `join(", ", var.names)` is shorter; directives earn their place when each item needs several lines.

## Conditional expressions

The **conditional expression** picks one of two values:

```hcl
<condition> ? <value if true> : <value if false>
```

```hcl
variable "environment" {
  type = string
}

locals {
  instance_type = var.environment == "prod" ? "t3.large" : "t3.micro"
  min_size      = var.environment == "prod" ? 3 : 1
}
```

- `==` tests equality and `!=` inequality. Other operators are `<`, `>`, `<=`, `>=`, and the logical `&&` (and), `||` (or) and `!` (not).
- Both result values should be of the same type.

When there are more than two cases, a map lookup reads better than nested conditionals:

```hcl
locals {
  sizes = {
    dev     = "t3.micro"
    staging = "t3.small"
    prod    = "t3.large"
  }
  instance_type = lookup(local.sizes, var.environment, "t3.micro")
}
```

`lookup(map, key, default)` returns the value for the key, or the default if the key is missing.

## Conditional resources

HCL has no `if` statement around a resource block. The idiom is to set how many copies exist: one or zero.

### With `count`

```hcl
variable "enable_alarm" {
  description = "Create a high-CPU alarm for the fleet"
  type        = bool
  default     = false
}

resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  count = var.enable_alarm ? 1 : 0

  alarm_name          = "${var.name}-cpu-high"
  namespace           = "AWS/EC2"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  comparison_operator = "GreaterThanThreshold"
  threshold           = 80
  period              = 300
  evaluation_periods  = 2

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.web.name
  }
}
```

- `count = var.enable_alarm ? 1 : 0` creates one alarm when the flag is true and none when it is false.
- The other arguments describe an alarm that fires when average processor use across the group exceeds 80 percent for two periods of 300 seconds. CloudWatch is AWS's monitoring service; see [CloudWatch metrics, logs and alarms](#/lesson/aws/cloudwatch).

This is the legitimate home for `count`: with only positions 0 and "absent", there is nothing to shift.

Because the resource is now a list of zero or one elements, references need care. `aws_cloudwatch_metric_alarm.cpu_high.arn` is an error. Two safe forms:

```hcl
output "alarm_arn" {
  value = var.enable_alarm ? aws_cloudwatch_metric_alarm.cpu_high[0].arn : null
}

output "alarm_arn_short" {
  value = one(aws_cloudwatch_metric_alarm.cpu_high[*].arn)
}
```

- The first guards the `[0]` with the same condition. `null` is Terraform's "no value"; an argument set to `null` behaves as if it were omitted.
- The second uses `one(list)`, which returns the single element of a one-element list and `null` for an empty list.

### If-else between two resources

To create one of two alternatives, give them opposite conditions:

```hcl
resource "aws_iam_user_policy_attachment" "full" {
  count      = var.give_full_access ? 1 : 0
  user       = aws_iam_user.auditor.name
  policy_arn = aws_iam_policy.full_access.arn
}

resource "aws_iam_user_policy_attachment" "read_only" {
  count      = var.give_full_access ? 0 : 1
  user       = aws_iam_user.auditor.name
  policy_arn = aws_iam_policy.read_only.arn
}
```

Exactly one of the two attachments exists. To output "whichever one was created", concatenate both lists and take the single element:

```hcl
output "attached_policy" {
  value = one(concat(
    aws_iam_user_policy_attachment.full[*].policy_arn,
    aws_iam_user_policy_attachment.read_only[*].policy_arn,
  ))
}
```

`concat(list_a, list_b)` joins lists end to end.

### With `for_each`

A conditional can also select the collection for `for_each`. An empty map or set means zero copies:

```hcl
resource "aws_autoscaling_schedule" "this" {
  for_each = var.enable_schedules ? var.schedules : {}

  scheduled_action_name  = each.key
  autoscaling_group_name = aws_autoscaling_group.web.name
  recurrence             = each.value.cron
  min_size               = each.value.size
  max_size               = each.value.size
  desired_capacity       = each.value.size
}
```

And a filter inside a `for` expression makes individual elements conditional, as in the queues example earlier.

### Conditional nested blocks

For an optional nested block, combine `dynamic` with a list that is empty or has one element:

```hcl
  dynamic "access_logs" {
    for_each = var.log_bucket == null ? [] : [var.log_bucket]

    content {
      bucket  = access_logs.value
      enabled = true
    }
  }
```

If `var.log_bucket` is `null`, the list is empty and no block is generated.

## What plans look like with conditionals

Flipping `enable_alarm` from false to true:

```bash
$ terraform plan -var="enable_alarm=true"

  # aws_cloudwatch_metric_alarm.cpu_high[0] will be created
  + resource "aws_cloudwatch_metric_alarm" "cpu_high" {
      + alarm_name = "bookshelf-dev-cpu-high"
      + threshold  = 80
      ...
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```

Note the `[0]` in the address. Flipping it back plans `1 to destroy`. Flipping `give_full_access` shows one attachment destroyed and the other created: `1 to add, 0 to change, 1 to destroy`.

> [!WARNING]
> **Safety.** A boolean that controls `count` is a destroy switch. Changing `create_database` from true to false in a variables file plans the deletion of the database and its data. Treat flag changes in review with the same care as deleting the resource block, and protect critical resources with `prevent_destroy`.

> [!TIP]
> Dense one-line expressions are hard to review. Give intermediate results names in a `locals` block, and check them in `terraform console` before using them in a resource.

## Pitfalls

- **Forgetting `[0]` after adding `count`.** Every reference to the resource must change.
- **Indexing `[0]` when the count may be zero.** The error is "Invalid index". Guard it or use `one()`.
- **Conditions that depend on unknown values.** `count = aws_instance.x.public_ip != "" ? 1 : 0` fails for the same reason as in the loops lesson: counts must be known at plan time.
- **Mismatched types in the two branches** of a conditional, such as a string and a list.
- **Using a list `for` when a map was needed.** `[ ... ]` gives a list, `{ ... => ... }` gives a map.
- **Missing strip markers.** Templates fill with blank lines.
- **Comparing with a string instead of a bool.** `var.enabled == "true"` is false when `enabled` is the boolean `true`.
- **Nested conditionals three deep.** Use a map and `lookup`.

## Cheat sheet

| Goal | Syntax |
|---|---|
| Transform a list | `[for x in list : f(x)]` |
| Filter | `[for x in list : x if cond]` |
| Index and value | `[for i, x in list : ...]` |
| Loop over a map | `[for k, v in map : ...]` |
| Build a map | `{for x in list : key => value}` |
| Group duplicates | `{for k, v in map : v => k...}` |
| Loop in a string | `%{ for x in list ~} ... %{ endfor ~}` |
| If in a string | `%{ if cond } ... %{ else } ... %{ endif }` |
| Strip whitespace | `~` inside the brace |
| Choose a value | `cond ? a : b` |
| Optional resource | `count = cond ? 1 : 0` |
| Safe reference to it | `one(res[*].attr)` |
| Optional collection | `for_each = cond ? var.m : {}` |
| Optional nested block | `dynamic "b" { for_each = cond ? [1] : [] ... }` |
| Try expressions | `terraform console` |

## Summary

- `for` expressions transform and filter collections; square brackets produce a list, curly braces with `=>` produce a map, and `...` groups values with the same key.
- Converting a list of objects to a keyed map is the standard way to feed `for_each`.
- String directives `%{ for }` and `%{ if }` add loops and conditions inside strings; `~` strips surrounding whitespace.
- The conditional expression `cond ? a : b` chooses between values.
- A resource is made optional with `count = cond ? 1 : 0` or with an empty collection for `for_each`; references then need `[0]`, a guard or `one()`.
- A flag that controls a count controls destruction, so review flag changes carefully.

## Glossary

- **`for` expression:** an expression that builds a list or map from another collection.
- **Filter clause:** the `if` at the end of a `for` expression that keeps only matching elements.
- **Grouping mode:** the `...` suffix that collects values sharing a key into a list.
- **String directive:** `%{ ... }` control flow inside a string.
- **Strip marker:** `~`, which trims whitespace next to a directive or interpolation.
- **Conditional expression:** `condition ? a : b`.
- **`null`:** the absence of a value; an argument set to it is treated as omitted.
- **`one`:** a function returning the only element of a list, or `null` if it is empty.
- **`concat`:** a function joining lists.
- **`lookup`:** a function reading a map key with a fallback.
- **`terraform console`:** an interactive prompt for evaluating expressions.

## Check yourself

```quiz
[
  {"q": "What is the value of `[for n in [\"asha\", \"ben\", \"chidi\"] : upper(n) if length(n) > 3]`?",
   "options": ["`[\"ASHA\", \"BEN\", \"CHIDI\"]`", "`[\"ASHA\", \"CHIDI\"]`", "`[\"BEN\"]`", "`{ASHA = 4, CHIDI = 5}`"], "answer": 1,
   "explain": "The filter keeps names longer than three characters, and each kept name is converted to capitals. Square brackets give a list."},
  {"q": "`{ for p, t in {asha = \"web\", ben = \"web\"} : t => p }` evaluates to what?",
   "options": ["`{web = \"ben\"}`", "`{web = [\"asha\", \"ben\"]}`", "An error: duplicate object key", "`{asha = \"web\", ben = \"web\"}`"], "answer": 2,
   "explain": "Both elements produce the key `web`. Without the `...` grouping suffix, duplicate keys are an error."},
  {"q": "A resource has `count = var.enable_alarm ? 1 : 0` and exists. You set enable_alarm to false. What does the plan show?",
   "options": ["No changes", "Plan: 0 to add, 0 to change, 1 to destroy.", "Plan: 0 to add, 1 to change, 0 to destroy.", "An error"], "answer": 1,
   "explain": "The count goes from 1 to 0, so index [0] is out of range and that instance is destroyed."},
  {"q": "With that count expression, which reference is safe when the flag may be false?",
   "options": ["`aws_cloudwatch_metric_alarm.cpu_high.arn`", "`aws_cloudwatch_metric_alarm.cpu_high[0].arn`", "`one(aws_cloudwatch_metric_alarm.cpu_high[*].arn)`", "`aws_cloudwatch_metric_alarm.cpu_high[1].arn`"], "answer": 2,
   "explain": "The splat gives a list of zero or one ARNs, and `one()` returns the element or null. Plain `[0]` fails with 'Invalid index' when the count is zero."},
  {"q": "Two resources have `count = var.full ? 1 : 0` and `count = var.full ? 0 : 1`. Both variants were applied with full = false. You now set full = true. What is the plan summary?",
   "options": ["Plan: 1 to add, 0 to change, 0 to destroy.", "Plan: 1 to add, 0 to change, 1 to destroy.", "Plan: 2 to add, 0 to change, 0 to destroy.", "Plan: 0 to add, 1 to change, 0 to destroy."], "answer": 1,
   "explain": "The read-only variant goes from one copy to zero and the full variant from zero to one: one destroy and one create."},
  {"q": "In a heredoc, what does the `~` in `%{ endfor ~}` do?",
   "options": ["Negates the loop", "Removes the whitespace and newline after the directive", "Marks the string as sensitive", "Repeats the loop"], "answer": 1,
   "explain": "A strip marker trims adjacent whitespace, so directive lines do not leave blank lines in the output."},
  {"q": "`for_each = { for q in var.queues : q.name => q if q.enabled }` with three queues of which one is disabled. How many resources are planned in a fresh state?",
   "options": ["3", "2", "1", "0"], "answer": 1,
   "explain": "The filter removes the disabled queue, so the map has two entries and two resources are created."},
  {"q": "What does `var.environment == \"prod\" ? 3 : 1` return when environment is `staging`?",
   "options": ["3", "1", "null", "An error"], "answer": 1,
   "explain": "The condition is false, so the value after the colon is used."}
]
```

> **Source:** Brikman, Terraform: Up & Running 3e, ch. 5 (loops with for expressions, loops with the for string directive, conditionals with count, for_each and the if string directive). Documentation: https://developer.hashicorp.com/terraform/language/expressions/for, https://developer.hashicorp.com/terraform/language/expressions/strings#directives, https://developer.hashicorp.com/terraform/language/expressions/conditionals and https://developer.hashicorp.com/terraform/cli/commands/console
