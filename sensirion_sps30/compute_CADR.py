# a script that just does the CADR computation from analyze_cadr.ipynb
import argparse
import pandas as pd
import numpy as np
import scipy.stats
from scipy.optimize import curve_fit


# column to fit on, mass PM2.5 (mPM2.5) is a good choice for NaCl aerosol CADR
# changing this variable makes it possible to explore other options
#
# Not recommended to bother with the PM4.0 and PM10 values because they are just
# interpolations based on 0.5, 1.0, and 2.5. It is plain to see from viewing a graph
# that they track nearly exactly with PM2.5 values. See the sensirion datasheet
# for further explanation.
col_fit = 'mPM2.5'

# For SPS30 error is multiplicative in the window of [1000, 100] for mPM1.0 and mPM2.5 at
# ±10%. For the range [100, 0] error becomes ±10, which means error will become more exaggerated
# than 10%, especially as the value approaches 0. For nPM0.5, nPM1.0, and nPM2.5 error is
# multiplicative in the range [3000,1000] at ±10%. For the range [1000,0] it is ±100.
# see: https://sensirion.com/media/documents/8600FF88/616542B5/Sensirion_PM_Sensors_Datasheet_SPS30.pdf
#
# To keep in the range where error is multiplicative, set the `fit_under` value to the high value
# (1000 for mPM2.5) and `fit_over` to the low value (100 for mPM2.5).
#
# The automated experimental setup captures the mPM2.5 range of [1000, 100]. This means the full range
# of [3000, 1000] for the number concentrations and [1000, 100] for mPM1.0 are not represented in the
# data. For mPM1.0 `fit_under` is recommended to be set at 450.
fit_under = 1000
fit_over = 100

# see equation (S1) from supplemental material here: https://www.tandfonline.com/doi/full/10.1080/02786826.2022.2054674?scroll=top&needAccess=true
# version of the functions where ACH is unknown and has to be solved for
class DecayFuncs:
    def __init__(self, C_bgd, C_pt0):
        ## logarithmic function
        def func(t, ACH):
            # divide by 3600 to convert seconds to hours
            return C_bgd + C_pt0 * np.exp(-ACH*t / 3600)

        # linear version of the same function, it's the natural log of the exponential function
        def linear_func(t, ACH):
            return np.log(C_pt0) - ACH * t / 3600

        self.func = func
        self.linear_func = linear_func

# perform the curve fitting and return the resulting parameters
def test_fit(df):
    C_bgd = 0
    C_pt0 = df[col_fit][df.index[0]]
    f = DecayFuncs(C_bgd, C_pt0)

    popt, pcov = curve_fit(f.linear_func, df.time, np.log(df[col_fit]))
    stderr = np.sqrt(np.diag(pcov)[0])
    return (C_pt0, popt, stderr)

def find_ACHvd(df):
    # begin window search at `col_fit` max
    pm25_max_idx = df.idxmax()[col_fit]
    if pm25_max_idx != 0:
        df = df.tail(-pm25_max_idx).copy()
        df.index -= df.index[0]
        df['time'] -= df.time[0]

    # cut off all records before `col_fit` dropped to `fit_under`
    drop_start_idx = df[df[col_fit] <= fit_under].index[0]
    if drop_start_idx != 0:
        df = df.tail(-drop_start_idx).copy()
        df.index -= df.index[0]
        df['time'] -= df.time[0]

    # cut off all records after `col_fit` dropped below `fit_over`
    lt25_iloc = df[df[col_fit] < fit_over].index[0]
    df = df.head(lt25_iloc).copy()

    print('num data points to fit: {}'.format(len(df)))

    C_pt0, popt, naturaldecay_stderr = test_fit(df)
    ACH_vd = popt[0]
    print('C_pt0: {}'.format(C_pt0))
    print('ACH_vd: {}'.format(ACH_vd))
    print('stderr: {}'.format(naturaldecay_stderr))

    return C_pt0, ACH_vd, naturaldecay_stderr

def find_trialACH(df):
    # begin window search at `col_fit` max
    pm25_max_idx = df.idxmax()[col_fit]
    if pm25_max_idx != 0:
        df = df.tail(-pm25_max_idx).copy()
        df.index -= df.index[0]
        df['time'] -= df.time[0]
    
    # cut off all records before `col_fit` dropped to `fit_under`
    drop_start_idx = df[df[col_fit] <= fit_under].index[0]
    if drop_start_idx != 0:
        df = df.tail(-drop_start_idx).copy()
        df.index -= df.index[0]
        df['time'] -= df.time[0]
    
    # cut off all records after `col_fit` dropped below `fit_over`
    lt25_iloc = df[df[col_fit] < fit_over].index[0]
    df = df.head(lt25_iloc).copy()
    
    print('num data points to fit: {}'.format(len(df)))
    
    C_pt0, popt, totaldecay_stderr = test_fit(df)
    ACH = popt[0]
    print('C_pt0: {}'.format(C_pt0))
    print('ACH: {}'.format(ACH))
    print('stderr: {}'.format(totaldecay_stderr))

    return C_pt0, ACH, totaldecay_stderr

def run(csvfile, V_r, num_trials):
    df = pd.read_csv(csvfile.format('vd'))
    C_pt0, ACH_vd, naturaldecay_stderr = find_ACHvd(df)

    trials = []
    for i in range(1, num_trials+1):
        df = pd.read_csv(csvfile.format('trial{}'.format(i)))
        C_pt0, ACH, totaldecay_stderr = find_trialACH(df)
        ACH_f = ACH - ACH_vd
        CADR = V_r * ACH_f / 60 # units of ACH are 1/h, divide by 60 to convert to 1/minutes so CADR is in cubic feet per minute
        CADR_err = V_r * np.sqrt((naturaldecay_stderr/60)**2 + (totaldecay_stderr/60)**2)
        print('CADR: {:0.2f} ±{:0.2f}'.format(CADR, CADR_err))
        trials.append(CADR)
    
    print()
    print('mean of trials: {}'.format(np.mean(trials)))
    print('std error of the mean: {}'.format(scipy.stats.sem(trials)))
    print('{:.1f} ±{:.2f}'.format(np.mean(trials), scipy.stats.sem(trials)))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--V_r', type=float, default=(59. / 12) * (59. / 12) * (72.8 / 12), help='Volume of room in cubic feet')
    parser.add_argument('--num-trials', type=int, default=3, help='number of trials in experiment')
    parser.add_argument('csvfile', type=str, help='name of csv file to parse')
#    parser.add_argument('--csvout', action='store_true', help='output in form of CSV: filename, C_pt0, ACH, stderr, CADR, CADR_err')

    args = parser.parse_args()

    run(args.csvfile, args.V_r, args.num_trials)

if __name__ == '__main__':
    main()
