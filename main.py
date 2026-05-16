from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from logging_middleware import log_middleware

app = FastAPI()

app.add_middleware(BaseHTTPMiddleware, dispatch=log_middleware)

@app.get("/")
async def root():
    return {"status": "running"}