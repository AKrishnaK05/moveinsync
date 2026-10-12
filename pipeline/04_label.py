#!/usr/bin/env python3
"""
04_label.py — Orchestrate Gemini batch classification of filtered reviews.

Usage:
  python pipeline/04_label.py [input.csv] [output.jsonl]

Defaults:
  input : data/processed/moveinsync_reviews_2025_2026.csv
  output: data/labeled/moveinsync_reviews_2025_2026_labels.jsonl

Resumable: already-classified batches are detected by review_id and skipped.
Progress is checkpointed after each batch so a partial run can be resumed.

Requires Python 3.8+ (walrus operator := is used in several list comprehensions).

"""

import csv
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PIPELINE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PIPELINE_DIR.parent
DATA_PROCESSED_DIR = REPO_ROOT / "data" / "processed"
DATA_LABELED_DIR = REPO_ROOT / "data" / "labeled"

INPUT = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else DATA_PROCESSED_DIR / "moveinsync_reviews_2025_2026.csv"
)
OUTPUT = (
    Path(sys.argv[2])
    if len(sys.argv) > 2
    else DATA_LABELED_DIR / "moveinsync_reviews_2025_2026_labels.jsonl"
)
BATCH_SIZE = int(os.getenv("GEMINI_BATCH_SIZE", "50"))
CLASSIFIER = PIPELINE_DIR / "05_classify.py"

# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------
if BATCH_SIZE < 1:
    raise SystemExit("GEMINI_BATCH_SIZE must be at least 1")

if not CLASSIFIER.exists():
    raise SystemExit(
        f"Required classifier not found: {CLASSIFIER}. "
        "Ensure pipeline/05_classify.py exists before running."
    )

if not INPUT.exists():
    raise SystemExit(f"Input CSV not found: {INPUT}")

# ---------------------------------------------------------------------------
# Load reviews
# ---------------------------------------------------------------------------
with INPUT.open("r", encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))

# Check for empty file before accessing rows[0]
if not rows:
    raise SystemExit(f"No reviews found in {INPUT}")

required = {"reviewId", "content", "at"}
missing = required - set(rows[0])
if missing:
    raise SystemExit(
        f"CSV input is missing required columns: {', '.join(sorted(missing))}"
    )

# ---------------------------------------------------------------------------
# Load any existing partial output (for resumability)
# ---------------------------------------------------------------------------
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
all_results: list = []
if OUTPUT.exists():
    try:
        all_results = [
            json.loads(line)
            for line in OUTPUT.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()
        ]
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(
            f"Existing output is not valid JSONL and cannot be resumed: {OUTPUT}"
        ) from exc

results_by_id = {str(result.get("review_id")): result for result in all_results}
batch_count = (len(rows) + BATCH_SIZE - 1) // BATCH_SIZE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_combined(results: list) -> None:
    """Atomically write the full results list to OUTPUT as JSONL.

    Writes to a temporary file on the same directory and atomically replaces
    OUTPUT to guarantee checkpoint integrity against abrupt process termination.
    """
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        "\n".join(
            json.dumps(result, ensure_ascii=False, separators=(",", ":"))
            for result in results
        )
        + "\n"
    )
    temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        dir=OUTPUT.parent,
        prefix="checkpoint_",
        suffix=".tmp",
        delete=False,
        encoding="utf-8",
    )
    try:
        temp_file.write(payload)
        temp_file.flush()
        os.fsync(temp_file.fileno())
        temp_file.close()
        Path(temp_file.name).replace(OUTPUT)
    except Exception:
        temp_path = Path(temp_file.name)
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise


# ---------------------------------------------------------------------------
# Batch loop
# ---------------------------------------------------------------------------
with tempfile.TemporaryDirectory(prefix="moveinsync-label-") as temp_dir:
    temp_dir_path = Path(temp_dir)

    for batch_number, start in enumerate(range(0, len(rows), BATCH_SIZE), 1):
        batch_rows = rows[start : start + BATCH_SIZE]

        # Normalise each row into the schema expected by 05_classify.py.
        # row_number starts at start + 2 to account for the header line (+1)
        # and the 0-to-1-index conversion (+1).
        normalized = []
        for row_number, row in enumerate(batch_rows, start + 2):
            review_id = (row.get("reviewId") or "").strip()
            if not review_id:
                raise SystemExit(f"Empty reviewId at CSV row {row_number}")
            score = row.get("score")
            normalized.append({
                "review_id": review_id,
                "score": int(score) if score else None,
                "review_text": row.get("content") or "",
                "date": row.get("at") or "",
                "app_version": row.get("reviewCreatedVersion") or "",
                "period": "2025_2026",
            })

        expected_ids = [row["review_id"] for row in normalized]

        # Skip batch if every review already has a label
        if all(review_id in results_by_id for review_id in expected_ids):
            print(f"Reusing completed batch {batch_number}/{batch_count} from {OUTPUT}.")
            continue

        # Write batch input and run the classifier
        input_path = temp_dir_path / f"batch_{batch_number:04d}.jsonl"
        batch_output_path = temp_dir_path / f"batch_{batch_number:04d}_labels.jsonl"
        input_path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in normalized) + "\n",
            encoding="utf-8",
        )

        print(f"Labeling batch {batch_number}/{batch_count} ({len(normalized)} reviews)...")
        try:
            subprocess.run(
                [sys.executable, str(CLASSIFIER), str(input_path), str(batch_output_path)],
                cwd=REPO_ROOT,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            # Save whatever was completed before this batch failed
            completed = [
                results_by_id[review_id]
                for row in rows
                if (review_id := (row.get("reviewId") or "").strip()) in results_by_id
            ]
            write_combined(completed)
            raise SystemExit(
                f"Stopped at batch {batch_number}/{batch_count}. "
                f"Combined output contains {len(completed)} labels at {OUTPUT}. "
                f"Resolve the API issue then re-run to resume. "
                f"Exit code: {exc.returncode}"
            ) from exc

        # Validate and merge batch results
        batch_results = [
            json.loads(line)
            for line in batch_output_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if [str(result.get("review_id")) for result in batch_results] != expected_ids:
            raise SystemExit(
                f"Batch {batch_number} returned unexpected IDs; "
                "temporary results were removed"
            )

        results_by_id.update(
            {str(result["review_id"]): result for result in batch_results}
        )
        # Rebuild all_results in input order, including only IDs we have so far
        all_results = [
            results_by_id[review_id]
            for row in rows
            if (review_id := (row.get("reviewId") or "").strip()) in results_by_id
        ]
        write_combined(all_results)
        print(f"Checkpoint saved: {len(all_results):,} labels in {OUTPUT}")

# ---------------------------------------------------------------------------
# Final write (ensures ordering matches input even after a full resume)
# ---------------------------------------------------------------------------
all_results = [
    results_by_id[review_id]
    for row in rows
    if (review_id := (row.get("reviewId") or "").strip()) in results_by_id
]
write_combined(all_results)
print(f"\nSaved {len(all_results):,} labels to {OUTPUT}")
