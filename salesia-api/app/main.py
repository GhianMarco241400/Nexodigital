import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import engine
from app.init_db import init_db
from app.routers import aws, auth, customers, extras, health, orders, orders_admin
from app.routers import plans, settings as settings_router

logger = logging.getLogger("salesia.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db(engine)
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
    yield


app = FastAPI(title="SalesIA API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(plans.router)
app.include_router(orders.router)
app.include_router(orders_admin.router)
app.include_router(customers.router)
app.include_router(auth.router)
app.include_router(extras.router)
app.include_router(aws.router)
app.include_router(settings_router.router)
