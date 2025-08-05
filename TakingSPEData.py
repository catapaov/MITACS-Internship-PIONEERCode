import pyvisa as visa
import numpy as np
import pandas as pd
import time
from datetime import date
import os, sys

""""This is Meghan's code to take data from the oscilloscope and save it as a CSV file. 
I added a small safety check (lines 191–200) to stop data taking if it takes too long,
originally, the code could get stuck in an infinite loop.
We later found and fixed the real issue, but I left the check in (currently commented) just in case it's useful in the future. 
It's commented out now because for the SPE check we need 10e4 waveforms for a smooth histogram, which takes longer than the previous 100.
 Feel free to leave it commented or enable it as needed.
 """

#BA0131
#BA030

############### filename info ##################
PMTnumber = 'BA0131'
PMT_voltage = 1300 #in Vs
LED_wavelength = 235 #in nm
laser_status = 'ON' #set as ON or OFF depending on if this is a laser or background dataset

#this is the name of the file-
Filename = f'SPEdataTest_{PMTnumber}-{PMT_voltage}V_L-{LED_wavelength}_LASER-{laser_status}'

#how many samples (light flashes) you want to save
num_waveforms = 10000

################### setup ########################

#oscilloscope address, make sure scope is connected to ethernet port
oscilloscope_address = 'TCPIP::142.90.115.154::inst0::INSTR'

#oscilloscope_address = 'TCPIP::142.90.100.19::inst0::INSTR'

#channel to readout
channel_id = 'CH1'

#file saving info, will save to a folder called SPE_PMT_data/{date}
today = date.today()
Date = today.strftime('%y-%m-%d')

folder = f'./SPE_PMT_data/{Date}/'

isExist = os.path.exists(folder)
if not isExist:
    os.makedirs(folder)
    print(f'Creating folder: {folder}')

name = f'{folder}{Filename}_{channel_id}'

################# functions to process & save data #####################

def convertToWave(datac, scal_info):
    """
    Converts raw data that is output by query_binary_values to the corrected
    time and voltage steps, and returns them as a 2D np.array. This requires the 
    scaling information from the scope, read in through the dictionary scal_info.

    input:
        datac: 1D array that is the output from query_binary_values()
        scal_info: dictionary with scope scaling details
    output:
        2D np.array of the converted data: [[time in s,] [voltages in V]]
    """

    x = []
    y = []
    for i in range(0,len(datac)):
        x.append((i-(len(datac)*(scal_info['HPos']/100)))* scal_info['xincr'] + scal_info['HDelay'])
        y.append(((datac[i]-scal_info['yoff']) * scal_info['ymult']) + scal_info['yzero'])
        
    return np.array([x,y])

def collect_waveform(oscilloscope):
    '''
    Collect and return a converted waveform from the scope using convertToWave

    input:
        oscilloscope: object holding the connection to the oscilloscope to read from
    output:
        2D converted array of scope data
    '''
    
    #configure and query waveform data
    oscilloscope.write('DAT:ENC RPB')  #set data encoding to binary
    oscilloscope.write('DAT:WID 1')    #set data width to 1 byte
    oscilloscope.write('DAT:STAR 1')   #set start of data to first byte

    dataLength = 1000 #this is how many datapoints you want to collect in each waveform, limited by record length set on scope so check this

    oscilloscope.write(f'DAT:STOP {dataLength}') #set end of data to 10000th byte
    oscilloscope.write(f"DATA:SOURCE {channel_id}") #change channel source being used

    raw_waveform_data = oscilloscope.query_binary_values('CURV?', datatype='B', container=np.array)

    #get data for converting the waveform
    info = oscilloscope.query('WFMOutpre?') 
    info = info.split(",")
    infoSplit = info[-1].split(";")
    xincr = float(infoSplit[5])

    #Vertical scale multiplying factor
    ymult = float(infoSplit[9])
    #Vertical position of the source waveform in digitizing levels
    yoff = float(infoSplit[10])
    yzero = float(infoSplit[11])
    Hscale = float(oscilloscope.query("HOR:SCA?"))
    HDelay = float(oscilloscope.query("HORizontal:DELay:TIMe?"))
    HPos = float(oscilloscope.query("HORIZONTAL:POSITION?"))

    # get information needed for convertToWave function
    scal_info = {     
        'xincr': xincr,
        'ymult': ymult, 
        'yoff': yoff, 
        'yzero': yzero,
        'Hscale': Hscale, 
        'HDelay': HDelay, 
        'HPos': HPos
    }

    #convert to [time [s], voltage [V]] using the scope settings
    waveform_data = convertToWave(raw_waveform_data, scal_info)

    return waveform_data

