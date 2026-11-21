# Ownership and delivering results

## Before this lesson

Read [Failure, mistakes and feedback](#/lesson/behavioural/failure-feedback) and [Teamwork and collaboration](#/lesson/behavioural/teamwork). You should know the question-family pattern and the habits of saying "I", using numbers and including a reflection.

## In plain words

Think about the difference between renting a flat and owning one. A tenant who sees a small leak under the sink might mention it to the landlord eventually, or might not. An owner fixes it this week, because they know a small leak today is a rotten floor next year. Neither person is lazy; they feel responsible for different things.

**Ownership** at work means acting like the owner of the outcome, not only of your assigned task. You notice problems that are not technically yours, you fix them or make sure someone does, and you think about what happens next year, not only this sprint. **Delivering results** is the partner idea: actually finishing what matters, on time and with quality, even when something gets in the way.

Both appear in company values everywhere. Amazon's Leadership Principles include "Ownership" (in Amazon's description, leaders think long term, act for the whole company rather than only their team, and never say "that's not my job") and "Deliver Results" (focus on the key inputs, deliver them with the right quality and on time, and rise to setbacks rather than settling). Grab's "How we hire" page says its behavioural interviews include questions about handling challenges, managing stakeholders and driving results, and asks candidates to highlight their individual contribution and its impact.

For a job, these are among the most valuable signals you can give, especially early in a career. A junior engineer who reliably finishes things and quietly fixes what is broken around them is often trusted with bigger work sooner.

## What the interviewer is really testing

- **Initiative**: did you act without being told?
- **Scope of care**: do you care about outcomes beyond your own task?
- **Follow-through**: did you finish, including the boring parts (tests, documentation, handover)?
- **Long-term thinking**: did you fix the cause so it stays fixed?
- **Judgement**: did you respect others' areas (asking before touching their code, handing over cleanly) rather than overstepping?
- **Persistence and trade-offs**: when obstacles came, did you find a way, and did you make sensible choices about scope, time and quality?

## Common phrasings

**Ownership:**
- "Tell me about a time you took on something outside your responsibilities."
- "Describe a problem you noticed that nobody else was dealing with."
- "Tell me about a time you went above and beyond."
- "Give me an example of a long-term improvement you made that was not part of your assigned work."

**Delivering results:**
- "Tell me about a time you delivered a project under a tight deadline."
- "Describe a time you faced a major obstacle in delivering something. What did you do?"
- "Tell me about the project you are proudest of. What was the result?"
- "Give an example of a time you had to cut scope to deliver."

## An example rubric

An **example** rubric, written for this lesson:

| Level | What it looks like for ownership and results |
|---|---|
| Outstanding | Noticed an unowned problem or risk and acted without being asked; fixed the root cause and made the fix last (automation, documentation, a clear owner); respected others' areas; persisted through an obstacle with sensible trade-offs; measured, meaningful result |
| Solid | Took clear responsibility for an outcome and followed through to a measured result, with some initiative beyond the assignment |
| Borderline | Did assigned work well, but little sign of initiative or care beyond the task; or result unclear |
| Poor | Story shows passing problems to others, giving up at obstacles, or acting recklessly in others' areas |

## A weak answer (dialogue)

> **Example (fictional).** Question: "Tell me about a time you took on something outside your responsibilities."
>
> **Candidate:** At my last company, I always tried to go above and beyond. For example, I'd often stay late to help other teams, and I'd pick up tickets that weren't mine. I'm the kind of person who doesn't like to see things left undone. My manager said I was very proactive.
>
> **Interviewer:** Could you pick one specific example?
>
> **Candidate:** Sure, there was a time the build was broken and I fixed it, even though it wasn't my code.
>
> **Interviewer:** What was wrong with it?
>
> **Candidate:** I don't remember exactly, a configuration issue I think. I fixed it and it worked again.

The answer opens with a self-description, not a story. When pushed, the example is thin: no detail, no root cause, no lasting fix, no result beyond "it worked again". Borderline at best on the example rubric.

## A strong answer (dialogue, full STAR)

