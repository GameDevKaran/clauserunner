import os
import time
import asyncio
import boto3
from typing import Dict, Any
from botocore.config import Config
from strands import Agent
from strands.models import BedrockModel

from backend.domain.models import ActionStatus, ObligationStatus
from backend.repositories.db import get_repo
from backend.tools import INVESTIGATION_TOOLS

_bedrock_cache_status = None
_bedrock_cache_time = 0.0

def is_bedrock_available(force_fresh: bool = False) -> bool:
    """
    Checks if Bedrock is configured and accessible using a real bedrock-runtime Converse probe.
    Keeps a 60-second TTL cache for general health calls, but run_investigation overrides and forces fresh.
    """
    global _bedrock_cache_status, _bedrock_cache_time
    now = time.time()
    if not force_fresh and _bedrock_cache_status is not None and (now - _bedrock_cache_time) < 60.0:
        return _bedrock_cache_status

    region = os.environ.get("AWS_REGION", "us-east-1")
    model_id = os.environ.get("BEDROCK_MODEL_ID", "us.amazon.nova-2-lite-v1:0") or "us.amazon.nova-2-lite-v1:0"

    try:
        config = Config(
            connect_timeout=2.0,
            read_timeout=3.0,
            retries={"max_attempts": 0}
        )
        
        profile_name = os.environ.get("AWS_PROFILE")
        if profile_name:
            session = boto3.Session(profile_name=profile_name, region_name=region)
        else:
            session = boto3.Session(region_name=region)
            
        client = session.client("bedrock-runtime", region_name=region, config=config)
        
        # Real converse probe
        client.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": "Reply exactly OK."}]}],
            inferenceConfig={"maxTokens": 8, "temperature": 0.0}
        )
        _bedrock_cache_status = True
    except Exception as e:
        from backend.services.logger import logger
        logger.info(f"Bedrock runtime probe failed (access pending): {type(e).__name__} - {str(e)}")
        _bedrock_cache_status = False
        
    _bedrock_cache_time = time.time()
    return _bedrock_cache_status


async def run_live_investigation(obligation_id: str) -> Dict[str, Any]:
    """Runs a live Strands Agent loop on AWS Bedrock using Nova 2 Lite with strict limits."""
    from backend.services.investigation_prep import prepare_investigation_cycle
    obligation, active_action, err = prepare_investigation_cycle(obligation_id)
    if err:
        return {"error": err}

    if active_action:
        return {
            "mode": "bedrock",
            "text": "An existing consequential action is already awaiting human review.",
            "proposed_action_id": active_action.id,
            "reused_existing_action": True,
        }

    region = os.environ.get("AWS_REGION", "us-east-1")
    model_id = os.environ.get("BEDROCK_MODEL_ID", "us.amazon.nova-2-lite-v1:0") or "us.amazon.nova-2-lite-v1:0"

    botocore_config = Config(
        connect_timeout=5.0,
        read_timeout=25.0,
        retries={"max_attempts": 2}
    )

    model = BedrockModel(
        model_id=model_id,
        region_name=region,
        temperature=0.0,
        max_tokens=2048,
        streaming=False,
        boto_client_config=botocore_config
    )

    system_prompt = (
        "You are ClauseRunner's autonomous contract operations agent.\n"
        "Your mission is to investigate post-signature obligations and resolve them safely.\n"
        "Follow these strict operational rules:\n"
        "1. Retrieve the obligation first using 'get_obligation'.\n"
        "2. Retrieve the contract and clauses using 'get_contract' and 'list_contract_clauses'.\n"
        "3. Retrieve the evidence artifacts using 'list_evidence'.\n"
        "4. NEVER calculate SLA remedies, deadlines, or business numbers yourself.\n"
        "5. ALWAYS use the deterministic tools 'evaluate_sla_obligation' or 'calculate_deadline' for computations.\n"
        "6. If the evaluation shows a breach/issue, propose the action using 'propose_action'.\n"
        "7. Request human approval for the proposed action using 'request_approval'.\n"
        "8. STOP immediately once a proposed action has been submitted for approval.\n"
        "9. Never claim an action was executed. Human approval is strictly required.\n"
        "10. Return a short, operational, JSON-safe summary only. No raw chain-of-thought.\n"
    )

    agent = Agent(
        model=model,
        tools=INVESTIGATION_TOOLS,
        system_prompt=system_prompt,
        name="ClauseRunner-Operations-Agent"
    )

    prompt = f"Please initiate a complete investigation and operations cycle for obligation ID: '{obligation_id}'."
    
    try:
        result = await asyncio.wait_for(
            agent.invoke_async(
                prompt,
                limits={
                    "turns": 8,
                    "output_tokens": 3000,
                    "total_tokens": 12000,
                }
            ),
            timeout=35.0
        )
    except asyncio.TimeoutError:
        return {"error": "Live Agent investigation timed out after 35 seconds."}
    except Exception as e:
        return {"error": f"Live Agent loop failed: {str(e)}"}

    # Postcondition validation check
    repo = get_repo()
    updated_ob = repo.get_obligation(obligation_id)
    if not updated_ob:
        return {"error": "Obligation not found after investigation."}
        
    actions = repo.list_proposed_actions(obligation_id)
    active_actions = [a for a in actions if a.status in {ActionStatus.DRAFT, ActionStatus.APPROVED}]
    executed_actions = [a for a in actions if a.status == ActionStatus.EXECUTED]

    # Postconditions:
    # 1. obligation.status == APPROVAL_REQUIRED
    if updated_ob.status != ObligationStatus.APPROVAL_REQUIRED:
        from backend.services.logger import logger
        logger.error(f"Live Bedrock investigation failed postcondition: obligation status is '{updated_ob.status.value}' instead of 'approval_required'")
        return {"error": f"Investigation completed with incorrect final status: '{updated_ob.status.value}'."}

    # 2. exactly one active service-credit action exists for the current cycle
    if len(active_actions) != 1:
        from backend.services.logger import logger
        logger.error(f"Live Bedrock investigation failed postcondition: expected exactly 1 active action, found {len(active_actions)}")
        return {"error": f"Investigation completed with invalid number of proposed actions: {len(active_actions)}."}

    latest_action = active_actions[0]

    # 3. no action has been executed
    if executed_actions:
        from backend.services.logger import logger
        logger.error("Live Bedrock investigation failed postcondition: action was autonomously executed")
        return {"error": "Security Breach: Autonomous execution occurred without human approval."}

    # 4. one corresponding approval request exists
    approvals = repo.list_approval_requests()
    matching_approval = next((a for a in approvals if a.proposed_action_id == latest_action.id), None)

    if not matching_approval:
        from backend.services.logger import logger
        logger.error("Live Bedrock investigation failed postcondition: matching approval request not found")
        return {"error": "Live Agent proposed an action but failed to submit a valid approval request."}

    return {
        "mode": "bedrock",
        "text": str(result),
        "stop_reason": getattr(result, "stop_reason", "completed"),
        "proposed_action_id": latest_action.id,
        "approval_request_id": matching_approval.id
    }

async def run_investigation(obligation_id: str) -> Dict[str, Any]:
    """Orchestrator that forces a fresh readiness check before choosing the path."""
    if is_bedrock_available(force_fresh=True):
        return await run_live_investigation(obligation_id)
    else:
        from backend.agent.mock_agent import run_mock_investigation
        return await run_mock_investigation(obligation_id)
