import os
import json
import boto3
from typing import List, Optional
from decimal import Decimal
from enum import Enum
from datetime import datetime, date

class DynamoDBJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to safely handle Decimal, Enum, and datetime objects inside JSON strings."""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
        return super().default(obj)

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

    def _serialize_value(self, v):
        """Converts native Python values to DynamoDB-supported formats at our canonical boundary."""
        if isinstance(v, (datetime, date)):
            return v.isoformat()
        if isinstance(v, Enum):
            return v.value
        if isinstance(v, float):
            return Decimal(str(v))
        if isinstance(v, (dict, list)):
            return json.dumps(v, cls=DynamoDBJSONEncoder)
        return v

    def _put_item(self, pk: str, sk: str, item_dict: dict) -> None:
        serializable = {}
        for k, v in item_dict.items():
            serializable[k] = self._serialize_value(v)
        serializable["PK"] = pk
        serializable["SK"] = sk
        self.table.put_item(Item=serializable)

    def _get_item(self, pk: str, sk: str) -> Optional[dict]:
        return self.table.get_item(Key={"PK": pk, "SK": sk}).get("Item")

    def _scan_by_sk(self, sk: str) -> List[dict]:
        """Scans and follows pagination via ExclusiveStartKey/LastEvaluatedKey until the complete result is gathered."""
        items = []
        response = self.table.scan(FilterExpression="SK = :sk", ExpressionAttributeValues={":sk": sk})
        items.extend(response.get("Items", []))
        while "LastEvaluatedKey" in response:
            response = self.table.scan(
                FilterExpression="SK = :sk",
                ExpressionAttributeValues={":sk": sk},
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            items.extend(response.get("Items", []))
        return items

