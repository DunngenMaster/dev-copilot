"""
Workflow data collection services.

This module contains functions for collecting workflow metrics from various sources
including GitHub, Jira, and Slack integrations.
"""

import random
from typing import Dict, Any, List


def run_collection(repo: str, team: str, window_days: int) -> Dict[str, Any]:
    """
    Collect workflow metrics from GitHub, Jira, and Slack.
    
    This is a stub implementation that returns fake metrics for development.
    In production, this would orchestrate calls to GitHub API, Jira API, and Slack API
    to collect real workflow data.
    
    Args:
        repo: Repository identifier (e.g., "owner/repository")
        team: Team name or identifier
        window_days: Number of days to analyze (lookback window)
        
    Returns:
        Dict containing metrics organized by source:
        - prs: Pull request metrics from GitHub
        - issues: Issue metrics from Jira
        - slack: Communication metrics from Slack
    """
    
    # Generate deterministic but varied fake data based on inputs
    # This ensures consistent results for the same inputs during development
    seed = hash(f"{repo}|{team}|{window_days}") % 1000
    random.seed(seed)
    
    # PR metrics (GitHub data)
    base_review_time = random.uniform(20.0, 60.0)
    prs = {
        "avg_time_to_first_review_h": round(base_review_time, 1),
        "avg_time_to_merge_h": round(base_review_time * 1.8 + random.uniform(10, 30), 1),
        "pct_prs_no_first_review_36h": round(random.uniform(0.2, 0.6), 2),
        "avg_reviews_per_pr": round(random.uniform(1.2, 2.5), 1)
    }
    
    # Issue metrics (Jira data)
    issues = {
        "unassigned_24h_rate": round(random.uniform(0.1, 0.4), 2),
        "reopen_rate": round(random.uniform(0.05, 0.25), 2),
        "stale_7d_ratio": round(random.uniform(0.15, 0.45), 2)
    }
    
    # Slack metrics (communication data)
    blocker_mentions = random.randint(5, 25)
    slack = {
        "blocker_mentions": blocker_mentions,
        "top_terms": _generate_top_terms(),
        "sample_permalinks": [],  # Empty for privacy/stub implementation
        "lookback_days": window_days
    }
    
    return {
        "prs": prs,
        "issues": issues,
        "slack": slack
    }


def _generate_top_terms() -> List[str]:
    """Generate fake top discussion terms for Slack analysis."""
    term_pool = [
        "stuck", "review", "blocked", "help", "urgent", "deploy", 
        "bug", "test", "merge", "conflict", "revert", "hotfix",
        "approval", "meeting", "demo", "release", "rollback"
    ]
    
    # Return 2-4 random terms
    num_terms = random.randint(2, 4)
    return random.sample(term_pool, num_terms)


def compute_score(metrics: dict, weights: dict = None) -> int:
    """
    Calculate workflow health score using the deterministic scoring algorithm.
    
    Formula:
    score = 100 
      - 10 * min(avg_time_to_first_review_h/24, 3)
      - 30 * unassigned_24h_rate
      - 25 * reopen_rate  
      - 20 * stale_7d_ratio * 0.8
    
    Args:
        metrics: Dictionary containing workflow metrics from run_collection()
        weights: Optional custom weights (not used in this implementation - reserved for future)
        
    Returns:
        Health score between 0-100 (integer)
    """
    prs = metrics.get("prs", {})
    issues = metrics.get("issues", {})
    
    # Extract metrics with safe defaults
    avg_time_to_first_review_h = prs.get("avg_time_to_first_review_h", 0.0)
    unassigned_24h_rate = issues.get("unassigned_24h_rate", 0.0)
    reopen_rate = issues.get("reopen_rate", 0.0)
    stale_7d_ratio = issues.get("stale_7d_ratio", 0.0)
    
    # Calculate score using exact formula
    score = 100 \
        - 10 * min(avg_time_to_first_review_h / 24, 3) \
        - 30 * unassigned_24h_rate \
        - 25 * reopen_rate \
        - 20 * stale_7d_ratio * 0.8
    
    # Clamp to [0, 100] and return as integer
    return max(0, min(100, int(round(score))))


def calculate_health_score(metrics: Dict[str, Any]) -> int:
    """
    Calculate workflow health score from collected metrics.
    
    DEPRECATED: Use compute_score() instead. This function uses the old algorithm.
    
    Args:
        metrics: Dictionary containing workflow metrics from run_collection()
        
    Returns:
        Health score between 0-100
    """
    # Delegate to the new compute_score function
    return compute_score(metrics)