import pathlib as _pl
import re as _re

_HERE = _pl.Path(__file__).parent
_DEFINED = set()
for _f in (_HERE / "problems").glob("*.py"):
    _DEFINED.update(_re.findall(r'^\s*id="(tf-[a-z0-9-]+)"', _f.read_text(encoding="utf-8"), _re.M))


def _m(mid, title, summary, lessons, problems=()):
    return dict(
        id=mid, title=title, summary=summary,
        lessons=[dict(id=i, title=t, file=f) for i, t, f in lessons if (_HERE / "lessons" / f).exists()],
        problems=[p for p in problems if p in _DEFINED],
    )


# Lesson ids are the file name without its number prefix. Lessons link to each other with
# #/lesson/terraform/<id>, so changing an id here breaks those links.
TRACK = dict(
    id="terraform",
    title="Terraform & Infrastructure as Code",
    icon="🧱",
    color="#7b42bc",
    group="Cloud & DevOps",
    blurb="Infrastructure as code from zero: how Terraform plans and applies, state, backends and locking, "
          "modules, count and for_each, zero-downtime changes, secrets, multiple providers, production-grade "
          "modules, testing, team workflows and CI/CD, a worked AWS project and interview answers, with "
          "Python simulations of plans, dependency graphs, drift and version constraints.",
    sources=[
        "Yevgeniy Brikman, Terraform: Up & Running, 3rd ed. (O'Reilly, 2022), ch. 1-10 "
        "(topic map and fact checking; all wording and examples are original)",
        "Official Terraform documentation: developer.hashicorp.com/terraform (language, CLI, S3 backend, "
        "state, tests, import and moved blocks)",
        "Provider documentation: registry.terraform.io (hashicorp/aws, hashicorp/kubernetes, kreuzwerker/docker)",
    ],
    modules=[
        _m("why-terraform", "1. Why Terraform",
           "What DevOps and infrastructure as code are, how Terraform turns code into API calls, and how it compares with other tools.",
           [("devops-and-iac", "From clicking to code: DevOps and infrastructure as code", "01-devops-and-iac.md"),
            ("how-terraform-works", "How Terraform works, and how it compares with the alternatives", "02-how-terraform-works.md")],
           ["tf-plan-summary", "tf-compute-plan"]),
        _m("getting-started", "2. Getting Started",
           "Install Terraform, authenticate safely, create one server, make it configurable, then grow it into a load-balanced cluster.",
           [("install-auth-first-resource", "Installing Terraform, signing in safely and creating a first resource", "03-install-auth-first-resource.md"),
            ("variables-outputs-web-server", "Variables, outputs, references and a configurable web server", "04-variables-outputs-web-server.md"),
            ("cluster-load-balancer", "A cluster of web servers behind a load balancer", "05-cluster-load-balancer.md")],
           ["tf-variable-precedence", "tf-interpolate", "tf-dependency-order", "tf-destroy-order", "tf-cycle-detect"]),
        _m("state", "3. Managing State",
           "What the state file records, sharing and locking it in a remote backend, isolating environments, and repairing state safely.",
           [("state-and-backends", "Terraform state, remote backends and locking", "06-state-and-backends.md"),
            ("state-isolation", "Isolating state: workspaces, file layout and reading another state", "07-state-isolation.md"),
            ("state-surgery", "State surgery: moving, removing, importing and repairing", "08-state-surgery.md")],
           ["tf-state-lock", "tf-stale-plan", "tf-workspace-key", "tf-detect-drift", "tf-blast-radius"]),
        _m("modules", "4. Reusable Modules",
           "Package infrastructure behind inputs and outputs, avoid the classic module traps, and release versions others can pin.",
           [("module-basics", "Reusable modules: inputs, outputs and locals", "09-module-basics.md"),
            ("module-gotchas-versioning", "Module gotchas and versioning: file paths, inline blocks and releases", "10-module-gotchas-versioning.md")],
           ["tf-module-outputs", "tf-version-constraint"]),
        _m("loops-deployment", "5. Loops, Conditionals and Zero-Downtime Deployment",
           "count and for_each, for expressions and conditionals, replacing resources without an outage, and refactoring without destroying.",
           [("loops-count-for-each", "Loops: count, for_each and the index-shifting trap", "11-loops-count-for-each.md"),
            ("for-expressions-conditionals", "For expressions, string directives and conditionals", "12-for-expressions-conditionals.md"),
            ("zero-downtime-refactoring", "Zero-downtime deployment, plans that fail and safe refactoring", "13-zero-downtime-refactoring.md")],
           ["tf-count-plan", "tf-foreach-plan", "tf-parse-address", "tf-for-expression", "tf-moved-blocks",
            "tf-create-before-destroy"]),
        _m("secrets", "6. Managing Secrets",
           "Keep credentials out of code: authenticating providers, passing secrets to resources, and protecting state and plan files.",
           [("secrets-basics-providers", "Secrets, part 1: the rules, the tools and authenticating providers", "14-secrets-basics-providers.md"),
            ("secrets-resources-state", "Secrets, part 2: resources, data sources, state files and plan files", "15-secrets-resources-state.md")]),
        _m("providers", "7. Working with Multiple Providers",
           "Provider versions and aliases, deploying to several Regions and accounts, and combining AWS with Docker and Kubernetes.",
           [("provider-aliases-regions-accounts", "Multiple providers, part 1: aliases, Regions and accounts", "16-provider-aliases-regions-accounts.md"),
            ("docker-kubernetes-providers", "Multiple providers, part 2: different providers, Docker and Kubernetes", "17-docker-kubernetes-providers.md")],
           ["tf-version-select"]),
        _m("production-grade", "8. Production-Grade Terraform Code",
           "Why infrastructure work overruns, the production checklist, and modules that are small, composable, testable and versioned.",
           [("production-checklist", "Production-grade infrastructure: why it takes so long, and the checklist", "18-production-checklist.md"),
            ("production-modules", "Production-grade modules: small, composable, testable, versioned, and beyond", "19-production-modules.md")]),
        _m("testing", "9. Testing Terraform Code",
           "Manual checks in a sandbox, static analysis and policy on the plan, then automated unit, integration and end-to-end tests.",
           [("manual-static-plan-testing", "Testing, part 1: manual tests, static analysis, policy and plan testing", "20-manual-static-plan-testing.md"),
            ("automated-tests", "Testing, part 2: automated unit, integration and end-to-end tests", "21-automated-tests.md")],
           ["tf-plan-review", "tf-policy-check"]),
        _m("team", "10. Terraform as a Team",
           "Introducing infrastructure as code to a team, the application and infrastructure workflows, golden rules and a CI/CD pipeline.",
           [("adopting-iac-workflows", "Terraform as a team, part 1: adopting IaC and the two deployment workflows", "22-adopting-iac-workflows.md"),
            ("cicd-for-terraform", "Terraform as a team, part 2: golden rules and a CI/CD pipeline", "23-cicd-for-terraform.md")],
           ["tf-cost-estimate"]),
        _m("worked-project", "11. Worked Project: a Three-Tier Service on AWS",
           "Build a real layout end to end: repository and remote state, network, database, container service, DNS and two environments.",
           [("project-foundations", "Worked project, part 1: repository, remote state, network and security groups", "24-project-foundations.md"),
            ("project-app-data-environments", "Worked project, part 2: database, container service, DNS and environments", "25-project-app-data-environments.md")],
           ["tf-cidrsubnet"]),
        _m("interview", "12. Terraform Interview Essentials",
           "Worked answers on state, plans, count versus for_each, drift, import, secrets, module design and recovering from failed applies.",
           [("interview-core", "Interview essentials, part 1: state, plan and apply, count and for_each, drift and import", "26-interview-core.md"),
            ("interview-operations", "Interview essentials, part 2: secrets, module design and recovering from failures", "27-interview-operations.md")]),
    ],
)
