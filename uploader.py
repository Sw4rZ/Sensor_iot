import os
import time
import base64
import requests
import serial
from datetime import datetime
from dotenv import load_dotenv

# Load .env
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME  = os.getenv("REPO_NAME")
FILE_PATH  = os.getenv("FILE_PATH")
SERIAL_PORT = os.getenv("SERIAL_PORT")
BAUD_RATE   = int(os.getenv("BAUD_RATE", "9600"))
BATCH_LINES = int(os.getenv("BATCH_LINES", "1"))
UPLOAD_INTERVAL = int(os.getenv("UPLOAD_INTERVAL", "3"))

API_URL_CONTENT = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

# -----------------------------
# Validate token before uploading
# -----------------------------
def validate_token():
    r = requests.get("https://api.github.com/user", headers=HEADERS)
    if r.status_code != 200:
        print("❌ Token invalid or unauthorized:", r.status_code, r.text)
        exit(1)
    print("✅ Token validated for user:", r.json()["login"])

# -----------------------------
# Get file SHA and content
# -----------------------------
def get_file_info():
    r = requests.get(API_URL_CONTENT, headers=HEADERS)
    r.raise_for_status()
    data = r.json()
    sha = data["sha"]
    content = base64.b64decode(data["content"]).decode("utf-8")
    return sha, content

# -----------------------------
# Upload new lines
# -----------------------------
def upload_lines(lines):
    sha, old_content = get_file_info()
    timestamped_lines = "".join([f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} - {l}\n" for l in lines])
    new_content = old_content + timestamped_lines
    payload = {"message": f"Append {len(lines)} sensor lines", "content": base64.b64encode(new_content.encode()).decode(), "sha": sha}
    r = requests.put(API_URL_CONTENT, headers=HEADERS, json=payload)
    r.raise_for_status()
    print(f"✅ Uploaded {len(lines)} lines to GitHub")

# -----------------------------
# Main loop
# -----------------------------
def main():
    buffer = []
    last_upload = time.time()

    validate_token()

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"📡 Listening on {SERIAL_PORT} @ {BAUD_RATE}")
    except Exception as e:
        print("❌ Could not open serial port:", e)
        return

    while True:
        try:
            raw = ser.readline().decode(errors="ignore").strip()
            if raw:
                print("Serial:", raw)
                buffer.append(raw)

            now = time.time()
            if len(buffer) >= BATCH_LINES or (now - last_upload >= UPLOAD_INTERVAL and buffer):
                upload_lines(buffer)
                buffer = []
                last_upload = now

        except KeyboardInterrupt:
            print("⛔ Exiting by user")
            if buffer:
                upload_lines(buffer)
            break
        except Exception as e:
            print("⚠️ Error:", e)
            time.sleep(1)

if __name__ == "__main__":
    main()
