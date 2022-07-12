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

def run(csvfile, ACH_vd, V_r, lower_bound):
    df = pd.read_csv(csvfile)

    # begin window search at pm2.5 max
    pm25_max_idx = df.idxmax()['pm2.5']
    if pm25_max_idx != 0:
        df = df.tail(-pm25_max_idx)
    df.index = df.index - df.index[0]
    df.time = df.time - df.time[0]

    end_start_search = df[df['>0.3'] < 65535].index[0]

    def test_fit(df):
        # cut all values after pm2.5 gets to about 25, they have an outsized impact on fit after converting to log
        lt25_iloc = df[df['pm2.5'] < lower_bound].index[0]
        df = df[:lt25_iloc]

        C_bgd = 0
        C_pt0 = df['pm2.5'][df.index[0]]
        f = DecayFuncsACHUnk(C_bgd, C_pt0)

        popt, pcov = curve_fit(f.linear_func, df.time, np.log(df['pm2.5']))
        ACH = popt[0]
        stddev = np.sqrt(np.diag(pcov)[0])
        return (C_pt0, ACH, stddev)

    fits = []
    for i in range(end_start_search):
        df_pm25 = df[['time','pm2.5']].copy()

        if i != 0:
            df_pm25 = df_pm25.tail(-i)
            # adjust times according to new t0 after tail was run
            df_pm25.time = df_pm25.time - df_pm25.time.iloc[0]
            df_pm25.index = df_pm25.index - df_pm25.index[0]
        
        C_pt0, ACH, stddev = test_fit(df_pm25)
        fits.append((i, C_pt0, ACH, stddev))
    df_fits = pd.DataFrame(fits, columns=['i', 'C_pt0', 'ACH', 'stddev'])
    j = df_fits.idxmin()['stddev']

    ACH = df_fits.ACH[j]
    print('ACH: {}'.format(ACH))

    ACH_f = ACH - ACH_vd
    CADR = V_r * ACH_f / 60 # units of ACH are 1/h, divide by 60 to convert to 1/minutes so CADR is in cubic feet per minute
    print('CADR: {:0.2f}'.format(CADR))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('ACH_vd', type=float, help='measured ACH due to deposition')
    parser.add_argument('V_r', type=float, help='Volume of room')
    parser.add_argument('csvfile', type=str, help='name of csv file to parse')
    parser.add_argument('--lower_bound', type=float, default=25, help='pm2.5 value to use as lower bound for fitting window')

    args = parser.parse_args()

    run(args.csvfile, args.ACH_vd, args.V_r, args.lower_bound)

if __name__ == '__main__':
    main()
