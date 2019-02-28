#!/usr/bin/env python3

"""

This tool simply counts logic used and spare logic and the number of elements used in a SELogic equation.

"""


import re

from named_constants import Constants
from helpers import flatten, unique, remove_empty
from intervals import get_interval_range, provide_string_range

class RDBOperatorsConst(Constants):
    """
    Information on variable types for ""SEL-400 series logic and
    regexes for processing of equations
    """
    TYPES = {'PSV': ['PSVxx'],
             'PMV': ['PMVxx'],
             'PLT': ['PLTxx$S$', 'PLTxx$R$', 'PLTxx'],
             'PCT': ['PCTxx$IN$', 'PCTxx$PU$', 'PCTxx$DO$', 'PCTxx$Q$'],
             'PST': ['PSTxx$IN$', 'PSTxx$PT$', 'PSTxx$R$', 'PSTxx$ET$', 'PSTxx$Q$'],
             'PCN': ['PCNxx$IN$', 'PCNxx$PV$', 'PCNxx$R$', 'PCNxx$CV$', 'PCNxx$Q$'],
             'ASV': ['ASVxxx'],
             'AMV': ['AMVxxx'],
             'ALT': ['ALTxx$S$', 'ALTxx$R$', 'ALTxx'],
             'AST': ['ASTxx$IN$', 'ASTxx$PT$', 'ASTxx$R$', 'ASTxx$ET$', 'ASTxx$Q$'],
             'ACN': ['ACNxx$IN$', 'ACNxx$PV$', 'ACNxx$R$', 'ACNxx$CV$', 'ACNxx$Q$']
            }

    LIMITS = {'PSV': [1, 64],
              'PMV': [1, 64],
              'PLT': [1, 32],
              'PCT': [1, 32],
              'PST': [1, 32],
              'PCN': [1, 32],
              'ASV': [1, 256],
              'AMV': [1, 256],
              'ALT': [1, 32],
              'AST': [1, 32],
              'ACN': [1, 32]
             }

    COMMENTS = re.compile(r'#.*')
    OPERATORS = re.compile(r'\+|\*|/')
    BOOL_OPERATORS = re.compile(r'\<|\>')
    EQUALITY_CHECK = r'='
    EQUATION_DEF = r'^\:\=$'
    NUMBERS = re.compile(r'^-?[0-9]*\.?[0-9]*$')
    LOGICAL_OPERATORS = re.compile(r'AND|NOT|OR|R_TRIG|F_TRIG')
    BRACKETS = re.compile(r'\(|\)')
    FUNCTIONS_RAW = ['ABS', 'ASIN', 'ACOS', 'CEIL', 'COS', 'EXP', 'FLOOR', 'LN', 'LOG', 'SIN', 'SQRT']
    FUNCTIONS = re.compile('|'.join([x + r'\(' for x in FUNCTIONS_RAW]))
    
def comp_sub(regex, list, replacement=''):
    """ carry out substitution on all elements in list """
    return [re.sub(regex, replacement, p) for p in list]

def comp_count(list, regex):
    """ combine array elements to a string and return counts of regex in the string """
    input_data = ' '.join(list)
    result = re.findall(regex, input_data)
    return len(result)

def getRawVariableFromTo(rdb_type):
    """
    Take a value from RDBOperatorsConst.TYPES (e.g. PSV$xx$ or PCT$xx$PU)
     1. Replace xx with regex to identify the number, PSV[0-9]{2}
     2. Remove the $ signs any suffix (remove the $ in $xx$ portion) <1>
     3. Remove the $xx$ portion entirely and replace with the first capture group.

    So given an input of PSV$xx$ this function returns:
     ['PSV([0-9]{2})', 'PSV\\1'] or
     ['PCT([0-9]{2})PU', 'PCT\\1']

    """
    number_regex = r'([0-9]{' + str(len(re.findall('x+', rdb_type)[0])) + '})'
    opWithRegex = re.sub('x+', number_regex, rdb_type)
    opWithRegexLessDollars = re.sub('\$', '', opWithRegex)
    # remove $xx$ portion
    opWithRegexLessDollarsBit = re.sub('\$.*\$', '', rdb_type)

    # replace with capture group
    newValue = re.sub('x+', r'\\1', opWithRegexLessDollarsBit)

    return [opWithRegexLessDollars, newValue]

def getVariableRegex(variable_info):
    """
    Given a variable in the form of PCT$xx$PU or PSV$xx$ return a regex of PSV([0-9]{2})
    """
    number_regex = r'([0-9]{' + str(len(re.findall('x+', variable_info)[0])) + '})'
    opWithRegex = re.sub('x+', number_regex, variable_info)
    # remove suffix or supplementary variable information
    opWithRegexLessDollarsBit = re.sub(r'\$.*\$', '', opWithRegex)
    return opWithRegexLessDollarsBit

def removeComment(eqn):
    """
    Remove comments from an equation received as a string
    """
    return re.sub(RDBOperatorsConst.COMMENTS,'', eqn.strip())

def eqnTokenise(eqn):
    """
    Tokenise an equation by splitting on whitespace
    """
    return eqn.split(" ")

