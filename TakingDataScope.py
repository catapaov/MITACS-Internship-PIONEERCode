import pyvisa as visa
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from time import *
from datetime import date
import os, sys


"""
This is Emma's code for taking data from oscilloscope"""

################ file name to change & data taking time ################
PMTnumber = "BA0004"
PMT_voltage = 1300#in V
LED_wavelength = 255 #in nm
LED_ADC_value = 1871 #the value that hitting 'Q' on the LED control terminal outputs 

#naming of files created, a _X_ will be appended for each file
Filename = f"PMT_dataTest_{PMTnumber}-{PMT_voltage}V_L-{LED_wavelength}_ADC{LED_ADC_value}"

#or hardcoding the name if you want
# Filename = f"PMT_noLEDon"
# Filename = f"PMT_dataTest_TB0412-740.6V_L-235_ADC1534"

#how long to take data for, in seconds
dataTakingTime = 60 #s


################ set up ################

# Replace 'USB0::0x0699::0x0363::C065087::INSTR' with your instrument's VISA address
oscilloscope_address = 'TCPIP::142.90.115.154::inst0::INSTR'

#the channel to read out
channel_id = "CH1"

#data to save data to - default is todays date
today = date.today()
d1 = today.strftime("%y-%m-%d")

# folder = "./example_data/Feb2/"
folder = f"./PMT_data/{d1}/"

isExist = os.path.exists(folder)
if not isExist:
   # Create a new directory because it does not exist
   os.makedirs(folder)
   print(f"Creating folder: {folder}")


#putting all the naming and folder together
name = f"{folder}{Filename}_{channel_id}"
name2 = f"{folder}{Filename}_TRIG_{channel_id}"


################ functions to save data ################
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


def saveData(oscilloscope, name, number):
    """
    input:
        oscilloscope: object holding the connection to the oscilloscope to read from
        name: str of full path name of file to save to, without file type extension
        number: int/str of the data set number to added to the end of the name
    output:
        None
    """
    # Save the waveform data to a CSV file
    csv_file_path = f'{name}_waveform_{number}.csv'
    csv_file_path_raw = f'{name}_waveform_{number}_raw.csv'

    # Configure and query waveform data
    oscilloscope.write('DAT:ENC RPB')  # Set data encoding to binary
    oscilloscope.write('DAT:WID 1')    # Set data width to 1 byte
    oscilloscope.write('DAT:STAR 1')   # Set start of data to first byte
    dateLength = 10000 #but will be limited by the record length set on the scope really
    oscilloscope.write(f'DAT:STOP {dateLength}') # Set end of data to 10,000th byte
    oscilloscope.write(f"DATA:SOURCE {channel_id}") #change channel source being used

    raw_waveform_data = oscilloscope.query_binary_values('CURV?', datatype='B', container=np.array)

    #get data for converting the waveform
    info = oscilloscope.query('WFMOutpre?') 
    info = info.split(",")
    VerticalScale = info[2]
    VerticalPos = info[3]
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

    #Other info for the header
    Vunits = infoSplit[8]
    Hunits = infoSplit[4]
    waveType = infoSplit[13]
    pointsFormat = infoSplit[2]
    ProbeA = int(float(oscilloscope.query("TRIGger:EXTernal:PRObe?").rstrip()))
    firmware = float(idn.split()[1].split("v")[1])

    headerInfo = {
        'Model': idn.strip(),
        'Channel': channel_id,      
        'xincr': xincr,
        'ymult': ymult, 
        'yoff': yoff, 
        'yzero': yzero,
        'Hscale': Hscale, 
        'HDelay': HDelay, 
        'HPos': HPos
    }

    headerInfo_forCSV = {
        'Model': idn.split(",")[1],
        'Firmware Version': firmware,    
        '':'',  
        'Waveform Type': waveType,
        'Point Format': pointsFormat, 
        'Horizontal Units': Hunits.split('"')[1], 
        'Horizontal Scale': Hscale,
        'Horizontal Delay': HDelay, 
        'Sample Interval': xincr, 
        'Record Length': dateLength,
        'Gating': "NA",
        'Probe Attenuation': ProbeA,
        'Vertical Units': Vunits.split('"')[1],
        'Vertical Offset': yzero,
        'Vertical Scale': VerticalScale,
        'Vertical Position': 'NA'
    }
    

    #convert to [time [s], voltage [V]] using the scope settings
    waveform_data = convertToWave(raw_waveform_data, headerInfo)

    #save just the raw reading
    np.savetxt(csv_file_path_raw, raw_waveform_data, delimiter=",")

    #and the fully converted waveform
    #header info
    (pd.DataFrame.from_dict(data=headerInfo_forCSV, orient='index').to_csv(csv_file_path, header=False, mode='w'))

    #the data
    with open(csv_file_path,'a') as f:
        subheader = np.array([["",""], ["",""], ["",""], 
                              ["Label",""],
                              ["TIME",channel_id]])

        np.savetxt(f,subheader, delimiter=",", fmt="%s")
        np.savetxt(f,waveform_data.T, delimiter=",")

    print(f"Waveform data saved to {csv_file_path}")

    return


