"""Veyra API server entry point."""
import uvicorn
from fastapi import FastAPI
from veyra.api.zwm import router as zwm_router

app = FastAPI(title="Veyra", version="0.1.0")
app.include_router(zwm_router, prefix="/zwm", tags=["ZWM Integration"])


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)  # nosec B104
