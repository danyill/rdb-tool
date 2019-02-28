#!/usr/bin/env python3

"""

This tool allows various useful operations to occur

"""

import re
from difflib import Differ

from colorama import Fore, Back, Style

import helpers
import sel_logic_count
import sel_logic_functions


ERR_START = Fore.RED + Back.LIGHTBLACK_EX + Style.BRIGHT
ERR_END = Fore.RESET + Back.RESET + Style.RESET_ALL

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

    def getDefinitions(self, df):
        result = []
        for l in self.lines:
            dfn = l.raw_text.split(':=')[0].strip()
            #print(dfn)
            if dfn == df:
                result.append(l)
        return result

    def replace(self, first, second):
        replacements = []
        for l in self.lines:
            result = l.replace(first, second)
            if result:
                replacements.append(l.getLine())
        self.updateLines()
        return replacements

    def updateLines(self):
        self.text = str(self)

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
        self.update()


    def getLine(self):
        return self.parent.lines.index(self)

    def replace(self, first, second, dummyRun=False, etype='equation',):
        new = None
        old = self.raw_text
        if etype == 'equation':
            new = self.raw_text.replace(first, second)
            if not dummyRun:
                self.raw_text = new
                self.update()
            return old != new
        else:
            print('Error!')

    def replace_line(self, raw, comment):
        self.raw_text = raw
        self.comment = comment
        self.type = None
        self.update()

    def update(self):
        if self.text.startswith('#'):
            self.type = 'comment'
        self.text = str(self)

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

    def change_type(self, e, to, onlyIfDefined=False):
        # onlyIfDefined= TODO: Not implemented yet
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

        # this might just be generic changes
        result = {}
        for var_to_change in items:
            things_to_change = sel_logic_functions.change_type_vals(var_to_change, to)
            changes = list(zip(things_to_change[0],
                            things_to_change[1]))

            for c in changes:
                lchange = self.l.replace(c[0], c[1])
                if lchange != []:
                    result[c] = lchange 
        return result

    def convert_timer(self, e, from_type, to_type):
        FREQUENCY = 50
        """
        from_type --> to_type
        PCT           PST
        PST           PCT
        PCT           AST
        AST           PCT
        """
        number_regex = re.compile(r'[A-Z]+([0-9]+)[A-Z]*')
        num = number_regex.findall(e)[0]

        if from_type == 'PCT' and to_type == 'AST':
            vals = sel_logic_functions.getInstVals(e)
            pu = [x for x in vals if x.endswith('PU')][0]
            do = [x for x in vals if x.endswith('DO')][0]
            inp = [x for x in vals if x.endswith('IN')][0]
            q = [x for x in vals if x.endswith('Q')][0]
            
            pu_def = self.l.getDefinitions(pu)[0]
            do_def = self.l.getDefinitions(do)[0]
            in_def = self.l.getDefinitions(inp)[0]
            q_def = self.l.getDefinitions(q)

            try:
                pu_time = float(pu_def.raw_text.split(':=')[1].strip()) 
            except ValueError:
                pu_time = pu_def.raw_text.split(':=')[1].strip()

            try:
                do_time = float(do_def.raw_text.split(':=')[1].strip()) 
            except ValueError:
                 do_time = do_def.raw_text.split(':=')[1].strip()

            in_val = in_def.raw_text.split(':=')[1].strip()
            
            print('Timer Info: PU: {} DO: {} IN: {}'.format(pu_time,do_time,in_val))

            if pu_time != 0 and do_time != 0:
                print(ERR_START + 'This will not end well, cannot replace timers with both PU and DO != zero, doing nothing' +
                      ERR_END)

            elif pu_time != 0 and do_time == 0:
                """
                pickup only 

                PCT01PU:= 5             AST01PT:= 5/50
                PCT01DO:= 0             AST01R:= NOT(X)
                PCT01IN:= X             AST01IN:= X
                Output == PCT01Q        Output == AST01Q
                """
                if isinstance(pu_time, float):
                    pu_def.replace_line('{}{}{} := {:-f}'.format('AST', num, 'PT', 
                                                                 round(pu_time/FREQUENCY,5)), 
                                                                 pu_def.comment)
                # Sometimes we set the time to a math variable, not a number!
                else:
                    print(ERR_START +  
                          'Need to _manually_ adjust {} time from cycles to seconds'.format(pu_time) + 
                          ERR_END)
                          # TODO: Recursive search for a numeric or convertible value. Complicated.
                    pu_def.replace_line('{}{}{} := {}'.format('AST', num, 'PT', 
                                                              pu_time), 
                                                              pu_def.comment)

                do_def.replace_line('{}{}{} := {}'.format('AST', num, 'R', 
                                                          'NOT(' + in_val + ')'),
                                                           pu_def.comment)
                in_def.replace_line('{}{}{} := {}'.format('AST', num, 'IN', 
                                                          in_val), 
                                                          pu_def.comment)
                self.l.replace(q, 'AST' + num + 'Q')
            
            elif pu_time == 0 and do_time != 0:
                """
                dropoff only 
                PCT01PU:= 25            AST01PT:= 25/50 * NOT AFRTEXP
                PCT01DO:= 0             AST01R:= X
                PCT01IN:= X             AST01IN:= NOT(X)
                Output == PCT01Q        Output == NOT(AST01Q)
                """
                if isinstance(pu_time, float):
                    pu_def.replace_line('{}{}{} := {:-f} * NOT AFRTEXP'.format('AST', num, 'PT', 
                                                                 round(pu_time/FREQUENCY,5)), 
                                                                 pu_def.comment)
                # Sometimes we set the time to a math variable, not a number!
                else:
                    print(ERR_START + 
                          'Need to _manually_ adjust {} time from cycles to seconds'.format(pu_time) + 
                          ERR_END)
                          # TODO: Recursive search for a numeric or convertible value. Complicated.
                    pu_def.replace_line('{}{}{} := {} * NOT AFRTEXP'.format('AST', num, 'PT', 
                                                              pu_time), 
                                                              pu_def.comment)

                do_def.replace_line('{}{}{} := {}'.format('AST', num, 'R', 
                                                           in_val),
                                                           pu_def.comment)
                in_def.replace_line('{}{}{} := {}'.format('AST', num, 'IN', 
                                                          'NOT' + '(' + in_val + ')'), 
                                                          pu_def.comment)
                self.l.replace(q, 'NOT' + '(' + 'AST' + num + 'Q' + ')')
                self.l.updateLines()
                print('Aha!')
                print(self.l.text)
                
                a = sel_logic_count.find_unused_logic('ASV', sel_logic_count.get_logic_usage(self.l.text)[1], provideRaw=True, lowestAllowed=37, highestAllowed=37)
                print(a)

                # We now end up with expressions like: 
                # F_TRIG NOT(AST18Q) or R_TRIG NOT(AST18Q)
                # which is invalid and we need another ASV allocation so that after AST18IN we have:
                # ASVxx := NOT(ASTQ18Q)
                # which we then replace
                # F_TRIG ASVxx and R_TRIG ASVxx

                # self.replace()

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

