import os
import json
import subprocess
import signal
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from bot_launcher.api_routers.api import aggregator_router

app = FastAPI(title="Bot Manager API [LOCAL MODE]")

app.include_router(aggregator_router)

# PID Tracking for local processes
active_processes: Dict[str, int] = {}


class BotLaunchRequest(BaseModel):
    bot_name: str
    bot_type: str  # e.g. "rebalancing"
    config: Dict[str, Any]


@app.get("/status")
def get_status():
    return {
        "manager": "running_locally",
        "running_bots": active_processes
    }


@app.post("/launch")
def launch_bot(request: BotLaunchRequest):
    if request.bot_name in active_processes:
        raise HTTPException(status_code=400, detail="Bot name already active.")

    print(f"🛠 Launching {request.bot_name} via: poetry run run-{request.bot_type}")

    try:
        # Dynamically builds the command: "run-rebalancing", "run-grid", etc.
        script_command = f"run-{request.bot_type}"

        process = subprocess.Popen(
            ["poetry", "run", script_command],
            env={
                **os.environ,
                "BOT_CONFIG": json.dumps(request.config),
                "PYTHONUNBUFFERED": "1"
            },
            start_new_session=True,
            stdout=None,  # Output goes to your current terminal
            stderr=None
        )

        active_processes[request.bot_name] = process.pid
        return {"message": "Bot launched", "pid": process.pid}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Check if {script_command} exists in pyproject.toml: {str(e)}")


@app.post("/stop/{bot_name}")
def stop_bot(bot_name: str):
    pid = active_processes.get(bot_name)
    if not pid:
        raise HTTPException(status_code=404, detail="Bot not found.")

    try:
        os.kill(pid, signal.SIGTERM)
        del active_processes[bot_name]
        return {"message": f"Stopped {bot_name}"}
    except Exception as e:
        # If process already died, just clean up the dict
        active_processes.pop(bot_name, None)
        return {"message": "Process was not running, removed from tracking."}