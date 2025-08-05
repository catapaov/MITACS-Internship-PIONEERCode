import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import pandas as pd
from matplotlib.gridspec import GridSpec
from scipy.special import factorial


"""
Here are the implementations of all the functions used in the file SPE_fit_notebook.
"""

tol = 1e-9

#This function computes the area under the curve of a waveform file between specified time intervals.

def compute_area(file,t0,t1):
    
    file_ = pd.read_csv(file, delimiter=',', header=0, skiprows=1)
    file_ = np.array(file_)

    #This is used to find the indices of the time intervals in the data.
    #It finds the first index where the time is greater than or equal to t0 -
    #tol and the first index where the time is greater than t1 + tol.
    #The tol is used to avoid numerical issues with floating point precision.
    #The times are then sliced to only include the data between these two indices.

    times = file_[:,0]
    index_0  = np.searchsorted(times, t0 - tol, side='left')
    index_f  = np.searchsorted(times, t1 + tol, side='right') - 1
    times = times[index_0:index_f+1]

    df= pd.DataFrame(columns=['Waveform', 'Area'])

    #TODO
    #This 99 has to be changed to the number of waveforms in the file.
    #It is currently hardcoded to 99, because the files have 99 waveforms but for a smoother histogram
    #it is better to have more waveforms say 10e4 as I showed in the report.

    for q in range(1,99):

        baseline = np.mean(file_[:index_0, q])
        signal = file_[index_0:index_f+1, q]
        #This computes the area under the curve of the signal using the trapezoidal rule.
        #The area is divided by 50, which is the resistance in Ohms.
        area= np.abs((np.trapz(signal, times)) / 50 )
        df = df.append({'Waveform': q, 'Area': area}, ignore_index=True)

    return df

"""
There are implementations for different types of fits: double Gaussian and a Gaussian convoluted with a Poisson distribution, but only the simple Gaussian fit is currently used.
These additional fits were included after reading some articles that used them to model the SPE distribution. The idea was to explore these alternatives later on.
However, since we were never able to collect a proper SPE distribution, these fits were never actually used, and the corresponding code remains in the file unused for now.
"""

def poisson_convolved_gaussian(x, A, mu, Q0, gain, sigma, n_max=10):

    result = np.zeros_like(x)
    for n in range(n_max + 1):
        weight = (mu**n) * np.exp(-mu) / factorial(n)
        center = Q0 + n * gain
        gaussian = np.exp(-0.5 * ((x - center) / sigma)**2) / (sigma * np.sqrt(2 * np.pi))
        result += weight * gaussian
    return A * result


def double_gaussian(x, A0, mu0, sigma0, A1, mu1, sigma1):
    gauss0 = A0 * np.exp(-0.5 * ((x - mu0) / sigma0)**2)
    gauss1 = A1 * np.exp(-0.5 * ((x - mu1) / sigma1)**2)
    return gauss0 + gauss1

def gaussian(x, A0, mu0, sigma0):
    gauss0 = A0 * np.exp(-0.5 * ((x - mu0) / sigma0)**2)

    return gauss0 

