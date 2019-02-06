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
             'PLT': ['PLTxx$S$', 'PLTxx$R$'],
             'PCT': ['PCTxx$IN$', 'PCTxx$PU$', 'PCTxx$DO$', 'PCTxx$Q$'],
             'PST': ['PSTxx$IN$', 'PSTxx$PT$', 'PSTxx$R$', 'PSTxx$ET$',  'PSTxx$Q$'],
             'PCN': ['PCNxx$IN$', 'PCNxx$PV$', 'PCNxx$R$', 'PCNxx$CV$', 'PCNxx$Q$'],
             'ASV': ['ASVxx'],
             'AMV': ['AMVxxx'],
             'ALT': ['ALTxx$S$', 'ALTxx$R$'],
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
    Remove comments from an equtaion received as a string
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

def make_limits(name):
    """
    for a given variable, e.g. PSV return a full list
    within capability of SEL-400 series logic
    """
    if name in RDBOperatorsConst.LIMITS:
        lims = RDBOperatorsConst.LIMITS[name]
        rng = list(range(lims[0], lims[1]))
        max_chars = str(len(str(lims[1])))
        return [name + ('{:0>' + max_chars + '}').format(str(r)) for r in rng]

def find_unused_logic(type, used):
    full_list = make_limits(type)
    if full_list != None:
        unused = [l for l in full_list if l not in used]
        regex_only_numbers = re.compile(r'^' + type)
        only_numbers = [int(re.sub(regex_only_numbers,'',val)) for val in unused]
        rng = get_interval_range(only_numbers)
        return provide_string_range(rng)
    else:
        return ''

def calc_logic_usage(logic_text):
    """
    Calculate the logic usage.
    Just I think a calculation of the number of "residual elements"
    Where Numbers also count
    """
    r = get_logic_usage(logic_text)
    [usage_info, logic_used, residue] = r

    print('Lines Used (ignoring comments):', str(usage_info['LINES']))
    print('Lines Used (eliminating only comment lines):', str(usage_info['LINES_UNCOMMENTED']))

    del usage_info['LINES']
    del usage_info['LINES_UNCOMMENTED']
 
    for operator_type, used_qty in usage_info.items():
        print(operator_type,
              'Used:', '{:>3}'.format(used_qty),
              'Unused: ' + find_unused_logic(operator_type, logic_used))

"""
 1. Make sure quickset is displaying non-aliased values
 2. Copy and paste logic below into the string logic_text between the quotes, (at start of lines)
 3. Copy and paste protection logic and then automation logic without blank lines (but then total lines is incorrect)
 4. Run.
"""

