# Calling REST endpoints: RestTemplate, RestClient and OpenFeign

> **Before this lesson:** you can build REST endpoints and understand requests, responses, JSON bodies and status codes ([REST endpoints with @RestController and ResponseEntity](#/lesson/spring/spring-rest-controllers), [Request bodies, validation and error handling with @RestControllerAdvice](#/lesson/spring/spring-rest-errors-validation)).

## In plain words

Until now your application has been the restaurant: it waits for orders and serves them. Restaurants also place orders themselves, with the bakery, the fishmonger, the laundry. For that, someone in the restaurant picks up the phone and becomes a customer.

Back ends do the same. The bookshop does not process credit cards itself; it calls a payment provider's API. It may call a shipping company for rates, or another team's stock service. In those moments your application is the **client** of somebody else's REST endpoint: it builds an HTTP request, sends it, waits, and turns the JSON answer back into Java objects.

Spring offers several tools for this. Because they arrived in different years, a typical code base contains more than one, and interviewers like to ask which you would choose today. This lesson covers the three **blocking** options: `RestTemplate` (the classic), `RestClient` (its modern successor) and declarative clients (Spring Cloud OpenFeign and Spring's own HTTP interfaces), where you write only a Java interface. The non-blocking `WebClient` follows in the next lesson.

## The scenario

The bookshop takes payment through an external payment service with this contract:

```text
POST https://payments.example.com/v1/payments
Headers:  Content-Type: application/json
          X-Request-Id: <unique id chosen by the caller>
Body:     {"orderId": "o-1001", "amountCents": 2500, "currency": "EUR"}

201 Created  {"paymentId": "p-77", "status": "AUTHORISED"}
402 Payment Required  {"reason": "card declined"}

GET https://payments.example.com/v1/payments/{paymentId}
200 OK  {"paymentId": "p-77", "status": "CAPTURED"}
```

Two records mirror the JSON:

```java
// src/main/java/com/bookshop/payment/PaymentRequest.java
public record PaymentRequest(String orderId, int amountCents, String currency) { }

// src/main/java/com/bookshop/payment/PaymentResponse.java
public record PaymentResponse(String paymentId, String status) { }
```

Following [Interfaces as contracts: decoupling your classes](#/lesson/spring/spring-interfaces-contracts), the rest of the application depends on a small interface, and each tool below provides an implementation. An object that represents an external system inside your code is often called a **proxy** or **gateway** (not to be confused with AOP proxies).

```java
// src/main/java/com/bookshop/payment/PaymentGateway.java
public interface PaymentGateway {
    PaymentResponse pay(PaymentRequest request);
    PaymentResponse status(String paymentId);
}
```

```mermaid
flowchart LR
    OS[OrderService] --> PG[[PaymentGateway interface]]
    PG -.implemented by.-> RC[RestClientPaymentGateway]
    RC -->|HTTP + JSON| EXT[payments.example.com]
```

## What every HTTP client has to do

Whatever the tool, a call consists of the same steps. Seeing them once in plain code makes the three APIs easy to compare.

```python-run
import json

def fake_payment_server(method, url, headers, body):
    """Stands in for payments.example.com so the example runs offline."""
    if method == "POST" and url.endswith("/v1/payments"):
        data = json.loads(body)
        if data["amountCents"] > 100_000:
            return 402, json.dumps({"reason": "card declined"})
        return 201, json.dumps({"paymentId": "p-77", "status": "AUTHORISED"})
    if method == "GET" and "/v1/payments/" in url:
        return 200, json.dumps({"paymentId": url.rsplit("/", 1)[1], "status": "CAPTURED"})
    return 404, ""

class PaymentDeclined(Exception):
    pass

def call(method, base_url, path_template, path_variables=None, headers=None, body=None):
    url = base_url + path_template.format(**(path_variables or {}))        # 1. build the URL
    headers = dict(headers or {})
    payload = None
    if body is not None:
        payload = json.dumps(body)                                          # 2. serialise the body
        headers["Content-Type"] = "application/json"
    print(f"  --> {method} {url} {headers} {payload or ''}")
    status, response_body = fake_payment_server(method, url, headers, payload)   # 3. send and wait
    print(f"  <-- {status} {response_body}")
    if status >= 400:                                                       # 4. turn error statuses into exceptions
        raise PaymentDeclined(f"{status}: {response_body}")
    return json.loads(response_body) if response_body else None             # 5. deserialise the answer

BASE = "https://payments.example.com"
print(call("POST", BASE, "/v1/payments", headers={"X-Request-Id": "r-1"},
           body={"orderId": "o-1001", "amountCents": 2500, "currency": "EUR"}))
print(call("GET", BASE, "/v1/payments/{id}", {"id": "p-77"}))
try:
    call("POST", BASE, "/v1/payments", body={"orderId": "o-1002", "amountCents": 500_000, "currency": "EUR"})
except PaymentDeclined as problem:
    print("  exception:", problem)
```

The five numbered steps (build the URL, serialise, send and wait, check the status, deserialise) are what each Spring client automates. The word *wait* in step 3 is what **blocking** means: the calling thread does nothing else until the response arrives.

## RestTemplate: the classic

`RestTemplate` has been part of Spring since version 3. It is in *maintenance mode*: still supported and safe to use, but it receives no new features, and the Spring documentation recommends `RestClient` for new blocking code. You will meet it constantly in existing projects.

```java
// src/main/java/com/bookshop/payment/PaymentClientConfig.java
@Configuration
public class PaymentClientConfig {

    @Bean
    RestTemplate paymentRestTemplate(RestTemplateBuilder builder) {
        return builder
                .rootUri("https://payments.example.com")
                .connectTimeout(Duration.ofSeconds(2))
                .readTimeout(Duration.ofSeconds(5))
                .build();
    }
}
```

`RestTemplateBuilder` is supplied by Boot and applies Boot's defaults (message converters, metrics). The two timeouts are explained in the pitfalls; never omit them.

```java
// src/main/java/com/bookshop/payment/RestTemplatePaymentGateway.java
@Component
public class RestTemplatePaymentGateway implements PaymentGateway {

    private final RestTemplate rest;

    public RestTemplatePaymentGateway(RestTemplate paymentRestTemplate) {
        this.rest = paymentRestTemplate;
    }

    @Override
    public PaymentResponse pay(PaymentRequest request) {
        HttpHeaders headers = new HttpHeaders();                                 // (1)
        headers.add("X-Request-Id", UUID.randomUUID().toString());
        HttpEntity<PaymentRequest> entity = new HttpEntity<>(request, headers);  // (2)

        ResponseEntity<PaymentResponse> response = rest.exchange(                // (3)
                "/v1/payments", HttpMethod.POST, entity, PaymentResponse.class);
        return response.getBody();
    }

    @Override
    public PaymentResponse status(String paymentId) {
        return rest.getForObject("/v1/payments/{id}", PaymentResponse.class, paymentId);   // (4)
    }
}
```

1. `HttpHeaders` collects request headers.
2. `HttpEntity` pairs a body with headers: the request seen as an object.
3. `exchange` is the general-purpose method: URL, HTTP method, request entity, and the class to convert the response body to. It returns a `ResponseEntity`, the same type your controllers return.
4. For simple cases there are shortcuts named after the method and the result: `getForObject`, `getForEntity`, `postForObject`, `put`, `delete`. The `{id}` placeholder is filled from the trailing arguments and URL-encoded.

By default `RestTemplate` throws an exception for every 4xx and 5xx response: `HttpClientErrorException` and `HttpServerErrorException`, both subclasses of `RestClientResponseException`, which gives access to the status and body.

## RestClient: the modern blocking client

`RestClient` arrived in Spring Framework 6.1 (Spring Boot 3.2). It does the same job with a **fluent** API, meaning calls are chained so that the code reads like a sentence. It uses the same underlying HTTP libraries and message converters as `RestTemplate`.

```java
// src/main/java/com/bookshop/payment/PaymentClientConfig.java
@Configuration
public class PaymentClientConfig {

    @Bean
    RestClient paymentRestClient(RestClient.Builder builder,
                                 @Value("${payments.base-url}") String baseUrl) {
        return builder
                .baseUrl(baseUrl)
                .defaultHeader("Accept", "application/json")
                .build();
    }
}
```

Boot provides the `RestClient.Builder` bean pre-configured. The base URL comes from configuration so that tests and environments can point elsewhere:

```properties
# src/main/resources/application.properties
payments.base-url=https://payments.example.com
```

```java
// src/main/java/com/bookshop/payment/RestClientPaymentGateway.java
@Component
@Primary
public class RestClientPaymentGateway implements PaymentGateway {

    private final RestClient client;

    public RestClientPaymentGateway(RestClient paymentRestClient) {
        this.client = paymentRestClient;
    }

    @Override
    public PaymentResponse pay(PaymentRequest request) {
        return client.post()                                              // HTTP method
                .uri("/v1/payments")                                      // path, relative to the base URL
                .header("X-Request-Id", UUID.randomUUID().toString())
                .body(request)                                            // serialised to JSON
                .retrieve()                                               // send, wait for the response
                .onStatus(status -> status.value() == 402, (req, res) -> {
                    throw new PaymentDeclinedException(request.orderId());   // map a status to our exception
                })
                .body(PaymentResponse.class);                             // deserialise
    }

    @Override
    public PaymentResponse status(String paymentId) {
        return client.get()
                .uri("/v1/payments/{id}", paymentId)
                .retrieve()
                .body(PaymentResponse.class);
    }
}
```

Read `pay` from top to bottom against the five steps: `uri` (build the URL), `body(request)` (serialise), `retrieve()` (send and wait), `onStatus` (check the status), `body(PaymentResponse.class)` (deserialise). Use `.toEntity(PaymentResponse.class)` in place of the last call when you also need the status or headers. Without an `onStatus` handler, 4xx and 5xx raise `RestClientResponseException` subclasses as with `RestTemplate`.

For a JSON array use a type token, because Java erases generic types at run time and Spring cannot otherwise know the element type:

```java
List<PaymentResponse> all = client.get()
        .uri("/v1/payments?orderId={id}", orderId)
        .retrieve()
        .body(new ParameterizedTypeReference<List<PaymentResponse>>() { });
```

> [!TIP]
> Timeouts for `RestClient` and `RestTemplate` can be set once for all clients built from Boot's builders with `spring.http.client.connect-timeout=2s` and `spring.http.client.read-timeout=5s` (Boot 3.4 and later), or per client by passing a configured `ClientHttpRequestFactory` to the builder.

## Declarative clients: write the interface, not the calls

Look at the two implementations above. They contain no decisions, only translation: this method means that URL, this parameter is that path variable. Translation can be generated. With a **declarative client** you describe the remote API as a Java interface with annotations, and a library creates the implementation at start-up.

### Spring Cloud OpenFeign

**OpenFeign** is the declarative client from the Spring Cloud project. It reuses the Spring MVC annotations you already know from the server side.

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-openfeign</artifactId>
</dependency>
```

Spring Cloud has its own release train, so the build also needs the `spring-cloud-dependencies` BOM in `<dependencyManagement>`, in the version matching your Boot version.

```java
// src/main/java/com/bookshop/payment/PaymentFeignClient.java
@FeignClient(name = "payments", url = "${payments.base-url}")
public interface PaymentFeignClient {

    @PostMapping("/v1/payments")
    PaymentResponse pay(@RequestHeader("X-Request-Id") String requestId,
                        @RequestBody PaymentRequest request);

    @GetMapping("/v1/payments/{id}")
    PaymentResponse status(@PathVariable("id") String paymentId);
}
```

```java
@SpringBootApplication
@EnableFeignClients                    // scan for @FeignClient interfaces and create implementations
public class BookshopApplication { ... }
```

There is no implementing class. At start-up Feign creates a proxy object for the interface and registers it as a bean, which you inject like any other:

```java
@Component
public class FeignPaymentGateway implements PaymentGateway {

    private final PaymentFeignClient client;

    public FeignPaymentGateway(PaymentFeignClient client) { this.client = client; }

    @Override
    public PaymentResponse pay(PaymentRequest request) {
        return client.pay(UUID.randomUUID().toString(), request);
    }

    @Override
    public PaymentResponse status(String paymentId) { return client.status(paymentId); }
}
```

Error statuses raise `FeignException`; timeouts are configured under `spring.cloud.openfeign.client.config.<name>.*`.

### Spring's built-in HTTP interfaces

Since Spring Framework 6 the same idea is available without Spring Cloud, through `@HttpExchange` annotations and a `RestClient` (or `WebClient`) underneath.

```java
// src/main/java/com/bookshop/payment/PaymentApi.java
@HttpExchange("/v1/payments")
public interface PaymentApi {

    @PostExchange
    PaymentResponse pay(@RequestHeader("X-Request-Id") String requestId, @RequestBody PaymentRequest request);

    @GetExchange("/{id}")
    PaymentResponse status(@PathVariable String id);
}
```

```java
@Bean
PaymentApi paymentApi(RestClient paymentRestClient) {
    HttpServiceProxyFactory factory = HttpServiceProxyFactory
            .builderFor(RestClientAdapter.create(paymentRestClient))
            .build();
    return factory.createClient(PaymentApi.class);       // the generated implementation
}
```

OpenFeign itself is feature-complete and in maintenance; the Spring team points new projects towards HTTP interfaces. Both remain widespread.

### How a declarative client works

The mechanism is the proxy idea once more. The generated object intercepts each method call, reads the annotations of the called method, and builds the HTTP request from them.

```python-run
import json

def fake_server(method, url, headers, body):
    if method == "POST":
        return 201, json.dumps({"paymentId": "p-77", "status": "AUTHORISED"})
    return 200, json.dumps({"paymentId": url.rsplit("/", 1)[1], "status": "CAPTURED"})

def exchange(method, path):                       # our stand-in for @GetExchange / @PostMapping
    def mark(function):
        function.http = (method, path)
        return function
    return mark

class PaymentApi:                                 # the "interface": signatures and metadata only
    @exchange("POST", "/v1/payments")
    def pay(self, body): ...
    @exchange("GET", "/v1/payments/{id}")
    def status(self, id): ...

def create_client(interface, base_url):
    class GeneratedClient:
        def __getattr__(self, method_name):
            http_method, path = getattr(interface, method_name).http          # read the annotation
            def invoke(**arguments):
                body = arguments.pop("body", None)
                url = base_url + path.format(**arguments)                     # path variables
                payload = json.dumps(body) if body is not None else None      # request body
                print(f"  generated request: {http_method} {url} {payload or ''}")
                status, text = fake_server(http_method, url, {}, payload)
                return json.loads(text)
            return invoke
    return GeneratedClient()

api = create_client(PaymentApi, "https://payments.example.com")
print(api.pay(body={"orderId": "o-1001", "amountCents": 2500, "currency": "EUR"}))
print(api.status(id="p-77"))
```

`PaymentApi` contains no logic; its methods have empty bodies. `create_client` returns an object whose `__getattr__` looks up the metadata attached by the decorator and performs the five steps. Feign and `HttpServiceProxyFactory` do this with Java's dynamic proxies.

## Which one?

| | `RestTemplate` | `RestClient` | OpenFeign | HTTP interface (`@HttpExchange`) | `WebClient` |
|---|---|---|---|---|---|
| Style | template methods | fluent | declarative interface | declarative interface | fluent, reactive |
| Blocking | yes | yes | yes | depends on the adapter | no |
| Status | maintenance mode | current recommendation | maintenance, widely used | current | current |
| Extra dependency | none | none | Spring Cloud | none | `spring-boot-starter-webflux` |
| Good for | existing code | new blocking code | many endpoints, teams already on Spring Cloud | many endpoints in new code | streaming, high concurrency, reactive apps |

> [!INTERVIEW]
> "How would you call another REST service from Spring Boot today?" For a servlet (blocking) application: `RestClient`, or an `@HttpExchange` interface on top of it when the API has many operations. `RestTemplate` is in maintenance mode, fine to keep but not to start with. `WebClient` when the application is reactive or needs non-blocking calls or streaming. OpenFeign when the project already uses Spring Cloud. Then mention timeouts, error mapping and that the client should sit behind an interface of your own.

## Calling other services responsibly

- **Always set timeouts.** Some underlying HTTP libraries wait indefinitely by default. A slow remote service then holds your request threads until none are left and your own service stops responding.
- **Translate errors at the boundary.** The rest of your code should see `PaymentDeclinedException`, not `HttpClientErrorException$PaymentRequired`. That keeps HTTP details inside the gateway class.
- **Do not call a remote service inside a database transaction** if you can avoid it. The transaction, and its database connection, stay open for as long as the remote call takes.
- **Make retried calls idempotent.** A POST that timed out may have succeeded. Sending a unique request id, which the server uses to recognise duplicates (an *idempotency key*), makes a retry safe.
- **Externalise URLs and secrets.** Base URLs in properties; credentials in environment variables or a secret store, never in the source.

> [!WARNING]
> A timeout tells you that you do not know what happened. The payment may have been taken. Never treat a timeout as "failed, so it is safe to try again" for a non-idempotent operation without an idempotency key or a status check.

## Pitfalls

- **`new RestTemplate()` or `RestClient.create()` scattered through the code.** They bypass Boot's configured builders: no shared timeouts, no metrics, no tracing headers. Inject the builder and define client beans.
- **No timeouts.** See above; this is the most damaging omission.
- **Building URLs by string concatenation.** `"/search?q=" + text` breaks on spaces and special characters and invites injection. Use URI templates with variables.
- **Ignoring error bodies.** The remote service's explanation is in the body of the 4xx response; read it from the exception when mapping errors.
- **Deserialising into the wrong shape.** A JSON array into a single object fails with a conversion exception. Use `ParameterizedTypeReference` for lists.
- **Forgetting `@EnableFeignClients`.** No client bean exists and injection fails with `NoSuchBeanDefinitionException`.
- **Leaking the remote API's model through your application.** Map the remote DTOs to your own types at the gateway, so that a change on their side touches one class.

## Cheat sheet

| Annotation / type | Meaning |
|---|---|
| `RestTemplate` + `RestTemplateBuilder` | classic blocking client and its Boot builder |
| `exchange(url, method, entity, type)` | general `RestTemplate` call |
| `getForObject`, `postForObject` | `RestTemplate` shortcuts |
| `RestClient` + `RestClient.Builder` | modern fluent blocking client |
| `.get()/.post().uri().body().retrieve().body(T.class)` | the `RestClient` chain |
| `.onStatus(predicate, handler)` | map error statuses to exceptions |
| `ParameterizedTypeReference<List<T>>` | type token for generic responses |
| `@FeignClient`, `@EnableFeignClients` | Spring Cloud OpenFeign declarative client |
| `@HttpExchange`, `@GetExchange`, `@PostExchange` | Spring's HTTP interface annotations |
| `HttpServiceProxyFactory` | creates the implementation of an HTTP interface |
| `RestClientResponseException` | base class of exceptions for 4xx/5xx responses |

## Summary

- Calling another REST API always means: build the URL, serialise the body, send and wait, check the status, deserialise.
- `RestTemplate` is the long-standing blocking client, now in maintenance mode; `RestClient` is its fluent successor and the default choice for new blocking code.
- Declarative clients (OpenFeign, `@HttpExchange` interfaces) generate the implementation from an annotated interface using a proxy.
- Hide the client behind your own interface and translate HTTP errors into your own exceptions there.
- Configure timeouts, keep URLs in properties, and be careful with retries of non-idempotent calls.

## Glossary

- **Blocking call**: a call during which the calling thread waits for the result.
- **Declarative client**: an HTTP client defined as an annotated interface whose implementation is generated.
- **Fluent API**: an API designed for chained method calls that read like a sentence.
- **Gateway (proxy)**: a class representing an external system inside your application.
- **Idempotency key**: a unique id sent with a request so that the server can detect repeats.
- **OpenFeign**: Spring Cloud's declarative HTTP client.
- **Read timeout**: the maximum time to wait for response data after connecting.
- **Connect timeout**: the maximum time to wait for the connection to be established.
- **`RestClient`**: Spring's current blocking HTTP client.
- **`RestTemplate`**: Spring's original blocking HTTP client.

```quiz
[
  {"q": "Which client does the Spring documentation recommend for new blocking (servlet) code?",
   "options": ["RestTemplate", "RestClient", "HttpURLConnection", "WebClient only"],
   "answer": 1,
   "explain": "RestTemplate is in maintenance mode. RestClient offers the same capabilities with a fluent API and is the current recommendation for blocking calls."},
  {"q": "In the RestClient chain, which call sends the request and waits for the response?",
   "options": ["uri(...)", "body(request)", "retrieve()", "header(...)"],
   "answer": 2,
   "explain": "retrieve() performs the exchange; the following call (body, toEntity) converts the response."},
  {"q": "What does a declarative client such as OpenFeign generate at start-up?",
   "options": ["Java source files", "A proxy implementation of your annotated interface that builds HTTP requests from the annotations", "A new controller", "A database table"],
   "answer": 1,
   "explain": "The interface carries the mapping metadata; the library creates a proxy bean that turns method calls into HTTP calls."},
  {"q": "Why must every HTTP client have timeouts configured?",
   "options": ["To make responses smaller", "Without them a slow remote service can hold your threads indefinitely and exhaust your own service", "Because JSON requires them", "To enable HTTPS"],
   "answer": 1,
   "explain": "Blocked threads accumulate until none are left to serve requests. Timeouts bound the damage."},
  {"q": "A POST to the payment service times out. What do you know?",
   "options": ["The payment certainly failed", "The payment certainly succeeded", "Nothing certain: it may or may not have been processed", "The server is down"],
   "answer": 2,
   "explain": "A timeout only says no answer arrived in time. Use an idempotency key or a status check before retrying."},
  {"q": "How do you receive a JSON array as a List<PaymentResponse> with RestClient?",
   "options": [".body(List.class) is fully typed", ".body(new ParameterizedTypeReference<List<PaymentResponse>>() { })", ".body(PaymentResponse.class)", "It is not possible"],
   "answer": 1,
   "explain": "Generic type information is erased at run time; the type reference preserves the element type for the converter."},
  {"q": "Why put the HTTP client behind your own PaymentGateway interface?",
   "options": ["Spring requires it", "So the rest of the code depends on a small contract, can be tested with a fake, and is isolated from HTTP details", "It makes calls faster", "To avoid JSON"],
   "answer": 1,
   "explain": "The gateway is a boundary: implementation and technology can change, and errors are translated in one place."}
]
```

> **Source:** Spilcă, *Spring Start Here*, ch. 11 (calling REST endpoints with OpenFeign and RestTemplate). Documentation: https://docs.spring.io/spring-framework/reference/integration/rest-clients.html and https://docs.spring.io/spring-boot/reference/io/rest-client.html
