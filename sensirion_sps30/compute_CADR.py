# a script that just does the CADR computation from analyze_cadr.ipynb
import argparse
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit

# see equation (S1) from supplemental material here: https://www.tandfonline.com/doi/full/10.1080/02786826.2022.2054674?scroll=top&needAccess=true
# version of the functions where ACH is unknown and has to be solved for
class DecayFuncsACHUnk:
    def __init__(self, C_bgd, C_pt0):
        ## logarithmic function
        def func(t, ACH):
            # divide by 3600 to convert seconds to hours
            return C_bgd + C_pt0 * np.exp(-ACH*t / 3600)

        def linear_func(t, ACH):
            return np.log(C_pt0) - ACH * t / 3600

        self.func = func
        self.linear_func = linear_func

def run(csvfile, ACH_vd, V_r, csvout):
    df = pd.read_csv(csvfile)

    # cut off lead up prior to pm2.5 max
    pm25_max_idx = df.idxmax()['mPM2.5']
    if pm25_max_idx != 0:
        df = df.tail(-pm25_max_idx).copy()
    df.index -= df.index[0]
    df.time -= df.time[0]

    # cut off all records before pm2.5 reached 1000
    drop_start_idx = df[df['mPM2.5'] <= 1000].index[0]
    if drop_start_idx != 0:
        df = df.tail(-drop_start_idx)
    df.index -= df.index[0]
    df.time -= df.time[0]

    def test_fit(df):
        # trim all values below 100, error stops being multiplicative below there
        lt25_iloc = df[df['mPM2.5'] < 100].index[0]
        df = df[:lt25_iloc]

        C_bgd = 0
        C_pt0 = df['mPM2.5'][df.index[0]]
        f = DecayFuncsACHUnk(C_bgd, C_pt0)

        popt, pcov = curve_fit(f.linear_func, df.time, np.log(df['mPM2.5']))
        ACH = popt[0]
        stderr = np.sqrt(np.diag(pcov)[0])
        return (C_pt0, ACH, stderr)

    C_pt0, ACH, stderr = test_fit(df)
    ACH_f = ACH - ACH_vd
    CADR = V_r * ACH_f / 60 # units of ACH are 1/h, divide by 60 to convert to 1/minutes so CADR is in cubic feet per minute
    CADR_err = V_r * stderr / 60
    if csvout:
        print('{}, {:0.2f}, {:0.2f}, {}, {:0.2f}, {:0.2f}'.format(csvfile, C_pt0, ACH, stderr, CADR, CADR_err))
    else:
        print('C_pt0: {:0.2f}\nACH: {:0.2f}\nstderr (ACH): {:0.2f}\nCADR: {:0.2f} ±{:0.2f}'.format(C_pt0, ACH, stderr, CADR, CADR_err))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('ACH_vd', type=float, help='measured ACH due to deposition')
    parser.add_argument('V_r', type=float, help='Volume of room')
    parser.add_argument('csvfile', type=str, help='name of csv file to parse')
    parser.add_argument('--csvout', action='store_true', help='output in form of CSV: filename, C_pt0, ACH, stderr, CADR, CADR_err')

    args = parser.parse_args()

    run(args.csvfile, args.ACH_vd, args.V_r, args.csvout)

if __name__ == '__main__':
    main()
