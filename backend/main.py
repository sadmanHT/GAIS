from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import config  # noqa: F401 - loads backend/.env before model/API startup
from api.routes import router
from database import init_db
from ml.loader import get_models


app = FastAPI(title="GAIS Backend API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


class DiagnosticsResponse(BaseModel):
    status: str
    version: str
    models_loaded: bool


@app.on_event("startup")
def startup():
    init_db()
    get_models()


@app.get("/diagnostics", response_model=DiagnosticsResponse)
def get_diagnostics():
    return DiagnosticsResponse(status="healthy", version="1.0.0", models_loaded=True)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
