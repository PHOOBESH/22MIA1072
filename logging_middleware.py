# logging_middleware.py
import logging
import time
import uuid
from fastapi import Request
import os

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
    ]
)

logger = logging.getLogger("affordmed")

async def log_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(f"REQUEST_ID={request_id} | METHOD={request.method} | PATH={request.url.path} | START")
    
    response = await call_next(request)
    
    duration = round((time.time() - start_time) * 1000, 2)
    logger.info(f"REQUEST_ID={request_id} | STATUS={response.status_code} | DURATION={duration}ms | END")
    
    return response