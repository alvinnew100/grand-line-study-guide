# Remote and video interviews, and questions to ask

## Before this lesson

Read [Saying "I", using data, and getting the length right](#/lesson/behavioural/i-data-length) (answer length matters even more on video) and [Red flags](#/lesson/behavioural/red-flags), which covered not asking questions and using outside help during interviews. The company lessons (20 to 23) list each employer's own suggestions about questions to ask.

## In plain words

Performing a song in a concert hall and performing it on a video call are different jobs. The song is the same, but on video the audience cannot feel your energy, there is a small delay, the sound can drop, and a dog barking next door suddenly matters. Good performers adjust: they check the equipment, they look into the lens, they pause a little longer, and they have a plan for when the connection fails.

Many interviews now happen by video or phone, especially recruiter calls and early screens, and at some companies the whole loop is remote. The content of a good answer does not change, but the delivery does, and small technical problems can cost you if you are not ready for them.

The second half of this lesson covers the questions **you** ask, usually in the last five minutes. Amazon describes an interview as a "two-way door", a chance for both sides to decide; one of its Bar Raisers says the best candidate questions feel more like a conversation with a curious friend than an interrogation. Good questions show interest and preparation, help you decide whether you want the job, and leave a final impression. "No, I think you've covered everything" wastes that chance, and Amazon lists skipping the chance to ask questions among its common interview mistakes.

## Part 1: remote and video interviews

### Formats

Microsoft's "How we hire" page says its interviews can take place by phone, video call or in person. Meta's process includes screens by phone or video. Amazon's "What it's like to interview" page describes phone interviews followed by remote interviews. Expect a mix, and ask your recruiter which format each stage uses.

### Before the day

Apple's interview tips suggest choosing a quiet space with few interruptions, having the interview link ready and previewing it, and checking that your equipment and internet connection work. Meta's process page suggests testing your computer and Wi-Fi beforehand and protecting your interview time, since last-minute rescheduling is difficult.

A practical checklist, based on that advice plus general good practice:

| Area | Check |
|---|---|
| Link and software | Open the link the day before; install any app it needs; sign in |
| Camera | At eye level, face lit from the front, plain background |
| Sound | Headphones with a microphone; test recording your own voice |
| Connection | Test speed; plan a backup (a phone hotspot) |
| Space | Quiet room, door closed, people at home warned, notifications off |
| Contacts | The recruiter's email and phone number written down in case the link fails |
| Materials | Water; a printed copy of your CV; paper and pen |
| Timing | Ready about 15 minutes early, as Apple suggests for virtual interviews too |

### Interactive: pre-call checklist

Tick each item as you prepare. The page shows how ready you are and lists what is left. It keeps nothing after you close it.

```html-run
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Pre-call checklist</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 12px; color: #1f2937; background: #fff; }
  label { display: block; padding: 4px 0; }
  .meter { height: 18px; background: #e5e7eb; border-radius: 9px; overflow: hidden; margin: 10px 0; }
  .fill { height: 100%; background: #059669; width: 0; transition: width 0.2s; }
  h3 { margin: 14px 0 4px; font-size: 15px; }
  #left { color: #b45309; }
</style>
</head>
<body>
<div id="list"></div>
<div class="meter"><div class="fill" id="fill"></div></div>
<div id="status"></div>
<div id="left"></div>
<script>
var groups = {
  "Day before": ["Opened the interview link and installed what it needs", "Tested camera, microphone and headphones", "Tested internet speed and set up a backup hotspot", "Wrote down the recruiter's email and phone number", "Read my story bank and the company's values page", "Prepared three questions to ask"],
  "One hour before": ["Room quiet, door closed, people at home warned", "Notifications off on computer and phone", "Camera at eye level, face lit from the front", "Water, printed CV, pen and paper ready"],
  "Fifteen minutes before": ["Joined or ready to join the call", "Closed every unrelated window, including any AI tools", "Took three slow breaths"]
};
var html = "";
Object.keys(groups).forEach(function (g) {
  html += "<h3>" + g + "</h3>";
  groups[g].forEach(function (item) { html += "<label><input type='checkbox'> " + item + "</label>"; });
});
document.getElementById("list").innerHTML = html;
function update() {
  var boxes = document.querySelectorAll("input[type=checkbox]");
  var done = 0, left = [];
  boxes.forEach(function (b) { if (b.checked) done++; else left.push(b.parentNode.textContent.trim()); });
  var pct = Math.round(100 * done / boxes.length);
  document.getElementById("fill").style.width = pct + "%";
  document.getElementById("status").textContent = done + " of " + boxes.length + " done (" + pct + "%).";
  document.getElementById("left").textContent = left.length ? "Still to do: " + left.slice(0, 3).join("; ") + (left.length > 3 ? "; and " + (left.length - 3) + " more." : ".") : "Ready. Good luck.";
}
document.querySelectorAll("input[type=checkbox]").forEach(function (b) { b.addEventListener("change", update); });
update();
</script>
</body>
</html>
```

The page builds one checkbox per item from the `groups` object, and `update` counts ticked boxes, fills the bar and names the first three items still to do.

### Delivering answers on video

- **Look at the camera when you speak**, at least for key sentences. Looking at the interviewer's face on screen looks, to them, like looking down.
- **Pause a beat longer.** Video adds a small delay; leave a second after the interviewer stops before you start, so you do not talk over each other.
- **Keep answers slightly shorter.** Attention drops faster on video. Aim for the lower end of the two-minute target.
- **Signpost.** Without full body language, short phrases help: "There were three things I did. First..." "So, the result..."
- **Check in occasionally.** "Would it help if I went deeper into the technical part?" replaces the cues you would read in a room.
- **Show your thinking on screen** if you are asked to share your screen or use a shared document, and narrate what you are doing.

### Phone interviews

With no video at all, your voice carries everything. Stand up or sit upright (it changes your voice), smile when greeting (it is audible), signpost even more, and keep your CV and story-bank keywords in front of you.

### Notes, honesty and tools

A printed CV and pen are normally fine. Reading **scripted answers** from the screen is not a good idea even where it is allowed: it sounds recited and fails at the first probe. Using **AI tools or any outside help** during the interview is a red flag unless the company explicitly permits it for that interview, as lesson 19 explained: Google and Microsoft say not to, while Meta's select technical interviews include a built-in assistant and forbid outside tools. If you are unsure what is allowed, ask the recruiter beforehand.

### When things go wrong

Something will go wrong eventually: frozen video, a fire alarm, a delivery at the door. One of Amazon's Bar Raisers advises candidates to speak up if their surroundings disrupt a virtual interview, and recalls a candidate who stepped away during an earthquake and was later hired. The lesson: say what is happening, calmly, and agree how to continue.

- **Connection drops:** rejoin; if you cannot within a couple of minutes, email or call the recruiter with the contact you wrote down.
- **Noise or interruption:** "I'm sorry, there's a loud noise outside. Could you give me ten seconds?" Mute, deal with it, return.
- **You missed the question because of lag:** "Sorry, the audio cut out. Could you repeat the last part?" Never guess.

## Part 2: questions to ask the interviewer

### Why your questions matter

1. **They show interest and preparation.** A specific question about the team's work shows research; a generic one shows little.
2. **They help you decide.** Amazon's mistakes article encourages asking about what matters to you, such as responsibility, growth, career development and culture.
3. **They are the last thing the interviewer hears.**

### What the companies suggest

- **Apple** suggests asking about the role and what success looks like in it, culture and community, and how Apple's values might align with your own.
- **Meta** suggests preparing questions for the recruiter call about team dynamics, role specifics and next steps.
- **Amazon** suggests questions about what is important to you, including responsibilities, growth and the Leadership Principles, and asking clarifying questions during technical exercises.

### Categories and examples

| Category | Example questions |
|---|---|
| The role and success | "What would success look like in the first six months?" "What is the biggest challenge someone in this role will face?" |
| The team | "How does the team decide what to work on next?" "How do engineers and product managers work together here?" |
| How work gets done | "What does a typical week look like?" "How are code reviews and releases handled?" |
| Growth | "How do engineers here usually grow into the next level?" "What does mentoring look like on this team?" |
| Culture and values | "Which of the company's values do you see most in this team's daily work, and can you give an example?" |
| The interviewer's own experience | "What has surprised you most since joining?" "What project are you most excited about right now?" |
| Next steps | "What are the next steps in the process, and when should I expect to hear?" |

### Tailor questions to the interviewer

| Interviewer | Good focus |
|---|---|
| Recruiter | Process, timeline, team structure, next steps |
| Engineer | Technical work, tools, code review, on-call, how decisions are made |
| Hiring manager | Success in the role, priorities, team challenges, growth |
| Senior leader | Direction of the team or product, how this role fits the bigger picture |

### Weak and strong questions

| Weak | Why weak | Stronger version |
|---|---|---|
| "What does your company do?" | Shows no research | "I read about your move to self-service onboarding for merchants. How has that changed the engineering team's priorities?" |
| "Do you have any questions for me?" reversed: "No, I'm good." | Wastes the chance | Any genuine, prepared question |
| "How did I do?" | Puts the interviewer on the spot; they usually cannot say | "Is there anything about my background you'd like me to clarify?" |
| "How many days of leave do I get?" (first interview, first question) | Can sound as if the package matters most | Save package details for the recruiter or the offer stage |
| A question answered earlier in the interview | Shows you were not listening | Build on it: "You mentioned the migration. How is the team handling..." |

### How many questions?

Prepare five or six, so that you still have two or three after some are answered during the interview. Ask two or three, depending on time. Listen to the answers and follow up on one, which turns questions into the conversation Amazon's Bar Raiser describes.

## After the interview

- **Write notes** straight away: questions asked, stories used, probes that surprised you (lesson 8).
- **Thank-you message**: MIT's career office suggests sending a thank-you email within 24 hours, repeating your interest and why you would be a good fit, with separate messages if you met several interviewers. Meta's process page suggests personalised thank-you messages to interviewers through its candidate portal. Keep them short and specific: mention one thing you discussed.
- **Next steps**: Apple says you should receive guidance on next steps; if you do not, contact your recruiter, and be patient while the team evaluates.

> **Example (fictional thank-you email).** "Dear Priya, thank you for your time today. I enjoyed hearing about how your team moved merchant onboarding to self-service, especially the decision to start with the smallest merchants. It made me more excited about the role. Best regards, Daniel."

## Summary

- Interviews may be by phone, video or in person; content stays the same, delivery adapts.
- Prepare as Apple and Meta suggest: quiet space, link ready, equipment and connection tested, about 15 minutes early.
- On video: look at the camera for key points, pause for lag, keep answers a little shorter, signpost and check in.
- Never read scripts or use outside help unless explicitly permitted; ask the recruiter if unsure.
- If something goes wrong, say so calmly; an Amazon Bar Raiser recalls a candidate hired after stepping away during an earthquake.
- Always ask questions. Apple suggests role, success, culture and values; Meta suggests team dynamics, role and next steps; Amazon suggests what matters to you, and calls interviews a two-way door.
- Afterwards: notes, a short specific thank-you (MIT suggests within 24 hours), and patience on next steps.

## Glossary

- **Remote interview**: an interview held by phone or video call rather than in person.
- **Lag**: the small delay in sound or video on a call.
- **Signposting**: short phrases that tell the listener where an answer is going.
- **Backup connection**: a second way to get online, such as a phone hotspot.
- **Two-way door**: Amazon's description of an interview as a mutual assessment.
- **Thank-you message**: a short note after an interview thanking the interviewer and restating interest.

```quiz
[
  {"q": "Your video freezes mid-answer and you cannot rejoin. What should you do?",
   "options": ["Wait silently for an hour", "Email or call the recruiter using the contact you wrote down beforehand", "Assume you have failed", "Send the interviewer a social media message"],
   "answer": 1,
   "explain": "Having the recruiter's contact ready lets you fix the problem quickly and calmly."},
  {"q": "According to Apple's tips, how early should you be ready for a virtual interview?",
   "options": ["On the minute", "About 15 minutes early", "Two hours early", "It does not apply to virtual interviews"],
   "answer": 1,
   "explain": "Apple suggests about 15 minutes early for both onsite and virtual interviews."},
  {"q": "Which closing question is strongest for a hiring manager?",
   "options": ["How did I do?", "What does your company do?", "What would success look like for this role in the first six months?", "No questions, thanks."],
   "answer": 2,
   "explain": "It shows interest in succeeding in the role and helps you decide; Apple suggests asking about the role and success."},
  {"q": "What does Amazon call an interview in its mistakes article?",
   "options": ["A one-way test", "A two-way door", "A formality", "A negotiation"],
   "answer": 1,
   "explain": "Amazon describes interviews as mutually beneficial, a two-way door."},
  {"q": "Is it acceptable to use an AI tool during a remote interview?",
   "options": ["Always", "Never, under any circumstances", "Only where the company explicitly permits it for that interview; otherwise it is a red flag", "Only if the camera is off"],
   "answer": 2,
   "explain": "Google and Microsoft say not to; Meta's select technical interviews include a built-in assistant and forbid outside tools. Follow each interview's stated rules."},
  {"q": "Why should you pause a beat longer before answering on video?",
   "options": ["To seem thoughtful", "Video adds a small delay, so pausing avoids talking over the interviewer", "It is required", "To check your notes"],
   "answer": 1,
   "explain": "Lag means the interviewer may still be speaking on their end when you hear silence."},
  {"q": "MIT's career office suggests sending a thank-you email within what time?",
   "options": ["24 hours", "One week", "One month", "Only after an offer"],
   "answer": 0,
   "explain": "MIT CAPD suggests within 24 hours, with separate messages for different interviewers."}
]
```

> **Source:** Apple, Interview tips (https://www.apple.com/careers/us/interview_tips.html); Amazon, Bar Raiser tips (https://www.aboutamazon.com/news/workplace/amazon-job-interview-questions-tips-bar-raisers); Amazon, Interview mistakes to avoid (https://www.aboutamazon.com/news/workplace/amazon-jobs-interview-mistakes); Amazon, What it's like to interview at Amazon (https://www.aboutamazon.com/working-at-amazon/whats-it-like-to-interview-at-amazon); Meta, Hiring process (https://www.metacareers.com/hiring-process/); Microsoft Careers, How we hire (https://careers.microsoft.com/i/us/en/how-we-hire); MIT CAPD, The STAR method for behavioral interviews (https://capd.mit.edu/resources/the-star-method-for-behavioral-interviews/). Checklist page and examples are original.
