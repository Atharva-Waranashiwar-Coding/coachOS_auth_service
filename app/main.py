from fastapi import FastAPI

app = FastAPI(title="CoachOS Auth Service")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "auth"}
