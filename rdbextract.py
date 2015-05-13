#!/usr/bin/python2
# NB: As per Debian Python policy #!/usr/bin/env python2 is not used here.

"""
rdbextract.py

A tool to browse SEL AcSELerator Quickset RDB files to extract parameter 
information intended for bulk processing.

Usage defined by running with option -h.

This tool can be run from the IDLE prompt using the start def, e.g.
start('-h') or start('start.rdb G1:50P1P')

Thoughtful ideas most welcome. 

Installation instructions (for Python *2.7.9*):
 - pip install tablib
 - or if behind a proxy server: pip install --proxy="user:password@server:port" packagename
 - within Transpower: pip install --proxy="transpower\mulhollandd:password@tptpxy001.transpower.co.nz:8080" tablib    

TODO: 
 - unbundle OleFileIO_PL
 - include settings group which parameter is used in:
  code like this could be used:
    print "used in: " 
    print re.findall('^' + SEL_SETTING_NAME + ",\"" + 
                   SEL_EXPRESSION + sys.argv[1] + SEL_EXPRESSION 
                   + "\"" + SEL_SETTING_EOL, 
                   rdat, flags=re.MULTILINE) 
 - sorting options on display and dump output?    
 - sort out guessing of Transpower standard design version 
"""

__author__ = "Daniel Mulholland"
__copyright__ = "Copyright 2015, Daniel Mulholland"
__credits__ = ["Decalage http://decalage.info/contact", "Kenneth Reitz https://github.com/kennethreitz/tablib"]
__license__ = "GPL"
__version__ = '0.10'
__maintainer__ = "Daniel Mulholland"
__hosted__ = "https://github.com/danyill/rdb-tool"
__email__ = "dan.mulholland@gmail.com"

# update this line if using from Python interactive
#__file__ = r'W:\Education\Current\pytooldev\rdb-tool'

import sys
import os
import argparse
import glob
import re
import tablib

RDB_EXTENSION = 'RDB'
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
PARAMETER_SEPARATOR = ':'
SEL_EXPRESSION = r'[\w :+/\\()!,.\-_\\*]*'
SEL_SETTING_EOL = r'\x1c\r\n'
SEL_SETTING_NAME = r'[\w _]*'
SEL_FID_EXPRESSION='^FID=([\w :+/\\()!,.\-_\\*]*)\r\n'
OUTPUT_FILE_NAME = "output"

# this probably needs to be expanded
SEL_FILES_TO_GROUP = {\
    'G1': ['SET_S1.TXT', 'SET_L1.TXT', 'SET_1.TXT'],\
    'G2': ['SET_S2.TXT', 'SET_L2.TXT', 'SET_2.TXT'],\
    'G3': ['SET_S3.TXT', 'SET_L3.TXT', 'SET_3.TXT'],\
    'G4': ['SET_S4.TXT', 'SET_L4.TXT', 'SET_4.TXT'],\
    'G5': ['SET_S5.TXT', 'SET_L5.TXT', 'SET_5.TXT'],\
    'G6': ['SET_S6.TXT', 'SET_L6.TXT', 'SET_6.TXT'],\
    'P1': ['SET_P1.TXT'],\
    'P2': ['SET_P2.TXT'],\
    'P3': ['SET_P3.TXT'],\
    'P5': ['SET_D5.TXT'],\
    'P87': ['SET_P87.TXT'],\
    };
OUTPUT_HEADERS = ['RDB File','Name','Setting File','Setting Name','Val','FID']

from thirdparty.OleFileIO_PL import OleFileIO_PL

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

    parser.add_argument('path', metavar='PATH|FILE', nargs=1, 
                       help='Go recursively go through path PATH. Redundant if FILE'\
                       ' with extension .rdb is used. When recursively called, only'\
                       ' searches for files with:' +  RDB_EXTENSION + '. Globbing is'\
                       ' allowed with the * and ? characters.')

    parser.add_argument('-s', '--screen', action="store_true",
                       help='Show output to screen')

    # Not implemented yet
    #parser.add_argument('-d', '--design', action="store_true",
    #                   help='Attempt to determine Transpower standard design version and' \
    #                   ' include this information in output')
                       
    parser.add_argument('settings', metavar='G:S', type=str, nargs='+',
                       help='Settings in the form of G:S where G is the group'\
                       ' and S is the SEL variable name. If G: is omitted the search' \
                       ' goes through all groups. Otherwise G should be the '\
                       ' group of interest. S should be the setting name ' \
                       ' e.g. OUT201.' \
                       ' Examples: G1:50P1P or G2:50P1P or 50P1P' \
                       ' '\
                       ' You can also get port settings using P:S'
                       ' Note: Applying a group for a non-grouped setting is unnecessary'\
                       ' and will prevent you from receiving results.')

    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)

    if arg == None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(arg.split())
    
    files_to_do = return_file_paths(args.path, RDB_EXTENSION)
    
    if files_to_do != []:
        process_rdb_files(files_to_do, args)
    else:
        print('Found nothing to do for path: ' + args.path[0])
        sys.exit()
        os.system("Pause")
    
