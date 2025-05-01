import bluetooth
import time
import utime
from micropython import const
from ble_advertising import advertising_payload
from machine import ADC, I2C, Pin

# ------------------------------
# BLE Setup
# ------------------------------

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)

SERVICE_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef0")
CHAR_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef1")
CHAR = (CHAR_UUID, bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY)
SERVICE = (SERVICE_UUID, (CHAR,),)

class BLEPeripheral:
    def __init__(self):
        print("🔌 Initializing BLE...")
        self.ble = bluetooth.BLE()
        self.ble.active(False)
        time.sleep_ms(100)
        self.ble.active(True)

        self.ble.irq(self._irq)
        ((self.handle,),) = self.ble.gatts_register_services((SERVICE,))
        self._connections = set()
        self.connected = False

        addr_type, addr = self.ble.config('mac')
        print("📟 MAC:", ':'.join('{:02X}'.format(b) for b in addr))

        self.advertise()

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            self.connected = True
            print("✅ Central connected!")
            utime.sleep_ms(200)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self._connections.discard(conn_handle)
            self.connected = False
            print("⚠️ Central disconnected. Re-advertising...")
            self.advertise()

    def advertise(self):
        payload = advertising_payload(name="Pico", services=[SERVICE_UUID])
        self.ble.gap_advertise(100_000, adv_data=payload)
        print("📡 Advertising as 'Pico'...")

    def send(self, msg):
        if self.connected:
            self.ble.gatts_write(self.handle, msg)
            for conn in self._connections:
                self.ble.gatts_notify(conn, self.handle, msg)
            print("📤 Sent:", msg)
        else:
            print("⛔ No central connected.")

# ------------------------------
# Sensor Setup
# ------------------------------

pulse = ADC(1)
max_samples = 1000
short_average = 15
long_average = 100
beat_threshold = 200
finger_threshold = 1500
sample_delay = 0.1
history = []
last_beat_time = 0
bpm_list = []

def finger_detected():
    if len(history) < long_average:
        return False
    avg_1 = sum(history[-short_average:]) / short_average
    avg_2 = sum(history[-long_average:]) / long_average
    return (avg_1 - avg_2) > beat_threshold

BMI088_ACCEL_ADDR = 0x19
i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=400000)
button = Pin(20, Pin.IN, Pin.PULL_DOWN)

def write_reg(addr, reg, data):
    i2c.writeto_mem(addr, reg, bytes([data]))

def read_reg(addr, reg, nbytes=1):
    return i2c.readfrom_mem(addr, reg, nbytes)

def init_accelerometer():
    write_reg(BMI088_ACCEL_ADDR, 0x7E, 0xB6)
    time.sleep(0.1)
    write_reg(BMI088_ACCEL_ADDR, 0x40, 0x15)
    write_reg(BMI088_ACCEL_ADDR, 0x41, 0x0C)
    write_reg(BMI088_ACCEL_ADDR, 0x7D, 0x04)
    time.sleep(0.1)
    chip_id = read_reg(BMI088_ACCEL_ADDR, 0x00)[0]
    print("Accelerometer chip ID: 0x{:02X}".format(chip_id))

def read_accel_z():
    data = read_reg(BMI088_ACCEL_ADDR, 0x16, 2)
    return int.from_bytes(data, 'little', True)

# ------------------------------
# Main Loop
# ------------------------------

ble = BLEPeripheral()

def main():
    global last_beat_time

    init_accelerometer()
    print("System initialized.")

    prev_button_state = 0
    workout_active = False

    z_history = []
    rep_count = 0
    state = "waiting"  # 'waiting', 'up', 'down'
    Z_SENSITIVITY = None
    last_rep_time = utime.ticks_ms()

    bpm = 0

    # Previous values to detect changes
    last_sent_reps = -1
    last_sent_bpm = -10
    last_sent_workout = -1

    while True:
        # --- BPM Logic ---
        value = pulse.read_u16()
        history.append(value)
        history[:] = history[-max_samples:]

        signal_range = max(history) - min(history)

        detected_bpm = 0
        if signal_range > finger_threshold and len(history) >= long_average:
            if finger_detected():
                now = utime.ticks_ms()
                if last_beat_time != 0:
                    time_diff = utime.ticks_diff(now, last_beat_time)
                    if 300 < time_diff < 2000:
                        detected_bpm = 60000 / time_diff
                        bpm_list.append(detected_bpm)
                        bpm_list[:] = bpm_list[-5:]
                        bpm = sum(bpm_list) / len(bpm_list)
                last_beat_time = now
        else:
            if bpm_list:
                bpm = sum(bpm_list) / len(bpm_list)
            else:
                bpm = 0

        # --- Button ---
        current_button_state = button.value()
        if current_button_state == 1 and prev_button_state == 0:
            workout_active = not workout_active
            if workout_active:
                print("🏋️ WORKOUT STARTED")
            else:
                print("🛑 WORKOUT ENDED")
        prev_button_state = current_button_state

        # --- Accelerometer & Rep Counting ---
        if workout_active:
            z_value = read_accel_z()
            z_history.append(z_value)
            z_history[:] = z_history[-50:]

            if Z_SENSITIVITY is None and len(z_history) >= 20:
                z_range = max(z_history) - min(z_history)
                Z_SENSITIVITY = z_range * 0.35
                print(f"📊 Rep detection threshold set to {Z_SENSITIVITY}")

            if Z_SENSITIVITY:
                baseline = sum(z_history) / len(z_history)
                now = utime.ticks_ms()

                if state == "waiting":
                    if z_value > baseline + Z_SENSITIVITY:
                        state = "up"

                elif state == "up":
                    if z_value < baseline - Z_SENSITIVITY:
                        if utime.ticks_diff(now, last_rep_time) > 600:
                            rep_count += 1
                            last_rep_time = now
                            state = "down"
                            print(f"✅ REP {rep_count}")

                elif state == "down":
                    if baseline - Z_SENSITIVITY < z_value < baseline + Z_SENSITIVITY:
                        state = "waiting"

        else:
            z_value = 0
            state = "waiting"

        # --- Send Data only on changes ---
        send = False

        # Workout change
        if int(workout_active) != last_sent_workout:
            send = True
            last_sent_workout = int(workout_active)

        # New rep
        if rep_count != last_sent_reps:
            send = True
            last_sent_reps = rep_count

        # Significant BPM change (2 BPM difference)
        if abs(round(bpm) - last_sent_bpm) >= 2:
            send = True
            last_sent_bpm = round(bpm)

        if send:
            data_str = f"BPM:{round(bpm)},Reps:{rep_count},Workout:{int(workout_active)}"
            ble.send(data_str)

        utime.sleep(sample_delay)

if __name__ == '__main__':
    main()

