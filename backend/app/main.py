from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
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
from services.redis_vector import ensure_index, upsert_workflow_doc, knn_search, is_semantic_enabled, rag_retrieve
from services.sanity_client import create_report
from services.anthropic_client import generate_sop
from utils.embeddings import embed_snapshot, to_f32bytes
from datetime import datetime
import time

# Import workflow services
from services.collection import run_collection, compute_score
from services.postman_client import run_collection_or_stub


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
    # Flags for frontend
    semantic_enabled: Optional[bool] = None
    postman_mode: Optional[str] = None
    similarity: Optional[float] = None
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
            
            postman_mode = "live" if os.getenv("POSTMAN_API_KEY") and os.getenv("POSTMAN_RUNNER_URL") else "stub"
            
            # Return cached result with HIT status and similarity
            return AnalyzeWorkflowResponse(
                score=hit["score"],
                bottlenecks=[f"Cached analysis (similarity: {hit['similarity']:.2f})"],
                sop=None,
                sop_preview=hit["sop"],
                report_url="#",
                cache_status="HIT",
                partial=False,
                semantic_enabled=semantic_enabled,
                postman_mode=postman_mode,
                similarity=hit["similarity"]
            )
        
        # Cache miss - run full analysis
        logger.info("CACHE MISS")
        
        # Collect workflow metrics via Postman when available
        metrics = run_collection_or_stub(request.repo, request.team, request.window_days)
        # Log mode based on environment availability
        postman_mode = "live" if os.getenv("POSTMAN_API_KEY") and os.getenv("POSTMAN_RUNNER_URL") else "stub"
        logger.info("POSTMAN mode: %s", postman_mode)
        
        # Calculate health score
        score = compute_score(metrics)
        
        # Try to generate bottlenecks and SOP using Claude with RAG context
        bottlenecks = []
        sop_full = None
        sop_preview = None
        summary = None
        
        try:
            # Retrieve similar SOPs for RAG context
            rag_docs = rag_retrieve(vector_bytes, k=5)
            logger.info(f"RAG retrieve: found {len(rag_docs)} context documents")
            
            # Generate bottlenecks and SOP using Claude
            claude_result = generate_sop(metrics, rag_docs)
            bottlenecks = claude_result.get("bottlenecks", [])[:5]  # Limit to top 5
            sop_full = claude_result.get("sop", "")
            summary = claude_result.get("summary", "")
            
            # Use summary as preview if available, otherwise truncate full SOP
            if summary:
                sop_preview = summary
            elif sop_full:
                sop_preview = sop_full[:500] + "..." if len(sop_full) > 500 else sop_full
            
            logger.info("CLAUDE reasoning: generated bottlenecks and SOP")
            
        except Exception as e:
            logger.warning(f"Claude reasoning failed: {e}")
            # Fallback to rule-based bottlenecks
            bottlenecks = _generate_bottlenecks_from_metrics(metrics)
            sop_preview = _generate_sop_preview(metrics, score)
            logger.info("Fallback to rule-based bottleneck generation")
        
        # Use sop_full for storage if available, otherwise use preview
        sop_for_storage = sop_full if sop_full else sop_preview
        
        # Use sop_full for storage if available, otherwise use preview
        sop_for_storage = sop_full if sop_full else sop_preview
        
        # Create Sanity report for this analysis
        report_payload = {
            "repo": request.repo,
            "team": request.team,
            "score": score,
            "bottlenecks": bottlenecks,
            "sop": sop_for_storage,
            "metrics": metrics,
            "version": 1,
            "createdAt": datetime.utcnow().isoformat()
        }
        report_url = create_report(report_payload)
        if report_url and report_url != "#":
            report_id = report_url.rstrip("/").split("/")[-1]
            logger.info("SANITY saved id=%s", report_id)
        else:
            logger.warning("SANITY report creation skipped")

        # Store in vector index for future similarity searches (if semantic cache enabled)
        if semantic_enabled:
            try:
                doc_payload = {
                    "repo": request.repo,
                    "team": request.team,
                    "score": score,
                    "sop": sop_for_storage
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
            report_url=report_url,
            cache_status="MISS",
            partial=False,
            semantic_enabled=semantic_enabled,
            postman_mode=postman_mode
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
            echo=request,
            semantic_enabled=False,
            postman_mode="unknown"
        )


@app.get("/test-sanity")
async def test_sanity_integration():
    """Temporary route to verify Sanity connectivity."""
    sample_payload = {
        "repo": "test/repo",
        "team": "qa",
        "score": 88,
        "bottlenecks": ["review delay", "stale issues"],
        "sop": "Test SOP from integration",
        "metrics": {"example": True},
        "version": 1,
        "createdAt": "2025-11-21T00:00:00Z"
    }

    report_url = create_report(sample_payload)
    status_code = 200 if report_url and report_url != "#" else 500
    base_url = os.getenv("SANITY_REPORT_BASE_URL", "").rstrip("/")

    if status_code == 200 and base_url and report_url.startswith(base_url):
        logger.info("Sanity test success: %s", report_url)
    elif report_url == "#":
        logger.error("Sanity test failed: configuration or API issue")
    else:
        logger.warning("Sanity test returned unexpected URL: %s", report_url)

    return {"report_url": report_url, "status_code": status_code}


if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host=settings.api_host, 
        port=settings.api_port, 
        reload=True,
        log_level=settings.log_level.lower()
    )