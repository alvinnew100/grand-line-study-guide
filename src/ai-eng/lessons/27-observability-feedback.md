# Observability, orchestration and user feedback

Once the architecture has context construction, guardrails, routers, gateways, caches and agentic loops, three questions come up. How do you know what the system is doing? How do the parts fit together? How does the system get better over time? Huyen's answers are **monitoring and observability**, **AI pipeline orchestration** and **user feedback**. User feedback is also the source of proprietary data, which makes it a competitive advantage.

## 1. Monitoring and observability

Observability should be part of a product's design from the start. The more complex the product, the more it matters. The goal of monitoring is the same as the goal of evaluation: to **mitigate risks and discover opportunities**. The risks are application failures, security attacks and drifts. The opportunities are improvements and cost savings.

Three DevOps metrics measure how good your observability is:

- **MTTD** (mean time to detection): when something bad happens, how long until you notice?
- **MTTR** (mean time to response): after detection, how long until it is resolved?
- **CFR** (change failure rate): the percentage of changes or deployments that cause failures needing fixes or rollbacks. If you don't know your CFR, your platform is not observable enough.

A high CFR points at your **evaluation pipeline**, since bad changes should be caught before deployment. Evaluation and monitoring have to work together. Metrics used in evaluation should carry over to monitoring, and issues found in monitoring should feed back into evaluation.

> [!NOTE]
> **Monitoring vs observability.** Monitoring tracks a system's external outputs to tell you *when* something is wrong, with no guarantee that the outputs explain *what*. Observability makes a stronger assumption: the system is instrumented well enough that its internal state can be inferred from its outputs, so you can find the cause **without shipping new code**. Huyen uses "monitoring" for tracking information and "observability" for the whole process of instrumenting, tracking and debugging.

### Metrics

Metrics are not the goal. Their purpose is to tell you when something is wrong and where to improve. **Design metrics around the failure modes you want to catch.**

- **Format failures** are the easiest to track. How often is the JSON invalid? Of those cases, how many are easily fixable (a missing closing bracket) and how many are not (missing keys)?
- **Generation quality**: factual consistency, relevance, conciseness and so on, often computed with AI judges.
- **Safety**: toxicity, PII in inputs and outputs, how often guardrails trigger, how often the system refuses, and abnormal queries (which may be edge cases or prompt attacks).
- **Conversational signals**. How often do users stop a generation halfway? What is the average number of turns per conversation? What are the average tokens per input and per output? How is the output token distribution changing over time?
- **Component metrics**: for RAG, context relevance and precision; for a vector database, storage and query time.
- **Latency**: TTFT, TPOT and total latency, tracked per user to see how the system scales.
- **Cost**: the number of queries, input and output token volume, requests per second against rate limits, and cache cost and hit rate.

Measure how metrics correlate with each other and with your **north-star business metrics** (DAU, session duration, subscriptions). Strongly correlated metrics suggest what to improve, and uncorrelated ones suggest what not to optimize.

Choose between **spot checks** (sampling) and **exhaustive checks** (every request), usually a mix. Make every metric sliceable by **user, release, prompt or chain version, prompt type and time**.

### Logs and traces

Metrics are aggregates. **Logs** are an append-only record of events. A typical debugging sequence:

1. Metrics tell you something went wrong five minutes ago.
2. You read the logs from around that time to see what happened.
3. You correlate the errors in the logs with the metrics to confirm you found the right issue.

For fast detection, metrics must be computed quickly. For fast response, logs must be available quickly. If logs are 15 minutes behind, you cannot debug something from 5 minutes ago.

**Log everything**, since you don't know what you will need. That includes configuration (model endpoint, model name, sampling settings such as temperature, top-p, top-k and stop conditions, and the prompt template), the user query, the **final prompt** sent to the model, the output, intermediate outputs, tool calls and tool outputs, and component start, end and crash events. Give each record tags and IDs so you know where it came from. Logs grow fast, so use automated log analysis and anomaly detection, and also **inspect production data manually** every day. Shankar et al. (2024) found that developers' ideas of good and bad outputs change as they see more data, which lets them rewrite prompts and update evaluation pipelines.

