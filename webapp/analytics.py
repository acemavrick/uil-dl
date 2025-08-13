import sys, platform, os, time, uuid, dotenv
from pathlib import Path
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

dotenv.load_dotenv()
relay_url = os.environ.get("GA4_RELAY_URL")
CID = None
SID = None
CONSENT = True
MT = True

def analytics_enabled_verbose():
    if not CONSENT:
        return False, "no consent"
    if not relay_url:
        return False, "no relay url"
    if not CID:
        return False, "no cid"
    if not SID:
        return False, "no sid"
    if not MT:
        return False, "no mt"
    return True, None

def analytics_enabled():
    return analytics_enabled_verbose()[0]

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

def ga4_detailed_device_info():
    system = platform.system()
    release = platform.release()
    version = platform.version()
    platplat = platform.platform()
    machine = platform.machine()
    processor = platform.processor()
    architecture = platform.architecture()
    name = os.name
    sys_platform = sys.platform

    
    return {
        "system": system,
        "release": release,
        "version": version,
        "platform": platplat,
        "machine": machine,
        "processor": processor,
        "architecture": ":".join(architecture),
        "os_name": name,
        "sys_platform": sys_platform
    }


def send_event(name, params=None):
    enabled, reason = analytics_enabled_verbose()
    if not enabled:
        return 0, f"analytics_disabled: {reason}"
    
    if not isinstance(name, str) or not name:
        return 400, "invalid_event_name"
    
    event_params = dict(params or {})

    # set basic params
    event_params["session_id"] = SID
    event_params["engagement_time_msec"] = 10
    event_params["app_version"] = os.environ.get("APP_VERSION")
    deviceInfo = ga4_detailed_device_info()
    event_params.update(deviceInfo)

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

def test():
    global CID, SID, CONSENT
    # CID = str(uuid.uuid4())
    SID = int(time.time())
    print(CID, SID, CONSENT)
    print(send_event("test_event", {"test_param": "test_value", "debug_mode": 1}))

if __name__ == "__main__":
    test()