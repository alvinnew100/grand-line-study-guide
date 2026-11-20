# Back-of-envelope estimation, Fermi questions and logic puzzles

> **Before this lesson:** you need only everyday arithmetic — multiplying, dividing and powers of ten. The answer shape from [A seven-step answer framework](#/lesson/thinking/answer-framework) helps but is not required.

## In plain words

How many slices of pizza do you need for a party? You do not know exactly, and you do not need to. Twenty guests, about three slices each, eight slices per pizza: sixty slices, so eight pizzas. Nobody would call that a calculation, yet it has every part of a professional estimate: a few assumptions said out loud, a small multiplication, a rounded answer, and a decision at the end.

**Back-of-envelope estimation** is that same habit applied to engineering questions: *how much storage will this feature need? how many servers? can one database cope?* The name comes from doing the sum on whatever scrap of paper is nearby. A **Fermi question** is its general-knowledge cousin — "how many piano tuners are there in a city?" — named after the physicist Enrico Fermi, who was famous for good rough answers from little data.

Interviewers ask these because engineers constantly have to decide *before* they can measure. An estimate that is within a factor of ten tells you whether a design is easy, hard, or impossible, and that is usually all you need to choose a direction.

## The method

1. **Clarify what is being estimated** and in which unit.
2. **Break it into factors** you can guess separately.
3. **State an assumption for each factor**, with a round number.
4. **Multiply**, using powers of ten.
5. **Sanity-check** the result against something you know.
6. **Say what it means** for the decision, and which assumption matters most.

The aim is the right **order of magnitude** — the right power of ten. Whether the answer is 3 terabytes or 5 does not change a design; whether it is 5 gigabytes or 5 petabytes does.

### The numbers worth knowing

You need very few facts by heart.

**Time**

| Period | Seconds | Rounded |
|---|---|---|
| 1 minute | 60 | |
| 1 hour | 3,600 | |
| 1 day | 86,400 | about $10^5$ |
| 1 month | about 2.6 million | $2.5 \times 10^6$ |
| 1 year | about 31.5 million | $3 \times 10^7$ |

"A day is about a hundred thousand seconds" is the single most useful shortcut: one million events per day is roughly 12 per second.

**Sizes.** A **byte** is the basic unit of computer storage, enough for one plain English character.

| Unit | Bytes | Roughly holds |
|---|---|---|
| Kilobyte (KB) | $10^3$ | A paragraph of text |
| Megabyte (MB) | $10^6$ | A short book; a small photo |
| Gigabyte (GB) | $10^9$ | A film in standard quality |
| Terabyte (TB) | $10^{12}$ | A large laptop disk |
| Petabyte (PB) | $10^{15}$ | A thousand such disks |

**Typical item sizes** (rough, for estimating): a short text message, 100 bytes to 1 KB; a database row for a user or an order, about 1 KB; a compressed photo, 1–3 MB; a minute of compressed video, tens of MB.

**Powers of two**, for when a question is about identifiers: $2^{10} \approx 10^3$ (a thousand), $2^{20} \approx 10^6$ (a million), $2^{30} \approx 10^9$ (a billion), $2^{32} \approx 4 \times 10^9$.

### Working in powers of ten

Write each number as a small number times a power of ten, multiply the small numbers, and add the exponents.

$$50{,}000{,}000 \times 20 \times 500 = (5 \times 10^7)(2 \times 10^1)(5 \times 10^2) = 50 \times 10^{10} = 5 \times 10^{11}$$

That is 500 GB. Doing it this way makes it hard to lose a zero, which is the usual way estimates go wrong.

## The three quantities in a system estimate

Most engineering estimates ask for some of these.

**1. Request rate.** How many operations per second? The usual unit is **QPS**, queries per second.

$$\text{average QPS} = \frac{\text{daily active users} \times \text{actions per user per day}}{86{,}400}$$

Traffic is never even: evenings are busier than nights. So multiply by a **peak factor**, commonly 2 to 5, to get the rate the system must survive.

**2. Storage.** How much data accumulates?

$$\text{storage} = \text{items per day} \times \text{bytes per item} \times \text{days kept} \times \text{copies}$$

**Copies** matters: real systems store each item several times for safety, a practice called **replication**. Three copies is a common default.

**3. Bandwidth or memory**, when relevant: bytes per second moving across the network (rate × size), or how much must be held in fast memory (for a cache, often "the hottest 20 % of items").

```python-run
def estimate(dau, actions, bytes_per_action, peak_factor, replication, retention_days):
    per_day = dau * actions                         # events per day
    avg_qps = per_day / 86_400                      # spread over the seconds in a day
    storage_gb = per_day * bytes_per_action * replication * retention_days / 1e9
    return avg_qps, avg_qps * peak_factor, storage_gb

avg, peak, gb = estimate(dau=10_000_000, actions=20, bytes_per_action=500,
                         peak_factor=3, replication=3, retention_days=365)
print(f"average {avg:,.0f} QPS, peak {peak:,.0f} QPS, storage {gb:,.0f} GB (= {gb/1000:,.0f} TB)")
```

Line by line: the function multiplies users by actions to get events per day; divides by the seconds in a day for the average rate; and multiplies events by size, copies and days for storage, converting bytes to gigabytes by dividing by $10^9$. The output — roughly 2,300 QPS average, 7,000 at peak, 110 TB a year — is the whole of a typical sizing answer.

## Worked estimate 1 — A photo-sharing app

**Prompt:** *"Estimate the storage needed per year for a photo-sharing app with 50 million daily users."* Try it before opening.

<details><summary>Model answer</summary>

**Clarify.** Photos only, or video too? Do we keep originals or compressed versions? I'll assume photos, stored compressed, with a small preview image as well.

**Assumptions.**

- 50 million daily active users ($5 \times 10^7$).
- Most people look and do not post. Say one user in five uploads on a given day, two photos each → an average of 0.4 photos per user per day.
- A compressed photo is about 2 MB; previews add roughly 10 %, so 2.2 MB — I'll use 2 MB and remember the extra.
- Three copies.

**Multiply.**

- Photos per day: $5 \times 10^7 \times 0.4 = 2 \times 10^7$ (20 million).
- Bytes per day: $2 \times 10^7 \times 2 \times 10^6 = 4 \times 10^{13}$ = 40 TB.
- Per year: $40 \text{ TB} \times 365 \approx 14{,}600 \text{ TB} \approx 15 \text{ PB}$.
- With three copies: about **45 PB per year**.

**Sanity check.** 20 million photos a day from 50 million users is believable. 45 PB is tens of thousands of large disks: big, but a normal scale for a major consumer photo service.

**Upload rate.** 20 million per day ÷ $10^5$ seconds ≈ 200 uploads per second on average, perhaps 600–1,000 at peak. Small as a request rate; the challenge is storage and bandwidth (200 × 2 MB = 400 MB per second inbound), not the number of requests.

**What it means.** Storage dominates the cost, so the design questions are about it: compress harder, keep fewer copies of old photos, move rarely viewed photos to cheaper, slower storage.

**Most sensitive assumption.** Photos per user per day. If users upload five times as many, everything is five times larger. I would ask for that number first.

</details>

## Worked estimate 2 — Can one database handle it?

**Prompt:** *"A ticketing site sells 2 million tickets in the first hour of a big sale. Is a single database server enough?"*

<details><summary>Model answer</summary>

**Clarify.** "Enough" for writes of ticket purchases. I'll assume one purchase is a handful of row writes in one transaction.

**Rate.** 2 million in an hour: $2 \times 10^6 \div 3{,}600 \approx 550$ purchases per second *on average*. But a sale is not smooth: most demand arrives in the first minutes. If half the tickets go in the first five minutes, that is $10^6 \div 300 \approx 3{,}300$ per second at the peak.

**Reads.** Each buyer looks at availability several times and many would-be buyers fail. Assume 50 page views or checks per purchase: around 150,000 reads per second at peak.

**Compare with capacity.** A well-tuned relational database on strong hardware handles on the order of a few thousand simple write transactions per second and tens of thousands of simple reads. So: writes are *near the limit*, and reads are *well beyond it*.

**Conclusion.** Not safely. The design needs to keep reads away from the database — a cache or a pre-computed availability view — and to protect writes, most easily with a **queue** (a waiting line) or virtual waiting room that admits buyers at a rate the database can sustain. The hardest part is not volume but **contention**: thousands of people trying to buy the same few seats at once.

**Sensitive assumption.** The shape of the first minutes. I'd ask for data from a past sale.

</details>

> [!INTERVIEW]
> End every estimate with a consequence: "…so storage dominates", "…so one server is not enough", "…so this fits comfortably in memory". A number with no "so" attached is arithmetic; a number with a "so" is engineering.

## Fermi questions

The classic kind has nothing to do with computers: *how many piano tuners work in a large city? how many golf balls fit in a bus? how much does a city's population spend on coffee each day?* The method is identical; only the factors change. There are two main ways to break a question down.

**Demand side** — who needs the thing, and how often? **Supply side** — how much can one provider do? Then divide.

**Example: piano tuners in a city of 4 million people.**

- People per household: about 2.5 → 1.6 million households.
- Share of households with a piano: perhaps 1 in 30 → about 50,000 pianos. Add schools, churches, venues: say 60,000.
- Tunings per piano per year: one.
- So demand ≈ 60,000 tunings a year.
- One tuner: about 4 tunings a day (each takes a couple of hours plus travel), 250 working days → 1,000 a year.
- Tuners ≈ 60,000 ÷ 1,000 = **about 60**.

Nobody knows the true number offhand. What is judged is that each step is reasonable and stated. Individual errors tend to partly cancel: one guess too high, another too low.

**Bounding** is a helpful extra. Give a number that is surely too low and one surely too high — "certainly more than 5, certainly fewer than 1,000" — and check that your estimate sits between them, somewhere near the geometric middle.

## Logic puzzles that still appear

Brain-teasers are rarer than they were, because they predict job performance poorly, but a few survive, mostly ones with a real engineering idea inside. A method serves you better than a memorised list:

1. **Restate** the puzzle and confirm the rules.
2. **Try the smallest case** by hand.
3. **Look for the quantity that halves** or the structure that repeats.
4. **Generalise** and state the answer with its reasoning.
5. **Check** on the small case.

Three representative puzzles follow. Attempt each first.

**Puzzle 1.** *You have 8 coins that look identical; one is slightly heavier. With a two-pan balance, find it in as few weighings as you can.*

<details><summary>Answer</summary>

Two weighings. The insight: one weighing has **three** outcomes — left heavier, right heavier, or balanced — so it can separate three groups, not two. Split into groups of 3, 3 and 2. Weigh 3 against 3. If they balance, the heavy coin is among the 2: weigh those. If one side is heavier, take its 3 coins, weigh one against another; if they balance it is the third.

In general, $k$ weighings distinguish up to $3^k$ coins: 2 weighings handle 9. The engineering echo: count the outcomes of each test to know how much it can tell you — the same reasoning that says binary search needs $\log_2 n$ steps.

</details>

**Puzzle 2.** *A building has 100 floors. You have two identical eggs. An egg breaks if dropped from floor F or above and survives below F. Find F with the fewest drops in the worst case.*

<details><summary>Answer</summary>

Fourteen drops. Start small: with **one** egg you must go floor by floor from the bottom (up to 100 drops), because a broken egg ends the search. With two, use the first egg to jump in big steps and the second to scan the gap floor by floor.

Equal steps of 10 give a worst case of 10 jumps + 9 scans = 19. Better: make each jump one floor shorter than the last, so that the total (jumps so far + remaining scan) stays constant. Start at floor $n$, then $n + (n-1)$, and so on; we need $n + (n-1) + \dots + 1 \ge 100$, that is $n(n+1)/2 \ge 100$, giving $n = 14$. Drop at 14, 27, 39, 50, …

The echo: balancing the cost of two phases so that the worst case is equal everywhere is a standard optimisation idea.

</details>

**Puzzle 3.** *You have a 3-litre jug and a 5-litre jug and unlimited water. Measure exactly 4 litres.*

<details><summary>Answer</summary>

Fill the 5. Pour into the 3 until full: 2 remain in the 5. Empty the 3. Pour the 2 into the 3. Fill the 5 again. Top up the 3 from the 5: it takes 1, leaving **4** in the 5.

The method if you are stuck: treat each pair (amount in jug A, amount in jug B) as a **state** and each pour as a move, then search outward from (0, 0) — the same state-space thinking as in the state-machine lessons.

</details>

If you already know a puzzle, say so. It is more honest, and the interviewer will usually give a different one or ask you to explain the reasoning, which is what they wanted to see anyway.

## Common mistakes

- **Silent arithmetic.** The interviewer cannot follow or correct numbers that never leave your head.
- **False precision.** "86,400 × 49.7 million…" Round. Nobody is checking the third digit.
- **Dropped units.** Write the unit beside every number; most errors of a factor of a thousand are MB/GB or seconds/milliseconds mix-ups.
- **Forgetting peak, copies or retention.**
- **No sanity check.** An answer of "12 bytes per user" or "40,000 servers for a small site" should set off an alarm.
- **Stopping at the number** without saying what it implies.
- **Refusing to guess.** "I don't know how many households have pianos" — nobody does. Pick a plausible value, say it is a guess, and carry on.

## Summary

- Estimation is: clarify, factor, assume, multiply, sanity-check, conclude.
- Aim for the right power of ten. A day is about $10^5$ seconds; a million events a day is about 12 per second.
- System estimates need request rate (average and peak), storage (items × size × days × copies), and sometimes bandwidth or memory.
- Fermi questions use the same steps: demand divided by what one provider can supply; bound the answer from both sides.
- For puzzles, use small cases and count what each test can distinguish.
- Always finish with what the number means and which assumption it depends on most.

## Glossary

| Term | Meaning |
|---|---|
| Back-of-envelope estimate | A quick, rough calculation from stated assumptions |
| Fermi question | A question answered by breaking an unknown quantity into guessable factors |
| Order of magnitude | The nearest power of ten |
| Byte | The basic unit of storage, enough for one plain character |
| Daily active users (DAU) | The number of distinct people who use a product on a given day |
| QPS | Queries per second: how many requests arrive each second |
| Peak factor | How many times busier the busiest period is than the average |
| Replication | Keeping several copies of data for safety |
| Retention | How long data is kept before deletion |
| Bandwidth | The amount of data moving across a network per second |
| Contention | Many requests competing for the same item at once |
| Queue | A waiting line that lets work be processed at a controlled rate |

## Check yourself

```quiz
[
  {"q": "A service handles 5 million requests per day. Roughly how many per second on average?",
   "options": ["About 6", "About 60", "About 600", "About 6,000"],
   "answer": 1,
   "explain": "A day is about 100,000 seconds; 5,000,000 / 100,000 = 50, close to the exact 58."},
  {"q": "Each of 2 million users stores 500 items of 1 KB each, with three copies. Total storage?",
   "options": ["3 GB", "30 GB", "3 TB", "300 TB"],
   "answer": 2,
   "explain": "2×10^6 × 500 × 10^3 bytes = 10^12 bytes = 1 TB; times three copies is 3 TB."},
  {"q": "Why multiply the average request rate by a peak factor?",
   "options": ["To make the number look bigger", "Traffic is uneven, and the system must survive its busiest period", "Because databases require it", "To convert bytes to bits"],
   "answer": 1,
   "explain": "Capacity must be planned for the peak, which is typically several times the daily average."},
  {"q": "What is the main purpose of the sanity check at the end of an estimate?",
   "options": ["To add more decimal places", "To catch a result that is wildly off because of a lost factor or a bad assumption", "To impress the interviewer", "To change the units"],
   "answer": 1,
   "explain": "Comparing with something familiar exposes errors of a factor of a thousand."},
  {"q": "In the piano-tuner estimate, which step is the 'supply side'?",
   "options": ["The number of households", "How many tunings one tuner can do in a year", "The share of households with a piano", "The population of the city"],
   "answer": 1,
   "explain": "Supply is what one provider can deliver; dividing demand by it gives the number of providers."},
  {"q": "One weighing on a balance can distinguish how many possibilities?",
   "options": ["Two", "Three", "Eight", "Nine"],
   "answer": 1,
   "explain": "Left heavy, right heavy or balanced: three outcomes, which is why 2 weighings can handle up to 9 coins."},
  {"q": "After computing '45 PB per year', what should come next?",
   "options": ["Recompute to four significant figures", "Say what it implies for the design and which assumption it is most sensitive to", "Change the subject", "Apologise for the size"],
   "answer": 1,
   "explain": "An estimate exists to support a decision; state the consequence and the key uncertainty."}
]
```

> **Source:** Estimation approach and reference numbers in the spirit of the back-of-envelope section of Donne Martin's System Design Primer (https://github.com/donnemartin/system-design-primer) and Google SRE Book, "Software Engineering in SRE" — capacity planning (https://sre.google/sre-book/software-engineering-in-sre/). Worked estimates, puzzles' explanations and wording are original; the puzzles themselves are traditional.
