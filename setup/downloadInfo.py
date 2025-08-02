# downloads and updates info.json if needed
import json
import shutil
import requests
import tempfile
from pathlib import Path
from setup.mylogging import LOGGER as logger

# LINK = "https://raw.githubusercontent.com/acemavrick/uil-dl/refs/heads/main/data/info.json"
LINK = "http://localhost:8000/info.json"

def download_info(path: Path):
    """Download the latest info.json from GitHub."""
    try:
        logger.info(f"Downloading info.json from {LINK} ----> {path}")
        response = requests.get(LINK, timeout=10)
        response.raise_for_status()
        with open(path, "w") as f:
            f.write(response.text)
        return True
    except (requests.RequestException, IOError) as e:
        logger.error(f"Failed to download info.json: {e}")
        return False

def update_info_from_online(data_dir: Path):
    """Downloads the latest info.json from GitHub and updates the local info.json if needed."""
    temp_path = Path(tempfile.gettempdir()) / "info.json"
    downloaded = download_info(temp_path)
    if not downloaded:
        logger.error("Failed to download info.json")
        return False
    
    # load the online info.json
    with open(temp_path, "r") as f:
        online_info = json.load(f)
    
    # load the local info.json, if it exists
    if (data_dir / "info.json").exists():
        with open(data_dir / "info.json", "r") as f:
            local_info = json.load(f)
        
        local_version = local_info.get("version", 0)
        online_version = online_info.get("version", 0)

        logger.info(f"local_version: {local_version}, online_version: {online_version}")
        if local_version < online_version:
            logger.info(f"Updating local: {local_version} -> {online_version}")

            # copy the online info.json to the local info.json
            shutil.copy(temp_path, data_dir / "info.json")

            return True
        else:
            logger.info("No update needed")
            return False
    else:
        logger.info("No local info.json found, creating one")
        shutil.copy(temp_path, data_dir / "info.json")
        return True