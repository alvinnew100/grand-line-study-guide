TRACK = dict(
    id="behavioural",
    title="Behavioural Interviews",
    icon="🗣️",
    color="#0f766e",
    group="Engineering Practice",
    blurb="Tell-me-about-a-time questions from zero to offer: how structured interviews are scored, STAR and its variants, "
          "a reusable story bank, ten question families with weak and strong model answers, follow-up probes and red flags, "
          "playbooks for Amazon, Google, Meta, Microsoft, Apple and Singapore employers, senior-level signals, and offers "
          "with Singapore employment basics. Interactive STAR builder, answer timer, story-bank matrix and probe drill.",
    sources=[
        "Amazon Leadership Principles and interview preparation pages (https://atoz.amazon/en-us/discover/leadership-principles)",
        "Amazon on the Bar Raiser and interviewing (https://www.aboutamazon.com/news/workplace/amazon-bar-raiser)",
        "Google, How we hire (https://www.google.com/about/careers/applications/how-we-hire/)",
        "Google re:Work, A guide to structured interviewing (https://rework.withgoogle.com/intl/en/guides/a-guide-to-structured-interviewing-for-better-hiring-practices)",
        "Meta, Preparing for your software engineering interview and Hiring process (https://www.metacareers.com/hiring-process/)",
        "Microsoft Careers, Interview tips and How we hire (https://careers.microsoft.com/v2/global/en/hiring-tips/interview-tips)",
        "Apple, Interview tips (https://www.apple.com/careers/us/interview_tips.html)",
        "US OPM, Structured interviews (https://www.opm.gov/policy-data-oversight/assessment-and-selection/other-assessment-methods/structured-interviews/)",
        "MIT CAPD, Northwestern, Michigan Tech and Strayer career centres on STAR and behavioural answers",
        "UC Berkeley Graduate Division, offer negotiation tips",
        "Singapore MOM and TAFEP employment guidance (https://www.mom.gov.sg, https://www.tal.sg/tafep)",
        "GovTech, Grab, DBS, ByteDance and Sea hiring and values pages",
    ],
    modules=[
        dict(
            id="foundations",
            title="Foundations",
            summary="What behavioural interviews are, why companies structure them, and how your answers are scored.",
            lessons=[
                dict(id="what-is-behavioural", title="What a behavioural interview is", file="01-what-is-behavioural.md"),
                dict(id="structured-interviews", title="Why companies use structured interviews", file="02-structured-interviews.md"),
                dict(id="how-you-are-scored", title="How you are scored", file="03-how-you-are-scored.md"),
            ],
            problems=[],
        ),
        dict(
            id="telling-a-story",
            title="Telling a Story",
            summary="STAR part by part, its variants (CARD, SAR, PAR, STAR(R)), and the habits that lift an answer's score.",
            lessons=[
                dict(id="star-in-depth", title="STAR in depth", file="04-star-in-depth.md"),
                dict(id="star-variants", title="STAR variants: CARD, SAR, PAR and STAR(R)", file="05-star-variants.md"),
                dict(id="i-data-length", title='Saying "I", using data, and getting the length right', file="06-i-data-length.md"),
            ],
            problems=[],
        ),
        dict(
            id="preparing-material",
            title="Preparing Your Material",
            summary="Finding stories in work, study and life, organising them into a story bank, and the opening questions.",
            lessons=[
                dict(id="mining-experience", title="Mining your experience for stories", file="07-mining-experience.md"),
                dict(id="story-bank", title="Building a story bank", file="08-story-bank.md"),
                dict(id="tell-me-about-yourself", title='"Tell me about yourself", "Why us?" and "Why this role?"', file="09-tell-me-about-yourself.md"),
            ],
            problems=[],
        ),
        dict(
            id="question-families-1",
            title="Question Families I",
            summary="Teamwork, conflict, failure and feedback, ownership and results, ambiguity: weak and strong answers, probes and practice.",
            lessons=[
                dict(id="teamwork", title="Teamwork and collaboration", file="10-teamwork.md"),
                dict(id="conflict", title="Conflict and disagreement", file="11-conflict.md"),
                dict(id="failure-feedback", title="Failure, mistakes and feedback", file="12-failure-feedback.md"),
                dict(id="ownership-results", title="Ownership and delivering results", file="13-ownership-results.md"),
                dict(id="ambiguity", title="Ambiguity and changing priorities", file="14-ambiguity.md"),
            ],
            problems=[],
        ),
        dict(
            id="question-families-2",
            title="Question Families II",
            summary="Influence, customers and standards, hypothetical scenarios, follow-up probes and red flags.",
            lessons=[
                dict(id="influence", title="Influence without authority and leadership as an individual contributor", file="15-influence.md"),
                dict(id="customer-standards", title="Customer focus and high standards", file="16-customer-standards.md"),
                dict(id="hypothetical-questions", title="Hypothetical and scenario questions", file="17-hypothetical-questions.md"),
                dict(id="follow-up-probes", title="Handling follow-up probes", file="18-follow-up-probes.md"),
                dict(id="red-flags", title="Red flags: what makes interviewers worry", file="19-red-flags.md"),
            ],
            problems=[],
        ),
        dict(
            id="company-playbooks",
            title="Company Playbooks",
            summary="What Amazon, Google, Meta, Microsoft, Apple and Singapore employers publish about their interviews and values.",
            lessons=[
                dict(id="amazon", title="Amazon: Leadership Principles, the loop and the Bar Raiser", file="20-amazon.md"),
                dict(id="google-meta", title="Google and Meta", file="21-google-meta.md"),
                dict(id="microsoft-apple", title="Microsoft and Apple", file="22-microsoft-apple.md"),
                dict(id="singapore-companies", title="Singapore companies: GovTech, Grab, DBS, ByteDance and Sea", file="23-singapore-companies.md"),
            ],
            problems=[],
        ),
        dict(
            id="level-format-offer",
            title="Level, Format and the Offer",
            summary="Senior-level signals, remote interviews and your questions, offers and Singapore employment basics, and a mock-interview checklist.",
            lessons=[
                dict(id="senior-signals", title="Senior-level signals: scope, stakeholders, risk, hiring and mentoring", file="24-senior-signals.md"),
                dict(id="remote-and-questions", title="Remote and video interviews, and questions to ask", file="25-remote-and-questions.md"),
                dict(id="offers-singapore", title="Offers, negotiation and Singapore employment basics", file="26-offers-singapore.md"),
            ],
            problems=[],
        ),
    ],
)
