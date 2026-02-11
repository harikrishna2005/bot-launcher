from bot_launcher.api_routers.v1.endpoints import bot_router
from bot_launcher.api_routers.v1.endpoints import launcher_router
from fastapi import APIRouter


v1_router= APIRouter(prefix="/v1")
v1_router.include_router(bot_router.router)
v1_router.include_router(launcher_router.router)





