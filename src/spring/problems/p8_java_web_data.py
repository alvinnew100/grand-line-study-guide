"""Spring track, REAL Java problems part 2 (judged on the server): transactions, web, validation, data access,
resilient clients and the security filter chain.

The judge has the JDK only (no Spring jars), so each exercise builds, in plain Java 21, the mechanism that Spring
provides. Helpers are loaded from p7_java_container.py so both files share one harness format.
"""
import importlib.util as _ilu
import os as _os

_spec = _ilu.spec_from_file_location("_spring_p7_helpers", _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "p7_java_container.py"))
_p7 = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_p7)
J, G, mut, JUDGE_NOTE = _p7.J, _p7.G, _p7.mut, _p7.JUDGE_NOTE

# ====================================================================================== 9. rollback rules
_RB_START = r'''import java.util.*;

class Solution {
    interface TxWork<T> { T run() throws Exception; }

    static boolean rollbackOn(Throwable ex, List<Class<? extends Throwable>> rollbackFor,
                              List<Class<? extends Throwable>> noRollbackFor) {
        // your code
        return false;
    }

    static <T> T executeInTransaction(List<String> log, TxWork<T> work, List<Class<? extends Throwable>> rollbackFor,
                                      List<Class<? extends Throwable>> noRollbackFor) throws Exception {
        // your code
        return work.run();
    }
}
'''

_RB_SOL = r'''import java.util.*;

class Solution {
    interface TxWork<T> { T run() throws Exception; }

    static boolean rollbackOn(Throwable ex, List<Class<? extends Throwable>> rollbackFor,
                              List<Class<? extends Throwable>> noRollbackFor) {
        int best = Integer.MAX_VALUE;
        Boolean decision = null;
        for (Class<? extends Throwable> rule : rollbackFor) {
            int d = depth(ex.getClass(), rule);
            if (d >= 0 && d < best) { best = d; decision = true; }
        }
        for (Class<? extends Throwable> rule : noRollbackFor) {
            int d = depth(ex.getClass(), rule);
            if (d >= 0 && d < best) { best = d; decision = false; }
        }
        if (decision != null) return decision;
        return ex instanceof RuntimeException || ex instanceof Error;
    }

    private static int depth(Class<?> type, Class<?> rule) {
        int d = 0;
        for (Class<?> c = type; c != null; c = c.getSuperclass(), d++) {
            if (c == rule) return d;
        }
        return -1;
    }

    static <T> T executeInTransaction(List<String> log, TxWork<T> work, List<Class<? extends Throwable>> rollbackFor,
                                      List<Class<? extends Throwable>> noRollbackFor) throws Exception {
        log.add("begin");
        T result;
        try {
            result = work.run();
        } catch (Throwable t) {
            log.add(rollbackOn(t, rollbackFor, noRollbackFor) ? "rollback" : "commit");
            throw t;
        }
        log.add("commit");
        return result;
    }
}
'''

_RB_FIRST_MATCH = r'''    static boolean rollbackOn(Throwable ex, List<Class<? extends Throwable>> rollbackFor,
                              List<Class<? extends Throwable>> noRollbackFor) {
        for (Class<? extends Throwable> rule : rollbackFor) if (rule.isInstance(ex)) return true;
        for (Class<? extends Throwable> rule : noRollbackFor) if (rule.isInstance(ex)) return false;
        return ex instanceof RuntimeException || ex instanceof Error;
    }

    private static int depth(Class<?> type, Class<?> rule) {
        return 0;
    }
'''

_RB_EXTRA = r'''
    static class InsufficientFundsException extends Exception { }
    static class PaymentDeclinedException extends InsufficientFundsException { }
    static class AuditFailure extends RuntimeException { }
    static class MinorAuditFailure extends AuditFailure { }
    static boolean rb(Throwable ex, List<Class<? extends Throwable>> yes, List<Class<? extends Throwable>> no) {
        return Solution.rollbackOn(ex, yes, no);
    }
'''

# ====================================================================================== 10. propagation
_PR_START = r'''import java.util.*;

class Solution {
    interface TxWork<T> { T run() throws Exception; }

    static class UnexpectedRollbackException extends RuntimeException {
        UnexpectedRollbackException(String message) { super(message); }
    }

    static class IllegalTransactionStateException extends RuntimeException {
        IllegalTransactionStateException(String message) { super(message); }
    }

    static class TxManager {
        TxManager(List<String> log) {
        }

        <T> T execute(String propagation, TxWork<T> work) throws Exception {
            // your code
            return work.run();
        }

        String currentTransaction() {
            return null;
        }
    }
}
'''

_PR_SOL = r'''import java.util.*;

class Solution {
    interface TxWork<T> { T run() throws Exception; }

    static class UnexpectedRollbackException extends RuntimeException {
        UnexpectedRollbackException(String message) { super(message); }
    }

    static class IllegalTransactionStateException extends RuntimeException {
        IllegalTransactionStateException(String message) { super(message); }
    }

    static class TxManager {
        private static final class Tx {
            final String name;
            boolean rollbackOnly;
            Tx(String name) { this.name = name; }
        }

        private final List<String> log;
        private int counter;
        private Tx current;

        TxManager(List<String> log) {
            this.log = log;
        }

        String currentTransaction() {
            return current == null ? null : current.name;
        }

        <T> T execute(String propagation, TxWork<T> work) throws Exception {
            switch (propagation) {
                case "REQUIRED":
                    return current != null ? participate(work) : runNew(work);
                case "SUPPORTS":
                    return current != null ? participate(work) : work.run();
                case "MANDATORY":
                    if (current == null) {
                        throw new IllegalTransactionStateException(
                                "No existing transaction found for transaction marked with propagation 'mandatory'");
                    }
                    return participate(work);
                case "REQUIRES_NEW":
                    return suspendAndRun(work, true);
                case "NOT_SUPPORTED":
                    return suspendAndRun(work, false);
                case "NEVER":
                    if (current != null) {
                        throw new IllegalTransactionStateException(
                                "Existing transaction found for transaction marked with propagation 'never'");
                    }
                    return work.run();
                default:
                    throw new IllegalArgumentException("Unknown propagation " + propagation);
            }
        }

        private static boolean rollsBack(Throwable t) {
            return t instanceof RuntimeException || t instanceof Error;
        }

        private static void rethrow(Throwable t) throws Exception {
            if (t instanceof Exception e) throw e;
            throw (Error) t;
        }

        private <T> T participate(TxWork<T> work) throws Exception {
            Tx tx = current;
            try {
                return work.run();
            } catch (Throwable t) {
                if (rollsBack(t) && !tx.rollbackOnly) {
                    tx.rollbackOnly = true;
                    log.add("rollback-only " + tx.name);
                }
                throw t;
            }
        }

        private <T> T suspendAndRun(TxWork<T> work, boolean newTransaction) throws Exception {
            Tx suspended = current;
            if (suspended != null) log.add("suspend " + suspended.name);
            current = null;
            try {
                return newTransaction ? runNew(work) : work.run();
            } finally {
                current = suspended;
                if (suspended != null) log.add("resume " + suspended.name);
            }
        }

        private <T> T runNew(TxWork<T> work) throws Exception {
            Tx tx = new Tx("tx" + (++counter));
            Tx outer = current;
            current = tx;
            log.add("begin " + tx.name);
            T result = null;
            Throwable failure = null;
            try {
                result = work.run();
            } catch (Throwable t) {
                failure = t;
            }
            current = outer;
            if (failure != null && rollsBack(failure)) {
                log.add("rollback " + tx.name);
                rethrow(failure);
            }
            if (tx.rollbackOnly) {
                log.add("rollback " + tx.name);
                throw new UnexpectedRollbackException("Transaction rolled back because it has been marked as rollback-only");
            }
            log.add("commit " + tx.name);
            if (failure != null) rethrow(failure);
            return result;
        }
    }
}
'''

_PR_EXTRA = r'''
    static Solution.TxManager mgr(List<String> log) { return new Solution.TxManager(log); }
    static Object boom() { throw new IllegalStateException("boom"); }
    static Object checked() throws Exception { throw new java.io.IOException("io"); }
'''

# ====================================================================================== 11. request mapping
_RM_START = r'''import java.util.*;

class Solution {
    record Match(int status, String handler, Map<String, String> variables, List<String> allow) { }

    static class Router {
        void map(String method, String pattern, String handler) {
            // your code
        }

        Match resolve(String method, String path) {
            return null;
        }
    }
}
'''

_RM_SOL = r'''import java.util.*;

class Solution {
    record Match(int status, String handler, Map<String, String> variables, List<String> allow) { }

    static class Router {
        private record Mapping(String method, String pattern, String[] segments, String handler, int index) { }

        private final List<Mapping> mappings = new ArrayList<>();

        private static String[] split(String path) {
            if (path.equals("/")) return new String[0];
            return path.substring(1).split("/", -1);
        }

        void map(String method, String pattern, String handler) {
            String[] segs = split(pattern);
            for (int i = 0; i < segs.length - 1; i++) {
                if (segs[i].equals("**")) throw new IllegalArgumentException("** must be the last segment: " + pattern);
            }
            for (Mapping m : mappings) {
                if (m.method().equals(method) && m.pattern().equals(pattern)) {
                    throw new IllegalStateException("Ambiguous mapping: " + method + " " + pattern);
                }
            }
            mappings.add(new Mapping(method, pattern, segs, handler, mappings.size()));
        }

        private static Map<String, String> match(String[] pattern, String[] path) {
            Map<String, String> vars = new LinkedHashMap<>();
            for (int i = 0; i < pattern.length; i++) {
                String p = pattern[i];
                if (p.equals("**")) return vars;
                if (i >= path.length) return null;
                String s = path[i];
                if (p.startsWith("{") && p.endsWith("}")) {
                    if (s.isEmpty()) return null;
                    vars.put(p.substring(1, p.length() - 1), s);
                } else if (p.equals("*")) {
                    if (s.isEmpty()) return null;
                } else if (!p.equals(s)) {
                    return null;
                }
            }
            return pattern.length == path.length ? vars : null;
        }

        private static boolean allows(String mapped, String requested) {
            return mapped.equals("*") || mapped.equals(requested) || (requested.equals("HEAD") && mapped.equals("GET"));
        }

        private static int[] score(Mapping m) {
            int doubles = 0, singles = 0, literals = 0;
            for (String s : m.segments()) {
                if (s.equals("**")) doubles++;
                else if (s.equals("*") || (s.startsWith("{") && s.endsWith("}"))) singles++;
                else literals++;
            }
            return new int[] { doubles, singles, -literals, m.index() };
        }

        Match resolve(String method, String path) {
            String[] segs = split(path);
            Mapping best = null;
            Map<String, String> bestVars = null;
            Set<String> allow = new TreeSet<>();
            boolean pathMatched = false;
            for (Mapping m : mappings) {
                Map<String, String> vars = match(m.segments(), segs);
                if (vars == null) continue;
                pathMatched = true;
                allow.add(m.method());
                if (m.method().equals("GET")) allow.add("HEAD");
                if (!allows(m.method(), method)) continue;
                if (best == null || Arrays.compare(score(m), score(best)) < 0) {
                    best = m;
                    bestVars = vars;
                }
            }
            if (best != null) return new Match(200, best.handler(), bestVars, List.of());
            if (pathMatched) return new Match(405, null, Map.of(), List.copyOf(allow));
            return new Match(404, null, Map.of(), List.of());
        }
    }
}
'''

_RM_EXTRA = r'''
    static Solution.Router shop() {
        Solution.Router r = new Solution.Router();
        r.map("GET", "/books", "listBooks");
        r.map("POST", "/books", "createBook");
        r.map("GET", "/books/{id}", "getBook");
        r.map("GET", "/books/featured", "featuredBooks");
        r.map("DELETE", "/books/{id}", "deleteBook");
        r.map("GET", "/books/{id}/reviews/{rid}", "getReview");
        r.map("*", "/health", "health");
        r.map("GET", "/files/**", "files");
        r.map("GET", "/files/{name}/meta", "fileMeta");
        r.map("GET", "/static/*/logo", "logo");
        return r;
    }
    static String show(Solution.Match m) {
        return m.status() + " " + m.handler() + " " + new TreeMap<>(m.variables()) + " " + m.allow();
    }
'''

# ====================================================================================== 12. bean validation
_BV_START = r'''import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

class Solution {
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.FIELD) @interface NotNull { }
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.FIELD) @interface NotBlank { }
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.FIELD) @interface Size { int min() default 0; int max() default Integer.MAX_VALUE; }
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.FIELD) @interface Min { long value(); }
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.FIELD) @interface Max { long value(); }
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.FIELD) @interface Email { }
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.FIELD) @interface Valid { }

    static Map<String, List<String>> validate(Object bean) {
        // your code
        return new TreeMap<>();
    }
}
'''

_BV_SOL = r'''import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

class Solution {
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.FIELD) @interface NotNull { }
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.FIELD) @interface NotBlank { }
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.FIELD) @interface Size { int min() default 0; int max() default Integer.MAX_VALUE; }
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.FIELD) @interface Min { long value(); }
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.FIELD) @interface Max { long value(); }
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.FIELD) @interface Email { }
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.FIELD) @interface Valid { }

    static Map<String, List<String>> validate(Object bean) {
        Map<String, List<String>> errors = new TreeMap<>();
        collect(bean, "", errors);
        for (List<String> messages : errors.values()) Collections.sort(messages);
        return errors;
    }

    private static void collect(Object bean, String prefix, Map<String, List<String>> errors) {
        for (Field f : bean.getClass().getDeclaredFields()) {
            if (f.isSynthetic() || Modifier.isStatic(f.getModifiers())) continue;
            f.setAccessible(true);
            Object v;
            try {
                v = f.get(bean);
            } catch (IllegalAccessException e) {
                throw new IllegalStateException(e);
            }
            String path = prefix + f.getName();
            List<String> messages = new ArrayList<>();
            if (f.isAnnotationPresent(NotNull.class) && v == null) messages.add("must not be null");
            if (f.isAnnotationPresent(NotBlank.class) && (v == null || v.toString().isBlank())) messages.add("must not be blank");
            Size size = f.getAnnotation(Size.class);
            if (size != null && v != null) {
                int len = length(v);
                if (len < size.min() || len > size.max()) {
                    messages.add("size must be between " + size.min() + " and " + size.max());
                }
            }
            Min min = f.getAnnotation(Min.class);
            if (min != null && v != null && ((Number) v).longValue() < min.value()) {
                messages.add("must be greater than or equal to " + min.value());
            }
            Max max = f.getAnnotation(Max.class);
            if (max != null && v != null && ((Number) v).longValue() > max.value()) {
                messages.add("must be less than or equal to " + max.value());
            }
            if (f.isAnnotationPresent(Email.class) && v != null && !isEmail(v.toString())) {
                messages.add("must be a well-formed email address");
            }
            if (!messages.isEmpty()) errors.computeIfAbsent(path, k -> new ArrayList<>()).addAll(messages);
            if (f.isAnnotationPresent(Valid.class) && v != null) {
                if (v instanceof List<?> list) {
                    for (int i = 0; i < list.size(); i++) {
                        if (list.get(i) != null) collect(list.get(i), path + "[" + i + "].", errors);
                    }
                } else {
                    collect(v, path + ".", errors);
                }
            }
        }
    }

    private static int length(Object v) {
        if (v instanceof CharSequence s) return s.length();
        if (v instanceof Collection<?> c) return c.size();
        if (v instanceof Map<?, ?> m) return m.size();
        if (v.getClass().isArray()) return Array.getLength(v);
        throw new IllegalArgumentException("@Size is not supported on " + v.getClass().getSimpleName());
    }

    private static boolean isEmail(String s) {
        if (s.isEmpty()) return true;
        int at = s.indexOf('@');
        return at > 0 && at == s.lastIndexOf('@') && at < s.length() - 1 && s.chars().noneMatch(Character::isWhitespace);
    }
}
'''

