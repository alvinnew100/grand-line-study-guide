"""Spring track, REAL Java problems part 1 (judged on the server): the container, scopes, lifecycle and AOP proxies.

The judge has the JDK only (no Spring jars), so each exercise builds, in plain Java 21, the mechanism that Spring
provides. The learner edits Solution.java; each harness is a Main.java that prints one CASE line per test.
"""

PRE = r'''import java.util.*;
import java.util.function.*;

public class Main {
    interface Check { String run() throws Throwable; }
    interface Action { Object run() throws Throwable; }
    static int n = 0;

    static void t(Check c) {
        n++;
        String r;
        try { r = c.run(); } catch (Throwable e) { r = "threw " + e; }
        if (r != null) r = r.replace('\n', ' ').replace('\r', ' ');
        System.out.println("CASE " + n + (r == null ? " OK" : " FAIL " + r));
    }

    static String eq(Object got, Object want) {
        return Objects.equals(got, want) ? null : "got " + got + " want " + want;
    }

    static String yes(boolean cond, String why) {
        return cond ? null : why;
    }

    static String thrown(Class<? extends Throwable> type, Action a) {
        try { a.run(); } catch (Throwable e) {
            return type.isInstance(e) ? null : "threw " + e + " but wanted " + type.getSimpleName();
        }
        return "no exception, wanted " + type.getSimpleName();
    }

    static String thrownMsg(Class<? extends Throwable> type, String message, Action a) {
        try { a.run(); } catch (Throwable e) {
            if (!type.isInstance(e)) return "threw " + e + " but wanted " + type.getSimpleName();
            return Objects.equals(e.getMessage(), message) ? null : "message was \"" + e.getMessage() + "\" want \"" + message + "\"";
        }
        return "no exception, wanted " + type.getSimpleName();
    }

    static String thrownWith(Class<? extends Throwable> type, String fragment, Action a) {
        try { a.run(); } catch (Throwable e) {
            if (!type.isInstance(e)) return "threw " + e + " but wanted " + type.getSimpleName();
            return e.getMessage() != null && e.getMessage().contains(fragment) ? null
                : "message \"" + e.getMessage() + "\" should mention " + fragment;
        }
        return "no exception, wanted " + type.getSimpleName();
    }
'''

MAIN = "\n    public static void main(String[] args) {\n"


def H(checks, extra=""):
    """Build Main.java: helper declarations in `extra`, then one t(...) per check.
    A check starting with '{' is a block lambda, otherwise an expression."""
    return PRE + extra + MAIN + "".join("        t(() -> %s);\n" % c for c in checks) + "    }\n}\n"


def G(prereqs, intuition, hints, brute, approach, complexity, pitfalls, follow_up=None):
    d = dict(prereqs=prereqs, intuition=intuition, hints=hints, brute_force=brute, approach=approach,
             complexity=complexity, pitfalls=pitfalls)
    if follow_up:
        d["follow_up"] = follow_up
    return d


def J(id, title, difficulty, pattern, description, starter, solution, checks, wrong, guide, extra=""):
    return dict(id=id, title=title, difficulty=difficulty, pattern=pattern, kind="java", cases=len(checks),
                description=description, starter=starter, solution=solution, harness=H(checks, extra),
                wrong_solutions=wrong, guide=guide)


def mut(src, old, new):
    """A wrong solution made by changing one piece of the reference solution."""
    assert old in src, old
    return src.replace(old, new, 1)


JUDGE_NOTE = ("\n*Real Java 21, compiled and run on the judge server (log in to submit). The judge has the JDK only, "
              "no Spring jars, so you build the mechanism Spring gives you. That is what interviewers probe.*\n")

# ====================================================================================== 1. bean registry
_REG_SOL = r'''import java.util.*;

class Solution {
    static class NoSuchBeanDefinitionException extends RuntimeException {
        NoSuchBeanDefinitionException(String message) { super(message); }
    }

    static class NoUniqueBeanDefinitionException extends RuntimeException {
        NoUniqueBeanDefinitionException(String message) { super(message); }
    }

    static class BeanDefinitionOverrideException extends RuntimeException {
        BeanDefinitionOverrideException(String message) { super(message); }
    }

    static class BeanRegistry {
        private final Map<String, Object> beans = new LinkedHashMap<>();

        void register(String name, Object bean) {
            if (name == null || bean == null) throw new IllegalArgumentException("name and bean must not be null");
            if (beans.containsKey(name)) throw new BeanDefinitionOverrideException("Bean '" + name + "' is already registered");
            beans.put(name, bean);
        }

        boolean containsBean(String name) {
            return beans.containsKey(name);
        }

        Object getBean(String name) {
            Object bean = beans.get(name);
            if (bean == null) throw new NoSuchBeanDefinitionException("No bean named '" + name + "' available");
            return bean;
        }

        List<String> getBeanNamesForType(Class<?> type) {
            List<String> names = new ArrayList<>();
            for (Map.Entry<String, Object> e : beans.entrySet()) {
                if (type.isInstance(e.getValue())) names.add(e.getKey());
            }
            return names;
        }

        <T> T getBean(Class<T> type) {
            List<String> names = getBeanNamesForType(type);
            String prefix = "No qualifying bean of type '" + type.getSimpleName() + "' available";
            if (names.isEmpty()) throw new NoSuchBeanDefinitionException(prefix);
            if (names.size() > 1) {
                throw new NoUniqueBeanDefinitionException(prefix + ": expected single matching bean but found "
                        + names.size() + ": " + String.join(",", names));
            }
            return type.cast(beans.get(names.get(0)));
        }
    }
}
'''

_REG_START = r'''import java.util.*;

class Solution {
    static class NoSuchBeanDefinitionException extends RuntimeException {
        NoSuchBeanDefinitionException(String message) { super(message); }
    }

    static class NoUniqueBeanDefinitionException extends RuntimeException {
        NoUniqueBeanDefinitionException(String message) { super(message); }
    }

    static class BeanDefinitionOverrideException extends RuntimeException {
        BeanDefinitionOverrideException(String message) { super(message); }
    }

    static class BeanRegistry {
        void register(String name, Object bean) {
            // your code
        }

        boolean containsBean(String name) {
            return false;
        }

        Object getBean(String name) {
            return null;
        }

        List<String> getBeanNamesForType(Class<?> type) {
            return List.of();
        }

        <T> T getBean(Class<T> type) {
            return null;
        }
    }
}
'''

_REG_EXTRA = r'''
    interface Greeter { String greet(); }
    static class English implements Greeter { public String greet() { return "hello"; } }
    static class French implements Greeter { public String greet() { return "bonjour"; } }
    static class Clock { }
'''

# ====================================================================================== 2. constructor injection
_CI_START = r'''import java.lang.reflect.*;
import java.util.*;

class Solution {
    static class NoSuchBeanDefinitionException extends RuntimeException {
        NoSuchBeanDefinitionException(String message) { super(message); }
    }

    static class NoUniqueBeanDefinitionException extends RuntimeException {
        NoUniqueBeanDefinitionException(String message) { super(message); }
    }

    static class BeanCurrentlyInCreationException extends RuntimeException {
        BeanCurrentlyInCreationException(String message) { super(message); }
    }

    static class MiniContainer {
        void register(Class<?> type) {
            // your code
        }

        <T> T getBean(Class<T> type) {
            return null;
        }

        List<String> creationOrder() {
            return List.of();
        }
    }
}
'''

_CI_SOL = r'''import java.lang.reflect.*;
import java.util.*;

class Solution {
    static class NoSuchBeanDefinitionException extends RuntimeException {
        NoSuchBeanDefinitionException(String message) { super(message); }
    }

    static class NoUniqueBeanDefinitionException extends RuntimeException {
        NoUniqueBeanDefinitionException(String message) { super(message); }
    }

    static class BeanCurrentlyInCreationException extends RuntimeException {
        BeanCurrentlyInCreationException(String message) { super(message); }
    }

    static class MiniContainer {
        private final List<Class<?>> types = new ArrayList<>();
        private final Map<Class<?>, Object> singletons = new HashMap<>();
        private final List<Class<?>> inCreation = new ArrayList<>();
        private final List<String> order = new ArrayList<>();

        void register(Class<?> type) {
            if (!types.contains(type)) types.add(type);
        }

        <T> T getBean(Class<T> type) {
            List<Class<?>> matches = new ArrayList<>();
            for (Class<?> c : types) {
                if (type.isAssignableFrom(c)) matches.add(c);
            }
            if (matches.isEmpty()) {
                throw new NoSuchBeanDefinitionException("No qualifying bean of type '" + type.getSimpleName() + "' available");
            }
            if (matches.size() > 1) {
                throw new NoUniqueBeanDefinitionException("expected single matching bean of type '"
                        + type.getSimpleName() + "' but found " + matches.size());
            }
            return type.cast(instance(matches.get(0)));
        }

        private Object instance(Class<?> c) {
            Object existing = singletons.get(c);
            if (existing != null) return existing;
            int at = inCreation.indexOf(c);
            if (at >= 0) {
                StringBuilder sb = new StringBuilder("Circular reference: ");
                for (int i = at; i < inCreation.size(); i++) sb.append(inCreation.get(i).getSimpleName()).append(" -> ");
                sb.append(c.getSimpleName());
                throw new BeanCurrentlyInCreationException(sb.toString());
            }
            Constructor<?>[] ctors = c.getDeclaredConstructors();
            if (ctors.length != 1) {
                throw new IllegalStateException(c.getSimpleName() + " must have exactly one constructor");
            }
            inCreation.add(c);
            try {
                Class<?>[] params = ctors[0].getParameterTypes();
                Object[] args = new Object[params.length];
                for (int i = 0; i < params.length; i++) args[i] = getBean(params[i]);
                ctors[0].setAccessible(true);
                Object bean = ctors[0].newInstance(args);
                singletons.put(c, bean);
                order.add(c.getSimpleName());
                return bean;
            } catch (ReflectiveOperationException e) {
                throw new IllegalStateException("Cannot create " + c.getSimpleName(), e);
            } finally {
                inCreation.remove(inCreation.size() - 1);
            }
        }

        List<String> creationOrder() {
            return List.copyOf(order);
        }
    }
}
'''

_CI_EXTRA = r'''
    static class Clock { int now() { return 42; } }
    interface Repo { String find(); }
    static class JdbcRepo implements Repo {
        final Clock clock;
        JdbcRepo(Clock clock) { this.clock = clock; }
        public String find() { return "row@" + clock.now(); }
    }
    static class Service { final Repo repo; Service(Repo repo) { this.repo = repo; } }
    static class Controller {
        final Service service;
        final Clock clock;
        Controller(Service service, Clock clock) { this.service = service; this.clock = clock; }
    }
    static class Ping { Ping(Pong p) { } }
    static class Pong { Pong(Ping p) { } }
    static class Alpha { Alpha(Beta b) { } }
    static class Beta { Beta(Gamma g) { } }
    static class Gamma { Gamma(Alpha a) { } }
    static class Outer { Outer(Alpha a) { } }
    static class Narcissus { Narcissus(Narcissus self) { } }
    static class Needy { Needy(Runnable r) { } }
    interface Pay { }
    static class Card implements Pay { }
    static class Cash implements Pay { }
    static class Shop { Shop(Pay pay) { } }
    static class TwoWays { TwoWays() { } TwoWays(Clock c) { } }

    static Solution.MiniContainer of(Class<?>... types) {
        Solution.MiniContainer c = new Solution.MiniContainer();
        for (Class<?> t : types) c.register(t);
        return c;
    }
'''

# ====================================================================================== 3. scopes and lazy
_SC_START = r'''import java.util.*;
import java.util.function.*;

class Solution {
    static class NoSuchBeanDefinitionException extends RuntimeException {
        NoSuchBeanDefinitionException(String message) { super(message); }
    }

    static class ScopedContainer {
        void register(String name, String scope, boolean lazy, Function<ScopedContainer, Object> factory) {
            // your code
        }

        void refresh() {
        }

        Object getBean(String name) {
            return null;
        }

        int created(String name) {
            return 0;
        }

        List<String> creationLog() {
            return List.of();
        }
    }
}
'''

