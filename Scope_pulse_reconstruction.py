import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os, sys


"""This script plots every waveform for a given PMT and voltage setting. 
It is useful to check the shape of the pulses and to see if there are any issues with the data.

It saves the plots in a folder, say for each PMT it creates a folder with the PMT ID, inside it creates a folder for each LED ID, 
and inside that folder it creates a folder for each voltage setting."""


#Adjust the date, PMT_IDs, LED_IDs and voltage settings as needed.
#PMT_IDs, and LED_IDs are lists to make it easier to loop over multiple PMTs or LEDs if needed.
#Make sure the paths to the data files are correct, change on line 42 to read the correct files



date = '25-07-24'
PMT_IDs = ['BA0100']
LED_IDs = ["235"]

for PMT_ID in PMT_IDs:
    isExist = os.path.exists(f'/home/aovelencio/PMTTesting/SPE_PMT_data/{date}/{PMT_ID}')
    if not isExist:
        os.makedirs(f'/home/aovelencio/PMTTesting/SPE_PMT_data/{date}/{PMT_ID}')

    for LED_ID in LED_IDs:
        isExist = os.path.exists(f'/home/aovelencio/PMTTesting/SPE_PMT_data/{date}/{PMT_ID}/{LED_ID}')
        if not isExist:
            os.makedirs(f'/home/aovelencio/PMTTesting/SPE_PMT_data/{date}/{PMT_ID}/{LED_ID}')
        #TODO
        #t0 is the time at which the PMT pulse starts, and t1 is the time point when the pulse ends. 

        t0, t1   = 0, 1.5e-7
        tol = 1e-9

        if LED_ID =="308":
            t1 = 3.5e-7
        #TODO
        #Do not forget to change the voltage range and step as needed
        for set_voltage in range(1300,1350,100):

            isExist = os.path.exists(f'/home/aovelencio/PMTTesting/SPE_PMT_data/{date}/{PMT_ID}/{LED_ID}/{set_voltage}')
            if not isExist:
                os.makedirs(f'/home/aovelencio/PMTTesting/SPE_PMT_data/{date}/{PMT_ID}/{LED_ID}/{set_voltage}')
        #TODO
        #Keep an eye on the file path, it may need to be adjusted
            file = f'/home/aovelencio/PMTTesting/SPE_PMT_data/{date}/SPE_CHECK_13_6_VSPEdataTest_{PMT_ID}-{set_voltage}V_L-{LED_ID}_LASER-ON_CH1.csv'
            file_ = pd.read_csv(file, delimiter=',', header=0, skiprows=1)
            file_ = np.array(file_)
            times = file_[:,0]

            index_0 = np.where(times == t0)[-1]
            index_f = np.where(times == t1)[0]

            #first element ≥ t0 − tol
            index_0  = np.searchsorted(times, t0 - tol, side='left')

            #first element  > t1 + tol  → subtract 1 to get the last ≤ t1
            index_f  = np.searchsorted(times, t1 + tol, side='right') - 1

            times = times[index_0:index_f+1]


            for i in range(1,100):
                plt.figure(figsize = (8,6))
                voltages = file_[:,i]
                voltages = voltages[index_0:index_f+1]

                #plt.plot(times, voltages,'o',markersize=3)
                plt.plot(times, voltages,'-')

                plt.xlabel('Time (s)')
                plt.ylabel('Voltage (V)')
                plt.title(f'PMT {PMT_ID} at {set_voltage} V\n LED {LED_ID}')
                plt.savefig(f'/home/aovelencio/PMTTesting/SPE_PMT_data/{date}/{PMT_ID}/{LED_ID}/{set_voltage}/{i}.png')
                plt.close()



