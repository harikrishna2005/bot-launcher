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
        host = bot_env_settings.host
        internal_port = bot_env_settings.internal_port

        # Use provided port or find next available
        external_port = bot_env_settings.external_port or get_next_available_port()

        version = bot_env_settings.version
        network_name = bot_env_settings.network
        script_command = f"run-{bot_type}"
        image = f"ghcr.io/harikrishna2005/bot-launcher:{version}"
        container_name = f"{bot_name}_container"

        try:
            print(f"📥 Pulling latest image: {image}")
            self.client.images.pull(image)

            bot_config_json = json.dumps({
                "bot_name": bot_name,
                "bot_type": bot_type,
                "config": config
            })

            container = self.client.containers.run(
                image=image,
                name=container_name,
                hostname=container_name,
                detach=True,
                command=[script_command],
                ports={f'{internal_port}/tcp': external_port},
                labels={
                    "app.managed_by": "bot-launcher",  # Used for strict filtering
                    "bot_type": bot_type,
                    "bot_version": version
                },
                environment={
                    "BOT_CONFIG": bot_config_json,
                    "APP_HOST": host,
                    "APP_INTERNAL_PORT": str(internal_port),
                    "APP_EXTERNAL_PORT": str(external_port),
                    "APP_VERSION": version,
                    "APP_DOCKER_NETWORK": network_name,
                    "PYTHONUNBUFFERED": "1"
                },
                network=network_name,
                restart_policy={"Name": "always"},
                log_config={"type": "json-file", "config": {"max-size": "10m", "max-file": "3"}}
            )

            return {
                "success": True,
                "container_id": container.short_id,
                "container_name": container.name,
                "status": container.status,
                "assigned_port": external_port
            }
        except Exception as e:
            print(f"❌ Launch error: {e}")
            return {"success": False, "error": str(e)}

    def stop_bot(self, bot_name: str) -> Dict[str, Any]:
        """Stop and remove a managed bot container."""
        target_name = f"{bot_name}_container"
        try:
            container = self.client.containers.get(target_name)
            container.stop()
            container.remove()
            return {"error": False, "message": f"Bot '{bot_name}' removed."}
        except NotFound:
            return {"error": True, "message": "Bot not found", "status_code": 404}
        except Exception as e:
            return {"error": True, "detail": str(e), "status_code": 500}

    def get_status(self) -> Dict[str, Any]:
        """Get summarized status of managed bots."""
        try:
            # Filter specifically for our bots using labels
            filters = {"label": "app.managed_by=bot-launcher"}
            bot_containers = self.client.containers.list(all=True, filters=filters)

            return {
                "manager": "running_in_docker",
                "mode": "docker",
                "total_bots": len(bot_containers),
                "running_bots": [
                    {
                        "name": c.name,
                        "status": c.status,
                        "bot_type": c.labels.get("bot_type", "unknown"),
                        "id": c.short_id
                    } for c in bot_containers
                ]
            }
        except Exception as e:
            return {"error": str(e), "total_bots": 0, "running_bots": []}

    def list_bots(self) -> Dict[str, Any]:
        """List detailed info including internal and external ports."""
        try:
            filters = {"label": "app.managed_by=bot-launcher"}
            containers = self.client.containers.list(all=True, filters=filters)

            bots = []
            for c in containers:
                # Extract port mappings from container attributes
                port_data = c.attrs.get('NetworkSettings', {}).get('Ports', {})
                internal_port = None
                external_port = None

                if port_data:
                    # Docker stores ports as '8000/tcp': [{'HostIp': '...', 'HostPort': '59001'}]
                    for container_port_proto, host_bindings in port_data.items():
                        if host_bindings:
                            internal_port = container_port_proto.split('/')[0]
                            external_port = host_bindings[0].get('HostPort')
                            break

                bots.append({
                    "bot_name": c.name.replace("_container", ""),
                    "container_id": c.short_id,
                    "status": c.status,
                    "bot_type": c.labels.get("bot_type", "unknown"),
                    "version": c.labels.get("bot_version", "unknown"),
                    "internal_port": internal_port,
                    "external_port": external_port,
                    "image": c.image.tags[0] if c.image.tags else "unknown",
                    "created": c.attrs.get("Created", "N/A")
                })

            return {"total": len(bots), "bots": bots}
        except Exception as e:
            return {"error": True, "detail": str(e), "bots": []}