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

from thirdparty.OleFileIO_PL import OleFileIO_PL

def arra():
  rdat = 'a'
  myfile = open('output/combined.txt', 'r')
  with myfile as f:
    rdat = f.read()

  print(rdat)

  SEL_expression = r'[\w :+/\\()!,.-_\\*]*'
  SEL_setting_EOL = r'\x1c\r\n'
  SEL_setting_name = r'[\w _]*'
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


def save_stream (ole, stream):
    fname = str(stream).replace('/','_')
    if fname is not None:
        f = open(os.path.join('output',fname), 'wb')
        data = ole.openstream(stream).getvalue()
        f.write(data)
        f.close()

def process_ole_streams(filename):
    try:
        ole = OleFileIO_PL.OleFileIO(filename)
        listdir = ole.listdir()
        streams = []
        dantest = []
        for direntry in listdir:            
            for i, val in enumerate(direntry):
                print str(i) + " " + val + " " + str(dantest)
                if i <= len(dantest)-1 and dantest != []: 
                    print dantest[i]
                    if dantest[i][0] == val:
                        #dantest[i][0].append(val)
                        pass
                    else:
                        print('hi')
                        dantest.append([val])
                elif dantest == [] or i > len(dantest):
                    print('really')
                    dantest.append([val])
            sys.exit()
        print dantest
        print streams
        #for r in streams:
        #    # print r
        #    save_stream(ole, r)
    except:
        print 'Failed to read streams.'

def start(arg=None):
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
        print(files_to_do)
        process_rdb_files(files_to_do, args)
    else:
        print('Found nothing to do')
        sys.exit()
    
    #print args.settings
    #print args.design
    #print args.path

def process_rdb_files(files_to_do, args):
    for filename in files_to_do:      
        rdb_info = process_ole_streams(filename)
    pass


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
    
if __name__ == '__main__':
    start('test.rdb asdf')
    
