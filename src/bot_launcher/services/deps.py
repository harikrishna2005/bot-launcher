import os
from bot_launcher.services.local_strategy import LocalSubprocessStrategy
from bot_launcher.services.docker_strategy import DockerExecutionStrategy

# --- Singleton Instances ---
# These are initialized ONLY when the file is first imported
_DOCKER_STRATEGY = None
_LOCAL_STRATEGY = LocalSubprocessStrategy()


def get_execution_strategy():
    """
    Get the appropriate execution strategy based on environment.
    Returns LocalSubprocessStrategy if not in Docker, otherwise DockerExecutionStrategy.
    """
    global _DOCKER_STRATEGY

    if os.path.exists('/var/run/docker.sock'):
        # Lazy initialization: Create only if needed, then reuse
        if _DOCKER_STRATEGY is None:
            print("🐳 Initializing Docker Client Singleton...")
            _DOCKER_STRATEGY = DockerExecutionStrategy()
        return _DOCKER_STRATEGY

    print("💻 Using Local Subprocess Strategy")
    return _LOCAL_STRATEGY