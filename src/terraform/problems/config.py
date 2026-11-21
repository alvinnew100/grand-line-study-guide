PROBLEMS = [
dict(
    id="tf-variable-precedence",
    title="Resolve input variables by precedence",
    difficulty="Medium",
    pattern="Variables & Expressions",
    entry="resolveVariables",
    description=r"""
One input variable can be given a value in several places at once. Terraform reads the places in a fixed
order and **the last one read wins**. Write `resolveVariables(declared, env, files, cli)` that reports the
final value of every declared variable and where it came from.

**Inputs**

- `declared`: dict from variable name to a dict that may contain `"default"`. (`{"default": None}` is a real
  default of null; `{}` means no default.)
- `env`: dict of environment variables. Only names of the exact form `TF_VAR_<name>` matter.
- `files`: dict from filename to a dict of `name → value`. These are the variable files in the working folder.
- `cli`: list of `[flag, argument]` pairs in the order typed: `["-var", "name=value"]` or
  `["-var-file", filename]` (the filename is always a key of `files`).

**Order of reading, lowest priority first**

1. the `default` in the declaration;
2. environment variables;
3. the file `terraform.tfvars`, if present;
4. the file `terraform.tfvars.json`, if present;
5. every file whose name ends in `.auto.tfvars` or `.auto.tfvars.json`, in alphabetical order of filename;
6. `-var` and `-var-file` options, in the order given.

Any other file in `files` is read **only** if a `-var-file` option names it.

For `-var`, the name is the text before the first `=` and the value is everything after it, as a string.
Values for names that are not declared are ignored in this exercise.

**Output.** A dict from each declared name to `[value, source]`, where `source` is `"default"`, `"env"`,
the filename, or `"-var"`. A variable that received no value at all maps to `[None, "missing"]`.

**Example:** declared `{"region": {"default": "ap-southeast-1"}, "size": {}}`, env `{"TF_VAR_size": "small"}`,
files `{"terraform.tfvars": {"size": "medium"}}`, cli `[]` →
`{"region": ["ap-southeast-1", "default"], "size": ["medium", "terraform.tfvars"]}`
""",
    starter='''def resolveVariables(declared, env, files, cli):
    pass
''',
    solution='''def resolveVariables(declared, env, files, cli):
    result = {}
    for name, spec in declared.items():
        if "default" in spec:
            result[name] = [spec["default"], "default"]
        else:
            result[name] = [None, "missing"]

    def assign(name, value, source):
        if name in declared:
            result[name] = [value, source]

    def load(filename):
        for name, value in files[filename].items():
            assign(name, value, filename)

    prefix = "TF_VAR_"
    for key, value in env.items():
        if key.startswith(prefix):
            assign(key[len(prefix):], value, "env")

    for fixed in ("terraform.tfvars", "terraform.tfvars.json"):
        if fixed in files:
            load(fixed)

    for filename in sorted(files):
        if filename.endswith(".auto.tfvars") or filename.endswith(".auto.tfvars.json"):
            load(filename)

    for flag, argument in cli:
        if flag == "-var":
            name, _, value = argument.partition("=")
            assign(name, value, "-var")
        else:
            load(argument)
    return result
''',
    tests=[
        [{"region": {"default": "ap-southeast-1"}, "size": {}}, {"TF_VAR_size": "small"},
         {"terraform.tfvars": {"size": "medium"}}, []],
        [{"size": {"default": "micro"}}, {"TF_VAR_size": "small"}, {"terraform.tfvars": {"size": "medium"}},
         [["-var", "size=large"]]],
        [{}, {}, {}, []],
        [{"size": {"default": None}}, {}, {}, []],
        [{"size": {"default": "micro"}}, {"TF_VAR_size": "small", "tf_var_size": "wrong", "SIZE": "wrong"}, {}, []],
        [{"size": {}}, {}, {"prod.tfvars": {"size": "large"}, "dev.tfvars": {"size": "small"}}, []],
        [{"size": {}}, {}, {"prod.tfvars": {"size": "large"}, "dev.tfvars": {"size": "small"}},
         [["-var-file", "dev.tfvars"]]],
        [{"size": {}, "zone": {}}, {},
         {"a.auto.tfvars": {"size": "from-a", "zone": "from-a"}, "terraform.tfvars": {"size": "from-t"},
          "terraform.tfvars.json": {"zone": "from-json", "size": "from-json"}}, []],
        [{"size": {}}, {}, {"b.auto.tfvars": {"size": "b"}, "a.auto.tfvars": {"size": "a"},
                            "c.auto.tfvars.json": {"size": "c"}}, []],
        [{"size": {}}, {}, {"z.auto.tfvars": {"size": "auto"}, "prod.tfvars": {"size": "file"}},
         [["-var", "size=first"], ["-var-file", "prod.tfvars"]]],
        [{"size": {}}, {}, {"prod.tfvars": {"size": "file"}},
         [["-var-file", "prod.tfvars"], ["-var", "size=last"]]],
        [{"tags": {"default": ""}}, {}, {}, [["-var", "tags=team=web,env=prod"]]],
        [{"size": {"default": "micro"}}, {"TF_VAR_colour": "red"}, {"terraform.tfvars": {"colour": "blue"}},
         [["-var", "colour=green"]]],
        [{"a": {"default": 1}, "b": {"default": 2}, "c": {}, "d": {}},
         {"TF_VAR_a": "env", "TF_VAR_b": "env", "TF_VAR_c": "env"},
         {"terraform.tfvars": {"b": 20, "c": 30}, "x.auto.tfvars": {"c": 300}, "extra.tfvars": {"a": 111, "d": 444}},
         [["-var", "c=cli"]]],
        [{"count": {}}, {}, {"terraform.tfvars": {"count": 3}, "terraform.tfvars.json": {"count": 4}}, []],
    ],
    examples=2,
    wrong_solutions=[
        '''def resolveVariables(declared, env, files, cli):
    result = {n: ([s["default"], "default"] if "default" in s else [None, "missing"]) for n, s in declared.items()}
    def assign(n, v, src):
        if n in declared:
            result[n] = [v, src]
    for k, v in env.items():
        if k.startswith("TF_VAR_"):
            assign(k[7:], v, "env")
    for f in sorted(files):
        for n, v in files[f].items():
            assign(n, v, f)
    for flag, arg in cli:
        if flag == "-var":
            n, _, v = arg.partition("="); assign(n, v, "-var")
        else:
            for n, v in files[arg].items():
                assign(n, v, arg)
    return result
''',
        '''def resolveVariables(declared, env, files, cli):
    result = {n: ([s["default"], "default"] if "default" in s else [None, "missing"]) for n, s in declared.items()}
    def assign(n, v, src):
        if n in declared:
            result[n] = [v, src]
    def load(f):
        for n, v in files[f].items():
            assign(n, v, f)
    for f in ("terraform.tfvars", "terraform.tfvars.json"):
        if f in files:
            load(f)
    for f in sorted(files):
        if f.endswith(".auto.tfvars") or f.endswith(".auto.tfvars.json"):
            load(f)
    for k, v in env.items():
        if k.startswith("TF_VAR_"):
            assign(k[7:], v, "env")
    for flag, arg in cli:
        if flag == "-var":
            n, _, v = arg.partition("="); assign(n, v, "-var")
        else:
            load(arg)
    return result
''',
        '''def resolveVariables(declared, env, files, cli):
    result = {n: [s.get("default"), "default" if s.get("default") is not None else "missing"] for n, s in declared.items()}
    def assign(n, v, src):
        if n in declared:
            result[n] = [v, src]
    def load(f):
        for n, v in files[f].items():
            assign(n, v, f)
    for k, v in env.items():
        if k.startswith("TF_VAR_"):
            assign(k[7:], v, "env")
    for f in ("terraform.tfvars", "terraform.tfvars.json"):
        if f in files:
            load(f)
    for f in sorted(files):
        if f.endswith(".auto.tfvars") or f.endswith(".auto.tfvars.json"):
            load(f)
    for flag, arg in cli:
        if flag == "-var":
            n, v = arg.split("=")[0], arg.split("=")[1]; assign(n, v, "-var")
        else:
            load(arg)
    return result
''',
    ],
    guide=dict(
        prereqs="Setting variable values in *Variables, outputs, references and a configurable web server*. Python dicts, `str.startswith`, `str.partition`.",
        intuition="Think of a whiteboard with one box per variable. Terraform walks through the sources from weakest to strongest and writes each value it finds into the box, wiping whatever was there. Whatever is on the board at the end is the answer. So the whole task is to visit the sources in the right order; no comparison logic is needed.",
        hints=[
            "Start by filling the result from the defaults, using `\"default\" in spec` (not `spec.get`) so that a null default is still a default.",
            "Write one `assign(name, value, source)` helper that ignores undeclared names, and call it from every source in turn.",
            "Three groups of files are read automatically: two fixed names, then the `.auto.` files sorted by name. Everything else waits for `-var-file`.",
        ],
        brute_force="For each variable separately, search every source from strongest to weakest and stop at the first hit. It gives the same answers at O(variables × sources) cost, but the command-line options have to be scanned backwards, which is easy to get wrong. One forward pass that overwrites is shorter and mirrors what Terraform does.",
        approach="""1. Defaults → `[default, "default"]`, or `[None, "missing"]`.
2. Environment: for each key starting with exactly `TF_VAR_`, assign the remainder of the key.
3. `terraform.tfvars`, then `terraform.tfvars.json`, when present.
4. `sorted(files)` filtered to names ending `.auto.tfvars` or `.auto.tfvars.json`.
5. Command line in order: `-var` → `partition("=")`; `-var-file` → load that file.

**Dry run:** `size` has default `micro`; env `TF_VAR_size=small`; `terraform.tfvars` says `medium`; `z.auto.tfvars` says `auto`; command line `-var size=first -var-file prod.tfvars` where the file says `file`.

| source read | box for `size` |
|---|---|
| default | micro |
| env | small |
| terraform.tfvars | medium |
| z.auto.tfvars | auto |
| -var | first |
| -var-file prod.tfvars | file |

Final: `["file", "prod.tfvars"]`. The `-var` did not win, because a later option on the same command line overrode it.""",
        complexity="Time O(V + E + F log F + A + C) for V variables, E environment entries, F files, A total assignments in loaded files and C options. Space O(V).",
        pitfalls="Loading every `.tfvars` file in the folder (first wrong solution): `prod.tfvars` is never read unless named. Giving the environment priority over files (second wrong solution): environment variables are the *weakest* source after defaults, which surprises people who set `TF_VAR_x` and see no effect. Splitting `-var` on every `=` and losing part of the value, or treating a null default as missing (third wrong solution). Matching `tf_var_` in lower case.",
        follow_up="Real Terraform is stricter about undeclared names: it ignores them in the environment, prints a warning for a variable file, and stops with an error for `-var`. Return a second list holding those warnings and errors.",
    ),
),
dict(
    id="tf-interpolate",
    title="Render a string template",
    difficulty="Easy",
    pattern="Variables & Expressions",
    entry="render",
    description=r"""
Inside a quoted string, `${ ... }` asks Terraform to evaluate a reference and insert the result. Write
`render(template, values)` for a simplified version of that.

- `values` maps a reference, written exactly as in code (`"var.name"`, `"local.env"`,
  `"aws_instance.web.id"`), to its value.
- Scan the template from left to right:
  - the three characters `$${` are an **escape**: they produce the two literal characters `${`, and nothing
    is looked up;
  - otherwise `${` starts an interpolation that ends at the next `}`. The text between, with surrounding
    spaces removed, is the reference to look up;
  - any other character is copied unchanged.
- Converting a value to text: a string is inserted as it is; a whole number in decimal; a bool as `true` or
  `false` in lower case.

Errors (return the message for the **first** problem met, scanning left to right):

- the reference is not a key of `values` → `"Error: undeclared reference <ref>"`;
- the value is `None`, a list or a dict → `"Error: invalid template value for <ref>"`.

Every unescaped `${` in the tests has a closing `}`.

**Example 1:** `render("web-${var.env}-${ var.index }", {"var.env": "prod", "var.index": 2})` → `"web-prod-2"`

**Example 2:** `render("echo $${HOME} on ${var.host}", {"var.host": "db1"})` → `"echo ${HOME} on db1"`
""",
    starter='''def render(template, values):
    pass
''',
    solution='''def render(template, values):
    out = []
    i, n = 0, len(template)
    while i < n:
        if template.startswith("$${", i):
            out.append("${")
            i += 3
        elif template.startswith("${", i):
            end = template.index("}", i)
            ref = template[i + 2:end].strip()
            if ref not in values:
                return "Error: undeclared reference " + ref
            value = values[ref]
            if isinstance(value, bool):
                out.append("true" if value else "false")
            elif isinstance(value, (int, str)):
                out.append(str(value))
            else:
                return "Error: invalid template value for " + ref
            i = end + 1
        else:
            out.append(template[i])
            i += 1
    return "".join(out)
''',
    tests=[
        ["web-${var.env}-${ var.index }", {"var.env": "prod", "var.index": 2}],
        ["echo $${HOME} on ${var.host}", {"var.host": "db1"}],
        ["", {}],
        ["${var.a}${var.b}${var.a}", {"var.a": "x", "var.b": "y"}],
        ["enabled=${var.on} debug=${var.debug}", {"var.on": True, "var.debug": False}],
        ["http://${aws_lb.web.dns_name}:${var.port}/health", {"aws_lb.web.dns_name": "lb.example.com", "var.port": 8080}],
        ["${var.missing} then ${var.also_missing}", {"var.x": 1}],
        ["id=${var.id} list=${var.items}", {"var.id": 7, "var.items": ["a", "b"]}],
        ["value: ${var.nothing}", {"var.nothing": None}],
        ["cost is $5 and 100% of ${var.what}", {"var.what": "budget"}],
        ["$${var.env} stays, ${var.env} goes", {"var.env": "dev"}],
        ["${var.empty}|${local.zero}|", {"var.empty": "", "local.zero": 0}],
        ["${var.a}", {"var.a": "${var.b}", "var.b": "never"}],
        ["${   module.net.vpc_id   }/${data.aws_region.current.name}", {"module.net.vpc_id": "vpc-1", "data.aws_region.current.name": "ap-southeast-1"}],
        ["-".join("${var.n}" for _ in range(300)), {"var.n": 9}],
    ],
    examples=2,
    wrong_solutions=[
        '''def render(template, values):
    for ref, value in values.items():
        template = template.replace("${" + ref + "}", str(value))
    return template
''',
        '''def render(template, values):
    out, i, n = [], 0, len(template)
    while i < n:
        if template.startswith("$${", i):
            out.append("${"); i += 3
        elif template.startswith("${", i):
            end = template.index("}", i)
            ref = template[i + 2:end].strip()
            if ref not in values:
                return "Error: undeclared reference " + ref
            value = values[ref]
            if value is None or isinstance(value, (list, dict)):
                return "Error: invalid template value for " + ref
            out.append(str(value)); i = end + 1
        else:
            out.append(template[i]); i += 1
    return "".join(out)
''',
        '''def render(template, values):
    out, i, n = [], 0, len(template)
    while i < n:
        if template.startswith("${", i):
            end = template.index("}", i)
            ref = template[i + 2:end].strip()
            if ref not in values:
                return "Error: undeclared reference " + ref
            value = values[ref]
            if isinstance(value, bool):
                out.append("true" if value else "false")
            elif isinstance(value, (int, str)):
                out.append(str(value))
            else:
                return "Error: invalid template value for " + ref
            i = end + 1
        else:
            out.append(template[i]); i += 1
    return "".join(out)
''',
    ],
    guide=dict(
        prereqs="References and interpolation in *Variables, outputs, references and a configurable web server*. Walking a string with an index; `str.startswith(prefix, position)`.",
        intuition="Read the template the way you would read a sentence aloud, one character at a time, with two special signals. `$${` means 'say a literal dollar-brace and carry on'. `${` means 'pause, look something up, say the answer, then resume after the closing brace'. Checking for the longer signal first is what stops the escape from being mistaken for an interpolation.",
        hints=[
            "Use a `while` loop with an index instead of a `for` loop, because you sometimes skip several characters at once.",
            "Test for `$${` before testing for `${`. What would go wrong the other way round?",
            "Python's `True` is also an `int`. Check `isinstance(value, bool)` before the general number case.",
        ],
        brute_force="Call `str.replace` once per entry in `values` (first wrong solution). It handles the plain cases but cannot see escapes, spaces inside the braces, undeclared references, or a substituted value that itself looks like a template.",
        approach="""Keep `i` and a list of output pieces.

- `template.startswith("$${", i)` → append `${`, `i += 3`.
- `template.startswith("${", i)` → `end = template.index("}", i)`; `ref = template[i+2:end].strip()`; look it up, convert, `i = end + 1`.
- otherwise copy one character.

**Dry run** on `echo $${HOME} on ${var.host}` with `var.host = "db1"`:

| i | sees | action | output so far |
|---|---|---|---|
| 0–4 | `echo ` | copy | `echo ` |
| 5 | `$${` | escape | `echo ${` |
| 8–12 | `HOME}` | copy | `echo ${HOME}` |
| 13–16 | ` on ` | copy | `echo ${HOME} on ` |
| 17 | `${` | look up `var.host` | `echo ${HOME} on db1` |

Each inserted value is appended to the output and never scanned again, so a value containing `${` stays literal.""",
        complexity="Time O(n) for a template of length n plus the length of inserted values; space O(n) for the output.",
        pitfalls="Missing the escape (third wrong solution): shell scripts in `user_data` are full of `${HOME}`-style text that must reach the server untouched. Printing Python's `True` instead of `true` (second wrong solution). Re-scanning substituted text. A lone `$` or `%` is ordinary text. Reporting the second error instead of the first.",
        follow_up="Terraform has a second template sequence, `%{ ... }`, for directives such as `%{ if }` and `%{ for }`, with `%%{` as its escape. Add the escape, then a simple `%{ if var.flag }...%{ endif }`.",
    ),
),
dict(
    id="tf-module-outputs",
    title="Wire module outputs to root outputs",
    difficulty="Medium",
    pattern="Modules",
    entry="resolveOutputs",
    description=r"""
Modules talk to each other only through inputs and outputs, and the root configuration does the wiring.
Write `resolveOutputs(root_vars, modules, outputs)` that follows the wires and computes the root outputs.

**Inputs**

- `root_vars`: dict of the root module's input variables, `name → value`.
- `modules`: dict from a module call's name to
  `{"inputs": {input_name: expression}, "outputs": {output_name: expression}}`.
  - `inputs` are the arguments written inside the `module` block. They are evaluated in the **root** scope.
  - `outputs` are the `output` blocks inside the module. They are evaluated in the **module's own** scope.
- `outputs`: dict of root outputs, `name → expression`, evaluated in the root scope.

**Expressions.** A string beginning with `var.` or `module.` is a reference. Any other value (a number, a
bool, a list, or a string without those prefixes) is a literal and evaluates to itself.

**Scopes**

- Root scope: `var.<name>` is a root variable; `module.<call>.<output>` is that module's output.
- Module scope: `var.<name>` is one of *that module's* inputs. Nothing else is visible: a module cannot see
  root variables or other modules, so any `module.` reference inside a module's outputs is undeclared.

**Undeclared references.** If following a root output's chain reaches a reference to something that does
not exist, that output's value is the string `"Error: undeclared <reference>"`, with the reference exactly
as written at the point of failure. Other outputs are unaffected. There are no circular references.

Return a dict from each root output name to its value.

**Example:** root variable `project = "shop"`; module `net` with input `name = var.project` and output
`vpc_name = var.name`; module `app` with input `network = module.net.vpc_name` and output
`summary = var.network`; root output `where = module.app.summary` → `{"where": "shop"}`
""",
    starter='''def resolveOutputs(root_vars, modules, outputs):
    pass
''',
    solution='''def resolveOutputs(root_vars, modules, outputs):
    class Undeclared(Exception):
        pass

    def is_reference(expr):
        return isinstance(expr, str) and (expr.startswith("var.") or expr.startswith("module."))

    def eval_root(expr):
        if not is_reference(expr):
            return expr
        if expr.startswith("var."):
            name = expr[len("var."):]
            if name not in root_vars:
                raise Undeclared(expr)
            return root_vars[name]
        parts = expr.split(".")
        if len(parts) != 3 or parts[1] not in modules or parts[2] not in modules[parts[1]]["outputs"]:
            raise Undeclared(expr)
        return eval_module(parts[1], modules[parts[1]]["outputs"][parts[2]])

    def eval_module(call, expr):
        if not is_reference(expr):
            return expr
        if expr.startswith("var."):
            name = expr[len("var."):]
            if name not in modules[call]["inputs"]:
                raise Undeclared(expr)
            return eval_root(modules[call]["inputs"][name])
        raise Undeclared(expr)

    result = {}
    for name, expr in outputs.items():
        try:
            result[name] = eval_root(expr)
        except Undeclared as problem:
            result[name] = "Error: undeclared " + str(problem)
    return result
''',
    tests=[
        [{"project": "shop"},
         {"net": {"inputs": {"name": "var.project"}, "outputs": {"vpc_name": "var.name"}},
          "app": {"inputs": {"network": "module.net.vpc_name"}, "outputs": {"summary": "var.network"}}},
         {"where": "module.app.summary"}],
        [{"env": "dev"}, {"net": {"inputs": {}, "outputs": {"cidr": "10.0.0.0/16", "zones": 3}}},
         {"cidr": "module.net.cidr", "zones": "module.net.zones", "env": "var.env", "fixed": "hello"}],
        [{}, {}, {}],
        [{}, {}, {"n": 5, "flag": True, "items": ["a", "b"]}],
        [{"env": "dev"}, {}, {"a": "var.env", "b": "var.region"}],
        [{"env": "dev"}, {"net": {"inputs": {}, "outputs": {"id": "vpc-1"}}},
         {"a": "module.net.id", "b": "module.net.arn", "c": "module.db.id"}],
        [{"env": "prod"}, {"app": {"inputs": {"size": "large"}, "outputs": {"where": "var.env", "size": "var.size"}}},
         {"where": "module.app.where", "size": "module.app.size"}],
        [{"size": "root-size"}, {"app": {"inputs": {"size": "small"}, "outputs": {"size": "var.size"}}},
         {"size": "module.app.size", "root": "var.size"}],
        [{}, {"net": {"inputs": {}, "outputs": {"id": "vpc-1"}},
              "app": {"inputs": {"vpc": "module.net.id"}, "outputs": {"peek": "module.net.id", "ok": "var.vpc"}}},
         {"peek": "module.app.peek", "ok": "module.app.ok"}],
        [{"a": 1},
         {"m1": {"inputs": {"x": "var.a"}, "outputs": {"o": "var.x"}},
          "m2": {"inputs": {"x": "module.m1.o"}, "outputs": {"o": "var.x"}},
          "m3": {"inputs": {"x": "module.m2.o"}, "outputs": {"o": "var.x"}},
          "m4": {"inputs": {"x": "module.m3.o", "y": "module.m1.o"}, "outputs": {"o": "var.x", "p": "var.y"}}},
         {"deep": "module.m4.o", "short": "module.m4.p"}],
        [{}, {"m1": {"inputs": {"x": "var.gone"}, "outputs": {"o": "var.x"}},
              "m2": {"inputs": {"x": "module.m1.o"}, "outputs": {"o": "var.x", "lit": "fine"}}},
         {"broken": "module.m2.o", "fine": "module.m2.lit"}],
        [{}, {"m": {"inputs": {"x": "module.m.nope"}, "outputs": {"o": "var.x"}}}, {"r": "module.m.o"}],
        [{"env": "dev"}, {"net": {"inputs": {"e": "var.env"}, "outputs": {"e": "var.e"}}}, {"bad": "module.net", "bad2": "module.net.e.x"}],
        [{"seed": "s"},
         {f"m{i}": {"inputs": {"x": ("var.seed" if i == 0 else f"module.m{i - 1}.o")}, "outputs": {"o": "var.x"}}
          for i in range(60)},
         {"end": "module.m59.o", "mid": "module.m30.o"}],
    ],
    examples=2,
    wrong_solutions=[
        '''def resolveOutputs(root_vars, modules, outputs):
    def ev(expr, call=None):
        if not (isinstance(expr, str) and (expr.startswith("var.") or expr.startswith("module."))):
            return expr
        if expr.startswith("var."):
            name = expr[4:]
            if call is not None and name in modules[call]["inputs"]:
                return ev(modules[call]["inputs"][name])
            if name in root_vars:
                return root_vars[name]
            raise KeyError(expr)
        parts = expr.split(".")
        if len(parts) != 3 or parts[1] not in modules or parts[2] not in modules[parts[1]]["outputs"]:
            raise KeyError(expr)
        return ev(modules[parts[1]]["outputs"][parts[2]], parts[1])
    out = {}
    for name, expr in outputs.items():
        try:
            out[name] = ev(expr)
        except KeyError as e:
            out[name] = "Error: undeclared " + e.args[0]
    return out
''',
        '''def resolveOutputs(root_vars, modules, outputs):
    out = {}
    for name, expr in outputs.items():
        if isinstance(expr, str) and expr.startswith("var."):
            out[name] = root_vars.get(expr[4:], "Error: undeclared " + expr)
        elif isinstance(expr, str) and expr.startswith("module."):
            parts = expr.split(".")
            if len(parts) == 3 and parts[1] in modules and parts[2] in modules[parts[1]]["outputs"]:
                out[name] = modules[parts[1]]["outputs"][parts[2]]
            else:
                out[name] = "Error: undeclared " + expr
        else:
            out[name] = expr
    return out
''',
    ],
    guide=dict(
        prereqs="Module inputs and outputs in *Reusable modules: inputs, outputs and locals*; passing one module's output to another in *Worked project, part 2: database, container service, DNS and environments*. Recursion.",
        intuition="A module is a sealed box with labelled sockets. Inside the box, `var.x` means 'whatever is plugged into my socket x'. Outside, `module.box.y` means 'whatever comes out of socket y'. Evaluating an output is following a cable: out of one box, into the root, perhaps into another box, until you reach a literal or a root variable. The one rule that must never be broken is that the meaning of `var.` depends on which side of the box wall you are standing.",
        hints=[
            "Write two evaluators, one for each scope, instead of one evaluator with flags. They call each other.",
            "In root scope, `module.a.b` means: find module `a`'s output `b` and evaluate *that expression in module scope*.",
            "In module scope, `var.x` means: find the argument `x` in the module call and evaluate *that expression in root scope*.",
        ],
        brute_force="Repeatedly sweep over every expression, replacing references whose targets are already known, until nothing changes. It reaches the answer in at most as many sweeps as the longest chain, O(chain × expressions), and needs extra care for errors. Direct recursion follows only the chains the root outputs need.",
        approach="""`eval_root(expr)`:
- literal → itself;
- `var.n` → `root_vars[n]`, or fail;
- `module.c.o` → must split into exactly three parts naming an existing call and output; then `eval_module(c, modules[c]["outputs"][o])`.

`eval_module(c, expr)`:
- literal → itself;
- `var.n` → `eval_root(modules[c]["inputs"][n])`, or fail if the call passes no such argument;
- `module.…` → fail: not visible here.

Failure is an exception carrying the reference text, caught once per root output.

**Dry run** of the example, output `where = module.app.summary`:

| step | scope | expression | goes to |
|---|---|---|---|
| 1 | root | module.app.summary | app's output `summary` |
| 2 | app | var.network | app's argument `network` |
| 3 | root | module.net.vpc_name | net's output `vpc_name` |
| 4 | net | var.name | net's argument `name` |
| 5 | root | var.project | `"shop"` |""",
        complexity="Time O(L) per root output for a chain of length L (O(R·L) in total without caching; add a memo dict to share work between outputs). Space O(L) for the recursion.",
        pitfalls="Letting a module read root variables when it has no such input (first wrong solution): this is the scope leak that modules exist to prevent, and Terraform reports `Reference to undeclared input variable`. Resolving only one hop and returning the text `var.x` as if it were a value (second wrong solution). Accepting `module.net` or `module.net.e.x` as valid. Letting one broken output abort the others.",
        follow_up="Give each module a `defaults` dict for inputs the caller may omit, and add `local.` references evaluated within their own scope.",
    ),
),
dict(
    id="tf-cidrsubnet",
    title="Implement cidrsubnet",
    difficulty="Medium",
    pattern="Variables & Expressions",
    entry="cidrsubnet",
    description=r"""
Terraform's built-in `cidrsubnet(prefix, newbits, netnum)` carves a smaller network out of a larger one, so
that subnet ranges can be computed instead of typed. Implement it for IPv4.

- `prefix` is a network in CIDR notation, such as `"10.20.0.0/16"`: four numbers 0–255 and a prefix length
  0–32 saying how many leading bits are fixed.
- `newbits` (≥ 0) is how many extra bits to fix. The result's prefix length is the old length plus `newbits`.
- `netnum` chooses which of the `2 ** newbits` possible subnets to return, counting from 0. Its binary digits
  are written into the newly fixed bit positions.

If `prefix` has any bits set after its prefix length (for example `"10.20.5.7/16"`), clear them first.

Errors, checked in this order:

1. the new prefix length would exceed 32 → `"Error: insufficient address space"`;
2. `netnum` is negative or does not fit in `newbits` bits → `"Error: netnum out of range"`.

Return the subnet in CIDR notation.

**Example 1:** `cidrsubnet("10.20.0.0/16", 8, 11)` → `"10.20.11.0/24"`

**Example 2:** `cidrsubnet("10.0.0.0/24", 2, 3)` → `"10.0.0.192/26"`
""",
    starter='''def cidrsubnet(prefix, newbits, netnum):
    pass
''',
    solution='''def cidrsubnet(prefix, newbits, netnum):
    ip, length = prefix.split("/")
    length = int(length)
    new_length = length + newbits
    if new_length > 32:
        return "Error: insufficient address space"
    if netnum < 0 or netnum >= 2 ** newbits:
        return "Error: netnum out of range"
    a, b, c, d = (int(part) for part in ip.split("."))
    address = (a << 24) | (b << 16) | (c << 8) | d
    mask = ((1 << length) - 1) << (32 - length)
    address &= mask
    address |= netnum << (32 - new_length)
    octets = [(address >> shift) & 255 for shift in (24, 16, 8, 0)]
    return ".".join(str(o) for o in octets) + "/" + str(new_length)
''',
    tests=[
        ["10.20.0.0/16", 8, 11],
        ["10.0.0.0/24", 2, 3],
        ["10.20.0.0/16", 8, 255],
        ["10.20.0.0/16", 8, 256],
        ["10.20.0.0/16", 0, 0],
        ["10.20.0.0/16", 0, 1],
        ["10.0.0.0/8", 12, 300],
        ["192.168.1.0/24", 9, 0],
        ["10.20.5.7/16", 8, 1],
        ["172.16.0.0/12", 4, 5],
        ["0.0.0.0/0", 2, 3],
        ["192.168.1.128/25", 7, 127],
        ["10.20.0.0/16", 4, -1],
        ["10.0.0.0/30", 4, 20],
        ["100.64.0.0/10", 14, 4097],
    ],
    examples=2,
    wrong_solutions=[
        '''def cidrsubnet(prefix, newbits, netnum):
    ip, length = prefix.split("/")
    length = int(length)
    if length + newbits > 32:
        return "Error: insufficient address space"
    if netnum < 0 or netnum >= 2 ** newbits:
        return "Error: netnum out of range"
    parts = [int(p) for p in ip.split(".")]
    parts[(length + newbits - 1) // 8] += netnum
    return ".".join(str(p) for p in parts) + "/" + str(length + newbits)
''',
        '''def cidrsubnet(prefix, newbits, netnum):
    ip, length = prefix.split("/")
    length = int(length)
    new_length = length + newbits
    a, b, c, d = (int(p) for p in ip.split("."))
    address = (a << 24) | (b << 16) | (c << 8) | d
    address |= netnum << (32 - new_length)
    return ".".join(str((address >> s) & 255) for s in (24, 16, 8, 0)) + "/" + str(new_length)
''',
    ],
    guide=dict(
        prereqs="`cidrsubnet` in *Worked project, part 1: repository, remote state, network and security groups*. CIDR notation; binary numbers and the bit operators `<<`, `>>`, `&`, `|`.",
        intuition="An IPv4 address is one 32-bit number written as four bytes. A prefix length of 16 says the first 16 bits are the network's name and the remaining 16 are free. `cidrsubnet` extends the name by `newbits` bits and writes `netnum` into exactly those new positions. Converted to a single integer, that is one shift and one OR; the dotted form is only how the number is printed.",
        hints=[
            "Combine the four numbers into one integer: `a << 24 | b << 16 | c << 8 | d`.",
            "The new bits sit immediately after the old prefix. Their lowest bit is `32 - new_length` positions from the right, so shift `netnum` left by that amount.",
            "To print, extract each byte with a shift and `& 255`.",
        ],
        brute_force="List every subnet of the new size inside the network in order and return the one at position `netnum`. Correct, but O(2^newbits) time; `newbits` of 14 already means 16,384 steps for one answer. The bit arithmetic is O(1).",
        approach="""1. Split into address and length; `new_length = length + newbits`.
2. Validate: `new_length > 32`, then `netnum` outside `0 .. 2**newbits - 1`.
3. Pack the four bytes into one integer.
4. Clear host bits with a mask of `length` ones followed by zeros: `((1 << length) - 1) << (32 - length)`.
5. `address |= netnum << (32 - new_length)`.
6. Unpack into four bytes and append `/new_length`.

**Dry run:** `cidrsubnet("10.0.0.0/24", 2, 3)`.

- `new_length = 26`. `netnum = 3` fits in 2 bits (0–3).
- The last byte in binary is `00 000000`: two new network bits, then six host bits.
- `3 << (32 - 26)` = `3 << 6` = 192 = `11 000000`.
- Result `10.0.0.192/26`.

For the lesson's network: `/16` plus 8 bits puts `netnum` in the third byte, so 11 gives `10.20.11.0/24`.""",
        complexity="Time O(1) and space O(1): a fixed number of arithmetic operations on 32-bit values.",
        pitfalls="Adding `netnum` to one of the dotted numbers (first wrong solution): it happens to work when the new bits fill exactly one byte and breaks when they straddle bytes or stop mid-byte, as in `/12 + 4` or `/24 + 2`. Skipping validation or leaving host bits in place (second wrong solution), which yields nonsense such as overlapping subnets. Checking `netnum > 2 ** newbits` instead of `>=`. Writing `1 << length - 1` and expecting `(1 << length) - 1`: subtraction binds tighter than a shift, so add the parentheses.",
        follow_up="Implement `cidrhost(prefix, hostnum)`, which returns one address inside a network, and `cidrsubnets(prefix, newbits...)`, which allocates several consecutive subnets of different sizes.",
    ),
),
]