def return_file_paths(args_path, file_extension):
    paths_to_work_on = []
    for p in args_path:
        p = p.translate(None, ",\"")
        if not os.path.isabs(p):
            paths_to_work_on +=  glob.glob(os.path.join(BASE_PATH,p))
        else:
            paths_to_work_on += glob.glob(p)
            
    files_to_do = []
    # make a list of files to iterate over
    if paths_to_work_on != None:
        for p_or_f in paths_to_work_on:
            if os.path.isfile(p_or_f) == True:
                # add file to the list
                print os.path.normpath(p_or_f)
                files_to_do.append(os.path.normpath(p_or_f))
            elif os.path.isdir(p_or_f) == True:
                # walk about see what we can find
                files_to_do = walkabout(p_or_f, file_extension)
    return files_to_do        

def walkabout(p_or_f, file_extension):
    """ searches through a path p_or_f, picking up all files with EXTN
    returns these in an array.
    """
    return_files = []
    for root, dirs, files in os.walk(p_or_f, topdown=False):
        #print files
        for name in files:
            if (os.path.basename(name)[-3:]).upper() == file_extension:
                return_files.append(os.path.join(root,name))
    return return_files
    
def process_rdb_files(files_to_do, args):
    parameter_info = []
    
    for filename in files_to_do:      
        # print filename
        rdb_info = get_ole_data(filename)
        extracted_data = extract_parameters(filename, rdb_info, args)
        parameter_info += extracted_data

    
    # for exporting to Excel or CSV
    data = tablib.Dataset()    
    for k in parameter_info:
        data.append(k)
    data.headers = OUTPUT_HEADERS

    # don't overwrite existing file
    name = OUTPUT_FILE_NAME 
    if args.o == 'csv' or args.o == 'xlsx': 
        # this is stupid and klunky
        while os.path.exists(name + '.csv') or os.path.exists(name + '.xlsx'):
            name += '_'        

    # write data
    if args.o == None:
        pass
    elif args.o == 'csv':
        with open(name + '.csv','wb') as output:
            output.write(data.csv)
    elif args.o == 'xlsx':
        with open(name + '.xlsx','wb') as output:
            output.write(data.xlsx)

    if args.screen == True:
        display_info(parameter_info)
     
def get_ole_data(filename):
    data = []
    try:
        ole = OleFileIO_PL.OleFileIO(filename)
        listdir = ole.listdir()
        for direntry in listdir:            
            data.append([direntry, ole.openstream(direntry).getvalue()])
    except:
        print 'Failed to read streams in file: ' + filename
    return data

def extract_parameters(filename, rdb_info, args):
    parameter_info=[]
    for stream in rdb_info:
        for parameter in args.settings:
            # parameters are always:
            # Relays > Setting Name > Settings Files
            # so length is always at least 3
            category_file_list = None
            # lookup for group to file to restrict examination
            if parameter.find(PARAMETER_SEPARATOR) != -1:
                category_file_list = \
                    SEL_FILES_TO_GROUP[(parameter.split(PARAMETER_SEPARATOR))[0]]
                parameter = parameter.split(PARAMETER_SEPARATOR)[1]
            
            if len(stream[0]) >= 3 and \
                    (category_file_list is None \
                    or stream[0][-1].upper() in category_file_list \
                    ):
                return_value = extract_parameter_from_stream(parameter,\
                    stream[1])
                # print stream
                fid = extract_fid(stream[1])
                if return_value <> []:
                    filename = os.path.basename(filename)
                    settings_name = str(stream[0][1])
                    stream_name = (str(stream[0][-1])).upper()
                    # print stream[0][-1]
                    parameter_info.append([filename, settings_name,\
                        stream_name, parameter, return_value[0], fid[0]])
    return parameter_info

def extract_fid(stream):
    # FIDs look like this for example:
    return re.findall(SEL_FID_EXPRESSION, \
        stream, flags=re.MULTILINE)

def extract_parameter_from_stream(parameter,stream):      
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
        print display_line
   
if __name__ == '__main__':   
    # main(r'-o xlsx W:/Education/Current/20150430_Stationware_Settings_Applied/SNI G1:81D1P G1:81D1T G1:81D2P G1:81D2T G1:TR')
    #main(r'-o xlsx "W:/Education/Current/20150430_Stationware_Settings_Applied/SNI" G1:81D1P G1:81D1T G1:81D2P G1:81D2T G1:TR')
    if len(sys.argv) == 1 :
        main(r'-o xlsx in G1:81D1P G1:81D1T G1:81D2P G1:81D2T G1:TR')
    else:
        main()
    os.system("Pause")
        
