# checks if there is a db, and builds it if there isn't (based on an info.json)
import orjson
from pathlib import Path
import sqlite3

def build_db():
    # hardcoding these
    TARGET_DIR = Path("data")
    INFO_FILE = TARGET_DIR / "info.json"
    DB_FILE = TARGET_DIR / "db.sqlite"

    if not INFO_FILE.exists():
        print("info.json not found. cannot build db.")
        raise FileNotFoundError("info.json not found")

    with open(INFO_FILE, "rb") as f:
        data = orjson.loads(f.read())
    
    # Validate required keys
    required_keys = ['subjectDict', 'titleAbbrevs', 'linkdata']
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key in info.json: {key}")

    subjectDict = data['subjectDict']
    titleAbbrevs = data['titleAbbrevs']
    linkdata = data['linkdata']
    version = data.get('version', 1)

    # Prepare contest entries
    contests_map = {}
    for key, url in linkdata.items():
        base_key = key.removesuffix('_data')
        parts = base_key.split('_')
        if len(parts) < 3:
            continue
        try:
            year = int(parts[-1])
        except ValueError:
            continue
        subject_key = '_'.join(parts[:-2])
        level_abbrev = parts[-2]
        subject = subjectDict.get(subject_key, subject_key)
        level = titleAbbrevs.get(level_abbrev, level_abbrev)
        contest_key = (subject, level, year)
        if contest_key not in contests_map:
            contests_map[contest_key] = {'pdf_link': None, 'zip_link': None, 'other_link': None}
        url_lower = url.lower()
        if url_lower.endswith('.pdf'):
            contests_map[contest_key]['pdf_link'] = url
        elif url_lower.endswith('.zip'):
            contests_map[contest_key]['zip_link'] = url
        else:
            contests_map[contest_key]['other_link'] = url

    # Level order for sorting
    LEVEL_ORDER = [
        'study packet',
        'invitational a',
        'invitational b',
        'district',
        'region',
        'state',
    ]

    def compute_level_sort(level_name):
        normalized = (level_name or '').strip().lower()
        try:
            return LEVEL_ORDER.index(normalized)
        except ValueError:
            return 999

    # Remove existing DB
    if DB_FILE.exists():
        DB_FILE.unlink()

    # Create DB and tables
    connection = sqlite3.connect(DB_FILE)
    cur = connection.cursor()
    cur.execute('''CREATE TABLE contests (
        id INTEGER PRIMARY KEY,
        subject TEXT NOT NULL,
        level TEXT NOT NULL,
        year INTEGER NOT NULL,
        level_sort INTEGER NOT NULL,
        pdf_link TEXT,
        zip_link TEXT,
        other_link TEXT,
        UNIQUE(subject, level, year)
    )''')
    cur.execute('''CREATE TABLE metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )''')

    # Insert contests
    insert_data = [
        (
            subject,
            level,
            year,
            compute_level_sort(level),
            links['pdf_link'],
            links['zip_link'],
            links['other_link']
        )
        for (subject, level, year), links in contests_map.items()
    ]

    cur.executemany(
        'INSERT INTO contests (subject, level, year, level_sort, pdf_link, zip_link, other_link) VALUES (?, ?, ?, ?, ?, ?, ?)',
        insert_data
    )

    cur.execute('INSERT INTO metadata (key, value) VALUES (?, ?)', ('version', str(version)))
    cur.execute('CREATE INDEX idx_contests_subject_level_year ON contests(subject, level, year)')
    cur.execute('CREATE INDEX idx_contests_subject_levelsort_year ON contests(subject, level_sort, year)')

    connection.commit()
    connection.close()

    print(f"Database built at {DB_FILE}")

def main():
    # for now, we hardcode these vars
    TARGET_DIR = Path("data")
    # info should be in data
    INFO_FILE = TARGET_DIR / "info.json"

    if not INFO_FILE.exists():
        print("info.json not found. cannot build db.")
        raise FileNotFoundError("info.json not found")

    with open(INFO_FILE, "rb") as f:
        info = orjson.loads(f.read())
    
    # we are assuming that info.json is the most up to date

    # we overwrite the db, even if it exists
    db_file = TARGET_DIR / "db.sqlite"

    if db_file.exists():
        print("overwriting database")
    
    connection = sqlite3.connect(db_file)
    cur = connection.cursor()

    # build db

if __name__ == "__main__":
    build_db()

# some reasoning as to why this was simplified
'''
This script will ideally be run by the application while it is starting up. Since this will be in a production setting, the info.json will be downloaded
from external sources (e.g. the github repository). There are very minimal checks because we expect that, when this file is run, the info.json is verified,
up-to-date, and correct. If any of these assumptions are violated, it is likely a larger issue with the deployment process and should be handled upstream.

Ideally, verification of the info.json would be done before it is released to production. It could also be done in the app itself at startup just to prevent
against any app crashes.
'''
