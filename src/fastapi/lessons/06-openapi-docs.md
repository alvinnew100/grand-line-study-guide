# Headers, cookies, forms of input and automatic docs

> **Before this lesson:** you should be able to declare path and query parameters
> ([lesson 4](#/lesson/fastapi/first-app)) and a JSON body with a Pydantic model
> ([lesson 5](#/lesson/fastapi/body-responses)), and know what headers and cookies are in an HTTP
> message ([lesson 1](#/lesson/fastapi/http-basics)).

## In plain words

A request can carry information in five places: the path, the query string, the body, the headers
and the cookies. You already know the first three. The first half of this lesson covers the remaining
two and gives you one table for all of them.

The second half is about a feature many people name as their favourite thing in FastAPI. Your program
can describe itself. From the functions and models you have written, FastAPI produces a complete,
machine-readable description of the API, and from that description a web page where anyone can read
about each endpoint and try it out.

An everyday picture: a restaurant whose printed menu is produced automatically from the kitchen's own
recipe cards. Change a recipe and the menu changes with it; the menu can never promise a dish the
kitchen no longer makes. The description of your API is that menu, and its standard format is called
**OpenAPI**.

Why this matters for a job: other teams will use your API by reading that page, and tools will
generate code from the description. Interviewers ask "what is OpenAPI and how does FastAPI produce
it?" because the answer shows whether you understand what the framework does with your type hints.

## Headers

Recall that a header is a `Name: value` line of metadata in the request. To read one, declare a
parameter as you would a query parameter, and mark it with `Header()`:

```python
from typing import Annotated
from fastapi import FastAPI, Header

app = FastAPI()

@app.get("/agent")
def get_agent(user_agent: Annotated[str | None, Header()] = None):
    return {"User-Agent": user_agent}
```

- `from fastapi import FastAPI, Header` loads the marker.
- `user_agent: Annotated[str | None, Header()] = None` means: an optional piece of text, taken from
  the request headers, `None` when the header was not sent.
- The function returns the value so that you can see it. A browser would produce something like
  `{"User-Agent": "Mozilla/5.0 ..."}`.

Two conveniences are at work:

- **Underscore conversion.** A Python name cannot contain a hyphen, but header names are full of
  them. FastAPI therefore converts `user_agent` into the header name `user-agent`. You can turn this
  off with `Header(convert_underscores=False)`, though that is rarely wise: some proxies throw away
  headers whose names contain underscores.
- **Case does not matter.** `User-Agent`, `user-agent` and `USER-AGENT` all match, as HTTP requires.

A header that appears several times in one request can be collected as a list:
`x_token: Annotated[list[str] | None, Header()] = None`.

Lubanovic's tour uses a header to pass the same "who" value that he earlier sent through the path,
the query and the body, and then observes that headers are the natural home for *metadata* (login
tokens, content types, request IDs) and not for the data your application is about.

Related headers can be grouped in a Pydantic model (FastAPI 0.115 and later), exactly as query
parameters were grouped in lesson 4:

```python
class CommonHeaders(BaseModel):
    host: str
    save_data: bool
    if_modified_since: str | None = None
    traceparent: str | None = None
    x_tag: list[str] = []

@app.get("/items/")
def read_items(headers: Annotated[CommonHeaders, Header()]):
    return headers
```

Each field of `CommonHeaders` is one header: `save_data` reads `save-data`, `if_modified_since` reads
`if-modified-since`, and `x_tag` gathers every `x-tag` header into a list.

## Cookies

A cookie is a small named value that the server asks a browser to keep and send back with every later
request to the same site. Reading one looks the same as reading a header, with `Cookie()` as the
marker:

```python
from fastapi import Cookie

@app.get("/items/")
def read_items(session_id: Annotated[str | None, Cookie()] = None):
    return {"session_id": session_id}
```

Here the endpoint reads a cookie named `session_id`. A **session** is the server's record of one
logged-in visit, and the cookie holds the ticket number for it.

Cookies are *set* with `response.set_cookie(...)`, shown in lesson 5. For a session cookie always pass
`httponly=True` (JavaScript in the page cannot read it, which limits the damage of an attack called
cross-site scripting, or XSS, where an attacker manages to run their own script in your page),
`secure=True` (sent over HTTPS only) and a suitable `samesite` value (`"lax"` or `"strict"`).

## Accessing the raw `Request`

Occasionally you need something that FastAPI's declarations do not cover: the client's network
address, the body as untouched bytes, or every header at once. Declare a parameter of type `Request`:

```python
from fastapi import Request

@app.post("/webhook")
async def webhook(request: Request):
    raw = await request.body()          # bytes - needed to verify an HMAC signature
    sig = request.headers.get("x-signature")
    ip = request.client.host if request.client else None
    return {"bytes": len(raw), "ip": ip}
```

- `async def` is used because reading the body is an operation that must be awaited.
- `await request.body()` returns the body as raw bytes.
- `request.headers.get("x-signature")` reads one header by name, giving `None` if it is absent.
- `request.client.host` is the client's address, when known.

Data read this way is **not** validated and does **not** appear in the documentation, so use it
sparingly. One legitimate case is a **webhook**: a request that another company's system sends *to
you* when something happens (a payment succeeded, for instance). Webhooks are usually signed. The
sender computes a keyed fingerprint of the body, called an **HMAC** (hash-based message authentication
code), and puts it in a header; you recompute it to prove the message is authentic. The fingerprint is
calculated over the *exact* bytes sent, so you must verify against the raw body. Parsing the JSON and
writing it out again could change spacing or key order and break the check.

## The full input decision table

| Source | Declaration | Validated | In docs |
|---|---|---|---|
| Path | name in template, or `Path()` | yes | yes |
| Query | simple type, or `Query()` | yes | yes |
| Header | `Header()` | yes | yes |
| Cookie | `Cookie()` | yes | yes |
| JSON body | `BaseModel`, or `Body()` | yes | yes |
| Form fields | `Form()` (needs `python-multipart`) | yes | yes |
| Files | `File()` / `UploadFile` | yes | yes |
| Anything | `Request` | **no** | **no** |

Lubanovic's "Which Method Is Best?" discussion arrives at the same place as this table: path for
identity, query for adjustments, body for data, headers for metadata. Declaring them in the function
signature also documents the choice, which brings us to the second half.

## OpenAPI: the contract generated from your code

A **schema** is a formal description of the shape of some data: which fields exist, their types and
their rules. **OpenAPI** (formerly called Swagger) is a standard for describing a whole HTTP API in
one document, written in JSON or in YAML (a more human-friendly notation for the same kind of data).
It lists the paths, the methods allowed on each, every parameter, the request bodies, the possible
responses and the login methods. Because it is a standard and not tied to Python, tools written in
any language can read it.

FastAPI builds this document from your declarations and serves it at `/openapi.json`. Two ready-made
web pages display it:

- **Swagger UI** at `/docs` is interactive. Its "Try it out" button sends real requests, including
  logging in.
- **ReDoc** at `/redoc` is a tidy three-column reference manual.

The shapes of your models are written in **JSON Schema**, a companion standard for describing JSON
data, which Pydantic generates. That is why the docs can show exact types, limits (`minLength`,
`maximum`, `pattern`), allowed values and examples. Lubanovic stresses the consequence in chapter 3:
the documentation is not a separate file that slowly falls out of date. It is produced from the code,
so it cannot disagree with the code.

See the JSON Schema of a model for yourself:

```python-run
import json
from typing import Literal
from pydantic import BaseModel, Field

class PredictRequest(BaseModel):
    """Features for a single house."""
    sqft: float = Field(gt=0, description="Living area in square feet", examples=[1450])
    bedrooms: int = Field(ge=0, le=20)
    city: Literal["Austin", "Boston", "Denver"]
    tags: list[str] = []

# This JSON Schema is what FastAPI embeds under components/schemas in /openapi.json
print(json.dumps(PredictRequest.model_json_schema(), indent=2))
```

What to look for in the output:

- `"description": "Features for a single house."` came from the **docstring**, the text in triple
  quotes directly under the `class` line.
- Under `"properties"` there is one entry per field. `sqft` has `"exclusiveMinimum": 0.0` (from
  `gt=0`), its description and its example. `bedrooms` has `"minimum": 0` and `"maximum": 20`.
  `city` has `"enum": ["Austin", "Boston", "Denver"]`, from the `Literal`.
- `"required": ["sqft", "bedrooms", "city"]` lists the fields with no default. `tags` is absent from
  that list because it has one.

FastAPI places exactly this structure inside `/openapi.json`.

### Enriching the docs

Everything below changes the documentation from within your Python code. No separate documentation
files are needed:

```python
app = FastAPI(
    title="House Price API",
    summary="Predicts sale prices.",
    description="Markdown **supported**. Links, lists, code blocks...",
    version="1.4.0",
    contact={"name": "ML Platform", "email": "ml@example.com"},
    license_info={"name": "MIT"},
    openapi_tags=[{"name": "predict", "description": "Inference endpoints"}],
)

@app.post(
    "/v1/predict",
    tags=["predict"],
    summary="Predict a price",
    response_description="The predicted price in USD",
    responses={404: {"description": "Model not loaded"}, 429: {"description": "Rate limited"}},
    deprecated=False,
    operation_id="predict_v1",
)
def predict(req: PredictRequest) -> PredictResponse:
    """
    Predict the sale price of a house.

    - **sqft**: living area
    - **city**: one of the supported markets
    """
```

The first call describes the API as a whole: a title, a one-line summary, a longer description, a
version number, a contact and a licence. The decorator then describes one endpoint.

- A function's **docstring** becomes the endpoint's description, and may use Markdown formatting.
- **`tags`** group endpoints under headings in the page.
- **`responses`** documents additional status codes, and can attach a model for the error body.
- **`examples`** on fields, or `Body(openapi_examples=...)`, provide sample request bodies in Swagger UI.
- **`deprecated=True`** greys an endpoint out, which is useful while moving clients to a new version.
- **`include_in_schema=False`** hides an endpoint, for example an internal health check, from the
  document while leaving it working.
- **`operation_id`** gives the endpoint a stable machine name, which matters for generated code (below).

### Controlling or disabling the docs

```python
app = FastAPI(docs_url="/api/docs", redoc_url=None, openapi_url="/api/openapi.json")
# In some production deployments:
app = FastAPI(openapi_url=None)       # disables /openapi.json, /docs and /redoc
```

The first line moves the pages to different addresses and switches ReDoc off. The second form switches
off the description itself, and with it both pages, since they have nothing left to display.

Turning the docs off in production is a judgement call. It hides the list of endpoints from casual
visitors, but it is *not* a security measure: the endpoints still exist and still answer. Many
internal APIs keep the docs available behind a login.

### Why the schema matters beyond pretty pages

- **Client generation.** Tools such as `openapi-generator` or `openapi-typescript` read
  `/openapi.json` and write a ready-to-use client library (often called an **SDK**, software
  development kit) in TypeScript, Kotlin, Go and other languages. Set `operation_id` values (or a
  `generate_unique_id_function`) so the generated functions get readable names.
- **Contract testing.** Tools such as Schemathesis read the schema and send your API thousands of
  generated inputs, hunting for ones that make it crash. Throwing semi-random input at a program in
  this way is known as *fuzz testing*.
- **Gateways.** An API gateway (a managed front door such as Kong or AWS API Gateway) can import the
  document to set up routing and input checking.
- **AI tool use.** An OpenAPI description is a ready-made list of tools for an AI agent.

> [!INTERVIEW]
> "What is OpenAPI and how does FastAPI produce it?" — OpenAPI is a standard machine-readable
> description of an HTTP API. FastAPI walks every registered route (it does so lazily, on the first
> request for `/openapi.json`), converts parameters and Pydantic models to JSON Schema, adds the
> metadata from decorators and docstrings, and caches the result. Swagger UI and ReDoc are static
> pages that display that JSON. The benefits: documentation that always matches the code, client
> generation, and contract testing.

## A worked example: one endpoint using every input

```python
@app.put("/v1/users/{user_id}/avatar-settings")
def update_settings(
    user_id: Annotated[int, Path(ge=1)],                        # path
    settings: AvatarSettings,                                   # JSON body
    dry_run: bool = False,                                      # query
    x_request_id: Annotated[str | None, Header()] = None,       # header  -> X-Request-ID
    session: Annotated[str | None, Cookie()] = None,            # cookie
):
    ...
```

One request to this endpoint is read from five places, and the signature says so line by line: an id
from the path (at least 1), a JSON body checked against a model, an optional true/false flag from the
query, an optional `X-Request-ID` header and an optional cookie. Each is validated, and each appears
in the docs labelled with its location (`in: path`, `in: query`, `in: header`, `in: cookie`,
`requestBody`).

## Anatomy of an OpenAPI document

It is worth reading a real `/openapi.json` once, because every tool mentioned above consumes exactly
this structure. For a single endpoint the document has four parts: general information (`info`), a
`paths` object organised by address and method, reusable model descriptions under
`components.schemas`, and the login methods under `securitySchemes`.

```json
{
  "openapi": "3.1.0",
  "info": {"title": "House Price API", "version": "1.4.0"},
  "paths": {
    "/v1/predict": {
      "post": {
        "tags": ["predict"],
        "summary": "Predict a price",
        "operationId": "predict_v1",
        "parameters": [
          {"name": "x-request-id", "in": "header", "required": false, "schema": {"type": "string"}}
        ],
        "requestBody": {"required": true, "content": {"application/json": {
            "schema": {"$ref": "#/components/schemas/PredictRequest"}}}},
        "responses": {
          "200": {"description": "The predicted price in USD", "content": {"application/json": {
              "schema": {"$ref": "#/components/schemas/PredictResponse"}}}},
          "422": {"description": "Validation Error", "content": {"application/json": {
              "schema": {"$ref": "#/components/schemas/HTTPValidationError"}}}}
        },
        "security": [{"OAuth2PasswordBearer": []}]
      }
    }
  },
  "components": {"schemas": {"PredictRequest": {"...": "..."}},
                 "securitySchemes": {"OAuth2PasswordBearer": {"type": "oauth2", "flows": {"...": "..."}}}}
}
```

One notation needs explaining: `"$ref": "#/components/schemas/PredictRequest"` is a *reference*. It
means "the description is not repeated here; look it up under components, schemas, PredictRequest in
this same document". A model used by ten endpoints is therefore described once.

Where each piece came from in your code:

| OpenAPI element | Source in FastAPI |
|---|---|
| `info` | `FastAPI(title=..., version=..., description=...)` |
| path + method | the decorator `@app.post("/v1/predict")` |
| `summary` / `description` | decorator arguments, or the function name and docstring |
| `parameters` (`in: path/query/header/cookie`) | function parameters and those of all dependencies |
| `requestBody` | Pydantic-model, `Body`, `Form` or `File` parameters |
| `responses.200` | return annotation / `response_model` and `status_code` |
| `responses.422` | added automatically whenever the operation has validated inputs |
| `security` | security dependencies such as `OAuth2PasswordBearer` or `APIKeyHeader` |
| `components.schemas` | every Pydantic model reachable from requests and responses |

The following cell builds a miniature version of that assembly, going from a function signature and
Pydantic models to an OpenAPI-like description of the operation.

```python-run
import inspect, json
from typing import Annotated, get_args, get_origin, get_type_hints
from pydantic import BaseModel, Field, TypeAdapter

class Header:           # stand-ins for fastapi.Header / fastapi.Query markers
    where = "header"
class Query:
    where = "query"

class PredictRequest(BaseModel):
    sqft: float = Field(gt=0, description="Living area")
    bedrooms: int = Field(ge=0, le=20)

class PredictResponse(BaseModel):
    price: float
    model_version: str
    model_config = {"protected_namespaces": ()}

def predict(req: PredictRequest,
            dry_run: bool = False,
            x_request_id: Annotated[str | None, Header()] = None) -> PredictResponse:
    """Predict the sale price of a house."""

def describe(func, path_template=""):
    hints = get_type_hints(func, include_extras=True)
    op = {"summary": func.__name__.replace("_", " ").title(), "description": inspect.getdoc(func),
          "parameters": [], "responses": {}}
    schemas = {}
    for name, param in inspect.signature(func).parameters.items():
        ann, where = hints[name], "query"
        if get_origin(ann) is Annotated:
            ann, *meta = get_args(ann)
            where = next((m.where for m in meta if hasattr(m, "where")), "query")
        if isinstance(ann, type) and issubclass(ann, BaseModel):           # model -> request body
            schemas[ann.__name__] = ann.model_json_schema()
            op["requestBody"] = {"$ref": f"#/components/schemas/{ann.__name__}"}
            continue
        if "{" + name + "}" in path_template:
            where = "path"
        op["parameters"].append({
            "name": name.replace("_", "-") if where == "header" else name,
            "in": where,
            "required": param.default is inspect.Parameter.empty,
            "schema": TypeAdapter(ann).json_schema(),
        })
    ret = hints.get("return")
    if ret:
        schemas[ret.__name__] = ret.model_json_schema()
        op["responses"]["200"] = {"$ref": f"#/components/schemas/{ret.__name__}"}
    if op["parameters"] or "requestBody" in op:
        op["responses"]["422"] = {"description": "Validation Error"}
    return op, schemas

op, schemas = describe(predict)
print(json.dumps(op, indent=1))
print("components:", list(schemas), "->", json.dumps(schemas["PredictRequest"]["properties"]))
```

How the miniature generator works:

- `Header` and `Query` are tiny stand-in classes whose only content is a `where` label. They play the
  role of FastAPI's markers.
- `predict` is an ordinary endpoint-style function: a model parameter, a flag with a default, and an
  annotated header.
- `describe` starts an `op` dictionary whose summary is the function name tidied up
  (`predict` becomes `Predict`) and whose description is the docstring.
- It then loops over the parameters. If the hint is `Annotated[...]`, it separates the real type from
  the markers and reads `where` from the marker. If the type is a model, the model's JSON Schema is
  stored under `schemas` and referenced as the request body. Otherwise a parameter entry is added:
  its name (with underscores changed to hyphens for headers), its location, whether it is required
  (no default), and its schema.
- The return hint becomes the `200` response, and a `422` response is added whenever there is any
  input to validate.

In the output, `dry_run` is listed as a query parameter that is not required, `x-request-id` as a
header whose schema allows a string or null, the request body and the 200 response are references,
and the final line shows the two properties of `PredictRequest` with their limits.

Real FastAPI performs the same walk over every route (including the parameters contributed by
dependencies, lesson 10) and then stores the result in `app.openapi_schema`, so the document is
computed once, on the first request for it.

## Input and output schemas can differ

Pydantic generates JSON Schema in two modes, and FastAPI uses both: **validation** mode for what
clients send and **serialization** mode for what they receive. The two can legitimately differ. A
field with a default is *optional when sent* but *always present when returned*; a field marked
`@computed_field` (calculated from the others, lesson 8) exists only in output. For such a model the
docs show two entries, for example `Item-Input` and `Item-Output`. That is correct, and it gives
generated clients accurate types. If you prefer one description per model, create the app with
`FastAPI(separate_input_output_schemas=False)`.

## Documenting errors properly

By default only `200` and `422` are documented for an endpoint. Clients deserve to know about the
other outcomes, each with a description of its body:

```python
class ErrorResponse(BaseModel):
    detail: str

@router.get(
    "/items/{item_id}",
    response_model=ItemPublic,
    responses={
        404: {"model": ErrorResponse, "description": "Item does not exist"},
        401: {"model": ErrorResponse, "description": "Missing or invalid token"},
        429: {"description": "Rate limit exceeded", "headers": {
            "Retry-After": {"schema": {"type": "integer"}, "description": "Seconds to wait"}}},
    },
)
def read_item(item_id: int): ...
```

`ErrorResponse` describes the usual `{"detail": "..."}` body. The `responses` dictionary then states
that `404` and `401` use it, and that `429` comes with a `Retry-After` header holding a number of
seconds. Shared entries can be declared once for a whole group of routes
(`APIRouter(responses={401: ...})`, lesson 14) so that every route in the group inherits them.

## Customising and extending the schema

For changes that FastAPI does not offer as arguments, you can replace the function that produces the
document: build the default with `fastapi.openapi.utils.get_openapi(...)`, modify the resulting
dictionary (add a logo, custom fields such as `x-internal`, server addresses, extra login methods),
store it in `app.openapi_schema`, and assign your function to `app.openapi`.

Three other switches are worth knowing:

- `servers=[{"url": "https://api.example.com"}]` makes "Try it out" and generated clients aim at the
  right host when your app sits behind a proxy.
- `root_path="/api/v1"` is needed when a gateway removes a prefix from the path before forwarding the
  request. Without it, the `/docs` page asks for `/openapi.json` at the wrong address and shows
  "Failed to load API definition".
- `swagger_ui_parameters={"persistAuthorization": True}` keeps you logged in when the docs page is
  reloaded.

## Pitfalls

- Expecting a header named `X_Token`, with an underscore, to arrive. FastAPI looks for `x-token`, and
  proxies such as nginx discard underscore headers by default.
- Reading `request.json()` by hand and so losing both validation and documentation.
- Treating "the docs are switched off" as protection for the endpoints.
- Very large `examples` in schemas, which bloat `/openapi.json`.

## Summary

- `Header()` and `Cookie()` declare those inputs; underscores map to hyphens in header names.
- `Request` gives raw access (body bytes, client address) but skips validation and documentation.
- FastAPI generates an OpenAPI document from routes, types and Pydantic models; Swagger UI (`/docs`)
  and ReDoc (`/redoc`) display it.
- Enrich the docs with app metadata, tags, docstrings, `responses`, examples and `deprecated`.
- The schema also powers client generation, fuzz testing and gateways.

## Glossary

- **Header parameter** — a function parameter marked `Header()`, read from the request headers.
- **Cookie** — a small value a browser stores for a site and sends back with each request.
- **Session** — the server's record of one logged-in visit, usually found through a cookie.
- **XSS (cross-site scripting)** — an attack in which hostile JavaScript runs inside your page.
- **`Request` object** — raw access to everything in the request, without validation.
- **Webhook** — a request another system sends to your API when an event happens.
- **HMAC** — a keyed fingerprint proving that a message is authentic and unaltered.
- **Schema** — a formal description of the shape of data.
- **OpenAPI** — the standard format for describing an HTTP API; served at `/openapi.json`.
- **JSON Schema** — the standard for describing the shape of JSON data; generated by Pydantic.
- **YAML** — a human-friendly text notation for the same kind of data as JSON.
- **Swagger UI / ReDoc** — the interactive page at `/docs` / the reference page at `/redoc`.
- **Docstring** — the triple-quoted description directly under a `def` or `class` line.
- **Tag** — a label that groups endpoints in the docs.
- **`$ref`** — a pointer to a description stored elsewhere in the same document.
- **SDK / generated client** — a library, produced from the schema, for calling the API.
- **Fuzz testing** — testing by sending large numbers of generated inputs.
- **API gateway** — a managed entry point placed in front of one or more APIs.

```quiz
[
  {"q": "What header does 'user_agent: Annotated[str | None, Header()] = None' read?", "options": ["user_agent", "User_Agent", "user-agent (case-insensitive)", "X-User-Agent"], "answer": 2,
   "explain": "FastAPI converts underscores to hyphens and header names are case-insensitive."},
  {"q": "Why read raw bytes via Request.body() when verifying a webhook HMAC signature?", "options": ["It is faster", "The signature covers the exact bytes; re-serialised JSON could differ", "Pydantic cannot parse webhooks", "Headers are unavailable otherwise"], "answer": 1,
   "explain": "Whitespace and key order can change when you parse and re-dump JSON, breaking the signature check."},
  {"q": "Where does FastAPI get the JSON Schema for request and response models?", "options": ["It is hand-written in YAML", "From Pydantic's model_json_schema", "From the database", "From docstrings"], "answer": 1,
   "explain": "Pydantic generates JSON Schema for models; FastAPI embeds it in the OpenAPI components."},
  {"q": "Setting openapi_url=None does what?", "options": ["Hides only ReDoc", "Disables the schema and the docs UIs that depend on it", "Removes all endpoints", "Requires auth for docs"], "answer": 1,
   "explain": "Without the schema, /docs and /redoc have nothing to render, so they are disabled too. The endpoints still work."},
  {"q": "Which is NOT a typical use of the OpenAPI document?", "options": ["Generating typed client SDKs", "Fuzz/contract testing", "Encrypting traffic", "Importing into an API gateway"], "answer": 2,
   "explain": "OpenAPI describes an API; TLS handles encryption."},
  {"q": "What does include_in_schema=False on a route do?", "options": ["Disables the route", "Hides it from OpenAPI and the docs while it still works", "Requires authentication", "Removes validation"], "answer": 1,
   "explain": "The route remains callable; it is only left out of the generated schema."}
]
```

> **Source:** Lubanovic, *FastAPI*, ch. 3 "FastAPI Tour" (HTTP Header, Multiple Request Data, Which Method Is Best?, Automated Documentation); https://fastapi.tiangolo.com/tutorial/header-params/, /tutorial/cookie-params/, /tutorial/metadata/, /tutorial/path-operation-configuration/, /advanced/using-request-directly/
