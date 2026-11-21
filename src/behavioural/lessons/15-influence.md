# Influence without authority and leadership as an individual contributor

## Before this lesson

Read [Conflict and disagreement](#/lesson/behavioural/conflict) and [Ambiguity and changing priorities](#/lesson/behavioural/ambiguity). Influence stories often contain a disagreement and a vague starting point, so the habits from those lessons (understanding the other view, using evidence, small reversible steps) appear again here.

## In plain words

Think of a neighbour who wants a pedestrian crossing outside the local school. She has no power over the town council. She cannot order anyone to build it. Yet some neighbours get crossings built: they count the cars at school time, photograph near-misses, talk to other parents, find out what the council cares about (budgets, safety statistics, complaints), and present a short, well-supported request at the right meeting. That is **influence without authority**: getting people to act when you cannot tell them to.

Most engineers have no formal authority. An **individual contributor**, often shortened to IC, is someone who does hands-on work and does not manage people. Yet many of the most valuable things an IC does require changing other people's minds: adopting a better tool, fixing a risky design, agreeing a shared standard across teams. Interviewers therefore ask how you lead **without** a title.

Google's re:Work guide describes the leadership attribute Google looks for in individual contributors as **emergent leadership**: stepping up with initiative, working effectively across teams, and developing yourself. Meta's preparation post includes "Tell me about a time you pushed an idea forward despite opposition" as a sample question and mentions leadership and mentorship among the qualities interviewers look for. Microsoft's interview tips ask candidates to be ready to describe how they worked with others and adapted their approach.

For a job, this family matters more as you become more senior: at mid and senior levels, influence across teams is often the main thing that distinguishes you (lesson 24 develops this). For juniors, a small, clear influence story is a strong signal of growth potential.

## What the interviewer is really testing

- **Initiative**: you saw something worth changing and did not wait for permission to start.
- **Understanding others' incentives**: you knew what the people you needed cared about.
- **Persuasion with evidence**: data, prototypes and pilots rather than opinion or pressure.
- **Making it easy to say yes**: you reduced the cost for others (did the setup, wrote the guide, offered help).
- **Building support**: you found allies and gave them credit.
- **Respect for "no"**: you accepted when some people declined, and did not force it.
- **Lasting change**: the new way of working stuck after you stopped pushing.

## Common phrasings

- "Tell me about a time you convinced others to adopt your idea."
- "Tell me about a time you pushed an idea forward despite opposition."
- "Describe a time you led something without being the formal lead."
- "Give me an example of influencing a team you did not belong to."
- "Tell me about a time you changed how your team works."
- "Describe a time you mentored or helped grow someone."
- "Tell me about a time your behaviour positively affected your team."

The last phrasing is close to the example behavioural question in Google's re:Work guide, which asks about a time your behaviour had a positive impact on your team, with follow-ups about your goal, how teammates responded and what came next.

## The influence toolkit

| Tool | What it means | Example |
|---|---|---|
| Understand incentives | Find out what the other person is measured on or worried about | The other team's lead worries about on-call load, not build speed |
| Start with data | Measure the problem before proposing a fix | "Our builds take 22 minutes; here is where the time goes" |
| Pilot with a friendly team | Prove it small before asking for a big commitment | One team tries it for two weeks |
| Write it down | A short proposal people can read and comment on in their own time | A two-page design document with the trade-offs |
| Do the work | Lower the cost of saying yes | "I'll migrate your first service myself" |
| Build allies | People who will speak for the idea in rooms you are not in | The pilot team's lead presents results with you |
| Give credit | Make it their success too | Thank the pilot team publicly |
| Accept "no" | Respect teams with good reasons to decline | One team keeps its setup for a specific reason |

Influence is not manipulation. The tools above all involve honesty: real data, real trade-offs, real choice for the other side. If your story involves going around people, pressuring them or hiding downsides, it will score badly however successful it was.

## An example rubric

An **example** rubric, written for this lesson:

| Level | What it looks like for influence |
|---|---|
| Outstanding | Saw an opportunity and acted without authority; understood others' incentives; persuaded with data or a pilot; lowered the cost of adoption; built allies and shared credit; respected those who declined; lasting, measured change |
| Solid | Persuaded others with reasons and evidence; change adopted; some sign of understanding others' views |
| Borderline | Idea adopted, but mainly because a manager mandated it, or the candidate's role in persuading is unclear |
| Poor | Pushed the idea by pressure or escalation alone; dismissed objections; or no real example of influencing anyone |

## A weak answer (dialogue)

> **Example (fictional).** Question: "Tell me about a time you convinced others to adopt your idea."
>
> **Candidate:** Our builds were really slow, so I suggested we move everything to a new build pipeline setup I'd used before. A couple of the other teams weren't keen, they were quite resistant to change. I kept bringing it up in meetings and eventually our director agreed it was a good idea and told everyone to switch. So in the end everyone moved over.
>
> **Interviewer:** Why were the other teams reluctant?
>
> **Candidate:** I think they didn't like change, really.

The idea was adopted because a director ordered it, not because the candidate persuaded anyone. The other teams are labelled "resistant to change" without curiosity about their reasons. No data, no pilot, no help offered. Borderline at best on the example rubric.

## A strong answer (dialogue, full STAR)

> **Example (fictional).** Same question.
>
> **Candidate:** I'll describe getting four of five product teams to adopt a shared build pipeline, with no authority over any of them, and what I learned from the one team that said no.
>
> *(Situation)* I was a software engineer at a property-listing company with five product teams of about six engineers each. Each team had its own build pipeline, the automated steps that test and package code before release. Ours took about 22 minutes per change, and the others were similar.
>
> *(Task)* Nobody owned build speed across teams. I wanted to show that a shared, faster pipeline template would help everyone, but I was a mid-level engineer on one team and couldn't tell the others what to do.
>
> *(Action)* First I measured. I timed every step of our pipeline for a week and found that about 60% of the time was spent reinstalling the same dependencies on every run, which caching could avoid. I built a template that cached them and ran tests in parallel, and tried it on our own team: builds went from 22 to about 8 minutes. Before proposing it to anyone else, I asked each team's lead for 20 minutes to learn what bothered them about builds. That changed my pitch. Two teams cared most about speed, but the payments team cared about something else entirely: their auditors needed a record of every build step, and they worried a shared template would lose it. I added a step that saved the full build log for a year, which solved their concern. I then wrote a two-page proposal with our before-and-after numbers and the trade-offs, including that teams would depend on a shared template, so I proposed a rotating maintainer from each team. I offered to migrate each team's first service myself, pairing with one of their engineers so they would know how it worked. The search team volunteered as a pilot, and their lead presented their results with me at the monthly engineering meeting.
>
> *(Result)* Within three months, four of the five teams had moved. Their median build time fell from around 20 minutes to under 9, and the payments team's auditors signed off the logging. The fifth team, data platform, declined because their builds ran on special hardware the template didn't support. I agreed that was a good reason and documented it rather than pushing.
>
> *(Reflection)* The 20-minute conversations mattered more than the template. I'd assumed everyone wanted speed; the payments team's real concern was the audit trail, and I'd never have found that in a meeting. I now start any cross-team change by asking each team what would make them say no.
>
> **Interviewer:** What would you have done if the director had said no?
>
> **Candidate:** I'd have kept the template on our team, where it already saved time, shared the numbers, and offered it to anyone who asked. Adoption by choice was what I wanted anyway; a mandate would have made teams resent it.

## Why the strong answer scores higher

| Rubric point | Weak answer | Strong answer |
|---|---|---|
| Acted without authority | Yes | Yes |
| Understood incentives | "They didn't like change" | Asked each lead; discovered the audit concern |
| Persuaded with evidence | Kept bringing it up | Timed the pipeline; own team 22 to 8 minutes |
| Lowered the cost | No | Migrated each team's first service, paired with their engineer |
| Allies and credit | Director's mandate | Pilot team presented results with the candidate |
| Respected "no" | Everyone forced to move | Data platform's reason accepted and documented |
| Lasting, measured change | "Everyone moved over" | Four of five teams, about 20 to under 9 minutes, rotating maintainers |

## Leadership as an individual contributor: more than persuasion

Influence is one form of IC leadership. Others count too, and are often easier for juniors to show:

- **Mentoring**: helping a newer person become effective. ("I paired with our new graduate for her first three tickets and wrote down the questions she asked; that list became our onboarding guide.")
- **Improving how the team works**: a better meeting format, a review checklist, a shared document.
- **Taking the lead on a piece of work**: running a small project, coordinating a release, organising an event.
- **Raising the quality bar by example**: writing the tests and documentation that others then copy.
- **Developing yourself**: Google's description of emergent leadership includes self-development, so a story about deliberately growing a skill and sharing it can fit.

## A junior version: changing how a project team worked

- **Situation.** In a team of five building a mobile app for a module project, we had no automated tests. Every Friday, features that worked on Thursday broke after someone else's changes.
- **Task.** I wasn't the team lead (we didn't really have one), but I wanted us to stop losing Fridays to fixing breakages.
- **Action.** I kept a simple log for two weeks of every breakage and how long it took to fix: seven breakages, about eleven hours in total. Two teammates thought writing tests would slow us down, which was a fair worry with the deadline. So I wrote tests only for the three screens that broke most, set them to run automatically on every change, and showed the team at our next meeting that the tests had already caught one breakage before it reached the shared branch. I offered to write the first test for each person's next feature together with them, so nobody had to learn alone.
- **Result.** By the end of the project, all five of us were writing tests, and breakages fell from about three a week to roughly one every two weeks. Our tutor mentioned our test setup in the feedback.
- **Reflection.** Showing a caught bug was more persuasive than any argument for testing. I now try to bring a small working example before asking anyone to change.

