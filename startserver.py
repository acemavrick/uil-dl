import asyncio
import logging
from hypercorn.asyncio import serve
from hypercorn.config import Config
from backend.mainapp import app
from pathlib import Path
from fastapi.staticfiles import StaticFiles

# enable logging
logging.basicConfig(level=logging.INFO)

async def _run() -> None:
    """start hypercron server for mainapp:app"""
    config = Config()
    config.bind = ["127.0.0.1:8000"]
    config.reload = True
    config.accesslog = "-"  # log to stdout

    # serve frontend/dist
    frontend_dist = Path("frontend") / "dist"
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
        print(f"Serving frontend from {frontend_dist}")
    else:
        print(f"Frontend dist not found at {frontend_dist}")
    
    await serve(app, config)

if __name__ == "__main__":
    asyncio.run(_run())

