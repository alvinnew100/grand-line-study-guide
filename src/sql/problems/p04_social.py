"""SQL track problems, part 4: analytics interview set on the `social` dataset."""

STARTER = "-- write your query\nSELECT "

USERS = "- `users(user_id, username, full_name, country, joined_on, is_verified)`"
POSTS = "- `posts(post_id, user_id, created_at, post_type, topic, char_count)` - `post_type` is `text`, `photo`, `video` or `link`; `created_at` is text like `'2024-10-07 18:22:05'`"
LIKES = "- `likes(like_id, user_id, post_id, liked_at)` - at most one like per user per post"
FOLLOWS = "- `follows(follower_id, followee_id, followed_at)` - one row means *follower* follows *followee*"
MESSAGES = "- `messages(message_id, sender_id, receiver_id, sent_at, read_at)` - `read_at` is NULL while unread"
COMMENTS = "- `comments(comment_id, post_id, user_id, parent_comment_id, created_at)` - `parent_comment_id` is NULL for a top-level comment, otherwise the comment it replies to"


def P(pid, title, difficulty, pattern, tables, task, columns, order, solution, guide, ordered=True):
    desc = task.strip() + "\n\n**Tables** (dataset `social`):\n\n" + "\n".join(tables) + "\n\n**Columns, in this order:** " + columns
    desc += "\n\n**Order:** " + order if order else "\n\nAny row order is accepted."
    return dict(id=pid, title=title, difficulty=difficulty, pattern=pattern, kind="sql", dataset="social",
                description=desc, starter=STARTER, solution=solution.strip(), ordered=ordered, guide=guide)


def G(prereqs, intuition, hints, approach, pitfalls, complexity, follow_up=None):
    g = dict(prereqs=prereqs, intuition=intuition, hints=hints, approach=approach, pitfalls=pitfalls,
             complexity=complexity)
    if follow_up:
        g["follow_up"] = follow_up
    return g


