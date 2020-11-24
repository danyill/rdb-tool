#!/usr/bin/env python3

"""

This tool extracts a pile of settings based on the hierachy of Quickset

"""

import collections
import os
import re

import olefile

import sel_logic_count

LINE_INFO = ['Lines Used (w/ comment lines)', 'Lines Used (w/o comment lines)']

LOGIC_INFO = [ 'PSV', 'PMV', 'PLT', 'PCT', 'PST', 'PCN',
                'ASV', 'AMV', 'ALT',        'AST', 'ACN']

TOTAL_SEL_PROTECTION_LINES = 250
TOTAL_SEL_AUTOMATION_LINES = 1000



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

def process_file(filepath, args, settingsName=None):
    rdb_info = get_ole_data(filepath, settingsName=settingsName)
    return extract_parameters(filepath, rdb_info, args)

def get_ole_data(filepath,settingsName=None):
    data = []
    listdir = []
    try:
        ole = olefile.OleFileIO(filepath)
        listdir = ole.listdir()
        if settingsName:
            listdir = [l for l in listdir if l[1]==settingsName]
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
            return [settings_name, stream[1].decode('utf-8')]

def get_sel_setting(text):
    setting_expression = re.compile(r'^([A-Z0-9_]+),\"(.*)\"(?:\r\n|\x1c\r\n)', flags=re.MULTILINE)
    return re.findall(setting_expression, text)

def format_logic(d):
    # get logic report
    if isinstance(d, str):
        raw_results = collections.OrderedDict()
        for k, v in d.items():
            raw_results[k] = sel_logic_count.calc_usage_raw(v)
        return raw_results
    else:
        return d

def make_table_data(raw_results):
    table_data = []

    for row_name in LINE_INFO + LOGIC_INFO:
        table_row = [row_name]
        for k, v in raw_results.items():
            if row_name in v:
                table_row.append(v[row_name])
        table_data.append(table_row)

    return table_data

def sum_logic_usage_multiple_groups(d, group_title='Group', settings_name=None, automation=None, total=None):
    """
    d is a dictionary with the group number as the key
    and the protection logic as the values
    This is processed and an Asciidoc table is produced
    """

    columns = 3*len(d) + 1

    # get logic report
    table_data = make_table_data(format_logic(d))

    no_groups = len(d)
    info = []

    #  Anchor
    info.append('[#overall_logic_usage]')

    # Title
    if settings_name:
        keys = ', '.join([str(ky)[1:2] for ky in d.keys()])
        info.append('.`{}` Logic Usage in Setting Groups {}'.format(settings_name.upper(), keys))

    # Column Definitions
    info.append('[cols="1*<.^,{}"]'.format(','.join(['1*>.^,1*^.^,1*>.^'] * no_groups)))

    info.append('|===')

    # Group Title
    info.append('h|')
    for group in d.keys():
        info.append('3+^.^h| '.format(no_groups) +
                    '{} {}'.format(group_title, group[1:]))

    info.append('')
    info.append(str(columns)+'+^.^h| Protection Usage')
    info.append('')

    # Overall line information
    for k in table_data:
        if k[0] in LINE_INFO:
            pr = ('h| {}').format(k[0]).ljust(50)
            for gd in k[1:]:
                pr += '3+^.^| {} / {} '.format(gd, TOTAL_SEL_PROTECTION_LINES).ljust(20)
            info.append(pr)

    # Capacity free from relay STA S command
    sta_s_info = ['Free protection settings capacity (%)', 'Free protection execution capacity (%)']

    for s in sta_s_info:
        pr = ('h| {} ').format(s).ljust(50)
        for gd in range(no_groups):
            pr += '3+^.^| #??# '.ljust(20)
        info.append(pr)

    info.append('')
    if d and not total:
        info.append(str(columns)+'+^.^h| Variable Usage for Protection Logic')    
    elif total and automation:
        info.append(str(columns)+'+^.^h| Variable Usage for Protection and Automation Logic')
    info.append('')

    info.append('h| Variable ' +
                ' '.join(['h| Used h| Free % h| Available']*no_groups))
    info.append('')

    if total:
        table_data = make_table_data(format_logic(total))

    for k in table_data:
        if k[0] in LOGIC_INFO:
            pr = ('h| `{}`'.format(k[0])).ljust(13)
            for gd in k[1:]:
                fstr = '| {:>12} | {:<7.0%} | {:<30}'
                pr += fstr.format('{} / {}'.format(gd['qty'], gd['total']),
                                  gd['free_pu'],
                                  '[small]#{}#'.format(gd['available_detail']))
            info.append(pr)

    if automation:
        info.append('')
        info.append(str(columns)+'+^.^h| Automation Usage')
        info.append('')

        # Group Title
        info.append('h|')
        for group in d.keys():
            info.append('3+^.^h| '.format(no_groups) +
                        '{} {}'.format(group_title, group[1:]))

        questions = ['3+^.^| #??# '] * no_groups

        info.append('{:<50} {}'.format('h| Free automation settings storage capacity (%)', ''.join(questions)))
        info.append('{:<50} {}'.format('h| Free automation execution availability (%)', ''.join(questions)))
        info.append('{:<50} {}'.format('h| Automation peak execution cycle time (ms)', ''.join(questions)))
        info.append('{:<50} {}'.format('h| Automation average execution cycle time (ms)', ''.join(questions)))

        table_data = make_table_data(format_logic(automation))

        # Overall line information
        for k in table_data:
            if k[0] in LINE_INFO:
                pr = ('h| {} ').format(k[0]).ljust(51)
                for gd in k[1:]:
                    pr +=  str(no_groups * 3) + '+^.^| {} / {} '.format(gd, TOTAL_SEL_AUTOMATION_LINES).ljust(20)
                info.append(pr)
                    
    info.append('|===')

    return('\n'.join(info))

