#!/usr/bin/env python3
"""
05_classify.py — Classify one JSONL batch of MoveInSync reviews with Gemini.

Internal worker script invoked per-batch by 04_label.py.

Usage:
  python pipeline/05_classify.py <input.jsonl> <output.jsonl>

Environment variables:
  GEMINI_API_KEY          (required)
  GEMINI_MODEL            primary model (default: gemini-2.5-flash)
  GEMINI_FALLBACK_MODELS  comma-separated fallbacks (default: gemini-1.5-flash)
"""

import json
import os
import random
import re
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path

from google import genai
from google.genai import types
from jsonschema import Draft202012Validator

# ---------------------------------------------------------------------------
# CLI & Paths
# ---------------------------------------------------------------------------
if len(sys.argv) < 3:
    raise SystemExit(
        "Usage: python pipeline/05_classify.py <input.jsonl> <output.jsonl>\n"
        "(This script is normally invoked automatically by 04_label.py)"
    )

PIPELINE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PIPELINE_DIR.parent
CONFIG_DIR = REPO_ROOT / "config"

INPUT = Path(sys.argv[1])
OUTPUT = Path(sys.argv[2])

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

_configured_fallbacks = os.getenv("GEMINI_FALLBACK_MODELS")
FALLBACK_MODELS = [
    value.strip()
    for value in (
        _configured_fallbacks
        if _configured_fallbacks is not None
        else "gemini-1.5-flash"
    ).split(",")
    if value.strip()
]

API_KEY = os.getenv("GEMINI_API_KEY")

# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------
if not API_KEY:
    raise SystemExit("GEMINI_API_KEY is not set")
if not INPUT.exists():
    raise SystemExit(f"Input JSONL not found: {INPUT}")

# ---------------------------------------------------------------------------
# Load config
# ---------------------------------------------------------------------------
schema = json.loads((CONFIG_DIR / "classification_schema.json").read_text(encoding="utf-8"))
prompt = (CONFIG_DIR / "classification_prompt.txt").read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# Load reviews
# ---------------------------------------------------------------------------
reviews = [
    json.loads(line)
    for line in INPUT.read_text(encoding="utf-8-sig").splitlines()
    if line.strip()
]
if not reviews:
    raise SystemExit(f"No reviews found in {INPUT}")

# ---------------------------------------------------------------------------
# Build the Gemini request
# ---------------------------------------------------------------------------
request = (
    f"{prompt}\n\n"
    "Return a JSON object with a `results` array containing exactly one "
    "classification for each input review, in the same order. "
    "Do not include markdown fences.\n\n"
    f"INPUT REVIEWS:\n{json.dumps(reviews, ensure_ascii=False)}"
)

response_schema = {
    "type": "OBJECT",
    "properties": {
        "results": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "review_id":          {"type": "STRING"},
                    "labels":             {"type": "ARRAY", "items": {"type": "STRING"}},
                    "primary_label":      {"type": "STRING", "nullable": True},
                    "sentiment":          {"type": "STRING"},
                    "issue_type":         {"type": "STRING"},
                    "evidence": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "label": {"type": "STRING"},
                                "text":  {"type": "STRING"},
                            },
                            "required": ["label", "text"],
                        },
                    },
                    "confidence":         {"type": "INTEGER"},
                    "needs_human_review": {"type": "BOOLEAN"},
                    "review_note":        {"type": "STRING"},
                },
                "required": [
                    "review_id", "labels", "primary_label", "sentiment",
                    "issue_type", "evidence", "confidence",
                    "needs_human_review", "review_note",
                ],
            },
        }
    },
    "required": ["results"],
}

client = genai.Client(api_key=API_KEY)
models = [MODEL] + [m for m in FALLBACK_MODELS if m != MODEL]


# ---------------------------------------------------------------------------
# Gemini call with retry + model fallback
# ---------------------------------------------------------------------------