#print(l.change_type('PLT','a')) # PLT15 PLT05-15 PLT5-15 result output
#print(l.change_type('PCT','a')) # PLT15 PLT05-15 PLT5-15 result output
print(l.change_type('PSV','a')) # PLT15 PLT05-15 PLT5-15 result output
#print(l.change_type('PMV','a')) # PLT15 PLT05-15 PLT5-15 result output

"""
d = Differ()
old_text = str(l.l).split('\n')
#l.convert_timer('PCT20', 'PCT', 'AST')


new_text = str(l.l).split('\n')
result = list(d.compare(old_text, new_text))
result = [l for l in result if l[0:1] in '-+']
from pprint import pprint
pprint(result)
"""

print(l.l.pretty_print())

l.convert_timer('PCT18', 'PCT', 'AST')

#print(l.l.pretty_print())


"""def do_replacement(data, subs, callouts=False):

    Carries out replacement
    If key is also a value does not replace twice in the dict subs

    # for whole words only
    # pattern = re.compile(r'\b(' + '|'.join(d.keys()) + r')\b')
    pattern = re.compile('|'.join(subs.keys()))
    result = pattern.sub(lambda x: subs[x.group()], data)

    if callouts == False:
        # remove callouts
        result = re.sub('<[0-9]{1,3}>','',result)
"""