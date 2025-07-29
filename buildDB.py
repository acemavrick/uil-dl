import json
import os
import sqlite3
import logging
from colorama import init, Fore, Style
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

# Initialize colorama for cross-platform color support
init()

# Configure colored logging
class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }

    def format(self, record):
        original_levelname = record.levelname
        if original_levelname in self.COLORS:
            colored_levelname = f"{self.COLORS[original_levelname]}{original_levelname}{Style.RESET_ALL}"
            # Colorize levelname and message for logging output.
            # This approach avoids complex Formatter method overrides by temporarily
            # modifying record fields before passing to the base class format method.
            colored_msg = f"{self.COLORS[original_levelname]}{record.msg}{Style.RESET_ALL}"
            
            # Store original msg, colorize the record's msg field for the current formatter pass
            original_msg = record.msg
            record.msg = colored_msg
            record.levelname = colored_levelname # Colorize levelname for the formatter
            
            formatted_log = super().format(record)
            
            # Restore original for other handlers / sanity
            record.levelname = original_levelname
            record.msg = original_msg
            return formatted_log
            
        return super().format(record)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers = [] 
handler = logging.StreamHandler()
# Ensure the format string does not double-color if we pre-color parts
# The ColoredFormatter's job is to take a plain record and colorize it.
handler.setFormatter(ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.propagate = False

@dataclass
class Contest:
    """Represents a single contest event, with links categorized by type."""
    subject: str
    level: str
    year: int
    pdf_link: Optional[str] = None
    zip_link: Optional[str] = None
    other_link: Optional[str] = None

def _load_and_parse_json_data(
    json_file_path: str, 
    parsed_data_store: Dict[str, Any]
) -> bool:
    """
    Loads, validates, and parses data from info.json into a unified contest list.
    Updates parsed_data_store with the results.
    Returns True if successful, False otherwise.
    """
    logger.info(f"Attempting to load and parse {json_file_path}...")
    
    # Clear/re-initialize data store for this parsing attempt
    parsed_data_store['subjectDict'] = {}
    parsed_data_store['titleAbbrevs'] = {}
    parsed_data_store['contests'] = []
    parsed_data_store['version'] = None  # add version tracking
    parsed_data_store['stats'] = {
        'total_contests': 0, 'with_pdf_link': 0, 'with_zip_link': 0, 'with_other_link': 0,
        'invalid_years': 0, 'invalid_keys': 0,
        'missing_subjects': 0, 'missing_levels': 0,
    }

    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
            
        required_keys = ['subjectDict', 'titleAbbrevs', 'linkdata']
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            logger.error(f"Missing required keys in JSON: {', '.join(missing_keys)}")
            return False
            
        if not isinstance(data['subjectDict'], dict) or \
           not isinstance(data['titleAbbrevs'], dict) or \
           not isinstance(data['linkdata'], dict):
            logger.error("Invalid data types for subjectDict, titleAbbrevs, or linkdata in JSON.")
            return False
            
        parsed_data_store['subjectDict'].update(data['subjectDict'])
        parsed_data_store['titleAbbrevs'].update(data['titleAbbrevs'])
        
        # extract version if present
        parsed_data_store['version'] = data.get('version', 1)  # default to 1 if not present
        
        current_stats = parsed_data_store['stats']
        # In-memory store to merge links for the same contest
        contests_map: Dict[Tuple[str, str, int], Dict[str, Optional[str]]] = {}

        for key, url in data['linkdata'].items():
            base_key = key.removesuffix('_data')
            parts = base_key.split('_')

            if len(parts) < 3:
                current_stats['invalid_keys'] += 1
                logger.warning(f"Invalid key format: {key}")
                continue
            
            try:
                year = int(parts[-1])
                if not (1900 <= year <= 2100):
                    current_stats['invalid_years'] += 1
                    logger.warning(f"Invalid year in key {key}: {year}")
                    continue
            except ValueError:
                current_stats['invalid_years'] += 1
                logger.warning(f"Non-integer year in key {key}")
                continue
            
            subject_key_part = '_'.join(parts[:-2])
            level_abbrev_part = parts[-2]

            subject_name = parsed_data_store['subjectDict'].get(subject_key_part, subject_key_part)
            level_full_name = parsed_data_store['titleAbbrevs'].get(level_abbrev_part, level_abbrev_part)
            
            if subject_key_part not in parsed_data_store['subjectDict']:
                current_stats['missing_subjects'] += 1
                logger.warning(f"Subject key '{subject_key_part}' (from item '{key}') not found in subjectDict. Using raw key as subject name: '{subject_name}'.")
            
            if level_abbrev_part not in parsed_data_store['titleAbbrevs']:
                current_stats['missing_levels'] += 1
                logger.warning(f"Level abbreviation '{level_abbrev_part}' (from item '{key}') not found in titleAbbrevs. Using raw abbreviation as level name: '{level_full_name}'.")

            contest_key = (subject_name, level_full_name, year)
            if contest_key not in contests_map:
                contests_map[contest_key] = {'pdf_link': None, 'zip_link': None, 'other_link': None}

            url_lower = url.lower()
            if url_lower.endswith('.pdf'):
                if contests_map[contest_key]['pdf_link']:
                    logger.warning(f"Duplicate PDF link for {contest_key}. Overwriting.")
                contests_map[contest_key]['pdf_link'] = url
            elif url_lower.endswith('.zip'):
                if contests_map[contest_key]['zip_link']:
                    logger.warning(f"Duplicate ZIP link for {contest_key}. Overwriting.")
                contests_map[contest_key]['zip_link'] = url
            else:
                if contests_map[contest_key]['other_link']:
                    logger.warning(f"Duplicate OTHER link for {contest_key}. Overwriting.")
                contests_map[contest_key]['other_link'] = url

        # Convert the map to a list of Contest objects and calculate final stats
        final_contests = []
        for (subject, level, year), links in contests_map.items():
            contest = Contest(
                subject=subject,
                level=level,
                year=year,
                pdf_link=links['pdf_link'],
                zip_link=links['zip_link'],
                other_link=links['other_link']
            )
            final_contests.append(contest)
            if contest.pdf_link:
                current_stats['with_pdf_link'] += 1
            if contest.zip_link:
                current_stats['with_zip_link'] += 1
            if contest.other_link:
                current_stats['with_other_link'] += 1

        parsed_data_store['contests'] = sorted(final_contests, key=lambda c: (c.subject, c.year, c.level))
        current_stats['total_contests'] = len(parsed_data_store['contests'])
        
        logger.info(f"Successfully parsed {json_file_path}.")
        return True

    except FileNotFoundError:
        logger.error(f"JSON file not found: {json_file_path}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {json_file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error loading or parsing JSON data from {json_file_path}: {e}")
        return False

def create_database(info_json_path='data/info.json', db_path='data/info.db', interactive=True):
    if os.path.exists(db_path):
        logger.info(f"Removing existing database at {db_path}")
        try:
            os.remove(db_path)
        except OSError as e:
            logger.error(f"Failed to remove existing database: {e}")
            raise # Critical, so re-raise
    
    parsed_data_store: Dict[str, Any] = {} # Holds all data from _load_and_parse_json_data

    while True: # Main loop for parsing and user confirmation
        if not _load_and_parse_json_data(info_json_path, parsed_data_store):
            if interactive:
                choice = input(
                    f"{Fore.RED}Failed to load/parse {info_json_path}. "
                    f"Do you want to fix the file and try again? (y/n): {Style.RESET_ALL}"
                ).lower().strip()
                if choice == 'y':
                    input(
                        f"{Fore.YELLOW}Okay, please make any necessary changes to {info_json_path} now. \n"
                        f"After saving your changes, press Enter here to re-process...{Style.RESET_ALL} "
                    )
                    continue # Re-attempt parsing
                else:
                    logger.error("Aborting database creation due to parsing error and user choice to not retry.")
                    return
            else:
                logger.error(f"Aborting database creation due to parsing error in non-interactive mode from {info_json_path}.")
                # In non-interactive, a parsing failure is fatal for this function.
                raise ValueError(f"Failed to parse {info_json_path} in non-interactive mode.")

        # Parsing was successful, display stats
        stats = parsed_data_store['stats']
        logger.info("Data processing from JSON completed with stats:")
        logger.info(f"  - Total unique contests found: {stats['total_contests']}")
        logger.info(f"  - Contests with PDF links: {stats['with_pdf_link']}")
        logger.info(f"  - Contests with ZIP links: {stats['with_zip_link']}")
        logger.info(f"  - Contests with OTHER links: {stats['with_other_link']}")
        logger.info(f"  - Invalid keys: {stats['invalid_keys']}")
        logger.info(f"  - Invalid years: {stats['invalid_years']}")
        logger.info(f"  - Subject keys not in subjectDict: {stats['missing_subjects']}")
        logger.info(f"  - Level abbrevs not in titleAbbrevs: {stats['missing_levels']}")

        if interactive:
            print(f"{Fore.YELLOW}Summary of data parsed from {Fore.CYAN}{info_json_path}{Style.RESET_ALL}:")
            print(f"  - {Fore.GREEN}{stats['total_contests']} unique contests identified.{Style.RESET_ALL}")
            print(f"    - {stats['with_pdf_link']} have a PDF link.")
            print(f"    - {stats['with_zip_link']} have a ZIP link.")
            print(f"    - {stats['with_other_link']} have an OTHER link.")
            if any(stats[k] > 0 for k in ['invalid_keys', 'invalid_years', 'missing_subjects', 'missing_levels']):
                print(f"{Fore.YELLOW}Warnings from parsing:{Style.RESET_ALL}")
                if stats['invalid_keys'] > 0: print(f"  - {Fore.YELLOW}{stats['invalid_keys']} invalid keys found.{Style.RESET_ALL}")
                if stats['invalid_years'] > 0: print(f"  - {Fore.YELLOW}{stats['invalid_years']} invalid years found.{Style.RESET_ALL}")
                if stats['missing_subjects'] > 0: print(f"  - {Fore.YELLOW}{stats['missing_subjects']} subject keys were not in subjectDict (used raw key).{Style.RESET_ALL}")
                if stats['missing_levels'] > 0: print(f"  - {Fore.YELLOW}{stats['missing_levels']} level abbreviations were not in titleAbbrevs (used raw abbrev).{Style.RESET_ALL}")
            
            user_choice = input(
                f"{Fore.GREEN}Proceed with building the database using this data? {Style.RESET_ALL}"
                f"({Fore.CYAN}y{Style.RESET_ALL}es / {Fore.CYAN}n{Style.RESET_ALL}o, re-edit {info_json_path} and re-parse / {Fore.CYAN}q{Style.RESET_ALL}uit): "
            ).lower().strip()

            if user_choice == 'y':
                logger.info(f"User confirmed parsed data. Proceeding to build database from {info_json_path}.")
                break # Exit while loop and proceed to DB operations
            elif user_choice == 'n':
                input(
                    f"{Fore.YELLOW}Okay, please make any necessary changes to {info_json_path} now. \n"
                    f"After saving your changes, press Enter here to re-process...{Style.RESET_ALL} "
                )
                # Loop continues, _load_and_parse_json_data will re-run
            elif user_choice == 'q':
                logger.info("User chose to quit database creation before DDL/DML operations.")
                return
            else:
                print(f"{Fore.RED}Invalid choice. Please enter 'y', 'n', or 'q'.{Style.RESET_ALL}")
        else: # Non-interactive mode
            logger.info("Non-interactive mode: proceeding with parsed data.")
            break # Proceed directly

    # ----- Database Operations -----
    contests_to_insert = parsed_data_store['contests']
    version = parsed_data_store['version']

    try:
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            logger.info("Creating database tables...")
            try:
                # contests table
                c.execute('''CREATE TABLE contests (
                    id INTEGER PRIMARY KEY,
                    subject TEXT NOT NULL,
                    level TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    pdf_link TEXT,
                    zip_link TEXT,
                    other_link TEXT,
                    UNIQUE(subject, level, year)
                )''')
                
                # metadata table for version and other config
                c.execute('''CREATE TABLE metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )''')
            except sqlite3.Error as e:
                logger.error(f"Error creating database tables: {e}")
                raise

            logger.info(f"Inserting {len(contests_to_insert)} contest entries...")
            try:
                # insert contest data
                insert_data = [
                    (
                        entry.subject, entry.level, entry.year,
                        entry.pdf_link, entry.zip_link, entry.other_link
                    ) for entry in contests_to_insert
                ]
                c.executemany(
                    'INSERT INTO contests (subject, level, year, pdf_link, zip_link, other_link) VALUES (?, ?, ?, ?, ?, ?)',
                    insert_data
                )
                
                # insert version metadata
                c.execute('INSERT INTO metadata (key, value) VALUES (?, ?)', ('version', str(version)))
                logger.info(f"Database version set to: {version}")
                
            except sqlite3.Error as e:
                logger.error(f"Error inserting data: {e}")
                if "UNIQUE constraint failed" in str(e): 
                    logger.error("This usually means duplicate contest entries were generated from the source data.")
                raise
            
            logger.info("Creating database index...")
            try:
                c.execute('CREATE INDEX idx_contests_subject_level_year ON contests(subject, level, year)')
            except sqlite3.Error as e:
                logger.error(f"Error creating index: {e}")
                raise
            
            conn.commit()
            logger.info(f"{Fore.GREEN}Database creation completed successfully! Schema and data populated in {db_path}{Style.RESET_ALL}")
            
    except sqlite3.Error as e:
        logger.error(f"A database error occurred: {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during database operations: {e}")
        raise

def repopulate_database(info_json_path='data/info.json', db_path='data/info.db'):
    """
    Repopulates both 'contests' and 'metadata' tables with fresh data from the JSON file
    without dropping the table or the database file. This is safe to call
    on a running application as it doesn't delete the DB file.
    """
    logger.info(f"Starting database repopulation from {info_json_path} into {db_path}...")
    
    parsed_data_store: Dict[str, Any] = {}
    if not _load_and_parse_json_data(info_json_path, parsed_data_store):
        # The _load_and_parse_json_data function logs the specific error.
        raise ValueError(f"Failed to parse {info_json_path}")

    contests_to_insert = parsed_data_store['contests']
    version = parsed_data_store['version']
    
    try:
        # The 'with' statement handles the transaction (commit/rollback)
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            
            logger.info("Deleting all existing entries from 'contests' table.")
            c.execute('DELETE FROM contests')
            
            logger.info("Updating metadata...")
            c.execute('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)', ('version', str(version)))
            
            logger.info(f"Inserting {len(contests_to_insert)} new contest entries...")
            insert_data = [
                (
                    entry.subject, entry.level, entry.year,
                    entry.pdf_link, entry.zip_link, entry.other_link
                ) for entry in contests_to_insert
            ]
            c.executemany(
                'INSERT INTO contests (subject, level, year, pdf_link, zip_link, other_link) VALUES (?, ?, ?, ?, ?, ?)',
                insert_data
            )
            
        logger.info(f"Database repopulation completed successfully. Version: {version}")
        return len(contests_to_insert)
            
    except sqlite3.Error as e:
        logger.error(f"A database error occurred during repopulation: {e}")
        raise

if __name__ == '__main__':
    try:
        create_database('data/info.json', 'data/info.db', interactive=True)
    except Exception as e:
        logger.critical(f"Database creation process failed: {e}")