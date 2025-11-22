"""Postman integration client for workflow metrics."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from typing import Dict, Any

logger = logging.getLogger(__name__)


def run_collection_or_stub(repo: str, team: str, window_days: int) -> Dict[str, Any]:
    """
    Run Newman CLI with local Postman collection, or return stub metrics.
    
    Args:
        repo: Repository in "owner/name" format
        team: Team name
        window_days: Number of days for analysis window
        
    Returns:
        Dictionary with metrics and postman_mode flag
    """
    # Parse repo into owner/name
    try:
        owner, name = repo.split("/", 1)
    except ValueError:
        logger.warning("[Postman] Invalid repo format '%s', using stub", repo)
        return _get_stub_metrics(window_days, "stub")
    
    # Determine mode based on environment variables
    postman_api_key = os.getenv("POSTMAN_API_KEY")
    postman_runner_url = os.getenv("POSTMAN_RUNNER_URL")
    github_token = os.getenv("GITHUB_TOKEN", "")
    
    mode = "live" if (postman_api_key or postman_runner_url) else "stub"
    
    # Try to run Newman CLI
    logger.info("[Postman] Running Newman for repo %s (mode: %s)", repo, mode)
    
    try:
        # Construct Newman command
        newman_cmd = [
            "newman",
            "run",
            "postman/collections/github_workflow.json",
            "-e",
            "postman/environments/local.json",
            "--env-var",
            f"gh_token={github_token}",
            "--env-var",
            f"repo_owner={owner}",
            "--env-var",
            f"repo_name={name}",
            "--env-var",
            f"window_days={window_days}",
            "--reporters",
            "cli"
        ]
        
        # Execute Newman with timeout
        cwd_path = os.path.join(os.path.dirname(__file__), "..", "..")
        logger.info("[Postman] Executing Newman from: %s", cwd_path)
        logger.debug("[Postman] Command: %s", " ".join(newman_cmd))
        
        result = subprocess.run(
            newman_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd_path
        )
        
        logger.info("[Postman] Newman exit code: %d", result.returncode)
        if result.stdout:
            logger.debug("[Postman] stdout: %s", result.stdout[:500])
        if result.stderr:
            logger.warning("[Postman] stderr: %s", result.stderr[:500])
        
        # Parse stdout for METRICS: line
        metrics = _parse_newman_output(result.stdout)
        
        if metrics:
            logger.info("[Postman] Parsed METRICS successfully")
            metrics["postman_mode"] = mode
            return metrics
        else:
            logger.warning("[Postman] METRICS: line not found in Newman output")
            
    except subprocess.TimeoutExpired:
        logger.warning("[Postman] Newman command timed out after 30s")
    except FileNotFoundError:
        logger.warning("[Postman] Newman CLI not found - install with: npm install -g newman")
    except Exception as exc:
        logger.warning("[Postman] Newman execution failed: %s", exc)
    
    # Fallback to stub
    logger.info("[Postman] fallback to stub metrics")
    return _get_stub_metrics(window_days, mode)


def _parse_newman_output(stdout: str) -> Dict[str, Any] | None:
    """
    Parse Newman CLI output for METRICS: JSON line.
    
    Args:
        stdout: Newman command output
        
    Returns:
        Parsed metrics dict or None if not found
    """
    for line in stdout.splitlines():
        if line.strip().startswith("METRICS:"):
            try:
                json_str = line.split("METRICS:", 1)[1].strip()
                return json.loads(json_str)
            except (json.JSONDecodeError, IndexError) as exc:
                logger.error("[Postman] Failed to parse METRICS JSON: %s", exc)
                return None
    return None


def _get_stub_metrics(window_days: int, mode: str) -> Dict[str, Any]:
    """
    Return stub metrics for testing.
    
    Args:
        window_days: Number of days for analysis
        mode: "live" or "stub"
        
    Returns:
        Dictionary with stub metrics
    """
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
        },
        "postman_mode": mode
    }
