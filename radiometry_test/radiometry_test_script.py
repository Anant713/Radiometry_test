import paramiko
import serial
import time
import json
import os

# --- PLEASE FILL IN YOUR DETAILS HERE ---
# Raspberry Pi SSH Credentials
PI_IP = "10.42.0.135"
PI_USERNAME = "vbn"
PI_PASSWORD = "iitbssp123"

# Pico Serial Port Configuration
PICO_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600

# --- NEW AUTOMATION SETTINGS ---
# Note: All X values are in millimeters (mm)
# Note: All Y values are in microseconds (µs)
X_i = 0      # Initial distance in mm
DX =  26      # Step/increment for distance in mm
X_f = 780     # Final distance in mm

Y_i = 200  # Initial shutter speed in µs
# DY =     # Step/increment for shutter speed in µs
Y_f = 200  # Final shutter speed in µs

Nmax = 1     # Number of frames to capture at each setting (from 1 to Nmax)

# Pico Conversion & Position
PICO_INITIAL_POS_STEPS = 0 # The Pico's starting position in STEPS
STEPS_PER_MM = 5           # 5 steps = 1mm movement on the X-axis

# State file for resuming
STATE_FILE = "state.json"
# --- END OF CONFIGURATION ---

def save_state(X, Y, N):
    """Saves the current loop state (X, Y, N) to a file."""
    state = {'X': X, 'Y': Y, 'N': N}
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def load_state():
    """Loads the loop state from a file, if it exists."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            print(f"Found state file '{STATE_FILE}'. Resuming session.")
            state = json.load(f)
            # Ensure all keys are present
            return {
                'X': state.get('X', X_i),
                'Y': state.get('Y', Y_i),
                'N': state.get('N', 1)
            }
    print("No state file found. Starting a new session from initial values.")
    return {'X': X_i, 'Y': Y_i, 'N': 1}

def get_expected_position_steps(current_X_mm):
    """Calculates the expected position of the Pico in STEPS."""
    # The total distance moved from the start in mm
    dist_moved_mm = current_X_mm - X_i
    # Convert that distance to steps
    steps_moved = dist_moved_mm * STEPS_PER_MM
    return PICO_INITIAL_POS_STEPS + steps_moved

def main():
    """Main function to run the uniform automation loop."""
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pico_serial = None
    
    initial_state = load_state()
    start_X, start_Y, start_N = initial_state['X'], initial_state['Y'], initial_state['N']

    try:
        print("Connecting to Raspberry Pi...")
        ssh_client.connect(hostname=PI_IP, username=PI_USERNAME, password=PI_PASSWORD,look_for_keys=False,
    allow_agent=False)
        print("Ensuring destination directory exists on Pi...")
        ssh_client.exec_command("mkdir -p /home/vbn/vbn_data")

        print(f"Connecting to Pico on port {PICO_PORT}...")
        pico_serial = serial.Serial(PICO_PORT, BAUD_RATE, timeout=2)
        time.sleep(2)

        # --- UNIFORM MAIN LOOPS ---
        # Generate the range of X and Y values
        x_range = list(range(X_i, X_f + 1, DX))
        y_range = [200]

        for X in x_range:
            # Skip past X values that are already completed
            if X < start_X:
                continue

            print(f"\n{'='*15} Starting Position X = {X} mm {'='*15}")
            
            # --- STEP 1: VERIFY CURRENT POSITION ---
            expected_pos = get_expected_position_steps(X)
            print(f"Verifying position... Expected: {expected_pos} steps.")
            pico_serial.write(b"POS?\n")
            time.sleep(0.5)
            pos_response = ""
            for _ in range(5): # Read a few lines to find the POS response
                line = pico_serial.readline().decode('utf-8', errors='ignore').strip()
                print(line)
                if line.startswith("POS:"):
                    pos_response = line
                    break
            
            if not pos_response:
                raise Exception("Did not receive POS response from Pico.")
            try:
                reported_pos = int(pos_response.split(':')[1].split(',')[0])
                if reported_pos != expected_pos:
                    raise Exception(f"Position Mismatch! Expected {expected_pos}, got {reported_pos}")
                print("Position verified successfully.")
            except (ValueError, IndexError):
                raise Exception(f"Could not parse POS response: '{pos_response}'")

            # --- STEP 2: CAPTURE ALL IMAGES FOR THIS POSITION ---
            for Y in y_range:
                # Skip past Y values for the current X if resuming
                if X == start_X and Y < start_Y:
                    continue

                print(f"\n--- Shutter Y = {Y} µs ---")

                for N in range(1, Nmax + 1):
                    # Skip past N values for the current X and Y if resuming
                    if X == start_X and Y == start_Y and N < start_N:
                        continue
                    
                    print(f"--- Capturing frame N = {N}/{Nmax} ---")
                    
                    filename = f"range{X}_exp{Y}_{N}.dng"
                    filepath = f"/home/vbn/vbn_data/{filename}"
                    ssh_command = f"python3 capture_dng.py {Y} {filepath}"
                    
                    print(f"Executing on Pi: {ssh_command}")
                    
                    _, stdout, stderr = ssh_client.exec_command(ssh_command)
                    exit_status = stdout.channel.recv_exit_status()

                    if exit_status == 0:
                        print(f"Successfully executed command for {filename}.")
                        # Save state for the *next* iteration
                        next_X, next_Y, next_N = X, Y, N + 1
                        if next_N > Nmax:
                            next_N = 1
                            try:
                                next_Y = y_range[y_range.index(Y) + 1]
                            except IndexError:
                                next_Y = Y_i
                                try:
                                    next_X = x_range[x_range.index(X) + 1]
                                except IndexError:
                                    next_X = X_f + 1 # Mark as complete
                        save_state(next_X, next_Y, next_N)
                    else:
                        raise Exception(f"Pi command failed. Error: {stderr.read().decode()}")

                start_N = 1 # Reset start_N for the next Y loop
            start_Y = Y_i # Reset start_Y for the next X loop

            # --- STEP 3: MOVE TO THE NEXT POSITION ---
            # Don't move after the final position has been captured
            if X < X_f:
                move_steps = DX * STEPS_PER_MM
                pico_command = f"{move_steps},0,0\n"
                pico_serial.reset_input_buffer()
                pico_serial.write(pico_command.encode('utf-8'))
                print(f"\nSent move command for {DX} mm ({move_steps} steps) to prepare for next position.")
                
                # Best-effort wait for move to finish
                start_wait = time.time()
                while time.time() - start_wait < 25:
                    if "DONE" in pico_serial.readline().decode('utf-8', errors='ignore'):
                        print("Pico reported DONE.")
                        break

        print("\nAutomation completed successfully!")

    except Exception as e:
        print(f"\nAN ERROR OCCURRED: {e}")
    finally:
        if ssh_client: ssh_client.close()
        if pico_serial and pico_serial.is_open: pico_serial.close()
        print("Connections closed.")

if __name__ == "__main__":
    main()