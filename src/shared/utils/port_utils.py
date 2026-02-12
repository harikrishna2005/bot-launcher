import socket

def get_next_available_port() -> int:
    """Finds any random free port on the host system."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Binding to port 0 tells the OS to assign a free ephemeral port
        s.bind(('', 0))
        return s.getsockname()[1]