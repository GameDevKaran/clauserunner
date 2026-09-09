from backend.repositories.interface import StorageInterface
from backend.repositories.sqlite_contract import SQLiteContract
from backend.repositories.sqlite_obligation import SQLiteObligation
from backend.repositories.sqlite_action import SQLiteAction

class SQLiteRepository(SQLiteContract, SQLiteObligation, SQLiteAction, StorageInterface):
    """Authoritative local SQLite persistence adapter with automatic seeding."""
    def __init__(self, db_path: str = ":memory:"):
        super().__init__(db_path)
        from backend.repositories.seed import seed_demo_data
        seed_demo_data(self)
