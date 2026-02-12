"""Unified FastAPI application for Bot Manager.

Automatically uses the correct execution strategy based on environment:
- LocalSubprocessStrategy when running locally (no Docker)
- DockerExecutionStrategy when running in Docker
"""
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from bot_launcher.api_routers.api import aggregator_router
from bot_launcher.services.deps import get_execution_strategy

# Initialize FastAPI app
app = FastAPI(
    title="Bot Manager API",
    description="Unified API for managing trading bots across local and Docker environments",
    version="1.0.0"
)

# Include all API routers
app.include_router(aggregator_router)

# Get the execution strategy singleton (auto-detects environment)
execution_strategy = get_execution_strategy()


class BotLaunchRequest(BaseModel):
    """Request model for launching a bot."""
    bot_name: str
    bot_type: str  # e.g., "rebalancing", "grid", etc.
    config: Dict[str, Any]
    version: str = "latest"  # Used only in Docker mode


@app.get("/")
def root():
    """Root endpoint - provides API information."""
    return {
        "service": "Bot Manager API",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    status_info = execution_strategy.get_status()
    return {
        "status": "healthy",
        "mode": status_info.get("mode", "unknown"),
        "manager": status_info.get("manager", "unknown")
    }


@app.get("/status")
def get_status():
    """Get the status of the manager and all running bots."""
    return execution_strategy.get_status()


@app.post("/launch")
def launch_bot(request: BotLaunchRequest):
    """Launch a new bot instance.

    The bot will be launched as:
    - A subprocess (local mode) using: poetry run run-{bot_type}
    - A Docker container (Docker mode) from the specified image
    """
    # Add version to config if provided (used in Docker mode)
    config_with_version = {**request.config, "version": request.version}

    result = execution_strategy.launch_bot(
        bot_name=request.bot_name,
        bot_type=request.bot_type,
        config=config_with_version
    )

    if result.get("error"):
        status_code = result.get("status_code", 500)
        raise HTTPException(status_code=status_code, detail=result.get("message"))

    return result


@app.post("/stop/{bot_name}")
def stop_bot(bot_name: str):
    """Stop a running bot.

    Stops and cleans up:
    - Subprocess (local mode) - terminates the process
    - Docker container (Docker mode) - stops and removes the container
    """
    result = execution_strategy.stop_bot(bot_name)

    if result.get("error"):
        status_code = result.get("status_code", 500)
        raise HTTPException(status_code=status_code, detail=result.get("message"))

    return result


@app.get("/bots")
def list_bots():
    """List all active bots with their details.

    Returns:
    - Local mode: List of processes with PIDs
    - Docker mode: List of containers with IDs and images
    """
    return execution_strategy.list_bots()

