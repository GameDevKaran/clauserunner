GOLDEN_CONTRACT_TEXT = """# SAAS VENDOR AGREEMENT
**Effective Date:** October 1, 2025  
**Parties:** Acme Cloud Solutions LLC ("Vendor") and ClauseRunner Labs Corp ("Customer")

## SECTION 4. SERVICE LEVEL AGREEMENT (SLA)
### 4.1 Uptime Commitment
Vendor will make the Acme Analytics Platform available with a Monthly Uptime Percentage of at least 99.9% during any monthly billing cycle (the "Uptime Commitment").

### 4.2 Measurement Period
The Service Level is calculated monthly over a calendar month billing period based on total minutes in the month minus total minutes of Unscheduled Downtime.

### 4.3 Service Credit Remedy
In the event that the Monthly Uptime Percentage falls below 99.9% in any calendar month, Customer shall be eligible to receive a Service Credit against their next monthly subscription invoice ($5,000 baseline fee), subject to the following tiers:
*   **Tier 1:** Monthly Uptime Percentage is less than 99.9% but equal to or greater than 99.0%: **10% Service Credit** (equivalent to $500).
*   **Tier 2:** Monthly Uptime Percentage is less than 99.0%: **20% Service Credit** (equivalent to $1,000).

### 4.4 Claim Window & Proof Requirements
To receive a Service Credit, Customer must submit a claim in writing to vendor-claims@acme-analytics.com within thirty (30) days of the end of the month in which the breach occurred, accompanied by server log evidence or monitoring reports demonstrating the downtime.
"""

SECONDARY_CONTRACT_TEXT = """# CYBERSECURITY COMPLIANCE & RENEWAL AGREEMENT
**Effective Date:** January 1, 2025  
**Parties:** CyberShield Guard Inc ("Provider") and ClauseRunner Labs Corp ("Customer")

## SECTION 8. TERM AND RENEWAL NOTICE WINDOW
### 8.1 Term and Automatic Renewal
This Agreement shall run for an initial term of one (1) year. It shall automatically renew for successive one-year terms unless either party provides written notice of non-renewal (the "Non-Renewal Notice") at least forty-five (45) days prior to the expiration of the then-current term.

### 8.2 Compliance Certificate Obligation
Provider must supply Customer with an updated SOC 2 Type II compliance certificate annually, no later than thirty (30) days following the anniversary of the Effective Date (i.e., by January 31st of each calendar year). Failure to provide this certificate shall trigger an immediate security review.
"""
