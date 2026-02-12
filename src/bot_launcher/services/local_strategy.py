import os
import json
import subprocess
from typing import Dict, Any
import psutil

from bot_launcher.services.base_strategy import ExecutionStrategy
from shared.config import bot_env_settings
from shared.utils.port_utils import get_next_available_port


class LocalSubprocessStrategy(ExecutionStrategy):
    """Strategy for launching bots as local subprocesses using Poetry."""

    def __init__(self):
        # Tracking for local processes: {bot_name: {"pid": int, "type": str, "port": int}}
        self.active_processes: Dict[str, Dict[str, Any]] = {}

    def launch_bot(self, bot_name: str, bot_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Launch a bot as a subprocess with matching environment injection."""
        if bot_name in self.active_processes:
            return {
                "success": False,
                "message": f"Bot '{bot_name}' is already active.",
                "status_code": 400
            }

        # 1. Technical Configuration (Matching Docker Strategy)
        host = bot_env_settings.host
        internal_port = bot_env_settings.internal_port

        # For local runs, internal and external ports are the same on your host machine
        external_port = bot_env_settings.external_port or get_next_available_port()

        version = bot_env_settings.version
        script_command = f"run-{bot_type}"

        # 2. Prepare BOT_CONFIG (Keep it clean, just trading data)
        bot_config_json = json.dumps({
            "bot_name": bot_name,
            "bot_type": bot_type,
            "config": config
        }, indent=2)

        print(f"🛠 Launching {bot_name} locally on port {external_port}")

        try:
            # 3. Environment Injection (Matching Docker Strategy names)
            process_env = {
                **os.environ,
                "BOT_CONFIG": bot_config_json,
                "APP_HOST": host,
                "APP_INTERNAL_PORT": str(internal_port),
                "APP_EXTERNAL_PORT": str(external_port),
                "APP_VERSION": version,
                "APP_DOCKER_NETWORK": "local_host",  # Placeholder for consistency
                "PYTHONUNBUFFERED": "1"
            }

            process = subprocess.Popen(
                ["poetry", "run", script_command],
                env=process_env,
                start_new_session=True,
                stdout=None,
                stderr=None
            )

            # Store metadata locally since we don't have Docker Labels
            self.active_processes[bot_name] = {
                "pid": process.pid,
                "bot_type": bot_type,
                "version": version,
                "port": external_port
            }

            return {
                "success": True,
                "bot_name": bot_name,
                "pid": process.pid,
                "assigned_port": external_port,
                "status": "running"
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to launch {bot_name}. Check if '{script_command}' exists.",
                "detail": str(e),
                "status_code": 500
            }

    def stop_bot(self, bot_name: str) -> Dict[str, Any]:
        """Stop a running bot by terminating its process and all child processes."""
        bot_data = self.active_processes.get(bot_name)

        if not bot_data:
            return {
                "error": True,
                "message": f"Bot '{bot_name}' not found.",
                "status_code": 404
            }

        pid = bot_data["pid"]

        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)

            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass

            parent.terminate()
            psutil.wait_procs([parent] + children, timeout=3)

            # Force kill if still alive
            if parent.is_running():
                parent.kill()

            del self.active_processes[bot_name]
            return {
                "error": False,
                "message": f"Bot '{bot_name}' stopped successfully",
                "bot_name": bot_name
            }

        except (psutil.NoSuchProcess, ProcessLookupError):
            self.active_processes.pop(bot_name, None)
            return {"error": False, "message": "Process already dead. Cleaned up tracking."}
        except Exception as e:
            return {"error": True, "message": str(e), "status_code": 500}

    def get_status(self) -> Dict[str, Any]:
        """Get summarized status matching the Docker version structure."""
        running_bots = []
        for name, data in self.active_processes.items():
            try:
                # Check if still actually alive
                p = psutil.Process(data["pid"])
                if p.is_running():
                    running_bots.append({
                        "name": name,
                        "status": p.status(),
                        "bot_type": data["bot_type"],
                        "id": str(data["pid"])
                    })
            except psutil.NoSuchProcess:
                continue

        return {
            "manager": "running_locally",
            "mode": "subprocess",
            "total_bots": len(running_bots),
            "running_bots": running_bots
        }

    def list_bots(self) -> Dict[str, Any]:
        """List active bots with technical details matching Docker's list_bots output."""
        bots = []
        for name, data in self.active_processes.items():
            try:
                process = psutil.Process(data["pid"])
                is_alive = process.is_running()

                bots.append({
                    "bot_name": name,
                    "container_id": str(data["pid"]),  # Using PID as ID for consistency
                    "status": "running" if is_alive else "dead",
                    "bot_type": data["bot_type"],
                    "version": data["version"],
                    "host_port": data["port"],
                    "created": "Local Process",
                    "state": process.status() if is_alive else "unknown"
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                bots.append({
                    "bot_name": name,
                    "container_id": str(data["pid"]),
                    "status": "dead",
                    "bot_type": data["bot_type"],
                    "host_port": data["port"],
                    "version": data["version"]
                })

        return {
            "total": len(bots),
            "bots": bots
        }