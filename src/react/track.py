TRACK = dict(
    id="react",
    title="React (with Firebase)",
    icon="⚛️",
    color="#0e9fbf",
    group="Web",
    blurb="Modern React from the first component to how the reconciler works: state, effects, data fetching, forms, "
          "routing, testing and TypeScript, then a full Firebase back end (auth, Firestore, security rules, hosting). "
          "Every idea runs live in the page with a hand-written mini React, plus 30 judged problems.",
    sources=[
        "Wieruch, The Road to React",
        "Wieruch, The Road to React with Firebase",
        "react.dev (official React documentation)",
        "firebase.google.com/docs (official Firebase documentation)",
    ],
    modules=[
        dict(
            id="fundamentals",
            title="Fundamentals: Components, JSX and Events",
            summary="Why React exists, setting up a project with Vite, describing UI with JSX, props, lists, keys and events.",
            lessons=[
                dict(id="why-react-vite", title="Why React, and a first project with Vite", file="01-why-react-vite.md"),
                dict(id="jsx-components-props", title="JSX, components and props", file="02-jsx-components-props.md"),
                dict(id="lists-keys-events", title="Lists, keys and events", file="03-lists-keys-events.md"),
            ],
            problems=["react-create-element", "react-event-delegation"],
        ),
        dict(
            id="state",
            title="State and Data Flow",
            summary="useState, state as a snapshot, lifting state, controlled inputs, composition and conditional rendering.",
            lessons=[
                dict(id="usestate", title="State with useState", file="04-usestate.md"),
                dict(id="lifting-controlled", title="Lifting state and controlled components", file="05-lifting-controlled.md"),
                dict(id="composition-conditional", title="Composition, children and conditional rendering", file="06-composition-conditional.md"),
            ],
            problems=["react-batch-updates", "react-set-in", "react-list-ops", "react-derive-view", "react-format-phone"],
        ),
        dict(
            id="effects-data",
            title="Side Effects and Data",
            summary="useEffect and its dependency rules, custom hooks, refs, legacy class components and their lifecycle, and fetching data with loading and error states.",
            lessons=[
                dict(id="useeffect", title="useEffect and its dependency rules", file="07-useeffect.md"),
                dict(id="custom-hooks-refs", title="Custom hooks and useRef", file="08-custom-hooks-refs.md"),
                dict(id="class-components", title="Class components: reading and migrating legacy React", file="08b-class-components.md"),
                dict(id="data-fetching", title="Fetching data: loading, errors and races", file="09-data-fetching.md"),
            ],
            problems=["react-deps-changed", "react-hooks-runtime", "react-fetch-reducer"],
        ),
        dict(
            id="advanced-state",
            title="Reducers, Forms and Memoisation",
            summary="useReducer and impossible states, forms the React way, and memo/useMemo/useCallback with honest advice on when to skip them.",
            lessons=[
                dict(id="usereducer", title="useReducer and impossible states", file="10-usereducer.md"),
                dict(id="forms", title="Forms", file="11-forms.md"),
                dict(id="memoization", title="memo, useMemo and useCallback", file="12-memoization.md"),
            ],
            problems=["react-todo-reducer", "react-form-machine", "react-shallow-deep-equal", "react-memo-shallow"],
        ),
        dict(
            id="maintenance",
            title="Styling and Maintenance",
            summary="Styling approaches, TypeScript with React, testing with Vitest and React Testing Library, project structure and profiling.",
            lessons=[
                dict(id="styling", title="Styling approaches", file="13-styling.md"),
                dict(id="typescript", title="TypeScript with React", file="14-typescript.md"),
                dict(id="testing", title="Testing with Vitest and React Testing Library", file="15-testing.md"),
                dict(id="structure-profiling", title="Project structure and performance profiling", file="16-structure-profiling.md"),
            ],
            problems=[],
        ),
        dict(
            id="real-world",
            title="Real-World Features",
            summary="Sorting, searching, pagination, optimistic updates, routing, context and global state, Suspense, error boundaries and server components.",
            lessons=[
                dict(id="sort-search-paginate", title="Sorting, searching, pagination and optimistic updates", file="17-sort-search-paginate.md"),
                dict(id="routing", title="Routing with React Router", file="18-routing.md"),
                dict(id="context-global-state", title="Context and global state", file="19-context-global-state.md"),
                dict(id="suspense-boundaries-rsc", title="Suspense, error boundaries and server components", file="20-suspense-boundaries-rsc.md"),
            ],
            problems=["react-sort-table", "react-paginate", "react-page-window", "react-optimistic-update",
                      "react-route-matcher", "react-context-lookup", "react-entity-cache"],
        ),
        dict(
            id="internals",
            title="How React Works",
            summary="The virtual DOM, reconciliation and keys, the render and commit phases, batching and fibers.",
            lessons=[
                dict(id="virtual-dom", title="The virtual DOM and reconciliation", file="21-virtual-dom.md"),
                dict(id="render-commit", title="Render, commit, batching and fibers", file="22-render-commit.md"),
            ],
            problems=["react-render-to-string", "react-keyed-list-diff", "react-vdom-diff"],
        ),
        dict(
            id="firebase-auth",
            title="Firebase: Setup and Authentication",
            summary="Creating a Firebase project, sign up, sign in, sign out, password reset, social login, email verification, sessions, protected routes and roles.",
            lessons=[
                dict(id="firebase-setup-auth", title="Firebase setup and authentication flows", file="23-firebase-setup-auth.md"),
                dict(id="sessions-roles", title="Sessions, protected routes and roles", file="24-sessions-roles.md"),
            ],
            problems=["react-route-guard"],
        ),
        dict(
            id="firebase-data",
            title="Firebase: Data, Rules and Deployment",
            summary="Firestore and the Realtime Database, modelling, queries, listeners, security rules, hosting, app structure, and when to choose a custom back end.",
            lessons=[
                dict(id="firestore-rtdb", title="Firestore and the Realtime Database", file="25-firestore-rtdb.md"),
                dict(id="security-rules", title="Security rules", file="26-security-rules.md"),
                dict(id="hosting-structure", title="Hosting, app structure, and Firebase vs a custom backend", file="27-hosting-structure.md"),
            ],
            problems=["react-firestore-query", "react-snapshot-changes", "react-rules-evaluator"],
        ),
        dict(
            id="interview",
            title="React Interview Essentials",
            summary="Worked answers: the life of a render, keys, stale closures, effect pitfalls, controlled vs uncontrolled, state colocation, and three classic builds.",
            lessons=[
                dict(id="interview-concepts", title="Interview essentials: renders, keys, closures and effects", file="28-interview-concepts.md"),
                dict(id="interview-builds", title="Interview builds: debounced search, modal, infinite scroll", file="29-interview-builds.md"),
            ],
            problems=["react-stale-closure", "react-debounce-search"],
        ),
    ],
)
