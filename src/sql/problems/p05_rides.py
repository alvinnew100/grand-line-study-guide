"""SQL track problems, part 5: analytics interview set on the `rides` dataset."""

STARTER = "-- write your query\nSELECT "

RIDERS = "- `riders(rider_id, name, city, signup_date)`"
DRIVERS = "- `drivers(driver_id, name, city, joined_on, vehicle_type, status)` - `status` is `active` or `inactive`"
TRIPS = ("- `trips(trip_id, rider_id, driver_id, city, requested_at, pickup_at, dropoff_at, distance_km, fare, surge_multiplier, status)` - "
         "`status` is `completed`, `cancelled_by_rider`, `cancelled_by_driver` or `no_show`; `pickup_at`, `dropoff_at`, "
         "`distance_km` and `fare` are NULL unless the trip was completed; timestamps are text like `'2024-03-07 18:22:05'`")
PAYMENTS = "- `payments(payment_id, trip_id, method, amount, tip, paid_at, status)` - `method` is `card`, `wallet` or `cash`; `status` is `succeeded`, `failed` or `refunded`; a trip can have several payment attempts"
RATINGS = "- `ratings(trip_id, driver_stars, rider_stars, comment)` - `driver_stars` is the 1-5 score the rider gave the driver (NULL if not given)"


def P(pid, title, difficulty, pattern, tables, task, columns, order, solution, guide, ordered=True):
    desc = task.strip() + "\n\n**Tables** (dataset `rides`):\n\n" + "\n".join(tables) + "\n\n**Columns, in this order:** " + columns
    desc += "\n\n**Order:** " + order if order else "\n\nAny row order is accepted."
    return dict(id=pid, title=title, difficulty=difficulty, pattern=pattern, kind="sql", dataset="rides",
                description=desc, starter=STARTER, solution=solution.strip(), ordered=ordered, guide=guide)


def G(prereqs, intuition, hints, approach, pitfalls, complexity, follow_up=None):
    g = dict(prereqs=prereqs, intuition=intuition, hints=hints, approach=approach, pitfalls=pitfalls,
             complexity=complexity)
    if follow_up:
        g["follow_up"] = follow_up
    return g


