# Secrets, part 1: the rules, the tools and authenticating providers

## In plain words

A bank does not write the vault combination on a sticky note by the door. It keeps the combination in a controlled place, gives it only to the people who need it, records who used it, and changes it regularly. The reasons are plain: a note can be photographed, copied and carried away, and once that happens nobody knows.

Software has its own combinations: database passwords, cloud access keys, tokens for third-party services. These are called **secrets**. Infrastructure code handles a great many of them, because infrastructure code is what creates the databases and connects the services. A secret typed into a Terraform file is the sticky note by the door.

This lesson gives you the rules for handling secrets, a map of the tools that store them, and the correct ways to hand Terraform the most powerful secret of all: the credentials that let it act in your cloud account. The next lesson covers secrets inside resources and the uncomfortable truth about state files.

Why this matters for a job: leaked credentials are among the most common causes of security breaches, and they are almost always leaked by accident through version control. Interviewers ask "how do you handle secrets in Terraform?" to check that you will not be the cause of one.

> **Before this lesson:** complete [Installing Terraform, signing in safely and creating a first resource](#/lesson/terraform/install-auth-first-resource) and [Terraform state, remote backends and locking](#/lesson/terraform/state-and-backends). From the AWS track, [IAM users, groups, roles and policies](#/lesson/aws/iam-identities) explains users, roles and policies, and [KMS, Secrets Manager and the detective and protective services](#/lesson/aws/security-services) introduces the services named here.

## The two rules

**Rule 1: never store a secret in plain text.** **Plain text** means readable by anyone who can open the file, with no decryption step. Here is what breaking the rule looks like:

```hcl
# DO NOT DO THIS
resource "aws_db_instance" "orders" {
  identifier = "orders"
  engine     = "postgres"
  username   = "admin"
  password   = "Tr0ub4dor&3"   # a secret in plain text, in version control
}
```

Why this is so damaging:

- **Everyone with access to the repository has the secret**, including every laptop that ever cloned it, every backup, and every tool the repository is connected to.
- **Version control never forgets.** Deleting the line in a later commit leaves the secret in the history. The only real fix after a leak is to change the secret itself.
- **You cannot audit or revoke.** There is no record of who read the file, and no way to take access back from one person.
- **Attackers scan for exactly this.** Automated programs search public code sites for strings shaped like cloud keys and use them within minutes.

**Rule 2: do not store secrets in plain text — and that includes places you do not think of as storage.** Shell history, chat messages, wiki pages, pipeline logs and, as the next lesson shows, Terraform state and plan files all count.

If a secret does leak, the response is always the same and the order matters: **revoke or rotate it first** (make the old value useless), then investigate, then clean up the history. Deleting the commit without rotating the secret achieves nothing, because you cannot know who already copied it.

## Kinds of secrets

It helps to sort secrets by who uses them, because the right storage differs:

| Kind | Examples | Used by |
|---|---|---|
| Personal secrets | Your own passwords, your SSH key | One human |
| Customer secrets | The passwords of your product's users | Your application, on behalf of customers |
| Infrastructure secrets | Database passwords, API keys, TLS certificates' private keys | Servers, pipelines and tools such as Terraform |

Customer passwords are a special case: they should not be stored in recoverable form at all. Applications store a **hash**, a one-way scramble from which the password cannot be recovered. That is an application topic, covered in the web security track. Terraform work is almost entirely about infrastructure secrets.

## How secrets are stored

Every storage method is one of two designs.

**File-based stores** keep secrets in an encrypted file that can live next to your code. Before use, the file is decrypted with a key. That raises the obvious question of where the key lives, and the answer is: in a **key management service** (KMS), a cloud service that holds encryption keys and performs encryption on request without ever handing the key out. AWS KMS, Google Cloud KMS and Azure Key Vault are examples. A popular tool for the encrypted-file approach is `sops`.

**Centralised secret stores** are services you call over the network to fetch a secret when it is needed. AWS Secrets Manager, Google Secret Manager, Azure Key Vault and HashiCorp Vault (and its open-source fork OpenBao) are examples. They add things a file cannot: per-secret access rules, a log of every read, and automatic **rotation**, which means replacing a secret with a fresh one on a schedule.

| | Encrypted file | Centralised secret store |
|---|---|---|
| Where the secret lives | In the repository, as ciphertext | In a service |
| Versioned and reviewed with code | Yes | No, separately |
| Audit log of each read | Limited to key usage | Yes |
| Rotation | Manual | Often automatic |
| Extra cost and infrastructure | Low | Some |
| Risk | Decrypted copies on laptops | A dependency on the service being reachable |

**Ciphertext** is the unreadable, encrypted form of data.

How secrets are *reached* also comes in two styles. Some stores have an **API**, used by programs. Others, such as password managers for people, have a user interface. For infrastructure secrets you want an API.

## A comparison of common tools

| Tool | Type | Typical use |
|---|---|---|
| A password manager (1Password, Bitwarden) | Centralised, for humans | Personal secrets, shared team logins |
| AWS Secrets Manager | Centralised service | Database passwords and API keys, with rotation |
| AWS Systems Manager Parameter Store | Centralised service | Configuration values and simpler secrets |
| HashiCorp Vault / OpenBao | Centralised, self-hosted or hosted | Multi-cloud secrets, short-lived dynamic credentials |
| `sops` with a KMS key | Encrypted files | Secrets versioned next to code |
| CI system secret settings (GitHub Actions secrets) | Centralised, per repository | Tokens the pipeline itself needs |

There is no single winner. Many teams use a cloud secret store for application and infrastructure secrets, a password manager for people, and as few pipeline secrets as possible.

## Secrets Terraform touches

Terraform meets secrets in three places:

1. **Providers.** Terraform needs credentials to call a cloud API. This lesson covers these.
2. **Resources and data sources.** Some arguments are secrets, such as a database password. Next lesson.
3. **State files and plan files.** Whatever passes through a resource is recorded. Next lesson.

## Provider authentication for people

You met the basic rule earlier: no keys in `.tf` files. This section gives the fuller picture for a human working on a laptop.

The weakest acceptable method is a long-lived access key stored by the AWS command-line tool in a file in your home folder. The key works for months or years, and the file is plain text. Anything that can read your home folder, including a malicious package installed by accident, can take it.

Better options, in rising order of safety:

- **Keep long-lived keys in an encrypted store.** The tool `aws-vault` keeps keys in your operating system's protected keychain and hands programs temporary credentials derived from them.

```bash
aws-vault add sandbox                   # prompts for the keys once and stores them encrypted
aws-vault exec sandbox -- terraform plan
```

  The second line runs `terraform plan` with temporary credentials placed in environment variables for that one command. The `--` separates aws-vault's own options from the command to run.

- **Use single sign-on and have no long-lived keys at all.** With AWS IAM Identity Center, you sign in through a browser and receive credentials that expire in hours.

```bash
aws sso login --profile sandbox
export AWS_PROFILE=sandbox
terraform plan
```

Whichever you use, the credentials reach Terraform through environment variables or a named profile, and the provider block stays free of secrets:

```hcl
provider "aws" {
  region = "eu-west-1"
}
```

## Provider authentication for machines

Most applies in a real team are run by an automated pipeline, not a person. A pipeline has no browser to sign in with, so the question is how a machine proves its identity. The answer depends on where the machine runs, and the goal in every case is the same: **no long-lived secret stored anywhere**.

### A server inside the cloud: IAM roles

An **IAM role** is an identity with permissions that is not tied to a password or key. Things *assume* a role and receive **temporary credentials**, valid for a short time and replaced automatically.

If Terraform runs on an EC2 server (a build machine in your account), attach a role to the server through an **instance profile**. AWS then makes temporary credentials available to programs on that server, and the provider picks them up with no configuration.

```hcl
data "aws_iam_policy_document" "assume_by_ec2" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "build_runner" {
  name_prefix        = "build-runner-"
  assume_role_policy = data.aws_iam_policy_document.assume_by_ec2.json
}

resource "aws_iam_instance_profile" "build_runner" {
  name_prefix = "build-runner-"
  role        = aws_iam_role.build_runner.name
}
```

- The `aws_iam_policy_document` data source builds a policy in JSON from HCL. This one is a **trust policy**: it states *who may assume the role*. Here the answer is the EC2 service.
- `aws_iam_role.build_runner` creates the role with that trust policy.
- `aws_iam_instance_profile` is the wrapper that lets a role be attached to a server. You would set `iam_instance_profile` on the instance or launch template, and attach a separate permissions policy to the role stating what it may do.

### A pipeline outside the cloud: OIDC

Hosted CI services such as GitHub Actions run on someone else's machines, so there is no instance profile. The old solution was to create an access key and paste it into the CI system's secret settings: a long-lived, powerful key stored at a third party.

The modern solution is **OIDC**, OpenID Connect. The idea in everyday terms: the CI system issues each job a signed identity document, like a stamped visitor badge saying "I am a job from repository X on branch Y". AWS is configured to trust badges from that issuer, checks the stamp and the details, and exchanges the badge for temporary credentials. No secret is stored anywhere.

```mermaid
sequenceDiagram
  participant J as CI job
  participant G as CI identity provider
  participant A as AWS STS
  J->>G: request identity token
  G-->>J: signed token, repo and branch inside
  J->>A: AssumeRoleWithWebIdentity with token
  A->>A: verify signature and conditions
  A-->>J: temporary credentials, about 1 hour
  J->>A: terraform plan and apply
```

The AWS side is three resources:

```hcl
resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

data "aws_iam_policy_document" "assume_by_github" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:harbour-books/infra-live:ref:refs/heads/main"]
    }
  }
}

resource "aws_iam_role" "terraform_apply" {
  name               = "terraform-apply"
  assume_role_policy = data.aws_iam_policy_document.assume_by_github.json
}
```

- `aws_iam_openid_connect_provider` tells the account to trust tokens issued by GitHub's token service.
- The trust policy allows the action `sts:AssumeRoleWithWebIdentity` for that provider, under two conditions.
- The first condition checks the token's audience (`aud`), confirming it was issued for AWS.
- The second checks the subject (`sub`): which repository and branch the job belongs to. This is the line that matters most. Without it, *any* repository on that CI service could assume your role. Here only jobs on the `main` branch of one repository qualify.

In the pipeline file, the job asks for a token and exchanges it. The CI/CD track's [A complete GitHub Actions pipeline, line by line](#/lesson/cicd/github-actions-workflow) explains workflow files in general.

```yaml
permissions:
  id-token: write
  contents: read

jobs:
  plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/terraform-apply
          aws-region: eu-west-1
      - uses: hashicorp/setup-terraform@v3
      - run: terraform init && terraform plan
```

- `id-token: write` lets the job request its identity token.
- The `configure-aws-credentials` step performs the exchange and places temporary credentials in environment variables for the following steps.
- No access key appears anywhere, in the file or in the CI system's settings.

### Least privilege for the role

Whatever the mechanism, decide what the role may do. A common pattern is two roles: a read-only one used for `plan` on every pull request, and a more powerful one used for `apply` only from the main branch after approval. If a pull request from a confused or malicious contributor runs with the plan role, the worst it can do is read.

> [!WARNING]
> **Safety.** The identity that runs Terraform can usually create identities and permissions, which makes it equivalent to an administrator. Protect the path to it as carefully as production itself: restrict which branches and repositories may assume the role, require review before apply, and never give a pull request from an untrusted fork access to the apply role.

## Catching leaks before they happen

People make mistakes, so add automatic nets:

- **`.gitignore`** for `*.tfvars`, `*.tfstate`, plan files and `.env` files.
- **A pre-commit secret scanner** such as `gitleaks` or `trufflehog`, which inspects each commit for strings that look like keys.
- **Push protection** on the code hosting service, which rejects pushes containing recognised key formats.

The simulation below is a tiny scanner of the kind those tools contain. It looks for two signs: values whose *shape* matches a known key format, and assignments to names that sound secret with a literal value.

```python-run
import re

PATTERNS = [
    ("AWS access key id",  re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private key block",  re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("hard-coded secret",  re.compile(r'(?i)\b(password|secret|token|api_key)\b\s*=\s*"([^"$]{6,})"')),
]

config = '''
provider "aws" {
  region     = "eu-west-1"
  access_key = "AKIAIOSFODNN7EXAMPLE"
}
resource "aws_db_instance" "orders" {
  username = "admin"
  password = "Tr0ub4dor&3"
}
resource "aws_db_instance" "billing" {
  username = "admin"
  password = var.db_password
}
variable "api_token" {
  default = "tok_live_9f8e7d6c5b"
}
output "note" { value = "password = ${var.db_password}" }
'''

for n, line in enumerate(config.strip().splitlines(), 1):
    for label, rx in PATTERNS:
        if rx.search(line):
            print(f"line {n:>2}: {label:18} | {line.strip()[:48]}")
```

Notice what is *not* flagged: `password = var.db_password` is a reference, not a literal. Notice also what is missed: the `api_token` default hides its secret under the argument name `default`, so the name-based rule cannot see it. Real scanners add many more patterns and entropy checks, and still miss things. Scanners are a net, not a substitute for the rules.

> [!INTERVIEW]
> "How does your pipeline authenticate to AWS?" The strong answer is OIDC federation: the CI job obtains a signed identity token, AWS exchanges it for short-lived credentials through a role whose trust policy is restricted to a specific repository and branch, and no long-lived key is stored. Add separate plan and apply roles with least privilege.

## Pitfalls

- **`access_key` and `secret_key` in a provider block.** The original sin.
- **Deleting a leaked secret from the latest commit and stopping there.** Rotate first; history still has it.
- **Long-lived keys in CI secret settings** when OIDC is available.
- **An OIDC trust policy without a `sub` condition.** Any repository on the CI service can assume the role.
- **One all-powerful role for plan and apply on every branch.**
- **Printing secrets in pipeline logs**, for example with a debugging `echo` or `env` command.
- **Sharing a personal key between teammates.** Nobody can tell who did what, and revoking it breaks everyone.

## Cheat sheet

| Situation | Recommended approach |
|---|---|
| Human on a laptop | Single sign-on, or `aws-vault` with keys in the OS keychain |
| Terraform on an EC2 build server | IAM role through an instance profile |
| Hosted CI pipeline | OIDC federation to an IAM role; no stored keys |
| Restrict who can assume a CI role | `sub` and `aud` conditions in the trust policy |
| Plan on pull requests | A read-only role |
| Store an infrastructure secret | A secret store, or an encrypted file with a KMS key |
| A secret leaked | Rotate, then investigate, then clean history |
| Prevent accidental commits | `.gitignore`, pre-commit scanner, push protection |

## Summary

- A secret in plain text in version control is exposed to everyone, forever, with no audit trail. Never do it.
- Secrets are stored either in encrypted files, with keys held by a key management service, or in centralised secret stores that add access control, audit logs and rotation.
- Terraform meets secrets in providers, in resources and data sources, and in state and plan files.
- People should authenticate with single sign-on or an encrypted key store, giving Terraform short-lived credentials through the environment.
- Machines should use IAM roles: an instance profile inside AWS, or OIDC federation from an external CI system, with a tightly conditioned trust policy.
- Separate plan and apply roles, least privilege and automated secret scanning limit the damage of mistakes.

## Glossary

- **Secret:** a value that grants access and must be kept from unauthorised people.
- **Plain text:** data readable without decryption.
- **Ciphertext:** data in encrypted, unreadable form.
- **Rotation:** replacing a secret with a new one, making the old one useless.
- **Hash:** a one-way transformation used to store passwords without being able to recover them.
- **Key management service (KMS):** a service that holds encryption keys and performs encryption on request.
- **Secret store:** a service that keeps secrets and controls and logs access to them.
- **IAM role:** an identity with permissions, assumed to obtain temporary credentials.
- **Temporary credentials:** credentials that expire after a short time.
- **Instance profile:** the attachment that gives an EC2 server a role.
- **Trust policy:** the policy on a role stating who may assume it.
- **OIDC:** OpenID Connect, a standard for proving identity with signed tokens.
- **Least privilege:** granting only the permissions needed for a task.

## Check yourself

```quiz
[
  {"q": "A database password was committed to Git yesterday. What must be done first?",
   "options": ["Delete the line and commit again", "Rewrite the Git history", "Rotate the password so the leaked value no longer works", "Make the repository private"], "answer": 2,
   "explain": "You cannot know who already copied it. Making the old value useless is the only action that removes the risk; cleaning up comes afterwards."},
  {"q": "What is the main advantage of OIDC federation for a CI pipeline?",
   "options": ["Plans run faster", "No long-lived cloud key is stored in the CI system; each job receives short-lived credentials", "It removes the need for IAM policies", "It encrypts the state file"], "answer": 1,
   "explain": "The job's signed identity token is exchanged for temporary credentials, so there is no standing secret to leak."},
  {"q": "An OIDC trust policy checks only the audience and has no condition on the token's subject. What is the risk?",
   "options": ["The role can never be assumed", "Any repository on that CI service could assume the role", "Credentials last for a year", "Terraform cannot find the provider"], "answer": 1,
   "explain": "The subject claim identifies the repository and branch. Without restricting it, every user of the CI service presents an acceptable token."},
  {"q": "Terraform runs on an EC2 build server inside your account. What is the preferred way to give it credentials?",
   "options": ["An access key in the provider block", "An access key in a file on the server", "An IAM role attached through an instance profile", "The root user's password"], "answer": 2,
   "explain": "The role supplies automatically rotated temporary credentials to programs on the server, with nothing stored."},
  {"q": "Which statement about an encrypted secrets file kept in the repository is true?",
   "options": ["It needs no key", "The decryption key should live in a key management service, with access controlled there", "It provides automatic rotation", "It logs every read of each secret"], "answer": 1,
   "explain": "The file is only as safe as its key. Keeping the key in a KMS means access is controlled and the key itself is never handed out."},
  {"q": "Why give pull-request plans a different role from main-branch applies?",
   "options": ["Plans need more permissions than applies", "So that code from an unreviewed branch can at most read, not change, infrastructure", "Because two roles make state locking work", "Roles cannot be reused between jobs"], "answer": 1,
   "explain": "A plan only needs read access. Limiting unreviewed code to a read-only role contains the damage of a malicious or mistaken change."},
  {"q": "A scanner looks for `password = \"...\"` with a literal value. Which line would it rightly NOT flag?",
   "options": ["`password = \"hunter2hunter2\"`", "`password = var.db_password`", "`secret = \"s3cr3t-value\"`", "`token = \"tok_live_123456\"`"], "answer": 1,
   "explain": "A reference to a variable contains no secret value. The other lines contain literals."}
]
```

> **Source:** Brikman, Terraform: Up & Running 3e, ch. 6 (secret management basics, secret management tools, secret management tools with Terraform: providers). Documentation: https://registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication-and-configuration, https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html and https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect
