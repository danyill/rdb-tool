#!/usr/bin/env python3

"""

This tool extracts a pile of settings based on the hierachy of Quickset

"""

import collections
import os
import re

import olefile

import sel_logic_count

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

def get_ole_data(filepath):
    data = []
    try:
        ole = olefile.OleFileIO(filepath)
        listdir = ole.listdir()
        for direntry in listdir:
            data.append([direntry, ole.openstream(direntry).getvalue()])
    except:
        print('Failed to read streams in file: ' + filepath)
    return data

def extract_parameters(filepath, rdb_info, txtfile):
    fn = os.path.basename(filepath)
    parameter_info=[]

    for stream in rdb_info:
        settings_name = str(stream[0][1])
        stream_name = str(stream[0][-1]).upper()

        if stream_name in SEL_FILES_TO_GROUP[txtfile]:

            #print(stream_name, settings_name)
            return [settings_name, stream[1].decode('utf-8')]

def get_sel_setting(text):
    setting_expression = re.compile(r'^([A-Z0-9_]+),\"(.*)\"(?:\r\n|\x1c\r\n)', flags=re.MULTILINE)
    return re.findall(setting_expression, text)

def sum_logic_usage_multiple_groups(d, group_title='Group', settings_name=None):
    """
    d is a dictionary with the group number as the key
    and the protection logic as the values
    This is processed and an Asciidoc table is produced
    """

    columns = 4*len(d) + 1

    # get logic report
    raw_results = collections.OrderedDict()
    for k, v in d.items():
        raw_results[k] = sel_logic_count.calc_usage_raw(v)

    line_info = ['Lines Used (w/ comment lines)', 'Lines Used (w/o comment lines)']

    logic_info = [ 'PSV', 'PMV', 'PLT', 'PCT', 'PST', 'PCN',
                   'ASV', 'AMV', 'ALT',        'AST', 'ACN']

    TOTAL_SEL_PROTECTION_LINES = 250

    table_data = []

    for row_name in line_info + logic_info:

        table_row = [row_name]

        for k, v in raw_results.items():
            table_row.append(v[row_name])

        table_data.append(table_row)

    no_groups = len(d)
    info = []

    #  Anchor
    info.append('[#overall_logic_usage]')

    # Title
    if settings_name:
        keys = ', '.join([str(ky) for ky in d.keys()])
        info.append('.`{}` Logic Usage in Setting Groups {}'.format(settings_name.upper(), keys))

    # Column Definitions
    info.append('[cols="1*<.^,{}"]'.format(','.join(['1*>.^,1*^.^,1*>.^'] * no_groups)))

    info.append('|===')

    # Group Title
    info.append('h|')
    for group in d.keys():
        info.append('3+^.^h| '.format(no_groups) +
                    '{} {}'.format(group_title, group))

    info.append('')

    # Overall line information
    for k in table_data:
        if k[0] in line_info:
            pr = ('h| {}').format(k[0]).ljust(50)
            for gd in k[1:]:
                pr += '3+^.^| {} / {} '.format(gd, TOTAL_SEL_PROTECTION_LINES).ljust(20)
            info.append(pr)

    info.append('')

    # Capacity free from relay STA S command
    sta_s_info = ['Free protection settings capacity (%)', 'Free protection execution capacity (%)']

    for s in sta_s_info:
        pr = ('h| {} ').format(s).ljust(50)
        for gd in k[1:]:
            pr += '3+^.^| ??? '.ljust(20)
        info.append(pr)

    info.append('')
    info.append('h| Variable ' +
                ' '.join(['h| Used h| Free % h| Available']*no_groups))
    info.append('')

    for k in table_data:
        if k[0] in logic_info:
            pr = ('h| `{}`'.format(k[0])).ljust(13)
            for gd in k[1:]:
                fstr = '| {:>12} | {:<7.0%} | {:<30}'
                pr += fstr.format('{} / {}'.format(gd['qty'], gd['total']),
                                  gd['free_pu'],
                                  '[small]#{}#'.format(gd['available_detail']))
            info.append(pr)

    info.append('|===')

    return('\n'.join(info))

def plogic_used(filepath, group_prefix, *nums):

    logics = {}
    for num in nums:
        print(filepath,num)
        [settings_name, output] = process_file(filepath, 'L'+str(num))
        lines = get_sel_setting(output)
        result = []
        for settings in lines:
            result.append(settings[1])
        logic_text = "\n".join(result)
        logics[num] = logic_text

    if len(nums) == 1:
        return sel_logic_count.calc_logic_usage(logics[nums[0]])
    else:
        return sum_logic_usage_multiple_groups(logics, group_prefix, settings_name)

if __name__ == '__main__':

    """
    path = r'F:\standard-designs\transformer-protection\SEL487E-3_Transformer_Protection_Settings\settings\SEL-487E-3.rdb'
    output = process_file(path, 'F1')


    k = get_sel_setting(output)
    result = []


    for item in k:
        val = item[1]
        cnt = sel_logic_count.countElementsUsed(val)
        result.append(('{: >3}').format(str(cnt)) + ' | ' + item[0] + ' ::= ' + val)

    result = sorted(result, key=lambda x: int((x.split('|'))[0].strip()))

    print(result)

    for k in result:
    #   print('x', k)
        print(int((k.split('|'))[0].strip()), k)

    """

    """output = process_file('/media/mulhollandd/KINGSTON/standard-designs/transformer-protection/SEL487E-3_Transformer_Protection_Settings/settings/SEL-487E-3.rdb', 'L1')

     #k = get_stream_parameter('',output)
    k = get_sel_setting(output)
    result = []
    for val in k:
        result.append(val[1])
    logic_text = "\n".join(result)

    print(sel_logic_count.calc_logic_usage(logic_text))"""

    #plogic_used('/home/mulhollandd/Downloads/SEL487E-3_Transformer_Protection_Settings_v14Aug2017.000.002/settings/SEL-487E-3.rdb', 1)

    
    path = '/media/mulhollandd/KINGSTON/standard-designs/transformer-protection/SEL487E-3_Transformer_Protection_Settings/settings/SEL-487E-3.rdb'
    #path = r'G:\standard-designs\transformer-protection\SEL487E-3_Transformer_Protection_Settings\settings\SEL-487E-3.rdb'
    #path = '/home/mulhollandd/Downloads/junk/SEL-487E-3.rdb'
    print(plogic_used(path, 'Application', 1,2))
    
