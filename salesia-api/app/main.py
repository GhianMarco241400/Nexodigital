from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import aws, auth, customers, extras, health, orders, orders_admin
from app.routers import plans, settings as settings_router

app = FastAPI(title="SalesIA API")

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
