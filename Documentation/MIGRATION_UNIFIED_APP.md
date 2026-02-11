# Migration to Unified app.py

## ✅ Changes Made

### 1. **Created Unified `app.py`**
📄 `src/bot_launcher/app.py`

Combined `app_local.py` and `app_docker.py` into a single file that:
- Automatically detects the environment (local vs Docker)
- Uses the appropriate execution strategy via dependency injection
- Provides consistent API endpoints regardless of environment
- Includes comprehensive docstrings and health check endpoints

### 2. **Updated `cli.py`**
📄 `src/bot_launcher/cli.py`

- Simplified to use `bot_launcher.app:app` instead of separate apps
- Removed unnecessary Docker client initialization
- Removed the `exit(1)` when not in Docker (now supports both modes)
- Added better logging messages

---

## 🗑️ Files to Delete (Optional)

These files are now obsolete and can be safely removed:

```
src/bot_launcher/app_local.py
src/bot_launcher/app_docker.py
```

**Note:** Keep them for now if you want to reference the old implementation. They won't interfere with the new unified app.

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────┐
│         CLI Entry Point                 │
│    poetry run run-manager               │
│    (cli.py → start_server())            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Unified FastAPI App             │
│         (app.py)                        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│    Strategy Auto-Selection              │
│    (deps.py → get_execution_strategy()) │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌─────────────┐  ┌──────────────────┐
│   Local     │  │     Docker       │
│  Subprocess │  │    Container     │
│  Strategy   │  │    Strategy      │
└─────────────┘  └──────────────────┘
```

---

## 🚀 How to Use

### **Local Development** (No Docker)
```bash
# Start the manager API
poetry run run-manager

# API will be available at:
# http://localhost:9501
# http://localhost:9501/docs (Swagger UI)

# The app will:
# ✅ Use LocalSubprocessStrategy
# ✅ Launch bots via: poetry run run-{bot_type}
# ✅ Enable reload for development
```

### **Docker Deployment**
```bash
# Start with docker-compose
docker-compose up -d

# API will be available at:
# http://localhost:9501
# http://localhost:9501/docs (Swagger UI)

# The app will:
# ✅ Use DockerExecutionStrategy
# ✅ Launch bots as Docker containers
# ✅ Disable reload for production
```

---

## 🔍 Environment Detection

The system automatically detects which mode to run in:

```python
# In deps.py
if os.path.exists('/var/run/docker.sock'):
    # Docker mode - use DockerExecutionStrategy
else:
    # Local mode - use LocalSubprocessStrategy
```

---

## 📡 API Endpoints (Unified)

All endpoints work in both local and Docker modes:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Root endpoint with API info |
| `GET` | `/health` | Health check |
| `GET` | `/status` | Manager and bot status |
| `GET` | `/bots` | List all bots |
| `POST` | `/launch` | Launch a new bot |
| `POST` | `/stop/{bot_name}` | Stop a running bot |
| `GET` | `/docs` | Swagger UI (auto-generated) |
| `GET` | `/v1/bots/` | List bots (via router) |
| `GET` | `/v1/bots/status` | Bot status (via router) |
| `GET` | `/v1/launcher/status` | Launcher status |
| `POST` | `/v1/launcher/launch` | Launch bot (via router) |
| `POST` | `/v1/launcher/stop/{bot_name}` | Stop bot (via router) |

---

## 🧪 Testing the Changes

### 1. **Test Local Mode**
```bash
# Make sure you're NOT in Docker
poetry run run-manager

# You should see:
# 💻 Running in Local mode
# 💻 Using Local Subprocess Strategy
# 🚀 Starting Bot Manager API on http://0.0.0.0:9501
```

### 2. **Test Docker Mode**
```bash
# Build and run
docker-compose build
docker-compose up -d

# Check logs
docker-compose logs -f manager

# You should see:
# 🐳 Running in Docker mode
# 🐳 Initializing Docker Client Singleton...
# 🚀 Starting Bot Manager API on http://0.0.0.0:9501
```

### 3. **Test API Endpoints**
```bash
# Health check
curl http://localhost:9501/health

# Get status
curl http://localhost:9501/status

# List bots
curl http://localhost:9501/v1/bots/

# Launch a bot (example)
curl -X POST http://localhost:9501/v1/launcher/launch \
  -H "Content-Type: application/json" \
  -d '{
    "bot_name": "test-bot",
    "bot_type": "rebalancing",
    "config": {"interval": 60}
  }'
```

---

## ✨ Benefits

### 1. **Simplified Codebase**
- ❌ Before: 2 separate app files (app_local.py, app_docker.py)
- ✅ After: 1 unified app.py

### 2. **No Duplication**
- All endpoints defined once
- Consistent behavior across environments
- Easier to maintain and test

### 3. **Automatic Environment Detection**
- No manual configuration needed
- Works seamlessly in both local and Docker environments
- Strategy pattern handles all the differences

### 4. **Better Developer Experience**
- Single source of truth
- Easier to add new endpoints
- Consistent API documentation

### 5. **Production Ready**
- Health check endpoint
- Proper error handling
- Comprehensive logging

---

## 🔧 Configuration Files Updated

### ✅ `cli.py`
- Now uses `bot_launcher.app:app` for both modes
- Removed redundant environment checks
- Better console output

### ✅ `app.py` (New)
- Unified FastAPI application
- Auto-detects execution strategy
- Includes health check and root endpoints

### ✅ No Changes Needed
- `deps.py` - Already handles strategy selection
- `local_strategy.py` - Works as-is
- `docker_strategy.py` - Works as-is
- `docker-compose.yml` - Already uses `run-manager`
- `Dockerfile` - No changes needed

---

## 📝 Summary

The refactoring is complete! You now have:

1. ✅ **Single unified `app.py`** that works in both environments
2. ✅ **Automatic environment detection** via the strategy pattern
3. ✅ **No code duplication** between local and Docker modes
4. ✅ **Backwards compatible** - all existing endpoints still work
5. ✅ **Ready to deploy** - works with existing docker-compose.yml

You can safely delete `app_local.py` and `app_docker.py` or keep them for reference.