_BV_EXTRA = r'''
    static class Address {
        @Solution.NotBlank String city;
        @Solution.Size(min = 5, max = 5) String zip;
        Address(String city, String zip) { this.city = city; this.zip = zip; }
    }
    static class Customer {
        @Solution.NotBlank @Solution.Size(min = 2, max = 20) String name;
        @Solution.Email String email;
        @Solution.NotNull @Solution.Min(18) @Solution.Max(130) Integer age;
        @Solution.Size(max = 3) List<String> tags;
        @Solution.Valid Address address;
        @Solution.Valid List<Address> others;
        String notes;
    }
    static class Product {
        @Solution.Min(1) private int quantity;
        @Solution.Max(500) private long price;
        @Solution.Size(min = 1, max = 2) private String[] codes;
        Product(int quantity, long price, String... codes) { this.quantity = quantity; this.price = price; this.codes = codes; }
    }
    static Customer ok() {
        Customer c = new Customer();
        c.name = "Ada"; c.email = "ada@example.com"; c.age = 36; c.tags = List.of("vip");
        c.address = new Address("London", "12345"); c.others = List.of();
        return c;
    }
    static Map<String, List<String>> v(Object o) { return Solution.validate(o); }
'''

# ====================================================================================== 13. JdbcTemplate
_JT_START = r'''import java.util.*;
import java.util.function.*;

class Solution {
    interface RowMapper<T> { T mapRow(Map<String, Object> row, int rowNum); }

    static class IncorrectResultSizeDataAccessException extends RuntimeException {
        final int expected, actual;
        IncorrectResultSizeDataAccessException(int expected, int actual) {
            super("Incorrect result size: expected " + expected + ", actual " + actual);
            this.expected = expected;
            this.actual = actual;
        }
    }

    static class EmptyResultDataAccessException extends IncorrectResultSizeDataAccessException {
        EmptyResultDataAccessException(int expected) { super(expected, 0); }
    }

    static class BadSqlGrammarException extends RuntimeException {
        BadSqlGrammarException(String message) { super(message); }
    }

    static class MiniJdbcTemplate {
        MiniJdbcTemplate(Map<String, List<Map<String, Object>>> tables) {
        }

        <T> List<T> query(String table, Predicate<Map<String, Object>> where, RowMapper<T> mapper) {
            // your code
            return List.of();
        }

        <T> T queryForObject(String table, Predicate<Map<String, Object>> where, RowMapper<T> mapper) {
            return null;
        }

        int update(String table, Predicate<Map<String, Object>> where, Map<String, Object> changes) {
            return 0;
        }
    }
}
'''

_JT_SOL = r'''import java.util.*;
import java.util.function.*;

class Solution {
    interface RowMapper<T> { T mapRow(Map<String, Object> row, int rowNum); }

    static class IncorrectResultSizeDataAccessException extends RuntimeException {
        final int expected, actual;
        IncorrectResultSizeDataAccessException(int expected, int actual) {
            super("Incorrect result size: expected " + expected + ", actual " + actual);
            this.expected = expected;
            this.actual = actual;
        }
    }

    static class EmptyResultDataAccessException extends IncorrectResultSizeDataAccessException {
        EmptyResultDataAccessException(int expected) { super(expected, 0); }
    }

    static class BadSqlGrammarException extends RuntimeException {
        BadSqlGrammarException(String message) { super(message); }
    }

    static class MiniJdbcTemplate {
        private final Map<String, List<Map<String, Object>>> tables;

        MiniJdbcTemplate(Map<String, List<Map<String, Object>>> tables) {
            this.tables = tables;
        }

        private List<Map<String, Object>> table(String name) {
            List<Map<String, Object>> rows = tables.get(name);
            if (rows == null) throw new BadSqlGrammarException("Table '" + name + "' not found");
            return rows;
        }

        <T> List<T> query(String table, Predicate<Map<String, Object>> where, RowMapper<T> mapper) {
            List<T> result = new ArrayList<>();
            for (Map<String, Object> row : table(table)) {
                if (where.test(row)) result.add(mapper.mapRow(Collections.unmodifiableMap(row), result.size()));
            }
            return result;
        }

        <T> T queryForObject(String table, Predicate<Map<String, Object>> where, RowMapper<T> mapper) {
            List<T> result = query(table, where, mapper);
            if (result.isEmpty()) throw new EmptyResultDataAccessException(1);
            if (result.size() > 1) throw new IncorrectResultSizeDataAccessException(1, result.size());
            return result.get(0);
        }

        int update(String table, Predicate<Map<String, Object>> where, Map<String, Object> changes) {
            List<Map<String, Object>> rows = table(table);
            Set<String> columns = new HashSet<>();
            for (Map<String, Object> row : rows) columns.addAll(row.keySet());
            for (String column : changes.keySet()) {
                if (!columns.contains(column)) throw new BadSqlGrammarException("Unknown column '" + column + "'");
            }
            int count = 0;
            for (Map<String, Object> row : rows) {
                if (where.test(row)) {
                    row.putAll(changes);
                    count++;
                }
            }
            return count;
        }
    }
}
'''

_JT_EXTRA = r'''
    static Map<String, Object> row(Object... kv) {
        Map<String, Object> m = new HashMap<>();
        for (int i = 0; i < kv.length; i += 2) m.put((String) kv[i], kv[i + 1]);
        return m;
    }
    static Solution.MiniJdbcTemplate db() {
        List<Map<String, Object>> users = new ArrayList<>();
        users.add(row("id", 1, "name", "ann", "active", true, "email", "ann@x.org"));
        users.add(row("id", 2, "name", "bob", "active", false, "email", null));
        users.add(row("id", 3, "name", "cid", "active", true, "email", "cid@x.org"));
        Map<String, List<Map<String, Object>>> tables = new HashMap<>();
        tables.put("users", users);
        tables.put("empty", new ArrayList<>());
        return new Solution.MiniJdbcTemplate(tables);
    }
    static final Solution.RowMapper<String> NAME = (r, n) -> (String) r.get("name");
    static Predicate<Map<String, Object>> id(int id) { return r -> Objects.equals(r.get("id"), id); }
    static final Predicate<Map<String, Object>> ACTIVE = r -> Boolean.TRUE.equals(r.get("active"));
'''

# ====================================================================================== 14. record row mapper
_DM_START = r'''import java.lang.reflect.*;
import java.util.*;

class Solution {
    interface RowMapper<T> { T mapRow(Map<String, Object> row, int rowNum); }

    static <T extends Record> RowMapper<T> dataClassRowMapper(Class<T> type) {
        // your code
        return (row, rowNum) -> null;
    }
}
'''

_DM_SOL = r'''import java.lang.reflect.*;
import java.util.*;

class Solution {
    interface RowMapper<T> { T mapRow(Map<String, Object> row, int rowNum); }

    static <T extends Record> RowMapper<T> dataClassRowMapper(Class<T> type) {
        RecordComponent[] components = type.getRecordComponents();
        Class<?>[] types = new Class<?>[components.length];
        for (int i = 0; i < components.length; i++) types[i] = components[i].getType();
        Constructor<T> constructor;
        try {
            constructor = type.getDeclaredConstructor(types);
        } catch (NoSuchMethodException e) {
            throw new IllegalStateException(e);
        }
        constructor.setAccessible(true);
        return (row, rowNum) -> {
            Map<String, Object> byKey = new HashMap<>();
            for (Map.Entry<String, Object> e : row.entrySet()) byKey.put(normalise(e.getKey()), e.getValue());
            Object[] args = new Object[components.length];
            for (int i = 0; i < components.length; i++) {
                String name = components[i].getName();
                args[i] = convert(byKey.get(normalise(name)), types[i], name);
            }
            try {
                return constructor.newInstance(args);
            } catch (InvocationTargetException e) {
                if (e.getCause() instanceof RuntimeException re) throw re;
                throw new IllegalStateException(e.getCause());
            } catch (ReflectiveOperationException e) {
                throw new IllegalStateException(e);
            }
        };
    }

    private static String normalise(String name) {
        return name.replace("_", "").toLowerCase(Locale.ROOT);
    }

    private static Object convert(Object value, Class<?> type, String name) {
        if (value == null) return type.isPrimitive() ? defaultValue(type) : null;
        Class<?> boxed = box(type);
        if (boxed.isInstance(value)) return value;
        if (Number.class.isAssignableFrom(boxed)) {
            Number n;
            if (value instanceof Number num) {
                n = num;
            } else if (value instanceof String s) {
                try {
                    n = new java.math.BigDecimal(s.trim());
                } catch (NumberFormatException e) {
                    throw new IllegalArgumentException("Cannot convert '" + s + "' for component '" + name + "'");
                }
            } else {
                throw new IllegalArgumentException("Cannot convert " + value.getClass().getSimpleName() + " for component '" + name + "'");
            }
            if (boxed == Integer.class) return n.intValue();
            if (boxed == Long.class) return n.longValue();
            if (boxed == Double.class) return n.doubleValue();
            if (boxed == Float.class) return n.floatValue();
            if (boxed == Short.class) return n.shortValue();
            if (boxed == Byte.class) return n.byteValue();
        }
        if (boxed.isEnum() && value instanceof String s) {
            for (Object constant : boxed.getEnumConstants()) {
                if (((Enum<?>) constant).name().equals(s)) return constant;
            }
        }
        throw new IllegalArgumentException("Cannot convert " + value + " for component '" + name + "'");
    }

    private static Class<?> box(Class<?> t) {
        if (!t.isPrimitive()) return t;
        if (t == int.class) return Integer.class;
        if (t == long.class) return Long.class;
        if (t == double.class) return Double.class;
        if (t == boolean.class) return Boolean.class;
        if (t == float.class) return Float.class;
        if (t == short.class) return Short.class;
        if (t == byte.class) return Byte.class;
        return Character.class;
    }

    private static Object defaultValue(Class<?> t) {
        if (t == boolean.class) return false;
        if (t == int.class) return 0;
        if (t == long.class) return 0L;
        if (t == double.class) return 0.0;
        if (t == float.class) return 0f;
        if (t == short.class) return (short) 0;
        if (t == byte.class) return (byte) 0;
        return (char) 0;
    }
}
'''

_DM_EXTRA = r'''
    record User(long id, String firstName, String email, boolean active) { }
    enum Status { NEW, PAID }
    record Order(int id, double total, Status status, Long customerId) { }
    record Positive(int value) {
        Positive { if (value < 0) throw new IllegalArgumentException("negative"); }
    }
    static Map<String, Object> row(Object... kv) {
        Map<String, Object> m = new LinkedHashMap<>();
        for (int i = 0; i < kv.length; i += 2) m.put((String) kv[i], kv[i + 1]);
        return m;
    }
'''

# ====================================================================================== 15. pageable
_PG_START = r'''import java.util.*;

class Solution {
    record Order(String property, boolean ascending) { }

    record PageRequest(int page, int size, List<Order> sort) { }

    record Page<T>(List<T> content, int number, int size, long totalElements, int totalPages, boolean first, boolean last) { }

    static Page<Map<String, Object>> findAll(List<Map<String, Object>> rows, PageRequest request) {
        // your code
        return null;
    }
}
'''

_PG_SOL = r'''import java.util.*;

class Solution {
    record Order(String property, boolean ascending) { }

    record PageRequest(int page, int size, List<Order> sort) { }

    record Page<T>(List<T> content, int number, int size, long totalElements, int totalPages, boolean first, boolean last) { }

    static Page<Map<String, Object>> findAll(List<Map<String, Object>> rows, PageRequest request) {
        if (request.page() < 0) throw new IllegalArgumentException("Page index must not be less than zero");
        if (request.size() < 1) throw new IllegalArgumentException("Page size must not be less than one");
        List<Map<String, Object>> sorted = new ArrayList<>(rows);
        Comparator<Map<String, Object>> comparator = (a, b) -> 0;
        for (Order o : request.sort()) comparator = comparator.thenComparing(byProperty(o));
        sorted.sort(comparator);
        long total = sorted.size();
        int totalPages = (int) ((total + request.size() - 1) / request.size());
        long from = (long) request.page() * request.size();
        List<Map<String, Object>> content = from >= total ? List.of()
                : List.copyOf(sorted.subList((int) from, (int) Math.min(total, from + request.size())));
        boolean last = request.page() + 1 >= totalPages;
        return new Page<>(content, request.page(), request.size(), total, totalPages, request.page() == 0, last);
    }

    private static Comparator<Map<String, Object>> byProperty(Order o) {
        return (a, b) -> {
            Object x = a.get(o.property());
            Object y = b.get(o.property());
            if (x == null && y == null) return 0;
            if (x == null) return 1;
            if (y == null) return -1;
            @SuppressWarnings("unchecked")
            int c = ((Comparable<Object>) x).compareTo(y);
            return o.ascending() ? c : -Integer.signum(c);
        };
    }
}
'''

_PG_EXTRA = r'''
    static Map<String, Object> p(String name, int age, String city) {
        Map<String, Object> m = new HashMap<>();
        m.put("name", name); m.put("age", age); m.put("city", city);
        return m;
    }
    static List<Map<String, Object>> people() {
        return new ArrayList<>(List.of(p("ann", 31, "Oslo"), p("bob", 25, null), p("cid", 31, "Bergen"), p("dan", 19, "Oslo"), p("eve", 25, "Bergen")));
    }
    static Solution.PageRequest req(int page, int size, Solution.Order... sort) { return new Solution.PageRequest(page, size, List.of(sort)); }
    static Solution.Order asc(String p) { return new Solution.Order(p, true); }
    static Solution.Order desc(String p) { return new Solution.Order(p, false); }
    static String names(Solution.Page<Map<String, Object>> page) {
        StringBuilder sb = new StringBuilder();
        for (Map<String, Object> r : page.content()) sb.append(sb.length() == 0 ? "" : ",").append(r.get("name"));
        return "[" + sb + "]";
    }
    static String meta(Solution.Page<Map<String, Object>> page) {
        return "n=" + page.number() + " total=" + page.totalElements() + " pages=" + page.totalPages() + " first=" + page.first() + " last=" + page.last();
    }
'''

# ====================================================================================== 16. retry
_RT_START = r'''import java.util.*;
import java.util.concurrent.Callable;
import java.util.function.*;

class Solution {
    static <T> T retry(Callable<T> call, int maxAttempts, long initialDelay, double multiplier, long maxDelay,
                       Predicate<Throwable> retryable, LongConsumer sleeper) throws Exception {
        // your code
        return call.call();
    }
}
'''

