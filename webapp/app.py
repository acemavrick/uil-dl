if __name__ == '__main__':
    print("Please use the main.py script to start the application.")
    exit(1)

import sys
import os
import json
import logging
import threading
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from sqlalchemy import func
from webapp.models import db, Contest
from setup.buildDB import repopulate_database
from setup.downloadInfo import update_info_from_online
from setup.mylogging import LOGGER as logger
from main import data_path


def _resolve_download_path(path_str: str) -> Path:
    """
    Resolves a path string. Relative paths are resolved against ~/Downloads.
    Absolute paths and paths with '~' are used as is.
    """
    if not path_str:
        raise ValueError("Path string cannot be empty.")

    path_obj = Path(path_str)
    expanded_path = path_obj.expanduser()

    if not expanded_path.is_absolute():
        return (Path.home() / 'Downloads' / expanded_path).resolve()
    else:
        return expanded_path.resolve()


# build tailwindcss
# os.system("npx tailwindcss -i ./static/css/in.css -o ./static/css/out.css")

# Load configuration
CONFIG_FILE = data_path / "config.cfg"
config_data = {}
if CONFIG_FILE.exists():
    with open(CONFIG_FILE, 'r') as f:
        config_data = json.load(f)

DOWNLOADS_DIR = _resolve_download_path(config_data.get('download_dir', config_data.get('default_download_dir', Path.home() / 'Downloads')))
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

TEMP_DIR = Path(tempfile.gettempdir()) / 'uil-dl-downloads'
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Create Flask app
if getattr(sys, 'frozen', False):
    # if the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS
    root_path = sys._MEIPASS
    app = Flask(__name__, template_folder=os.path.join(root_path, 'templates'), static_folder=os.path.join(root_path, 'static'))
