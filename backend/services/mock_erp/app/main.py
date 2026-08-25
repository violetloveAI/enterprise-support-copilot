from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import seed_database
from .routes import approvals, claims, interfaces, tickets, users, vouchers


@asynccontextmanager
async def lifespan(_: FastAPI):
    seed_database()
    yield


app = FastAPI(
    title="Synthetic Expense ERP API",
    version="2.0.0",
    description="Mock REST API. All records are synthetic and safe for public demos.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
for router in (
    claims.router,
    users.router,
    approvals.router,
    vouchers.router,
    interfaces.router,
    tickets.router,
):
    app.include_router(router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "mock-erp", "data_classification": "synthetic"}
