# Question bank 3: estimation, metrics, planning, code quality, security, machine learning and behavioural questions

> **Before this lesson:** this is a practice page. Each group links to the lesson that teaches its method — for example [Back-of-envelope estimation](#/lesson/thinking/estimation-fermi) and [Behavioural-technical questions: the STAR method](#/lesson/thinking/behavioural-star). The "how to use" section of [Question bank 1](#/lesson/thinking/question-bank-design) applies here too.

## In plain words

A chess player improves less by learning new openings than by playing through hundreds of positions and asking, each time, "what would I do here, and why?" The answers matter less than the habit of weighing options and committing to one.

The questions on this page are positions of that kind. Few have a calculation at the end, and none has a single right answer. They ask for **judgment**: how big is this, roughly? how would we know it worked? what should we do first? is this code safe to merge? what could an attacker do? should a model be making this decision? what did you do when it went wrong? Interviewers lean on such questions for mid-level and senior roles because they are the closest thing to watching you work for a month.

Questions 153–230 are here, completing the bank. Attempt first; open the outline second.

## What a good judgment answer contains

Whatever the topic, strong answers to these questions share five features. Use them as a checklist after each attempt.

| Feature | Ask yourself |
|---|---|
| **A stated goal** | Did I say what we are trying to achieve before proposing anything? |
| **Explicit assumptions** | Did I say what I was taking for granted? |
| **Options with costs** | Did I name at least two ways and what each gives up? |
| **A decision** | Did I actually choose? |
| **A check** | Did I say how I would know whether I was right? |

```mermaid
flowchart LR
    G[Goal] --> A[Assumptions]
    A --> O[Options and their costs]
    O --> D[Decision]
    D --> C[How I would check]
```

## N. Estimation, Fermi questions and puzzles (questions 153–162)

Method: [back-of-envelope estimation](#/lesson/thinking/estimation-fermi): clarify → factors → assumptions → multiply in powers of ten → sanity check → consequence.

153. How much storage does a messaging app with 100 million daily users need per year for text messages?
154. How many requests per second does a search engine with 1 billion searches a day handle?
155. How many servers are needed for a service at 20,000 requests per second if one handles 500?
156. How many petrol stations are there in a country of 60 million people?
157. How much bandwidth does a video service use at peak with 1 million simultaneous viewers?
158. How long would it take to copy 1 petabyte over a 1 gigabit-per-second link?
159. How many unique identifiers do you need for every person on Earth, and how many bits is that?
160. You have nine balls; one is heavier. Find it in two weighings.
161. How many tennis balls fit in a school bus?
162. A table grows by 5 million rows a day at 200 bytes each. When does a 1 TB disk fill?

<details><summary>Outline answers 153–162</summary>

153. Assume 40 messages per user per day at 200 bytes: 10^8 × 40 × 200 = 8 × 10^11 bytes ≈ 0.8 TB per day ≈ 300 TB per year; with three copies about 0.9 PB. Text is small; media would dominate.
154. 10^9 ÷ 86,400 ≈ 11,600 per second on average; with a peak factor of 2–3, about 25,000–35,000. Each search fans out to many machines, so internal load is far higher.
155. 20,000 ÷ 500 = 40 at full load; run at about two thirds utilisation → 60; add spares for failures → about 65. State that the per-server figure must come from a load test.
156. Demand: about 30 million cars, each filling up weekly → 30 million fills a week. Supply: a station with 8 pumps, about 10 fills per pump per hour, 15 busy hours, but pumps used perhaps 30 % of the time → roughly 2,500 fills a week. About 12,000 stations. Bound: more than 1,000, fewer than 100,000.
157. Assume 5 megabits per second per stream: 10^6 × 5 Mbit/s = 5 × 10^6 Mbit/s = 5 terabits per second. Far beyond one site, which is why content delivery networks spread it across many locations.
158. 1 Gbit/s ≈ 125 MB/s. 10^15 bytes ÷ 1.25 × 10^8 bytes/s = 8 × 10^6 seconds ≈ 93 days. Consequence: at that size, shipping disks or using many parallel links is faster.
159. About 8 billion ≈ 2^33, so 33 bits suffice for one each; 64 bits gives enormous room. If ids are random and must not collide, far more bits are needed (128-bit identifiers are common).
160. Three groups of three. Weigh two groups: the heavier one, or the unweighed one if they balance, holds the ball. Then weigh two balls from that group the same way. One weighing separates three possibilities, so two handle nine.
161. Bus interior roughly 10 m × 2.5 m × 2 m = 50 m³. A tennis ball is about 6.5 cm across; treated as a small cube it takes about 0.27 litres, so about 3,600 fit per m³ → roughly 180,000. Subtract seats and awkward gaps: about 120,000–150,000.
162. 5 × 10^6 × 200 = 10^9 bytes = 1 GB per day, plus indexes — say 1.5 GB. 1,000 GB ÷ 1.5 ≈ 670 days, under two years. Consequence: plan archiving or partitioning within the year.

</details>

## O. Metrics, experiments and data questions (questions 163–172)

Method: [metrics and experiments](#/lesson/thinking/metrics-experiments): goal → behaviour → metric → guardrails; and for a moved metric: real? shape? expected? slice, internal, external.

163. Define success metrics for a new "dark mode" setting.
164. Define success metrics for a search feature in a documentation site.
165. How would you measure the quality of an on-call rotation?
166. Design an A/B test for a new onboarding flow.
167. An A/B test shows +3 % conversion with p = 0.04 after two days. Ship?
168. Average session length rose 20 % after a release. Is that good?
169. Sign-ups are flat but revenue fell 10 %. Where do you look?
170. An experiment improved the primary metric and worsened page load time. What do you do?
171. How would you measure developer productivity?
172. Two teams report different numbers for "active users". How do you resolve it?

<details><summary>Outline answers 163–172</summary>

163. Goal: comfort and choice, perhaps retention. Metrics: adoption rate, share who keep it on after a week, effect on session length at night. Guardrails: crash rate, readability complaints, support tickets. It may be a hygiene feature with little measurable gain — say so.
164. Goal: readers find answers. Metrics: share of searches followed by a click and a stay on the page, searches with zero results, repeated searches, support tickets on documented topics. Guardrail: latency. Review top failing queries monthly.
165. Pages per shift and share that needed action; out-of-hours pages; time to acknowledge and to mitigate; repeat incidents; share of alerts with a runbook; and the people measure — reported fatigue and willingness to stay on the rota.
166. Hypothesis and one primary metric (completion of onboarding, then 7-day retention). Randomise by user; guardrails (support contacts, time to complete); sample size and at least one or two full weeks; decision rule fixed beforehand; check group sizes and logging parity.
167. Not yet. Two days miss weekly patterns and invite a novelty effect; stopping at the first p below 0.05 is peeking. Check sample size, the confidence interval, guardrails and sample-ratio balance. Run to the planned duration.
168. Not necessarily. People may be staying longer because tasks became harder to complete. Check task completion, error rates and return visits; slice by user type; look at whether logging of sessions changed.
169. Revenue = customers × conversion to paid × average price × retention. Check each: plan mix shifting to cheaper plans, discounts or pricing change, more refunds or cancellations, payment failures, currency effects, a billing bug. Slice by plan, country and cohort.
170. A guardrail breach is not a win. Check whether the slowdown is intrinsic or an implementation detail; try to keep the gain and remove the cost (lazy loading, caching); re-test. If inseparable, present the trade-off with long-term latency evidence.
171. No single number; individual output counts mislead and are gamed. Use team-level delivery measures (lead time, deployment frequency, change-fail rate, recovery time), plus developer-experience surveys and time lost to waiting. Use for improvement, not ranking.
172. Compare definitions line by line: what counts as active, which time window and time zone, de-duplication across devices, inclusion of bots, test or internal accounts, and data source. Agree one written definition and one owner.

</details>

## P. Prioritisation and planning (questions 173–182)

Method: [prioritisation](#/lesson/thinking/prioritisation) and [planning and estimating](#/lesson/thinking/planning-estimating).

173. You have three weeks and a list that needs six. What do you do?
174. A senior stakeholder asks for a feature "by Friday". It is a two-week job. How do you respond?
175. How would you estimate a project in an area you have never worked in?
176. Your team spends 40 % of its time on unplanned work. What would you do?
177. How do you decide whether to fix a bug now or later?
178. You are handed a half-finished project from a colleague who left. Where do you start?
179. How would you break down "improve the reliability of our service"?
180. Two projects need the same engineer. How is that decided?
181. Midway through, you discover the chosen approach will not work. What now?
182. How do you say no to a request?

<details><summary>Outline answers 173–182</summary>

173. Clarify the goal and what the date is tied to. Rank by value over effort with the product owner; draw the line at capacity; propose what ships, what is cut and what moves. Do not promise all six, and do not cut quality.
174. Understand the need behind Friday. Offer options: a reduced version by Friday, the full version in two weeks, or full by Friday with something else dropped and help added — with risks. Let the owner choose. Never silently accept or silently miss.
175. Break it down; identify unknowns; time-box spikes to turn them into knowns; ask people who have done similar work; give a wide range with assumptions; commit to re-estimating after the first week.
176. Measure where it comes from: incidents, support questions, other teams' requests, bugs. Fix the top source (a flaky system, missing documentation, missing self-service). Reserve explicit capacity; rotate an interrupt handler so that others can focus.
177. Severity × reach, workaround, trend, exposure — against the cost of the fix and what it displaces. Data loss, security or money: now. Cosmetic with low reach: later or never, closed with a note. Cheap fixes near current work: do them.
178. Find the goal and who depends on it. Read what exists: code, tickets, notes, history. Run it. Talk to the stakeholders and anyone who worked with the colleague. List what is done, unknown and remaining. Re-plan and re-estimate; share that openly.
179. Define reliability with a number: an availability or error-rate target for named user journeys. Measure the present state. List the biggest causes of past incidents. Slice: quick wins (alerts, timeouts), then structural work. Track the measure over time.
180. Not by the two requesters arguing. Compare value, urgency and cost of delay for each against team goals; consider sequencing or splitting; whoever owns priorities decides. Avoid giving the engineer two half-time projects.
181. Stop and confirm with a small proof. Tell the owner immediately with facts and options: a different approach with a new estimate, a reduced scope, or stopping. Salvage what is reusable. Reflect on what an early spike would have shown.
182. Understand the request and its reason first. Say no to the solution, not the person; explain the trade-off in their terms; offer an alternative, a later date, or what would have to be dropped to say yes; and be clear and prompt.

</details>

## Q. Code review and code quality (questions 183–190)

Method: [reviewing a snippet](#/lesson/thinking/code-review-snippets) and [changing legacy code](#/lesson/thinking/refactoring-legacy).

183. What do you look for first in a code review?
184. A colleague's pull request has 2,000 changed lines. What do you do?
185. How do you review code in a language or area you do not know well?
186. You and the author disagree about a design choice in review. How is it resolved?
187. How do you decide whether code has enough tests?
188. You find a function with no tests that you must change. Steps?
189. What makes code "readable"?
190. How do you handle a reviewer who blocks your change over style?

<details><summary>Outline answers 183–190</summary>

183. Purpose, then correctness, then safety (data, security, concurrency), robustness under failure, readability and design, tests and performance. Lead with what could cause harm; style last. Also note what is good.
184. Ask for it to be split: refactoring apart from behaviour change, and by feature slice. If it cannot be, ask for a walkthrough and review in ordered sections with the riskiest first. Large changes get skimmed, which is the real danger.
185. Say so. Focus on what you can judge: clarity, tests, error handling, edge cases, security basics. Ask questions that make the author explain. Bring in someone with the expertise for the parts you cannot assess.
186. Discuss with reasons and evidence, not preference; check the style guide and existing conventions; talk in person if the thread grows; consider whether it is reversible; escalate jointly to the tech lead if stuck; then commit to the decision.
187. Not by a coverage percentage alone. Would the tests fail if the behaviour broke? Are edge cases and failure paths covered? Are they at the right level, fast and reliable? Does a regression test accompany each bug fix?
188. Understand it and its callers; write characterisation tests that pin current behaviour; create a seam if it is untestable; refactor in small steps keeping tests green; then make the change separately with its own test; release behind a flag if risky.
189. Names that say what things are; small functions doing one thing; obvious control flow; consistent style; comments that explain why; no surprises. The test: can a new colleague change it safely without asking?
190. Check whether the style guide covers it; if so, comply. If not, it is a preference: ask for it to be marked as a nit, propose adding a rule to the formatter or guide so that the question is settled for everyone, and involve a third person if it stays blocked.

</details>

## R. Security and privacy (questions 191–200)

Method: [threat modelling](#/lesson/thinking/threat-modelling) and [credentials and personal data](#/lesson/thinking/credentials-and-personal-data). Defensive throughout.

191. What are the security concerns in a "forgot password" feature?
192. Threat-model a feature that lets users upload a profile picture.
193. How should passwords be stored?
194. A customer reports that they can see another customer's data. What do you do?
195. How would you design access control for an admin panel?
196. You discover that application logs contain users' email addresses and addresses. What now?
197. How would you handle a request from a user to export all their data?
198. What is the principle of least privilege, with an example?
199. A third-party library you use is reported to have a serious vulnerability. Steps?
200. How do you keep secrets out of source code?

<details><summary>Outline answers 191–200</summary>

191. Account takeover is the asset at risk. Token: random, single-use, short-lived, stored hashed. Do not reveal whether the email exists. Rate-limit. Invalidate sessions after reset. Notify the user. Security questions are weak; avoid them.
192. Asset: other users and our domain. Threats: disguised executable or script content, huge files, hostile filenames, images carrying location metadata, inappropriate content. Controls: size and type checks by content, re-encode the image, generated names, separate serving domain, strip metadata, limits, reporting.
193. Never in readable form and never with reversible encryption. A slow, salted password-hashing function designed for the purpose, with a per-user random salt; standard library; re-hash on login when parameters are raised. Add multi-factor sign-in and breached-password checks.
194. Treat as a security incident immediately. Reproduce and scope: which data, which customers, since when. Mitigate fast — disable the endpoint or roll back. Involve security and legal about notification duties. Root cause is usually a missing per-object authorisation check; add tests for it everywhere.
195. Separate strong sign-in with multi-factor; role-based permissions with least privilege; every action checked on the server; audit log of who did what; no shared accounts; sensitive actions need a second approval; reachable only from the company network; periodic access review.
196. Stop the leak: redact at the logging layer. Assess: who has access to those logs, how long are they kept, where are they shipped (third parties?). Purge or shorten retention where possible. Add automated detection. Review whether notification is required.
197. Verify the requester's identity. Use the data inventory to gather from every store and third party. Provide a readable, portable format within the legal deadline. Exclude other people's data and security-sensitive internals. Automate and log the fulfilment.
198. Each person and program gets only the access needed for its task, so a mistake or compromise does little. Example: a reporting job has read-only access to two tables — not an administrator account for the whole database.
199. Check whether you use the affected version and whether the vulnerable part is reachable. Assess severity. Upgrade and test, or mitigate temporarily (configuration, firewall rule). Deploy quickly through the normal pipeline. Look for signs of exploitation. Improve dependency tracking.
200. Store them in a secrets manager and inject at run time; never in code, configuration files in the repository, or images. Scan commits automatically; separate secrets per environment; short-lived credentials where possible; rotate regularly; least privilege for each.

</details>

## S. Machine learning and AI (questions 201–212)

Method: [ML questions](#/lesson/thinking/ml-open-ended) and [LLM and RAG questions](#/lesson/thinking/llm-and-rag-questions).

201. When would you *not* use machine learning?
202. A fraud model has 99.5 % accuracy. What do you ask?
203. Which matters more for a cancer-screening model: precision or recall?
204. A model performs well in testing and badly in production. List possible causes.
205. How would you detect that a deployed model is getting worse?
206. Your training data has 2 % positive examples. What are the consequences?
207. How would you evaluate a chatbot that answers customer questions?
208. How do you reduce hallucinations in an LLM feature?
209. Design, at a high level, a system that answers questions from a company's policy documents.
210. A RAG system gives a wrong answer. How do you debug it?
211. What is prompt injection and how do you defend against it?
212. A model's decisions affect loan approvals. What extra concerns arise?

<details><summary>Outline answers 201–212</summary>

201. When clear rules exist; when there is little or biased data; when every decision must be exact and explainable; when errors are intolerable; when success cannot be measured; when a simple heuristic gets most of the value; when nobody will maintain it.
202. What is the base rate of fraud? If 0.5 %, predicting "never" scores the same. Ask for precision and recall, the cost of each error, the comparison with the current rules, and performance by slice and on recent data.
203. Recall first: a missed cancer is far worse than a false alarm followed by another test. But very low precision overwhelms clinics and frightens patients, so set the threshold from the costs and confirm with clinicians.
204. Training–serving skew (features computed differently), data leakage, test set not representative or overlapping with training, drift since training, a different threshold or model version in production, bugs in the serving pipeline, feedback loops.
205. Monitor inputs (feature distributions, missing values), outputs (prediction distribution, rate of positives), delayed true outcomes where available, business metrics and user corrections. Alerts on shifts; periodic re-evaluation on fresh labelled samples.
206. Accuracy becomes meaningless; a model can ignore the positives. Use precision, recall and a suitable threshold; ensure enough positive examples in the test set; consider reweighting or resampling in training; evaluate at the real base rate.
207. Build an evaluation set from real questions including unanswerable and out-of-scope ones. Score correctness, groundedness, relevance, tone and refusal behaviour with code checks, a calibrated model judge and human review. Online: resolution rate, hand-offs to humans, re-asks, satisfaction.
208. Ground it in retrieved sources; instruct it to say when the answer is absent; narrow the task; use tools for facts and arithmetic; require and verify citations; lower randomness; keep humans in the loop for consequential actions. Reduced, never eliminated.
209. Ingest documents, split into chunks, embed, index with permissions and dates. At question time: retrieve by hybrid search filtered by the user's access, rerank, build a grounded prompt, answer with citations, verify citations, refuse when nothing relevant is found. Evaluate retrieval and generation separately.
210. Look at what was retrieved. If the right passage is missing: fix chunking, search or ranking. If present: the prompt, too much irrelevant context, or the model. If the passage itself is wrong or outdated: a content problem. Add the case to the evaluation set.
211. Text crafted so that the model follows an attacker's instructions — typed directly, or hidden in a document, page or email the system reads. Defences: treat external text as data, give the model minimal powers, require approval for actions, keep secrets out of prompts, filter and monitor. No complete cure.
212. Fairness across groups, including indirect discrimination through correlated features; legal requirements to explain decisions; the right to human review; auditability and reproducibility; feedback loops from only observing outcomes of approved loans; careful monitoring and governance.

</details>

## T. Behavioural and situational (questions 213–224)

Method: [STAR, disagreement and outages](#/lesson/thinking/behavioural-star) and [ambiguity and explaining](#/lesson/thinking/behavioural-communication). For each, the outline lists what the interviewer listens for — your own story must supply the content.

213. Tell me about a time you made a mistake at work.
214. Tell me about a time you disagreed with your manager.
215. Tell me about a time you had to deliver bad news.
216. Tell me about the most technically difficult problem you have solved.
217. Tell me about a time you helped someone else succeed.
218. Tell me about a time you received feedback you disagreed with.
219. Tell me about a time you had to make a decision without enough information.
220. Tell me about a time a project failed.
221. Tell me about a time you improved a process.
222. Tell me about a time you had to push back on a deadline.
223. Explain a technical concept you know well to someone with no technical background.
224. Why are you leaving your current role, and why this company?

<details><summary>Outline answers 213–224</summary>

213. A real mistake of moderate size. Own it plainly; what you did immediately to limit harm; whom you told; the cause as a gap in the system as well as your slip; the concrete change you made. No disguised boast, no blame.
214. Understanding their reasoning first; raising it privately with evidence; proposing options; accepting the decision and carrying it out fully — or changing your mind. The relationship afterwards. Not a story about winning.
215. Early, direct and with the facts; what it means for the listener; options and a recommendation; taking responsibility for your part; follow-through afterwards. Shows that you do not hide problems.
216. A clear statement of the problem and why it was hard; how you narrowed it down — hypotheses, measurements, experiments; dead ends; the decisive insight; the result with a number; what you would do differently. Depth under follow-up questions.
217. A specific person and need; what you did — teaching, pairing, reviewing, unblocking — in a way that built their ability instead of doing it for them; the result for them. Generosity without self-praise.
218. Listening before defending; asking for examples; separating the valid part from the part you disputed; what you changed; how you responded to the person. Self-awareness and the ability to be coached.
219. What was unknown and why waiting was costly; how you reduced the uncertainty cheaply; the assumptions you stated; choosing a reversible option where possible; how you checked afterwards and adjusted.
220. What the goal was and how it fell short; your part in it, honestly; early signs that were missed; what you learned and applied since. Avoid both self-flagellation and blaming others.
221. The pain and its cost, measured; what you proposed and how you got agreement; the small first step; the before-and-after numbers; what stuck. Initiative with evidence.
222. Bringing facts early: the estimate, the gap and the reasons; offering options — less scope, more time, more help — with their risks; recommending one; the outcome and the relationship. Not a flat refusal, and not silently missing.
223. Audience first; one sentence of what it is; an analogy from everyday life; one concrete example; why it matters; a check for understanding. No jargon; calm handling of a naive follow-up.
224. Positive and forward-looking: what you want to learn or do next and why this role offers it; evidence that you know what the company builds. Never run down the current employer.

</details>

## U. Ship decisions and product sense (questions 225–230)

Method: ["Should we ship it?"](#/lesson/thinking/ship-decisions-product-sense).

225. A feature is ready except for accessibility support. Ship now?
226. A bug affects only users on a five-year-old phone model. Fix it?
227. How would you improve the checkout of an online shop?
228. A competitor has released a feature your users are asking for. What do you do?
229. Performance tests show the new version is 15 % slower and has an important feature. Ship?
230. Pick a product you use daily. What would you change, and how would you know it helped?

<details><summary>Outline answers 225–230</summary>

225. Ask who is excluded and what the law and company commitments require; in many places accessibility is a legal duty. Options: ship behind a flag to a limited audience while finishing, or delay briefly with a firm date. Do not treat it as optional polish.
226. Size it: how many users, how severe, is there a workaround, what does the fix cost, and does supporting that model matter commercially? Either fix, or officially end support with notice and a clear message — not silent neglect.
227. Goal: more completed purchases without more refunds. Find where people drop out with funnel data; pick the worst step; hypotheses (forced account creation, surprise costs, slow pages, few payment methods); cheapest test first; measure conversion with revenue and refund guardrails.
228. Do not copy by reflex. Understand the need behind the requests and how many users have it; check fit with the product's direction; consider a smaller version that meets the need; estimate cost; test demand cheaply; decide with the product owner.
229. Is 15 % noticeable where it matters — which percentile, which users, which pages? Can the cost be reduced or the feature loaded lazily? Is the feature's value proven? Options: ship to a small share and measure, optimise first, or ship with a plan and a deadline to recover the speed.
230. Goal of the product; a specific user group; one concrete pain you have observed; two or three solutions from small to large with cost and risk; choose one; the metric and guardrail that would show it worked; what could go wrong.

</details>

## Glossary

| Term | Meaning |
|---|---|
| Judgment question | A question assessed on reasoning and decision, not on a single correct answer |
| Base rate | How common something is in the whole population |
| Peak factor | How many times busier the busiest period is than the average |
| Guardrail metric | A measure that must not get worse while another is improved |
| Peeking | Repeatedly checking an experiment and stopping when it first looks significant |
| Cost of delay | What is lost for each unit of time a piece of work is postponed |
| Spike | A short, time-limited investigation to remove an unknown |
| Characterisation test | A test recording what code currently does |
| Least privilege | Granting only the access needed for a task |
| Data inventory | A record of what personal data is held and where |
| Training–serving skew | A difference between how inputs are prepared in training and in production |
| Groundedness | Every claim in an answer being supported by supplied sources |
| STAR | Situation, task, action, result: a structure for behavioural answers |
| Funnel | A sequence of steps in which some users drop out at each |

## Check yourself

```quiz
[
  {"q": "A service must handle 30,000 requests per second; one server handles 600. Running at about two thirds of capacity, roughly how many servers before spares?",
   "options": ["50", "75", "150", "600"],
   "answer": 1,
   "explain": "30,000 / 600 = 50 at full load; dividing by about 0.67 gives roughly 75."},
  {"q": "An experiment shows a small gain with p = 0.04 after two days of a planned two weeks. What is the right response?",
   "options": ["Ship immediately", "Continue to the planned duration and check guardrails and group balance", "Abandon the test", "Double the traffic and stop tomorrow"],
   "answer": 1,
   "explain": "Stopping at the first significant reading is peeking, and two days miss weekly patterns and novelty effects."},
  {"q": "Sign-ups are flat and revenue fell. Which decomposition helps most?",
   "options": ["Revenue = customers × conversion to paid × average price × retention", "Revenue = lines of code × engineers", "Revenue = page views", "Revenue cannot be decomposed"],
   "answer": 0,
   "explain": "Breaking the number into its factors shows which one moved: plan mix, price, refunds or churn."},
  {"q": "You must review a 2,000-line change. What is the best first move?",
   "options": ["Approve it quickly", "Ask for it to be split, or for a walkthrough ordered by risk", "Reject it without comment", "Review only the first file"],
   "answer": 1,
   "explain": "Large changes get skimmed; smaller pieces or a guided, risk-ordered review restore real scrutiny."},
  {"q": "A customer says they can see another customer's data. How should this be classed?",
   "options": ["A minor display bug", "A security incident requiring immediate scoping and mitigation", "A feature request", "Expected behaviour"],
   "answer": 1,
   "explain": "It is a confidentiality breach: reproduce, scope, mitigate quickly and involve security and legal."},
  {"q": "A cancer-screening model is being tuned. Which statement is most defensible?",
   "options": ["Maximise accuracy", "Favour recall, while keeping false alarms low enough for clinics to cope", "Favour precision only", "Ignore both and minimise latency"],
   "answer": 1,
   "explain": "Misses are far costlier than false alarms, but the threshold must still reflect the real cost of both errors."},
  {"q": "In a behavioural answer about a failed project, what should you avoid?",
   "options": ["Describing your own part honestly", "Blaming colleagues or the previous employer", "Saying what you learned", "Giving a concrete example"],
   "answer": 1,
   "explain": "Interviewers look for ownership and learning; blame signals the opposite."}
]
```

> **Source:** Behavioural question categories and STAR as described in Yangshun Tay's Tech Interview Handbook (https://www.techinterviewhandbook.org/behavioral-interview/); estimation prompts in the spirit of Donne Martin's System Design Primer (https://github.com/donnemartin/system-design-primer); OWASP cheat sheets (https://cheatsheetseries.owasp.org/); Google, "Rules of Machine Learning" (https://developers.google.com/machine-learning/guides/rules-of-ml); Google Engineering Practices on code review (https://google.github.io/eng-practices/review/); DORA metrics guidance (https://dora.dev/guides/dora-metrics-four-keys/). All outlines are original.
