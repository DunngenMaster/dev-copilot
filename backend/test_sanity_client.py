"""Manual test runner for the Sanity client."""

import logging
import os
from pprint import pprint

from app.services.sanity_client import create_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SAMPLE_DATA = {
    "repo": "test/repo",
    "team": "qa",
    "score": 88,
    "bottlenecks": ["review delay", "stale issues"],
    "sop": "Test SOP from integration",
    "metrics": {"example": True},
    "version": 1,
    "createdAt": "2025-11-21T00:00:00Z",
}


def run_test() -> None:
    """Invoke create_report with sample data and print the outcome."""
    report_url = create_report(SAMPLE_DATA)
    status_code = 200 if report_url and report_url != "#" else 500

    print("=== Sanity Client Test ===")
    print(f"Status Code: {status_code}")
    print(f"Report URL: {report_url}")

    expected_prefix = os.getenv("SANITY_REPORT_BASE_URL", "").rstrip("/")
    if status_code == 200 and expected_prefix and report_url.startswith(expected_prefix):
        logging.info("Sanity client success: report stored at %s", report_url)
    elif report_url == "#":
        logging.error("Sanity client failed: missing configuration or API error")
    else:
        logging.warning("Sanity client returned unexpected URL: %s", report_url)

    pprint({"report_url": report_url, "status_code": status_code})


if __name__ == "__main__":
    run_test()