A **trace** is the detailed record of one request's path through the system: from the user's query through every action (retrieval, model call, tool use) to the final response, with the **time and cost of each step**. Ideally you can follow each query's transformation step by step and see exactly where it failed.

```python-run
import time, json, uuid
# A tiny tracer: one trace per request, one span per step with duration and cost.
class Trace:
    def __init__(self, query): self.id, self.query, self.spans = uuid.uuid4().hex[:8], query, []
    def span(self, name, fn, cost=0.0, **meta):
        t = time.perf_counter(); out = fn()
        self.spans.append({"step": name, "ms": round((time.perf_counter() - t) * 1000, 2), "cost_usd": cost, **meta})
        return out
tr = Trace("When does my order arrive?")
intent = tr.span("router", lambda: "order_status", model="intent-small")
ctx = tr.span("retrieval", lambda: ["order 123: ships Friday"], k=1)
prompt = tr.span("prompt_build", lambda: f"Context: {ctx}\nQ: {tr.query}", template="support_v7")
answer = tr.span("generation", lambda: "Your order ships Friday.", cost=0.0004, model="big", temperature=0.2, input_tokens=24, output_tokens=6)
ok = tr.span("output_guardrail", lambda: "Friday" in ctx[0], check="consistency")
print(json.dumps({"trace_id": tr.id, "query": tr.query, "spans": tr.spans}, indent=1))
print("total cost:", sum(s["cost_usd"] for s in tr.spans))
```

### Drift detection

The more parts a system has, the more can change:

- **System prompt changes.** Someone edits the prompt template, fixes a typo, or a coworker updates it without telling you. Simple logic catches this.
- **User behaviour changes.** Users adapt to the technology. They learn to phrase queries to get better answers, or to write more concise prompts, which gradually shifts response lengths. If you only watch metrics you may not see the cause. Investigation is needed.
- **Underlying model changes.** With an API, the model can change while the API stays the same. Providers do not always disclose updates. Chen et al. (2023) and Voiceflow documented significant shifts between versions of GPT-4 and GPT-3.5, so track quality on a fixed evaluation set over time.

```python-run
import numpy as np
rng = np.random.default_rng(0)
# Detect a silent change by comparing this week's output-length distribution to a baseline.
baseline = rng.normal(180, 40, 2000)       # output tokens per response last month
this_week = rng.normal(230, 40, 500)       # after an unannounced model update
def psi(a, b, bins=10):                    # population stability index
    edges = np.quantile(a, np.linspace(0, 1, bins + 1)); edges[0], edges[-1] = -np.inf, np.inf
    pa = np.histogram(a, edges)[0] / len(a) + 1e-6; pb = np.histogram(b, edges)[0] / len(b) + 1e-6
    return float(np.sum((pb - pa) * np.log(pb / pa)))
print(f"mean length {baseline.mean():.0f} -> {this_week.mean():.0f} tokens, PSI = {psi(baseline, this_week):.2f} (above 0.25 is usually treated as a significant shift)")
```

## 2. AI pipeline orchestration

An **orchestrator** specifies how models, databases and tools work together in an end-to-end pipeline, and makes sure data flows between them. It works in two steps:

1. **Components definition.** Tell the orchestrator which models, retrieval data sources and tools the system uses, and any evaluation and monitoring tools. A model gateway makes adding models easier.
2. **Chaining**, which is function composition: the steps from receiving a query to completing the task. For example: process the raw query, retrieve relevant data, combine query and data into a prompt, generate, evaluate the response, and return it if it is good or route to a human if not.

The orchestrator passes data between steps, helps ensure each step's output matches the next step's expected input, and should notify you when the flow breaks because of component failures or data mismatches.

> [!WARNING]
> An AI pipeline orchestrator is **not** a general workflow orchestrator such as Airflow or Metaflow.

For latency-sensitive applications, **do as much in parallel as possible**. Routing and PII removal can run at the same time.

Tools include LangChain, LlamaIndex, Flowise, Langflow and Haystack. Many RAG and agent frameworks are orchestrators too. Huyen's advice is to **start without an orchestrator**. Any external tool adds complexity, and an orchestrator can hide details of how your system works, making it harder to understand and debug. Adopt one later if it makes life easier. When evaluating one, look at:

