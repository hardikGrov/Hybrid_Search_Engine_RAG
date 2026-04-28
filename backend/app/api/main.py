from fastapi import FastAPI
from backend.app.api.routes import router

app = FastAPI(title="Hybrid Search API")

app.include_router(router)