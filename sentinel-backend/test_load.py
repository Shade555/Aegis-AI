import asyncio
import os
import uuid
import sys
from pathlib import Path

# Add src to path
sys.path.append(r"C:\Users\slevi\Documents\Kaggle_agent_dev\sentinel-backend\src")

from aegis.application.execution.manager import SessionManager
from aegis.application.services.analysis import AnalysisService

async def test_load():
    try:
        sm = SessionManager()
        service = AnalysisService(sm)
        print(f"Loaded {len(sm._sessions)} sessions!")
    except Exception as e:
        print(f"FAILED TO LOAD: {e}")

if __name__ == "__main__":
    asyncio.run(test_load())
