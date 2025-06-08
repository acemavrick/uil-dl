import os
import json
import sqlite3
import logging
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename

# build tailwindcss
# os.system("npx tailwindcss -i ./static/css/in.css -o ./static/css/out.css")

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

file_handler = logging.FileHandler('logs/dev.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

# Create Flask app
app = Flask(__name__)

# Ensure downloads directory exists
DOWNLOADS_DIR = Path('downloads')
DOWNLOADS_DIR.mkdir(exist_ok=True)

# Create a semaphore to limit concurrent downloads
download_semaphore = threading.Semaphore(4)  # Maximum 4 concurrent downloads

# Initialize database connection
def get_db_connection():
    """Connect to the SQLite database and return the connection."""
    try:
        conn = sqlite3.connect('info.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        return None

class DownloadCache:
    """Class to manage the download cache."""
    CACHE_FILE = "cache_manifest.json"
    
    def __init__(self, downloads_dir=DOWNLOADS_DIR):
        self.downloads_dir = Path(downloads_dir)
        self.downloads_dir.mkdir(exist_ok=True)
        self._cache_index = {}
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

def format_filename(item_type, subject, level, year, extension):
    """Format filename according to the required pattern: subject_year_level(_data).extension"""
    base_name = f"{subject.replace(' ', '_')}_{year}_{level.replace(' ', '_')}"
    if item_type == "data_file":
        return f"{base_name}_data{extension}"
    return f"{base_name}{extension}"

def generate_cache_key(item_type, subject, level, year):
    """Generate a consistent cache key for a contest or data file."""
    base_key = f"{subject.replace(' ', '_')}_{year}_{level.replace(' ', '_')}"
    if item_type == "data_file":
        return f"{base_key}_data"
    return base_key

@app.route('/')
def index():
    """Render the main page."""
    logger.info("Loading main page")
    try:
        conn = get_db_connection()
        if conn is None:
            return render_template('index.html', error="Database connection failed", contests=[])
        
        # Get unique subjects, levels, and years for filters
        subjects = conn.execute('SELECT DISTINCT subject FROM contests ORDER BY subject').fetchall()
        levels = conn.execute('SELECT DISTINCT level FROM contests ORDER BY level').fetchall()
        years = conn.execute('SELECT DISTINCT year FROM contests ORDER BY year DESC').fetchall()
        
        conn.close()
        
        # Get cache stats
        cache_stats = download_cache.get_stats()
        
        return render_template('index.html', 
                               subjects=[s['subject'] for s in subjects],
                               levels=[l['level'] for l in levels],
                               years=[y['year'] for y in years],
                               cache_stats=cache_stats)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return render_template('index.html', error=str(e), contests=[])

@app.route('/download/<int:item_id>/<item_type>')
def download_file(item_id, item_type):
    """Download a file for a specific contest or data file."""
    logger.info(f"Download requested for {item_type} ID: {item_id}")
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Get item info based on type
        if item_type == 'contest':
            item = conn.execute('SELECT * FROM contests WHERE id = ?', (item_id,)).fetchone()
            table_name = 'contests'
        elif item_type == 'data_file':
            item = conn.execute('SELECT * FROM data_files WHERE id = ?', (item_id,)).fetchone()
            table_name = 'data_files'
        else:
            conn.close()
            return jsonify({"error": "Invalid item type"}), 400
        
        conn.close()
        
        if not item:
            logger.error(f"{item_type.capitalize()} with ID {item_id} not found")
            return jsonify({"error": f"{item_type.capitalize()} not found"}), 404
        
        # Create a key for the cache
        cache_key = generate_cache_key(
            item_type, 
            item['subject'], 
            item['level'], 
            item['year']
        )
        
        # Check if the file is already in the cache
        cached_path = download_cache.get_cached_file_path(cache_key)
        if cached_path:
            logger.info(f"Serving cached file: {cached_path}")
            # Return success response for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    "success": True,
                    "message": "File already downloaded",
                    "item_id": item_id,
                    "item_type": item_type,
                    "file_path": cached_path,
                    "downloaded": True
                })
            # Otherwise serve the file directly
            return send_file(cached_path, as_attachment=True)
        
        # If not in cache, download the file
        import requests
        try:
            # Use a semaphore to limit concurrent downloads
            with download_semaphore:
                logger.info(f"Downloading file from {item['link']}")
                response = requests.get(item['link'], timeout=30)
                response.raise_for_status()
            
            # Determine file extension from URL
            file_extension = os.path.splitext(item['link'])[1]
            if not file_extension:
                # Guess extension from content type
                content_type = response.headers.get('Content-Type', '')
                if 'pdf' in content_type:
                    file_extension = '.pdf'
                elif 'zip' in content_type or 'application/octet-stream' in content_type:
                    file_extension = '.zip'
                else:
                    file_extension = '.dat'
            
            # Make sure the extension is properly formed
            if not file_extension.startswith('.'):
                file_extension = '.' + file_extension
                
            # Format the filename according to the pattern
            formatted_filename = format_filename(
                item_type,
                item['subject'],
                item['level'],
                item['year'],
                file_extension
            )
            
            # Create the file in the downloads directory
            file_path = DOWNLOADS_DIR / formatted_filename
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Add to cache
            download_cache.add_to_cache(cache_key, str(file_path))
            
            logger.info(f"File downloaded successfully: {file_path}")
            
            # Return success response with file info
            return jsonify({
                "success": True,
                "message": "File downloaded successfully",
                "item_id": item_id,
                "item_type": item_type,
                "file_path": str(file_path),
                "downloaded": True
            })
            
        except requests.RequestException as e:
            logger.error(f"Download error: {e}")
            return jsonify({"error": f"Download failed: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Error in download route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/refresh-cache')
def refresh_cache():
    """Refresh the download cache."""
    logger.info("Refreshing download cache")
    count = download_cache.rebuild_cache()
    return jsonify({
        "success": True,
        "message": f"Cache refreshed. Found {count} files.",
        "count": count
    })

@app.route('/reset-cache')
def reset_cache():
    """Reset the download cache (forget all downloads)."""
    logger.info("Resetting download cache")
    count = download_cache.reset_cache()
    return jsonify({
        "success": True,
        "message": f"Cache reset. Forgot {count} files.",
        "count": count
    })

@app.route('/api/contests')
def get_contests():
    """API endpoint to get contest data with their associated data files."""
    try:
        # Get filter parameters (can have multiple values per parameter)
        subjects = request.args.getlist('subject')
        levels = request.args.getlist('level')
        years = request.args.getlist('year')
        downloaded = request.args.get('downloaded')
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Build query to get all contests and all data files, including unlinked ones.
        # This is done by finding all unique (subject, level, year) combinations
        # and then LEFT JOINING both contests and data_files to that set.

        where_conditions = []
        params = []
        if subjects:
            placeholders = ', '.join(['?'] * len(subjects))
            where_conditions.append(f"subject IN ({placeholders})")
            params.extend(subjects)
        
        if levels:
            placeholders = ', '.join(['?'] * len(levels))
            where_conditions.append(f"level IN ({placeholders})")
            params.extend(levels)
        
        if years:
            placeholders = ', '.join(['?'] * len(years))
            where_conditions.append(f"year IN ({placeholders})")
            params.extend([int(year) for year in years])

        # The WHERE clause applies to both parts of the UNION inside the CTE
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
            # Parameters need to be duplicated for the two SELECTs in the UNION
            params = params * 2

        query = f"""
            WITH all_items AS (
                SELECT subject, level, year FROM contests {where_clause}
                UNION
                SELECT subject, level, year FROM data_files {where_clause}
            )
            SELECT
                i.subject, i.level, i.year,
                c.id AS contest_id, c.link AS contest_link,
                d.id AS data_file_id, d.link AS data_file_link
            FROM all_items i
            LEFT JOIN contests c ON i.subject = c.subject AND i.level = c.level AND i.year = c.year
            LEFT JOIN data_files d ON i.subject = d.subject AND i.level = d.level AND i.year = d.year
            ORDER BY i.subject, i.level, i.year DESC
        """
        
        contests = conn.execute(query, params).fetchall()
        conn.close()
        
        result = []
        for item in contests:
            contest_dict = {
                'id': item['contest_id'],  # May be None if it's a data_file-only item
                'subject': item['subject'],
                'level': item['level'],
                'year': item['year'],
                'contest': None,
                'data_file': None
            }
            
            # Add contest info if available
            if item['contest_id']:
                contest_dict['contest'] = {
                    'id': item['contest_id'],
                    'link': item['contest_link'],
                    'downloaded': download_cache.is_cached(generate_cache_key('contest', item['subject'], item['level'], item['year']))
                }

            # Add data file info if available
            if item['data_file_id']:
                contest_dict['data_file'] = {
                    'id': item['data_file_id'],
                    'link': item['data_file_link'],
                    'downloaded': download_cache.is_cached(generate_cache_key('data_file', item['subject'], item['level'], item['year']))
                }
            
            # Filter by download status if requested
            if downloaded == 'true':
                # Item is considered fully downloaded if all its available parts are downloaded.
                contest_downloaded = not contest_dict['contest'] or contest_dict['contest']['downloaded']
                data_file_downloaded = not contest_dict['data_file'] or contest_dict['data_file']['downloaded']
                if contest_downloaded and data_file_downloaded:
                    result.append(contest_dict)
            elif downloaded == 'false':
                # Item is considered "not downloaded" if any of its parts are missing.
                contest_missing = contest_dict['contest'] and not contest_dict['contest']['downloaded']
                data_file_missing = contest_dict['data_file'] and not contest_dict['data_file']['downloaded']
                if contest_missing or data_file_missing:
                    result.append(contest_dict)
            else:
                result.append(contest_dict)
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in API route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get download cache statistics."""
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
            
        total_contests = conn.execute('SELECT COUNT(*) FROM contests').fetchone()[0]
        total_data_files = conn.execute('SELECT COUNT(*) FROM data_files').fetchone()[0]
        conn.close()
        
        cache_stats = download_cache.get_stats()
        
        stats = {
            "total_contests": total_contests,
            "total_data_files": total_data_files,
            "downloaded_files": cache_stats['total_files'],
            "download_size_bytes": cache_stats['total_size'],
            "download_percentage": (cache_stats['total_files'] / (total_contests + total_data_files)) * 100 if (total_contests + total_data_files) > 0 else 0
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error in stats route: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting UIL Download Flask application")
    app.run(debug=False, port=5001) 