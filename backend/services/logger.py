import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """Formats standard log records into cloud-ready JSON payloads, filtering secrets."""
    def format(self, record: logging.LogRecord) -> str:
        # Standard attributes
        payload: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        
        # Inject custom operational attributes if passed in extra
        extra = getattr(record, "extra_fields", {})
        if isinstance(extra, dict):
            for k, v in extra.items():
                # Filter out sensitive fields
                if k.lower() in ("aws_access_key_id", "aws_secret_access_key", "secret", "token"):
                    continue
                payload[k] = v
                
        return json.dumps(payload)

def setup_logger(name: str = "clauserunner") -> logging.Logger:
    """Configures and returns the system-wide JSON logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        
    return logger

# Global log instance
logger = setup_logger()
