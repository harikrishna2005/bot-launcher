import docker
import uvicorn
import os


RUNNING_IN_DOCKER = os.path.exists('/var/run/docker.sock')
client = docker.from_env() if RUNNING_IN_DOCKER else None

def start_server():
    """Entry point for poetry run run-manager"""
    if RUNNING_IN_DOCKER:
        print("RUNNING INSIDE DOCKERR")
        uvicorn.run("bot_launcher.app_docker:app", host="0.0.0.0", port=9501, reload=True)
    else:
        print("⚠️  Not running inside Docker. Please run this command within a Docker container.")
        uvicorn.run("bot_launcher.app_local:app", host="0.0.0.0", port=9501, reload=True)
        exit(1)

