"""CLI entry point for the bot manager server."""
import uvicorn
import os

# sample input
# {
#   "bot_name": "rebalance_top_2_crypto",
#   "bot_type": "rebalancing",
#   "config": {
#     "assets": ["BTC", "ETH"],
#     "target_weights": {
#       "BTC": 0.50,
#       "ETH": 0.50
#     }
#   }
# }


def start_launcher():
    """Entry point for poetry run run-manager.

    Automatically detects the environment and uses the appropriate execution strategy:
    - Local mode: Uses LocalSubprocessStrategy
    - Docker mode: Uses DockerExecutionStrategy
    """
    running_in_docker = os.path.exists('/var/run/docker.sock')

    if running_in_docker:
        print("🐳 Running in Docker mode")
        print("🚀 Starting Bot Manager API on http://0.0.0.0:9501")
        uvicorn.run("bot_launcher.app:app", host="0.0.0.0", port=9501, reload=False)
    else:
        print("💻 Running in Local mode")
        print("🚀 Starting Bot Manager API on http://0.0.0.0:9501")
        print("📝 API docs available at http://localhost:9501/docs")
        uvicorn.run("bot_launcher.app:app", host="0.0.0.0", port=9501, reload=True)

