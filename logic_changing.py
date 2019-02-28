#!/usr/bin/env python3

"""

This tool allows various useful operations to occur

"""

import re

from colorama import Fore, Back, Style

import sel_logic_count
import sel_logic_functions


logic = """
## ## AUTO RECLOSE LOGIC. CONSULT WITH TRANSPOWER BEFORE USING ## ##
# TIMER SETTINGS
PMV25 := 250.000000 # HV CB OPEN INTERVAL
PMV26 := 750.000000 # LV CB OPEN INTERVAL
PMV27 := 750.000000 # AUTO RECLOSE RECLAIM TIME
PMV28 := 500.000000 # MANUAL CLOSE RECLAIM TIME
PMV29 := 50.000000 # AUTO RECLOSE CLOSE SUPERVISION TIME
PMV30 := 9.000000 # CLOSE FAILURE TIME
# LOGIC SETTINGS
PSV29 := IN106 # AUTO RECLOSE INITIATE
PSV30 := 52CLS AND 52CLU AND PLT15 # RECLOSER INITIATE SUPERVISION
PSV31 := TRIP OR IN107 OR IN201 # DRIVE TO LOCKOUT CONDITIONS
PSV32 := 594P1 # HV CLOSE SUPERVISION CONDITION
PSV35 := 595P1 # LV CLOSE SUPERVISION CONDITION
#
# FIXED AUTO RECLOSE LOGIC PAST THIS POINT. DO NOT MODIFY #
PSV36 := NOT (52CLS AND 52CLU) # THREE POLE OPEN FOR BOTH TRANSFORMER BREAKERS
PLT15S := R_TRIG RB16
PLT15R := R_TRIG RB15
PCT16PU := 0.000000 # HV CB OPEN INTERVAL TIMER
PCT16DO := PMV25
PCT16IN := PLT21 AND R_TRIG PSV36
PCT17PU := 0.000000 # LV CB OPEN INTERVAL TIMER
PCT17DO := PMV26
PCT17IN := PLT21 AND R_TRIG PSV36
PCT18PU := 0.000000 # RECLOSE INITIATE SUPERVISION TIMER.
PCT18DO := 15.000000
PCT18IN := R_TRIG PLT21
PCT19PU := 0.000000 # AUTO RECLOSE RECLAIM TIMER
PCT19DO := PMV27
PCT19IN := PLT21 AND R_TRIG 52CLU
PCT20PU := PMV28 # MANUAL RECLAIM TIMER
PCT20DO := 0.000000
PCT20IN := PLT22 AND NOT PSV31 AND PSV30
PCT21PU := PMV30 # CB CLOSE FAILURE TIMER
PCT21DO := 1.000000
PCT21IN := PLT15 AND (PCT05Q AND NOT 52CLS OR PCT07Q AND NOT 52CLU)
PCT22PU := PMV29 # HV CLOSE SUPERVISION TIMER
PCT22DO := 0.000000
PCT22IN := PLT23
PCT23PU := PMV29 # LV CLOSE SUPERVISION TIMER
PCT23DO := 0.000000
PCT23IN := PLT24
# RESET STATE #
PLT20S := PLT22 AND R_TRIG PCT20Q OR PLT21 AND F_TRIG PCT19Q
PLT20R := R_TRIG PLT21 OR R_TRIG PLT22
# CYCLE STATE #
PLT21S := PLT20 AND PSV29 AND PSV30
PLT21R := R_TRIG PLT20 OR R_TRIG PLT22
# LOCKOUT STATE #
PLT22S := PSV31 OR (PLT20 AND F_TRIG PSV30) OR (F_TRIG PCT18Q AND NOT PSV36) OR PCT21Q OR PCT22Q OR PCT23Q OR F_TRIG PLT15 OR PFRTEX
PLT22R := R_TRIG PCT20Q
# AUTO RECLOSE CLOSE COMMANDS #
PLT23S := F_TRIG PCT16Q AND NOT PSV32 # HV RECLOSE SUPERVISION
PLT23R := R_TRIG PSV32 OR R_TRIG PCT22Q
PSV33 := (PLT21 AND F_TRIG PCT16Q AND PSV32) OR (PLT21 AND PLT23 AND R_TRIG PSV32) # HV CB CLOSE COMMAND
PLT24S := F_TRIG PCT17Q AND NOT PSV35 # LV RECLOSE SUPERVISION
PLT24R := R_TRIG PSV35 OR R_TRIG PCT23Q
PSV34 := (PLT21 AND F_TRIG PCT17Q AND PSV35) OR (PLT21 AND PLT24 AND R_TRIG PSV35) # LV CB CLOSE COMMAND
## END OF AUTO RECLOSE LOGIC ##
"""

