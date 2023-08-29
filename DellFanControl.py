import os
import sys
import subprocess
import time

# IPMI settings
IPMI_HOST = "192.168.1.105"
IPMI_USER = "root"
IPMI_PASS = "calvin"

# Temperature thresholds
MIN_TEMP = 30
MAX_TEMP = 75

# Fan speed percentages for the temperature thresholds
MIN_FAN_SPEED = 10
MAX_FAN_SPEED = 100

def get_temperatures():
    cmd = ["ipmitool", "-I", "lanplus", "-H", IPMI_HOST, "-U", IPMI_USER, "-P", IPMI_PASS, "sdr", "type", "temperature"]
    output = subprocess.check_output(cmd).decode('utf-8')
    temperatures = {}
    for line in output.split("\n"):
        if "degrees C" in line:
            parts = line.split("|")
            sensor_id = parts[1].strip()
            temp_value = float(parts[4].split()[0])
            temperatures[sensor_id] = temp_value
    return temperatures

def set_fan_speed(percentage):
    hex_value = "{:02x}".format(int(percentage * 2.55))
    print("Fan(B): 0x" + hex_value)
    cmd = ["ipmitool", "-I", "lanplus", "-H", IPMI_HOST, "-U", IPMI_USER, "-P", IPMI_PASS, "raw", "0x30", "0x30", "0x02", "0xff", "0x" + hex_value]

    subprocess.run(cmd)

def enable_fan_control():
    cmd = ["ipmitool", "-I", "lanplus", "-H", IPMI_HOST, "-U", IPMI_USER, "-P", IPMI_PASS, "raw", "0x30", "0x30", "0x01", "0x00"]
    subprocess.run(cmd)

def calculate_fan_speed(temp):
    if temp <= MIN_TEMP:
        return MIN_FAN_SPEED
    elif temp >= MAX_TEMP:
        return MAX_FAN_SPEED
    else:
        slope = (MAX_FAN_SPEED - MIN_FAN_SPEED) / (MAX_TEMP - MIN_TEMP)
        return MIN_FAN_SPEED + slope * (temp - MIN_TEMP)

def main():
    enable_fan_control()
    start_time = time.time()

    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time >= 86400:  # 24 hours in seconds
            os.execv(__file__, sys.argv)  # Restart the script

        temperatures = get_temperatures()
        cpu1_temp = temperatures.get("0Eh")
        cpu2_temp = temperatures.get("0Fh")

        # Check if temperatures are None and handle accordingly
        if cpu1_temp is None or cpu2_temp is None:
            print("Error: Unable to get temperatures for one or both CPUs.")
            time.sleep(60)
            continue
        else:
            print("CPU1(C):", cpu1_temp, "\tCPU2(C):", cpu2_temp, end='\t')

        max_temp = max(cpu1_temp, cpu2_temp)  # Get the maximum temperature of the two CPUs
        fan_speed = calculate_fan_speed(max_temp)

        print("Fan(%):", fan_speed, end='\t')

        set_fan_speed(fan_speed)
        time.sleep(3) # 120 second pause

if __name__ == "__main__":
    main()
