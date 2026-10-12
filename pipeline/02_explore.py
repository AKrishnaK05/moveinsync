"""
02_explore.py — Exploratory analysis for MoveInSync Play Store reviews.

Usage:
  python pipeline/02_explore.py [input.csv] [--outdir path]

Defaults:
  input : data/raw/reviews_com.moveinsync.ets.csv
          (falls back to data/processed/ if raw is not found)
  outdir: outputs/exploration/

Outputs:
  data_quality_overview.csv
  yearly_summary.csv
  monthly_summary.csv
  rating_distribution_by_period.csv
  top_100_app_versions.csv
  negative_share_by_year.png
  recent_monthly_trend.png

This script runs on the full dataset across all years to uncover long-term
trends and provide EDA charts for stakeholder reporting.
"""

import argparse
import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PIPELINE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PIPELINE_DIR.parent
DATA_PROCESSED_DIR = REPO_ROOT / "data" / "processed"
DATA_RAW_DIR = REPO_ROOT / "data" / "raw"
DEFAULT_OUTDIR = str(REPO_ROOT / "outputs" / "exploration")

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(
    description="Exploratory analysis for MoveInSync Play Store reviews."
)
parser.add_argument(
    "input_csv",
    nargs="?",
    help="Path to CSV file with Play Store reviews. "
    "Auto-detected from data/ directories if omitted.",
)
parser.add_argument(
    "--outdir",
    default=DEFAULT_OUTDIR,
    help=f"Directory for output files (default: {DEFAULT_OUTDIR})",
)
args = parser.parse_args()

# Auto-detect input when not supplied — prefer the full raw CSV (all years)
if args.input_csv is None:
    candidates = [
        DATA_RAW_DIR / "reviews_com.moveinsync.ets.csv",
        *sorted(DATA_RAW_DIR.glob("*.csv")),
        DATA_PROCESSED_DIR / "moveinsync_reviews_2025_2026.csv",
        *sorted(DATA_PROCESSED_DIR.glob("*.csv")),
    ]
    selected = next((p for p in candidates if p.exists()), None)
    if selected is None:
        parser.error(
            "No input CSV supplied and no review CSV was found in data/raw/ "
            "or data/processed/. Pass the file path explicitly."
        )
    args.input_csv = str(selected)
    print(f"Auto-detected input: {args.input_csv}")

os.makedirs(args.outdir, exist_ok=True)

# ---------------------------------------------------------------------------
# Load and clean
# ---------------------------------------------------------------------------
df = pd.read_csv(args.input_csv)
df["at"] = pd.to_datetime(df["at"], errors="coerce", utc=True)
df["score"] = pd.to_numeric(df["score"], errors="coerce")
df["content"] = df["content"].fillna("").astype(str)
df = df.drop_duplicates(subset="reviewId", keep="first").copy()
df["year"] = df["at"].dt.year
df["month"] = df["at"].dt.strftime("%Y-%m")
df["review_length_chars"] = df["content"].str.len()
df["review_length_words"] = df["content"].str.split().str.len()
df["negative_1_2"] = df["score"].isin([1, 2])
df["period"] = df["year"].apply(
    lambda y: "Historical: pre-2025" if pd.notna(y) and y < 2025
    else ("Recent: 2025 onward" if pd.notna(y) and y >= 2025 else "Unknown date")
)

# ---------------------------------------------------------------------------
# Data quality overview
# ---------------------------------------------------------------------------
overview = pd.DataFrame({
    "metric": [
        "Rows after deduplication", "Missing review text", "Missing date",
        "Missing score", "Missing app version", "Earliest review date",
        "Latest review date", "Reviews from 2025 onward", "Reviews before 2025",
        "Reviews with 1-2 stars (all years)", "1-2 star share (all years, %)",
    ],
    "value": [
        len(df),
        int(df["content"].str.strip().eq("").sum()),
        int(df["at"].isna().sum()),
        int(df["score"].isna().sum()),
        int(df["reviewCreatedVersion"].isna().sum()) if "reviewCreatedVersion" in df else None,
        str(df["at"].min().date()) if df["at"].notna().any() else "",
        str(df["at"].max().date()) if df["at"].notna().any() else "",
        int((df["year"] >= 2025).sum()),
        int((df["year"] < 2025).sum()),
        int(df["negative_1_2"].sum()),
        round(df["negative_1_2"].mean() * 100, 2),
    ],
})
overview.to_csv(os.path.join(args.outdir, "data_quality_overview.csv"), index=False)

