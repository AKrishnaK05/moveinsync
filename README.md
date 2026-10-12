# MoveInSync Play Store Review Analysis

An end-to-end engineering pipeline for scraping, exploring, filtering, AI-classifying, and synthesizing Google Play Store reviews for the MoveInSync employee transport app (`com.moveinsync.ets`).

> **Primary Submission Deliverable:**  
> The executive analysis, root-cause diagnosis, and prioritized Day-1 engineering roadmap authored after analyzing the data can be accessed directly in **[RECOMMENDATIONS.md](RECOMMENDATIONS.md)**.

---

## Project Structure

```
moveinsync/
├── config/
│   ├── classification_schema.json   # JSON Schema for Gemini output validation
│   └── classification_prompt.txt    # Zero-shot multi-label domain classification prompt
├── pipeline/
│   ├── 01_collect.py                # Scrape all reviews from Google Play Store
│   ├── 02_explore.py                # Exploratory Data Analysis (EDA) across all years
│   ├── 03_filter.py                 # Filter scraped reviews to target evaluation window
│   ├── 04_label.py                  # Orchestrate resumable Gemini batch classification
│   ├── 05_classify.py               # Worker classifier called per-batch by 04_label.py
│   └── 06_report.py                 # Aggregate root causes & export analytics CSV tables
├── data/
│   ├── raw/                         # 24,314 historical reviews (2014–2026)
│   ├── processed/                   # 5,201 reviews filtered to 2025–2026 window
│   └── labeled/                     # 5,201 classified reviews in structured JSONL
├── outputs/
│   ├── exploration/                 # Trend charts (.png) and EDA summary tables (.csv)
│   └── reports/                     # Quantitative issue rankings and response audits (.csv)
├── dashboard.py                     # Interactive Streamlit intelligence dashboard
├── RECOMMENDATIONS.md               # Primary candidate recommendations deliverable
├── requirements.txt                 # Python dependencies
└── README.md                        # Documentation & pipeline runner guide
```

---

## Quickstart & Installation

### 1. Clone & Install Dependencies

Ensure Python 3.8+ is installed:

```bash
pip install -r requirements.txt
```

### 2. Launch the Interactive Dashboard

Explore the ratings data, pain points, and strategic action plan interactively:

```bash
streamlit run dashboard.py
```

### 3. Run the Analytics Aggregator (Offline)

Computes quantitative rankings, developer response audits, and priority matrices across the 5,201 classified reviews:

```bash
python pipeline/06_report.py
```
*(Writes summary tables to `outputs/reports/` for consumption by the dashboard and candidate analysis).*

---

### 4. (Optional) Configure Gemini API Key for Batch Labeling

Only required if re-running AI batch classification on new raw reviews (`04_label.py`):

- **PowerShell (Windows)**:
  ```powershell
  $env:GEMINI_API_KEY="your-api-key-here"
  ```
- **Command Prompt (Windows)**:
  ```cmd
  set GEMINI_API_KEY=your-api-key-here
  ```
- **Bash / Linux / macOS**:
  ```bash
  export GEMINI_API_KEY="your-api-key-here"
  ```

---

## Interactive Analytics Dashboard (Streamlit)

To answer leadership's recurring question — *"How are our Play Store ratings?"* — with dynamic exploration, interactive filtering, and drill-downs:

```bash
streamlit run dashboard.py
```

The dashboard includes 4 specialized tabs:
1. **Overview & Trends**: Star rating distribution, monthly rolling average rating, and high-level executive takeaways.
2. **Root Cause Analysis**: Pain point ranking for 1–2★ reviews across 15 domain categories, and cross-tabulation of complaint frequency across app versions.
3. **Evidence Explorer**: Interactive data table, keyword search (`crash`, `otp`, `driver`, `update`), sample review cards with exact verified quotes, and CSV export.
4. **Action Plan Matrix**: The candidate's prioritized Day-1 engineering roadmap and direct links to the full analytical deliverable.

---

### Full Step-by-Step Pipeline Execution

#### Step 1 — Collect reviews from Play Store
Scrapes all available reviews from the Play Store with pagination, polite rate limits, and exponential backoff:

```bash
python pipeline/01_collect.py
# or with custom app URL / package ID:
python pipeline/01_collect.py com.moveinsync.ets data/raw/reviews_com.moveinsync.ets.csv
```
*Output: `data/raw/reviews_com.moveinsync.ets.csv`*

---

#### Step 2 — Exploratory Data Analysis (All Years)
Runs on the complete raw dataset across all years (2014–2026) to generate long-term trend lines and data quality summaries:

```bash
python pipeline/02_explore.py
# or specify explicit paths:
python pipeline/02_explore.py data/raw/reviews_com.moveinsync.ets.csv --outdir outputs/exploration
```
*Outputs in `outputs/exploration/`:*
- `yearly_summary.csv` & `monthly_summary.csv`
- `rating_distribution_by_period.csv`
- `top_100_app_versions.csv`
- `negative_share_by_year.png` (discrete yearly bar chart)
- `recent_monthly_trend.png` (dual-axis volume vs. negative-share trend)

