from fastapi import APIRouter
from bot_launcher.services.deps import get_execution_strategy

router = APIRouter(prefix="/bots", tags=["Bot Management"])

# Get the singleton instance once at module level
execution_strategy = get_execution_strategy()


@router.get("/")
async def list_bots():
    """Endpoint to list all active bots."""
    return execution_strategy.list_bots()


@router.get("/status")
async def get_bots_status():
    """Get detailed status of all bots."""
    return execution_strategy.get_status()
