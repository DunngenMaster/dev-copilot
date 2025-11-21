"""Sanity API client helpers."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)

SANITY_API_VERSION = "v2021-10-21"


def create_report(data: Dict[str, Any]) -> str:
    """Create a workflow report document in Sanity and return its URL."""
    project_id = os.getenv("SANITY_PROJECT_ID")
    dataset = os.getenv("SANITY_DATASET")
    token = os.getenv("SANITY_TOKEN")
    base_url = os.getenv("SANITY_REPORT_BASE_URL", "").rstrip("/") if os.getenv("SANITY_REPORT_BASE_URL") else ""

    if not all([project_id, dataset, token]):
        logger.warning("SANITY configuration missing - skipping report creation")
        return "#"

    api_url = f"https://{project_id}.api.sanity.io/{SANITY_API_VERSION}/data/mutate/{dataset}"
    payload = {
        "mutations": [
            {
                "create": {
                    "_type": "workflowReport",
                    **data,
                }
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        body = response.json()
        results = body.get("results") or []
        created = results[0] if results else {}
        doc_id = created.get("id") or created.get("_id")
        if not doc_id:
            raise ValueError("Sanity response missing document id")

        logger.info("SANITY saved id=%s", doc_id)
        if base_url:
            return f"{base_url}/{doc_id}"
        return f"{api_url}/{doc_id}"
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("SANITY report creation failed: %s", exc)
        return "#"
