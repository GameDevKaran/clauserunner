import os
from typing import Any
from backend.repositories.sqlite_repo import SQLiteRepository
from backend.repositories.dynamodb_repo import DynamoDBRepository

_repo = None

def init_db(db_path: str = "clauserunner.sqlite") -> Any:
    """Explicitly initializes the global database instance, choosing DynamoDB if configured."""
    global _repo
    table_name = os.environ.get("CLAUSERUNNER_DYNAMODB_TABLE")
    if table_name:
        # Resolve AWS profile name if set, otherwise default to None (important for deployed IAM roles)
        profile = os.environ.get("AWS_PROFILE")
        if not profile or profile.lower() in ("none", "null", "false", ""):
            profile = None
        _repo = DynamoDBRepository(table_name=table_name, profile_name=profile)
    else:
        _repo = SQLiteRepository(db_path)
    return _repo

def get_repo() -> Any:
    """Retrieves the active database instance, default initializing if not set."""
    global _repo
    if _repo is None:
        init_db()
    return _repo

