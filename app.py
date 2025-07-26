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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///info.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Ensure downloads directory exists
DOWNLOADS_DIR = Path('downloads')
DOWNLOADS_DIR.mkdir(exist_ok=True)

# Create a semaphore to limit concurrent downloads
download_semaphore = threading.Semaphore(4)  # Maximum 4 concurrent downloads

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
        return render_template('index.html', error=str(e), contests=[])

@app.route('/download/<int:item_id>/<link_type>')
def download_file(item_id, link_type):
    """Download a file for a specific contest, identified by link_type (pdf, zip, other)."""
    logger.info(f"Download requested for contest ID {item_id}, link type: {link_type}")
    
    if link_type not in ['pdf', 'zip', 'other']:
        return jsonify({"error": "Invalid link type specified. Must be 'pdf', 'zip', or 'other'."}), 400

    try:
        item = db.session.get(Contest, item_id)
        if not item:
            logger.error(f"Contest with ID {item_id} not found")
            return jsonify({"error": "Contest not found"}), 404

        link_map = {
            'pdf': item.pdf_link,
            'zip': item.zip_link,
            'other': item.other_link
        }
        
        url_to_download = link_map.get(link_type)

        if not url_to_download:
            logger.error(f"No {link_type} link found for contest ID {item_id}")
            return jsonify({"error": f"No {link_type} link available for this contest."}), 404

        cache_key = generate_cache_key(
            item.subject, 
            item.level, 
            item.year,
            link_type # use link_type in cache key
        )
        
        cached_path = download_cache.get_cached_file_path(cache_key)
        if cached_path:
            logger.info(f"Serving cached file: {cached_path}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    "success": True, "message": "File already downloaded",
                    "item_id": item_id, "link_type": link_type,
                    "file_path": cached_path, "downloaded": True
                })
            return send_file(cached_path, as_attachment=True)
        
        # If not in cache, download the file
        import requests
        try:
            # Use a semaphore to limit concurrent downloads
            with download_semaphore:
                logger.info(f"Downloading file from {url_to_download}")
                response = requests.get(url_to_download, timeout=30)
                response.raise_for_status()
            
            # Determine file extension from URL
            file_extension = os.path.splitext(url_to_download)[1]
            if not file_extension:
                file_extension = '.dat' # Fallback
            
            # Make sure the extension is properly formed
            if not file_extension.startswith('.'):
                file_extension = '.' + file_extension
                
            # Format the filename according to the pattern
            formatted_filename = format_filename(
                item.subject,
                item.level,
                item.year,
                link_type,
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
                "link_type": link_type,
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

if __name__ == '__main__':
    logger.info("Starting UIL Download Flask application")
    app.run(debug=False, port=5001) 