logic_text = """
PMV63 := 1.000000 # BASE APPLICATION NUMBER AS PER SETTING GUIDE
## ## CUSTOM OC/EF, VOLTAGE AND OVERLOAD ELEMENTS FOR DESIGNER MODIFICATION## ##
#PHASE INST/DEFT LEVEL 1 SETTINGS (CUSTOM P1). OC(DEFT)LV1 OR OC(DEFT)MV1 (FOR ICTS). THIS ELEMENT CAN BE CHANGED TO OC(VCON,DEFT)LV1 BY CHANGING THE TORQUE T VOLTAGE CONTROL PROTECTION
PCT13DO := 250.000000
PCT13IN := PMV63 <> 3.000000 AND (VAZFM > PMV08 AND VBZFM > PMV08 AND VCZFM > PMV08)
PCT14PU := 0.000000 # RESERVED FOR LV VOLTAGE CONTROL LATCHING LOGIC
PCT14DO := 0.000000
PCT14IN := 0
PCT15PU := 20.000000 # 400MS DELAY (20 CYCLES). STAGE 2 TRIP OF HV CB
PCT15DO := 0.000000
PCT15IN := PMV63 <> 3.000000 AND (PSV19 OR REF50T2 OR PCT32Q)
PCT16PU := 20.000000 # 400 MS DELAY (20 CYCLES). STAGE 2 TRIP OF MV/LV CB. INTERCONNECTING TRANSFORMER APPLICATIONS ONLY
PCT16DO := 0.000000
PCT16IN := PMV63 = 3.000000 AND PCT30Q
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
PSV01 := PCT09Q # TEMP(MAIN) TRIP OPERATED INTERMEDIATE VARIABLE
PSV02 := PCT10Q # TEMP(ET) TRIP OR TEMP(LV)TRIP OPERATED INTERMEDIATE VARIABLE
PSV03 := REFF1 # RESTRICTED EARTH FAULT 1 PROTECTION OPERATED INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV04 := REFF2 # RESTRICTED EARTH FAULT 2 PROTECTION OPERATED INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV05 := REF50T1 # EF(DEFT,NEUT)HV1 PROTECTION OPERATED INTERMEDIATE VARIALBE USED FOR SCADA MAP
PSV06 := REF50T2 # EF(DEFT,NEUT)LV1 PROTECTION OPERATED INTERMEDIATE VARIALBE USED FOR SCADA MAP
PSV07 := PCT27Q # OC(DEFT)LV1 / OC(VCON,DEFT)LV1 / OC(DEFT)MV1 PROTECTION OPERATED. INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV08 := (PCT19Q OR PCT25Q) AND PCT26Q # OC(SOTF) PROTECTION OPERATED. INTERMEDIATE VARIABLE
PSV09 := PCT28Q # OC(DIREC,DEFT)LV PROTECTION OPERATED. INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV10 := PCT29Q # SPARE OC(DEFT)LV1 ELEMENT OPERATED. INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV11 := PCT30Q # EF(DEFT)HV1 PROTECTION OPERATED. INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV12 := PCT31Q # EF(ALARM)1 OPERATED. INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV13 := PCT32Q # EF(DEFT)LV1 PROTECTION OPERATED. INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV14 := FBFS # TERMINAL S BREAKER FAIL PROTECTION OPERATED INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV15 := FBFT # TERMINAL T BREAKER FAIL PROTECTION OPERATED INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV16 := FBFU # TERMINAL U BREAKER FAIL PROTECTION OPERATED INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV17 := FBFW # TERMINAL W BREAKER FAIL PROTECTION OPERATED INTERMEDIATE VARABLE USED FOR SCADA MAP
PSV18 := PCT15Q OR (PMV64 = 3.000000 AND PCT16Q) # TWO STAGE PROTECTION ELEMENT OPERATED
PSV21 := PMV63 <> 3.000000 AND (LOPV OR PCT11Q) # HV VT SUPERVISION INTERMEDIATE VARIABLE
PSV22 := LOPZ OR PCT12Q # LV/MV (FOR ICTS) VT SUPERVISION INTERMEDIATE VARIABLE
PSV23 := PTP_OK # PTP TIME SYNC OK. INTERMEDIATE VARIABLE USED FOR SCADA MAP
PSV24 := BUBCWAL # CB U WEAR EXCESSIVE. INTERMEDIATE VARIABLE USE FOR SCADA MAP
PSV25 := 0 # SPARE. AVAILABLE FOR GENERAL USE
PSV26 := 0 # SPARE. AVAILABLE FOR GENERAL USE
PSV27 := 0 # SPARE. AVAILABLE FOR GENERAL USE
PSV28 := 0 # SPARE. AVAILABLE FOR GENERAL USE
#
## ## FIXED LOGIC - CHANGES TO LOGIC BEYOND THIS POINT GENERALLY NOT REQUIRED ## ##
## CUSTOM OC/EF ELEMENTS AND CUSTOM OVERVOLTAGE ELEMENT PICKUPS ##
PSV20 := (PMV63 <> 5.000000 AND (IAUFM > PMV01 OR IBUFM > PMV01 OR ICUFM > PMV01) AND PSV41)
PSV51 := PSV20 OR (PMV63 = 5.000000 AND (IAUWFM > PMV01 OR IBUWFM > PMV01 OR ICUWFM > PMV01) AND PSV41) # OC(DEFT)LV1 / OC(DEFT)MV1
PSV29 := PMV63 <> 5.000000 AND (IAUFM > PMV02 OR IBUFM > PMV02 OR ICUFM > PMV02) AND PSV42
PSV52 := PSV29 OR (PMV63 = 5.000000 AND (IAUWFM > PMV02 OR IBUWFM > PMV02 OR ICUWFM > PMV02) AND PSV42) # OC(DIREC,DEFT)LV1"
PSV30 := PMV63 <> 5.000000 AND ((IAUFM > PMV03 OR IBUFM > PMV03 OR ICUFM > PMV03) AND PSV43)
PSV53 := PSV30 AND PMV63 = 5.000000 AND ((IAUWFM > PMV03 OR IBUWFM > PMV03 OR ICUWFM > PMV03) AND PSV43) # SPARE OC(DEFT)LV1
PSV54 := (PMV63 <> 4.000000 AND (3I0SM > PMV04) AND PSV44) OR (PMV63 = 4.000000 AND ((3I0STM > PMV04) AND PSV44)) # EF(DEFT)HV1
PSV55 := (IY2FM > PMV05) AND PSV45 # EF(ALARM)1
PSV56 := (PMV63 <> 5.000000 AND 3I0UM > PMV06) OR (PMV63 = 5.000000 AND 3I0UWM > PMV06) AND PSV46 # EF(DEFT)LV1
## CUSTOM SOTF ELEMENT, CUSTOM OC/EF ELEMENTS AND CUSTOM VOLTAGE ELEMENTS TIME DELAYED TRIPS ##
PCT19PU := 15.000000 #  SOTF ARMED 300MS AFTER CIRCUIT BREAKER S OR T (IF HV 1.5 CB) OPENED, SOTF ENABLED FOR 200MS AFTER CIRCUIT BREAKER S CLOSED
PCT19DO := 10.000000
PCT19IN := NOT (52CLS OR (PMV63 <> 4.000000 AND 52CLT))
PCT25PU := 15.000000 #  SOTF ARMED 300MS AFTER CIRCUIT BREAKER U (AND W WHERE DUAL LV INCOMERS EXIST) OPENED, SOTF ENABLED FOR 200MS AFTER THEY ARE CLOSED
PCT25DO := 17.500000
PCT25IN := NOT (52CLU OR (PMV63 <> 5.000000 AND 52CLW))
PCT26PU := 7.500000 # DELAY, CYCLES. 150MS SOTF OPERATE DELAY
PCT26DO := 0.000000
PSV31 := PMV63 <> 5.000000 AND (IAUFM > PMV09 OR IBUFM > PMV09 OR ICUFM > PMV09 OR ((PMV63 <> 3.000000) AND 3I0UM > PMV06))
PCT26IN := PSV31 OR (PMV63 = 5.000000 AND (IAUWFM > PMV09 OR IBUWFM > PMV09 OR ICUWFM > PMV09 OR 3I0UWM > PMV06))
PCT27PU := PMV11
PCT27DO := 0.000000
PCT27IN := PSV51
PCT28PU := PMV12
PCT28DO := 0.000000
PCT28IN := PSV52
PCT29PU := PMV13
PCT29DO := 0.000000
PCT29IN := PSV53
PCT30PU := PMV14
PCT30DO := 0.000000
PCT30IN := PSV54
PCT31PU := PMV15
PCT31DO := 0.000000
PCT31IN := PSV55
PCT32PU := PMV16
PCT32DO := 0.000000
PCT32IN := PSV56
## CUSTOM OL(ET,NER)LV1 ELEMENT LOGIC NOT FOR CASUAL MODIFICATION ##
# ENSURE THAT AMV001 AMV002 AMV003 AMV004 ARE SET CORRECTLY IN AUTOMATION 1
PSV19 := IY2FM <= AMV004 # C = IM <= IR
PMV23 := IY2FM * IY2FM * AMV001 - AMV002 * PSV19 # D = IM*IM*DT-K*C
PMV24 := PMV21 # X = B
PMV21 := PMV21 + PMV23 # B = B+D
PMV22 := PMV22 + (PMV23 - (PMV21 - PMV24)) # S = S + (D - (B-X))
PMV24 := PMV21 # X = B
PMV21 := PMV21 + PMV22 #  B = B+S
PMV22 := PMV22 - (PMV21 - PMV24) # S = S - (B-X)
PSV19 := (0.000000 < PMV21) AND NOT LB01 # TEST IF J/R < 0 OR LB01 = 1 RESET THERMAL STATE TO ZERO REQUEST
PMV21 := PMV21 * PSV19 # FORCE J/R B TO 0 IF J/R<0 OR LB01 = 1
PMV22 := PMV22 * PSV19 # FORCE J/R S TO 0 IF J/R<0 OR LB01 = 1
PSV19 := (PMV21 > AMV003) AND NOT AFRTEXP AND PSV55 # TEST FOR TRIP AND BLOCK TRIP UNTIL AMVS ARE INITIALISED AND APPLY CURRENT GUARD
PMV23 := PMV21 / AMV003 * 100.000000 # THERMAL STATE AS PERCENT
## LOCK BUTTON LOGIC ##
PLT03S := PCT24Q AND NOT PLT03
PLT03R := PB12PUL AND PLT03
PCT24PU := 150.000000
PCT24DO := 0.000000
PCT24IN := PB12
"""

if __name__ == "__main__":
    calc_logic_usage(logic_text)
    e = "(PCT27Q OR (PMV63 <> SIN(PMV62) AND (51T01 OR 51T02 OR REF50T2 OR 67UG1T OR PCT29Q OR PSV19)) OR (PMV63 = 3.000000 AND (67UQ1T OR PCT32Q))) AND R_TRIG TRIP AND TRIP"

    print(countElementsUsed(e))
    #calc_logic_usage(e)
    #print(len(getLineComponents(e, keepNumbers=True)[0][1]))