---

#### Step 3 — Filter to Evaluation Date Range
Narrows the dataset to the recent operating window (2025–today) for active classification:

```bash
python pipeline/03_filter.py
# or with custom start date:
python pipeline/03_filter.py data/raw/reviews_com.moveinsync.ets.csv data/processed/moveinsync_reviews_2025_2026.csv --start 2025-01-01
```
*Output: `data/processed/moveinsync_reviews_2025_2026.csv`*

---

#### Step 4 — Multi-Label Classification with Gemini
Batches reviews through Gemini using schema constraints, confidence scoring, exact-match evidence verification, and atomic checkpointing:

```bash
python pipeline/04_label.py
# or with custom input/output:
python pipeline/04_label.py data/processed/moveinsync_reviews_2025_2026.csv data/labeled/moveinsync_reviews_2025_2026_labels.jsonl
```
- **Resumable**: If interrupted, re-running automatically detects completed batches and resumes from the last checkpoint.
- **Worker**: Calls `pipeline/05_classify.py` internally per batch.
*Output: `data/labeled/moveinsync_reviews_2025_2026_labels.jsonl`*

---

#### Step 5 — Aggregate Analytics & Root Cause Backlog
Merges classified labels with review metadata, calculates negative friction rankings, audits developer response rates, and generates analytical CSV tables:

```bash
python pipeline/06_report.py
```
*Outputs in `outputs/reports/`:*
- `ranked_negative_issues.csv` (15 categories ranked by negative volume & upvotes)
- `action_plan_priority_matrix.csv` (prioritized engineering backlog by impact tier)
- `developer_response_audit.csv` (reply rate analysis across 1-5 star cohorts)
- `version_negative_trends.csv` (volume of negative reports across app versions)
- `issue_type_breakdown.csv` (breakdown by BUG, USABILITY, FEATURE_REQUEST, etc.)

*(Note: The strategic deliverable and executive roadmap authored from this analysis is documented in **[RECOMMENDATIONS.md](RECOMMENDATIONS.md)**).*

---

## Environment Configuration

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(required for AI)* | Google AI Studio API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Primary Gemini model |
| `GEMINI_FALLBACK_MODELS` | `gemini-1.5-flash` | Comma-separated fallback models |
| `GEMINI_BATCH_SIZE` | `50` | Reviews per classification batch |

---

## Domain Taxonomy & Labels

The classification engine maps employee commute reviews against 15 domain-specific categories:

| Label | Scope & Definition |
|---|---|
| `APP_RELIABILITY` | App crashes, freezes, blank white screens, timeouts, slow performance |
| `LOGIN_ACCESS` | Session expirations, auto-logouts, OTP delivery failures, credentials loops |
| `TRACKING_MAPS` | Vehicle GPS location lag, camera zoom resetting, inaccurate map coordinates |
| `BOOKING_SCHEDULING` | Shift roster sync delays, booking cutoff errors, sudden ride cancellations |
| `TIMING_ROUTING` | Circuitous detours, erratic ETAs, abrupt pickup time changes |
| `DRIVER_TRANSPORT_OPERATIONS` | Premature "Boarded" status, driver no-shows, missed pickups, driver conduct |
| `CONTACT_SUPPORT` | Unresponsive transport desk, tickets closed without resolution, emergency SOS |
| `NOTIFICATIONS_PERMISSIONS` | Intrusive update prompts, missed ride alerts, push permission loops |
| `USABILITY_ACCESSIBILITY` | Confusing UI hierarchies, seatbelt popups blocking boarding, high-contrast issues |
| `FEATURE_GAP_OR_REMOVAL` | Missing requested functionality (e.g. call driver directly, dark mode) |
| `POLICY_EXPECTATION_MISMATCH` | Company transport policies (e.g. AC rules, nodal vs. doorstep drop rules) |
| `DATA_VISIBILITY` | Missing trip history, invisible vehicle details, co-passenger visibility |
| `POSITIVE_VALUE` | Explicit praise for commute convenience, driver safety, or reliability |
| `UNCLEAR_INSUFFICIENT_DETAIL` | Vague 1-word venting without actionable details (e.g., "worst app") |
| `FEEDBACK_OR_RATING_FLOW` | Malfunctioning in-app post-trip feedback or aggressive review prompts |

---

## Technical Highlights for Reviewers

- **Anti-Hallucination Pipeline**: All extracted evidence quotes are verified using exact substring matching against source review text in Python before acceptance.
- **Atomic Checkpointing**: Checkpoint files are written using OS-level temporary files and atomic replacements (`os.replace`), protecting runs from corruption during process interruption.
- **Operational Support Audit**: Pinpoints that **95.5% of negative reviews** receive zero developer response, presenting leadership with an immediate non-code operational win.
