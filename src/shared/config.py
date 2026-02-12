from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class BotEnvSettings(BaseSettings):
    """
    Standard environment variables passed to every bot.
    Pydantic automatically reads these from the OS environment.
    """
    # Use Field aliases so the code stays clean even if the ENV name is long
    host: str = Field(alias="APP_HOST", default="0.0.0.0")
    external_port: Optional[int] = Field(alias="APP_EXTERNAL_PORT", default=None)
    internal_port: int = Field(alias="APP_INTERNAL_PORT", default=59000)
    version: str = Field(alias="APP_VERSION", default="develop")
    network: str = Field(alias="APP_DOCKER_NETWORK", default="my_home_network")

    # This tells Pydantic to ignore case and look for these specific names
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True
    )


# Create a single instance to be imported elsewhere
bot_env_settings = BotEnvSettings()