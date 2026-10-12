#!/usr/bin/env python3
"""
06_report.py — Aggregate metrics and export analytical summaries from labeled reviews.

Merges AI-classified review labels with review metadata to compute root-cause rankings,
version correlations, and developer response audits. Generates quantitative CSV tables
consumed by the interactive dashboard and candidate analysis.

Usage:
  python pipeline/06_report.py [input.csv] [labels.jsonl] [--outdir path]

Defaults:
  input : data/processed/moveinsync_reviews_2025_2026.csv
  labels: data/labeled/moveinsync_reviews_2025_2026_labels.jsonl
  outdir: outputs/reports/

Outputs (written to --outdir):
  ├── ranked_negative_issues.csv
  ├── issue_type_breakdown.csv
  ├── version_negative_trends.csv
  ├── developer_response_audit.csv
  └── action_plan_priority_matrix.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd

# ---------------------------------------------------------------------------
# Paths & CLI Configuration
# ---------------------------------------------------------------------------
PIPELINE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PIPELINE_DIR.parent
DATA_PROCESSED_DIR = REPO_ROOT / "data" / "processed"
DATA_LABELED_DIR = REPO_ROOT / "data" / "labeled"
DEFAULT_OUTDIR = REPO_ROOT / "outputs" / "reports"

parser = argparse.ArgumentParser(
    description="Aggregate metrics and generate analytical CSV summaries from labeled Play Store reviews."
)
parser.add_argument(
    "input_csv",
    nargs="?",
    default=str(DATA_PROCESSED_DIR / "moveinsync_reviews_2025_2026.csv"),
    help="Path to filtered reviews CSV (default: data/processed/moveinsync_reviews_2025_2026.csv)",
)
parser.add_argument(
    "labels_jsonl",
    nargs="?",
    default=str(DATA_LABELED_DIR / "moveinsync_reviews_2025_2026_labels.jsonl"),
    help="Path to labeled reviews JSONL (default: data/labeled/moveinsync_reviews_2025_2026_labels.jsonl)",
)
parser.add_argument(
    "--outdir",
    default=str(DEFAULT_OUTDIR),
    help=f"Directory for generated report outputs (default: {DEFAULT_OUTDIR})",
)
args = parser.parse_args()

input_csv = Path(args.input_csv)
labels_jsonl = Path(args.labels_jsonl)
outdir = Path(args.outdir)
outdir.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Pre-flight Validation & Data Loading
# ---------------------------------------------------------------------------
if not input_csv.exists():
    raise SystemExit(f"Input reviews CSV not found: {input_csv}")
if not labels_jsonl.exists():
    raise SystemExit(f"Labels JSONL file not found: {labels_jsonl}")

print(f"Loading reviews metadata from {input_csv}...")
df_csv = pd.read_csv(input_csv)
if df_csv.empty:
    raise SystemExit(f"Input CSV is empty: {input_csv}")

if "reviewId" not in df_csv.columns:
    raise SystemExit(f"Required column 'reviewId' missing from {input_csv}")

df_csv["score"] = pd.to_numeric(df_csv.get("score"), errors="coerce")
df_csv["thumbsUpCount"] = (
    pd.to_numeric(df_csv.get("thumbsUpCount"), errors="coerce").fillna(0).astype(int)
    if "thumbsUpCount" in df_csv.columns
    else 0
)

# Parse response flag
if "replyContent" in df_csv.columns:
    df_csv["has_reply"] = df_csv["replyContent"].notna() & (
        df_csv["replyContent"].astype(str).str.strip() != ""
    )
else:
    df_csv["has_reply"] = False

# Load labeled JSONL
print(f"Loading classified labels from {labels_jsonl}...")
labels_data: List[Dict[str, Any]] = []
with open(labels_jsonl, "r", encoding="utf-8") as f:
    for line_idx, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            labels_data.append(
                {
                    "reviewId": record.get("review_id"),
                    "primary_label": record.get("primary_label", "UNCATEGORIZED"),
                    "all_labels": record.get("labels", []),
                    "sentiment": record.get("sentiment", "unspecified"),
                    "issue_type": record.get("issue_type", "OTHER"),
                    "confidence": record.get("confidence", 3),
                    "evidence": record.get("evidence", []),
                }
            )
        except json.JSONDecodeError:
            continue

df_labels = pd.DataFrame(labels_data)
if df_labels.empty:
    raise SystemExit("No valid classification labels loaded.")

merged = pd.merge(df_csv, df_labels, on="reviewId", how="inner")
total_merged = len(merged)
if total_merged == 0:
    raise SystemExit("Merge between metadata and labels resulted in 0 rows.")

print(f"Successfully merged {total_merged:,} classified reviews.")

# ---------------------------------------------------------------------------
# 2. Key Statistical Computations
# ---------------------------------------------------------------------------
total_reviews = total_merged
positive = merged[merged["score"].isin([4, 5])]
neutral = merged[merged["score"] == 3]
negative = merged[merged["score"].isin([1, 2])]

total_positive = len(positive)
total_neutral = len(neutral)
total_negative = len(negative)

pct_positive = (total_positive / total_reviews * 100) if total_reviews > 0 else 0.0
pct_neutral = (total_neutral / total_reviews * 100) if total_reviews > 0 else 0.0
pct_negative = (total_negative / total_reviews * 100) if total_reviews > 0 else 0.0
avg_score = merged["score"].mean() if total_reviews > 0 else 0.0

# Developer Response Audit
neg_replied = int(negative["has_reply"].sum())
neg_reply_pct = (neg_replied / total_negative * 100) if total_negative > 0 else 0.0
pos_replied = int(positive["has_reply"].sum())
pos_reply_pct = (pos_replied / total_positive * 100) if total_positive > 0 else 0.0
neu_replied = int(neutral["has_reply"].sum())
neu_reply_pct = (neu_replied / total_neutral * 100) if total_neutral > 0 else 0.0

df_audit = pd.DataFrame(
    [
        {"Cohort": "1-2 Star (Negative)", "Total": total_negative, "Replied": neg_replied, "Reply_Rate_Pct": round(neg_reply_pct, 2)},
        {"Cohort": "3 Star (Neutral)", "Total": total_neutral, "Replied": neu_replied, "Reply_Rate_Pct": round(neu_reply_pct, 2)},
        {"Cohort": "4-5 Star (Positive)", "Total": total_positive, "Replied": pos_replied, "Reply_Rate_Pct": round(pos_reply_pct, 2)},
        {"Cohort": "All Reviews", "Total": total_reviews, "Replied": int(merged["has_reply"].sum()), "Reply_Rate_Pct": round(merged["has_reply"].mean() * 100, 2)},
    ]
)
df_audit.to_csv(outdir / "developer_response_audit.csv", index=False)

# ---------------------------------------------------------------------------
# 3. Negative Issue Rankings
# ---------------------------------------------------------------------------
ranked_issues = (
    negative.groupby("primary_label")
    .agg(
        negative_reviews=("reviewId", "count"),
        total_thumbs_up=("thumbsUpCount", "sum"),
        avg_rating=("score", "mean"),
    )
    .reset_index()
    .sort_values(by="negative_reviews", ascending=False)
)
ranked_issues["share_of_negative_pct"] = (
    ranked_issues["negative_reviews"] / total_negative * 100
).round(2)
ranked_issues.to_csv(outdir / "ranked_negative_issues.csv", index=False)

# ---------------------------------------------------------------------------
# 4. Issue Type Breakdown
# ---------------------------------------------------------------------------
issue_type_breakdown = (
    negative.groupby("issue_type")
    .agg(count=("reviewId", "count"), total_upvotes=("thumbsUpCount", "sum"))
    .reset_index()
    .sort_values(by="count", ascending=False)
)
issue_type_breakdown["share_pct"] = (
    issue_type_breakdown["count"] / total_negative * 100
).round(2)
issue_type_breakdown.to_csv(outdir / "issue_type_breakdown.csv", index=False)

# ---------------------------------------------------------------------------
# 5. App Version Correlation
# ---------------------------------------------------------------------------
version_trends = (
    negative[negative["reviewCreatedVersion"].notna()]
    .groupby("reviewCreatedVersion")
    .agg(negative_count=("reviewId", "count"), avg_score=("score", "mean"))
    .reset_index()
    .sort_values(by="negative_count", ascending=False)
    .head(15)
)
version_trends.to_csv(outdir / "version_negative_trends.csv", index=False)

# ---------------------------------------------------------------------------
# 6. Action Plan Priority Matrix (Data-driven backlog)
# ---------------------------------------------------------------------------
actionable_ranked = ranked_issues[
    ~ranked_issues["primary_label"].isin(["UNCLEAR_INSUFFICIENT_DETAIL", "POSITIVE_VALUE"])
].reset_index(drop=True)

matrix_rows = []
for idx, row in actionable_ranked.iterrows():
    cat = row["primary_label"]
    cnt = int(row["negative_reviews"])
    pct = float(row["share_of_negative_pct"])
    upvotes = int(row["total_thumbs_up"])
    
    if idx < 2:
        priority = "P0 (Immediate / Day 1)"
    elif idx < 5:
        priority = "P1 (Sprint / Weeks 1-2)"
    else:
        priority = "P2 (Milestone / Month 1)"

    matrix_rows.append(
        {
            "Priority": priority,
            "Category": cat,
            "Negative_Reviews": cnt,
            "Share_of_Negatives_Pct": pct,
            "Thumbs_Up_Endorsements": upvotes,
        }
    )

df_action_matrix = pd.DataFrame(matrix_rows)
df_action_matrix.to_csv(outdir / "action_plan_priority_matrix.csv", index=False)

# ---------------------------------------------------------------------------
# Console Output
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("AGGREGATION SUMMARY (MoveInSync 2025-2026)")
print("=" * 60)
print(f"Total Reviews Evaluated   : {total_reviews:,}")
print(f"Average Star Rating       : {avg_score:.2f} / 5.0")
print(f"Positive Reviews (4-5*)   : {total_positive:,} ({pct_positive:.1f}%)")
print(f"Neutral Reviews (3*)      : {total_neutral:,} ({pct_neutral:.1f}%)")
print(f"Negative Reviews (1-2*)   : {total_negative:,} ({pct_negative:.1f}%)")
print(f"Developer Reply Rate (Neg): {neg_reply_pct:.1f}% ({neg_replied:,}/{total_negative:,})")
print("\nTop 5 Actionable Negative Friction Points:")
for _, r in actionable_ranked.head(5).iterrows():
    print(f"  - {r['primary_label']:<28}: {int(r['negative_reviews']):>4} reviews ({r['share_of_negative_pct']}%)")
print("\nExported Analytics Tables:")
for f in [
    "ranked_negative_issues.csv",
    "issue_type_breakdown.csv",
    "version_negative_trends.csv",
    "developer_response_audit.csv",
    "action_plan_priority_matrix.csv",
]:
    print(f"  [+] {outdir / f}")
print("=" * 60 + "\n")
