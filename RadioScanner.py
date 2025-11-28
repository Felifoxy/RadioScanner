import numpy as np
from rtlsdr import RtlSdr
import time
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from gpiozero import LED
from threading import Thread

# --- Configuration ---
start_freq = 380_000_000  # MHz range start
end_freq = 385_000_000    # MHz range end
sample_rate = 2.4e6       # Hz — max reliable for RTL-SDR
gain = 40                 # dB
signal_threshold = 5.0    # Adjust based on noise floor
fft_size = 2048           # FFT resolution (higher = finer detail, slower)
samples_per_read = 128 * 1024  # Samples per read (~50ms window)
sweep_dwell_time = 3.0    # Seconds to stay on each window before moving

# --- LED Setup ---
led = LED(17)
is_blinking = False

# --- I2C / OLED Setup ---
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
oled.fill(0)
oled.show()

image = Image.new("1", (oled.width, oled.height))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()

oled_last_update_time = time.time()
oled_update_interval = 0.5  # seconds

# --- Bar Layout ---
bar_width = 10
bar_spacing = 4
base_y = 63
bar_heights = [12, 20, 28, 38, 50]
bar_thresholds = [0, 8, 15, 25, 45]
bar_x_positions = [10 + i * (bar_width + bar_spacing) for i in range(5)]

# --- Helper: Blink LED ---
def blink_led(duration=5, interval=0.3):
    global is_blinking
    if is_blinking:
        return
    is_blinking = True
    end_time = time.time() + duration
    while time.time() < end_time:
        led.toggle()
        time.sleep(interval)
    led.off()
    is_blinking = False

# --- Helper: OLED signal bars ---
def update_signal_bars(signal_strength, frequency):
    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    # Bars
    for i in range(5):
        x = bar_x_positions[i]
        y_top = base_y - bar_heights[i] + 1
        fill_bar = signal_strength > bar_thresholds[i]
        draw.rectangle((x, y_top, x + bar_width, base_y), outline=255, fill=255 if fill_bar else 0)
    # Text
    draw.text((0, 0), f"Signal: {signal_strength:.1f} dB", fill=255)
    draw.text((100, 44), f"Freq:", fill=255)
    draw.text((100, 54), f"{frequency/1e6:.3f} MHz", fill=255)
    oled.image(image)
    oled.show()

# --- Error Display ---
def send_error_notification_to_display(code, desc):
    draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=255)
    draw.text((0, 0), f"ERROR: {code}", font=font, fill=0)
    draw.text((0, 16), desc[:18], font=font, fill=0)
    oled.image(image)
    oled.show()

# --- SDR Init ---
try:
    sdr = RtlSdr()
    sdr.sample_rate = sample_rate
    sdr.gain = gain
    sdr.read_samples(1024 * 8)  # warmup
except Exception as e:
    print(f"RTL-SDR not found: {e}")
    send_error_notification_to_display("SDR", "Device not found")
    exit()

# --- Main Monitor ---
print(f"Starting wideband monitor from {start_freq/1e6:.1f} to {end_freq/1e6:.1f} MHz")

# Compute step to cover full range in chunks of sample_rate
center_frequencies = np.arange(start_freq + sample_rate/2, end_freq, sample_rate)

Thread(target=blink_led, args=(3, 0.5), daemon=True).start()

while True:
    try:
        for center_freq in center_frequencies:
            sdr.center_freq = center_freq
            start_time = time.time()
            print(f"\nMonitoring window {center_freq/1e6:.3f} MHz ±{sample_rate/2/1e6:.1f} MHz")

            while time.time() - start_time < sweep_dwell_time:
                samples = sdr.read_samples(samples_per_read)
                spectrum = np.fft.fftshift(np.fft.fft(samples, fft_size))
                power_spectrum = 20 * np.log10(np.abs(spectrum))

                # Noise floor / dynamic threshold
                noise_floor = np.median(power_spectrum)
                threshold = noise_floor + signal_threshold

                # Peak detection
                peak_power = np.max(power_spectrum)
                if peak_power > threshold:
                    idx = np.argmax(power_spectrum)
                    freqs = np.linspace(center_freq - sample_rate/2,
                                        center_freq + sample_rate/2,
                                        fft_size)
                    peak_freq = freqs[idx]

                    print(f"Ping: {peak_freq/1e6:.3f} MHz | {peak_power:.1f} dB")
                    update_signal_bars(peak_power - noise_floor, peak_freq)

                    # Blink LED when strong
                    #if peak_power - noise_floor > 20:
                    #    Thread(target=blink_led, args=(2, 0.2), daemon=True).start()
                        
                    if peak_power > bar_thresholds[4]:
                        Thread(target=blink_led, args=(10, 0.2), daemon=True).start()

                # Periodic OLED refresh even with no signal
                if time.time() - oled_last_update_time > oled_update_interval:
                    #update_signal_bars(peak_power - noise_floor, center_freq)
                    update_signal_bars(peak_power, center_freq)
                    oled_last_update_time = time.time()

    except Exception as e:
        print(f"Error: {e}")
        send_error_notification_to_display("ERR", str(e))
        sdr.close()
        break

sdr.close()
