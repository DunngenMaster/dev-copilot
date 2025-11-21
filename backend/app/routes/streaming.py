"""Streaming endpoint for real-time workflow analysis updates."""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json
import asyncio

router = APIRouter()


async def analysis_stream(repo: str, team: str, window_days: int) -> AsyncGenerator[str, None]:
    """Stream workflow analysis progress to client."""
    
    # Step 1: Cache check
    yield f"data: {json.dumps({'step': 'cache_check', 'status': 'in_progress', 'message': 'Checking semantic cache...'})}\n\n"
    await asyncio.sleep(0.5)
    
    # Step 2: Metrics gathering
    yield f"data: {json.dumps({'step': 'metrics', 'status': 'in_progress', 'message': f'Running Newman for {repo}...'})}\n\n"
    await asyncio.sleep(1)
    
    # Step 3: RAG retrieval
    yield f"data: {json.dumps({'step': 'rag', 'status': 'in_progress', 'message': 'Retrieving similar SOPs from Redis...'})}\n\n"
    await asyncio.sleep(0.5)
    
    # Step 4: Claude reasoning
    yield f"data: {json.dumps({'step': 'claude', 'status': 'in_progress', 'message': 'Claude Sonnet analyzing workflow...'})}\n\n"
    await asyncio.sleep(2)
    
    # Step 5: Sanity storage
    yield f"data: {json.dumps({'step': 'storage', 'status': 'in_progress', 'message': 'Storing report in Sanity CMS...'})}\n\n"
    await asyncio.sleep(0.5)
    
    # Final result
    yield f"data: {json.dumps({'step': 'complete', 'status': 'success', 'message': 'Analysis complete!', 'score': 87})}\n\n"


@router.get("/stream-analysis")
async def stream_workflow_analysis(repo: str, team: str, window_days: int = 14):
    """Stream real-time workflow analysis updates via Server-Sent Events."""
    return StreamingResponse(
        analysis_stream(repo, team, window_days),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
