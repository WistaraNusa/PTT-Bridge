import subprocess
from datetime import datetime
import os

DEVICE_IN = "plughw:2,0"
SAVE_PATH = "./wav"
RECORD_TIMEOUT = 10  # Max seconds to wait for sound + record
THRESHOLD_DB = 50  # Lower = more sensitive

os.makedirs(SAVE_PATH, exist_ok=True)
print(f"🎤 Waiting for sound... (device: {DEVICE_IN})")

try:
    while True:
        filename = f"recorded_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        filepath = os.path.join(SAVE_PATH, filename)

        print("🟡 Listening for sound...")
        result = subprocess.run(
            [
                "arecord",
                "-D",
                DEVICE_IN,
                "-r",
                "8000",
                "-f",
                "S16_LE",
                "-c",
                "1",
                "-d",
                str(RECORD_TIMEOUT),
                "--vumeter=mono",
                "--quiet",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Check if any data was actually recorded
        if len(result.stdout) > 0 or len(result.stderr) > 100:
            print(f"🔴 Sound detected — saving to {filename}")

            subprocess.run(
                [
                    "arecord",
                    "-D",
                    DEVICE_IN,
                    "-r",
                    "8000",
                    "-f",
                    "S16_LE",
                    "-c",
                    "1",
                    "-d",
                    "5",  # fixed 5 sec after trigger
                    filepath,
                ]
            )
            print("✅ Recording saved\n")
        else:
            print("⚪ No sound, idle...\n")

except KeyboardInterrupt:
    print("❌ Interrupted, exiting...")
