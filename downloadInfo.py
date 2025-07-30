# downloads and updates info.json if needed
import json
import requests
import tempfile
import logging
from pathlib import Path

# LINK = "https://raw.githubusercontent.com/acemavrick/uil-dl/refs/heads/data/info.json"
LINK = "https://raw.githubusercontent.com/acemavrick/uil-dl/refs/heads/improvements/data/info.json"
# LINK = "http://localhost:8000/info.json"

# configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

def update_info_from_online():
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
    if Path("data/info.json").exists():
        with open("data/info.json", "r") as f:
            local_info = json.load(f)
        
        local_version = local_info.get("version", 0)
        online_version = online_info.get("version", 0)

        logger.info(f"local_version: {local_version}, online_version: {online_version}")
        if local_version < online_version:
            logger.info(f"Updating local: {local_version} -> {online_version}")
            # update the local info.json
            with open("data/info.json", "w") as f:
                json.dump(online_info, f, indent=4)
            return True
        else:
            logger.info("No update needed")
            return False
    else:
        logger.info("No local info.json found, creating one")
        with open("data/info.json", "w") as f:
            json.dump(online_info, f, indent=4)
        return True

if __name__ == "__main__":
    update_info_from_online()