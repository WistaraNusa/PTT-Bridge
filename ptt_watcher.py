import subprocess
from datetime import datetime
import os

# --- CONFIG ---
DEVICE_IN = "plughw:2,0"
SAVE_PATH = "./wav"
SILENCE_THRESHOLD = "1%"  # VOX sensitivity
MAX_SILENCE = "2.0"       # Max silence to auto-stop

# Setup
os.makedirs(SAVE_PATH, exist_ok=True)

def record_voice():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recorded_{timestamp}.wav"
    filepath = os.path.join(SAVE_PATH, filename)

    print("🎙️ Start VOX recording... Speak now.")

    subprocess.run([
        "sox", "-t", "alsa", DEVICE_IN,
        "-r", "8000", "-c", "1", "-e", "signed", "-b", "16",
        filepath,
        "silence", "1", "0.1", SILENCE_THRESHOLD,
                   "1", MAX_SILENCE, SILENCE_THRESHOLD
    ])

    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        print(f"✅ Voice saved: {filename}")
    else:
        print("⚠️ No valid voice recorded.")
        if os.path.exists(filepath):
            os.remove(filepath)

# --- RUN ---
record_voice()
