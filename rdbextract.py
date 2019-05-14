#!/usr/bin/env python3

"""
rdbextract.py
A tool to browse SEL AcSELerator Quickset RDB files to extract parameter
information intended for bulk processing.

Usage defined by running with option -h.

This tool can be run from the IDLE prompt using the start def, e.g.
start('-h') or start('start.rdb G1:50P1P')

Installation instructions (for Python 3):
 - pip install tablib olefile

TODO:
 - include settings group which parameter is used in:
  code like this could be used:
    print "used in: "
    print re.findall('^' + SEL_SETTING_NAME + ",\"" +
                   SEL_EXPRESSION + sys.argv[1] + SEL_EXPRESSION
                   + "\"" + SEL_SETTING_EOL,
                   rdat, flags=re.MULTILINE)
 - sorting options on display and dump output?
 - sort out guessing of Transpower standard design version
 - sort out handling of protection and automation logic in 400 series
"""

import sys
import os
import argparse
import glob
import re

from itertools import zip_longest
from pathlib import Path

import tablib
import olefile

from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

__version__ = "GratefulDead"

RDB_EXTENSION = 'RDB'
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
PARAMETER_SEPARATOR = ':'

SEL_EXPRESSION = r'[\w :+/\\()!,.\-_\\*#]*'
SEL_SETTING_EOL = r'\x1c\r\n'
# these seem to be the options
# this needs to be verified
SEL_SETTING_EOL = r'(\r\n|\x1c\r\n)'
# presently using this as covers all cases.
# this seems to work differently to others: SEL-421-4 LineProt Std Rev01.rdb
SEL_SETTING_EOL = r''
SEL_SETTING_NAME = r'[\w _]*'
SEL_FID_EXPRESSION='^FID=([\w :+/\\()!,.\-_\\*]{10,})\r\n'

OUTPUT_FILE_NAME = "output"
NOT_FOUND = 'Not Found'

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

OUTPUT_HEADERS = ['RDB File','Name','Setting File','Setting Name','Val']

def main(arg=None):
    parser = argparse.ArgumentParser(
        description='Process individual or multiple RDB files and produce summary'\
            ' of results as a csv or xls file.',
        epilog='Enjoy. Bug reports and feature requests welcome. Feel free to build a GUI :-)',
        prefix_chars='-/')

    parser.add_argument('-o', choices=['csv','xlsx'],
                        help='Produce output as either comma separated values (csv) or as'\
                        ' a Micro$oft Excel .xls spreadsheet. If no output provided then'\
                        ' output is to the screen.')
    # ' '.join(opts.dmp) 1
    parser.add_argument('path', metavar='PATH|FILE', nargs='+',
                       help='Go recursively go through path PATH. Redundant if FILE'\
                       ' with extension .rdb is used. When recursively called, only'\
                       ' searches for files with:' +  RDB_EXTENSION + '. Globbing is'\
                       ' allowed with the * and ? characters.')

    parser.add_argument('-c', '--console', action="store_true",
                       help='Show output to console')

    # Not implemented yet
    #parser.add_argument('-d', '--design', action="store_true",
    #                   help='Attempt to determine Transpower standard design version and' \
    #                   ' include this information in output')

    parser.add_argument('-s', '--settings', metavar='G:S', type=str, nargs='+',
                       help='Settings in the form of G:S where G is the group'\
                       ' and S is the SEL variable name. If G: is omitted the search' \
                       ' goes through all groups. Otherwise G should be the '\
                       ' group of interest. S should be the setting name ' \
                       ' e.g. OUT201.' \
                       ' Examples: G1:50P1P or G2:50P1P or 50P1P' \
                       ' '\
                       ' You can also get port settings using P:S'
                       ' Note: Applying a group for a non-grouped setting is unnecessary'\
                       ' and will prevent you from receiving results.'\
                       ' '\
                       ' Special arguments include: FID')

    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)

    if arg == None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(arg.split())

    files_to_do = return_file_paths([' '.join(args.path)], RDB_EXTENSION)

    if files_to_do != []:
        process_rdb_files(files_to_do, args)
    else:
        print('Found nothing to do for path: ' + args.path[0])
        sys.exit()
        os.system("Pause")

def return_file_paths(args_path, file_extension):

    fpath = args_path[0].replace(r'"', '')
    
    if fpath == ".":
        files = list(Path('.').glob('**/*.' + file_extension.lower()))
    else:
        files = Path(fpath).resolve().glob('*.rdb')

    return [str(f) for f in files]

def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def process_rdb_files(files_to_do, args):
    parameter_info = []

    for filename in files_to_do:
        # print filename
        rdb_info = get_ole_data(filename)
        new_data = extract_parameters(filename, rdb_info, args)
        parameter_info += new_data

    data = tablib.Dataset(headers=['filename'] + args.settings)

    # group output data by parameter
    grouped = grouper(parameter_info, len(args.settings), '')

    for file_data in grouped:
        data.append([file_data[0][0]] + [k[-1] for k in file_data])

    # don't overwrite existing file
    name = OUTPUT_FILE_NAME
    if args.o == 'csv' or args.o == 'xlsx':
        # this is stupid and klunky but hey
        while os.path.exists(name + '.csv') or os.path.exists(name + '.xlsx'):
            name += '_'

    # write data
    if args.o == None:
        pass
    elif args.o == 'csv':
        with open(name + '.csv', 'wb') as output:
            output.write(data.csv)
    elif args.o == 'xlsx':
        with open(name + '.xlsx', 'wb') as output:
            output.write(data.xlsx)

    if args.console == True:
        display_info(parameter_info)

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

