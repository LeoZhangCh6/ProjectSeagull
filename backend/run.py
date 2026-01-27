"""Run the FastAPI backend server."""

import os
import sys

# Add project root to path
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Load environment variables from .env file
from dotenv import load_dotenv

# Load from backend/.env
env_path = os.path.join(_HERE, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"[Config] Loaded environment from: {env_path}")
else:
    print(f"[Config] No .env file found at: {env_path}")

# Also try project root .env as fallback
root_env_path = os.path.join(_PROJECT_ROOT, ".env")
if os.path.exists(root_env_path):
    load_dotenv(root_env_path, override=False)
    print(f"[Config] Loaded environment from: {root_env_path}")

# Verify required keys
required_keys = ["DATABASE_URL"]
optional_keys = ["MASSIVE_API_KEY", "POLYGON_API_KEY", "NASDAQ_DATA_LINK_API_KEY"]

for key in required_keys:
    if not os.environ.get(key):
        print(f"[Config] WARNING: Required environment variable {key} is not set!")

for key in optional_keys:
    if os.environ.get(key):
        print(f"[Config] {key} is set")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[_HERE],
    )