- **Integration and extensibility.** Does it support the components you use now and may use later, and is it easy to extend when it doesn't?
- **Support for complex pipelines**: branching, parallel processing, error handling.
- **Ease of use, performance and scalability.** Look for intuitive APIs, good documentation and community support, no hidden API calls, no added latency, and the ability to scale with your applications and traffic.

## 3. User feedback

User feedback has always served two purposes: **evaluating** the application and **informing its development**. In AI applications it has a third role. Feedback is **proprietary data**, and data is a competitive advantage. It powers the **data flywheel**: a product that launches early and attracts users collects data that improves its models, which makes it harder for competitors to catch up. Feedback is also *user data*, so respect privacy. Users have the right to know how their data is used.

### Extracting conversational feedback

- **Explicit feedback** is what users give when asked: thumbs up or down, star ratings, a yes/no to "Did we solve your problem?". It is standard across applications, but **sparse**, and biased toward people who bother to respond.
- **Implicit feedback** is inferred from user actions. It depends on the application and is abundant but **noisy**.

Conversational interfaces make feedback easy to give and hard to extract. Suppose an assistant suggests three hotels. Replying "Yes, book me the one close to galleries" reveals an interest in art. "Is there nothing under \$200?" reveals price sensitivity and tells you the assistant has not understood the user yet.

Feedback can be used for **evaluation** (deriving monitoring metrics), **development** (training future models or guiding improvements) and **personalization**.

**Natural language feedback** (signals in the content of messages):

- **Early termination.** The user stops a response mid-generation, exits the app, tells the model to stop, or just walks away. The conversation is probably going badly.
- **Error correction.** Follow-ups starting with "No, …" or "I meant, …" indicate a miss. Users may **rephrase** their request (detectable with heuristics or ML models), point out specific errors ("Bill is the suspect, not the victim"), ask the model to check itself ("Are you sure?", "Check again", "Show me the sources"), or **edit the model's output directly**. A user edit is a strong signal and gives you free **preference data**: the original is the losing response and the edited version is the winning one.
- **Complaints.** Users complain without correcting: the answer is wrong, irrelevant, toxic, lengthy, lacking detail. In the FITS dataset analysis cited by Huyen, the most common complaint types were that the bot did not answer the question, was not specific enough, or gave wrong facts.
- **Sentiment.** Frustration ("Uggh"), disappointment or, less often, satisfaction. Call centers track voices that get louder through a call. Sentiment changing over a conversation is informative. The model's own **refusal rate** ("Sorry, I can't…", "As a language model…") is also a signal.

**Other conversational feedback** (signals in actions):

- **Regeneration.** The first response may have been unsatisfying, or the user may just want options, which is common for creative and image tasks. Regeneration signals are stronger under usage-based billing than under flat subscriptions. Some apps ask users to compare the new response with the old one, which gives comparative feedback.
- **Conversation organization.** Deleting, renaming, sharing and bookmarking. Deleting is a strong negative signal, unless it is for embarrassment or privacy. Renaming suggests the conversation was good and the auto-title was bad.
- **Conversation length.** Its meaning depends on the product. For an AI companion, long conversations mean engagement. For a customer-support bot, long conversations mean inefficiency.
- **Dialogue diversity.** Measured by distinct tokens or topics. A long conversation in which the bot keeps repeating itself means the user is stuck in a loop.

Explicit feedback is easier to interpret but sparse. Implicit feedback is plentiful but ambiguous. Use both, and study your own users to learn what the signals mean.