def fix_string(text):
    return re.sub(ILLEGAL_CHARACTERS_RE, '', text)

def extract_parameters(filename, rdb_info, args):
    fn = os.path.basename(filename)
    parameter_info=[]

    parameter_list = []
    for k in args.settings:
        parameter_list.append(k.replace(r'"', '')) #.translate(None, '\"'))

    # iterate across all parameters the user specified
    for parameter in parameter_list:
        category_file_list = None
        search_parameter = ''

        # is it a parameter associated wtih a group?
        if parameter.find(PARAMETER_SEPARATOR) != -1:
            category_file_list = \
                SEL_FILES_TO_GROUP[(parameter.split(PARAMETER_SEPARATOR))[0]]
            search_parameter = parameter.split(PARAMETER_SEPARATOR)[1]
        else:
            search_parameter = parameter

        # print search_parameter
        # iterate over stream in rdb file
        for stream in rdb_info:
            return_value = []
            settings_name = str(stream[0][1])
            stream_name = str(stream[0][-1]).upper()

            # lookup for group to file to restrict examination
            # parameters are always:
            # Relays > Setting Name > Settings Files
            # so length is always at least 3
            if len(stream[0]) >= 3 and \
                (category_file_list == None \
                or stream[0][-1].upper() in category_file_list):

                if search_parameter == 'FID':
                    try:
                        return_value = extract_fid(stream[1].decode('ascii', errors="ignore"))
                    except:
                        return_value = "Unable to decode rdb file"

                else:
                    try:
                        return_value = get_stream_parameter(search_parameter,
                                                            stream[1].decode('ascii', errors="ignore"))
                    except:
                        return_value = "Unable to decode rdb file"

            if return_value != []:
                parameter_info.append([fn, settings_name, \
                    stream_name, search_parameter, return_value[0]])
                break

        else:
            parameter_info.append([fn, 'NA',\
                    "N/A", search_parameter, NOT_FOUND])

    return parameter_info

def extract_fid(stream):
    # FIDs look like this for example:
    return re.findall(SEL_FID_EXPRESSION, \
        stream, flags=re.MULTILINE)

def get_stream_parameter(parameter, stream):
    return re.findall('^' + parameter + \
        ",\"(" + SEL_EXPRESSION + ")\"" + \
        SEL_SETTING_EOL, \
        stream, flags=re.MULTILINE)

def display_info(parameter_info):
    lengths = []
    # first pass to determine column widths:
    for line in parameter_info:
        for index,element in enumerate(line):
            try:
                lengths[index] = max(lengths[index], len(element))
            except IndexError:
                lengths.append(len(element))

    parameter_info.insert(0,OUTPUT_HEADERS)
    # now display in columns
    for line in parameter_info:
        display_line = ''
        for index,element in enumerate(line):
            display_line += element.ljust(lengths[index]+2,' ')
        print(display_line)

if __name__ == '__main__':
    if len(sys.argv) == 1 :
        # main(r'-o xlsx --console "in\SEL-421-4 LineProt Std Rev01.rdb" --settings "RID TID G1:81D1P 81D1T 81D2P 81D2T TR FID"')
        # main(r'-o xlsx --console "in\SEL-421-4 LineProt Std Rev01.rdb" --settings "TR"')
        #main(r'-o xlsx "in/other/SEL-351S-6-R5 Standard Rev01 (2).rdb" --settings "RID TID SID G1:81D1P G1:81D1T 81D2P 81D2T TR FID"')
        # main(r'-o xlsx "W:\Education\Current\Stationware Dump\20150511\SI" --settings "RID TID SID G1:81D1P G1:81D1D 81D2P 81D2D TR FID"')
        # main(r'-o xlsx "in/other/SEL-351S-6-R5 Standard Rev01 (2).rdb" --settings "RID TID SID G1:81D1P G1:81D1T 81D2P 81D2T TR FID"')
        # main(r'-o xlsx "W:\Education\Current\Stationware Dump\20150511\SI" --settings "RID TID SID G1:81D1P G1:81D1D 81D2P 81D2D TR FID"')
        # main(r'-o xlsx "W:\Education\Current\Stationware Dump\20150511\" --settings "RID TID G1:51P1P G1:51P1TD G1:51P1C TR FID"')
        # W:\Education\Current\Stationware Dump
        #main(r'-o xlsx "/media/mulhollandd/KINGSTON/stationware/rdb" --settings "RID TID FID"')
        main(r'-o xlsx "/media/mulhollandd/KINGSTON/stationware/rdb" --settings "RID TID SID FID"')

    else:
        main()
