#!/usr/bin/env python3

import sel_logic_count

def getInstVals(name):
    """ For an instantiated variable type, get the usage
    so PLT13 returns PLT13S and PLT13R
    """
    type = name[0:3] # SEL variables all have a type 3 chars long
    num = name[3:]   #     and a value which is the remainder

    type_inst = sel_logic_count.RDBOperatorsConst.TYPES[type]
    types = [e.replace('xx', num).replace('$','') for e in type_inst]
    return types