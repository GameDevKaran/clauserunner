from datetime import datetime
from typing import List, Optional
from backend.domain.models import Contract, Clause
from backend.repositories.dynamodb_base import DynamoDBBase

class DynamoDBContract(DynamoDBBase):
    """Mixin for DynamoDB Contract and Clause CRUD."""
    def save_contract(self, c: Contract) -> None:
        self._put_item(f"CONTRACT#{c.id}", "METADATA", c.dict())

    def get_contract(self, id: str) -> Optional[Contract]:
        r = self._get_item(f"CONTRACT#{id}", "METADATA")
        if not r: return None
        return Contract(
            id=r["id"], name=r["name"], description=r["description"], counterparty=r["counterparty"],
            signed_at=datetime.fromisoformat(r["signed_at"]), effective_date=datetime.fromisoformat(r["effective_date"]),
            status=r["status"], raw_text=r["raw_text"],
            created_at=datetime.fromisoformat(r["created_at"]), updated_at=datetime.fromisoformat(r["updated_at"])
        )

    def list_contracts(self) -> List[Contract]:
        items = self._scan_by_sk("METADATA")
        return [Contract(
            id=r["id"], name=r["name"], description=r["description"], counterparty=r["counterparty"],
            signed_at=datetime.fromisoformat(r["signed_at"]), effective_date=datetime.fromisoformat(r["effective_date"]),
            status=r["status"], raw_text=r["raw_text"],
            created_at=datetime.fromisoformat(r["created_at"]), updated_at=datetime.fromisoformat(r["updated_at"])
        ) for r in items if r["PK"].startswith("CONTRACT#")]

    def save_clause(self, c: Clause) -> None:
        self._put_item(f"CLAUSE#{c.id}", "METADATA", c.dict())

    def get_clause(self, id: str) -> Optional[Clause]:
        r = self._get_item(f"CLAUSE#{id}", "METADATA")
        if not r: return None
        return Clause(id=r["id"], contract_id=r["contract_id"], number=r["number"], title=r["title"], text=r["text"], created_at=datetime.fromisoformat(r["created_at"]))

    def list_contract_clauses(self, contract_id: str) -> List[Clause]:
        items = self._scan_by_sk("METADATA")
        return [Clause(id=r["id"], contract_id=r["contract_id"], number=r["number"], title=r["title"], text=r["text"], created_at=datetime.fromisoformat(r["created_at"])) for r in items if r["PK"].startswith("CLAUSE#") and r.get("contract_id") == contract_id]
