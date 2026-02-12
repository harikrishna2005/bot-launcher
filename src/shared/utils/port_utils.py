"""Utility functions for port management."""
import socket
from typing import Optional


def is_port_available(port: int, host: str = '127.0.0.1') -> bool:
    """Check if a port is available for binding.

    Args:
        port: Port number to check
        host: Host address to check (default: localhost)

    Returns:
        True if port is available, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            sock.bind((host, port))
            return True
    except OSError:
        return False


def get_available_port(start_port: int = 59001, max_attempts: int = 100, host: str = '127.0.0.1') -> Optional[int]:
    """Find an available port starting from the given port number.

    Args:
        start_port: Starting port number (default: 59001)
        max_attempts: Maximum number of ports to try (default: 100)
        host: Host address to check (default: localhost)

    Returns:
        Available port number, or None if no port found within max_attempts

    Example:
        >>> port = get_available_port()
        >>> print(f"Available port: {port}")
        Available port: 59001
    """
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(port, host):
            print(f"✅ Found available port: {port}")
            return port

    print(f"❌ No available port found between {start_port} and {start_port + max_attempts - 1}")
    return None


def get_next_available_port(start_port: int = 59001, exclude_ports: list[int] = None, host: str = '127.0.0.1') -> Optional[int]:
    """Find the next available port, excluding specific ports.

    Args:
        start_port: Starting port number (default: 59001)
        exclude_ports: List of ports to exclude from selection
        host: Host address to check (default: localhost)

    Returns:
        Available port number, or None if no port found

    Example:
        >>> port = get_next_available_port(exclude_ports=[59001, 59002])
        >>> print(f"Available port: {port}")
        Available port: 59003
    """
    if exclude_ports is None:
        exclude_ports = []

    port = start_port
    max_port = start_port + 1000  # Safety limit

    while port < max_port:
        if port not in exclude_ports and is_port_available(port, host):
            print(f"✅ Found available port: {port} (excluded: {exclude_ports})")
            return port
        port += 1

    print(f"❌ No available port found between {start_port} and {max_port}")
    return None