def plot_and_compute_spe(areas):

    #TODO
    #20 bins seems to be a good number of bins for the histogram but it can be changed to a different number 
    # if needed, in that case you should change the number of bins in the line 139 and 151 as well.

    counts, bin_edges = np.histogram(areas, bins=20)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    A0_guess_g = max(counts)
    mu0_guess_g = bin_centers[np.argmax(counts)]
    sigma0_guess_g = np.std(areas) / 10
    # A1_guess_g = A0_guess_g / 2
    # mu1_guess_g = mu0_guess_g + (np.std(areas) / 3)
    # sigma1_guess_g = sigma0_guess_g

    p0_g = [A0_guess_g, mu0_guess_g, sigma0_guess_g]


    popt_g, pcov_g = curve_fit(gaussian, bin_centers, counts, p0=p0_g)


    A0_g, mu0_g, sigma0_g = popt_g
    #gain_g = mu1_g - mu0_g


    print(f"\nResults of Gaussian fit:")
    print(f"\n Mean (mu0): {mu0_g:.2e} C")
   # print(f"SPE mean (mu1): {mu1_g:.2e} C")
    print(f"Sigma (sigma0): {sigma0_g:.2e} C")
    #print(f"SPE sigma (sigma1): {sigma1_g:.2e} C")
    print(f"Amplitude (A0): {A0_g:.2e}")
    #print(f"SPE amplitude (A1): {A1_g:.2e}")
    #print(f"Gain: {gain_g:.2e}")

    residuals_g = counts - gaussian(bin_centers, *popt_g)
    r2_g = 1 - (np.sum(residuals_g**2) / np.sum((counts - np.mean(counts))**2))
    print(f"R² of fit: {r2_g:.2e}")


    # A_guess = max(counts)
    # mu_guess = 0.5
    # Q0_guess = bin_centers[np.argmax(counts)]
    # gain_guess = np.std(areas) / 2
    # sigma_guess = np.std(areas) / 10

    # p0 = [A_guess, mu_guess, Q0_guess, gain_guess, sigma_guess]


    # popt, pcov = curve_fit(poisson_convolved_gaussian, bin_centers, counts, p0=p0)

    # A, mu, Q0, gain, sigma = popt


    # print(f"\nResults of Poisson*Gaussian fit:")
    # print(f" \n Amplitude (A): {A:.2e}")
    # print(f"Mean number of photoelectrons (mu): {mu:.2e}")
    # print(f"Pedestal position (Q0): {Q0:.2e} C")
    # print(f"Gain: {gain:.2e} ")
    # print(f"Sigma: {sigma:.2e} ")

    x_fit = np.linspace(min(areas), max(areas), 20)
    # y_fit = poisson_convolved_gaussian(x_fit, *popt)

    # residuals = counts - y_fit
    # r2 = 1 - np.sum(residuals**2) / np.sum((counts - np.mean(counts))**2)

    # print(f"R² of fit: {r2:.2e}")

    plt.figure(figsize=(8,6))
    gs = GridSpec(2, 1, height_ratios=[3, 1])
    ax0 = plt.subplot(gs[0])

    ax0.hist(areas, bins=20, alpha=0.6, label='Data')

    ax0.plot(x_fit, gaussian(x_fit, *popt_g), 'b--', label='Gaussian Fit')
    ax0.axvline(mu0_g, color='b', linestyle=':', label='Mean Gaussian Fit')
    # ax0.axvline(mu1_g, color='b', linestyle='-', label='SPE mean Gaussian Fit')

    #ax0.plot(x_fit, y_fit, 'r--', label='Poisson ⊗ Gaussian Fit')
    #ax0.axvline(Q0, color='r', linestyle=':', label='Pedestal Poisson ⊗ Gaussian')
    #ax0.axvline(Q0 + gain, color='r', linestyle='-', label='1 p.e. Poisson ⊗ Gaussian Fit')
    ax0.set_ylabel("Counts")
    ax0.legend()

    ax1 = plt.subplot(gs[1], sharex=ax0)
    ax1.errorbar(x_fit, residuals_g, fmt='o', markersize=3, color='blue', capsize=2)
    ax1.errorbar(x_fit, residuals_g, fmt='-', markersize=3, color='blue', capsize=2)
    # ax1.errorbar(x_fit, residuals, fmt='o', markersize=3, color='red', capsize=2)
    # ax1.errorbar(x_fit, residuals, fmt='-', markersize=3, color='red', capsize=2)
    ax1.axhline(0, color='gray', linestyle='--')
    ax1.set_xlabel("Integrated Charge [C]")
    ax1.set_ylabel("Residuals")
    ax1.grid(True)


    plt.tight_layout()
    plt.show();