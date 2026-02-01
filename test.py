import numpy as np
from rtlsdr import RtlSdr
import time

def scan_with_noise_floor():
    sdr = RtlSdr()
    
    # Configuration
    sdr.sample_rate = 2.4e6
    sdr.gain = 15
    
    # We'll monitor the TETRA uplink band in two steps
    scan_frequencies = [381.25e6, 383.75e6]
    threshold = -35  # Trigger level for a "Ping"

    print(f"{'Time':<10} | {'Freq (MHz)':<12} | {'Peak (dB)':<10} | {'Status'}")
    print("-" * 55)

    try:
        while True:
            for freq in scan_frequencies:
                sdr.center_freq = freq
                time.sleep(0.05)
                
                samples = sdr.read_samples(128 * 1024)
                
                # PSD Calculation
                psd = 10 * np.log10(np.abs(np.fft.fft(samples))**2 / len(samples))
                max_pwr = np.max(psd)
                avg_noise = np.mean(psd)
                
                current_time = time.strftime("%H:%M:%S")
                
                if max_pwr > threshold:
                    status = f"*** PING DETECTED ***"
                else:
                    status = f"Noise (Floor: {avg_noise:.1f} dB)"
                
                print(f"{current_time:<10} | {freq/1e6:<12.2f} | {max_pwr:<10.1f} | {status}")
            
    except KeyboardInterrupt:
        print("\nScan stopped by user.")
    finally:
        sdr.close()

if __name__ == "__main__":
    scan_with_noise_floor()