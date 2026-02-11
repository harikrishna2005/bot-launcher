import os
import json
import subprocess
from typing import Dict, Any
import psutil

from bot_launcher.services.base_strategy import ExecutionStrategy


class LocalSubprocessStrategy(ExecutionStrategy):
    """Strategy for launching bots as local subprocesses using Poetry."""

    def __init__(self):
        # PID Tracking for local processes
        self.active_processes: Dict[str, int] = {}

    def launch_bot(self, bot_name: str, bot_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Launch a bot as a subprocess using Poetry."""
        if bot_name in self.active_processes:
            return {
                "error": True,
                "message": f"Bot '{bot_name}' is already active.",
                "status_code": 400
            }

        # Dynamically builds the command: "run-rebalancing", "run-grid", etc.
        script_command = f"run-{bot_type}"
        print(f"🛠 Launching {bot_name} via: poetry run {script_command}")

        try:
            process = subprocess.Popen(
                ["poetry", "run", script_command],
                env={
                    **os.environ,
                    "BOT_CONFIG": json.dumps(config),
                    "PYTHONUNBUFFERED": "1"
                },
                start_new_session=True,
                stdout=None,  # Output goes to your current terminal
                stderr=None
            )

            self.active_processes[bot_name] = process.pid
            return {
                "error": False,
                "message": "Bot launched successfully",
                "bot_name": bot_name,
                "pid": process.pid,
                "bot_type": bot_type
            }

        except Exception as e:
            return {
                "error": True,
                "message": f"Failed to launch bot. Check if '{script_command}' exists in pyproject.toml",
                "detail": str(e),
                "status_code": 500
            }

    def stop_bot(self, bot_name: str) -> Dict[str, str]:
        """Stop a running bot by terminating its process and all child processes."""
        pid = self.active_processes.get(bot_name)

        if not pid:
            return {
                "error": True,
                "message": f"Bot '{bot_name}' not found in active processes.",
                "status_code": 404
            }

        try:
            # Use psutil to kill the process and all its children
            try:
                parent = psutil.Process(pid)
                children = parent.children(recursive=True)

                # Terminate all child processes first
                for child in children:
                    try:
                        child.terminate()
                        print(f"🔸 Terminated child process {child.pid}")
                    except psutil.NoSuchProcess:
                        pass

                # Terminate the parent process
                parent.terminate()
                print(f"🔸 Terminated parent process {pid}")

                # Wait for processes to terminate gracefully (max 3 seconds)
                gone, alive = psutil.wait_procs([parent] + children, timeout=3)

                # Force kill any processes that didn't terminate
                for p in alive:
                    try:
                        p.kill()
                        print(f"⚠️ Force killed process {p.pid}")
                    except psutil.NoSuchProcess:
                        pass

                print(f"✅ Successfully stopped bot '{bot_name}' and {len(children)} child process(es)")

            except psutil.NoSuchProcess:
                print(f"⚠️ Process {pid} not found, may have already terminated")

            del self.active_processes[bot_name]
            return {
                "error": False,
                "message": f"Bot '{bot_name}' and all child processes stopped successfully",
                "bot_name": bot_name,
                "pid": pid
            }

        except ProcessLookupError:
            # Process already died, just clean up the dict
            self.active_processes.pop(bot_name, None)
            return {
                "error": False,
                "message": f"Process for '{bot_name}' was not running. Removed from tracking.",
                "bot_name": bot_name
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
        return {
            "manager": "running_locally",
            "mode": "subprocess",
            "running_bots": self.active_processes,
            "total_bots": len(self.active_processes)
        }

    def list_bots(self) -> Dict[str, Any]:
        """List all active bots with their details."""
        bots = []
        for bot_name, pid in self.active_processes.items():
            # Check if process is still alive using psutil
            try:
                process = psutil.Process(pid)
                is_alive = process.is_running()
                status = process.status() if is_alive else "dead"

                # Count child processes (e.g., Uvicorn workers)
                children_count = len(process.children(recursive=True)) if is_alive else 0

                bots.append({
                    "bot_name": bot_name,
                    "pid": pid,
                    "status": status,
                    "child_processes": children_count
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                bots.append({
                    "bot_name": bot_name,
                    "pid": pid,
                    "status": "dead",
                    "child_processes": 0
                })

        return {
            "total": len(bots),
            "bots": bots
        }

