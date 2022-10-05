import time
import argparse
import csv
from sensirion_sps30 import SPS30

from bme280 import BME280

try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus

bus = SMBus(1)
bme280 = BME280(i2c_dev=bus)

def run(output):
    sps30 = SPS30('/dev/ttyUSB0')
    product_type = sps30.read_product_type()
    assert(product_type == '00080000') # if this is wrong maybe wrong port has been selected

    print('product type: {}'.format(product_type))
    print('serial number: {}'.format(sps30.read_serial_number()))
    print('firmware version: {}'.format(sps30.read_firmware_version()))
    status_register = sps30.read_status_register()
    fan_speed_status = 'OK' if status_register & (1<<21) == 0 else 'TOO HIGH OR LOW'
    laser_status = 'OK' if status_register & (1<<5) == 0 else 'CURRENT IS OUT OF RANGE'
    fan_status = 'OK' if status_register & (1<<4) == 0 else 'FAN IS ON BUT MEASURED RPM IS 0'
    print('fan speed: {}'.format(fan_speed_status))
    print('laser: {}'.format(laser_status))
    print('fan: {}'.format(fan_status))

    start = time.time()
    with open(output, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['time', 'mPM1.0', 'mPM2.5', 'mPM4.0', 'mPM10', 'nPM0.5', 'nPM1.0', 'nPM2.5', 'nPM4.0', 'nPM10', 'typical', 'temp_C', 'temp_F', 'rh'])
        sps30.start_measurement()
        try:
            while True:
                data = sps30.read_values()
                while data is None:
                    data = sps30.read_values()
                elapsed = time.time() - start

                temperature = bme280.get_temperature()
                humidity = bme280.get_humidity()

                writer.writerow([elapsed,
                    data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9],
                    '{:5.2f}'.format(temperature), '{:5.2f}'.format(temperature * 1.8 + 32), '{:5.2f}'.format(humidity)])
                csvfile.flush()
                
                t_min = int(elapsed / 60)
                t_sec = elapsed - (t_min * 60)
                print('''time: {}:{:05.2f}
Mass   PM1.0: {:5d}, PM2.5: {:5d}, PM4.0: {:5d}, PM10: {:5d}
Number PM0.5: {:5d}, PM1.0: {:5d}, PM2.5: {:5d}, PM4.0: {:5d}, PM10: {:5d}
typical particle size: {:5d}
temp: {:05.2f} *F
rh: {:05.2f}%\n'''.format(t_min, t_sec, data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9], temperature * 1.8 + 32, humidity))
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        sps30.stop_measurement()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=str, default='output.csv', help='name of csv file to output')

    args = parser.parse_args()

    run(args.output)

if __name__ == '__main__':
    main()