def getEquationElements(eqnArr, keepNumbers=False, removeEmpty=True, uniqueOnly=True, sorted=True):
    """
    Remove cruft from equations:
     * Remove operators
     * Remove equation definition
     * Remove logical operators
     * Remove equality checks
     * Optionally remove numbers
    """

    notElements = [RDBOperatorsConst.OPERATORS,
                   RDBOperatorsConst.EQUATION_DEF,
                   RDBOperatorsConst.LOGICAL_OPERATORS,
                   RDBOperatorsConst.BOOL_OPERATORS,
                   RDBOperatorsConst.FUNCTIONS,
                   RDBOperatorsConst.BRACKETS,
                   RDBOperatorsConst.EQUALITY_CHECK]

    if not keepNumbers:
        notElements.append(RDBOperatorsConst.NUMBERS)

    for removal in notElements:
        eqnArr = comp_sub(removal, eqnArr)

    if removeEmpty:
        eqnArr = remove_empty(eqnArr)

    if uniqueOnly:
        eqnArr = unique(eqnArr)

    if sorted:
        eqnArr.sort()

    return eqnArr

def getSimpleLogicElements(arrEqnElements, uniqueOnly=True, sorted=True):
    """
    Given an array containing SEL logic variables, reduce them to the raw elements and
    return an array of them. Anything additional in the array should not be affected
    """

    # substitute all element types
    for key, value in RDBOperatorsConst.TYPES.items():
        for ident in value:
            # get regex
            [variableRegex, variableNameAndNumOnly] = getRawVariableFromTo(ident)
            # substitute
            arrEqnElements = comp_sub(variableRegex, arrEqnElements, variableNameAndNumOnly)

    if uniqueOnly:
        #print(arrEqnElements)
        arrEqnElements = unique(arrEqnElements)

    if sorted:
        arrEqnElements.sort()

    return arrEqnElements

def getEqnResidual(eqnArray, removeEmpty=True):
    """
    Given an array of RDB elements remove all known SELogic equation operators
    """
    # substitute all element types
    for key, value in RDBOperatorsConst.TYPES.items():
        variableName = getVariableRegex(value[0])
        eqnArray = comp_sub(variableName, eqnArray, '')

        if removeEmpty:
            eqnArray = remove_empty(eqnArray)

    return eqnArray

def getEqnArrayOfArraysResidual(arr, removeEmpty=True):
    # TODO: I can remove this?
    # Given an array of arrays ([lines] and [elements in equations])
    # Return the residual elements after removing operators and SELogic items
    return getEqnResidual(flatten(arr),removeEmpty)

def getLineComponents(eqn, keepNumbers=False, uniqueOnly=True):
    """
    For a given line return three arrays:
    [line containing logic types and RWBs] [only logic] [only RWBs]
    """
    raw_line = eqnTokenise(removeComment(eqn))
    # remove operators, brackets etc. TODO: Is ABS(x) more expensive than x? I don't take this into account
    raw_line = getEquationElements(raw_line, keepNumbers, uniqueOnly=uniqueOnly)
    eqn_elements = getSimpleLogicElements(raw_line, uniqueOnly=uniqueOnly)

    residual_elements = getEqnResidual(eqn_elements)

    logic_elements = [x for x in eqn_elements if x not in residual_elements]

    return [eqn_elements, logic_elements, residual_elements]

def countElementsUsed(eqn):
    """ 
    Counts the amount of logic used in an equation
    Can handle the use of functions
    """
    elements = getLineComponents(eqn, keepNumbers=True, uniqueOnly=False)
    functions = re.findall(RDBOperatorsConst.FUNCTIONS, eqn)
    return len(elements[0]) + len(functions)

def get_logic_usage(ltext):

    results = {}

    logic_lines = ltext.strip().split("\n")
    results['LINES'] = len(logic_lines)

    # lines without comments
    lines_less_comments = [removeComment(l) for l in logic_lines]

    # lines without blank or comment lines
    lines_nb_nc = remove_empty(lines_less_comments)
    results['LINES_UNCOMMENTED'] = len(lines_nb_nc)

    tokenised_lines = [[l.split(" ")] for l in lines_less_comments]

    raw_line_elements = []
    logic_elements = []
    residual_elements = []

    for line in logic_lines:
        [int_eqn_elements, int_logic_elements, int_residual_elements] = getLineComponents(line,keepNumbers=False)

        raw_line_elements.append(int_eqn_elements)
        logic_elements.append(int_logic_elements)
        residual_elements.append(int_residual_elements)

    # We are only interested in totals, so flatten the array and take only unique values
    logic_elements = unique(flatten(logic_elements))
    residual_elements = unique(flatten(residual_elements))

    logic_elements.sort()
    residual_elements.sort()

    for key, value in RDBOperatorsConst.TYPES.items():
        search_string = getVariableRegex(value[0])
        count = comp_count(logic_elements, search_string)
        results[key] = str(count)

    return [results, logic_elements, residual_elements]

