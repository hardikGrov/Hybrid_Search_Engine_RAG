from fastapi import FastAPI
from backend.app.api.routes import router
from backend.app.db.sqlite import init_db

app = FastAPI(title="Hybrid Search API")
init_db()

app.include_router(router)