def save_all_waveforms(all_waveforms, name):
    '''
    Save all waveforms to a single CSV file - time in first column, each waveform in its own column

    input:
        all_waveforms: a list of all of the waveforms collected in a single run
        name: str of full path name of file to save to, without file extension
    output:
        none
    '''

    csv_file_path = f'{name}.csv'

    time_axis = all_waveforms[0][0]  #define the timing as the first row of the first waveform
    data = np.vstack([time_axis] + [wf[1] for wf in all_waveforms]) #put each waveform together sequentially
    column_data = data.T  #change it into column format
    headers = ['time (s)'] + [f'waveform_{i}' for i in range(len(all_waveforms))]   #define headers for each column
    
    df = pd.DataFrame(column_data, columns=headers) #make into dataframe
    df.to_csv(csv_file_path, index=False)    #change to csv
    print(f"Saved all waveforms to {csv_file_path}")

################# main ######################

rm = visa.ResourceManager('@py')

all_waveforms = []       #list to hold the waveforms in as the thing runs

try:
    #open a connection to the oscilloscope
    scope = rm.open_resource(oscilloscope_address)

    #query the instrument's identification
    idn = scope.query('*IDN?')
    print(f"Instrument Identification: {idn}")

    #put scope into continuous trigger
    scope.write('ACQuire:STOPAfter RUNSTop')
    
    scope.write('TRIGger:A:TYPe EDGE') #set to edge trigger
    scope.write('TRIGger:A:EDGE:SOUrce AUX')  #specifies that this is externally triggered (scope trigger port is AUX)
    #CHECK RISE OR FALL TO SEE WHEN LED FLASHES (ie. beginning or end of square wave from function generator)
    scope.write('TRIGger:A:EDGE:SLOpe RISE')

    SquareWave_height = 1 #height of square wave on function generator in V

    scope.write(f'TRIGger:A:LEVel:AUXin {SquareWave_height}') #says the trigger level is coming from AUX and it's height is X volts

    print('Trigger set to: ', scope.query('TRIGger:A:EDGE:SLOpe?').rstrip(), scope.query(f'TRIGger:A:LEVel:AUXin?').rstrip(), 'V')

    waveform_id = 0 #initialize number of waveforms to be zero

    #start counting time 

    t_0= time.time()

    t_max=120

    while waveform_id < num_waveforms:

        # if abs(time.time()-t_0)> t_max:
        #     print("t_max exceeded (1)")
        #     break

        #start acquiring mode
        scope.write('ACQuire:STATE RUN')

        # while True:
        #    if abs(time.time()-t_0)> t_max:
        #     print("t_max exceeded (2)")
        #     break
        #    waiting = int(scope.query('ACQ:STATE?').rstrip()) 
        #    if waiting == 0:
        #        break
           
        #    #this is just to not continually query, change this depending on how fast function generator is
        #    time.sleep(0.0005) #script check oscilloscope for trigger every 0.5ms

        trigger = scope.query('TRIGGER:STATE?').rstrip()
        
        if waveform_id % 1000 == 0: #check status every 1000 waveforms
            print(f"[{waveform_id}] Triggered: {trigger}")

        waveform = collect_waveform(scope)
        all_waveforms.append(waveform)

        waveform_id += 1

        if waveform_id % 1000 == 0:
            print(f"Collected waveform {waveform_id}/{num_waveforms}")

    save_all_waveforms(all_waveforms, name)

finally:
    print('Data taking complete')
    print(f'{waveform_id} data files saved: {name}.csv')
    scope.close()
    rm.close()

        