def generate_results(contents: str) -> list:
    """Send contents to Gemini and return the parsed results list.

    Tries each configured model in order. Retries up to 5 times per model on:
      - Transient HTTP 5xx errors (500, 502, 503, 504)
      - Rate-limiting (429) with exponential cooldown
      - Network dropouts, connection resets, and socket timeouts
      - Malformed or truncated JSON response payloads
    Falls back to secondary models if primary model remains unavailable.
    """
    last_error = None
    for model_index, model in enumerate(models):
        for attempt in range(5):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema,
                        temperature=0,
                    ),
                )
                if not response.text or not response.text.strip():
                    raise ValueError(f"Empty response text received from {model}")

                payload = json.loads(response.text)
                if "results" not in payload or not isinstance(payload["results"], list):
                    raise ValueError(f"Malformed response payload (missing 'results' list): {payload}")

                if model != MODEL:
                    print(f"Used fallback model: {model}")
                return payload["results"]

            except Exception as exc:
                last_error = exc
                code = getattr(exc, "code", getattr(exc, "status_code", None))
                err_str = str(exc).lower()

                # Model not found / unavailable in this region -> switch immediately
                if code == 404:
                    print(f"{model} is unavailable (404); skipping to next fallback model.")
                    break

                # Rate limiting (429) -> exponential backoff before retry or fallback
                if code == 429:
                    if attempt >= 3 and model_index < len(models) - 1:
                        print(f"{model} quota exhausted (429); switching to fallback model {models[model_index + 1]}...")
                        break
                    delay = min(60.0, 15.0 * (2 ** attempt)) + random.uniform(1.0, 3.0)
                    print(f"{model} rate limited (429); cooling down for {delay:.1f}s ({attempt + 1}/5)...")
                    time.sleep(delay)
                    continue

                # Determine if error is transient
                is_transient = (
                    code in (500, 502, 503, 504, 408)
                    or isinstance(exc, (TimeoutError, ConnectionError, json.JSONDecodeError, ValueError))
                    or any(k in err_str for k in ("timeout", "connection", "reset", "unavailable", "econnreset", "socket"))
                )

                if not is_transient:
                    # Non-retryable operational error for this model -> attempt next model
                    print(f"{model} encountered non-retryable error ({exc}); checking fallback...")
                    break

                if attempt == 4:
                    print(f"{model} exhausted all 5 retry attempts.")
                    break

                delay = min(60.0, (2.0 ** attempt) * 2.0) + random.uniform(0.5, 2.0)
                print(
                    f"{model} request issue ({type(exc).__name__}: {code or exc}); "
                    f"retrying in {delay:.1f}s ({attempt + 1}/5)..."
                )
                time.sleep(delay)

        if model_index < len(models) - 1:
            print(
                f"{model} unavailable or exhausted; trying fallback model "
                f"{models[model_index + 1]}..."
            )

    raise SystemExit(f"Gemini classification failed after attempting all configured models: {last_error}")


# ---------------------------------------------------------------------------
# Evidence repair
# ---------------------------------------------------------------------------

def repair_close_evidence(text: str, review_text: str):
    """Return the best-matching source span when the model made a small text typo.

    Scans all word-aligned windows of the same length as `text` and scores them
    with SequenceMatcher.  Returns the unique highest-scoring candidate if it
    scores >= 0.92, otherwise None.

    Candidates are ranked by similarity score so a clear best match is
    returned when the top score is unique (no tie).
    """
    words = text.split()
    if not words:
        return None

    # best_by_text: deduplicate spans that appear at multiple positions,
    # keeping the highest score seen for each unique text value.
    best_by_text: dict = {}
    tokens = list(re.finditer(r"\S+", review_text))
    for start_index in range(len(tokens) - len(words) + 1):
        start = tokens[start_index].start()
        end = tokens[start_index + len(words) - 1].end()
        candidate = review_text[start:end]
        ratio = SequenceMatcher(None, text, candidate).ratio()
        if ratio >= 0.92:
            best_by_text[candidate] = max(best_by_text.get(candidate, 0.0), ratio)

    if not best_by_text:
        return None

    # Sort unique candidates by descending score.
    ranked = sorted(best_by_text.items(), key=lambda x: x[1], reverse=True)
    top_candidate, top_score = ranked[0]

    # Return only when there is a single unambiguous winner at the top score.
    if len(ranked) == 1 or ranked[1][1] < top_score:
        return top_candidate
    return None


# ---------------------------------------------------------------------------
# First pass
# ---------------------------------------------------------------------------
results = generate_results(request)

expected_ids = [str(review["review_id"]) for review in reviews]
actual_ids = [str(result.get("review_id")) for result in results]

# Duplicate ID check
if len(actual_ids) != len(set(actual_ids)):
    raise SystemExit("Gemini returned duplicate review IDs")

