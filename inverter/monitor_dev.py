import serial
import time
import json
import paho.mqtt.client as mqtt

def send_command(command, port='/dev/ttyUSB0', baudrate=2400):
    try:
        with serial.Serial(port, baudrate=baudrate, timeout=2) as ser:
            ser.write((command + '\r').encode())
            time.sleep(0.2)
            return ser.readline().decode(errors='ignore').strip()
    except serial.SerialException as e:
        print("Serial error:", e)
        return None

def parse_qpigs(response):
    if not response.startswith('('):
        return None
    response = response[1:]
    fields = response.split()

    if len(fields) < 21:
        print("Unexpected field count:", len(fields))
        print("Raw fields:", fields)
        return None

    try:
        return {
            "grid_voltage": float(fields[0]),
            "grid_frequency": float(fields[1]),
            "ac_output_voltage": float(fields[2]),
            "ac_output_frequency": float(fields[3]),
            "output_apparent_power": float(fields[4]),
            "output_active_power": float(fields[5]),
            "output_load_percent": float(fields[6]),
            "bus_voltage": float(fields[7]),
            "battery_voltage": float(fields[8]),
            "battery_charging_current": float(fields[9]),
            "battery_capacity": float(fields[10]),
            "inverter_temperature": float(fields[11]),
            "pv_input_current": float(fields[12]),
            "pv_input_voltage": float(fields[13]),
            "battery_voltage_scc": float(fields[14]),
            "battery_discharge_current": float(fields[15]),
            "device_status": fields[16],
            "fan_on_voltage_offset": float(fields[17]) * 0.01,  # convert from 10mV to V
            "eeprom_version": fields[18],
            "pv_charging_power": float(fields[19]),
            "device_status_b10_b8": fields[20][:3]
        }
    except (IndexError, ValueError) as e:
        print("Failed to parse:", fields, "Error:", e)
        return None


BASE_TOPIC = "homeassistant/sensor/inverter"

units = {
    "grid_voltage": ("V", "voltage"),
    "grid_frequency": ("Hz", "frequency"),
    "ac_output_voltage": ("V", "voltage"),
    "ac_output_frequency": ("Hz", "frequency"),
    "output_apparent_power": ("VA", None),
    "output_active_power": ("W", "power"),
    "output_load_percent": ("%", None),
    "battery_voltage": ("V", "voltage"),
    "battery_charging_current": ("A", "current"),
    "battery_capacity": ("%", None),
    "inverter_temperature": ("°C", "temperature"),
    "pv_input_current": ("A", "current"),
    "pv_input_voltage": ("V", "voltage"),
    "battery_voltage_scc": ("V", "voltage"),
    "battery_discharge_current": ("A", "current"),
    "device_status": ("", None)
}

def publish_discovery_config(client, key, name, unit, device_class):
    config_topic = f"homeassistant/sensor/inverter_{key}/config"
    payload = {
        "name": name,
        "state_topic": f"{BASE_TOPIC}/{key}/state",
        "unique_id": f"{key}",
        "unit_of_measurement": unit,
        "device_class": device_class,
        "device": {
            "identifiers": ["inverter_1"],
            "name": "Inverter",
            "model": "Axpert",
            "manufacturer": "Voltronic"
        }
    }
    client.publish(config_topic, json.dumps(payload), retain=True)

def publish_mqtt(data):
    client = mqtt.Client(callback_api_version=2)
    client.connect("localhost")

    for key, value in data.items():
        unit, device_class = units.get(key, ("", None))
        name = f"Inverter {key.replace('_', ' ').title()}"
        publish_discovery_config(client, key, name, unit, device_class)
        topic = f"{BASE_TOPIC}/{key}/state"
        client.publish(topic, str(value), retain=True)

    client.loop(2)
    client.disconnect()

def main():
    print("Requesting inverter status...")
    response = send_command("QPIGS")
    if response:
        data = parse_qpigs(response)
        if data:
            print("Parsed inverter data:")
            print(json.dumps(data, indent=2))
            publish_mqtt(data)
        else:
            print("Failed to parse data.")
    else:
        print("No response from inverter.")

if __name__ == "__main__":
    main()

