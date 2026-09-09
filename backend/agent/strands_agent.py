import os
import asyncio
from typing import Dict, Any

import boto3
from strands import Agent
from strands.models import BedrockModel

from backend.tools import ALL_TOOLS

def is_bedrock_available() -> bool:
    """
    Checks if Bedrock is configured and accessible.
    We try to establish a boto3 client session and check for model access.
    """
    region = os.environ.get("AWS_REGION", "us-east-1")
    # Check if we have standard keys or profile
    has_keys = bool(os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"))
    has_profile = bool(os.environ.get("AWS_PROFILE"))
    
    if not (has_keys or has_profile or os.environ.get("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")):
        return False
        
    try:
        # Create bedrock runtime client to test connection
        client = boto3.client("bedrock", region_name=region)
        client.list_custom_models(maxResults=1)
        return True
    except Exception:
        return False

async def run_live_investigation(obligation_id: str) -> Dict[str, Any]:
    """Runs a live Strands Agent loop on AWS Bedrock using Claude 3.5 Sonnet."""
    region = os.environ.get("AWS_REGION", "us-east-1")
    model_id = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0")
    
    model = BedrockModel(model_id=model_id, region_name=region)
    system_prompt = (
        "You are ClauseRunner's autonomous contract operations agent.\n"
        "Your mission is to investigate post-signature obligations and resolve them safely.\n"
        "Follow these steps:\n"
        "1. Inspect the obligation and get the source contract & clauses.\n"
        "2. List and load the attached evidence artifacts.\n"
        "3. Evaluate compliance. ALWAYS use the deterministic tool 'evaluate_numeric_threshold' "
        "or 'calculate_deadline' rather than calculating metrics yourself.\n"
        "4. Based on the evaluation, if there is a breach, propose the exact remedy action "
        "using 'propose_action'.\n"
        "5. If approval is required, submit an approval request using 'request_approval'.\n"
        "Never show any raw chain-of-thought or internal system parameters.\n"
    )
    
    agent = Agent(
        model=model,
        tools=ALL_TOOLS,
        system_prompt=system_prompt,
        name="ClauseRunner-Operations-Agent"
    )
    
    prompt = f"Please initiate a complete investigation and operations cycle for obligation ID: '{obligation_id}'."
    result = await agent.invoke_async(prompt)
    return {
        "text": str(result),
        "stop_reason": result.stop_reason,
        "metrics": result.metrics.to_dict() if hasattr(result.metrics, "to_dict") else {}
    }

async def run_investigation(obligation_id: str) -> Dict[str, Any]:
    """Orchestrator that routes to either real Bedrock or our Mock simulator."""
    if is_bedrock_available():
        return await run_live_investigation(obligation_id)
    else:
        from backend.agent.mock_agent import run_mock_investigation
        return await run_mock_investigation(obligation_id)
