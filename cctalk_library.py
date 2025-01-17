import sys
import serial
import time
import csv
import PySimpleGUI as sg
#import numpy as np
#import pandas as pd


def comms(port, baud, timeout):             # Serial Communication with VAL364
    try:                                        
        ser=serial.Serial(port, baud, timeout=timeout)
        print("Connected")
        return(ser)

    except:
        print("Connection Error")

def com_window():
    gui_flag = True
    sg.theme('DarkAmber')
    layout = [  [sg.Text('COM port parameters')],
                [sg.Text('Enter COM port number:'), sg.InputText()],
                [sg.Button('Next'), sg.Button('Exit')] ]
    
    window = sg.Window('CX Backplane Data Collection', layout)

    while gui_flag:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            exit()
        
        elif event == 'Next':
            com_port = values[0]
            gui_flag = False
            window.close()

        else:
            continue

    return(com_port)

def tube_window(): 
    coin_count = []   
    
    gui_flag = True
    sg.theme('DarkAmber')
    layout = [  [sg.Text('Collected data will be located in the Users directory on the C drive')],
                [sg.Text('Enter Tube A value:'), sg.InputText()],
                [sg.Text('Enter Tube B value:'), sg.InputText()],
                [sg.Text('Enter Tube C value:'), sg.InputText()],
                [sg.Text('Enter Tube D value:'), sg.InputText()],
                [sg.Text('Enter Tube E value:'), sg.InputText()],
                [sg.Button('Start'), sg.Button('Exit')] ]
    
    window = sg.Window('CX Backplane Data Collection', layout)

    while gui_flag:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            exit()
        
        elif event == 'Start':
            for value in values:
                coin_count.append(int(values[value]))
            
            gui_flag = False
            window.close()

        else:
            continue

    return(coin_count)


    gui_flag = True
    sg.theme('DarkAmber')
    layout = [  [sg.Text('Remaing Coins In Tube')],
                [sg.Text('Tube A: ' + str(coin_count[0]))],
                [sg.Text('Tube B: ' + str(coin_count[1]))],
                [sg.Text('Tube C: ' + str(coin_count[2]))],
                [sg.Text('Tube D: ' + str(coin_count[3]))],
                [sg.Text('Tube E: ' + str(coin_count[4]))],
                [sg.Button('Stop')] ]
    
    window = sg.Window('CX Backplane Data Collection', layout)

    window.read(close = True)
    

class ccTalk_read():                        # Checking slave data
    '''
    This class takes recieved data from a slave device,
    cleans the data into a readable decimal format,
    and after checking the validity of the message,
    will return the recived message information.
    '''
    def __init__(self, msg):                    # Initialization
        self.msg = msg                              # This data variable should always be a byte array.
        self.decimal = self.hex_convert()           # Class will always convert byte array to hexidecimal to decimal.   


    def msg_check(self):                        # Checks the converted decimal array's CRC values
                                            
        self.address = self.decimal[0]  
        self.header = self.decimal[3]

        if self.decimal[1] == 0:                    # Checks if message has data to convert
            self.length = 0
            self.data = None
        else:
            self.length = self.decimal[1]
            self.data = self.decimal[4 : 4 + self.decimal[1]]     # data starts at the 4th byte and count from 4 + length of data.

                                                    # Extracted message parsed to ccTalk_msg.message() method 
                                                    # to generate a calculated message
        self.message = ccTalk_msg(self.address, self.length, self.header, self.data).message()

        if self.message == self.decimal:            # Compares extracted message(.decimal) to calculated message(.message)
            return(self.message)
        else:                                       # If comparision fails, the extracted message is wrong 
            print('CRC check failed')
            return(1)


    def hex_convert(self):                      # Conversion from byte array to hexidecimal list
        bite_array = list(self.msg.hex())   
    
        hex_array = []                              # Since the hexidecimal array is individual characters within a list
        array_count = 0                             # they must be appended into pairs of hexidecimal bytes
        loop_count = int(len(bite_array)/2) 
    
        for bit in range(loop_count):               # This loop takes 2 bytes of the hexidecimal list and appends them into hex_array
            hex_array.append(bite_array[array_count] + bite_array[array_count+1])
            array_count += 2
    
        dec_array = []                              # Conversion from hexidecimal array to decimal array
        array_count = 0
        loop_count = int(len(hex_array))

        for bit in range(loop_count):               # This loop takes the appended bytes from hex_array and applies decimal conversion
            dec_array.append(int(hex_array[array_count], 16))
            array_count += 1

        return(dec_array)                           # Return the decimal converted byte array


    def slave_msg_label(self):                  # Slave message identification
        header_types = {                            # Dictionary of responses                  
        '[1, 0, 48, 0, 55]' : "ACK",
        '[1, 0, 149, 5, 103]' : "NAK",
        '[1, 0, 246, 6, 87]' : "BUSY"
        }
        string_convert = str(self.decimal)          # String conversion for easier terminal readability
        return(header_types.get(string_convert))


