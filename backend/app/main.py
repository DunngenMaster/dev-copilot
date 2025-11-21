from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import logging

# Import configuration
from core.config import get_settings

# Get application settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import cache functionality
try:
    from integrations.redis.cache import semantic_cache, embed_snapshot
    CACHE_AVAILABLE = True
except ImportError:
    logger.warning("Cache module not available - running without cache")
    CACHE_AVAILABLE = False
    
    # Fallback embed function if cache module not available
    import hashlib
    
    def embed_snapshot(repo: str, team: str, window_days: int) -> List[float]:
        """Fallback embed function when cache module not available"""
        input_string = f"{repo}|{team}|{window_days}"
        hash_bytes = hashlib.sha256(input_string.encode('utf-8')).digest()
        
        vector = []
        for i in range(32):
            byte_idx = (i * 4) % len(hash_bytes)
            byte_slice = hash_bytes[byte_idx:byte_idx + 4]
            
            if len(byte_slice) < 4:
                byte_slice += b'\x00' * (4 - len(byte_slice))
            
            int_val = int.from_bytes(byte_slice, byteorder='big')
            float_val = int_val / (2**32 - 1)
            
            vector.append(float_val)
        
        return vector

# Import workflow services
from services.collection import run_collection, compute_score


# Pydantic models
class HealthResponse(BaseModel):
    status: str


class AnalyzeWorkflowRequest(BaseModel):
    repo: str
    team: str
    window_days: int = 14


class AnalyzeWorkflowResponse(BaseModel):
    # For cache HIT
    score: Optional[int] = None
    bottlenecks: Optional[List[str]] = None
    sop: Optional[str] = None
    sop_preview: Optional[str] = None
    report_url: Optional[str] = None
    cache_status: str
    partial: Optional[bool] = None
    # For cache MISS
    message: Optional[str] = None
    echo: Optional[AnalyzeWorkflowRequest] = None


# FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Autonomous AI Operations Consultant for engineering teams",
    version=settings.app_version
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="ok")


def _generate_bottlenecks_from_metrics(metrics: Dict[str, Any]) -> List[str]:
    """Generate bottleneck descriptions from workflow metrics."""
    bottlenecks = []
    
    prs = metrics.get("prs", {})
    issues = metrics.get("issues", {})
    
    # PR review time bottleneck
    avg_review_time = prs.get("avg_time_to_first_review_h", 0)
    if avg_review_time > 36:
        pct_slow = prs.get("pct_prs_no_first_review_36h", 0) * 100
        bottlenecks.append(f"{pct_slow:.0f}% of PRs wait >{avg_review_time:.0f}h for first review")
    
    # Issue assignment bottleneck
    unassigned_rate = issues.get("unassigned_24h_rate", 0)
    if unassigned_rate > 0.15:  # 15% threshold
        bottlenecks.append(f"{unassigned_rate:.0%} of issues remain unassigned after 24h")
    
    # Issue reopen bottleneck
    reopen_rate = issues.get("reopen_rate", 0)
    if reopen_rate > 0.10:  # 10% threshold
        bottlenecks.append(f"{reopen_rate:.0%} issue reopen rate exceeds 10% threshold")
    
    # Stale issues bottleneck
    stale_ratio = issues.get("stale_7d_ratio", 0)
    if stale_ratio > 0.25:  # 25% threshold
        bottlenecks.append(f"{stale_ratio:.0%} of issues are stale for 7+ days")
    
    # Fallback if no specific bottlenecks
    if not bottlenecks:
        bottlenecks.append("No significant bottlenecks detected in current metrics")
    
    return bottlenecks


def _generate_sop_preview(metrics: Dict[str, Any], score: int) -> str:
    """Generate a stub SOP preview based on metrics."""
    return f"""## Workflow Optimization SOP (Score: {score})

**Goals:**
- Reduce PR review time to <24h average
- Maintain <10% issue reopen rate
- Ensure >90% issue assignment within 24h

**Key Process Changes:**
1. Implement automated PR assignment rotation
2. Add review time SLA alerts at 24h mark
3. Weekly stale issue triage sessions
4. Quality gates before issue closure

**RACI Matrix:**
- Responsible: Engineering team leads
- Accountable: Engineering manager
- Consulted: Product owner
- Informed: QA team

*Full SOP available in detailed report.*"""


@app.post("/analyze-workflow", response_model=AnalyzeWorkflowResponse)
async def analyze_workflow(request: AnalyzeWorkflowRequest):
    """Analyze team workflow with semantic caching"""
    
    # Initialize cache if available
    if CACHE_AVAILABLE:
        semantic_cache.connect_from_env()
        
        # Generate vector for this workflow snapshot
        snapshot_vector = embed_snapshot(request.repo, request.team, request.window_days)
        
        logger.info(f"CACHE_CHECK: {request.repo}|{request.team}|{request.window_days}")
        
        # Search for similar cached results
        similar_results = semantic_cache.search_snapshot(
            vector=snapshot_vector,
            k=1,
            min_sim=0.80
        )
        
        if similar_results:
            logger.info(f"HIT: Found similar result with similarity {similar_results[0]['similarity']:.3f}")
            
            # Return cached result simulation
            return AnalyzeWorkflowResponse(
                score=72,
                bottlenecks=["stub"],
                sop="stub sop", 
                report_url="#",
                cache_status="HIT"
            )
    
    # Cache miss or cache not available - run full analysis
    logger.info("MISS: No similar results found or cache unavailable - running analysis")
    
    # Collect workflow metrics
    metrics = run_collection(request.repo, request.team, request.window_days)
    
    # Calculate health score
    score = compute_score(metrics)
    
    # Generate bottlenecks from metrics
    bottlenecks = _generate_bottlenecks_from_metrics(metrics)
    
    # Generate SOP preview
    sop_preview = _generate_sop_preview(metrics, score)
    
    # Cache the result if cache is available
    if CACHE_AVAILABLE:
        try:
            # Store in cache for future hits
            cache_payload = {
                "score": score,
                "bottlenecks": bottlenecks,
                "sop_preview": sop_preview,
                "metrics": metrics,
                "timestamp": logger.handlers[0].format(logger.makeRecord(
                    logger.name, logging.INFO, "", 0, "", (), None
                )) if logger.handlers else "unknown"
            }
            
            snapshot_vector = embed_snapshot(request.repo, request.team, request.window_days)
            cache_key = f"{request.repo}|{request.team}|{request.window_days}d"
            semantic_cache.upsert_snapshot(cache_key, snapshot_vector, cache_payload)
            
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")
    
    return AnalyzeWorkflowResponse(
        score=score,
        bottlenecks=bottlenecks,
        sop_preview=sop_preview,
        report_url="#",
        cache_status="MISS",
        partial=False
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host=settings.api_host, 
        port=settings.api_port, 
        reload=True,
        log_level=settings.log_level.lower()
    )