import sys
import portalocker
import json
import setup.mylogging
from pathlib import Path
from platformdirs import user_data_path

# get user directory
data_path = user_data_path(appname="uil-dl", appauthor="acemavrick", ensure_exists=True)
downloads_dir_path = None

if not data_path.exists():
    print("xx user data directory does not exist. creating...")
    data_path.mkdir(parents=True, exist_ok=True)
    print("OK user data directory created")

print(f"Data path: {data_path.as_uri()}")
print("This is where the app stores logs, config, and other important files.\
     Do not modify this directory unless you know what you are doing.\n")


# configure logging to file
setup.mylogging.setup_logging(data_path)

# verify config
def verify_config():
    global data_path, downloads_dir_path
    print()
    config_file = data_path / "config.cfg"
    downloads_dir = Path.home() / "Downloads" / "uil-dl"
    config_data = {
        "default_download_dir": downloads_dir.as_posix(),
        "download_dir": downloads_dir.as_posix(),
    }

    ## check if exists
    if not config_file.exists():
        print("xx config file does not exist. creating...")
        config_file.touch()
        with open(config_file, "w") as f:
            json.dump(config_data, f, sort_keys=True)
        print("OK config file created")
    else:
        opening_went_well = False
        with open(config_file, "r") as f:
            try:
                loaded_config = json.load(f)
                opening_went_well = True
            except json.JSONDecodeError:
                print("xx config file is not valid json. recreating config file...")
                config_file.touch()
                with open(config_file, "w") as f:
                    json.dump(config_data, f, sort_keys=True)
                print("OK config file created")

        ## verify everything is in place
        if opening_went_well:
            print("OK config file exists")

            changed_config = False

            for key, value in config_data.items():
                if not loaded_config.get(key):
                    print(f"xx {key} is not set. setting...")
                    loaded_config[key] = value
                    changed_config = True
                    print(f"OK {key} set")
                else:
                    print(f"OK {key} is in place")

            if changed_config:
                with open(config_file, "w") as f:
                    json.dump(loaded_config, f, sort_keys=True)
                print("OK config saved")
            else:
                print("OK config proper")

    with open(config_file, "r") as f:
        config_data = json.load(f)
    downloads_dir_path = Path(config_data["download_dir"])

updated_info = False

def verify_info_json():
    global data_path, updated_info
    import setup.downloadInfo as downloadInfo
    from setup.downloadInfo import UpdateResult

    result, err_msg = downloadInfo.update_info_from_online(data_path)
    print()
    if result == UpdateResult.UPDATED:
        print("OK info.json updated")
        updated_info = True
    elif result == UpdateResult.NOT_UPDATED:
        print("OK info.json not updated")
    elif result == UpdateResult.ERROR:
        print(f"xx Failed to update info.json. Check logs for details")
        setup.mylogging.LOGGER.error(f"When updating info.json: \n {err_msg}")
        # check if info.json exists... if it does, then attempt to load it (see if it's valid)
        if (data_path / "info.json").exists():
            try:
                with open(data_path / "info.json", "r") as f:
                    json.load(f)
                print("OK local info.json is valid")
                return
            except json.JSONDecodeError:
                print("xx info.json is not valid.")
        else:
            print("xx no local info.json found")
        
        print("-- No proper info.json found. The app will not work properly.")
        sys.exit(1)


def verify_info_db():
    global data_path, updated_info
    print()
    import setup.buildDB as buildDB
    if updated_info or not (data_path / "info.db").exists():
        buildDB.create_database(data_path / "info.json", data_path / "info.db", interactive=False)
    else:
        print("OK info.db exists")

def find_free_port(port_range=range(5000, 60000)):
    import socket
    for i in port_range:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("127.0.0.1", i))
            s.close()
            return i
        except OSError:
            continue
    return None

def start_app():
    print()
    import threading
    import webapp.app as myapp

    def print_app_started(app_thread):
        if app_thread.is_alive():
            print(f"""
UIL-DL is now running.
Access it through your browser at: http://127.0.0.1:{port}
Downloads directory: {downloads_dir_path.as_uri()}
Log file: {(data_path / "uil-dl.log").as_uri()}
Press Ctrl+C to shutdown
            """)
        else:
            print("xx app failed to start")
            print("Press Ctrl+C to shutdown")

    # find a free port
    port = find_free_port()

    if port is None:
        print("xx no free port found")
        return

    print(f"OK port {port} found")
    
    # start app in a separate thread
    app_thread = threading.Thread(target=myapp.app.run, kwargs={"debug": False, "port": port})
    app_thread.daemon = True  # allow the thread to exit when main program exits

    timer = threading.Timer(1.5, lambda: print_app_started(app_thread))
    timer.daemon = True

    print("Starting app...\n")
    timer.start()
    app_thread.start()

    timer.join()
    app_thread.join()

def shutdown():
    import sys
    print("\n\nShutting down. See you next time!")
    sys.exit(0)

if __name__ == "__main__":
    LOCKFILEPATH = data_path / ".uil-dl.lock"

    try: 
        LOCK_FILE = LOCKFILEPATH.open("w")
        portalocker.lock(LOCK_FILE, portalocker.LOCK_EX | portalocker.LOCK_NB)
    except portalocker.LockException:
        print("xx another instance of UIL-DL is running. exiting...")
        sys.exit(1)
    
    try:
        verify_config()
        verify_info_json()
        verify_info_db()
        start_app()
    except KeyboardInterrupt:
        shutdown()
    finally:
        portalocker.unlock(LOCK_FILE)
        LOCK_FILE.close()
        try:
            LOCKFILEPATH.unlink()
        except FileNotFoundError:
            pass
        print("OK lock file released")
