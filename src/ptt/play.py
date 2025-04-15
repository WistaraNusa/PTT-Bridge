# play_recording.py
import subprocess
import os
import time
from gpiozero import LED


def start(
    DEVICE_OUT: str = "plughw:2,0",
    PTT_PIN: int = 17,
    SAVE_PATH: str = "./wav",
    INPUT_FILE: str = "last_recording.wav",
):
    filepath = os.path.join(SAVE_PATH, INPUT_FILE)
    ptt = LED(PTT_PIN)
    ptt.off()

    if not os.path.exists(filepath):
        print("❌ No recording found to play.")
        exit()

    print("📡 Transmitting recording...")
    ptt.on()
    time.sleep(0.3)  # Wait for radio to go TX

    subprocess.run(
        ["aplay", "-D", DEVICE_OUT, "-r", "8000", "-f", "S16_LE", "-c", "1", filepath]
    )

    ptt.off()
    print("✅ Done playing.")
