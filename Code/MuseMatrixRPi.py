import RPi.GPIO as GPIO
import spidev
import serial
import time

# GPIO Pin Definitions (BCM numbering)
DATA_595 = 17    # 74HC595 DS (Pin 14), Physical Pin 11
CLOCK_595 = 27   # 74HC595 SHCP (Pin 11), Physical Pin 13
LATCH_595 = 22   # 74HC595 STCP (Pin 12), Physical Pin 15
LOAD_165 = 23    # 74HC165 PL (Pin 1), Physical Pin 16
CLOCK_165 = 24   # 74HC165 CP (Pin 2), Physical Pin 18
DATA_165 = 25    # 74HC165 Q7 (Pin 9), Physical Pin 22
MIDI_TX = 14     # UART TXD for MIDI, Physical Pin 8

# SPI Pins for MCP3008 (already assigned by SPI0)
SPI_CE0 = 8      # MCP3008 CS\, Physical Pin 24
SPI_MISO = 9     # MCP3008 DOUT, Physical Pin 21
SPI_MOSI = 10    # MCP3008 DIN, Physical Pin 19
SPI_SCLK = 11    # MCP3008 CLK, Physical Pin 23

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup([DATA_595, CLOCK_595, LATCH_595, LOAD_165, CLOCK_165, MIDI_TX], GPIO.OUT)
GPIO.setup(DATA_165, GPIO.IN)

# Setup SPI for MCP3008
spi = spidev.SpiDev()
spi.open(0, 0)  # Bus 0, Device 0 (CE0)
spi.max_speed_hz = 1350000

# Setup UART for MIDI (31,250 baud)
midi_out = serial.Serial(
    port='/dev/ttyS0',
    baudrate=31250,
    bytesize=8,
    parity='N',
    stopbits=1,
    timeout=1
)

# Function to read MCP3008 ADC (0-1023)
def read_adc(channel):
    if channel < 0 or channel > 7:
        return -1
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

# Function to convert ADC value to MIDI CC (0-127)
def get_midi_cc(value):
    return value >> 3  # Scale 0-1023 to 0-127

# Function to send MIDI Note On/Off
def send_midi_note(channel, note, velocity, on=True):
    status = 0x90 if on else 0x80  # Note On: 0x90, Off: 0x80
    status |= (channel & 0x0F)    # Channel 0-15
    midi_out.write(bytes([status, note & 0x7F, velocity & 0x7F]))

# Function to send MIDI Control Change
def send_midi_cc(channel, controller, value):
    status = 0xB0 | (channel & 0x0F)  # Control Change
    midi_out.write(bytes([status, controller & 0x7F, value & 0x7F]))

# Function to shift out data to 74HC595
def shift_out_595(data):
    GPIO.output(LATCH_595, GPIO.LOW)
    for i in range(8):
        GPIO.output(DATA_595, (data >> (7 - i)) & 1)
        GPIO.output(CLOCK_595, GPIO.HIGH)
        GPIO.output(CLOCK_595, GPIO.LOW)
    GPIO.output(LATCH_595, GPIO.HIGH)

# Function to read 74HC165
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
        # Scan each column
        for col in range(8):
            # Activate column (e.g., 0b00000001 for C1)
            shift_out_595(1 << col)
            time.sleep(0.01)  # Stabilize LDRs

            # Read row states
            row_data = read_165()
            # row_data: Bit 0 = R1, Bit 1 = R2, ..., Bit 6 = R7 (1 = blocked)

            # Process grid states
            for row in range(7):
                if row_data & (1 << row):
                    # Blocked slot: Send Note On
                    note = 60 + row + col * 7  # C4=60, maps R1C1 to 60, R7C8 to 115
                    send_midi_note(0, note, 127, True)
                    time.sleep(0.05)  # Short note duration
                    send_midi_note(0, note, 0, False)
                # Unblocked: No note (or could send Note Off if tracking)

            # Read potentiometer
            pot_value = read_adc(col)  # 0-1023
            cc_value = get_midi_cc(pot_value)  # Scale to 0-127
            send_midi_cc(0, 1 + col, cc_value)  # Controller 1-8 for C1-C8

            # Debug output
            print(f"C{col+1}: Rows={bin(row_data)[2:].zfill(8)}, Pot={pot_value}, CC={cc_value}")

        print("---")
        time.sleep(0.5)  # Loop delay

except KeyboardInterrupt:
    print("Exiting...")
    midi_out.close()
    spi.close()
    GPIO.cleanup()