# ID set mismatch — attempt recovery
if set(actual_ids) != set(expected_ids):
    results_by_id = {str(result["review_id"]): result for result in results}
    missing_ids = set(expected_ids) - set(actual_ids)
    unexpected_ids = set(actual_ids) - set(expected_ids)

    if len(missing_ids) == len(unexpected_ids) == 1:
        expected_id = next(iter(missing_ids))
        unexpected_id = next(iter(unexpected_ids))
        one_char_diff = (
            len(expected_id) == len(unexpected_id)
            and sum(
                exp != act
                for exp, act in zip(expected_id, unexpected_id)
            ) == 1
        )
        if one_char_diff:
            # Correct the single-character typo in the result dict
            result = results_by_id.pop(unexpected_id)
            result["review_id"] = expected_id
            results_by_id[expected_id] = result
            print(
                f"Corrected one-character review ID typo: {unexpected_id} -> {expected_id}"
            )
            # Note: actual_ids is intentionally not updated here; results is
            # rebuilt from results_by_id on the shared path below.
        else:
            raise SystemExit(
                "Gemini returned unexpected review IDs: "
                f"missing={sorted(missing_ids)[:3]}, "
                f"unexpected={sorted(unexpected_ids)[:3]}"
            )
    else:
        raise SystemExit(
            "Gemini returned unexpected review IDs: "
            f"missing={sorted(missing_ids)[:3]}, "
            f"unexpected={sorted(unexpected_ids)[:3]}"
        )
    # Rebuild results in expected order from the (now-corrected) dict
    results = [results_by_id[review_id] for review_id in expected_ids]

elif actual_ids != expected_ids:
    # IDs are correct but order differs — reorder to match input
    results_by_id = {str(result["review_id"]): result for result in results}
    results = [results_by_id[review_id] for review_id in expected_ids]

# ---------------------------------------------------------------------------
# Normalise sentiment casing
# ---------------------------------------------------------------------------
SENTIMENT_MAP = {
    "NEGATIVE": "negative",
    "MIXED":    "mixed",
    "NEUTRAL":  "neutral",
    "POSITIVE": "positive",
    "UNCLEAR":  "unclear",
}


def normalize_sentiments(results: list) -> None:
    for result in results:
        sentiment = result.get("sentiment")
        if isinstance(sentiment, str):
            result["sentiment"] = SENTIMENT_MAP.get(sentiment.upper(), sentiment)


normalize_sentiments(results)

# ---------------------------------------------------------------------------
# Evidence validation — regenerate if any evidence span is not verbatim
# ---------------------------------------------------------------------------
review_text_by_id = {
    str(review["review_id"]): review.get("review_text", "") for review in reviews
}
validator = Draft202012Validator(schema)

invalid_evidence = [
    (result["review_id"], item["text"])
    for result in results
    for item in result.get("evidence", [])
    if item["text"] not in review_text_by_id[result["review_id"]]
]

if invalid_evidence:
    correction = (
        request
        + "\n\nCORRECTION REQUIRED: The previous response contained invalid "
        "evidence. Regenerate the entire results array. Every evidence.text "
        "must be copied exactly and contiguously from the matching "
        "review_text, including spelling, punctuation, spaces, and emoji. "
        "Do not paraphrase or correct typos in the review. Invalid examples: "
        + json.dumps(invalid_evidence[:5], ensure_ascii=False)
    )
    print(
        f"Invalid evidence detected for {len(invalid_evidence)} item(s); "
        "regenerating response..."
    )
    results = generate_results(correction)
    normalize_sentiments(results)

    actual_ids = [str(result.get("review_id")) for result in results]
    if len(actual_ids) != len(set(actual_ids)) or set(actual_ids) != set(expected_ids):
        raise SystemExit("Evidence regeneration returned unexpected review IDs")
    results_by_id = {str(result["review_id"]): result for result in results}
    results = [results_by_id[review_id] for review_id in expected_ids]

    # Check again after regeneration
    invalid_evidence = [
        (result["review_id"], item["text"])
        for result in results
        for item in result.get("evidence", [])
        if item["text"] not in review_text_by_id[result["review_id"]]
    ]

    if invalid_evidence:
        # Try to repair minor typos with fuzzy matching
        repaired = 0
        for result in results:
            review_text = review_text_by_id[result["review_id"]]
            for item in result.get("evidence", []):
                if item["text"] not in review_text:
                    replacement = repair_close_evidence(item["text"], review_text)
                    if replacement is not None:
                        item["text"] = replacement
                        repaired += 1

        # Final check after repair
        invalid_evidence = [
            (result["review_id"], item["text"])
            for result in results
            for item in result.get("evidence", [])
            if item["text"] not in review_text_by_id[result["review_id"]]
        ]
        if invalid_evidence:
            raise SystemExit(
                f"Invalid evidence after regeneration and repair: "
                f"{invalid_evidence[0][1]!r}"
            )
        if repaired:
            print(f"Repaired {repaired} typo-level evidence span(s) from source text")

# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------
for result in results:
    errors = list(validator.iter_errors(result))
    if errors:
        raise SystemExit(
            f"Schema validation failed for {result['review_id']}: "
            f"{errors[0].message}"
        )

# ---------------------------------------------------------------------------
# Write output
# ---------------------------------------------------------------------------
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(
    "\n".join(
        json.dumps(result, ensure_ascii=False, separators=(",", ":"))
        for result in results
    ) + "\n",
    encoding="utf-8",
)
print(f"Saved {len(results)} labels to {OUTPUT}")
