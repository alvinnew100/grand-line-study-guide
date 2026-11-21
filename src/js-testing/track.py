TRACK = dict(
    id="js-testing",
    title="JavaScript Testing and TDD",
    icon="🧪",
    color="#2f9e6e",
    group="Web",
    blurb="Automated testing and test-driven development in JavaScript, from a twenty-line test runner to fake "
          "timers, test doubles, Vitest and Jest, Testing Library, Playwright, coverage and CI, with runnable "
          "examples and judged problems.",
    sources=[
        "Johansen, Test-Driven JavaScript Development (Addison-Wesley, 2010), ch. 1-17",
        "Meszaros, xUnit Test Patterns (terminology for test doubles and test smells)",
        "Vitest, Jest, node:test, Testing Library and Playwright documentation",
        "MDN Web Docs (developer.mozilla.org)",
    ],
    modules=[
        dict(
            id="automated-testing",
            title="Automated Testing",
            summary="Why tests check themselves, assertions, a tiny runner, setup and teardown, unit and integration tests.",
            lessons=[
                dict(id="first-unit-test", title="Why automate tests: your first unit test", file="01-first-unit-test.md"),
                dict(id="setup-suites-integration", title="Setup, teardown, suites and integration tests", file="02-setup-suites-integration.md"),
            ],
            problems=["jstest-assert-equals", "jstest-first-difference", "jstest-tiny-runner", "jstest-runner-hooks"],
        ),
        dict(
            id="tdd",
            title="Test-Driven Development",
            summary="The red, green, refactor loop, why each step exists, and a full session worked test by test.",
            lessons=[
                dict(id="red-green-refactor", title="Test-driven development: red, green, refactor", file="03-red-green-refactor.md"),
                dict(id="tdd-worked-session", title="A complete TDD session, test by test", file="04-tdd-worked-session.md"),
            ],
            problems=["jstest-string-calculator"],
        ),
        dict(
            id="tools-learning",
            title="Tools and Learning Tests",
            summary="xUnit and BDD styles, runners then and now, where tests run, and tests written to learn or to measure.",
            lessons=[
                dict(id="test-runners-tools", title="Tools of the trade: runners, styles, coverage and CI", file="05-test-runners-tools.md"),
                dict(id="learning-tests-benchmarks", title="Test to learn: learning tests and honest benchmarks", file="06-learning-tests-benchmarks.md"),
            ],
            problems=["jstest-suite-names"],
        ),
        dict(
            id="functions",
            title="Functions and Closures Under Test",
            summary="Declarations, arguments, scope and this, then binding, closures, private state and memoisation, all pinned by tests.",
            lessons=[
                dict(id="functions-scope-this", title="Functions under test: declarations, arguments, scope and `this`", file="07-functions-scope-this.md"),
                dict(id="closures-binding-memoize", title="Applied functions: binding, closures, state and memoisation", file="08-closures-binding-memoize.md"),
            ],
            problems=["jstest-bind", "jstest-once", "jstest-memoize"],
        ),
        dict(
            id="objects-modern",
            title="Objects, Prototypes and Modern JavaScript",
            summary="Own and inherited properties, prototype chains, encapsulation, mixins, classes, strict mode and newer syntax.",
            lessons=[
                dict(id="objects-prototype-chains", title="Objects and prototype chains, explored with tests", file="09-objects-prototype-chains.md"),
                dict(id="encapsulation-mixins-classes", title="Private state, composition, mixins and how classes map to prototypes", file="10-encapsulation-mixins-classes.md"),
                dict(id="strict-mode-modern-features", title="Strict mode and modern language features, verified by tests", file="11-strict-mode-modern-features.md"),
            ],
            problems=["jstest-prototype-lookup"],
        ),
        dict(
            id="unobtrusive-observer",
            title="Unobtrusive JavaScript and the Observer Pattern",
            summary="Behaviour kept apart from markup, feature detection, and an observable built one failing test at a time.",
            lessons=[
                dict(id="unobtrusive-feature-detection", title="Unobtrusive JavaScript, progressive enhancement and feature detection", file="12-unobtrusive-feature-detection.md"),
                dict(id="observer-pattern-tdd", title="The observer pattern, built test-first", file="13-observer-pattern-tdd.md"),
            ],
            problems=["jstest-observable"],
        ),
        dict(
            id="async-http",
            title="Asynchronous Code and HTTP",
            summary="Making the runner wait, testing rejections, and replacing the network with stubs that answer, record and fail on demand.",
            lessons=[
                dict(id="testing-async-code", title="Testing asynchronous code: callbacks, promises and async/await", file="14-testing-async-code.md"),
                dict(id="stubbing-http", title="Stubbing HTTP requests", file="15-stubbing-http.md"),
            ],
            problems=["jstest-spy", "jstest-stub", "jstest-mock-http"],
        ),
        dict(
            id="streaming",
            title="Polling, Long Polling and Streaming",
            summary="Timers under a fake clock, a poller built test-first, backoff, server push and one connection for many topics.",
            lessons=[
                dict(id="polling-fake-timers", title="Polling a server and testing time with a fake clock", file="16-polling-fake-timers.md"),
                dict(id="long-polling-streaming", title="Long polling, streaming and one connection for many topics", file="17-long-polling-streaming.md"),
            ],
            problems=["jstest-fake-clock", "jstest-debounce-clock", "jstest-poller", "jstest-topic-dispatcher"],
        ),
        dict(
            id="server-client",
            title="Server and Client, Test-First",
            summary="A small Node HTTP service split into model and controller, then a DOM app tested in layers down to the real page.",
            lessons=[
                dict(id="node-http-service-tdd", title="Test-driving a small Node HTTP service", file="18-node-http-service-tdd.md"),
                dict(id="dom-client-tdd", title="Test-driving a DOM client: a packing list app", file="19-dom-client-tdd.md"),
            ],
            problems=["jstest-request-handler"],
        ),
        dict(
            id="doubles-quality",
            title="Test Doubles and Good Tests",
            summary="Dummies, stubs, spies, mocks and fakes and when each fits; names, focus, isolation and the common test smells.",
            lessons=[
                dict(id="test-doubles", title="Test doubles in depth: dummies, stubs, spies, mocks and fakes", file="20-test-doubles.md"),
                dict(id="good-unit-tests", title="Writing good unit tests: names, focus and test smells", file="21-good-unit-tests.md"),
            ],
            problems=["jstest-spy-on", "jstest-mock-expectations"],
        ),
        dict(
            id="modern-tooling",
            title="Modern Tooling",
            summary="Vitest, Jest and node:test in practice, async and timer control, module and fetch mocking, Testing Library, Playwright, coverage, mutation testing and CI.",
            lessons=[
                dict(id="modern-runners", title="Vitest, Jest and node:test in daily use", file="22-modern-runners.md"),
                dict(id="async-timers-promises", title="Promises, timers and async code under test", file="23-async-timers-promises.md"),
                dict(id="mocking-modules-fetch", title="Mocking modules, globals and fetch", file="24-mocking-modules-fetch.md"),
                dict(id="testing-library-playwright", title="Component and end-to-end tests: Testing Library and Playwright", file="25-testing-library-playwright.md"),
                dict(id="coverage-mutation-ci", title="Coverage, mutation testing and tests in CI", file="26-coverage-mutation-ci.md"),
            ],
            problems=["jstest-matchers", "jstest-retry", "jstest-latest-wins", "jstest-module-registry", "jstest-get-by-role"],
        ),
        dict(
            id="interview",
            title="Interview Preparation",
            summary="The testing questions interviewers ask, with model answers, a debounce exercise and tests that cannot fail.",
            lessons=[
                dict(id="interview-questions", title="Interview: common testing questions and model answers", file="27-interview-questions.md"),
            ],
            problems=["jstest-boundary-values"],
        ),
    ],
)
