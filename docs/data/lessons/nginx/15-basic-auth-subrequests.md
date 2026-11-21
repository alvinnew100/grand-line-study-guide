# HTTP basic authentication and auth subrequests

## Before this lesson

You need `location` blocks and inheritance ([How NGINX picks a location block](#/lesson/nginx/location-matching)), `proxy_pass` with `proxy_set_header` ([HTTP load balancing](#/lesson/nginx/lb-http-upstreams)), and internal redirects and `error_page` ([Serving a first static site](#/lesson/nginx/first-static-site)). The 4xx status family from [lesson 1](#/lesson/nginx/what-nginx-is) is used throughout.

## In plain words

**Authentication** is answering "who are you, and can you prove it?". **Authorisation** is the next question: "are you allowed to do this?". People mix the two up constantly; keeping them apart makes every security conversation clearer.

Two ways a building can check visitors:

- **A guard with a printed list.** You say your name and a password, the guard looks at the list, and you are in or out. Quick to set up, and the list lives at the door. This is **HTTP basic authentication**.
- **A guard with a telephone.** The guard knows nothing personally. For each visitor the guard rings the security office, describes the visitor, and does what the office says. The rules can be as elaborate as the office likes and can change without retraining the guard. This is an **authentication subrequest**.

NGINX can be either guard. The first protects an internal dashboard in five minutes. The second is how one login system protects many applications without each of them containing login code, a pattern every platform engineer ends up building or maintaining.

## How basic authentication works on the wire

The whole protocol is two headers.

```mermaid
sequenceDiagram
    participant B as Browser
    participant N as NGINX
    B->>N: GET /admin/
    N-->>B: 401 Unauthorized, WWW-Authenticate Basic realm=Staff
    Note over B: browser shows a login box
    B->>N: GET /admin/ with Authorization Basic cm9zYTp0aWRlcG9vbA==
    N->>N: decode, look up user, compare password hash
    N-->>B: 200 OK
    Note over B: browser resends the header on every later request
```

1. A request arrives without credentials. NGINX answers **401 Unauthorized** with the header `WWW-Authenticate: Basic realm="Staff"`. The **realm** is a label shown in the login box.
2. The browser asks the user for a name and password, joins them as `name:password`, encodes that text in **Base64**, and sends `Authorization: Basic <encoded text>`.
3. NGINX decodes it and checks the password.

Base64 is an encoding, a reversible way to write bytes using 64 safe characters. It is **not encryption**. Anyone who sees the header can decode it:

```bash
$ printf 'rosa:tidepool' | base64
cm9zYTp0aWRlcG9vbA==
$ printf 'cm9zYTp0aWRlcG9vbA==' | base64 -d
rosa:tidepool
```

> [!WARNING]
> Basic authentication sends the password, merely encoded, with **every request**. Over plain HTTP anyone on the network path can read it. Use it only over HTTPS.

## Setting it up

### Step 1: create the password file

The file has one line per user: `name:hashed-password`. A **hash** here is a one-way scrambling of the password: the file lets NGINX check a password without storing it.

```bash
$ sudo apt install -y apache2-utils
$ sudo htpasswd -c /etc/nginx/.htpasswd rosa
New password:
Re-type new password:
Adding password for user rosa
$ sudo htpasswd /etc/nginx/.htpasswd kofi
$ sudo cat /etc/nginx/.htpasswd
rosa:$apr1$Qm0d1x7k$u0y7c2p5nE0y2ev6wU4fT/
kofi:$apr1$9bT4hJ2a$2rZkXQ0eGqfY3o1VnL8gM1
$ sudo chown root:www-data /etc/nginx/.htpasswd && sudo chmod 640 /etc/nginx/.htpasswd
```

- `htpasswd` is a small tool from the Apache utilities package. `-c` creates the file; leave `-c` off when adding further users, or it starts the file again from empty.
- `$apr1$` marks the hashing scheme (an MD5-based scheme with a random **salt**, the text between the next two dollar signs, which makes identical passwords hash differently). NGINX also accepts the system's `crypt()` formats such as `$6$` (SHA-512) and the `{SHA}` and `{SSHA}` forms.
- `chown` and `chmod 640` make the file readable by root and the worker group only.

Without the Apache tool, `openssl passwd -apr1` prints a compatible hash to paste after `name:`.

### Step 2: protect a location

```nginx
server {
    listen 443 ssl;
    server_name shop.test;
    ssl_certificate     /etc/nginx/tls/shop.crt;
    ssl_certificate_key /etc/nginx/tls/shop.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
    }

    location /admin/ {
        auth_basic           "Staff";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header X-Remote-User $remote_user;
    }

    location = /admin/healthz {
        auth_basic off;
        return 200 "ok\n";
    }
}
```

- `listen 443 ssl;` with a certificate and key makes this an HTTPS site; the TLS lesson explains these lines.
- `auth_basic "Staff";` switches basic authentication on for this location, with that realm text.
- `auth_basic_user_file ...;` names the password file.
- `$remote_user` holds the authenticated user name. Forwarding it in a header tells the application who logged in. (The application must only believe that header on requests that come from NGINX.)
- `auth_basic off;` cancels an inherited setting, here so that a monitoring probe can reach the health check without credentials. Both directives inherit like any other, so setting them at `server` level protects a whole site.

### Step 3: test

```bash
$ curl -ik https://shop.test/admin/
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Basic realm="Staff"
Content-Type: text/html

$ curl -ik -u rosa:wrong https://shop.test/admin/
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Basic realm="Staff"

$ curl -ik -u rosa:tidepool https://shop.test/admin/
HTTP/1.1 200 OK
Content-Type: text/html
```

`-u name:password` makes `curl` build the `Authorization` header; `-k` accepts a self-signed test certificate. A missing and a wrong password both give 401: the server never says which part was wrong. The error log records the reason:

```text
2026/11/21 12:41:09 [error] 912#912: *6120 user "rosa": password mismatch, client: 198.51.100.7, server: shop.test, request: "GET /admin/ HTTP/1.1"
```

The check itself in miniature, using the `{SHA}` file format so that it runs with the standard library:

```python-run
import base64, hashlib

def sha_entry(user, password):
    """One htpasswd line in the {SHA} format NGINX accepts (unsalted; fine for a demo only)."""
    digest = base64.b64encode(hashlib.sha1(password.encode()).digest()).decode()
    return f"{user}:{{SHA}}{digest}"

USER_FILE = dict(line.split(":", 1) for line in [sha_entry("rosa", "tidepool"), sha_entry("kofi", "lagoon")])

def check(authorization_header):
    if not authorization_header or not authorization_header.startswith("Basic "):
        return 401, 'WWW-Authenticate: Basic realm="Staff"'
    try:
        user, _, password = base64.b64decode(authorization_header[6:]).decode().partition(":")
    except Exception:
        return 401, "undecodable credentials"
    stored = USER_FILE.get(user)
    offered = sha_entry(user, password).split(":", 1)[1]
    if stored is None or stored != offered:
        return 401, "user unknown or password mismatch"
    return 200, f"$remote_user = {user}"

good = "Basic " + base64.b64encode(b"rosa:tidepool").decode()
print("header sent by the browser:", good)
for h in [None, "Basic " + base64.b64encode(b"rosa:wrong").decode(), good, "Bearer abc"]:
    print(check(h))
```

### Limits of basic authentication

- No logout: the browser resends the header until it is closed.
- No second factor, no password reset, no lockout after failed attempts. Add `limit_req` on protected locations to slow guessing.
- The password file must be copied to every NGINX instance.
- Every request re-checks the hash, which is a little CPU work per request.

It is the right tool for a staging site, a metrics page or an internal tool behind a VPN, and the wrong tool for customer login.

## Authentication subrequests

### The idea

The `auth_request` directive makes NGINX pause each incoming request, send a **subrequest** (an internal request NGINX makes itself) to an address you choose, and decide based on the status that comes back:

| Subrequest answers | NGINX does |
|---|---|
| any 2xx | lets the original request continue |
| 401 or 403 | refuses the original request with that same status |
| anything else, or a failure to connect | answers 500 and logs an error |

The body of the subrequest's response is ignored; only its status and headers are used. The service on the other end can be anything that speaks HTTP: your own login service, or a ready-made one such as oauth2-proxy, Authelia or Vouch.

```mermaid
sequenceDiagram
    participant C as Client
    participant N as NGINX
    participant S as Auth service
    participant A as Application
    C->>N: GET /api/orders with Cookie session=abc
    N->>S: GET /validate, headers only, no body
    alt session is valid
        S-->>N: 204 with X-Auth-User rosa
        N->>A: GET /api/orders with X-User rosa
        A-->>N: 200
        N-->>C: 200
    else session is invalid
        S-->>N: 401
        N-->>C: 401
    end
```

### A complete configuration

```nginx
server {
    listen 443 ssl;
    server_name shop.test;
    ssl_certificate     /etc/nginx/tls/shop.crt;
    ssl_certificate_key /etc/nginx/tls/shop.key;

    location /api/ {
        auth_request      /_auth;
        auth_request_set  $auth_user  $upstream_http_x_auth_user;
        auth_request_set  $auth_roles $upstream_http_x_auth_roles;

        proxy_set_header  X-User  $auth_user;
        proxy_set_header  X-Roles $auth_roles;
        proxy_pass http://127.0.0.1:8000;
    }

    location = /_auth {
        internal;
        proxy_pass http://127.0.0.1:9000/validate;
        proxy_pass_request_body off;
        proxy_set_header Content-Length "";
        proxy_set_header X-Original-URI    $request_uri;
        proxy_set_header X-Original-Method $request_method;
    }
}
```

In `location /api/`:

- `auth_request /_auth;` before doing anything else here, ask the location `/_auth`.
- `auth_request_set $auth_user $upstream_http_x_auth_user;` after the subrequest, copy a value from its response into a variable. `$upstream_http_x_auth_user` is the response header `X-Auth-User` from the auth service (any upstream response header is available as `$upstream_http_` plus its lowercased name with underscores).
- The two `proxy_set_header` lines pass the verified identity to the application, which now needs no login code of its own.

In `location = /_auth`:

- `internal;` nobody outside can call this location directly.
- `proxy_pass http://127.0.0.1:9000/validate;` the auth service's endpoint. The client's request headers, including `Cookie` and `Authorization`, are forwarded automatically, which is how the service sees the credentials.
- `proxy_pass_request_body off;` do not send the original body. The auth service needs headers only, and uploading a 50-megabyte file twice would be wasteful.
- `proxy_set_header Content-Length "";` an empty value removes the header. The original `Content-Length` would otherwise promise a body that is not sent, and the auth service would wait for it.
- `X-Original-URI` and `X-Original-Method` tell the service what the client is trying to do, so it can decide per path and method. That turns the check from authentication only into authorisation as well.

```bash
$ curl -ik https://shop.test/api/orders
HTTP/1.1 401 Unauthorized

$ curl -ik -H 'Cookie: session=abc123' https://shop.test/api/orders
HTTP/1.1 200 OK
Content-Type: application/json

[{"id": 17, "owner": "rosa"}]

$ sudo systemctl stop auth-service
$ curl -ik -H 'Cookie: session=abc123' https://shop.test/api/orders
HTTP/1.1 500 Internal Server Error
$ sudo tail -n 1 /var/log/nginx/error.log
2026/11/21 13:02:44 [error] 912#912: *6388 auth request unexpected status: 502 while sending to client, client: 198.51.100.7, server: shop.test, request: "GET /api/orders HTTP/1.1", host: "shop.test"
```

The last case is the one that surprises people: when the auth service is down, clients get **500**, not 401 or 502, because the subrequest's 502 is "anything else" in the table above. The system **fails closed**: if identity cannot be verified, nobody gets in. That is the safe default.

### Sending browsers to a login page

An API client can handle a bare 401. A person in a browser should be taken to a login form.

```nginx
location / {
    auth_request /_auth;
    error_page 401 = @to_login;
    proxy_pass http://127.0.0.1:8000;
}

location @to_login {
    return 302 https://login.shop.test/?next=$scheme://$host$request_uri;
}
```

`error_page 401 = @to_login;` catches the 401 produced by the failed auth check and jumps to the named location, which redirects to the login site with the original address in a `next` parameter. The `=` lets the named location's own status (302) replace the 401.

### Making it fast

Every request now costs a round trip to the auth service. Three measures keep that cheap:

```nginx
proxy_cache_path /var/cache/nginx/auth keys_zone=auth_cache:5m max_size=50m inactive=5m;

location = /_auth {
    internal;
    proxy_pass http://auth_service/validate;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";

    proxy_cache           auth_cache;
    proxy_cache_key       "$cookie_session|$http_authorization";
    proxy_cache_valid     200 204 30s;
    proxy_cache_valid     401 403 5s;
    proxy_http_version    1.1;
    proxy_set_header      Connection "";
}
```

- **Cache the verdict briefly.** The key is the credential itself, so each session has its own entry. Thirty seconds of caching removes nearly all the load for active users. The cost: a revoked session keeps working for up to 30 seconds. Choose the lifetime with that in mind.
- **Reuse connections** to the auth service with an `upstream` block that has `keepalive`, plus the two `proxy_` lines shown.
- **Keep the service small**: a lookup in an in-memory store, not a slow database query.

`auth_request` is part of open-source NGINX but is an optional build module (`--with-http_auth_request_module`); official and distribution packages include it. Check with `nginx -V 2>&1 | grep -o http_auth_request_module`.

## Combining methods

A location can require several conditions: an address rule, basic authentication, an auth subrequest. By default **all** of them must pass. `satisfy any;` changes that to "any one is enough", for example "office network or a password". The security module's first lesson covers `satisfy` in detail.

> [!INTERVIEW]
> "How would you put single sign-on in front of several internal apps with NGINX?" Use `auth_request` to delegate the decision to one auth service; 2xx allows, 401 or 403 denies, and an `error_page 401` redirect sends browsers to the login page. Pass identity to the applications with headers set by NGINX from `auth_request_set`, strip any such headers the client sent, do not forward the request body to the auth service, and cache verdicts for a short time keyed by the credential. Mention that it fails closed with a 500 if the auth service is unreachable.

## Pitfalls

- **Basic authentication over HTTP.**
- **`htpasswd -c` when adding a second user**, wiping the first.
- **A password file the worker cannot read**, producing 403 or 500 with `open() ... failed (13: Permission denied)` in the error log.
- **Forgetting the body settings on the auth location.** Uploads hang or are sent twice.
- **Trusting identity headers from clients.** If the application reads `X-User`, a client can send `X-User: admin` on any path NGINX does not overwrite it on. Set the header in every proxied location (an empty `proxy_set_header X-User "";` clears it where no auth applies) and make the application reachable only through NGINX.
- **Caching auth verdicts under a key that lacks the credential**, which lets the first user's success apply to everyone.
- **Expecting the auth service's response body** to reach the client. It does not; use `error_page` for custom messages.
- **Protecting `/admin/` but not `/admin`**, or a regex location that takes the request before the protected prefix. Review with the location algorithm.

## Cheat sheet

| Goal | Configuration |
|---|---|
| Create a password file | `htpasswd -c /etc/nginx/.htpasswd user` |
| Add a user | `htpasswd /etc/nginx/.htpasswd other` |
| Require a password | `auth_basic "Realm"; auth_basic_user_file /etc/nginx/.htpasswd;` |
| Exempt a sub-location | `auth_basic off;` |
| Who logged in | `$remote_user` |
| Delegate the decision | `auth_request /_auth;` |
| Read a header from the verdict | `auth_request_set $v $upstream_http_x_name;` |
| Auth location essentials | `internal; proxy_pass_request_body off; proxy_set_header Content-Length "";` |
| Redirect browsers to login | `error_page 401 = @login;` |
| Test | `curl -i -u user:pass URL` |
| Verdict mapping | 2xx allow; 401/403 deny; other gives 500 |

## Summary

- Authentication proves identity; authorisation decides permissions.
- Basic authentication is a 401 challenge plus an `Authorization: Basic` header holding Base64 text; it needs HTTPS and suits internal tools.
- `auth_request` asks another service about every request and maps 2xx to allow, 401/403 to deny and everything else to 500.
- The auth location is `internal`, sends no body, and forwards the original path and method.
- Pass identity onward in headers set by NGINX, cache verdicts briefly per credential, and remember it fails closed.

## Glossary

- **Authentication / authorisation**: proving who you are / deciding what you may do.
- **Base64**: a reversible text encoding of bytes; not encryption.
- **Fail closed**: denying access when the check itself cannot be performed.
- **Hash (password)**: a one-way transformation used to verify a password without storing it.
- **htpasswd**: the tool and file format for basic-auth users.
- **Realm**: the label of a protected area shown in the browser's login box.
- **Salt**: random text mixed into a hash so equal passwords differ.
- **Single sign-on**: one login that grants access to many applications.
- **Subrequest**: an internal request made by NGINX while handling another.
- **401 / 403**: "prove who you are" / "I know who you are and the answer is no".

## Check yourself

```quiz
[
  {"q": "A request without credentials reaches a location with auth_basic. What status code and header are returned?",
   "options": ["403 with no special header", "401 with WWW-Authenticate: Basic realm=...", "302 to a login page", "407 with Proxy-Authenticate"], "answer": 1,
   "explain": "401 plus the WWW-Authenticate challenge is what makes the browser show its login box."},
  {"q": "What does the header `Authorization: Basic cm9zYTp0aWRlcG9vbA==` contain?",
   "options": ["An encrypted password", "A one-way hash of the password", "The user name and password, Base64-encoded and trivially decodable", "A session token"], "answer": 2,
   "explain": "Base64 is an encoding, not encryption, which is why basic auth requires HTTPS."},
  {"q": "auth_request /_auth; and the auth service answers 204. What happens to the original request?",
   "options": ["It is refused with 204", "It continues to the content handler, for example proxy_pass", "It is redirected", "It returns 500"], "answer": 1,
   "explain": "Any 2xx verdict allows the request to proceed."},
  {"q": "Same setup, but the auth service is unreachable so the subrequest ends in 502. What status code does the client receive?",
   "options": ["401", "502", "500", "200"], "answer": 2,
   "explain": "Only 2xx, 401 and 403 are understood. Any other subrequest result is treated as an error and the client gets 500."},
  {"q": "Why set `proxy_pass_request_body off;` and an empty Content-Length in the auth location?",
   "options": ["To hide the cookie", "The auth service needs only headers; sending or promising a body wastes time or makes the service wait", "To enable caching", "Because subrequests cannot use POST"], "answer": 1,
   "explain": "Without the body, a leftover Content-Length would tell the auth service to wait for bytes that never arrive."},
  {"q": "server has auth_basic \"Staff\"; and `location = /healthz { auth_basic off; return 200; }`. What status code does an anonymous GET /healthz receive?",
   "options": ["401", "200", "403", "404"], "answer": 1,
   "explain": "The exact location overrides the inherited setting with off, so no credentials are required."},
  {"q": "An application trusts the X-User header. Which practice keeps that safe?",
   "options": ["Let clients send it", "Have NGINX set or clear it on every proxied request and expose the application only through NGINX", "Base64-encode it", "Put it in the query string"], "answer": 1,
   "explain": "proxy_set_header overwrites any client-supplied value, and the application must not be reachable by another route."}
]
```

> **Source:** DeJonghe, NGINX Cookbook, ch. 6 (HTTP basic authentication, authentication subrequests). Docs: https://nginx.org/en/docs/http/ngx_http_auth_basic_module.html, https://nginx.org/en/docs/http/ngx_http_auth_request_module.html