class ccTalk_msg():                         # ccTalk message generator
    '''
    This class generates a ccTalk message in the form a decimal array,
    the input data required is only the: address, length of data, header and data,
    CRC is calculated within itself and will return the result in an array
    '''
    def __init__(self, address, length, header, data):  # Initialization
        self.address = address
        self.length = length                        # Class global variables
        self.header = header
        
        if data != None:                            # Checking if data is present
            if self.length > 1:                     # If there is more than 1 byte of data in the message
                self.data = []
                for bite in data:
                    self.data.append(bite)          # Individually append each data byte into a single message list
        
            else:
                self.data = data                    # Append a single byte of data into the message list
        
        else:
            self.data = data                        # Append datatype "None" into the global data variable
        
                   
    def message(self):                          # Message generation
        result = [] 
        result.append(self.address)                 # Append global class variables into a message list array
        result.append(self.length)
        
        crc_hex = self.crc_calculation()            # CRC calculation from global variables
        self.crc_lsb = int(crc_hex[1], 16)
        self.crc_msb = int(crc_hex[0], 16)
        
        result.append(self.crc_lsb)                 # Each 'result.append' is in order of the ccTalk protocol
        result.append(self.header)

        if self.data != None:                       # Checks if data is to be inserted in the message
            if self.length > 1:                     # If data is great than 1 byte, it needs to be extraced out of the
                for bite in self.data:              # generated data array and appended into message list array
                    result.append(bite)
        
            elif self.length == 1:                  # If data is a single byte append the single byte
                result.append(self.data[0])         # into the message list array
                                                    # If no data exists(None), do not append
        result.append(self.crc_msb)
            
        return result                               # Return generated message


    def crc_calculation(self):                  # 16-bit CRC calculation
        if self.data == None:                       # CRC calculation is dependant on if data is present or not
            array = [self.address, self.length, self.header]
        else:                                       # If data is present append the lists
            array = [self.address, self.length, self.header] + self.data


        crc = 0x0000                                # Initial CRC register
        poly = 0x1021                               # CRC polynomial

        ##############*CRC Algorithm*######################## Black box of unknown
        for bite in array:                                  #
            crc ^= (bite << 8) & 0xffff                     #
            for j in range(0, 8):                           #
                if crc & 0x8000:                            #
                    crc = ((crc << 1) ^ poly) & 0xffff      #
                else:                                       #
                    crc <<= 1                               #
                    crc &= 0xffff                           # 
        ##################################################### Result is in Decimal request Hex conversion        
        
        hex = '{0:x}'.format(crc)                   # I assume hexidecimal formatting      
        hex = (4 - len(hex)) * '0' + hex
        hex_convert = list(hex)                     # Place formatted data into a list
        crc_array = [hex_convert[0] + hex_convert[1], hex_convert[2] + hex_convert[3]] # [LSB, MSB] string clean up
        
        return(crc_array)                           # Return calculated CRC values                                          


    def host_msg_label(self):                   # Host message identificaion
        header_types = {                            # Dictionary of responses
        255 : 'Factory set:up and test',
        254 : 'Simple poll',
        253 : 'Address poll',
        252 : 'Address clash',
        251 : 'Address change',
        250 : 'Address random',
        249 : 'Request polling priority',
        248 : 'Request status',
        247 : 'Request variable set',
        246 : 'Request manufacturer id',
        245 : 'Request equipment category id',
        244 : 'Request product code',
        243 : 'Request database version',
        242 : 'Request serial number',
        241 : 'Request software revision',
        240 : 'Test solenoids',
        239 : 'Operate motors',
        238 : 'Test output lines',
        237 : 'Read input lines',
        236 : 'Read opto states',
        235 : 'Read last credit or error code',
        234 : 'Issue guard code',
        233 : 'Latch output lines',
        232 : 'Perform self:check',
        231 : 'Modify inhibit status',
        230 : 'Request inhibit status',
        229 : 'Read buffered credit or error codes',
        228 : 'Modify master inhibit status',
        227 : 'Request master inhibit status',
        226 : 'Request insertion counter',
        225 : 'Request accept counter',
        224 : 'Dispense coins',
        223 : 'Dispense change',
        222 : 'Modify sorter override status',
        221 : 'Request sorter override status',
        220 : 'One:shot credit',
        219 : 'Enter new PIN number',
        218 : 'Enter PIN number',
        217 : 'Request payout high / low status',
        216 : 'Request data storage availability',
        215 : 'Read data block',
        214 : 'Write data block',
        213 : 'Request option flags',
        212 : 'Request coin position',
        211 : 'Power management control',
        210 : 'Modify sorter paths',
        209 : 'Request sorter paths',
        208 : 'Modify payout absolute count',
        207 : 'Request payout absolute count',
        206 : 'Empty payout',
        205 : 'Request audit information block',
        204 : 'Meter control',
        203 : 'Display control',
        202 : 'Teach mode control',
        201 : 'Request teach status',
        200 : 'Upload coin data',
        199 : 'Configuration to EEPROM',
        198 : 'Counters to EEPROM',
        197 : 'Calculate ROM checksum',
        196 : 'Request creation date',
        195 : 'Request last modification date',
        194 : 'Request reject counter',
        193 : 'Request fraud counter',
        192 : 'Request build code',
        191 : 'Keypad control',
        190 : 'Request payout status',
        189 : 'Modify default sorter path',
        188 : 'Request default sorter path',
        187 : 'Modify payout capacity',
        186 : 'Request payout capacity',
        185 : 'Modify coin id',
        184 : 'Request coin id',
        183 : 'Upload window data',
        182 : 'Download calibration info',
        181 : 'Modify security setting',
        180 : 'Request security setting',
        179 : 'Modify bank select',
        178 : 'Request bank select',
        177 : 'Handheld function',
        176 : 'Request alarm counter',
        175 : 'Modify payout float',
        174 : 'Request payout float',
        173 : 'Request thermistor reading',
        172 : 'Emergency stop',
        171 : 'Request hopper coin',
        170 : 'Request base year',
        169 : 'Request address mode',
        168 : 'Request hopper dispense count',
        167 : 'Dispense hopper coins',
        166 : 'Request hopper status',
        165 : 'Modify variable set',
        164 : 'Enable hopper',
        163 : 'Test hopper',
        162 : 'Modify inhibit and override registers',
        161 : 'Pump RNG',
        160 : 'Request cipher key',
        159 : 'Read buffered bill events',
        158 : 'Modify bill id',
        157 : 'Request bill id',
        156 : 'Request country scaling factor',
        155 : 'Request bill position',
        154 : 'Route bill',
        153 : 'Modify bill operating mode',
        152 : 'Request bill operating mode',
        151 : 'Test lamps',
        150 : 'Request individual accept counter',
        149 : 'Request individual error counter',
        148 : 'Read opto voltages',
        147 : 'Perform stacker cycle',
        146 : 'Operate bi:directional motors',
        145 : 'Request currency revision',
        144 : 'Upload bill tables',
        143 : 'Begin bill table upgrade',
        142 : 'Finish bill table upgrade',
        141 : 'Request firmware upgrade capability',
        140 : 'Upload firmware',
        139 : 'Begin firmware upgrade',
        138 : 'Finish firmware upgrade',
        137 : 'Switch encryption code',
        136 : 'Store encryption code',
        135 : 'Set accept limit',
        134 : 'Dispense hopper value',
        133 : 'Request hopper polling value',
        132 : 'Emergency stop value',
        131 : 'Request hopper coin value',
        130 : 'Request indexed hopper dispense count',
        129 : 'Read barcode data',
        128 : 'Request money in',
        127 : 'Request money out',
        126 : 'Clear money counters',
        125 : 'Pay money out',
        124 : 'Verify money out',
        123 : 'Request activity register',
        122 : 'Request error status',
        121 : 'Purge hopper',
        120 : 'Modify hopper balance',
        119 : 'Request hopper balance',
        118 : 'Modify cashbox value',
        117 : 'Request cashbox value',
        116 : 'Modify real time clock',
        115 : 'Request real time clock',
        114 : 'Request USB id',
        113 : 'Switch baud rate',
        112 : 'Read encrypted events',
        111 : 'Request encryption support',
        110 : 'Switch encryption key',
        109 : 'Request encrypted hopper status',
        108 : 'Request encrypted monetary id',
        107 : "Operate escrow",
        106 : 'Request escrow status',
        105 : 'Data stream',
        104 : 'Request service status',
        4 : 'Request comms revision',
        3 : 'Clear comms status variables',
        2 : 'Request comms status variables',
        1 : 'Reset device',
        0 : 'Reply'
        }
        return(header_types.get(self.header))


