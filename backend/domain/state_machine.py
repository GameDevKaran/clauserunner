from typing import Dict, Set
from backend.domain.models import ObligationStatus

class InvalidStateTransition(Exception):
    def __init__(self, current: ObligationStatus, target: ObligationStatus, message: str = None):
        self.current = current
        self.target = target
        msg = message or f"Deterministic state machine blocked transition from '{current.value}' to '{target.value}'"
        super().__init__(msg)

class ObligationStateMachine:
    # Key: Current State -> Value: Set of allowed Next States
    _VALID_TRANSITIONS: Dict[ObligationStatus, Set[ObligationStatus]] = {
        ObligationStatus.PENDING: {
            ObligationStatus.MONITORING,
            ObligationStatus.EVIDENCE_REQUIRED
        },
        ObligationStatus.MONITORING: {
            ObligationStatus.EVIDENCE_REQUIRED,
            ObligationStatus.INVESTIGATING,
            ObligationStatus.COMPLETED
        },
        ObligationStatus.EVIDENCE_REQUIRED: {
            ObligationStatus.INVESTIGATING,
            ObligationStatus.MONITORING,
            ObligationStatus.COMPLETED
        },
        ObligationStatus.INVESTIGATING: {
            ObligationStatus.MONITORING,
            ObligationStatus.ACTION_REQUIRED,
            ObligationStatus.APPROVAL_REQUIRED,
            ObligationStatus.COMPLETED
        },
        ObligationStatus.ACTION_REQUIRED: {
            ObligationStatus.APPROVAL_REQUIRED,
            ObligationStatus.COMPLETED,
            ObligationStatus.MONITORING
        },
        ObligationStatus.APPROVAL_REQUIRED: {
            ObligationStatus.COMPLETED,
            ObligationStatus.ACTION_REQUIRED,
            ObligationStatus.INVESTIGATING
        },
        ObligationStatus.COMPLETED: {
            ObligationStatus.MONITORING,  # Allows restarting monitoring for periodic obligations
            ObligationStatus.EVIDENCE_REQUIRED
        }
    }

    @classmethod
    def validate_transition(cls, current: ObligationStatus, target: ObligationStatus) -> None:
        """
        Validates that transitioning from 'current' to 'target' is a deterministic and allowed path.
        Raises InvalidStateTransition if not permitted.
        """
        if current == target:
            return  # No change is always valid
            
        allowed_targets = cls._VALID_TRANSITIONS.get(current, set())
        if target not in allowed_targets:
            raise InvalidStateTransition(current, target)
