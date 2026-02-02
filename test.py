import numpy as np
from rtlsdr import RtlSdr
import time

def scan_attenuated():
    sdr = RtlSdr()
    
    # 1. Zero Gain - Let the antenna do the work, no internal amplification
    sdr.gain = 0.0 
    sdr.sample_rate = 1.024e6 # Lower rate is more stable on Pi 4
    
    # 2. Offset Tuning - Helps the SDR chip handle very strong signals
    sdr.set_offset_tuning(True)
    
    # We will scan in smaller steps to find the actual peak frequency
    scan_frequencies = [380.5e6, 381.5e6, 382.5e6, 383.5e6, 384.5e6]
    
    print(f"{'Time':<10} | {'Freq (MHz)':<10} | {'Peak (dB)':<10} | {'Status'}")
    print("-" * 50)

    try:
        while True:
            for freq in scan_frequencies:
                sdr.center_freq = freq
                time.sleep(0.05) # Give the tuner time to settle
                
                samples = sdr.read_samples(128 * 1024)
                # Apply a window function to clean up the signal shape
                window = np.blackman(len(samples))
                psd = 10 * np.log10(np.abs(np.fft.fft(samples * window))**2 / len(samples))
                
                max_pwr = np.max(psd)
                
                current_time = time.strftime("%H:%M:%S")
                
                # With gain 0, a real signal should stay below -10dB. 
                # Anything above 0dB is still "Screaming" at the SDR.
                if max_pwr > 0:
                    status = "OVERLOAD - Signal too strong!"
                elif max_pwr > -15:
                    status = "!!! POSSIBLE PING !!!"
                else:
                    status = "Clear"
                
                print(f"{current_time:<10} | {freq/1e6:<10.2f} | {max_pwr:<10.1f} | {status}")
            
    except KeyboardInterrupt:
        sdr.close()

if __name__ == "__main__":
    scan_attenuated()