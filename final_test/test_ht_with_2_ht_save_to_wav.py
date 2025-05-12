import sounddevice as sd
import soundfile as sf
import numpy as np
import time
from gpiozero import LED
import queue
import threading
import os

# === CONFIG ===
DEVICES = {
    "HT_A": {
        "index": 1,
        "gpio": 17,
        "label": "HT A → HT B",
        "threshold": 0.02,
        "input_gain": 0.8,
        "volume_scale": 0.5
    },
    "HT_B": {
        "index": 2,
        "gpio": 27,
        "label": "HT B → HT A",
        "threshold": 0.03,
        "input_gain": 0.5,
        "volume_scale": 0.4
    },
}

SAMPLE_RATE = 44100
BLOCKSIZE = 1024
SILENCE_TIMEOUT = 1.0
ACTIVATION_DELAY = 0.5
MIN_HOLD_TIME = 1.0
MAX_RECORD_SECONDS = 30  # maximum duration per recording
SAVE_PATH = "recordings"

os.makedirs(SAVE_PATH, exist_ok=True)

ptt_state = {
    "HT_A": {"active": False, "last_signal": 0, "trigger_time": None, "gpio_on_time": 0, "recording": False, "record_start_time": 0, "record_buffer": []},
    "HT_B": {"active": False, "last_signal": 0, "trigger_time": None, "gpio_on_time": 0, "recording": False, "record_start_time": 0, "record_buffer": []},
}

ptt_gpio = {
    "HT_A": LED(DEVICES["HT_A"]["gpio"]),
    "HT_B": LED(DEVICES["HT_B"]["gpio"]),
}

audio_queues = {
    "HT_A": queue.Queue(maxsize=5),
    "HT_B": queue.Queue(maxsize=5),
}

output_streams = {}

# === RECORD SAVING ===
def save_recording(ht_key):
    frames = ptt_state[ht_key]["record_buffer"]
    if frames:
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime(ptt_state[ht_key]["record_start_time"]))
        filename = os.path.join(SAVE_PATH, f"record_{ht_key}_{timestamp}.wav")
        with sf.SoundFile(filename, mode='w', samplerate=SAMPLE_RATE, channels=1, subtype='PCM_16') as f:
            for frame in frames:
                f.write(frame)
        print(f"\n[REC] Saved {filename}")
    ptt_state[ht_key]["record_buffer"] = []

# === OUTPUT AUDIO ===
def start_output_stream(key, device_index):
    def callback(outdata, frames, time_info, status):
        try:
            data = audio_queues[key].get_nowait()
        except queue.Empty:
            data = np.zeros((frames, 1), dtype=np.float32)
        outdata[:] = data
    stream = sd.OutputStream(
        device=device_index,
        channels=1,
        samplerate=SAMPLE_RATE,
        blocksize=BLOCKSIZE,
        dtype='float32',
        callback=callback
    )
    stream.start()
    return stream

# === VOX HANDLER ===
def handle_vox(config, gpio, state_key, output_key):
    def callback(indata, frames, time_info, status):
        now = time.time()
        rms = np.sqrt(np.mean(indata**2))
        print(f"[{config['label']}] RMS: {rms:.5f}", end="\r", flush=True)

        scaled_input = indata * config["input_gain"]

        if rms > config["threshold"]:
            if ptt_state[state_key]["trigger_time"] is None:
                ptt_state[state_key]["trigger_time"] = now
            elif now - ptt_state[state_key]["trigger_time"] >= ACTIVATION_DELAY:
                ptt_state[state_key]["last_signal"] = now
                if not ptt_state[state_key]["active"]:
                    print(f"\n[{config['label']}] 🎤 Signal Confirmed — GPIO {gpio.pin.number} ON", flush=True)
                    gpio.on()
                    ptt_state[state_key]["active"] = True
                    ptt_state[state_key]["gpio_on_time"] = now
                    ptt_state[state_key]["recording"] = True
                    ptt_state[state_key]["record_start_time"] = now
            try:
                audio_queues[output_key].put_nowait(scaled_input.copy() * config["volume_scale"])
            except queue.Full:
                pass

            if ptt_state[state_key]["recording"]:
                ptt_state[state_key]["record_buffer"].append(indata.copy())

        elif ptt_state[state_key]["active"]:
            time_since_signal = now - ptt_state[state_key]["last_signal"]
            time_since_gpio_on = now - ptt_state[state_key]["gpio_on_time"]

            if time_since_signal > SILENCE_TIMEOUT and time_since_gpio_on > MIN_HOLD_TIME:
                print(f"\n[{config['label']}] 💭 Silence — GPIO {gpio.pin.number} OFF", flush=True)
                gpio.off()
                ptt_state[state_key]["active"] = False
                ptt_state[state_key]["trigger_time"] = None
                ptt_state[state_key]["gpio_on_time"] = 0
                if ptt_state[state_key]["recording"]:
                    ptt_state[state_key]["recording"] = False
                    save_recording(state_key)
                # Reset for next transmission
                ptt_state[state_key]["record_buffer"] = []
                ptt_state[state_key]["record_start_time"] = 0
                print(f"[{config['label']}] Ready for next VOX trigger.")
        else:
            ptt_state[state_key]["trigger_time"] = None
            try:
                audio_queues[output_key].put_nowait(np.zeros((frames, 1), dtype=np.float32))
            except queue.Full:
                pass

    stream = sd.InputStream(
        device=config["index"],
        channels=1,
        samplerate=SAMPLE_RATE,
        blocksize=BLOCKSIZE,
        dtype='float32',
        callback=callback
    )
    stream.start()
    return stream

# === MAIN ===
try:
    print("\n🎧 Starting VOX PTT Bridge + WAV Recording...\n")
    streams = []

    output_streams["HT_A"] = start_output_stream("HT_A", DEVICES["HT_A"]["index"])
    output_streams["HT_B"] = start_output_stream("HT_B", DEVICES["HT_B"]["index"])

    streams.append(handle_vox(
        DEVICES["HT_A"],
        ptt_gpio["HT_B"],
        "HT_A",
        "HT_B"
    ))
    streams.append(handle_vox(
        DEVICES["HT_B"],
        ptt_gpio["HT_A"],
        "HT_B",
        "HT_A"
    ))

    while True:
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n🛑 Exiting cleanly...")
    for gpio in ptt_gpio.values():
        gpio.off()
    for stream in streams + list(output_streams.values()):
        stream.stop()
        stream.close()
    print("✅ All GPIOs released. Streams closed.")