PROBLEMS = [
P("sql-trip-outcome-share", "Trip Outcomes by City", "Easy", "Percent of total",
  [TRIPS],
  "Operations wants to compare reliability across cities. For each city report the number of trip requests and the percentage that ended in each outcome.",
  "`city`, `requests`, `completed_pct`, `rider_cancel_pct`, `driver_cancel_pct`, `no_show_pct` (each rounded to 1)",
  "by `completed_pct` descending, then `city`.",
  """
SELECT city,
       COUNT(*) AS requests,
       ROUND(100.0 * SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) / COUNT(*), 1) AS completed_pct,
       ROUND(100.0 * SUM(CASE WHEN status = 'cancelled_by_rider' THEN 1 ELSE 0 END) / COUNT(*), 1) AS rider_cancel_pct,
       ROUND(100.0 * SUM(CASE WHEN status = 'cancelled_by_driver' THEN 1 ELSE 0 END) / COUNT(*), 1) AS driver_cancel_pct,
       ROUND(100.0 * SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) / COUNT(*), 1) AS no_show_pct
FROM trips
GROUP BY city
ORDER BY completed_pct DESC, city;""",
  G("GROUP BY, CASE inside SUM.",
    "A percentage of a group's rows is 'rows meeting the condition' divided by 'all rows in the group' - both available in one grouped pass.",
    ["Group by `city`.", "`SUM(CASE WHEN status = '...' THEN 1 ELSE 0 END)` counts one outcome.", "Multiply by 100.0 before dividing by `COUNT(*)`."],
    "One scan, four conditional counts, each divided by the group size.",
    "- `100 * x / COUNT(*)` with integers truncates to a whole number.\n- Rounded percentages may sum to 99.9 or 100.1; that is expected.\n- Equivalent shortcut: `AVG(CASE WHEN ... THEN 100.0 ELSE 0 END)`.",
    "Single pass over `trips`.")),

P("sql-idle-active-drivers", "Active Drivers With No Q4 Trips", "Easy", "Anti-join",
  [DRIVERS, TRIPS],
  "Find drivers whose status is `active` but who have **no completed trip requested in the fourth quarter of 2024** (1 Oct - 31 Dec). Show the date of their most recent completed trip ever, or NULL if they have never completed one.",
  "`driver_id`, `name`, `city`, `last_completed_trip` (a date `'YYYY-MM-DD'` or NULL)",
  "by `driver_id`.",
  """
SELECT d.driver_id, d.name, d.city,
       (SELECT date(MAX(t.requested_at)) FROM trips t
        WHERE t.driver_id = d.driver_id AND t.status = 'completed') AS last_completed_trip
FROM drivers d
WHERE d.status = 'active'
  AND NOT EXISTS (SELECT 1 FROM trips t
                  WHERE t.driver_id = d.driver_id
                    AND t.status = 'completed'
                    AND t.requested_at >= '2024-10-01' AND t.requested_at < '2025-01-01')
ORDER BY d.driver_id;""",
  G("NOT EXISTS, half-open date ranges, scalar subqueries.",
    "'No trip in the period' is an anti-join whose inner condition includes the date range. The last-trip date is a separate lookup that ignores the period.",
    ["`NOT EXISTS` with the driver correlation, the status and the Q4 range.", "Use `>= '2024-10-01' AND < '2025-01-01'` so 31 December afternoons are included.", "A correlated `MAX(requested_at)` gives the last completed trip; it is NULL when there is none."],
    "Filter active drivers, anti-join against Q4 completed trips, decorate with a scalar subquery.",
    "- Putting the date filter in an outer WHERE after a LEFT JOIN turns it into an inner join and loses the very drivers you want.\n- `<= '2024-12-31'` misses trips later that day because the column holds timestamps.\n- A driver who never drove must still appear - with NULL.",
    "With an index on `trips(driver_id, requested_at)` each probe is a short range scan.")),

P("sql-tipping-by-payment-method", "Tipping by Payment Method", "Easy", "Conditional aggregation",
  [PAYMENTS],
  "Looking only at payments with status `succeeded`, compare tipping behaviour per payment method: how many payments, how many included a tip, the tipping rate, and the average tip as a percentage of the amount among payments that did include a tip.",
  "`method`, `payments`, `tipped`, `tipped_pct` (rounded to 1), `avg_tip_pct_when_tipped` (rounded to 1)",
  "by `tipped_pct` descending.",
  """
SELECT method,
       COUNT(*) AS payments,
       SUM(CASE WHEN tip > 0 THEN 1 ELSE 0 END) AS tipped,
       ROUND(100.0 * SUM(CASE WHEN tip > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS tipped_pct,
       ROUND(AVG(CASE WHEN tip > 0 THEN 100.0 * tip / amount END), 1) AS avg_tip_pct_when_tipped
FROM payments
WHERE status = 'succeeded'
GROUP BY method
ORDER BY tipped_pct DESC;""",
  G("WHERE vs HAVING, CASE without ELSE inside AVG.",
    "The last column is an average over a *subset* of the group's rows. A CASE with no ELSE returns NULL for the other rows, and AVG ignores NULLs.",
    ["Filter `status = 'succeeded'` in WHERE - it is a row condition.", "Tipped count: `SUM(CASE WHEN tip > 0 THEN 1 ELSE 0 END)`.", "`AVG(CASE WHEN tip > 0 THEN 100.0 * tip / amount END)` averages tippers only."],
    "One grouped pass with a conditional count and a conditional average.",
    "- Adding `ELSE 0` inside the AVG would average in all the non-tippers and understate the figure.\n- Including failed payments counts money that was never collected.\n- Integer division is avoided by the 100.0.",
    "Single pass over `payments`.")),

P("sql-fare-by-distance-band", "Fare per Kilometre by Distance Band", "Easy", "Histograms and bucketing",
  [TRIPS],
  "Pricing wants to know whether short trips cost more per kilometre. Using completed trips, bucket by distance into `'short'` (under 3 km), `'medium'` (3 km up to but not including 8 km) and `'long'` (8 km or more).",
  "`band`, `trips`, `avg_distance_km` (rounded to 2), `avg_fare` (rounded to 2), `avg_fare_per_km` (average of each trip's `fare / distance_km`, rounded to 2)",
  "`'short'`, `'medium'`, `'long'`.",
  """
SELECT CASE WHEN distance_km < 3 THEN 'short'
            WHEN distance_km < 8 THEN 'medium'
            ELSE 'long' END AS band,
       COUNT(*) AS trips,
       ROUND(AVG(distance_km), 2) AS avg_distance_km,
       ROUND(AVG(fare), 2) AS avg_fare,
       ROUND(AVG(fare / distance_km), 2) AS avg_fare_per_km
FROM trips
WHERE status = 'completed'
GROUP BY band
ORDER BY MIN(distance_km);""",
  G("CASE bucketing, GROUP BY an expression, ordering by an aggregate.",
    "Turn a continuous measure into a label with CASE, then group by the label.",
    ["Thresholds in ascending order; the first true branch wins.", "Restrict to completed trips - cancelled ones have NULL distance.", "Order the bands by `MIN(distance_km)` rather than alphabetically."],
    "Filter, label, aggregate, sort by a numeric key.",
    "- Without the status filter, cancelled trips (NULL distance) all fall into the ELSE branch and are labelled 'long'.\n- `AVG(fare) / AVG(distance_km)` is a different (distance-weighted) number from `AVG(fare / distance_km)`.\n- Alphabetical order gives long, medium, short.",
    "Single pass.")),

P("sql-yoy-monthly-trips", "Year-over-Year Trips by Month", "Medium", "Year-over-year growth",
  [TRIPS],
  "Compare completed trips month by month between 2023 and 2024.",
  "`month` (two digits, `'01'` to `'12'`), `trips_2023`, `trips_2024`, `yoy_pct` (`100 * (trips_2024 - trips_2023) / trips_2023`, rounded to 1)",
  "by `month`.",
  """
SELECT strftime('%m', requested_at) AS month,
       SUM(CASE WHEN strftime('%Y', requested_at) = '2023' THEN 1 ELSE 0 END) AS trips_2023,
       SUM(CASE WHEN strftime('%Y', requested_at) = '2024' THEN 1 ELSE 0 END) AS trips_2024,
       ROUND(100.0 * (SUM(CASE WHEN strftime('%Y', requested_at) = '2024' THEN 1 ELSE 0 END)
                    - SUM(CASE WHEN strftime('%Y', requested_at) = '2023' THEN 1 ELSE 0 END))
             / SUM(CASE WHEN strftime('%Y', requested_at) = '2023' THEN 1 ELSE 0 END), 1) AS yoy_pct
FROM trips
WHERE status = 'completed'
GROUP BY month
ORDER BY month;""",
  G("Date parts with `strftime`, pivoting with CASE.",
    "Group by the month *number* so that January 2023 and January 2024 land in the same row, then split the years into columns with conditional sums.",
    ["`strftime('%m', ...)` is the month, `strftime('%Y', ...)` the year - both text.", "One conditional SUM per year.", "Growth = (new - old) / old, with 100.0 to force real division."],
    "Pivot years into columns within month groups; compute the ratio from the two columns.",
    "- `strftime` returns text: compare with `'2023'`, not `2023`.\n- Grouping by `'%Y-%m'` would give 24 rows and nothing to compare.\n- The LAG alternative - `LAG(trips, 12)` over a monthly series - breaks if any month is missing.\n- Guard with NULLIF if a 2023 month could be zero.",
    "Single pass.")),

P("sql-rolling-three-month-revenue", "Rolling Three-Month Revenue", "Medium", "Rolling averages",
  [TRIPS],
  "Finance wants a smoothed revenue trend. For each calendar month compute fare revenue from completed trips and the average revenue over that month and the two months before it. The first two months average over the months available.",
  "`month` (`'YYYY-MM'`), `revenue` (rounded to 2), `rolling_3m_avg` (rounded to 2)",
  "by `month`.",
  """
WITH monthly AS (
  SELECT strftime('%Y-%m', requested_at) AS month, SUM(fare) AS revenue
  FROM trips
  WHERE status = 'completed'
  GROUP BY month
)
SELECT month,
       ROUND(revenue, 2) AS revenue,
       ROUND(AVG(revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS rolling_3m_avg
FROM monthly
ORDER BY month;""",
  G("Window frames (lesson *LAG, LEAD, running totals and frames*).",
    "Aggregate to one row per month first; a sliding frame of three rows then is a three-month window.",
    ["CTE: revenue per month.", "`AVG(revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`.", "Round only in the final SELECT."],
    "Monthly aggregate, then a framed window average.",
    "- A ROWS frame counts rows, not months: it is only a three-month window because every month has data.\n- Averaging raw trips over three months weights busy months more - a different metric.\n- Rounding inside the CTE compounds rounding error.",
    "One aggregate plus one ordered pass.")),

P("sql-top-drivers-per-city", "Top Earning Drivers per City", "Medium", "Top-N per group",
  [TRIPS, DRIVERS],
  "For each city, find the three drivers with the highest total fares from completed trips requested in 2024. Break ties by the smaller `driver_id` so that exactly three drivers are returned per city.",
  "`city`, `position` (1 to 3), `driver_id`, `name`, `trips`, `total_fare` (rounded to 2)",
  "by `city`, then `position`.",
  """
WITH earn AS (
  SELECT t.city, t.driver_id, COUNT(*) AS trips, SUM(t.fare) AS total_fare
  FROM trips t
  WHERE t.status = 'completed'
    AND t.requested_at >= '2024-01-01' AND t.requested_at < '2025-01-01'
  GROUP BY t.city, t.driver_id
), ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY city ORDER BY total_fare DESC, driver_id) AS position
  FROM earn
)
SELECT r.city, r.position, r.driver_id, d.name, r.trips, ROUND(r.total_fare, 2) AS total_fare
FROM ranked r JOIN drivers d ON d.driver_id = r.driver_id
WHERE r.position <= 3
ORDER BY r.city, r.position;""",
  G("ROW_NUMBER with PARTITION BY.",
    "Aggregate to driver totals, number drivers within each city from best to worst, keep numbers 1 to 3.",
    ["Totals per (city, driver) for 2024 completed trips.", "`ROW_NUMBER() OVER (PARTITION BY city ORDER BY total_fare DESC, driver_id)`.", "Filter on the row number in an outer query, then join for names."],
    "Aggregate, rank, filter, decorate. ROW_NUMBER with a tie-breaker guarantees exactly three rows per city.",
    "- `ORDER BY ... LIMIT 3` gives three rows overall, not per city.\n- Ranking the rounded totals can create false ties.\n- Joining `drivers` before aggregating is fine but adds columns to the GROUP BY.",
    "One sort per city.")),

P("sql-rider-first-and-latest-trip", "First and Latest Trip per Rider", "Medium", "First and last event per user",
  [TRIPS],
  "For every rider with at least 10 completed trips, show when their first and their most recent completed trips were requested and what each of those two trips cost.",
  "`rider_id`, `trips`, `first_trip` (timestamp), `first_fare`, `latest_trip` (timestamp), `latest_fare`",
  "by `trips` descending, then `rider_id`.",
  """
WITH c AS (
  SELECT rider_id, requested_at, fare,
         ROW_NUMBER() OVER (PARTITION BY rider_id ORDER BY requested_at, trip_id) AS rn_first,
         ROW_NUMBER() OVER (PARTITION BY rider_id ORDER BY requested_at DESC, trip_id DESC) AS rn_last,
         COUNT(*) OVER (PARTITION BY rider_id) AS trips
  FROM trips
  WHERE status = 'completed'
)
SELECT rider_id, MAX(trips) AS trips,
       MAX(CASE WHEN rn_first = 1 THEN requested_at END) AS first_trip,
       MAX(CASE WHEN rn_first = 1 THEN fare END) AS first_fare,
       MAX(CASE WHEN rn_last = 1 THEN requested_at END) AS latest_trip,
       MAX(CASE WHEN rn_last = 1 THEN fare END) AS latest_fare
FROM c
GROUP BY rider_id
HAVING MAX(trips) >= 10
ORDER BY trips DESC, rider_id;""",
  G("ROW_NUMBER in both directions, pivoting with MAX(CASE).",
    "`MIN(requested_at)` finds the first time but not the fare *of that trip*. Number the rows from both ends, then pick the row numbered 1 in each direction.",
    ["Two ROW_NUMBERs: ascending and descending by time.", "`COUNT(*) OVER (PARTITION BY rider_id)` carries the trip count.", "Collapse per rider with `MAX(CASE WHEN rn = 1 THEN ... END)`."],
    "Window pass, then one grouped pivot. `FIRST_VALUE` / `LAST_VALUE` with a full frame is an equivalent formulation.",
    "- `SELECT rider_id, MIN(requested_at), fare ... GROUP BY rider_id` returns an arbitrary fare in SQLite and is an error elsewhere.\n- `LAST_VALUE` with the default frame returns the current row.\n- Without a tie-breaker two trips at the same second make the result non-deterministic.",
    "Two sorts per rider partition.")),

P("sql-cancellations-by-daypart", "Cancellations by Time of Day", "Medium", "Date arithmetic",
  [TRIPS],
  "Do requests fail more often at certain times? Split each request by the hour of `requested_at` into `'night'` (00-05), `'morning'` (06-11), `'afternoon'` (12-17) and `'evening'` (18-23). A request *failed* if its status is anything other than `completed`.",
  "`daypart`, `requests`, `failed`, `failed_pct` (rounded to 1)",
  "`'night'`, `'morning'`, `'afternoon'`, `'evening'`.",
  """
SELECT CASE WHEN CAST(strftime('%H', requested_at) AS INTEGER) < 6 THEN 'night'
            WHEN CAST(strftime('%H', requested_at) AS INTEGER) < 12 THEN 'morning'
            WHEN CAST(strftime('%H', requested_at) AS INTEGER) < 18 THEN 'afternoon'
            ELSE 'evening' END AS daypart,
       COUNT(*) AS requests,
       SUM(CASE WHEN status <> 'completed' THEN 1 ELSE 0 END) AS failed,
       ROUND(100.0 * SUM(CASE WHEN status <> 'completed' THEN 1 ELSE 0 END) / COUNT(*), 1) AS failed_pct
FROM trips
GROUP BY daypart
ORDER BY MIN(CAST(strftime('%H', requested_at) AS INTEGER));""",
  G("`strftime` date parts, CAST, CASE bucketing.",
    "Extract the hour as a number, bucket it, and compute a failure rate per bucket.",
    ["`strftime('%H', requested_at)` is text such as `'07'`; CAST it to INTEGER before comparing with numbers.", "Bucket with a searched CASE in ascending order.", "Order by the smallest hour in each bucket."],
    "Derive the hour, label, aggregate, sort by a numeric key.",
    "- Comparing the text `'07' < 6` uses text-versus-number rules and gives wrong buckets.\n- Alphabetical order would be afternoon, evening, morning, night.\n- MySQL: `HOUR(requested_at)`; PostgreSQL: `EXTRACT(HOUR FROM requested_at)`.",
    "Single pass.")),

P("sql-unpaid-completed-trips", "Completed Trips Without a Successful Payment", "Medium", "NULL handling traps",
  [TRIPS, PAYMENTS],
  "Revenue assurance: list completed trips requested in 2024 that have **no payment with status `succeeded`**. Classify each as `'no payment record'` (no payment rows at all), `'refunded'` (at least one refunded payment) or `'failed only'`.",
  "`trip_id`, `fare`, `payment_attempts`, `issue`",
  "by `fare` descending, then `trip_id`.",
  """
SELECT t.trip_id, t.fare,
       COUNT(p.payment_id) AS payment_attempts,
       CASE WHEN COUNT(p.payment_id) = 0 THEN 'no payment record'
            WHEN SUM(CASE WHEN p.status = 'refunded' THEN 1 ELSE 0 END) > 0 THEN 'refunded'
            ELSE 'failed only' END AS issue
FROM trips t
LEFT JOIN payments p ON p.trip_id = t.trip_id
WHERE t.status = 'completed'
  AND t.requested_at >= '2024-01-01' AND t.requested_at < '2025-01-01'
GROUP BY t.trip_id, t.fare
HAVING SUM(CASE WHEN p.status = 'succeeded' THEN 1 ELSE 0 END) = 0
ORDER BY t.fare DESC, t.trip_id;""",
  G("LEFT JOIN, COUNT(column), HAVING with conditional sums.",
    "Keep every completed trip, attach whatever payment rows exist, and keep the trips whose attached rows contain no success. A trip with no rows at all must survive too.",
    ["`trips LEFT JOIN payments` - an inner join would lose trips with no payment record.", "`HAVING SUM(CASE WHEN p.status = 'succeeded' THEN 1 ELSE 0 END) = 0`.", "`COUNT(p.payment_id)` is 0 for the NULL-padded row."],
    "Outer join, group per trip, filter groups with a conditional sum, classify with CASE over aggregates.",
    "- `WHERE p.status <> 'succeeded'` is wrong twice: it drops trips with no payments (NULL), and keeps trips that failed once and then succeeded.\n- `COUNT(*)` would report 1 attempt for trips with none.\n- Trip-level filters belong in WHERE, the payment condition in HAVING.",
    "Linear in payments with an index on `payments(trip_id)`.")),

P("sql-driver-rating-ranks", "Driver Rating Ranks", "Medium", "Ranking with ties",
  [TRIPS, RATINGS, DRIVERS],
  "Rank drivers by their average `driver_stars`, considering only drivers with at least 25 rated trips (trips where `driver_stars` is not NULL). Round the average to 2 decimals and rank on the rounded value with **dense** ranking, so drivers with equal averages share a rank and no ranks are skipped.",
  "`rnk`, `driver_id`, `name`, `rated_trips`, `avg_stars`",
  "by `rnk`, then `driver_id`.",
  """
WITH s AS (
  SELECT t.driver_id, COUNT(r.driver_stars) AS rated_trips, ROUND(AVG(r.driver_stars), 2) AS avg_stars
  FROM trips t
  JOIN ratings r ON r.trip_id = t.trip_id
  GROUP BY t.driver_id
  HAVING COUNT(r.driver_stars) >= 25
)
SELECT DENSE_RANK() OVER (ORDER BY s.avg_stars DESC) AS rnk,
       s.driver_id, d.name, s.rated_trips, s.avg_stars
FROM s JOIN drivers d ON d.driver_id = s.driver_id
ORDER BY rnk, s.driver_id;""",
  G("Aggregates and NULLs, HAVING, DENSE_RANK.",
    "AVG and COUNT(column) already ignore missing ratings. Compute per-driver statistics, keep drivers with enough evidence, and rank what remains.",
    ["`COUNT(r.driver_stars)` counts rated trips only.", "The minimum-sample rule is a HAVING condition.", "`DENSE_RANK() OVER (ORDER BY avg_stars DESC)` over the filtered rows."],
    "Aggregate with a HAVING threshold, then apply the window - windows run after HAVING, so only qualifying drivers are ranked.",
    "- `COUNT(*) >= 25` counts rating rows whose driver score is NULL.\n- Ranking before applying the threshold leaves gaps in the ranks.\n- A minimum sample size matters: one 5-star trip should not top the board.",
    "Aggregate plus one sort.")),

P("sql-city-revenue-ytd", "Year-to-Date Revenue by City", "Medium", "Running totals",
  [TRIPS],
  "For each city and each month of 2024, report fare revenue from completed trips and the cumulative revenue since 1 January 2024 for that city.",
  "`city`, `month` (`'YYYY-MM'`), `revenue` (rounded to 2), `ytd_revenue` (rounded to 2)",
  "by `city`, then `month`.",
  """
WITH m AS (
  SELECT city, strftime('%Y-%m', requested_at) AS month, SUM(fare) AS revenue
  FROM trips
  WHERE status = 'completed'
    AND requested_at >= '2024-01-01' AND requested_at < '2025-01-01'
  GROUP BY city, month
)
SELECT city, month,
       ROUND(revenue, 2) AS revenue,
       ROUND(SUM(revenue) OVER (PARTITION BY city ORDER BY month
                                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS ytd_revenue
FROM m
ORDER BY city, month;""",
  G("Cumulative window aggregates with PARTITION BY.",
    "A running total is `SUM(...) OVER (ORDER BY ...)`; adding PARTITION BY restarts it for each city.",
    ["Aggregate to (city, month) first.", "`SUM(revenue) OVER (PARTITION BY city ORDER BY month ...)`.", "State the frame explicitly with ROWS."],
    "Monthly aggregate, partitioned cumulative sum.",
    "- Omitting PARTITION BY accumulates across cities.\n- Applying the window to raw trips gives a per-trip running total, not per month.\n- Filtering the year *after* the window would let 2023 revenue leak into the running total; filter first.",
    "One sort by (city, month).")),

P("sql-loyal-rider-driver-pairs", "Riders Who Keep Getting the Same Driver", "Medium", "Percent of total within a group",
  [TRIPS],
  "Find rider-driver pairs with at least 8 completed trips together, and show what share of that rider's completed trips was with that driver.",
  "`rider_id`, `driver_id`, `trips_together`, `rider_trips`, `pct_of_rider_trips` (rounded to 1)",
  "by `trips_together` descending, then `rider_id`, then `driver_id`.",
  """
WITH pairs AS (
  SELECT rider_id, driver_id, COUNT(*) AS trips_together
  FROM trips
  WHERE status = 'completed'
  GROUP BY rider_id, driver_id
), shared AS (
  SELECT *, SUM(trips_together) OVER (PARTITION BY rider_id) AS rider_trips
  FROM pairs
)
SELECT rider_id, driver_id, trips_together, rider_trips,
       ROUND(100.0 * trips_together / rider_trips, 1) AS pct_of_rider_trips
FROM shared
WHERE trips_together >= 8
ORDER BY trips_together DESC, rider_id, driver_id;""",
  G("Window aggregates over grouped rows.",
    "The denominator (all of a rider's trips) must be computed over *all* that rider's pairs, before the small pairs are filtered out.",
    ["Count trips per (rider, driver).", "`SUM(trips_together) OVER (PARTITION BY rider_id)` gives the rider's total on every row.", "Filter `>= 8` only in the final query."],
    "Aggregate pairs, add a partition total with a window, then filter.",
    "- Using `HAVING COUNT(*) >= 8` in the first CTE removes small pairs before the total is computed, shrinking the denominator and inflating every percentage.\n- This is why the order of 'window' and 'filter' matters.",
    "One aggregate and one partitioned pass.")),

P("sql-busiest-weekday-per-city", "Busiest Weekday in Each City", "Medium", "Top-N per group",
  [TRIPS],
  "For each city, find the day of the week with the most trip requests (any status). If several weekdays tie, return all of them.",
  "`city`, `weekday` (`'Sunday'` ... `'Saturday'`), `requests`",
  "by `city`, then `weekday`.",
  """
WITH w AS (
  SELECT city, strftime('%w', requested_at) AS dow, COUNT(*) AS requests
  FROM trips
  GROUP BY city, dow
), r AS (
  SELECT *, RANK() OVER (PARTITION BY city ORDER BY requests DESC) AS rnk
  FROM w
)
SELECT city,
       CASE dow WHEN '0' THEN 'Sunday' WHEN '1' THEN 'Monday' WHEN '2' THEN 'Tuesday'
                WHEN '3' THEN 'Wednesday' WHEN '4' THEN 'Thursday' WHEN '5' THEN 'Friday'
                ELSE 'Saturday' END AS weekday,
       requests
FROM r
WHERE rnk = 1
ORDER BY city, weekday;""",
  G("`strftime('%w')`, RANK, simple CASE.",
    "Count requests per (city, weekday), rank weekdays inside each city, keep rank 1. RANK keeps ties; ROW_NUMBER would drop them.",
    ["`strftime('%w', ts)` returns '0' (Sunday) to '6' (Saturday) as text.", "`RANK() OVER (PARTITION BY city ORDER BY requests DESC)`.", "Translate the digit to a name with a simple CASE."],
    "Aggregate, rank, filter rank 1, label.",
    "- The weekday code is text: compare with `'0'`, not `0`.\n- ROW_NUMBER silently picks one of several tied weekdays.\n- MySQL: `DAYNAME(ts)`; PostgreSQL: `to_char(ts, 'FMDay')`.",
    "One aggregate plus a tiny sort per city.")),

P("sql-median-fare-by-city", "Median Fare by City", "Hard", "Median without built-ins",
  [TRIPS],
  "SQLite has no MEDIAN function. Compute the median fare of completed trips in each city. With an even number of trips, the median is the average of the two middle fares.",
  "`city`, `trips`, `median_fare` (rounded to 2), `mean_fare` (rounded to 2)",
  "by `city`.",
  """
WITH f AS (
  SELECT city, fare,
         ROW_NUMBER() OVER (PARTITION BY city ORDER BY fare) AS rn,
         COUNT(*) OVER (PARTITION BY city) AS n,
         AVG(fare) OVER (PARTITION BY city) AS mean_fare
  FROM trips
  WHERE status = 'completed'
)
SELECT city, MAX(n) AS trips,
       ROUND(AVG(fare), 2) AS median_fare,
       ROUND(MAX(mean_fare), 2) AS mean_fare
FROM f
WHERE rn IN ((n + 1) / 2, (n + 2) / 2)
GROUP BY city
ORDER BY city;""",
  G("ROW_NUMBER, COUNT(*) OVER, integer division.",
    "Sort each city's fares and number them. The median is the middle row, or the mean of the two middle rows. With integer division `(n+1)/2` and `(n+2)/2` are the same position when n is odd and the two middle positions when n is even.",
    ["Number fares within each city and carry the partition size `n`.", "Keep rows where `rn IN ((n + 1) / 2, (n + 2) / 2)`.", "Average the one or two rows kept; the mean must be computed before that filter (a window does it)."],
    "Dry run: n = 6 -> positions 3 and 4; n = 7 -> position 4 twice. Averaging the kept rows yields the median.",
    "- Computing `AVG(fare)` for the mean *after* filtering to the middle rows just returns the median again.\n- PostgreSQL has `percentile_cont(0.5) WITHIN GROUP (ORDER BY fare)`.\n- Fares are right-skewed, so the mean exceeds the median.",
    "One sort per city: O(n log n).")),

P("sql-pickup-wait-percentiles", "Pickup Wait Percentiles", "Hard", "Percentiles without built-ins",
  [TRIPS],
  "The pickup wait of a completed trip is the time from `requested_at` to `pickup_at`, in minutes. For each city report the median (p50) and 90th percentile (p90) wait using the **nearest-rank** method: sort the n waits ascending and take the value at position `ceil(p * n)`. (Hint: without a ceiling function, `ceil(0.9 * n)` equals `(9 * n + 9) / 10` and `ceil(0.5 * n)` equals `(n + 1) / 2` in integer arithmetic.)",
  "`city`, `trips`, `p50_wait_min`, `p90_wait_min` (both rounded to 1), `max_wait_min` (rounded to 1)",
  "by `p90_wait_min` descending, then `city`.",
  """
WITH w AS (
  SELECT city, (julianday(pickup_at) - julianday(requested_at)) * 1440 AS wait_min
  FROM trips
  WHERE status = 'completed'
), n AS (
  SELECT city, wait_min,
         ROW_NUMBER() OVER (PARTITION BY city ORDER BY wait_min) AS rn,
         COUNT(*) OVER (PARTITION BY city) AS n
  FROM w
)
SELECT city, MAX(n) AS trips,
       ROUND(MAX(CASE WHEN rn = (n + 1) / 2 THEN wait_min END), 1) AS p50_wait_min,
       ROUND(MAX(CASE WHEN rn = (9 * n + 9) / 10 THEN wait_min END), 1) AS p90_wait_min,
       ROUND(MAX(wait_min), 1) AS max_wait_min
FROM n
GROUP BY city
ORDER BY p90_wait_min DESC, city;""",
  G("Date arithmetic with `julianday`, ROW_NUMBER, MAX(CASE).",
    "A percentile is 'the value at a certain position in the sorted list'. Number the sorted waits, compute the target position from n, and pick that row.",
    ["Minutes between timestamps: `(julianday(b) - julianday(a)) * 1440`.", "ROW_NUMBER and COUNT(*) OVER per city.", "`MAX(CASE WHEN rn = position THEN wait_min END)` picks the row at a position; integer arithmetic replaces ceil."],
    "Compute waits, number them, pick positions `(n+1)/2` and `(9n+9)/10` per city in one grouped pass.",
    "- The browser SQLite has no `ceil`; `(9 * n + 9) / 10` is the integer ceiling of 0.9 n.\n- Averages hide the slow tail - percentiles are how wait-time targets are stated.\n- Interpolated percentiles (`percentile_cont`) give slightly different values than nearest-rank.",
    "One sort per city.")),

P("sql-driver-cancellation-runs", "Drivers Cancelling Several Trips in a Row", "Hard", "Gaps and islands",
  [TRIPS],
  "Flag drivers who cancelled **three or more consecutive trips**: order each driver's trips by `requested_at`, and look for an unbroken run of rows whose status is `cancelled_by_driver`.",
  "`driver_id`, `run_length`, `run_start`, `run_end` (the `requested_at` of the first and last trip in the run)",
  "by `run_length` descending, then `driver_id`, then `run_start`.",
  """
WITH s AS (
  SELECT driver_id, requested_at, status,
         ROW_NUMBER() OVER (PARTITION BY driver_id ORDER BY requested_at, trip_id)
       - ROW_NUMBER() OVER (PARTITION BY driver_id, status ORDER BY requested_at, trip_id) AS grp
  FROM trips
)
SELECT driver_id, COUNT(*) AS run_length,
       MIN(requested_at) AS run_start, MAX(requested_at) AS run_end
FROM s
WHERE status = 'cancelled_by_driver'
GROUP BY driver_id, grp
HAVING COUNT(*) >= 3
ORDER BY run_length DESC, driver_id, run_start;""",
  G("Gaps and islands with two row numbers.",
    "Number a driver's trips overall, and separately within each status. Inside an unbroken run of one status both counters advance together, so their difference stays constant; when another status interrupts, the difference changes.",
    ["`ROW_NUMBER() OVER (PARTITION BY driver_id ORDER BY requested_at)` minus `ROW_NUMBER() OVER (PARTITION BY driver_id, status ORDER BY requested_at)`.", "Group by (driver, status, difference) - each group is one run.", "Keep cancelled-by-driver runs of length 3 or more."],
    "Difference of two row numbers as the island key, then aggregate and filter. A flag-and-running-sum formulation (new group whenever status differs from LAG) works equally well.",
    "- The difference alone is not unique across statuses; group by status too (here the WHERE does it).\n- Counting total cancellations per driver misses the 'consecutive' requirement.\n- Add `trip_id` as a tie-breaker so equal timestamps cannot reorder rows.",
    "Two sorts per driver.")),

P("sql-rider-lifecycle-by-month", "Rider Lifecycle: New, Retained, Reactivated, Churned", "Hard", "Churn and reactivation",
  [TRIPS],
  "A rider is *active* in a month if they completed at least one trip requested in it. For each month of 2024 classify active riders as **new** (first active month ever), **retained** (also active in the previous month) or **reactivated** (active before, but not in the previous month), and count **churned** riders (active in the previous month but not in this one).",
  "`month` (`'YYYY-MM'`), `new_riders`, `retained`, `reactivated`, `churned`",
  "by `month`.",
  """
WITH m AS (
  SELECT DISTINCT rider_id,
         CAST(strftime('%Y', requested_at) AS INTEGER) * 12 + CAST(strftime('%m', requested_at) AS INTEGER) AS idx
  FROM trips
  WHERE status = 'completed'
), l AS (
  SELECT rider_id, idx,
         LAG(idx)  OVER (PARTITION BY rider_id ORDER BY idx) AS prev_idx,
         LEAD(idx) OVER (PARTITION BY rider_id ORDER BY idx) AS next_idx
  FROM m
), active AS (
  SELECT idx,
         SUM(CASE WHEN prev_idx IS NULL THEN 1 ELSE 0 END) AS new_riders,
         SUM(CASE WHEN prev_idx = idx - 1 THEN 1 ELSE 0 END) AS retained,
         SUM(CASE WHEN prev_idx < idx - 1 THEN 1 ELSE 0 END) AS reactivated
  FROM l GROUP BY idx
), churn AS (
  SELECT idx + 1 AS idx, COUNT(*) AS churned
  FROM l
  WHERE next_idx IS NULL OR next_idx > idx + 1
  GROUP BY idx + 1
)
SELECT printf('%04d-%02d', (a.idx - 1) / 12, (a.idx - 1) % 12 + 1) AS month,
       a.new_riders, a.retained, a.reactivated, COALESCE(c.churned, 0) AS churned
FROM active a
LEFT JOIN churn c ON c.idx = a.idx
WHERE a.idx BETWEEN 2024 * 12 + 1 AND 2024 * 12 + 12
ORDER BY a.idx;""",
  G("LAG / LEAD, month index arithmetic, multi-step CTEs.",
    "Reduce activity to one row per rider per month, numbered with a month index (year x 12 + month) so that consecutive months differ by exactly 1. Each row's state follows from the gap to the rider's previous active month; a churn event belongs to the month *after* a rider's last consecutive active month.",
    ["Distinct (rider, month index).", "`LAG(idx)` gives the previous active month: NULL = new, idx-1 = retained, older = reactivated.", "`LEAD(idx)`: if the next active month is not idx+1, the rider churned in month idx+1."],
    "Four CTEs: rider-months, neighbours, active-state counts, churn counts shifted forward one month; join and convert the index back to a label.",
    "- Dividing day differences by 30 is not month arithmetic.\n- Churn is counted in the month the rider is *absent*, so it needs a shift, and riders whose last activity is in the final month of data are counted as churned in a month outside the report (correctly excluded).\n- Identity check: active(m) = active(m-1) - churned(m) + new(m) + reactivated(m).",
    "One sort by (rider, month) plus small aggregates.")),
]
