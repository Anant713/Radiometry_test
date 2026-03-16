from numpy import tan
import paramiko
import serial
import time

from sympy import atan2

# ---------------- CONFIGURATION ---------------- #

# Raspberry Pi SSH Credentials
PI_IP = "10.42.0.135"
PI_USERNAME = "vbn"
PI_PASSWORD = "iitbssp123"

# Pico Serial
PICO_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600

# Motion Settings (mm)
X_i = 0
DX = 10
X_f = 700

# Y_i = 0
# DY = 30
# Y_f = 300

STEPS_PER_MM = 5  # 5 steps = 1 mm

# CSV Location
CSV_SOURCE = "~/RPOD-Software/tools/data/tmp/vbn_monitor/pose_log.csv"

# ------------------------------------------------ #


def get_current_position(pico_serial):
    """Query Pico for absolute position using POS?"""
    pico_serial.reset_input_buffer()
    pico_serial.write(b"POS?\n")

    while True:
        line = pico_serial.readline().decode('utf-8', errors='ignore').strip()
        if line.startswith("POS:"):
            parts = line.split(":")[1].split(",")
            return int(parts[0]), int(parts[1])


def move_to_position(pico_serial, current_x, current_y, target_x, target_y):
    """Move to absolute target position using relative motion"""
    delta_x = target_x - current_x
    delta_y = target_y - current_y

    print(f"Relative move: {delta_x},{delta_y},0")

    command = f"{delta_x},{delta_y},0\n"
    print(command)
    pico_serial.write(command.encode('utf-8'))

    # Wait for DONE
    while True:
        line = pico_serial.readline().decode('utf-8', errors='ignore')
        if "DONE" in line:
            break

    # Verify absolute position
    abs_x, abs_y = get_current_position(pico_serial)

    if abs_x != target_x or abs_y != target_y:
        raise Exception(
            f"Position mismatch! Expected {target_x},{target_y} "
            f"but got {abs_x},{abs_y}"
        )

    print(f"Position verified: {abs_x},{abs_y}")
    return abs_x, abs_y


def main():
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    pico_serial = None

    try:
        # ---- SSH CONNECT ----
        print("Connecting to Raspberry Pi...")
        ssh_client.connect(
            hostname=PI_IP,
            username=PI_USERNAME,
            password=PI_PASSWORD,
            look_for_keys=False,
            allow_agent=False
        )

        # ---- SERIAL CONNECT ----
        print("Connecting to Pico...")
        pico_serial = serial.Serial(PICO_PORT, BAUD_RATE, timeout=2)
        time.sleep(2)

        # ---- RANGES ----
        #x_range_1 = list(range(0, 210, 15))
        #x_range_2 = list(range(225, 765, 45))
        x_range = list(range(X_i, X_f + 1, DX))
        Azimuth = [0,7,14,21]
        y_ranges = {}
        Az = {}
        for X in x_range:
            y_ranges[X] = [0]
            # Az[X] = []
            # for a in Azimuth:
            #     X_eff = X +33.03
            #     y = (X_eff) * tan(a * 3.14159 / 180)
            #     y = round(y)
            #     if y <= 290:
            #         y_ranges[X].append(y)
            #         Az[X].append(round(atan2(y, X_eff) * (180 / 3.14159), 2))
            #     else:
            #         y_ranges[X].append(290)
            #         Az[X].append(round(atan2(290, X_eff) * (180 / 3.14159), 2))
        # y_pos = list(range(Y_i, Y_f + 1, DY))
        # y_range = {}
        # for X in x_range:
        #     y_range[X] = []
        #     for Y in y_pos:
        #         if atan2(Y, X + 30) * (180 / 3.14159) <= 35:
        #             y_range[X].append(Y)
        #         else:
        #             y_range[X].append(Y)
        #             break
        print(y_ranges)
        print(Az)
        current_x_steps = 0
        current_y_steps = 0

        # Verify starting position
        current_x_steps, current_y_steps = get_current_position(pico_serial)
        print(f"Starting at absolute position: {current_x_steps},{current_y_steps}")
        
        # ---- MAIN GRID LOOP ----
        for X in x_range:
            for Y in y_ranges[X]:
                Azimuth = round(atan2(Y, X + 33.03) * (180 / 3.14159))
                print(f"\n=== Target X={X}mm Y={Y}mm ===")

                target_x_steps = X * STEPS_PER_MM
                target_y_steps = Y * STEPS_PER_MM

                # Move
                current_x_steps, current_y_steps = move_to_position(
                    pico_serial,
                    current_x_steps,
                    current_y_steps,
                    target_x_steps,
                    target_y_steps                                                      
                )
                time.sleep(3)
                # ---- RUN PIPELINE ----
                print("Running vbn_pipeline_test...")

                stdin, stdout, stderr = ssh_client.exec_command(
                    "cd ~/RPOD-Software/build && sudo ./vbn_pipeline_test"
                )
                # ADD THIS - read output in background or consume it
                # stdout_data = stdout.read()  # or use non-blocking reads
                # stderr_data = stderr.read()

                # Let it run for desired duration
                print("Waiting 120 seconds...")
                time.sleep(5)
                while True:
                    stdin, stdout_len, stderr = ssh_client.exec_command(
                        "wc -l < ~/RPOD-Software/tools/data/tmp/vbn_monitor/pose_log.csv"
                    )
                    readings = int(stdout_len.read().decode().strip())
                    print(readings)
                    print(type(readings))
                    if readings >=499 :
                        break
                    time.sleep(5)

                # ---- FIND PID ----
                stdin_pid, stdout_pid, stderr_pid = ssh_client.exec_command(
                    "pidof vbn_pipeline_test"
                )

                pid_output = stdout_pid.read().decode().strip()

                if pid_output:
                    print(f"Found PID(s): {pid_output}")

                    # There may be multiple PIDs
                    pids = pid_output.split()

                    for pid in pids:
                        print(f"Killing PID {pid}")
                        ssh_client.exec_command(f"sudo kill -9 {pid}")

                    print("Process killed successfully.")
                else:
                    print("No running vbn_pipeline_test process found.")

                # # Read any remaining output
                # print("stdout:", stdout_data)
                # print("stderr:", stderr_data)

                # ---- RENAME CSV ----
                destination = f"~/RPOD-Software/tools/data/tmp/vbn_monitor/{X}_{Y}_{Azimuth}_pose.csv"
                rename_command = f"mv {CSV_SOURCE} {destination}"

                stdin, stdout, stderr = ssh_client.exec_command(rename_command)
                exit_status = stdout.channel.recv_exit_status()
                print(exit_status)
                if exit_status == 0:
                    print(f"Saved CSV as {X}_{Y}_{Azimuth}_pose.csv")
                else:
                    raise Exception(stderr.read().decode())
                time.sleep(3)

        # ---- RETURN TO ORIGIN ----
        # print("\nReturning to origin (0,0)...")
        print("\nWon't return to origin (0,0)... warna crash ho jaunga :/")
        # current_x_steps, current_y_steps = move_to_position(
        #     pico_serial,
        #     current_x_steps,
        #     current_y_steps,
        #     0,
        #     0
        # )

        print("\nAutomation completed successfully!")

    except Exception as e:
        print(f"\nERROR: {e}")

    finally:
        if ssh_client:
            ssh_client.close()
        if pico_serial and pico_serial.is_open:
            pico_serial.close()
        print("Connections closed.")


if __name__ == "__main__":
    main()
