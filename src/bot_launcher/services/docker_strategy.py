import json
import os
from typing import Dict, Any
import docker
from docker.errors import NotFound, APIError
from shared.utils.port_utils import get_next_available_port

from bot_launcher.services.base_strategy import ExecutionStrategy
from shared.config import bot_env_settings


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
        # 1. Configuration Setup
        host = bot_env_settings.host
        internal_port = bot_env_settings.internal_port

        # Check for provided port, otherwise generate one
        external_port = external_port = bot_env_settings.external_port or get_next_available_port()

        version = bot_env_settings.version
        network_name = bot_env_settings.network
        script_command = f"run-{bot_type}"
        image = f"ghcr.io/harikrishna2005/bot-launcher:{version}"
        container_name = f"{bot_name}_container"

        print(f"🐳 Launching {bot_name} with image {image}")

        try:
            # Replicates pull_policy: always
            print(f"📥 Pulling latest image: {image}")
            self.client.images.pull(image)

            # Prepare the BOT_CONFIG (Keep it clean, just trading data)
            bot_config_json = json.dumps({
                "bot_name": bot_name,
                "bot_type": bot_type,
                "config": config
            }, indent=2)

            container = self.client.containers.run(
                image=image,
                name=container_name,
                hostname=container_name,  # Added: self-identification
                detach=True,
                command=[script_command],
                ports={f'{internal_port}/tcp': external_port},
                labels={
                    "app.managed_by": "bot-launcher",
                    "bot_type": bot_type,
                    "bot_version": version
                },
                environment={
                    "BOT_CONFIG": bot_config_json,
                    "APP_HOST": host,
                    "APP_INTERNAL_PORT": str(internal_port),  # Convert to str
                    "APP_EXTERNAL_PORT": str(external_port),  # Convert to str
                    "APP_VERSION": version,
                    "APP_DOCKER_NETWORK": network_name,
                    "PYTHONUNBUFFERED": "1"
                },
                network=network_name,
                restart_policy={"Name": "always"},
                log_config={
                    "type": "json-file",
                    "config": {
                        "max-size": "10m",
                        "max-file": "3"
                    }
                }
            )

            return {
                "success": True,
                "container_id": container.short_id,
                "container_name": container.name,
                "status": container.status,
                "assigned_port": external_port  # Useful to return this to the API
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

