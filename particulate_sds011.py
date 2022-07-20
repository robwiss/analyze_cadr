import time
import argparse
import csv
import serial

def run(output):
    ser = serial.Serial('/dev/ttyUSB0')

    start = time.time()
    with open(output, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['time', 'pm2.5', 'pm10'])
        try:
            while True:
                data = []
                for i in range(0,10):
                    datum = ser.read()
                    data.append(datum)
                
                pm2_5 = int.from_bytes(b''.join(data[2:4]), byteorder='little') / 10
                pm10 = int.from_bytes(b''.join(data[4:6]), byteorder='little') / 10

                elapsed = time.time() - start
                writer.writerow([elapsed, pm2_5, pm10])
                print('PM2.5: {:3.2f}, PM10: {:3.2f}'.format(pm2_5, pm10))
        except KeyboardInterrupt:
            pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=str, default='output.sds011.csv', help='name of csv file to output')

    args = parser.parse_args()

    run(args.output)

if __name__ == '__main__':
    main()
