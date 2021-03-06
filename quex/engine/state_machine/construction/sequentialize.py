# Project Quex (http://quex.sourceforge.net); License: MIT;
# (C) 2005-2020 Frank-Rene Schaefer; 
from   quex.engine.state_machine.core import DFA
from   quex.engine.misc.tools         import typed
import quex.engine.misc.error         as     error


@typed(the_state_machine_list=[DFA])
def do(the_state_machine_list, 
       LeaveIntermediateAcceptanceStatesF = False, 
       MountToFirstStateMachineF          = False, 
       CloneRemainingStateMachinesF       = True):
    """Creates a state machine connecting all state machines in the array
    'state_machine_list'. When the flag 'LeaveIntermediateAcceptanceStatesF' is
    given as True, the connection points between the state machines will remain
    acceptances states. In any other case (e.g. the normal sequentialization)
    the connection points leave there acceptance status and only the last state
    machine in the list keeps its acceptance states.

    If MountToFirstStateMachineF is set, then the first state machine will
    contain the result of the concatination.
    """
    assert the_state_machine_list

    for sm in the_state_machine_list:   # DEBUG
        sm.assert_consistency()         # DEBUG

    if any(sm.is_Empty() for sm in the_state_machine_list):
        error.log("Empty state machine cannot be subject to concatenation.\n"
                  "It does not have an acceptance state.", the_state_machine_list[0].sr)

    # state machines with no states can be deleted from the list. they do not do anything
    # and do not introduce triggers.          
    state_machine_list = [
        sm for sm in the_state_machine_list if not sm.is_Nothing()
    ]
   
    if not state_machine_list:         return DFA.Nothing()
    elif len(state_machine_list) == 1: return state_machine_list[0]

    # (*) collect all transitions from both state machines into a single one
    #     (clone to ensure unique identifiers of states)
    result = state_machine_list[0]
    if not MountToFirstStateMachineF:  result = result.clone()

    # (*) need to clone the state machines, i.e. provide their internal
    #     states with new ids, but the 'behavior' remains. This allows
    #     state machines to appear twice, or being used in 'larger'
    #     conglomerates.
    appended_sm_list = state_machine_list[1:]
    if CloneRemainingStateMachinesF: 
        appended_sm_list = [sm.clone() for sm in appended_sm_list]

    # (*) all but last state machine enter the subsequent one, in case of SUCCESS
    #     NOTE: The start index is unique. Therefore, one can assume that each
    #           appended_sm_list's '.states' dictionary has different keys. One can simply
    #           take over all transitions of a start index into the result without
    #           considering interferences (see below)
    for appendix in appended_sm_list:
        appendix.assert_consistency() # DEBUG
        # Mount on every acceptance state the initial state of the following state
        # machine via epsilon transition.
        result.mount_to_acceptance_states(appendix.init_state_index, 
                                          CancelStartAcceptanceStateF = not LeaveIntermediateAcceptanceStatesF)
        for state_index, state in list(appendix.states.items()):        
            result.states[state_index] = state # state is already cloned (if desired), so no deepcopy here

    # (*) double check for consistency (each target state is contained in state machine)
    result.assert_consistency() # DEBUG
    return result
