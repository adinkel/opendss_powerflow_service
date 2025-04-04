from fastapi import FastAPI
from contextlib import asynccontextmanager
from opendss_powerflow_service.app.api.routes import router as api_router

app = FastAPI(title="Powerflow Service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app.include_router(api_router)






