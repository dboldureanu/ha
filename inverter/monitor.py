import serial
import time

def send_command(command, port='/dev/ttyUSB0', baudrate=2400):
    try:
        with serial.Serial(port, baudrate=baudrate, timeout=2) as ser:
            full_command = command + '\r'
            ser.write(full_command.encode())
            time.sleep(0.2)
            response = ser.readline().decode(errors='ignore').strip()
            return response
    except serial.SerialException as e:
        print("Serial communication error:", e)
        return None

def parse_qpigs(response):
    if not response.startswith('('):
        print("Unexpected response:", response)
        return

    response = response[1:]  # remove leading '('
    fields = response.split(' ')

    try:
        print("=== QPIGS – Real-Time Inverter Status ===")
        print(f"Grid voltage:                 {fields[0]} V")
        print(f"Grid frequency:               {fields[1]} Hz")
        print(f"AC output voltage:            {fields[2]} V")
        print(f"AC output frequency:          {fields[3]} Hz")
        print(f"AC output apparent power:     {fields[4]} VA")
        print(f"AC output active power:       {fields[5]} W")
        print(f"Output load percentage:       {fields[6]} %")
        print(f"Battery voltage:              {fields[7]} V")
        print(f"Battery charging current:     {fields[8]} A")
        print(f"Battery capacity:             {fields[9]} %")
        print(f"Inverter heat sink temp:      {fields[10]} °C")
        print(f"PV input current:             {fields[11]} A")
        print(f"PV input voltage:             {fields[12]} V")
        print(f"Battery voltage from SCC:     {fields[13]} V")
        print(f"Battery discharge current:    {fields[14]} A")
        print(f"Device status (bitfield):     {fields[15]}")
        # You can continue parsing more flags if needed
    except IndexError:
        print("Incomplete or unrecognized response:")
        print(fields)

def main():
    print("Sending QPIGS command to inverter...")
    response = send_command("QPIGS")
    if response:
        parse_qpigs(response)
    else:
        print("No response received.")

if __name__ == "__main__":
    main()
