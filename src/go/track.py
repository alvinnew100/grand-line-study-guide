TRACK = dict(
    id="go",
    title="Go (Learning Go)",
    icon="🐹",
    color="#00add8",
    group="Languages",
    blurb="Go from the first `go run` to production services: types, slices and maps, interfaces, generics, "
          "errors, modules, goroutines and channels, context, testing, the standard library and the runtime "
          "questions interviewers love. Written for complete beginners, with runnable simulations and practice problems.",
    sources=[
        "Jon Bodner, Learning Go: An Idiomatic Approach to Real-World Go Programming, 2nd ed. (O'Reilly), ch. 1-16 "
        "(topic coverage and fact-checking only; all wording and examples are original)",
        "The Go Programming Language Specification, go.dev/ref/spec",
        "Go documentation: Effective Go, the Go Memory Model, the Go blog and package docs, go.dev/doc and pkg.go.dev",
    ],
    modules=[
        dict(
            id="go-setup",
            title="1. Setting up and the go command",
            summary="Install the toolchain, write a first program, and learn the build-format-vet loop.",
            lessons=[
                dict(id="go-toolchain", title="The toolchain and your first program", file="01-toolchain-first-program.md"),
                dict(id="go-fmt-vet", title="go fmt, go vet and the daily workflow", file="02-fmt-vet-workflow.md"),
            ],
            problems=[],
        ),
        dict(
            id="go-types",
            title="2. Predeclared types and declarations",
            summary="Zero values, numeric types and overflow, strings and runes, var versus :=, and constants.",
            lessons=[
                dict(id="go-predeclared-types", title="Predeclared types, zero values and conversions", file="03-predeclared-types.md"),
                dict(id="go-declarations-const", title="Declarations, constants and typed versus untyped", file="04-declarations-const.md"),
            ],
            problems=["go-real-c-to-f", "go-int-overflow"],
        ),
        dict(
            id="go-composite",
            title="3. Composite types",
            summary="Arrays, slices and their backing arrays, strings as bytes and runes, maps and structs.",
            lessons=[
                dict(id="go-arrays-slices", title="Arrays and slices: length, capacity and append", file="05-arrays-slices.md"),
                dict(id="go-slicing-aliasing", title="Slicing, aliasing and copy", file="06-slicing-aliasing-copy.md"),
                dict(id="go-strings-runes", title="Strings, runes and bytes", file="07-strings-runes-bytes.md"),
                dict(id="go-maps-structs", title="Maps and structs", file="08-maps-structs.md"),
            ],
            problems=["go-real-reverse-runes", "go-real-word-freq", "go-real-dedupe", "go-real-rotate-left",
                      "go-slice-append-sim", "go-slice-expr", "go-rune-byte-iter", "go-map-comma-ok"],
        ),
        dict(
            id="go-control",
            title="4. Blocks, shadows and control structures",
            summary="Scope and shadowing, if with init statements, the four shapes of for, switch and goto.",
            lessons=[
                dict(id="go-blocks-shadowing", title="Blocks, shadowing and if", file="09-blocks-shadowing-if.md"),
                dict(id="go-for-switch", title="for, switch and goto", file="10-for-switch-goto.md"),
            ],
            problems=["go-real-fizzbuzz", "go-real-is-prime", "go-real-grade", "go-shadowing-scopes", "go-switch-fallthrough"],
        ),
        dict(
            id="go-functions",
            title="5. Functions",
            summary="Multiple returns, variadics, function values, closures, defer and call by value.",
            lessons=[
                dict(id="go-functions-basics", title="Declaring and calling functions", file="11-functions-basics.md"),
                dict(id="go-closures-defer", title="Closures, defer and call by value", file="12-closures-defer.md"),
            ],
            problems=["go-real-split-seconds", "go-real-safe-div", "go-real-closure-counter", "go-defer-order"],
        ),
        dict(
            id="go-pointers",
            title="6. Pointers",
            summary="What a pointer is in Go, when to use one, nil, mutability and the garbage collector's view.",
            lessons=[
                dict(id="go-pointers-basics", title="Pointers, nil and mutability", file="13-pointers-basics.md"),
                dict(id="go-pointers-gc", title="Pointers, performance and the garbage collector", file="14-pointers-performance-gc.md"),
            ],
            problems=["go-real-reverse-list", "go-escape-analysis"],
        ),
        dict(
            id="go-types-interfaces",
            title="7. Types, methods and interfaces",
            summary="Defined types, receivers and method sets, embedding, implicit interfaces and dependency injection.",
            lessons=[
                dict(id="go-types-methods", title="Defined types, methods and embedding", file="15-types-methods-embedding.md"),
                dict(id="go-interfaces", title="Interfaces, any, assertions and the nil trap", file="16-interfaces.md"),
                dict(id="go-interface-design", title="Interface design and dependency injection", file="17-interface-design-di.md"),
            ],
            problems=["go-real-rect-methods", "go-real-stack", "go-real-shapes", "go-real-stringer",
                      "go-embed-promotion", "go-method-sets", "go-nil-interface"],
        ),
        dict(
            id="go-generics",
            title="8. Generics",
            summary="Type parameters, constraints and type sets, inference, and where generics do not belong.",
            lessons=[
                dict(id="go-generics-basics", title="Type parameters and generic functions", file="18-generics-basics.md"),
                dict(id="go-generics-constraints", title="Constraints, type sets and idiomatic generics", file="19-generics-constraints.md"),
            ],
            problems=["go-real-generic-map-filter", "go-real-generic-max", "go-constraint-check"],
        ),
        dict(
            id="go-errors",
            title="9. Errors",
            summary="Errors as values, sentinels, custom types, wrapping, errors.Is and errors.As, panic and recover.",
            lessons=[
                dict(id="go-errors-values", title="Errors are values: creating, returning and wrapping", file="20-errors-values-wrapping.md"),
                dict(id="go-errors-is-as-panic", title="errors.Is, errors.As, panic and recover", file="21-is-as-panic-recover.md"),
            ],
            problems=["go-real-error-wrap", "go-real-error-as", "go-real-safe-call", "go-error-chain"],
        ),
        dict(
            id="go-modules",
            title="10. Modules, packages and imports",
            summary="Package layout and visibility, internal, go.mod, semantic import versioning, MVS and workspaces.",
            lessons=[
                dict(id="go-packages-imports", title="Packages, visibility and imports", file="22-packages-imports.md"),
                dict(id="go-modules-versioning", title="Modules, versions and minimal version selection", file="23-modules-versioning.md"),
            ],
            problems=["go-import-path-version", "go-mvs"],
        ),
        dict(
            id="go-tooling",
            title="11. Go tooling",
            summary="Linters and scanners, embed, go generate, build constraints and cross-compilation.",
            lessons=[
                dict(id="go-quality-tools", title="vet, staticcheck, golangci-lint and govulncheck", file="24-quality-tools.md"),
                dict(id="go-embed-generate-cross", title="embed, go generate and cross-compilation", file="25-embed-generate-crosscompile.md"),
            ],
            problems=["go-build-constraint"],
        ),
        dict(
            id="go-concurrency",
            title="12. Concurrency",
            summary="Goroutines, channels, select, pipelines and worker pools, sync primitives, deadlocks and leaks.",
            lessons=[
                dict(id="go-goroutines-channels", title="Goroutines and channels", file="26-goroutines-channels.md"),
                dict(id="go-select-patterns", title="select and concurrency patterns", file="27-select-patterns.md"),
                dict(id="go-sync-primitives", title="WaitGroup, Mutex, Once, atomics and errgroup", file="28-sync-primitives.md"),
                dict(id="go-deadlocks-leaks", title="Deadlocks, leaks and the race detector", file="29-deadlocks-leaks-races.md"),
            ],
            problems=["go-real-parallel-map", "go-real-safe-counter", "go-real-pipeline", "go-real-merge",
                      "go-real-worker-pool", "go-channel-sim", "go-select-sim", "go-worker-pool",
                      "go-pipeline-backpressure", "go-waitgroup-validate", "go-mutex-timeline"],
        ),
        dict(
            id="go-stdlib",
            title="13. The standard library",
            summary="io and its small interfaces, time, encoding/json, net/http and structured logging with slog.",
            lessons=[
                dict(id="go-io-time", title="io, bufio and time", file="30-io-and-time.md"),
                dict(id="go-json", title="encoding/json", file="31-encoding-json.md"),
                dict(id="go-http-slog", title="net/http and log/slog", file="32-net-http-slog.md"),
            ],
            problems=["go-ticker-rate-limiter", "go-json-tags"],
        ),
        dict(
            id="go-context",
            title="14. The context package",
            summary="Cancellation, deadlines and request-scoped values, and how they flow through a call tree.",
            lessons=[
                dict(id="go-context-cancel", title="Context: cancellation and its tree", file="33-context-cancellation.md"),
                dict(id="go-context-deadlines-values", title="Deadlines, timeouts and context values", file="34-context-deadlines-values.md"),
            ],
            problems=["go-real-context-wait", "go-context-tree"],
        ),
        dict(
            id="go-testing",
            title="15. Writing tests",
            summary="The testing package: table tests, subtests, coverage, fuzzing, benchmarks, httptest and stubs.",
            lessons=[
                dict(id="go-testing-basics", title="Tests, tables, subtests and coverage", file="35-testing-basics.md"),
                dict(id="go-fuzz-bench-httptest", title="Fuzzing, benchmarks, stubs and httptest", file="36-fuzz-bench-httptest.md"),
            ],
            problems=["go-table-test-summary"],
        ),
        dict(
            id="go-dragons",
            title="16. Here be dragons: reflect, unsafe and cgo",
            summary="Runtime type inspection, breaking the type system on purpose, and calling C.",
            lessons=[
                dict(id="go-reflection", title="Reflection", file="37-reflection.md"),
                dict(id="go-unsafe-cgo", title="unsafe and cgo", file="38-unsafe-cgo.md"),
            ],
            problems=["go-struct-tag-parse"],
        ),
        dict(
            id="go-backend",
            title="17. Go for backend services",
            summary="A complete REST service: routing, middleware, Postgres, configuration, shutdown and a Docker image.",
            lessons=[
                dict(id="go-rest-service", title="A REST service: routing, handlers and middleware", file="39-rest-service.md"),
                dict(id="go-db-shutdown-docker", title="Postgres, configuration, graceful shutdown and Docker", file="40-database-shutdown-docker.md"),
            ],
            problems=["go-middleware-chain"],
        ),
        dict(
            id="go-interview",
            title="18. Go interview essentials",
            summary="The questions that come up again and again, with worked answers and predicted output.",
            lessons=[
                dict(id="go-interview-language", title="Language puzzles: slices, maps, nil and channels", file="41-interview-language.md"),
                dict(id="go-interview-runtime", title="Runtime questions: scheduler, escape analysis and GC", file="42-interview-runtime.md"),
            ],
            problems=["go-real-valid-parens", "go-real-binary-search", "go-real-two-sum", "go-real-group-anagrams",
                      "go-gmp-scheduler"],
        ),
    ],
)
