import sqlite3

class SQLiteBase:
    """Manages database connection and base table provisions."""
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        # Pass check_same_thread=False to allow connections across FastAPI worker threads safely
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _get_connection(self):
        return self._conn

    def _init_db(self):
        conn = self._get_connection()
        conn.execute("CREATE TABLE IF NOT EXISTS contracts (id TEXT PRIMARY KEY, name TEXT, description TEXT, counterparty TEXT, signed_at TEXT, effective_date TEXT, status TEXT, raw_text TEXT, created_at TEXT, updated_at TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS clauses (id TEXT PRIMARY KEY, contract_id TEXT, number TEXT, title TEXT, text TEXT, created_at TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS obligations (id TEXT PRIMARY KEY, contract_id TEXT, source_clause_id TEXT, title TEXT, description TEXT, obligation_type TEXT, responsible_party TEXT, counterparty TEXT, effective_from TEXT, effective_until TEXT, trigger TEXT, deadline TEXT, measurement_period TEXT, evidence_requirements TEXT, threshold TEXT, remedy TEXT, approval_policy INTEGER, status TEXT, created_at TEXT, updated_at TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS evidence_artifacts (id TEXT PRIMARY KEY, obligation_id TEXT, name TEXT, content_type TEXT, file_path_or_url TEXT, raw_data_summary TEXT, status TEXT, upload_date TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS investigations (id TEXT PRIMARY KEY, obligation_id TEXT, status TEXT, steps TEXT, findings TEXT, confidence REAL, proposed_action_id TEXT, created_at TEXT, completed_at TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS proposed_actions (id TEXT PRIMARY KEY, obligation_id TEXT, investigation_id TEXT, title TEXT, description TEXT, action_type TEXT, cost_or_impact TEXT, requires_approval INTEGER, draft_payload TEXT, status TEXT, created_at TEXT, updated_at TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS approval_requests (id TEXT PRIMARY KEY, proposed_action_id TEXT, requested_by TEXT, approved_by TEXT, status TEXT, comments TEXT, created_at TEXT, decided_at TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS action_executions (id TEXT PRIMARY KEY, proposed_action_id TEXT, executed_by TEXT, status TEXT, result_artifact TEXT, executed_at TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS audit_events (id TEXT PRIMARY KEY, contract_id TEXT, obligation_id TEXT, action_type TEXT, description TEXT, user_or_system TEXT, request_id TEXT, timestamp TEXT, metadata TEXT)")
        conn.commit()


