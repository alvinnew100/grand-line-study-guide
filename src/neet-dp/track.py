TRACK = dict(
    id="neet-dp",
    title="Patterns V — Dynamic Programming",
    icon="🍖",
    color="#e76f51",
    group="Data Structures & Algorithms",
    blurb="From recursion trees to tables: the state / recurrence / base case / order / answer framework, "
          "then the NeetCode 1-D and 2-D DP problems plus knapsack, LIS, string, grid and interval DP.",
    sources=[
        "Goodrich, Tamassia & Goldwasser, Data Structures and Algorithms in Python, ch. 13.3 (Dynamic Programming)",
        "NeetCode 150 roadmap — 1-D and 2-D Dynamic Programming",
    ],
    modules=[
        dict(
            id="dp-fundamentals",
            title="DP Fundamentals",
            summary="Recursion → memoization → tabulation → space optimisation, the five-part DP framework, and a map of DP families.",
            lessons=[
                dict(id="dp-from-recursion", title="From recursion to dynamic programming", file="01-from-recursion.md"),
                dict(id="dp-framework", title="The DP framework: state, recurrence, base, order, answer", file="02-framework.md"),
                dict(id="dp-families", title="A field guide to DP families", file="03-families.md"),
            ],
            problems=["fibonacci-number", "n-th-tribonacci-number"],
        ),
        dict(
            id="dp-1d",
            title="1-D Dynamic Programming",
            summary="One index of state: take-or-skip sequences, decoding, knapsack-style coin and subset problems, LIS and palindromes.",
            lessons=[
                dict(id="dp-linear", title="Linear DP: stairs, robbers and decoders", file="04-linear.md"),
                dict(id="dp-knapsack", title="Knapsack: 0/1 and unbounded, derived from scratch", file="05-knapsack.md"),
                dict(id="dp-lis", title="Longest increasing subsequence and patience sorting", file="06-lis.md"),
                dict(id="dp-palindromes", title="Palindromes, products and word breaks", file="07-palindromes.md"),
            ],
            problems=[
                "climbing-stairs", "min-cost-climbing-stairs", "house-robber", "house-robber-ii",
                "longest-palindromic-substring", "palindromic-substrings", "decode-ways", "coin-change",
                "maximum-product-subarray", "word-break", "longest-increasing-subsequence",
                "partition-equal-subset-sum",
            ],
        ),
        dict(
            id="dp-2d",
            title="2-D Dynamic Programming",
            summary="Two indices of state: grids, two-string tables (LCS, edit distance, regex), counting knapsacks, state machines and interval DP.",
            lessons=[
                dict(id="dp-grids", title="Grid DP and DP on DAGs", file="08-grids.md"),
                dict(id="dp-strings", title="String DP: LCS, edit distance and friends", file="09-strings.md"),
                dict(id="dp-counting-states", title="Counting knapsacks and state machines", file="10-counting-states.md"),
                dict(id="dp-intervals", title="Interval DP: matrix chains and burst balloons", file="11-intervals.md"),
            ],
            problems=[
                "unique-paths", "minimum-path-sum", "maximal-square", "longest-common-subsequence",
                "best-time-to-buy-and-sell-stock-with-cooldown", "dp-knapsack-01", "coin-change-ii", "target-sum",
                "interleaving-string", "longest-increasing-path-in-a-matrix", "distinct-subsequences",
                "edit-distance", "burst-balloons", "regular-expression-matching",
            ],
        ),
    ],
)