class LogicLines:
    def __init__(self, text):
        self.text = text
        self.lines = []
        self.makeLines()
        
    def makeLines(self):
        all_lines = (self.text.strip()).split('\n')
        for idx, l in enumerate(all_lines):
            self.lines.append(Line(l, parent=self))

    def addLine(self, text):
        self.lines.append(Line(text, parent=self))
        self.text += '\n' + text

    def insertLine(self, n, text):
        self.lines.insert(n, Line(text, parent=self))
        self.text += '\n' + text

    def deleteLine(self, line):
        self.lines.remove(line)

    def deleteLineByIndex(self, n):
        del self.lines[n]

    def pretty_print(self):
        line_text = ''
        for l in self.lines:
            line_text += l.pretty_print() + '\n'

        return line_text + '\n' + '\n' + str(sel_logic_count.calc_logic_usage(str(self)))

    def __str__(self):
        """
        comment_lines = 0
        for l in self.lines:
            if l.type == 'comment':
                comment_lines += 1
        """
        #return 'Total Lines' + ' ' + str(len(self.lines)) + '\n' + 'Comment Lines' + ' ' + str(comment_lines)
        line_text = ''

        for l in self.lines:
            line_text += str(l) + '\n'

        return line_text 
                
class Line:
    """ an SEL logic line """

    def __init__(self, text, parent=None):
        self.parent = parent
        self.text = text
        self.type = None
        self.raw_text = sel_logic_count.removeComment(text).strip()
        COMMENTS = re.compile(r'^.*?(#+.*$)')
        comment = COMMENTS.findall(self.text)
        self.comment = '' if not comment else '' + comment[0].strip()

        if self.text.startswith('#'):
            self.type = 'comment'

    def getLine(self):
        return self.parent.lines.index(self)

    def pretty_print(self):
        if self.type == 'comment':
            return '{:<8}        {}'.format(Fore.BLUE + str(self.getLine()),
                                         Fore.RESET + self.raw_text.strip() + 
                                         Fore.GREEN + Style.DIM + self.comment +
                                         Fore.RESET + Style.RESET_ALL)
        else:
            elems = sel_logic_count.countElementsUsed(self.text) - 1
            return '{:<8} {:>8}    {}'.format(Fore.BLUE + str(self.getLine()), 
                                           Fore.LIGHTCYAN_EX + str(elems), 
                                           Fore.WHITE + self.raw_text +
                                           Fore.GREEN + Style.DIM + ' ' + self.comment +
                                           Fore.RESET + Style.RESET_ALL)

    def __str__(self):
        if len(self.raw_text) > 0:
            return self.raw_text + ' ' +  self.comment
        else:
            return self.comment

class LogicManipulator:

    def __init__(self, text):
        self.l = LogicLines(logic)

    def change_type(self, e, to):
        valsToChange = sel_logic_functions.getInstVals('PLT13')
        
        newVals = []
        if to.lower() in ['p', 'prot', 'protection']:
            newVals = ['P' + n[1:] for n in valsToChange]
        elif to.lower() in ['a', 'auto', 'automation']:
            newVals = ['A' + n[1:] for n in valsToChange]
        else:
            print("Error")

        print(valsToChange, newVals)

        """
        to: 'protection' or 'automation'

        """
        pass

    def convert_timer(e, from_type, to_type):
        """
        from_type --> to_type
        PCT           PST
        PST           PCT
        PCT           AST
        AST           PCT 
        """
        pass

    def reorder(type,start, exclude):
        """
        e.g. PSV, 1, [5]
         will reorder PSV01, 02, 03, 04, 06, 07 ...
         and return a dict of substitutions
        """
        pass

    def substitute_aliases(d):
        # accepts a dict
        pass

    def __str__(self):
        return str(self.l)


l = LogicManipulator(logic)
print(l)

#l.addLine('PSV99 := AST13S')
#print(l)
#print(l.lines[35].getLine())
"""
for k in l.lines.values():
    print(k)

"""


#print(sel_logic_count.getVariableRegex())
print()



print(l.l.pretty_print())
print(l.change_type('PLT13','a'))