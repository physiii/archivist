# Focus — Week 5: 2026-04-13 through 2026-04-17

Andy Payne, AI Director — Versant Cognitive Engineering
Reports to: Sharif | Direct reports: Garrett, Tanmay | Leadership trio: Sharif, Andy, Victor

> **Entering Week 5 with momentum from Week 4:** Quality branch merged (regression caught
> and fixed Apr 9). 20 E2E scenarios running via Nova agent evaluator. 3-step interview
> process agreed. Jonathan onsite → week of Apr 27 in LA. Prism repo set up by Tanmay with
> gap analysis ready to review. Two new forcing functions this week: **Jason beta-customer
> call Mon Apr 13** (Sharif introducing Andy) and **EasyLynx real data arriving Tue Apr 14**.
>
> **Performance goals deadline this week:** Versant's new performance management system
> opens **Mon Apr 13**. Employee draft due **Fri Apr 17** (3-5 SMART goals in MyVersant).
> Manager finalization (Sharif) by May 1.
>
> **Sharif's strategic info asymmetry continues:** Agentic coding vision NOT shared with
> broader team. Direct reports (Garrett, Tanmay, Jim, Zach, Sherry) are focused on project
> work; the leadership trio (Sharif + Andy + Victor) hold the broader picture.

---

## Table of Contents

