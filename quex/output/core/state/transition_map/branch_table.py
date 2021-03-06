# Project Quex (http://quex.sourceforge.net); License: MIT;
# (C) 2005-2020 Frank-Rene Schaefer; 
#_______________________________________________________________________________
from   quex.blackboard import Lng

class BranchTable(object):
    __slots__ = ("sub_map", "moat")
    def __init__(self, SubMap, Moat):
        self.sub_map = SubMap
        self.moat    = Moat

    def implement(self):
        """Transitions of characters that lie close to each other can be very 
        efficiently be identified by a switch statement. For example:

               switch( Value ) {
               case 1: ..
               case 2: ..
               ...
               case 100: ..
               }

        Is implemented by the very few lines in assembler (i386): 

               sall    $2, %eax
               movl    .L13(%eax), %eax
               jmp     *%eax

        where 'jmp *%eax' jumps immediately to the correct switch case.
        
        It is therefore of vital interest that those regions are *identified* 
        and *not split* by a bisection. To achieve this, such regions are made 
        a transition for themselves based on the character range that they 
        cover.
        """
        case_code_list = [
            (interval, Lng.TRANSITION_MAP_TARGET(interval, target))
            for interval, target in self.sub_map
            if target != self.moat
        ]

        return Lng.BRANCH_TABLE_ON_INTERVALS("input", case_code_list,
                   DefaultConsequence=Lng.TRANSITION_MAP_TARGET(None, self.moat))


