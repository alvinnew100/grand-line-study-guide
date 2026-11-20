_RETRYABLE = ["timeout", 502, 503, 504]

PROBLEMS = [
dict(
    id="spring-retry-backoff",
    title="Retry with exponential backoff",
    difficulty="Medium",
    pattern="REST clients",
    entry="retry_plan",
    description=r"""
A client calling a remote REST service may retry failures that are likely to be temporary. A sound policy limits
the number of retries, waits longer before each one (*exponential backoff*) and never repeats a request that
cannot succeed.

`retry_plan(outcomes, max_retries, first_delay, multiplier, max_delay, retryable)`:

- `outcomes` — what each successive attempt would produce: an HTTP status code (an `int`) or the string
  `"timeout"`. Attempt 1 gets `outcomes[0]`, attempt 2 gets `outcomes[1]`, and so on. If the list is shorter
  than the number of attempts made, the **last** entry repeats.
- `max_retries` — how many retries are allowed after the first attempt (so at most `max_retries + 1` attempts).
- `first_delay`, `multiplier`, `max_delay` — the wait before retry number *k* (counting from 0) is
  `min(first_delay * multiplier**k, max_delay)` milliseconds. All are integers.
- `retryable` — the list of outcomes that may be retried (status codes and possibly `"timeout"`).

Procedure: make an attempt. A status below 400 is a **success**: stop. An outcome that is not in `retryable` is
a definite **failure**: stop without waiting. A retryable outcome with retries left: wait, then try again.
A retryable outcome with no retries left: stop, the retries are **exhausted**.

Return a dict:

- `"result"` — `"success"`, `"failed"` or `"exhausted"`,
- `"attempts"` — number of attempts made,
- `"last"` — the outcome of the final attempt,
- `"waits"` — the list of waits in milliseconds, in order,
- `"total_wait"` — their sum.

**Example:** `retry_plan([503, 503, 200], 3, 200, 2, 5000, [503])` →
`{"result": "success", "attempts": 3, "last": 200, "waits": [200, 400], "total_wait": 600}`.
""",
    starter='''def retry_plan(outcomes: list, max_retries: int, first_delay: int, multiplier: int,
               max_delay: int, retryable: list) -> dict:
    pass
''',
    solution='''def retry_plan(outcomes, max_retries, first_delay, multiplier, max_delay, retryable):
    waits = []
    attempt = 0
    while True:
        outcome = outcomes[min(attempt, len(outcomes) - 1)]
        attempt += 1
        if isinstance(outcome, int) and outcome < 400:
            result = "success"
            break
        if outcome not in retryable:
            result = "failed"
            break
        if attempt > max_retries:
            result = "exhausted"
            break
        waits.append(min(first_delay * multiplier ** len(waits), max_delay))
    return {"result": result, "attempts": attempt, "last": outcome, "waits": waits, "total_wait": sum(waits)}
''',
    tests=[
        [[503, 503, 200], 3, 200, 2, 5000, [503]],
        [[200], 3, 200, 2, 5000, _RETRYABLE],
        [[503], 3, 200, 2, 5000, _RETRYABLE],
        [[400], 3, 200, 2, 5000, _RETRYABLE],
        [["timeout", 404], 5, 100, 3, 10000, _RETRYABLE],
        [["timeout", "timeout", 201], 5, 100, 3, 10000, _RETRYABLE],
        [[503], 6, 500, 2, 3000, _RETRYABLE],
        [[503], 0, 200, 2, 5000, _RETRYABLE],
        [[500, 200], 3, 200, 2, 5000, _RETRYABLE],
        [[502, 504, "timeout", 503, 204], 4, 50, 2, 150, _RETRYABLE],
        [[502, 504, "timeout", 503, 204], 3, 50, 2, 150, _RETRYABLE],
        [["timeout"], 2, 1000, 1, 5000, [503]],
        [[503, 302], 2, 10, 10, 1000, _RETRYABLE],
        [[429], 4, 100, 2, 100000, [429]],
    ],
    examples=2,
    wrong_solutions=[
        '''def retry_plan(outcomes, max_retries, first_delay, multiplier, max_delay, retryable):
    waits, attempt = [], 0
    while True:
        outcome = outcomes[min(attempt, len(outcomes) - 1)]
        attempt += 1
        if isinstance(outcome, int) and outcome < 400:
            result = "success"; break
        if outcome not in retryable:
            result = "failed"; break
        if attempt > max_retries:
            result = "exhausted"; break
        waits.append(first_delay * multiplier ** len(waits))
    return {"result": result, "attempts": attempt, "last": outcome, "waits": waits, "total_wait": sum(waits)}
''',
        '''def retry_plan(outcomes, max_retries, first_delay, multiplier, max_delay, retryable):
    waits, attempt = [], 0
    while True:
        outcome = outcomes[min(attempt, len(outcomes) - 1)]
        attempt += 1
        if isinstance(outcome, int) and outcome < 400:
            result = "success"; break
        if attempt > max_retries:
            result = "exhausted"; break
        waits.append(min(first_delay * multiplier ** len(waits), max_delay))
    return {"result": result, "attempts": attempt, "last": outcome, "waits": waits, "total_wait": sum(waits)}
''',
        '''def retry_plan(outcomes, max_retries, first_delay, multiplier, max_delay, retryable):
    waits, attempt = [], 0
    while True:
        outcome = outcomes[min(attempt, len(outcomes) - 1)]
        attempt += 1
        if isinstance(outcome, int) and outcome < 400:
            result = "success"; break
        if outcome not in retryable:
            result = "failed"; break
        if attempt >= max_retries:
            result = "exhausted"; break
        waits.append(min(first_delay * multiplier ** len(waits), max_delay))
    return {"result": result, "attempts": attempt, "last": outcome, "waits": waits, "total_wait": sum(waits)}
''',
    ],
    guide=dict(
        prereqs="Lesson: *WebClient, timeouts and resilient calls*. Loops and `min`.",
        intuition="Three questions after every attempt, in this order: did it work? could trying again help? am I "
                  "still allowed to try? Only when the answers are no, yes, yes does the client wait, and each "
                  "wait is longer than the previous one up to a ceiling.",
        hints=[
            "Count attempts from 1 and keep the list of waits; the number of waits so far is the exponent for the next one.",
            "Check 'not retryable' before 'no retries left': a 400 is `failed` even when retries remain, and never `exhausted`.",
            "The condition for giving up is `attempt > max_retries` after the attempt: with `max_retries = 0` exactly one attempt is made.",
        ],
        brute_force="A fixed number of immediate retries in a `for` loop ignores which errors are worth retrying and "
                    "hammers a struggling service; it also makes the wait schedule impossible to report.",
        approach=r"""
Loop: read the outcome for this attempt (repeating the last entry when the list runs out), then apply the three
checks. Append `min(first_delay * multiplier**k, max_delay)` where `k` is the number of waits made so far.

**Dry run** `outcomes = [503]`, `max_retries = 6`, `first_delay = 500`, `multiplier = 2`, `max_delay = 3000`:
waits are 500, 1000, 2000, then capped: 3000, 3000, 3000. Seven attempts, all 503 → `exhausted`, total wait
12 500 ms.

With `WebClient` (Reactor):

```java
Mono<ShippingQuote> quote = client.get().uri("/v1/quotes?postcode={p}", postcode)
        .retrieve()
        .bodyToMono(ShippingQuote.class)
        .timeout(Duration.ofSeconds(2))
        .retryWhen(Retry.backoff(3, Duration.ofMillis(200))          // 200, 400, 800 ms
                        .maxBackoff(Duration.ofSeconds(5))
                        .filter(e -> e instanceof TimeoutException
                                  || e instanceof WebClientResponseException.ServiceUnavailable));
```

With Spring Retry on a blocking client:

```java
@Retryable(retryFor = HttpServerErrorException.class, maxAttempts = 4,
           backoff = @Backoff(delay = 200, multiplier = 2, maxDelay = 5000))
public ShippingQuote quote(String postcode) { ... }
```

Note that `maxAttempts = 4` counts the first call too: one attempt plus three retries.
""",
        complexity="Time and space O(max_retries).",
        pitfalls="Retrying client errors such as 400 or 404, which will fail identically; forgetting the delay cap, "
                 "so waits grow without bound; confusing 'max retries' with 'max attempts' (off by one); retrying "
                 "non-idempotent requests without an idempotency key.",
        follow_up="Add jitter (a random factor on each wait) and explain why it prevents many clients from retrying at the same instant.",
    ),
),
]
