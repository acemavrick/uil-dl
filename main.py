import os
import buildDB
import downloadInfo
from pathlib import Path

# update info.json and info.db
print("Checking for updates to info.json...")

# update and build database if needed
if downloadInfo.update_info_from_online():
    print("Updated info.json")
    buildDB.create_database("data/info.json", "data/info.db", interactive=False)
else:
    print("No update needed to info.json")

# check if info.db exists, if not, create it
if not Path("data/info.db").exists():
    print("info.db not found, creating it...")
    buildDB.create_database("data/info.json", "data/info.db", interactive=False)

# start flask server
import app
app.app.run(debug=False, port=5001)