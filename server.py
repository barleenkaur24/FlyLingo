"""
Root forwarder for FlyLingo ASGI application.
Allows running 'python -m uvicorn server:app' directly from the P6 root directory.
"""
import os
import sys

# Add FlyLingo directory to sys.path
FLY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "FlyLingo")
if os.path.isdir(FLY_DIR) and FLY_DIR not in sys.path:
    sys.path.insert(0, FLY_DIR)

# Import app from FlyLingo.server
from FlyLingo.server import app

__all__ = ["app"]
