// download logic with progress tracking
use reqwest;
use std::path::Path;
use tokio::fs;
use tokio::io::AsyncWriteExt;

#[derive(Debug)]
pub enum DownloadError {
    Network(String),
    Filesystem(String),
    Verification(String),
    RateLimited(Option<u64>), // optional retry-after seconds
}

impl std::fmt::Display for DownloadError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            DownloadError::Network(e) => write!(f, "network error: {}", e),
            DownloadError::Filesystem(e) => write!(f, "filesystem error: {}", e),
            DownloadError::Verification(e) => write!(f, "verification error: {}", e),
            DownloadError::RateLimited(secs) => match secs {
                Some(s) => write!(f, "rate limited (retry after {}s)", s),
                None => write!(f, "rate limited"),
            },
        }
    }
}

impl std::error::Error for DownloadError {}

pub struct DownloadOptions {
    pub url: String,
    pub dest_path: std::path::PathBuf,
    pub expected_size: Option<u64>,
}

/// download file with progress tracking
/// returns Ok(bytes_written) on success
pub async fn download_file<F>(
    options: DownloadOptions,
    mut progress_callback: F,
) -> Result<u64, DownloadError>
where
    F: FnMut(u64, Option<u64>) + Send,
{
    // create temp file path
    let temp_path = options.dest_path.with_extension("tmp");

    // ensure parent directory exists
    if let Some(parent) = options.dest_path.parent() {
        fs::create_dir_all(parent)
            .await
            .map_err(|e| DownloadError::Filesystem(format!("create parent dir: {}", e)))?;
    }

    // start download (connect timeout only — no total timeout for large files)
    let client = reqwest::Client::builder()
        .connect_timeout(std::time::Duration::from_secs(15))
        .build()
        .map_err(|e| DownloadError::Network(format!("client error: {}", e)))?;

    let response = client
        .get(&options.url)
        .send()
        .await
        .map_err(|e| DownloadError::Network(format!("request failed: {}", e)))?;

    // check status — detect rate limiting
    let status = response.status();
    if status == reqwest::StatusCode::TOO_MANY_REQUESTS || status == reqwest::StatusCode::SERVICE_UNAVAILABLE {
        let retry_after = response
            .headers()
            .get("retry-after")
            .and_then(|v| v.to_str().ok())
            .and_then(|v| v.parse::<u64>().ok());
        return Err(DownloadError::RateLimited(retry_after));
    }
    if !status.is_success() {
        return Err(DownloadError::Network(format!("http status: {}", status)));
    }

    // get content length if available
    let total_size = response.content_length();

    // open temp file for writing
    let mut file = fs::File::create(&temp_path)
        .await
        .map_err(|e| DownloadError::Filesystem(format!("create temp file: {}", e)))?;

    // stream download with progress tracking
    let mut downloaded: u64 = 0;
    let mut stream = response.bytes_stream();

    use futures_util::StreamExt;
    while let Some(chunk) = stream.next().await {
        let chunk = chunk.map_err(|e| DownloadError::Network(format!("stream error: {}", e)))?;

        file.write_all(&chunk)
            .await
            .map_err(|e| DownloadError::Filesystem(format!("write chunk: {}", e)))?;

        downloaded += chunk.len() as u64;
        progress_callback(downloaded, total_size);
    }

    // flush and close file
    file.flush()
        .await
        .map_err(|e| DownloadError::Filesystem(format!("flush file: {}", e)))?;
    drop(file);

    // verify size if expected_size provided
    if let Some(expected) = options.expected_size {
        if downloaded != expected {
            // cleanup temp file
            let _ = fs::remove_file(&temp_path).await;
            return Err(DownloadError::Verification(format!(
                "size mismatch: expected {}, got {}",
                expected, downloaded
            )));
        }
    }

    // verify size matches content-length if available
    if let Some(total) = total_size {
        if downloaded != total {
            let _ = fs::remove_file(&temp_path).await;
            return Err(DownloadError::Verification(format!(
                "incomplete download: expected {}, got {}",
                total, downloaded
            )));
        }
    }

    // move temp file to final destination atomically
    fs::rename(&temp_path, &options.dest_path)
        .await
        .map_err(|e| DownloadError::Filesystem(format!("move to dest: {}", e)))?;

    Ok(downloaded)
}

/// cleanup temp file if it exists
pub async fn cleanup_temp_file(dest_path: &Path) {
    let temp_path = dest_path.with_extension("tmp");
    if temp_path.exists() {
        let _ = fs::remove_file(&temp_path).await;
    }
}
