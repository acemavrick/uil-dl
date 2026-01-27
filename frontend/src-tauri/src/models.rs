use serde::{Deserialize, Serialize};
use std::collections::HashMap;

// raw info.json format from UIL website
#[derive(Debug, Deserialize)]
pub struct RawInfo {
    pub linkdata: HashMap<String, String>,
    #[serde(rename = "subjectDict")]
    pub subject_dict: HashMap<String, String>,
    #[serde(rename = "titleAbbrevs")]
    pub title_abbrevs: HashMap<String, String>,
    pub version: u32,
}

// contest with assigned ID for IPC
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Contest {
    pub id: u32,
    pub subject: String,
    pub level: String,
    pub year: u16,
    pub level_sort: u8,
    pub pdf_link: Option<String>,
    pub zip_link: Option<String>,
    pub other_link: Option<String>,
}

// user preferences
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserConfig {
    pub download_dir: String,
    pub dev_mode: bool,
}

impl Default for UserConfig {
    fn default() -> Self {
        let download_dir = dirs::download_dir()
            .map(|p| p.join("UIL-DL"))
            .unwrap_or_else(|| std::path::PathBuf::from("./downloads"))
            .to_string_lossy()
            .to_string();
        Self {
            download_dir,
            dev_mode: false,
        }
    }
}

// loading progress event payload
#[derive(Debug, Clone, Serialize)]
pub struct LoadingProgress {
    pub stage: String,
    pub done: bool,
    pub message: Option<String>,
    pub count: Option<u32>,
}

// queue item for downloads
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QueueItem {
    pub id: String, // "{contest_id}_{type}" e.g. "42_pdf"
    pub contest_id: u32,
    pub file_type: String, // "pdf", "zip", or "other"
    pub status: QueueStatus,
    pub progress: Option<DownloadProgress>,
    pub error: Option<String>,
    pub retries: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum QueueStatus {
    Pending,
    Downloading,
    Complete,
    Failed,
    Cancelled,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DownloadProgress {
    pub bytes: u64,
    pub total: Option<u64>,
}

// queue update event payload
#[derive(Debug, Clone, Serialize)]
pub struct QueueUpdate {
    pub queue: Vec<QueueItem>,
    pub active_count: usize,
    pub pending_count: usize,
    pub completed_count: usize,
}

// request to add items to queue
#[derive(Debug, Deserialize)]
pub struct QueueRequest {
    pub contest_id: u32,
    pub file_type: String,
}
