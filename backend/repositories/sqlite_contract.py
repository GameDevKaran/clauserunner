from datetime import datetime
from typing import List, Optional
from backend.domain.models import Contract, Clause
from backend.repositories.sqlite_base import SQLiteBase

class SQLiteContract(SQLiteBase):
    """Mixin for Contract and Clause CRUD."""
    def save_contract(self, c: Contract) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO contracts 
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (c.id, c.name, c.description, c.counterparty, c.signed_at.isoformat(), c.effective_date.isoformat(), c.status, c.raw_text, c.created_at.isoformat(), c.updated_at.isoformat()))
            conn.commit()

    def get_contract(self, id: str) -> Optional[Contract]:
        with self._get_connection() as conn:
            r = conn.execute("SELECT * FROM contracts WHERE id = ?", (id,)).fetchone()
            if not r: return None
            return Contract(
                id=r["id"], name=r["name"], description=r["description"], counterparty=r["counterparty"],
                signed_at=datetime.fromisoformat(r["signed_at"]), effective_date=datetime.fromisoformat(r["effective_date"]),
                status=r["status"], raw_text=r["raw_text"],
                created_at=datetime.fromisoformat(r["created_at"]), updated_at=datetime.fromisoformat(r["updated_at"])
            )

    def list_contracts(self) -> List[Contract]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM contracts").fetchall()
            return [Contract(
                id=r["id"], name=r["name"], description=r["description"], counterparty=r["counterparty"],
                signed_at=datetime.fromisoformat(r["signed_at"]), effective_date=datetime.fromisoformat(r["effective_date"]),
                status=r["status"], raw_text=r["raw_text"],
                created_at=datetime.fromisoformat(r["created_at"]), updated_at=datetime.fromisoformat(r["updated_at"])
            ) for r in rows]

    def save_clause(self, c: Clause) -> None:
        with self._get_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO clauses VALUES (?,?,?,?,?,?)", (c.id, c.contract_id, c.number, c.title, c.text, c.created_at.isoformat()))
            conn.commit()

    def get_clause(self, id: str) -> Optional[Clause]:
        with self._get_connection() as conn:
            r = conn.execute("SELECT * FROM clauses WHERE id = ?", (id,)).fetchone()
            if not r: return None
            return Clause(id=r["id"], contract_id=r["contract_id"], number=r["number"], title=r["title"], text=r["text"], created_at=datetime.fromisoformat(r["created_at"]))

    def list_contract_clauses(self, contract_id: str) -> List[Clause]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM clauses WHERE contract_id = ?", (contract_id,)).fetchall()
            return [Clause(id=r["id"], contract_id=r["contract_id"], number=r["number"], title=r["title"], text=r["text"], created_at=datetime.fromisoformat(r["created_at"])) for r in rows]
