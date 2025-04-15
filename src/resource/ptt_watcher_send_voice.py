from gpiozero import LED
import subprocess
import time
import threading

# --- CONFIG ---
PTT_PIN = 17
WAV_FILE = "./test.wav"
DEVICE_OUT = "plughw:3,0"
PAUSE_BETWEEN = 2  # seconds between loops

ptt = LED(PTT_PIN)
stop_loop = False


def wait_for_enter():
    global stop_loop
    input("🔘 Press Enter to stop transmission...\n")
    stop_loop = True


print(f"🔁 Looping audio: {WAV_FILE}")
threading.Thread(target=wait_for_enter, daemon=True).start()

try:
    while not stop_loop:
        ptt.on()
        time.sleep(0.3)  # Give HT time to enter TX

        subprocess.run(
            [
                "aplay",
                "-D",
                DEVICE_OUT,
                "-r",
                "8000",
                "-f",
                "S16_LE",
                "-c",
                "1",
                WAV_FILE,
            ]
        )

        ptt.off()
        print("✅ One round complete. Waiting...\n")
        time.sleep(PAUSE_BETWEEN)

except Exception as e:
    print(f"⚠️ Error: {e}")

finally:
    ptt.off()
    print("🛑 Transmission ended.")
