import os
import sys
import subprocess
import time

# IPMI settings
IPMI_HOST = "192.168.1.105"
IPMI_USER = "root"
IPMI_PASS = "calvin"

# Temperature thresholds
MIN_TEMP = 25
MAX_TEMP = 85

# Fan speed percentages for the temperature thresholds
MIN_FAN_SPEED = 10
MAX_FAN_SPEED = 100

def get_temperature(sensor_id):
    cmd = ["ipmitool", "-I", "lanplus", "-H", IPMI_HOST, "-U", IPMI_USER, "-P", IPMI_PASS, "sdr", "get", sensor_id]
    output = subprocess.check_output(cmd).decode('utf-8')
    for line in output.split("\n"):
        if "degrees C" in line:
            return float(line.split("|")[3].strip().split()[0])
    return None

def set_fan_speed(percentage):
    hex_value = hex(int(percentage * 2.55))[2:]
    cmd = ["ipmitool", "-I", "lanplus", "-H", IPMI_HOST, "-U", IPMI_USER, "-P", IPMI_PASS, "raw", "0x30", "0x30", "0x02", "0xff", hex_value]
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

        cpu1_temp = get_temperature("0Eh")
        cpu2_temp = get_temperature("0Fh")
        max_temp = max(cpu1_temp, cpu2_temp)  # Get the maximum temperature of the two CPUs
        fan_speed = calculate_fan_speed(max_temp)

        set_fan_speed(fan_speed)
        time.sleep(120) # 120 second pause

if __name__ == "__main__":
    main()
