import numpy as np
from rtlsdr import RtlSdr
import time

# --- Configuration ---
start_freq = 380_000_000  # MHz range start
end_freq = 385_000_000    # MHz range end
sample_rate = 2.4e6       # Hz — max reliable for RTL-SDR
gain = 40                 # dB
signal_threshold = 5.0    # Adjust based on noise floor
fft_size = 2048           # FFT resolution (higher = finer detail, slower)
samples_per_read = 128 * 1024  # Samples per read (~50ms window)
sweep_dwell_time = 3.0    # Seconds to stay on each window before moving

# --- SDR Init ---
try:
    sdr = RtlSdr()
    sdr.sample_rate = sample_rate
    sdr.gain = gain
    sdr.read_samples(1024 * 8)  # warmup
except Exception as e:
    print(f"RTL-SDR not found: {e}")
    exit()

# --- Main Monitor ---
print(f"Starting wideband monitor from {start_freq/1e6:.1f} to {end_freq/1e6:.1f} MHz")

# Compute step to cover full range in chunks of sample_rate
center_frequencies = np.arange(start_freq + sample_rate/2, end_freq, sample_rate)

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

    except Exception as e:
        print(f"Error: {e}")
        sdr.close()
        break

sdr.close()
