# Project Quex (http://quex.sourceforge.net); License: MIT;
# (C) 2005-2020 Frank-Rene Schaefer; 
#_______________________________________________________________________________
"""PURPOSE: Determine sets of matching lexemes for a given DFA.

This module analyzes paths through a DFA which reach an acceptance state
and provides them as a distinct set of lexemes. This result result is
built on Python immutables, so that quick comparison and hashing is 
possible. The main function of this module is 

    get(Dfa) ---> set of lexeme descriptions provided as a tuple
                  that has been recursively sorted.

Additionally, the string representation functions are provided which help
to display the lexeme sets:

    lexeme_set_to_string(...): provides a string with numeric interpretation
                               of the lexatoms.

    lexeme_set_to_character(...): provides a string where lexatoms are 
                                  interpreted as Unicode characters.

The latter provides expressions which are close to Regular Expressions
as used in 'lex'.

-------------------------------------------------------------------------------

INTERNALS:

A DFA is a directed graph with acceptance states. Any path that reaches such
an acceptance state represents an admissible sequence of lexatoms, i.e. a 
lexeme (actually already a set of lexemes). The set of paths to acceptance
states delivers then the set of lexemes which are matched by the given DFA.

DFAs, however, may describe lexemes of arbitrary length. To handle this the
lexeme element 'LOOP' is used. A 'LOOP' is an optional sequence of lexatoms
that may be arbitrarily repeated. For example the DFA

                      a          b          e
               ( 0 )----->( 1 )----->( 2 )----->(( 3 ))
                            '-----<--------'
                                 c

matches "abe", "abcbe", "abcbcbe" ... This is described internally as ("a",
"b", LOOP("bc"), "e"). The lexeme itself is described in numbers and and tuples
so that it is 'immutable'. This has significant advantages with respect to
hashing and set operations.

(C) 2017 Frank-Rene Schaefer
"""
import os
import sys
sys.path.insert(0, os.path.abspath("../../../../"))

from quex.engine.misc.interval_handling import NumberSet
from quex.engine.misc.quex_enum         import Enum
from copy import copy
from collections import defaultdict, namedtuple

from itertools import tee, takewhile

E_SubLexemeId = Enum("SEQUENCE", "NUMBER_SET", "LOOP")

Step = namedtuple("Step", ("by_trigger_set", "target_si"))

def __unicode_char(X):
    """Avoid problems with python's narrow build--do not use 'UNICHR()'."""
    return eval("u'\\U%08X'" % N)

def get(Dfa):
    """RETURNS: 'set' of lexeme which are matched by 'Dfa'.

    The lexeme representation is suited for quick comparison. All
    elements are *immutables*, so they may also serve as hash keys
    or set elements.

    * 'set' => provides distinctness
               Two 'DFA's match the same set of lexemes if and only if 
               the return values of this functions are the same
            => set operations on the set of lexemes can directly be 
               applied.

    * lexemes = 'tuples' which are also distinct, i.e. in places of 
               ambiguity they are sorted.
    """
    path_list, \
    loop_db    = __find_paths(Dfa)

    return set([ __expand(Dfa.init_state_index, path, loop_db) for path in path_list ])

def lexeme_set_to_string(LexemeSet):
    """RETURNS: List of strings each one representing a lexeme of 'LexemeSet'.

    Lexatoms are represented by numbers.
    """
    class Interpreter:
        @staticmethod
        def do(I):
            if I[0] == I[1]: return "%s" % I[0]
            else:            return "[%s-%s]" % (I[0], I[1])
        seperator     = ","
        right_bracket = "("
        left_bracket  = "("

    return [ __beautify(lexeme, Interpreter) for lexeme in sorted(LexemeSet) ]

def lexeme_set_to_characters(LexemeSet):
    """RETURNS: List of strings each one representing a lexeme of 'LexemeSet'.

    Lexatoms are represented by Unicode characters.
    """
    class Interpreter:
        @staticmethod
        def do(I):
            if I[0] == I[1]: return "%s" % __unicode_char(I[0])
            else:            return "[%s-%s]" % (__unicode_char(I[0]), __unicode_char(I[1]))
        seperator     = ""
        right_bracket = ""
        left_bracket  = ""

    return [ __beautify(lexeme, Interpreter) for lexeme in sorted(LexemeSet) ]

def get_immutable_for_number_set(N):
    def do_interval(I):
        return (I.begin, I.end - 1)

    interval_list = N.get_intervals(PromiseToTreatWellF=True)
    return tuple(__representation(interval_list, do_interval, 
                                  Prefix=E_SubLexemeId.NUMBER_SET))