> **Example (fictional).** Same question.
>
> **Candidate:** I'll tell you about noticing that our security certificates had no owner, two weeks before one of them would have taken our app offline, and how I made sure it couldn't happen again.
>
> *(Situation)* I was a backend engineer at a fintech company with about 40 engineers. Our services use security certificates, the files that let a browser or app trust an encrypted connection. Each one expires on a fixed date, and if it expires, connections fail.
>
> *(Task)* Renewing certificates wasn't my job, or officially anyone's: it was done by hand by whoever remembered. While debugging something else, I noticed that the certificate for our payments API expired in sixteen days. I couldn't find any ticket or calendar reminder for it.
>
> *(Action)* First I fixed the immediate risk. I messaged the infrastructure lead, Siti, because her team controlled the servers, told her the date and asked whether she wanted me to renew it or her team to. She was in the middle of a migration and asked me to do it with one of her engineers reviewing. We renewed it that week. Then I looked for the cause: I wrote a short script that listed every certificate we used and its expiry date. There were 23, and three more would expire within two months, also with no owner. I took that list to our weekly engineering meeting and proposed automatic renewal, which our cloud provider supported, plus an alert 30 days before any expiry. Siti agreed her team should own it long term, so I offered to build the first version and hand it over. Over the next two sprints, in about a day a week alongside my own work, I moved 20 of the 23 certificates to automatic renewal. Three couldn't be automated because a partner bank issued them, so I added those to the team calendar with the alert and named owners. Finally I wrote a one-page guide and walked Siti's team through it before handing over.
>
> *(Result)* No certificate has expired since, which is now about eighteen months. The alert has fired twice, both for the partner-bank certificates, and both were renewed with weeks to spare. When another team later found that their own certificates were in the same state, they reused my script.
>
> *(Reflection)* What I took from it is that ownership isn't only fixing the thing; it's making sure someone owns it afterwards. I could have kept renewing them myself, but then the knowledge would leave with me.
>
> **Interviewer:** How did you balance this with your own work?
>
> **Candidate:** I agreed it with my manager first. I showed him the list of 23 and the four near expiries, and we agreed one day a week for two sprints. My own feature slipped by two days, which I flagged at the start.

## Why the strong answer scores higher

| Rubric point | Weak answer | Strong answer |
|---|---|---|
| Noticed an unowned problem | "I always go above and beyond" (a claim) | Found an expiring certificate with no owner |
| Acted without being asked | Fixed a build, details forgotten | Acted the same day, contacted the right team |
| Fixed root cause, made it last | No | Inventory script, automatic renewal, alerts, named owners |
| Respected others' areas | Unknown | Asked Siti first, had her engineer review, handed over to her team |
| Trade-offs | None | Agreed time with manager; own feature slipped two days, flagged |
| Measured result | "It worked again" | Zero expiries in about eighteen months; alerts caught two; script reused |

The weak candidate may well be proactive. But "I am proactive" is a claim, and the only example offered has no details. The strong candidate never says "I am proactive"; the story shows it.

## Ownership without overstepping

Beginners sometimes hear "ownership" as "do everything yourself". That can go wrong. Fixing another team's code without asking, or taking over a colleague's task without telling them, creates confusion and resentment. Notice what the strong candidate did: asked the team that controlled the servers before acting, had their engineer review the change, agreed time with their own manager, and handed the long-term work back to the right team. That is ownership **of the outcome**, not of every piece of the work.

A useful test: after you acted, did the right people know, and does someone clearly own the thing now? If yes, it was ownership. If you left confusion behind, it was overstepping.

## Delivering results: obstacles and trade-offs

Results stories have a shape of their own: a goal with a deadline, an obstacle, a trade-off, and delivery. The **trade-off** is the key moment. Almost every real project has to give up something among scope (how much is built), time and quality. Strong candidates name the trade-off they chose and why.

**A fictional short example**, answering "Tell me about delivering under a tight deadline":

- **Situation.** A government agency client needed an online appointment form live before a policy change took effect, in four weeks.
- **Task.** I was one of two developers. In week two, the identity verification service we depended on announced a three-week delay.
- **Action.** I listed what the form needed on day one versus later. I proposed launching with verification by one-time code sent to a phone number, which we could build in four days, and adding the full identity check in a second release. I wrote down the risk (weaker verification for the first weeks) and how we would limit it (appointments only, no personal records shown), and the client's product owner agreed in writing. I built the phone verification and pair-tested every path with our tester.
- **Result.** We launched on the date; about 3,000 appointments were booked in the first week, and the full identity check shipped three weeks later as planned.
- **Reflection.** Cutting scope deliberately, with the risk written down and agreed, is very different from cutting it silently.

## A junior version: a club

- **Situation.** I was a member, not an officer, of my university's computing club. Our annual hackathon used a shared spreadsheet for registration, and the year before, about 30 people had been double-registered or lost.
- **Task.** Nobody was assigned to fix it. I offered to the president to own registration for that year.
- **Action.** I built a simple form that wrote to a database, with a check that refused a second registration with the same student email, and an automatic confirmation email. I tested it with ten friends, including trying to register twice. I wrote a half-page guide for next year's committee and stored the form in the club's shared account, not mine.
- **Result.** 140 people registered with no duplicates or lost entries, and check-in on the day took about 20 minutes instead of over an hour. The next committee used the same form.
- **Reflection.** I learned to set things up so they outlive me: the shared account and the guide mattered as much as the form.

## Likely follow-up probes

| Probe | What it checks | How to answer |
|---|---|---|
| "Why did you take it on?" | Motivation | The risk you saw and why it mattered |
| "Did anyone ask you to?" | Initiative | Honest; if you volunteered, say so |
| "How did you make sure it stayed fixed?" | Long-term thinking | Automation, documentation, a named owner |
| "Who else was involved, and did you check with them?" | Overstepping | Who you consulted and when |
| "What did you give up to do it?" | Trade-offs | What slipped, and how you flagged it |
| "What would have happened if you hadn't?" | Impact | A concrete, honest estimate of the risk |