class ccTalk_write():                       # Master command label to decimal conversion
    '''
    This class generates ccTalk parameters from human commands.
    Commands are currently implimented within the cmd_msg_label() method.
    This class is implimented to make commands easier for the programmer.
    '''
    def __init__(self, cmd):                    # Initialization
        self.cmd = cmd


    def command(self):                          # Generate message parameters from command label              
        self.parameters = self.cmd_msg_label()
        
        if len(self.parameters) < 4:                # Check command message for the presence of data
            self.address = self.parameters[0]
            self.length = self.parameters[1]
            self.header = self.parameters[2]
            self.data = None                        
        else:
            self.address = self.parameters[0]
            self.length = self.parameters[1]
            self.header = self.parameters[2]
            self.data = self.parameters[3:]         # Creates a specific array for data, which is extracted in .message()
                                                    # Parses message parameters to generate ccTalk message
        host_msg = ccTalk_msg(self.address, self.length, self.header, self.data).message()
                                                    # Cross checks message label from generated message
        host_label = ccTalk_msg(self.address, self.length, self.header, self.data).host_msg_label() 
        val364.write(host_msg)                      # Sends generated message from ccTalk_msg() class
        #print("Sent message ", host_msg, host_label)

        slave_msg_head = val364.read(4)             # Read the first 4 bytes of data from slave
        try:
            slave_msg_tail = val364.read(slave_msg_head[1] + 1) # Reads the remain bytes of data including the MSB CRC
            slave_msg_raw = slave_msg_head + slave_msg_tail     # Combine the data arrays to get full ccTalk message
            slave_msg = ccTalk_read(slave_msg_raw).msg_check()  # Cross checks the CRC to insure correct message was received
            slave_label = ccTalk_read(slave_msg_raw).slave_msg_label()  # Cross checks message label from received message
            #print("Recieved message", slave_msg, slave_label)
            return(slave_msg) 
        except:
            print('No response or an error occured')                    # If 'slave_msg'tail' fails,
            return(slave_msg_head)                                      # this means the device failed to respond
                                                                        # most likely due to an error from the master message


    def cmd_msg_label(self):                    # Master message identification
        command_types = {
            'poll' : [55, 0, 254],                  # Currently set for CX only(55), backplane is 240
            'dispense' : [240, 6, 97, 1, 1, 1, 1, 1, 0],
            'dispense_a' : [240, 6, 97, 1, 0, 0, 0, 0, 0],
            'dispense_b' : [240, 6, 97, 0, 1, 0, 0, 0, 0],
            'dispense_c' : [240, 6, 97, 0, 0, 1, 0, 0, 0],
            'dispense_d' : [240, 6, 97, 0, 0, 0, 1, 0, 0],
            'dispense_e' : [240, 6, 97, 0, 0, 0, 0, 1, 0],
            'request_adc' : [240, 1, 91, 12 ],
            'read_adc': [240, 1, 90, 12],
            'read_bp_temp' : [240, 1, 91, 8]
        }
        return(command_types.get(self.cmd))