## Likely follow-up probes

| Probe | What it checks | How to answer |
|---|---|---|
| "Why did people resist at first?" | Empathy, understanding incentives | Their real reason, stated fairly |
| "What evidence did you use?" | Data over opinion | The numbers or pilot results |
| "What did you do to make it easy for them?" | Lowering cost | The help you offered |
| "Did anyone not adopt it?" | Respect for "no" | Who, why, and how you responded |
| "How did you share credit?" | Humility | Who you credited and how |
| "What if your manager had disagreed?" | Influence without a mandate | Your fallback, honestly |

## Pitfalls

1. **The mandate story.** Your idea was adopted because someone senior ordered it. That is not influence.
2. **Labelling opponents.** "They were resistant to change" without understanding their reasons.
3. **Persistence as pressure.** "I kept bringing it up until they agreed" sounds like wearing people down.
4. **Hiding downsides.** Every change has trade-offs; name them.
5. **Taking all the credit.** Influence succeeds through others; credit them.
6. **No lasting change.** It was adopted, then abandoned when you stopped pushing.

## Your turn

1. Recall a time you changed how others worked, in any setting. Write the other side's real concern in one sentence.
2. List the evidence you used, and what you did to make it easy to say yes.
3. If nobody declined, ask yourself whether anyone had a reason to, and whether you listened.
4. Tell the story aloud and answer "Why did people resist at first?" and "Did anyone not adopt it?".

