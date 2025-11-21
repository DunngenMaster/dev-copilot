from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn


# Pydantic models
class HealthResponse(BaseModel):
    status: str


class AnalyzeWorkflowRequest(BaseModel):
    repo: str
    team: str
    window_days: int = 14


class AnalyzeWorkflowResponse(BaseModel):
    repo: str
    team: str
    window_days: int
    message: str


# FastAPI app
app = FastAPI(
    title="Dev-Copilot API",
    description="Autonomous AI Operations Consultant for engineering teams",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="ok")


@app.post("/analyze-workflow", response_model=AnalyzeWorkflowResponse)
async def analyze_workflow(request: AnalyzeWorkflowRequest):
    """Analyze team workflow - stub implementation"""
    return AnalyzeWorkflowResponse(
        repo=request.repo,
        team=request.team,
        window_days=request.window_days,
        message="stub"
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)