else:
    root_path = Path(__file__).parent
    app = Flask(__name__, template_folder=root_path / "templates", static_folder=root_path / "static")

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.abspath(data_path / "info.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def get_database_version(db_path=data_path / "info.db"):
    """Get the database version from the metadata table."""
    import sqlite3
    try:
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT value FROM metadata WHERE key = ?', ('version',))
            result = c.fetchone()
            return int(result[0]) if result else None
    except sqlite3.Error as e:
        logger.error(f"Error getting database version: {e}")
        return None
    except (ValueError, TypeError) as e:
        logger.error(f"Error parsing database version: {e}")
        return None

# Create tables within app context
with app.app_context():
    db.create_all()

# Create a semaphore to limit concurrent downloads
download_semaphore = threading.Semaphore(4)  # Maximum 4 concurrent downloads
db_rebuild_lock = threading.Lock()

# Track active downloads
active_downloads = set()  # set of cache_keys for active downloads
active_downloads_lock = threading.Lock()

# ---------- per-file locking utilities ----------
_download_locks: dict[str, threading.Lock] = {}
_download_locks_lock = threading.Lock()


def _get_download_lock(cache_key: str) -> threading.Lock:
    """Return a unique lock per cache_key so concurrent requests for the
    same file are serialised. Thread-safe thanks to the global lock dict."""
    with _download_locks_lock:
        return _download_locks.setdefault(cache_key, threading.Lock())
# -------------------------------------------------

class DownloadCache:
    """Class to manage the download cache."""
    CACHE_FILE = ".cache_manifest.json"
    
    def __init__(self, downloads_dir=DOWNLOADS_DIR):
        self.downloads_dir = Path(downloads_dir)
        self.downloads_dir.mkdir(exist_ok=True)
        self._cache_index = {}
        self._cache_lock = threading.RLock()  # guard cache mutations
        self._load_or_build_cache()
        logger.info(f"Download cache initialized with {len(self._cache_index)} files")
    
    def _build_cache_index(self):
        """Build an index of already downloaded files by scanning the downloads directory."""
        cache = {}
        for file_path in self.downloads_dir.glob('*'):
            if file_path.is_file() and file_path.name != self.CACHE_FILE:
                # Use the filename without extension as the key
                key = file_path.stem
                cache[key] = {
                    'path': str(file_path),
                    'size': file_path.stat().st_size,
                    'timestamp': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
        return cache
    
    def _save_cache_manifest(self):
        """Save the cache index to the manifest file."""
        cache_file_path = self.downloads_dir / self.CACHE_FILE
        try:
            with open(cache_file_path, 'w') as f:
                json.dump(self._cache_index, f, indent=2)
            logger.info(f"Cache manifest saved with {len(self._cache_index)} entries")
        except Exception as e:
            logger.error(f"Error saving cache manifest: {e}")
    
    def _load_or_build_cache(self):
        """Load the cache from the manifest file or build it if not found."""
        cache_file_path = self.downloads_dir / self.CACHE_FILE
        
        if cache_file_path.exists():
            try:
                with open(cache_file_path, 'r') as f:
                    self._cache_index = json.load(f)
                logger.info(f"Cache manifest loaded with {len(self._cache_index)} entries")
                
                # Verify that the files in the cache actually exist
                # If any are missing, rebuild the cache
                missing_files = []
                for key, info in list(self._cache_index.items()):
                    if not Path(info['path']).exists():
                        missing_files.append(key)
                
                if missing_files:
                    logger.warning(f"Found {len(missing_files)} missing files in cache manifest. Rebuilding cache.")
                    self.rebuild_cache()
                    
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading cache manifest: {e}. Rebuilding cache.")
                self.rebuild_cache()
        else:
            logger.info("No cache manifest found. Building new cache.")
            self.rebuild_cache()
    
    def rebuild_cache(self):
        """Rebuild the cache by scanning the downloads directory."""
        self._cache_index = self._build_cache_index()
        self._save_cache_manifest()
        logger.info(f"Cache rebuilt with {len(self._cache_index)} files")
        return len(self._cache_index)
    
    def reset_cache(self):
        """Reset the cache (forget all downloads without deleting files)."""
        old_count = len(self._cache_index)
        self._cache_index = {}
        self._save_cache_manifest()
        logger.info(f"Cache reset. Forgot {old_count} files.")
        return old_count
    
    def is_cached(self, file_key):
        """Check if a file is already in the cache."""
        return file_key in self._cache_index
    
    def get_cached_file_path(self, file_key):
        """Get the path to a cached file."""
        if self.is_cached(file_key):
            return self._cache_index[file_key]['path']
        return None
    
    def add_to_cache(self, file_key, file_path):
        """Add a file to the cache index."""
        path_obj = Path(file_path)
        if path_obj.exists():
            with self._cache_lock:
                self._cache_index[file_key] = {
                    'path': str(path_obj),
                    'size': path_obj.stat().st_size,
                    'timestamp': datetime.fromtimestamp(path_obj.stat().st_mtime).isoformat()
                }
                self._save_cache_manifest()
            logger.info(f"Added file to cache: {file_key}")
        else:
            logger.warning(f"Attempted to add non-existent file to cache: {file_path}")
    
    def get_stats(self):
        """Get statistics about the cache."""
        if not self._cache_index:
            return {
                'total_files': 0,
                'total_size': 0,
                'newest_file': None,
                'oldest_file': None
            }
            
        timestamps = [datetime.fromisoformat(item['timestamp']) 
                     for item in self._cache_index.values()]
        
        return {
            'total_files': len(self._cache_index),
            'total_size': sum(item['size'] for item in self._cache_index.values()),
            'newest_file': max(timestamps).isoformat() if timestamps else None,
            'oldest_file': min(timestamps).isoformat() if timestamps else None
        }

# Initialize the download cache
download_cache = DownloadCache()

def format_filename(subject, level, year, link_type, extension):
    """Format filename: subject_year_level_linktype.extension"""
    base_name = f"{subject.replace(' ', '_')}_{year}_{level.replace(' ', '_')}"
    # Use link_type to differentiate files for the same contest
    return f"{base_name}_{link_type}{extension}"

def generate_cache_key(subject, level, year, link_type):
    """Generate a consistent cache key for a contest's file."""
    base_key = f"{subject.replace(' ', '_')}_{year}_{level.replace(' ', '_')}"
    return f"{base_key}_{link_type}"

@app.route('/splash')
def splash():
    """Render the splash screen."""
    return render_template('splash.html')

@app.route('/')
def index():
    """Render the main page."""
    logger.info("Loading main page")
    try:
        # Use SQLAlchemy to get distinct values for filters
        subjects = [s[0] for s in db.session.query(Contest.subject).distinct().order_by(Contest.subject).all()]
        levels = [l[0] for l in db.session.query(Contest.level).distinct().order_by(Contest.level).all()]
        years = [y[0] for y in db.session.query(Contest.year).distinct().order_by(Contest.year.desc()).all()]

        # Get cache stats and database version
        cache_stats = download_cache.get_stats()
        db_version = get_database_version()
        
        return render_template('index.html',
                               subjects=subjects,
                               levels=levels,
                               years=years,
                               cache_stats=cache_stats,
                               download_dir_absolute=DOWNLOADS_DIR.absolute(),
                               info_version=db_version,
                               total_contest_count=db.session.query(Contest).count())
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        # Get cache stats and database version even when there's an error
        cache_stats = download_cache.get_stats()
        db_version = get_database_version()
        return render_template('index.html', error=str(e), contests=[], cache_stats=cache_stats, database_version=db_version)

@app.route('/refresh-info', methods=['POST'])
def refresh_info():
    """Refreshes the contest information from the UIL website."""
    logger.info("Refresh info requested.")
    
    if not db_rebuild_lock.acquire(blocking=False):
        logger.warning("Refresh info already in progress.")
        return "A refresh info process is already in progress. Please wait.", 503

    try:
        logger.info("Starting refresh info process.")
        
        # Call the update_info_from_online function
        updated = update_info_from_online()
        
        if updated:
            logger.info("Info refreshed successfully - new version downloaded.")
            # rebuild the database
            repopulate_database(db_path=app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
            return "Info refreshed successfully - new version downloaded. Database rebuilt.", 200
        else:
            logger.info("Info refresh completed - no update needed.")
            return "Info refresh completed - no update needed.", 200
    except Exception as e:
        logger.error(f"Failed to refresh info: {e}", exc_info=True)
        return f"Failed to refresh info: {str(e)}", 500
    finally:
        db_rebuild_lock.release()

@app.route('/download/<int:item_id>/<link_type>', methods=['GET', 'POST'])
def download_file(item_id, link_type):
    """Download a file for a specific contest, identified by link_type (pdf, zip, other)."""
    logger.info(f"Download requested for contest ID {item_id}, link type: {link_type}")
    
    if link_type not in ['pdf', 'zip', 'other']:
        return jsonify({"error": "Invalid link type specified. Must be 'pdf', 'zip', or 'other'."}), 400

    try:
        item = db.session.get(Contest, item_id)
        if not item:
            logger.error(f"Contest with ID {item_id} not found")
            if request.headers.get('HX-Request'):
                return f"""
                <div class="flex items-center justify-center space-x-2">
                    <span class="text-red-500 text-sm">Contest not found</span>
                </div>
                """
            return jsonify({"error": "Contest not found"}), 404

        link_map = {
            'pdf': item.pdf_link,
            'zip': item.zip_link,
            'other': item.other_link
        }
        
        url_to_download = link_map.get(link_type)

        if not url_to_download:
            logger.error(f"No {link_type} link found for contest ID {item_id}")
            if request.headers.get('HX-Request'):
                return f"""
                <div class="flex items-center justify-center space-x-2">
                    <span class="text-gray-500 text-sm">N/A</span>
                </div>
                """
            return jsonify({"error": f"No {link_type} link available for this contest."}), 404

        cache_key = generate_cache_key(
            item.subject, 
            item.level, 
            item.year,
            link_type # use link_type in cache key
        )
        
        # ---------- thread-safe & atomic download ----------
        download_result = _perform_download(item, link_type)

        if not download_result.get("downloaded"):
            reason = download_result.get("reason", "Unknown error")
            logger.error(f"Download failed: {reason}")
            if request.headers.get('HX-Request'):
                return f"""
                <div class="flex items-center justify-center space-x-2">
                    <input type="checkbox" 
                           class="{'packet-checkbox' if link_type == 'pdf' else 'datafile-checkbox'} h-5 w-5 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded"
                           data-id="{item_id}"
                           data-type="{link_type}">
                    <span class="text-xs text-red-600">✗</span>
                    <span class="text-xs text-red-600" title="{reason}">Error</span>
                </div>
                """
            return jsonify({"error": reason}), 500

        cached = download_result.get("cached", False)
        file_path = download_result.get("file_path")

        # success responses
        if request.headers.get('HX-Request'):
            return f"""
            <div class="flex items-center justify-center space-x-2">
                <input type="checkbox" 
                       class="{'packet-checkbox' if link_type == 'pdf' else 'datafile-checkbox'} h-5 w-5 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded"
                       data-id="{item_id}"
                       data-type="{link_type}"
                       disabled 
                       checked
                       title="{'Already downloaded' if cached else 'Downloaded successfully'}">
                <span class="text-xs text-green-600">✓</span>
            </div>
            """
        elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "success": True,
                "message": "File already downloaded" if cached else "File downloaded successfully",
                "item_id": item_id,
                "link_type": link_type,
                "file_path": file_path,
                "downloaded": True
            })

        return send_file(file_path, as_attachment=True)
    except Exception as e:
        logger.error(f"Error in download route: {e}")
        if request.headers.get('HX-Request'):
            return f"""
            <div class="flex items-center justify-center space-x-2">
                <input type="checkbox" 
                       class="{'packet-checkbox' if link_type == 'pdf' else 'datafile-checkbox'} h-5 w-5 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded"
                       data-id="{item_id}"
                       data-type="{link_type}">
                <span class="text-xs text-red-600">✗</span>
                <span class="text-xs text-red-600" title="{str(e)}">Error</span>
            </div>
            """
        return jsonify({"error": str(e)}), 500

@app.route('/refresh-cache', methods=['GET', 'POST'])
def refresh_cache():
    """Refresh the download cache."""
    logger.info("Refreshing download cache")
    count = download_cache.rebuild_cache()
    
    # Return HTMX-friendly response for cache info update
    cache_stats = download_cache.get_stats()
    return f"""
    <div class="text-sm text-gray-600 dark:text-gray-300 space-y-1">
        <p>Downloaded Files: <span>{cache_stats['total_files']}</span></p>
        <p>Total Size: <span>{cache_stats['total_size'] // 1024 // 1024} MB</span></p>
        <p class="text-green-600 dark:text-green-400">Cache refreshed! Found {count} files.</p>
    </div>
    """

@app.route('/reset-cache', methods=['GET', 'POST'])
def reset_cache():
    """Reset the download cache (forget all downloads)."""
    logger.info("Resetting download cache")
    count = download_cache.reset_cache()
    
    # Return HTMX-friendly response for cache info update
    cache_stats = download_cache.get_stats()
    return f"""
    <div class="text-sm text-gray-600 dark:text-gray-300 space-y-1">
        <p>Downloaded Files: <span>{cache_stats['total_files']}</span></p>
        <p>Total Size: <span>{cache_stats['total_size'] // 1024 // 1024} MB</span></p>
        <p class="text-yellow-600 dark:text-yellow-400">Cache reset! Forgot {count} files.</p>
    </div>
    """

@app.route('/cache-stats')
def get_cache_stats():
    """Get cache statistics for the sidebar."""
    cache_stats = download_cache.get_stats()
    return f"""
    <div class="text-sm text-gray-600 dark:text-gray-300 space-y-1">
        <p>Downloaded Files: <span>{cache_stats['total_files']}</span></p>
        <p>Total Size: <span>{cache_stats['total_size'] // 1024 // 1024} MB</span></p>
    </div>
    """

@app.route('/contests', methods=['GET', 'POST'])
def get_contests_htmx():
    """Get contests formatted for HTMX table body."""
    try:
        query = db.session.query(Contest)
        
        # Get filter parameters from either GET args or POST form data
        if request.method == 'POST':
            form_data = request.form
            subjects = form_data.getlist('subjects')
            levels = form_data.getlist('levels') 
            years = form_data.getlist('years')
            downloaded_filter = form_data.get('downloaded', '')
            sort_by = form_data.get('sort_by', 'year')
            sort_dir = form_data.get('sort_dir', 'desc')
        else:
            subjects = request.args.getlist('subject')
            levels = request.args.getlist('level')
            years = request.args.getlist('year')
            downloaded_filter = request.args.get('downloaded', '')
            sort_by = request.args.get('sort_by', 'year')
            sort_dir = request.args.get('sort_dir', 'desc')
        
        # Apply filters
        if subjects:
            query = query.filter(Contest.subject.in_(subjects))
        if levels:
            query = query.filter(Contest.level.in_(levels))
        if years:
            query = query.filter(Contest.year.in_([int(y) for y in years]))

        # Apply sorting
        if sort_by == 'subject':
            if sort_dir == 'desc':
                query = query.order_by(Contest.subject.desc())
            else:
                query = query.order_by(Contest.subject.asc())
        elif sort_by == 'level':
            if sort_dir == 'desc':
                query = query.order_by(Contest.level.desc())
            else:
                query = query.order_by(Contest.level.asc())
        elif sort_by == 'year':
            if sort_dir == 'desc':
                query = query.order_by(Contest.year.desc())
            else:
                query = query.order_by(Contest.year.asc())
        else:
            # Default sorting
            query = query.order_by(Contest.subject, Contest.level, Contest.year.desc())
        
        contests = query.all()
        
        # Filter by download status and build result
        result_contests = []
        for item in contests:
            pdf_downloaded = download_cache.is_cached(generate_cache_key(item.subject, item.level, item.year, 'pdf')) if item.pdf_link else None
            zip_downloaded = download_cache.is_cached(generate_cache_key(item.subject, item.level, item.year, 'zip')) if item.zip_link else None
            other_downloaded = download_cache.is_cached(generate_cache_key(item.subject, item.level, item.year, 'other')) if item.other_link else None

            # Determine status (ignore 'other' link for completeness)
            has_pdf = item.pdf_link is not None
            has_zip = item.zip_link is not None

            # a contest is fully downloaded if its downloadable files (pdf/zip) are downloaded.
            all_downloaded = (
                (not has_pdf or pdf_downloaded) and
                (not has_zip or zip_downloaded)
            )

            if not has_pdf and not has_zip:
                status = 'no-links'
            elif all_downloaded:
                status = 'downloaded'
            elif (pdf_downloaded or zip_downloaded):
                status = 'partial'
            else:
                status = 'pending'

            item_data = {
                'contest': item,
                'pdf_downloaded': pdf_downloaded,
                'zip_downloaded': zip_downloaded,
                'other_downloaded': other_downloaded,
                'status': status
            }

            # Apply download filter
            if downloaded_filter == 'true' and status != 'downloaded':
                continue
            elif downloaded_filter == 'false' and status == 'downloaded':
                continue
            elif downloaded_filter == 'partial' and status != 'partial':
                continue
                
            result_contests.append(item_data)
        
        return render_template('contests_table.html', contests=result_contests)
        
    except Exception as e:
        logger.error(f"Error in contests route: {e}")
        return f'<tbody><tr><td colspan="7" class="text-center text-red-600">Error loading contests: {str(e)}</td></tr></tbody>'

@app.route('/shutdown', methods=['POST', 'GET'])
def shutdown():
    """Shutdown the application."""
    import os
    import signal
    
    # development server runs in a separate thread, so we need to kill the parent process
    pid = os.getpid()
    os.kill(pid, signal.SIGINT)
    return "Server shutting down. Thank you for using, see you next time!"

@app.route('/api/contests')
def get_contests():
    """API endpoint to get contest data based on filters."""
    try:
        query = db.session.query(Contest)
        
        # Apply filters from query parameters
        subjects = request.args.getlist('subject')
        if subjects:
            query = query.filter(Contest.subject.in_(subjects))
        
        levels = request.args.getlist('level')
        if levels:
            query = query.filter(Contest.level.in_(levels))
        
        years = request.args.getlist('year')
        if years:
            # Ensure years are integers for correct filtering
            query = query.filter(Contest.year.in_([int(y) for y in years]))

        # Order results for consistent presentation
        query = query.order_by(Contest.subject, Contest.level, Contest.year.desc())
        
        contests = query.all()
        
        # Filter by download status in Python after the database query
        downloaded_filter = request.args.get('downloaded')
        result_data = []
        for item in contests:
            item_dict = {
                'id': item.id,
                'subject': item.subject,
                'level': item.level,
                'year': item.year,
                'pdf_link': {
                    'link': item.pdf_link,
                    'downloaded': download_cache.is_cached(generate_cache_key(item.subject, item.level, item.year, 'pdf')) if item.pdf_link else None
                },
                'zip_link': {
                    'link': item.zip_link,
                    'downloaded': download_cache.is_cached(generate_cache_key(item.subject, item.level, item.year, 'zip')) if item.zip_link else None
                },
                'other_link': {
                    'link': item.other_link,
                    'downloaded': download_cache.is_cached(generate_cache_key(item.subject, item.level, item.year, 'other')) if item.other_link else None
                }
            }

            if downloaded_filter in ['true', 'false']:
                has_pdf = item_dict['pdf_link']['link'] is not None
                has_zip = item_dict['zip_link']['link'] is not None
                has_other = item_dict['other_link']['link'] is not None
                
                # A link is considered downloaded if it doesn't exist or is cached
                pdf_downloaded = not has_pdf or item_dict['pdf_link']['downloaded']
                zip_downloaded = not has_zip or item_dict['zip_link']['downloaded']
                other_downloaded = not has_other or item_dict['other_link']['downloaded']
                
                is_fully_downloaded = pdf_downloaded and zip_downloaded and other_downloaded
                
                if downloaded_filter == 'true' and is_fully_downloaded:
                    result_data.append(item_dict)
                elif downloaded_filter == 'false' and not is_fully_downloaded:
                    result_data.append(item_dict)
            else:
                # No download filter, so add the item
                result_data.append(item_dict)
            
        return jsonify(result_data)
    except Exception as e:
        logger.error(f"Error in API route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get download cache statistics."""
    try:
        total_contests_query = db.session.query(func.count(Contest.id))
        
        # Count total available files by checking for non-null links
        total_files = total_contests_query.filter(Contest.pdf_link.isnot(None)).scalar() + \
                      total_contests_query.filter(Contest.zip_link.isnot(None)).scalar() + \
                      total_contests_query.filter(Contest.other_link.isnot(None)).scalar()

        total_contests = total_contests_query.scalar()
        
        cache_stats = download_cache.get_stats()
        
        stats = {
            "total_contests": total_contests,
            "total_files_available": total_files,
            "downloaded_files": cache_stats['total_files'],
            "download_size_bytes": cache_stats['total_size'],
            "download_percentage": (cache_stats['total_files'] / total_files) * 100 if total_files > 0 else 0,
            "database_version": get_database_version()
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error in stats route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/version')
def get_version():
    """Get the database version."""
    try:
        version = get_database_version()
        return jsonify({"database_version": version})
    except Exception as e:
        logger.error(f"Error in version route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/active-downloads')
def get_active_downloads():
    """Get the count of currently active downloads."""
    try:
        with active_downloads_lock:
            active_count = len(active_downloads)
            active_list = list(active_downloads)
        
        return jsonify({
            "active_count": active_count,
            "active_downloads": active_list,
            "has_active": active_count > 0
        })
    except Exception as e:
        logger.error(f"Error getting active downloads: {e}")
        return jsonify({"error": str(e)}), 500

# Helper function to perform an individual download (shared by single and batch routes)

def _perform_download(contest_item, link_type):
    """Download a specific file for a contest item and add it to cache. Returns dict result."""
    link_map = {
        'pdf': contest_item.pdf_link,
        'zip': contest_item.zip_link,
        'other': contest_item.other_link
    }

    url_to_download = link_map.get(link_type)
    if not url_to_download:
        return {"item_id": contest_item.id, "link_type": link_type, "downloaded": False, "reason": "No link available"}

    cache_key = generate_cache_key(contest_item.subject, contest_item.level, contest_item.year, link_type)
    # ensure only one thread handles a given file at a time
    download_lock = _get_download_lock(cache_key)
    with download_lock:
        cached_path = download_cache.get_cached_file_path(cache_key)
        if cached_path:
            return {"item_id": contest_item.id, "link_type": link_type, "downloaded": True, "cached": True, "file_path": cached_path}

        import requests, os
        
        # Add to active downloads tracking
        with active_downloads_lock:
            active_downloads.add(cache_key)
        
        try:
            with download_semaphore:
                response = requests.get(url_to_download, timeout=30, stream=True)
                response.raise_for_status()

            # Determine extension
            file_extension = os.path.splitext(url_to_download)[1] or '.dat'
            if not file_extension.startswith('.'):
                file_extension = '.' + file_extension

            formatted_filename = format_filename(contest_item.subject, contest_item.level, contest_item.year, link_type, file_extension)
            file_path = DOWNLOADS_DIR / formatted_filename
            tmp_file_path = TEMP_DIR / formatted_filename

            # atomic streaming write to a temporary file, then move it
            try:
                with open(tmp_file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                shutil.move(str(tmp_file_path), str(file_path))
            except Exception:
                # if something goes wrong, try to clean up the temporary file
                if tmp_file_path.exists():
                    tmp_file_path.unlink()
                raise # re-raise the exception to be caught by the outer handler

            download_cache.add_to_cache(cache_key, str(file_path))
            return {"item_id": contest_item.id, "link_type": link_type, "downloaded": True, "cached": False, "file_path": str(file_path)}
        except Exception as e:
            logger.error(f"Download error for item {contest_item.id} ({link_type}): {e}")
            return {"item_id": contest_item.id, "link_type": link_type, "downloaded": False, "reason": str(e)}
        finally:
            # Remove from active downloads tracking
            with active_downloads_lock:
                active_downloads.discard(cache_key)

@app.route('/api/currently-downloading')
def get_currently_downloading():
    """Get the count of currently active downloads."""
    with active_downloads_lock:
        active_count = len(active_downloads)
        return str(active_count)

@app.route('/batch-download', methods=['POST'])
def batch_download():
    """Endpoint to download multiple selected files in one request."""
    logger.info("Batch download request received")
    try:
        data = request.get_json(silent=True) or {}
        items = data.get('items', [])
        if not items:
            return jsonify({"error": "No items provided"}), 400

        results = []
        for entry in items:
            item_id = entry.get('id')
            link_type = entry.get('type')
            if link_type not in ['pdf', 'zip']:
                # Skip unsupported types (other is just a link)
                results.append({"item_id": item_id, "link_type": link_type, "downloaded": False, "reason": "Unsupported type"})
                continue
            contest_item = db.session.get(Contest, int(item_id))
            if not contest_item:
                results.append({"item_id": item_id, "link_type": link_type, "downloaded": False, "reason": "Contest not found"})
                continue
            results.append(_perform_download(contest_item, link_type))

        # After downloads, return summary and updated cache stats
        cache_stats = download_cache.get_stats()
        return jsonify({"success": True, "results": results, "cache_stats": cache_stats})
    except Exception as e:
        logger.error(f"Error in batch download route: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/set-path')
def set_path_page():
    """Render the path setting page."""
    return render_template('set_path.html', current_path=str(DOWNLOADS_DIR.absolute()))

@app.route('/api/validate-path', methods=['POST'])
def validate_path():
    """Validate a directory path and return absolute path."""
    try:
        data = request.get_json()
        path_str = data.get('path', '').strip()
        
        if not path_str:
            return jsonify({"valid": False, "error": "Please enter a path"})
        
        # expand user path (~/Downloads becomes /Users/username/Downloads)
        try:
            path_obj = _resolve_download_path(path_str)
        except Exception as e:
            return jsonify({"valid": False, "error": f"Invalid path format: {str(e)}"})
        
        # check various conditions
        absolute_path = str(path_obj)
        
        if path_obj.exists():
            if not path_obj.is_dir():
                return jsonify({
                    "valid": False, 
                    "error": "Path exists but is not a directory",
                    "absolute_path": absolute_path
                })
            elif not os.access(path_obj, os.W_OK):
                return jsonify({
                    "valid": False,
                    "error": "Directory exists but is not writable", 
                    "absolute_path": absolute_path
                })
            else:
                return jsonify({
                    "valid": True,
                    "message": "✓ Valid directory",
                    "absolute_path": absolute_path,
                    "exists": True
                })
        else:
            # directory doesn't exist - check if we can create it
            if not path_obj.parent.exists():
                return jsonify({
                    "valid": False,
                    "error": "Parent directory does not exist",
                    "absolute_path": absolute_path
                })
            elif not os.access(path_obj.parent, os.W_OK):
                return jsonify({
                    "valid": False,
                    "error": "Cannot create directory - parent not writable",
                    "absolute_path": absolute_path
                })
            else:
                return jsonify({
                    "valid": True,
                    "message": "✓ Directory will be created",
                    "absolute_path": absolute_path,
                    "exists": False
                })
                
    except Exception as e:
        logger.error(f"Error validating path: {e}")
        return jsonify({"valid": False, "error": "Validation error occurred"})

@app.route('/api/set-path', methods=['POST'])
def set_download_path():
    """Validate and set the download directory path."""
    global DOWNLOADS_DIR, download_cache, config_data
    
    try:
        data = request.get_json()
        path_str = data.get('path', '').strip()
        
        if not path_str:
            return jsonify({"success": False, "error": "Please enter a path"})
        
        # first validate the path
        try:
            path_obj = _resolve_download_path(path_str)
        except Exception as e:
            return jsonify({"success": False, "error": f"Invalid path format: {str(e)}"})
        
        # create directory if it doesn't exist
        if not path_obj.exists():
            if not path_obj.parent.exists():
                return jsonify({"success": False, "error": "Parent directory does not exist"})
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {path_obj}")
            except PermissionError:
                return jsonify({"success": False, "error": "Permission denied - cannot create directory"})
            except Exception as e:
                return jsonify({"success": False, "error": f"Cannot create directory: {str(e)}"})
        
        # verify it's a directory and writable
        if not path_obj.is_dir():
            return jsonify({"success": False, "error": "Path exists but is not a directory"})
        
        # test write access
        test_file = path_obj / '.write_test_uil'
        try:
            test_file.touch()
            test_file.unlink()
        except Exception:
            return jsonify({"success": False, "error": "Directory is not writable"})
        
        # save to config
        old_dir = str(DOWNLOADS_DIR.absolute())
        config_data['download_dir'] = str(path_obj)
        
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            return jsonify({"success": False, "error": f"Cannot save configuration: {str(e)}"})
        
        # update global variables
        DOWNLOADS_DIR = path_obj
        
        # reinitialize download cache for new directory
        download_cache = DownloadCache(DOWNLOADS_DIR)
        
        logger.info(f"Download directory changed from {old_dir} to {DOWNLOADS_DIR}")
        
        return jsonify({
            "success": True,
            "message": f"Download path set to {path_obj}",
            "absolute_path": str(path_obj),
            "cache_files": len(download_cache._cache_index)
        })
        
    except Exception as e:
        logger.error(f"Error setting download path: {e}")
        return jsonify({"success": False, "error": "Failed to set download path"})