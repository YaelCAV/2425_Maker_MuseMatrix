import lgpio
import time

# GPIO Pins (BCM)
DATA_595 = 17
CLOCK_595 = 27
LATCH_595 = 22
LOAD_165 = 23
CLOCK_165 = 24
DATA_165 = 25

# Open GPIO chip
h = lgpio.gpiochip_open(0)

# Setup GPIO
lgpio.gpio_claim_output(h, DATA_595)
lgpio.gpio_claim_output(h, CLOCK_595)
lgpio.gpio_claim_output(h, LATCH_595)
lgpio.gpio_claim_output(h, LOAD_165)
lgpio.gpio_claim_output(h, CLOCK_165)
lgpio.gpio_claim_input(h, DATA_165)

def shift_out_595(data):
    lgpio.gpio_write(h, LATCH_595, 0)
    for i in range(8):
        lgpio.gpio_write(h, DATA_595, (data >> (7 - i)) & 1)
        lgpio.gpio_write(h, CLOCK_595, 1)
        lgpio.gpio_write(h, CLOCK_595, 0)
    lgpio.gpio_write(h, LATCH_595, 1)

def read_165():
    lgpio.gpio_write(h, LOAD_165, 0)
    lgpio.gpio_write(h, LOAD_165, 1)
    data = 0
    for _ in range(8):
        data = (data << 1) | lgpio.gpio_read(h, DATA_165)
        lgpio.gpio_write(h, CLOCK_165, 1)
        lgpio.gpio_write(h, CLOCK_165, 0)
    return data

try:
    while True:
        for col in range(8):
            shift_out_595(1 << col)
            time.sleep(0.01)
            row_data = read_165()
            print(f"C{col+1}: Rows={bin(row_data)[2:].zfill(8)}")
        print("---")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Exiting...")
    lgpio.gpiochip_close(h)