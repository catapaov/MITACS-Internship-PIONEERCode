import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


"""This script plots the linearity of the PMT response by measuring the peak height of the PMT pulse.

It creates a plot per PMT and in a same plot it compares the response of different LEDs."""


#Adjust the date, PMT_IDs, LED_IDs and voltage settings as needed.
#PMT_IDs, and LED_IDs are lists to make it easier to loop over multiple PMTs or LEDs if needed.
#Make sure the paths to the data files are correct, change on line 40 to read the correct files


date = '25-07-16'
PMT_IDs = ['BA0131','BA0030']

LED_IDs = ["235","308"]

t0, t1   = 0.38e-7, 2e-7
tol = 1e-9

colors = ['red', 'blue', 'green', 'orange', 'purple', 
          'cyan', 'magenta', 'brown', 'gold', 'teal']
            

for PMT_ID in PMT_IDs:

    c=0
    plt.figure(figsize = (8,6))

    for LED_ID in LED_IDs:

        if LED_ID =="308":
            #t1 = 4e-7
            t1 = 3.5e-7
        peak_data = []

        for set_voltage in range(500,1350,100):

            all_voltages = []
            #TODO
            #Keep an eye on the file path, it may need to be adjusted
            file = f'/home/aovelencio/PMTTesting/SPE_PMT_data/{date}/SPEdataTest_{PMT_ID}-{set_voltage}V_L-{LED_ID}_LASER-ON_CH1.csv'
            file_ = pd.read_csv(file, delimiter=',', header=0, skiprows=1)
            file_ = np.array(file_)

            times = file_[:,0]
            index_0  = np.searchsorted(times, t0 - tol, side='left')
            index_f  = np.searchsorted(times, t1 + tol, side='right') - 1

            for q in range(1,99):
                voltages = file_[:,q]
                voltages = voltages[index_0:index_f+1]
                all_voltages.append(voltages)

            average_pulse = np.mean(all_voltages, axis=0)
            peak_voltage = np.min(average_pulse)
            peak_data.append((set_voltage, peak_voltage))

        peak_data = np.array(peak_data)

        HV = peak_data[:,0]
        peaks = np.abs(peak_data[:,1])

        plt.plot(HV, peaks, 'o', label=f'Measured Peaks LED_{LED_ID}',color=colors[c])
        # plt.plot(HV, peaks, '-',color=colors[c])

        c+=1

    plt.legend()
    plt.title(f'Signal Peak Height vs. HV Supply for PMT {PMT_ID}')
    plt.xlabel('High Voltage Supplied (V)')
    plt.ylabel('Abs. Peak Height (V)')
    plt.tight_layout()
    #TODO
    #Change the path to save the figure as needed
    plt.savefig(f'/home/aovelencio/PMTTesting/SPE_PMT_data/{date}/FIXED_linearity_PMT_{PMT_ID}.png')
    plt.close()
