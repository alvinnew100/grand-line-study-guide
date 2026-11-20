import string

_CHARS = string.ascii_letters + string.digits
_SECRET = "Qw3rTyUiOpAsDfGhJkLzXcVbNm123456"
_OTHER = "zzzzTyUiOpAsDfGhJkLzXcVbNm123456"


def _mask(secret, mask):
    return mask + "".join(_CHARS[(_CHARS.index(s) + _CHARS.index(m)) % len(_CHARS)] for s, m in zip(secret, mask))


_MASK1 = "a1B2c3D4e5F6g7H8i9J0kLmNoPqRsTuV"
_MASK2 = "9999999999zzzzzzzzzzZZZZZZZZZZ00"

_SIGNUP = {
    "handle": {"type": "char", "min_length": 3, "max_length": 12},
    "email": {"type": "email"},
    "age": {"type": "int", "required": False, "min_value": 13, "max_value": 120},
    "plan": {"type": "choice", "choices": ["free", "crew"]},
    "bio": {"type": "char", "required": False, "max_length": 20},
}

_MODEL = [
    {"name": "id", "type": "BigAutoField"},
    {"name": "headline", "type": "CharField"},
    {"name": "slug", "type": "SlugField", "blank": True},
    {"name": "body", "type": "TextField"},
    {"name": "status", "type": "CharField", "choices": ["draft", "live"]},
    {"name": "author", "type": "ForeignKey"},
    {"name": "tags", "type": "ManyToManyField", "blank": True},
    {"name": "pinned", "type": "BooleanField"},
    {"name": "word_count", "type": "IntegerField", "editable": False},
    {"name": "embargo", "type": "DateField", "blank": True},
    {"name": "created", "type": "DateTimeField", "auto_now_add": True},
    {"name": "updated", "type": "DateTimeField", "auto_now": True},
    {"name": "contact", "type": "EmailField", "blank": True},
    {"name": "goes_live", "type": "DateTimeField"},
]

_USER = {"username": "marisol.reyes", "email": "mari@harbour.example", "first_name": "Marisol"}
_COMMON = ["password", "12345678", "qwertyuiop", "letmein123", "iloveyou1"]