################ main ################

# Create a VISA resource manager
rm = visa.ResourceManager('@py')
data_number = 0

try:
    # Open a connection to the oscilloscope
    scope = rm.open_resource(oscilloscope_address)

    # Query the instrument's identification
    idn = scope.query('*IDN?')
    print(f"Instrument Identification: {idn}")

    #could put acq and trigger set up here automatically
    #set scope to single SEQ mode
    scope.write("ACQuire:STOPAfter SEQuence")
    #Specifies that this will be an edge trigger 
    scope.write("TRIGger:A:TYPe EDGE")
    # Specifies the channel as the source waveform.
    scope.write(f"TRIGger:A:EDGE:SOUrce {channel_id}")
    scope.write("TRIGger:A:EDGE:SLOpe FALL")

    # Specifies (1.4) volts as the threshold level.
    VsetTrig = -1450.0 #mV 
    scope.write(f"TRIGger:A:LEVel:{channel_id} {VsetTrig/1000}")

    print("Trigger set to: ", scope.query("TRIGger:A:EDGE:SLOpe?").rstrip(), 
                    scope.query(f"TRIGger:A:LEVel:{channel_id}?").rstrip(), "V")

    end_time = time() + (dataTakingTime)
    print(f"Taking data for {dataTakingTime} s ({dataTakingTime/60:.2} min)")

    while time() < end_time:
        #start the acquiring mode
        scope.write("ACQ:STATE RUN")
        waiting = 1
        looptime = time()
        triggertime = time()
        # print(end_time, triggertime)

        # wait here until trigger received or time ends
        while (waiting == 1):
            #returns 1 if in acquiring mode, 0 if stopped
            waiting = int(scope.query("ACQ:STATE?"))
            # print("waiting...", waiting)

            #capture the trigger time - this is not being used anywhere cause I don't
            # really think we care about the exact timing right now, but could be added in
            #later
            if waiting == 0:
                # Saved the data as CSV file if the acquisition has stopped
                trigger = scope.query("TRIGGER:STATE?").rstrip()
                print(f"acquisition stopped, {trigger}")
                saveData(scope, name, data_number)
                data_number += 1 #add one for the next data set
                # triggertime = time()

            looptime = time()
            if looptime > end_time:
                if scope.query("TRIGGER:STATE?").rstrip() == 'REA':
                    print("No trigger event for finale capture")
                break
        
            #print status of the trigger state, and the acquisition date
            # print(scope.query("TRIGGER:STATE?").rstrip(), scope.query("ACQ:STATE?").rstrip())

        #this seems to only work for very consistent waveforms, and I don't really know why
        # Saved the data as CSV file if the trigger has been triggered        
        # if scope.query("TRIGGER:STATE?").rstrip() == "TRIG":
        #     print(f"{channel_id} triggered")
        #     #call function that actually does the savings

        #     saveData(scope, name2, data_number)
        #     data_number += 1 #add one for the next data set

finally:
    print("Data taking complete.")
    print(f"{data_number} data files saved: {name}_waveform_X.csv")
    # Close the connection    
    scope.close()
    rm.close()