def make_limits(name, min=False, max=False):
    """
    for a given variable, e.g. PSV return a full list
    within capability of SEL-400 series logic
    """
    if name in RDBOperatorsConst.LIMITS:
        
        if min and not max:
            lims = list(range(min, RDBOperatorsConst.LIMITS[name][1]+1))
        elif max and not min:
            lims = list(range(RDBOperatorsConst.LIMITS[name][0]+1,max))
        elif min and max:
            lims = [min, max]
        else:
            lims = RDBOperatorsConst.LIMITS[name]
        
        rng = list(range(lims[0], lims[1]+1))

        max_chars = str(len(str(lims[1])))
        return [name + ('{:0>' + max_chars + '}').format(str(r)) for r in rng]

def find_unused_logic(type, used, provideRaw=False, lowestAllowed=None, highestAllowed=None):
    # TODO: FIXME: lowestAllowed only works with provideRaw
    full_list = make_limits(type)
    if full_list != None:
        unused = [l for l in full_list if l not in used]
        regex_only_numbers = re.compile(r'^' + type)
        only_numbers = [int(re.sub(regex_only_numbers,'',val)) for val in unused]
        rng = get_interval_range(only_numbers)

        if provideRaw == False:
            return provide_string_range(rng)
        else:
            if lowestAllowed and not highestAllowed:
                return [u for u in unused if int(re.findall(r'[A-Z]+([0-9]+)[A-Z]*', u)[0]) >= lowestAllowed]
            elif not lowestAllowed and highestAllowed:
                return [u for u in unused if int(re.findall(r'[A-Z]+([0-9]+)[A-Z]*', u)[0]) <= highestAllowed]
            elif lowestAllowed and highestAllowed:
                return [u for u in unused if lowestAllowed <= int(re.findall(r'[A-Z]+([0-9]+)[A-Z]*', u)[0]) <= highestAllowed]
            else:
                return unused
    else:
        return ''

def calc_logic_usage(logic_text):
    """
    Calculate the logic usage.
    Just I think a calculation of the number of "residual elements"
    Where Numbers also count
    """
    returnval = ''
    r = get_logic_usage(logic_text)
    [usage_info, logic_used, residue] = r

    returnval += 'Lines Used (w/ comment lines):  ' + str(usage_info['LINES']) + '\n'
    returnval += 'Lines Used (w/o comment lines): ' + str(usage_info['LINES_UNCOMMENTED']) + '\n'

    del usage_info['LINES']
    del usage_info['LINES_UNCOMMENTED']
 
    for operator_type, used_qty in usage_info.items():
        total = RDBOperatorsConst.LIMITS[operator_type][1]
        returnval += ' '.join([operator_type,
              'Used:', '{:>3}'.format(used_qty),
              '/' ' {:<4}'.format(RDBOperatorsConst.LIMITS[operator_type][1]), 
              'Unused: {:<4.0%}   Available: '.format(1-int(used_qty)/total) + 
              find_unused_logic(operator_type, logic_used), '\n'])
    
    return returnval

def calc_usage_raw(logic_texts):
    """
    Calculate the logic usage.
    Just I think a calculation of the number of "residual elements"
    Where Numbers also count
    """

    usage_sum = {}

    r = get_logic_usage(logic_texts)
    [usage_info, logic_used, residue] = r

    usage_sum['Lines Used (w/ comment lines)'] = usage_info['LINES']
    usage_sum['Lines Used (w/o comment lines)'] = usage_info['LINES_UNCOMMENTED']

    del usage_info['LINES']
    del usage_info['LINES_UNCOMMENTED']
 
    for operator_type, used_qty in usage_info.items():
        total = RDBOperatorsConst.LIMITS[operator_type][1]
        usage_sum[operator_type] = {}
        usage_sum[operator_type]['qty'] = used_qty
        usage_sum[operator_type]['total'] = RDBOperatorsConst.LIMITS[operator_type][1]
        usage_sum[operator_type]['free_pu'] = (1-int(used_qty)/total)
        usage_sum[operator_type]['available_detail'] = find_unused_logic(operator_type, logic_used)

    return usage_sum

"""
 1. Make sure quickset is displaying non-aliased values
 2. Copy and paste logic below into the string logic_text between the quotes, (at start of lines)
 3. Copy and paste protection logic and then automation logic without blank lines (but then total lines is incorrect)
 4. Run.
"""

