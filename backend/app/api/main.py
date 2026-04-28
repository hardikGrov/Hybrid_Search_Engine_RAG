from fastapi import FastAPI

app = FastAPI(title="Hybrid Search API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