def get_logic(filepath, *names, settingsName=None):
    logics = {}
    for name in names:
        [settings_name, output] = process_file(filepath, name, settingsName)
        lines = get_sel_setting(output)
        result = []
        for settings in lines:
            result.append(settings[1])
        logic_text = "\n".join(result)
        logics[name] = logic_text
    return logics

def get_logic_total(path, groups, includeAutomation=True, settings_name=None):
    # get logic for number of protection 
    groups_new = ['L' + str(g) for g in groups]
    protection = get_logic(path, *groups_new, settingsName=settings_name)
    
    automation_arr = []
    if includeAutomation:
        for block in range(1,10+1):
            #print(get_logic(path, 'A' + str(block)))
            automation_arr.append(get_logic(path, 'A' + str(block), settingsName=settings_name)['A' + str(block)])
        automation = '\n'.join(automation_arr)
        return [protection, automation]
    
    return [protection]

def plogic_used(filepath, group_prefix, settings_name, *nums):

    logics = get_logic(filepath, *nums)

    if len(nums) == 1:
        return sel_logic_count.calc_logic_usage(logics[nums[0]])
    else:
        return sum_logic_usage_multiple_groups(logics, group_prefix, settings_name)

def pa_logic_used(filepath, group_prefix, settings_name, *nums):

    logics = get_logic_total(filepath, nums, includeAutomation=True, settings_name=settings_name)
    LINES = ['Lines Used (w/ comment lines)', 'Lines Used (w/o comment lines)']
    
    automation = sel_logic_count.calc_usage_raw(logics[1])
    automation = {k:v for (k,v) in automation.items() if k in LINES}
    automation = {'A': automation}
    
    protection = {}
    total = {}

    for group in nums:
        # print(group)
        pg = sel_logic_count.calc_usage_raw(logics[0]['L' + str(group)])
        protection['L' + str(group)] = {k:v for (k,v) in pg.items() if k in LINES}
                
        tg = sel_logic_count.calc_usage_raw(logics[0]['L' + str(group)] + '\n' + logics[1])
        total['L' + str(group)] = {k:v for (k,v) in tg.items() if k not in LINES}
        
    #print('p',protection, 'a', automation, 't', total)
    print(sum_logic_usage_multiple_groups(protection, group_prefix, settings_name, automation, total))
        
    """
    if len(nums) == 1:
        return sel_logic_count.calc_logic_usage(logics[nums[0]])
    else:
        return sum_logic_usage_multiple_groups(logics, group_prefix, settings_name)
    """


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

    
    #path = '/media/mulhollandd/KINGSTON/standard-designs/transformer-protection/SEL487E-3_Transformer_Protection_Settings/settings/SEL-487E-3.rdb'
    #path = r'G:\standard-designs\transformer-protection\SEL487E-3_Transformer_Protection_Settings\settings\SEL-487E-3.rdb'
    path = r'F:\standard-designs\transformer-protection\SEL487E-3_Transformer_Protection_Settings\settings\SEL-487E-3.rdb'
    path = r'/media/mulhollandd/KINGSTON/standard-designs/capacitor-protection/SEL487E-3_Capacitor_Protection_Settings/settings/SEL-487E-3.rdb'
    #path = '/home/mulhollandd/Downloads/junk/SEL-487E-3.rdb'
    #print(plogic_used(path, 'Application', 1, 2))


    #print(get_logic_total(path, [1,2]))
    
    
    #print(pa_logic_used(path, 'Application', 1, 2))
    #print(plogic_used(path, 'Application', 'Blah', 'L1', 'L2'))
    pa_logic_used(path, 'Application', 'TYP123_DStarNE', '1')
    
    #output = process_file(path, 'R1')
    #print(output)

    
    

    #print(output)
    """
    ser_points_and_aliases = {}
    for counter in range(1, 250+1):
        num = str(counter)
        #SITM70,"TRIPT"\x1c\r\nSNAME70,"TRIPT"\x1c\r\nSSET70,"Asserted"\x1c\r\nSCLR70,"Deasserted"\x1c\r\nSHMI70,"N"
        match = re.compile(r'SITM' + num + r',"([A-Z0-9_]*)"\x1c\r\nSNAME' + num + r',"([A-Za-z0-9_]+)*"\x1c\r\nSSET' + num + ',"(.*)"\x1c\r\nSCLR'+ num + ',"(.*)"\x1c\r\nSHMI' + num + r',"([A-Z0-9_]+)*"', flags=re.MULTILINE)
        result = match.findall('\n'.join(output))
        rwb = result[0][0]
        aliases = result[0][1]
        alias_set = result[0][2]
        alias_clear = result[0][3]
        hmi_alarm = result[0][4]
        
        ser_points_and_aliases[rwb] = [aliases, alias_set, alias_clear, hmi_alarm]
        
        print(rwb, [aliases, alias_set, alias_clear, hmi_alarm])
        
    
    output = process_file(path, 'P1')

    protection = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6']
    automation = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10']

    for logic in protection + automation
    output = process_file(path, 'P1')
    output = process_file(path, 'P1')
    output = process_file(path, 'P1')
    output = process_file(path, 'P1')
    output = process_file(path, 'P1')
    """


    #for k in output:
    #    print(k)

    #  SITM248,"PST07Q"    SNAME248,"PST07Q"    SSET248,"Asserted"    SCLR248,"Deasserted"    SHMI248,"N"
    #  

    # tool to remove protection and automation aliases which are unused.

    
