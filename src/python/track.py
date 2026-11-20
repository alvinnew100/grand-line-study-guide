TRACK = dict(
    id="python",
    title="Python Mastery",
    icon="🐍",
    color="#3776ab",
    group="Python",
    blurb="From names and references to decorators, generators, the data model, typing, asyncio and "
          "CPython internals: the Python you need to read, write and defend in an interview.",
    sources=[
        "Goodrich, Tamassia & Goldwasser, Data Structures and Algorithms in Python, ch. 1-2",
        "The Python Tutorial, Language Reference (Data Model) and Library Reference, docs.python.org/3",
    ],
    modules=[
        dict(
            id="py-basics",
            title="Python Basics",
            summary="Objects, names and references, built-in types, mutability, operators, control flow and functions.",
            lessons=[
                dict(id="py-objects-names", title="Objects, names, types and mutability", file="01-objects-names-types.md"),
                dict(id="py-operators-control", title="Expressions, operators and control flow", file="02-operators-control-flow.md"),
                dict(id="py-functions-args", title="Functions and arguments", file="03-functions-arguments.md"),
            ],
            problems=["py-count-calls", "py-flatten-dict"],
        ),
        dict(
            id="py-builtins",
            title="Built-in Data Structures in Depth",
            summary="list, tuple, str, dict and set: operations, costs, slicing, comprehensions and copying.",
            lessons=[
                dict(id="py-sequences", title="Lists, tuples and strings", file="04-sequences.md"),
                dict(id="py-dicts-sets", title="Dictionaries and sets", file="05-dicts-sets.md"),
                dict(id="py-comprehensions-copying", title="Comprehensions, unpacking and copying", file="06-comprehensions-copying.md"),
            ],
            problems=["py-group-anagrams", "py-deep-merge", "py-unique-everseen"],
        ),
        dict(
            id="py-functions-deeper",
            title="Functions, Deeper",
            summary="Scope and LEGB, closures, lambdas, decorators and the functools toolbox.",
            lessons=[
                dict(id="py-scope-closures", title="Scope, closures and lambdas", file="07-scope-closures-lambdas.md"),
                dict(id="py-decorators", title="Decorators and functools", file="08-decorators-functools.md"),
            ],
            problems=["py-memoize", "py-retry"],
        ),
        dict(
            id="py-iteration",
            title="Iteration",
            summary="The iterator protocol, generators, yield from, generator expressions and itertools.",
            lessons=[
                dict(id="py-iterator-protocol", title="The iterator protocol", file="09-iterator-protocol.md"),
                dict(id="py-generators", title="Generators and yield from", file="10-generators.md"),
                dict(id="py-itertools", title="itertools and lazy pipelines", file="11-itertools.md"),
            ],
            problems=["py-custom-range", "py-flatten", "py-chunked", "py-moving-average", "py-groupby", "py-run-length"],
        ),
        dict(
            id="py-oop",
            title="Object-Oriented Python",
            summary="Classes, inheritance, MRO and super, the data model, properties, dataclasses, ABCs and composition.",
            lessons=[
                dict(id="py-classes", title="Classes and instances", file="12-classes.md"),
                dict(id="py-inheritance", title="Inheritance, MRO and super", file="13-inheritance-mro.md"),
                dict(id="py-data-model", title="The data model: dunder methods", file="14-data-model.md"),
                dict(id="py-properties-dataclasses", title="Properties, dataclasses, ABCs and composition", file="15-properties-dataclasses-abc.md"),
            ],
            problems=["py-vector", "py-temperature", "py-dataclass-sort"],
        ),
        dict(
            id="py-errors",
            title="Errors and Context Managers",
            summary="Exceptions, custom exception hierarchies, the with statement and contextlib.",
            lessons=[
                dict(id="py-exceptions", title="Exceptions", file="16-exceptions.md"),
                dict(id="py-context-managers", title="Context managers and contextlib", file="17-context-managers.md"),
            ],
            problems=["py-timer", "py-suppress-log"],
        ),
        dict(
            id="py-modules",
            title="Modules, Packages and Environments",
            summary="Imports, packages, virtual environments, pip and uv, and a sane project layout.",
            lessons=[
                dict(id="py-imports", title="Modules, packages and imports", file="18-modules-packages.md"),
                dict(id="py-envs", title="Virtual environments, pip, uv and project layout", file="19-venvs-pip-uv.md"),
            ],
            problems=[],
        ),
        dict(
            id="py-typing",
            title="Typing",
            summary="Type hints, generics, Protocol, TypedDict, mypy, and a first look at Pydantic.",
            lessons=[
                dict(id="py-type-hints", title="Type hints and mypy", file="20-type-hints.md"),
                dict(id="py-advanced-typing", title="Generics, Protocol, TypedDict and Pydantic", file="21-advanced-typing.md"),
            ],
            problems=[],
        ),
        dict(
            id="py-stdlib",
            title="The Standard Library for Interviews",
            summary="collections, heapq, bisect, sorting with keys, math and string tricks.",
            lessons=[
                dict(id="py-collections", title="collections: deque, Counter, defaultdict, OrderedDict", file="22-collections.md"),
                dict(id="py-heapq-bisect-sorting", title="heapq, bisect, sorting and math", file="23-heapq-bisect-sorting.md"),
            ],
            problems=["py-top-k-words", "py-lru-cache", "py-kth-largest", "py-merge-sorted"],
        ),
        dict(
            id="py-concurrency",
            title="Concurrency",
            summary="The GIL, threads, processes, and asyncio with async/await, tasks and gather.",
            lessons=[
                dict(id="py-threads-processes", title="The GIL, threading and multiprocessing", file="24-gil-threads-processes.md"),
                dict(id="py-asyncio", title="asyncio: async/await, tasks and gather", file="25-asyncio.md"),
            ],
            problems=["py-async-gather"],
        ),
        dict(
            id="py-files",
            title="Files, Data Formats and Regex",
            summary="Reading and writing files, pathlib, JSON, CSV and regular expressions.",
            lessons=[
                dict(id="py-files-json-csv", title="Files, pathlib, JSON and CSV", file="26-files-json-csv.md"),
                dict(id="py-regex", title="Regular expressions", file="27-regex.md"),
            ],
            problems=["py-parse-logs", "py-csv-records", "py-json-path"],
        ),
        dict(
            id="py-testing",
            title="Testing and Debugging",
            summary="pytest from first test to fixtures and parametrize, plus debugging with pdb and logging.",
            lessons=[
                dict(id="py-pytest", title="Testing with pytest", file="28-pytest.md"),
                dict(id="py-debugging", title="Debugging and logging", file="29-debugging.md"),
            ],
            problems=[],
        ),
        dict(
            id="py-performance",
            title="Pythonic Idioms and Performance",
            summary="Idiomatic code, the cost of builtins, profiling, memory, and how CPython actually runs your code.",
            lessons=[
                dict(id="py-idioms", title="Pythonic idioms", file="30-idioms.md"),
                dict(id="py-profiling", title="Performance, profiling and memory", file="31-performance.md"),
                dict(id="py-cpython", title="CPython internals: bytecode, refcounting and GC", file="32-cpython-internals.md"),
            ],
            problems=[],
        ),
    ],
)
