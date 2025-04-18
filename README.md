# Raspberry Pi VOX + PTT Transmit System for Radio

This project sets up a Raspberry Pi as a voice-activated (VOX) transmitter for a handheld transceiver (HT/WT), using a USB sound card for audio I/O and GPIO to control Push-To-Talk (PTT).

## 📦 Requirements

### Hardware

- Raspberry Pi (any model with GPIO and audio output)
- USB sound card (for microphone and speaker interface)
- HT/WT radio with PTT interface (e.g. Baofeng UV-5R)
- 2N2222 transistor (for GPIO PTT control)
- Resistors, jumper wires, breadboard or PCB
- Optional: Speaker connected to GPIO 18 via PWM (low quality)

### Wiring

- **PTT**: GPIO 17 → Resistor → Base of 2N2222 → Emitter to GND → Collector to PTT line of radio (with pull-up or direct pull-to-ground)
- **Audio Output**: GPIO 18 (PWM audio, not recommended for HQ)
- **Audio Input/Output**: USB sound card (recommended)

## 🧰 Software

Install the following packages:

```bash
sudo apt update
sudo apt install sox alsa-utils python3-gpiozero python3-pyaudio
```

> ⚠️ If using SoX with MP3 or other formats, you may need `libsox-fmt-all`.

## 🎤 Audio Devices

Check your sound devices:

```bash
arecord -l
aplay -l
```

Find the card/device number for your USB sound card (e.g., `plughw:1,0`).

## ▶️ Record and Play (Test)

Test recording:

```bash
arecord -D plughw:1,0 -f cd test.wav
```

Test playback:

```bash
aplay -D plughw:1,0 test.wav
```

## 🚀 Running the App

Your main script should:

- Listen for voice using SoX VOX (`rec`)
- Record to a `.wav` file when voice is detected
- Trigger GPIO 17 high (PTT ON)
- Play audio using `aplay`
- Set GPIO 17 low (PTT OFF)
- Delete the `.wav` file
- Loop back to listening

Example code snippet for playback with GPIO:

```python
from gpiozero import LED
from time import sleep
import subprocess

ptt = LED(17)  # GPIO 17 for PTT

def transmit(filename):
    ptt.on()
    subprocess.run(["aplay", filename])
    sleep(0.2)  # small buffer to ensure complete TX
    ptt.off()
```

VOX recording example (SoX):

```bash
rec -q -r 16000 -c 1 recorded.wav silence 1 0.1 2% 1 1.0 2%
```

## 🧠 Notes

- Adjust `silence` thresholds in SoX based on your mic sensitivity.
- If audio is poor, use USB sound card instead of PWM audio on GPIO 18.
- Use proper timing (e.g., `sleep(0.2)`) to ensure clean TX before switching back to RX.
- Consider logging or adding LED indicators for TX/RX mode.

## 🛠️ TODO

- Add RX audio bridging (optional full-duplex)
- Improve VOX trigger reliability
- Add configuration file for device settings

---

Happy Hacking & 73! 📻


## Activate the environment:
```
pyenv activate ptt-bridge
```