_RT_SOL = r'''import java.util.*;
import java.util.concurrent.Callable;
import java.util.function.*;

class Solution {
    static <T> T retry(Callable<T> call, int maxAttempts, long initialDelay, double multiplier, long maxDelay,
                       Predicate<Throwable> retryable, LongConsumer sleeper) throws Exception {
        if (maxAttempts < 1) throw new IllegalArgumentException("maxAttempts must be at least 1");
        long delay = Math.min(initialDelay, maxDelay);
        for (int attempt = 1; ; attempt++) {
            try {
                return call.call();
            } catch (Exception e) {
                if (!retryable.test(e) || attempt == maxAttempts) throw e;
                sleeper.accept(delay);
                delay = Math.min(maxDelay, (long) (delay * multiplier));
            }
        }
    }
}
'''

_RT_EXTRA = r'''
    static class Flaky implements java.util.concurrent.Callable<String> {
        final int failures;
        final List<Exception> plan;
        int attempts;
        Flaky(int failures) { this.failures = failures; this.plan = null; }
        Flaky(List<Exception> plan) { this.failures = plan.size(); this.plan = plan; }
        public String call() throws Exception {
            attempts++;
            if (attempts <= failures) {
                if (plan != null) throw plan.get(attempts - 1);
                throw new java.io.IOException("attempt " + attempts);
            }
            return "ok after " + attempts;
        }
    }
    static final Predicate<Throwable> ALL = e -> true;
'''

# ====================================================================================== 17. circuit breaker
_CB_START = r'''import java.util.*;
import java.util.concurrent.Callable;
import java.util.function.*;

class Solution {
    static class CallNotPermittedException extends RuntimeException {
        CallNotPermittedException(String message) { super(message); }
    }

    static class CircuitBreaker {
        CircuitBreaker(int windowSize, int failureRateThreshold, long waitInOpenMillis, int permittedCallsInHalfOpen,
                       LongSupplier clock) {
        }

        <T> T call(Callable<T> supplier) throws Exception {
            // your code
            return supplier.call();
        }

        String state() {
            return "CLOSED";
        }
    }
}
'''

_CB_SOL = r'''import java.util.*;
import java.util.concurrent.Callable;
import java.util.function.*;

class Solution {
    static class CallNotPermittedException extends RuntimeException {
        CallNotPermittedException(String message) { super(message); }
    }

    static class CircuitBreaker {
        private final int windowSize, threshold, permitted;
        private final long wait;
        private final LongSupplier clock;
        private final ArrayDeque<Boolean> window = new ArrayDeque<>();
        private String state = "CLOSED";
        private long openedAt;
        private int halfOpenCalls, halfOpenFailures;

        CircuitBreaker(int windowSize, int failureRateThreshold, long waitInOpenMillis, int permittedCallsInHalfOpen,
                       LongSupplier clock) {
            if (windowSize < 1 || failureRateThreshold < 1 || failureRateThreshold > 100 || permittedCallsInHalfOpen < 1
                    || waitInOpenMillis < 0) {
                throw new IllegalArgumentException("invalid circuit breaker configuration");
            }
            this.windowSize = windowSize;
            this.threshold = failureRateThreshold;
            this.wait = waitInOpenMillis;
            this.permitted = permittedCallsInHalfOpen;
            this.clock = clock;
        }

        <T> T call(Callable<T> supplier) throws Exception {
            if (state.equals("OPEN")) {
                if (clock.getAsLong() - openedAt >= wait) {
                    state = "HALF_OPEN";
                    halfOpenCalls = 0;
                    halfOpenFailures = 0;
                } else {
                    throw new CallNotPermittedException("CircuitBreaker is OPEN and does not permit further calls");
                }
            }
            T result;
            try {
                result = supplier.call();
            } catch (Exception e) {
                record(true);
                throw e;
            }
            record(false);
            return result;
        }

        private void record(boolean failed) {
            if (state.equals("HALF_OPEN")) {
                halfOpenCalls++;
                if (failed) halfOpenFailures++;
                if (halfOpenCalls >= permitted) {
                    if ((long) halfOpenFailures * 100 >= (long) threshold * halfOpenCalls) {
                        open();
                    } else {
                        state = "CLOSED";
                        window.clear();
                    }
                }
                return;
            }
            window.addLast(failed);
            if (window.size() > windowSize) window.removeFirst();
            if (window.size() == windowSize) {
                long failures = window.stream().filter(b -> b).count();
                if (failures * 100 >= (long) threshold * windowSize) open();
            }
        }

        private void open() {
            state = "OPEN";
            openedAt = clock.getAsLong();
            window.clear();
        }

        String state() {
            return state;
        }
    }
}
'''

_CB_EXTRA = r'''
    static final long[] NOW = {0};
    static int targetCalls;
    static Solution.CircuitBreaker cb(int window, int threshold, long wait, int halfOpen) {
        NOW[0] = 0;
        targetCalls = 0;
        return new Solution.CircuitBreaker(window, threshold, wait, halfOpen, () -> NOW[0]);
    }
    static String ok(Solution.CircuitBreaker c) throws Exception {
        return c.call(() -> { targetCalls++; return "ok"; });
    }
    static String fail(Solution.CircuitBreaker c) {
        try { c.call(() -> { targetCalls++; throw new java.io.IOException("down"); }); return "no failure"; }
        catch (Solution.CallNotPermittedException e) { return "rejected"; }
        catch (Exception e) { return "failed"; }
    }
    static String run(Solution.CircuitBreaker c, String plan) throws Exception {
        StringBuilder sb = new StringBuilder();
        for (char ch : plan.toCharArray()) {
            String r;
            if (ch == 'S') {
                try { r = ok(c); } catch (Solution.CallNotPermittedException e) { r = "rejected"; }
            } else {
                r = fail(c);
            }
            sb.append(r.charAt(0)).append(c.state().charAt(0));
        }
        return sb.toString();
    }
'''

# ====================================================================================== 18. security filter chain
_SF_START = r'''import java.util.*;
import java.util.function.*;

class Solution {
    record Request(String method, String path, Map<String, String> headers) { }

    record Principal(String name, Set<String> roles) { }

    record Rule(String pattern, String access) { }

    static final class Exchange {
        final Request request;
        final List<String> trace = new ArrayList<>();
        int status = 200;
        String user;
        Set<String> roles = Set.of();
        Exchange(Request request) { this.request = request; }
    }

    interface Chain { void proceed(Exchange exchange); }

    interface Filter { void doFilter(Exchange exchange, Chain chain); }

    static class FilterChainProxy {
        void addFilter(String name, int order, Filter filter) {
            // your code
        }

        Exchange handle(Request request, Consumer<Exchange> servlet) {
            return new Exchange(request);
        }
    }

    static Filter bearerTokenFilter(Map<String, Principal> tokens) {
        return (exchange, chain) -> chain.proceed(exchange);
    }

    static Filter authorizationFilter(List<Rule> rules) {
        return (exchange, chain) -> chain.proceed(exchange);
    }
}
'''

_SF_SOL = r'''import java.util.*;
import java.util.function.*;

class Solution {
    record Request(String method, String path, Map<String, String> headers) { }

    record Principal(String name, Set<String> roles) { }

    record Rule(String pattern, String access) { }

    static final class Exchange {
        final Request request;
        final List<String> trace = new ArrayList<>();
        int status = 200;
        String user;
        Set<String> roles = Set.of();
        Exchange(Request request) { this.request = request; }
    }

    interface Chain { void proceed(Exchange exchange); }

    interface Filter { void doFilter(Exchange exchange, Chain chain); }

    static class FilterChainProxy {
        private record Registered(String name, int order, Filter filter) { }

        private final List<Registered> filters = new ArrayList<>();

        void addFilter(String name, int order, Filter filter) {
            filters.add(new Registered(name, order, filter));
        }

        Exchange handle(Request request, Consumer<Exchange> servlet) {
            List<Registered> sorted = new ArrayList<>(filters);
            sorted.sort(Comparator.comparingInt(Registered::order));
            Exchange exchange = new Exchange(request);
            step(sorted, 0, exchange, servlet);
            return exchange;
        }

        private void step(List<Registered> sorted, int i, Exchange exchange, Consumer<Exchange> servlet) {
            if (i == sorted.size()) {
                exchange.trace.add("servlet");
                servlet.accept(exchange);
                return;
            }
            Registered r = sorted.get(i);
            exchange.trace.add(r.name());
            r.filter().doFilter(exchange, next -> step(sorted, i + 1, next, servlet));
        }
    }

    static Filter bearerTokenFilter(Map<String, Principal> tokens) {
        return (exchange, chain) -> {
            String header = exchange.request.headers().get("Authorization");
            if (header == null) {
                chain.proceed(exchange);
                return;
            }
            Principal p = header.startsWith("Bearer ") ? tokens.get(header.substring(7)) : null;
            if (p == null) {
                exchange.status = 401;
                return;
            }
            exchange.user = p.name();
            exchange.roles = p.roles();
            chain.proceed(exchange);
        };
    }

    static boolean matches(String pattern, String path) {
        if (pattern.endsWith("/**")) {
            String prefix = pattern.substring(0, pattern.length() - 3);
            return path.equals(prefix) || path.startsWith(prefix + "/") || prefix.isEmpty();
        }
        return pattern.equals(path);
    }

    static Filter authorizationFilter(List<Rule> rules) {
        return (exchange, chain) -> {
            String access = "denyAll";
            for (Rule r : rules) {
                if (matches(r.pattern(), exchange.request.path())) {
                    access = r.access();
                    break;
                }
            }
            boolean anonymous = exchange.user == null;
            boolean granted;
            if (access.equals("permitAll")) granted = true;
            else if (access.equals("authenticated")) granted = !anonymous;
            else if (access.startsWith("hasRole:")) granted = !anonymous && exchange.roles.contains(access.substring(8));
            else granted = false;
            if (granted) {
                chain.proceed(exchange);
            } else {
                exchange.status = anonymous ? 401 : 403;
            }
        };
    }
}
'''

_SF_EXTRA = r'''
    static final Map<String, Solution.Principal> TOKENS = Map.of(
            "t-ann", new Solution.Principal("ann", Set.of("ADMIN", "USER")),
            "t-bob", new Solution.Principal("bob", Set.of("USER")));
    static final List<Solution.Rule> RULES = List.of(
            new Solution.Rule("/public/**", "permitAll"),
            new Solution.Rule("/admin/**", "hasRole:ADMIN"),
            new Solution.Rule("/api/**", "authenticated"));
    static Solution.FilterChainProxy app(List<Solution.Rule> rules) {
        Solution.FilterChainProxy p = new Solution.FilterChainProxy();
        p.addFilter("authorization", 300, Solution.authorizationFilter(rules));
        p.addFilter("bearer", 100, Solution.bearerTokenFilter(TOKENS));
        p.addFilter("cors", 50, (ex, chain) -> chain.proceed(ex));
        return p;
    }
    static Solution.Exchange call(Solution.FilterChainProxy p, String path, String auth) {
        Map<String, String> h = new HashMap<>();
        if (auth != null) h.put("Authorization", auth);
        return p.handle(new Solution.Request("GET", path, h), ex -> { });
    }
    static String show(Solution.Exchange e) { return e.status + " " + e.user + " " + e.trace; }
'''