_SC_SOL = r'''import java.util.*;
import java.util.function.*;

class Solution {
    static class NoSuchBeanDefinitionException extends RuntimeException {
        NoSuchBeanDefinitionException(String message) { super(message); }
    }

    static class ScopedContainer {
        private record Definition(String scope, boolean lazy, Function<ScopedContainer, Object> factory) { }

        private final Map<String, Definition> definitions = new LinkedHashMap<>();
        private final Map<String, Object> singletons = new HashMap<>();
        private final Map<String, Integer> counts = new HashMap<>();
        private final List<String> log = new ArrayList<>();
        private boolean refreshed;

        void register(String name, String scope, boolean lazy, Function<ScopedContainer, Object> factory) {
            if (!scope.equals("singleton") && !scope.equals("prototype")) {
                throw new IllegalArgumentException("Unknown scope '" + scope + "'");
            }
            if (definitions.containsKey(name)) throw new IllegalStateException("Bean '" + name + "' already defined");
            definitions.put(name, new Definition(scope, lazy, factory));
        }

        void refresh() {
            if (refreshed) throw new IllegalStateException("already refreshed");
            refreshed = true;
            for (Map.Entry<String, Definition> e : definitions.entrySet()) {
                Definition d = e.getValue();
                if (d.scope().equals("singleton") && !d.lazy()) getBean(e.getKey());
            }
        }

        Object getBean(String name) {
            if (!refreshed) throw new IllegalStateException("context has not been refreshed yet");
            Definition d = definitions.get(name);
            if (d == null) throw new NoSuchBeanDefinitionException("No bean named '" + name + "' available");
            boolean singleton = d.scope().equals("singleton");
            if (singleton && singletons.containsKey(name)) return singletons.get(name);
            Object bean = d.factory().apply(this);
            counts.merge(name, 1, Integer::sum);
            log.add(name);
            if (singleton) singletons.put(name, bean);
            return bean;
        }

        int created(String name) {
            return counts.getOrDefault(name, 0);
        }

        List<String> creationLog() {
            return List.copyOf(log);
        }
    }
}
'''

_SC_EXTRA = r'''
    static class Counter { }
    static class Holder { final Object dep; Holder(Object dep) { this.dep = dep; } }
    static Solution.ScopedContainer box() { return new Solution.ScopedContainer(); }
'''

# ====================================================================================== 4. qualifier / primary
_QP_START = r'''import java.util.*;

class Solution {
    record Candidate(String name, Class<?> type, boolean primary) { }

    static class NoSuchBeanDefinitionException extends RuntimeException {
        NoSuchBeanDefinitionException(String message) { super(message); }
    }

    static class NoUniqueBeanDefinitionException extends RuntimeException {
        NoUniqueBeanDefinitionException(String message) { super(message); }
    }

    static String resolve(List<Candidate> beans, Class<?> wanted, String qualifier, String parameterName) {
        // your code
        return null;
    }
}
'''

_QP_SOL = r'''import java.util.*;

class Solution {
    record Candidate(String name, Class<?> type, boolean primary) { }

    static class NoSuchBeanDefinitionException extends RuntimeException {
        NoSuchBeanDefinitionException(String message) { super(message); }
    }

    static class NoUniqueBeanDefinitionException extends RuntimeException {
        NoUniqueBeanDefinitionException(String message) { super(message); }
    }

    static String resolve(List<Candidate> beans, Class<?> wanted, String qualifier, String parameterName) {
        String prefix = "No qualifying bean of type '" + wanted.getSimpleName() + "' available";
        List<Candidate> candidates = new ArrayList<>();
        for (Candidate c : beans) {
            if (wanted.isAssignableFrom(c.type())) candidates.add(c);
        }
        if (qualifier != null) {
            for (Candidate c : candidates) {
                if (c.name().equals(qualifier)) return c.name();
            }
            throw new NoSuchBeanDefinitionException(prefix + ": qualifier '" + qualifier + "'");
        }
        if (candidates.isEmpty()) throw new NoSuchBeanDefinitionException(prefix);
        if (candidates.size() == 1) return candidates.get(0).name();
        List<String> primaries = new ArrayList<>();
        for (Candidate c : candidates) {
            if (c.primary()) primaries.add(c.name());
        }
        if (primaries.size() == 1) return primaries.get(0);
        if (primaries.size() > 1) {
            throw new NoUniqueBeanDefinitionException("more than one 'primary' bean found among candidates: " + primaries);
        }
        for (Candidate c : candidates) {
            if (c.name().equals(parameterName)) return c.name();
        }
        List<String> names = new ArrayList<>();
        for (Candidate c : candidates) names.add(c.name());
        throw new NoUniqueBeanDefinitionException(prefix + ": expected single matching bean but found "
                + names.size() + ": " + String.join(",", names));
    }
}
'''

_QP_EXTRA = r'''
    interface Notifier { }
    static class EmailNotifier implements Notifier { }
    static class SmsNotifier implements Notifier { }
    static class PushNotifier implements Notifier { }
    static class Clock { }
    static class BaseRepo { }
    static class JpaRepo extends BaseRepo { }

    static List<Solution.Candidate> beans(String primaries) {
        Set<String> p = new HashSet<>(Arrays.asList(primaries.split(",")));
        return List.of(new Solution.Candidate("emailNotifier", EmailNotifier.class, p.contains("emailNotifier")),
                       new Solution.Candidate("smsNotifier", SmsNotifier.class, p.contains("smsNotifier")),
                       new Solution.Candidate("pushNotifier", PushNotifier.class, p.contains("pushNotifier")),
                       new Solution.Candidate("clock", Clock.class, p.contains("clock")));
    }
'''

# ====================================================================================== 5. lifecycle
_LC_START = r'''import java.util.*;
import java.util.function.*;

class Solution {
    interface InitializingBean { void afterPropertiesSet() throws Exception; }

    interface DisposableBean { void destroy() throws Exception; }

    interface BeanPostProcessor {
        default Object postProcessBeforeInitialization(Object bean, String name) { return bean; }
        default Object postProcessAfterInitialization(Object bean, String name) { return bean; }
    }

    static class BeanCreationException extends RuntimeException {
        BeanCreationException(String message, Throwable cause) { super(message, cause); }
    }

    static class LifecycleContext {
        void register(String name, Supplier<Object> factory) {
            // your code
        }

        void addBeanPostProcessor(BeanPostProcessor processor) {
        }

        void refresh() {
        }

        Object getBean(String name) {
            return null;
        }

        void close() {
        }
    }
}
'''

_LC_SOL = r'''import java.util.*;
import java.util.function.*;

class Solution {
    interface InitializingBean { void afterPropertiesSet() throws Exception; }

    interface DisposableBean { void destroy() throws Exception; }

    interface BeanPostProcessor {
        default Object postProcessBeforeInitialization(Object bean, String name) { return bean; }
        default Object postProcessAfterInitialization(Object bean, String name) { return bean; }
    }

    static class BeanCreationException extends RuntimeException {
        BeanCreationException(String message, Throwable cause) { super(message, cause); }
    }

    static class LifecycleContext {
        private final Map<String, Supplier<Object>> factories = new LinkedHashMap<>();
        private final List<BeanPostProcessor> processors = new ArrayList<>();
        private final Map<String, Object> exposed = new HashMap<>();
        private final List<Object> createdRaw = new ArrayList<>();
        private boolean closed;

        void register(String name, Supplier<Object> factory) {
            factories.put(name, factory);
        }

        void addBeanPostProcessor(BeanPostProcessor processor) {
            processors.add(processor);
        }

        void refresh() {
            for (Map.Entry<String, Supplier<Object>> e : factories.entrySet()) {
                String name = e.getKey();
                try {
                    Object raw = e.getValue().get();
                    Object bean = raw;
                    for (BeanPostProcessor p : processors) {
                        Object result = p.postProcessBeforeInitialization(bean, name);
                        if (result != null) bean = result;
                    }
                    if (bean instanceof InitializingBean ib) ib.afterPropertiesSet();
                    for (BeanPostProcessor p : processors) {
                        Object result = p.postProcessAfterInitialization(bean, name);
                        if (result != null) bean = result;
                    }
                    exposed.put(name, bean);
                    createdRaw.add(raw);
                } catch (Exception ex) {
                    close();
                    throw new BeanCreationException("Error creating bean with name '" + name + "'", ex);
                }
            }
        }

        Object getBean(String name) {
            if (closed) throw new IllegalStateException("context is closed");
            Object bean = exposed.get(name);
            if (bean == null) throw new NoSuchElementException("No bean named '" + name + "'");
            return bean;
        }

        void close() {
            if (closed) return;
            closed = true;
            for (int i = createdRaw.size() - 1; i >= 0; i--) {
                if (createdRaw.get(i) instanceof DisposableBean d) {
                    try {
                        d.destroy();
                    } catch (Exception ignored) {
                        // Spring logs the failure and carries on with the other beans
                    }
                }
            }
        }
    }
}
'''

_LC_EXTRA = r'''
    static final List<String> LOG = new ArrayList<>();

    static class Tracked implements Solution.InitializingBean, Solution.DisposableBean {
        final String id;
        Tracked(String id) { this.id = id; LOG.add("new " + id); }
        public void afterPropertiesSet() { LOG.add("init " + id); }
        public void destroy() { LOG.add("destroy " + id); }
    }
    static class Plain { Plain() { LOG.add("new plain"); } }
    static class BadInit implements Solution.InitializingBean {
        BadInit() { LOG.add("new bad"); }
        public void afterPropertiesSet() throws Exception { throw new Exception("boom"); }
    }
    static class BadDestroy implements Solution.DisposableBean {
        public void destroy() throws Exception { LOG.add("destroy bad"); throw new IllegalStateException("nope"); }
    }
    static class Tagging implements Solution.BeanPostProcessor {
        final String tag;
        Tagging(String tag) { this.tag = tag; }
        public Object postProcessBeforeInitialization(Object bean, String name) { LOG.add(tag + " before " + name); return bean; }
        public Object postProcessAfterInitialization(Object bean, String name) { LOG.add(tag + " after " + name); return bean; }
    }
    static class Wrapper { final Object inner; Wrapper(Object inner) { this.inner = inner; } }

    static Solution.LifecycleContext ctx() { LOG.clear(); return new Solution.LifecycleContext(); }
'''

# ====================================================================================== 6. JDK proxy
_PX_START = r'''import java.lang.reflect.*;
import java.util.*;

class Solution {
    static <T> T loggingProxy(T target, Class<T> iface, List<String> log) {
        // your code: return a java.lang.reflect.Proxy that implements iface
        return target;
    }
}
'''

_PX_SOL = r'''import java.lang.reflect.*;
import java.util.*;

class Solution {
    static <T> T loggingProxy(T target, Class<T> iface, List<String> log) {
        InvocationHandler handler = (proxy, method, args) -> {
            if (method.getDeclaringClass() == Object.class) {
                try {
                    return method.invoke(target, args);
                } catch (InvocationTargetException e) {
                    throw e.getCause();
                }
            }
            log.add("before " + method.getName());
            try {
                Object result = method.invoke(target, args);
                log.add("after " + method.getName() + " returned " + result);
                return result;
            } catch (InvocationTargetException e) {
                Throwable cause = e.getCause();
                log.add("after " + method.getName() + " threw " + cause.getClass().getSimpleName());
                throw cause;
            }
        };
        Object proxy = Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[] { iface }, handler);
        return iface.cast(proxy);
    }
}
'''

_PX_EXTRA = r'''
    interface Calculator {
        int add(int a, int b);
        int divide(int a, int b);
        void reset();
        String describe() throws java.io.IOException;
    }
    static class SimpleCalculator implements Calculator {
        public int add(int a, int b) { return a + b; }
        public int divide(int a, int b) { return a / b; }
        public void reset() { }
        public String describe() throws java.io.IOException { throw new java.io.IOException("disk"); }
        @Override public String toString() { return "SimpleCalculator"; }
    }
'''

# ====================================================================================== 7. advice chain
_AC_START = r'''import java.lang.reflect.*;
import java.util.*;
import java.util.function.*;

class Solution {
    interface Invocation {
        String methodName();
        Object proceed() throws Throwable;
    }

    interface Advice {
        Object invoke(Invocation invocation) throws Throwable;
    }

    record OrderedAdvice(int order, Advice advice) { }

    static Advice before(Consumer<String> action) {
        return null;
    }

    static Advice afterReturning(BiConsumer<String, Object> action) {
        return null;
    }

    static Advice afterThrowing(BiConsumer<String, Throwable> action) {
        return null;
    }

    static Advice after(Consumer<String> action) {
        return null;
    }

    static <T> T proxy(T target, Class<T> iface, List<OrderedAdvice> advices) {
        // your code
        return target;
    }
}
'''

