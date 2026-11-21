# Product analytics case questions

> **Before this lesson:** [A/B testing pitfalls: peeking, novelty, SRM and network effects](#/lesson/statistics/ab-pitfalls), [Power and sample size for A/B tests](#/lesson/statistics/power-sample-size), [Correlation, causation and Simpson's paradox](#/lesson/statistics/causation-simpson) and [Statistics interview essentials](#/lesson/statistics/interview-essentials). Weighted means and the "average of averages" trap come from [Data types and estimates of location](#/lesson/statistics/data-and-location).

## In plain words

A **product analytics case** is an open-ended business question asked in an interview, such as "daily active users dropped 8% last week: what happened?", "how would you measure the success of a new feature?" or "design an experiment for a new checkout flow". There is no single right answer. Interviewers watch how you structure the problem, which metrics you choose, how you use data to narrow down causes, and whether you apply statistics correctly. This lesson gives frameworks for the four common case types, with small worked analyses in Python.

An everyday picture: a doctor's consultation. A good doctor does not order every test at once. They ask questions to narrow the possibilities (when did it start, where does it hurt, anything unusual lately?), rule out the common simple causes first, then test the remaining hypotheses. Metric investigations work the same way.

Why it matters for a job: product data scientists at consumer technology companies, from ride-hailing and food delivery to e-commerce and social apps, spend much of their time defining metrics, diagnosing metric movements and designing experiments. The case round is often the deciding round for these roles.

## 1. The four case types

1. **Metric definition**: "How would you measure the success of feature X?"
2. **Metric investigation**: "Metric Y dropped; why?"
3. **Experiment design and interpretation**: "How would you test X? The results look like this; what do you recommend?"
4. **Product sense and trade-offs**: "Should we launch X if metric A rises but metric B falls?"

A general answering structure that works for all four:

```mermaid
flowchart LR
    A[Clarify goal and context] --> B[Define metrics]
    B --> C[Form hypotheses]
    C --> D[Use data to test them]
    D --> E[Recommend and state risks]
```

## 2. Defining success metrics

Start from the product goal and the user behaviour that shows value, then choose a set of metrics rather than one:

- **North star metric**: the single metric that best captures long-term value delivered to users, such as weekly active buyers for a marketplace or completed trips for ride-hailing.
- **Primary (decision) metric** for the feature: the most direct measure of the behaviour it should change, sensitive enough to detect in a test. For a new search ranking: search-to-purchase conversion.
- **Secondary metrics**: supporting evidence of the mechanism (click-through on results, time to first click).
- **Guardrail metrics**: things that must not get worse: latency, crash rate, cancellations, revenue, complaints, unsubscribe rate.
- **Counter-metrics** for gaming: if you reward clicks, watch for clickbait (short dwell time after the click).

Good metrics are **measurable**, **sensitive** (they move when the product improves), **timely** (not only visible after six months), and **hard to game**. Be precise about definitions: a "daily active user" must specify what counts as active (an app open? a meaningful action?), in which time zone the day is cut, and whether bots and employees are excluded. Prefer ratio metrics with a clear unit (orders per active user) and decide whether you want per-user averages or pooled rates, since they answer different questions.

> [!TIP]
> Metric trade-offs are inevitable. Say how you would weigh them: convert to a common currency (expected revenue or long-term retention) where possible, or agree in advance on acceptable guardrail thresholds.

## 3. Investigating a metric change

A standard investigation sequence:

1. **Confirm the change is real.** Is it outside normal day-to-day variation (compare with the same weekday in previous weeks)? Is there a logging, pipeline or definition change? Did a dashboard filter change? Many "drops" are data bugs.
2. **Check timing and external factors.** Sudden or gradual? Public holidays, seasonality, marketing campaigns ending, competitor launches, outages, app store issues, news events.
3. **Check internal changes.** App releases, experiments launched or ended, pricing changes, ranking changes.
4. **Decompose the metric.** Break a ratio into numerator and denominator; break a total into segments (platform, country, app version, new versus returning users, traffic source); break a funnel into steps.
5. **Locate and explain.** Find the segment or step where the change concentrates, form a hypothesis, and verify it with more data.

### Decomposition 1: rate change or mix change?

Overall conversion fell from 5.20% to 4.99%. Did conversion get worse, or did traffic shift towards platforms that always convert less?

```python-run
import pandas as pd
df = pd.DataFrame({
    "platform": ["android", "ios", "web"],
    "visits_w1": [50_000, 30_000, 20_000], "orders_w1": [2_500, 2_100, 600],
    "visits_w2": [52_000, 26_000, 32_000], "orders_w2": [2_652, 1_846, 992],
})
df["rate_w1"] = df.orders_w1 / df.visits_w1
df["rate_w2"] = df.orders_w2 / df.visits_w2
df["share_w1"] = df.visits_w1 / df.visits_w1.sum()
df["share_w2"] = df.visits_w2 / df.visits_w2.sum()
overall_w1 = df.orders_w1.sum() / df.visits_w1.sum()
overall_w2 = df.orders_w2.sum() / df.visits_w2.sum()
print(df[["platform", "rate_w1", "rate_w2", "share_w1", "share_w2"]].round(4).to_string(index=False))
print(f"overall conversion: week 1 {overall_w1:.4f}, week 2 {overall_w2:.4f}, change {overall_w2 - overall_w1:+.4f}")
rate_effect = (df.share_w1 * (df.rate_w2 - df.rate_w1)).sum()
mix_effect = ((df.share_w2 - df.share_w1) * df.rate_w2).sum()
print(f"rate effect {rate_effect:+.4f} + mix effect {mix_effect:+.4f} = {rate_effect + mix_effect:+.4f}")
```

**Reading this code line by line**

- For each platform we have visits and orders in two weeks; we compute each platform's conversion rate and its share of visits.
- The overall rate is the visit-weighted average of platform rates, so it can change because rates change or because shares change.
- The **rate effect** holds week-1 shares fixed and applies the rate changes; the **mix effect** applies the share changes at week-2 rates. Together they add up exactly to the total change. (This is a **shift-share** or mix-rate decomposition.)

Every platform's conversion *rose* by 0.1 points, yet overall conversion *fell* by 0.21 points. The rate effect is $+0.0010$; the mix effect is $-0.0031$. Web, the lowest-converting platform, jumped from 20% to 29% of traffic (perhaps a new ad campaign driving web visits). This is Simpson's paradox in a dashboard. The right message is "conversion behaviour is healthy; traffic mix shifted towards web; check the campaign's targeting and whether the extra web visits are valuable", not "conversion is broken".

### Decomposition 2: which funnel step?

```python-run
import pandas as pd
funnel = pd.DataFrame({
    "step": ["visit", "search", "view item", "add to cart", "checkout", "pay"],
    "last_week": [100_000, 62_000, 41_000, 12_300, 7_400, 6_100],
    "this_week": [101_000, 63_100, 41_900, 12_600, 6_300, 5_150],
})
for col in ["last_week", "this_week"]:
    funnel[col + "_step_rate"] = (funnel[col] / funnel[col].shift(1)).round(3)
print(funnel.to_string(index=False))
print("end-to-end:", round(funnel.last_week.iloc[-1] / funnel.last_week.iloc[0], 4), "->",
      round(funnel.this_week.iloc[-1] / funnel.this_week.iloc[0], 4))
```

**Reading this code line by line**

- Each row is a step of a purchase funnel with the number of users reaching it.
- `funnel[col].shift(1)` moves the column down one row, so dividing by it gives each step's **step conversion rate** (users at this step divided by users at the previous step). The first step has no previous step, hence `NaN` (not a number).
- `.iloc[-1]` and `.iloc[0]` pick the last and first rows for the end-to-end rate.

End-to-end conversion fell from 6.1% to 5.1%. Every step is stable except add-to-cart to checkout, which fell from 60.2% to 50.0%. That points to the cart or checkout page: a release that broke a button on some devices, a new mandatory field, a shipping fee shown earlier, a payment provider outage. Next steps: split that step by platform and app version, check error logs, and check the release calendar.

### Decomposition 3: which segment?

```python-run
import pandas as pd
dau = pd.DataFrame({
    "segment": ["SG android", "SG ios", "MY android", "MY ios", "ID android", "ID ios"],
    "last_week": [120_000, 90_000, 150_000, 60_000, 400_000, 80_000],
    "this_week": [119_000, 91_000, 149_000, 61_000, 330_000, 79_000],
})
dau["change"] = dau.this_week - dau.last_week
total_change = dau.change.sum()
dau["share_of_drop"] = (dau.change / total_change).round(3)
print(dau.sort_values("change").to_string(index=False))
print("total change:", total_change, f"({total_change / dau.last_week.sum():+.1%})")
```

**Reading this code line by line**

- Daily active users by country and platform for two weeks.
- `change` is the absolute difference; `share_of_drop` is each segment's share of the total change (negative values are segments that grew).
- `sort_values("change")` lists the biggest declines first.

DAU fell 71,000 (7.9%), and Indonesian Android users account for 98.6% of the drop; every other segment moved by about 1,000 either way. A drop concentrated in one country and one platform suggests a local cause: an Android release that crashes on popular Indonesian devices, a regional outage, a telecom or payment issue, a local holiday, or a competitor promotion there. Always rank segments by *absolute contribution*, not percentage change: a small segment can have a dramatic percentage drop that explains little of the total.

## 4. Experiment design cases

A complete answer covers:

1. **Hypothesis**: "Showing delivery-time estimates on restaurant cards will increase orders per visitor because users can choose faster options."
2. **Unit of randomisation**: user (most common), session, device, or cluster (city, time slot) when there are network or marketplace effects.
3. **Metrics**: primary (orders per visitor), secondary (card click-through), guardrails (cancellations, delivery-time accuracy, courier utilisation).
4. **Sample size and duration**: from baseline, variance and minimum detectable effect; whole weeks; consider novelty.
5. **Checks**: A/A or pre-period balance, sample ratio mismatch, logging validation.
6. **Analysis plan**: test at the randomisation unit, confidence intervals, pre-registered segments, multiple-testing awareness.
7. **Decision rule**: ship if primary improves with guardrails within agreed bounds; otherwise iterate.

Interpreting results: separate statistical from practical significance; check consistency across days and key segments (not to fish, but to detect novelty and bugs); consider long-term effects and holdouts; be explicit about uncertainty. When the primary metric wins but a guardrail loses (orders up 2%, cancellations up 4%), quantify both in a common currency (net revenue, customer lifetime value) and discuss whether a design tweak could keep the gain without the loss.

> [!INTERVIEW]
> When asked "What would you do if the experiment cannot be randomised by user?" mention switchback designs (alternating treatment over time in a whole market), geo experiments (randomising cities or regions, analysed with methods like difference-in-differences or synthetic control), and observational approaches with their assumptions.

## 5. Product sense: estimation and trade-offs

Some cases ask for rough estimates ("how many food delivery orders happen in Singapore each day?"). Use a transparent chain of assumptions: population, share of users, frequency, then sanity-check with a second route. State assumptions as ranges and say which one matters most.

Trade-off questions ("engagement up, revenue down: launch?") test judgement. Clarify the company's current priority, the size and confidence of each effect, short versus long term (engagement often leads revenue), effects on different user groups, and reversibility. A good answer proposes a decision rule and further analysis rather than a bare yes or no.

## 6. Common mistakes in case rounds

- Jumping to a cause before confirming the change is real and checking data pipelines.
- Choosing a single metric with no guardrails.
- Reporting percentage changes for segments without their absolute contribution.
- Ignoring mix shifts (Simpson's paradox) when comparing aggregate rates.
- Designing experiments with no power calculation or the wrong randomisation unit.
- Declaring "no effect" from an underpowered test, or "it works" from peeking.
- Proposing causal conclusions from observational correlations.

## Summary

- Case questions cover metric definition, metric investigation, experiment design and trade-offs; structure every answer as clarify, define, hypothesise, test with data, recommend.
- Success metrics come as a set: north star, primary, secondary, guardrails and counter-metrics, precisely defined.
- Investigate changes by confirming they are real, checking timing and releases, then decomposing by rate versus mix, funnel step and segment contribution.
- Experiment answers state hypothesis, unit, metrics, power, checks, analysis plan and decision rule.
- Trade-offs need a common currency, a view of uncertainty and a decision rule.

## Glossary

- **Product analytics case**: an open-ended interview question about a product decision or metric.
- **North star metric**: the metric that best reflects long-term value to users.
- **Primary / secondary / guardrail / counter-metric**: the deciding metric / supporting metrics / metrics that must not worsen / metrics that detect gaming.
- **Daily active users (DAU)**: users counted as active on a day under a precise definition.
- **Shift-share (mix-rate) decomposition**: splitting a change in an overall rate into rate changes within segments and changes in segment mix.
- **Funnel / step conversion rate**: a sequence of steps users pass through / the share reaching a step out of those at the previous step.
- **Absolute contribution**: a segment's share of a total change.
- **Geo experiment**: randomising regions rather than users.
- **Synthetic control**: building a comparison region from a weighted mix of untreated regions.

## Check yourself

```quiz
[
  {"q": "Overall conversion fell, but conversion rose on every platform. The most likely explanation is…", "options": ["traffic shifted towards lower-converting platforms (a mix effect)", "a data bug in every platform", "the test was underpowered", "conversion was measured wrongly"], "answer": 0,
   "explain": "An overall rate is a weighted average; weights can change even when every rate improves."},
  {"q": "End-to-end funnel conversion fell from 6.1% to 5.1%, and only the cart-to-checkout step rate dropped (60% to 50%). The next step is…", "options": ["split that step by platform and app version and check recent releases and errors", "redesign the home page", "conclude users dislike the products", "run a new A/B test on search"], "answer": 0,
   "explain": "Localise the change, then look for causes specific to that step."},
  {"q": "DAU fell 71,000; one segment fell 70,000 (−17.5%) and a tiny segment fell 30%. Which matters most for explaining the drop?", "options": ["The segment that fell 70,000, by absolute contribution", "The tiny segment, because its percentage drop is larger", "Both equally", "Neither"], "answer": 0,
   "explain": "Rank segments by contribution to the total change, not percentage."},
  {"q": "Which is a guardrail metric for a feature meant to increase orders on a food delivery app?", "options": ["Order cancellation rate", "Orders per visitor", "Restaurant card click-through", "Number of restaurants listed"], "answer": 0,
   "explain": "Guardrails capture harm that the primary metric could hide."},
  {"q": "Before investigating causes of a sudden 20% metric drop, you should first…", "options": ["confirm it is real: check data pipelines, logging and definition changes", "launch an A/B test", "fit a regression", "blame seasonality"], "answer": 0,
   "explain": "Many dramatic drops are instrumentation or pipeline problems."},
  {"q": "A new courier-assignment algorithm cannot be randomised by user because users share couriers. A suitable design is…", "options": ["a switchback or city-level (geo) experiment", "a user-level A/B test", "a survey", "a before-after comparison with no control"], "answer": 0,
   "explain": "Interference between users requires randomising whole markets or time slots."}
]
```

> **Source:** Builds on Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 1 (exploratory analysis), ch. 3 (experiments and significance testing) and ch. 4 (regression and confounding); the case frameworks and examples are original and reflect common industry practice in product analytics.
