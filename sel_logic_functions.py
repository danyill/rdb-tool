#!/usr/bin/env python3

import re

import helpers
import sel_logic_count

def getInstVals(name):
    """ For an instantiated variable type, get the usage
    so PLT13 returns PLT13S and PLT13R
    """
    type = name[0:3] # SEL variables all have a type 3 chars long
    num = name[3:]   #     and a value which is the remainder

    type_inst = sel_logic_count.RDBOperatorsConst.TYPES[type]
    types = [re.sub(r'x+', num, e).replace('$', '') for e in type_inst]
    return types

def change_type_vals(e, to):
    valsToChange = getInstVals(e)

    newVals = []
    if to.lower() in ['p', 'prot', 'protection']:
        newVals = ['P' + n[1:] for n in valsToChange]
        # TODO: Update to handle moving from the many AMV/ASVs to the few PMV/PSVs
    elif to.lower() in ['a', 'auto', 'automation']:
        newVals = ['A' + n[1:] for n in valsToChange]
        # TODO: Check this
        if newVals[0][0:3] in ['ASV','AMV']:
            newVals = [n[0:3] + '0' + n[3:] for n in newVals if n[0:3] in ['ASV','AMV']]
        #print(newVals)
    else:
        print("Error")

    return [valsToChange, newVals]

def makeLogicItems(e):
    find_lots = re.compile(r'^([A-Z]+)([0-9]{1,3})-([0-9]{1,3})$')
    find_digits = helpers.hasNumbers(e)

    result = find_lots.findall(e)

    items = None
    if result:
        items = sel_logic_count.make_limits(result[0][0],
                                            int(result[0][1]),
                                            int(result[0][2]))
    elif find_digits:
        items = [e]
    else:
        items = sel_logic_count.make_limits(e)
    return items