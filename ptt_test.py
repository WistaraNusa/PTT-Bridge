from gpiozero import LED
from time import sleep

PTT_PIN = 17
ptt = LED(PTT_PIN)

print("🔴 PTT ON (TX Mode)")
ptt.on()

input("🎧 Press Enter to stop transmission...")

print("⚪ PTT OFF")
ptt.off()
