from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bot_launcher.services.deps import get_execution_strategy

router = APIRouter(prefix="/launcher", tags=["Launcher Management"])

# Get the singleton instance once at module level
execution_strategy = get_execution_strategy()


class BotLaunchRequest(BaseModel):
    bot_name: str
    bot_type: str  # e.g. "rebalancing"
    config: Dict[str, Any]


@router.get("/status")
async def launcher_status():
    """Endpoint to check the status of the launcher."""
    return execution_strategy.get_status()


@router.post("/launch")
async def launch_bot(request: BotLaunchRequest):
    """Launch a new bot instance."""
    result = execution_strategy.launch_bot(
        bot_name=request.bot_name,
        bot_type=request.bot_type,
        config=request.config
    )

    if result.get("error"):
        status_code = result.get("status_code", 500)
        raise HTTPException(status_code=status_code, detail=result.get("message"))

    return result


@router.post("/stop/{bot_name}")
async def stop_bot(bot_name: str):
    """Stop a running bot."""
    result = execution_strategy.stop_bot(bot_name)

    if result.get("error"):
        status_code = result.get("status_code", 500)
        raise HTTPException(status_code=status_code, detail=result.get("message"))

    return result
