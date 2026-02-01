import numpy as np
from rtlsdr import RtlSdr
import time

def detect_tetra_uplink():
    # Initialize SDR
    sdr = RtlSdr()

    # Configuration
    sdr.sample_rate = 2.4e6  # 2.4 MHz bandwidth
    sdr.gain = 'auto'
    
    # We split 380-385 into two sweeps (381.25 and 383.75) 
    # to cover the full range with some overlap
    scan_frequencies = [381.25e6, 383.75e6]
    threshold = -35  # Adjust based on your noise floor (dB)

    print(f"Starting TETRA Uplink Scan (380-385 MHz)...")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            for freq in scan_frequencies:
                sdr.center_freq = freq
                time.sleep(0.1)  # Allow PLL to settle
                
                # Read samples
                samples = sdr.read_samples(256 * 1024)
                
                # Perform FFT to get Power Spectral Density
                power, freqs = np.histogram(np.angle(samples), bins=100) # Simple energy detection
                # More accurate PSD calculation
                psd = 10 * np.log10(np.abs(np.fft.fft(samples))**2 / len(samples))
                freq_axis = np.fft.fftfreq(len(samples), 1/sdr.sample_rate) + freq

                # Find peaks above threshold
                max_pwr = np.max(psd)
                if max_pwr > threshold:
                    peak_freq = freq_axis[np.argmax(psd)]
                    print(f"[!] Potential TETRA Ping: {peak_freq/1e6:.4f} MHz | Power: {max_pwr:.2f} dB")
            
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("\nStopping Scan...")
    finally:
        sdr.close()

if __name__ == "__main__":
    detect_tetra_uplink()