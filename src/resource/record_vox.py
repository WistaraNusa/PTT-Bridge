# record_vox.py
import subprocess
import os

DEVICE_IN = "plughw:2,0"
SAVE_PATH = "./wav"
OUTPUT_FILE = "last_recording.wav"
SILENCE_THRESHOLD = "1%"
MAX_SILENCE = "2.0"

os.makedirs(SAVE_PATH, exist_ok=True)
filepath = os.path.join(SAVE_PATH, OUTPUT_FILE)

print("🎙️ Listening... Speak to record.")

subprocess.run(
    [
        "sox",
        "-t",
        "alsa",
        DEVICE_IN,
        "-r",
        "8000",
        "-c",
        "1",
        "-e",
        "signed",
        "-b",
        "16",
        filepath,
        "silence",
        "1",
        "0.1",
        SILENCE_THRESHOLD,
        "1",
        MAX_SILENCE,
        SILENCE_THRESHOLD,
    ]
)

if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
    print(f"✅ Recorded and saved to: {filepath}")
else:
    print("⚠️ No valid audio recorded.")
    if os.path.exists(filepath):
        os.remove(filepath)
