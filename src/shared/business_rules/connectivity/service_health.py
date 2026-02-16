from shared.domain.specifications.connectivity_specs import IConnectivitySpecification
import httpx

class ServiceHealthRule(IConnectivitySpecification):
    """
    Checks the /health endpoint of a service.
    Matches Docker's healthcheck logic.
    """
    def __init__(self, service_name: str, base_url: str):
        self.service_name = service_name
        self.base_url = base_url
        self._error = ""

    async def is_satisfied(self, context: any = None) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                # Use the same logic Docker uses
                response = await client.get(f"{self.base_url}/health", timeout=2.0)
                if response.status_code == 200:
                    return True
                self._error = f"{self.service_name} reported status {response.status_code}"
                return False
        except Exception:
            self._error = f"{self.service_name} is unreachable (Network Error)"
            return False

    def get_error(self) -> str:
        return self._error