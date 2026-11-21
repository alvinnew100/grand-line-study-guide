def _l(i, t, f):
    return dict(id=i, title=t, file=f)


TRACK = dict(
    id="spring",
    title="Spring Boot",
    icon="🌱",
    color="#5aa02c",
    group="Languages",
    blurb="From 'what is a framework?' to production Spring Boot 3: the container, dependency injection, AOP, "
          "web and REST, data access, transactions, Spring Data, testing, security and interview preparation. "
          "Every mechanism is modelled in runnable Python so you can watch it work, then rebuilt in real Java 21 "
          "on the judge: an IoC container, AOP proxies, transactions, a router, validation and a filter chain.",
    sources=[
        "Spilcă, Spring Start Here (Manning), ch. 1–15",
        "Spring Framework reference documentation (docs.spring.io/spring-framework/reference)",
        "Spring Boot reference documentation (docs.spring.io/spring-boot)",
    ],
    modules=[
        dict(
            id="spring-real-world",
            title="1. Spring in the real world",
            summary="What a framework is, what Spring is for, the ecosystem, and a first project with and without Boot.",
            lessons=[
                _l("spring-why-frameworks", "What a framework is and why Spring exists", "01-why-frameworks.md"),
                _l("spring-ecosystem-first-project", "The Spring ecosystem and your first project", "02-ecosystem-first-project.md"),
            ],
            problems=[],
        ),
        dict(
            id="spring-context",
            title="2. The Spring context: defining beans",
            summary="The application context, @Bean methods, stereotype annotations, component scanning and programmatic registration.",
            lessons=[
                _l("spring-context-bean", "The application context and @Bean", "03-context-and-bean.md"),
                _l("spring-stereotypes-scan", "Stereotype annotations, component scanning and programmatic registration", "04-stereotypes-scanning.md"),
            ],
            problems=["spring-component-scan", "spring-java-bean-registry"],
        ),
        dict(
            id="spring-wiring",
            title="3. Wiring beans",
            summary="@Autowired, constructor versus field versus setter injection, circular dependencies, @Primary and @Qualifier.",
            lessons=[
                _l("spring-wiring-autowired", "Wiring beans with @Bean methods and @Autowired", "05-wiring-autowired.md"),
                _l("spring-circular-primary-qualifier", "Circular dependencies, @Primary and @Qualifier", "06-circular-primary-qualifier.md"),
            ],
            problems=["spring-creation-order", "spring-resolve-candidate",
                      "spring-java-constructor-injection", "spring-java-qualifier-primary"],
        ),
        dict(
            id="spring-abstractions",
            title="4. Using abstractions",
            summary="Interfaces as contracts, decoupling, injecting implementations, and the layered architecture behind the stereotypes.",
            lessons=[
                _l("spring-interfaces-contracts", "Interfaces as contracts: decoupling your classes", "07-interfaces-contracts.md"),
                _l("spring-di-abstractions-layers", "Dependency injection with abstractions and layered design", "08-di-abstractions-layers.md"),
            ],
            problems=["spring-wire-by-type"],
        ),
        dict(
            id="spring-scopes",
            title="5. Bean scopes and lifecycle",
            summary="Singleton and prototype scope, eager and lazy creation, thread-safety consequences and lifecycle callbacks.",
            lessons=[
                _l("spring-singleton-scope", "Singleton scope, eager and lazy beans, thread safety", "09-singleton-scope.md"),
                _l("spring-prototype-lifecycle", "Prototype scope and the bean lifecycle", "10-prototype-lifecycle.md"),
            ],
            problems=["spring-scope-count", "spring-lazy-eager-order", "spring-lifecycle-order",
                      "spring-java-scopes-lazy", "spring-java-lifecycle"],
        ),
        dict(
            id="spring-aop",
            title="6. Aspects with Spring AOP",
            summary="How proxies intercept calls, the five advice types, pointcut expressions, execution order and the self-invocation limit.",
            lessons=[
                _l("spring-aop-proxies", "How Spring AOP works: proxies and your first aspect", "11-aop-proxies.md"),
                _l("spring-aop-advice-pointcuts", "Advice types, pointcut expressions and aspect order", "12-advice-pointcuts-order.md"),
            ],
            problems=["spring-advice-order", "spring-pointcut-match", "spring-self-invocation",
                      "spring-java-jdk-proxy", "spring-java-advice-chain", "spring-java-self-invocation"],
        ),
        dict(
            id="spring-boot-mvc",
            title="7. Spring Boot and Spring MVC",
            summary="Starters and auto-configuration, the embedded server, and the path of a request through DispatcherServlet to a controller and a template.",
            lessons=[
                _l("spring-boot-autoconfig", "Spring Boot: starters and auto-configuration", "13-boot-starters-autoconfig.md"),
                _l("spring-mvc-request-flow", "Spring MVC: the request flow through DispatcherServlet", "14-mvc-request-flow.md"),
            ],
            problems=["spring-conditional-autoconfig", "spring-request-mapping", "spring-java-request-mapping"],
        ),
        dict(
            id="spring-web-apps",
            title="8. Implementing web apps",
            summary="Request parameters, path variables, the Model, HTTP methods and HTML forms.",
            lessons=[
                _l("spring-request-data", "Request parameters, path variables and the Model", "15-params-path-model.md"),
                _l("spring-http-methods-forms", "HTTP methods and HTML forms", "16-http-methods-forms.md"),
            ],
            problems=["spring-param-binding"],
        ),
        dict(
            id="spring-web-scopes",
            title="9. Web scopes",
            summary="Request, session and application scope: lifetimes, scoped proxies and when each is appropriate.",
            lessons=[
                _l("spring-request-session-scope", "Request and session scope", "17-request-session-scope.md"),
                _l("spring-application-scope", "Application scope and choosing a scope", "18-application-scope.md"),
            ],
            problems=["spring-web-scope-lifetime"],
        ),
        dict(
            id="spring-rest",
            title="10. REST services",
            summary="@RestController, ResponseEntity, request bodies, validation and consistent error responses.",
            lessons=[
                _l("spring-rest-controllers", "REST endpoints with @RestController and ResponseEntity", "19-rest-controllers.md"),
                _l("spring-rest-errors-validation", "Request bodies, validation and error handling with @RestControllerAdvice", "20-rest-errors-validation.md"),
            ],
            problems=["spring-content-negotiation", "spring-bean-validation", "spring-exception-status",
                      "spring-java-bean-validation"],
        ),
        dict(
            id="spring-rest-clients",
            title="11. Consuming REST endpoints",
            summary="Calling other services with RestTemplate, RestClient, declarative clients (OpenFeign, HTTP interfaces) and WebClient.",
            lessons=[
                _l("spring-rest-clients", "Calling REST endpoints: RestTemplate, RestClient and OpenFeign", "21-rest-clients.md"),
                _l("spring-webclient", "WebClient, timeouts and resilient calls", "22-webclient-resilience.md"),
            ],
            problems=["spring-retry-backoff", "spring-java-retry-backoff", "spring-java-circuit-breaker"],
        ),
        dict(
            id="spring-data-sources",
            title="12. Using data sources",
            summary="JDBC, JdbcTemplate, configuring a DataSource and how connection pools behave.",
            lessons=[
                _l("spring-jdbc-template", "JDBC, DataSource and JdbcTemplate", "23-jdbc-jdbctemplate.md"),
                _l("spring-datasource-pools", "Configuring the DataSource and connection pools", "24-datasource-pools.md"),
            ],
            problems=["spring-connection-pool", "spring-java-jdbc-template", "spring-java-record-row-mapper"],
        ),
        dict(
            id="spring-transactions",
            title="13. Transactions",
            summary="@Transactional, rollback rules, the self-invocation pitfall, propagation and isolation.",
            lessons=[
                _l("spring-transactional", "@Transactional, rollback rules and the self-invocation pitfall", "25-transactional.md"),
                _l("spring-propagation-isolation", "Propagation and isolation", "26-propagation-isolation.md"),
            ],
            problems=["spring-rollback-rules", "spring-tx-propagation", "spring-isolation-anomaly",
                      "spring-java-rollback-rules", "spring-java-propagation"],
        ),
        dict(
            id="spring-data",
            title="14. Spring Data",
            summary="Repositories, derived queries, @Query, paging, JPA entity mapping and the N+1 problem.",
            lessons=[
                _l("spring-data-repositories", "Spring Data repositories: derived queries and @Query", "27-spring-data-repositories.md"),
                _l("spring-jpa-mapping", "JPA basics: entity mapping, relationships and the N+1 problem", "28-jpa-mapping-nplus1.md"),
            ],
            problems=["spring-page-request", "spring-derived-query", "spring-n-plus-one", "spring-java-pageable"],
        ),
        dict(
            id="spring-testing",
            title="15. Testing your Spring app",
            summary="Unit tests with mocks, integration tests with @SpringBootTest, and slices such as @WebMvcTest and @DataJpaTest.",
            lessons=[
                _l("spring-unit-tests", "Unit tests with JUnit and Mockito", "29-unit-tests-mocks.md"),
                _l("spring-integration-tests", "Integration tests with @SpringBootTest and test slices", "30-integration-tests-slices.md"),
            ],
            problems=["spring-test-slice"],
        ),
        dict(
            id="spring-production",
            title="16. Production Spring Boot",
            summary="Configuration properties and profiles, logging, Actuator, Docker images, virtual threads and Spring Security with JWT.",
            lessons=[
                _l("spring-config-profiles-logging", "Configuration properties, profiles and logging", "31-config-profiles-logging.md"),
                _l("spring-actuator-docker-vthreads", "Actuator, Docker images and virtual threads", "32-actuator-docker-virtual-threads.md"),
                _l("spring-security-jwt", "Spring Security basics and JWT resource servers", "33-security-jwt.md"),
            ],
            problems=["spring-property-precedence", "spring-placeholder-expand", "spring-health-aggregate",
                      "spring-security-filter-chain", "spring-jwt-validate", "spring-java-security-filter-chain"],
        ),
        dict(
            id="spring-interview",
            title="17. Spring interview essentials",
            summary="Worked answers to the questions that come up most: the container, auto-configuration, proxies, transactions, JPA and the web stack.",
            lessons=[
                _l("spring-interview-core", "Spring interview essentials: the container", "34-interview-core.md"),
                _l("spring-interview-web-data", "Spring interview essentials: web, data and transactions", "35-interview-web-data.md"),
            ],
            problems=[],
        ),
    ],
)
