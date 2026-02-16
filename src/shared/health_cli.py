import sys
import httpx
import asyncio

async def check_local_health():
    try:
        async with httpx.AsyncClient() as client:
            # Docker checks usually hit localhost inside the container
            response = await client.get("http://localhost:8000/health", timeout=2.0)
            if response.status_code == 200:
                sys.exit(0)  # Docker sees this as HEALTHY
            sys.exit(1)      # Docker sees this as UNHEALTHY
    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(check_local_health())