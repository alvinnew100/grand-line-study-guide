TRACK = dict(
    id="javascript",
    title="JavaScript (Eloquent JavaScript)",
    icon="✨",
    color="#c99a06",
    group="Web",
    blurb="The JavaScript language from values and closures to promises and the event loop, then the browser "
          "(DOM, events, canvas, fetch) and Node.js, with runnable examples, live pages and judged problems.",
    sources=[
        "Haverbeke, Eloquent JavaScript (4th ed.), ch. 1-21",
        "MDN Web Docs (developer.mozilla.org)",
    ],
    modules=[
        dict(
            id="values-structure",
            title="Values, Types and Program Structure",
            summary="Numbers, strings, booleans, the empty values, conversion rules, bindings and control flow.",
            lessons=[
                dict(id="values-types-operators", title="Values, types and operators", file="01-values-types-operators.md"),
                dict(id="coercion-equality", title="Type coercion and equality", file="02-coercion-equality.md"),
                dict(id="program-structure", title="Program structure: bindings and control flow", file="03-program-structure.md"),
            ],
            problems=["js-loose-equals", "js-collatz-steps"],
        ),
        dict(
            id="functions",
            title="Functions, Closures and Recursion",
            summary="Defining functions, scope, the call stack, closures that remember, and recursive thinking.",
            lessons=[
                dict(id="functions-scope", title="Functions and scope", file="04-functions-scope.md"),
                dict(id="closures-recursion", title="Closures and recursion", file="05-closures-recursion.md"),
            ],
            problems=["js-counter-factory", "js-memoize", "js-permutations"],
        ),
        dict(
            id="data-structures",
            title="Data Structures: Objects and Arrays",
            summary="Properties, methods, mutability, array and string toolkits, destructuring, spread and JSON.",
            lessons=[
                dict(id="objects-arrays", title="Objects, arrays and mutability", file="06-objects-arrays.md"),
                dict(id="destructuring-json", title="Destructuring, spread, rest and JSON", file="07-destructuring-json.md"),
            ],
            problems=["js-deep-equal", "js-deep-clone", "js-pick-omit", "js-deep-merge", "js-get-path"],
        ),
        dict(
            id="higher-order",
            title="Higher-Order Functions",
            summary="Functions that take and return functions: map, filter, reduce, composition and text processing.",
            lessons=[
                dict(id="higher-order-functions", title="Higher-order functions: map, filter, reduce", file="08-higher-order-functions.md"),
                dict(id="composition-strings", title="Composition, pipelines and Unicode strings", file="09-composition-strings.md"),
            ],
            problems=["js-array-methods", "js-group-by", "js-flat", "js-compose-pipe"],
        ),
        dict(
            id="objects",
            title="The Secret Life of Objects",
            summary="Prototypes, classes, private fields, symbols, iterators, accessors, inheritance, and a simulation project.",
            lessons=[
                dict(id="prototypes-classes", title="Prototypes, classes and encapsulation", file="10-prototypes-classes.md"),
                dict(id="symbols-iterators-inheritance", title="Symbols, iterators, accessors and inheritance", file="11-symbols-iterators-inheritance.md"),
                dict(id="project-elevator", title="Project: an elevator simulator", file="12-project-elevator.md"),
            ],
            problems=["js-bank-account", "js-iter-tools", "js-lru-cache", "js-event-emitter"],
        ),
        dict(
            id="errors",
            title="Bugs and Errors",
            summary="Strict mode, types, tests, debugging method, exceptions, cleanup and assertions.",
            lessons=[
                dict(id="bugs-strict-testing", title="Bugs, strict mode, testing and debugging", file="13-bugs-strict-testing.md"),
                dict(id="exceptions", title="Exceptions and error handling", file="14-exceptions.md"),
            ],
            problems=["js-parse-records"],
        ),
        dict(
            id="regex",
            title="Regular Expressions",
            summary="Pattern syntax, groups, flags, backtracking, replace, sticky and global matching, Unicode.",
            lessons=[
                dict(id="regex-basics", title="Regular expressions: patterns, sets, groups", file="15-regex-basics.md"),
                dict(id="regex-advanced", title="Regular expressions: backtracking, replace, lastIndex, parsing", file="16-regex-advanced.md"),
            ],
            problems=["js-hex-color", "js-extract-dates", "js-camel-snake"],
        ),
        dict(
            id="modules",
            title="Modules",
            summary="Why programs are split up, ES modules, CommonJS, packages, bundlers and interface design.",
            lessons=[
                dict(id="es-modules-commonjs", title="ES modules and CommonJS", file="17-es-modules-commonjs.md"),
                dict(id="bundlers-module-design", title="Packages, bundlers and module design", file="18-bundlers-module-design.md"),
            ],
            problems=["js-load-order"],
        ),
        dict(
            id="async",
            title="Asynchronous Programming",
            summary="Callbacks, promises, async functions, generators, the event loop and its two queues.",
            lessons=[
                dict(id="callbacks-promises", title="Callbacks and promises", file="19-callbacks-promises.md"),
                dict(id="async-await-generators", title="Async functions and generators", file="20-async-await-generators.md"),
                dict(id="event-loop-microtasks", title="The event loop, tasks and microtasks", file="21-event-loop-microtasks.md"),
            ],
            problems=["js-event-loop-order"],
        ),
        dict(
            id="language-project",
            title="Project: A Small Programming Language",
            summary="Build Pebble, a tiny expression language: tokenizer, precedence parser, evaluator, closures.",
            lessons=[
                dict(id="language-parsing", title="Pebble part 1: tokens and parsing", file="22-language-parsing.md"),
                dict(id="language-evaluating", title="Pebble part 2: evaluation, scope and functions", file="23-language-evaluating.md"),
            ],
            problems=["js-eval-expression"],
        ),
        dict(
            id="browser-dom",
            title="The Browser and the DOM",
            summary="How pages reach the browser, how scripts load, the document tree, querying and changing it.",
            lessons=[
                dict(id="browser-dom-tree", title="JavaScript in the browser and the DOM tree", file="24-browser-dom-tree.md"),
                dict(id="changing-document", title="Changing the document: nodes, attributes, layout, style", file="25-changing-document.md"),
            ],
            problems=["js-vdom-diff"],
        ),
        dict(
            id="events",
            title="Handling Events",
            summary="Listeners, event objects, propagation, default actions, keyboard, pointer, scroll, focus, timers.",
            lessons=[
                dict(id="event-handling", title="Event handlers, propagation and delegation", file="26-event-handling.md"),
                dict(id="keys-pointers-timers", title="Keys, pointers, scrolling, timers and debouncing", file="27-keys-pointers-timers.md"),
            ],
            problems=["js-debounce-sim"],
        ),
        dict(
            id="canvas-game",
            title="Canvas and a Platform Game",
            summary="SVG versus canvas, paths, text, images, transforms, animation, and a complete small game.",
            lessons=[
                dict(id="canvas-drawing", title="Drawing on canvas", file="28-canvas-drawing.md"),
                dict(id="project-platform-game", title="Project: a platform game explained", file="29-project-platform-game.md"),
            ],
            problems=["js-spiral-matrix"],
        ),
        dict(
            id="http-forms",
            title="HTTP, Forms and a Pixel Editor",
            summary="Requests and responses, fetch, security, form fields, client-side storage and an editor project.",
            lessons=[
                dict(id="http-fetch-forms", title="HTTP, fetch, forms and client-side storage", file="30-http-fetch-forms.md"),
                dict(id="project-pixel-editor", title="Project: a pixel art editor explained", file="31-project-pixel-editor.md"),
            ],
            problems=["js-query-string", "js-flood-fill"],
        ),
        dict(
            id="node",
            title="Node.js",
            summary="JavaScript outside the browser: modules, files, streams, npm, HTTP servers and a small project.",
            lessons=[
                dict(id="node-core", title="Node.js: modules, files, streams and npm", file="32-node-core.md"),
                dict(id="node-http-project", title="Node HTTP servers and a tip-sharing project", file="33-node-http-project.md"),
            ],
            problems=["js-parse-csv"],
        ),
        dict(
            id="modern-typescript",
            title="Modern JavaScript and TypeScript Basics",
            summary="The ES2015+ feature set worth knowing cold, then static types with TypeScript.",
            lessons=[
                dict(id="modern-javascript", title="Modern JavaScript: ES2015 and beyond", file="34-modern-javascript.md"),
                dict(id="typescript-basics", title="TypeScript basics: types, interfaces, generics, narrowing", file="35-typescript-basics.md"),
            ],
            problems=["js-template-engine", "js-json-stringify"],
        ),
        dict(
            id="interview",
            title="JavaScript Interview Essentials",
            summary="this, closures, hoisting, equality, event-loop ordering, utilities and output-prediction puzzles.",
            lessons=[
                dict(id="interview-core", title="Interview core: this, closures, hoisting, equality", file="36-interview-core.md"),
                dict(id="interview-async-utilities", title="Interview async and utilities: ordering, debounce, clone, leaks", file="37-interview-async-utilities.md"),
            ],
            problems=["js-throttle-sim", "js-curry"],
        ),
    ],
)
