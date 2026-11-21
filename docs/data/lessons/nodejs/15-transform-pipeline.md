# Duplex, transform and pipeline

## In plain words

In a bottling plant, bottles travel on a conveyor through stations: one washes, one fills, one caps, one labels. Each station takes bottles in on one side and puts them out on the other. A station does not know what comes before or after it, so stations can be added, removed or reordered. And if the labelling station jams, the belt stops feeding it, right back to the start of the line, so bottles do not pile up on the floor.

In Node the stations are **Transform** streams: they receive chunks, change them, and pass results on. The conveyor that connects them and stops the whole line on trouble is the `pipeline` function. Together they let you build data-processing programs out of small, reusable parts that handle input of any size.

Why it matters for a job: compressing a response, parsing an uploaded CSV file row by row, encrypting a backup, converting a database export: all of these are written as pipelines of transforms. Knowing why `pipeline` replaced the older `pipe` for error handling is a common interview check on practical stream experience.

> **Before this lesson:** read [Why streams: readable, writable and backpressure](#/lesson/nodejs/streams-readable-writable). You need generators (`function*` and `yield`) at a basic level; [Async functions and generators](#/lesson/javascript/async-await-generators) introduces them, and a later lesson in this track returns to them.

## Duplex streams

A **Duplex** stream is readable and writable at once, with the two sides independent of each other. Think of a telephone: what you say and what you hear travel on separate channels. The standard example is a network socket: you write requests into it and read responses out of it, and there is no fixed relationship between a chunk written and a chunk read.

```javascript
import net from "node:net";

const socket = net.connect(80, "example.com");          // a Duplex
socket.write("GET / HTTP/1.0\r\nHost: example.com\r\n\r\n");   // writable side
for await (const chunk of socket) {                            // readable side
  console.log(chunk.toString().split("\r\n")[0]);              // HTTP/1.0 200 OK
  break;
}
```

A Duplex has all the methods and events of both kinds, and separate buffers and high-water marks for each side.

## Transform streams

A **Transform** is a Duplex in which the readable side is *computed from* the writable side. Data goes in, something is done to it, and the result comes out. Compression, encryption, parsing and filtering are transforms.

To create one you supply up to two functions:

- `transform(chunk, encoding, callback)`: called once per incoming chunk. Call `this.push(result)` zero, one or many times to emit output, then `callback()` to say this chunk is finished. Passing an error to the callback fails the stream.
- `flush(callback)`: called once after the last input chunk and before the stream ends. This is the place to emit anything you were holding back.

### The simplest transform

```javascript
import { Transform } from "node:stream";

const upperCase = new Transform({
  transform(chunk, encoding, callback) {
    callback(null, chunk.toString().toUpperCase());     // shorthand for push + callback
  },
});

process.stdin.pipe(upperCase).pipe(process.stdout);
```

```text
$ echo "hello streams" | node upper.js
HELLO STREAMS
```

`callback(null, data)` is a shortcut for "push this, then signal done". The program reads standard input, upper-cases whatever passes through, and writes to standard output, for input of any length.

### A transform that needs memory: splitting into lines

The upper-case transform treats each chunk independently. Most real transforms cannot, because a chunk boundary can fall anywhere. To produce whole lines we must keep the unfinished tail of each chunk and glue it to the front of the next one.

```javascript
import { Transform } from "node:stream";

class LineSplitter extends Transform {
  constructor() {
    super({ readableObjectMode: true });     // bytes in, one string per line out
    this.tail = "";
  }
  _transform(chunk, encoding, callback) {
    const pieces = (this.tail + chunk.toString()).split("\n");
    this.tail = pieces.pop();                // last piece may be an unfinished line
    for (const line of pieces) this.push(line);
    callback();
  }
  _flush(callback) {
    if (this.tail !== "") this.push(this.tail);   // the final line had no newline
    callback();
  }
}
```

- When extending the class, the methods carry a leading underscore (`_transform`, `_flush`); with the constructor-options form they do not. Both styles are equivalent.
- `this.tail` is the state carried between chunks.
- One input chunk may produce no output at all (a chunk with no newline), or many lines.
- `_flush` is essential: without it the last line of a file that does not end with a newline would be lost.
- `readableObjectMode: true` makes the output side an object stream, so each line stays a separate chunk and is not merged with its neighbours.

### Filtering and aggregating

Two shapes of transform occur constantly in data processing.

- A **filter** pushes a chunk only if it passes a test; otherwise it calls `callback()` without pushing.
- An **aggregator** (or *reducer*) pushes nothing while data flows, accumulates a result, and emits it once in `flush`.

```javascript
const onlyErrors = new Transform({
  objectMode: true,
  transform(line, encoding, callback) {
    if (line.includes(" 500 ")) this.push(line);    // keep
    callback();                                     // or drop silently
  },
});

class CountPerPath extends Transform {
  constructor() { super({ objectMode: true }); this.counts = new Map(); }
  _transform(line, encoding, callback) {
    const path = line.split(" ")[1];
    this.counts.set(path, (this.counts.get(path) ?? 0) + 1);
    callback();                                     // nothing pushed yet
  }
  _flush(callback) {
    this.push(JSON.stringify(Object.fromEntries(this.counts)) + "\n");
    callback();
  }
}
```

Chained after the line splitter, these answer "which paths produced server errors, and how often?" for a log of any size, holding in memory only the current line and the map of counters.

## Connecting streams: `pipe`

`readable.pipe(writable)` connects a source to a destination. It listens for data, writes it to the destination, pauses the source when `write` returns `false`, resumes on `"drain"`, and calls `end()` on the destination when the source ends. In other words, it implements the backpressure loop from the last lesson.

`pipe` returns the **destination**, so calls can be chained when the destination is itself readable (a Duplex or Transform):

```javascript
source.pipe(transformA).pipe(transformB).pipe(destination);
```

```mermaid
flowchart LR
  S["Readable: file"] -- chunks --> A["Transform: split lines"]
  A -- lines --> B["Transform: filter"]
  B -- lines --> C["Transform: count"]
  C -- result --> D["Writable: stdout"]
  D -. "backpressure: slow down" .-> C
  C -. backpressure .-> B
  B -. backpressure .-> A
  A -. backpressure .-> S
```

Data moves left to right; the "slow down" signal moves right to left, one stage at a time, until it reaches the source.

### The weakness of `pipe`: errors

`pipe` has two defects that matter in production.

1. **Errors are not forwarded.** Each stream in a chain emits its own `"error"`. A handler on the last stream sees only that stream's errors. An unhandled error on any of the others crashes the process.
2. **Nothing is cleaned up.** When one stream fails, the others are left open: file descriptors stay allocated, and a destination waits forever for an `end` that will not come.

Handling this properly with `pipe` means attaching an error handler to every stream and manually destroying all the others in each handler. Nobody gets that right twice in a row.

## `pipeline`: the right way to connect streams

`pipeline` from `node:stream/promises` takes the streams in order, connects them with backpressure, and returns a promise that fulfils when the whole chain has finished. If **any** stream fails, it destroys **all** of them and rejects the promise with the error.

```javascript
import { createReadStream, createWriteStream } from "node:fs";
import { createGzip } from "node:zlib";
import { pipeline } from "node:stream/promises";

try {
  await pipeline(
    createReadStream("access.log"),
    createGzip(),                               // a Transform from the core library
    createWriteStream("access.log.gz"),
  );
  console.log("compressed");
} catch (error) {
  console.error("pipeline failed:", error.message);
}
```

```text
$ node compress.js
compressed
$ node compress.js        # after deleting access.log
pipeline failed: ENOENT: no such file or directory, open 'access.log'
```

One `try`/`catch` covers the reader, the compressor and the writer. A callback version, `pipeline(a, b, c, (err) => ...)`, lives in `node:stream`.

> [!WARNING]
> Prefer `pipeline` to `.pipe()` in all new code. The only thing `pipe` does better is fit on one line in a tutorial. In a server, a client that disconnects mid-download is an everyday event, and with bare `pipe` each one can leak an open file.

### Transforms as async generator functions

`pipeline` accepts more than stream objects. Any stage after the first may be an **async generator function**: a function declared with `async function*` that receives the previous stage as an async iterable and `yield`s its output. This is the most pleasant way to write a transform today.

```javascript
import { pipeline } from "node:stream/promises";
import { createReadStream } from "node:fs";

async function* splitLines(source) {
  let tail = "";
  for await (const chunk of source) {
    const pieces = (tail + chunk).split("\n");
    tail = pieces.pop();
    yield* pieces;                              // emit each complete line
  }
  if (tail !== "") yield tail;                  // what flush() did in the class version
}

async function* serverErrorsOnly(lines) {
  for await (const line of lines) if (line.includes(" 500 ")) yield line + "\n";
}

await pipeline(
  createReadStream("access.log", "utf8"),
  splitLines,
  serverErrorsOnly,
  process.stdout,
);
```

Compare `splitLines` with the `LineSplitter` class: the state is a local variable, the per-chunk work is the loop body, and the flush is the code after the loop. Backpressure still works, because a generator runs only when its consumer asks for the next value.

### A pipeline you can run

Node's stream module is not available in this page, but async generators are part of the language. The model below wires three generator stages together by hand and logs when each stage works, so you can watch items flow through **one at a time** and the stages overlap.

```js-run
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function* readChunks() {                      // source: awkward chunk boundaries on purpose
  const chunks = ["GET /home 200\nGET /ca", "rt 500\nPOST /pay 500\nGET /ho", "me 200\nGET /cart 500"];
  for (const chunk of chunks) {
    await sleep(10);
    console.log(`[source] produced a chunk of ${chunk.length} characters`);
    yield chunk;
  }
}

async function* splitLines(source) {
  let tail = "";
  for await (const chunk of source) {
    const pieces = (tail + chunk).split("\n");
    tail = pieces.pop();
    yield* pieces;
  }
  if (tail !== "") yield tail;
}

async function* serverErrorsOnly(lines) {
  for await (const line of lines) {
    if (line.endsWith(" 500")) { console.log(`  [filter] kept    "${line}"`); yield line; }
    else console.log(`  [filter] dropped "${line}"`);
  }
}

async function countPerPath(lines) {                // sink: aggregates everything into one result
  const counts = {};
  for await (const line of lines) {
    const path = line.split(" ")[1];
    counts[path] = (counts[path] ?? 0) + 1;
  }
  return counts;
}

const result = await countPerPath(serverErrorsOnly(splitLines(readChunks())));
console.log("errors per path:", result);
```

Read the output order. The first chunk yields one complete line, which the filter handles **before the source produces its second chunk**. Nothing is read ahead: each stage pulls from the one before it only when it is ready, which is backpressure in its purest form. The line `GET /cart 500`, cut across two chunks, is reassembled by the `tail` logic, and the last line, which has no trailing newline, is emitted by the code after the loop.

The problem [A transform pipeline with backpressure](#/problem/node-stream-pipeline) models the buffer accounting of such a pipeline precisely.

## PassThrough: a pipe section that does nothing

`PassThrough` is a Transform that outputs exactly what it receives. That sounds useless and has three practical uses.

**Observation.** Insert one in a pipeline and listen to its `data` events to measure what flows through, without disturbing it:

```javascript
import { PassThrough } from "node:stream";

let bytes = 0;
const meter = new PassThrough();
meter.on("data", (chunk) => { bytes += chunk.length; });

await pipeline(createReadStream("access.log"), createGzip(), meter, createWriteStream("access.log.gz"));
console.log("compressed size:", bytes, "bytes");
```

**A placeholder for data that will arrive later.** Some functions want a readable stream immediately, while your data source is not ready yet (it must first be looked up, or will be chosen later). Hand over a `PassThrough` now and pipe the real source into it when it exists.

**Postponing expensive set-up.** Creating thousands of file streams up front opens thousands of files at once. A stand-in that creates the real stream only when someone starts reading from it avoids that; small packages such as `lazystream` do this.

## Useful helpers

```javascript
import { finished } from "node:stream/promises";
import { compose, Readable } from "node:stream";

await finished(stream);                         // wait until a stream is done or has failed

const compressAndEncrypt = compose(createGzip(), createCipher());   // several transforms as one
```

`compose` builds one Duplex out of several streams, which the next lesson uses to package pipelines as reusable components. Recent Node versions also give Readables array-like helpers such as `.map()`, `.filter()` and `.toArray()`; they are convenient, and still marked experimental at the time of writing.

> [!TIP]
> Design transforms the way you would design small command-line tools: one job, no knowledge of neighbours, and a decision about mode (bytes or objects) on each side. A parser is bytes-in, objects-out; a serialiser is the reverse; filters and mappers in the middle are objects on both sides.

> [!INTERVIEW]
> **"What is the difference between `pipe` and `pipeline`?"** "Both connect streams and handle backpressure. `pipe` does not propagate errors and does not destroy the other streams when one fails, so it leaks resources unless you add handlers to every stream. `pipeline` takes the whole chain, destroys every stream on error or premature close, and reports completion or failure once, through a callback or a promise. It also accepts async generator functions as stages." Follow-up: **"What is `flush` for in a Transform?"** To emit data held back until the end, such as the last partial line or an aggregate.

## Pitfalls

- **Forgetting to call `callback()`** in `transform`: the stream stalls silently after the first chunk.
- **Calling `callback()` twice**, or pushing after it for the same chunk.
- **No `flush`** in a transform that keeps state: the final piece of data disappears.
- **Mode mismatch**: pushing objects from a byte-mode stream throws `ERR_INVALID_ARG_TYPE`; set `objectMode`, `readableObjectMode` or `writableObjectMode`.
- **Chaining `.pipe()` and handling errors only on the last stream.**
- **Reusing a stream instance in two pipelines.** A stream is consumed once; create a new one each time.
- **An aggregator over unbounded distinct keys** (a counter per IP address, say) is buffering in disguise: its map grows with the input.

## Cheat sheet

| Goal | Code |
|---|---|
| Transform, inline | `new Transform({ transform(chunk, enc, cb) { cb(null, out); }, flush(cb) { cb(); } })` |
| Transform, class | `class X extends Transform { _transform(c, e, cb) {} _flush(cb) {} }` |
| Emit several outputs | `this.push(a); this.push(b); cb();` |
| Drop a chunk (filter) | `cb();` without pushing |
| Emit at the end (aggregate) | push inside `flush` |
| Connect with error handling | `await pipeline(source, t1, t2, dest)` from `node:stream/promises` |
| Generator as a stage | `async function* stage(source) { for await (const x of source) yield f(x); }` |
| Do-nothing stage | `new PassThrough()` |
| Several transforms as one | `compose(t1, t2)` |
| Wait for a stream to finish | `await finished(stream)` |
| Built-in transforms | `zlib.createGzip()`, `zlib.createGunzip()`, `crypto.createCipheriv(...)` |

## Summary

- A Duplex has independent readable and writable sides; a Transform is a Duplex whose output is derived from its input.
- `transform` handles each chunk and may push any number of results; `flush` emits what was held back.
- Stateful transforms carry leftovers between chunks; filters drop chunks; aggregators emit once at the end.
- `pipe` connects streams with backpressure but neither forwards errors nor cleans up. `pipeline` does both and returns a promise.
- Async generator functions are the simplest way to write pipeline stages, and they are lazy: each stage pulls only when ready.
- `PassThrough` serves for observation and as a placeholder.

## Glossary

- **Duplex stream**: a stream that is both readable and writable, with independent sides.
- **Transform stream**: a Duplex whose output is computed from its input.
- **`transform` / `flush`**: the per-chunk function / the end-of-input function of a Transform.
- **Stateful transform**: one that remembers something between chunks.
- **Filter**: a transform that passes only some chunks.
- **Aggregator (reducer)**: a transform that combines all input into one output.
- **`pipe`**: the method connecting a Readable to a Writable.
- **`pipeline`**: the function that connects a chain of streams with error handling and clean-up.
- **Destroy**: to close a stream and release its resources immediately.
- **Async generator function**: an `async function*`; it produces values over time with `yield`.
- **`PassThrough`**: a Transform that forwards data unchanged.
- **Lazy**: doing work only when the result is requested.

```quiz
[
  {"q": "What distinguishes a Transform from a general Duplex?", "options": ["A Transform is only writable", "In a Transform the readable output is computed from the written input; in a Duplex the two sides are independent", "A Duplex cannot be piped", "A Transform has no buffers"], "answer": 1,
   "explain": "A socket is a Duplex: what you write and what you read are unrelated. Gzip is a Transform: output derives from input."},
  {"q": "A line-splitting Transform has no flush function. The input is \"a\\nb\\nc\" (no final newline). What comes out?", "options": ["a, b, c", "a, b", "a", "Nothing"], "answer": 1,
   "explain": "The last line stays in the leftover buffer; only flush can emit it when the input ends."},
  {"q": "In `a.pipe(b).pipe(c)`, stream b emits 'error' and only c has an error listener. What happens?", "options": ["c's listener receives it", "The error is unhandled and can crash the process; a and c are not destroyed", "The chain restarts", "The error is ignored safely"], "answer": 1,
   "explain": "pipe does not forward errors or clean up. pipeline does both."},
  {"q": "What does `await pipeline(src, gzip, dest)` do when gzip fails halfway?", "options": ["It leaves src and dest open", "It destroys all three streams and rejects with the error", "It retries from the beginning", "It resolves with a partial file"], "answer": 1,
   "explain": "pipeline tears the whole chain down and reports the failure once."},
  {"q": "How does a filter Transform drop a chunk?", "options": ["It pushes null", "It calls the callback without pushing anything", "It throws an error", "It calls this.end()"], "answer": 1,
   "explain": "Pushing null would end the stream. Calling the callback alone says: done with this chunk, no output."},
  {"q": "In the generator pipeline model, when does the source produce its second chunk?", "options": ["Immediately, before any line is processed", "Only when the downstream stages have consumed what the first chunk produced and ask for more", "After a fixed timeout", "Never"], "answer": 1,
   "explain": "Generators are pull-based: a stage runs only when its consumer requests the next value."},
  {"q": "In what order do these log?\n\n`async function* gen() { console.log('G1'); yield 1; console.log('G2'); } const it = gen(); console.log('A'); for await (const x of it) console.log('X' + x); console.log('B');`", "options": ["G1, A, X1, G2, B", "A, G1, X1, G2, B", "A, G1, G2, X1, B", "A, X1, G1, G2, B"], "answer": 1,
   "explain": "Calling gen() runs nothing. The loop's first request runs the body to the first yield (G1), the loop body logs X1, the next request logs G2 and finishes."},
  {"q": "Which is a legitimate use of PassThrough?", "options": ["Speeding up a pipeline", "Counting the bytes that flow through a pipeline without changing them", "Converting bytes to objects", "Encrypting data"], "answer": 1,
   "explain": "A PassThrough forwards data unchanged, so it is a convenient tap for observation or a placeholder."}
]
```

> **Source:** Casciaro & Mammino, *Node.js Design Patterns* 3e, ch. 6 (topics only; wording and examples are original). Documentation: https://nodejs.org/docs/latest/api/stream.html#streampipelinesource-transforms-destination-options, https://nodejs.org/docs/latest/api/stream.html#class-streamtransform, https://nodejs.org/docs/latest/api/zlib.html
