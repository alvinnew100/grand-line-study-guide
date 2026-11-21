# Installing Terraform, signing in safely and creating a first resource

## In plain words

Learning Terraform by reading is like learning to drive by reading. At some point you have to sit in the car. This lesson is the first drive, in an empty car park: you install the tool, give it permission to act in a cloud account in a way that cannot leak your keys, create one tiny server, look at it, and remove it again.

The everyday analogy for the permission part is a hotel key card. You do not hand a contractor the master key to the building. You issue a card that opens only the rooms they need, that expires, and that you can cancel. Giving Terraform access to your cloud account should work the same way.

Why this matters for a job: the four commands in this lesson (`init`, `plan`, `apply`, `destroy`) are the whole daily loop, and the most damaging beginner mistake in the industry, pasting cloud keys into a file and publishing it, is avoided by one habit you will form here.

> **Before this lesson:** read [How Terraform works, and how it compares with the alternatives](#/lesson/terraform/how-terraform-works). You need an AWS account set up the careful way described in [A safe first account: root user, MFA, budgets and the free tier](#/lesson/aws/account-and-billing), and you should know what an EC2 instance is from [EC2 instances, instance types, AMIs and user data](#/lesson/aws/ec2-instances). You should be able to open a terminal and change folders; the Linux command line track covers that.

> [!WARNING]
> **Cost and safety.** This lesson creates a real virtual server. With a small instance type it costs a fraction of a cent per hour and is often covered by the AWS free tier, but only if you remove it. Before you start: set a billing budget alert in your account, use a personal or sandbox account and never your employer's production account, and finish the lesson by running `terraform destroy`. A forgotten server bills you every hour until it is deleted.

## Step 1: install the program

Terraform is one executable file. Install it with your operating system's package manager, which is a tool that downloads and updates software for you.

```bash
# macOS, using Homebrew
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Windows, using winget
winget install HashiCorp.Terraform

# Ubuntu or Debian: add HashiCorp's package repository first (see the install page), then
sudo apt-get install terraform

# Check it worked
terraform version
```

- `brew tap hashicorp/tap` tells Homebrew where HashiCorp publishes its packages; `brew install ...` downloads the program.
- `winget install HashiCorp.Terraform` does the same on Windows.
- `terraform version` prints the installed version, for example `Terraform v1.13.4`. If the terminal answers "command not found", the folder containing the program is not on your **PATH**, the list of folders the terminal searches for programs.

To use OpenTofu instead, install the `tofu` package the same way and type `tofu` wherever this track types `terraform`.

> [!TIP]
> Teams pin an exact Terraform version so everyone gets identical behaviour. A small helper called `tfenv` (or `tenv`, which also handles OpenTofu) reads a file named `.terraform-version` in the project and switches to that version automatically.

## Step 2: give Terraform permission, safely

Terraform acts on your behalf, so it needs **credentials**: proof of identity that the cloud accepts. On AWS the classic form is an **access key**, a pair of values (an access key ID and a secret access key) that work like a username and password for programs.

Start with the rule, then the reasons.

**Never write credentials in a `.tf` file.** Configuration files go into version control, version control gets shared, and automated scanners find leaked cloud keys on public code sites within minutes. People have received bills of thousands of dollars from strangers mining cryptocurrency on a leaked key.

The AWS provider looks for credentials in several places outside your code. From most to least preferable for a learner:

1. **Short-lived credentials from single sign-on.** If your account uses IAM Identity Center, run `aws sso login --profile sandbox`. This gives temporary credentials that expire after a few hours.
2. **A named profile.** The AWS command-line tool stores keys in a file in your home folder, outside any project. Run `aws configure --profile sandbox` once and paste the keys when asked.
3. **Environment variables.** An environment variable is a named value held by your terminal session and visible to programs started from it.

```bash
# Option 2 or 1: tell tools which profile to use for this terminal session
export AWS_PROFILE=sandbox

# Option 3: keys as environment variables (they vanish when the terminal closes)
export AWS_ACCESS_KEY_ID="AKIA................"
export AWS_SECRET_ACCESS_KEY="........................................"

# Confirm who you are before running anything else
aws sts get-caller-identity
```

- `export NAME=value` sets an environment variable in Bash or zsh. On Windows PowerShell the equivalent is `$env:AWS_PROFILE = "sandbox"`.
- `aws sts get-caller-identity` asks AWS "who am I?" and prints the account number and identity. Run it every time before applying; it is the cheapest protection against deploying into the wrong account.

Two more safety rules belong here:

- **Do not use the root user.** The root user is the all-powerful identity created with the account. Create a separate identity for daily work, as the AWS account lesson describes.
- **Least privilege.** Give the identity only the permissions the task needs. For this lesson that is permission to manage EC2 instances. An administrator-level key that leaks is a disaster; a narrow one is an inconvenience.

In automated pipelines there is an even better method called OIDC, where no long-lived key exists at all. The secrets module covers it.

## Step 3: write the configuration

Create an empty folder and, inside it, a file named `main.tf`. Terraform reads every file ending in `.tf` in the current folder and treats them as one configuration; the file name itself has no special meaning.

```hcl
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "eu-west-1"
}

resource "aws_instance" "sandbox" {
  ami           = "ami-0abc1234def567890" # replace with a current AMI for your Region
  instance_type = "t3.micro"

  tags = {
    Name  = "tf-first-server"
    Owner = "learner"
  }
}
```

The general shape of HCL first. A **block** has a type, zero or more quoted **labels**, and a body in curly braces. Inside the body, an **argument** is a `name = value` line. The `#` character starts a comment that Terraform ignores.

Now each block:

- `terraform { ... }` configures Terraform itself.
  - `required_version = ">= 1.6.0"` refuses to run with an older Terraform, which protects teammates from confusing errors.
  - `required_providers` names the plug-ins needed. `source` is the registry address in the form `namespace/name`, and `version = "~> 6.0"` accepts any 6.x version but not 7.0.
- `provider "aws" { region = "eu-west-1" }` configures the AWS plug-in. There are no keys here: the provider finds them through the profile or environment variables from step 2.
- `resource "aws_instance" "sandbox" { ... }` declares one EC2 instance. The first label, `aws_instance`, is the **resource type** and is defined by the provider. The second label, `sandbox`, is a **local name** you invent. Together they form the resource's **address**, `aws_instance.sandbox`, which is how the rest of your code and the command line refer to it.
  - `ami` is the machine image to boot from. AMI identifiers differ per Region and change as new images are published, so the value above is a placeholder. A later lesson replaces it with an automatic lookup.
  - `instance_type` is the size. `t3.micro` is small and cheap.
  - `tags` is a **map**: a set of key and value pairs inside braces. Tags are labels attached to the cloud object. The `Name` tag is what the AWS console shows in its Name column.

Before running anything, add a file named `.gitignore` so that local and sensitive files never reach version control:

```bash
# .gitignore
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
crash.log
```

`.terraform/` holds downloaded plug-ins, `*.tfstate` files hold state (which can contain secrets), and `*.tfvars` files often hold environment-specific values. The file `.terraform.lock.hcl`, which appears in the next step, is deliberately *not* ignored.

## Step 4: `terraform init`

```bash
$ terraform init

Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 6.0"...
- Installing hashicorp/aws v6.4.0...
- Installed hashicorp/aws v6.4.0 (signed by HashiCorp)

Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository.

Terraform has been successfully initialized!
```

What happened:

- "Initializing the backend" sets up where state will be stored. With no setting it is a file in this folder; the state module changes that.
- The provider was downloaded into `.terraform/`. That folder can be hundreds of megabytes and is never committed.
- A **dependency lock file**, `.terraform.lock.hcl`, was written. It records the exact provider version chosen and checksums of its files, so that a colleague or a pipeline installs the identical plug-in. Commit it. To move to a newer provider on purpose, run `terraform init -upgrade`.

`init` is safe to run as often as you like. It never changes infrastructure.

Two more harmless commands are worth making a habit:

```bash
terraform fmt        # rewrites files into the standard layout
terraform validate   # checks syntax and internal consistency without contacting the cloud
```

## Step 5: `terraform plan`

```bash
$ terraform plan

Terraform used the selected providers to generate the following execution plan.
Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # aws_instance.sandbox will be created
  + resource "aws_instance" "sandbox" {
      + ami                    = "ami-0abc1234def567890"
      + arn                    = (known after apply)
      + id                     = (known after apply)
      + instance_type          = "t3.micro"
      + private_ip             = (known after apply)
      + public_ip              = (known after apply)
      + tags                   = {
          + "Name"  = "tf-first-server"
          + "Owner" = "learner"
        }
      # (many more attributes hidden here)
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```

Reading it from the top:

- The legend lists the symbols used in this plan. Only `+ create` appears.
- The comment line `# aws_instance.sandbox will be created` names the resource by its address and states the action in words.
- Every attribute has a `+`. The ones you wrote show their values. The ones AWS will assign show `(known after apply)`.
- The summary is `1 to add`.

Nothing has been created. `plan` only reads.

## Step 6: `terraform apply`

```bash
$ terraform apply
...
Plan: 1 to add, 0 to change, 0 to destroy.

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

aws_instance.sandbox: Creating...
aws_instance.sandbox: Still creating... [10s elapsed]
aws_instance.sandbox: Creation complete after 14s [id=i-0f3a9c1e27b4d5a60]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
```

`apply` computes a fresh plan, shows it, and waits. Only the full word `yes` continues. Then the provider calls AWS, waits for the server to exist, and Terraform records the result. The value in square brackets is the real instance ID.

Look in the AWS console under EC2 and you will find a server named `tf-first-server`. Look in your folder and you will find a new file, `terraform.tfstate`. It is the record that ties the address `aws_instance.sandbox` to instance `i-0f3a9c1e27b4d5a60`. You can inspect it safely with:

```bash
terraform state list                      # every address Terraform manages
terraform show                            # all recorded attributes, human-readable
```

Do not open the state file and edit it by hand. The state module explains why.

## Step 7: change something

Edit the tags in `main.tf`:

```hcl
  tags = {
    Name  = "tf-first-server"
    Owner = "learner"
    Stage = "sandbox"
  }
```

```bash
$ terraform plan

aws_instance.sandbox: Refreshing state... [id=i-0f3a9c1e27b4d5a60]

  # aws_instance.sandbox will be updated in-place
  ~ resource "aws_instance" "sandbox" {
        id            = "i-0f3a9c1e27b4d5a60"
      ~ tags          = {
            "Name"  = "tf-first-server"
            "Owner" = "learner"
          + "Stage" = "sandbox"
        }
        # (30 unchanged attributes hidden)
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```

- "Refreshing state" means Terraform asked AWS for the server's current settings before comparing. That is how it would notice a manual change.
- `~` marks an **update in place**: the same server, edited while it runs. Tags can be changed on a live instance.
- Inside the map, the single `+` shows the one new tag.

Now imagine you changed `ami` instead. The plan would read `# aws_instance.sandbox must be replaced`, show `-/+` next to the resource and `# forces replacement` next to the `ami` line, and the summary would be `1 to add, 0 to change, 1 to destroy`. The image of a running server cannot be swapped, so the only way to honour the new value is a new server. Any data on the old server's disk would be gone.

Apply the tag change with `terraform apply` and confirm in the console.

## Step 8: `terraform destroy`

```bash
$ terraform destroy

  # aws_instance.sandbox will be destroyed
  - resource "aws_instance" "sandbox" {
      - ami           = "ami-0abc1234def567890" -> null
      - id            = "i-0f3a9c1e27b4d5a60" -> null
      - instance_type = "t3.micro" -> null
      # ...
    }

Plan: 0 to add, 0 to change, 1 to destroy.

Do you really want to destroy all resources?
  Enter a value: yes

aws_instance.sandbox: Destroying... [id=i-0f3a9c1e27b4d5a60]
aws_instance.sandbox: Destruction complete after 40s

Destroy complete! Resources: 1 destroyed.
```

- Every attribute shows `- value -> null`: it has a value now and will have none.
- `destroy` removes **everything** the configuration in this folder manages. There is no undo.

> [!WARNING]
> `terraform destroy` is appropriate for sandboxes and almost never for production. To remove one thing from a real system, delete its block from the code and run a normal `plan` and `apply`, so the removal is reviewed like any other change. Check `aws sts get-caller-identity` and the folder you are in before every destroy.

## Saved plans

Between `plan` and `apply` the world can change: a colleague may apply something, or a file may be edited. To guarantee that what you reviewed is what runs, save the plan to a file and apply that file.

```bash
terraform plan -out=tfplan      # write the plan to a file named tfplan
terraform show tfplan           # read it again, in human form
terraform apply tfplan          # apply exactly that plan; no question is asked
```

- `-out=tfplan` stores the plan in a binary file.
- `terraform apply tfplan` skips the confirmation because the file *is* the approved plan. If state has changed since the plan was made, Terraform refuses with a "saved plan is stale" error.

Pipelines always work this way: one step produces the plan for a human to approve, and a later step applies that exact file. Treat plan files as sensitive, because they can contain secret values in plain text. Add `tfplan` to `.gitignore`.

## What lives in the folder

| Item | What it is | Commit to Git? |
|---|---|---|
| `main.tf` and other `.tf` files | Your configuration | Yes |
| `.terraform.lock.hcl` | Exact provider versions and checksums | Yes |
| `.terraform/` | Downloaded providers and modules | No |
| `terraform.tfstate` | State: the record of real objects | No (move it to a remote backend) |
| `terraform.tfstate.backup` | Previous copy of state | No |
| `tfplan` | A saved plan | No |

## Pitfalls

- **Keys in code.** `access_key = "AKIA..."` inside a provider block is the classic leak. Use profiles, environment variables or single sign-on.
- **Wrong account or Region.** A stray `AWS_PROFILE` from yesterday's terminal sends today's apply somewhere unexpected. Check identity first.
- **Forgetting `init`.** After adding a provider or cloning a repository, other commands fail with "provider not installed" until you run it.
- **Deleting `terraform.tfstate`.** The server keeps running, but Terraform forgets it exists and will try to create a second one.
- **Ignoring the lock file.** If it is not committed, two people can get different provider versions and different plans from the same code.
- **Leaving the sandbox running.** Destroy at the end of every practice session.
- **Assuming `-auto-approve` is a convenience.** It skips the one moment a human reads the plan. Reserve it for pipelines that apply a saved, already reviewed plan.

## Cheat sheet

| Command | Purpose | Changes infrastructure? |
|---|---|---|
| `terraform version` | Show installed version | No |
| `terraform init` | Download providers, set up backend | No |
| `terraform fmt` | Standardise formatting | No |
| `terraform validate` | Check the configuration is well formed | No |
| `terraform plan` | Preview changes | No |
| `terraform plan -out=tfplan` | Preview and save | No |
| `terraform apply` | Preview, confirm, change | Yes |
| `terraform apply tfplan` | Apply a saved plan | Yes |
| `terraform show` | Print state or a saved plan | No |
| `terraform state list` | List managed addresses | No |
| `terraform destroy` | Remove everything in this configuration | Yes |

## Summary

- Terraform is one executable; pin its version for a team.
- Credentials stay outside the code: profiles, environment variables or single sign-on, with least privilege and never the root user.
- A resource block has a type, a local name and arguments; type and name form its address.
- `init` downloads providers and writes a lock file to commit; `plan` previews; `apply` asks and then acts; `destroy` removes everything.
- In a plan, `+` creates, `~` updates in place, `-` destroys and `-/+` replaces.
- A saved plan file guarantees that what was reviewed is what is applied.

## Glossary

- **Terminal:** the text window where commands are typed.
- **PATH:** the list of folders searched when you type a program name.
- **Credentials:** proof of identity accepted by the cloud.
- **Access key:** an ID and secret pair used by programs to sign in to AWS.
- **Environment variable:** a named value held by a terminal session.
- **Profile:** a named set of credentials stored by the AWS command-line tool outside your project.
- **Least privilege:** granting only the permissions a task needs.
- **Block, label, argument:** the three building pieces of HCL syntax.
- **Resource type / local name / address:** what kind of object, your nickname for it, and the two joined with a dot.
- **Map:** a set of key and value pairs in braces.
- **Tag:** a label attached to a cloud object.
- **Dependency lock file:** the file recording exact provider versions.
- **Update in place:** changing a live object without recreating it.
- **Saved plan:** a plan stored in a file so it can be applied exactly as reviewed.

## Check yourself

```quiz
[
  {"q": "Where should AWS credentials for Terraform be kept?",
   "options": ["In the provider block of main.tf", "In a variables file committed to Git", "Outside the code: a profile, environment variables or single sign-on", "In the state file"], "answer": 2,
   "explain": "Anything in a .tf file ends up in version control. The AWS provider reads credentials from profiles, environment variables and SSO sessions without any being written in code."},
  {"q": "You add one new tag to an existing EC2 instance and run `terraform plan`. Which summary do you expect?",
   "options": ["Plan: 1 to add, 0 to change, 0 to destroy.", "Plan: 0 to add, 1 to change, 0 to destroy.", "Plan: 1 to add, 0 to change, 1 to destroy.", "No changes."], "answer": 1,
   "explain": "Tags can be edited on a running instance, so the resource is updated in place and counted under 'to change'."},
  {"q": "Which file should be committed to version control?",
   "options": ["terraform.tfstate", ".terraform.lock.hcl", "The .terraform folder", "tfplan"], "answer": 1,
   "explain": "The lock file pins exact provider versions for everyone. State, the plug-in folder and saved plans stay out of Git."},
  {"q": "A plan shows the line `# aws_instance.sandbox must be replaced` with `-/+`. What will apply do?",
   "options": ["Restart the server", "Edit the server while it runs", "Destroy the server and create a new one", "Nothing until init is run"], "answer": 2,
   "explain": "`-/+` is a replacement: the old object is destroyed and a new one created, because an attribute that cannot be changed in place was modified."},
  {"q": "What does `terraform apply tfplan` do differently from `terraform apply`?",
   "options": ["It applies the saved plan exactly and does not ask for confirmation", "It only validates syntax", "It destroys resources first", "It ignores the state file"], "answer": 0,
   "explain": "Applying a saved plan file runs precisely what was reviewed. If state changed since the plan was made, Terraform rejects the file as stale."},
  {"q": "You delete terraform.tfstate by accident while the server is still running, then run `terraform plan`. What does it show?",
   "options": ["No changes", "1 to destroy", "1 to add", "An error naming the server"], "answer": 2,
   "explain": "Without state Terraform has no record of the server, so the resource looks new and it plans to create another one. The original keeps running and keeps billing."},
  {"q": "Which command is safe to run at any time because it never contacts the cloud to change anything and only downloads plug-ins?",
   "options": ["terraform apply -auto-approve", "terraform destroy", "terraform init", "terraform apply tfplan"], "answer": 2,
   "explain": "`init` prepares the working folder. It installs providers and modules and configures the backend, but never creates, changes or deletes infrastructure."}
]
```

> **Source:** Brikman, Terraform: Up & Running 3e, ch. 2 (setting up an account, installing Terraform, deploying a single server). Documentation: https://developer.hashicorp.com/terraform/install, https://developer.hashicorp.com/terraform/cli/commands/init, https://developer.hashicorp.com/terraform/language/files/dependency-lock and https://registry.terraform.io/providers/hashicorp/aws/latest/docs
