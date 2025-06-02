import json
import sqlite3

def create_database(json_file, db_path):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    subject_dict = data['subjectDict']
    title_abbrevs = data['titleAbbrevs']
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE contests (
        id INTEGER PRIMARY KEY,
        subject TEXT, level TEXT, year INTEGER, link TEXT, data_file_id INTEGER)''')
    
    c.execute('''CREATE TABLE data_files (
        id INTEGER PRIMARY KEY, 
        subject TEXT, level TEXT, year INTEGER, link TEXT, contest_id INTEGER)''')
    
    # Parse and separate data
    contests, data_files = [], []
    for key, url in data['linkdata'].items():
        parts = key.replace('_data', '').split('_')
        if len(parts) < 3: continue
        
        try: year = int(parts[-1])
        except: continue
        
        subject = subject_dict.get('_'.join(parts[:-2]), '_'.join(parts[:-2]))
        level = title_abbrevs.get(parts[-2], parts[-2])
        
        if key.endswith('_data'):
            data_files.append((subject, level, year, url))
        else:
            contests.append((subject, level, year, url))
    
    # Bulk insert contests
    c.executemany('INSERT INTO contests (subject, level, year, link) VALUES (?, ?, ?, ?)', contests)
    
    # Bulk insert data files with contest IDs
    data_with_contest_ids = []
    for subject, level, year, url in data_files:
        c.execute('SELECT id FROM contests WHERE subject=? AND level=? AND year=?', (subject, level, year))
        contest_id = c.fetchone()
        contest_id = contest_id[0] if contest_id else None
        data_with_contest_ids.append((subject, level, year, url, contest_id))
    
    c.executemany('INSERT INTO data_files (subject, level, year, link, contest_id) VALUES (?, ?, ?, ?, ?)', data_with_contest_ids)
    
    # Update contests with data file IDs
    c.execute('''UPDATE contests SET data_file_id = (
        SELECT id FROM data_files WHERE data_files.contest_id = contests.id)''')
    
    conn.commit()
    conn.close()