PROBLEMS = [
dict(
    id="django-form-validate",
    title="Validate a form like Django does",
    difficulty="Medium",
    pattern="Forms",
    entry="validate_form",
    description=r"""
A Django form takes the raw strings a browser posted, **cleans** each field into a Python value and collects
error messages for the ones that fail. Reproduce `form.is_valid()`, `form.cleaned_data` and `form.errors`.

`validate_form(data, fields)`:

- `data`: dict of submitted values; every value is a string. A missing key is treated as `""`.
- `fields`: dict (in display order) mapping field name to rules. `type` is always present:
  `"char"`, `"int"`, `"email"` or `"choice"`. `required` defaults to `True`.

For each field, in order: take the value, **strip** surrounding whitespace, then

1. If it is empty: when required, the error is `This field is required.`; when optional, the field is valid and
   its cleaned value is `""` (for `int`: `None`).
2. `char`: with `n = len(value)`, if `min_length` is set and `n < min_length` →
   `Ensure this value has at least {min_length} characters (it has {n}).`; if `max_length` is set and
   `n > max_length` → `Ensure this value has at most {max_length} characters (it has {n}).` Cleaned value: the stripped string.
3. `int`: the text must be an optional `-` followed by digits, else `Enter a whole number.` Then, with the
   integer value `v`: `v < min_value` → `Ensure this value is greater than or equal to {min_value}.`;
   `v > max_value` → `Ensure this value is less than or equal to {max_value}.` Cleaned value: the `int`.
4. `email`: valid when it contains no whitespace, exactly one `@`, a non-empty part before it, and after it a
   domain made of at least two non-empty labels separated by `.`. Otherwise `Enter a valid email address.`
   Cleaned value: the stripped string.
5. `choice`: must be one of `choices`, else `Select a valid choice. {value} is not one of the available choices.`

Return `[is_valid, cleaned_data, errors]`: `errors` maps each failing field to a **list** with its one message;
`cleaned_data` contains only the fields that passed; `is_valid` is `True` when `errors` is empty.

**Example:** `validate_form({"handle": " al ", "age": "x"}, {"handle": {"type": "char", "min_length": 3}, "age": {"type": "int"}})`
→ `[False, {}, {"handle": ["Ensure this value has at least 3 characters (it has 2)."], "age": ["Enter a whole number."]}]`.
""",
    starter='''def validate_form(data: dict, fields: dict) -> list:
    pass
''',
    solution=r'''import re


def _email_ok(value):
    if re.search(r"\s", value) or value.count("@") != 1:
        return False
    local, domain = value.split("@")
    labels = domain.split(".")
    return bool(local) and len(labels) >= 2 and all(labels)


def validate_form(data, fields):
    cleaned, errors = {}, {}
    for name, rule in fields.items():
        value = data.get(name, "").strip()
        kind = rule["type"]
        if value == "":
            if rule.get("required", True):
                errors[name] = ["This field is required."]
            else:
                cleaned[name] = None if kind == "int" else ""
            continue
        if kind == "char":
            n = len(value)
            if "min_length" in rule and n < rule["min_length"]:
                errors[name] = ["Ensure this value has at least %d characters (it has %d)." % (rule["min_length"], n)]
            elif "max_length" in rule and n > rule["max_length"]:
                errors[name] = ["Ensure this value has at most %d characters (it has %d)." % (rule["max_length"], n)]
            else:
                cleaned[name] = value
        elif kind == "int":
            if not re.fullmatch(r"-?[0-9]+", value):
                errors[name] = ["Enter a whole number."]
                continue
            v = int(value)
            if "min_value" in rule and v < rule["min_value"]:
                errors[name] = ["Ensure this value is greater than or equal to %d." % rule["min_value"]]
            elif "max_value" in rule and v > rule["max_value"]:
                errors[name] = ["Ensure this value is less than or equal to %d." % rule["max_value"]]
            else:
                cleaned[name] = v
        elif kind == "email":
            if _email_ok(value):
                cleaned[name] = value
            else:
                errors[name] = ["Enter a valid email address."]
        else:
            if value in rule["choices"]:
                cleaned[name] = value
            else:
                errors[name] = ["Select a valid choice. %s is not one of the available choices." % value]
    return [not errors, cleaned, errors]
''',
    tests=[
        [{"handle": " al ", "age": "x"}, {"handle": {"type": "char", "min_length": 3}, "age": {"type": "int"}}],
        [{"handle": "marisol", "email": "m@harbour.example", "age": "34", "plan": "crew", "bio": ""}, _SIGNUP],
        [{}, _SIGNUP],
        [{"handle": "   ", "email": " ", "plan": ""}, _SIGNUP],
        [{"handle": "averyveryverylonghandle", "email": "m@harbour", "age": "12", "plan": "gold"}, _SIGNUP],
        [{"handle": "  mari  ", "email": " m@h.io ", "age": " 121 ", "plan": "free", "bio": "x" * 21}, _SIGNUP],
        [{"handle": "abc", "email": "a@b@c.io", "age": "13", "plan": "free"}, _SIGNUP],
        [{"handle": "abcdefghijkl", "email": "@b.io", "age": "120", "plan": "free", "bio": "x" * 20}, _SIGNUP],
        [{"handle": "abc", "email": "a b@c.io", "age": "3.5", "plan": "Free"}, _SIGNUP],
        [{"handle": "abc", "email": "a@b..io", "age": "-5", "plan": "free"}, _SIGNUP],
        [{"n": "-7"}, {"n": {"type": "int"}}],
        [{"n": "--7", "m": "+7", "k": "007"}, {"n": {"type": "int"}, "m": {"type": "int"}, "k": {"type": "int", "min_value": 7}}],
        [{"extra": "ignored"}, {}],
        [{"t": "0"}, {"t": {"type": "int", "required": False, "min_value": 0, "max_value": 0}, "u": {"type": "email", "required": False}}],
        [{"e": "first.last@mail.harbour.example"}, {"e": {"type": "email"}}],
    ],
    examples=2,
    wrong_solutions=[
        '''def validate_form(data, fields):
    cleaned, errors = {}, {}
    for name, rule in fields.items():
        value = data.get(name, "")
        if value == "":
            if rule.get("required", True):
                errors[name] = ["This field is required."]
            else:
                cleaned[name] = ""
            continue
        cleaned[name] = int(value) if rule["type"] == "int" and value.lstrip("-").isdigit() else value
    return [not errors, cleaned, errors]
''',
        r'''import re
def validate_form(data, fields):
    cleaned, errors = {}, {}
    for name, rule in fields.items():
        value = data.get(name, "").strip()
        kind = rule["type"]
        if value == "":
            if rule.get("required", True):
                errors[name] = ["This field is required."]
            else:
                cleaned[name] = ""
            continue
        if kind == "char":
            n = len(value)
            if n < rule.get("min_length", 0):
                errors[name] = ["Ensure this value has at least %d characters (it has %d)." % (rule["min_length"], n)]
            elif n >= rule.get("max_length", 10 ** 9):
                errors[name] = ["Ensure this value has at most %d characters (it has %d)." % (rule["max_length"], n)]
            else:
                cleaned[name] = value
        elif kind == "int":
            try:
                v = int(value)
            except ValueError:
                errors[name] = ["Enter a whole number."]
                continue
            if v < rule.get("min_value", v):
                errors[name] = ["Ensure this value is greater than or equal to %d." % rule["min_value"]]
            elif v > rule.get("max_value", v):
                errors[name] = ["Ensure this value is less than or equal to %d." % rule["max_value"]]
            else:
                cleaned[name] = v
        elif kind == "email":
            if "@" in value and "." in value:
                cleaned[name] = value
            else:
                errors[name] = ["Enter a valid email address."]
        else:
            if value in rule["choices"]:
                cleaned[name] = value
            else:
                errors[name] = ["Select a valid choice. %s is not one of the available choices." % value]
    return [not errors, cleaned, errors]
''',
    ],
    guide=dict(
        prereqs="Lesson *Forms, ModelForm, validation and CSRF*; string methods and `re.fullmatch`.",
        intuition="Validation is a pipeline per field: normalise the raw text, handle emptiness, convert to the right "
                  "Python type, then check constraints. A field ends up in exactly one of two places: `cleaned_data` or "
                  "`errors`. Django's `Field.clean()` does `to_python` → `validate` → `run_validators` in this spirit.",
        hints=[
            "Deal with the empty case first; it is the same for every type except for the optional `int` giving `None`.",
            "Parse integers with a regex rather than `int()`, which accepts `+7`, `1_000` and surrounding spaces.",
            "Build messages with the *stripped* length and value.",
        ],
        brute_force="A long chain of field-specific `if` statements in the view (how people validated before form "
                    "classes). It mixes rules with flow and repeats itself; the table-driven loop is the same O(fields) work, reusable.",
        approach="""1. Loop over `fields` in order; `value = data.get(name, "").strip()`.
2. Empty → required error, or the optional default.
3. Dispatch on type; on success store the converted value in `cleaned`, on failure store `[message]` in `errors`.
4. Return `[not errors, cleaned, errors]`.

**Dry run** `{"handle": " al ", "age": "x"}`: handle → `"al"`, length 2 < 3 → error; age → `"x"` is not digits →
`Enter a whole number.` → `[False, {}, {...}]`.""",
        complexity="O(total length of the submitted values).",
        pitfalls="""- Forgetting to strip: `"   "` must count as empty, and lengths are measured after stripping.
- `int("+7")` and `int(" 7 ")` succeed in Python but are not accepted here.
- An optional empty integer cleans to `None`, not `0` and not `""`.
- `errors` values are lists, because real fields can accumulate several messages.""",
        follow_up="Add a form-level `clean()` step with a `must_match` rule (two password fields) that reports under the `__all__` key.",
    ),
),
dict(
    id="django-modelform-fields",
    title="Derive ModelForm fields from a model",
    difficulty="Medium",
    pattern="Forms",
    entry="form_fields",
    description=r"""
A `ModelForm` builds its form fields by inspecting the model. Implement that derivation for a model described
as data.

`form_fields(model, fields, exclude)`:

- `model`: list of field descriptors in declaration order. Each has `name`, `type` and optional flags
  `blank` (default `False`), `editable` (default `True`), `auto_now`, `auto_now_add`, `choices`.
- `fields`: `"__all__"`, a list of names, or `None`. `exclude`: a list of names or `None`.

**Editable fields.** A model field never appears in a form when its type is `AutoField` or `BigAutoField`,
when `editable` is `False`, or when `auto_now` or `auto_now_add` is true.

**Selection.**

- If `fields` and `exclude` are both `None`, return `None` (Django refuses to guess: `ImproperlyConfigured`).
- If `fields` is a list, the form has those fields **in that list's order**. If a listed name does not exist
  on the model or is not editable, return `None` (`FieldError`).
- If `fields` is `"__all__"` or `None`, start from all editable fields in model order.
- Finally remove every name in `exclude` (unknown names in `exclude` are ignored).

**Mapping** to `[name, form_field_class, required]`:

| model type | form field class |
|---|---|
| `CharField`, `TextField` | `CharField`, or `TypedChoiceField` when the descriptor has `choices` |
| `SlugField` | `SlugField` |
| `EmailField` | `EmailField` |
| `IntegerField` | `IntegerField` |
| `BooleanField` | `BooleanField` |
| `DateField` | `DateField` |
| `DateTimeField` | `DateTimeField` |
| `ForeignKey` | `ModelChoiceField` |
| `ManyToManyField` | `ModelMultipleChoiceField` |

`required` is `not blank`, except that a `BooleanField` is never required (an unticked box must be allowed).

**Example:** for a model with `id` (BigAutoField), `headline` (CharField) and `slug` (SlugField, blank),
`form_fields(model, "__all__", None)` → `[["headline", "CharField", True], ["slug", "SlugField", False]]`.
""",
    starter='''def form_fields(model: list, fields, exclude):
    pass
''',
    solution='''_MAP = {
    "CharField": "CharField", "TextField": "CharField", "SlugField": "SlugField", "EmailField": "EmailField",
    "IntegerField": "IntegerField", "BooleanField": "BooleanField", "DateField": "DateField",
    "DateTimeField": "DateTimeField", "ForeignKey": "ModelChoiceField", "ManyToManyField": "ModelMultipleChoiceField",
}


def _editable(f):
    if f["type"] in ("AutoField", "BigAutoField"):
        return False
    return f.get("editable", True) and not f.get("auto_now") and not f.get("auto_now_add")


def form_fields(model, fields, exclude):
    if fields is None and exclude is None:
        return None
    by_name = {f["name"]: f for f in model if _editable(f)}
    if isinstance(fields, list):
        for name in fields:
            if name not in by_name:
                return None
        names = list(fields)
    else:
        names = list(by_name)
    skip = set(exclude or [])
    out = []
    for name in names:
        if name in skip:
            continue
        f = by_name[name]
        cls = _MAP[f["type"]]
        if f["type"] in ("CharField", "TextField") and f.get("choices"):
            cls = "TypedChoiceField"
        required = False if f["type"] == "BooleanField" else not f.get("blank", False)
        out.append([name, cls, required])
    return out
''',
    tests=[
        [_MODEL[:3], "__all__", None],
        [_MODEL, "__all__", None],
        [_MODEL, None, None],
        [_MODEL, None, ["author", "tags", "nonexistent"]],
        [_MODEL, ["body", "headline"], None],
        [_MODEL, ["headline", "id"], None],
        [_MODEL, ["headline", "created"], None],
        [_MODEL, ["headline", "word_count"], None],
        [_MODEL, ["headline", "missing"], None],
        [_MODEL, ["status", "pinned", "tags", "goes_live"], ["pinned"]],
        [_MODEL, [], None],
        [_MODEL, "__all__", ["headline", "slug", "body", "status", "author", "tags", "pinned", "embargo", "contact", "goes_live"]],
        [[], "__all__", None],
        [[{"name": "n", "type": "IntegerField", "blank": True}, {"name": "ok", "type": "BooleanField", "blank": False}, {"name": "kind", "type": "TextField", "choices": ["a"], "blank": True}], None, []],
    ],
    examples=2,
    wrong_solutions=[
        '''_MAP = {"CharField": "CharField", "TextField": "CharField", "SlugField": "SlugField", "EmailField": "EmailField",
    "IntegerField": "IntegerField", "BooleanField": "BooleanField", "DateField": "DateField", "DateTimeField": "DateTimeField",
    "ForeignKey": "ModelChoiceField", "ManyToManyField": "ModelMultipleChoiceField"}
def form_fields(model, fields, exclude):
    out = []
    for f in model:
        if f["type"] in ("AutoField", "BigAutoField"):
            continue
        if isinstance(fields, list) and f["name"] not in fields:
            continue
        if exclude and f["name"] in exclude:
            continue
        out.append([f["name"], _MAP[f["type"]], not f.get("blank", False)])
    return out
''',
        '''_MAP = {"CharField": "CharField", "TextField": "CharField", "SlugField": "SlugField", "EmailField": "EmailField",
    "IntegerField": "IntegerField", "BooleanField": "BooleanField", "DateField": "DateField", "DateTimeField": "DateTimeField",
    "ForeignKey": "ModelChoiceField", "ManyToManyField": "ModelMultipleChoiceField"}
def form_fields(model, fields, exclude):
    if fields is None and exclude is None:
        return None
    ok = [f for f in model if f["type"] not in ("AutoField", "BigAutoField") and f.get("editable", True)
          and not f.get("auto_now") and not f.get("auto_now_add")]
    names = [f["name"] for f in ok]
    if isinstance(fields, list):
        if any(n not in names for n in fields):
            return None
        ok = [f for f in ok if f["name"] in fields]
    out = []
    for f in ok:
        if f["name"] in (exclude or []):
            continue
        cls = "TypedChoiceField" if f.get("choices") else _MAP[f["type"]]
        out.append([f["name"], cls, not f.get("blank", False)])
    return out
''',
    ],
    guide=dict(
        prereqs="Lesson *Forms, ModelForm, validation and CSRF*.",
        intuition="A ModelForm is a translation table plus two filters. Filter one: which model fields can a human edit at "
                  "all? Filter two: which of those did `Meta.fields`/`Meta.exclude` ask for, and in what order? Then each "
                  "survivor is translated to a form field class, with `blank` deciding `required`.",
        hints=[
            "Build a dict of editable fields keyed by name first; everything else reads from it.",
            "An explicit `fields` list dictates the order; `__all__` uses model order.",
            "Special-case `BooleanField` (never required) and `choices` (a select box).",
        ],
        brute_force="Write each form class by hand, repeating every field's type and `max_length`. It drifts out of sync with the model the first time someone adds a column.",
        approach="""1. Both `fields` and `exclude` missing → `None`.
2. Collect editable fields. A listed name that is not among them → `None`.
3. Choose the name order, drop excluded names, map each to `[name, class, required]`.

**Dry run** `fields=["body", "headline"]`: both editable → order body, headline →
`[["body", "CharField", True], ["headline", "CharField", True]]`.""",
        complexity="O(F) for F model fields.",
        pitfalls="""- Returning model order when an explicit `fields` list asked for another order.
- Including `auto_now_add` timestamps or `editable=False` columns.
- Marking `BooleanField` as required, which would force the box to be ticked.
- Silently accepting a typo in `fields`; Django fails loudly and so should you.""",
        follow_up="Carry `max_length` across to the form field and add `help_text`/`label` derivation from `verbose_name`.",
    ),
),
dict(
    id="django-csrf-compare",
    title="Check a masked CSRF token",
    difficulty="Medium",
    pattern="Security",
    entry="csrf_ok",
    description=r"""
Django stores a 32-character CSRF **secret** (in a cookie or the session). The value it prints into forms is not
the secret itself but a 64-character **masked token** that changes on every page load, so that compression
side-channel attacks cannot recover it. The server must *unmask* the submitted token and compare.

Alphabet: `CHARS = string.ascii_letters + string.digits`, i.e. `a-z`, then `A-Z`, then `0-9` (62 characters;
`a` has index 0, `A` 26, `0` 52).

Masking a secret `s` with a random 32-character mask `m`: for each position
`cipher[i] = CHARS[(index(s[i]) + index(m[i])) % 62]`; the token is `m + cipher`.

`csrf_ok(token, secret)` returns `True` or `False`:

- `secret` is always a valid 32-character string over the alphabet.
- If `token` is not a string, or contains a character outside the alphabet, return `False`.
- If `len(token) == 64`: split it into mask (first 32) and cipher (last 32), recover each secret character as
  `CHARS[(index(cipher[i]) - index(mask[i])) % 62]`, and return whether the result equals `secret`.
- If `len(token) == 32`: it is an unmasked secret; return whether it equals `secret`.
- Any other length → `False`.

Use `hmac.compare_digest` (constant-time) for the final comparison, as Django does.

**Example:** secret `"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"`, mask `"b" * 32` gives cipher `"b" * 32`, so the token
`"b" * 64` is valid for that secret.
""",
    starter='''def csrf_ok(token, secret: str) -> bool:
    pass
''',
    solution='''import hmac
import string

CHARS = string.ascii_letters + string.digits


def csrf_ok(token, secret):
    if not isinstance(token, str) or any(c not in CHARS for c in token):
        return False
    if len(token) == 64:
        mask, cipher = token[:32], token[32:]
        token = "".join(CHARS[(CHARS.index(c) - CHARS.index(m)) % len(CHARS)] for c, m in zip(cipher, mask))
    elif len(token) != 32:
        return False
    return hmac.compare_digest(token, secret)
''',
    tests=[
        ["b" * 64, "a" * 32],
        [_mask(_SECRET, _MASK1), _SECRET],
        [_mask(_SECRET, _MASK2), _SECRET],
        [_mask(_SECRET, _MASK1), _OTHER],
        [_SECRET, _SECRET],
        [_OTHER, _SECRET],
        [_MASK1 + _SECRET, _SECRET],
        ["", _SECRET],
        [None, _SECRET],
        [_mask(_SECRET, _MASK1)[:-1], _SECRET],
        [_mask(_SECRET, _MASK1) + "a", _SECRET],
        [_mask(_SECRET, _MASK1)[:-1] + "-", _SECRET],
        ["a" * 32 + _SECRET, _SECRET],
        [_mask(_OTHER, "9" * 32), _OTHER],
        [_mask(_SECRET, _MASK1).swapcase(), _SECRET],
        [12345, _SECRET],
    ],
    examples=2,
    wrong_solutions=[
        '''def csrf_ok(token, secret):
    return token == secret
''',
        '''import string
CHARS = string.ascii_letters + string.digits
def csrf_ok(token, secret):
    if not isinstance(token, str) or any(c not in CHARS for c in token):
        return False
    if len(token) == 64:
        mask, cipher = token[:32], token[32:]
        token = "".join(CHARS[(CHARS.index(c) + CHARS.index(m)) % 62] for c, m in zip(cipher, mask))
    return token == secret
''',
        '''import string
CHARS = string.ascii_letters + string.digits
def csrf_ok(token, secret):
    if not isinstance(token, str):
        return False
    if len(token) == 64:
        return token[32:] == secret
    return token == secret
''',
    ],
    guide=dict(
        prereqs="Lesson *Forms, ModelForm, validation and CSRF*; modular arithmetic.",
        intuition="Masking is a one-time pad over a 62-letter alphabet: add the mask letter by letter, modulo 62. Unmasking "
                  "subtracts it again. The mask travels with the token, so no state is needed on the server beyond the secret.",
        hints=[
            "Validate type and alphabet before indexing, or `CHARS.index` will raise.",
            "Subtract the mask index from the cipher index and take `% 62`; Python's modulo is non-negative for a positive modulus.",
            "A 32-character token is compared directly; anything not 32 or 64 long fails.",
        ],
        brute_force="There is nothing to search here; the naive version is plain `token == secret`, which rejects every masked token and leaks timing information.",
        approach="""1. Reject non-strings and out-of-alphabet characters.
2. Length 64 → unmask with per-character subtraction modulo 62. Length 32 → use as is. Otherwise `False`.
3. Compare with `hmac.compare_digest`.

**Dry run** token `"b" * 64`, secret `"a" * 32`: mask `b` (index 1), cipher `b` (index 1) → `(1 - 1) % 62 = 0` → `a`
for each position → equals the secret → `True`.""",
        complexity="O(n) with n = 64; `CHARS.index` is a constant-size scan (precompute a dict for speed).",
        pitfalls="""- Adding instead of subtracting when unmasking.
- Comparing only the second half to the secret.
- Using `==`, which stops at the first differing byte and can leak how many leading characters matched.
- Forgetting that the token might be missing entirely (`None`).""",
        follow_up="Django additionally checks the `Origin`/`Referer` header on HTTPS requests. Add an `origin_ok(origin, host, trusted)` helper.",
    ),
),
dict(
    id="django-slugify",
    title="slugify: titles into URL-safe slugs",
    difficulty="Easy",
    pattern="Text",
    entry="slugify",
    description=r"""
A **slug** is the readable part of a URL that identifies a page, such as `first-hike-of-spring` in
`/journal/first-hike-of-spring/`. Implement Django's `django.utils.text.slugify` in its default ASCII mode.

`slugify(value)` applies these steps in order:

1. Convert the text to its Unicode **NFKD** normal form and drop every character that is not ASCII
   (so `é` becomes `e`, and characters with no ASCII decomposition, such as `ß` or `日`, vanish).
2. Lower-case the result.
3. Remove every character that is not a word character (`a-z`, `0-9`, `_`), whitespace or a hyphen.
4. Replace each run of whitespace and/or hyphens with a single `-`.
5. Strip leading and trailing `-` and `_` characters.

**Examples:** `slugify("First Hike of Spring!")` → `"first-hike-of-spring"`;
`slugify("  Crème brûlée -- at 9°C ")` → `"creme-brulee-at-9c"`; `slugify("???")` → `""`.
""",
    starter='''def slugify(value: str) -> str:
    pass
''',
    solution=r'''import re
import unicodedata


def slugify(value):
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")
''',
    tests=[
        ["First Hike of Spring!"],
        ["  Crème brûlée -- at 9°C "],
        ["???"],
        [""],
        ["already-a-slug"],
        ["snake_case stays_put"],
        ["__dunder__ title__"],
        ["Tabs\tand\nnewlines  everywhere"],
        ["Rock & Roll: 50% off (today)"],
        ["Ærøskøbing / Zürich / Łódź"],
        ["---"],
        ["A - B - C"],
        ["日本語 title 2026"],
        ["ﬁne ligature ½ price"],
        ["MiXeD CaSe 123"],
        ["trailing dash- "],
    ],
    examples=3,
    wrong_solutions=[
        '''def slugify(value):
    return value.strip().lower().replace(" ", "-")
''',
        r'''import re
def slugify(value):
    value = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return value.strip("-")
''',
    ],
    guide=dict(
        prereqs="Lesson *Foreign keys, detail views and slugs*; `unicodedata.normalize`; `re.sub`.",
        intuition="Slugifying is a funnel of clean-ups, each one narrowing the alphabet: accents off, case folded, "
                  "punctuation dropped, separators collapsed, edges trimmed. NFKD splits `é` into `e` plus a combining "
                  "accent; encoding to ASCII with `ignore` then discards the accent and keeps the letter.",
        hints=[
            "`unicodedata.normalize(\"NFKD\", s).encode(\"ascii\", \"ignore\").decode(\"ascii\")` performs step 1.",
            "Remove unwanted characters *before* collapsing separators, otherwise `a & b` leaves a double hyphen.",
            "Underscores are word characters: they survive inside, but are stripped from the ends.",
        ],
        brute_force="Loop over characters with a hand-written table of accents. It works for the letters you remembered and fails for the rest; normal forms cover all of Unicode.",
        approach="""1. Normalise and drop non-ASCII. 2. Lower-case. 3. `re.sub(r"[^\\w\\s-]", "", ...)`.
4. `re.sub(r"[-\\s]+", "-", ...)`. 5. `.strip("-_")`.

**Dry run** `"  Crème brûlée -- at 9°C "` → `"  Creme brulee -- at 9C "` (the degree sign has no ASCII form) →
lower → punctuation step changes nothing → runs of space/hyphen become `-` → `-creme-brulee-at-9c-` → strip →
`creme-brulee-at-9c`.""",
        complexity="O(n) time and space.",
        pitfalls="""- Replacing punctuation with a hyphen instead of deleting it gives `rock---roll`.
- Stripping only hyphens leaves leading underscores.
- Two different titles can produce the same slug, and some titles produce an empty one; a real model needs a
  uniqueness strategy (append `-2`, or put the primary key in the URL as well).""",
        follow_up="Write `unique_slug(title, existing)` that appends `-2`, `-3`, ... until the slug is not in the set.",
    ),
),
dict(
    id="django-pagination",
    title="A paginator page with an elided page range",
    difficulty="Medium",
    pattern="Views",
    entry="page_info",
    description=r"""
`ListView` with `paginate_by` hands the template a `page_obj`. Compute what it knows, including the compact page
list `1 … 4 5 [6] 7 8 … 20` produced by `Paginator.get_elided_page_range`.

`page_info(total, per_page, number, on_each_side, on_ends)`:

- `total` items (≥ 0), `per_page` ≥ 1. `num_pages = max(1, ceil(total / per_page))` (an empty list still has
  one, empty, page).
- If `number` is not an integer in `1..num_pages` return `None` (Django raises `EmptyPage`).
- Otherwise return a dict with:
  - `num_pages`;
  - `has_previous`, `has_next`;
  - `start_index`, `end_index`: 1-based positions of the first and last item on the page (both `0` when `total` is 0);
  - `page_range`: a list of page numbers and the string `"…"`, built as follows.

**Elided range.** If `num_pages <= (on_each_side + on_ends) * 2`, list every page. Otherwise:

- *Left part.* If `number > on_each_side + on_ends + 2`: pages `1..on_ends`, then `"…"`, then
  `number - on_each_side .. number`. Else: pages `1..number`.
- *Right part.* If `number < num_pages - on_each_side - on_ends - 1`: pages
  `number + 1 .. number + on_each_side`, then `"…"`, then the last `on_ends` pages. Else:
  pages `number + 1 .. num_pages`.

**Example:** `page_info(200, 10, 10, 2, 1)` → `page_range` `[1, "…", 8, 9, 10, 11, 12, "…", 20]`,
`start_index` 91, `end_index` 100.
""",
    starter='''def page_info(total: int, per_page: int, number: int, on_each_side: int, on_ends: int):
    pass
''',
    solution='''def page_info(total, per_page, number, on_each_side, on_ends):
    num_pages = max(1, -(-total // per_page))
    if isinstance(number, bool) or not isinstance(number, int) or number < 1 or number > num_pages:
        return None
    if num_pages <= (on_each_side + on_ends) * 2:
        pages = list(range(1, num_pages + 1))
    else:
        pages = []
        if number > on_each_side + on_ends + 2:
            pages += list(range(1, on_ends + 1)) + ["…"] + list(range(number - on_each_side, number + 1))
        else:
            pages += list(range(1, number + 1))
        if number < num_pages - on_each_side - on_ends - 1:
            pages += list(range(number + 1, number + on_each_side + 1)) + ["…"]
            pages += list(range(num_pages - on_ends + 1, num_pages + 1))
        else:
            pages += list(range(number + 1, num_pages + 1))
    return {
        "num_pages": num_pages,
        "has_previous": number > 1,
        "has_next": number < num_pages,
        "start_index": 0 if total == 0 else (number - 1) * per_page + 1,
        "end_index": min(number * per_page, total),
        "page_range": pages,
    }
''',
    tests=[
        [200, 10, 10, 2, 1],
        [45, 10, 1, 2, 1],
        [45, 10, 5, 2, 1],
        [0, 10, 1, 2, 1],
        [0, 10, 2, 2, 1],
        [45, 10, 0, 2, 1],
        [45, 10, 6, 2, 1],
        [200, 10, 1, 2, 1],
        [200, 10, 20, 2, 1],
        [200, 10, 4, 2, 1],
        [200, 10, 5, 2, 1],
        [200, 10, 6, 2, 1],
        [200, 10, 16, 2, 1],
        [200, 10, 17, 2, 1],
        [1000, 7, 71, 3, 2],
        [10, 10, 1, 3, 2],
        [11, 10, 2, 0, 0],
        [70, 10, 4, 1, 2],
        [70, 10, "3", 1, 2],
    ],
    examples=2,
    wrong_solutions=[
        '''def page_info(total, per_page, number, on_each_side, on_ends):
    num_pages = total // per_page + 1
    if not isinstance(number, int) or number < 1 or number > num_pages:
        return None
    return {"num_pages": num_pages, "has_previous": number > 1, "has_next": number < num_pages,
            "start_index": (number - 1) * per_page + 1, "end_index": number * per_page,
            "page_range": list(range(1, num_pages + 1))}
''',
        '''def page_info(total, per_page, number, on_each_side, on_ends):
    num_pages = max(1, -(-total // per_page))
    if isinstance(number, bool) or not isinstance(number, int) or number < 1 or number > num_pages:
        return None
    pages = []
    if number > on_each_side + on_ends + 1:
        pages += list(range(1, on_ends + 1)) + ["…"] + list(range(number - on_each_side, number + 1))
    else:
        pages += list(range(1, number + 1))
    if number < num_pages - on_each_side - on_ends:
        pages += list(range(number + 1, number + on_each_side + 1)) + ["…"] + list(range(num_pages - on_ends + 1, num_pages + 1))
    else:
        pages += list(range(number + 1, num_pages + 1))
    return {"num_pages": num_pages, "has_previous": number > 1, "has_next": number < num_pages,
            "start_index": 0 if total == 0 else (number - 1) * per_page + 1, "end_index": min(number * per_page, total),
            "page_range": pages}
''',
    ],
    guide=dict(
        prereqs="Lesson *ListView, querysets and tests with a database* (pagination); integer ceiling division.",
        intuition="A page is a window of `per_page` items; everything follows from `number` and `num_pages`. The elided "
                  "range is two independent halves, left of and right of the current page. A half is abbreviated only "
                  "when the gap it would hide is at least two pages wide, because an ellipsis that hides a single page saves nothing.",
        hints=[
            "Ceiling division without floats: `-(-total // per_page)`.",
            "Build the left half ending at `number`, then the right half starting at `number + 1`.",
            "The `+ 2` and `- 1` in the conditions are what prevent an ellipsis standing in for exactly one page.",
        ],
        brute_force="Generate the full range and delete pages that are far from the current one and from the ends, then "
                    "insert ellipses where numbers jump. O(num_pages) per render, versus O(on_each_side + on_ends) for the direct construction.",
        approach="""1. Compute `num_pages`; validate `number`.
2. Short ranges are listed in full.
3. Left half and right half by the two rules.
4. Indices: `start = (number-1)*per_page + 1`, `end = min(number*per_page, total)`, with the empty-list special case.

**Dry run** `(200, 10, 4, 2, 1)`: 20 pages. Left: `4 > 2+1+2`? No → `1,2,3,4`. Right: `4 < 20-2-1-1 = 16` → `5,6`,
`…`, `20`. Result `[1,2,3,4,5,6,"…",20]`.""",
        complexity="O(on_each_side + on_ends) for the elided range (O(num_pages) when it is listed in full).",
        pitfalls="""- `total // per_page + 1` gives one page too many when `total` is an exact multiple.
- `end_index` on the last page is `total`, not `number * per_page`.
- Zero items still means one valid page with indices 0.
- Off-by-one in the ellipsis thresholds shows `1 … 3` where `1 2 3` is shorter and clearer.""",
        follow_up="Page numbers do not scale to huge tables (`OFFSET 1000000` is slow). Read about keyset/cursor pagination in the DRF lesson.",
    ),
),
dict(
    id="django-password-validators",
    title="Run the password validator set",
    difficulty="Easy",
    pattern="Auth",
    entry="password_errors",
    description=r"""
`AUTH_PASSWORD_VALIDATORS` lists four validators in a default project. Django runs **all** of them and reports
every failure, in the order they are configured. Implement a simplified but precisely defined version.

`password_errors(password, user, common)` returns the list of error codes, in this order:

1. `"password_too_similar"`: take every string value in the `user` dict (for example username, e-mail, first
   name). Split each value into parts on runs of non-word characters (anything except letters, digits and
   `_`), and also consider the whole value. If any part of **length 3 or more** occurs inside the password,
   ignoring case, the password is too similar. (Real Django uses a fuzzy ratio; this is the simplified rule.)
2. `"password_too_short"`: fewer than 8 characters.
3. `"password_too_common"`: the lower-cased password is in the list `common` (already lower-case).
4. `"password_entirely_numeric"`: the password consists only of digits (and is not empty).

Return `[]` for an acceptable password.

**Example:** user `{"username": "marisol.reyes"}`: `password_errors("Reyes2026", user, [])` →
`["password_too_similar"]`; `password_errors("1234", user, [])` → `["password_too_short", "password_entirely_numeric"]`.
""",
    starter='''def password_errors(password: str, user: dict, common: list) -> list:
    pass
''',
    solution=r'''import re


def password_errors(password, user, common):
    errors = []
    lowered = password.lower()
    similar = False
    for value in user.values():
        if not isinstance(value, str):
            continue
        for part in re.split(r"\W+", value) + [value]:
            if len(part) >= 3 and part.lower() in lowered:
                similar = True
    if similar:
        errors.append("password_too_similar")
    if len(password) < 8:
        errors.append("password_too_short")
    if lowered in common:
        errors.append("password_too_common")
    if password.isdigit():
        errors.append("password_entirely_numeric")
    return errors
''',
    tests=[
        ["Reyes2026", {"username": "marisol.reyes"}, []],
        ["1234", {"username": "marisol.reyes"}, []],
        ["tide-Chart-88-lamp", _USER, _COMMON],
        ["", _USER, _COMMON],
        ["12345678", _USER, _COMMON],
        ["PASSWORD", _USER, _COMMON],
        ["xXMARISOLXx99", _USER, _COMMON],
        ["harbour-lights", _USER, _COMMON],
        ["mari@harbour.example", _USER, _COMMON],
        ["908172635445", _USER, _COMMON],
        ["LetMeIn123", _USER, _COMMON],
        ["correct horse", {"username": "al", "first_name": "Bo", "id": 7}, _COMMON],
        ["al-and-bo-99", {"username": "al", "first_name": "Bo", "id": 7}, _COMMON],
        ["mar", _USER, ["mar"]],
        ["éclair-éclair", {}, []],
        ["ann_lee_2026", {"username": "ann_lee"}, []],
    ],
    examples=2,
    wrong_solutions=[
        '''def password_errors(password, user, common):
    if len(password) < 8:
        return ["password_too_short"]
    if password.lower() in common:
        return ["password_too_common"]
    if password.isdigit():
        return ["password_entirely_numeric"]
    return []
''',
        r'''import re
def password_errors(password, user, common):
    errors = []
    for value in user.values():
        if isinstance(value, str) and value in password and "password_too_similar" not in errors:
            errors.append("password_too_similar")
    if len(password) <= 8:
        errors.append("password_too_short")
    if password in common:
        errors.append("password_too_common")
    if password.isdigit():
        errors.append("password_entirely_numeric")
    return errors
''',
    ],
    guide=dict(
        prereqs="Lesson *The auth app: users, passwords and sessions*; `re.split`.",
        intuition="Validators are independent yes/no checks run one after another, and the user deserves to see every "
                  "problem at once rather than fixing them one submit at a time. So: no early return, append as you go, keep the configured order.",
        hints=[
            "Lower-case the password once and reuse it for the similarity and common checks.",
            "`re.split(r\"\\W+\", value)` yields the parts; add the whole value to the list too.",
            "Collect errors in a list; never `return` after the first failure.",
        ],
        brute_force="No search is involved. The naive mistake is returning at the first failed rule, which hides the remaining problems from the user.",
        approach="""1. Similarity: any part (length ≥ 3) of any string attribute inside the lower-cased password.
2. Length below 8. 3. Membership in the common list. 4. `isdigit()`.

**Dry run** `"1234"`: no attribute part is contained → skip; length 4 → too short; not in the common list;
all digits → numeric. Result `["password_too_short", "password_entirely_numeric"]`.""",
        complexity="O(A · P) for total attribute length A and password length P (substring checks), plus O(C) for the common-list scan (a set makes it O(1); Django's real list has about 20,000 entries).",
        pitfalls="""- Stopping at the first error.
- Case-sensitive comparison lets `PASSWORD` through.
- Two-letter name parts would match almost everything; the length-3 floor avoids false alarms.
- `"".isdigit()` is `False`, so the empty password is short but not 'numeric'.
- Non-string attributes (an integer id) must be skipped, not crash.""",
        follow_up="Write a custom validator class with `validate(password, user)` and `get_help_text()` that requires one non-alphanumeric symbol, and add it to `AUTH_PASSWORD_VALIDATORS`.",
    ),
),
]
