"""
01_collect.py — Scrape all Play Store reviews for a given app.

Usage:
  python pipeline/01_collect.py [app_url_or_package_id] [output.csv]

Defaults:
  app   : com.moveinsync.ets  (MoveInSync employee app)
  output: data/raw/reviews_<package_id>.csv

"""

import random
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd
from google_play_scraper import Sort, reviews

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PIPELINE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PIPELINE_DIR.parent
DATA_RAW_DIR = REPO_ROOT / "data" / "raw"

DEFAULT_APP_URL = (
    "https://play.google.com/store/apps/details?id=com.moveinsync.ets&pcampaignid=web_share"
)

# Retry settings
MAX_RETRIES = 3
BASE_RETRY_DELAY = 2.0  # seconds; doubles on each attempt
PAGE_DELAY = 0.5        # seconds between successful page fetches

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = [
    "reviewId", "score", "content", "at",
    "thumbsUpCount", "reviewCreatedVersion",
    "replyContent", "repliedAt",
]


def get_package_id(value: str) -> str:
    """Extract a package ID from a Play Store URL or return the value as-is.

    Emits a warning to stderr when the value looks URL-like but no ``id``
    query parameter can be found, so callers notice the potential mis-parse
    instead of silently using a garbage string.
    """
    parsed = urlparse(value)
    if parsed.query:
        package_id = parse_qs(parsed.query).get("id", [None])[0]
        if package_id:
            return package_id
    # Value appears URL-like but we could not extract a package ID
    if "/" in value or value.startswith("http"):
        print(
            f"Warning: could not extract a package ID from '{value}'; "
            "using the last path segment as-is. Pass the package ID directly "
            "(e.g. com.moveinsync.ets) to suppress this warning.",
            file=sys.stderr,
        )
    return value.rstrip("/").split("/")[-1]


def save_partial(all_reviews: list, out_file: Path) -> None:
    """Write whatever has been collected so far and print a summary."""
    if not all_reviews:
        print("No reviews collected — nothing to save.", file=sys.stderr)
        return
    df = pd.DataFrame(all_reviews)
    available = [c for c in REQUIRED_COLUMNS if c in df.columns]
    out_file.parent.mkdir(parents=True, exist_ok=True)
    df[available].to_csv(out_file, index=False)
    print(f"Partial save: {len(df):,} reviews written to {out_file}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

app_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_APP_URL
package_id = get_package_id(app_url)

DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
out_file = Path(sys.argv[2]) if len(sys.argv) > 2 else DATA_RAW_DIR / f"reviews_{package_id}.csv"

all_reviews: list = []
token = None

print(f"Collecting reviews for: {package_id}")
print(f"Output: {out_file}")

while True:
    # --- Fetch one page with retries ---
    batch = None
    for attempt in range(MAX_RETRIES):
        try:
            batch, token = reviews(
                package_id,
                lang="en",
                country="in",
                sort=Sort.NEWEST,
                count=200,
                continuation_token=token,
            )
            break  # success
        except Exception as exc:
            if attempt == MAX_RETRIES - 1:
                print(
                    f"\nFailed to fetch page after {MAX_RETRIES} attempts: {exc}",
                    file=sys.stderr,
                )
                save_partial(all_reviews, out_file)
                raise SystemExit(1) from exc
            delay = BASE_RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
            print(
                f"  Request failed ({exc}); "
                f"retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})..."
            )
            time.sleep(delay)

    all_reviews.extend(batch)
    print(f"  Collected {len(all_reviews):,} reviews so far...")

    if token is None or not batch:
        break  # no more pages

    time.sleep(PAGE_DELAY)

# --- Build and save the final DataFrame ---
df = pd.DataFrame(all_reviews)
available = [c for c in REQUIRED_COLUMNS if c in df.columns]
out_file.parent.mkdir(parents=True, exist_ok=True)
df[available].to_csv(out_file, index=False)

print(f"\nSaved {len(df):,} reviews to {out_file}")
print(df["score"].value_counts().sort_index().to_string())
