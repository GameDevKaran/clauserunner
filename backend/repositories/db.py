from backend.repositories.sqlite_repo import SQLiteRepository

_repo = None

def init_db(db_path: str = "clauserunner.sqlite") -> SQLiteRepository:
    """Explicitly initializes the global database instance."""
    global _repo
    _repo = SQLiteRepository(db_path)
    return _repo

def get_repo() -> SQLiteRepository:
    """Retrieves the active database instance, default initializing if not set."""
    global _repo
    if _repo is None:
        _repo = SQLiteRepository("clauserunner.sqlite")
    return _repo
