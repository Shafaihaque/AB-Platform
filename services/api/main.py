from fastapi import FastAPI
from contextlib import asynccontextmanager
from db.database import connect_db, disconnect_db
from routers import experiments, assign, results


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()


app = FastAPI(title="AB Platform API", lifespan=lifespan)

app.include_router(experiments.router)
app.include_router(assign.router)
app.include_router(results.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "api"}
