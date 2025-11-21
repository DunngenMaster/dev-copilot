"""Anthropic Claude client for SOP generation with retry logic."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List

import anthropic
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are OpsPilot's reasoning engine. Output valid JSON only.

Required JSON schema:
{
  "bottlenecks": ["string", "string", "string"],
  "sop": "single markdown-formatted string",
  "summary": "single string"
}

CRITICAL RULES:
- "sop" must be ONE string with markdown formatting (use \\n for newlines)
- Include sections: Goals, SLAs, Auto-triage rules, Assignment policy, PR review policy, QA gates, Weekly cadence, RACI
- bottlenecks: array of 3-5 measurable items from METRICS
- summary: 1-2 sentences
- Output ONLY valid JSON, no extra text"""


def _build_user_prompt(metrics: Dict[str, Any], rag_docs: List[str]) -> str:
    """Construct user prompt from metrics and RAG context."""
    import json
    pretty_metrics = json.dumps(metrics, indent=2)
    
    # Take up to 5 RAG docs
    rag_snippets = rag_docs[:5] if rag_docs else []
    joined_rag = "\n---\n".join(rag_snippets) if rag_snippets else "No RAG context available."
    
    return f"""METRICS:
{pretty_metrics}

RAG CONTEXT (top-k snippets):
{joined_rag}

Tasks:
1) Produce 3-5 bottlenecks (measurable, use METRICS).
2) Produce SOP (<700 words) with required sections and explicit SLAs in hours.
3) Produce a 1-2 sentence summary.

Return JSON ONLY."""


def _extract_json_from_text(text: str) -> Dict[str, Any]:
    """Extract first JSON object from potentially noisy text."""
    logger.debug(f"Raw Claude response (first 500 chars): {text[:500]}")
    
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON block with balanced braces
    brace_count = 0
    start_idx = text.find('{')
    if start_idx == -1:
        logger.error(f"No opening brace found in response")
        raise RuntimeError(f"Failed to extract valid JSON from Claude response")
    
    for i in range(start_idx, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                # Found matching closing brace
                json_str = text[start_idx:i+1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {e}")
                    logger.error(f"Problematic JSON: {json_str[:500]}")
                    raise RuntimeError(f"Failed to extract valid JSON from Claude response")
    
    logger.error(f"No matching closing brace found. Full response: {text}")
    raise RuntimeError(f"Failed to extract valid JSON from Claude response")


def _validate_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize Claude response structure."""
    if not isinstance(data, dict):
        raise RuntimeError("Claude response is not a dictionary")
    
    # Validate required keys with detailed logging
    bottlenecks = data.get("bottlenecks", [])
    sop = data.get("sop", "")
    summary = data.get("summary", "")
    
    logger.debug(f"Validating response: bottlenecks type={type(bottlenecks)}, sop type={type(sop)}, summary type={type(summary)}")
    
    if not isinstance(bottlenecks, list):
        raise RuntimeError(f"bottlenecks must be a list, got {type(bottlenecks).__name__}")
    
    # Handle sop as either string or dict (convert dict to formatted string)
    if isinstance(sop, dict):
        logger.info("Converting SOP from dict to formatted string")
        sop_parts = []
        for key, value in sop.items():
            if isinstance(value, dict):
                sop_parts.append(f"\n{key.upper()}:")
                for subkey, subvalue in value.items():
                    sop_parts.append(f"  - {subkey}: {subvalue}")
            else:
                sop_parts.append(f"\n{key.upper()}: {value}")
        sop = "\n".join(sop_parts)
    elif not isinstance(sop, str):
        logger.error(f"sop validation failed: type={type(sop).__name__}, value preview={str(sop)[:100]}")
        raise RuntimeError(f"sop must be a string or dict, got {type(sop).__name__}")
    
    if not isinstance(summary, str):
        raise RuntimeError(f"summary must be a string, got {type(summary).__name__}")
    
    # Normalize
    return {
        "bottlenecks": [str(b) for b in bottlenecks],
        "sop": str(sop),
        "summary": str(summary)
    }


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, anthropic.APIStatusError)),
    reraise=True
)
def _call_claude_with_retry(
    client: anthropic.Anthropic,
    model: str,
    system: str,
    user_prompt: str
) -> str:
    """Call Claude API with retry logic for transient failures."""
    response = client.messages.create(
        model=model,
        max_tokens=1200,
        temperature=0.2,
        system=system,
        messages=[
            {"role": "user", "content": user_prompt}
        ],
        timeout=httpx.Timeout(15.0)
    )
    
    # Extract text from response
    if not response.content:
        raise RuntimeError("Empty response from Claude")
    
    # Get first text block
    for block in response.content:
        if hasattr(block, 'text'):
            return block.text
    
    raise RuntimeError("No text content in Claude response")


def generate_sop(
    metrics: Dict[str, Any], 
    rag_docs: List[str], 
    model: str = "claude-3-haiku-20240307"
) -> Dict[str, Any]:
    """
    Generate SOP analysis using Claude with strict JSON parsing.
    
    Args:
        metrics: Workflow metrics dictionary
        rag_docs: List of RAG document snippets for context
        model: Claude model identifier
        
    Returns:
        Dictionary with keys: bottlenecks (list), sop (str), summary (str)
        
    Raises:
        RuntimeError: On API failure, timeout, or invalid response format
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable not set")
    
    logger.info("CLAUDE: request sent (model=%s)", model)
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        user_prompt = _build_user_prompt(metrics, rag_docs)
        
        # Call with retry logic
        response_text = _call_claude_with_retry(client, model, SYSTEM_PROMPT, user_prompt)
        
        # Parse and validate
        parsed = _extract_json_from_text(response_text)
        logger.debug(f"Parsed JSON keys: {list(parsed.keys())}, types: {[(k, type(v).__name__) for k, v in parsed.items()]}")
        
        validated = _validate_response(parsed)
        
        logger.info(
            "CLAUDE: response parsed (chars=%d, bottlenecks=%d)",
            len(validated["sop"]),
            len(validated["bottlenecks"])
        )
        
        return validated
        
    except anthropic.APIError as exc:
        logger.error("CLAUDE: error APIError: %s", str(exc))
        raise RuntimeError(f"Claude API error: {type(exc).__name__}") from exc
    except httpx.TimeoutException as exc:
        logger.error("CLAUDE: error TimeoutException: request timeout")
        raise RuntimeError("Claude request timeout") from exc
    except Exception as exc:
        logger.error("CLAUDE: error %s: %s", type(exc).__name__, str(exc))
        raise RuntimeError(f"Claude generation failed: {type(exc).__name__}") from exc
