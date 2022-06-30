import time
from pms5003 import PMS5003
import argparse
import csv

from bme280 import BME280

try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus

bus = SMBus(1)
bme280 = BME280(i2c_dev=bus)

# Get the temperature of the CPU for compensation
def get_cpu_temperature():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        temp = f.read()
        temp = int(temp) / 1000.0
    return temp

def get_comp_temp():
    # Tuning factor for compensation. Decrease this number to adjust the
    # temperature down, and increase to adjust up
    factor = 2.35

    if not hasattr(get_comp_temp, 'cpu_temps'):
        get_comp_temp.cpu_temps = [get_cpu_temperature()] * 5
    cpu_temp = get_cpu_temperature()
    # Smooth out with some averaging to decrease jitter
    cpu_temps = get_comp_temp.cpu_temps
    cpu_temps = cpu_temps[1:] + [cpu_temp]
    avg_cpu_temp = sum(cpu_temps) / float(len(cpu_temps))
    raw_temp = bme280.get_temperature()
    comp_temp = raw_temp - ((avg_cpu_temp - raw_temp) / factor)
    return comp_temp

def run(output, warmup, details):
    pms5003 = PMS5003()

    # let the sensor warm up
    for x in range(warmup):
        pms5003.read()

    start = time.time()
    with open(output, 'w') as csvfile:
        writer = csv.writer(csvfile)
        if details:
            writer.writerow(['time', 'pm1.0', 'pm2.5', 'pm10', '>0.3', '>0.5', '>1.0', '>2.5', '>5', '>10'])
        else:
            writer.writerow(['time', 'pm1.0', 'pm2.5', 'pm10'])
        try:
            while True:
 #               comp_temp = get_comp_temp()
 #               humidity = bme280.get_humidity()

                readings = pms5003.read()
                elapsed = time.time() - start
                if details:
                    writer.writerow([elapsed, readings.pm_ug_per_m3(1.0), readings.pm_ug_per_m3(2.5), readings.pm_ug_per_m3(10),
                        readings.pm_per_1l_air(0.3), readings.pm_per_1l_air(0.5), readings.pm_per_1l_air(1.0), readings.pm_per_1l_air(2.5),
                        readings.pm_per_1l_air(5), readings.pm_per_1l_air(10)])
                else:
                    writer.writerow([elapsed, readings.pm_ug_per_m3(1.0), readings.pm_ug_per_m3(2.5), readings.pm_ug_per_m3(10)])
#                 print("""Temperature: {:05.2f} *C
# Relative humidity: {:05.2f} %
# """.format(comp_temp, humidity))
                print(readings)
        except KeyboardInterrupt:
            pass
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--details', action='store_true', help='read the detailed size groups')
    parser.add_argument('--output', type=str, default='output.csv', help='name of csv file to output')
    parser.add_argument('--warmup', type=int, default=15, help='readings to throw away before starting to record csv')

    args = parser.parse_args()

    run(args.output, args.warmup, args.details)

if __name__ == '__main__':
    main()
