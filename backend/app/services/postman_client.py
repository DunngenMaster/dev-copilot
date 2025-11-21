"""Postman integration client for workflow metrics."""

from __future__ import annotations

import logging
import os
from typing import Dict, Any

import requests

logger = logging.getLogger(__name__)

POSTMAN_API_KEY = os.getenv("POSTMAN_API_KEY")
POSTMAN_RUNNER_URL = os.getenv("POSTMAN_RUNNER_URL")


def run_collection_or_stub(repo: str, team: str, window_days: int) -> Dict[str, Any]:
    """Run remote Postman collection if configured, else return stub metrics."""
    if POSTMAN_API_KEY and POSTMAN_RUNNER_URL:
        try:
            payload = {
                "repo": repo,
                "team": team,
                "window_days": window_days
            }
            headers = {
                "X-Api-Key": POSTMAN_API_KEY,
                "Content-Type": "application/json"
            }
            resp = requests.post(POSTMAN_RUNNER_URL, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            logger.info("POSTMAN_RUNNER: success %s", list(data.keys()))
            return data
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("POSTMAN_RUNNER failed, using stub: %s", exc)

    logger.info("POSTMAN_RUNNER: stub mode active")
    return {
        "prs": {
            "avg_time_to_first_review_h": 30.0,
            "avg_time_to_merge_h": 50.0,
            "pct_prs_no_first_review_36h": 0.4,
            "avg_reviews_per_pr": 1.6
        },
        "issues": {
            "unassigned_24h_rate": 0.25,
            "reopen_rate": 0.18,
            "stale_7d_ratio": 0.30
        },
        "slack": {
            "blocker_mentions": 12,
            "top_terms": ["stuck", "review", "blocked"],
            "sample_permalinks": [],
            "lookback_days": window_days
        }
    }
