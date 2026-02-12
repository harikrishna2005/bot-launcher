# src/shared/launcher.py
import docker
import uvicorn
import os
import sys


def run_app(package_name: str, port: int):
    """
    Generic runner that checks for Docker and starts Uvicorn.
    :param package_name: The string path to the FastAPI app (e.g. "bots.rebalance_bot.main:app")
    :param port: The port to run on
    """
    app_path =f"{package_name}.main:app"
    running_in_docker = os.path.exists('/var/run/docker.sock')

    if running_in_docker:
        print(f"🚀 RUNNING INSIDE DOCKER - Port: {port}")
        # In Docker, we usually don't want reload=True in production,
        # but for your dev setup, we can keep it.
        uvicorn.run(app_path, host="0.0.0.0", port=port, reload=False)
    else:
        print(f"⚠️  Not running inside Docker. Attempting local start on {port}...")
        # You can choose to allow local running or exit(1) as you did before
        uvicorn.run(app_path, host="0.0.0.0", port=port, reload=True)