_AC_SOL = r'''import java.lang.reflect.*;
import java.util.*;
import java.util.function.*;

class Solution {
    interface Invocation {
        String methodName();
        Object proceed() throws Throwable;
    }

    interface Advice {
        Object invoke(Invocation invocation) throws Throwable;
    }

    record OrderedAdvice(int order, Advice advice) { }

    static Advice before(Consumer<String> action) {
        return inv -> {
            action.accept(inv.methodName());
            return inv.proceed();
        };
    }

    static Advice afterReturning(BiConsumer<String, Object> action) {
        return inv -> {
            Object result = inv.proceed();
            action.accept(inv.methodName(), result);
            return result;
        };
    }

    static Advice afterThrowing(BiConsumer<String, Throwable> action) {
        return inv -> {
            try {
                return inv.proceed();
            } catch (Throwable t) {
                action.accept(inv.methodName(), t);
                throw t;
            }
        };
    }

    static Advice after(Consumer<String> action) {
        return inv -> {
            try {
                return inv.proceed();
            } finally {
                action.accept(inv.methodName());
            }
        };
    }

    static <T> T proxy(T target, Class<T> iface, List<OrderedAdvice> advices) {
        List<OrderedAdvice> sorted = new ArrayList<>(advices);
        sorted.sort(Comparator.comparingInt(OrderedAdvice::order));
        InvocationHandler handler = (p, method, args) -> {
            if (method.getDeclaringClass() == Object.class) return callTarget(target, method, args);
            return chain(sorted, 0, target, method, args);
        };
        return iface.cast(Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[] { iface }, handler));
    }

    private static Object chain(List<OrderedAdvice> advices, int i, Object target, Method method, Object[] args)
            throws Throwable {
        if (i == advices.size()) return callTarget(target, method, args);
        Invocation invocation = new Invocation() {
            public String methodName() { return method.getName(); }
            public Object proceed() throws Throwable { return chain(advices, i + 1, target, method, args); }
        };
        return advices.get(i).advice().invoke(invocation);
    }

    private static Object callTarget(Object target, Method method, Object[] args) throws Throwable {
        try {
            return method.invoke(target, args);
        } catch (InvocationTargetException e) {
            throw e.getCause();
        }
    }
}
'''

_AC_CURSOR = r'''        InvocationHandler handler = (p, method, args) -> {
            if (method.getDeclaringClass() == Object.class) return callTarget(target, method, args);
            int[] index = {0};
            Invocation cursor = new Invocation() {
                public String methodName() { return method.getName(); }
                public Object proceed() throws Throwable {
                    if (index[0] == sorted.size()) return callTarget(target, method, args);
                    return sorted.get(index[0]++).advice().invoke(this);
                }
            };
            return cursor.proceed();
        };'''

_AC_EXTRA = r'''
    interface Greeter {
        String greet(String who);
        String load() throws java.io.IOException;
    }
    static class Target implements Greeter {
        final List<String> log;
        final int failFirst;
        int calls;
        Target(List<String> log, int failFirst) { this.log = log; this.failFirst = failFirst; }
        public String greet(String who) {
            calls++;
            log.add("target " + who);
            if (calls <= failFirst) throw new IllegalStateException("flaky " + calls);
            if (who.isEmpty()) throw new IllegalArgumentException("empty");
            return "hi " + who;
        }
        public String load() throws java.io.IOException { throw new java.io.IOException("disk"); }
        @Override public String toString() { return "Target"; }
    }
    static Solution.Advice around(String tag, List<String> log) {
        return inv -> { log.add(tag + " in"); Object r = inv.proceed(); log.add(tag + " out"); return r; };
    }
    static Solution.OrderedAdvice at(int order, Solution.Advice advice) { return new Solution.OrderedAdvice(order, advice); }
'''

# ====================================================================================== 8. self-invocation
_SI_START = r'''import java.lang.reflect.*;
import java.util.*;

class Solution {
    static <T> T transactionalProxy(T target, Class<T> iface, Set<String> transactionalMethods, List<String> log) {
        // your code
        return target;
    }

    static Object currentProxy() {
        // your code
        return null;
    }
}
'''

_SI_SOL = r'''import java.lang.reflect.*;
import java.util.*;

class Solution {
    private static final ThreadLocal<Object> CURRENT = new ThreadLocal<>();

    static <T> T transactionalProxy(T target, Class<T> iface, Set<String> transactionalMethods, List<String> log) {
        InvocationHandler handler = (proxy, method, args) -> {
            if (method.getDeclaringClass() == Object.class) return invokeTarget(target, method, args);
            Object previous = CURRENT.get();
            CURRENT.set(proxy);
            try {
                String name = method.getName();
                if (!transactionalMethods.contains(name)) return invokeTarget(target, method, args);
                log.add("begin " + name);
                Object result;
                try {
                    result = invokeTarget(target, method, args);
                } catch (Throwable t) {
                    log.add("rollback " + name);
                    throw t;
                }
                log.add("commit " + name);
                return result;
            } finally {
                if (previous == null) CURRENT.remove(); else CURRENT.set(previous);
            }
        };
        return iface.cast(Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[] { iface }, handler));
    }

    static Object currentProxy() {
        Object proxy = CURRENT.get();
        if (proxy == null) throw new IllegalStateException("Cannot find current proxy: is exposeProxy enabled?");
        return proxy;
    }

    private static Object invokeTarget(Object target, Method method, Object[] args) throws Throwable {
        try {
            return method.invoke(target, args);
        } catch (InvocationTargetException e) {
            throw e.getCause();
        }
    }
}
'''

_SI_EXTRA = r'''
    interface OrderService { void placeOrder(); void placeOrderFixed(); void saveAudit(); void fail(); }
    static class OrderServiceImpl implements OrderService {
        final List<String> log;
        OrderServiceImpl(List<String> log) { this.log = log; }
        public void placeOrder() { log.add("placeOrder body"); this.saveAudit(); }
        public void placeOrderFixed() { log.add("placeOrderFixed body"); ((OrderService) Solution.currentProxy()).saveAudit(); }
        public void saveAudit() { log.add("saveAudit body"); }
        public void fail() { log.add("fail body"); throw new IllegalStateException("no stock"); }
        @Override public String toString() { return "impl"; }
    }
    interface Named { String name(); String callOther(); }
    static class NamedImpl implements Named {
        final String id;
        Named other;
        Object self;
        NamedImpl(String id) { this.id = id; }
        public String name() { return id + (Solution.currentProxy() == self ? "+" : "-"); }
        public String callOther() { String o = other.name(); return o + "," + name(); }
    }
    static OrderService svc(List<String> log, String... tx) {
        return Solution.transactionalProxy(new OrderServiceImpl(log), OrderService.class, Set.of(tx), log);
    }
'''