PROBLEMS = [
# ------------------------------------------------------------------ spring-java-rollback-rules
J("spring-java-rollback-rules", "Java: @Transactional rollback rules", "Medium", "Transactions (Java)",
  r"""
`@Transactional` commits when the method returns normally. When it throws, the outcome depends on **rollback rules**
(lesson [@Transactional, rollback rules and the self-invocation pitfall](#/lesson/spring/spring-transactional)).
Implement them as Spring's `RuleBasedTransactionAttribute` does.

`static boolean rollbackOn(Throwable ex, List<Class<? extends Throwable>> rollbackFor, List<Class<? extends Throwable>> noRollbackFor)`:

1. For every rule class `R` in both lists, its **depth** is the number of `getSuperclass()` steps from `ex.getClass()`
   up to `R` (0 when the class is `R` itself); a rule that is not a superclass of the exception does not match.
2. The matching rule with the **smallest depth** wins: from `rollbackFor` → `true`, from `noRollbackFor` → `false`.
   On a tie, `rollbackFor` wins.
3. No rule matches → the default: roll back for `RuntimeException` and `Error`, **commit** for checked exceptions.

`static <T> T executeInTransaction(List<String> log, TxWork<T> work, rollbackFor, noRollbackFor)`: log `"begin"`,
run the work; on success log `"commit"` and return its result; on any exception log `"rollback"` or `"commit"` as
`rollbackOn` decides and rethrow the **same** exception object.

**Examples** `IOException` with no rules → commit (the surprise every interview asks about).
`rollbackFor = [RuntimeException]`, `noRollbackFor = [AuditFailure]`, exception `AuditFailure` → commit: the
no-rollback rule is closer (depth 0 against depth 1).
""" + JUDGE_NOTE,
  _RB_START, _RB_SOL,
  [r'''{ List<String> log = new ArrayList<>(); String r = Solution.executeInTransaction(log, () -> "saved", List.of(), List.of()); return eq(r + " " + log, "saved [begin, commit]"); }''',
   r'''{ List<String> log = new ArrayList<>(); RuntimeException boom = new IllegalStateException("x"); try { Solution.executeInTransaction(log, () -> { throw boom; }, List.of(), List.of()); return "no exception"; } catch (Exception e) { return e == boom ? eq(log, List.of("begin", "rollback")) : "a different exception came out: " + e; } }''',
   r'''{ List<String> log = new ArrayList<>(); java.io.IOException io = new java.io.IOException("disk"); try { Solution.executeInTransaction(log, () -> { throw io; }, List.of(), List.of()); return "no exception"; } catch (Exception e) { return e == io ? eq(log, List.of("begin", "commit")) : "a different exception came out: " + e; } }''',
   r'''{ List<String> log = new ArrayList<>(); try { Solution.executeInTransaction(log, () -> { throw new AssertionError("bug"); }, List.of(), List.of()); return "no error"; } catch (AssertionError e) { return eq(log, List.of("begin", "rollback")); } }''',
   r'''eq(rb(new java.io.IOException(), List.of(Exception.class), List.of()), true)''',
   r'''eq(rb(new MinorAuditFailure(), List.of(), List.of(AuditFailure.class)), false)''',
   r'''eq(rb(new AuditFailure(), List.of(RuntimeException.class), List.of(AuditFailure.class)) + " " + rb(new IllegalStateException(), List.of(RuntimeException.class), List.of(AuditFailure.class)), "false true")''',
   r'''eq(rb(new MinorAuditFailure(), List.of(MinorAuditFailure.class), List.of(AuditFailure.class)) + " " + rb(new AuditFailure(), List.of(MinorAuditFailure.class), List.of(AuditFailure.class)), "true false")''',
   r'''eq(rb(new PaymentDeclinedException(), List.of(InsufficientFundsException.class), List.of()) + " " + rb(new PaymentDeclinedException(), List.of(Exception.class), List.of(PaymentDeclinedException.class)), "true false")''',
   r'''eq(rb(new AuditFailure(), List.of(AuditFailure.class), List.of(AuditFailure.class)), true)''',
   r'''eq(rb(new IllegalArgumentException(), List.of(java.io.IOException.class), List.of()) + " " + rb(new InsufficientFundsException(), List.of(java.io.IOException.class), List.of()), "true false")''',
   r'''eq(rb(new MinorAuditFailure(), List.of(Throwable.class), List.of(RuntimeException.class)), false)''',
   r'''{ List<String> log = new ArrayList<>(); try { Solution.executeInTransaction(log, () -> { throw new PaymentDeclinedException(); }, List.of(InsufficientFundsException.class), List.of()); return "no exception"; } catch (PaymentDeclinedException e) { return eq(log, List.of("begin", "rollback")); } }'''],
  [mut(_RB_SOL, r'''    static boolean rollbackOn(Throwable ex, List<Class<? extends Throwable>> rollbackFor,
                              List<Class<? extends Throwable>> noRollbackFor) {
        int best = Integer.MAX_VALUE;
        Boolean decision = null;
        for (Class<? extends Throwable> rule : rollbackFor) {
            int d = depth(ex.getClass(), rule);
            if (d >= 0 && d < best) { best = d; decision = true; }
        }
        for (Class<? extends Throwable> rule : noRollbackFor) {
            int d = depth(ex.getClass(), rule);
            if (d >= 0 && d < best) { best = d; decision = false; }
        }
        if (decision != null) return decision;
        return ex instanceof RuntimeException || ex instanceof Error;
    }

    private static int depth(Class<?> type, Class<?> rule) {
        int d = 0;
        for (Class<?> c = type; c != null; c = c.getSuperclass(), d++) {
            if (c == rule) return d;
        }
        return -1;
    }
''', _RB_FIRST_MATCH),
   mut(_RB_SOL, "        return ex instanceof RuntimeException || ex instanceof Error;", "        return true;"),
   mut(_RB_SOL, "if (d >= 0 && d < best) { best = d; decision = false; }", "if (d >= 0 && d <= best) { best = d; decision = false; }")],
  G("Lesson [@Transactional, rollback rules and the self-invocation pitfall](#/lesson/spring/spring-transactional). Java: the exception hierarchy, `getSuperclass()`.",
    "Rules are matched by *distance* in the class hierarchy, not by list order: the rule closest to the actual exception class is the most specific statement of intent, so it wins.",
    ["Write `depth(Class<?> type, Class<?> rule)` that walks `getSuperclass()` and counts steps, returning -1 when it reaches `null`.",
     "Scan `rollbackFor` first with a strict `<`, then `noRollbackFor` with a strict `<`: that makes `rollbackFor` win ties.",
     "In `executeInTransaction`, catch `Throwable t` and `throw t`: Java's precise rethrow lets you do that in a method declared `throws Exception`."],
    "Checking `rollbackFor` first and returning on the first `isInstance` match is the natural shortcut, and it gets the 'broad rollbackFor plus narrow noRollbackFor' case wrong.",
    r"""```java
for (Class<? extends Throwable> rule : rollbackFor) {
    int d = depth(ex.getClass(), rule);
    if (d >= 0 && d < best) { best = d; decision = true; }
}
for (Class<? extends Throwable> rule : noRollbackFor) {
    int d = depth(ex.getClass(), rule);
    if (d >= 0 && d < best) { best = d; decision = false; }
}
if (decision != null) return decision;
return ex instanceof RuntimeException || ex instanceof Error;
```

**Dry run** `AuditFailure` with `rollbackFor = [RuntimeException]` and `noRollbackFor = [AuditFailure]`: depth to `RuntimeException` is 1, to `AuditFailure` 0 → the no-rollback rule wins → commit.

In Spring code:

```java
@Transactional(rollbackFor = Exception.class, noRollbackFor = AuditFailure.class)
public void transfer(...) throws InsufficientFundsException { ... }
```""",
    "O(R · H) for R rules and hierarchy height H.",
    "- Assuming checked exceptions roll back by default (they commit).\n- Letting list order decide instead of depth.\n- Swallowing or replacing the exception: the caller must see the original.\n- Catching the exception *inside* the `@Transactional` method: then nothing reaches the proxy and the transaction commits.",
    "Spring matches rules by class **name** substring for `rollbackForClassName`, a known source of surprises; the `Class`-based attributes used here are the safer choice."),
  extra=_RB_EXTRA),

# ------------------------------------------------------------------ spring-java-propagation
J("spring-java-propagation", "Java: transaction propagation with a fake connection log", "Hard", "Transactions (Java)",
  r"""
Build a tiny `PlatformTransactionManager` that understands propagation (lesson
[Propagation and isolation](#/lesson/spring/spring-propagation-isolation)) and logs what it would do to a real
connection.

`TxManager(List<String> log)`, `<T> T execute(String propagation, TxWork<T> work) throws Exception` and
`String currentTransaction()` (the name of the transaction the current code runs in, or `null`).

**Physical transactions** are named `tx1`, `tx2`, ... in the order they begin. Log lines: `begin txN`, `commit txN`,
`rollback txN`, `suspend txN`, `resume txN`, `rollback-only txN`.

| propagation | a transaction T is active | none active |
|---|---|---|
| `REQUIRED` | participate in T | begin a new one |
| `SUPPORTS` | participate in T | run without a transaction |
| `MANDATORY` | participate in T | throw `IllegalTransactionStateException` (work not run) |
| `REQUIRES_NEW` | `suspend T`, run in a new transaction, then `resume T` | begin a new one |
| `NOT_SUPPORTED` | `suspend T`, run without, then `resume T` | run without |
| `NEVER` | throw `IllegalTransactionStateException` (work not run) | run without |

Anything else → `IllegalArgumentException`. `resume` happens even if the inner work threw.

**Rollback rule:** `RuntimeException` and `Error` cause rollback; checked exceptions do not.

- **Participant** (joined T): if the work throws a rollback exception, mark T rollback-only (log
  `rollback-only T` the first time) and rethrow. Checked exceptions are rethrown without marking.
- **Owner** (began T), when its work ends:
  - threw a rollback exception → `rollback T`, rethrow it;
  - otherwise, if T is rollback-only → `rollback T` and throw `UnexpectedRollbackException` (even when the work
    ended with a checked exception, which is then lost: a real Spring gotcha);
  - otherwise `commit T` and return the result (or rethrow the checked exception).

**Example** an outer `REQUIRED` call catches a failure from an inner `REQUIRED` call and returns normally →
`[begin tx1, rollback-only tx1, rollback tx1]` and the caller gets `UnexpectedRollbackException`.
""" + JUDGE_NOTE,
  _PR_START, _PR_SOL,
  [r'''{ List<String> log = new ArrayList<>(); var m = mgr(log); String r = m.execute("REQUIRED", () -> "done:" + m.currentTransaction()); return eq(r + " " + log + " " + m.currentTransaction(), "done:tx1 [begin tx1, commit tx1] null"); }''',
   r'''{ List<String> log = new ArrayList<>(); var m = mgr(log); String r = m.execute("REQUIRED", () -> m.execute("REQUIRED", () -> m.currentTransaction())); return eq(r + " " + log, "tx1 [begin tx1, commit tx1]"); }''',
   r'''{ List<String> log = new ArrayList<>(); var m = mgr(log); String r = m.execute("REQUIRED", () -> m.execute("REQUIRES_NEW", () -> m.currentTransaction()) + "/" + m.currentTransaction()); return eq(r + " " + log, "tx2/tx1 [begin tx1, suspend tx1, begin tx2, commit tx2, resume tx1, commit tx1]"); }''',
   r'''{ List<String> log = new ArrayList<>(); var m = mgr(log); m.execute("REQUIRED", () -> { try { m.execute("REQUIRES_NEW", () -> boom()); } catch (IllegalStateException e) { } return null; }); return eq(log, List.of("begin tx1", "suspend tx1", "begin tx2", "rollback tx2", "resume tx1", "commit tx1")); }''',
   r'''{ List<String> log = new ArrayList<>(); var m = mgr(log); try { m.execute("REQUIRED", () -> { m.execute("REQUIRES_NEW", () -> "audit"); return boom(); }); return "no exception"; } catch (IllegalStateException e) { return eq(log, List.of("begin tx1", "suspend tx1", "begin tx2", "commit tx2", "resume tx1", "rollback tx1")); } }''',
   r'''{ List<String> log = new ArrayList<>(); var m = mgr(log); try { m.execute("REQUIRED", () -> { try { m.execute("REQUIRED", () -> boom()); } catch (IllegalStateException e) { } return "swallowed"; }); return "no exception"; } catch (Solution.UnexpectedRollbackException e) { return eq(log, List.of("begin tx1", "rollback-only tx1", "rollback tx1")); } }''',
   r'''{ List<String> log = new ArrayList<>(); var m = mgr(log); String r = m.execute("REQUIRED", () -> { try { m.execute("REQUIRED", () -> checked()); } catch (java.io.IOException e) { } return "fine"; }); return eq(r + " " + log, "fine [begin tx1, commit tx1]"); }''',
   r'''{ List<String> log = new ArrayList<>(); var m = mgr(log); boolean[] ran = {false}; String r = thrown(Solution.IllegalTransactionStateException.class, () -> m.execute("MANDATORY", () -> { ran[0] = true; return null; })); return r != null ? r : yes(!ran[0] && log.isEmpty(), "MANDATORY without a transaction must not run the work"); }''',
   r'''{ List<String> log = new ArrayList<>(); var m = mgr(log); String r = m.execute("REQUIRED", () -> thrown(Solution.IllegalTransactionStateException.class, () -> m.execute("NEVER", () -> "x"))); return r != null ? r : eq(log, List.of("begin tx1", "commit tx1")); }''',
   r'''{ List<String> log = new ArrayList<>(); var m = mgr(log); String a = m.execute("SUPPORTS", () -> String.valueOf(m.currentTransaction())); String b = m.execute("REQUIRED", () -> m.execute("SUPPORTS", () -> m.currentTransaction())); return eq(a + " " + b + " " + log, "null tx1 [begin tx1, commit tx1]"); }''',
   r'''{ List<String> log = new ArrayList<>(); var m = mgr(log); String r = m.execute("REQUIRED", () -> m.execute("NOT_SUPPORTED", () -> String.valueOf(m.currentTransaction())) + "/" + m.currentTransaction()); return eq(r + " " + log, "null/tx1 [begin tx1, suspend tx1, resume tx1, commit tx1]"); }''',
   r'''{ List<String> log = new ArrayList<>(); var m = mgr(log); m.execute("REQUIRED", () -> 1); m.execute("REQUIRED", () -> 2); return eq(log, List.of("begin tx1", "commit tx1", "begin tx2", "commit tx2")); }''',
   r'''{ List<String> log = new ArrayList<>(); var m = mgr(log); try { m.execute("REQUIRED", () -> { try { m.execute("REQUIRED", () -> boom()); } catch (IllegalStateException e) { } return checked(); }); return "no exception"; } catch (Solution.UnexpectedRollbackException e) { return eq(log, List.of("begin tx1", "rollback-only tx1", "rollback tx1")); } }''',
   r'''{ List<String> log = new ArrayList<>(); var m = mgr(log); try { m.execute("REQUIRED", () -> m.execute("REQUIRES_NEW", () -> boom())); return "no exception"; } catch (IllegalStateException e) { return eq(log + " " + m.currentTransaction(), "[begin tx1, suspend tx1, begin tx2, rollback tx2, resume tx1, rollback tx1] null"); } }''',
   r'''{ List<String> log = new ArrayList<>(); var m = mgr(log); try { m.execute("REQUIRED", () -> checked()); return "no exception"; } catch (java.io.IOException e) { return eq(log, List.of("begin tx1", "commit tx1")); } }'''],
  [mut(_PR_SOL, '''                case "REQUIRES_NEW":
                    return suspendAndRun(work, true);''', '''                case "REQUIRES_NEW":
                    return current != null ? participate(work) : runNew(work);'''),
   mut(_PR_SOL, "                if (rollsBack(t) && !tx.rollbackOnly) {", "                if (false) {"),
   mut(_PR_SOL, "            } finally {\n                current = suspended;\n                if (suspended != null) log.add(\"resume \" + suspended.name);\n            }",
       "            } catch (Exception e) {\n                throw e;\n            } finally {\n                current = suspended;\n            }\n            // resume is never logged")],
  G("Lessons [@Transactional and rollback rules](#/lesson/spring/spring-transactional) and [Propagation and isolation](#/lesson/spring/spring-propagation-isolation). The `spring-java-rollback-rules` exercise.",
    "There is only ever one *current* transaction. `REQUIRED` reuses it, `REQUIRES_NEW` parks it and starts another, and the owner of a transaction is the only one allowed to commit or roll back. Participants can only vote, by marking it rollback-only.",
    ["Keep `Tx current` (null when none) and a counter for names. Each `Tx` has a `rollbackOnly` flag.",
     "Write three helpers: `participate(work)`, `runNew(work)` and `suspendAndRun(work, newTx)` (saves `current`, sets it to null, restores it in `finally`).",
     "In `runNew`, capture the outcome first (result or `Throwable`), restore `current`, then decide: rollback exception → rollback; rollback-only → rollback + `UnexpectedRollbackException`; else commit."],
    "Treating every call as its own transaction (no participation) gives the right log for `REQUIRES_NEW` only; treating every call as `REQUIRED` hides the audit-log pattern.",
    r"""```java
case "REQUIRED":      return current != null ? participate(work) : runNew(work);
case "REQUIRES_NEW":  return suspendAndRun(work, true);
...
private <T> T participate(TxWork<T> work) throws Exception {
    Tx tx = current;
    try { return work.run(); }
    catch (Throwable t) {
        if (rollsBack(t) && !tx.rollbackOnly) { tx.rollbackOnly = true; log.add("rollback-only " + tx.name); }
        throw t;
    }
}
```

**Dry run** of the classic surprise: outer `REQUIRED` begins tx1; inner `REQUIRED` participates and throws `IllegalStateException` → `rollback-only tx1`; the outer method catches it and returns normally; as owner it sees rollback-only → `rollback tx1` and throws `UnexpectedRollbackException("Transaction rolled back because it has been marked as rollback-only")`. The fix in real code: let the exception propagate, or give the inner call `REQUIRES_NEW` if its failure really is independent.

**Audit pattern** (case 5): the audit row is written in its own `REQUIRES_NEW` transaction and commits, so it survives the outer rollback.""",
    "O(1) per call besides the work itself; nesting depth is the call depth.",
    "- Forgetting `resume` when the inner work throws (use `finally`).\n- Letting a participant commit or roll back.\n- Starting a new `REQUIRES_NEW` transaction while the outer one is still `current`.\n- `REQUIRES_NEW` in Spring needs a **second connection** from the pool while the first is held: with a small pool this can deadlock.",
    "`NESTED` uses JDBC savepoints inside the same physical transaction: a nested failure rolls back to the savepoint without dooming the outer transaction. It works with `DataSourceTransactionManager`, not with JPA."),
  extra=_PR_EXTRA),

# ------------------------------------------------------------------ spring-java-request-mapping
J("spring-java-request-mapping", "Java: a request-mapping router with path variables, 404 and 405", "Hard", "Spring MVC (Java)",
  r"""
`DispatcherServlet` asks its `HandlerMapping` which controller method serves a request. Build that router (lessons
[Spring MVC: the request flow through DispatcherServlet](#/lesson/spring/spring-mvc-request-flow) and
[Request parameters, path variables and the Model](#/lesson/spring/spring-request-data)).

`record Match(int status, String handler, Map<String, String> variables, List<String> allow)` is given. Complete `Router`:

**`void map(String method, String pattern, String handler)`** — `method` is an HTTP method or `"*"` (any).
`**` anywhere but the last segment → `IllegalArgumentException`. The same method and pattern twice →
`IllegalStateException` ("Ambiguous mapping", which Spring reports at startup).

**Matching** a pattern against a path: split both on `/` after the leading slash (`"/"` has zero segments; keep
empty segments, so `/books/` has segments `books` and `""`). Segment by segment: literal text must be equal;
`{name}` matches one **non-empty** segment and captures it; `*` matches one non-empty segment; `**` (last only)
matches all remaining segments, zero or more. Otherwise the segment counts must be equal.

**A mapping allows** a request method when it is equal, when the mapping says `"*"`, or when the request is `HEAD`
and the mapping is `GET` (Spring serves `HEAD` from `GET` handlers).

**`Match resolve(String method, String path)`**

1. Among mappings that match the path and allow the method, pick the **most specific**: fewest `**`, then fewest
   one-segment wildcards (`{x}` and `*` together), then most literal segments, then earliest registered.
   → `Match(200, handler, variables, [])`.
2. Some mapping matched the path but none allows the method → `Match(405, null, {}, allow)` where `allow` is the
   sorted list of methods of the path-matching mappings, with `HEAD` added when `GET` is present (Spring's `Allow` header).
3. Nothing matched the path → `Match(404, null, {}, [])`.

**Example** `GET /books/featured` matches `/books/{id}` and `/books/featured`: the literal one wins.
`PUT /books/7` → `405` with allow `[DELETE, GET, HEAD]`.
""" + JUDGE_NOTE,
  _RM_START, _RM_SOL,
  [r'''eq(show(shop().resolve("GET", "/books")), "200 listBooks {} []")''',
   r'''eq(show(shop().resolve("GET", "/books/42")), "200 getBook {id=42} []")''',
   r'''eq(show(shop().resolve("GET", "/books/featured")), "200 featuredBooks {} []")''',
   r'''eq(show(shop().resolve("PUT", "/books/42")), "405 null {} [DELETE, GET, HEAD]")''',
   r'''eq(show(shop().resolve("GET", "/authors")), "404 null {} []")''',
   r'''eq(show(shop().resolve("GET", "/books/")), "404 null {} []")''',
   r'''eq(show(shop().resolve("GET", "/books/7/reviews/3")), "200 getReview {id=7, rid=3} []")''',
   r'''eq(show(shop().resolve("PATCH", "/health")), "200 health {} []")''',
   r'''eq(show(shop().resolve("GET", "/files")) + " | " + show(shop().resolve("GET", "/files/a/b/c")), "200 files {} [] | 200 files {} []")''',
   r'''eq(show(shop().resolve("GET", "/files/report/meta")), "200 fileMeta {name=report} []")''',
   r'''eq(show(shop().resolve("HEAD", "/books/9")), "200 getBook {id=9} []")''',
   r'''{ Solution.Router r = shop(); String before = show(r.resolve("GET", "/")); r.map("GET", "/", "home"); return eq(before + " | " + show(r.resolve("GET", "/")), "404 null {} [] | 200 home {} []"); }''',
   r'''{ Solution.Router r = shop(); String a = thrown(IllegalStateException.class, () -> { r.map("GET", "/books/{id}", "again"); return null; }); if (a != null) return "duplicate: " + a; return thrown(IllegalArgumentException.class, () -> { r.map("GET", "/a/**/b", "bad"); return null; }); }''',
   r'''eq(show(shop().resolve("POST", "/books/1/reviews/2")) + " | " + show(shop().resolve("POST", "/files/x")), "405 null {} [GET, HEAD] | 405 null {} [GET, HEAD]")''',
   r'''eq(show(shop().resolve("GET", "/static/v2/logo")) + " | " + show(shop().resolve("GET", "/static//logo")), "200 logo {} [] | 404 null {} []")''',
   r'''eq(show(shop().resolve("DELETE", "/books/featured")), "200 deleteBook {id=featured} []")'''],
  [mut(_RM_SOL, "if (best == null || Arrays.compare(score(m), score(best)) < 0) {", "if (best == null) {"),
   mut(_RM_SOL, "            if (pathMatched) return new Match(405, null, Map.of(), List.copyOf(allow));\n", ""),
   mut(_RM_SOL, "                    if (s.isEmpty()) return null;\n                    vars.put(", "                    vars.put(")],
  G("Lessons [Spring MVC: the request flow](#/lesson/spring/spring-mvc-request-flow) and [Request parameters, path variables and the Model](#/lesson/spring/spring-request-data). Java: `String.split` with limit -1, records, `Arrays.compare`.",
    "Two passes in one loop: first ask 'does the **path** match?' (this decides 404 versus the rest), then 'does the **method** match?' (this decides 405 versus 200). Among full matches, a score tuple picks the most specific.",
    ["`path.substring(1).split(\"/\", -1)` keeps trailing empty segments; treat `\"/\"` as zero segments.",
     "Return the captured variables from the matcher, or `null` for no match, so one call answers both questions.",
     "Score each mapping as `int[]{doubleStars, singleWildcards, -literals, index}` and compare with `Arrays.compare`: smaller is more specific."],
    "Returning the first matching mapping is simpler and wrong as soon as a literal route (`/books/featured`) is registered after a variable route (`/books/{id}`).",
    r"""```java
for (Mapping m : mappings) {
    Map<String, String> vars = match(m.segments(), segs);
    if (vars == null) continue;                 // path does not match
    pathMatched = true;
    allow.add(m.method());
    if (m.method().equals("GET")) allow.add("HEAD");
    if (!allows(m.method(), method)) continue;  // path matches, method does not
    if (best == null || Arrays.compare(score(m), score(best)) < 0) { best = m; bestVars = vars; }
}
if (best != null) return new Match(200, best.handler(), bestVars, List.of());
if (pathMatched) return new Match(405, null, Map.of(), List.copyOf(allow));
return new Match(404, null, Map.of(), List.of());
```

**Dry run** `GET /files/report/meta`: `/files/**` matches (score `[1, 0, -1, 7]`), `/files/{name}/meta` matches (score `[0, 1, -2, 8]`); the second is smaller at the first position → `fileMeta` with `{name=report}`.

The real controller side:

```java
@GetMapping("/books/{id}")
Book get(@PathVariable long id) { ... }
```""",
    "O(M · S) per request for M mappings and S segments. Spring precomputes a lookup by direct path and parsed `PathPattern`s to do better.",
    "- `split(\"/\")` without `-1` silently drops the trailing empty segment, so `/books/` would match `/books`.\n- Letting `{id}` match an empty segment.\n- Answering 404 when the path exists under another method (that is 405).\n- Forgetting that `HEAD` is served by `GET` handlers.",
    "Spring's real `PathPattern` comparator also weighs pattern length and treats `{*path}` captures; trailing-slash matching was turned off by default in Spring Framework 6."),
  extra=_RM_EXTRA),

# ------------------------------------------------------------------ spring-java-bean-validation
J("spring-java-bean-validation", "Java: a Bean Validation engine with annotations and reflection", "Medium", "REST validation (Java)",
  r"""
`@Valid @RequestBody` makes Spring run Jakarta Bean Validation over the request object and turn the violations
into a 400 response with a field-error map (lesson
[Request bodies, validation and error handling with @RestControllerAdvice](#/lesson/spring/spring-rest-errors-validation)).
Build that validator yourself: the annotations are given (`@NotNull`, `@NotBlank`, `@Size(min, max)`, `@Min`,
`@Max`, `@Email`, `@Valid`), you read them with reflection.

`static Map<String, List<String>> validate(Object bean)` inspects the **declared fields** of the bean's class
(skip static and synthetic fields; private fields too, with `setAccessible(true)`) and returns a `TreeMap` from
property path to the **alphabetically sorted** list of messages. Fields without errors are absent; a valid bean
gives an empty map.

| annotation | violation | message |
|---|---|---|
| `@NotNull` | value is `null` | `must not be null` |
| `@NotBlank` | `null`, or `toString().isBlank()` | `must not be blank` |
| `@Size(min, max)` | length of a `CharSequence`, size of a `Collection`/`Map`, or array length outside `[min, max]` | `size must be between <min> and <max>` |
| `@Min(v)` | `((Number) value).longValue() < v` | `must be greater than or equal to <v>` |
| `@Max(v)` | `> v` | `must be less than or equal to <v>` |
| `@Email` | not: exactly one `@`, at least one character on each side, no whitespace | `must be a well-formed email address` |

As in Bean Validation, every constraint **except** `@NotNull` and `@NotBlank` treats `null` as valid, and `@Email`
also accepts the empty string.

`@Valid` cascades: a non-null field value is validated too, with keys prefixed `"<field>."`; for a `List`, element
`i` uses the prefix `"<field>[i]."` (null elements are skipped).

**Example** name `" "` with `@NotBlank @Size(min = 2, max = 20)` →
`{name=[must not be blank, size must be between 2 and 20]}`.
""" + JUDGE_NOTE,
  _BV_START, _BV_SOL,
  [r'''eq(v(ok()), Map.of())''',
   r'''{ Customer c = ok(); c.name = " "; return eq(v(c), Map.of("name", List.of("must not be blank", "size must be between 2 and 20"))); }''',
   r'''{ Customer c = ok(); c.name = null; return eq(v(c), Map.of("name", List.of("must not be blank"))); }''',
   r'''{ String[] tries = {"bob", "", null, "a@b@c", "a b@c.d", "@x.org", "x@", "z@y"}; StringBuilder sb = new StringBuilder(); for (String e : tries) { Customer c = ok(); c.email = e; sb.append(v(c).containsKey("email") ? "x" : "."); } return eq(sb.toString(), "x..xxxx."); }''',
   r'''{ Customer a = ok(); a.age = null; Customer b = ok(); b.age = 17; Customer c = ok(); c.age = 200; return eq(v(a).get("age") + " " + v(b).get("age") + " " + v(c).get("age"), "[must not be null] [must be greater than or equal to 18] [must be less than or equal to 130]"); }''',
   r'''{ Customer c = ok(); c.tags = List.of("a", "b", "c", "d"); return eq(v(c), Map.of("tags", List.of("size must be between 0 and 3"))); }''',
   r'''{ Customer c = ok(); c.address = new Address("", "123"); return eq(v(c), Map.of("address.city", List.of("must not be blank"), "address.zip", List.of("size must be between 5 and 5"))); }''',
   r'''{ Customer c = ok(); c.address = null; c.tags = null; return eq(v(c), Map.of()); }''',
   r'''{ Customer c = ok(); c.others = Arrays.asList(new Address("Paris", "75001"), null, new Address(null, "1")); return eq(v(c), Map.of("others[2].city", List.of("must not be blank"), "others[2].zip", List.of("size must be between 5 and 5"))); }''',
   r'''{ Customer c = new Customer(); c.email = "nope"; c.age = 5; return eq(new ArrayList<>(v(c).keySet()), List.of("age", "email", "name")); }''',
   r'''eq(v(new Product(0, 501, "A", "B", "C")), Map.of("codes", List.of("size must be between 1 and 2"), "price", List.of("must be less than or equal to 500"), "quantity", List.of("must be greater than or equal to 1")))''',
   r'''eq(v(new Product(1, 500, "A")), Map.of())''',
   r'''{ Customer c = ok(); c.notes = null; c.name = "x".repeat(21); return eq(v(c), Map.of("name", List.of("size must be between 2 and 20"))); }'''],
  [mut(_BV_SOL, "if (size != null && v != null) {", "if (size != null) {").replace(
       "        if (v instanceof CharSequence s) return s.length();", "        if (v == null) return 0;\n        if (v instanceof CharSequence s) return s.length();"),
   mut(_BV_SOL, "            if (f.isAnnotationPresent(Valid.class) && v != null) {", "            if (false) {"),
   mut(_BV_SOL, "                        if (list.get(i) != null) collect(list.get(i), path + \"[\" + i + \"].\", errors);",
       "                        if (list.get(i) != null) collect(list.get(i), path + \".\", errors);")],
  G("Lesson [Request bodies, validation and error handling](#/lesson/spring/spring-rest-errors-validation). Java: annotations with `RetentionPolicy.RUNTIME`, `Field.getAnnotation`, `setAccessible`, recursion.",
    "Validation is a loop over fields with one small rule per annotation. The interesting parts are the null convention (only the not-null family rejects `null`) and the cascade, which is plain recursion with a growing path prefix.",
    ["`f.getAnnotation(Size.class)` returns the annotation instance or `null`; read `size.min()` like a method call.",
     "Collect messages for one field into a list, add them to the map only if non-empty, and sort every list at the end.",
     "For `@Valid`, call the same collector with prefix `path + \".\"` (or `path + \"[\" + i + \"].\"` for list elements)."],
    "Hard-coding checks per DTO class (`if (c.name == null ...)`) works for one class and is exactly what the annotations remove.",
    r"""```java
Size size = f.getAnnotation(Size.class);
if (size != null && v != null) {
    int len = length(v);
    if (len < size.min() || len > size.max())
        messages.add("size must be between " + size.min() + " and " + size.max());
}
...
if (f.isAnnotationPresent(Valid.class) && v != null) {
    if (v instanceof List<?> list) { for (int i = 0; i < list.size(); i++) if (list.get(i) != null) collect(list.get(i), path + "[" + i + "].", errors); }
    else collect(v, path + ".", errors);
}
```

**Dry run** `others = [ok, null, Address(null, "1")]`: element 0 has no errors, element 1 is skipped, element 2 yields `others[2].city` (blank) and `others[2].zip` (size).

In Spring the controller and the error handler look like this:

```java
@PostMapping("/customers")
ResponseEntity<?> create(@Valid @RequestBody CustomerDto dto) { ... }

@ExceptionHandler(MethodArgumentNotValidException.class)
ResponseEntity<Map<String, List<String>>> invalid(MethodArgumentNotValidException ex) {
    Map<String, List<String>> errors = new TreeMap<>();
    ex.getBindingResult().getFieldErrors().forEach(fe ->
        errors.computeIfAbsent(fe.getField(), k -> new ArrayList<>()).add(fe.getDefaultMessage()));
    return ResponseEntity.badRequest().body(errors);
}
```""",
    "O(F) per object for F fields, recursively over the object graph.",
    "- Applying `@Size`/`@Min` to `null` (they must pass; add `@NotNull` if null is not allowed).\n- Forgetting `setAccessible(true)` for private fields.\n- Using `isEmpty()` instead of `isBlank()` for `@NotBlank`.\n- Forgetting `@Valid` on nested objects in real code: without it, nested constraints are silently ignored.",
    "Real Bean Validation also supports class-level constraints, groups and message interpolation from `ValidationMessages.properties`; the messages used here are Hibernate Validator's English defaults."),
  extra=_BV_EXTRA),

# ------------------------------------------------------------------ spring-java-jdbc-template
J("spring-java-jdbc-template", "Java: a JdbcTemplate with RowMapper over in-memory rows", "Easy", "Data access (Java)",
  r"""
`JdbcTemplate` removes JDBC boilerplate: you supply the query and a `RowMapper` that turns one row into an object,
and it loops, maps and translates errors into Spring's `DataAccessException` hierarchy (lesson
[JDBC, DataSource and JdbcTemplate](#/lesson/spring/spring-jdbc-template)). Build a version that works on
in-memory tables, with a `Predicate` standing in for the `WHERE` clause.

Given: `RowMapper<T> { T mapRow(Map<String, Object> row, int rowNum); }` and the exceptions
`IncorrectResultSizeDataAccessException(expected, actual)`, `EmptyResultDataAccessException` (a subclass, actual 0)
and `BadSqlGrammarException`. A table is a `List<Map<String, Object>>` (column → value).

Complete `MiniJdbcTemplate(Map<String, List<Map<String, Object>>> tables)`:

- Unknown table → `BadSqlGrammarException("Table '<name>' not found")`, for every method.
- `query(table, where, mapper)` — for each row in table order that passes `where`, call the mapper with a
  **read-only view** of the row (`Collections.unmodifiableMap`) and `rowNum` = 0, 1, 2, ... counting **result** rows.
  Return the mapped list.
- `queryForObject(table, where, mapper)` — exactly one result → return it; none →
  `EmptyResultDataAccessException(1)`; more → `IncorrectResultSizeDataAccessException(1, n)`.
- `update(table, where, changes)` — if `changes` names a column that no row of the table has →
  `BadSqlGrammarException("Unknown column '<c>'")` and nothing changes. Otherwise `putAll(changes)` on every
  matching row and return how many rows matched.

**Example** `query("users", r -> Boolean.TRUE.equals(r.get("active")), (r, n) -> n + ":" + r.get("name"))` →
`[0:ann, 1:cid]`.
""" + JUDGE_NOTE,
  _JT_START, _JT_SOL,
  [r'''eq(db().query("users", r -> true, NAME), List.of("ann", "bob", "cid"))''',
   r'''eq(db().query("users", ACTIVE, (r, n) -> n + ":" + r.get("name")), List.of("0:ann", "1:cid"))''',
   r'''eq(db().queryForObject("users", id(2), NAME), "bob")''',
   r'''{ try { db().queryForObject("users", id(9), NAME); return "expected EmptyResultDataAccessException"; } catch (Solution.EmptyResultDataAccessException e) { return yes(e instanceof Solution.IncorrectResultSizeDataAccessException && e.expected == 1 && e.actual == 0, "expected 1, actual 0"); } }''',
   r'''{ try { db().queryForObject("users", ACTIVE, NAME); return "expected IncorrectResultSizeDataAccessException"; } catch (Solution.EmptyResultDataAccessException e) { return "two rows is not an empty result"; } catch (Solution.IncorrectResultSizeDataAccessException e) { return eq(e.expected + "/" + e.actual, "1/2"); } }''',
   r'''{ var t = db(); int n = t.update("users", r -> "ann".equals(r.get("name")), Map.of("active", false)); return eq(n + " " + t.query("users", ACTIVE, NAME), "1 [cid]"); }''',
   r'''{ var t = db(); String r = thrownWith(Solution.BadSqlGrammarException.class, "nickname", () -> t.update("users", x -> true, Map.of("active", false, "nickname", "z"))); return r != null ? r : eq(t.query("users", ACTIVE, NAME), List.of("ann", "cid")); }''',
   r'''thrownMsg(Solution.BadSqlGrammarException.class, "Table 'orders' not found", () -> db().query("orders", r -> true, NAME))''',
   r'''eq(db().query("users", r -> false, NAME), List.of())''',
   r'''thrown(UnsupportedOperationException.class, () -> db().query("users", r -> true, (r, n) -> r.put("name", "hacked")))''',
   r'''{ var t = db(); return eq(t.update("users", id(42), Map.of("active", true)) + " " + t.update("empty", r -> true, Map.of()), "0 0"); }''',
   r'''eq(db().query("users", r -> r.get("email") == null, (r, n) -> r.get("id")), List.of(2))''',
   r'''{ var t = db(); t.update("users", r -> true, Map.of("email", "all@x.org")); return eq(t.query("users", r -> "all@x.org".equals(r.get("email")), (r, n) -> n), List.of(0, 1, 2)); }'''],
  [mut(_JT_SOL, "            if (result.size() > 1) throw new IncorrectResultSizeDataAccessException(1, result.size());\n", ""),
   mut(_JT_SOL, '''            List<T> result = new ArrayList<>();
            for (Map<String, Object> row : table(table)) {
                if (where.test(row)) result.add(mapper.mapRow(Collections.unmodifiableMap(row), result.size()));
            }''', '''            List<T> result = new ArrayList<>();
            List<Map<String, Object>> rows = table(table);
            for (int i = 0; i < rows.size(); i++) {
                if (where.test(rows.get(i))) result.add(mapper.mapRow(Collections.unmodifiableMap(rows.get(i)), i));
            }'''),
   mut(_JT_SOL, "mapper.mapRow(Collections.unmodifiableMap(row), result.size())", "mapper.mapRow(row, result.size())")],
  G("Lesson [JDBC, DataSource and JdbcTemplate](#/lesson/spring/spring-jdbc-template). Java: functional interfaces, generic methods, `Collections.unmodifiableMap`.",
    "`JdbcTemplate` is the *template method* pattern: the loop, the error handling and the size checks are fixed; only the mapping step varies, and you pass it in as a lambda.",
    ["`rowNum` is `result.size()` at the moment you map a row, which counts result rows, not table rows.",
     "`queryForObject` can call `query` and then check the size of the list.",
     "In `update`, validate every column name before changing any row, so a bad statement changes nothing."],
    "Without a template, every DAO method repeats the loop, the null checks and the 'exactly one row' logic, and they drift apart.",
    r"""```java
<T> List<T> query(String table, Predicate<Map<String, Object>> where, RowMapper<T> mapper) {
    List<T> result = new ArrayList<>();
    for (Map<String, Object> row : table(table))
        if (where.test(row)) result.add(mapper.mapRow(Collections.unmodifiableMap(row), result.size()));
    return result;
}
```

**Dry run** `query(users, ACTIVE, (r, n) -> n + ":" + name)`: row ann passes → `0:ann`; bob fails; cid passes → `1:cid`.

The Spring equivalent:

```java
List<String> names = jdbc.query("SELECT name FROM users WHERE active = ?", (rs, rowNum) -> rs.getString("name"), true);
User u = jdbc.queryForObject("SELECT * FROM users WHERE id = ?", userMapper, 2);   // throws EmptyResultDataAccessException if absent
int n = jdbc.update("UPDATE users SET active = ? WHERE name = ?", false, "ann");
```""",
    "O(R) per call for R rows in the table.",
    "- Returning `null` from `queryForObject` when no row matches (Spring throws; catch it or use `query` and `stream().findFirst()`).\n- Passing table row indexes as `rowNum`.\n- Giving mappers a mutable row.\n- Building SQL by string concatenation in real code: always use `?` parameters.",
    "`NamedParameterJdbcTemplate` and the fluent `JdbcClient` (Spring 6.1) are thin layers over the same template."),
  extra=_JT_EXTRA),

# ------------------------------------------------------------------ spring-java-record-row-mapper
J("spring-java-record-row-mapper", "Java: map rows to records like DataClassRowMapper", "Medium", "Data access (Java)",
  r"""
Writing a `RowMapper` by hand for every table is tedious. Spring's `DataClassRowMapper` (and
`BeanPropertyRowMapper` for JavaBeans) does it with reflection: it matches column names to record components,
converts values, and calls the canonical constructor (lesson [JDBC, DataSource and JdbcTemplate](#/lesson/spring/spring-jdbc-template)).

Write `static <T extends Record> RowMapper<T> dataClassRowMapper(Class<T> type)` (`RowMapper` is given; a row is a
`Map<String, Object>`). Do the reflection work (components, constructor) once, when the mapper is created.

For every record component, in order:

1. **Column match**: the column whose name, with underscores removed and lower-cased, equals the component name
   lower-cased. So `first_name`, `FIRST_NAME` and `firstName` all fill `firstName`. Extra columns are ignored.
2. **Missing column or `null` value** → `null` for reference types, the default (`0`, `0.0`, `false`, ...) for
   primitives (as Spring's `BeanUtils` does).
3. **Conversion**: a value that is already an instance of the (boxed) component type is used as is. For numeric
   components (`int`/`Integer`, `long`/`Long`, `double`/`Double`, ...) any `Number` is converted, and a `String` is
   parsed (`"42"` → 42). An `enum` component accepts a `String` equal to a constant's name. Anything else →
   `IllegalArgumentException` whose message contains the component name.
4. Call the canonical constructor. If it throws (a compact constructor validating its input), the caller must see
   that **same exception**, not an `InvocationTargetException`.

**Example** `record User(long id, String firstName, String email, boolean active)` and the row
`{ID=1, FIRST_NAME=Bo}` → `User[id=1, firstName=Bo, email=null, active=false]` (the `Integer` 1 became a `long`).
""" + JUDGE_NOTE,
  _DM_START, _DM_SOL,
  [r'''eq(Solution.dataClassRowMapper(User.class).mapRow(row("id", 7L, "first_name", "Ann", "email", "a@x", "active", true), 0), new User(7, "Ann", "a@x", true))''',
   r'''eq(Solution.dataClassRowMapper(User.class).mapRow(row("ID", 1, "FIRST_NAME", "Bo", "EMAIL", null, "ACTIVE", false), 0), new User(1, "Bo", null, false))''',
   r'''eq(Solution.dataClassRowMapper(User.class).mapRow(row("id", 3L, "firstName", "Cy"), 0), new User(3, "Cy", null, false))''',
   r'''eq(Solution.dataClassRowMapper(User.class).mapRow(row("id", 4L, "first_name", "Di", "email", "d@x", "active", true, "created_at", "2024-01-01", "score", 9.5), 0), new User(4, "Di", "d@x", true))''',
   r'''eq(Solution.dataClassRowMapper(Order.class).mapRow(row("id", 10, "total", 12, "status", "PAID", "customer_id", 5), 0), new Order(10, 12.0, Status.PAID, 5L))''',
   r'''eq(Solution.dataClassRowMapper(Order.class).mapRow(row("id", "42", "total", "19.99", "status", "NEW", "customer_id", null), 0), new Order(42, 19.99, Status.NEW, null))''',
   r'''eq(Solution.dataClassRowMapper(User.class).mapRow(row("id", null, "first_name", "Ed", "active", null), 0), new User(0, "Ed", null, false))''',
   r'''thrownMsg(IllegalArgumentException.class, "negative", () -> Solution.dataClassRowMapper(Positive.class).mapRow(row("value", -1), 0))''',
   r'''thrownWith(IllegalArgumentException.class, "status", () -> Solution.dataClassRowMapper(Order.class).mapRow(row("id", 1, "total", 1.0, "status", 3), 0))''',
   r'''{ var m = Solution.dataClassRowMapper(Positive.class); List<Positive> out = new ArrayList<>(); for (int i = 0; i < 3; i++) out.add(m.mapRow(row("VALUE", i * 10L), i)); return eq(out, List.of(new Positive(0), new Positive(10), new Positive(20))); }''',
   r'''thrownWith(IllegalArgumentException.class, "total", () -> Solution.dataClassRowMapper(Order.class).mapRow(row("id", 1, "total", "lots", "status", "NEW"), 0))''',
   r'''eq(Solution.dataClassRowMapper(Order.class).mapRow(row("id", 2.9, "total", 3L, "status", "NEW", "customer_id", "77"), 0), new Order(2, 3.0, Status.NEW, 77L))'''],
  [mut(_DM_SOL, '        return name.replace("_", "").toLowerCase(Locale.ROOT);', '        return name.toLowerCase(Locale.ROOT);'),
   mut(_DM_SOL, "        if (Number.class.isAssignableFrom(boxed)) {", "        if (Number.class.isAssignableFrom(boxed) && value instanceof String) {"),
   mut(_DM_SOL, "                if (e.getCause() instanceof RuntimeException re) throw re;\n", "")],
  G("Lesson [JDBC, DataSource and JdbcTemplate](#/lesson/spring/spring-jdbc-template). Java: records, `getRecordComponents()`, `getDeclaredConstructor`, boxing.",
    "A record tells you everything at run time: its components (names and types, in order) and its canonical constructor, whose parameter types are exactly those component types. Mapping a row is then: for each component, find the column, convert the value, collect the arguments, construct.",
    ["`type.getRecordComponents()` gives names and types; `type.getDeclaredConstructor(types)` gives the canonical constructor.",
     "Normalise both sides the same way: `name.replace(\"_\", \"\").toLowerCase(Locale.ROOT)`; build a map from normalised column name to value once per row.",
     "Box primitive types (`int.class` → `Integer.class`) before `isInstance`, and convert through `Number` (`n.longValue()`, ...)."],
    "Calling `constructor.newInstance(row.values().toArray())` depends on map order and on exact types, and breaks on the first `Integer` going into a `long`.",
    r"""```java
return (row, rowNum) -> {
    Map<String, Object> byKey = new HashMap<>();
    for (Map.Entry<String, Object> e : row.entrySet()) byKey.put(normalise(e.getKey()), e.getValue());
    Object[] args = new Object[components.length];
    for (int i = 0; i < components.length; i++) {
        String name = components[i].getName();
        args[i] = convert(byKey.get(normalise(name)), types[i], name);
    }
    try { return constructor.newInstance(args); }
    catch (InvocationTargetException e) { if (e.getCause() instanceof RuntimeException re) throw re; throw new IllegalStateException(e.getCause()); }
    catch (ReflectiveOperationException e) { throw new IllegalStateException(e); }
};
```

**Dry run** `Order` from `{id=10, total=12, status=PAID, customer_id=5}`: `id` is an `Integer` and the component is `int` → used as is; `total` 12 → `12.0`; `status` → `Status.PAID`; `customer_id` normalises to `customerid`, matches `customerId`, 5 → `5L`.

Spring usage: `jdbc.query("SELECT * FROM orders", new DataClassRowMapper<>(Order.class))`, or with `JdbcClient`: `client.sql("...").query(Order.class).list()`.""",
    "Reflection once per mapper; O(C + K) per row for C components and K columns.",
    "- Exact name matching (snake_case columns never match camelCase components).\n- Forgetting primitive defaults for `null`, which makes `newInstance` throw.\n- Letting `InvocationTargetException` escape instead of the record's own validation error.\n- Redoing the reflection lookups for every row.",
    "`BeanPropertyRowMapper` does the same for classes with setters, and logs columns it could not map; for large result sets a hand-written mapper is still the fastest."),
  extra=_DM_EXTRA),

# ------------------------------------------------------------------ spring-java-pageable
J("spring-java-pageable", "Java: Pageable, Sort and Page like Spring Data", "Easy", "Spring Data (Java)",
  r"""
A Spring Data repository method that takes a `Pageable` returns a `Page`: one slice of the sorted results plus the
numbers a UI needs to draw a pager (lesson
[Spring Data repositories: derived queries and @Query](#/lesson/spring/spring-data-repositories)). Build that
behaviour over in-memory rows.

Given: `record Order(String property, boolean ascending)`, `record PageRequest(int page, int size, List<Order> sort)`
and `record Page<T>(List<T> content, int number, int size, long totalElements, int totalPages, boolean first, boolean last)`.

Write `static Page<Map<String, Object>> findAll(List<Map<String, Object>> rows, PageRequest request)`:

- `page < 0` → `IllegalArgumentException("Page index must not be less than zero")`; `size < 1` →
  `IllegalArgumentException("Page size must not be less than one")` (Spring's messages).
- Sort a **copy** (never modify `rows`) by the orders in turn: the first order decides, the next breaks ties, and
  so on. Values are `Comparable`; a missing property counts as `null`; **nulls come last in both directions**.
  The sort is stable: rows that compare equal keep their input order.
- `content` = the rows from index `page * size`, at most `size` of them; empty if the page is past the end. (Compute
  the offset in `long`: `page * size` can overflow `int`.)
- `totalElements` = number of rows; `totalPages` = ceiling of `totalElements / size` (0 for no rows);
  `first` = `page == 0`; `last` = `page + 1 >= totalPages` (so an empty result is both first and last).

**Example** five people, `PageRequest(0, 2, [age desc])` → content `[ann, cid]` (both 31), totalPages 3, first true, last false.
""" + JUDGE_NOTE,
  _PG_START, _PG_SOL,
  [r'''{ var pg = Solution.findAll(people(), req(0, 2)); return eq(names(pg) + " " + meta(pg), "[ann,bob] n=0 total=5 pages=3 first=true last=false"); }''',
   r'''{ var pg = Solution.findAll(people(), req(2, 2)); return eq(names(pg) + " " + meta(pg), "[eve] n=2 total=5 pages=3 first=false last=true"); }''',
   r'''{ var pg = Solution.findAll(people(), req(5, 2)); return eq(names(pg) + " " + meta(pg), "[] n=5 total=5 pages=3 first=false last=true"); }''',
   r'''eq(names(Solution.findAll(people(), req(0, 10, desc("age")))), "[ann,cid,bob,eve,dan]")''',
   r'''eq(names(Solution.findAll(people(), req(0, 10, asc("city"), desc("name")))), "[eve,cid,dan,ann,bob]")''',
   r'''eq(names(Solution.findAll(people(), req(0, 10, desc("city"), asc("name")))), "[ann,dan,cid,eve,bob]")''',
   r'''eq(names(Solution.findAll(people(), req(0, 10, asc("age")))), "[dan,bob,eve,ann,cid]")''',
   r'''{ var pg = Solution.findAll(new ArrayList<>(), req(0, 5)); return eq(names(pg) + " " + meta(pg), "[] n=0 total=0 pages=0 first=true last=true"); }''',
   r'''{ String a = thrownMsg(IllegalArgumentException.class, "Page index must not be less than zero", () -> Solution.findAll(people(), req(-1, 5))); return a != null ? a : thrownMsg(IllegalArgumentException.class, "Page size must not be less than one", () -> Solution.findAll(people(), req(0, 0))); }''',
   r'''{ var rows = people(); Solution.findAll(rows, req(0, 2, desc("name"))); StringBuilder sb = new StringBuilder(); for (var r : rows) sb.append(r.get("name")).append(' '); return eq(sb.toString().trim(), "ann bob cid dan eve"); }''',
   r'''{ var pg = Solution.findAll(people(), req(300_000_000, 10)); return eq(names(pg) + " " + meta(pg), "[] n=300000000 total=5 pages=1 first=false last=true"); }''',
   r'''{ var pg = Solution.findAll(people(), req(0, 50, asc("name"))); return eq(names(pg) + " " + meta(pg), "[ann,bob,cid,dan,eve] n=0 total=5 pages=1 first=true last=true"); }''',
   r'''{ var pg = Solution.findAll(people(), req(1, 3, asc("nickname"), asc("age"))); return eq(names(pg) + " " + meta(pg), "[ann,cid] n=1 total=5 pages=2 first=false last=true"); }'''],
  [mut(_PG_SOL, "int totalPages = (int) ((total + request.size() - 1) / request.size());", "int totalPages = (int) (total / request.size());"),
   mut(_PG_SOL, "            return o.ascending() ? c : -Integer.signum(c);\n        };\n    }",
       "            return c;\n        };\n    }").replace(
       "for (Order o : request.sort()) comparator = comparator.thenComparing(byProperty(o));",
       "for (Order o : request.sort()) comparator = comparator.thenComparing(o.ascending() ? byProperty(o) : byProperty(o).reversed());"),
   mut(_PG_SOL, "long from = (long) request.page() * request.size();", "long from = request.page() * request.size();")],
  G("Lesson [Spring Data repositories: derived queries and @Query](#/lesson/spring/spring-data-repositories). Java: `Comparator.thenComparing`, `List.subList`, records, `long` arithmetic.",
    "Paging is arithmetic on a sorted list: sort once, then the page is a window `[page·size, page·size + size)`. Everything else in `Page` is derived from the total count and the size.",
    ["Start from `Comparator<Map<String, Object>> c = (a, b) -> 0;` and chain `c = c.thenComparing(byProperty(order))` for each order; `List.sort` is stable.",
     "Handle nulls inside `byProperty` **before** applying the direction, so that reversing never moves nulls to the front.",
     "`totalPages = (total + size - 1) / size` is the integer ceiling; compute the offset as `(long) page * size`."],
    "Sorting with `Comparator.reversed()` for descending orders is natural and also reverses the null placement, which is why the null handling belongs inside the per-property comparator.",
    r"""```java
long total = sorted.size();
int totalPages = (int) ((total + request.size() - 1) / request.size());
long from = (long) request.page() * request.size();
List<Map<String, Object>> content = from >= total ? List.of()
        : List.copyOf(sorted.subList((int) from, (int) Math.min(total, from + request.size())));
boolean last = request.page() + 1 >= totalPages;
```

**Dry run** `desc(city), asc(name)`: cities Oslo (ann, dan), Bergen (cid, eve), null (bob). Descending: Oslo before Bergen; ties by name ascending; bob's null goes last → `[ann, dan, cid, eve, bob]`.

In Spring Data:

```java
Page<Person> page = repo.findAll(PageRequest.of(0, 2, Sort.by("age").descending()));
page.getContent(); page.getTotalPages(); page.isLast();
```

The `Page` needs a second `count(*)` query in a real database; return `Slice` instead when you only need 'is there a next page?'.""",
    "O(n log n) for the sort plus O(size) for the page.",
    "- Floor division for `totalPages` (5 rows of 2 is 3 pages, not 2).\n- `page * size` overflowing `int`.\n- Sorting the caller's list in place.\n- Offset pagination gets slow for deep pages in SQL (`OFFSET 100000`); keyset pagination (`WHERE id > ?`) or Spring Data's `ScrollPosition` avoids it.",
    "Spring Data's `Sort.Order` also supports `nullsFirst()`/`nullsLast()` and `ignoreCase()`; by default null handling is left to the database."),
  extra=_PG_EXTRA),

# ------------------------------------------------------------------ spring-java-retry-backoff
J("spring-java-retry-backoff", "Java: retry with exponential backoff", "Medium", "Resilient clients (Java)",
  r"""
Remote calls fail transiently. Spring Retry's `@Retryable(maxAttempts = ..., backoff = @Backoff(delay, multiplier, maxDelay))`
and Resilience4j's `Retry` wrap the call in a loop that waits longer after each failure (lesson
[WebClient, timeouts and resilient calls](#/lesson/spring/spring-webclient)). Write that loop.

```java
static <T> T retry(Callable<T> call, int maxAttempts, long initialDelay, double multiplier, long maxDelay,
                   Predicate<Throwable> retryable, LongConsumer sleeper) throws Exception
```

- `maxAttempts < 1` → `IllegalArgumentException`. `maxAttempts` counts **all** attempts, including the first.
- Call `call.call()`. Success → return the result at once.
- An `Exception` that is not `retryable` → rethrow it immediately. After the last attempt → rethrow the exception of
  that last attempt (the same object).
- Otherwise wait, by calling `sleeper.accept(delay)` (the tests record the delays; never call `Thread.sleep`), then
  try again. The first delay is `min(initialDelay, maxDelay)`; after each wait the next delay is
  `min(maxDelay, (long) (delay * multiplier))`.
- An `Error` is not an `Exception`: it passes through without retrying.

**Example** fails twice then succeeds, `maxAttempts 3`, delay 100, multiplier 2 → sleeps `[100, 200]`, returns the result.
""" + JUDGE_NOTE,
  _RT_START, _RT_SOL,
  [r'''{ List<Long> s = new ArrayList<>(); Flaky f = new Flaky(0); String r = Solution.retry(f, 3, 100, 2.0, 10_000, ALL, s::add); return eq(r + " " + s + " " + f.attempts, "ok after 1 [] 1"); }''',
   r'''{ List<Long> s = new ArrayList<>(); Flaky f = new Flaky(2); String r = Solution.retry(f, 3, 100, 2.0, 10_000, ALL, s::add); return eq(r + " " + s, "ok after 3 [100, 200]"); }''',
   r'''{ List<Long> s = new ArrayList<>(); Flaky f = new Flaky(10); try { Solution.retry(f, 4, 100, 2.0, 10_000, ALL, s::add); return "expected the last exception"; } catch (java.io.IOException e) { return eq(e.getMessage() + " " + s + " " + f.attempts, "attempt 4 [100, 200, 400] 4"); } }''',
   r'''{ List<Long> s = new ArrayList<>(); try { Solution.retry(new Flaky(10), 5, 1000, 3.0, 5000, ALL, s::add); return "expected exception"; } catch (java.io.IOException e) { return eq(s, List.of(1000L, 3000L, 5000L, 5000L)); } }''',
   r'''{ List<Long> s = new ArrayList<>(); Flaky f = new Flaky(List.of(new IllegalArgumentException("bad input"))); try { Solution.retry(f, 5, 100, 2.0, 10_000, e -> e instanceof java.io.IOException, s::add); return "expected exception"; } catch (IllegalArgumentException e) { return eq(s + " " + f.attempts, "[] 1"); } }''',
   r'''{ List<Long> s = new ArrayList<>(); IllegalStateException fatal = new IllegalStateException("fatal"); Flaky f = new Flaky(List.of(new java.io.IOException("t1"), fatal)); try { Solution.retry(f, 5, 100, 2.0, 10_000, e -> e instanceof java.io.IOException, s::add); return "expected exception"; } catch (IllegalStateException e) { return e == fatal ? eq(s + " " + f.attempts, "[100] 2") : "wrong exception object"; } }''',
   r'''{ List<Long> s = new ArrayList<>(); Flaky f = new Flaky(1); try { Solution.retry(f, 1, 100, 2.0, 10_000, ALL, s::add); return "expected exception"; } catch (java.io.IOException e) { return eq(s + " " + f.attempts, "[] 1"); } }''',
   r'''thrown(IllegalArgumentException.class, () -> Solution.retry(new Flaky(0), 0, 100, 2.0, 1000, ALL, x -> { }))''',
   r'''{ List<Long> s = new ArrayList<>(); try { Solution.retry(new Flaky(10), 5, 100, 1.5, 10_000, ALL, s::add); return "expected exception"; } catch (java.io.IOException e) { return eq(s, List.of(100L, 150L, 225L, 337L)); } }''',
   r'''{ List<Long> s = new ArrayList<>(); Solution.retry(new Flaky(2), 3, 9000, 2.0, 5000, ALL, s::add); return eq(s, List.of(5000L, 5000L)); }''',
   r'''{ List<Long> s = new ArrayList<>(); int[] calls = {0}; try { Solution.retry(() -> { calls[0]++; throw new AssertionError("bug"); }, 5, 100, 2.0, 1000, ALL, s::add); return "expected AssertionError"; } catch (AssertionError e) { return eq(calls[0] + " " + s, "1 []"); } }''',
   r'''{ List<Long> s = new ArrayList<>(); Solution.retry(new Flaky(3), 4, 0, 2.0, 1000, ALL, s::add); return eq(s, List.of(0L, 0L, 0L)); }'''],
  [mut(_RT_SOL, "if (!retryable.test(e) || attempt == maxAttempts) throw e;", "if (!retryable.test(e) || attempt > maxAttempts) throw e;"),
   mut(_RT_SOL, "delay = Math.min(maxDelay, (long) (delay * multiplier));", "delay = (long) (delay * multiplier);"),
   mut(_RT_SOL, "            } catch (Exception e) {", "            } catch (Throwable e) {").replace(
       "                if (!retryable.test(e) || attempt == maxAttempts) throw e;",
       "                if (attempt == maxAttempts) throw new Exception(e);\n                if (!retryable.test(e)) throw new Exception(e);")],
  G("Lesson [WebClient, timeouts and resilient calls](#/lesson/spring/spring-webclient). Java: `Callable`, functional interfaces, loops with `try`/`catch`.",
    "A retry is a loop with three exits: success, a non-retryable failure, or running out of attempts. Between attempts the delay grows geometrically up to a ceiling, so a struggling service gets breathing room.",
    ["Use `for (int attempt = 1; ; attempt++)` and `return` from inside the `try` on success.",
     "In the `catch`, decide first whether to give up (`!retryable.test(e) || attempt == maxAttempts`), then sleep, then grow the delay.",
     "Inject the sleeper so tests run instantly; production code would pass `Thread::sleep` wrapped to handle `InterruptedException`."],
    "Recursion (`return retry(..., maxAttempts - 1, ...)`) works and makes the delay bookkeeping awkward; a loop keeps the state in two local variables.",
    r"""```java
long delay = Math.min(initialDelay, maxDelay);
for (int attempt = 1; ; attempt++) {
    try {
        return call.call();
    } catch (Exception e) {
        if (!retryable.test(e) || attempt == maxAttempts) throw e;
        sleeper.accept(delay);
        delay = Math.min(maxDelay, (long) (delay * multiplier));
    }
}
```

**Dry run** `maxAttempts 5`, delay 1000, multiplier 3, max 5000, always failing: attempts 1–4 fail and sleep 1000, 3000, min(5000, 9000) = 5000, 5000; attempt 5 fails and rethrows.

With Spring Retry:

```java
@Retryable(retryFor = IOException.class, maxAttempts = 4, backoff = @Backoff(delay = 100, multiplier = 2, maxDelay = 2000))
public Quote fetch() throws IOException { ... }
```""",
    "O(maxAttempts) calls; total waiting is bounded by `(maxAttempts - 1) * maxDelay`.",
    "- Treating `maxAttempts` as the number of *retries* (one call too many).\n- No cap, so delays explode.\n- Retrying non-idempotent operations (a POST that charges a card) without an idempotency key.\n- Wrapping the exception, so callers cannot catch the original type.\n- Many clients retrying in lockstep: production policies add random **jitter** to each delay.",
    "Put the retry outside the transaction and inside (or instead of) a circuit breaker: the next exercise builds the breaker."),
  extra=_RT_EXTRA),

# ------------------------------------------------------------------ spring-java-circuit-breaker
J("spring-java-circuit-breaker", "Java: a circuit breaker state machine", "Hard", "Resilient clients (Java)",
  r"""
Retrying a service that is down only adds load. A **circuit breaker** (Resilience4j, used through Spring Cloud
Circuit Breaker) stops calling it for a while after too many failures (lesson
[WebClient, timeouts and resilient calls](#/lesson/spring/spring-webclient)). Implement Resilience4j's count-based
breaker.

`CircuitBreaker(int windowSize, int failureRateThreshold, long waitInOpenMillis, int permittedCallsInHalfOpen, LongSupplier clock)`:
invalid settings (`windowSize < 1`, threshold outside 1..100, `permittedCallsInHalfOpen < 1`, negative wait) →
`IllegalArgumentException`. `String state()` returns `"CLOSED"`, `"OPEN"` or `"HALF_OPEN"`. `<T> T call(Callable<T>)`:

- **CLOSED** — run the call. A thrown `Exception` is a failure (rethrow it unchanged); a return is a success.
  Record the outcome in a **sliding window** of the last `windowSize` outcomes. Once the window is full, if
  `failures * 100 >= threshold * windowSize`, switch to **OPEN**: remember `openedAt = clock`, clear the window.
- **OPEN** — if `clock - openedAt >= waitInOpenMillis`, switch to **HALF_OPEN** and let this call through;
  otherwise throw `CallNotPermittedException` (given) **without** running the call. `state()` does not change by
  itself: it stays `OPEN` until a call arrives after the wait.
- **HALF_OPEN** — run trial calls and count them separately. After `permittedCallsInHalfOpen` trial outcomes: if the
  failure rate is at least the threshold → **OPEN** again (new `openedAt`); otherwise → **CLOSED** with an empty window.

**Example** window 4, threshold 50: outcomes F, S, F keep it CLOSED (window not full); a fourth outcome S makes
2 failures in 4 = 50% → OPEN.
""" + JUDGE_NOTE,
  _CB_START, _CB_SOL,
  [r'''{ var c = cb(4, 50, 1000, 2); return eq(run(c, "SSSSSS"), "oCoCoCoCoCoC"); }''',
   r'''{ var c = cb(4, 50, 1000, 2); return eq(run(c, "FSFS"), "fCoCfCoO"); }''',
   r'''{ var c = cb(4, 50, 1000, 2); run(c, "FFFF"); int before = targetCalls; String r = run(c, "SF"); return eq(r + " " + (targetCalls - before), "rOrO 0"); }''',
   r'''{ var c = cb(4, 50, 1000, 2); run(c, "FFFF"); NOW[0] = 1000; return eq(run(c, "S"), "oH"); }''',
   r'''{ var c = cb(4, 50, 1000, 2); run(c, "FFFF"); NOW[0] = 1500; return eq(run(c, "SSSS"), "oHoCoCoC"); }''',
   r'''{ var c = cb(4, 50, 1000, 2); run(c, "FFFF"); NOW[0] = 1000; String a = run(c, "SF"); NOW[0] = 1999; String b = run(c, "S"); NOW[0] = 2000; String d = run(c, "S"); return eq(a + " " + b + " " + d, "oHfO rO oH"); }''',
   r'''{ var c = cb(3, 66, 1000, 1); return eq(run(c, "FSSFF"), "fCoCoCfCfO"); }''',
   r'''{ var c = cb(3, 50, 1000, 1); java.io.IOException io = new java.io.IOException("x"); try { c.call(() -> { throw io; }); return "no exception"; } catch (java.io.IOException e) { return yes(e == io, "the original exception must be rethrown"); } }''',
   r'''{ var c = cb(2, 50, 1000, 1); run(c, "FF"); NOW[0] = 999; String a = run(c, "S"); NOW[0] = 5000; String s = c.state(); return eq(a + " " + s + " " + run(c, "S"), "rO OPEN oC"); }''',
   r'''{ var c = cb(2, 50, 1000, 1); run(c, "FF"); NOW[0] = 1000; run(c, "S"); return eq(c.state() + " " + run(c, "F") + " " + run(c, "S"), "CLOSED fC oO"); }''',
   r'''{ String a = thrown(IllegalArgumentException.class, () -> new Solution.CircuitBreaker(0, 50, 1000, 1, () -> 0)); if (a != null) return "window 0: " + a; String b = thrown(IllegalArgumentException.class, () -> new Solution.CircuitBreaker(5, 101, 1000, 1, () -> 0)); if (b != null) return "threshold 101: " + b; return thrown(IllegalArgumentException.class, () -> new Solution.CircuitBreaker(5, 50, 1000, 0, () -> 0)); }''',
   r'''{ var c = cb(3, 100, 1000, 1); return eq(run(c, "FFSFFF"), "fCfCoCfCfCfO"); }''',
   r'''{ var c = cb(2, 50, 100, 3); run(c, "FF"); NOW[0] = 100; return eq(run(c, "SFS"), "oHfHoC"); }'''],
  [mut(_CB_SOL, "if (failures * 100 >= (long) threshold * windowSize) open();", "if (failures * 100 > (long) threshold * windowSize) open();"),
   mut(_CB_SOL, "            if (window.size() == windowSize) {\n                long failures = window.stream().filter(b -> b).count();\n                if (failures * 100 >= (long) threshold * windowSize) open();\n            }",
       "            if (window.size() == windowSize) {\n                long failures = window.stream().filter(b -> b).count();\n                if (failures * 100 >= (long) threshold * windowSize) open(); else window.clear();\n            }"),
   mut(_CB_SOL, "                if (clock.getAsLong() - openedAt >= wait) {", "                if (clock.getAsLong() - openedAt > wait) {")],
  G("Lesson [WebClient, timeouts and resilient calls](#/lesson/spring/spring-webclient). The `spring-java-retry-backoff` exercise. Java: `ArrayDeque`, `LongSupplier`, state machines.",
    "Three states, and the only question in each is 'may this call go through, and what does its outcome change?'. CLOSED watches a sliding window, OPEN watches the clock, HALF_OPEN runs a small experiment and decides.",
    ["Keep the window as an `ArrayDeque<Boolean>` (true = failure): `addLast`, and `removeFirst` when it grows past `windowSize`.",
     "Do the OPEN → HALF_OPEN check at the start of `call`, before running anything; it is the only place time matters.",
     "Use one `record(boolean failed)` method that branches on the state, called after the outcome is known."],
    "Counting failures in fixed blocks (clear the window every `windowSize` calls) is a *tumbling* window: a burst of failures that straddles two blocks never trips the breaker.",
    r"""```java
<T> T call(Callable<T> supplier) throws Exception {
    if (state.equals("OPEN")) {
        if (clock.getAsLong() - openedAt >= wait) { state = "HALF_OPEN"; halfOpenCalls = 0; halfOpenFailures = 0; }
        else throw new CallNotPermittedException("CircuitBreaker is OPEN and does not permit further calls");
    }
    T result;
    try { result = supplier.call(); }
    catch (Exception e) { record(true); throw e; }
    record(false);
    return result;
}
```

**Dry run** window 3, threshold 66, outcomes F S S F F: windows `[F]`, `[F,S]`, `[F,S,S]` 33%, `[S,S,F]` 33%, `[S,F,F]` 66.7% ≥ 66 → OPEN (with threshold 67 it would stay closed: 200 < 201 in integer terms).

With Spring Cloud Circuit Breaker and Resilience4j:

```yaml
resilience4j.circuitbreaker.instances.quotes:
  sliding-window-type: COUNT_BASED
  sliding-window-size: 10
  failure-rate-threshold: 50
  wait-duration-in-open-state: 10s
  permitted-number-of-calls-in-half-open-state: 3
```

```java
@CircuitBreaker(name = "quotes", fallbackMethod = "cachedQuote")
public Quote fetch() { ... }
```""",
    "O(1) per call (the failure count could be kept incrementally instead of streaming the window).",
    "- Rate check with `>` instead of `>=`.\n- Judging the rate before the window is full (Resilience4j's `minimumNumberOfCalls`).\n- Calling the target while OPEN.\n- Not resetting the window when closing again, so old failures re-open it at once.",
    "Resilience4j also counts *slow* calls as failures (`slowCallRateThreshold`) and offers a time-based window; a fallback method turns `CallNotPermittedException` into a cached or default answer."),
  extra=_CB_EXTRA),

# ------------------------------------------------------------------ spring-java-security-filter-chain
J("spring-java-security-filter-chain", "Java: a Spring Security filter chain with bearer tokens and URL rules", "Hard", "Spring Security (Java)",
  r"""
Spring Security is a chain of servlet filters run before your controller: one filter authenticates (works out
*who* is calling), a later one authorises (decides whether they *may*). Each filter either passes the request on
or stops the chain by writing an error (lesson
[Spring Security basics and JWT resource servers](#/lesson/spring/spring-security-jwt)).

Given: `Request(method, path, headers)`, `Principal(name, roles)`, `Rule(pattern, access)`, the mutable
`Exchange` (request, `trace`, `status` = 200, `user` = null, `roles`), `Chain.proceed(exchange)` and
`Filter.doFilter(exchange, chain)`.

**`FilterChainProxy`** — `addFilter(name, order, filter)`; `handle(request, servlet)` creates an `Exchange`, runs
the filters sorted by `order` ascending (equal orders keep insertion order) and returns the exchange. Before
running a filter, append its name to `trace`. When the last filter proceeds, append `"servlet"` and call
`servlet.accept(exchange)`. A filter that does not call `chain.proceed` ends the chain.

**`bearerTokenFilter(Map<String, Principal> tokens)`** — reads the `Authorization` header:

- absent → anonymous, proceed;
- not starting with `"Bearer "`, or the token after it is not in `tokens` → `status = 401`, stop;
- valid → set `user` and `roles` from the principal, proceed.

**`authorizationFilter(List<Rule> rules)`** — the **first** rule whose pattern matches the path decides; no match
means `denyAll`. A pattern ending in `/**` matches its prefix itself and anything below it (`/admin/**` matches
`/admin` and `/admin/x/y`, not `/administrator`); `/**` matches everything; other patterns must equal the path.
Access values: `permitAll`; `authenticated`; `hasRole:<ROLE>`; `denyAll`. Granted → proceed. Refused →
`status = 401` if the caller is anonymous (Spring sends anonymous users to authentication), otherwise `403`.

**Example** filters `cors`(50), `bearer`(100), `authorization`(300); `GET /api/orders` with no token → status 401,
trace `[cors, bearer, authorization]`.
""" + JUDGE_NOTE,
  _SF_START, _SF_SOL,
  [r'''eq(show(call(app(RULES), "/public/info", null)), "200 null [cors, bearer, authorization, servlet]")''',
   r'''eq(show(call(app(RULES), "/api/orders", null)), "401 null [cors, bearer, authorization]")''',
   r'''eq(show(call(app(RULES), "/api/orders", "Bearer t-bob")), "200 bob [cors, bearer, authorization, servlet]")''',
   r'''eq(show(call(app(RULES), "/admin/users", "Bearer t-bob")), "403 bob [cors, bearer, authorization]")''',
   r'''eq(show(call(app(RULES), "/admin/users", "Bearer t-ann")), "200 ann [cors, bearer, authorization, servlet]")''',
   r'''eq(show(call(app(RULES), "/api/orders", "Bearer forged")), "401 null [cors, bearer]")''',
   r'''eq(show(call(app(RULES), "/public/info", "Basic YW5uOnB3")), "401 null [cors, bearer]")''',
   r'''eq(show(call(app(RULES), "/other", "Bearer t-ann")) + " | " + show(call(app(RULES), "/other", null)), "403 ann [cors, bearer, authorization] | 401 null [cors, bearer, authorization]")''',
   r'''eq(show(call(app(RULES), "/admin", "Bearer t-ann")) + " | " + show(call(app(RULES), "/administrator", "Bearer t-ann")), "200 ann [cors, bearer, authorization, servlet] | 403 ann [cors, bearer, authorization]")''',
   r'''{ Solution.FilterChainProxy p = app(RULES); p.addFilter("maintenance", 10, (ex, chain) -> ex.status = 503); return eq(show(call(p, "/public/info", null)), "503 null [maintenance]"); }''',
   r'''{ Solution.FilterChainProxy p = new Solution.FilterChainProxy(); p.addFilter("b", 5, (ex, ch) -> ch.proceed(ex)); p.addFilter("a", 5, (ex, ch) -> ch.proceed(ex)); p.addFilter("c", 1, (ex, ch) -> ch.proceed(ex)); return eq(show(call(p, "/x", null)), "200 null [c, b, a, servlet]"); }''',
   r'''{ var open = List.of(new Solution.Rule("/api/public/**", "permitAll"), new Solution.Rule("/api/**", "authenticated")); var shut = List.of(new Solution.Rule("/api/**", "authenticated"), new Solution.Rule("/api/public/**", "permitAll")); return eq(call(app(open), "/api/public/x", null).status + " " + call(app(shut), "/api/public/x", null).status, "200 401"); }''',
   r'''{ var rules = List.of(new Solution.Rule("/health", "permitAll"), new Solution.Rule("/**", "hasRole:USER")); return eq(call(app(rules), "/health", null).status + " " + call(app(rules), "/health/db", "Bearer t-bob").status + " " + call(app(rules), "/health/db", null).status + " " + call(app(rules), "/anything/else", "Bearer t-ann").status, "200 200 401 200"); }''',
   r'''{ Solution.FilterChainProxy p = app(RULES); String[] seen = new String[1]; Solution.Exchange e = p.handle(new Solution.Request("GET", "/api/me", Map.of("Authorization", "Bearer t-ann")), ex -> seen[0] = ex.user + ex.roles.contains("ADMIN")); return eq(seen[0] + " " + e.status, "anntrue 200"); }'''],
  [mut(_SF_SOL, "            sorted.sort(Comparator.comparingInt(Registered::order));\n", ""),
   mut(_SF_SOL, "                exchange.status = anonymous ? 401 : 403;", "                exchange.status = 403;"),
   mut(_SF_SOL, "            return path.equals(prefix) || path.startsWith(prefix + \"/\") || prefix.isEmpty();", "            return path.startsWith(prefix);")],
  G("Lesson [Spring Security basics and JWT resource servers](#/lesson/spring/spring-security-jwt). The `spring-java-advice-chain` exercise uses the same chaining idea. Java: lambdas, records, `Comparator`.",
    "A filter chain is the chain-of-responsibility pattern: each filter receives a `Chain` it may call to continue. Authentication only *labels* the request (or rejects a bad credential); authorisation reads that label against ordered URL rules.",
    ["Implement `step(sorted, i, exchange, servlet)`: at the end call the servlet, otherwise add the name to `trace` and call filter `i` with `next -> step(sorted, i + 1, next, servlet)`.",
     "In the bearer filter, a missing header is fine (anonymous); a present but bad header is a 401.",
     "In the authorisation filter, compute `granted`, then choose 401 or 403 from `exchange.user == null`."],
    "A single big `if` chain in the controller works for one endpoint and must be copied into every other one; filters put the policy in one place, ahead of all controllers.",
    r"""```java
private void step(List<Registered> sorted, int i, Exchange exchange, Consumer<Exchange> servlet) {
    if (i == sorted.size()) { exchange.trace.add("servlet"); servlet.accept(exchange); return; }
    Registered r = sorted.get(i);
    exchange.trace.add(r.name());
    r.filter().doFilter(exchange, next -> step(sorted, i + 1, next, servlet));
}
```

**Dry run** `/admin/users` with `Bearer t-bob`: cors proceeds; bearer finds bob with roles `[USER]` and proceeds; authorization matches `/admin/**` → `hasRole:ADMIN`, bob is authenticated but lacks ADMIN → 403, chain ends.

The Spring configuration this models:

```java
@Bean
SecurityFilterChain api(HttpSecurity http) throws Exception {
    return http
        .authorizeHttpRequests(a -> a
            .requestMatchers("/public/**").permitAll()
            .requestMatchers("/admin/**").hasRole("ADMIN")
            .requestMatchers("/api/**").authenticated()
            .anyRequest().denyAll())
        .oauth2ResourceServer(o -> o.jwt(Customizer.withDefaults()))
        .build();
}
```""",
    "O(F + R) per request for F filters and R rules.",
    "- Running filters in insertion order instead of by `order`.\n- 403 for anonymous users (they must get 401 so the client knows to authenticate).\n- `startsWith(\"/admin\")` also matching `/administrator`.\n- Putting a broad rule (`/api/**`) before a narrow one (`/api/public/**`): the first match wins, so order rules from specific to general.",
    "A real JWT filter also verifies the token's signature and its `exp`, `iss` and `aud` claims; see the Python exercise `spring-jwt-validate`."),
  extra=_SF_EXTRA),
]
