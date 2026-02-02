import numpy as np
from rtlsdr import RtlSdr
import time

def scan_robust():
    sdr = RtlSdr()

    try:
        # Hardware setup
        sdr.sample_rate = 1.024e6  # Lower rate = less stress on Pi 4
        sdr.center_freq = 382.5e6
        sdr.gain = 0.0             # Keep gain at minimum for now
        
        # C2000 Uplink band segments
        scan_frequencies = [380.5e6, 381.5e6, 382.5e6, 383.5e6, 384.5e6]
        
        print(f"{'Time':<10} | {'Freq (MHz)':<10} | {'Peak (dB)':<10} | {'Status'}")
        print("-" * 55)

        while True:
            for freq in scan_frequencies:
                try:
                    sdr.center_freq = freq
                    # Short pause to let the R820T PLL lock
                    time.sleep(0.1) 
                    
                    samples = sdr.read_samples(128 * 1024)
                    
                    # Manual DC Offset removal (removes the spike in the middle)
                    samples = samples - np.mean(samples)
                    
                    # Calculate PSD
                    psd = 10 * np.log10(np.abs(np.fft.fft(samples))**2 / len(samples))
                    max_pwr = np.max(psd)
                    
                    current_time = time.strftime("%H:%M:%S")
                    
                    # Logic: With 0 gain, anything above -10dB is a real signal
                    if max_pwr > -10:
                        status = "!!! UPLINK PING !!!"
                    elif max_pwr > -20:
                        status = "Weak Signal"
                    else:
                        status = "Clear"
                    
                    print(f"{current_time:<10} | {freq/1e6:<10.2f} | {max_pwr:<10.1f} | {status}")
                
                except Exception as e:
                    print(f"Error tuning to {freq/1e6}MHz: {e}")
                    continue
                    
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        sdr.close()

if __name__ == "__main__":
    scan_robust()