PROBLEMS = [
P("sql-post-type-mix", "Monthly Post Mix", "Easy", "Conditional aggregation",
  [POSTS],
  "The content team wants to see how the mix of post formats changes over time. For each calendar month, count the posts of each type, side by side.",
  "`month` (`'YYYY-MM'`), `text_posts`, `photo_posts`, `video_posts`, `link_posts`, `total_posts`",
  "by `month`.",
  """
SELECT strftime('%Y-%m', created_at) AS month,
       SUM(CASE WHEN post_type = 'text'  THEN 1 ELSE 0 END) AS text_posts,
       SUM(CASE WHEN post_type = 'photo' THEN 1 ELSE 0 END) AS photo_posts,
       SUM(CASE WHEN post_type = 'video' THEN 1 ELSE 0 END) AS video_posts,
       SUM(CASE WHEN post_type = 'link'  THEN 1 ELSE 0 END) AS link_posts,
       COUNT(*) AS total_posts
FROM posts
GROUP BY month
ORDER BY month;""",
  G("CASE inside aggregates (lesson *CASE patterns*), `strftime`.",
    "Each output column is a count that only 'sees' one post type. A CASE that yields 1 for the wanted type and 0 otherwise, summed per month, is that count.",
    ["Group by the month label `strftime('%Y-%m', created_at)`.",
     "One `SUM(CASE WHEN post_type = '...' THEN 1 ELSE 0 END)` per type.",
     "`COUNT(*)` gives the row total for the month."],
    "One scan of `posts`: bucket by month, compute four conditional sums and a count, sort by the month label (which sorts chronologically because it is `YYYY-MM`).",
    "- `COUNT(CASE WHEN ... THEN 1 ELSE 0 END)` counts every row, because 0 is not NULL. Use SUM, or COUNT with no ELSE.\n- Grouping by a month *name* would merge the same month of different years and sort alphabetically.\n- PostgreSQL: `to_char(created_at, 'YYYY-MM')` and `COUNT(*) FILTER (WHERE post_type = 'text')`.",
    "Single pass plus a sort of four groups.")),

P("sql-users-who-never-posted", "Lurkers: Users Who Never Posted", "Easy", "Anti-join",
  [USERS, POSTS],
  "Growth wants to email people who signed up but have never published anything. List every user with no posts.",
  "`user_id`, `username`, `joined_on`",
  "by `joined_on`, then `user_id`.",
  """
SELECT u.user_id, u.username, u.joined_on
FROM users u
WHERE NOT EXISTS (SELECT 1 FROM posts p WHERE p.user_id = u.user_id)
ORDER BY u.joined_on, u.user_id;""",
  G("EXISTS / NOT EXISTS, outer joins.",
    "Ask a yes/no question per user: is there at least one post by this user? Keep the users for whom the answer is no.",
    ["A correlated subquery can refer to `u.user_id`.",
     "`NOT EXISTS (SELECT 1 FROM posts p WHERE p.user_id = u.user_id)`.",
     "Equivalent: `LEFT JOIN posts ... WHERE p.post_id IS NULL`."],
    "An anti-join. The engine probes `posts` for each user and stops at the first match; users with no match survive.",
    "- `NOT IN (SELECT user_id FROM posts)` works here only because `posts.user_id` is NOT NULL; with a nullable column it would return nothing.\n- An inner join can never answer a 'never' question: it only returns users who *do* have posts.",
    "With an index on `posts(user_id)` each probe is O(log n).",
    "Users who never posted but did like something (combine with EXISTS on `likes`).")),

P("sql-topic-audience-sets", "Tech and Travel, but Never Memes", "Easy", "Set operations",
  [POSTS],
  "An advertiser wants authors who have posted about **both** `tech` and `travel`, but have **never** posted about `memes`. Solve it with set operators.",
  "`user_id`",
  "ascending.",
  """
SELECT user_id FROM posts WHERE topic = 'tech'
INTERSECT
SELECT user_id FROM posts WHERE topic = 'travel'
EXCEPT
SELECT user_id FROM posts WHERE topic = 'memes'
ORDER BY user_id;""",
  G("UNION / INTERSECT / EXCEPT (module *Working with sets*).",
    "Each topic defines a set of authors. 'Both' is an intersection; 'but never' is a set difference. One row can only have one topic, so a plain WHERE with AND cannot express this.",
    ["Write one SELECT of `user_id` per topic.", "INTERSECT the first two sets, then EXCEPT the third.", "One ORDER BY at the very end."],
    "Three de-duplicated sets combined top to bottom: (tech INTERSECT travel) EXCEPT memes. Here SQLite's top-to-bottom evaluation and the standard's INTERSECT-first rule agree.",
    "- `WHERE topic = 'tech' AND topic = 'travel'` is always false.\n- Writing the EXCEPT first changes the meaning, and operator precedence differs between engines when INTERSECT comes last - use a CTE if in doubt.\n- MySQL before 8.0.31 lacks INTERSECT/EXCEPT; use `GROUP BY user_id HAVING SUM(topic='tech') > 0 AND SUM(topic='travel') > 0 AND SUM(topic='memes') = 0`.",
    "Sort or hash each input: O(n log n).")),

P("sql-unread-message-rate", "Unread Message Rate", "Easy", "NULL handling",
  [MESSAGES],
  "For every user who has received at least 5 messages, report how many they received, how many are still unread (`read_at` is NULL) and the unread percentage.",
  "`receiver_id`, `received`, `unread`, `unread_pct` (`100.0 * unread / received`, rounded to 1)",
  "by `unread_pct` descending, then `receiver_id`.",
  """
SELECT receiver_id,
       COUNT(*) AS received,
       COUNT(*) - COUNT(read_at) AS unread,
       ROUND(100.0 * (COUNT(*) - COUNT(read_at)) / COUNT(*), 1) AS unread_pct
FROM messages
GROUP BY receiver_id
HAVING COUNT(*) >= 5
ORDER BY unread_pct DESC, receiver_id;""",
  G("COUNT(*) versus COUNT(column), HAVING.",
    "`COUNT(read_at)` counts only the messages that have a read time. The difference from `COUNT(*)` is the number of NULLs - the unread ones.",
    ["Group by `receiver_id`.", "Unread = `COUNT(*) - COUNT(read_at)` or `SUM(read_at IS NULL)`.", "Filter groups with `HAVING COUNT(*) >= 5`."],
    "One grouped pass. NULL-aware counting does the work; no CASE is needed.",
    "- `WHERE read_at = NULL` matches nothing - use IS NULL.\n- `100 * unread / received` is integer division; multiply by 100.0.\n- Putting `COUNT(*) >= 5` in WHERE is an error: it is a group condition.",
    "Single pass over `messages`.")),

P("sql-likes-per-post-type", "Engagement by Post Type", "Easy", "Percent of total",
  [POSTS, LIKES],
  "Compare formats: for each `post_type`, report the number of posts, the total likes they received, the average likes per post, and that type's share of all likes. Posts with no likes must count as zero-like posts.",
  "`post_type`, `posts`, `likes`, `avg_likes` (rounded to 2), `pct_of_likes` (rounded to 1)",
  "by `avg_likes` descending.",
  """
SELECT p.post_type,
       COUNT(DISTINCT p.post_id) AS posts,
       COUNT(l.like_id) AS likes,
       ROUND(1.0 * COUNT(l.like_id) / COUNT(DISTINCT p.post_id), 2) AS avg_likes,
       ROUND(100.0 * COUNT(l.like_id) / (SELECT COUNT(*) FROM likes), 1) AS pct_of_likes
FROM posts p
LEFT JOIN likes l ON l.post_id = p.post_id
GROUP BY p.post_type
ORDER BY avg_likes DESC;""",
  G("LEFT JOIN, COUNT(column), scalar subqueries.",
    "Start from posts so that unliked posts are kept, attach likes, and count at two different grains from the same joined rows: distinct posts and like rows.",
    ["`posts LEFT JOIN likes` keeps posts with zero likes.", "After the join one row is one like (or one unliked post): use `COUNT(DISTINCT p.post_id)` for posts and `COUNT(l.like_id)` for likes.", "Divide by the grand total of likes for the share."],
    "Left join, group by type, count each grain correctly, compute the ratio and the share (a scalar subquery or `SUM(...) OVER ()`).",
    "- An inner join drops unliked posts and inflates the average.\n- `COUNT(*)` would count an unliked post's padded row as a like.\n- Integer division: multiply by 1.0 / 100.0.",
    "Linear in likes with an index on `likes(post_id)`.")),

P("sql-top-posts-per-topic", "Top Posts in Each Topic", "Medium", "Top-N per group",
  [POSTS, LIKES],
  "For each topic, return the posts ranked in the top 2 by number of likes. Posts tied on like count share a rank, so a topic can return more than two posts (use `DENSE_RANK`). Posts with zero likes are not eligible.",
  "`topic`, `post_id`, `likes`, `rnk`",
  "by `topic`, then `rnk`, then `post_id`.",
  """
WITH counts AS (
  SELECT p.topic, p.post_id, COUNT(*) AS likes
  FROM posts p JOIN likes l ON l.post_id = p.post_id
  GROUP BY p.topic, p.post_id
), ranked AS (
  SELECT topic, post_id, likes,
         DENSE_RANK() OVER (PARTITION BY topic ORDER BY likes DESC) AS rnk
  FROM counts
)
SELECT topic, post_id, likes, rnk
FROM ranked
WHERE rnk <= 2
ORDER BY topic, rnk, post_id;""",
  G("Window ranking functions (lesson *Window basics and ranking*).",
    "Aggregate to one row per post, rank the posts inside each topic, then keep the best ranks. Window results cannot be filtered in the same SELECT, hence the CTE.",
    ["Step 1: likes per post (an inner join already excludes zero-like posts).", "Step 2: `DENSE_RANK() OVER (PARTITION BY topic ORDER BY likes DESC)`.", "Step 3: filter `rnk <= 2` in an outer query."],
    "Aggregate, rank, filter: the standard top-N-per-group recipe. DENSE_RANK gives 1, 2 to the two highest *distinct* like counts.",
    "- ROW_NUMBER would break ties arbitrarily and return exactly two rows; RANK would skip rank 2 after a tie for first.\n- `WHERE DENSE_RANK() ... <= 2` is not allowed; wrap it.\n- Ranking likes rows instead of per-post totals ranks the wrong thing.",
    "One sort per topic partition: O(n log n).")),

P("sql-mutual-follows", "Mutual Follows", "Medium", "Self-join pairs",
  [FOLLOWS, USERS],
  "Two users are *mutuals* when each follows the other. List every mutual pair once, with the smaller `user_id` first, and both usernames.",
  "`user_a`, `username_a`, `user_b`, `username_b`",
  "by `user_a`, then `user_b`.",
  """
SELECT f1.follower_id AS user_a, ua.username AS username_a,
       f1.followee_id AS user_b, ub.username AS username_b
FROM follows f1
JOIN follows f2 ON f2.follower_id = f1.followee_id
               AND f2.followee_id = f1.follower_id
JOIN users ua ON ua.user_id = f1.follower_id
JOIN users ub ON ub.user_id = f1.followee_id
WHERE f1.follower_id < f1.followee_id
ORDER BY user_a, user_b;""",
  G("Self joins (lesson *Three or more tables, self joins and non-equi joins*).",
    "A mutual pair is a row (A follows B) for which the mirrored row (B follows A) also exists. Join the table to its own mirror image.",
    ["Join `follows f1` to `follows f2` with follower and followee swapped.", "Every pair appears twice (A-B and B-A); keep the one with `f1.follower_id < f1.followee_id`.", "Join `users` twice for the two names."],
    "Self join on the swapped key pair, de-duplicate symmetric pairs with `<`, decorate with usernames.",
    "- Using `<>` instead of `<` returns every pair twice.\n- Forgetting one of the two swap conditions matches unrelated rows.\n- An INTERSECT of `(follower, followee)` with `(followee, follower)` also works but returns only ids.",
    "The primary key `(follower_id, followee_id)` makes the mirrored lookup an index probe.")),

P("sql-follower-leaderboard", "Follower Leaderboard", "Medium", "Ranking with ties",
  [USERS, FOLLOWS],
  "Build a leaderboard of **all** users by number of followers, including users nobody follows (0 followers). Use competition ranking: ties share a rank and the next rank is skipped (`RANK`). Return the top 10 ranks (ties at rank 10 included).",
  "`rnk`, `user_id`, `username`, `followers`",
  "by `rnk`, then `user_id`.",
  """
WITH counts AS (
  SELECT u.user_id, u.username, COUNT(f.follower_id) AS followers
  FROM users u
  LEFT JOIN follows f ON f.followee_id = u.user_id
  GROUP BY u.user_id, u.username
), ranked AS (
  SELECT RANK() OVER (ORDER BY followers DESC) AS rnk, user_id, username, followers
  FROM counts
)
SELECT rnk, user_id, username, followers
FROM ranked
WHERE rnk <= 10
ORDER BY rnk, user_id;""",
  G("LEFT JOIN counting, RANK vs DENSE_RANK vs ROW_NUMBER.",
    "Count followers per user with an outer join so that zero-follower users exist in the result, then apply a ranking function over the counts.",
    ["`users LEFT JOIN follows ON followee_id = user_id`.", "`COUNT(f.follower_id)` - not `COUNT(*)` - so that users without followers get 0.", "`RANK() OVER (ORDER BY followers DESC)`, filtered in an outer query."],
    "Outer join and aggregate, rank, filter. RANK gives 1, 2, 2, 4 for ties.",
    "- Joining on `follower_id` counts how many people a user *follows*.\n- `COUNT(*)` reports 1 for users with no followers.\n- `LIMIT 10` cuts through a tie arbitrarily; filtering on the rank keeps tied users together.",
    "Aggregate plus one sort.")),

P("sql-days-to-first-post", "Time to First Post", "Medium", "First event per user",
  [USERS, POSTS],
  "Activation analysis: for users who joined on or after 2024-06-01 and have posted, compute how many days passed between joining and their first post (posts made before the dataset window simply do not exist). Summarise by bucket: `'same week'` (0-6 days), `'within a month'` (7-29 days), `'later'` (30+ days).",
  "`bucket`, `users`, `avg_days` (rounded to 1)",
  "`'same week'`, then `'within a month'`, then `'later'`.",
  """
WITH first_post AS (
  SELECT u.user_id,
         CAST(julianday(date(MIN(p.created_at))) - julianday(u.joined_on) AS INTEGER) AS days_to_post
  FROM users u
  JOIN posts p ON p.user_id = u.user_id
  WHERE u.joined_on >= '2024-06-01'
  GROUP BY u.user_id, u.joined_on
)
SELECT CASE WHEN days_to_post < 7 THEN 'same week'
            WHEN days_to_post < 30 THEN 'within a month'
            ELSE 'later' END AS bucket,
       COUNT(*) AS users,
       ROUND(AVG(days_to_post), 1) AS avg_days
FROM first_post
GROUP BY bucket
ORDER BY MIN(days_to_post);""",
  G("MIN per group, date arithmetic with `julianday`, CASE bucketing.",
    "Two steps: reduce each user to one number (days from join to first post), then bucket those numbers and count.",
    ["First post per user is `MIN(created_at)` after grouping by user.", "Days between two dates: `julianday(date(a)) - julianday(b)`.", "Bucket with a searched CASE and group by the bucket; sorting by `MIN(days_to_post)` puts buckets in natural order."],
    "CTE with one row per user, then a second aggregation by bucket. Truncating the timestamp with `date()` avoids fractional days.",
    "- Subtracting the raw strings gives a difference of years, not days.\n- Averaging before bucketing loses the distribution.\n- Alphabetical bucket order is not the business order; sort by a numeric key.",
    "Two aggregations, each linear after grouping.")),

P("sql-like-count-histogram", "Histogram of Likes per Post", "Medium", "Histograms and bucketing",
  [POSTS, LIKES],
  "Product wants the distribution of engagement. Classify every post by its number of likes into the buckets `'0'`, `'1-2'`, `'3-5'` and `'6+'`, and report how many posts fall in each bucket and what percentage of all posts that is.",
  "`bucket`, `posts`, `pct_of_posts` (rounded to 1)",
  "`'0'`, `'1-2'`, `'3-5'`, `'6+'`.",
  """
WITH per_post AS (
  SELECT p.post_id, COUNT(l.like_id) AS likes
  FROM posts p
  LEFT JOIN likes l ON l.post_id = p.post_id
  GROUP BY p.post_id
)
SELECT CASE WHEN likes = 0 THEN '0'
            WHEN likes <= 2 THEN '1-2'
            WHEN likes <= 5 THEN '3-5'
            ELSE '6+' END AS bucket,
       COUNT(*) AS posts,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM posts), 1) AS pct_of_posts
FROM per_post
GROUP BY bucket
ORDER BY MIN(likes);""",
  G("LEFT JOIN, two-level aggregation, CASE.",
    "A histogram is a count of counts: first count likes per post, then count posts per like-bucket.",
    ["Likes per post with a LEFT JOIN so that zero-like posts are present.", "Label each post with a CASE.", "Group by the label; order by `MIN(likes)` to keep the buckets in numeric order."],
    "Inner aggregation to the post grain, outer aggregation to the bucket grain.",
    "- An inner join makes the '0' bucket disappear.\n- Sorting the labels as text puts '6+' before... nothing here, but '10+' would sort before '3-5'. Sort by a number.\n- Percentages must use the total number of posts, not of liked posts.",
    "Linear in likes plus a tiny final group.")),

P("sql-daily-active-users", "Daily Active Users", "Medium", "Active-user metrics",
  [POSTS, LIKES, COMMENTS],
  "A user is *active* on a day if they posted, liked or commented that day. Report daily active users (DAU) for 1-14 December 2024, with the number of those users who posted that day.",
  "`day` (`'YYYY-MM-DD'`), `dau`, `posters`",
  "by `day`.",
  """
WITH activity AS (
  SELECT user_id, date(created_at) AS day, 1 AS is_post FROM posts
  UNION ALL
  SELECT user_id, date(liked_at), 0 FROM likes
  UNION ALL
  SELECT user_id, date(created_at), 0 FROM comments
)
SELECT day,
       COUNT(DISTINCT user_id) AS dau,
       COUNT(DISTINCT CASE WHEN is_post = 1 THEN user_id END) AS posters
FROM activity
WHERE day BETWEEN '2024-12-01' AND '2024-12-14'
GROUP BY day
ORDER BY day;""",
  G("UNION ALL, COUNT(DISTINCT), date truncation.",
    "Stack the three kinds of activity into one long table of (user, day) rows, then count distinct users per day.",
    ["`UNION ALL` three SELECTs with the same two columns.", "`COUNT(DISTINCT user_id)` so a user with five actions counts once.", "A tag column lets one query also count posters."],
    "Unify the event sources, truncate timestamps to dates, aggregate per day with distinct counts.",
    "- `COUNT(*)` counts actions, not users.\n- UNION (without ALL) would also work but wastes a de-duplication the DISTINCT count repeats.\n- A day with no activity at all would be missing; scaffold with a calendar if zeros matter.",
    "Linear in total events plus a sort for the distinct counts.")),

P("sql-dau-mau-stickiness", "Stickiness: DAU / MAU", "Hard", "Active-user metrics",
  [POSTS, LIKES, COMMENTS],
  "*Stickiness* is average daily active users divided by monthly active users. A user is active on a day if they posted, liked or commented. For each month from September to December 2024 report MAU, the average DAU over the days of that month that had any activity, and the stickiness percentage.",
  "`month` (`'YYYY-MM'`), `mau`, `avg_dau` (rounded to 2), `stickiness_pct` (`100 * avg_dau / mau`, rounded to 1)",
  "by `month`.",
  """
WITH activity AS (
  SELECT user_id, date(created_at) AS day FROM posts
  UNION
  SELECT user_id, date(liked_at) FROM likes
  UNION
  SELECT user_id, date(created_at) FROM comments
), daily AS (
  SELECT day, COUNT(*) AS dau FROM activity GROUP BY day
), monthly AS (
  SELECT strftime('%Y-%m', day) AS month, COUNT(DISTINCT user_id) AS mau
  FROM activity GROUP BY month
)
SELECT m.month, m.mau,
       ROUND(AVG(d.dau), 2) AS avg_dau,
       ROUND(100.0 * AVG(d.dau) / m.mau, 1) AS stickiness_pct
FROM monthly m
JOIN daily d ON strftime('%Y-%m', d.day) = m.month
WHERE m.month BETWEEN '2024-09' AND '2024-12'
GROUP BY m.month, m.mau
ORDER BY m.month;""",
  G("Multi-step CTEs, distinct counts at two grains.",
    "DAU and MAU are distinct-user counts at different grains, so each needs its own aggregation; they cannot be derived from one another.",
    ["`UNION` (not ALL) gives one row per user per active day.", "Daily CTE: users per day. Monthly CTE: distinct users per month.", "Join days to their month and average the daily counts."],
    "Build a de-duplicated activity table, aggregate twice, join, divide.",
    "- MAU is **not** the sum of DAU: the same user is active on many days.\n- Averaging over calendar days instead of active days is a different definition; state yours.\n- Integer division if you forget the 100.0.",
    "Dominated by de-duplicating the activity rows.")),

P("sql-longest-posting-streak", "Longest Posting Streak", "Hard", "Gaps and islands",
  [POSTS, USERS],
  "A *streak* is a run of consecutive calendar days on each of which a user published at least one post. Find each user's longest streak and return the users whose longest streak is at least 4 days. If a user has several streaks of the same maximal length, report the earliest.",
  "`user_id`, `username`, `streak_days`, `streak_start`, `streak_end`",
  "by `streak_days` descending, then `user_id`.",
  """
WITH days AS (
  SELECT DISTINCT user_id, date(created_at) AS day FROM posts
), keyed AS (
  SELECT user_id, day,
         julianday(day) - ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY day) AS grp
  FROM days
), islands AS (
  SELECT user_id, MIN(day) AS streak_start, MAX(day) AS streak_end, COUNT(*) AS streak_days
  FROM keyed GROUP BY user_id, grp
), ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY streak_days DESC, streak_start) AS rn
  FROM islands
)
SELECT r.user_id, u.username, r.streak_days, r.streak_start, r.streak_end
FROM ranked r JOIN users u ON u.user_id = r.user_id
WHERE r.rn = 1 AND r.streak_days >= 4
ORDER BY r.streak_days DESC, r.user_id;""",
  G("Gaps and islands (lesson *Gaps and islands, sessions and cohort retention*).",
    "Inside a run of consecutive days, the date and the row number both rise by one per row, so their difference is constant. That constant labels the streak.",
    ["De-duplicate to one row per user per day first - two posts on one day would break the arithmetic.", "`julianday(day) - ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY day)` is the island key.", "Group by the key for streak length, then take each user's best streak with ROW_NUMBER."],
    "Distinct days, island key, aggregate islands, top-1 per user, filter and join names.",
    "- Skipping the DISTINCT step silently splits streaks.\n- Forgetting PARTITION BY lets one user's days continue another's.\n- PostgreSQL: `day - (ROW_NUMBER() ...)::int`.",
    "Two sorts per user: O(n log n).")),

P("sql-comment-thread-depth", "Deepest Comment Threads", "Hard", "Recursive hierarchies",
  [COMMENTS],
  "Comments form reply trees through `parent_comment_id`. A top-level comment has depth 1, a reply to it depth 2, and so on. For each post that has comments, compute the total number of comments and the maximum reply depth; return the posts whose maximum depth is at least 3.",
  "`post_id`, `comments`, `max_depth`",
  "by `max_depth` descending, then `comments` descending, then `post_id`.",
  """
WITH RECURSIVE tree(comment_id, post_id, depth) AS (
  SELECT comment_id, post_id, 1
  FROM comments
  WHERE parent_comment_id IS NULL
  UNION ALL
  SELECT c.comment_id, c.post_id, t.depth + 1
  FROM comments c
  JOIN tree t ON c.parent_comment_id = t.comment_id
)
SELECT post_id, COUNT(*) AS comments, MAX(depth) AS max_depth
FROM tree
GROUP BY post_id
HAVING MAX(depth) >= 3
ORDER BY max_depth DESC, comments DESC, post_id;""",
  G("Recursive CTEs.",
    "Depth is 'my parent's depth plus one', which is exactly what a recursive CTE computes: start from the roots and repeatedly attach children.",
    ["Anchor: top-level comments (`parent_comment_id IS NULL`) at depth 1.", "Recursive member: join comments to the previous level on `parent_comment_id`, depth + 1.", "Aggregate the finished tree per post; filter with HAVING."],
    "Top-down traversal carrying a depth counter, then an ordinary GROUP BY.",
    "- A single self join only reaches depth 2.\n- Aggregating inside the recursive member is not allowed; aggregate afterwards.\n- With cyclic data the recursion would not stop - add a depth guard.",
    "Each comment is visited once.")),

P("sql-follow-suggestions", "Who to Follow", "Hard", "Self-joins",
  [FOLLOWS, USERS],
  "Recommend accounts to **user 1**: users followed by the people user 1 follows ('friends of friends') whom user 1 does not already follow, excluding user 1 themself. Rank suggestions by how many of user 1's followees follow them.",
  "`suggested_user_id`, `username`, `followed_by_my_followees`",
  "by `followed_by_my_followees` descending, then `suggested_user_id`.",
  """
SELECT f2.followee_id AS suggested_user_id, u.username,
       COUNT(*) AS followed_by_my_followees
FROM follows f1
JOIN follows f2 ON f2.follower_id = f1.followee_id
JOIN users u    ON u.user_id = f2.followee_id
WHERE f1.follower_id = 1
  AND f2.followee_id <> 1
  AND NOT EXISTS (SELECT 1 FROM follows x
                  WHERE x.follower_id = 1 AND x.followee_id = f2.followee_id)
GROUP BY f2.followee_id, u.username
ORDER BY followed_by_my_followees DESC, suggested_user_id;""",
  G("Self joins, NOT EXISTS, grouping.",
    "Walk two hops in the follow graph: me -> my followees -> their followees. Then remove the candidates I already follow and count how many paths lead to each remaining candidate.",
    ["`f1` = rows where I am the follower; `f2` = rows whose follower is one of my followees.", "Exclude myself and anyone I already follow (anti-join).", "Group by the candidate and count the paths."],
    "Two-hop self join, anti-join against the first hop, aggregate.",
    "- Forgetting to exclude user 1 suggests following yourself (when a followee follows you back).\n- `NOT IN` on a list that could contain NULL is risky; NOT EXISTS is safe.\n- The count is the number of *my followees* who follow the candidate - not the candidate's total followers.",
    "Index probes on the `(follower_id, followee_id)` key for each hop.")),

P("sql-busiest-conversations", "Busiest Conversations", "Medium", "Self-joins for pairs",
  [MESSAGES],
  "A *conversation* is an unordered pair of users: messages from A to B and from B to A belong to the same conversation. Report the conversations with at least 6 messages, with how many each side sent.",
  "`user_low`, `user_high` (the smaller and larger user id), `messages`, `sent_by_low`, `sent_by_high`",
  "by `messages` descending, then `user_low`, then `user_high`.",
  """
SELECT MIN(sender_id, receiver_id) AS user_low,
       MAX(sender_id, receiver_id) AS user_high,
       COUNT(*) AS messages,
       SUM(CASE WHEN sender_id < receiver_id THEN 1 ELSE 0 END) AS sent_by_low,
       SUM(CASE WHEN sender_id > receiver_id THEN 1 ELSE 0 END) AS sent_by_high
FROM messages
GROUP BY user_low, user_high
HAVING COUNT(*) >= 6
ORDER BY messages DESC, user_low, user_high;""",
  G("Grouping by expressions, conditional aggregation.",
    "Give each unordered pair a canonical name: (smaller id, larger id). Both directions then land in the same group.",
    ["SQLite's two-argument `MIN(a, b)` / `MAX(a, b)` pick the smaller / larger value on a row (elsewhere: LEAST / GREATEST).", "Group by the canonical pair.", "Count each direction with a CASE on `sender_id < receiver_id`."],
    "Normalise the pair, group, conditional counts, HAVING.",
    "- Grouping by `(sender_id, receiver_id)` splits each conversation in two.\n- In MySQL and PostgreSQL use `LEAST(a, b)` and `GREATEST(a, b)`; multi-argument MIN/MAX is SQLite-specific.\n- A user messaging themself would need separate handling.",
    "Single pass.")),

P("sql-new-vs-returning-posters", "New versus Returning Posters", "Hard", "Multi-step CTE pipeline",
  [POSTS],
  "For each month, split the users who posted into **new** posters (their first-ever post is in that month) and **returning** posters (they first posted in an earlier month).",
  "`month` (`'YYYY-MM'`), `posters`, `new_posters`, `returning_posters`, `returning_pct` (rounded to 1)",
  "by `month`.",
  """
WITH monthly AS (
  SELECT DISTINCT user_id, strftime('%Y-%m', created_at) AS month FROM posts
), firsts AS (
  SELECT user_id, MIN(month) AS first_month FROM monthly GROUP BY user_id
)
SELECT m.month,
       COUNT(*) AS posters,
       SUM(CASE WHEN m.month = f.first_month THEN 1 ELSE 0 END) AS new_posters,
       SUM(CASE WHEN m.month > f.first_month THEN 1 ELSE 0 END) AS returning_posters,
       ROUND(100.0 * SUM(CASE WHEN m.month > f.first_month THEN 1 ELSE 0 END) / COUNT(*), 1) AS returning_pct
FROM monthly m
JOIN firsts f ON f.user_id = m.user_id
GROUP BY m.month
ORDER BY m.month;""",
  G("CTE pipelines, MIN per user, conditional aggregation.",
    "Label every (user, month) of activity by comparing the month with that user's first month; then count labels per month.",
    ["CTE 1: distinct (user, month).", "CTE 2: each user's first month with MIN.", "Join and count with CASE."],
    "Three small steps, each with an obvious grain: user-month, user, month.",
    "- Counting posts instead of distinct users overweights prolific posters.\n- A window `MIN(month) OVER (PARTITION BY user_id)` avoids the second CTE - equally valid.\n- The first month in the data has 100% new posters by construction (left-censoring).",
    "Distinct plus two aggregations.")),
]