# ---------------------------------------------------------------------------
# Yearly summary
# ---------------------------------------------------------------------------
yearly = df.groupby("year", dropna=False).agg(
    reviews=("reviewId", "count"),
    negative_1_2=("negative_1_2", "sum"),
    negative_share_pct=("negative_1_2", lambda s: round(s.mean() * 100, 2)),
    median_review_words=("review_length_words", "median"),
    missing_text=("content", lambda s: int(s.str.strip().eq("").sum())),
).reset_index()
yearly.to_csv(os.path.join(args.outdir, "yearly_summary.csv"), index=False)

# ---------------------------------------------------------------------------
# Monthly summary
# ---------------------------------------------------------------------------
monthly = df[df["at"].notna()].groupby("month").agg(
    reviews=("reviewId", "count"),
    negative_1_2=("negative_1_2", "sum"),
    negative_share_pct=("negative_1_2", lambda s: round(s.mean() * 100, 2)),
).reset_index()
monthly.to_csv(os.path.join(args.outdir, "monthly_summary.csv"), index=False)

# ---------------------------------------------------------------------------
# Rating distribution by period
# ---------------------------------------------------------------------------
ratings = df.groupby(["period", "score"], dropna=False).size().rename("reviews").reset_index()
ratings.to_csv(os.path.join(args.outdir, "rating_distribution_by_period.csv"), index=False)

# ---------------------------------------------------------------------------
# Top 100 app versions by review volume
# ---------------------------------------------------------------------------
if "reviewCreatedVersion" in df:
    version = df.groupby("reviewCreatedVersion", dropna=False).agg(
        reviews=("reviewId", "count"),
        negative_share_pct=("negative_1_2", lambda s: round(s.mean() * 100, 2)),
    ).reset_index().sort_values("reviews", ascending=False)
    version.head(100).to_csv(os.path.join(args.outdir, "top_100_app_versions.csv"), index=False)


# ---------------------------------------------------------------------------
# Chart 1 — Share of 1–2 star reviews by year
# ---------------------------------------------------------------------------
plot_df = yearly[yearly["year"].notna()].copy()
years = plot_df["year"].astype(int).tolist()
pcts = plot_df["negative_share_pct"].tolist()

fig, ax = plt.subplots(figsize=(max(6, len(years) * 1.5), 5))
bars = ax.bar(years, pcts, color="#d62728", width=0.5, zorder=3)

# Annotate each bar with its exact percentage value
for bar, pct in zip(bars, pcts):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.3,
        f"{pct:.1f}%",
        ha="center", va="bottom", fontsize=10, fontweight="bold",
    )

ax.set_xticks(years)                    # force integer ticks — one per year
ax.set_xticklabels([str(y) for y in years])
ax.set_xlabel("Review year")
ax.set_ylabel("1–2 star reviews (%)")
ax.set_title("Share of 1–2 star reviews by year")
ax.set_ylim(0, max(pcts) * 1.2)        # headroom for labels
ax.yaxis.grid(True, linestyle="--", alpha=0.5, zorder=0)
ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig(os.path.join(args.outdir, "negative_share_by_year.png"), dpi=160)
plt.close(fig)

# ---------------------------------------------------------------------------
# Chart 2 — Recent monthly volume and negative-rating share (dual axis)
# ---------------------------------------------------------------------------
mrecent = monthly[monthly["month"] >= "2025-01"].copy()
fig, ax1 = plt.subplots(figsize=(12, 5))

COLOR_VOLUME = "#1f77b4"   # blue  — review count
COLOR_NEG = "#d62728"      # red   — negative share

ax1.plot(mrecent["month"], mrecent["reviews"], marker="o", color=COLOR_VOLUME, label="Review count")
ax1.set_xlabel("Month")
ax1.set_ylabel("Review count", color=COLOR_VOLUME)
ax1.tick_params(axis="x", rotation=70)
ax1.tick_params(axis="y", labelcolor=COLOR_VOLUME)

ax2 = ax1.twinx()
ax2.plot(mrecent["month"], mrecent["negative_share_pct"], marker="s", color=COLOR_NEG, label="1–2 star share (%)")
ax2.set_ylabel("1–2 star share (%)", color=COLOR_NEG)
ax2.tick_params(axis="y", labelcolor=COLOR_NEG)

# Combined legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

plt.title("Recent monthly review volume and negative-rating share")
fig.tight_layout()
plt.savefig(os.path.join(args.outdir, "recent_monthly_trend.png"), dpi=160)
plt.close()

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print(f"Processed {len(df):,} reviews")
print(f"Recent (2025 onward):  {int((df['year'] >= 2025).sum()):,}")
print(f"Historical (pre-2025): {int((df['year'] < 2025).sum()):,}")
print(f"Outputs saved to:      {args.outdir}")
