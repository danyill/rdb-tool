#!/usr/bin/env python3

"""

This tool extracts a pile of settings based on the hierachy of Quickset

"""

import os
import re

import olefile

# this probably needs to be expanded
SEL_FILES_TO_GROUP = {
    'G': ['SET_G1'],
    'G1': ['SET_S1.TXT', 'SET_L1.TXT', 'SET_1.TXT'], # Groups
    'G2': ['SET_S2.TXT', 'SET_L2.TXT', 'SET_2.TXT'],
    'G3': ['SET_S3.TXT', 'SET_L3.TXT', 'SET_3.TXT'],
    'G4': ['SET_S4.TXT', 'SET_L4.TXT', 'SET_4.TXT'],
    'G5': ['SET_S5.TXT', 'SET_L5.TXT', 'SET_5.TXT'],
    'G6': ['SET_S6.TXT', 'SET_L6.TXT', 'SET_6.TXT'],

    'P1': ['SET_P1.TXT'], # Ports
    'P2': ['SET_P2.TXT'],
    'P3': ['SET_P3.TXT'],
    'P5': ['SET_P5.TXT'],
    'PF': ['SET_PF.TXT'], # Front Port
    'P87': ['SET_P87.TXT'], # Differential Port Settings

    'A1': ['SET_A1.TXT'], # Automation
    'A2': ['SET_A2.TXT'],
    'A3': ['SET_A3.TXT'],
    'A4': ['SET_A4.TXT'],
    'A5': ['SET_A5.TXT'],
    'A6': ['SET_A6.TXT'],
    'A7': ['SET_A7.TXT'],
    'A8': ['SET_A8.TXT'],
    'A9': ['SET_A9.TXT'],
    'A10': ['SET_A10.TXT'],

    'L1': ['SET_L1.TXT'], # Protection Logic
    'L2': ['SET_L2.TXT'],
    'L3': ['SET_L3.TXT'],
    'L4': ['SET_L4.TXT'],
    'L5': ['SET_L5.TXT'],
    'L6': ['SET_L6.TXT'],
    'L7': ['SET_L7.TXT'],
    'L8': ['SET_L8.TXT'],
    'L9': ['SET_L9.TXT'],


    'B1': ['SET_B1.TXT'], # Bay Control information

    'D1': ['SET_D1.TXT'], # DNP
    'D2': ['SET_D2.TXT'],
    'D3': ['SET_D3.TXT'],
    'D4': ['SET_D4.TXT'],
    'D5': ['SET_D5.TXT'],

    'F1': ['SET_F1.TXT'], # Front Panel
    'M1': ['SET_M1.TXT'], # CB Monitoring
    'N1': ['SET_N1.TXT'], # Notes
    'O1': ['SET_O1.TXT'], # Outputs
    'R1': ['SET_R1.TXT'], # SER
    'T1': ['SET_R1.TXT'], # Aliases

    }

def process_file(filepath, args):
    rdb_info = get_ole_data(filepath)
    return extract_parameters(filepath, rdb_info, args)

def get_ole_data(filename):
    data = []
    try:
        ole = olefile.OleFileIO(filename)
        listdir = ole.listdir()
        for direntry in listdir:
            data.append([direntry, ole.openstream(direntry).getvalue()])
    except:
        print('Failed to read streams in file: ' + filename)
    return data

def extract_parameters(filename, rdb_info, txtfile):
    fn = os.path.basename(filename)
    parameter_info=[]

    for stream in rdb_info:
        settings_name = str(stream[0][1])
        stream_name = str(stream[0][-1]).upper()

        if stream_name in SEL_FILES_TO_GROUP[txtfile]:

            print(stream_name, settings_name)
            return stream[1].decode('utf-8')

def get_stream_parameter(parameter, text):
    setting_expression = re.compile(r'^([A-Z0-9_]+),\"(.*)\"(?:\r\n|\x1c\r\n)', flags=re.MULTILINE)
    return re.findall(setting_expression, text)

if __name__ == '__main__':
    output = process_file('/media/mulhollandd/KINGSTON/standard-designs/transformer-protection/SEL487E-3_Transformer_Protection_Settings/settings/SEL-487E-3.rdb', 'F1')

    k = get_stream_parameter('',output)
    result = []

    import sel_logic_count

    for item in k:
        val = item[1]
        cnt = sel_logic_count.countElementsUsed(val)
        result.append(('{: >3}').format(str(cnt)) + ' | ' + item[0] + ' ::= ' + val)

    result = sorted(result, key=lambda x: int((x.split('|'))[0].strip()))

    print(result)

    for k in result:
        #print('x', k)
        print(int((k.split('|'))[0].strip()), k)



    #str = [x(0) + ':=' + x(1) for x in k]
