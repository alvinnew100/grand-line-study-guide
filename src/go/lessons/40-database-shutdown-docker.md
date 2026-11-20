# Postgres, configuration, graceful shutdown and Docker

> **Before this lesson:** read [A REST service: routing, handlers and middleware](#/lesson/go/go-rest-service), which built the task API and its `TaskStore` interface. You also need contexts with deadlines ([Deadlines, timeouts and context values](#/lesson/go/go-context-deadlines-values)), `defer` and error wrapping, goroutines and channels, and cross-compilation ([embed, go generate and cross-compilation](#/lesson/go/go-embed-generate-cross)). Basic SQL (`SELECT`, `INSERT`) helps; the [SQL track](#/track/sql) teaches it from zero.

## In plain words

The service from the previous lesson works, and it has four weaknesses that keep it from being a real product.

1. **It forgets everything when it stops.** Tasks live in a map in memory. A real service stores data in a **database**, a separate program whose job is to keep data safe on disk and find it quickly. We will use **PostgreSQL** (often shortened to Postgres), a popular free database.
2. **Its settings are written into the code.** The port and the database address differ between your laptop, the test environment and production. Settings that vary by environment are **configuration**, and they should come from outside the program.
3. **It dies mid-sentence.** When a new version is deployed, the old process is told to stop. If it stops instantly, requests that were being handled at that moment fail. A polite program finishes what it is doing first. That is **graceful shutdown**: a restaurant that stops seating new guests at closing time, lets those already eating finish, and only then switches off the lights.
4. **It only runs where Go and its surroundings are set up.** A **container** packages a program with everything it needs into a sealed, standard box that runs the same way on any machine. **Docker** is the best-known tool for building and running containers.

This lesson fixes all four, and the result is the skeleton of a production Go service.

Why this matters for a job: these are the parts of a take-home assignment that separate "it works on my machine" from "this person has shipped software". Interviewers ask how connection pools work, how you prevent SQL injection, how a Go server shuts down cleanly and what your Dockerfile looks like.

**Compared with Python.** Python services typically use an ORM such as SQLAlchemy or Django's, run under a separate server process (gunicorn, uvicorn), and ship in images containing an interpreter and installed packages. A Go service usually writes SQL directly, is its own server, and ships as one static binary in an almost empty image.

## Part 1: PostgreSQL through database/sql

### The pieces

The standard library package **`database/sql`** defines a common way to talk to SQL databases. It does not know any particular database; for that you add a **driver**, a package that speaks one database's network protocol. For Postgres the usual choice today is **pgx**:

```text
$ go get github.com/jackc/pgx/v5
```

```go
import (
	"database/sql"

	_ "github.com/jackc/pgx/v5/stdlib" // blank import: registers the driver named "pgx"
)
```

The blank import runs the driver's `init`, which registers it with `database/sql` ([Packages, visibility and imports](#/lesson/go/go-packages-imports)).

### Opening a pool

```go
func openDB(ctx context.Context, url string) (*sql.DB, error) {
	db, err := sql.Open("pgx", url) // validates arguments; does not connect yet
	if err != nil {
		return nil, fmt.Errorf("open database: %w", err)
	}

	db.SetMaxOpenConns(10)                  // at most 10 connections to the database
	db.SetMaxIdleConns(5)                   // keep up to 5 ready for reuse
	db.SetConnMaxLifetime(30 * time.Minute) // recycle connections periodically

	pingCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	if err := db.PingContext(pingCtx); err != nil { // actually connect, to fail fast
		db.Close()
		return nil, fmt.Errorf("ping database: %w", err)
	}
	return db, nil
}
```

The URL looks like `postgres://user:password@host:5432/dbname?sslmode=disable`.

The most important fact about `*sql.DB`: **it is not one connection. It is a connection pool.** Opening a connection to a database is slow, so the pool keeps a set of open connections, lends one out for each query and takes it back afterwards. Consequences:

- Create **one** `*sql.DB` when the program starts, share it everywhere, and close it when the program ends. It is safe for concurrent use.
- `SetMaxOpenConns` matters. Without a limit, a burst of requests opens connections until the database refuses more. With a limit, extra queries wait their turn, which is backpressure.
- `sql.Open` does not contact the database. `PingContext` does; call it at start-up so that a wrong address stops the program immediately instead of failing on the first request.

### The table

```sql
CREATE TABLE tasks (
    id    BIGSERIAL PRIMARY KEY,
    title TEXT      NOT NULL,
    done  BOOLEAN   NOT NULL DEFAULT FALSE
);
```

`BIGSERIAL` makes the database assign increasing IDs. Changes to the schema over time are managed with **migrations**: numbered SQL files applied in order by a tool such as `golang-migrate` or `goose`, often embedded in the binary with `//go:embed`.

### The store

This type satisfies the `TaskStore` interface from the previous lesson. No handler changes.

```go
type postgresStore struct {
	db *sql.DB
}

func (s *postgresStore) Create(ctx context.Context, title string) (Task, error) {
	const q = `INSERT INTO tasks (title) VALUES ($1) RETURNING id, title, done`
	var t Task
	err := s.db.QueryRowContext(ctx, q, title).Scan(&t.ID, &t.Title, &t.Done)
	if err != nil {
		return Task{}, fmt.Errorf("insert task: %w", err)
	}
	return t, nil
}

func (s *postgresStore) Get(ctx context.Context, id int) (Task, error) {
	const q = `SELECT id, title, done FROM tasks WHERE id = $1`
	var t Task
	err := s.db.QueryRowContext(ctx, q, id).Scan(&t.ID, &t.Title, &t.Done)
	if errors.Is(err, sql.ErrNoRows) {
		return Task{}, ErrNotFound // translate the database's error into ours
	}
	if err != nil {
		return Task{}, fmt.Errorf("select task %d: %w", id, err)
	}
	return t, nil
}

func (s *postgresStore) List(ctx context.Context) ([]Task, error) {
	const q = `SELECT id, title, done FROM tasks ORDER BY id`
	rows, err := s.db.QueryContext(ctx, q)
	if err != nil {
		return nil, fmt.Errorf("select tasks: %w", err)
	}
	defer rows.Close() // returns the connection to the pool

	tasks := []Task{}
	for rows.Next() {
		var t Task
		if err := rows.Scan(&t.ID, &t.Title, &t.Done); err != nil {
			return nil, fmt.Errorf("scan task: %w", err)
		}
		tasks = append(tasks, t)
	}
	if err := rows.Err(); err != nil { // an error that ended the loop early
		return nil, fmt.Errorf("iterate tasks: %w", err)
	}
	return tasks, nil
}

func (s *postgresStore) Delete(ctx context.Context, id int) error {
	res, err := s.db.ExecContext(ctx, `DELETE FROM tasks WHERE id = $1`, id)
	if err != nil {
		return fmt.Errorf("delete task %d: %w", id, err)
	}
	n, err := res.RowsAffected()
	if err != nil {
		return fmt.Errorf("delete task %d: %w", id, err)
	}
	if n == 0 {
		return ErrNotFound
	}
	return nil
}
```

Three methods cover almost all use:

| Method | For | Returns |
|---|---|---|
| `QueryRowContext` | a query expected to return at most one row | a `*Row`; call `.Scan(...)` |
| `QueryContext` | a query returning many rows | `*Rows`; loop with `Next`, `Scan`, then check `Err`; always `Close` |
| `ExecContext` | statements that return no rows (`INSERT`, `UPDATE`, `DELETE`) | a `Result` with `RowsAffected()` |

Always use the `...Context` variants, with the request's context, so that a cancelled or timed-out request cancels its query.

Details that matter:

- **`Scan` copies columns into variables**, in order, through pointers. The number and types must match the selected columns.
- **`QueryRowContext(...).Scan` returns `sql.ErrNoRows`** when nothing matched. The store converts that into its own `ErrNotFound`, so the HTTP layer never needs to know that SQL exists.
- **`rows.Close()` must be called** (deferred). Until then the connection stays checked out of the pool; forgetting it eventually exhausts the pool and every request hangs.
- **`rows.Err()` after the loop**: `rows.Next()` returns `false` both at the end and on a failure.
- A column that can be `NULL` cannot be scanned into a plain `string` or `int`. Use a pointer (`*string`) or the wrapper types `sql.NullString`, `sql.NullInt64`, or the generic `sql.Null[T]`.

### Placeholders and SQL injection

Look at how values enter the queries: as `$1`, `$2`, with the actual values passed as separate arguments. These are **placeholders**. The database receives the SQL text and the values separately and never interprets a value as SQL.

The alternative is catastrophic:

```go
// NEVER do this
q := "SELECT id, title, done FROM tasks WHERE title = '" + userInput + "'"
```

If `userInput` is `x'; DROP TABLE tasks; --`, the text becomes two statements, and the second deletes your table. This attack is **SQL injection**, and it has been among the most damaging vulnerabilities on the web for decades. Placeholders prevent it completely. **Never build SQL by concatenating or formatting user-supplied values.** (Postgres uses `$1`; MySQL and SQLite use `?`.)

### Transactions

Sometimes several statements must succeed or fail **together**. Marking a task done and recording that fact in a history table should not half-happen. A **transaction** groups statements: either all take effect (**commit**) or none do (**rollback**).

```go
func (s *postgresStore) Complete(ctx context.Context, id int) (err error) {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("begin: %w", err)
	}
	defer tx.Rollback() // does nothing if the transaction was already committed

	res, err := tx.ExecContext(ctx, `UPDATE tasks SET done = TRUE WHERE id = $1`, id)
	if err != nil {
		return fmt.Errorf("update task %d: %w", id, err)
	}
	if n, _ := res.RowsAffected(); n == 0 {
		return ErrNotFound
	}
	if _, err := tx.ExecContext(ctx, `INSERT INTO task_events (task_id, kind) VALUES ($1, 'completed')`, id); err != nil {
		return fmt.Errorf("record event: %w", err)
	}
	return tx.Commit()
}
```

The pattern is "begin, `defer tx.Rollback()`, do the work **through `tx`**, commit at the end". Any early return leaves through the deferred rollback and nothing is changed. A transaction holds one connection for its whole duration, so keep transactions short and never do slow outside work (HTTP calls) inside one.

Some teams add tools on top of `database/sql`: `sqlc` generates typed Go functions from SQL files; `pgx` can be used directly for more speed and Postgres-specific features; ORMs such as GORM and ent map structs to tables. The fundamentals above apply to all of them.

## Part 2: configuration

Follow one rule: **code is the same in every environment; configuration comes from the environment.** The simplest carrier, supported by every deployment platform and by Docker, is **environment variables**: named strings that the operating system passes to a process when it starts.

```go
type Config struct {
	Addr            string        // where the HTTP server listens
	DatabaseURL     string        // required
	ShutdownTimeout time.Duration
	LogLevel        slog.Level
}

func loadConfig() (Config, error) {
	cfg := Config{
		Addr:            getenv("HTTP_ADDR", ":8080"),
		DatabaseURL:     os.Getenv("DATABASE_URL"),
		ShutdownTimeout: 15 * time.Second,
		LogLevel:        slog.LevelInfo,
	}
	if cfg.DatabaseURL == "" {
		return Config{}, errors.New("DATABASE_URL is required")
	}
	if v := os.Getenv("SHUTDOWN_TIMEOUT"); v != "" {
		d, err := time.ParseDuration(v)
		if err != nil {
			return Config{}, fmt.Errorf("SHUTDOWN_TIMEOUT: %w", err)
		}
		cfg.ShutdownTimeout = d
	}
	if v := os.Getenv("LOG_LEVEL"); v != "" {
		if err := cfg.LogLevel.UnmarshalText([]byte(v)); err != nil {
			return Config{}, fmt.Errorf("LOG_LEVEL: %w", err)
		}
	}
	return cfg, nil
}

func getenv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
```

Principles:

- **Read configuration once, at start-up, into a typed struct.** The rest of the program receives values, not variable names. Code that calls `os.Getenv` deep inside a handler is hard to test and hides what the program depends on.
- **Validate and fail fast.** A missing or malformed setting should stop the program at launch with a clear message, not at the first request three hours later.
- **Sensible defaults for what is safe** (a port), **no defaults for what is dangerous** (database credentials).
- **Never commit secrets** (passwords, API keys) to the repository, and never log them. They arrive through the environment or a secrets manager.

Command-line flags (package `flag`) are the other standard carrier and suit tools run by hand. Larger projects use libraries that merge files, variables and flags; the principles stay the same.

## Part 3: graceful shutdown

### The problem

Deployment platforms stop a program by sending it a **signal**, a notification from the operating system. The standard one is `SIGTERM` ("please terminate"); pressing Ctrl+C in a terminal sends `SIGINT`. If the program ignores the request, after a grace period (30 seconds by default in Kubernetes, 10 in Docker) it is killed outright with `SIGKILL`.

By default a Go program exits the instant it receives `SIGTERM`. Requests in progress are cut off and their clients see errors. With several deployments a day, that is a steady trickle of failures for no reason.

### The solution

```go
func run() error {
	cfg, err := loadConfig()
	if err != nil {
		return err
	}
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: cfg.LogLevel}))

	// ctx is cancelled when the process receives SIGINT or SIGTERM
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	db, err := openDB(ctx, cfg.DatabaseURL)
	if err != nil {
		return err
	}
	defer db.Close()

	api := &API{store: &postgresStore{db: db}, log: logger}
	srv := &http.Server{
		Addr:              cfg.Addr,
		Handler:           api.Routes(),
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       15 * time.Second,
		WriteTimeout:      30 * time.Second,
		IdleTimeout:       120 * time.Second,
	}

	serverErr := make(chan error, 1)
	go func() {
		logger.Info("server listening", "addr", cfg.Addr)
		serverErr <- srv.ListenAndServe()
	}()

	select {
	case err := <-serverErr: // the server failed to start or crashed
		return fmt.Errorf("server: %w", err)
	case <-ctx.Done(): // a shutdown signal arrived
		logger.Info("shutdown requested")
	}

	shutdownCtx, cancel := context.WithTimeout(context.Background(), cfg.ShutdownTimeout)
	defer cancel()
	if err := srv.Shutdown(shutdownCtx); err != nil {
		return fmt.Errorf("graceful shutdown: %w", err)
	}
	logger.Info("server stopped cleanly")
	return nil
}

func main() {
	if err := run(); err != nil {
		slog.Error("fatal", "err", err)
		os.Exit(1)
	}
}
```

Walk through the sequence:

1. **`signal.NotifyContext`** returns a context that is cancelled when one of the listed signals arrives. A signal becomes an ordinary cancellation.
2. **The server runs in its own goroutine**, because `ListenAndServe` blocks. Its result goes to a buffered channel.
3. **`main` waits with `select`** for one of two things: the server failing, or the shutdown signal.
4. **`srv.Shutdown(ctx)`** does the polite closing: it stops accepting new connections, closes idle ones, and waits for requests in progress to finish. It gives up when its context expires, which is why it gets a fresh context with a timeout (the first one is already cancelled).
5. **Deferred clean-ups run in reverse order**, so the database pool closes **after** the server has drained. Closing it first would break the requests still running.

Two structural choices are worth copying. Everything lives in `run() error`, and `main` only calls it and sets the exit code: `os.Exit` skips deferred functions, so calling it inside `run` would skip `db.Close()`. And when `Shutdown` is called, `ListenAndServe` returns `http.ErrServerClosed` at once; that is expected, not a failure.

```mermaid
sequenceDiagram
    participant P as platform
    participant M as main goroutine
    participant S as http.Server
    participant R as in-flight requests
    participant D as database pool
    P->>M: SIGTERM
    M->>S: Shutdown(ctx with 15s timeout)
    S-->>P: stop accepting new connections
    R-->>S: running requests finish normally
    S-->>M: Shutdown returns nil
    M->>D: db.Close()
    M-->>P: exit status 0
```

### Try it: abrupt versus graceful

```python-run
def shutdown(in_flight, signal_at, graceful, timeout):
    """in_flight: (name, start, duration). Returns one outcome line per request."""
    out = []
    for name, start, duration in in_flight:
        end = start + duration
        if start >= signal_at:
            out.append(f"{name}: arrived after the signal -> refused (load balancer retries elsewhere)")
        elif end <= signal_at:
            out.append(f"{name}: finished at {end} before the signal -> OK")
        elif not graceful:
            out.append(f"{name}: running at the signal -> CUT OFF, client sees an error")
        elif end <= signal_at + timeout:
            out.append(f"{name}: allowed to finish at {end} -> OK")
        else:
            out.append(f"{name}: still running at the deadline {signal_at + timeout} -> cut off")
    return out

requests = [("A", 0, 3), ("B", 8, 4), ("C", 9, 30), ("D", 11, 2)]
for label, graceful in (("abrupt exit", False), ("graceful, 15 s timeout", True)):
    print(f"--- SIGTERM at t=10, {label} ---")
    for line in shutdown(requests, signal_at=10, graceful=graceful, timeout=15):
        print("   ", line)
```

Request B survives only in the graceful version. Request C shows why there is a timeout: a request that will not finish in time cannot be allowed to block shutdown for ever.

### Health checks

Platforms ask a service whether it is all right by calling an endpoint. Provide two:

- **Liveness** (`GET /healthz`): "the process is running". Return 200 without checking anything else. If it fails, the platform restarts the process.
- **Readiness** (`GET /readyz`): "I can serve traffic now". Check essential dependencies, for example `db.PingContext` with a short timeout, and return 503 when they are unavailable. The platform then stops routing requests to this instance without killing it.

## Part 4: a container image

### The Dockerfile

A **Dockerfile** is the recipe for a container **image**, the packaged file system from which containers are started. Go suits a **multi-stage build**: one stage has the full toolchain and compiles; the final stage contains the binary and almost nothing else.

```dockerfile
# ---- stage 1: build ----
FROM golang:1.25 AS build
WORKDIR /src

# Download dependencies first. This layer is cached until go.mod or go.sum changes.
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /out/server ./cmd/server

# ---- stage 2: run ----
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/server /server
EXPOSE 8080
USER nonroot:nonroot
ENTRYPOINT ["/server"]
```

Line by line:

- `FROM golang:1.25 AS build` starts from an image that contains the Go toolchain and names this stage `build`.
- Copying `go.mod` and `go.sum` and downloading modules **before** copying the source lets Docker reuse that step when only your code changes, which makes rebuilds fast.
- `CGO_ENABLED=0` produces a **static binary** with no dependencies on system libraries, which is what allows the tiny final image. The other flags are from the tooling lesson.
- The second `FROM` starts a fresh image. `distroless/static` contains no shell, no package manager and no compiler: only what a static binary needs (certificates for HTTPS, time-zone data, a user database). Fewer contents mean fewer things an attacker can use and a smaller download.
- `COPY --from=build` takes only the compiled binary from the first stage.
- `USER nonroot` runs the service as an unprivileged user.
- `ENTRYPOINT ["/server"]` in this bracketed form runs the binary directly as the container's main process, so it receives `SIGTERM` itself and the graceful shutdown you wrote takes effect. (The form `ENTRYPOINT /server` wraps it in a shell that may not forward the signal.)

The result is typically 10 to 20 megabytes; an image with the Go toolchain is close to a gigabyte.

Add a `.dockerignore` file listing `.git`, local binaries and secrets, so they are not sent into the build.

### Running the service with its database

**Docker Compose** describes several containers that belong together:

```yaml
services:
  db:
    image: postgres:17
    environment:
      POSTGRES_USER: tasks
      POSTGRES_PASSWORD: tasks
      POSTGRES_DB: tasks
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tasks"]
      interval: 2s
      timeout: 2s
      retries: 15

  api:
    build: .
    environment:
      DATABASE_URL: postgres://tasks:tasks@db:5432/tasks?sslmode=disable
      HTTP_ADDR: ":8080"
    ports:
      - "8080:8080"
    depends_on:
      db:
        condition: service_healthy
```

```text
$ docker compose up --build
$ curl -X POST localhost:8080/tasks -d '{"title":"ship it"}'
{"id":1,"title":"ship it","done":false}
$ docker compose stop api       # sends SIGTERM: watch the "server stopped cleanly" log line
```

The host name `db` in the URL is the service name; Compose gives the containers a private network on which they find each other by name. `depends_on` with `service_healthy` waits until Postgres accepts connections before starting the API. The configuration reaches the Go program as environment variables, exactly as `loadConfig` expects.

## Pitfalls

> [!WARNING]
> Building SQL with string concatenation or `fmt.Sprintf` from user input is a security hole (SQL injection). Always pass values as placeholder arguments (`$1`, `$2`).

- **A new `sql.Open` per request**, or closing the pool after each query. Create one pool for the process.
- **Forgetting `rows.Close()` or `rows.Err()`**; leaked connections make the service hang under load.
- **No `SetMaxOpenConns`**, overwhelming the database during traffic spikes.
- **Queries without a context**, which keep running after the client has gone.
- **Letting `sql.ErrNoRows` escape** to the HTTP layer, coupling it to the database.
- **Using `db` instead of `tx` inside a transaction**: that statement runs outside it.
- **`os.Getenv` scattered through the code**; settings validated on first use instead of at start-up.
- **Secrets in the repository, the image or the logs.**
- **`log.Fatal` or `os.Exit` after resources are open**: deferred clean-ups are skipped.
- **Passing the already-cancelled signal context to `srv.Shutdown`**: it gives up immediately.
- **Closing the database before the server has drained.**
- **A shell-form `ENTRYPOINT`** that swallows `SIGTERM`; a final image that still contains the toolchain; running as root.

> [!TIP]
> Test the shutdown path by hand once: start the service, begin a request to an endpoint that sleeps a few seconds, press Ctrl+C, and confirm the request completes and the log shows a clean stop. Code that has never been exercised tends not to work on the day it is needed.

> [!INTERVIEW]
> **"How do you shut a Go HTTP server down gracefully?"** Create a context with `signal.NotifyContext` for `SIGINT`/`SIGTERM`; run `ListenAndServe` in a goroutine; when the context is cancelled call `srv.Shutdown` with a fresh timeout context, which stops accepting connections and waits for active requests; afterwards close dependencies such as the database pool; treat `http.ErrServerClosed` as normal. **"What is `*sql.DB`?"** A concurrency-safe connection pool, created once; tune `SetMaxOpenConns`/`SetMaxIdleConns`/`SetConnMaxLifetime`, use the `Context` methods, close `rows`, check `rows.Err`, map `sql.ErrNoRows` to a domain error, and use placeholders to prevent SQL injection. **"What does your Dockerfile look like?"** Multi-stage: build with the Go image and `CGO_ENABLED=0`, copy the static binary into a distroless or scratch image, run as non-root with an exec-form entrypoint.

## Cheat sheet

| Task | Code or command |
|---|---|
| Register the driver | `import _ "github.com/jackc/pgx/v5/stdlib"` |
| Open the pool | `db, err := sql.Open("pgx", url)`; `db.PingContext(ctx)` |
| Pool limits | `db.SetMaxOpenConns(n)`, `SetMaxIdleConns`, `SetConnMaxLifetime` |
| One row | `db.QueryRowContext(ctx, q, args...).Scan(&a, &b)` |
| Many rows | `rows, err := db.QueryContext(...)`; `defer rows.Close()`; `for rows.Next() { rows.Scan(...) }`; `rows.Err()` |
| No rows | `errors.Is(err, sql.ErrNoRows)` → your `ErrNotFound` |
| Write | `res, err := db.ExecContext(ctx, q, args...)`; `res.RowsAffected()` |
| Placeholders | `$1, $2` (Postgres), `?` (MySQL, SQLite) |
| Transaction | `tx, _ := db.BeginTx(ctx, nil)`; `defer tx.Rollback()`; ...; `tx.Commit()` |
| Read config | `os.Getenv("NAME")`, once, into a validated struct |
| Signal context | `ctx, stop := signal.NotifyContext(ctx, os.Interrupt, syscall.SIGTERM)` |
| Graceful stop | `srv.Shutdown(timeoutCtx)` |
| Static binary | `CGO_ENABLED=0 go build -trimpath -ldflags="-s -w"` |
| Image | multi-stage Dockerfile; final stage distroless or scratch, non-root |
| Run locally | `docker compose up --build` |

## Summary

- `database/sql` plus a driver gives a **connection pool** (`*sql.DB`): create it once, limit it, ping at start-up.
- Use `QueryRowContext`, `QueryContext` and `ExecContext` with the request's context; scan into variables; close rows and check `rows.Err()`; translate `sql.ErrNoRows` into a domain error.
- **Placeholders** keep values separate from SQL text and prevent SQL injection. **Transactions** make several statements succeed or fail together.
- Load **configuration** from the environment once, into a typed, validated struct; fail fast; keep secrets out of code and logs.
- **Graceful shutdown**: turn signals into context cancellation, call `srv.Shutdown` with a timeout, then release resources in reverse order.
- A **multi-stage Dockerfile** builds a static binary and ships it in a minimal, non-root image; Compose runs the service next to its database.

## Glossary

- **Commit / rollback**: making a transaction's changes permanent / discarding them.
- **Connection pool**: a set of reusable open connections to a database.
- **Container / image**: an isolated running process with its packaged file system / the package it starts from.
- **Driver**: a package that implements a specific database's protocol for `database/sql`.
- **Environment variable**: a named string passed to a process by its environment.
- **Graceful shutdown**: stopping after finishing in-progress work.
- **Liveness / readiness probe**: health checks for "is it running" / "can it take traffic".
- **Migration**: a versioned change to a database schema.
- **Multi-stage build**: a Dockerfile with separate build and run stages.
- **Placeholder**: a marker such as `$1` in SQL, filled by a separately supplied value.
- **Signal**: an operating-system notification to a process, such as `SIGTERM`.
- **SQL injection**: an attack that smuggles SQL into a query through unsanitised input.
- **Transaction**: a group of statements that take effect together or not at all.

```quiz
[
  {"q": "What is a `*sql.DB` value?",
   "options": ["A single open connection that must be locked before use", "A pool of connections, safe for concurrent use, created once per program", "A prepared statement", "A transaction"],
   "answer": 1,
   "explain": "`sql.DB` manages a pool: it opens, lends out and reuses connections. Create it at start-up and share it."},
  {"q": "A handler runs `rows, _ := db.QueryContext(ctx, q)`, loops over the rows and returns without calling `rows.Close()` when an error occurs mid-loop. What is the long-term effect?",
   "options": ["None; the garbage collector closes it immediately", "Connections stay checked out; the pool is exhausted and requests hang", "The database is corrupted", "The query is repeated"],
   "answer": 1,
   "explain": "Open rows hold a connection. Always `defer rows.Close()` right after the error check."},
  {"q": "Which query is safe from SQL injection?",
   "options": ["`db.QueryContext(ctx, \"SELECT * FROM tasks WHERE title = '\" + title + \"'\")`", "`db.QueryContext(ctx, fmt.Sprintf(\"SELECT * FROM tasks WHERE title = '%s'\", title))`", "`db.QueryContext(ctx, \"SELECT * FROM tasks WHERE title = $1\", title)`", "All of them"],
   "answer": 2,
   "explain": "With a placeholder the value is sent separately from the SQL text and is never interpreted as SQL. Concatenation and Sprintf both splice user input into the statement."},
  {"q": "`db.QueryRowContext(ctx, \"SELECT title FROM tasks WHERE id = $1\", 99).Scan(&title)` finds no row. What does `Scan` return?",
   "options": ["nil, with title empty", "`sql.ErrNoRows`", "It panics", "`io.EOF`"],
   "answer": 1,
   "explain": "The single-row form reports 'nothing found' as the sentinel `sql.ErrNoRows`, which the store should translate into its own not-found error."},
  {"q": "In a transaction, why is `defer tx.Rollback()` written immediately after `BeginTx`?",
   "options": ["It commits the transaction", "So every early return undoes the changes; after a successful Commit the deferred Rollback does nothing", "It speeds up the queries", "It is required syntax"],
   "answer": 1,
   "explain": "Rollback after Commit is a harmless no-op, so the single defer covers all error paths."},
  {"q": "What does `srv.Shutdown(ctx)` do?",
   "options": ["Kills all connections immediately", "Stops accepting new connections and waits for active requests to finish, until ctx expires", "Restarts the server", "Closes the database"],
   "answer": 1,
   "explain": "Shutdown is the graceful path. `srv.Close()` is the abrupt one. The context bounds how long to wait."},
  {"q": "Why is `CGO_ENABLED=0` used when building for a distroless or scratch image?",
   "options": ["It enables compiler optimisations", "It yields a static binary that needs no system C libraries, which such images do not contain", "It turns off the garbage collector", "It is needed for HTTP/2"],
   "answer": 1,
   "explain": "Minimal images lack the shared libraries a dynamically linked binary expects. A pure-Go static binary runs anywhere."},
  {"q": "Where should a service read its database password from?",
   "options": ["A constant in the source code", "A file committed to the repository", "An environment variable or secrets manager, loaded and validated at start-up", "The request headers"],
   "answer": 2,
   "explain": "Configuration, and secrets above all, come from the environment so that the same code runs everywhere and credentials never enter version control."}
]
```

> **Source:** original material for this guide (not from the book), building on Bodner, *Learning Go* 2e, ch. 11, 13 and 14 for the underlying features. Official references: https://pkg.go.dev/database/sql, https://go.dev/doc/database/, https://pkg.go.dev/github.com/jackc/pgx/v5, https://pkg.go.dev/net/http#Server.Shutdown, https://pkg.go.dev/os/signal#NotifyContext, https://docs.docker.com/build/building/multi-stage/, https://12factor.net/config
