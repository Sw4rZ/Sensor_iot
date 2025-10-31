import os
import time
import base64
import requests
import serial
from datetime import datetime

# -----------------------------
# CONFIGURATION
# -----------------------------
GITHUB_TOKEN = "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"   # <-- paste your token
REPO_OWNER   = "Sw4rZ"
REPO_NAME    = "Sensor_iot"
FILE_PATH    = "sensor_log.txt"

SERIAL_PORT  = "COM7"   # ✅ Updated port
BAUD_RATE    = 9600
BATCH_LINES  = 5
UPLOAD_INTERVAL = 10

API_URL_CONTENT = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# -----------------------------
# FUNCTIONS
# -----------------------------
def get_file_info():
    r = requests.get(API_URL_CONTENT, headers=HEADERS)
    if r.status_code == 200:
        return r.json()
    else:
        raise RuntimeError(f"Failed to get file info: {r.status_code} {r.text}")

def upload_content(new_content, sha, message="Update log"):
    payload = {
        "message": message,
        "content": base64.b64encode(new_content.encode()).decode(),
        "sha": sha
    }
    r = requests.put(API_URL_CONTENT, headers=HEADERS, json=payload)
    if r.status_code in (200, 201):
        return r.json()
    else:
        raise RuntimeError(f"Upload failed: {r.status_code} {r.text}")

def append_lines_to_github(lines):
    info = get_file_info()
    sha = info["sha"]
    old = base64.b64decode(info["content"]).decode("utf-8")
    updated = old + "".join(lines)
    upload_content(updated, sha, message=f"Added {len(lines)} sensor entries")

def format_line(raw):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"{ts} - {raw}\n"

# -----------------------------
# MAIN PROCESS
# -----------------------------
def main():
    buffer = []
    last_upload = time.time()

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"✅ Listening on {SERIAL_PORT} @ {BAUD_RATE}")
    except Exception as e:
        print("❌ Serial error:", e)
        return

    while True:
        try:
            raw = ser.readline().decode(errors="ignore").strip()
            if raw:
                print("📡 Serial:", raw)
                buffer.append(format_line(raw))

            now = time.time()
            if (len(buffer) >= BATCH_LINES) or (now - last_upload >= UPLOAD_INTERVAL and buffer):
                append_lines_to_github(buffer)
                print(f"✅ Uploaded {len(buffer)} lines to GitHub")
                buffer = []
                last_upload = now

        except KeyboardInterrupt:
            print("\n⛔ Exiting manually.")
            if buffer:
                append_lines_to_github(buffer)
                print("✅ Final lines uploaded.")
            break
        except Exception as e:
            print("⚠️ Error:", e)
            time.sleep(1)

if __name__ == "__main__":
    main()
