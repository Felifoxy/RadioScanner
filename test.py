import numpy as np
from rtlsdr import RtlSdr
import time

def scan_surgical():
    sdr = RtlSdr()
    
    # --- AGGRESSIVE REDUCTION ---
    sdr.sample_rate = 2.048e6 
    sdr.gain = 12.5  # Very low gain to stop the clipping at -7dB
    
    scan_frequencies = [381.25e6, 383.75e6]
    
    print(f"{'Time':<10} | {'Freq (MHz)':<10} | {'Peak (dB)':<10} | {'Status'}")
    print("-" * 50)

    last_peak = -100

    try:
        while True:
            for freq in scan_frequencies:
                sdr.center_freq = freq
                time.sleep(0.02)
                
                samples = sdr.read_samples(64 * 1024)
                psd = 10 * np.log10(np.abs(np.fft.fft(samples))**2 / len(samples))
                
                max_pwr = np.max(psd)
                # A 'ping' should be a sudden spike compared to the last read
                delta = max_pwr - last_peak
                
                current_time = time.strftime("%H:%M:%S")
                
                # Check: Is it loud AND did it just appear?
                if max_pwr > -25 and delta > 10:
                    status = "!!! BURST DETECTED !!!"
                elif max_pwr > -20:
                    status = "Constant High Signal (Noise?)"
                else:
                    status = "Quiet"
                
                print(f"{current_time:<10} | {freq/1e6:<10.2f} | {max_pwr:<10.1f} | {status}")
                last_peak = max_pwr
            
    except KeyboardInterrupt:
        print("\nScan stopped.")
    finally:
        sdr.close()

if __name__ == "__main__":
    scan_surgical()