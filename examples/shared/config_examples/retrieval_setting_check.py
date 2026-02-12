from shared.config import bot_env_settings


if __name__ == "__main__":
    print("config printing")
    print(f"Default Host : {bot_env_settings.host}")
    print(f"Default external : {bot_env_settings.external_port}")
    print(f"Default internal : {bot_env_settings.internal_port}")
    print(f"Default version : {bot_env_settings.version}")
    print(f"Default network : {bot_env_settings.network}")
