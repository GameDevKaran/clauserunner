from datetime import datetime
from backend.domain.models import (
    Contract, Clause, Obligation, EvidenceArtifact, AuditEvent,
    ObligationStatus, ObligationType, EvidenceStatus
)
from backend.domain.demo_contracts import GOLDEN_CONTRACT_TEXT, SECONDARY_CONTRACT_TEXT

def seed_demo_data(repo) -> None:
    if len(repo.list_contracts()) > 0:
        return

    # Contracts
    repo.save_contract(Contract(
        id="clauserunner-contract-acme",
        name="Acme Analytics Platform SaaS Agreement",
        description="Enterprise Agreement covering monthly log ingestion.",
        counterparty="Acme Cloud Solutions LLC",
        signed_at=datetime(2025, 10, 1),
        effective_date=datetime(2025, 10, 1),
        status="active",
        raw_text=GOLDEN_CONTRACT_TEXT
    ))
    repo.save_contract(Contract(
        id="clauserunner-contract-cybershield",
        name="CyberShield Guard Security Agreement",
        description="Annual managed cybersecurity services.",
        counterparty="CyberShield Guard Inc",
        signed_at=datetime(2025, 1, 1),
        effective_date=datetime(2025, 1, 1),
        status="active",
        raw_text=SECONDARY_CONTRACT_TEXT
    ))

    # Clauses
    repo.save_clause(Clause(id="c-acme-1", contract_id="clauserunner-contract-acme", number="4.1", title="Uptime Commit", text="Vendor commits to 99.9% Monthly Uptime Percentage."))
    repo.save_clause(Clause(id="c-acme-2", contract_id="clauserunner-contract-acme", number="4.3", title="SLA Remedy", text="Tier 1: <99.9% to >=99.0% -> 10% credit. Tier 2: <99.0% -> 20% credit."))
    repo.save_clause(Clause(id="c-cyber-1", contract_id="clauserunner-contract-cybershield", number="8.1", title="Term", text="Renewal occurs unless notice is given 45 days prior."))
    repo.save_clause(Clause(id="c-cyber-2", contract_id="clauserunner-contract-cybershield", number="8.2", title="SOC2", text="SOC 2 Type II certificate annually by Jan 31st."))

    # Obligations
    repo.save_obligation(Obligation(
        id="clauserunner-obligation-acme-sla", contract_id="clauserunner-contract-acme", source_clause_id="c-acme-1",
        title="Acme Platform Uptime SLA", description="Monthly uptime committed at 99.9%.",
        obligation_type=ObligationType.SLA, responsible_party="Acme Cloud Solutions LLC", counterparty="ClauseRunner Labs Corp",
        effective_from=datetime(2025, 10, 1), effective_until=datetime(2026, 10, 1),
        trigger="End of month", deadline=datetime(2026, 4, 30), measurement_period="monthly",
        evidence_requirements="Uptime report metrics", threshold="99.9", remedy="10% or 20% service credit",
        approval_policy=True, status=ObligationStatus.EVIDENCE_REQUIRED
    ))

    repo.save_obligation(Obligation(
        id="clauserunner-obligation-cyber-renewal", contract_id="clauserunner-contract-cybershield", source_clause_id="c-cyber-1",
        title="CyberShield Renewal Notice Window", description="Notice of non-renewal 45 days prior to expiration.",
        obligation_type=ObligationType.RENEWAL, responsible_party="ClauseRunner Labs Corp", counterparty="CyberShield Guard Inc",
        effective_from=datetime(2025, 1, 1), effective_until=datetime(2027, 1, 1),
        trigger="45 days prior", deadline=datetime(2026, 11, 17), measurement_period="annual",
        evidence_requirements="Written notice copy", threshold="45", remedy="Auto-renewal at $25k",
        approval_policy=True, status=ObligationStatus.MONITORING
    ))

    repo.save_obligation(Obligation(
        id="clauserunner-obligation-cyber-soc2", contract_id="clauserunner-contract-cybershield", source_clause_id="c-cyber-2",
        title="Annual SOC 2 Submission", description="Provider SOC 2 report by Jan 31st.",
        obligation_type=ObligationType.COMPLIANCE, responsible_party="CyberShield Guard Inc", counterparty="ClauseRunner Labs Corp",
        effective_from=datetime(2025, 1, 1), effective_until=datetime(2027, 1, 1),
        trigger="Anniversary", deadline=datetime(2026, 1, 31), measurement_period="annual",
        evidence_requirements="SOC 2 certificate", threshold="SOC 2 compliant", remedy="Immediate audit trigger",
        approval_policy=False, status=ObligationStatus.COMPLETED
    ))

    # Evidence
    repo.save_evidence(EvidenceArtifact(
        id="clauserunner-evidence-acme-march-2026", obligation_id="clauserunner-obligation-acme-sla",
        name="Acme March 2026 Report", content_type="application/json", file_path_or_url="/s3/evidence/acme_march_2026.json",
        raw_data_summary={"measured_uptime": 99.4, "month": "March 2026", "downtime_minutes": 268},
        status=EvidenceStatus.UNVERIFIED
    ))
    repo.save_evidence(EvidenceArtifact(
        id="clauserunner-evidence-cyber-soc2-2026", obligation_id="clauserunner-obligation-cyber-soc2",
        name="CyberShield SOC 2 Report 2026", content_type="application/pdf", file_path_or_url="/s3/evidence/cybershield_soc2.pdf",
        raw_data_summary={"report_period": "2025-2026", "auditor": "EY", "exceptions_noted": 0},
        status=EvidenceStatus.VERIFIED
    ))

    # Audits
    repo.save_audit_event(AuditEvent(
        id="audit-acme-init", contract_id="clauserunner-contract-acme", obligation_id="clauserunner-obligation-acme-sla",
        action_type="obligation_created", description="Uptime SLA created. Waiting for evidence.", user_or_system="System"
    ))
    repo.save_audit_event(AuditEvent(
        id="audit-cyber-init", contract_id="clauserunner-contract-cybershield", obligation_id="clauserunner-obligation-cyber-soc2",
        action_type="obligation_completed", description="SOC 2 validated and approved.", user_or_system="System"
    ))
