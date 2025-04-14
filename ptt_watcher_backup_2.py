import subprocess
from datetime import datetime
import os

DEVICE_IN = "plughw:2,0"
SAVE_PATH = "./wav"
SILENCE_THRESHOLD = "10%"  # How loud to trigger (lower = more sensitive)
MAX_SILENCE = "2.0"         # How long silence before stopping (seconds)

os.makedirs(SAVE_PATH, exist_ok=True)
print(f"🎤 Smart VOX activated! Listening on {DEVICE_IN}")

try:
    while True:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recorded_{timestamp}.wav"
        filepath = os.path.join(SAVE_PATH, filename)

        print("🟡 Listening for voice...")

        subprocess.run([
            "sox", "-t", "alsa", DEVICE_IN,
            "-r", "8000", "-c", "1", "-e", "signed", "-b", "16",
            filepath,
            "silence", "1", "0.1", SILENCE_THRESHOLD,
                       "1", MAX_SILENCE, SILENCE_THRESHOLD
        ])

        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            print(f"🎙️ Sound detected! Saved: {filename}\n")
        else:
            print("⚪ No voice activity detected, skipping...\n")
            if os.path.exists(filepath):
                os.remove(filepath)

except KeyboardInterrupt:
    print("❌ Interrupted, exiting...")
