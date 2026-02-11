from bot_launcher.api_routers.v1.api_v1 import v1_router
from fastapi import APIRouter

aggregator_router= APIRouter(prefix="/api")
aggregator_router.include_router(v1_router)