logic_text = """
APP_SEL := 1.000000 # BASE APPLICATION NUMBER AS PER SETTING GUIDE
## ## CUSTOM OC/EF, VOLTAGE AND OVERLOAD ELEMENTS FOR DESIGNER MODIFICATION## ##
#PHASE INST/DEFT LEVEL 1 SETTINGS (CUSTOM P1). OC(DEFT)LV1 OR OC(DEFT)MV1 (FOR ICTS). THIS ELEMENT CAN BE CHANGED TO OC(VCON,DEFT)LV1 BY CHANGING THE TORQUE CONTROL AS PER THE SETTING GUIDE
C67UP1P := 999.000000 # PICKUP, AMPS SECONDARY
C67UP1D := 999.000000 # DELAY, CYCLES
C67UP1C := 1 # TORQUE CONTROL
#PHASE INST/DEFT LEVEL 2 SETTINGS (CUSTOM P2). OC(DIREC, DEFT)LV1 OR OC(DEFT)MV1 ELEMENT FOR ICT
C67UP2P := 999.000000 # PICKUP, AMPS SECONDARY
C67UP2D := 999.000000 # DELAY, CYCLES
C67UP2C := (((APP_SEL <> 3.000000 AND UF32P) OR (APP_SEL = 5.000000 AND WF32P)) AND NOT PSV22) OR (APP_SEL = 3.000000) # TORQUE CONTROL
#PHASE INST/DEFT LEVEL 3 SETTINGS (CUSTOM P3). SPARE OC(DEFT)LV1 OR OC(DEFT)MV1 (FOR ICTS) ELEMENT FOR CUSTOM USE. THIS ELEMENT CAN BE VOLTAGE CONTROLLED BY CHANGING THE TORQUE CONTROL AS PER THE SETTING GUIDE
C67UP3P := 999.000000 # PICKUP, AMPS SECONDARY
C67UP3D := 999.000000 # DELAY, CYCLES
C67UP3C := 1 # TORQUE CONTROL
#PHASE INST/DEFT LEVEL 4 SETTINGS (CUSTOM P4). OC(SOTF). THIS IS THE PICKUP FOR SOTF ELEMENTS
C50USTF := 999.000000 # PICKUP, AMPS SECONDARY
#GROUND INST/DEFT LEVEL 1 SETTINGS (OPERATES FROM IGS) (CUSTOM G1). EF(DEFT)HV1 FOR YD SUPPLY BANK TRANSFORMERS AND INTERCONNECTING TRANSFORMER APPLICATIONS ONLY
C67SG1P := 999.000000 # PICKUP, AMPS SECONDARY
C67SG1D := 999.000000 # DELAY, CYCLES
C67SG1C := 1 # TORQUE CONTROL
#NEUTRAL INST/DEFT LEVEL 1 SETTINGS (OPERATES FROM IY2) (CUSTOM N1). EF(ALARM)1 FOR SUPPLY BANK TRANSFORMERS ONLY
C67UN1P := 999.000000 # PICKUP, AMPS SECONDARY
C67UN1D := 6000.000000 # DELAY, CYCLES
C67UN1C := 1 # TORQUE CONTROL
#GROUND INST/DEFT LEVEL 1 SETTINGS (OPERATES FROM IGU)(CUSTOM G1). EF(DEFT)LV1 AND EF(SOTF)LV1 (PICKUP ONLY) FOR SUPPLY BANK TRANSFORMERS ONLY
C67UG1P := 999.000000 # PICKUP, AMPS SECONDARY
C67UG1D := 999.000000 # DELAY, CYCLES
C67UG1C := 1 # TORQUE CONTROL
#VOLTAGE INST/DEFT LEVEL 1 SETTINGS (OPERATES FROM VPV)(CUSTOM V1). HV VT HEALTHY OVERVOLTAGE ELEMENT FOR SUPPLY BANK TRANSFORMERS ONLY
C59VV1P := 999.000000 # PICKUP, VOLTS SECONDARY
#VOLTAGE INST/DEFT LEVEL 2 SETTINGS (OPERATES FROM VPZ)(CUSTOM V2). LV/MV (FOR ICT) VT HEALTHY OVERVOLTAGE ELEMENT
C59ZV2P := 999.000000 # PICKUP, VOLTS SECONDARY
#
## ## USER CUSTOMISABLE TIMERS (SEE SETTING GUIDE) ## ##
PCT01PU := 0.000000 # S TERMINAL CB DROP OFF TIMER FOR REMOTE OPEN AND LAT
PCT01DO := 25.000000
PCT01IN := OCS OR IN203 OR (APP_SEL <> 3.000000 AND IN201)
PCT02PU := 0.000000 # T TERMINAL CB DROP OFF TIMER FOR REMOTE OPEN AND LAT
PCT02DO := 25.000000
PCT02IN := (APP_SEL = 4.000000 AND (OCT OR IN202 OR IN201))
PCT03PU := 0.000000 # U TERMINAL CB DROP OFF TIMER FOR REMOTE OPEN AND LAT
PCT03DO := 25.000000
PCT03IN := OCU OR IN201 OR ((APP_SEL <> 3.000000 OR APP_SEL <> 4.000000) AND IN203)
PCT04PU := 0.000000 # W TERMINAL CB DROP OFF TIMER FOR REMOTE OPEN AND LAT
PCT04DO := 25.000000
PCT04IN := APP_SEL = 5.000000 AND (OCU OR IN201 OR IN203)
PCT05PU := 0.000000 # CB S CLOSE DROPOFF TIMER
PCT05DO := 10.000000
PCT05IN := CLSS
PCT06PU := 0.000000 # CB T CLOSE DROPOFF TIMER
PCT06DO := 10.000000
PCT06IN := CLST
PCT07PU := 0.000000 # CB U CLOSE DROPOFF TIMER
PCT07DO := 10.000000
PCT07IN := CLSU
PCT08PU := 0.000000 # CB W CLOSE DROPOFF TIMER
PCT08DO := 10.000000
PCT08IN := CLSW
PST01PT := 100.000000 # TX TEMP(MAIN) TRIP
PST01R := NOT (IN208)
PST01IN := IN208
PST02PT := 100.000000 # TEMP(ET)/TEMP(LV) TRIP
PST02R := NOT (IN210)
PST02IN := IN210
PST03PT := 250.000000 # HV VT SUPERVISION  LOGIC
PST03R := NOT (APP_SEL <> 3.000000 AND (NOT (VAVFM > C59VV1P AND VBVFM > C59VV1P AND VCVFM > C59VV1P) AND (52CLS OR (APP_SEL = 4.000000 AND 52CLT))))
PST03IN := APP_SEL <> 3.000000 AND (NOT (VAVFM > C59VV1P AND VBVFM > C59VV1P AND VCVFM > C59VV1P) AND (52CLS OR (APP_SEL = 4.000000 AND 52CLT)))
PST04PT := 250.000000 # LV/MV (FOR ICTS) VT SUPERVISION LOGIC
PST04R := NOT (NOT (VAZFM > C59ZV2P AND VBZFM > C59ZV2P AND VCZFM > C59ZV2P) AND (52CLU OR (APP_SEL = 5.000000 AND 52CLW)))
PST04IN := NOT (VAZFM > C59ZV2P AND VBZFM > C59ZV2P AND VCZFM > C59ZV2P) AND (52CLU OR (APP_SEL = 5.000000 AND 52CLW))
PCT13PU := 0.000000 # LV/MV (FOR ICTS) VT VOLTAGE CONTROL PROTECTION
PCT13DO := 250.000000
PCT13IN := APP_SEL <> 3.000000 AND (VAZFM > C59ZV2P AND VBZFM > C59ZV2P AND VCZFM > C59ZV2P)
PCT14PU := 0.000000 # RESERVED FOR LV VOLTAGE CONTROL LATCHING LOGIC
PCT14DO := 0.000000
PCT14IN := 0
PST05PT := 20.000000 # 400MS DELAY (20 CYCLES). STAGE 2 TRIP OF HV CB
PST05R := NOT (APP_SEL <> 3.000000 AND (C49TRP OR REF50T2 OR C67UG1T))
PST05IN := APP_SEL <> 3.000000 AND (C49TRP OR REF50T2 OR C67UG1T)
PST06PT := 20.000000 # 400 MS DELAY (20 CYCLES). STAGE 2 TRIP OF MV/LV CB. INTERCONNECTING TRANSFORMER APPLICATIONS ONLY
PST06R := NOT (APP_SEL = 3.000000 AND C67SG1T)
PST06IN := APP_SEL = 3.000000 AND C67SG1T
PCT17PU := 0.000000 # SPARE. AVAILABLE FOR GENERAL USE
PCT17DO := 0.000000
PCT17IN := 0
PCT18PU := 0.000000 # SPARE. AVAILABLE FOR GENERAL USE
PCT18DO := 0.000000
PCT18IN := 0
#
## ## USER CUSTOMISABLE LATCHES FOR CONTROL (SEE SETTING GUIDE) ## ##
PLT01S := 0 # SPARE. AVAILABLE FOR GENERAL USE
PLT01R := 0 # SPARE. AVAILABLE FOR GENERAL USE
PLT02S := 0 # SPARE. AVAILABLE FOR GENERAL USE
PLT02R := 0 # SPARE. AVAILABLE FOR GENERAL USE
#
## ## INTERMEDIATE VARIABLE ## ##
PSV01 := PST01Q # TEMP(MAIN) TRIP OPERATED INTERMEDIATE VARIABLE
PSV02 := PST02Q # TEMP(ET) TRIP OR TEMP(LV)TRIP OPERATED INTERMEDIATE VARIABLE
PSV03 := REFF1 # RESTRICTED EARTH FAULT 1 PROTECTION OPERATED INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV04 := REFF2 # RESTRICTED EARTH FAULT 2 PROTECTION OPERATED INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV05 := REF50T1 # EF(DEFT,NEUT)HV1 PROTECTION OPERATED INTERMEDIATE VARIALBE USED FOR SCADA MAP
PSV06 := REF50T2 # EF(DEFT,NEUT)LV1 PROTECTION OPERATED INTERMEDIATE VARIALBE USED FOR SCADA MAP
PSV07 := C67UP1T # OC(DEFT)LV1 / OC(VCON,DEFT)LV1 / OC(DEFT)MV1 PROTECTION OPERATED. INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV08 := (PCT19Q OR PCT25Q) AND PCT26Q # OC(SOTF) PROTECTION OPERATED. INTERMEDIATE VARIABLE
PSV09 := C67UP2T # OC(DIREC,DEFT)LV PROTECTION OPERATED. INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV10 := C67UP3T # SPARE OC(DEFT)LV1 ELEMENT OPERATED. INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV11 := C67SG1T # EF(DEFT)HV1 PROTECTION OPERATED. INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV12 := C67UN1T # EF(ALARM)1 OPERATED. INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV13 := C67UG1T # EF(DEFT)LV1 PROTECTION OPERATED. INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV14 := FBFS # TERMINAL S BREAKER FAIL PROTECTION OPERATED INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV15 := FBFT # TERMINAL T BREAKER FAIL PROTECTION OPERATED INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV16 := FBFU # TERMINAL U BREAKER FAIL PROTECTION OPERATED INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV17 := FBFW # TERMINAL W BREAKER FAIL PROTECTION OPERATED INTERMEDIATE VARABLE USED FOR SCADA MAP
PSV18 := PST05Q OR (APP_SEL = 3.000000 AND PST06Q) # TWO STAGE PROTECTION ELEMENT OPERATED
PSV21 := APP_SEL <> 3.000000 AND (LOPV OR PST03Q) # HV VT SUPERVISION INTERMEDIATE VARIABLE
PSV22 := LOPZ OR PST04Q # LV/MV (FOR ICTS) VT SUPERVISION INTERMEDIATE VARIABLE
PSV23 := PTP_OK # PTP TIME SYNC OK. INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV24 := BUBCWAL # CB U WEAR EXCESSIVE. INTERMEDIATE VARIABLE USE FOR SCADA MAP
PSV25 := 0 # SPARE. AVAILABLE FOR GENERAL USE
PSV26 := 0 # SPARE. AVAILABLE FOR GENERAL USE
PSV27 := 0 # SPARE. AVAILABLE FOR GENERAL USE
PSV28 := 0 # SPARE. AVAILABLE FOR GENERAL USE
#
## ## FIXED LOGIC - CHANGES TO LOGIC BEYOND THIS POINT GENERALLY NOT REQUIRED ## ##
## CUSTOM OC/EF ELEMENTS AND CUSTOM OVERVOLTAGE ELEMENT PICKUPS ##
PSV20 := (APP_SEL <> 5.000000 AND (IAUFM > C67UP1P OR IBUFM > C67UP1P OR ICUFM > C67UP1P) AND C67UP1C)
C67UP1 := PSV20 OR (APP_SEL = 5.000000 AND (IAUWFM > C67UP1P OR IBUWFM > C67UP1P OR ICUWFM > C67UP1P) AND C67UP1C) # OC(DEFT)LV1 / OC(DEFT)MV1
PSV29 := APP_SEL <> 5.000000 AND (IAUFM > C67UP2P OR IBUFM > C67UP2P OR ICUFM > C67UP2P) AND C67UP2C
C67UP2 := PSV29 OR (APP_SEL = 5.000000 AND (IAUWFM > C67UP2P OR IBUWFM > C67UP2P OR ICUWFM > C67UP2P) AND C67UP2C) # OC(DIREC,DEFT)LV1"
PSV30 := APP_SEL <> 5.000000 AND ((IAUFM > C67UP3P OR IBUFM > C67UP3P OR ICUFM > C67UP3P) AND C67UP3C)
C67UP3 := PSV30 AND APP_SEL = 5.000000 AND ((IAUWFM > C67UP3P OR IBUWFM > C67UP3P OR ICUWFM > C67UP3P) AND C67UP3C) # SPARE OC(DEFT)LV1
C67SG1 := (APP_SEL <> 4.000000 AND (3I0SM > C67SG1P) AND C67SG1C) OR (APP_SEL = 4.000000 AND ((3I0STM > C67SG1P) AND C67SG1C)) # EF(DEFT)HV1
C67UN1 := (IY2FM > C67UN1P) AND C67UN1C # EF(ALARM)1
C67UG1 := ((APP_SEL <> 5.000000 AND 3I0UM > C67UG1P) OR (APP_SEL = 5.000000 AND 3I0UWM > C67UG1P)) AND C67UG1C # EF(DEFT)LV1
## CUSTOM SOTF ELEMENT, CUSTOM OC/EF ELEMENTS AND CUSTOM VOLTAGE ELEMENTS TIME DELAYED TRIPS ##
PCT19PU := 15.000000 #  SOTF ARMED 300MS AFTER CIRCUIT BREAKER S OR T (IF HV 1.5 CB) OPENED, SOTF ENABLED FOR 200MS AFTER CIRCUIT BREAKER S CLOSED
PCT19DO := 10.000000
PCT19IN := NOT (52CLS OR (APP_SEL = 4.000000 AND 52CLT))
PCT25PU := 15.000000 #  SOTF ARMED 300MS AFTER CIRCUIT BREAKER U (AND W WHERE DUAL LV INCOMERS EXIST) OPENED, SOTF ENABLED FOR 200MS AFTER THEY ARE CLOSED
PCT25DO := 17.500000
PCT25IN := NOT (52CLU OR (APP_SEL = 5.000000 AND 52CLW))
PCT26PU := 7.500000 # DELAY, CYCLES. 150MS SOTF OPERATE DELAY
PCT26DO := 0.000000
PSV31 := APP_SEL <> 5.000000 AND (IAUFM > C50USTF OR IBUFM > C50USTF OR ICUFM > C50USTF OR ((APP_SEL <> 3.000000) AND 3I0UM > C67UG1P))
PCT26IN := PSV31 OR (APP_SEL = 5.000000 AND (IAUWFM > C50USTF OR IBUWFM > C50USTF OR ICUWFM > C50USTF OR 3I0UWM > C67UG1P))
PCT27PU := C67UP1D
PCT27DO := 0.000000
PCT27IN := C67UP1
PCT28PU := C67UP2D
PCT28DO := 0.000000
PCT28IN := C67UP2
PCT29PU := C67UP3D
PCT29DO := 0.000000
PCT29IN := C67UP3
PCT30PU := C67SG1D
PCT30DO := 0.000000
PCT30IN := C67SG1
PCT31PU := C67UN1D
PCT31DO := 0.000000
PCT31IN := C67UN1
PCT32PU := C67UG1D
PCT32DO := 0.000000
PCT32IN := C67UG1
## CUSTOM OL(ET,NER)LV1 ELEMENT LOGIC NOT FOR CASUAL MODIFICATION ##
# ENSURE THAT AMV001 AMV002 AMV003 AMV004 ARE SET CORRECTLY IN AUTOMATION 1
C49TRP := IY2FM <= C49_IR # C = IM <= IR
C49_TH := IY2FM * IY2FM * C49_DT - C49__K * C49TRP # D = IM*IM*DT-K*C
PMV24 := PMV21 # X = B
PMV21 := PMV21 + C49_TH # B = B+D
PMV22 := PMV22 + (C49_TH - (PMV21 - PMV24)) # S = S + (D - (B-X))
PMV24 := PMV21 # X = B
PMV21 := PMV21 + PMV22 #  B = B+S
PMV22 := PMV22 - (PMV21 - PMV24) # S = S - (B-X)
C49TRP := (0.000000 < PMV21) AND NOT LB01 # TEST IF J/R < 0 OR LB01 = 1 RESET THERMAL STATE TO ZERO REQUEST
PMV21 := PMV21 * C49TRP # FORCE J/R B TO 0 IF J/R<0 OR LB01 = 1
PMV22 := PMV22 * C49TRP # FORCE J/R S TO 0 IF J/R<0 OR LB01 = 1
C49TRP := (PMV21 > C49__M) AND NOT AFRTEXP AND C67UN1 # TEST FOR TRIP AND BLOCK TRIP UNTIL AMVS ARE INITIALISED AND APPLY CURRENT GUARD
C49_TH := PMV21 / C49__M * 100.000000 # THERMAL STATE AS PERCENT
## LOCK BUTTON LOGIC ##
PLT03S := PST07Q AND NOT FP_LOCK
PLT03R := PB12PUL AND FP_LOCK
PST07PT := 150.000000
PST07R := NOT (PB12)
PST07IN := PB12 # LOCK/UNLOCK
# FRONT PANEL INTERMEDIATE VARIABLES
PSV32 := (APP_SEL <> 1.000000 AND APP_SEL <> 6.000000 AND C67SG1T) OR ((APP_SEL = 2.000000 OR APP_SEL = 4.000000 OR APP_SEL = 5.000000) AND REF50T1) # HV SYSTEM FAULT FRONT PANEL INTERMEDIATE VARIABLE
PSV33 := C67UP1T OR (APP_SEL <> 3.000000 AND (51T01 OR 51T02 OR REF50T2 OR 67UG1T OR C67UP3T OR C49TRP)) # MV/LV SYSTEM FAULT FRONT PANEL INTERMEDIATE VARIABLE
PSV34 := (PHA_U AND TRIPU) OR ((APP_SEL = 3.000000 OR APP_SEL = 5.000000) AND PHA_W AND TRIPW) # RED PH FRONT PANEL INDICATION INTERMEDIATE VARIABLE
PSV35 := (PHB_U AND TRIPU) OR ((APP_SEL = 3.000000 OR APP_SEL = 5.000000) AND PHB_W AND TRIPW) # YELLOW PH FRONT PANEL INDICATION INTERMEDIATE VARIABLE
PSV36 := (PHC_U AND TRIPU) OR ((APP_SEL = 3.000000 OR APP_SEL = 5.000000) AND PHC_W AND TRIPW) # BLUE PH FRONT PANEL INDICATION INTERMEDIATE VARIABLE
PSV37 := (APP_SEL <> 1.000000 AND APP_SEL <> 6.000000) AND (REFF1 OR C67SG1T) OR (APP_SEL <> 3.000000 AND (REFF2 OR C67UG1T OR REF50T2 OR C49TRP)) # EARTH FAULT FRONT PANEL INDICATION INTERMEDIATE VARIABLE 1
PSV38 := ((APP_SEL = 1.000000 OR APP_SEL = 6.000000) AND 591P1T) OR (APP_SEL = 3.000000 AND (592P1T OR 593P1T)) # EARTH FAULT FRONT PANEL INDICATION INTERMEDIATE VARIABLE 2



























































"""

