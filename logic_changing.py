#!/usr/bin/env python3

"""

This tool allows various useful operations to occur

"""

import sel_logic_count


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
        self.lines = {}
        self.lines_obj = {}

        self.makeLines()
        
    def makeLines(self):
        all_lines = (self.text.strip()).split('\n')
        for idx, l in enumerate(all_lines):
            self.lines[idx] = Line(l, parent=self)

        self.lines_obj = {v:k for k,v in self.lines.items()}

    def insertLine(self, n, text):

        pass

    def deleteLine(self, n):
        pass

    def __str__(self):
        """
        comment_lines = 0
        for l in self.lines:
            if l.type == 'comment':
                comment_lines += 1
        """
        #return 'Total Lines' + ' ' + str(len(self.lines)) + '\n' + 'Comment Lines' + ' ' + str(comment_lines)
        line_text = ''

        for idx, l in self.lines.items():
            line_text += str(l) + '\n'

        return line_text + '\n' + '\n' + str(sel_logic_count.calc_logic_usage(self.text))
                
class Line:
    """ an SEL logic line """

    def __init__(self, text, parent=None):
        self.parent = parent
        self.text = text
        self.type = ''
        self.raw_text = sel_logic_count.removeComment(text)

        if self.text.startswith('#'):
            self.type = 'comment'

    def getLine(self):
        return self.parent.lines_obj[self]

    def __str__(self):
        if self.type == 'comment':
            return '{:<4}     {}'.format(self.getLine(), self.text)
        else:
            elems = sel_logic_count.countElementsUsed(self.text) - 1
            return '{:<4} {:<3} {}'.format(self.getLine(), elems, self.text)
            

l = LogicLines(logic)
print(l)

#print(l.lines[35].getLine())
"""
for k in l.lines.values():
    print(k)

"""