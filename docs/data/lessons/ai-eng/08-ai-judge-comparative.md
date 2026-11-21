# AI as a judge and comparative evaluation

> **Before this lesson:** read [Exact evaluation and similarity measures](#/lesson/ai-eng/aie-exact-similarity), which explains reference answers and why word-overlap scores miss meaning. It helps to know what a reward model and RLHF are (see [Post-training: SFT and preference finetuning](#/lesson/ai-eng/aie-post-training)), and that model outputs vary from run to run because of sampling (see [Sampling](#/lesson/ai-eng/aie-sampling)). The two small formulas here are explained in words with worked numbers.

## In plain words

Most of what we want from an AI answer, such as being helpful, polite, faithful to a document or free of made-up facts, cannot be checked by running a unit test or matching a reference string. Asking people to read every answer is slow and expensive. The approach the industry settled on is **AI as a judge** (often written *LLM-as-a-judge*): you ask one AI model to grade the outputs of another.

The second half of the lesson covers **comparative evaluation**: instead of giving each model a grade, you show two models' answers side by side, ask which is better, and turn thousands of such contests into a ranking, the way chess players or sports teams are ranked.

An everyday picture: a cooking competition. One way to judge is to give every dish a score out of 10, but different judges mean different things by "7", and the same judge drifts over the day. Another way is to put two plates in front of a taster and ask "which one?". People find the second question much easier, and a league table can be built from enough head-to-head tastings. But tasters have quirks: some prefer whichever plate they tried first, some prefer the bigger portion. AI judges have the same quirks, and this lesson shows how to catch them.

Why this matters for a job: nearly every team building with language models uses AI judges somewhere, from offline test sets to live monitoring. Leaderboards such as LMSYS Chatbot Arena are built on comparative evaluation. Interviewers ask how you would make an LLM judge trustworthy, what position bias is, and how Elo ratings work; this lesson answers all three.

## 1. Why AI as a judge?

AI judges are **fast, cheap and easy to set up**, and they **do not need reference data**. A *reference-free* method can score an answer on its own, which matters in production, where live user questions have no prepared correct answer. You can ask a judge about almost anything: correctness, repetitiveness, toxicity (rude or hateful content), hallucination, wholesomeness. Judges can also **explain** their verdicts, which helps when someone audits the scores later.

The key question is whether their verdicts match what people think. **Agreement** here means the share of cases where the judge and a human chose the same answer; **correlation** is a number between −1 and 1 that says how closely two rankings move together (1 means perfectly in step). The evidence is encouraging:

- Zheng and colleagues (2023) found that on MT-Bench, a set of multi-turn conversation questions, GPT-4 agreed with human raters **85%** of the time. That is higher than the rate at which humans agreed with *each other* (**81%**).
- The AI judges of AlpacaEval, an automatic leaderboard, had a correlation of **0.98** with the human-vote leaderboard of LMSYS Chatbot Arena.

## 2. How to use AI as a judge

There are three common setups:

1. **Score a response on its own**: "Given this question and answer, rate how good the answer is from 1 to 5."
2. **Compare with a reference**: "Given the question, the reference answer and this answer, does this answer say the same as the reference?" This replaces the hand-designed similarity metrics of the previous lesson.
3. **Compare two responses**: "Which of these two answers is better?" This is the basis of comparative evaluation and of the preference data used in post-training.

A judge's instructions are themselves a prompt (the text you send to a model), and a good judge prompt states four things:

- **The task**, for example "evaluate whether the answer is relevant to the question".
- **The criteria**, with explicit definitions. A **criterion** is one quality you score, such as relevance or faithfulness. Vague criteria give vague scores.
- **The scoring system**: a *classification* (good/bad, relevant/irrelevant), discrete numbers (1 to 5) or continuous numbers (0 to 1). Huyen notes that **language models are generally better with words than with numbers**, so classification labels or small discrete scales work better than wide numeric ranges. Very fine scales, such as 1 to 10, make the judgments noisier: the judge cannot reliably tell a 6 from a 7.
- **Examples** of each score with a short justification. This kind of reference sheet is called a **rubric**, and it improves consistency.

Here is a judge prompt that checks **faithfulness**: whether every claim in an answer is supported by a given context. The `{{context}}` and `{{answer}}` placeholders are filled in by your code for each example.

```text
You are evaluating whether an ANSWER is faithful to a CONTEXT.
Faithful = every factual claim in the ANSWER can be inferred from the CONTEXT.
Return exactly one word: FAITHFUL or UNFAITHFUL, then one sentence of justification.

Example:
CONTEXT: The store opens at 9am on weekdays.
ANSWER: The store opens at 8am on Mondays.
VERDICT: UNFAITHFUL - the context says 9am.

CONTEXT: {{context}}
ANSWER: {{answer}}
VERDICT:
```

Read it top to bottom: the first line sets the task; the second defines the criterion in one sentence; the third fixes the output to a two-label classification plus a reason, which makes the verdict easy for code to read; the worked example shows the judge what an unfaithful answer looks like; the last three lines are where each real case goes. In code, using a judge is one more model call, shown here as a static example because it needs an account and a network connection:

```python
JUDGE_PROMPT = open("faithfulness_judge.txt").read()        # the template above
def judge_faithfulness(context, answer):
    prompt = JUDGE_PROMPT.replace("{{context}}", context).replace("{{answer}}", answer)
    reply = client.chat.completions.create(
        model="gpt-4o", temperature=0,                     # same settings every time
        messages=[{"role": "user", "content": prompt}])
    verdict = reply.choices[0].message.content.strip()
    return verdict.startswith("FAITHFUL")                   # True or False
```

The template is loaded once; each call fills in the two placeholders; `temperature=0` (from the sampling lesson) makes the judge as repeatable as the provider allows; and the function turns the judge's words into a True/False your test suite can count.

Many tools ship ready-made judge criteria. Huyen lists Azure AI Studio (groundedness, relevance, coherence, fluency, similarity), MLflow (faithfulness, relevance), LangChain's criteria (conciseness, relevance, correctness, coherence, harmfulness, maliciousness, helpfulness, controversiality, misogyny, insensitivity, criminality) and Ragas (faithfulness, answer relevance).

## 3. Limitations

### Inconsistency

Judges are probabilistic models, so the same judge on the same input can give different scores, and a small change in the judge prompt can swing results. Zheng and colleagues raised GPT-4's consistency from **65% to 77.5%** by adding examples to the judge prompt. Two caveats: consistency is not accuracy (a judge can be consistently wrong), and the longer prompts made their GPT-4 bill **four times** larger.

### Criteria ambiguity

AI judge metrics are not standardised. MLflow, Ragas and LlamaIndex all offer a "faithfulness" criterion, but they score it on 1 to 5, 0/1 and YES/NO scales respectively, with different prompts behind them. Their scores cannot be compared. Worse, **a judge is itself an application that changes over time**. If someone swaps the judge's model or edits its prompt, your metric moves even though your product did not. Huyen's rule: **treat the judge (model plus prompt plus sampling settings) as part of the metric, and version it.** *Versioning* means giving each configuration a name or number and recording it with every score. Do not trust a judge score unless you know exactly which model and prompt produced it.

### Cost and latency

**Latency** is the time a user waits for a response. Using GPT-4 to judge each GPT-4 answer on several criteria can triple your number of model calls. Ways to cut the cost: use cheaper or specialised judges; judge only a random **sample** of traffic (spot-checking); or judge **asynchronously**, meaning after the answer has already gone to the user rather than while they wait. A judge placed *in* the request path, for example as a **guardrail** that blocks bad answers before they are shown, adds its full latency to every request.

### Biases

A **bias** here is a systematic tilt in the judge's verdicts that has nothing to do with answer quality.

- **Self-bias.** Models favour their own outputs. In Zheng and colleagues' study GPT-4 gave itself a 10% higher win rate, and Claude-v1 gave itself 25%.
- **First-position bias.** Many AI judges prefer whichever answer they see first in a pair or list. Humans tend to do the **opposite**: they show **recency bias** and favour the last answer seen. The fix is to ask twice with the order swapped and see whether the verdict follows the answer or the position.
- **Verbosity bias.** Judges prefer longer answers. Wu and Aji (2023) found GPT-4 and Claude-1 preferred answers of about 100 words containing factual errors over correct answers of about 50 words. Saito and colleagues (2023) found that when one answer is about twice as long as the other, the judge almost always picks it. GPT-4 showed less of this than GPT-3.5, which suggests the bias may fade as models improve.
- **Privacy and intellectual property.** A judge hosted by another company sees your data, and you do not know what its own training data contained.

The demo below simulates a judge with first-position bias and measures **swap consistency**: the share of pairs where the judge picks the same *answer* whichever order it sees them in.

```python-run
# Position-bias check: ask the judge about (A,B) and (B,A). A consistent judge flips its label.
# Here we simulate a biased judge that prefers position 1 with probability 0.3 regardless of quality.
import random
random.seed(1)
def judge(first_quality, second_quality, bias=0.3):
    if random.random() < bias: return "first"
    return "first" if first_quality >= second_quality else "second"
pairs = [(random.random(), random.random()) for _ in range(1000)]
consistent = 0
for qa, qb in pairs:
    v1 = judge(qa, qb)            # A shown first
    v2 = judge(qb, qa)            # B shown first
    winner1 = "A" if v1 == "first" else "B"
    winner2 = "B" if v2 == "first" else "A"
    consistent += (winner1 == winner2)
print(f"swap-consistency: {consistent/len(pairs):.1%}  (a bias-free judge would score 100%)")
```

**Reading this Python line by line**

- `random.seed(1)` fixes the random-number generator so the demo gives the same result on every run.
- `judge(first_quality, second_quality, bias=0.3)` is the fake judge. `random.random()` returns a number between 0 and 1, so 30% of the time the judge answers "first" without looking; otherwise it honestly picks the higher-quality answer.
- `pairs` holds 1,000 pairs of answers, each with a random hidden quality between 0 and 1.
- For each pair the judge is asked twice: once with A first (`v1`) and once with B first (`v2`). The next two lines translate "first"/"second" back into which answer, A or B, won.
- `consistent += (winner1 == winner2)` adds 1 when both orders picked the same answer (Python counts `True` as 1).
- Output: `swap-consistency: 68.9%`. Roughly three verdicts in ten flip when the order flips, so any single verdict from this judge is unreliable. In practice you keep only swap-consistent verdicts, or count a flip as a tie.

## 4. Which model should judge?

- **A stronger judge** is the intuitive choice, like an examiner who knows more than the student. It fits a common pattern: generate with a cheap model and have a stronger model grade a sample (say 1%), or grade in the background and replace bad answers. The catch: the strongest model has nobody stronger to judge it, and you need some other way to know which model is strongest in the first place.
- **The same model (self-evaluation or self-critique)** sounds like cheating because of self-bias, but it works as a sanity check and nudges a model to revise its own answers. Huyen's example: asked "What's 10+3?", a model answers 30; asked to check its answer, it corrects itself to 13.
- **A weaker judge** can work because judging may be easier than producing: anyone can tell whether a song is catchy, but few can write one. Still, Zheng and colleagues found that stronger judges agree better with humans, so teams usually pick the strongest judge they can afford.

### Specialised judges

Small models trained for judging can be cheaper and more consistent than large general ones. **Finetuning** means continuing to train an existing model on examples of one task, and these judges are finetuned for scoring:

- **Reward models** take a (prompt, response) pair and output a score, as in RLHF. Google's Cappy, with 360 million parameters, outputs a score between 0 and 1 for how correct a response is.
- **Reference-based judges** score a response against one or more references. BLEURT outputs a similarity score; Prometheus scores against a reference and a rubric.
- **Preference models** take (prompt, response 1, response 2) and say which response is better. PandaLM and JudgeLM also explain their reasoning.

> [!INTERVIEW]
> **"How would you make an LLM-as-judge evaluation trustworthy?"** Version the judge (model, prompt, sampling settings) as part of the metric. Use clear criteria with rubric examples and small discrete or classification outputs. Set temperature to 0. Calibrate against a human-labelled set and report agreement. Counter position bias by swapping order and counting only swap-consistent verdicts, and control for answer length. Avoid having a model judge its own family. Combine with exact metrics where possible, and spot-check with humans.

## 5. Comparative evaluation

Often you do not care about a model's absolute score; you want to know **which model is best for you**. You can rank models by **pointwise** evaluation, scoring each one on its own and sorting by score, or by **comparative** evaluation, putting models head to head and ranking them from the results. For subjective quality, comparing is easier than scoring: choosing the better of two songs is easier than giving one song a mark out of ten.

Anthropic used comparative evaluation for AI models in 2021. LMSYS **Chatbot Arena** made it famous: a visitor types a prompt, two anonymous models answer, and the visitor votes for the better answer (or a tie). Each such comparison is a **match**, and the share of matches in which A beats B is A's **win rate** over B.

Comparative evaluation is **not A/B testing**. In an **A/B test**, each user sees only one version of a product (A or B), and you compare how the two groups behave. In comparative evaluation, one person sees several candidates side by side and picks between them.

> [!WARNING]
> Not every question should be settled by preference. "Is there a link between cell phone radiation and brain tumors?" should be settled by evidence, not votes. Preference voting works only when voters know the subject, for example when the AI helps with tasks the users already understand.

### From matches to ratings: Elo and Bradley–Terry

A **rating** is a number per model, computed from match results, that predicts how likely the model is to beat others; models are then ranked by rating. Rating algorithms borrowed from games and sports include **Elo** (from chess), **Bradley–Terry** and **TrueSkill** (from online gaming). Chatbot Arena started with Elo and later switched to Bradley–Terry, which does not depend on the order in which matches happened.

**Elo, step 1: the expected score.** In words: the bigger A's rating lead over B, the closer A's expected score gets to 1. Elo uses a base-10 curve on which every 400 points of difference multiplies the odds by ten:

$$
E_A = \frac{1}{1 + 10^{(R_B - R_A)/400}}
$$

Worked example: $R_A = 1500$ and $R_B = 1100$. The exponent is $(1100 - 1500)/400 = -1$, so $E_A = 1/(1 + 10^{-1}) = 1/1.1 = 0.909$. A 400-point lead means A is expected to win about ten times for every loss. Equal ratings give $E_A = 1/(1+1) = 0.5$.

**Elo, step 2: the update.** After a match, A's actual score $S_A$ is 1 for a win, 0.5 for a tie and 0 for a loss. In words: each rating moves by $K$ times the surprise, the gap between what happened and what was expected:

$$
R_A' = R_A + K\,(S_A - E_A), \qquad R_B' = R_B + K\,\big((1-S_A) - (1-E_A)\big)
$$

$K$ is a chosen constant (32 is common) that sets how fast ratings move. Worked example with both models at 1000 and $K = 32$: $E_A = 0.5$; if A wins, A gains $32 \times (1 - 0.5) = 16$ points and B loses 16. An upset (a low expected score, then a win) moves ratings a lot; an expected win moves them a little.

```python-run
def expected(ra, rb): return 1 / (1 + 10 ** ((rb - ra) / 400))
def elo(ratings, matches, k=32):
    r = dict(ratings)
    for a, b, s in matches:                # s = 1 (a wins), 0.5 tie, 0 (b wins)
        ea = expected(r[a], r[b])
        r[a] += k * (s - ea)
        r[b] += k * ((1 - s) - (1 - ea))
    return r
start = {"model-1": 1000, "model-2": 1000, "model-3": 1000}
matches = [("model-1","model-2",1), ("model-2","model-3",1), ("model-1","model-3",1),
           ("model-3","model-1",0.5), ("model-2","model-1",1)]
for m, v in sorted(elo(start, matches).items(), key=lambda x: -x[1]):
    print(f"{m}: {v:.1f}")
print("P(1400 beats 1000) =", round(expected(1400, 1000), 3))
```

**Reading this Python line by line**

- `expected(ra, rb)` is the step 1 formula; `**` is Python's "to the power of".
- `elo(ratings, matches, k=32)` copies the starting ratings into `r` (so the original dictionary is not changed), then processes matches one at a time in order.
- Each match is a tuple `(a, b, s)`: the two model names and A's score. The two `+=` lines are the step 2 update.
- `sorted(..., key=lambda x: -x[1])` sorts the (name, rating) pairs by rating from highest to lowest; `lambda x: -x[1]` is a tiny unnamed function that returns minus the rating.
- Output: model-2 1018.0, model-1 1010.4, model-3 971.6, and `P(1400 beats 1000) = 0.909`. The first match gives model-1 exactly +16, as computed by hand; later matches between unequal ratings move less or more depending on how surprising they were.

**Bradley–Terry** takes a different route. It gives each model a strength score $s$ and assumes that the probability A beats B depends only on the difference of their scores, passed through the **sigmoid** function $\sigma(x) = 1/(1 + e^{-x})$, which squashes any number into a probability between 0 and 1. In symbols, $P(A \text{ beats } B) = \sigma(s_A - s_B)$. Worked example: if $s_A - s_B = 1$, then $\sigma(1) = 1/(1 + e^{-1}) = 1/1.368 = 0.73$. (The difference $s_A - s_B$ is the *log-odds* of A winning: $\ln(0.73/0.27) = 1$.) Bradley–Terry then picks the scores that make *all* observed matches as likely as possible at once. This is the same model behind the reward-model loss in RLHF. Because it fits all matches together, shuffling their order cannot change the result. Elo's one-at-a-time updates can. The demo shows both:

```python-run
import math

def expected(ra, rb): return 1 / (1 + 10 ** ((rb - ra) / 400))
def elo(matches, k=32):
    r = {"model-1": 1000.0, "model-2": 1000.0, "model-3": 1000.0}
    for a, b, s in matches:
        ea = expected(r[a], r[b])
        r[a] += k * (s - ea)
        r[b] += k * ((1 - s) - (1 - ea))
    return {m: round(v, 1) for m, v in r.items()}

def bradley_terry(matches, names, steps=3000, lr=0.1):
    s = {m: 0.0 for m in names}
    for _ in range(steps):
        grad = {m: -0.01 * s[m] for m in names}          # tiny pull towards 0 keeps scores finite
        for a, b, out in matches:
            p = 1 / (1 + math.exp(-(s[a] - s[b])))        # current P(a beats b)
            grad[a] += out - p
            grad[b] -= out - p
        for m in names:
            s[m] += lr * grad[m]
    mean = sum(s.values()) / len(s)                       # only differences matter
    return {m: round(v - mean, 2) for m, v in s.items()}

matches = [("model-1","model-2",1), ("model-2","model-3",1), ("model-1","model-3",1),
           ("model-3","model-1",0.5), ("model-2","model-1",1)]
names = ["model-1", "model-2", "model-3"]
print("Elo, original order :", elo(matches))
print("Elo, reversed order :", elo(matches[::-1]))
print("BT,  original order :", bradley_terry(matches, names))
print("BT,  reversed order :", bradley_terry(matches[::-1], names))
```

How the Bradley–Terry part works: all scores start at 0. On each of 3,000 passes, for every match it computes the current predicted probability `p` that A wins, compares it with what happened (`out`), and nudges A's score up and B's down by the difference (a method called *gradient ascent*: repeatedly step in the direction that makes the observed results more likely). The `-0.01 * s[m]` term gently pulls scores towards zero so that a model that never lost cannot run off to infinity. At the end the average is subtracted, because only differences between scores mean anything. `matches[::-1]` is the same list in reverse order.

Output: Elo puts model-2 first (1018.0 versus 1010.4) with the original order but model-1 first (1018.7 versus 1013.1) with the order reversed, from exactly the same five results. Bradley–Terry gives identical scores both times (model-2 0.68, model-1 0.41, model-3 −1.09). With very many matches Elo's order effect shrinks, but Bradley–Terry removes it entirely.

### Challenges of comparative evaluation

- **Scalability.** With $m$ models there are $m(m-1)/2$ pairs, which grows roughly with the square of $m$ (*quadratically*). In January 2024 LMSYS had 244,000 comparisons over 57 models: that is $57 \times 56 / 2 = 1{,}596$ pairs, or only about 153 comparisons per pair. Rating algorithms also assume **transitivity** (if A beats B and B beats C, then A beats C), but human preferences are not always transitive. Every new model must play existing ones, which can reshuffle the ranking. Smarter *matchmaking* picks the pairs whose result would reduce uncertainty the most.
- **Standardisation and quality control.** **Crowdsourced** voters (members of the public who volunteer) type whatever prompts they like, rarely fact-check, may prefer unfiltered answers your product would refuse to give, and some vote maliciously. Many Arena prompts are trivial ("hello"), and trivial prompts cannot separate strong models.
- **From comparative to absolute.** Knowing that B beats A 51% of the time does not tell you whether B is *good enough* for your product, or whether that small gain is worth B's higher price.

Despite these challenges, comparative evaluation captures what users actually care about, is hard to game, and does not saturate the way fixed benchmarks do. Huyen expects its use to grow, especially in combination with other methods.

## Summary

- **AI judges** are fast, flexible, reference-free and agree well with humans (GPT-4 at 85% on MT-Bench). Specify the task, the criteria, a small discrete or label-based scoring system, and rubric examples.
- Limitations: **inconsistency**, **criteria ambiguity** (version your judge), **cost and latency**, and **biases** (self, first-position, verbosity).
- A judge can be stronger, weaker or the same model as the one judged. **Specialised judges** include reward models, reference-based judges and preference models.
- **Comparative evaluation** ranks models from pairwise matches using Elo, Bradley–Terry or TrueSkill. Elo updates one match at a time and depends on order; Bradley–Terry fits all matches together. Watch for quadratic growth in pairs, non-transitive preferences, crowd quality, and the gap between "better than" and "good enough".

## Glossary

- **AI as a judge (LLM-as-a-judge)**: using a model to grade another model's outputs.
- **Reference-free**: able to score an answer without a known correct answer.
- **Agreement / correlation**: share of cases where two raters pick the same; how closely two sets of scores move together (−1 to 1).
- **Criterion**: one quality being scored, such as relevance or faithfulness.
- **Faithfulness**: every claim in the answer is supported by the given context.
- **Rubric**: a scoring guide with examples of each score.
- **Versioning**: recording exactly which configuration (model, prompt, settings) produced a result.
- **Latency**: how long a user waits for a response.
- **Asynchronous evaluation**: scoring after the response has been delivered, off the user's waiting path.
- **Guardrail**: a check that blocks or fixes bad inputs or outputs.
- **Self-bias / first-position bias / verbosity bias**: favouring one's own outputs; favouring the first answer shown; favouring longer answers.
- **Recency bias**: the human tendency to favour the last option seen.
- **Swap consistency**: the share of pairs judged the same way when the order is swapped.
- **Self-evaluation (self-critique)**: a model checking its own answer.
- **Reward model / preference model**: a model that scores one response; a model that picks the better of two.
- **Pointwise vs comparative evaluation**: scoring each model alone vs ranking them by head-to-head matches.
- **Match / win rate**: one head-to-head comparison; the share of matches one model wins against another.
- **A/B test**: showing different users different versions and comparing outcomes.
- **Rating**: a number per model, computed from matches, used to rank and predict wins.
- **Elo**: a rating method that updates after each match by K times (actual minus expected score).
- **Bradley–Terry**: a rating method that fits all matches at once with P(A beats B) = sigmoid(sA − sB).
- **Sigmoid**: the function 1/(1+e^−x), which turns any number into a probability.
- **Transitivity**: if A beats B and B beats C, then A beats C.
- **Crowdsourcing**: collecting judgements from many volunteers or paid members of the public.

```quiz
[
  {"q": "On MT-Bench, how did GPT-4-human agreement compare with human-human agreement (Zheng et al., 2023)?", "options": ["65% vs 90%", "85% vs 81%", "50% vs 50%", "99% vs 70%"], "answer": 1, "explain": "GPT-4 agreed with humans 85% of the time, slightly above the 81% agreement among humans."},
  {"q": "MLflow, Ragas and LlamaIndex each give a 'faithfulness' score for the same output. What's the main problem?", "options": ["They are all identical", "Different prompts and scales (1-5, 0/1, YES/NO) make the scores incomparable", "None support RAG", "They require references"], "answer": 1, "explain": "AI-judge metrics aren't standardised. The judge's model and prompt define the metric."},
  {"q": "AI judges' position bias typically favours…", "options": ["The last answer (recency), like humans", "The first answer, the opposite of humans", "The shorter answer", "Neither"], "answer": 1, "explain": "Many AI judges show first-position bias, while humans tend to show recency bias."},
  {"q": "A cheap, robust mitigation for position bias in pairwise judging is…", "options": ["Increase temperature", "Evaluate both orderings and keep only consistent verdicts (or count a flip as a tie)", "Use longer answers", "Remove the system prompt"], "answer": 1, "explain": "Swapping order exposes position effects, and agreement across both orders signals a real preference."},
  {"q": "Two models have Elo ratings 1500 and 1100. The expected score of the 1500 model is about…", "options": ["0.50", "0.76", "0.91", "0.99"], "answer": 2, "explain": "A 400-point gap gives E = 1/(1+10^-1) ≈ 0.909."},
  {"q": "Why did Chatbot Arena move from Elo to Bradley-Terry?", "options": ["Bradley-Terry is faster to compute on GPUs", "Elo's sequential updates make results depend on match order; Bradley-Terry fits all matches jointly", "Elo can't handle ties", "Bradley-Terry needs no data"], "answer": 1, "explain": "Bradley-Terry estimates ratings from all comparisons at once, so the result does not depend on order, as the demo shows."},
  {"q": "Which question should NOT be resolved by preference voting?", "options": ["Which of two poems is more fun?", "Is there a link between cell phone radiation and brain tumors?", "Which email draft sounds friendlier?", "Which logo do you like?"], "answer": 1, "explain": "Factual questions should be decided by evidence, not popularity."},
  {"q": "Comparative evaluation differs from A/B testing because…", "options": ["A/B tests show users multiple outputs at once", "In comparative evaluation one person sees outputs from multiple models side by side", "Comparative evaluation never uses humans", "They are the same"], "answer": 1, "explain": "An A/B test shows each user one variant, while comparative evaluation shows candidates side by side."}
]
```

> **Source:** Huyen, *AI Engineering*, ch. 3 ("AI as a Judge", "Ranking Models with Comparative Evaluation").