- [Priority Table](#this-week--priority-order)
- [Critical Path](#critical-path)
- [Calendar](#calendar)
- [Blockers](#blockers)
- [Details](#details)
  - [1. Jason Beta Customer Call (Mon Apr 13)](#1-jason-beta-customer-call-mon-apr-13)
  - [2. EasyLynx Real Data (Tue Apr 14)](#2-easylynx-real-data-tue-apr-14)
  - [3. Caddy Eval Pipeline (CI A/B + Production Sampling + Pre-flight)](#3-caddy-eval-pipeline-ci-ab--production-sampling--pre-flight)
  - [4. Prism Dig (Week 1)](#4-prism-dig-week-1-of-12-week-budget)
  - [5. Performance Goals (Due Apr 17)](#5-performance-goals-due-apr-17)
  - [6. Jonathan Onsite Logistics](#6-jonathan-onsite-logistics-apr-27-week)
  - [7. Interview Process + Packet](#7-interview-process--packet)
  - [8. Recurring 1:1 Setup (OVERDUE)](#8-recurring-11-setup-tanmay--garrett--overdue)
  - [9. Production Bugs](#9-production-bugs-p1)
  - [10. Internship Program](#10-internship-program)
- [Direct Reports](#direct-reports)
- [Product Ideas Pipeline](#product-ideas-pipeline)
- [Accomplished (Weeks 1-4)](#accomplished-weeks-14)
- [Open Questions](#open-questions)

---

## This Week — Priority Order

| # | What | Owner | Status | Next Action |
|---|------|-------|--------|-------------|
| 1 | **Jason beta-customer call (Mon Apr 13)** | Andy + Sharif | Sharif will introduce Andy. Jason is the Caddy beta-customer foothold; leadership (Steve → Will) are explicitly excited about landing real call data even at 1-2 calls/day. | Prep talking points; confirm time with Sharif; Sharif to do warm intro |
| 2 | **EasyLynx real data (Tue Apr 14)** | Andy + Jim + Sarah | Sarah confirmed on track. Real data is the final piece for the Caddy happy path (no credit card, no prepayment). Session-cache design for double-booking risk must be concrete before data arrives. | Confirm Sarah's Apr 14 delivery scope; verify session-cache design with Jim; smoke plan for live data |
| 3 | **Caddy CI A/B GitHub Action** | Andy (+ Garrett started) | Garrett started building on GitHub Actions Apr 9. Replaces Jim's existing E2E test repo (Jim "totally fine"). | Finish the Action: PR trigger, spin both branches, S3 reports, summary back on PR |
| 4 | **Caddy production-call sampling judge** | Andy | Sharif's explicit ask (doubled down Apr 8). LLM-as-judge on real golf-course call transcripts. | Define scope, draft judge prompt ("was the request fulfilled?"), wire to S3 |
| 5 | **Prism dig (week 1 of 1-2 week budget)** | Andy + Tanmay | Tanmay set up repo + gap analysis Apr 9. Gap analysis compares PRISM vs current vendor vs industry standard. | Review Tanmay's gap analysis; start reading code; aim to be ready for Dan Lee intro in ~1-2 weeks |
| 6 | **2026 performance goals draft** | Andy | System opens Apr 13. Draft due **Apr 17** (3-5 SMART goals from business unit goal library). Finalization by May 1 with Sharif. | Log into MyVersant (rocket-ship icon); pick business unit goals; customize with SMART criteria |
| 7 | **Jonathan onsite logistics** | Andy + Sarah/HR | Apr 9 decision: week of Apr 27 in LA. Sharif will be there. | Contact Sarah/HR; confirm Jonathan's availability Apr 27 week; nail down format (presentation → Q&A → coding per new 3-step process) |
| 8 | **Single-container ECS quality test (with Garrett)** | Andy + Garrett | Redirected Apr 8: simple single-container dev sanity check, NOT multi-task AWS wiring. Production testing is Sharif + Garrett's separate design. | Unblock Garrett; keep it simple; confirm the ECS container runs what we run locally |
| 9 | **Interview process Confluence doc** | Victor (first pass) → Andy (review) | Agreed at Apr 9 leadership huddle. Victor writing first pass. Andy to review and refine. | Check if Victor sent link; review draft; add R3 format details (hands-on Claude + follow-up questions not in repo) |
| 10 | **Recurring 1:1s with Tanmay + Garrett** | Andy | **OVERDUE from Week 4.** Sharif's Apr 8 push: "Don't hesitate there." Not set up yet. | Set up this week. Even if there's nothing to talk about, build the rhythm. |
| 11 | **Pre-flight checks for caddy repos** | Andy | Tanmay and Andy worked on this Apr 7 PM. Green/red status checks on AWS, Keystone, EasyLinks, Mongo, env vars before eval runs. | Finish script; add to eval test repo; add equivalent to caddy repo itself |
| 13 | **Interview packet R3 format design** | Andy | 3-step process agreed Apr 9. R3 = in-person hands-on with Claude + follow-up questions not in the repo. | Design the R3 exercise + follow-up question set; update PACKET.md |
| 14 | **Production bugs (P1)** | Andy + Jim | P0s closed (verification bypass, cancellation contradiction fixed by quality branch merge). P1s remain. | Signal tag bypass, course-identity leakage, price inconsistency, EasyLynx session-cache design |
| 15 | **Jim: tool-call middleware + EasyLinks new endpoint** | Jim | Tool-call middleware: enforcement in orchestrator's tool-call layer. EasyLinks new endpoint: "very fragile" per Jim Apr 9. | Follow up; confirm middleware design; validate whether new EasyLinks endpoint is stable enough to use |
| 16 | **Tanmay: toxicity feedback API + Terraform IAM PRs** | Tanmay | Toxicity feedback: false positive/negative learning loop. Terraform IAM PRs open and waiting for DevOps review. | Check on DevOps approval; follow up on feedback API scope |
| 17 | **Zach: OAuth/WAX + At Home completion** | Zach | OAuth: MCP endpoint opening OAuth window to Fandango login (2-year-outstanding unification ask). At Home: custom user lists + points (last piece of auth epic). Blocked on promo codes endpoint. | Confirm OAuth demo progress; resolve promo codes test token question |
| 18 | **Twilio USA2P SMS confirmation (Sherry)** | Sherry + Andy | Blocked on USA2P compliance flow. Sherry to send Andy the docs. | Work through compliance flow with Sherry once docs arrive |

---

## Critical Path

1. **Jason call is the week's forcing function for Caddy.** Sharif explicitly said he'd
   introduce Andy to Jason as a warm handoff. Jason represents real production call data
   at 1-2 calls/day, which feeds the production-call sampling judge and production testing
   design. Success here changes the quality conversation from synthetic to real.
2. **EasyLynx Apr 14 data is the last piece for the Caddy happy path.** Sarah confirmed
   she's on track. Session-cache design for double-booking risk must be concrete before
   data arrives so there's a plan if the live data surfaces edge cases.
3. **Prism week 1 starts now.** Andy committed a 1-2 week budget Apr 8. Tanmay has the
   repo set up and gap analysis ready. If this slips another week, the Dan Lee intro
   (which unlocks the product roadmap) gets pushed past mid-April.
4. **Performance goals draft by Apr 17 is non-negotiable.** System opens Apr 13.
   Andy needs 3-5 SMART goals from the Cog Eng / Digital business unit goal library.
   Two-week collaboration window with Sharif follows immediately.
5. **1:1 cadence with Tanmay + Garrett is overdue by a full week.** Sharif said this
   in the Apr 8 1:1. Build the rhythm now; it gets harder to start the longer it's deferred.
6. **Jonathan onsite target is Apr 27 week.** Sarah/HR contact needs to happen now to
   confirm Jonathan's availability and avoid a scheduling crunch.

---

## Calendar

| Day | Time | Event |
|-----|------|-------|
| **Mon Apr 13** | AM | **Performance system opens** — MyVersant, rocket-ship icon |
| **Mon Apr 13** | TBD | **Jason call (Caddy beta customer)** — Andy + Sharif. Sharif to introduce. Beta foothold. |
| **Tue Apr 14** | — | **EasyLynx real data arrives** — Sarah on track. Final piece for Caddy happy path. |
| **Thu Apr 16** | AM | Team standup |
| **Fri Apr 17** | EOD | **Performance goals draft due** — 3-5 SMART goals in MyVersant system |
| **Week of Apr 27** | — | **Jonathan onsite in LA** — Andy to confirm with Sarah/HR; Sharif will be in LA |
| Late April | — | AI summit Orlando — remote participation for Andy + Victor (Zoom) |
| **May 1** | EOD | Performance goals finalization deadline (manager/Sharif approves) |

---

## Blockers

| Blocker | Impact | Who Can Unblock |
|---------|--------|-----------------|
| Promo codes endpoint test creds | Blocks Zach's At Home promo-code work | Fandango team (int tokens) |
| Twilio USA2P spam-control compliance | Blocks Sherry's SMS confirmation | Sherry + Andy |
| Datadog not connected to CogEng | Tanmay toxicity + Victor reviews monitoring | Unknown owner (needs identification) |
| Easy Links new search endpoint stability | Jim warns "very fragile" Apr 9; significant MCP changes needed if it works | Easy Links vendor |
| Nova Sonic 2 system prompt immutable after stream start | Per-state prompts must use alternative injection mechanism | Team design decision |
| Okta/GitHub auth (Andy) | Local Bedrock testing | Victor (Okta ticket) |
| Okta/ARTI access (Tanmay) | Minor code changes | IT / access management |
| DevOps approvals | Terraform IAM PRs waiting (Tanmay) | Dylan/Tom |
| Keystone budget ($2,531/$500) | Andy over budget | Fandango platform team |
| JIRA API token | Blocks MCP integration | Nate Longstreet |

---

## Details

### 1. Jason Beta Customer Call (Mon Apr 13)

Caddy beta-customer foothold. Sharif's Apr 7 standup: *"You're probably going to have to
get a lot closer to him."* Sharif will make the introduction. Jason represents the path to
real production call data (1-2 calls/day). Leadership (Steve → Will) are explicitly excited
about landing even a single beta customer.

**Stakes:** Even 1-2 real calls/day feeds the production-call sampling judge (Sharif's
drum-beat). Real data validates what synthetic E2E tests cannot — actual caller behavior,
edge cases in booking flow, signal quality from real golf courses.

**Prep checklist:**
- [ ] Confirm time with Sharif; is Sharif joining or just introducing async?
- [ ] Review Caddy's current quality state (post-merge: ~85%+ E2E pass rate, 20 scenarios)
- [ ] Prepare 2-3 talking points: what Caddy does, current state, what beta deployment
      would look like for Jason's courses
- [ ] Know the gaps: which P1 bugs are still open? What's the honest timeline for 90%+?
- [ ] Know the production sampling plan: if Jason asks "how do you know it's working?"

---

### 2. EasyLynx Real Data (Tue Apr 14)

Sarah confirmed "on track" at the Apr 7 standup. EasyLynx real data = the last piece for
the Caddy happy path (no credit card, no prepayment, real-time course availability).

**Key concern: double-booking / session-cache design.** EasyLynx has a known sync delay —
a caller can re-book before the lookup sync catches up. Before Apr 14, Andy + Jim need a
concrete design for session-cache to prevent this in the production path.

**This week's checklist:**
- [ ] Confirm Sarah's Apr 14 delivery scope: real-time search, inventory, no-prepay path —
      what exactly is included?
- [ ] Finalize session-cache design with Jim before data arrives
- [ ] Prepare smoke plan: first live-data test run, what to watch for, who to loop in
- [ ] Coordinate with Sherry: does SMS confirmation depend on the EasyLynx integration?

---

### 3. Caddy Eval Pipeline (CI A/B + Production Sampling + Pre-flight)

**Sharif's drum-beat.** These three layers together form the quality measurement system
Caddy needs before it can be trusted at scale.

**Apr 9 status updates:**
- Quality branch merged to main — regression caught (85%→35%), fixed same day.
- **Garrett building CI A/B on GitHub Actions** — the pipeline is materializing.
- **Jim building tool-call middleware** — enforcement in orchestrator layer, not just prompts.
- EasyLinks: new search endpoint but "very fragile" — don't depend on it yet.

**Layer 1 — CI A/B GitHub Action (primary focus):**
- PR-triggered GitHub Action: spin two containers (main + branch under test)
- Pull reports from S3; run A/B comparison; post summary back on PR
- **Replaces Jim's existing E2E test repo** — confirmed by Jim, "totally fine"
- Jim also uploads his local manual-test transcripts to the same S3 path

**Layer 2 — Production-call sampling judge:**
- LLM-as-judge on real golf-course call transcripts
- Judge prompt: *"was the user's request fulfilled?"*
- Feeds back as scenarios for the synthetic test set
- Eventually expose as a quality metric to golf courses themselves
- Jason call (Apr 13) is the path to getting real transcripts

**Layer 3 — Pre-flight checks:**
- Green/red status on AWS, Keystone, EasyLinks, Mongo, env vars before eval runs
- Add to both the **eval test repo** (`index.t`) and the **caddy repo** itself
- Andy + Tanmay worked the design Apr 7 PM; needs implementation + merge

**This week's checklist:**
- [ ] Finish Caddy CI A/B GitHub Action (Garrett started on GHA Apr 9; coordinate)
- [ ] Define production-call sampler scope (sources, sample rate, retention)
- [ ] Draft judge prompt and wire to S3
- [ ] Push pre-flight check script to eval test repo; merge to main
- [ ] Add equivalent pre-flight checks to caddy repo
- [ ] Sync with Jim on S3 transcript format (branch + transcript + metadata)
- [ ] Backfill JIRA ticket for caddy quality-fixes work (no ticket exists)

---

### 4. Prism Dig (Week 1 of 1-2 Week Budget)

Andy committed a **1-2 week budget** in the Apr 8 Sharif 1:1. Tanmay set up the Prism
repo and produced a **gap analysis** (PRISM vs current vendor vs industry standard) on
Apr 9. This is the first concrete Prism artifact. Week 5 is week 1 of the dig.

**Why this week is the line:** Dan Lee (Prism product lead) is in active contract
negotiation with Vion Labs (competitor). Sharif will intro Andy + Tanmay to Dan Lee once
they're comfortable with the codebase — but that intro unlocks the product roadmap, and
every week of delay costs negotiation leverage. Sharif is also arranging Vion Labs
competitor access for Andy + Tanmay.

**Spike plan (10-15h total over 1-2 weeks):**
1. Review Tanmay's gap analysis — understand where PRISM stands relative to the baseline
2. Get Prism codebase running on local machine (Big Buck Bunny as test video)
3. Read the code: diarization pipeline, face recognition pipeline, temporal correlation
4. Write a temporal correlation prototype: SPEAKER_XX → actor name via majority vote
5. Evaluate accuracy against ground truth ("You've Got Mail" was the original target)
6. Document findings: accuracy numbers + integration path

**This week's checklist:**
- [ ] Review Tanmay's gap analysis (PRISM vs current vendor vs industry standard)
- [ ] Get Big Buck Bunny or equivalent test video; run PRISM on it
- [ ] Start reading the codebase — understand the diarization + face recognition pipeline
- [ ] Pair session with Tanmay — coordinate reading strategy
- [ ] Don't wait for Dan Lee intro — that comes after comfort with the codebase

---

### 5. Performance Goals (Due Apr 17)

**Versant 2026 Performance Framework** — new process introduced at company-wide training
Apr 10 (Sam, Christina Noval, Destiny Gregory, Elisa Grossberg, Lincoln Palmer from the
Talent team). System opens **Apr 13**, draft due **Apr 17**, finalized with Sharif by
**May 1**.

**Company's five 2026 goals (from CEO Mark's March Orlando town hall):**
1. Establish a resilient stand-alone public company foundation
2. Strengthen competitive position in premium content + expand digital market share
3. Advance growth initiatives and new business models to reach broader audiences
4. Modernize operations to drive cost efficiency and organizational agility
5. Build a vibrant, distinct corporate culture (trust, transparency, teamwork)

**Framework:** WHAT (results/outcomes) + HOW (behaviors modeling company values) = WHY
IT MATTERS (evaluation, comp, recognition, growth). Individual goals ladder up through
business unit goals (Cog Eng is under the Digital division).

**SMART criteria:** Specific, Measurable, Actionable, Relevant, Time-bound.
**Target:** 3-5 individual goals. Each ties to a pre-populated business unit goal from the
system library.

**How to set goals:** MyVersant portal → rocket-ship icon in left toolbar → performance
system → select 3-5 business unit goals → customize with SMART framework → submit to
Sharif by Apr 17.

**Suggested goal areas for Andy (Cog Eng AI Director):**
- Voice AI call-center quality (E2E pass rate, production-call sampling, beta customers)
- PRISM actor labeling platform (capability milestone + Dan Lee integration)
- Hiring + team growth (3-step interview process, junior hire, internship program)
- Agent team strategy (agentic coding platform design, cost-shift narrative)
- Engineering velocity + quality culture (CI A/B, production testing design, 1:1 cadence)

**This week's checklist:**
- [ ] Log into MyVersant (rocket-ship icon in left toolbar) on Apr 13
- [ ] Review Cog Eng / Digital business unit goal library
- [ ] Draft 3-5 SMART goals by Apr 17 EOD
- [ ] Consult Sharif during collaboration window Apr 17–May 1

---

### 6. Jonathan Onsite Logistics (Apr 27 Week)

**Decision made Apr 9 leadership huddle:** In-person in LA, week of Apr 27. Sharif will
be in LA that week. The 3-step interview process was also agreed:
1. R1 — Remote screen + basic tech (done for Jonathan)
2. R2 — Remote AI coding on unfamiliar project (done for Jonathan)
3. R3 — In-person hands-on with Claude + follow-up questions NOT in the repo

**R3 design note from Sharif (Apr 9):** The core exercise might be solvable in 15 minutes,
so *"we need to have follow-up questions that are not anywhere in the repo."* No more 6
people in the room for 3 hours — break it up: presentation/intro from candidate → Q&A →
coding session.

**This week's checklist:**
- [ ] Contact Sarah (HR) — confirm Jonathan's availability for week of Apr 27 in LA
- [ ] Confirm Sharif's LA dates for that week
- [ ] Design the R3 format: intro/presentation → Q&A → hands-on coding with Claude
- [ ] Draft R3 follow-up questions that go beyond what's in the CollectiveFS repo
- [ ] Update hiring requisition: "Senior" → "junior" (HR artifact, Sharif's Apr 8 call)
- [ ] Don't pre-share the codebase for R3

---

### 7. Interview Process + Packet

**Apr 9 leadership huddle agreement:** Victor to write first pass of the interview process
doc in Confluence. Andy to review and refine. The 3-step process is agreed; the details
(R3 format, scorecard, evaluation criteria) still need to be written down.

**Packet revision outstanding items:**
- Apply Apr 6 R2 lessons: hint discipline, no codebase pre-share, quantitative-quality probe
- Add OS-diversity probe (Jonathan's Windows-only setup exposed a gap)
- Update PACKET.md with the 3-step process structure
- Plant a clear bug in the interview repo for the fix-a-bug phase
- Create anomaly data in reports/ directory for the anomaly detection phase
- Confirm repo runs on Windows via Docker
- Prepare scorecards for R1, R2, and R3 phases

**This week's checklist:**
- [ ] Check if Victor sent the Confluence link for the process doc
- [ ] Review Victor's draft; add R3 format and follow-up question guidelines
- [ ] Final pass on `PACKET.md`, `QUESTIONS.md`, and `AGENDA.md`
- [ ] Update the scorecard template with Apr 6 lessons + R3 format

---

### 8. Recurring 1:1 Setup (Tanmay + Garrett) — OVERDUE

**Sharif's Apr 8 push (verbatim):** *"Set up one-on-ones with them. Start that managerial
stuff with them and don't hesitate there. Even if there's nothing to talk about, it gives
you both a place to build that rhythm."*

This was supposed to happen in Week 4. It didn't. Week 5 is non-negotiable.

**This week's checklist:**
- [ ] Schedule recurring 1:1 with Tanmay (weekly or biweekly — set the cadence)
- [ ] Schedule recurring 1:1 with Garrett (weekly or biweekly)
- [ ] First 1:1s ideally before end of week

---

### 9. Production Bugs (P1)

P0s are closed — verification bypass, cancellation contradiction, signal tag bypass all
fixed by the quality branch merge. Remaining P1s:

| Bug | P | Description |
|-----|---|-------------|
| EasyLynx sync delay / double-booking | P1 | Session-cache design must be concrete before Apr 14 data arrives |
| Course-identity leakage | P1 | Wrong course booking surfaced |
| Price inconsistency | P1 | $30 x 3 = $135 (no monetary validation) |
| Bella verbosity | P1 | Voice agent still too wordy for production confidence |
| Replayed speech | P1 | Agent repeats messages (may be resolved by state machine merge) |
| Duplicate tool execution | P1 | idempotency_key per-call, not per-intent |

**Week 5 exit bar:** EasyLynx session-cache design finalized; 0 new P0s; Bella verbosity
under 60 words average on voice flows.

---

### 10. Internship Program

Sharif heading the reintroduced Versant internship program. Two interns coming to Cog Eng.
First referral candidate declined. Both slots still open — awaiting next candidates from
Sharif. Sharif will pull Andy + team into the interview loop when candidates surface.

---

## Direct Reports

> **Recurring 1:1s still not set up** — this is the most overdue item entering Week 5.
> Sharif said this on Apr 8 and it slipped through all of Week 4. Set them up this week.

### Garrett — CI A/B + ECS + Monitor + Production

**Apr 9 update:** Started building CI A/B on GitHub Actions. The shared eval pipeline is
materializing. Garrett is building the "scenario-for-every-complaint" philosophy into the
test harness.

**This week:**
- Finish CI A/B GitHub Action (coordinate with Andy)
- Single-container ECS quality test (simple, not multi-task)
- Scenario-for-every-complaint: grow the test set from 20 scenarios
- Production testing design (separate surface area — Sharif will talk to Garrett about this)

### Jim — State Machine + Middleware + EasyLinks + Beta

**Apr 9 update:** Building tool-call middleware (enforcement in orchestrator layer). New
EasyLinks search endpoint deployed but "very fragile." State machine merged to main.

**This week:**
- Tool-call middleware: confirm design and timeline
- EasyLinks new endpoint: validate stability before building on it
- Upload local manual-test transcripts to S3 (align format with Andy)
- Jason call followup: Jim needs to know what's expected for beta deployment

### Tanmay — Toxicity + Prism + JIRA + IAM

**Apr 9 update:** Set up PRISM repo + gap analysis. Building toxicity feedback API.
Terraform Teams IAM PRs open and waiting. Okta/ARTI access lost.

**This week:**
- Pair with Andy on Prism gap analysis review + code reading
- Toxicity feedback API: confirm scope (false positive/negative learning loop)
- Terraform IAM PRs: follow up on DevOps approval (Garrett offered to request review)
- Okta/ARTI access restoration: escalate if blocked
- Multimodal moderation (images/video) with Harrison + Victor: follow up on scope

---

## Product Ideas Pipeline

| Idea | Source | Status |
|------|--------|--------|
| Content rating conversion (R → PG) | Andy + Sharif + Victor | Scope after Prism spike |
| Nova Sonic workflow "attractor" | Andy | Orchestrator sets path attractiveness params |
| Mermaid charts with perf data | Andy | Enrich state machine viz with timing |
| OpenClaw self-repair for call center | Andy + Garrett | Evaluate for dev-line integration |
| Vulnerability/penetration testing | Andy | Add adversarial scenarios to E2E |
| Classical fast paths | Andy | Encoding models for deterministic routes |
| Agent-to-agent architecture | Andy | E2E pattern demonstrates; formalize |
| Production-call quality metric for golf courses | Andy + Sharif | Expose sampling judge to courses as quality signal |

---

## Accomplished (Weeks 1-4)

**Call center quality:** 46-step audit, state machine, voice guardrails, JWT propagation,
MCP hardening, 20+ E2E scenarios. Quality branch merged; regression caught and fixed Apr 9.
10pp improvement (62% → 72%), quality branch now at 85%+.

**Infrastructure:** Keystone auth investigation + fix, Docker local stack, 8-PR deployment
strategy, dual-account Bedrock, AB testing infra (two containers per PR, GitHub Actions, S3).

**Hiring:** CollectiveFS repo-based interview (Andy + Garrett) replacing HackerRank.
Garrett's 5-phase restructure. Fraud incidents identified (Jay, George). Jonathan R2 done.
3-step interview process agreed with Sharif + Victor.

**Documentation:** 130K+ word journal, architecture docs, quality audit, 16 research
appendices, candidate notes, interview packet.

**Prism:** Tanmay set up PRISM repo + gap analysis (PRISM vs current vendor vs industry
standard). Prism dig begins Week 5.

---

## Open Questions

- **What is Andy's business unit goal library in MyVersant?** Cog Eng sits under the Digital
  division — which business unit goal library should Andy pull from? (New — Apr 10)
- **How does the $30K token spend narrative land with Steve in the post-Jason-call framing?**
  One beta customer changes the story from "we're spending" to "we're getting real data."
- **Why is Sharif NOT sharing his agentic vision with the broader team?** When does this
  change? What's the trigger for broadening the circle?
- **What is the R3 in-person format?** Hands-on with Claude + follow-up questions not in
  the repo — but the specific exercises and evaluation criteria are still undefined.
- **What is Haven (Jason Rojas) and how does it relate to Cog Eng's secrets management?**
  And what is Morning (Adam Kane) and how does it relate to deployment?
- **Does Andy adopt the 4-tens schedule?** Sharif revealed Mon-Thu 10-12hr days, Fri
  optional / side-project. Andy hasn't formally adopted this rhythm.
- **When does Andy get walked through the Versant career matrix?** Sharif deferred to
  next 1:1 — deferred again in Week 4. When does this actually happen?
- **Who are the Cog Eng interns?** Sharif heading the program; first referral candidate
  declined. Both slots open — awaiting next candidates from Sharif.
- Future-candidate process: codebase ahead of time, during, or with explicit reading time?
- Should Linux/Mac be a prerequisite or is Docker-on-Windows acceptable?
- What's in Steve's "small ideas" call center feedback?
- Is the April 14 EasyLynx data scope (real-time search + inventory + no-prepay) firm?
- Who owns call center after GolfNow/G1 handoff?
- **Should the team write down the "per-project Keystone service token" rule as policy?**
- **How do we structurally compare CI A/B eval results vs. production-call sampling judge
  results?** They measure different things but both feed the same "are we getting better"
  question.
- **Does Claude really under-attend to messages in the middle of a queued sequence?** Andy
  switched to Codex on personal machine — worth filing feedback if the pattern holds.
- What is the Bionlabs renewal / decision deadline, and what accuracy threshold would replace it?
- How many UIs should consolidate? (Viz, Golf, Sharif's, Jim's harness)
- Who owns the Datadog → CogEng connection?
- Nova Sonic 2 system prompt can't change mid-stream — what is the right per-state prompt
  strategy long-term?
- What is Cloud Center Stage's relationship to Cog Eng's work — complementary, competing,
  or future integration target?
- Benefits setup for mom/Jonas — status?
