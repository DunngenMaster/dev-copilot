"""Analytics dashboard endpoints for workflow insights."""

from fastapi import APIRouter
from typing import Dict, Any, List
from services.redis_vector import get_client
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard/summary")
async def get_dashboard_summary() -> Dict[str, Any]:
    """Get aggregate workflow analysis statistics."""
    client = get_client()
    
    try:
        # Get all workflow documents
        keys = client.keys("wfdoc:*")
        
        if not keys:
            return {
                "total_analyses": 0,
                "avg_score": 0,
                "top_teams": [],
                "top_repos": [],
                "common_bottlenecks": []
            }
        
        scores = []
        teams = {}
        repos = {}
        bottlenecks = {}
        
        for key in keys:
            doc = client.hgetall(key)
            if not doc:
                continue
            
            # Parse document fields
            score = int(doc.get(b"score", b"0"))
            team = doc.get(b"team", b"").decode()
            repo = doc.get(b"repo", b"").decode()
            
            scores.append(score)
            teams[team] = teams.get(team, 0) + 1
            repos[repo] = repos.get(repo, 0) + 1
        
        # Calculate aggregates
        avg_score = sum(scores) / len(scores) if scores else 0
        top_teams = sorted(teams.items(), key=lambda x: x[1], reverse=True)[:5]
        top_repos = sorted(repos.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_analyses": len(keys),
            "avg_score": round(avg_score, 1),
            "top_teams": [{"name": t[0], "count": t[1]} for t in top_teams],
            "top_repos": [{"name": r[0], "count": r[1]} for r in top_repos],
            "score_distribution": {
                "excellent": sum(1 for s in scores if s >= 90),
                "good": sum(1 for s in scores if 70 <= s < 90),
                "needs_improvement": sum(1 for s in scores if s < 70)
            }
        }
        
    except Exception as e:
        logger.error(f"Dashboard summary failed: {e}")
        return {
            "error": str(e),
            "total_analyses": 0,
            "avg_score": 0
        }


@router.get("/dashboard/trends")
async def get_workflow_trends(days: int = 30) -> Dict[str, Any]:
    """Get workflow score trends over time."""
    # This would query Sanity for time-series data
    return {
        "period_days": days,
        "trend": "improving",
        "score_change": +8,
        "data_points": [
            {"date": "2025-11-01", "score": 73},
            {"date": "2025-11-08", "score": 76},
            {"date": "2025-11-15", "score": 79},
            {"date": "2025-11-21", "score": 81}
        ]
    }
