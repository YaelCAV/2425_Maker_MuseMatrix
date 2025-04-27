import RPi.GPIO as GPIO
import time

# GPIO Pins (BCM)
DATA_595 = 17    # 74HC595 DS
CLOCK_595 = 27   # 74HC595 SHCP
LATCH_595 = 22   # 74HC595 STCP
LOAD_165 = 23    # 74HC165 PL
CLOCK_165 = 24   # 74HC165 CP
DATA_165 = 25    # 74HC165 Q7

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup([DATA_595, CLOCK_595, LATCH_595, LOAD_165, CLOCK_165], GPIO.OUT)
GPIO.setup(DATA_165, GPIO.IN)

# Shift out to 74HC595
def shift_out_595(data):
    GPIO.output(LATCH_595, GPIO.LOW)
    for i in range(8):
        GPIO.output(DATA_595, (data >> (7 - i)) & 1)
        GPIO.output(CLOCK_595, GPIO.HIGH)
        GPIO.output(CLOCK_595, GPIO.LOW)
    GPIO.output(LATCH_595, GPIO.HIGH)

# Read from 74HC165
def read_165():
    GPIO.output(LOAD_165, GPIO.LOW)
    GPIO.output(LOAD_165, GPIO.HIGH)
    data = 0
    for _ in range(8):
        data = (data << 1) | GPIO.input(DATA_165)
        GPIO.output(CLOCK_165, GPIO.HIGH)
        GPIO.output(CLOCK_165, GPIO.LOW)
    return data

try:
    while True:
        for col in range(8):
            # Activate column
            shift_out_595(1 << col)
            time.sleep(0.01)  # Allow LDRs to stabilize

            # Read rows
            row_data = read_165()
            # Bit 0=R1, Bit 1=R2, ..., Bit 6=R7 (1=blocked, 0=unblocked)

            print(f"C{col+1}: Rows={bin(row_data)[2:].zfill(8)}")
            # Example: 0b00000010 = R2 blocked

        print("---")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Exiting...")
    GPIO.cleanup()