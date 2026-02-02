import numpy as np
from rtlsdr import RtlSdr
import time

def scan_tetra_final():
    sdr = RtlSdr()
    sdr.sample_rate = 2.048e6
    sdr.gain = 15.0 # Increased slightly now that noise is gone
    
    # TETRA Uplink 380-385 MHz
    # We use 4 centers to cover the band with 2MHz chunks
    scan_freqs = [381.0e6, 383.0e6, 384.0e6]
    
    print("SCANNING FOR C2000 UPLINK...")
    print("Baseline looks good (~ -23dB). Waiting for burst...")
    print("-" * 60)

    try:
        while True:
            for freq in scan_freqs:
                sdr.center_freq = freq
                # Small sleep for Pi stability
                time.sleep(0.02)
                
                # Capture fewer samples so we can loop FASTER
                samples = sdr.read_samples(32 * 1024)
                
                # Remove the center DC spike (essential for RTL-SDR)
                samples = samples - np.mean(samples)
                
                psd = 10 * np.log10(np.abs(np.fft.fft(samples))**2 / len(samples))
                max_pwr = np.max(psd)
                
                # Trigger: If signal is 10dB louder than your quiet baseline (-23)
                if max_pwr > -12:
                    # Find exactly which frequency in the 2MHz window is active
                    freq_axis = np.fft.fftfreq(len(samples), 1/sdr.sample_rate)
                    peak_idx = np.argmax(psd)
                    exact_freq = (freq + freq_axis[peak_idx]) / 1e6
                    
                    print(f"{time.strftime('%H:%M:%S')} | DETECTED | {exact_freq:.4f} MHz | Pwr: {max_pwr:.1f} dB")
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        sdr.close()

if __name__ == "__main__":
    scan_tetra_final()