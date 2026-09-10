import os
import json
import boto3
from typing import List, Optional

class DynamoDBBase:
    """Manages AWS DynamoDB connections and base single-table operational helpers."""
    def __init__(self, table_name: str = "clauserunner-state", profile_name: Optional[str] = "clauserunner-dev", region_name: str = "us-east-1"):
        self.table_name = table_name
        self.region_name = region_name
        
        # Resolve session with explicit profile if provided, otherwise default fallback for EC2/AppRunner IAM roles
        if profile_name:
            session = boto3.Session(profile_name=profile_name, region_name=region_name)
        else:
            session = boto3.Session(region_name=region_name)
            
        self.table = session.resource('dynamodb').Table(self.table_name)

    def _put_item(self, pk: str, sk: str, item_dict: dict) -> None:
        from datetime import datetime
        serializable = {}
        for k, v in item_dict.items():
            if isinstance(v, datetime):
                serializable[k] = v.isoformat()
            elif isinstance(v, (dict, list)):
                serializable[k] = json.dumps(v)
            else:
                serializable[k] = v
        serializable["PK"] = pk
        serializable["SK"] = sk
        self.table.put_item(Item=serializable)

    def _get_item(self, pk: str, sk: str) -> Optional[dict]:
        return self.table.get_item(Key={"PK": pk, "SK": sk}).get("Item")

    def _scan_by_sk(self, sk: str) -> List[dict]:
        return self.table.scan(FilterExpression="SK = :sk", ExpressionAttributeValues={":sk": sk}).get("Items", [])
