from pathlib import Path

_HERE = Path(__file__).resolve().parent


def L(id, title, file):
    return dict(id=id, title=title, file=file)


_MODULES = [
    dict(
        id="from-zero", title="Node.js from zero",
        summary="What Node.js is, installing it, running scripts, npm and package.json, reading a file and a first HTTP server.",
        lessons=[
            L("what-is-node", "What Node.js is: install, run a script, read a file", "01-what-is-node.md"),
            L("npm-first-server", "npm, package.json and your first HTTP server", "02-npm-first-server.md"),
        ],
        problems=["node-semver-satisfies"],
    ),
    dict(
        id="platform", title="The Node.js Platform",
        summary="The design philosophy, slow I/O, the reactor pattern, libuv, and the phases of the event loop.",
        lessons=[
            L("nonblocking-reactor", "Philosophy, non-blocking I/O and the reactor pattern", "03-nonblocking-reactor.md"),
            L("event-loop-phases", "The event loop in detail: phases, microtasks and the thread pool", "04-event-loop-phases.md"),
        ],
        problems=["node-event-loop-flat", "node-event-loop-nested"],
    ),
    dict(
        id="module-system", title="The Module System",
        summary="CommonJS and ES modules: how files are found, loaded once, cached, and what happens when they import each other in a circle.",
        lessons=[
            L("commonjs-modules", "CommonJS: require, resolution, the cache and cycles", "05-commonjs-modules.md"),
            L("es-modules-node", "ES modules in Node: live bindings, loading phases and interop", "06-es-modules-node.md"),
        ],
        problems=["node-module-resolution", "node-require-cycle"],
    ),
    dict(
        id="callbacks-events", title="Callbacks and Events",
        summary="The callback pattern and its conventions, and the observer pattern with EventEmitter.",
        lessons=[
            L("callback-pattern", "The callback pattern and its conventions", "07-callback-pattern.md"),
            L("observer-eventemitter", "The observer pattern and EventEmitter", "08-observer-eventemitter.md"),
        ],
        problems=["node-mini-emitter"],
    ),
    dict(
        id="async-callbacks", title="Asynchronous Control Flow with Callbacks",
        summary="Taming callback hell, then running tasks in sequence, in parallel and with a concurrency limit.",
        lessons=[
            L("callback-hell-sequential", "Callback hell, its cures and sequential execution", "09-callback-hell-sequential.md"),
            L("parallel-limited-callbacks", "Parallel execution, race conditions and limited concurrency", "10-parallel-limited-callbacks.md"),
        ],
        problems=["node-run-sequential", "node-run-parallel", "node-run-limited"],
    ),
    dict(
        id="promises-async-await", title="Promises and Async/Await",
        summary="Promises, promisification, async functions, sequential and parallel flows, limited concurrency and the classic pitfalls.",
        lessons=[
            L("promises-promisification", "Promises and promisification", "11-promises-promisification.md"),
            L("async-await-flows", "Async/await: sequential and parallel flows", "12-async-await-flows.md"),
            L("async-limits-pitfalls", "Limited concurrency and async pitfalls", "13-async-limits-pitfalls.md"),
        ],
        problems=["node-promisify", "node-retry-backoff", "node-priority-queue"],
    ),
    dict(
        id="streams", title="Coding with Streams",
        summary="Readable, writable, duplex and transform streams, backpressure, pipelines and piping patterns.",
        lessons=[
            L("streams-readable-writable", "Why streams: readable, writable and backpressure", "14-streams-readable-writable.md"),
            L("transform-pipeline", "Duplex, transform and pipeline", "15-transform-pipeline.md"),
            L("stream-patterns", "Stream patterns: concurrency, combining, forking, merging, multiplexing", "16-stream-patterns.md"),
        ],
        problems=["node-lines-from-chunks", "node-stream-pipeline"],
    ),
    dict(
        id="creational", title="Creational Design Patterns",
        summary="Factory, builder, revealing constructor, singleton and module caching, and dependency injection.",
        lessons=[
            L("factory-builder-revealing", "Factory, builder and revealing constructor", "17-factory-builder-revealing.md"),
            L("singleton-di", "Singleton, module wiring and dependency injection", "18-singleton-di.md"),
        ],
        problems=["node-factory", "node-builder", "node-di-container"],
    ),
    dict(
        id="structural", title="Structural Design Patterns",
        summary="Proxy, decorator and adapter: wrapping objects to control, extend or translate them.",
        lessons=[
            L("proxy-pattern", "The proxy pattern", "19-proxy-pattern.md"),
            L("decorator-adapter", "Decorator and adapter", "20-decorator-adapter.md"),
        ],
        problems=["node-proxy", "node-decorator", "node-adapter"],
    ),
    dict(
        id="behavioural", title="Behavioural Design Patterns",
        summary="Strategy, state, template, iterator and generators, middleware and command.",
        lessons=[
            L("strategy-state-template", "Strategy, state and template", "21-strategy-state-template.md"),
            L("iterators-generators", "Iterators, generators and async iterators", "22-iterators-generators.md"),
            L("middleware-command", "Middleware and command", "23-middleware-command.md"),
        ],
        problems=["node-strategy", "node-state-machine", "node-iterator", "node-middleware-onion", "node-command-undo"],
    ),
    dict(
        id="universal", title="Universal JavaScript",
        summary="Sharing code between the browser and the server: bundlers, code branching, server-side rendering and hydration.",
        lessons=[
            L("universal-sharing-code", "Sharing code between browser and server", "24-universal-sharing-code.md"),
            L("universal-ssr", "Server-side rendering, hydration and universal data loading", "25-universal-ssr.md"),
        ],
        problems=[],
    ),
    dict(
        id="recipes", title="Advanced Recipes",
        summary="Asynchronously initialised components, request batching and caching, cancellation, and CPU-bound work.",
        lessons=[
            L("async-init-batching", "Async initialisation, request batching and caching", "26-async-init-batching.md"),
            L("cancel-cpu-bound", "Cancelling async work and running CPU-bound tasks", "27-cancel-cpu-bound.md"),
        ],
        problems=["node-batch-cache", "node-cancel-token"],
    ),
    dict(
        id="scalability", title="Scalability and Architecture",
        summary="The scale cube, cluster, load balancing, zero-downtime restarts, containers and microservices.",
        lessons=[
            L("scaling-cluster", "The scale cube, cluster and zero-downtime restarts", "28-scaling-cluster.md"),
            L("balancing-microservices", "Reverse proxies, service discovery and microservices", "29-balancing-microservices.md"),
        ],
        problems=["node-round-robin", "node-consistent-hash"],
    ),
    dict(
        id="messaging", title="Messaging and Integration",
        summary="Publish/subscribe, task distribution with queues, and request/reply, with Redis and message brokers.",
        lessons=[
            L("messaging-pubsub", "Messaging fundamentals and publish/subscribe", "30-messaging-pubsub.md"),
            L("queues-request-reply", "Task queues, competing consumers and request/reply", "31-queues-request-reply.md"),
        ],
        problems=["node-pubsub-broker", "node-work-queue", "node-request-reply"],
    ),
    dict(
        id="production-interview", title="Node.js in production and interview essentials",
        summary="Express and Fastify basics, error handling, logging, configuration, security, event-loop puzzles, leaks and when not to use Node.",
        lessons=[
            L("production-basics", "Production basics: frameworks, errors, logging, config, security", "32-production-basics.md"),
            L("interview-essentials", "Interview essentials: ordering puzzles, leaks, streams vs buffers", "33-interview-essentials.md"),
        ],
        problems=["node-lru-cache"],
    ),
]

# While the track is being written, list only what exists on disk (a no-op once the track is complete).
_DEFINED = "".join(p.read_text(encoding="utf-8") for p in sorted((_HERE / "problems").glob("*.py")))
for _m in _MODULES:
    _m["lessons"] = [l for l in _m["lessons"] if (_HERE / "lessons" / l["file"]).exists()]
    _m["problems"] = [p for p in _m["problems"] if f'id="{p}"' in _DEFINED]

TRACK = dict(
    id="nodejs",
    title="Node.js Design Patterns",
    icon="🟩",
    color="#3c873a",
    group="Web",
    blurb="Node.js from the first script to production: the event loop, modules, callbacks, promises and streams, "
          "the classic design patterns in idiomatic JavaScript, scaling and messaging, with runnable models and judged problems.",
    sources=[
        "Casciaro & Mammino, Node.js Design Patterns (3rd ed.), ch. 1-13",
        "Node.js API documentation (nodejs.org/docs/latest/api)",
    ],
    modules=_MODULES,
)
