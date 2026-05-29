"""
Backend package root.
Ensures the backend directory is on sys.path for absolute imports.
"""
import sys
import os

# Add the backend directory to sys.path so that 'schedulers', 'workload_generator',
# 'rl_agent' etc. can be imported as top-level packages regardless of how
# uvicorn or pytest invokes the code.
_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