logic_text_2 = """
## ## AUTO RECLOSE LOGIC. CONSULT WITH TRANSPOWER BEFORE USING ## ##
# TIMER SETTINGS
C79OI1 := 250.000000 # HV CB OPEN INTERVAL
C79OI2 := 750.000000 # LV CB OPEN INTERVAL
C79RCD := 750.000000 # AUTO RECLOSE RECLAIM TIME
C79MRCD := 500.000000 # MANUAL CLOSE RECLAIM TIME
C79CLSD := 50.000000 # AUTO RECLOSE CLOSE SUPERVISION TIME
C79CFD := 9.000000 # CLOSE FAILURE TIME
# LOGIC SETTINGS
C79RI := IN106 # AUTO RECLOSE INITIATE
C79RIS := 52CLS AND 52CLU AND PLT15 # RECLOSER INITIATE SUPERVISION
C79DTL := TRIP OR IN107 OR IN201 # DRIVE TO LOCKOUT CONDITIONS
C79CLS1 := 594P1 # HV CLOSE SUPERVISION CONDITION
C79CLS2 := 595P1 # LV CLOSE SUPERVISION CONDITION
#
# FIXED AUTO RECLOSE LOGIC PAST THIS POINT. DO NOT MODIFY #
C3POTX := NOT (52CLS AND 52CLU) # THREE POLE OPEN FOR BOTH TRANSFORMER BREAKERS
PLT15S := R_TRIG RB16
PLT15R := R_TRIG RB15
PCT16PU := 0.000000 # HV CB OPEN INTERVAL TIMER
PCT16DO := C79OI1
PCT16IN := PLT21 AND R_TRIG C3POTX
PCT17PU := 0.000000 # LV CB OPEN INTERVAL TIMER
PCT17DO := C79OI2
PCT17IN := PLT21 AND R_TRIG C3POTX
PCT18PU := 0.000000 # RECLOSE INITIATE SUPERVISION TIMER.
PCT18DO := 15.000000
PCT18IN := R_TRIG PLT21
PCT19PU := 0.000000 # AUTO RECLOSE RECLAIM TIMER
PCT19DO := C79RCD
PCT19IN := PLT21 AND R_TRIG 52CLU
PCT20PU := C79MRCD # MANUAL RECLAIM TIMER
PCT20DO := 0.000000
PCT20IN := PLT22 AND NOT C79DTL AND C79RIS
PCT21PU := C79CFD # CB CLOSE FAILURE TIMER
PCT21DO := 1.000000
PCT21IN := PLT15 AND (PCT05Q AND NOT 52CLS OR PCT07Q AND NOT 52CLU)
PCT22PU := C79CLSD # HV CLOSE SUPERVISION TIMER
PCT22DO := 0.000000
PCT22IN := PLT23
PCT23PU := C79CLSD # LV CLOSE SUPERVISION TIMER
PCT23DO := 0.000000
PCT23IN := PLT24
# RESET STATE #
PLT20S := PLT22 AND R_TRIG PCT20Q OR PLT21 AND F_TRIG PCT19Q
PLT20R := R_TRIG PLT21 OR R_TRIG PLT22
# CYCLE STATE #
PLT21S := PLT20 AND C79RI AND C79RIS
PLT21R := R_TRIG PLT20 OR R_TRIG PLT22
# LOCKOUT STATE #
PLT22S := C79DTL OR (PLT20 AND F_TRIG C79RIS) OR (F_TRIG PCT18Q AND NOT C3POTX) OR PCT21Q OR PCT22Q OR PCT23Q OR F_TRIG PLT15 OR PFRTEX
PLT22R := R_TRIG PCT20Q
# AUTO RECLOSE CLOSE COMMANDS #
PLT23S := F_TRIG PCT16Q AND NOT C79CLS1 # HV RECLOSE SUPERVISION
PLT23R := R_TRIG C79CLS1 OR R_TRIG PCT22Q
PSV33 := (PLT21 AND F_TRIG PCT16Q AND C79CLS1) OR (PLT21 AND PLT23 AND R_TRIG C79CLS1) # HV CB CLOSE COMMAND
PLT24S := F_TRIG PCT17Q AND NOT C79CLS2 # LV RECLOSE SUPERVISION
PLT24R := R_TRIG C79CLS2 OR R_TRIG PCT23Q
PSV34 := (PLT21 AND F_TRIG PCT17Q AND C79CLS2) OR (PLT21 AND PLT24 AND R_TRIG C79CLS2) # LV CB CLOSE COMMAND
## END OF AUTO RECLOSE LOGIC ##
"""

if __name__ == "__main__":
    #pass
    calc_logic_usage(logic_text_2)
    print(calc_usage_raw(logic_text_2))
    #e = "PSVxx = (PHA_U AND TRIPU) OR ((PMV63 = 3 OR PMV63 = 5) PHA_W AND TRIPW)"
    e2 = "(PSV44 OR PSV45 OR ((PMV64 = 2.000000 OR PMV64 = 4.000000 OR PMV64 = 5.000000) AND REF50T1)) AND R_TRIG TRIP # GROUND FAULT"

    #print(countElementsUsed(e))
    print(countElementsUsed(e2))
    
    #calc_logic_usage(e)
    #print(len(getLineComponents(e, keepNumbers=True)[0][1]))

"""
    Use paired parentheses to control the execution order of operations in a SELOGIC 
control equation. Use as many as 14 nested sets of parentheses in each SELOGIC 
control equation. The relay calculates the result of the operation on the innermost 
pair of parentheses first and then uses this result with the remaining operations. 
Table 13.17 is a truth table for an example operation that illustrates how paren-
theses can affect equation evaluation.

Could also add a check for this.
"""