def __representation(interval_list, do_interval, Prefix=None, Suffix=None):

    result = []

    if Prefix is not None: result.append(Prefix)

    result.extend(
        do_interval(interval) for interval in interval_list
    )

    if Suffix is not None: result.append(Suffix)

    return result

def __beautify(SubLexeme, Interpreter):
    return "".join(__beautify_sequence(SubLexeme, Interpreter))

def __beautify_sequence(SubLexeme, Interpreter):

    def next_tuple(sub_lexeme, i, L):
        if i == L - 1: return None, L
        else:          i += 1; return sub_lexeme[i], i

    txt = []
    L   = len(SubLexeme)
    i   = 0
    tpl = SubLexeme[i]
    while tpl is not None:
        while tpl is not None and tpl[0] == E_SubLexemeId.NUMBER_SET:
            txt.append(
                "".join(__representation(tpl[1:], Interpreter.do,
                        Interpreter.right_bracket, Interpreter.left_bracket))
            )
            tpl, i = next_tuple(SubLexeme, i, L)

        loop_txt = []
        while tpl is not None and tpl[0] == E_SubLexemeId.LOOP:
            loop_txt.append(
                "".join(__beautify_sequence(tpl[1:], Interpreter))
            )
            tpl, i = next_tuple(SubLexeme, i, L)

        if loop_txt:
            txt.append("(%s)*" % "|".join(loop_txt))

    return txt

def __expand(StartSi, path, loop_db):
    def loop_lexeme(StartSi, loop_path, loop_db):
        loop_lexeme = [ E_SubLexemeId.LOOP ]
        if len(loop_path) > 1:
            # sub_path = loop_path[:-1]
            sub_path = __expand(StartSi, loop_path[:-1], loop_db)
            loop_lexeme.extend(sub_path)

        last = get_immutable_for_number_set(loop_path[-1].by_trigger_set)
        loop_lexeme.append(last)
        return tuple(loop_lexeme)

    if not path: return []

    lexeme     = []
    current_si = StartSi
    for trigger_set, target_si in path:
        lexeme.append(get_immutable_for_number_set(trigger_set))
        lexeme.extend(sorted(loop_lexeme(StartSi, loop_path, loop_db)
                      for loop_path in loop_db[current_si]))
        current_si = target_si

    lexeme.extend(sorted(loop_lexeme(StartSi, loop_path, loop_db)
                  for loop_path in loop_db[current_si]))

    return tuple(lexeme)

def __find_paths(Dfa):
    """RETURNS: [0] List of paths
                [1] LoopDb: si --> path that comes back to 'si'

    where each 'path' is a sequence of (state index, trigger), representing the
    path through a Dfa. '(state index, trigger)' represents a transition to
    'state index' via the 'trigger'.
    """
    def is_on_path(path, si):
        """RETURNS: Index 'i' with path[i].si == si, if exists.
                    None, if 'si' is not on path. 
        """
        for i, step in enumerate(path):
            if step.target_si == si: return i
        return None

    loop_db   = defaultdict(list)
    path_list = []
    #           from where:  with what trigger:
    work_list = [ (Step(None,   Dfa.init_state_index), []) ]

    print("#Dfa:", Dfa.get_string(NormalizeF=False))
    while work_list:
        step, path = work_list.pop()
            
        path  = path + [step]
        si    = step.target_si

        state = Dfa.states[si]
        if state.is_acceptance(): 
            path_list.append(path[1:])

        for target_si, trigger_set in state.target_map:
            step     = Step(trigger_set, target_si)
            prev_pos = is_on_path(path, target_si)
            if prev_pos is not None:
                loop_db[si].append([step] + path[prev_pos+1:])
                print("#loop_db:", loop_db)
            else:
                work_list.append((step, path))

    print("#path_list:", path_list)
    return path_list, loop_db

if "__main__" == __name__: 
    import quex.input.regular_expression.engine as regex
    # re_str     = "x((ab*c|cd)*y)"
    # re_str     = "x(ab*c)*"
    # re_str     = "(ab(cb)*e)"
    re_str     = "(aXc)+"
    # re_str     = "(ab)+|(ac)+"
    dfa        = regex.do(re_str, {}, AllowNothingIsNecessaryF=True).sm
    lexeme_set = get(dfa)
    for i, lexeme in enumerate(lexeme_set_to_characters(lexeme_set)):
    # for i, lexeme in enumerate(lexeme_set):
        print("[%i] %s " % (i, lexeme))
