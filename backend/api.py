# main fastapi backend
from fastapi import FastAPI, Response
from pathlib import Path
import sqlite3

app: FastAPI = FastAPI()
DB_CONNECTION: sqlite3.Connection
DOWNLOADS_DIR: Path = Path("downloads")

def init():
    global app, DB_CONNECTION

    DATA_DIR = Path("data")
    DB_FILE = DATA_DIR / "db.sqlite"

    DB_CONNECTION = sqlite3.connect(DB_FILE, check_same_thread=False)
    print("DB connection established.")


def deinit():
    global DB_CONNECTION
    DB_CONNECTION.close()
    print("DB connection closed.")

@app.get("/api/health")
def health():
    return Response(content="OK", status_code=200)

@app.get("/api/contests")
def get_contests():
    cur = DB_CONNECTION.cursor()
    cols = ["id", "subject", "level", "year", "level_sort", "pdf_link", "zip_link", "other_link"]
    cur.execute(f"SELECT {','.join(cols)} FROM contests")
    contests = [dict(zip(cols, row)) for row in cur.fetchall()]
    cur.close()
    return {"contests": contests}
