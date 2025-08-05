import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

"""This script plots the charge of the PMT response by measuring the area under the PMT pulse.

It creates a plot per PMT and in a same plot it compares the response of different LEDs."""


#Adjust the date, PMT_IDs, LED_IDs and voltage settings as needed.
#PMT_IDs, and LED_IDs are lists to make it easier to loop over multiple PMTs or LEDs if needed.
#Make sure the paths to the data files are correct, change on line 44 to read the correct files

date = '25-07-16'
PMT_IDs = ['BA0131','BA0030']

LED_IDs = ["235","308"]

t0, t1   = 0.38e-7, 2e-7
tol = 1e-9

colors = ['red', 'blue', 'green', 'orange', 'purple', 
          'cyan', 'magenta', 'brown', 'gold', 'teal']

R=50 # Resistance in Ohms

            

for PMT_ID in PMT_IDs:

    c=0
    plt.figure(figsize = (8,6))

    for LED_ID in LED_IDs:

        if LED_ID =="308":
            #t1 = 4e-7
            t1 = 3.5e-7
        area_data = []

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
            times = times[index_0:index_f+1]

            for q in range(1,99):
                voltages = file_[:,q]
                voltages = voltages[index_0:index_f+1]
                all_voltages.append(voltages)

            average_pulse = np.mean(all_voltages, axis=0)
            # Here we calculate the area under the pulse and divide by R to get the charge
            area = (np.trapz(average_pulse, times))/R
            area_data.append((set_voltage, area))

        area_data = np.array(area_data)

        HV = area_data[:,0]
        areas = np.abs(area_data[:,1])

        plt.plot(HV, areas, 'o', label=f'Measured Charge LED_{LED_ID}',color=colors[c])
        # plt.plot(HV, areas, '-',color=colors[c])

        c+=1

    plt.legend()
    plt.title(f'Abs. Charge vs. HV Supply for PMT {PMT_ID}')
    plt.xlabel('High Voltage Supplied (V)')
    plt.ylabel('Abs. Charge (C)')
    plt.tight_layout()
    #TODO
    #Change the path to save the figure as needed
    plt.savefig(f'/home/aovelencio/PMTTesting/SPE_PMT_data/{date}/FIXED_Charge_PMT_{PMT_ID}_{LED_ID}.png')
    plt.close()
