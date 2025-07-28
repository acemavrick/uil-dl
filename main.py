import downloadInfo
import os
import buildDB

# check for info updates
updated = downloadInfo.update_info_from_online()

print()
if updated:
    print("Updated info.json")
    buildDB.create_database("info.json", "info.db", interactive=False)
    print("Database created with updated info")
else:
    print("No update needed to info.json")


# check if there is a databse. if not, create it.
if not os.path.exists("info.db"):
    print("No database found, creating one")
    buildDB.create_database("info.json", "info.db", interactive=False)

# run the app
import app
app.myapp.run(debug=False, port=5001)