```python-run
import re
# Heuristic extraction of implicit signals from conversations (a classifier would do this in production).
def signals(turns):
    s = set()
    user = [t for r, t in turns if r == "user"]
    for t in user[1:]:
        low = t.lower()
        if re.match(r"(no[,.!]|i meant|that's not)", low): s.add("error_correction")
        if re.search(r"are you sure|check again|show me the sources", low): s.add("asks_to_verify")
        if re.search(r"ugh|useless|this is wrong|terrible", low): s.add("negative_sentiment")
    if len(user) > 1 and len(set(re.findall(r"\w+", user[0].lower())) & set(re.findall(r"\w+", user[-1].lower()))) >= 3: s.add("rephrase")
    bot = [t for r, t in turns if r == "assistant"]
    if len(bot) != len(set(bot)): s.add("bot_repeating (low dialogue diversity)")
    return sorted(s)
convo = [("user", "Find me a hotel in Sydney under 200 dollars"), ("assistant", "Here is the Historic Rocks Hotel at 400 per night."),
         ("user", "No, I meant under 200 dollars"), ("assistant", "Here is the Historic Rocks Hotel at 400 per night."),
         ("user", "Ugh, this is wrong. Find me a hotel in Sydney under 200 dollars")]
print(signals(convo))
```

### Feedback design

**When to collect feedback.** Throughout the journey, without getting in the user's way.

- **In the beginning (calibration).** Face ID scans your face, a voice assistant learns your voice, a language app tests your level. Make it optional unless it is necessary, because it adds friction.
- **When something bad happens.** Let users downvote, regenerate, switch models, or say "You're wrong". Ideally users can still finish their task: let them **edit** the output or **collaborate** with the AI (inpainting is an example of collaboration that also gives high-quality feedback). If that fails, hand off to humans.
- **When the model has low confidence.** Ask the user. Show a short and a long summary side by side, which gives **comparative feedback**. Google Photos asks "Is this the same person?" for uncertain face matches. Showing two **full** responses to compare can be poor feedback, because few users read both. Showing partial responses or shorter options works better.

Positive feedback matters too, to reveal the "aha" features. Some product people argue it is unnecessary, because good results are the expected default. Asking only in specific contexts and sampling a small share of users (around 1%) limits disruption, though sampling introduces bias.

**How to collect feedback.** It should integrate into the workflow, be easy to give, and be easy to ignore.

- **Midjourney**: for each prompt, users can upscale an image (U), generate variations (V) or regenerate. Each choice is a strong signal about which image was best.
- **GitHub Copilot**: suggestions appear in lighter text. Tab accepts, and continuing to type ignores. Feedback comes at almost no cost to the user.
- Standalone chat apps such as ChatGPT and Claude are less embedded in daily workflows than tools like Copilot, so they may get less natural feedback.
- **Context matters.** A thumbs-down without the preceding conversation is hard to act on. Ask for consent to attach recent interaction data and say clearly how it will be used. Some products ask users to donate the last N conversations along with their feedback.
- **Explain how feedback is used.** Is it for personalization, aggregate statistics or training? If users fear it is not private, they will not give it. Tell users when their feedback changes their experience.
- **Avoid ambiguous design.** Huyen shows icon-only emotion buttons that users misread. A choice between a "shorter" and a "longer" version is useful only if you can tell why the user chose it.

### Feedback limitations

**Biases:**

- **Leniency bias.** People rate more positively than deserved, to be nice or to avoid follow-up questions. Uber's average driver rating in 2015 was 4.8, with below 4.6 risking deactivation. Replacing numbers with descriptive options ("Great ride", "Could've been better", "Don't match me with this driver again") gives more granular signals.
- **Randomness.** Users click at random because they cannot be bothered to read two long responses.
- **Position bias.** Users click the first suggestion more often, whatever its quality. Randomize positions or model the bias.
- **Preference bias.** People prefer longer responses in side-by-side comparisons even when they are less accurate, because length is easier to notice than errors. There is also **recency bias**: favouring the answer seen last.

**Degenerate feedback loops.** You only get feedback on what you show. When predictions influence feedback, and that feedback trains the next model, initial biases are amplified. In a video recommender, items ranked high get more clicks and are then ranked higher still. This is exposure bias, also called popularity bias or filter bubbles. A model that learns users like cat photos shows more cats until the product is only cats. For assistants, the same loop can train **sycophancy**: Sharma et al. (2023) and Stray (2023) describe models learning to tell users what they want to hear rather than what is accurate or beneficial.

So understand the limits of feedback before training on it, inspect it for biases, and consider how it will change the product over time.

