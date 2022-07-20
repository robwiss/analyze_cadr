import time
from pms5003 import PMS5003
import argparse
import csv

def run(output, warmup):
    pms5003 = PMS5003()

    # let the sensor warm up
    for x in range(warmup):
        pms5003.read()

    start = time.time()
    with open(output, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['time', 'pm1.0', 'pm2.5', 'pm10', '>0.3', '>0.5', '>1.0', '>2.5', '>5', '>10'])
        try:
            while True:
                readings = pms5003.read()
                elapsed = time.time() - start
                writer.writerow([elapsed, readings.pm_ug_per_m3(1.0), readings.pm_ug_per_m3(2.5), readings.pm_ug_per_m3(10),
                    readings.pm_per_1l_air(0.3), readings.pm_per_1l_air(0.5), readings.pm_per_1l_air(1.0), readings.pm_per_1l_air(2.5),
                    readings.pm_per_1l_air(5), readings.pm_per_1l_air(10)])
                print(readings)
        except KeyboardInterrupt:
            pass
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=str, default='output.csv', help='name of csv file to output')
    parser.add_argument('--warmup', type=int, default=15, help='readings to throw away before starting to record csv')

    args = parser.parse_args()

    run(args.output, args.warmup)

if __name__ == '__main__':
    main()
