import subprocess
from datetime import datetime
import os
import time
from gpiozero import LED

# --- CONFIG ---
DEVICE_IN = "plughw:2,0"
DEVICE_OUT = "plughw:3,0" 
PTT_PIN = 17  # GPIO pin number (BCM)
SAVE_PATH = "./wav"
SILENCE_THRESHOLD = "1%"  # Lower = more sensitive
MAX_SILENCE = "2.0"       # Stop after this much silence

# Setup
os.makedirs(SAVE_PATH, exist_ok=True)
ptt = LED(PTT_PIN)
ptt.off()

is_transmitting = False  # Prevent RX during TX

print("🎤 Smart VOX + Auto-TX ready!")

try:
    while True:
        if is_transmitting:
            time.sleep(0.1)
            continue

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
            print(f"🎤 Detected voice — saved: {filename}")

            is_transmitting = True
            print("📡 Transmitting...")
            ptt.on()
            time.sleep(0.3)  # Let HT go TX

            subprocess.run([
                "aplay", "-D", DEVICE_OUT,
                "-r", "8000", "-f", "S16_LE", "-c", "1",
                "./test.wav"
            ])

            ptt.off()
            is_transmitting = False
            print("✅ TX done.")

            # Comment out this block if you want to keep the file
            # try:
            #     os.remove(filepath)
            #     print(f"🧹 Deleted: {filename}\n")
            # except Exception as e:
            #     print(f"⚠️ Error deleting file: {e}")
        else:
            print("⚪ No voice activity detected.\n")
            if os.path.exists(filepath):
                os.remove(filepath)

        time.sleep(0.5)  # Small delay

except KeyboardInterrupt:
    print("❌ Interrupted, exiting...")

finally:
    ptt.off()
