import time
import sys
from picamera2 import Picamera2

# --- Check for correct arguments before initializing the camera ---
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 picam2_dng.py <shutter_speed_us> <output_path/name.dng>")
        print("Example: python3 picam2_dng.py 5000 /home/pi/images/capture.dng")
        sys.exit(1)

    # --- Assign arguments to variables ---
    try:
        shutter_speed = int(sys.argv[1])
    except ValueError:
        print("Error: Shutter speed must be an integer.")
        sys.exit(1)
        
    output_file = sys.argv[2]

# --- Initialize and configure the camera ---
picam2 = Picamera2()

# Define the raw stream configuration for OV9281
raw_config = {
    'size': (1280, 800),
    'format': 'R8'      # Could also use 'R8' if needed
}

config = picam2.create_still_configuration(raw=raw_config)
picam2.configure(config)

# --- Start camera ---
picam2.start()
time.sleep(1)  # Let it warm up

# --- Disable auto-exposure and set shutter from argument ---
picam2.set_controls({
    "ExposureTime": shutter_speed,  # Use the provided shutter speed
    "AnalogueGain": 1.0,            # No gain
    "AeEnable": False               # Disable auto-exposure
})

time.sleep(0.5)  # Give it time to apply settings

# --- Capture the raw image ---
if __name__ == "__main__":
    print(f"Capturing image with shutter speed {shutter_speed}µs to {output_file}")
    picam2.capture_file(output_file, 'raw')
    print("Done.")