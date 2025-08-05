import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

"""
This script plots the average pulse from multiple waveform files for a given PMT and voltage setting.
"""


#Here you can set the parameters
#Adjust the date, PMT_IDs, LED_IDs, time window (t0, t1), and voltage settings as needed.
#PMT_IDs, and LED_IDs are lists to make it easier to loop over multiple PMTs or LEDs if needed.
#Make sure the paths to the data files are correct, change on line 40 to read the correct files 
# and on line 66 to save the plots in the correct location.

#t0 is the time at which the PMT pulse starts, and t1 is the time point when the pulse ends. 

date = '25-07-24'
PMT_IDs = ['BA0100']
LED_IDs = ["235"]
t0, t1   = 1.5e-7, 4e-7
tol = 1e-9

colors = ['red', 'blue', 'green', 'orange', 'purple', 
          'cyan', 'magenta', 'brown', 'gold', 'teal']

R=50 # Resistance in Ohms

            

for PMT_ID in PMT_IDs:

    plt.figure(figsize = (8,6))
#TODO
#Do not forget to change the voltage range and step as needed
    for set_voltage in range(1300,1350,100):
        c=0
        for LED_ID in LED_IDs:

            if LED_ID =="308":
                #t1 = 4e-7
                t1 = 3.5e-7
            all_voltages = []
            #TODO
            file = f'/home/aovelencio/PMTTesting/SPE_PMT_data/{date}/SPE_CHECK_200ns_7_VSPEdataTest_{PMT_ID}-{set_voltage}V_L-{LED_ID}_LASER-ON_CH1.csv'
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
            plt.plot(times, average_pulse, 'o', label=f'LED_{LED_ID} ON',color=colors[c], markersize=3)
            # plt.plot(HV, areas, '-',color=colors[c])

            c+=1

        plt.legend()
        plt.xlabel('Time (s)')
        plt.ylabel('Voltage (V)')
        plt.title(f'PMT {PMT_ID} at {set_voltage} V')
        plt.tight_layout()
        #TODO
        plt.savefig(f'/home/aovelencio/PMTTesting/SPE_PMT_data/{date}/200ns_7V_TRIAL_Pulse_PMT_{PMT_ID}_{set_voltage}.png')
        plt.close()
