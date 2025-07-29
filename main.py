import os
import buildDB
import downloadInfo
from pathlib import Path

# update info.json and info.db
print("Checking for updates to info.json...")

# update and build database if needed
if downloadInfo.update_info_from_online():
    print("Updated info.json")
else:
    print("No update needed to info.json")

# build database regardless of whether it exists or not (it's very cheap anyway)
buildDB.create_database("data/info.json", "data/info.db", interactive=False)

# start flask server
import app
app.app.run(debug=False, port=5001)