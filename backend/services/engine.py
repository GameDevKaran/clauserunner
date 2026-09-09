from datetime import datetime, timedelta
from typing import Dict, Any

def calculate_sla_remedy(measured_uptime: float, base_monthly_fee: float = 5000.0) -> Dict[str, Any]:
    """
    Deterministically calculates SLA compliance, breach status, credit tier, and credit amount.
    No LLM is used here to avoid hallucinated calculations.
    """
    threshold = 99.9
    is_breached = measured_uptime < threshold
    
    tier = 0
    credit_percentage = 0.0
    credit_amount = 0.0
    remedy_description = "Compliant. No remedy required."

    if is_breached:
        if measured_uptime >= 99.0:
            tier = 1
            credit_percentage = 0.10
            credit_amount = base_monthly_fee * credit_percentage
            remedy_description = f"Tier 1 SLA Breach (measured: {measured_uptime:.2f}% < {threshold}%). 10% Service Credit applies."
        else:
            tier = 2
            credit_percentage = 0.20
            credit_amount = base_monthly_fee * credit_percentage
            remedy_description = f"Tier 2 SLA Breach (measured: {measured_uptime:.2f}% < {threshold}%). 20% Service Credit applies."
            
    return {
        "threshold": threshold,
        "measured_uptime": measured_uptime,
        "is_breached": is_breached,
        "tier": tier,
        "credit_percentage": credit_percentage,
        "credit_amount": credit_amount,
        "remedy_description": remedy_description
    }

def calculate_remediation_deadline(month_end: datetime, claim_window_days: int = 30) -> datetime:
    """
    Deterministically calculates the claim window deadline.
    """
    return month_end + timedelta(days=claim_window_days)

def evaluate_notice_window(expiration_date: datetime, notice_days_required: int = 45, current_time: datetime = None) -> Dict[str, Any]:
    """
    Deterministically calculates notice window deadlines and status.
    """
    if current_time is None:
        current_time = datetime.utcnow()
        
    deadline = expiration_date - timedelta(days=notice_days_required)
    days_until_deadline = (deadline - current_time).days
    is_missed = current_time > deadline
    
    return {
        "expiration_date": expiration_date,
        "notice_days_required": notice_days_required,
        "notice_deadline": deadline,
        "days_until_deadline": days_until_deadline,
        "is_missed": is_missed,
        "status": "missed" if is_missed else ("urgent" if days_until_deadline <= 15 else "monitoring")
    }
