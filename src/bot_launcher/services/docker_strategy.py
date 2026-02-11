import json
from typing import Dict, Any
import docker
from docker.errors import NotFound, APIError

from bot_launcher.services.base_strategy import ExecutionStrategy


class DockerExecutionStrategy(ExecutionStrategy):
    """Strategy for launching bots as Docker containers."""

    def __init__(self):
        """Initialize Docker client."""
        try:
            self.client = docker.from_env()
            print("🐳 Docker client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Docker client: {e}")
            raise

    def launch_bot(self, bot_name: str, bot_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Launch a bot as a Docker container matching the Compose configuration."""
        # Use 'develop' as requested in your compose file
        version = "develop"
        image = f"ghcr.io/harikrishna2005/bot-launcher:{version}"

        # Matches the container_name from your compose
        container_name = f"{bot_name}_container"

        print(f"🐳 Launching {bot_name} with image {image}")

        try:
            # --- THIS REPLICATES pull_policy: always ---
            # It forces the Docker daemon to check for a newer version of the tag
            print(f"📥 Pulling latest image: {image}")
            self.client.images.pull(image)

            # Prepare the BOT_CONFIG environment variable as a JSON string
            bot_config_json = json.dumps({
                "bot_name": bot_name,
                "bot_type": bot_type,
                "config": config
            }, indent=2)

            container = self.client.containers.run(
                image=image,
                name=container_name,
                detach=True,
                # Matches command: ["run-rebalancing"]
                command=["run-rebalancing"],
                # Matches ports: ["9501:9501"]
                ports={'9501/tcp': 9501},
                # Matches environment: BOT_CONFIG
                environment={
                    "BOT_CONFIG": bot_config_json
                },
                # Matches networks: my_home_network
                network="my_home_network",
                # Matches restart: always
                restart_policy={"Name": "always"}
            )

            return {
                "success": True,
                "container_id": container.short_id,
                "container_name": container.name,
                "status": container.status
            }
        except APIError as e:
            print(f"❌ Docker API error: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return {"success": False, "error": str(e)}

    def stop_bot(self, bot_name: str) -> Dict[str, str]:
        """Stop a running bot container and remove it."""
        try:
            container = self.client.containers.get(bot_name)
            container.stop()
            container.remove()  # Clean up the container after stopping

            return {
                "error": False,
                "message": f"Bot '{bot_name}' stopped and removed successfully",
                "bot_name": bot_name
            }

        except NotFound:
            return {
                "error": True,
                "message": f"Bot '{bot_name}' not found",
                "status_code": 404
            }
        except Exception as e:
            return {
                "error": True,
                "message": f"Failed to stop bot '{bot_name}'",
                "detail": str(e),
                "status_code": 500
            }

    def get_status(self) -> Dict[str, Any]:
        """Get the status of the manager and all running bots."""
        try:
            containers = self.client.containers.list(all=True)
            # Filter out the manager container itself
            bot_containers = [c for c in containers if "manager" not in c.name]

            return {
                "manager": "running_in_docker",
                "mode": "docker",
                "total_bots": len(bot_containers),
                "running_bots": [
                    {
                        "name": c.name,
                        "status": c.status,
                        "image": c.image.tags[0] if c.image.tags else "unknown",
                        "id": c.short_id
                    } for c in bot_containers
                ]
            }
        except Exception as e:
            return {
                "manager": "running_in_docker",
                "mode": "docker",
                "error": str(e),
                "total_bots": 0,
                "running_bots": []
            }

    def list_bots(self) -> Dict[str, Any]:
        """List all bot containers with their details."""
        try:
            containers = self.client.containers.list(all=True)
            # Filter out the manager container itself
            bot_containers = [c for c in containers if "manager" not in c.name]

            bots = [
                {
                    "bot_name": c.name,
                    "container_id": c.short_id,
                    "status": c.status,
                    "image": c.image.tags[0] if c.image.tags else "unknown",
                    "created": c.attrs.get("Created", "N/A"),
                    "state": c.attrs.get("State", {}).get("Status", "unknown")
                } for c in bot_containers
            ]

            return {
                "total": len(bots),
                "bots": bots
            }
        except Exception as e:
            return {
                "error": True,
                "message": "Failed to list bots",
                "detail": str(e),
                "total": 0,
                "bots": []
            }

