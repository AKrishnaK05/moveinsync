"""
03_filter.py — Filter the raw reviews CSV to a date range.

Usage:
  python pipeline/03_filter.py [input.csv] [output.csv] [--start YYYY-MM-DD]

Defaults:
  input : data/raw/reviews_com.moveinsync.ets.csv
  output: data/processed/moveinsync_reviews_2025_2026.csv
  start : 2025-01-01
  end   : today (dynamic — always current date at run time)
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PIPELINE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PIPELINE_DIR.parent
DATA_RAW_DIR = REPO_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = REPO_ROOT / "data" / "processed"

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(
    description="Filter a Play Store reviews CSV to a date range."
)
parser.add_argument(
    "input_csv",
    nargs="?",
    default=str(DATA_RAW_DIR / "reviews_com.moveinsync.ets.csv"),
    help="Path to the raw reviews CSV (default: data/raw/reviews_com.moveinsync.ets.csv)",
)
parser.add_argument(
    "output_csv",
    nargs="?",
    default=str(DATA_PROCESSED_DIR / "moveinsync_reviews_2025_2026.csv"),
    help="Destination CSV path (default: data/processed/moveinsync_reviews_2025_2026.csv)",
)
parser.add_argument(
    "--start",
    default="2025-01-01",
    metavar="YYYY-MM-DD",
    help="Inclusive start date in UTC (default: 2025-01-01)",
)
args = parser.parse_args()

INPUT = Path(args.input_csv)
OUTPUT = Path(args.output_csv)
START_DATE = pd.Timestamp(args.start, tz="UTC")
END_DATE = pd.Timestamp.now(tz="UTC")   # always up to the moment of execution

if not INPUT.exists():
    print(f"Error: input file not found: {INPUT}", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------
df = pd.read_csv(INPUT)
df["at"] = pd.to_datetime(df["at"], errors="coerce", utc=True)

recent_df = df[(df["at"] >= START_DATE) & (df["at"] < END_DATE)].copy()

if recent_df.empty:
    print(
        f"Error: no reviews found between {args.start} and today. "
        "Check that the input file contains data in this range.",
        file=sys.stderr,
    )
    sys.exit(1)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
recent_df.to_csv(OUTPUT, index=False)

print(f"Original reviews:      {len(df):,}")
print(f"Filtered reviews:      {len(recent_df):,}")
print(f"Invalid/missing dates: {int(df['at'].isna().sum()):,}")
print(f"Date range:            {recent_df['at'].min()} to {recent_df['at'].max()}")
print(f"Saved to:              {OUTPUT}")
