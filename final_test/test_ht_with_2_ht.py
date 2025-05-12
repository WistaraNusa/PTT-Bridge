import sounddevice as sd
import numpy as np
import time
from gpiozero import LED
import queue

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

# === STATE ===
ptt_state = {
    "HT_A": {"active": False, "last_signal": 0, "trigger_time": None, "gpio_on_time": 0},
    "HT_B": {"active": False, "last_signal": 0, "trigger_time": None, "gpio_on_time": 0},
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

def handle_vox(config, gpio, state_key, output_key):
    def callback(indata, frames, time_info, status):
        now = time.time()

        # === Step 1: Measure true RMS (before gain)
        rms = np.sqrt(np.mean(indata**2))
        print(f"[{config['label']}] RMS: {rms:.5f}", end="\r", flush=True)

        # === Step 2: Apply gain for output
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
            try:
                audio_queues[output_key].put_nowait(scaled_input.copy() * config["volume_scale"])
            except queue.Full:
                pass

        elif ptt_state[state_key]["active"]:
            time_since_signal = now - ptt_state[state_key]["last_signal"]
            time_since_gpio_on = now - ptt_state[state_key]["gpio_on_time"]

            if time_since_signal > SILENCE_TIMEOUT and time_since_gpio_on > MIN_HOLD_TIME:
                print(f"\n[{config['label']}] 💤 Silence — GPIO {gpio.pin.number} OFF", flush=True)
                gpio.off()
                ptt_state[state_key]["active"] = False
                ptt_state[state_key]["trigger_time"] = None
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
    print("\n🎧 Starting VOX PTT Bridge with Per-HT Gain & Volume...\n")
    streams = []

    output_streams["HT_A"] = start_output_stream("HT_A", DEVICES["HT_A"]["index"])
    output_streams["HT_B"] = start_output_stream("HT_B", DEVICES["HT_B"]["index"])

    streams.append(handle_vox(
        DEVICES["HT_A"],
        ptt_gpio["HT_B"],  # HT_A talks → HT_B PTT on
        "HT_A",
        "HT_B"
    ))
    streams.append(handle_vox(
        DEVICES["HT_B"],
        ptt_gpio["HT_A"],  # HT_B talks → HT_A PTT on
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
