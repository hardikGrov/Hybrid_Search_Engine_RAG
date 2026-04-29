import json
import logging
from datetime import datetime, timezone
from uuid import uuid4


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("hybrid_search")


def log_request(data: dict) -> None:
    payload = dict(data)
    payload["timestamp"] = datetime.now(timezone.utc).isoformat()
    payload["request_id"] = str(uuid4())
    logger.info(json.dumps(payload))
