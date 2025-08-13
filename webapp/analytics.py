from platform import platform
import os, time, uuid, json, dotenv
from pathlib import Path
import requests

dotenv.load_dotenv()
relay_url = os.environ.get("GA4_RELAY_URL")
CID = None
SID = None
CONSENT = False
MT = True

def analytics_enabled():
    return CONSENT and bool(relay_url) and bool(CID) and bool(SID) and MT

def init(appdir):
    global CID, SID, CONSENT

    consentFile = appdir / "ga4_csnt"

    # get cid
    cid_file = appdir / "ga4_cid"
    if not cid_file.exists():
        # treat as new install, generate new cid and enable consent
        cid_file.touch()
        consentFile.touch()
        cid_file.write_text(str(uuid.uuid4()))

    CID = cid_file.read_text().strip()
    CONSENT = consentFile.exists()

    SID = int(time.time())
    send_event("app_startup", {"app_version": os.environ.get("APP_VERSION")})

def send_event(name, params=None):
    if not analytics_enabled():
        return 0, "analytics_disabled"
    
    if not isinstance(name, str) or not name:
        return 400, "invalid_event_name"
    
    event_params = dict(params or {})

    # set basic params
    event_params["session_id"] = SID
    event_params["engagement_time_msec"] = 10
    event_params["app_version"] = os.environ.get("APP_VERSION")
    event_params["os"] = platform()

    body = {
        "client_id": CID,
        "events": [
            {
                "name": name,
                "params": event_params,
            }
        ]
    }

    headers = {"content-type": "application/json"}

    try:
        resp = requests.post(relay_url, json=body, headers=headers, timeout=10, verify=False)
    except Exception as e:
        return 0, f"network_error: {e}"
    
    try:
        return resp.status_code, resp.json()
    except Exception as e:
        # couldn't parse response, return raw text
        return resp.status_code, resp.text