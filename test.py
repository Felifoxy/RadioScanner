import numpy as np
from rtlsdr import RtlSdr
import time

def scan_improved():
    sdr = RtlSdr()
    
    # --- HARDWARE TUNING ---
    sdr.sample_rate = 2.4e6
    sdr.gain = 25.4 
    
    scan_frequencies = [381.25e6, 383.75e6]
    
    print(f"{'Time':<10} | {'Freq (MHz)':<10} | {'Peak (dB)':<10} | {'SNR (dB)':<8} | {'Status'}")
    print("-" * 65)

    try:
        while True:
            for freq in scan_frequencies:
                sdr.center_freq = freq
                time.sleep(0.05)
                
                samples = sdr.read_samples(128 * 1024)
                psd = 10 * np.log10(np.abs(np.fft.fft(samples))**2 / len(samples))
                
                max_pwr = np.max(psd)
                avg_noise = np.mean(psd)
                snr = max_pwr - avg_noise # Signal-to-Noise Ratio
                
                current_time = time.strftime("%H:%M:%S")
                
                # A "Ping" is usually at least 15-20dB above the average noise floor
                if snr > 20:
                    status = f"*** PING DETECTED ***"
                else:
                    status = "Idle"
                
                print(f"{current_time:<10} | {freq/1e6:<10.2f} | {max_pwr:<10.1f} | {snr:<8.1f} | {status}")
            
    except KeyboardInterrupt:
        print("\nScan stopped.")
    finally:
        sdr.close()

if __name__ == "__main__":
    scan_improved()