PROBLEMS = [
# ------------------------------------------------------------------ spring-java-bean-registry
J("spring-java-bean-registry", "Java: a bean registry with lookup by name and by type", "Easy", "Spring container (Java)",
  r"""
The heart of a Spring `ApplicationContext` is a **registry**: a map from bean names to objects, plus a lookup *by
type* that finds every bean that is an instance of a class or interface. This is the mechanism behind
`context.getBean("clock")`, `context.getBean(Clock.class)` and the two famous exceptions you meet in the lesson
[The application context and @Bean](#/lesson/spring/spring-context-bean).

Inside `Solution`, complete `static class BeanRegistry` (the three exception classes are given):

| method | behaviour |
|---|---|
| `void register(String name, Object bean)` | `null` name or bean → `IllegalArgumentException`. A name that is already registered → `BeanDefinitionOverrideException("Bean '<name>' is already registered")` and the first bean stays (Spring Boot's default, `spring.main.allow-bean-definition-overriding=false`). |
| `boolean containsBean(String name)` | whether the name is registered |
| `Object getBean(String name)` | the object itself, or `NoSuchBeanDefinitionException("No bean named '<name>' available")` |
| `List<String> getBeanNamesForType(Class<?> type)` | names of beans that are instances of `type`, **in registration order** |
| `<T> T getBean(Class<T> type)` | the single matching bean; none → `NoSuchBeanDefinitionException("No qualifying bean of type '<SimpleName>' available")`; several → `NoUniqueBeanDefinitionException("No qualifying bean of type '<SimpleName>' available: expected single matching bean but found <n>: <name1>,<name2>")` |

**Example**

```java
BeanRegistry r = new BeanRegistry();
r.register("english", new English());     // English implements Greeter
r.register("french", new French());       // French implements Greeter
r.getBeanNamesForType(Greeter.class);     // [english, french]
r.getBean(Greeter.class);                 // NoUniqueBeanDefinitionException ... found 2: english,french
```
""" + JUDGE_NOTE,
  _REG_START, _REG_SOL,
  [r'''{ Solution.BeanRegistry r = new Solution.BeanRegistry(); Clock c = new Clock(); r.register("clock", c); return yes(r.getBean("clock") == c, "getBean(name) must return the registered object itself"); }''',
   r'''{ Solution.BeanRegistry r = new Solution.BeanRegistry(); Clock c = new Clock(); r.register("clock", c); return yes(r.getBean(Clock.class) == c, "getBean(Clock.class) must return the clock"); }''',
   r'''{ Solution.BeanRegistry r = new Solution.BeanRegistry(); r.register("english", new English()); r.register("clock", new Clock()); return eq(r.getBean(Greeter.class).greet(), "hello"); }''',
   r'''{ Solution.BeanRegistry r = new Solution.BeanRegistry(); r.register("french", new French()); r.register("clock", new Clock()); r.register("english", new English()); return eq(r.getBeanNamesForType(Greeter.class), List.of("french", "english")); }''',
   r'''{ Solution.BeanRegistry r = new Solution.BeanRegistry(); r.register("english", new English()); r.register("french", new French()); return thrownMsg(Solution.NoUniqueBeanDefinitionException.class, "No qualifying bean of type 'Greeter' available: expected single matching bean but found 2: english,french", () -> r.getBean(Greeter.class)); }''',
   r'''{ Solution.BeanRegistry r = new Solution.BeanRegistry(); r.register("clock", new Clock()); return thrownMsg(Solution.NoSuchBeanDefinitionException.class, "No bean named 'missing' available", () -> r.getBean("missing")); }''',
   r'''{ Solution.BeanRegistry r = new Solution.BeanRegistry(); r.register("clock", new Clock()); return thrownMsg(Solution.NoSuchBeanDefinitionException.class, "No qualifying bean of type 'Runnable' available", () -> r.getBean(Runnable.class)); }''',
   r'''{ Solution.BeanRegistry r = new Solution.BeanRegistry(); Clock first = new Clock(); r.register("clock", first); String bad = thrownMsg(Solution.BeanDefinitionOverrideException.class, "Bean 'clock' is already registered", () -> { r.register("clock", new Clock()); return null; }); if (bad != null) return bad; return yes(r.getBean("clock") == first, "the first bean must survive a rejected duplicate"); }''',
   r'''{ Solution.BeanRegistry r = new Solution.BeanRegistry(); r.register("clock", new Clock()); return eq(r.containsBean("clock") + " " + r.containsBean("Clock"), "true false"); }''',
   r'''{ Solution.BeanRegistry r = new Solution.BeanRegistry(); String a = thrown(IllegalArgumentException.class, () -> { r.register("x", null); return null; }); if (a != null) return "null bean: " + a; String b = thrown(IllegalArgumentException.class, () -> { r.register(null, new Clock()); return null; }); return b == null ? yes(!r.containsBean("x"), "nothing may be registered") : "null name: " + b; }''',
   r'''{ Solution.BeanRegistry r = new Solution.BeanRegistry(); r.register("c", new Clock()); r.register("a", new English()); r.register("b", "text"); return eq(r.getBeanNamesForType(Object.class), List.of("c", "a", "b")); }''',
   r'''{ Solution.BeanRegistry r = new Solution.BeanRegistry(); if (!r.getBeanNamesForType(Object.class).isEmpty()) return "an empty registry has no names"; return thrown(Solution.NoSuchBeanDefinitionException.class, () -> r.getBean(Object.class)); }'''],
  [mut(_REG_SOL, "            if (names.size() > 1) {", "            if (names.size() > 99) {"),
   mut(_REG_SOL, '            if (beans.containsKey(name)) throw new BeanDefinitionOverrideException("Bean \'" + name + "\' is already registered");\n', "")],
  G("Lesson [The application context and @Bean](#/lesson/spring/spring-context-bean). Java: `Map`, `LinkedHashMap`, `Class.isInstance`, generic methods.",
    "A registry is a map from names to objects. Lookup by type is a scan: keep every bean for which `type.isInstance(bean)` is true. Then the count decides: zero, one or too many.",
    ["Use a `LinkedHashMap<String, Object>` so that iteration follows registration order.",
     "`type.isInstance(bean)` is true when the bean's class is `type`, a subclass of it, or implements it.",
     "`getBean(Class<T>)` can reuse `getBeanNamesForType`, then `type.cast(...)` turns the `Object` into a `T` without an unchecked warning."],
    "Scanning all beans on every by-type lookup is O(B). Spring caches the name lists per type after startup; for this exercise the scan is fine.",
    r"""1. `register`: validate, refuse duplicates, `put`.
2. `getBeanNamesForType`: loop over `entrySet()`, keep names where `type.isInstance(value)`.
3. `getBean(Class<T>)`: build the names list once; size 0 → no such bean, size > 1 → not unique, otherwise cast and return.

```java
<T> T getBean(Class<T> type) {
    List<String> names = getBeanNamesForType(type);
    String prefix = "No qualifying bean of type '" + type.getSimpleName() + "' available";
    if (names.isEmpty()) throw new NoSuchBeanDefinitionException(prefix);
    if (names.size() > 1) throw new NoUniqueBeanDefinitionException(prefix
            + ": expected single matching bean but found " + names.size() + ": " + String.join(",", names));
    return type.cast(beans.get(names.get(0)));
}
```

**Dry run** with `english`, `french` registered: `getBeanNamesForType(Greeter.class)` → `[english, french]`; size 2 → the exception message ends with `found 2: english,french`, the same wording Spring prints.""",
    "register and getBean(name) O(1); by-type lookups O(B) for B beans.",
    "- A `HashMap` loses registration order.\n- Comparing `bean.getClass() == type` misses interfaces and subclasses.\n- Overwriting on duplicate names hides configuration mistakes; Spring Boot refuses them by default.\n- Returning the first match instead of failing when two beans qualify.",
    "Real Spring keeps *bean definitions* (recipes) separately from *singleton instances*; see the next exercise, which creates beans from their constructors."),
  extra=_REG_EXTRA),

# ------------------------------------------------------------------ spring-java-constructor-injection
J("spring-java-constructor-injection", "Java: constructor injection and cycle detection with reflection", "Medium", "Spring container (Java)",
  r"""
Build the core of an IoC container with reflection: it reads a class's constructor, works out which beans to pass
in **by type**, creates them first, and caches every bean as a singleton. This is what Spring does for
constructor injection (lesson [Wiring beans with @Bean methods and @Autowired](#/lesson/spring/spring-wiring-autowired)),
including the circular-dependency failure from
[Circular dependencies, @Primary and @Qualifier](#/lesson/spring/spring-circular-primary-qualifier).

Complete `MiniContainer` (exception classes are given):

- `void register(Class<?> type)` — remember a concrete class. Registering the same class twice has no effect.
- `<T> T getBean(Class<T> type)` — find the registered classes `c` with `type.isAssignableFrom(c)`.
  None → `NoSuchBeanDefinitionException` whose message contains the simple name of `type`; more than one →
  `NoUniqueBeanDefinitionException`. Otherwise return the singleton instance of that class, creating it on first use.
- **Creating** class `C`: it must declare exactly one constructor (`getDeclaredConstructors()`), otherwise
  `IllegalStateException`. Resolve each parameter type, left to right, with `getBean` (which may create more beans),
  then call the constructor (use `setAccessible(true)`). Cache the instance and append `C`'s simple name to the
  creation order **after** it has been constructed, so dependencies appear before the beans that need them.
- **Cycles**: if `C` is requested while it is still being created, throw `BeanCurrentlyInCreationException` with the
  message `"Circular reference: "` followed by the classes from the first occurrence of `C` in the current creation
  path to the end, then `C` again, joined by `" -> "`. Example: requesting `Outer`, which needs `Alpha → Beta → Gamma → Alpha`,
  gives `Circular reference: Alpha -> Beta -> Gamma -> Alpha`.
- After any failure the container must still work: nothing may be left marked as "in creation".
- `List<String> creationOrder()` — simple names of the classes created so far.

Only beans that are asked for (directly or as dependencies) are created.
""" + JUDGE_NOTE,
  _CI_START, _CI_SOL,
  [r'''{ var c = of(Clock.class, JdbcRepo.class, Service.class, Controller.class); c.getBean(Controller.class); return eq(c.creationOrder(), List.of("Clock", "JdbcRepo", "Service", "Controller")); }''',
   r'''{ var c = of(Controller.class, Service.class, JdbcRepo.class, Clock.class); Controller k = c.getBean(Controller.class); return yes(k.clock == c.getBean(Clock.class) && ((JdbcRepo) k.service.repo).clock == k.clock && k == c.getBean(Controller.class), "singletons: every injection point must receive the same instance"); }''',
   r'''{ var c = of(Clock.class, JdbcRepo.class); return eq(c.getBean(Repo.class).find(), "row@42"); }''',
   r'''{ var c = of(Clock.class, JdbcRepo.class, Service.class); c.getBean(Service.class); c.getBean(Service.class); c.getBean(Repo.class); return eq(c.creationOrder(), List.of("Clock", "JdbcRepo", "Service")); }''',
   r'''thrownMsg(Solution.BeanCurrentlyInCreationException.class, "Circular reference: Ping -> Pong -> Ping", () -> of(Ping.class, Pong.class).getBean(Ping.class))''',
   r'''thrownMsg(Solution.BeanCurrentlyInCreationException.class, "Circular reference: Alpha -> Beta -> Gamma -> Alpha", () -> of(Outer.class, Alpha.class, Beta.class, Gamma.class).getBean(Outer.class))''',
   r'''{ var c = of(Ping.class, Pong.class, Clock.class); String first = thrownMsg(Solution.BeanCurrentlyInCreationException.class, "Circular reference: Ping -> Pong -> Ping", () -> c.getBean(Ping.class)); if (first != null) return first; String again = thrownMsg(Solution.BeanCurrentlyInCreationException.class, "Circular reference: Pong -> Ping -> Pong", () -> c.getBean(Pong.class)); if (again != null) return "second attempt: " + again; return yes(c.getBean(Clock.class) != null && c.creationOrder().equals(List.of("Clock")), "after a failure the container must still create other beans"); }''',
   r'''thrownMsg(Solution.BeanCurrentlyInCreationException.class, "Circular reference: Narcissus -> Narcissus", () -> of(Narcissus.class).getBean(Narcissus.class))''',
   r'''thrownWith(Solution.NoSuchBeanDefinitionException.class, "Runnable", () -> of(Needy.class).getBean(Needy.class))''',
   r'''thrown(Solution.NoUniqueBeanDefinitionException.class, () -> of(Card.class, Cash.class, Shop.class).getBean(Shop.class))''',
   r'''thrown(IllegalStateException.class, () -> of(Clock.class, TwoWays.class).getBean(TwoWays.class))''',
   r'''thrownWith(Solution.NoSuchBeanDefinitionException.class, "Service", () -> of(Clock.class).getBean(Service.class))''',
   r'''{ var c = of(Clock.class, Clock.class, JdbcRepo.class); c.getBean(Repo.class); return eq(c.creationOrder(), List.of("Clock", "JdbcRepo")); }'''],
  [mut(_CI_SOL, "            if (existing != null) return existing;\n", ""),
   mut(_CI_SOL, "for (int i = at; i < inCreation.size(); i++)", "for (int i = 0; i < inCreation.size(); i++)"),
   mut(_CI_SOL, "            } finally {\n                inCreation.remove(inCreation.size() - 1);\n            }",
       "            } finally {\n                if (singletons.containsKey(c)) inCreation.remove(inCreation.size() - 1);\n            }")],
  G("Lessons [Wiring beans with @Bean methods and @Autowired](#/lesson/spring/spring-wiring-autowired) and [Circular dependencies, @Primary and @Qualifier](#/lesson/spring/spring-circular-primary-qualifier). Java reflection: `getDeclaredConstructors`, `getParameterTypes`, `newInstance`.",
    "Creating a bean is a depth-first walk of the dependency graph. A cache of finished singletons stops repeated work, and a list of beans *currently being created* is exactly the recursion stack: meeting a class that is already on it means a cycle.",
    ["Keep three structures: registered classes, a `Map<Class<?>, Object>` of finished singletons, and a `List<Class<?>>` path of classes in creation.",
     "Check the singleton cache first, then the path. Push onto the path before resolving parameters and pop in a `finally` block so that exceptions cannot leave stale entries.",
     "For the cycle message, `inCreation.indexOf(c)` is where the cycle starts; join from there to the end and add `c` again."],
    "Without the in-creation path, a cycle recurses until `StackOverflowError`. Without the singleton cache, every injection point receives a fresh object and the creation order lists classes many times.",
    r"""```java
private Object instance(Class<?> c) {
    Object existing = singletons.get(c);
    if (existing != null) return existing;                 // 1. finished already
    int at = inCreation.indexOf(c);
    if (at >= 0) { /* build "A -> B -> A" from 'at' */ }    // 2. cycle
    Constructor<?>[] ctors = c.getDeclaredConstructors();
    if (ctors.length != 1) throw new IllegalStateException(...);
    inCreation.add(c);
    try {
        Class<?>[] params = ctors[0].getParameterTypes();
        Object[] args = new Object[params.length];
        for (int i = 0; i < params.length; i++) args[i] = getBean(params[i]);   // 3. depth first
        ctors[0].setAccessible(true);
        Object bean = ctors[0].newInstance(args);
        singletons.put(c, bean);
        order.add(c.getSimpleName());                       // 4. after construction
        return bean;
    } catch (ReflectiveOperationException e) {
        throw new IllegalStateException("Cannot create " + c.getSimpleName(), e);
    } finally {
        inCreation.remove(inCreation.size() - 1);           // 5. always pop
    }
}
```

**Dry run** `getBean(Outer)`: path `[Outer]` → needs `Alpha` → `[Outer, Alpha]` → `[Outer, Alpha, Beta]` → `[Outer, Alpha, Beta, Gamma]` → Gamma needs `Alpha`, which is at index 1 → message `Alpha -> Beta -> Gamma -> Alpha`. The exception unwinds through four `finally` blocks, leaving the path empty.""",
    "Each class is constructed once: O(V + E) over the dependency graph, plus O(B) per by-type lookup.",
    "- Recording the creation order before construction (dependencies would then appear after their users).\n- Forgetting to pop the path when an exception passes through.\n- Printing the whole path instead of the cycle.\n- Using `getConstructors()`, which only sees `public` constructors.",
    "Real Spring can resolve some cycles between *setter* or *field* injected singletons by exposing an early reference (a three-level cache). Constructor cycles can never be resolved, which is one reason constructor injection is recommended: cycles fail fast. Since Spring Boot 2.6 all cycles fail by default (`spring.main.allow-circular-references=false`)."),
  extra=_CI_EXTRA),

# ------------------------------------------------------------------ spring-java-scopes-lazy
J("spring-java-scopes-lazy", "Java: singleton, prototype and lazy beans", "Medium", "Bean scopes (Java)",
  r"""
Model how a Spring context creates beans of different **scopes** (lessons
[Singleton scope, eager and lazy beans, thread safety](#/lesson/spring/spring-singleton-scope) and
[Prototype scope and the bean lifecycle](#/lesson/spring/spring-prototype-lifecycle)). Beans are registered as
factory functions, like `@Bean` methods: a factory receives the container and may call `getBean` to obtain its
dependencies.

Complete `ScopedContainer`:

- `register(String name, String scope, boolean lazy, Function<ScopedContainer, Object> factory)` — `scope` is
  `"singleton"` or `"prototype"`; anything else → `IllegalArgumentException`. A name registered twice →
  `IllegalStateException`. `lazy` only matters for singletons (`@Lazy`).
- `refresh()` — starts the context: creates every **non-lazy singleton** in registration order (skipping any that
  already exist because an earlier bean needed them). Prototypes and lazy singletons are not created. A second call
  → `IllegalStateException`.
- `getBean(String name)` — before `refresh()` → `IllegalStateException`. Unknown name →
  `NoSuchBeanDefinitionException` (given). A singleton is created on first request (that is how a lazy one is
  born) and the same object is returned afterwards. A prototype calls its factory **on every request**.
- Every time a factory is called, after it returns: `created(name)` goes up by one and `name` is appended to
  `creationLog()`.

Classic consequence to observe: a singleton that receives a prototype in its factory keeps that **one** prototype
instance forever.
""" + JUDGE_NOTE,
  _SC_START, _SC_SOL,
  [r'''{ var c = box(); c.register("a", "singleton", false, x -> new Counter()); c.refresh(); return yes(c.getBean("a") == c.getBean("a") && c.created("a") == 1, "a singleton is created once and shared (created=" + c.created("a") + ")"); }''',
   r'''{ var c = box(); c.register("p", "prototype", false, x -> new Counter()); c.refresh(); int before = c.created("p"); Object a = c.getBean("p"); Object b = c.getBean("p"); return yes(before == 0 && a != b && c.created("p") == 2, "a prototype is not created by refresh() and is new on every getBean (before=" + before + ", created=" + c.created("p") + ")"); }''',
   r'''{ var c = box(); c.register("e1", "singleton", false, x -> new Counter()); c.register("l", "singleton", true, x -> new Counter()); c.register("e2", "singleton", false, x -> new Counter()); c.refresh(); String r = eq(c.creationLog(), List.of("e1", "e2")); if (r != null) return "after refresh: " + r; c.getBean("l"); c.getBean("l"); return eq(c.creationLog(), List.of("e1", "e2", "l")); }''',
   r'''{ var c = box(); c.register("service", "singleton", false, x -> new Holder(x.getBean("repo"))); c.register("repo", "singleton", false, x -> new Counter()); c.refresh(); Holder s = (Holder) c.getBean("service"); return yes(c.creationLog().equals(List.of("repo", "service")) && s.dep == c.getBean("repo"), "log " + c.creationLog() + " should be [repo, service] and the repo shared"); }''',
   r'''{ var c = box(); c.register("cart", "prototype", false, x -> new Counter()); c.register("shop", "singleton", false, x -> new Holder(x.getBean("cart"))); c.refresh(); Holder s1 = (Holder) c.getBean("shop"); Holder s2 = (Holder) c.getBean("shop"); if (s1.dep != s2.dep || c.created("cart") != 1) return "the singleton keeps one prototype: created(cart)=" + c.created("cart"); c.getBean("cart"); return eq(c.created("cart"), 2); }''',
   r'''{ var c = box(); c.register("mailer", "singleton", true, x -> new Counter()); c.register("notifier", "singleton", false, x -> new Holder(x.getBean("mailer"))); c.refresh(); return eq(c.creationLog(), List.of("mailer", "notifier")); }''',
   r'''{ var c = box(); c.register("clock", "singleton", false, x -> new Counter()); c.register("job", "prototype", false, x -> new Holder(x.getBean("clock"))); c.refresh(); Holder a = (Holder) c.getBean("job"); Holder b = (Holder) c.getBean("job"); return yes(a != b && a.dep == b.dep && c.created("clock") == 1, "prototypes are new, their singleton dependency is shared"); }''',
   r'''{ var c = box(); c.refresh(); return thrownWith(Solution.NoSuchBeanDefinitionException.class, "nope", () -> c.getBean("nope")); }''',
   r'''{ var c = box(); c.register("a", "singleton", false, x -> new Counter()); return thrown(IllegalStateException.class, () -> c.getBean("a")); }''',
   r'''thrown(IllegalArgumentException.class, () -> { box().register("a", "request", false, x -> new Counter()); return null; })''',
   r'''{ var c = box(); c.register("a", "singleton", false, x -> new Counter()); c.refresh(); String r = thrown(IllegalStateException.class, () -> { c.refresh(); return null; }); return r != null ? r : eq(c.created("a"), 1); }''',
   r'''{ var c = box(); c.register("a", "singleton", false, x -> new Counter()); return thrown(IllegalStateException.class, () -> { c.register("a", "prototype", false, x -> new Counter()); return null; }); }''',
   r'''{ var c = box(); c.register("leaf", "prototype", false, x -> new Counter()); c.register("mid", "prototype", false, x -> new Holder(x.getBean("leaf"))); c.refresh(); for (int i = 0; i < 3; i++) c.getBean("mid"); return eq(c.created("mid") + "/" + c.created("leaf") + " " + c.creationLog(), "3/3 [leaf, mid, leaf, mid, leaf, mid]"); }'''],
  [mut(_SC_SOL, "if (singleton && singletons.containsKey(name))", "if (singletons.containsKey(name))").replace(
       "if (singleton) singletons.put(name, bean);", "singletons.put(name, bean);"),
   mut(_SC_SOL, 'if (d.scope().equals("singleton") && !d.lazy()) getBean(e.getKey());', 'if (d.scope().equals("singleton")) getBean(e.getKey());')],
  G("Lessons [Singleton scope, eager and lazy beans](#/lesson/spring/spring-singleton-scope) and [Prototype scope and the bean lifecycle](#/lesson/spring/spring-prototype-lifecycle). Java: `Function`, `LinkedHashMap`, records.",
    "Scope only decides one thing: whether `getBean` consults a cache. Singletons go through a cache, prototypes never do. Eager versus lazy only decides whether `refresh()` warms that cache up front.",
    ["Store each definition as a small record `(scope, lazy, factory)` in a `LinkedHashMap` so `refresh()` can follow registration order.",
     "`refresh()` can simply call `getBean` for every non-lazy singleton; the cache takes care of beans that were already created as dependencies.",
     "Update the counter and the log after `factory.apply(this)` returns, so that dependencies created inside the factory are logged first."],
    "Creating every bean in `refresh()` is simpler but wrong: lazy beans and prototypes would be built at startup.",
    r"""```java
Object getBean(String name) {
    if (!refreshed) throw new IllegalStateException(...);
    Definition d = definitions.get(name);
    if (d == null) throw new NoSuchBeanDefinitionException(...);
    boolean singleton = d.scope().equals("singleton");
    if (singleton && singletons.containsKey(name)) return singletons.get(name);
    Object bean = d.factory().apply(this);   // may call getBean for dependencies
    counts.merge(name, 1, Integer::sum);
    log.add(name);
    if (singleton) singletons.put(name, bean);
    return bean;
}
```

**Dry run** of the prototype-in-singleton case: `refresh()` creates `shop`; its factory calls `getBean("cart")`, which creates one cart (log `[cart]`), then `shop` is logged. Every later `getBean("shop")` returns the cached shop holding that same cart. To get a fresh prototype each time, Spring offers `ObjectProvider<Cart>`, `@Lookup` methods or a scoped proxy.""",
    "Each getBean is O(1) plus the cost of the factory.",
    "- Caching prototypes.\n- Creating lazy singletons in `refresh()`.\n- Logging before the factory runs, which puts a bean before its dependencies.\n- Allowing `getBean` before `refresh()`.",
    "In Spring, `@Lazy` on an *injection point* injects a proxy that creates the bean on first method call, which is different from `@Lazy` on the bean definition modelled here."),
  extra=_SC_EXTRA),

# ------------------------------------------------------------------ spring-java-qualifier-primary
J("spring-java-qualifier-primary", "Java: choose the bean with @Qualifier, @Primary and the parameter name", "Medium", "Spring container (Java)",
  r"""
When several beans fit an injection point, Spring follows a fixed decision procedure. Implement it with real Java
types (lesson [Circular dependencies, @Primary and @Qualifier](#/lesson/spring/spring-circular-primary-qualifier)).

`static String resolve(List<Candidate> beans, Class<?> wanted, String qualifier, String parameterName)` returns the
**name** of the bean to inject. `Candidate(name, type, primary)` is given; `qualifier` is `null` when there is no
`@Qualifier`.

1. **Candidates** are the beans with `wanted.isAssignableFrom(type)`, in list order.
2. If `qualifier != null`: return the candidate whose name equals it (primary is ignored). None →
   `NoSuchBeanDefinitionException("No qualifying bean of type '<Wanted>' available: qualifier '<q>'")`.
3. No candidates → `NoSuchBeanDefinitionException("No qualifying bean of type '<Wanted>' available")`.
4. Exactly one candidate → its name.
5. Several: if exactly one is primary → it. More than one primary →
   `NoUniqueBeanDefinitionException("more than one 'primary' bean found among candidates: [a, b]")` (names in
   list order, formatted like `List.toString()`).
6. No primary: a candidate whose name equals `parameterName` → it (Spring's fallback match by parameter name).
7. Otherwise `NoUniqueBeanDefinitionException("No qualifying bean of type '<Wanted>' available: expected single matching bean but found <n>: a,b,c")`.

`<Wanted>` is `wanted.getSimpleName()`.

**Example** three `Notifier` beans, `smsNotifier` primary, no qualifier → `"smsNotifier"`; with
`qualifier = "pushNotifier"` → `"pushNotifier"`.
""" + JUDGE_NOTE,
  _QP_START, _QP_SOL,
  [r'''eq(Solution.resolve(beans(""), Clock.class, null, "clock"), "clock")''',
   r'''thrownMsg(Solution.NoUniqueBeanDefinitionException.class, "No qualifying bean of type 'Notifier' available: expected single matching bean but found 3: emailNotifier,smsNotifier,pushNotifier", () -> Solution.resolve(beans(""), Notifier.class, null, "notifier"))''',
   r'''eq(Solution.resolve(beans("smsNotifier"), Notifier.class, null, "notifier"), "smsNotifier")''',
   r'''eq(Solution.resolve(beans("smsNotifier"), Notifier.class, "pushNotifier", "notifier"), "pushNotifier")''',
   r'''thrownMsg(Solution.NoSuchBeanDefinitionException.class, "No qualifying bean of type 'Notifier' available: qualifier 'faxNotifier'", () -> Solution.resolve(beans(""), Notifier.class, "faxNotifier", "notifier"))''',
   r'''thrownMsg(Solution.NoUniqueBeanDefinitionException.class, "more than one 'primary' bean found among candidates: [smsNotifier, pushNotifier]", () -> Solution.resolve(beans("smsNotifier,pushNotifier"), Notifier.class, null, "notifier"))''',
   r'''eq(Solution.resolve(beans(""), Notifier.class, null, "emailNotifier"), "emailNotifier")''',
   r'''eq(Solution.resolve(beans("smsNotifier"), Notifier.class, null, "emailNotifier"), "smsNotifier")''',
   r'''thrownMsg(Solution.NoSuchBeanDefinitionException.class, "No qualifying bean of type 'Runnable' available", () -> Solution.resolve(beans(""), Runnable.class, null, "task"))''',
   r'''{ List<Solution.Candidate> b = List.of(new Solution.Candidate("baseRepo", BaseRepo.class, false), new Solution.Candidate("jpaRepo", JpaRepo.class, true)); return eq(Solution.resolve(b, BaseRepo.class, null, "repo") + " " + Solution.resolve(b, JpaRepo.class, null, "repo"), "jpaRepo jpaRepo"); }''',
   r'''thrown(Solution.NoSuchBeanDefinitionException.class, () -> Solution.resolve(beans(""), Notifier.class, "clock", "notifier"))''',
   r'''thrownWith(Solution.NoUniqueBeanDefinitionException.class, "found 3", () -> Solution.resolve(beans("clock"), Notifier.class, null, "x"))''',
   r'''thrown(Solution.NoSuchBeanDefinitionException.class, () -> Solution.resolve(beans(""), Clock.class, "systemClock", "clock"))''',
   r'''eq(Solution.resolve(beans(""), Object.class, "clock", "x"), "clock")'''],
  [mut(_QP_SOL, "        if (primaries.size() == 1) return primaries.get(0);\n",
       "        for (Candidate c : candidates) {\n            if (c.name().equals(parameterName)) return c.name();\n        }\n        if (primaries.size() == 1) return primaries.get(0);\n"),
   mut(_QP_SOL, "            for (Candidate c : candidates) {\n                if (c.name().equals(qualifier)) return c.name();",
       "            for (Candidate c : beans) {\n                if (c.name().equals(qualifier)) return c.name();")],
  G("Lesson [Circular dependencies, @Primary and @Qualifier](#/lesson/spring/spring-circular-primary-qualifier). Java: `Class.isAssignableFrom`, records.",
    "Narrow first, then decide. The type filter always applies; a qualifier is a hard requirement on top of it; only when several beans remain do primary and then the parameter name break the tie.",
    ["`wanted.isAssignableFrom(c.type())` reads as: can a `c.type()` be stored in a variable of type `wanted`?",
     "Handle the qualifier before counting candidates: with a qualifier, one candidate with the wrong name is still an error.",
     "Collect primary names into a list; its size (0, 1, more) drives the next step."],
    "Trying every rule on the full bean list (ignoring types) gives wrong answers when a qualifier names a bean of another type.",
    r"""Steps in order: filter by type → qualifier → empty? → single? → primaries → parameter name → not unique.

**Dry run** `beans("smsNotifier")`, wanted `Notifier`, no qualifier, parameter `emailNotifier`: candidates are the three notifiers (the clock is filtered out). Several remain, primaries = `[smsNotifier]`, size 1 → `"smsNotifier"`. The parameter name is never consulted because `@Primary` already decided.

In Spring code this corresponds to:

```java
@Service
class AlertService {
    AlertService(@Qualifier("pushNotifier") Notifier n) { ... }   // rule 2
}
@Bean @Primary Notifier smsNotifier() { ... }                     // rule 5
AlertService(Notifier emailNotifier) { ... }                       // rule 6 (needs -parameters, on by default in Boot)
```""",
    "O(B) for B beans.",
    "- Letting the parameter name override `@Primary` (it is only a fallback).\n- Applying the qualifier before the type filter.\n- Treating a primary bean of another type as relevant.",
    "Spring 6.2 adds `@Fallback` (the opposite of `@Primary`) and also considers `@Priority`; both slot in between rules 5 and 6."),
  extra=_QP_EXTRA),

# ------------------------------------------------------------------ spring-java-lifecycle
J("spring-java-lifecycle", "Java: bean lifecycle callbacks and post-processors", "Medium", "Bean lifecycle (Java)",
  r"""
Implement the lifecycle a Spring context runs for every singleton (lesson
[Prototype scope and the bean lifecycle](#/lesson/spring/spring-prototype-lifecycle)): construct, post-process,
initialise, post-process again, and on shutdown destroy in reverse order.

The interfaces `InitializingBean`, `DisposableBean`, `BeanPostProcessor` and `BeanCreationException` are given.
Complete `LifecycleContext`:

- `register(String name, Supplier<Object> factory)`; `addBeanPostProcessor(BeanPostProcessor p)`.
- `refresh()` — for each bean in registration order:
  1. `raw = factory.get()` (the constructor);
  2. `bean = raw`, then for every processor in the order added: `bean = p.postProcessBeforeInitialization(bean, name)`
     (a `null` result keeps the previous `bean`);
  3. if `bean` is an `InitializingBean`, call `afterPropertiesSet()` on it;
  4. for every processor: `bean = p.postProcessAfterInitialization(bean, name)` (again ignoring `null`);
  5. `getBean(name)` will return this final `bean` (it may be a wrapper, like an AOP proxy).
- If step 1 or 3 throws, destroy the beans created so far (as `close()` does) and throw
  `BeanCreationException("Error creating bean with name '<name>'", cause)`. Later beans are not created.
- `close()` — destroy in **reverse creation order**: call `destroy()` on each **raw** object that is a
  `DisposableBean` (Spring registers the raw instance, not the proxy). If a `destroy()` throws, ignore it and carry
  on. A second `close()` does nothing.
- `getBean(name)` — unknown → `NoSuchElementException`; after `close()` → `IllegalStateException`.
""" + JUDGE_NOTE,
  _LC_START, _LC_SOL,
  [r'''{ var c = ctx(); c.register("a", () -> new Tracked("a")); c.refresh(); c.close(); return eq(LOG, List.of("new a", "init a", "destroy a")); }''',
   r'''{ var c = ctx(); c.addBeanPostProcessor(new Tagging("p1")); c.addBeanPostProcessor(new Tagging("p2")); c.register("a", () -> new Tracked("a")); c.register("b", Plain::new); c.refresh(); return eq(LOG, List.of("new a", "p1 before a", "p2 before a", "init a", "p1 after a", "p2 after a", "new plain", "p1 before b", "p2 before b", "p1 after b", "p2 after b")); }''',
   r'''{ var c = ctx(); c.register("a", () -> new Tracked("a")); c.register("b", () -> new Tracked("b")); c.register("c", () -> new Tracked("c")); c.refresh(); LOG.clear(); c.close(); return eq(LOG, List.of("destroy c", "destroy b", "destroy a")); }''',
   r'''{ var c = ctx(); c.register("p", Plain::new); c.refresh(); c.close(); return eq(LOG, List.of("new plain")); }''',
   r'''{ var c = ctx(); c.addBeanPostProcessor(new Solution.BeanPostProcessor() { public Object postProcessAfterInitialization(Object bean, String name) { return new Wrapper(bean); } }); c.register("a", () -> new Tracked("a")); c.refresh(); Object got = c.getBean("a"); LOG.clear(); c.close(); return yes(got instanceof Wrapper w && w.inner instanceof Tracked && LOG.equals(List.of("destroy a")), "getBean returns the wrapper and close() destroys the raw bean; log " + LOG); }''',
   r'''{ var c = ctx(); c.register("a", () -> new Tracked("a")); c.register("bad", BadInit::new); c.register("c", () -> new Tracked("c")); try { c.refresh(); return "refresh() should throw"; } catch (Solution.BeanCreationException e) { if (!"Error creating bean with name 'bad'".equals(e.getMessage())) return "message " + e.getMessage(); if (e.getCause() == null || !"boom".equals(e.getCause().getMessage())) return "cause should be the init exception, got " + e.getCause(); return eq(LOG, List.of("new a", "init a", "new bad", "destroy a")); } }''',
   r'''{ var c = ctx(); c.register("a", () -> new Tracked("a")); c.register("bad", BadDestroy::new); c.register("c", () -> new Tracked("c")); c.refresh(); LOG.clear(); c.close(); return eq(LOG, List.of("destroy c", "destroy bad", "destroy a")); }''',
   r'''{ var c = ctx(); c.register("a", () -> new Tracked("a")); c.refresh(); c.close(); c.close(); return eq(LOG, List.of("new a", "init a", "destroy a")); }''',
   r'''{ var c = ctx(); c.register("a", () -> new Tracked("a")); c.refresh(); c.close(); return thrown(IllegalStateException.class, () -> c.getBean("a")); }''',
   r'''{ var c = ctx(); c.addBeanPostProcessor(new Solution.BeanPostProcessor() { public Object postProcessBeforeInitialization(Object bean, String name) { return null; } }); c.register("a", () -> new Tracked("a")); c.refresh(); return yes(c.getBean("a") instanceof Tracked && LOG.equals(List.of("new a", "init a")), "a null from a post-processor keeps the bean; log " + LOG); }''',
   r'''{ var c = ctx(); c.register("a", () -> new Tracked("a")); c.register("x", () -> { throw new IllegalStateException("no db"); }); try { c.refresh(); return "refresh() should throw"; } catch (Solution.BeanCreationException e) { return e.getCause() instanceof IllegalStateException && "Error creating bean with name 'x'".equals(e.getMessage()) ? eq(LOG, List.of("new a", "init a", "destroy a")) : "got " + e.getMessage() + " / " + e.getCause(); } }''',
   r'''{ var c = ctx(); c.register("a", () -> new Tracked("a")); c.refresh(); return thrown(NoSuchElementException.class, () -> c.getBean("b")); }''',
   r'''{ var c = ctx(); c.addBeanPostProcessor(new Solution.BeanPostProcessor() { public Object postProcessBeforeInitialization(Object bean, String name) { return new Tracked("swapped"); } }); c.register("a", () -> new Tracked("a")); c.refresh(); c.close(); return eq(LOG, List.of("new a", "new swapped", "init swapped", "destroy a")); }'''],
  [mut(_LC_SOL, "for (int i = createdRaw.size() - 1; i >= 0; i--) {", "for (int i = 0; i < createdRaw.size(); i++) {"),
   mut(_LC_SOL, "                    Object bean = raw;\n", "                    Object bean = raw;\n                    if (bean instanceof InitializingBean early) early.afterPropertiesSet();\n").replace(
       "                    if (bean instanceof InitializingBean ib) ib.afterPropertiesSet();\n", ""),
   mut(_LC_SOL, "                    try {\n                        d.destroy();\n                    } catch (Exception ignored) {\n                        // Spring logs the failure and carries on with the other beans\n                    }",
       "                    try {\n                        d.destroy();\n                    } catch (Exception e) {\n                        return;\n                    }")],
  G("Lesson [Prototype scope and the bean lifecycle](#/lesson/spring/spring-prototype-lifecycle). Java: interfaces with default methods, `instanceof` patterns, `Supplier`.",
    "The lifecycle is a fixed pipeline per bean plus a stack for shutdown: whatever was created last depends on things created earlier, so it must be destroyed first.",
    ["Keep the raw objects in a list in creation order; `close()` walks it backwards.",
     "Track `bean` (what the processors return) separately from `raw` (what the factory returned).",
     "Wrap the whole per-bean pipeline in one try/catch: on failure call `close()` (which destroys what exists so far) and throw `BeanCreationException` with the cause."],
    "Calling `afterPropertiesSet()` straight after construction ignores post-processors that must run before initialisation (in Spring, `@PostConstruct` itself is run by such a processor).",
    r"""```java
Object raw = factory.get();
Object bean = raw;
for (BeanPostProcessor p : processors) { Object r = p.postProcessBeforeInitialization(bean, name); if (r != null) bean = r; }
if (bean instanceof InitializingBean ib) ib.afterPropertiesSet();
for (BeanPostProcessor p : processors) { Object r = p.postProcessAfterInitialization(bean, name); if (r != null) bean = r; }
exposed.put(name, bean);     // what getBean returns (maybe a proxy)
createdRaw.add(raw);         // what close() destroys
```

**Dry run** of the failure case: `a` is created and initialised; `bad` is constructed, its `afterPropertiesSet()` throws; `close()` destroys `a`; `c` never starts. Log `[new a, init a, new bad, destroy a]`.

The full Spring order for one bean is: constructor → dependency injection → `Aware` callbacks → `postProcessBeforeInitialization` (this runs `@PostConstruct`) → `afterPropertiesSet()` → custom `initMethod` → `postProcessAfterInitialization` (AOP proxies are created here). Shutdown: `@PreDestroy` → `destroy()` → custom `destroyMethod`.""",
    "O(B · P) for B beans and P post-processors.",
    "- Destroying in creation order.\n- Letting one failing `destroy()` stop the others.\n- Calling `destroy()` on the proxy returned by a post-processor.\n- Forgetting that Spring does **not** call destroy callbacks on prototype beans.",
    "AOP proxies are created in `postProcessAfterInitialization`, which is why `@PostConstruct` code runs on the raw object and is not intercepted by `@Transactional`."),
  extra=_LC_EXTRA),

# ------------------------------------------------------------------ spring-java-jdk-proxy
J("spring-java-jdk-proxy", "Java: a logging aspect with java.lang.reflect.Proxy", "Easy", "Spring AOP (Java)",
  r"""
Spring AOP never changes your class. It hands out a **proxy**: an object that implements the same interface,
runs advice, and forwards to the real object. For interface-based beans that proxy is a JDK dynamic proxy, the
exact class you will use here (lesson [How Spring AOP works: proxies and your first aspect](#/lesson/spring/spring-aop-proxies)).

Write `static <T> T loggingProxy(T target, Class<T> iface, List<String> log)` that returns a
`java.lang.reflect.Proxy` implementing `iface`:

- For each call of a method declared by the interface: append `"before <method>"`, call the target, then append
  either `"after <method> returned <value>"` (`String.valueOf` of the result, `null` for `void`) or
  `"after <method> threw <ExceptionSimpleName>"`.
- An exception from the target must reach the caller **unchanged** (same type, same object). `Method.invoke`
  wraps it in an `InvocationTargetException`: unwrap it with `getCause()`.
- Methods inherited from `Object` (`toString`, `hashCode`, `equals`) go straight to the target, without logging.
- If `iface` is not an interface, `Proxy.newProxyInstance` throws `IllegalArgumentException`; let it propagate.

**Example**

```java
Calculator c = Solution.loggingProxy(new SimpleCalculator(), Calculator.class, log);
c.add(2, 3);        // 5; log = [before add, after add returned 5]
```
""" + JUDGE_NOTE,
  _PX_START, _PX_SOL,
  [r'''{ List<String> log = new ArrayList<>(); Calculator c = Solution.loggingProxy(new SimpleCalculator(), Calculator.class, log); int r = c.add(2, 3); return r != 5 ? "add returned " + r : eq(log, List.of("before add", "after add returned 5")); }''',
   r'''{ List<String> log = new ArrayList<>(); Calculator c = Solution.loggingProxy(new SimpleCalculator(), Calculator.class, log); try { c.divide(1, 0); return "expected ArithmeticException"; } catch (ArithmeticException e) { return eq(log, List.of("before divide", "after divide threw ArithmeticException")); } }''',
   r'''{ List<String> log = new ArrayList<>(); Calculator c = Solution.loggingProxy(new SimpleCalculator(), Calculator.class, log); c.reset(); return eq(log, List.of("before reset", "after reset returned null")); }''',
   r'''{ List<String> log = new ArrayList<>(); Calculator c = Solution.loggingProxy(new SimpleCalculator(), Calculator.class, log); try { c.describe(); return "expected IOException"; } catch (java.io.IOException e) { return eq(e.getMessage() + " " + log, "disk [before describe, after describe threw IOException]"); } }''',
   r'''{ List<String> log = new ArrayList<>(); Calculator c = Solution.loggingProxy(new SimpleCalculator(), Calculator.class, log); return eq(c.toString() + log, "SimpleCalculator[]"); }''',
   r'''{ Calculator c = Solution.loggingProxy(new SimpleCalculator(), Calculator.class, new ArrayList<>()); return yes(java.lang.reflect.Proxy.isProxyClass(c.getClass()) && !(c instanceof SimpleCalculator), "the result must be a JDK proxy, not the target itself"); }''',
   r'''{ List<String> log = new ArrayList<>(); Calculator c = Solution.loggingProxy(new SimpleCalculator(), Calculator.class, log); c.add(1, 1); c.add(2, 2); return eq(log, List.of("before add", "after add returned 2", "before add", "after add returned 4")); }''',
   r'''thrown(IllegalArgumentException.class, () -> Solution.loggingProxy(new SimpleCalculator(), SimpleCalculator.class, new ArrayList<>()))''',
   r'''{ List<String> log = new ArrayList<>(); SimpleCalculator target = new SimpleCalculator(); Calculator c = Solution.loggingProxy(target, Calculator.class, log); return yes(c.hashCode() == target.hashCode() && log.isEmpty(), "hashCode goes to the target without logging"); }''',
   r'''{ List<String> a = new ArrayList<>(); List<String> b = new ArrayList<>(); Calculator x = Solution.loggingProxy(new SimpleCalculator(), Calculator.class, a); Calculator y = Solution.loggingProxy(new SimpleCalculator(), Calculator.class, b); x.add(1, 2); return eq(a.size() + "/" + b.size(), "2/0"); }''',
   r'''{ List<String> log = new ArrayList<>(); Calculator c = Solution.loggingProxy(new SimpleCalculator(), Calculator.class, log); RuntimeException seen = null; try { c.divide(5, 0); } catch (RuntimeException e) { seen = e; } return yes(seen != null && seen.getClass() == ArithmeticException.class, "the caller must see the original ArithmeticException, got " + seen); }'''],
  [mut(_PX_SOL, "                throw cause;", "                throw e;"),
   mut(_PX_SOL, "            if (method.getDeclaringClass() == Object.class) {", "            if (method.getDeclaringClass() == Void.class) {")],
  G("Lesson [How Spring AOP works: proxies and your first aspect](#/lesson/spring/spring-aop-proxies). Java: interfaces, lambdas, checked versus unchecked exceptions.",
    "A JDK proxy routes **every** call on the interface to one `InvocationHandler`. Your handler is the aspect: it decides what to do before and after forwarding with `method.invoke(target, args)`.",
    ["`Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[] { iface }, handler)` creates the proxy; `iface.cast(...)` gives it the right static type.",
     "`method.getDeclaringClass() == Object.class` identifies `toString`, `equals` and `hashCode`.",
     "Catch `InvocationTargetException` and `throw e.getCause()`; the handler may throw any `Throwable`."],
    "Writing a hand-made `LoggingCalculator implements Calculator` class works for one interface. A dynamic proxy does it for any interface at run time, which is what a framework needs.",
    r"""```java
InvocationHandler handler = (proxy, method, args) -> {
    if (method.getDeclaringClass() == Object.class) { /* forward, unwrap */ }
    log.add("before " + method.getName());
    try {
        Object result = method.invoke(target, args);
        log.add("after " + method.getName() + " returned " + result);
        return result;
    } catch (InvocationTargetException e) {
        Throwable cause = e.getCause();
        log.add("after " + method.getName() + " threw " + cause.getClass().getSimpleName());
        throw cause;
    }
};
```

**Why unwrapping matters.** If the handler rethrows the `InvocationTargetException` itself, it is a checked exception that `add` does not declare, so the proxy wraps it once more in `UndeclaredThrowableException`. The caller's `catch (ArithmeticException e)` then misses it. Spring's `AopUtils.invokeJoinpointUsingReflection` does exactly this unwrapping.

The Spring version of this exercise is a few lines:

```java
@Aspect @Component
class LoggingAspect {
    @Around("execution(* com.shop..*Calculator.*(..))")
    Object log(ProceedingJoinPoint pjp) throws Throwable { ... pjp.proceed() ... }
}
```""",
    "O(1) overhead per call (plus reflection cost).",
    "- Rethrowing `InvocationTargetException`.\n- Logging `toString`/`hashCode` calls (debuggers and collections call them constantly).\n- Returning the target instead of the proxy.\n- Passing a class instead of an interface: classes need a subclassing proxy (CGLIB, which Spring Boot uses by default).",
    "Spring Boot defaults to CGLIB class proxies (`spring.aop.proxy-target-class=true`), which subclass your bean; the self-invocation trap is the same for both kinds."),
  extra=_PX_EXTRA),

# ------------------------------------------------------------------ spring-java-advice-chain
J("spring-java-advice-chain", "Java: an ordered chain of before, after and around advice", "Hard", "Spring AOP (Java)",
  r"""
When several aspects apply to one method, Spring builds a **chain of interceptors** ordered by `@Order`: the lowest
number is the outermost. Every advice type is really an *around* advice in disguise. Build that chain on top of a JDK
proxy (lesson [Advice types, pointcut expressions and aspect order](#/lesson/spring/spring-aop-advice-pointcuts)).

Given: `Invocation { String methodName(); Object proceed() throws Throwable; }`,
`Advice { Object invoke(Invocation inv) throws Throwable; }` and `record OrderedAdvice(int order, Advice advice)`.

Write the four advice factories, each returning an `Advice`:

| factory | behaviour |
|---|---|
| `before(Consumer<String> action)` | `action.accept(methodName)`, then proceed |
| `afterReturning(BiConsumer<String, Object> action)` | proceed; on normal return `action.accept(methodName, result)`, return the result |
| `afterThrowing(BiConsumer<String, Throwable> action)` | proceed; if it throws, `action.accept(methodName, ex)` and rethrow the same exception |
| `after(Consumer<String> action)` | proceed; **always** run `action.accept(methodName)` afterwards (a `finally`) |

and `static <T> T proxy(T target, Class<T> iface, List<OrderedAdvice> advices)`:

- Sort a **copy** of the list by `order` ascending; equal orders keep their list order. Do not modify the argument.
- A call to an interface method runs advice 0, whose `proceed()` runs advice 1, and so on; the last `proceed()`
  calls the target. Exceptions from the target reach advice (and finally the caller) unwrapped.
- `proceed()` may be called **more than once** (a retry advice) or **not at all** (a cache advice). Each call must
  run the rest of the chain again from the next advice. (Spring's own `MethodInvocation` keeps a cursor and needs
  `invocableClone()` for that; give each level its own `Invocation` instead.)
- `Object` methods (`toString`, ...) bypass the advice.

**Example** orders 1 around (logs in/out), 2 before, 3 afterReturning, 4 after, method returns normally:
`[outer in, before greet, target bob, after greet, returned greet hi bob, outer out]`. Note `after` (order 4) runs
before `afterReturning` (order 3): it is further in.
""" + JUDGE_NOTE,
  _AC_START, _AC_SOL,
  [r'''{ List<String> log = new ArrayList<>(); Greeter p = Solution.proxy(new Target(log, 0), Greeter.class, List.of(at(1, around("outer", log)), at(2, Solution.before(m -> log.add("before " + m))), at(3, Solution.afterReturning((m, r) -> log.add("returned " + m + " " + r))), at(4, Solution.after(m -> log.add("after " + m))))); String r = p.greet("bob"); return r.equals("hi bob") ? eq(log, List.of("outer in", "before greet", "target bob", "after greet", "returned greet hi bob", "outer out")) : "returned " + r; }''',
   r'''{ List<String> log = new ArrayList<>(); Greeter p = Solution.proxy(new Target(log, 0), Greeter.class, List.of(at(5, around("inner", log)), at(1, around("outer", log)))); p.greet("bob"); return eq(log, List.of("outer in", "inner in", "target bob", "inner out", "outer out")); }''',
   r'''{ List<String> log = new ArrayList<>(); Greeter p = Solution.proxy(new Target(log, 0), Greeter.class, List.of(at(2, around("first", log)), at(2, around("second", log)), at(1, around("zero", log)))); p.greet("x"); return eq(log, List.of("zero in", "first in", "second in", "target x", "second out", "first out", "zero out")); }''',
   r'''{ List<String> log = new ArrayList<>(); Greeter p = Solution.proxy(new Target(log, 0), Greeter.class, List.of(at(1, Solution.afterThrowing((m, e) -> log.add("threw " + m + " " + e.getClass().getSimpleName()))), at(2, Solution.after(m -> log.add("after " + m))), at(3, Solution.afterReturning((m, r) -> log.add("returned " + m))))); try { p.greet(""); return "expected IllegalArgumentException"; } catch (IllegalArgumentException e) { return eq(log, List.of("target ", "after greet", "threw greet IllegalArgumentException")); } }''',
   r'''{ List<String> log = new ArrayList<>(); Solution.Advice fallback = inv -> { try { return inv.proceed(); } catch (IllegalArgumentException e) { log.add("recovered"); return "fallback"; } }; Greeter p = Solution.proxy(new Target(log, 0), Greeter.class, List.of(at(0, Solution.afterReturning((m, r) -> log.add("returned " + m + " " + r))), at(1, fallback), at(2, Solution.afterThrowing((m, e) -> log.add("threw " + m))))); String r = p.greet(""); return eq(r + " " + log, "fallback [target , threw greet, recovered, returned greet fallback]"); }''',
   r'''{ List<String> log = new ArrayList<>(); Greeter p = Solution.proxy(new Target(log, 0), Greeter.class, List.of(at(1, inv -> ((String) inv.proceed()).toUpperCase()))); return eq(p.greet("bob"), "HI BOB"); }''',
   r'''{ List<String> log = new ArrayList<>(); Solution.Advice retry = inv -> { try { return inv.proceed(); } catch (IllegalStateException e) { log.add("retry"); return inv.proceed(); } }; Greeter p = Solution.proxy(new Target(log, 1), Greeter.class, List.of(at(1, retry), at(2, Solution.before(m -> log.add("before " + m))))); String r = p.greet("bob"); return eq(r + " " + log, "hi bob [before greet, target bob, retry, before greet, target bob]"); }''',
   r'''{ List<String> log = new ArrayList<>(); Target t = new Target(log, 0); Greeter p = Solution.proxy(t, Greeter.class, List.of(at(1, inv -> "cached"), at(2, Solution.before(m -> log.add("before " + m))))); return eq(p.greet("bob") + " " + log + " " + t.calls, "cached [] 0"); }''',
   r'''{ List<String> log = new ArrayList<>(); Greeter p = Solution.proxy(new Target(log, 0), Greeter.class, List.of(at(1, Solution.before(m -> log.add("before " + m))))); try { p.load(); return "expected IOException"; } catch (java.io.IOException e) { return eq(e.getMessage() + " " + log, "disk [before load]"); } }''',
   r'''{ List<String> log = new ArrayList<>(); Greeter p = Solution.proxy(new Target(log, 0), Greeter.class, List.of(at(1, around("outer", log)))); return eq(p.toString() + log, "Target[]"); }''',
   r'''{ List<String> log = new ArrayList<>(); Greeter p = Solution.proxy(new Target(log, 0), Greeter.class, List.of()); return eq(p.greet("amy") + " " + log, "hi amy [target amy]"); }''',
   r'''{ List<String> log = new ArrayList<>(); List<Solution.OrderedAdvice> list = new ArrayList<>(List.of(at(9, around("a", log)), at(1, around("b", log)))); Solution.proxy(new Target(log, 0), Greeter.class, list); return eq(list.get(0).order() + "," + list.get(1).order(), "9,1"); }''',
   r'''{ List<String> log = new ArrayList<>(); Greeter p = Solution.proxy(new Target(log, 0), Greeter.class, List.of(at(1, Solution.after(m -> log.add("after1"))), at(2, Solution.afterThrowing((m, e) -> log.add("threw2"))))); try { p.greet(""); return "expected exception"; } catch (IllegalArgumentException e) { return eq(log, List.of("target ", "threw2", "after1")); } }'''],
  [mut(_AC_SOL, "sorted.sort(Comparator.comparingInt(OrderedAdvice::order));", "sorted.sort(Comparator.comparingInt(OrderedAdvice::order).reversed());"),
   mut(_AC_SOL, r'''        InvocationHandler handler = (p, method, args) -> {
            if (method.getDeclaringClass() == Object.class) return callTarget(target, method, args);
            return chain(sorted, 0, target, method, args);
        };''', _AC_CURSOR),
   mut(_AC_SOL, "            } finally {\n                action.accept(inv.methodName());\n            }",
       "            } catch (Throwable t) {\n                throw t;\n            }")],
  G("Lessons [How Spring AOP works](#/lesson/spring/spring-aop-proxies) and [Advice types, pointcut expressions and aspect order](#/lesson/spring/spring-aop-advice-pointcuts). The `spring-java-jdk-proxy` exercise.",
    "Every advice type is an around advice with a fixed shape: `before` = act, then proceed; `afterReturning` = proceed, then act; `afterThrowing` = proceed inside try/catch; `after` = proceed inside try/finally. Ordering is then nothing more than nesting: advice *i* calls advice *i + 1* through `proceed()`.",
    ["Write `chain(advices, i, target, method, args)`: if `i == size` call the target, otherwise create an `Invocation` whose `proceed()` calls `chain(..., i + 1, ...)` and pass it to advice `i`.",
     "Because each `Invocation` object fixes its own `i`, calling `proceed()` twice replays the remaining chain: retries work for free.",
     "`List.sort` is stable, so `Comparator.comparingInt(OrderedAdvice::order)` keeps equal orders in list order."],
    "A shared index (a cursor) that `proceed()` increments is the obvious design and is how Spring's `ReflectiveMethodInvocation` works. It breaks retries: the second `proceed()` finds the cursor at the end and jumps straight to the target, skipping inner advice.",
    r"""```java
private static Object chain(List<OrderedAdvice> advices, int i, Object target, Method method, Object[] args) throws Throwable {
    if (i == advices.size()) return callTarget(target, method, args);
    Invocation invocation = new Invocation() {
        public String methodName() { return method.getName(); }
        public Object proceed() throws Throwable { return chain(advices, i + 1, target, method, args); }
    };
    return advices.get(i).advice().invoke(invocation);
}
```

**Dry run** of the example: around(1) logs `outer in` → before(2) logs `before greet` → afterReturning(3) proceeds → after(4) proceeds → target logs `target bob` and returns → after(4)'s `finally` logs `after greet` → afterReturning(3) logs `returned greet hi bob` → around(1) logs `outer out`.

Inside **one** `@Aspect` class Spring 5.3+ orders advice types as around, before, after, afterReturning, afterThrowing on the way in; across aspects, `@Order` decides, exactly as here.""",
    "O(A) extra calls per invocation for A advices.",
    "- Highest order outermost (it is the lowest).\n- `after` implemented with `catch` instead of `finally`, so it is skipped on success.\n- Swallowing the exception in `afterThrowing`.\n- Sorting the caller's list in place.",
    "Spring Retry's `@Retryable` and Resilience4j's annotations are exactly around advices that call `proceed()` several times; that is why their `@Order` relative to `@Transactional` matters (retry should be outside the transaction so each attempt gets a fresh one)."),
  extra=_AC_EXTRA),

# ------------------------------------------------------------------ spring-java-self-invocation
J("spring-java-self-invocation", "Java: the self-invocation trap and AopContext.currentProxy()", "Medium", "Spring AOP (Java)",
  r"""
A Spring proxy only sees calls that **go through the proxy**. When a bean method calls another method of the same
bean with `this.other()`, the call goes straight to the raw object and the advice (for example `@Transactional`)
is silently skipped (lessons [How Spring AOP works](#/lesson/spring/spring-aop-proxies) and
[@Transactional, rollback rules and the self-invocation pitfall](#/lesson/spring/spring-transactional)).
One documented way out is `@EnableAspectJAutoProxy(exposeProxy = true)` plus `AopContext.currentProxy()`.

Implement both sides:

`static <T> T transactionalProxy(T target, Class<T> iface, Set<String> transactionalMethods, List<String> log)` returns
a JDK proxy that:

- for a method whose name is in `transactionalMethods`: logs `"begin <m>"`, calls the target, then logs
  `"commit <m>"`, or `"rollback <m>"` if it threw (rethrow the original exception, unwrapped);
- for other interface methods: calls the target with no logging;
- for `Object` methods: calls the target directly;
- **while any interface method runs** (transactional or not), makes `currentProxy()` return *this proxy*.

`static Object currentProxy()` returns the proxy whose method is currently executing. Calls can nest (a method of
proxy A calls proxy B): inside B it returns B, and after B returns, A again. Outside any proxy call it throws
`IllegalStateException`. Use a `ThreadLocal`, as Spring does, and restore the **previous** value when a call ends,
even if it threw.

The test service calls `this.saveAudit()` from `placeOrder()` (no transaction starts) and
`((OrderService) Solution.currentProxy()).saveAudit()` from `placeOrderFixed()` (a transaction starts).
""" + JUDGE_NOTE,
  _SI_START, _SI_SOL,
  [r'''{ List<String> log = new ArrayList<>(); svc(log, "saveAudit").placeOrder(); return eq(log, List.of("placeOrder body", "saveAudit body")); }''',
   r'''{ List<String> log = new ArrayList<>(); svc(log, "saveAudit").placeOrderFixed(); return eq(log, List.of("placeOrderFixed body", "begin saveAudit", "saveAudit body", "commit saveAudit")); }''',
   r'''{ List<String> log = new ArrayList<>(); svc(log, "saveAudit").saveAudit(); return eq(log, List.of("begin saveAudit", "saveAudit body", "commit saveAudit")); }''',
   r'''thrown(IllegalStateException.class, () -> Solution.currentProxy())''',
   r'''{ List<String> log = new ArrayList<>(); svc(log, "saveAudit").placeOrderFixed(); return thrown(IllegalStateException.class, () -> Solution.currentProxy()); }''',
   r'''{ List<String> log = new ArrayList<>(); OrderService s = svc(log, "fail"); try { s.fail(); return "expected IllegalStateException"; } catch (IllegalStateException e) { if (!"no stock".equals(e.getMessage())) return "wrong exception " + e; } String after = thrown(IllegalStateException.class, () -> Solution.currentProxy()); return after != null ? "after a failed call: " + after : eq(log, List.of("begin fail", "fail body", "rollback fail")); }''',
   r'''{ NamedImpl a = new NamedImpl("a"); NamedImpl b = new NamedImpl("b"); Named pa = Solution.transactionalProxy(a, Named.class, Set.of(), new ArrayList<>()); Named pb = Solution.transactionalProxy(b, Named.class, Set.of(), new ArrayList<>()); a.self = pa; b.self = pb; a.other = pb; return eq(pa.callOther(), "b+,a+"); }''',
   r'''{ List<String> log = new ArrayList<>(); svc(log, "placeOrderFixed", "saveAudit").placeOrderFixed(); return eq(log, List.of("begin placeOrderFixed", "placeOrderFixed body", "begin saveAudit", "saveAudit body", "commit saveAudit", "commit placeOrderFixed")); }''',
   r'''{ List<String> log = new ArrayList<>(); OrderService s = svc(log, "saveAudit", "toString"); return eq(s.toString() + log, "impl[]"); }''',
   r'''{ List<String> log = new ArrayList<>(); OrderService s = svc(log, "saveAudit"); s.placeOrder(); s.placeOrderFixed(); return eq(log, List.of("placeOrder body", "saveAudit body", "placeOrderFixed body", "begin saveAudit", "saveAudit body", "commit saveAudit")); }'''],
  [mut(_SI_SOL, "            CURRENT.set(proxy);", "            CURRENT.set(target);"),
   mut(_SI_SOL, "                if (previous == null) CURRENT.remove(); else CURRENT.set(previous);", "                CURRENT.remove();"),
   mut(_SI_SOL, "                if (!transactionalMethods.contains(name)) return invokeTarget(target, method, args);\n", "")],
  G("Lessons [How Spring AOP works](#/lesson/spring/spring-aop-proxies) and [@Transactional and the self-invocation pitfall](#/lesson/spring/spring-transactional). The `spring-java-jdk-proxy` exercise.",
    "`this` inside the target is the raw object, never the proxy. Advice can only run if the call is made on the proxy reference, so the fix is to get hold of that reference: inject it, or ask a thread-local holder that the proxy fills in while it runs.",
    ["The handler's first parameter `proxy` is the proxy object itself: store it in the `ThreadLocal`.",
     "Save `previous = CURRENT.get()` before setting, and restore it in `finally` (use `remove()` when it was `null`).",
     "Only the logging depends on `transactionalMethods`; exposing the proxy happens for every interface method."],
    "Clearing the thread-local at the end of each call works until calls nest: the outer method then finds no current proxy after the inner call returns.",
    r"""```java
Object previous = CURRENT.get();
CURRENT.set(proxy);
try {
    if (!transactionalMethods.contains(name)) return invokeTarget(target, method, args);
    log.add("begin " + name);
    ... invoke, log commit or rollback ...
} finally {
    if (previous == null) CURRENT.remove(); else CURRENT.set(previous);
}
```

**Dry run** `placeOrder()` with `saveAudit` transactional: the proxy sees `placeOrder` (not transactional) and forwards. The body calls `this.saveAudit()`, a plain Java call on the raw object: no `begin`. With `placeOrderFixed()` the body asks for `currentProxy()`, gets the proxy, and calls `saveAudit()` on it: the handler runs and logs `begin`/`commit`.

Fixes in real Spring, best first: move the method to another bean; inject the bean into itself (`@Lazy @Autowired OrderService self`); use `TransactionTemplate` programmatically; or `exposeProxy = true` with `AopContext.currentProxy()` (works but couples code to Spring AOP).""",
    "O(1) per call.",
    "- Exposing the target instead of the proxy.\n- Not restoring the previous proxy after nested calls.\n- Leaving the thread-local set after an exception (a leak on pooled threads).\n- Thinking `private` or `final` methods can be advised: proxies cannot intercept them either.",
    "AspectJ load-time or compile-time weaving changes the bytecode itself, so self-invocation is advised too; that is the heavyweight alternative to proxies."),
  extra=_SI_EXTRA),
]
