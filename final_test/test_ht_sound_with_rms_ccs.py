import sounddevice as sd
import numpy as np
import time

# === CONFIGURATION ===
INPUT_DEVICE_INDEX = 2   # USB sound card (HT receiver input)
OUTPUT_DEVICE_INDEX = 1  # USB sound card (speaker/headset/next HT output)

SAMPLE_RATE = 44100
BLOCKSIZE = 1024
INPUT_GAIN = 0.5         # << New: Scale input down by 50%
VOLUME_SCALE = 0.4       # Output volume (40% of input)
TALK_THRESHOLD = 0.05    # RMS threshold to detect real talking

# === STATE TRACKING ===
max_rms = 0

def audio_callback(indata, outdata, frames, time_info, status):
    global max_rms

    # === Step 1: Scale input audio down (reduce RMS) ===
    scaled_indata = indata * INPUT_GAIN

    # === Step 2: Forward scaled audio to output, with VOLUME_SCALE ===
    outdata[:] = scaled_indata * VOLUME_SCALE

    # === Step 3: Measure RMS based on scaled input ===
    rms = np.sqrt(np.mean(scaled_indata**2))

    # Update maximum RMS value
    if rms > max_rms:
        max_rms = rms

    # === Step 4: Print State ===
    if rms > TALK_THRESHOLD:
        print(f"[TALKING] RMS: {rms:.5f} | Max RMS: {max_rms:.5f}     ", end="\r", flush=True)
    else:
        print(f"[IDLE/SILENT] RMS: {rms:.5f} | Max RMS: {max_rms:.5f}     ", end="\r", flush=True)

# === MAIN PROGRAM ===
try:
    print("? Starting Audio Bridge with GAIN scaling + RMS monitor...\n")

    # Open input and output audio streams together
    with sd.Stream(device=(INPUT_DEVICE_INDEX, OUTPUT_DEVICE_INDEX),
                   samplerate=SAMPLE_RATE,
                   blocksize=BLOCKSIZE,
                   dtype='float32',
                   channels=1,
                   callback=audio_callback):

        while True:
            time.sleep(0.1)

except KeyboardInterrupt:
    print("\n\n? Exiting cleanly...")
    print(f"Final Max RMS: {max_rms:.5f}")
