from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import ai_routes, auth_routes, blockchain_routes, conversations, dashboard, messages, ws
from backend.config import CORS_ORIGINS
from backend.database.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AI-Powered Secure Messaging API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
for r in (auth_routes.router, conversations.router, messages.router, ai_routes.router, blockchain_routes.router, dashboard.router, ws.router):
    app.include_router(r)


@app.get("/api/health")
def health():
    return {"status": "ok"}
