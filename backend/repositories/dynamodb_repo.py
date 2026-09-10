from backend.repositories.interface import StorageInterface
from backend.repositories.dynamodb_contract import DynamoDBContract
from backend.repositories.dynamodb_obligation import DynamoDBObligation
from backend.repositories.dynamodb_action import DynamoDBAction

class DynamoDBRepository(DynamoDBContract, DynamoDBObligation, DynamoDBAction, StorageInterface):
    """Authoritative AWS DynamoDB single-table persistence adapter with auto-seeding."""
    def __init__(self, table_name: str = "clauserunner-state", profile_name: str = "clauserunner-dev", region_name: str = "us-east-1"):
        super().__init__(table_name, profile_name, region_name)
        from backend.repositories.seed import seed_demo_data
        seed_demo_data(self)
