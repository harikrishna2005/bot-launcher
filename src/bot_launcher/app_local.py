import docker
import json
import os

import uvicorn
# uvicorn src.bot_launcher.app:app --host 127.0.0.1 --port 9501

from bot_launcher import test1_check
# from bot_launcher.test1_check import get_text_v1

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Bot Manager API")
# client = docker.from_env()
RUNNING_IN_DOCKER = os.path.exists('/var/run/docker.sock')
client = docker.from_env() if RUNNING_IN_DOCKER else None


class BotLaunchRequest(BaseModel):
    bot_name: str
    bot_type: str  # e.g., "rebalancing" or "grid"
    config: dict
    version: str = "latest"


@app.get("/status")
def get_all_bots():
    return {f"Getting all the bots --->  {test1_check.get_text_v1()} "}
    # """List all containers managed by this API"""
    # containers = client.containers.list(all=True)
    # return [
    #     {
    #         "name": c.name,
    #         "status": c.status,
    #         "image": c.image.tags[0] if c.image.tags else "unknown"
    #     } for c in containers if "manager" not in c.name
    # ]


@app.post("/launch")
def launch_bot(request: BotLaunchRequest):
    return {"Launching the bot"}
    # image = f"ghcr.io/harikrishna2005/rebalancing-trading-bot:{request.version}"
    # try:
    #     # Pull latest if version is 'latest'
    #     if request.version == "latest":
    #         client.images.pull(image)
    #
    #     container = client.containers.run(
    #         image=image,
    #         name=request.bot_name,
    #         detach=True,
    #         command=["python", f"src/bots/{request.bot_type}/main.py"],
    #         environment={"BOT_CONFIG": json.dumps(request.config)},
    #         restart_policy={"Name": "unless-stopped"}
    #     )
    #     return {"message": "Bot started", "id": container.id}
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop/{bot_name}")
def stop_bot(bot_name: str):
    return {"STOP the bot"}
    # try:
    #     container = client.containers.get(bot_name)
    #     container.stop()
    #     container.remove()  # Clean up the container after stopping
    #     return {"message": f"Bot {bot_name} stopped and removed"}
    # except docker.errors.NotFound:
    #     raise HTTPException(status_code=404, detail="Bot not found")


