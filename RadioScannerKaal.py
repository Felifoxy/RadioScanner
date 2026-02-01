import numpy as np
from rtlsdr import RtlSdr
import time

# --- Configuration ---
start_freq = 380_000_000 
end_freq = 385_000_000   
sample_rate = 2.4e6      
gain = 17                
fft_size = 2048          
samples_per_read = 128 * 1024  
sweep_dwell_time = 3.0   
fixed_threshold = -20.0                 # A higher number is less sensitive; a lower number is more sensitive.

# --- SDR Init ---
try:
    sdr = RtlSdr()
    sdr.sample_rate = sample_rate
    sdr.gain = gain
    sdr.read_samples(1024 * 8)  # warmup
except Exception as e:
    print(f"RTL-SDR not found: {e}")
    exit()

print(f"Starting wideband monitor with FIXED THRESHOLD: {fixed_threshold} dB")

center_frequencies = np.arange(start_freq + sample_rate/2, end_freq, sample_rate)

while True:
    try:
        for center_freq in center_frequencies:
            sdr.center_freq = center_freq
            start_time = time.time()
            
            while time.time() - start_time < sweep_dwell_time:
                samples = sdr.read_samples(samples_per_read)
                
                # Convert to Power Spectrum
                spectrum = np.fft.fftshift(np.fft.fft(samples, fft_size))
                power_spectrum = 20 * np.log10(np.abs(spectrum))

                # Simple Fixed Comparison
                peak_power = np.max(power_spectrum)
                
                if peak_power > fixed_threshold:
                    idx = np.argmax(power_spectrum)
                    freqs = np.linspace(center_freq - sample_rate/2,
                                        center_freq + sample_rate/2,
                                        fft_size)
                    peak_freq = freqs[idx]

                    print(f"Ping: {peak_freq/1e6:.3f} MHz | {peak_power:.1f} dB")

    except KeyboardInterrupt:
        print("\nStopping scanner...")
        break
    except Exception as e:
        print(f"Error: {e}")
        break

sdr.close()