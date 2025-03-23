import machine
import time
from machine import I2C, Pin

# BMI088 Accelerometer I2C address
BMI088_ACCEL_ADDR = 0x19

# Setup I2C (adjust the scl and sda pins as needed)
i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=400000)

# Setup button on Pin 20 (with internal pull-down)
button = Pin(20, Pin.IN, Pin.PULL_DOWN)

def write_reg(addr, reg, data):
    i2c.writeto_mem(addr, reg, bytes([data]))

def read_reg(addr, reg, nbytes=1):
    return i2c.readfrom_mem(addr, reg, nbytes)

def init_accelerometer():
    # Soft-reset accelerometer
    write_reg(BMI088_ACCEL_ADDR, 0x7E, 0xB6)
    time.sleep(0.1)
    # Configure accelerometer:
    # 0x40: set range (here, +/-12g)
    # 0x41: set bandwidth (here, 500 Hz)
    # 0x7D: enable acceleration measurement
    write_reg(BMI088_ACCEL_ADDR, 0x40, 0x15)
    write_reg(BMI088_ACCEL_ADDR, 0x41, 0x0C)
    write_reg(BMI088_ACCEL_ADDR, 0x7D, 0x04)
    time.sleep(0.1)
    chip_id = read_reg(BMI088_ACCEL_ADDR, 0x00)[0]
    print("Accelerometer chip ID: 0x{:02X}".format(chip_id))

def read_accel_z():
    # Read 2 bytes from the Z-axis data register (0x16)
    data = read_reg(BMI088_ACCEL_ADDR, 0x16, 2)
    return int.from_bytes(data, 'little', True)

def calibrate_baseline(num_samples=20, delay=0.05):
    """
    Take several readings while the device is at rest (assumed to be in the upward/standing position)
    to establish a baseline for the Z-axis value.
    """
    samples = []
    for _ in range(num_samples):
        samples.append(read_accel_z())
        time.sleep(delay)
    baseline = sum(samples) // len(samples)
    return baseline

def main():
    init_accelerometer()
    print("Accelerometer initialized.")
    
    # Calibrate baseline (device should be at rest/upward)
    baseline = calibrate_baseline()
    print("Calibrated baseline (Z):", baseline)
    
    print("Squat detection activated. Perform a squat (move down then up) with the sensor on your arm.")
    print("Press the button to see 'PRESSED' printed.")
    
    update_period = 0.1  # seconds between sensor readings
    
    # Adjusted thresholds for more sensitivity on the arm:
    down_threshold = -2000  # trigger a downward movement if z_value falls below baseline + down_threshold
    up_threshold = 2500     # trigger an upward movement if z_value rises above baseline + up_threshold
    
    # State machine for squat detection:
    # "waiting_down" - waiting for a significant downward movement.
    # "waiting_up"   - downward movement detected; waiting for a significant upward movement.
    state = "waiting_down"
    
    # For detecting button press (rising edge)
    prev_button_state = 0
    start = True
    
    rep_count = 0
    
    while True:
        z_value = read_accel_z()
        
        # Check for button press (rising edge detection)
        current_button_state = button.value()
        if current_button_state == 1 and prev_button_state == 0 :
            if start:
                print("START WORKOUT (send signal to the model)")
                start = False
            else:
                print("FINISH WORKOUT (send signal to the model)")
                start = True
            
        prev_button_state = current_button_state
    
        
        # Squat detection state machine
        if state == "waiting_down":
            # Detect a significant downward movement
            if z_value < baseline + down_threshold:
                state = "waiting_up"
                print("Downward movement detected")
        elif state == "waiting_up":
            # Wait for a significant upward movement
            if z_value > baseline + up_threshold:
                rep_count += 1
                print("Upward movement detected - Squat rep count:", rep_count)
                state = "waiting_down"
                
        time.sleep(update_period)

if __name__ == '__main__':
    main()
