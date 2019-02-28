#!/usr/bin/env python3

import sel_logic_count

def getInstVals(name):
    """ For an instantiated variable type, get the usage
    so PLT13 returns PLT13S and PLT13R
    """
    type = name[0:3] # SEL variables all have a type 3 chars long
    num = name[3:]   #     and a value which is the remainder

    type_inst = sel_logic_count.RDBOperatorsConst.TYPES[type]
    types = [e.replace('xx', num).replace('$', '') for e in type_inst]
    return types

def change_type_vals(e, to):
    valsToChange = getInstVals(e)
    
    newVals = []
    if to.lower() in ['p', 'prot', 'protection']:
        newVals = ['P' + n[1:] for n in valsToChange]
        # TODO: Update to handle moving from the many AMV/ASVs to the few PMV/PSVs
    elif to.lower() in ['a', 'auto', 'automation']:
        newVals = ['A' + n[1:] for n in valsToChange]
        newVals = [n[0:3] + '0' + n[3:] for n in newVals if n[0:3] in ['ASV','AMV']]
        print(newVals)
    else:
        print("Error")

    return [valsToChange, newVals]    