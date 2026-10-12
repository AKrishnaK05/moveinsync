# MoveInSync Play Store Rating Recovery Strategy
## Candidate Assignment — Forward Deployed Engineer (Intern to FTE)

---

### Executive Summary

MoveInSync coordinates daily commute logistics for **1.5M+ employees across 430+ enterprise clients**. While the official Google Play Store storefront displays a strong aggregate rating of **4.6★** (anchored by lifetime installations and silent star-only submissions), the recent written review cohort reveals concentrated friction:

- **Official Play Store Storefront Rating**: **4.6★** (benchmark across 100k+ lifetime ratings)
- **Total 2025–2026 Written Reviews Analyzed**: `5,201` (Cohort Mean: **3.75★**)
- **4–5 Star Positive Reviews**: `3,556` (**68.4%** of recent written volume — strong commute baseline)
- **1–2 Star Negative Reviews**: `1,497` (**28.8%** of recent written volume)
- **Developer Reply Rate to Negative Reviews**: **4.5%** (only 68 of 1,497 negative reviews received any response)

Our classification pipeline analyzed **100% of 2025–2026 reviews** using Google's Gemini models under a 15-category domain schema tailored to enterprise commute workflows.

**The Verdict**: MoveInSync's rating problem is **not a generalized dislike of the service** — it is concentrated in high-friction technical and operational failure modes. We focus on three critical engineering areas:
1. **App Reliability (Crashes, Freezes & Web-View Fallback)** — 256 negative reviews (74 community upvotes)
2. **Login & Session Expirations (Auth Friction & OTP Drops)** — 219 negative reviews (44 community upvotes)
3. **Live GPS Tracking & Camera Zoom Reset** — 83 negative reviews (37 community upvotes)

*Note on Category Selection*: While `DRIVER_TRANSPORT_OPERATIONS` (103 reviews) and `BOOKING_SCHEDULING` (86 reviews) have higher raw review volumes, they depend heavily on enterprise transport desk shift policies and driver partner behavior. We prioritized **`TRACKING_MAPS`** because of its high community endorsement (37 upvotes, averaging ~0.45 upvotes/review) and its **immediate, high-feasibility client-side fixability** (a front-end camera bounds bug that mobile engineers can resolve on Day 1 without cross-company policy changes).

