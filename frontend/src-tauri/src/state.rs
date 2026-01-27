use crate::models::{Contest, QueueItem, UserConfig};
use std::collections::HashSet;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::RwLock;

// shared application state
pub struct AppState {
    pub contests: RwLock<Vec<Contest>>,
    pub config: RwLock<UserConfig>,
    pub cache: RwLock<CacheIndex>,
    pub queue: RwLock<Vec<QueueItem>>,
    pub info_version: RwLock<u32>,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            contests: RwLock::new(Vec::new()),
            config: RwLock::new(UserConfig::default()),
            cache: RwLock::new(CacheIndex::new(PathBuf::new())),
            queue: RwLock::new(Vec::new()),
            info_version: RwLock::new(0),
        }
    }
}

// in-memory cache of downloaded files
pub struct CacheIndex {
    pub downloaded: HashSet<String>,
    pub downloads_dir: PathBuf,
}

impl CacheIndex {
    pub fn new(downloads_dir: PathBuf) -> Self {
        Self {
            downloaded: HashSet::new(),
            downloads_dir,
        }
    }

    pub fn is_cached(&self, id: &str) -> bool {
        self.downloaded.contains(id)
    }

    pub fn mark_downloaded(&mut self, id: &str) {
        self.downloaded.insert(id.to_string());
    }

    pub fn mark_removed(&mut self, id: &str) {
        self.downloaded.remove(id);
    }

    pub fn count(&self) -> usize {
        self.downloaded.len()
    }

    // scan downloads folder and rebuild cache
    pub fn rebuild(&mut self, contests: &[Contest]) {
        self.downloaded.clear();
        if !self.downloads_dir.exists() {
            return;
        }

        let Ok(entries) = std::fs::read_dir(&self.downloads_dir) else {
            return;
        };

        for entry in entries.flatten() {
            let path = entry.path();
            if let Some(id) = filename_to_cache_id(&path, contests) {
                self.downloaded.insert(id);
            }
        }
    }
}

// convert filename back to cache ID by matching against contests
fn filename_to_cache_id(path: &std::path::Path, contests: &[Contest]) -> Option<String> {
    let stem = path.file_stem()?.to_str()?;
    let ext = path.extension()?.to_str()?;

    // filename format: {Subject}_{Year}_{Level}.{ext}
    let parts: Vec<&str> = stem.rsplitn(3, '_').collect();
    if parts.len() < 3 {
        return None;
    }

    let level = parts[0];
    let year: u16 = parts[1].parse().ok()?;
    let subject = parts[2];

    // find matching contest
    let contest = contests.iter().find(|c| {
        c.subject.replace(' ', "-") == subject.replace(' ', "-")
            && c.year == year
            && c.level.replace(' ', "-") == level.replace(' ', "-")
    })?;

    // determine file type from extension
    let file_type = match ext.to_lowercase().as_str() {
        "pdf" => "pdf",
        "zip" => "zip",
        _ => "other",
    };

    Some(format!("{}_{}", contest.id, file_type))
}

// generate filename for a download
pub fn cache_id_to_filename(contest: &Contest, file_type: &str) -> String {
    let subject = contest.subject.replace(' ', "-");
    let level = contest.level.replace(' ', "-");
    let ext = match file_type {
        "pdf" => "pdf",
        "zip" => "zip",
        _ => "link",
    };
    format!("{}_{}_{}.{}", subject, contest.year, level, ext)
}
