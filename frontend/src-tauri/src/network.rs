// network state management
use std::time::{Duration, SystemTime};

#[derive(Debug, Clone)]
pub struct NetworkState {
    pub online: bool,
    pub last_check: SystemTime,
    pub last_error: Option<String>,
}

impl NetworkState {
    pub fn new() -> Self {
        Self {
            online: true, // assume online initially
            last_check: SystemTime::now(),
            last_error: None,
        }
    }

    /// check if we should retry checking network status
    pub fn should_recheck(&self) -> bool {
        if self.online {
            return false; // don't recheck if online
        }

        // recheck every 60 seconds when offline
        match self.last_check.elapsed() {
            Ok(elapsed) => elapsed > Duration::from_secs(60),
            Err(_) => true,
        }
    }

    /// mark as offline with error
    pub fn mark_offline(&mut self, error: String) {
        self.online = false;
        self.last_error = Some(error);
        self.last_check = SystemTime::now();
    }

    /// mark as online
    pub fn mark_online(&mut self) {
        self.online = true;
        self.last_error = None;
        self.last_check = SystemTime::now();
    }
}

/// check if network is available by making lightweight request
pub async fn check_network_connectivity() -> bool {
    // try to fetch status code of a simple request
    match reqwest::Client::builder()
        .timeout(Duration::from_secs(5))
        .build()
    {
        Ok(client) => {
            match client
                .get("https://www.google.com")
                .send()
                .await
            {
                Ok(resp) => resp.status().is_success(),
                Err(_) => false,
            }
        }
        Err(_) => false,
    }
}

/// determine if error is network-related
pub fn is_network_error(error: &str) -> bool {
    let error_lower = error.to_lowercase();
    error_lower.contains("network")
        || error_lower.contains("dns")
        || error_lower.contains("connection")
        || error_lower.contains("timeout")
        || error_lower.contains("unreachable")
        || error_lower.contains("offline")
}
