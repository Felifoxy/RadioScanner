import numpy as np
from rtlsdr import RtlSdr
import time
import sys

def monitor_with_status():
    sdr = RtlSdr()
    sdr.sample_rate = 2.4e6
    sdr.gain = 15.0 
    
    # Coverage: 
    # Window A (380.0 - 382.4 MHz)
    # Window B (382.6 - 385.0 MHz)
    windows = [
        {'freq': 381.2e6, 'label': 'WINDOW A (Lower)'},
        {'freq': 383.8e6, 'label': 'WINDOW B (Upper)'}
    ]
    
    dwell_time = 0.8 # Slightly longer dwell to catch full TDMA sequences
    
    print(f"{'Time':<15} | {'Event':<5} | {'Frequency':<12} | {'Power'}")
    print("-" * 60)

    try:
        while True:
            for win in windows:
                sdr.center_freq = win['freq']
                time.sleep(0.04) # Settle time
                
                start_dwell = time.time()
                
                while (time.time() - start_dwell) < dwell_time:
                    # Update the live status line at the bottom
                    remaining = dwell_time - (time.time() - start_dwell)
                    sys.stdout.write(f"\r[SCANNING] {win['label']} | Next switch in: {remaining:.1f}s...   ")
                    sys.stdout.flush()

                    samples = sdr.read_samples(16384)
                    samples = samples - np.mean(samples)
                    
                    fft_data = np.abs(np.fft.fft(samples))**2 / len(samples)
                    psd = 10 * np.log10(fft_data + 1e-12)
                    
                    # Ignore DC spike
                    center_bin = len(psd) // 2
                    psd[center_bin-5:center_bin+5] = -100
                    
                    max_pwr = np.max(psd)
                    
                    if max_pwr > -12:
                        freq_axis = np.fft.fftfreq(len(samples), 1/sdr.sample_rate)
                        peak_idx = np.argmax(psd)
                        exact_freq = (win['freq'] + freq_axis[peak_idx]) / 1e6
                        
                        # Print hit (clears the status line temporarily)
                        sys.stdout.write("\r" + " " * 70 + "\r") 
                        print(f"{time.strftime('%H:%M:%S.%f')[:-3]:<15} | HIT   | {exact_freq:.4f} MHz | {max_pwr:.1f} dB")

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
    finally:
        sdr.close()

if __name__ == "__main__":
    monitor_with_status()