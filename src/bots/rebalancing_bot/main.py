import os
import json
import asyncio

import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from shared.launcher import run_app

# --- 1. Load Configuration ---
# This is sent by the Manager API via Environment Variables
raw_config = os.getenv("BOT_CONFIG", "{}")
config = json.loads(raw_config)


# --- 2. Trading Strategy Logic ---
async def rebalancing_logic():
    """Simulates the rebalancing bot's brain."""
    bot_name = config.get("bot_name", "Unknown Bot")
    assets = config.get("assets", ["BTC", "ETH"])
    interval = config.get("interval", 10)  # Seconds

    print(f"🚀 [STRATEGY] {bot_name} started with assets: {assets}")

    while True:
        # This is where your CCXT / Indian Connector code will eventually go
        print(f"📊 [{bot_name}] Checking prices and rebalancing {assets}...")

        # Simulating work
        await asyncio.sleep(interval)


# --- 3. Life Cycle Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run the trading loop in the background
    task = asyncio.create_task(rebalancing_logic())
    yield
    # Shutdown: Stop the loop gracefully
    task.cancel()
    print("🛑 Bot strategy stopped.")


# --- 4. FastAPI App ---
app = FastAPI(title=f"Bot: {config.get('bot_name', 'Rebalance')}", lifespan=lifespan)


@app.get("/status")
def get_bot_status():
    """Used by the Manager to check if the bot is healthy"""
    return {
        "bot_name": config.get("bot_name"),
        "status": "running",
        "config": config
    }


# # --- 5. CLI Entry Point ---
# def main():
#     # Use the shared launcher you created!
#     # Port is 59001 as we discussed for the first bot
#     # run_app("bots.rebalance_bot", port=59001)
#     uvicorn.run("bots.rebalancing_bot.main:main", host="0.0.0.0", port=59001, reload=True)


# if __name__ == "__main__":
#     main()