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

# Import Redis Stack vector functionality
from services.redis_vector import ensure_index, upsert_workflow_doc, knn_search, is_semantic_enabled
from utils.embeddings import embed_snapshot, to_f32bytes
from datetime import datetime
import time

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


@app.on_event("startup")
async def startup_event():
    """Initialize Redis Stack vector index on startup"""
    try:
        ensure_index()
        logger.info("Redis Stack vector index initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize vector index: {e}")
        # Continue startup even if index fails - will handle gracefully


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
    """Analyze team workflow with Redis Cloud semantic vector caching"""
    
    # Generate vector embedding from workflow parameters
    logger.info(f"Processing workflow analysis: {request.repo}|{request.team}|{request.window_days}")
    
    try:
        # Create deterministic vector embedding
        vector = embed_snapshot(request.repo, request.team, request.window_days, dims=settings.vector_dims)
        vector_bytes = to_f32bytes(vector)
        
        # Check if semantic cache is enabled
        semantic_enabled = is_semantic_enabled() and settings.semantic_cache.lower() == "on"
        logger.info(f"Semantic cache enabled = {semantic_enabled}")
        
        hit = None
        if semantic_enabled:
            # Search for similar workflow documents
            hit = knn_search(vector_bytes, k=3, min_sim=0.80)
        
        if hit:
            logger.info(f"KNN search similarity={hit['similarity']:.2f}")
            logger.info("CACHE HIT")
            
            # Return cached result with HIT status and similarity
            return AnalyzeWorkflowResponse(
                score=hit["score"],
                bottlenecks=[f"Cached analysis (similarity: {hit['similarity']:.2f})"],
                sop=None,
                sop_preview=hit["sop"],
                report_url="#",
                cache_status="HIT",
                partial=False
            )
        
        # Cache miss - run full analysis
        logger.info("CACHE MISS")
        
        # Collect workflow metrics
        metrics = run_collection(request.repo, request.team, request.window_days)
        
        # Calculate health score
        score = compute_score(metrics)
        
        # Generate bottlenecks from metrics
        bottlenecks = _generate_bottlenecks_from_metrics(metrics)
        
        # Generate SOP preview
        sop_preview = _generate_sop_preview(metrics, score)
        
        # Store in vector index for future similarity searches (if semantic cache enabled)
        if semantic_enabled:
            try:
                doc_payload = {
                    "repo": request.repo,
                    "team": request.team,
                    "score": score,
                    "sop": sop_preview
                }
                
                # Create unique document key with timestamp
                timestamp = int(time.time())
                doc_key = f"wfdoc:{request.repo}:{request.team}:{request.window_days}:{timestamp}"
                
                # Store document with vector embedding
                upsert_workflow_doc(doc_key, doc_payload, vector_bytes)
                logger.info(f"Stored new workflow document: {doc_key}")
                
            except Exception as e:
                logger.warning(f"Failed to cache workflow document: {e}")
                # Continue without caching
        else:
            logger.info("Semantic cache disabled - document not stored for vector search")
        
        # Return analysis result
        return AnalyzeWorkflowResponse(
            score=score,
            bottlenecks=bottlenecks,
            sop=None,
            sop_preview=sop_preview,
            report_url="#",
            cache_status="MISS",
            partial=False
        )
        
    except Exception as e:
        logger.error(f"Error in workflow analysis: {e}")
        
        # Fallback to basic response
        return AnalyzeWorkflowResponse(
            score=None,
            bottlenecks=None,
            sop=None,
            sop_preview=None,
            report_url=None,
            cache_status="ERROR",
            partial=True,
            message="Analysis temporarily unavailable",
            echo=request
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host=settings.api_host, 
        port=settings.api_port, 
        reload=True,
        log_level=settings.log_level.lower()
    )