> [!INTERVIEW]
> **"How would you build a feedback loop for an AI writing assistant?"** Instrument implicit signals in the workflow (accept, edit, regenerate, copy, early stop) plus light explicit signals (thumbs, optional comment). Log context with consent and say how it will be used. Derive monitoring metrics (acceptance rate, edit distance between suggestion and final text, regeneration rate) and correlate them with north-star metrics. Turn user edits into preference data (original = losing, edited = winning) for evaluation sets and later finetuning. Guard against bias: randomize positions, watch for leniency and length preference, and avoid degenerate loops and sycophancy by not optimizing engagement alone. Feed production failures back into the evaluation pipeline.

## Summary

- **Observability**: judge it by MTTD, MTTR and CFR. Design **metrics** around failure modes, and make them sliceable and correlated with north-star metrics. **Log everything**, keep **traces** per request, read production data manually, and detect **drift** in prompts, user behaviour and underlying models.
- **Orchestration**: define components, then chain them. Run steps in parallel where possible. Start without an orchestrator, and when you choose one, check integration, complex-pipeline support, ease of use, performance and hidden API calls.
- **User feedback** is evaluation data, development guidance and a proprietary data moat (the data flywheel). Collect **explicit** and **implicit** signals: early termination, error correction, complaints, sentiment, regeneration, organization, length, diversity.
- **Design** feedback to be seamless and contextual, and respect privacy. Collect it at the start, when things go wrong, and when the model is unsure.
- **Limits**: leniency, randomness, position and preference biases, and degenerate feedback loops that can amplify bias and sycophancy.

```quiz
[
  {"q": "Which three metrics does Huyen use to judge the quality of a system's observability?", "options": ["TTFT, TPOT, TPS", "MTTD, MTTR, CFR", "BLEU, ROUGE, F1", "MFU, MBU, QPS"], "answer": 1, "explain": "Mean time to detection, mean time to response, and change failure rate."},
  {"q": "A high change failure rate (CFR) most directly suggests you should…", "options": ["Buy more GPUs", "Strengthen the evaluation pipeline so bad changes are caught before deployment", "Disable logging", "Raise temperature"], "answer": 1, "explain": "Evaluation and monitoring must work together. Pre-deployment evaluation should catch regressions."},
  {"q": "What is a trace?", "options": ["An aggregate metric", "The linked record of a request's whole path through the system, with time and cost per step", "A type of guardrail", "A cache key"], "answer": 1, "explain": "Traces let you follow a query step by step and locate the failing component."},
  {"q": "Which is NOT one of the drift sources discussed?", "options": ["System prompt changes", "User behaviour changes", "Underlying model changes behind an API", "Changes in GPU fan speed"], "answer": 3, "explain": "Prompts, users and underlying models are the drift sources. Providers may update models without notice."},
  {"q": "Huyen's advice about orchestration tools is to…", "options": ["Adopt the most complex one on day one", "Start building without one, and adopt later if it helps", "Use Airflow as an AI orchestrator", "Avoid them forever"], "answer": 1, "explain": "Orchestrators add complexity and can hide critical details. Understand your pipeline first."},
  {"q": "A user edits the assistant's generated text before using it. Why is this especially valuable?", "options": ["It reduces token cost", "It is a strong signal and yields preference data: original = losing response, edited = winning response", "It proves the model is perfect", "It disables caching"], "answer": 1, "explain": "User edits are free preference-finetuning examples."},
  {"q": "For a customer-support bot, a very long conversation usually indicates…", "options": ["High engagement, which is always good", "Inefficiency: the bot is struggling to resolve the issue", "Low latency", "A cache hit"], "answer": 1, "explain": "Interpretation depends on the product. Long is good for companions and bad for support."},
  {"q": "A degenerate feedback loop is when…", "options": ["Users stop giving feedback", "Predictions influence the feedback used to train the next model, amplifying initial biases", "The cache evicts entries", "Logs are delayed"], "answer": 1, "explain": "You only get feedback on what you show. This leads to popularity bias and can even train sycophancy."}
]
```

> **Source:** Huyen, *AI Engineering*, ch. 10 ("Monitoring and Observability", "AI Pipeline Orchestration", "User Feedback": extracting conversational feedback, feedback design, feedback limitations).
