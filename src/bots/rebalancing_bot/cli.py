import docker
import uvicorn
import os
from shared.config import bot_env_settings



# RUNNING_IN_DOCKER = os.path.exists('/var/run/docker.sock')
# client = docker.from_env() if RUNNING_IN_DOCKER else None

# Environment variable to username
#
# # Inside launch_bot method
# env_vars = {
#     "APP_EXTERNAL_PORT": str(host_port),
#     "APP_INTERNAL_PORT": str(internal_port),
#     "APP_VERSION": version,
#     "APP_NETWORK_NAME": "my_home_network",
#     # Pass the trading config separately as we discussed
#     "BOT_TRADING_CONFIG": json.dumps(config)
# }





def start_server():
    # RUNNING_IN_DOCKER = os.path.exists('/var/run/docker.sock')
    running_in_docker = os.path.exists('/var/run/docker.sock')
    """Entry point for poetry run run-manager"""
    if running_in_docker:
        print("RUNNING INSIDE DOCKERR")
        # uvicorn.run("bot_launcher.app_docker:app", host="0.0.0.0", port=9501, reload=False)
        uvicorn.run("bots.rebalancing_bot.main:app", host=bot_env_settings.host, port=bot_env_settings.external_port, reload=False)
    else:
        print("⚠️  Not running inside Docker. Please run this command within a Docker container.")
        uvicorn.run("bots.rebalancing_bot.main:app", host=bot_env_settings.host, port=bot_env_settings.external_port, reload=True)
        exit(1)

