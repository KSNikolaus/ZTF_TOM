import numpy as np
import matplotlib.pyplot as plt
from math import pi, cos


def setup(calc_time, timesteps, min_harmonics, max_harmonics, period_mean = 2, period_sigma = 1, suppression = 0):
    harmonics = int(np.random.uniform(min_harmonics, max_harmonics))    #np.random.uniform(start, stop)
    ampl_k = []
    phase_k = []
    time = []
    period = np.random.normal(period_mean, period_sigma)                #np.random.normal(mean, sigma)
    for idx in range(timesteps):
        time.append(idx*calc_time/timesteps)

    for idx in range(harmonics):
        ampl_k.append(np.random.uniform(0.1, 2)/((idx+1)**suppression))
        phase_k.append(np.random.uniform(0, 6*pi))

    return time, period, ampl_k, phase_k

    
def RR_fourier(time, ampl_k, phase_k, period = 1, epoch = 0, ampl_0 = 0):

    M = ampl_0
    if len(ampl_k) != len(phase_k):
        raise 'different parameter number'

    for idx in range(len(ampl_k)):
        M = M + ampl_k[idx] * cos(((2*pi*(idx+1))/period)*(time-epoch)+phase_k[idx])

    return M


def lightcurve(time, period, ampl_k, phase_k, epoch = 0, ampl_0 = 0): 
    curve = []
    for idx in range(len(time)):
        curve.append(RR_fourier(time[idx], ampl_k, phase_k, period, epoch, ampl_0))

    return curve


def uncertainties(time, curve, uncertain_factor):

    N = len(time)
    uncertainty = np.random.normal(0, uncertain_factor/100, N)
    realcurve = []
    for idx in range(N):
        realcurve.append(curve[idx]+uncertainty[idx])

    return realcurve



calc_time = 2
timesteps = 10000
min_harmonics = 4
max_harmonics = 12
suppression = 3
period_mean = 0.7
period_sigma = 0.2
uncertain_factor = 4

time, period, ampl_k, phase_k = setup(calc_time, timesteps, min_harmonics, max_harmonics, period_mean, period_sigma, suppression)
curve = lightcurve(time, period, ampl_k, phase_k)
realcurve = uncertainties(time, curve, uncertain_factor)

plt.plot(np.array(time), np.array(realcurve), marker='.', color='r')
plt.plot(np.array(time), np.array(curve), marker='.', color='b')
plt.show()