## Pitfalls

1. **Self-description instead of a story.** "I'm very proactive" is not evidence.
2. **The heroic overtime story.** Working all weekend is effort, not necessarily ownership. Show judgement and lasting fixes.
3. **Overstepping presented as ownership.** Rewriting someone's code without telling them.
4. **No lasting fix.** Fixing the symptom every time instead of the cause.
5. **Silent scope cuts.** "We dropped some features to make the date" without saying who agreed.
6. **Results without numbers.** Ownership stories especially need a measurable "what would have happened" and "what did happen".

## Your turn

1. List three problems you noticed in any setting (work, school, club, part-time job) that were nobody's job. For each, did you act? What would have happened if nobody had?
2. Pick one where you acted, and write: the immediate fix, the root-cause fix, how it was made to last, and who owns it now.
3. Pick a deadline story and name the trade-off you made among scope, time and quality, and who agreed.
4. Tell both stories aloud and answer "Did anyone ask you to?" and "What did you give up?".

## Summary

- Ownership means acting for the outcome beyond your task; delivering results means finishing what matters, on time and with quality, through obstacles.
- Amazon's "Ownership" and "Deliver Results" principles and Grab's emphasis on driving results and individual contribution both target these signals.
- Strong ownership stories show noticing, acting, fixing the root cause, making it last, and respecting others' areas.
- Strong results stories name the obstacle and the trade-off among scope, time and quality, and who agreed to it.
- Show, do not claim: the story should prove initiative without the word "proactive".

## Glossary

- **Ownership**: taking responsibility for an outcome beyond your assigned task, including making the fix last.
- **Delivering results**: completing important work on time and with quality, despite obstacles.
- **Security certificate**: a file that lets software trust an encrypted connection; it expires on a fixed date.
- **Trade-off**: giving up some of one thing (scope, time or quality) to get more of another.
- **Scope**: how much work or how many features are included.
- **Overstepping**: acting in someone else's area without involving them.
- **Handover**: transferring ownership of work to someone else, with the knowledge they need.

```quiz
[
  {"q": "Which answer opening shows ownership most convincingly?",
   "options": ["I'm the kind of person who goes above and beyond.", "My manager says I'm proactive.", "While debugging, I noticed our payments certificate expired in sixteen days and nobody owned renewing it.", "I work long hours."],
   "answer": 2,
   "explain": "It starts a concrete story about an unowned risk. The others are claims."},
  {"q": "In the strong answer, which action best shows the fix was made to last?",
   "options": ["Renewing one certificate", "Moving 20 of 23 certificates to automatic renewal, alerting 30 days ahead, naming owners and handing over with a guide", "Messaging Siti", "Debugging something else"],
   "answer": 1,
   "explain": "Root-cause fixes plus ownership and documentation keep the problem from returning."},
  {"q": "What separates ownership from overstepping?",
   "options": ["Ownership means doing everything yourself", "Ownership involves the right people and leaves a clear owner; overstepping acts in others' areas without them", "There is no difference", "Overstepping is always faster"],
   "answer": 1,
   "explain": "The test: did the right people know, and does someone clearly own it now?"},
  {"q": "A results story says 'we dropped some features to make the date'. What probe is likely coming?",
   "options": ["Who agreed to that trade-off, and what was the risk?", "What is your favourite feature?", "How many lines of code was it?", "What time did you start work?"],
   "answer": 0,
   "explain": "Interviewers check that scope cuts were deliberate, agreed and understood, not silent."},
  {"q": "Which Amazon Leadership Principle includes never saying 'that's not my job', in Amazon's description?",
   "options": ["Frugality", "Ownership", "Think Big", "Learn and Be Curious"],
   "answer": 1,
   "explain": "Amazon's Ownership principle describes thinking long term, acting for the whole company and not saying it is not your job."},
  {"q": "In the club example, why did storing the form in the club's shared account matter?",
   "options": ["It was cheaper", "It meant the fix outlived the student, which is part of ownership", "It was required by the university", "It made registration slower"],
   "answer": 1,
   "explain": "Making something survive your departure is a sign of long-term ownership."},
  {"q": "Grab's 'How we hire' page asks candidates in behavioural interviews to highlight what?",
   "options": ["Their hobbies", "Their individual contribution and its impact", "Their salary history", "Only team achievements"],
   "answer": 1,
   "explain": "Grab asks for specifics about individual contribution and impact."}
]
```

> **Source:** Amazon, Leadership Principles (https://atoz.amazon/en-us/discover/leadership-principles); Grab, How we hire (https://grab.careers/en/how-we-hire/general/). Rubric and dialogues are original and fictional.
