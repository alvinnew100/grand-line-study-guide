# Customer focus and high standards

## Before this lesson

Read [Ownership and delivering results](#/lesson/behavioural/ownership-results) and [Influence without authority](#/lesson/behavioural/influence). Customer and quality stories often include ownership (fixing what nobody owned) and influence (persuading others to raise the bar), so those habits carry over.

## In plain words

Two bakers make bread. The first follows the recipe, sells what comes out of the oven and never asks customers anything. The second notices that regulars stopped buying the rye loaf, asks one of them why ("it goes stale by Tuesday"), adjusts the recipe, and refuses to sell loaves that come out under-baked even on a busy morning. Both work hard. Only the second is focused on the customer and holds a high standard.

**Customer focus** means caring about the people who use what you build, understanding their real problems, and letting that guide your decisions. **High standards** means caring about quality beyond what anyone checks: fixing problems properly so they do not come back, and not passing defects on to others. These two often appear together, because the reason for high standards is usually someone downstream (a customer, a colleague, the on-call engineer at 3 am) who will pay for low ones.

Companies make these explicit. Amazon's first Leadership Principle is "Customer Obsession": in Amazon's description, leaders start with the customer and work backwards, and work hard to earn and keep customer trust. Another is "Insist on the Highest Standards": leaders keep raising the bar, and make sure defects are not sent down the line and problems are fixed so they stay fixed. Sea's first value is "We Serve", which in Sea's words holds that customers alone decide what its products and services are worth.

For an engineer, the "customer" is not always an external user. An **internal customer** is anyone inside the company who uses your work: another team calling your service, the support team using your admin tool, the analyst reading your data. Stories about internal customers count fully.

## What the interviewer is really testing

- **Who you build for**: do you think about the end user, or only the ticket?
- **Getting close to customers**: did you talk to them, read their feedback, watch them use the product, look at data about their behaviour?
- **Turning feedback into action**: did what you learned change what you built?
- **Fixing properly**: did you find the root cause and make sure it stayed fixed?
- **Raising the bar for others**: did your standard influence the team?
- **Pragmatism**: do you balance quality with speed sensibly, rather than polishing forever?

## Common phrasings

**Customer focus:**
- "Tell me about a time you went out of your way for a customer or user."
- "Describe a time you used customer feedback to change what you were building."
- "Tell me about a difficult customer and how you handled them."
- "Give an example of a decision you made because of the user, even though it cost you something."

**High standards:**
- "Tell me about a time you refused to compromise on quality."
- "Describe a time you raised the quality bar for your team."
- "Tell me about a time you were not satisfied with something that others thought was good enough."
- "How do you decide when something is good enough to ship?"

## An example rubric

An **example** rubric, written for this lesson:

| Level | What it looks like for customer focus and standards |
|---|---|
| Outstanding | Went to the source (customers, support, data) to understand a real problem; changed the product or plan because of it; fixed the root cause and prevented recurrence; raised the bar for others; balanced quality and speed with a clear reason; measured effect on customers |
| Solid | Understood and acted on a real customer problem or quality issue; good outcome for users |
| Borderline | Customer mentioned but at a distance ("users would like it"); or quality story is about personal polish with no user benefit |
| Poor | Story shows ignoring users, shipping known defects carelessly, or perfectionism that blocked delivery without reason |

## A weak answer (dialogue)

> **Example (fictional).** Question: "Tell me about a time you went out of your way for a customer."
>
> **Candidate:** I always put the customer first. In my last role I was working on the checkout page and I made sure everything was really polished. I spent extra time on animations and making the design pixel-perfect because I think customers really appreciate attention to detail. The designers were impressed with how closely it matched the mock-ups.
>
> **Interviewer:** How did customers respond?
>
> **Candidate:** I think they liked it. We didn't really get complaints.

The answer opens with a slogan, then describes polish chosen by the candidate's taste. The people impressed are designers, not customers. There is no contact with any customer, no evidence of a customer problem, and "no complaints" is not a result. Borderline on the example rubric.

## A strong answer (dialogue, full STAR)

> **Example (fictional).** Same question.
>
> **Candidate:** I'll tell you about sitting with our support team for two afternoons to understand why older customers kept failing to pay, and the fix that came out of it.
>
> *(Situation)* I was a mobile engineer at a grocery delivery company. Our payment success rate was about 94%, which the team considered normal, and nobody had looked closely at the failures.
>
> *(Task)* While on support rotation, a week where an engineer helps answer escalated customer issues, I noticed that many payment complaints came from customers over 60. I wasn't assigned to payments, but I wanted to know whether we were failing a whole group of customers.
>
> *(Action)* First I asked the support lead, Jia Hui, if I could sit with her team for two afternoons. I listened to eleven calls about failed payments. In eight of them, the customer had been sent to their bank's verification page, a step where the bank sends a one-time code by text message, and our app's countdown timer had expired before they found and typed the code. Our timeout was 60 seconds; the bank allowed five minutes. Then I checked the data: I pulled a month of failed payments and found that about 40% failed at that verification step, and the failure rate rose sharply with customer age. I wrote this up in a one-page note with the call notes and the chart, and took it to the payments team, because it was their code. They agreed the 60-second limit had been an arbitrary choice. I offered to make the change with them: we matched the bank's five-minute window, added a clear message telling customers a code was on its way to their phone, and added a "resend code" button. I also asked for an alert if the verification failure rate rose above its new level, so we'd notice a regression, a return of the old problem, quickly.
>
> *(Result)* Over the next month, payment success rose from about 94% to about 97.5%, and failed-payment calls to support fell by roughly half. Among customers over 60, success rose the most. Jia Hui started forwarding a weekly summary of payment complaints to the payments team, which hadn't happened before.
>
> *(Reflection)* What I learned is that the most useful customer data I've ever seen came from listening to calls, not from dashboards. The dashboard told us the failure rate; the calls told us why. I now try to spend an afternoon with support whenever I work on a feature that customers complain about.
>
> **Interviewer:** Why did you take this to the payments team rather than fixing it yourself?
>
> **Candidate:** It was their code and their on-call. If I'd changed it alone, they'd have been supporting a change they didn't understand. Bringing them the evidence also meant they owned the alert afterwards.

## Why the strong answer scores higher

| Rubric point | Weak answer | Strong answer |
|---|---|---|
| Went to the source | No customer contact | Sat in on eleven support calls, then checked a month of data |
| Real customer problem | Assumed customers like polish | Verification timeout failing older customers |
| Changed the product because of it | Polish chosen by taste | Timeout, message, resend button |
| Root cause and prevention | None | Arbitrary 60-second limit; alert for regressions |
| Raised the bar for others | None | Weekly complaint summary from support to payments |
| Measured customer effect | "No complaints" | Success 94% to 97.5%; support calls roughly halved |

## High standards: a separate story shape

A high-standards story often has a moment of tension: someone wants to move on, and you think the work is not good enough yet. The interviewer is checking two things at once: that you care about quality **and** that you are pragmatic about it.

**A fictional short example**, answering "Tell me about a time you raised the quality bar for your team":

- **Situation.** On a team of seven running a booking service, about one build in four failed because of **flaky tests**: tests that sometimes pass and sometimes fail without any code change.
- **Task.** The team habit was to press "retry" until the build passed. I thought this was hiding real bugs, but nobody owned the problem.
- **Action.** I tracked every flaky failure for two weeks: 31 failures from nine tests. I investigated the worst three and found that one was not flaky at all: it was catching a real timing bug that happened in production roughly once a week. I fixed that bug, fixed the timing assumptions in the other two tests, and proposed a rule to the team: any test that fails without a code change gets a ticket and is either fixed or switched off within a week, never silently retried. I offered to fix the first batch myself.
- **Result.** Over the next month, build failures fell from about one in four to about one in twenty-five, and the production timing bug stopped.
- **Reflection.** The flaky test that turned out to be a real bug convinced the team more than any argument about quality. It taught me that "retry until green" is how real problems hide.

### "How do you decide when something is good enough to ship?"

This question tests pragmatism. A strong answer names a principle, then proves it with a story. For example: the standard depends on how reversible the decision is and who pays for a defect. A layout detail on an internal page can ship and be improved later; anything touching payments, personal data or safety gets full tests and review. Then give an example where you shipped something imperfect on purpose, and one where you held something back.

## A junior version: volunteering

- **Situation.** I volunteered with a community centre that ran free computer classes for retirees. Their sign-up page, built by a previous volunteer, was used by about 50 people a month.
- **Task.** The centre's coordinator mentioned that many seniors phoned to sign up instead of using the page, which took her hours each week. I offered to find out why.
- **Action.** Instead of guessing, I asked to watch three seniors try the page at the centre. All three struggled with the same things: small text, a date picker that needed precise taps, and an error message in red that said only "invalid input". I made the text larger, replaced the date picker with a list of the next eight class dates as large buttons, and rewrote the error messages in plain words ("Please enter a phone number with 8 digits"). I tested the new page with two other seniors before switching over.
- **Result.** Over the next two months, phone sign-ups fell from about 30 a month to about 8, and the coordinator said she got back most of an afternoon each week.
- **Reflection.** Watching three people use the page told me more than any design guide. I now test with real users before I consider something done.

## Likely follow-up probes

| Probe | What it checks | How to answer |
|---|---|---|
| "How did you know it was a real problem?" | Going to the source | The calls, data or observation |
| "Who was the customer exactly?" | Clarity about the user | Name the group, internal or external |
| "What did it cost you or the team?" | Trade-offs | Time, a delayed feature, and why it was worth it |
| "How did you make sure it stayed fixed?" | Root cause and prevention | Alert, test, process change |
| "When have you shipped something you weren't fully happy with?" | Pragmatism | A real example with your reasoning |
| "How did others react to your standard?" | Influence, respect | Any pushback, and how it resolved |

## Pitfalls

1. **The slogan.** "I always put the customer first" is not evidence.
2. **Customers at a distance.** Assuming what users want without asking, watching or measuring.
3. **Polish for its own sake.** Quality that benefits nobody but your sense of craft.
4. **Perfectionism that blocks delivery.** High standards without pragmatism worry interviewers.
5. **Blaming the customer.** "The users didn't understand the feature" is a red flag.
6. **No measured effect on users.** "No complaints" is not a result.

## Your turn

1. Name your customers in one recent project: external users and internal ones.
2. Find one moment where you learned something directly from a customer (a conversation, feedback, watching them, data). What did you change because of it?
3. Find one moment where you held back work that was not good enough, or shipped something imperfect on purpose. Write your reasoning.
4. Tell one of these stories aloud and answer "How did you know it was a real problem?".

## Summary

- Customer focus means understanding the real problems of the people who use your work and letting them guide decisions; high standards means fixing things properly and not passing defects downstream.
- Amazon's "Customer Obsession" and "Insist on the Highest Standards" and Sea's "We Serve" target these signals.
- Internal customers (other teams, support staff, analysts) count fully.
- Strong stories go to the source (calls, observation, data), change the product because of it, fix the root cause, raise the bar for others and measure the effect on users.
- Show pragmatism: high standards that block delivery without reason worry interviewers.

## Glossary

- **Customer focus**: caring about and acting on the real needs of the people who use your work.
- **Internal customer**: someone inside your organisation who uses your work.
- **High standards**: holding work to a quality level that prevents problems for others, and fixing issues so they stay fixed.
- **Support rotation**: a period when an engineer helps the support team with escalated customer issues.
- **Flaky test**: a test that sometimes passes and sometimes fails without any code change.
- **Regression**: the return of a problem that had been fixed, or a new defect in something that used to work.
- **Pragmatism**: choosing a sensible level of quality for the situation rather than the maximum possible.

```quiz
[
  {"q": "Which opening is the strongest start to a customer-focus answer?",
   "options": ["I always put the customer first.", "I made the design pixel-perfect.", "I sat in on eleven support calls about failed payments and found most customers ran out of time at the bank verification step.", "Customers are important to every business."],
   "answer": 2,
   "explain": "It shows going to the source and finding a real, specific customer problem."},
  {"q": "In the weak answer, who was impressed by the candidate's work?",
   "options": ["Customers", "Designers", "Support staff", "Nobody"],
   "answer": 1,
   "explain": "The evidence came from designers, not customers, and 'no complaints' is not a customer result."},
  {"q": "In the strong answer, which part is the Task?",
   "options": ["Payment success was about 94%", "I noticed many complaints came from customers over 60 and wanted to know whether we were failing a whole group", "Success rose to about 97.5%", "I listened to eleven calls"],
   "answer": 1,
   "explain": "The Task is the goal the candidate took on; the others are Situation, Result and Action."},
  {"q": "Which Amazon Leadership Principle includes not sending defects down the line, in Amazon's description?",
   "options": ["Frugality", "Insist on the Highest Standards", "Think Big", "Earn Trust"],
   "answer": 1,
   "explain": "Insist on the Highest Standards describes raising the bar and fixing problems so they stay fixed."},
  {"q": "A candidate is asked 'How do you decide when something is good enough to ship?' Which answer is strongest?",
   "options": ["When it is perfect", "Whenever the deadline arrives", "It depends on reversibility and who pays for a defect, with an example of shipping something imperfect on purpose and one of holding something back", "When my manager says so"],
   "answer": 2,
   "explain": "A principle plus evidence shows pragmatic high standards."},
  {"q": "After a high-standards story, which follow-up probe is most likely?",
   "options": ["When have you shipped something you weren't fully happy with?", "What is your favourite colour?", "Explain recursion.", "Do you have a driving licence?"],
   "answer": 0,
   "explain": "Interviewers check that high standards come with pragmatism, not perfectionism."},
  {"q": "Does a story about another team using your service count as customer focus?",
   "options": ["No, only paying customers count", "Yes, internal customers count fully", "Only at Amazon", "Only for managers"],
   "answer": 1,
   "explain": "Anyone who uses your work is a customer of it, inside or outside the company."}
]
```

> **Source:** Amazon, Leadership Principles (https://atoz.amazon/en-us/discover/leadership-principles); Sea, Our values (https://sea.com/aboutus/ourvalues). Rubric and dialogues are original and fictional.
