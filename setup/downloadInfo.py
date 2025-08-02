# downloads and updates info.json
import json
import shutil
import requests
import tempfile
from enum import Enum
from pathlib import Path
from setup.mylogging import LOGGER as logger

LINK = "https://raw.githubusercontent.com/acemavrick/uil-dl/refs/heads/main/data/info.json"
# LINK = "http://localhost:8000/info.json"


class UpdateResult(Enum):
    UPDATED = "updated"
    NOT_UPDATED = "not_updated"
    ERROR = "error"


def download_info(path: Path) -> tuple[bool, str | None]:
    """Download the latest info.json from GitHub."""
    try:
        logger.info(f"Downloading info.json from {LINK} ----> {path}")
        response = requests.get(LINK, timeout=10)
        response.raise_for_status()
        with open(path, "w") as f:
            f.write(response.text)
        return True, None
    except (requests.RequestException, IOError) as e:
        err_msg = f"Failed to download info.json: {e}"
        logger.error(err_msg)
        return False, err_msg


def update_info_from_online(data_dir: Path) -> tuple[UpdateResult, str | None]:
    """
    Downloads the latest info.json and updates the local one if needed.

    Returns a tuple of (UpdateResult, optional error message).
    """
    temp_path = Path(tempfile.gettempdir()) / "info.json"
    downloaded, error_msg = download_info(temp_path)
    if not downloaded:
        return UpdateResult.ERROR, error_msg

    try:
        with open(temp_path, "r") as f:
            online_info = json.load(f)
        online_version = online_info.get("version", 0)

        local_info_path = data_dir / "info.json"
        if local_info_path.exists():
            try:
                with open(local_info_path, "r") as f:
                    local_info = json.load(f)
                local_version = local_info.get("version", 0)
            except (IOError, json.JSONDecodeError) as e:
                logger.warning(
                    f"Could not read local info.json, will treat as missing. Error: {e}"
                )
                local_version = 0

            logger.info(
                f"local_version: {local_version}, online_version: {online_version}"
            )
            if local_version < online_version:
                logger.info(f"Updating local: {local_version} -> {online_version}")
                shutil.copy(temp_path, local_info_path)
                return UpdateResult.UPDATED, None
            else:
                logger.info("No update needed")
                return UpdateResult.NOT_UPDATED, None
        else:
            logger.info("No local info.json found, creating one")
            shutil.copy(temp_path, local_info_path)
            return UpdateResult.UPDATED, None
    except (IOError, json.JSONDecodeError, shutil.Error) as e:
        error_message = f"Failed to process info.json: {e}"
        logger.error(error_message)
        return UpdateResult.ERROR, error_message
