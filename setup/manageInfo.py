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
        response = requests.get(LINK, timeout=10, verify=False)
        response.raise_for_status()
        with open(path, "w") as f:
            f.write(response.text)
        return True, None
    except (requests.RequestException, IOError) as e:
        err_msg = f"Failed to download info.json: {e}"
        logger.error(err_msg)
        return False, err_msg


def update_info(data_dir: Path) -> tuple[UpdateResult, str | None]:
    """
    Downloads the latest info.json and updates the local one if needed.
    Creates a local info.json if it doesn't exist.

    Returns a tuple of (UpdateResult, optional error message).
    """
    temp_path = Path(tempfile.gettempdir()) / "info.json"
    downloaded, error_msg = download_info(temp_path)
    if not downloaded:
        logger.error(f"Failed to download info.json: {error_msg}")
        # could not download. check for local info.json, and if it doesn't exist, use embedded default
        local_info_path = data_dir / "info.json"
        if local_info_path.exists():
            logger.info(f"Local info.json exists: {local_info_path}")
            return UpdateResult.NOT_UPDATED, None
        else:
            # use embedded default info.json if online download fails
            from localinfojson import INFOJSON
            logger.info("Using embedded default info.json")
            with open(local_info_path, "w") as f:
                f.write(INFOJSON)
            logger.info(f"Created local info.json: {local_info_path}")
            return UpdateResult.UPDATED, "Using embedded default info.json"

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
            # use embedded default info.json if online download fails
            from localinfojson import INFOJSON
            logger.info("No local info.json found, creating one")
            try:
                # first try to use the downloaded version
                shutil.copy(temp_path, local_info_path)
            except (IOError, shutil.Error) as e:
                # fallback to embedded version if copy fails
                logger.warning(f"Failed to copy downloaded info.json: {e}, using embedded version")
                with open(local_info_path, "w") as f:
                    f.write(INFOJSON)
            return UpdateResult.UPDATED, None
    except (IOError, json.JSONDecodeError, shutil.Error) as e:
        error_message = f"Failed to process info.json: {e}"
        logger.error(error_message)
        return UpdateResult.ERROR, error_message
    

if __name__ == "__main__":
    import shutil
    from pathlib import Path
    import tempfile

    # test config vars to control environment
    CREATE_LOCAL_INFO = False  # create a starting info.json in data dir
    ALLOW_INTERNET = False     # if true, mock download succeeds; else it fails
    
    # create a test environment using the config vars
    def setup_test_env(create_local: bool, allow_internet: bool):
        # make a temp data directory
        temp_dir = Path(tempfile.mkdtemp())

        # optionally seed local info.json using embedded default
        if create_local:
            from setup.localinfojson import INFOJSON

            local_path = temp_dir / "info.json"
            with open(local_path, "w") as f:
                f.write(INFOJSON)

        # save original and install a mock downloader
        original_download = download_info

        def mock_download(path: Path) -> tuple[bool, str | None]:
            # when blocked, simulate a network error
            if not allow_internet:
                logger.info("TESTING: internet blocked for test; mock download fails")
                return False, "internet blocked for test"
            # when allowed, use download_info to download the file
            try:
                downloaded, error_msg = original_download(path)
                return downloaded, error_msg
            except Exception as e:
                return False, f"failed to download mock download: {e}"

        globals()["download_info"] = mock_download
        return temp_dir, original_download

    # clean up test environment
    def cleanup_test_env(temp_dir: Path, original_download):
        # restore original download function
        globals()["download_info"] = original_download
        # remove temporary directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    # run a simple test with the configured environment
    test_dir, orig_download = setup_test_env(CREATE_LOCAL_INFO, ALLOW_INTERNET)
    try:
        print(
            f"Testing with create_local={CREATE_LOCAL_INFO}, allow_internet={ALLOW_INTERNET} in {test_dir}"
        )
        result, msg = update_info(test_dir)
        print(f"Result: {result}, Message: {msg}")
    finally:
        cleanup_test_env(test_dir, orig_download)