import os
import json
import logging
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from sqlalchemy import func
from models import db, Contest

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
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.abspath("info.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create tables within app context
with app.app_context():
    db.create_all()

# Ensure downloads directory exists
DOWNLOADS_DIR = Path('downloads')
DOWNLOADS_DIR.mkdir(exist_ok=True)

# Create a semaphore to limit concurrent downloads
download_semaphore = threading.Semaphore(4)  # Maximum 4 concurrent downloads

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
    CACHE_FILE = "cache_manifest.json"
    
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

@app.route('/')
def index():
    """Render the main page."""
    logger.info("Loading main page")
    try:
        # Use SQLAlchemy to get distinct values for filters
        subjects = [s[0] for s in db.session.query(Contest.subject).distinct().order_by(Contest.subject).all()]
        levels = [l[0] for l in db.session.query(Contest.level).distinct().order_by(Contest.level).all()]
        years = [y[0] for y in db.session.query(Contest.year).distinct().order_by(Contest.year.desc()).all()]

        # Get cache stats
        cache_stats = download_cache.get_stats()
        
        return render_template('index.html',
                               subjects=subjects,
                               levels=levels,
                               years=years,
                               cache_stats=cache_stats)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        # Get cache stats even when there's an error
        cache_stats = download_cache.get_stats()
        return render_template('index.html', error=str(e), contests=[], cache_stats=cache_stats)

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
            "download_percentage": (cache_stats['total_files'] / total_files) * 100 if total_files > 0 else 0
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error in stats route: {e}")
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
            tmp_path = file_path.with_suffix(file_path.suffix + '.tmp')

            # atomic streaming write to tmp then rename
            with open(tmp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            tmp_path.replace(file_path)

            download_cache.add_to_cache(cache_key, str(file_path))
            return {"item_id": contest_item.id, "link_type": link_type, "downloaded": True, "cached": False, "file_path": str(file_path)}
        except Exception as e:
            logger.error(f"Download error for item {contest_item.id} ({link_type}): {e}")
            return {"item_id": contest_item.id, "link_type": link_type, "downloaded": False, "reason": str(e)}


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

if __name__ == '__main__':
    logger.info("Starting UIL Download Flask application")
    app.run(debug=False, port=5001) 