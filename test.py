import numpy as np
from rtlsdr import RtlSdr
import time

def scan_tetra_final():
    sdr = RtlSdr()
    sdr.sample_rate = 2.048e6
    sdr.gain = 15.0 
    
    # TETRA Uplink 380-385 MHz
    scan_freqs = [381.0e6, 383.0e6, 384.0e6]
    
    print("--- C2000 UPLINK MONITOR ACTIVE ---")
    print("Filtering DC Spike and calculating peaks...")
    print("-" * 60)

    try:
        while True:
            for freq in scan_freqs:
                sdr.center_freq = freq
                time.sleep(0.02)
                
                samples = sdr.read_samples(32 * 1024)
                samples = samples - np.mean(samples) # Remove average DC
                
                # Calculate PSD with a tiny offset to prevent log(0)
                fft_data = np.abs(np.fft.fft(samples))**2 / len(samples)
                psd = 10 * np.log10(fft_data + 1e-12) 
                
                # IGNORE THE CENTER (DC SPIKE)
                # We mask the middle 10 bins of the FFT
                center_idx = len(psd) // 2
                psd[center_idx-5 : center_idx+5] = -100 
                
                max_pwr = np.max(psd)
                
                if max_pwr > -12:
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