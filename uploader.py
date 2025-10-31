import serial
import requests
import base64
from datetime import datetime

# ----------- GitHub CONFIG -----------
GITHUB_TOKEN = "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"
REPO_OWNER   = "Sw4rZ"                     
REPO_NAME    = "sensor-cloud"              
FILE_PATH    = "sensor_log.txt"           
# ------------------------------------


# ----------- Arduino CONFIG ----------
SERIAL_PORT = "COM4"   # change this
BAUD_RATE = 9600
# -------------------------------------

def get_file_sha():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    return r.json()["sha"]

def upload_line(line):
    sha = get_file_sha()
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"

    new_line = f"{datetime.now()} - {line}\n"

    # Get old content
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    old_content = base64.b64decode(r.json()["content"]).decode("utf-8")

    updated_content = old_content + new_line
    encoded = base64.b64encode(updated_content.encode()).decode()

    data = {
        "message": "update log",
        "content": encoded,
        "sha": sha
    }

    requests.put(url, json=data, headers=headers)
    print("Uploaded:", new_line)

# ------------- READ SERIAL ------------
ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
print("Started reading…")

while True:
    try:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if line:
            print("Serial:", line)
            upload_line(line)
    except KeyboardInterrupt:
        print("Stopped.")
        break
