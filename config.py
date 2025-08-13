from pathlib import Path
from platformdirs import user_data_path

# central app data directory (side-effect free; no prints)
data_path: Path = user_data_path(
    appname="uil-dl", appauthor="acemavrick", ensure_exists=True
)