class raw_adc():                            # Read and saves raw ADC values to CSV file
    '''
    This class requests ADC values from backplane,
    converts bytes to integer/decimal format,
    and writes formatted data to CSV file
    '''

    def __init__(self, start_flag, coin_count):     # Initialization
        self.start_flag = start_flag                    # Flag for first loop
        self.coin_count = coin_count                    # Coin count for total loops
        
        ACK = [1, 0, 48, 0, 55]                         # Message Checking
        BUSY = [1, 0, 246, 6, 87]
        
                
        loop_flag = True                                # Ensure the the request command was acknowledged
        while loop_flag:                                # If NAK or BUSY then wait 1 second and try again
            time.sleep(1)

            if ccTalk_write('request_adc').command() == ACK:    # Once ACK is recieved, quit loop
                loop_flag = False


        loop_flag = True                                # Ensure that the read ADC values command was acknowledged   
        while loop_flag:                                # If BUSY wait 1 second and try again
            time.sleep(1)
            check_adc_read = ccTalk_write('read_adc').command()

            if check_adc_read != BUSY:                  # If NOT BUSY, store values sent from the CX, quit loop
                self.adc_msg = check_adc_read
                loop_flag = False    
                

        self.int_adc_array = self.bite_to_int()         # Run the Class method that converts the data recieved from the CX
                                                        # into usable data


    def bite_to_int(self):                          # Converts Byte Array to Decimal Array
        adc_list = self.adc_msg[5:-1]                   # Extracts the specific ADC data from the ccTalk message
        adc_array = []
        array_count = 0
        loop_count = int(len(adc_list)/2)

        for bit in range(loop_count):                   # Appends the two bytes into a single Byte, E.g: 'AA', 'BB' to 'AABB'
            adc_array.append([adc_list[array_count], adc_list[array_count+1]])
            array_count += 2
        
        int_adc_array = []

        for bite in adc_array:                          # Converts the each Byte to decimal by little order, E.g 'AABB' to 'BBAA'
            int_adc_array.append(int.from_bytes(bite, byteorder='little', signed=False))
        
        return(int_adc_array)


    def request(self):                              # Creates CSV file of raw ADC coil data
        low_fields = ['Low Sensor A', 'Low Sensor B','Low Sensor C', 'Low Sensor D', 'Low Sensor E', 'Coins A', 'Coins B', 'Coins C', 'Coins D', 'Coins E']
        low_sensor = self.int_adc_array[0:5] + self.coin_count  # data array of low sensors with coin count
        

        mid_fields = ['Mid Sensor A', 'Mid Sensor B','Mid Sensor C', 'Mid Sensor D', 'Mid Sensor E', 'Coins A', 'Coins B', 'Coins C', 'Coins D', 'Coins E']
        mid_sensor = self.int_adc_array[6:11] + self.coin_count # data array of middle sensros with coin count
        

        if self.start_flag == 0:                                # If first row, save coloumn fields + first data extraction
            filename = "low_sensor_data.csv"
            with open(filename, 'a', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(low_fields)
                csvwriter.writerow(low_sensor)

            filename = "mid_sensor_data.csv"
            with open(filename, 'a', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(mid_fields)
                csvwriter.writerow(mid_sensor)

        else:                                                   # If not first row, save data extraction only
            filename = "low_sensor_data.csv"
            with open(filename, 'a', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(low_sensor)

            filename = "mid_sensor_data.csv"
            with open(filename, 'a', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(mid_sensor)


class compensate_adc():                     # Firmware specific parameter calculations for ADC compensation
    '''
    This class prepares the data for mathematical compensation of the ADC data.
    It is used to emulate and accurately calculate the backplane ADC values for config creation.
    '''

    def __init__(self):                         # Initialization
        temperature_msg = ccTalk_write('read_bp_temp').command()        # Extract the backplane temperature
        temperature_data = 256*temperature_msg[5] + temperature_msg[4]  # convertion to 16bit value
        temperature_value = float(temperature_data)/100                 # degrees celsius divide by 10 (firmware thing)
        self.temperature = temperature_value
    
    
    def free_air_temp_compensate(self):         # Free air temperature calculation
        '''
        Polynomial calculation
        Y = AX^4 + BX^3 + CX^2 + DX + E
        '''

        # coil_sensors_task.c values
        free_air_fact_a = 0.389669
        free_air_fact_b = -1.082703
        free_air_fact_c = 2.737358
        free_air_fact_d = 8.759172
        free_air_fact_e = -42.27787

        free_temp_comp = ((free_air_fact_a * self.temperature) + free_air_fact_b) * self.temperature
        free_temp_comp = (((free_temp_comp + free_air_fact_c) * self.temperature) + free_air_fact_d) * self.temperature
        free_temp_comp = free_temp_comp + free_air_fact_e

        return(free_temp_comp)


    def temperature_compensate(self):           # Active inductive temperature calculation
        '''
        Polynomial calculation
        Y = AX^4 + BX^3 + CX^2 + DX + E
        '''

        # MC1FactorySettings.xml values
        inductive_temp_compensation_a = 0.73171967
        inductive_temp_compensation_b = -5.89161115
        inductive_temp_compensation_c = 25.6138176
        inductive_temp_compensation_d = -50.6784931
        inductive_temp_compensation_e = 29.9393305

        normal_temp_comp = ((inductive_temp_compensation_a * self.temperature) + inductive_temp_compensation_b) * self.temperature
        normal_temp_comp = (((normal_temp_comp + inductive_temp_compensation_c) * self.temperature) + inductive_temp_compensation_d) * self.temperature
        normal_temp_comp = normal_temp_comp + inductive_temp_compensation_e

        return(normal_temp_comp)


    def free_air_adc(self):                     # Free air coil ADC extraction
        filename = 'mid_sensor_data.csv'            # Middle sensor data is uninfluenced by coins when the cassette is empy
        with open(filename, 'r') as file:
            last_row = None

            for last_row in csv.reader(file):       # Loop through the data within the CSV file
                pass
            
            free_air = last_row[0:5]                # Last row of data is the equivalent of an empty cassette reading for fre air ADC
            return(free_air)


class adc_data_automation():                # Data automation for ADC collection
    '''
    This class encapsulates the functions, methods and loops
    for the automation of extracting backplane data.

    Keeps 'Main' clean.
    '''

    def __init__(self, coin_count):             # Initilization
        self.coin_count = coin_count                # Coin count to track amount of loops to run
                                                    
        self.start_flag = 0                         # Flag for first loop
        self.finish_flag = sum(self.coin_count)     # Flag for final loop, is tracking remaining coins from coin_count
        
        self.nak = [1, 0, 149, 5, 103]              # Message checking


    def collection(self):                       # Raw data collection
        '''
        This method is used to collect 
        and extract raw ADC data from the CX backplane.

        It will issue dispense commands until cassette is empty
        and will record an ADC value each dispense.
        '''
        raw_adc(self.start_flag, self.coin_count).request()     # Initial data extraction
        self.start_flag = 1                                     # Raise starting flag to prevent coloumn headers from being saved to CSV
    
        while self.finish_flag != 0:                            # Loop through coin count until coin count == 0
            position = 0
            for coin in self.coin_count:
                if coin != 0:
                    self.coin_count[position] = coin - 1 
                position += 1                                   # Loop through array position, used for individual dispensing

            if ccTalk_write('dispense').command() == self.nak:  # Dispense all tubes until NAK (low tube counts)
            
                if self.coin_count[0] != 0:                     # Dispense tube A until tube count == 0
                    ccTalk_write('dispense_a').command()
                    print('')
                    print('tube A', self.coin_count[0])
                    time.sleep(2)
            
                if self.coin_count[1] != 0:                     # Dispense tube B until tube count == 0           
                    ccTalk_write('dispense_b').command()
                    print('tube B', self.coin_count[1])
                    time.sleep(2)
            
                if self.coin_count[2] != 0:                     # Dispense tube C until tube count == 0
                    ccTalk_write('dispense_c').command()
                    print('tube C', self.coin_count[2])
                    time.sleep(2)
            
                if self.coin_count[3] != 0:                     # Dispense tube D until tube count == 0
                    ccTalk_write('dispense_d').command()
                    print('tube D', self.coin_count[3])
                    time.sleep(2)
            
                if self.coin_count[4] != 0:                     # Dispense tube E until tube count == 0
                    ccTalk_write('dispense_e').command()
                    print('tube E', self.coin_count[4])
                    time.sleep(2)

            else:
                print('')
                print('A B C D E')
                print(self.coin_count)

            raw_adc(self.start_flag, self.coin_count).request() # Save current loop's data and coin count
            self.finish_flag = sum(self.coin_count)             # Check if coin count is 0

    
    def compensation(self):                     # Compensated data collection
        '''
        This method is used to calculate the compensated ADC values from raw data.

        It generates all the data it needs within itself and from the CSV data generated
        from the collection method.

        It will collect free air data from the last row and iterate and resave calcuation into 
        a second CSV file.
        '''

        self.free_air_temp = compensate_adc().free_air_temp_compensate()    # Extract temperature and calculate free air temp compensation
        self.normal_air_temp = compensate_adc().temperature_compensate()    # Extract temperature and calculate active temp compensation
        self.free_air_adc = compensate_adc().free_air_adc()                 # Extract and store free air ADC values
        
        # Middle sensor data compensation
        filename = 'mid_sensor_data.csv'
        with open(filename, 'r') as raw_data:       # Opens and read the raw CSV data file
            line_count = 0                          # CSV row count
            
            for adc_data in csv.reader(raw_data):                           # If first row, save coloumn fields
                if line_count == 0:
                    filename = "mid_sensor_data_comp.csv"
                    with open(filename, 'a', newline='') as comp_data:
                        csvwriter = csv.writer(comp_data)
                        csvwriter.writerow(adc_data)                        # The first row will be coloumn fields                 
                        line_count += 1                                     # add one to CSV row

                else:
                    adc_data_array = []             # Create array for compensated ADC data
                                     
                    for position in range(10):      # Loop to iterate through data to append into data array
                        if position < 5:            # Check if adc_data from raw csv file is ADC values NOT coin count
                            try:
                                normal_adc = float(adc_data[position])                  # Iterate through adc_data
                                free_adc = float(self.free_air_adc[position])           # Iterate through the free-air array
                            
                                adc_calculation_1 = free_adc + self.free_air_temp       # Firmware calculations for compensation
                                adc_calculation_2 = normal_adc + self.normal_air_temp
                                compensated_adc = adc_calculation_1 - adc_calculation_2
                            
                                adc_data_array.append(compensated_adc)
                            
                            except:
                                continue

                        else:                       # Check is adc_data from raw csv file is coin count NOT ADC values
                            adc_data_array.append(adc_data[position])                   # Iterate through adc_data

                    filename = "mid_sensor_data_comp.csv"
                    with open(filename, 'a', newline='') as comp_data:
                        csvwriter = csv.writer(comp_data)
                        csvwriter.writerow(adc_data_array)          # Save row of compensated data array to CSV file
                        line_count += 1

        # Lower sensor data compensation
        filename = 'low_sensor_data.csv'
        with open(filename, 'r') as raw_data:       # Opens and read the raw CSV data file         
            line_count = 0                          # CSV row count
            
            for adc_data in csv.reader(raw_data):                           # If first row, save coloumn fields
                if line_count == 0:
                    filename = "low_sensor_data_comp.csv"
                    with open(filename, 'a', newline='') as comp_data:
                        csvwriter = csv.writer(comp_data)                   
                        csvwriter.writerow(adc_data)                        # The first row will be coloumn fields
                        line_count += 1                                     # add one to CSV row

                else:
                    adc_data_array = []             # Create array for compensated data
                                     
                    for position in range(10):      # Loop to iterate through data to append into data array
                        if position < 5:            # Check if adc_data from raw CSV file is ADC values NOT coin count
                            try:
                                normal_adc = float(adc_data[position])                  # Iterate through adc_data
                                free_adc = float(self.free_air_adc[position])           # Iterate through the free-air array
                            
                                adc_calculation_1 = free_adc + self.free_air_temp       # Firmware calculations for compensation
                                adc_calculation_2 = normal_adc + self.normal_air_temp
                                compensated_adc = adc_calculation_1 - adc_calculation_2
                            
                                adc_data_array.append(compensated_adc)
                            
                            except:
                                continue

                        else:                       # Check is adc_data from raw csv file is coin count NOT ADC values
                            adc_data_array.append(adc_data[position])                   # Iterate through adc_data

                    filename = "low_sensor_data_comp.csv"
                    with open(filename, 'a', newline='') as comp_data:
                        csvwriter = csv.writer(comp_data)
                        csvwriter.writerow(adc_data_array)          # Save row of compensated data array to CSV file
                        line_count += 1                    

                        


                        






if __name__ == "__main__":
    # Serial Communication Parameters
    com_port = "COM" + com_window()
    baud_rate = 57600
    timeout = 2

    val364 = comms(com_port, baud_rate, timeout)

    coin_count = tube_window()

    # Main code    
    '''
    ADC coil data collection.
    
    Compensated data requires both action 1 & 2
    However if raw data is only required comment out 'action_2' with #
    '''

    auto = adc_data_automation(coin_count)
    action_1 = auto.collection()        # Raw ADC data collection
    action_2 = auto.compensation()      # Compensated ADC data collection     


            

    
            
        
        









    
     
    
