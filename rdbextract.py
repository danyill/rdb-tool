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
"""

__author__ = "Daniel Mulholland"
__copyright__ = "Copyright 2015, Daniel Mulholland"
__credits__ = ["Whoever wrote pdf-merge, pdftk, ghostscript, python!"]
__license__ = "GPL"
__version__ = '0.01'
__maintainer__ = "Daniel Mulholland"
__email__ = "dan.mulholland@gmail.com"
__file__ = r'W:\Education\Current\RDB Tool\''

import sys
import os
import argparse
import glob
import re

RDB_EXTENSION = '.rdb'
INPUT_FOLDER = "in"
BASE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),INPUT_FOLDER)
# this needs to be a character which can't be used in file RDB naming and
# SEL don't use it within their filename structure.
RDB_SEPARATOR = '/'
SEL_expression = r'[\w :+/\\()!,.-_\\*]*'
SEL_setting_EOL = r'\x1c\r\n'
SEL_setting_name = r'[\w _]*'

from thirdparty.OleFileIO_PL import OleFileIO_PL

def get_ole_data(filename):
    data = []
    try:
        ole = OleFileIO_PL.OleFileIO(filename)
        listdir = ole.listdir()
        for direntry in listdir:            
            #print direntry
            data.append([direntry, ole.openstream(direntry).getvalue()])
    except:
        print 'Failed to read streams.'
    return data

def main(arg=None):
    parser = argparse.ArgumentParser(
        description='Process individual or multiple RDB files and produce summary'\
            ' of results as a csv or xls file.',
        epilog='Enjoy. Bug reports and feature requests welcome. Feel free to build a GUI :-)',
        prefix_chars='-/')

    parser.add_argument('-o', choices=['csv','xls'],
                        help='Produce output as either comma separated values (csv) or as'\
                        ' a Micro$oft Excel .xls spreadsheet. If no output provided then'\
                        ' output is to the screen.')

    parser.add_argument('path', metavar='PATH|FILE', nargs=1, 
                       help='Go recursively go through path PATH. Redundant if FILE'\
                       ' with extension .rdb is used. When recursively called, only'\
                       ' searches for files with:' +  RDB_EXTENSION + '. Globbing is'\
                       ' allowed with the * and ? characters.')

    parser.add_argument('-d', '--design', action="store_true",
                       help='Attempt to determine Transpower standard design version and' \
                       ' include this information in output')
                       
    parser.add_argument('settings', metavar='G:S', type=str, nargs='+',
                       help='Settings in the form of G:S where G is the group'\
                       ' and S is the SEL variable name. If G: is omitted the default' \
                       ' group, 1 is selected. Otherwise G should be a comma delimited'\
                       ' list of groups of interest, or alternatively in the form of ' \
                       ' a hypenated group. Commas and hyphens can be joined so that ' \
                       ' a form of 1-2,6 is acceptable. S should be the setting name ' \
                       ' e.g. OUT201.' \
                       ' Examples: 1-2,6:50P1P or 1:50P1P or 1,2:50P1P or 50P1P' \
                       ' '\
                       ' Note: Applying a group for a non-grouped setting is unnecessary'\
                       ' and will not have any affect.')

    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)

    if arg == None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(arg.split())

    path_result = glob.glob(os.path.join(BASE_PATH,args.path[0]))

    files_to_do = return_file_paths(path_result, RDB_EXTENSION)
    if files_to_do != []:
        # print(files_to_do)
        process_rdb_files(files_to_do, args)
    else:
        print('Found nothing to do')
        sys.exit()

def process_rdb_files(files_to_do, args):
    parameter_info = []
    for filename in files_to_do:      
        # print filename
        rdb_info = get_ole_data(filename)
        # print rdb_info
        #parameter_info = extract_parameters(filename, rdb_info, args)
        #print parameter_info
        #display_info(parameter_info)
        parameter_info += extract_parameters(filename, rdb_info, args)
    #print parameter_info
    results_for_display = []
    #for k in parameter_info:
    #    results_for_display.join(k)
    display_info(parameter_info)

def display_info(parameter_info):
    lengths = []
    # first pass to determine column widths:
    for line in parameter_info:
        for index,element in enumerate(line):
            try:
                lengths[index] = max(lengths[index], len(element))
            except IndexError:
                lengths.append(len(element))
    
    parameter_info.insert(0,['File','Name','Setting','RDB','Val'])
    # now display in columns            
    for line in parameter_info:
        display_line = '' 
        for index,element in enumerate(line):
            display_line += element.ljust(lengths[index]+2,' ')
        print display_line

    # need to add sorting options

def extract_parameters(filename, rdb_info, args):
    parameter_info=[]
    for stream in rdb_info:
        for parameter in args.settings:
            # parameters are always:
            # Relays > Setting Name > Settings Files
            # so length is always at least 3
            if len(stream[0]) >= 3:
                return_value = extract_parameter_from_stream(parameter,\
                    stream[1])
                if return_value <> []:
                    filename = os.path.basename(filename)
                    settings_name = str(stream[0][1])
                    stream_name = str(stream[0][-1])
                    parameter_info.append([filename, settings_name,\
                        stream_name, parameter, return_value[0]])
    return parameter_info

def extract_parameter_from_stream(parameter,stream):
      return re.findall('^' + parameter + \
            ",\"(" + SEL_expression + ")\"" + \
            SEL_setting_EOL, \
            stream, flags=re.MULTILINE)

def return_file_paths(path_result, file_extension):
    files_to_do = []
    # make a list of files to iterate over
    if path_result != None:
        for p_or_f in path_result:
            if os.path.isfile(p_or_f) == True:
                # add file to the list
                files_to_do.append(os.path.realpath(p_or_f))
            elif os.path.isdir(p_or_f) == True:
                # walk about see what we can find
                files_to_do += walkabout(p_or_f, file_extension)
    return files_to_do
    
if __name__ == '__main__':
    main('*.rdb IN101D IN102D IN103D IN104D')

def arra():
  rdat = 'a'
  myfile = open('output/combined.txt', 'r')
  with myfile as f:
    rdat = f.read()

  print(rdat)

  
  #  print re.findall(pattern, string, flags)
  # print re.findall('^'+sys.argv[1]+'.*\r\n', rdat, flags=re.MULTILINE)

  # this is for finding named settings of sys.argv[1]
  print "variable of the name: " + sys.argv[1]

  variable_name = re.findall('^' + sys.argv[1] + ",\"([\w :+/()!,.-]*)\"\x1c\r\n", rdat, flags=re.MULTILINE)
  variable_name = re.findall('^' + sys.argv[1] + 
                             ",\"(" + SEL_expression + ")\"" + 
                             SEL_setting_EOL, 
                             rdat, flags=re.MULTILINE)

  print sys.argv[1] + '=' + str(variable_name)
  # SV1,"(51P1T+67P1T+67N1T+IN206+IN208*LT8+SV1)*50P5"
  print "used in: " 

  print re.findall('^' + SEL_setting_name + ",\"" + 
                   SEL_expression + sys.argv[1] + SEL_expression 
                   + "\"" + SEL_setting_EOL, 
                   rdat, flags=re.MULTILINE) 

  myfile.close()


def walkabout(p_or_f, file_extension):
    """ searches through a path p_or_f, picking up all files with EXTN
    returns these in an array.
    """
    return_files = []
    for root, dirs, files in os.walk(p_or_f, topdown=False):
        for name in files:        
            if os.path.basename(p_or_f)[0:-3] == file_extension:
                return_files.append(os.path.realpath(os.path.join(root,name)))
                print("Found: " + name)
    print('here you are sir')
    print return_files
