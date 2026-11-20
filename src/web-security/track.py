TRACK = dict(
    id="web-security",
    title="Web Application Security",
    icon="🛡️",
    color="#b91c1c",
    group="Engineering Practice",
    blurb="Defensive security for developers, from zero: how the web works, how each class of vulnerability arises, "
          "vulnerable-versus-fixed code, layered defences, testing, threat modelling, the secure development "
          "lifecycle, LLM application security and interview-ready answers.",
    sources=[
        "Andrew Hoffman, Web Application Security (O'Reilly, 2020)",
        "OWASP Top 10 — https://owasp.org/www-project-top-ten/",
        "OWASP Cheat Sheet Series — https://cheatsheetseries.owasp.org/",
        "MDN Web Docs, Security on the web — https://developer.mozilla.org/en-US/docs/Web/Security",
    ],
    modules=[
        dict(
            id="foundations",
            title="Security Foundations",
            summary="The security mindset, a short history of attacks, and the two rules the whole web stands on: HTTP and the same-origin policy.",
            lessons=[
                dict(id="security-mindset", title="The security mindset and a short history", file="01-security-mindset.md"),
                dict(id="http-same-origin", title="HTTP, origins and the same-origin policy", file="02-http-same-origin.md"),
            ],
            problems=[],
        ),
        dict(
            id="web-structure",
            title="How Web Applications Are Built",
            summary="Cookies and sessions, authentication versus authorisation, REST and GraphQL APIs, and how an application looks from the outside.",
            lessons=[
                dict(id="cookies-sessions", title="Cookies and sessions", file="03-cookies-sessions.md"),
                dict(id="authn-authz", title="Authentication and authorisation models", file="04-authn-authz.md"),
                dict(id="apis-architecture", title="APIs, dependencies and architecture review", file="05-apis-architecture.md"),
                dict(id="attack-surface", title="The attacker's view: leaks and attack surface", file="06-attack-surface.md"),
            ],
            problems=["sec-cookie-audit"],
        ),
        dict(
            id="browser-attacks",
            title="Attacks Through the Browser",
            summary="Cross-site scripting, cross-site request forgery, clickjacking and open redirects, with the encoding, token and header defences.",
            lessons=[
                dict(id="xss", title="Cross-site scripting (XSS) and output encoding", file="07-xss.md"),
                dict(id="csrf", title="Cross-site request forgery (CSRF)", file="08-csrf.md"),
                dict(id="clickjacking-redirects", title="Clickjacking and open redirects", file="09-clickjacking-redirects.md"),
            ],
            problems=["sec-html-escape", "sec-samesite-decision", "sec-csrf-token", "sec-safe-redirect"],
        ),
        dict(
            id="injection",
            title="Injection and Unsafe Parsing",
            summary="SQL, command and template injection, XML external entities and insecure deserialisation: one root cause, several disguises.",
            lessons=[
                dict(id="sql-injection", title="SQL injection and parameterised queries", file="10-sql-injection.md"),
                dict(id="command-template-injection", title="Command and template injection", file="11-command-template-injection.md"),
                dict(id="xxe-deserialisation", title="XML external entities and insecure deserialisation", file="12-xxe-deserialisation.md"),
            ],
            problems=["sec-parameterised-query"],
        ),
        dict(
            id="access-identity",
            title="Access Control, Authentication and Sessions",
            summary="Broken access control and IDOR, password storage and multi-factor authentication, and session management done properly.",
            lessons=[
                dict(id="broken-access-control", title="Broken access control and IDOR", file="13-broken-access-control.md"),
                dict(id="authentication-passwords", title="Authentication failures, password storage and MFA", file="14-authentication-passwords.md"),
                dict(id="session-management", title="Session management flaws and cookie attributes", file="15-session-management.md"),
            ],
            problems=["sec-rbac-check", "sec-object-authz", "sec-constant-time-compare", "sec-password-policy",
                      "sec-password-hash", "sec-session-check"],
        ),
        dict(
            id="server-side",
            title="Server-Side Weaknesses",
            summary="Server-side request forgery, path traversal and file uploads, denial of service and rate limiting, and business-logic flaws.",
            lessons=[
                dict(id="ssrf", title="Server-side request forgery (SSRF)", file="16-ssrf.md"),
                dict(id="path-traversal-uploads", title="Path traversal and file upload risks", file="17-path-traversal-uploads.md"),
                dict(id="dos-rate-limiting", title="Denial of service and rate limiting", file="18-dos-rate-limiting.md"),
                dict(id="business-logic", title="Business-logic flaws", file="19-business-logic.md"),
            ],
            problems=["sec-ssrf-guard", "sec-safe-join", "sec-upload-validate", "sec-login-limiter"],
        ),
        dict(
            id="config-supply-chain",
            title="Configuration, Headers and Supply Chain",
            summary="Security headers, Content Security Policy and CORS, misconfiguration and secrets management, and vulnerable dependencies.",
            lessons=[
                dict(id="headers-csp-cors", title="Security headers, CSP and CORS", file="20-headers-csp-cors.md"),
                dict(id="misconfiguration-secrets", title="Security misconfiguration and secrets management", file="21-misconfiguration-secrets.md"),
                dict(id="dependencies-supply-chain", title="Vulnerable dependencies and the supply chain", file="22-dependencies-supply-chain.md"),
            ],
            problems=["sec-header-audit", "sec-csp-audit", "sec-cors-decision", "sec-secrets-scan", "sec-dependency-check"],
        ),
        dict(
            id="identity-protocols",
            title="Identity Protocols and Tokens",
            summary="OAuth 2.0 and OpenID Connect flows and their pitfalls, and how to handle JSON Web Tokens without hurting yourself.",
            lessons=[
                dict(id="oauth-oidc", title="OAuth 2.0 and OpenID Connect", file="23-oauth-oidc.md"),
                dict(id="jwt", title="JWT handling pitfalls", file="24-jwt.md"),
            ],
            problems=["sec-jwt-validate"],
        ),
        dict(
            id="secure-engineering",
            title="Secure Engineering Practice",
            summary="Threat modelling with STRIDE, secure code review and input validation, security in the development lifecycle, logging and vulnerability management.",
            lessons=[
                dict(id="threat-modelling", title="Secure architecture and threat modelling (STRIDE)", file="25-threat-modelling.md"),
                dict(id="code-review-validation", title="Secure code review and input validation", file="26-code-review-validation.md"),
                dict(id="sdlc-automation", title="Security in the SDLC: SAST, DAST and CI gates", file="27-sdlc-automation.md"),
                dict(id="logging-vuln-management", title="Logging, monitoring and vulnerability management", file="28-logging-vuln-management.md"),
            ],
            problems=["sec-stride-gaps", "sec-risk-prioritise", "sec-schema-validate", "sec-log-redact"],
        ),
        dict(
            id="ai-interviews",
            title="AI Applications and Interview Essentials",
            summary="Defending applications built on machine-learning and large language models, then worked answers to the classic security interview questions.",
            lessons=[
                dict(id="llm-security", title="Security for ML and LLM applications", file="29-llm-security.md"),
                dict(id="interview-essentials", title="Security interview essentials", file="30-interview-essentials.md"),
            ],
            problems=[],
        ),
    ],
)
