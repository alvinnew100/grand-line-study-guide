# Wiring beans with @Bean methods and @Autowired

> **Before this lesson:** you can register beans with `@Bean` methods and with stereotype annotations plus component scanning ([The application context and @Bean](#/lesson/spring/spring-context-bean), [Stereotype annotations, component scanning and programmatic registration](#/lesson/spring/spring-stereotypes-scan)).

## In plain words

A new employee starts on Monday. They need a laptop, a door card and a desk phone. In a badly run company the employee walks to a shop and buys a laptop, cuts their own door card and installs a phone line. In a well-run company the employee states what the role requires, and the office manager has everything waiting on the desk.

So far every bean in our context has stood alone. Real objects need other objects: an order service needs a repository, the repository needs a database connection. **Wiring** means connecting each bean to the beans it needs. With **dependency injection** the bean states its needs and Spring, the office manager, places them on the desk.

This lesson shows the ways to state those needs: in a configuration class, and with the `@Autowired` annotation on a constructor, a field or a setter. It also explains why professional teams have settled on constructor injection. "Which injection style do you use and why?" is asked in almost every Spring interview.

## The relationship we want to build

Two classes of the bookshop. An `OrderService` cannot work without a `BookRepository`. In object-oriented terms the service *has a* repository.

```java
// src/main/java/com/bookshop/catalogue/BookRepository.java
package com.bookshop.catalogue;

import java.util.Map;

public class BookRepository {
    private final Map<String, Integer> priceCentsByIsbn = Map.of("9780441172719", 1250);

    public int priceCents(String isbn) {
        return priceCentsByIsbn.get(isbn);
    }
}
```

```java
// src/main/java/com/bookshop/order/OrderService.java
package com.bookshop.order;

import com.bookshop.catalogue.BookRepository;

public class OrderService {

    private final BookRepository books;        // the dependency

    public OrderService(BookRepository books) {
        this.books = books;
    }

    public int totalCents(String isbn, int quantity) {
        return books.priceCents(isbn) * quantity;
    }
}
```

Neither class contains anything from Spring yet. `OrderService` receives its repository through the constructor and stores it in a `final` field. A `final` field must be given a value in the constructor and can never be changed afterwards.

```mermaid
flowchart LR
    OS[OrderService] -->|has a| BR[BookRepository]
```

## Wiring in a configuration class, style 1: call the other @Bean method

```java
// src/main/java/com/bookshop/config/AppConfig.java
package com.bookshop.config;

import com.bookshop.catalogue.BookRepository;
import com.bookshop.order.OrderService;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AppConfig {

    @Bean
    BookRepository bookRepository() {
        return new BookRepository();
    }

    @Bean
    OrderService orderService() {
        return new OrderService(bookRepository());     // looks like a second call...
    }
}
```

Reading this as ordinary Java, `bookRepository()` runs twice: once when Spring creates the repository bean and once inside `orderService()`. That would give two different repository objects.

It does not, and here is why. The previous lessons mentioned that Spring replaces a `@Configuration` class with a generated subclass. That subclass overrides every `@Bean` method with roughly this logic: "if the bean already exists in the context, return it; otherwise run the real method and store the result". The call inside `orderService()` therefore returns the bean that is already there.

```java
var context = new AnnotationConfigApplicationContext(AppConfig.class);
OrderService service = context.getBean(OrderService.class);
BookRepository repository = context.getBean(BookRepository.class);
System.out.println(service.totalCents("9780441172719", 2));
```

```text
2500
```

The service uses the very same repository instance that the context hands out.

## Wiring in a configuration class, style 2: ask for a parameter

```java
@Configuration
public class AppConfig {

    @Bean
    BookRepository bookRepository() {
        return new BookRepository();
    }

    @Bean
    OrderService orderService(BookRepository books) {   // Spring supplies the argument
        return new OrderService(books);
    }
}
```

When an `@Bean` method has parameters, Spring looks in the context for a bean of each parameter's type and passes it in. This is dependency injection in its purest form: the method declares a need, the container satisfies it.

Style 2 is preferred. It works even when the dependency is defined in a different configuration class or by a stereotype annotation, and it does not rely on the subclassing trick.

## Wiring with stereotype annotations: @Autowired

When the classes are registered by scanning there is no method body in which to call `new`. The class itself has to say what it needs. The annotation for that is `@Autowired`, and it can be placed in three positions.

### 1. On the constructor (recommended)

```java
// src/main/java/com/bookshop/catalogue/BookRepository.java
@Repository
public class BookRepository { /* as before */ }
```

```java
// src/main/java/com/bookshop/order/OrderService.java
package com.bookshop.order;

import com.bookshop.catalogue.BookRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class OrderService {

    private final BookRepository books;

    @Autowired                                   // optional when there is only one constructor
    public OrderService(BookRepository books) {
        this.books = books;
    }

    public int totalCents(String isbn, int quantity) {
        return books.priceCents(isbn) * quantity;
    }
}
```

Spring must call a constructor to create the bean anyway. Seeing the parameter of type `BookRepository`, it fetches that bean and passes it. When a class has exactly **one** constructor, Spring uses it automatically and `@Autowired` may be left out. Most modern code omits it:

```java
@Service
public class OrderService {
    private final BookRepository books;

    public OrderService(BookRepository books) {     // no annotation needed
        this.books = books;
    }
}
```

### 2. On the field

```java
@Service
public class OrderService {

    @Autowired
    private BookRepository books;       // cannot be final

    public int totalCents(String isbn, int quantity) {
        return books.priceCents(isbn) * quantity;
    }
}
```

Spring first creates the object with the no-argument constructor, then reaches into the private field using **reflection** (a Java facility that lets code inspect and modify other objects at run time, even private members) and sets it. It is the shortest to write, which is why older tutorials are full of it.

### 3. On a setter

```java
@Service
public class OrderService {

    private BookRepository books;

    @Autowired
    public void setBooks(BookRepository books) {    // called by Spring after construction
        this.books = books;
    }
}
```

Spring creates the object, then calls the setter with the bean.

## Why constructor injection wins

| Question | Constructor | Field | Setter |
|---|---|---|---|
| Can the field be `final`? | yes | no | no |
| Can the object exist without its dependency? | no | yes, the field is `null` until Spring sets it | yes |
| Can you create it in a plain unit test with `new`? | yes: `new OrderService(fakeRepository)` | only with reflection or a Spring context | yes, by calling the setter |
| Are the dependencies visible from outside? | yes, in the constructor signature | hidden | partly |
| Does a long list of dependencies look painful? | yes, which is a useful warning | no, which hides the design problem | somewhat |

Four reasons, in the order an interviewer hopes to hear them:

1. **Immutability.** `final` fields cannot be reassigned by mistake and are safe to read from many threads.
2. **Completeness.** An object built through its constructor is fully usable the moment it exists. With field injection there is a window in which the object exists with `null` fields, and calling it from its own constructor throws `NullPointerException`.
3. **Testability.** A unit test can construct the class directly and pass a fake dependency, with no Spring involved.
4. **Honesty.** The constructor is a visible contract. A constructor with nine parameters tells you the class does too much; nine `@Autowired` fields hide the same problem.

> [!INTERVIEW]
> "Why is constructor injection preferred over field injection?" Answer with the four points above: final fields, no half-built objects, plain-Java unit tests, explicit dependencies. Add that the Spring team itself recommends constructor injection for mandatory dependencies and setter injection only for optional ones.

> [!WARNING]
> Field injection fails silently in a specific way: if someone creates the class with `new OrderService()` instead of obtaining the bean, the field stays `null` and the first method call crashes far away from the real mistake. With constructor injection that code does not even compile.

## A model: a container that injects by type

The following container extends the earlier toy. It reads each class's constructor parameters, finds a bean of each parameter's type, and creates objects in an order that satisfies everyone.

```python-run
import inspect

class BookRepository:
    def __init__(self):
        self.prices = {"9780441172719": 1250}
    def price_cents(self, isbn):
        return self.prices[isbn]

class PriceCalculator:
    def __init__(self):
        pass
    def total(self, unit, quantity):
        return unit * quantity

class OrderService:
    def __init__(self, books: BookRepository, calculator: PriceCalculator):
        self.books, self.calculator = books, calculator
    def total_cents(self, isbn, quantity):
        return self.calculator.total(self.books.price_cents(isbn), quantity)

class OrderController:
    def __init__(self, orders: OrderService):
        self.orders = orders

class Container:
    def __init__(self, classes):
        self.classes = classes
        self.beans = {}                                   # type -> instance

    def get(self, wanted):
        if wanted in self.beans:                          # already built: reuse (singleton)
            return self.beans[wanted]
        if wanted not in self.classes:
            raise LookupError(f"NoSuchBeanDefinitionException: {wanted.__name__}")
        parameters = inspect.signature(wanted.__init__).parameters
        needs = [p.annotation for name, p in parameters.items() if name != "self"]
        arguments = [self.get(need) for need in needs]    # build dependencies first
        instance = wanted(*arguments)                     # constructor injection
        self.beans[wanted] = instance
        print(f"created {wanted.__name__}({', '.join(n.__name__ for n in needs)})")
        return instance

    def refresh(self):
        for cls in self.classes:                          # eager: create everything at start-up
            self.get(cls)

container = Container([OrderController, OrderService, BookRepository, PriceCalculator])
container.refresh()
controller = container.get(OrderController)
print(controller.orders.total_cents("9780441172719", 2))
print(controller.orders.books is container.get(BookRepository))
```

Key lines:

- `inspect.signature(...)` reads the constructor's parameter list, as Spring reads a Java constructor through reflection.
- `self.get(need)` is recursive: to build `OrderController` the container first builds `OrderService`, which first builds its two dependencies. Look at the order of the "created" lines: the leaves come first even though `OrderController` was listed first.
- The last line prints `True`: the repository inside the service is the same object the container returns. One bean, shared.

Remove `BookRepository` from the list passed to `Container` and run it again. The error appears at start-up, before any business call, which is the fail-fast behaviour from the earlier lesson. The practice problems [Wire a bean graph by type](#/problem/spring-wire-by-type) and [Constructor injection order and cycle detection](#/problem/spring-creation-order) build on this model.

## Optional dependencies

By default an injection point is mandatory: no matching bean, no start-up. Sometimes a collaborator is truly optional.

```java
@Service
public class OrderService {

    private final BookRepository books;
    private final Optional<GiftWrapService> giftWrap;         // may be absent

    public OrderService(BookRepository books, Optional<GiftWrapService> giftWrap) {
        this.books = books;
        this.giftWrap = giftWrap;
    }
}
```

Declaring the parameter as `Optional<T>` tells Spring to pass an empty `Optional` when no such bean exists. Alternatives are `@Autowired(required = false)` on a setter or field, a parameter annotated `@Nullable`, and `ObjectProvider<T>`, which also lets you fetch the bean lazily.

## Injecting several beans at once

If you ask for a collection, Spring injects **all** beans of the element type:

```java
@Service
public class CheckoutService {

    private final List<DiscountRule> rules;       // every DiscountRule bean in the context

    public CheckoutService(List<DiscountRule> rules) {
        this.rules = rules;
    }
}
```

This is the basis of plug-in style designs: adding a new class that implements `DiscountRule` and is annotated `@Component` extends the checkout without touching `CheckoutService`. A `Map<String, DiscountRule>` parameter receives the same beans keyed by bean name. Put `@Order(1)`, `@Order(2)` on the classes to control the list order.

## Injecting simple values with @Value

Not every constructor argument is a bean. Configuration values such as a shop name or a page size are injected with `@Value`:

```java
@Service
public class CatalogueService {

    private final int pageSize;

    public CatalogueService(@Value("${shop.page-size:20}") int pageSize) {
        this.pageSize = pageSize;
    }
}
```

The text `${shop.page-size:20}` is a **placeholder**: Spring replaces it with the value of the property `shop.page-size`, or with `20` when the property is not defined, and converts the text to `int`. Properties and the grouped alternative `@ConfigurationProperties` are covered in [Configuration properties, profiles and logging](#/lesson/spring/spring-config-profiles-logging).

## Pitfalls

- **`new` breaks the chain.** `new OrderService(new BookRepository())` in your own code produces unmanaged objects. The repository inside is not the bean, so anything Spring adds to the bean (transactions, for example) is missing.
- **Two constructors without `@Autowired`.** With several constructors Spring uses the no-argument one if it exists, and otherwise fails with "No default constructor found". Mark the intended constructor with `@Autowired`, or keep exactly one.
- **Using an injected field in the constructor.** With field injection the field is still `null` while the constructor runs. Move the logic to `@PostConstruct`, or better, switch to constructor injection.
- **Injecting into a static field.** Spring injects into instances. `@Autowired` on a `static` field is ignored and leaves it `null`.
- **Calling an `@Bean` method from outside its configuration class.** The "returns the existing bean" behaviour belongs to the generated subclass. Calling the method on an object you built with `new AppConfig()` runs the body again and creates an unmanaged duplicate.
- **`@Bean` methods in a `@Component` class.** Classes not marked `@Configuration` are processed in "lite" mode: they are not subclassed, so one `@Bean` method calling another really executes it twice. Use parameters (style 2) and the problem disappears.

## Cheat sheet

| Annotation / type | Where | Meaning |
|---|---|---|
| `@Autowired` | constructor | inject the parameters (implicit with a single constructor) |
| `@Autowired` | field | inject by reflection after construction (discouraged) |
| `@Autowired` | setter | call the setter with the bean after construction (for optional dependencies) |
| `@Autowired(required = false)` | field or setter | skip injection when no bean exists |
| `Optional<T>` parameter | constructor | empty when no bean exists |
| `ObjectProvider<T>` parameter | constructor | look the bean up later, possibly not at all |
| `List<T>` / `Map<String, T>` parameter | constructor | all beans of type `T` |
| `@Value("${key:default}")` | parameter or field | inject a configuration value |
| `@Bean` method parameter | configuration class | Spring supplies a bean of that type |

## Summary

- Wiring connects beans to the beans they need; with dependency injection the container does it.
- In configuration classes, declare the dependency as a method parameter of the `@Bean` method.
- With stereotype annotations, declare dependencies as constructor parameters. A single constructor needs no `@Autowired`.
- Field and setter injection exist, but constructor injection gives `final` fields, complete objects, plain unit tests and visible dependencies.
- Asking for a `List<T>` injects every bean of that type; `Optional<T>` makes a dependency optional; `@Value` injects configuration values.

## Glossary

- **`@Autowired`**: annotation marking a constructor, field or setter where Spring should inject beans.
- **Constructor injection**: dependencies are passed as constructor arguments.
- **Field injection**: Spring sets a field directly through reflection.
- **Injection point**: a place (parameter, field, setter) where a dependency is supplied.
- **Placeholder**: text of the form `${key}` replaced by a configuration value.
- **Reflection**: the Java ability to inspect and manipulate classes and objects at run time.
- **Setter injection**: Spring calls a setter method with the dependency.
- **Wiring**: establishing the relationships between beans.

```quiz
[
  {"q": "A @Service class has exactly one constructor taking a BookRepository. Is @Autowired required on it?",
   "options": ["Yes, always", "No, Spring uses a single constructor automatically", "Only in Spring Boot", "Only if the class is final"],
   "answer": 1,
   "explain": "With a single constructor Spring injects its parameters without any annotation. @Autowired is needed only to choose among several constructors."},
  {"q": "Why can a field-injected dependency not be declared final?",
   "options": ["Spring forbids final fields", "A final field must be assigned in the constructor, but field injection assigns it afterwards", "Final fields cannot hold objects", "Reflection cannot read final fields"],
   "answer": 1,
   "explain": "Field injection happens after the constructor has finished, which is too late for a final field."},
  {"q": "In a @Configuration class, orderService() calls bookRepository(), which is also an @Bean method. How many BookRepository instances exist?",
   "options": ["Two", "One, because the generated subclass returns the existing bean", "None", "One per call to getBean"],
   "answer": 1,
   "explain": "Spring subclasses the configuration class and intercepts @Bean method calls so that the singleton already in the context is returned."},
  {"q": "Which is NOT an advantage of constructor injection?",
   "options": ["Dependencies can be final", "The class can be created in a unit test with new", "It needs fewer lines of code than field injection", "The object is never in a half-initialised state"],
   "answer": 2,
   "explain": "Field injection is shorter to type. Constructor injection is preferred for immutability, completeness, testability and explicitness."},
  {"q": "A constructor parameter is declared as List<DiscountRule>. What does Spring inject?",
   "options": ["An empty list always", "Only the @Primary DiscountRule", "All beans whose type is DiscountRule", "It fails with NoUniqueBeanDefinitionException"],
   "answer": 2,
   "explain": "Collection injection gathers every matching bean, which makes plug-in style extension possible."},
  {"q": "In the Python container, why is BookRepository created before OrderController although it is listed later?",
   "options": ["Lists are sorted alphabetically", "The container builds a bean's constructor arguments before the bean itself", "Repositories always come first", "It is random"],
   "answer": 1,
   "explain": "Constructor injection forces dependencies to exist first, so creation proceeds depth-first from the requested bean to its leaves."},
  {"q": "What happens if someone writes new OrderService() for a class that uses @Autowired on a private field?",
   "options": ["Spring injects the field anyway", "The code does not compile", "The object is created with a null field and fails when used", "A new application context is started"],
   "answer": 2,
   "explain": "Spring only injects into objects it creates. A hand-made instance has its field left null, causing a NullPointerException later."}
]
```

> **Source:** Spilcă, *Spring Start Here*, ch. 3 (wiring beans, @Autowired). Documentation: https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html and https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/autowired.html