Fixing these three engineering pain points addresses **37.3% of all 1–2★ reviews (47.4% excluding vague/non-actionable reviews)**. If all negative reviews across these three categories were successfully remediated toward 4★, it would provide an upper-bound potential lift of **up to ~+0.3 on the evaluated review sample mean** (bringing our analyzed review cohort mean from ~3.75 up to ~4.06, providing an essential buffer to protect MoveInSync's flagship **4.6★** Play Store storefront rating against ongoing version regressions).

---

### Root Cause Analysis: The Negative Review Breakdown

The table below ranks the primary complaint themes among 1–2 star reviews, prioritized by overall user impact (review volume and community thumbs-up endorsements):

| Rank | Category | 1–2★ Reviews | % of Negatives | Thumbs Up | Primary User Pain Point | Severity |
|:---:|:---|:---:|:---:|:---:|:---|:---:|
| 1 | **APP_RELIABILITY** | 256 | 17.1% | 74 | App freezes, launch crashes, web-view fallback post-update | Critical (P0) |
| 2 | **LOGIN_ACCESS** | 219 | 14.6% | 44 | Repeated re-login loops, session drops, OTP delivery failures | Critical (P0) |
| 3 | **DRIVER_TRANSPORT_OPERATIONS** | 103 | 6.9% | 30 | Driver arrival coordination, uncontactable drivers, no-shows | High (P1) |
| 4 | **BOOKING_SCHEDULING** | 86 | 5.7% | 40 | Roster sync delay, cutoff confusion, shift schedule drops | High (P1) |
| 5 | **TRACKING_MAPS** | 83 | 5.5% | 37 | Camera auto-refits to destination, GPS icon freezes on map | High (P1) |
| 6 | **TIMING_ROUTING** | 77 | 5.1% | 16 | Circuitous routes, abrupt pickup time shifts | Medium (P2) |
| 7 | **CONTACT_SUPPORT** | 71 | 4.7% | 27 | Unresponsive transport desk, closed tickets | Medium (P2) |
| 8 | **USABILITY_ACCESSIBILITY** | 68 | 4.5% | 14 | Confusing multi-step trip workflows, unintuitive confirmation dialogs | Medium (P2) |
| 9 | **FEATURE_GAP_OR_REMOVAL** | 57 | 3.8% | 26 | Missing direct driver calling, missing dark mode | Medium (P2) |
| 10 | **FEEDBACK_OR_RATING_FLOW** | 52 | 3.5% | 15 | Aggressive rating popups after delayed trips | Medium (P2) |
| - | *UNCLEAR_INSUFFICIENT_DETAIL* | 321 | 21.4% | 2 | Generic 1-word venting ("worst app", "bad") | Non-actionable |

*(Note: 321 reviews were vague venting with no actionable details; they received only 2 thumbs up in total, demonstrating that users actively rally and upvote specific functional defects).*

---

### Deep Dive: Top 3 Problem Areas & Evidence

#### 1. APP_RELIABILITY: Crashes, Launch Freezes & Web-View UI Fallback
- **The Problem**: When employees open the app to verify trip details, the app frequently hangs or crashes. Crucially, reviews identify a specific recurring defect: **post-update web-view UI fallback**. Following an update, the app intermittently fails to load its native Android interface, instead rendering an embedded web-page view that breaks transactions and live tracking until the employee completely uninstalls and reinstalls the app.
- **Direct User Quotes**:
  - *"The app frequently crashes or hangs while booking cabs, which makes it really frustrating, especially when I’m in a hurry. The GPS tracking is unreliable..."* (1★, 27 upvotes)
  - *"It has been a frustrating experience not only to me but all of my team mates since the last update. I log in and first time it logs in to the app correctly. But after some time it shows up like the web page inside the app and not like the regular UI of app. And we cannot do any transactions properly and no tracking etc can be done. Then we have to reinstall the app and login again to make it work. Please take care of this quickly."* (1★, 10 upvotes)
  - *"whenever i update this app, i am not able to open the app again, I need to uninstall and reinstall again. facing this issue since 3 months"* (1★, 0 upvotes)

#### 2. LOGIN_ACCESS: Repeated Re-Authentication & OTP Delivery Failures
- **The Problem**: Across the 219 login complaints, the dominant systemic issues are **session invalidation** and **unreliable OTP delivery**. Sessions fail to persist across app updates or backgrounding, forcing employees to repeatedly re-authenticate. When attempting to log in, SMS/email OTPs frequently fail to arrive or arrive with no system status messaging, locking users out when they need access to cab numbers or trip details.
- **Direct User Quotes**:
  - *"I might give it 5 star but after the latest update this app has become so stupid. Everytime it looses my login info and then I've to reenter it..."* (1★, 8 upvotes)
  - *"Most frustrating aspect of this app is, when cab is waiting for you and you are in hurry, you will be logged out with no access to cab number/otp..."* (2★, 5 upvotes)
  - *"This app is the worst. Not able to login via phone/email as the OTP is not received. The most disgusting thing is, it won't give any message whether OTP sent or not..."* (1★, 6 upvotes)

#### 3. TRACKING_MAPS: Map Viewport Auto-Reset & GPS Latency
- **The Problem**: While waiting at their pickup location, employees zoom in on the cab icon to inspect which lane or turn the driver is approaching. However, the Google Maps camera logic automatically resets every 30 seconds to fit **both the pickup source and the destination in the viewport**, zooming out so far that it becomes impossible to see how far away the vehicle is. Additionally, users report GPS location markers remaining frozen on the map for extended intervals even though the vehicle is already moving.
- **Direct User Quotes**:
  - *"App has very poor logic of setting zoom level and automatically reset it every 30 seconds. When user is waiting for cab at source why you want to keep the destination also in the view? which makes impossible to see how far the cab is. suggestion to keep one point at a time in focus while boarding pickup point and vehicle and once you start the trip vehicle and destination. also when user zooms in respect his zooming don't reset automatically optionally you can give reset button to reset."* (1★, 10 upvotes)
  - *"The GPS tracking system is often unreliable and sometimes shows the driver at an incorrect location, which can lead to unnecessary delays..."* (1★, 8 upvotes)
  - *"The GPS system of the app needs serious improvement. The cab icon often stays at the same point for over 10 minutes, even though the driver has clearly already moved..."* (1★, 4 upvotes)

---

### The Operational Blind Spot: Developer Response Audit

Play Store reviews represent a public customer support touchpoint. Currently:
- **Only 4.5% of 1–2 star reviews** received a response from MoveInSync (68 out of 1,497).
- Unanswered negative reviews accumulate thumbs-up votes from other frustrated employees, pushing those 1-star reviews to the top of Google Play.
- **Action**: Implementing an automated triage workflow to reply to critical 1–2 star reviews within 4 hours (with deep links to corporate transport helpdesk escalation) can immediately de-escalate public frustration and help convert negative reviews into resolved ratings.

---

### Day-1 Actionable Roadmap (What to Fix & What to Do First)

| Timeline | Initiative | Target Category | Concrete Engineering / Product Action | Target / Expected Impact |
|---|---|---|---|---|
| **Day 1** (Immediate) | **Session Retention & Token Fix** | `LOGIN_ACCESS` | Extend OAuth refresh token validity to 30 days in secure keystore. Stop invalidating local sessions on app backgrounding or minor patch updates. | *Target to validate*: Aim to reduce session dropouts and auth-related exceptions by up to 70% in telemetry |
| **Day 1** (Immediate) | **Map Viewport Bounds Fix** | `TRACKING_MAPS` | Adjust camera logic: focus bounds on pickup pin + cab position prior to boarding (do not include destination until trip starts). Disable automatic 30s camera recentering when manual user zoom is active. | Immediate elimination of the #1 user-reported tracking friction |
| **Day 1** (Immediate) | **Play Store Response SLA** | `SUPPORT` | Set up automated alert webhooks for 1–2★ reviews with quick deep links to corporate transport helpdesk. | 100% reply rate on critical complaints within 4-hour SLA |
| **Week 1–2** | **Native UI Shell Integrity** | `APP_RELIABILITY` | Investigate and eliminate the web-view fallback bug post-update. Set up Sentry crash alerting and local SQLite caching for roster and trip cards. | Target crash-free sessions > 99.5%; eliminates forced app reinstalls |
| **Week 2–3** | **OTP Redundancy Gateway** | `LOGIN_ACCESS` | Add fallback WhatsApp / Email OTP delivery channels and biometric authentication (Fingerprint / FaceID) to unlock active sessions instantly. | Mitigates SMS carrier latency and prevents lockout at cab arrival |
| **Month 1** | **Geofenced Driver Status Validation** | `DRIVER_OPERATIONS` | Explore geofence constraints requiring driver GPS to be within designated proximity before allowing trip status progression (to validate against reported premature boarding disputes). | Hypothesis test: reduction in disputed boarding claims |
| **Month 1** | **Smart In-App Review Prompts** | `FEEDBACK_FLOW` | Never prompt users for a Play Store rating right after a delayed or canceled trip. Trigger Play Store review prompts only after consecutive smooth rides. | Organic capture of positive sentiment to drive the ~+0.3 review mean recovery |

---

### Methodology & Tools Note

*As requested in the assignment ("Alongside it, a short note on how you got there and which tools you used"):*

This analysis was developed using an end-to-end, reproducible data pipeline:
1. **Data Collection (`pipeline/01_collect.py`)**: Used `google-play-scraper` to scrape all 24,314 historical reviews for `com.moveinsync.ets` with pagination and exponential backoff retry.
2. **Exploratory Data Analysis (`pipeline/02_explore.py`)**: Used `pandas` and `matplotlib` to analyze long-term trends from 2014 to 2026, generating year-over-year rating distributions and data quality summaries.
3. **Filtering (`pipeline/03_filter.py`)**: Filtered down to the recent evaluation window (`2025-01-01` to today), isolating a clean cohort of 5,201 reviews.
4. **AI Multi-Label Classification (`pipeline/04_label.py` & `05_classify.py`)**: Batched all 5,201 reviews through Google's Gemini models (`gemini-2.5-flash`) under a strict 15-category JSON Schema (`config/classification_schema.json`), extracting exact substring evidence without hallucination.
5. **Analytics & Backlog Aggregation (`pipeline/06_report.py`)**: Merged classified labels with review metadata, computed developer reply rates, and exported structured analytics tables.
6. **Interactive Dashboard (`dashboard.py`)**: Built a Streamlit telemetry dashboard styled with MoveInSync's mobile app theme to let engineering leads explore ratings, filter by version/date, and inspect customer evidence in real time.