## Summary

- Influence without authority means getting people to act when you cannot tell them to; individual contributors need it constantly.
- Google describes "emergent leadership" for ICs: initiative, effective work across teams and self-development. Meta asks about pushing ideas through opposition; Microsoft asks how you worked with others and adapted.
- Strong stories show understanding incentives, persuading with data or pilots, lowering the cost of saying yes, building allies, sharing credit, respecting "no" and lasting change.
- A mandate from above is not influence; labelling opponents as resistant is a weak sign.
- IC leadership also includes mentoring, improving team practices and raising the bar by example.

## Glossary

- **Influence without authority**: persuading people to act when you have no power to instruct them.
- **Individual contributor (IC)**: someone who does hands-on work and does not manage people.
- **Emergent leadership**: Google's term for leadership shown by individual contributors through initiative, cross-team work and self-development.
- **Incentive**: what a person or team is rewarded for or worried about, which shapes what they will agree to.
- **Pilot**: a small trial of a change with a willing group before wider adoption.
- **Build pipeline**: the automated steps that test and package code before release.
- **Mandate**: an instruction from someone with authority, as opposed to agreement won by persuasion.

```quiz
[
  {"q": "In the weak answer, why does the adoption not count as strong evidence of influence?",
   "options": ["The idea was bad", "It was adopted because a director ordered it, not because the candidate persuaded anyone", "Build pipelines are not important", "It took too long"],
   "answer": 1,
   "explain": "A mandate from above is authority, not influence. The rubric looks for persuasion without authority."},
  {"q": "What does Google's re:Work guide call the leadership it looks for in individual contributors?",
   "options": ["Command leadership", "Emergent leadership", "Servant management", "Executive presence"],
   "answer": 1,
   "explain": "Emergent leadership covers stepping up with initiative, working across teams and self-development."},
  {"q": "In the strong answer, what changed the candidate's pitch?",
   "options": ["The director's opinion", "20-minute conversations that revealed the payments team cared about an audit trail, not speed", "A new build tool release", "A deadline"],
   "answer": 1,
   "explain": "Understanding each team's incentives revealed a hidden concern that the candidate could then solve."},
  {"q": "One team declines your proposal for a good technical reason. What is the strongest response?",
   "options": ["Escalate until they comply", "Accept the reason, document it and leave the door open", "Exclude them from future meetings", "Migrate their service without asking"],
   "answer": 1,
   "explain": "Respecting a well-reasoned 'no' is part of the rubric's outstanding level."},
  {"q": "After an influence story, which follow-up probe is most likely?",
   "options": ["Why did people resist at first?", "What is your favourite IDE?", "Can you reverse a linked list?", "How many years have you lived here?"],
   "answer": 0,
   "explain": "Interviewers check that you understood and respected the other side's reasons."},
  {"q": "A student has never influenced another team. Which story best shows IC leadership?",
   "options": ["Logging breakages, writing tests for the worst screens, showing a caught bug and helping each teammate write their first test", "Telling the team they were doing it wrong", "Waiting for the tutor to require tests", "Writing all the tests alone without telling anyone"],
   "answer": 0,
   "explain": "It shows initiative, evidence, a small working example, lowering the cost for others and lasting change."},
  {"q": "Which item is NOT part of honest influence?",
   "options": ["Measuring the problem first", "Piloting with a willing team", "Hiding the downsides so people agree faster", "Offering to do the first migration"],
   "answer": 2,
   "explain": "Hiding trade-offs is manipulation; strong stories name the trade-offs openly."}
]
```

> **Source:** Google re:Work, A guide to structured interviewing (https://rework.withgoogle.com/intl/en/guides/a-guide-to-structured-interviewing-for-better-hiring-practices); Meta, Preparing for your software engineering interview, 2022 (https://www.metacareers.com/blog/preparing-for-your-software-engineering-interview-at-meta/); Microsoft Careers, Interview tips (https://careers.microsoft.com/v2/global/en/hiring-tips/interview-tips). Rubric and dialogues are original and fictional.
