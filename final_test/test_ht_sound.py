import sounddevice as sd
import numpy as np
import time

# === CONFIG ===
INPUT_DEVICE_INDEX = 2   # Listening device
OUTPUT_DEVICE_INDEX = 1  # Talking device

SAMPLE_RATE = 44100
BLOCKSIZE = 1024
TARGET_VOLUME = 0.4  # 40% intended output

def audio_callback(indata, outdata, frames, time_info, status):
    # Calculate RMS of input
    rms = np.sqrt(np.mean(indata**2))

    # Optional: print RMS value for debug
    print(f"Input RMS: {rms:.5f}", end="\r")

    # Normalize if needed
    if rms > 0:
        scaled_audio = indata * TARGET_VOLUME
    else:
        scaled_audio = indata  # If completely silent, just pass it

    outdata[:] = scaled_audio

# === MAIN ===
try:
    print("? Starting Audio Bridge with RMS Monitoring (scaled to 40%)...\n")

    with sd.Stream(device=(INPUT_DEVICE_INDEX, OUTPUT_DEVICE_INDEX),
                   samplerate=SAMPLE_RATE,
                   blocksize=BLOCKSIZE,
                   dtype='float32',
                   channels=1,
                   callback=audio_callback):

        while True:
            time.sleep(0.2)

except KeyboardInterrupt:
    print("\n? Exiting cleanly...")
