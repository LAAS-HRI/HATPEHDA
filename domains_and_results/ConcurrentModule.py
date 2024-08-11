from typing import Any, Dict, List, Tuple
from copy import deepcopy, copy
import CommonModule as CM
from anytree import RenderTree, NodeMixin
import dill
import logging as lg
import logging.config
import sys
from statistics import mean
import numpy as np
import time

from progress.bar import IncrementalBarWithLeaf

logging.config.fileConfig(CM.path + 'log.conf')

import pstats


#############
## CLASSES ##
#############
class ActionPair:
    def __init__(self, human_action: CM.Action, robot_action: CM.Action):
        self.human_action = human_action    #type: CM.Action
        self.robot_action = robot_action    #type: CM.Action

        self.parent = None # id of parent PState
        self.child = None # id of child PState

        self._best_metrics = None
        self._best = False
        self._best_compliant = False
        self._best_compliant_h = False

        self._h_best_metrics = None
        self._h_best = False
        self._h_best_compliant = False
        self._h_best_compliant_h = False

    def set_best_metrics(self, value):
        attr_name = '_best_metrics'
        setattr(self, attr_name if CM.g_use_robot_metrics else '_h'+attr_name, value)
    def get_best_metrics(self):
        attr_name = '_best_metrics'
        return getattr(self, attr_name if CM.g_use_robot_metrics else '_h'+attr_name)

    def set_best(self, value):
        attr_name = '_best'
        setattr(self, attr_name if CM.g_use_robot_metrics else '_h'+attr_name, value)
    def get_best(self):
        attr_name = '_best'
        return getattr(self, attr_name if CM.g_use_robot_metrics else '_h'+attr_name)

    def set_best_compliant(self, value):
        attr_name = '_best_compliant'
        setattr(self, attr_name if CM.g_use_robot_metrics else '_h'+attr_name, value)
    def get_best_compliant(self):
        attr_name = '_best_compliant'
        return getattr(self, attr_name if CM.g_use_robot_metrics else '_h'+attr_name)

    def set_best_compliant_h(self, value):
        attr_name = '_best_compliant_h'
        setattr(self, attr_name if CM.g_use_robot_metrics else '_h'+attr_name, value)
    def get_best_compliant_h(self):
        attr_name = '_best_compliant_h'
        return getattr(self, attr_name if CM.g_use_robot_metrics else '_h'+attr_name)

    def __lt__(self, other):
        return compare_metrics( self.get_best_metrics(), other.get_best_metrics(), g_prefs[G_POLICY_NAME])

    def getBestRank(self):
        return getattr(self, "best_rank_"+G_POLICY_NAME)
    def setBestRank(self, rank):
        setattr(self, "best_rank_"+G_POLICY_NAME, rank)

    def is_passive(self) -> bool:
        return self.human_action.is_passive() and self.robot_action.is_passive()
    
    def both_active(self) -> bool:
        return not self.human_action.is_passive() and not self.robot_action.is_passive()

    def is_similar_to(self, pair) -> bool:
        return CM.Action.are_similar(self.human_action, pair.human_action) and CM.Action.are_similar(self.robot_action, pair.robot_action)
    
    def shared_resource_conflict(self) -> bool:
        return self.human_action.shared_resource!=None and self.robot_action.shared_resource!=None\
            and self.human_action.shared_resource == self.robot_action.shared_resource
        
    def is_begin(self) -> bool:
        return self.is_passive() and self.human_action.parameters[0]=="BEGIN" and self.robot_action.parameters[0]=="BEGIN"
    
    def is_final(self) -> bool:
        if self.human_action.is_idle() and self.robot_action.is_idle():
            return True
        if self.human_action.is_wait_turn() and self.robot_action.is_idle():
            if self.previous.human_action.is_idle() and self.previous.robot_action.is_wait_turn():
                return True
        if self.human_action.is_idle() and self.robot_action.is_wait_turn():
            if self.previous.human_action.is_wait_turn() and self.previous.robot_action.is_idle():
                return True
        return False

    def get_short_str(self) -> str:
        return f"{self.human_action.short_str()}{self.robot_action.short_str()}"

    def get_in_step(self):
        return self.in_human_option.in_step

    def __repr__(self):
        return f"H{self.human_action.id}-{self.human_action.name}{self.human_action.parameters}|R{self.robot_action.id}-{self.robot_action.name}{self.robot_action.parameters}"

G_POLICY_NAME = ""
def setPolicyName(policy_name):
    global G_POLICY_NAME
    G_POLICY_NAME = policy_name

#############
## EXPLORE ##
#############
def explore():

    CM.g_FINAL_IPSTATES = []
    CM.g_PSTATES = {0: CM.g_PSTATES[0]}
    CM.g_BACK_EDGES = []

    ipstates_to_explore = [0]
    bar = IncrementalBarWithLeaf("Exploring", max=len(ipstates_to_explore), width=60, suffix=" - %(elapsed_td)s - %(index)d/%(max)d")
    bar.set_n_leaf(0)
    while ipstates_to_explore!=[]:
        ipstates_to_explore = pstate_exploration(ipstates_to_explore)
        bar.max = max(bar.max, len(ipstates_to_explore))
        bar.set_n_leaf(len(CM.g_FINAL_IPSTATES))
        bar.goto(len(ipstates_to_explore))
    bar.finish()

    # Remove useless PStates
    ips_to_remove = []
    for ips in CM.g_PSTATES:
        ps = CM.g_PSTATES[ips]
        if ps.children==[] and ps.parents==[]:
            ips_to_remove.append(ips)
    print(f"Useless PStates to remove: {len(ips_to_remove)}")
    for ips in ips_to_remove:
        CM.g_PSTATES.pop(ips)

DEBUG_MSG = False
def pstate_exploration(ipstates_to_explore):
    selected_ipstate = select_pstate_to_explore(ipstates_to_explore)
    aapstates = compute_AAPStates(selected_ipstate)

    new_ipstates = extract_pstates_non_double_pass(aapstates)

    new_ipstates_to_explore = merge(new_ipstates, ipstates_to_explore)

    return new_ipstates_to_explore

def select_pstate_to_explore(ipstates_to_explore):
    selected_ipstate = ipstates_to_explore.pop(0)
    if DEBUG_MSG:
        print(" ")
        print(f"selected_ipstate={selected_ipstate}")
    return selected_ipstate

def compute_AAPStates(selected_ipstate):
    current_pstate = CM.g_PSTATES[selected_ipstate]

    human_pass = CM.Action.create_passive("H", "PASS")
    robot_pass = CM.Action.create_passive("R", "PASS")

    # Double passive AAPState
    double_pass_AAPState =  CM.AAPState( ActionPair(human_pass, robot_pass),  selected_ipstate)

    # Compute H starting pairs
    HS_AAPStates = [] #type: List[CM.AAPState]
    R_PASS_AAPStates = [] #type: List[CM.AAPState]
    HS_APStates_h = getAPStates('H', selected_ipstate)
    for h_apstate in HS_APStates_h:
        # robot pass
        if not h_apstate.action.is_passive():
            pair = ActionPair(h_apstate.action, robot_pass)
            R_PASS_AAPStates.append( CM.AAPState(pair, h_apstate.ipstate) )
        HS_APStates_r = getAPStates('R', h_apstate.ipstate)
        for r_apstate in HS_APStates_r:
            pair = ActionPair(h_apstate.action, r_apstate.action)
            HS_AAPStates.append( CM.AAPState(pair, r_apstate.ipstate) )

    # Compute R starting pairs
    RS_AAPStates = [] #type: List[CM.AAPState]
    H_PASS_AAPStates = [] #type: List[CM.AAPState]
    RS_APStates_r = getAPStates('R', selected_ipstate)
    for r_apstate in RS_APStates_r:
        # human pass
        if not r_apstate.action.is_passive():
            pair = ActionPair(human_pass, r_apstate.action)
            H_PASS_AAPStates.append( CM.AAPState(pair, r_apstate.ipstate) )
        RS_APStates_h = getAPStates('H', r_apstate.ipstate)
        for h_apstate in RS_APStates_h:
            pair = ActionPair(h_apstate.action, r_apstate.action)
            RS_AAPStates.append( CM.AAPState(pair, h_apstate.ipstate) )

    
    # Merge passive
    for hp in HS_AAPStates:
        if hp.action_pair.human_action.is_passive():
            # find corresponding pair in human_pass_aapstates
            for p in H_PASS_AAPStates:
                if CM.Action.are_similar(hp.action_pair.robot_action, p.action_pair.robot_action):
                    # and add type, if not already there
                    t = hp.action_pair.human_action.parameters[0]
                    if t not in p.action_pair.human_action.parameters:
                        p.action_pair.human_action.parameters.append(t)
        if hp.action_pair.robot_action.is_passive():
            # find corresponding pair in robot_pass_aapstates
            for p in R_PASS_AAPStates:
                if CM.Action.are_similar(hp.action_pair.human_action, p.action_pair.human_action):
                    # and add type, if not already there
                    t = hp.action_pair.robot_action.parameters[0]
                    if t not in p.action_pair.robot_action.parameters:
                        p.action_pair.robot_action.parameters.append(t)
    for rp in RS_AAPStates:
        if rp.action_pair.human_action.is_passive():
            # find corresponding pair in human_pass_pairs
            for p in H_PASS_AAPStates:
                if CM.Action.are_similar(rp.action_pair.robot_action, p.action_pair.robot_action):
                    # and add type, if not already there
                    t = rp.action_pair.human_action.parameters[0]
                    if t not in p.action_pair.human_action.parameters:
                        p.action_pair.human_action.parameters.append(t)
        if rp.action_pair.robot_action.is_passive():
            # find corresponding pair in robot_pass_pairs
            for p in R_PASS_AAPStates:
                if CM.Action.are_similar(rp.action_pair.human_action, p.action_pair.human_action):
                    # and add type, if not already there
                    t = rp.action_pair.robot_action.parameters[0]
                    if t not in p.action_pair.robot_action.parameters:
                        p.action_pair.robot_action.parameters.append(t)

    # Extract parallel
    parallel_AAPStates = [] #type: List[CM.AAPState]
    for hp in HS_AAPStates:
        if hp.action_pair.both_active():
            for rp in RS_AAPStates:
                if hp.action_pair.is_similar_to(rp.action_pair):
                    if not hp.action_pair.shared_resource_conflict():
                        parallel_AAPStates.append(hp)
                        break

    aapstates = parallel_AAPStates + H_PASS_AAPStates + R_PASS_AAPStates + [double_pass_AAPState]
    # TODO: Remove pstates from CM.g_PSTATES when not present in aapstates
    
    
    # check if over
    if HS_AAPStates[0].action_pair.is_final() and RS_AAPStates[0].action_pair.is_final():
        # update links of final pstate
        final_aapstate = HS_AAPStates[0]
        final_pstate = CM.g_PSTATES[final_aapstate.ipstate]
        idle_pair = final_aapstate.action_pair
        ###
        current_pstate.children.append(idle_pair)
        idle_pair.parent = current_pstate.id
        idle_pair.child = final_pstate.id
        final_pstate.parents.append(idle_pair) 
        final_pstate.possible_traces = []
        CM.g_FINAL_IPSTATES.append(final_pstate.id)
        ###
        return [final_aapstate]
    else:
        # update links
        current_pstate.children.append(double_pass_AAPState.action_pair)
        double_pass_AAPState.action_pair.parent = current_pstate.id
        for aapstate in aapstates:
            if not aapstate.action_pair.is_passive():
                new_pstate = CM.g_PSTATES[aapstate.ipstate]
                action_pair = aapstate.action_pair
                ###
                current_pstate.children.append(action_pair)
                action_pair.parent = current_pstate.id
                action_pair.child = new_pstate.id
                new_pstate.parents.append(action_pair) # should be equal to [action_pair]

    if DEBUG_MSG:
        print("pairs:")
        for aapstate in aapstates:
            print(f"\t- {aapstate.action_pair} -> ({aapstate.ipstate})")

    return aapstates

def extract_pstates_non_double_pass(aapstates: List[CM.AAPState]):
    ipstates = []

    for aapstate in aapstates:
        if not aapstate.action_pair.is_passive():
            ipstates.append(aapstate.ipstate)

    return ipstates


g_checked_ipstates = {0}
def merge(new_ipstates: List[int], ipstates_to_explore):
    global g_checked_ipstates

    new_ipstates_to_explore = set()

    for new_ips in new_ipstates:

        similar_found = False
        for ips in g_checked_ipstates:
            if CM.PState.are_similar(ips, new_ips):
                if DEBUG_MSG:
                    print(f"Merge found ({new_ips}) -> ({ips})")  

                similar_found = True

                # update pair child
                action_pair = CM.g_PSTATES[new_ips].parents[0] # type: ActionPair
                action_pair.child = ips

                # check if cycle
                iparents = rec_extract_parent_pstates(new_ips)
                if ips in iparents:
                    # store in back edges
                    CM.g_BACK_EDGES.append(action_pair)
                    print("back edge")
                    # remove from graph
                    CM.g_PSTATES[action_pair.parent].children.remove(action_pair)
                else:
                    # not a cycle, update similar state to connect pair
                    ps = CM.g_PSTATES[ips]
                    ps.parents.append(action_pair)
                
                # delete new_ips from g_PSTATES
                CM.g_PSTATES.pop(new_ips)
                break

        if not similar_found:
            g_checked_ipstates = g_checked_ipstates.union({new_ips})
            new_ipstates_to_explore = new_ipstates_to_explore.union({new_ips})

    new_ipstates_to_explore = list(new_ipstates_to_explore) + ipstates_to_explore
    
    if DEBUG_MSG:
        print(f"new_ipstate_to_explore= {new_ipstates_to_explore}")

    return new_ipstates_to_explore

def rec_extract_parent_pstates(ipstate, parents=set(), rec=False):
    if rec:
        parents = parents.union({ipstate})

    ps = CM.g_PSTATES[ipstate]
    if ps.parents==[]:
        return parents
    else:
        for ap in ps.parents:
            parents = parents.union( rec_extract_parent_pstates(ap.parent, parents, rec=True) )
        return parents

def extract_ipstates_to_explore(aapstates: List[CM.AAPState]):
    new_ipstates_to_explore = []

    for aapstate in aapstates:
        if not aapstate.action_pair.is_passive():
            new_ipstates_to_explore.append(aapstate.ipstate)

    return new_ipstates_to_explore

def compute_nb_final_leaves():
    final_leaves = []

    rec_compute_nb_leaves(0, final_leaves)

    final_leaves = set(final_leaves)
    return len(final_leaves)
def rec_compute_nb_leaves(current_ipstate, final_leaves):
    pstate = CM.g_PSTATES[current_ipstate]
    for action_pair in pstate.children:
        if action_pair.is_final():
            final_leaves.append( action_pair.child )
        elif not action_pair.is_passive():
            rec_compute_nb_leaves(action_pair.child, final_leaves)

def compute_non_final_leaves():
    non_final_leaves = [] # type: List[CM.PState]
    for s in CM.g_PSTATES.values():
        if len(s.children)==1 and s.children[0].is_passive() and not s.children[0].is_final():
            if not s in CM.g_FINAL_IPSTATES:
                non_final_leaves.append(s.id)

    return non_final_leaves

def prune_deadends():
    non_final_leaves = compute_non_final_leaves()

    while len(non_final_leaves):
        leaf_to_remove = CM.g_PSTATES[non_final_leaves.pop()]

        for parent_pair in leaf_to_remove.parents:

            parent_state = CM.g_PSTATES[parent_pair.parent]

            # Disconnect pair from parent_state
            parent_state.children.remove(parent_pair)

            # If parent_state becomes a leaf, then add it to list
            if len(parent_state.children)==1 and parent_state.children[0].is_passive():
                non_final_leaves.append(parent_state.id)


            # delete pair and leaf_to_remove
            # leaf_to_remove.parents.remove(parent_pair)
            parent_pair.parent = None
            parent_pair.child = None

        CM.g_PSTATES.pop(leaf_to_remove.id)
            

################
## REFINEMENT ##
################
def getAPStates(agent, ipstate) -> List[CM.APState]:
    # Format inputs
    s_ag = CM.g_static_agents[agent]

    current_pstate = CM.g_PSTATES[ipstate]

    if agent=='H': 
        agenda = current_pstate.H_agenda
    elif agent=='R':
        agenda = current_pstate.R_agenda

    state = current_pstate.state
    
    # Refine
    refinement = refine_agenda(agent, state, agenda)

    # Inspect and Apply refinement 
    apstates = [] #type: List[CM.APState]
    for dec in refinement.decompos:

        new_state = state

        # If not OK
        if not CM.DecompType.OK == dec.type:
            if CM.DecompType.NO_APPLICABLE_METHOD == dec.type:
                action = CM.Action.create_passive(agent, "WAIT")
                dec.type = CM.DecompType.OK
            elif CM.DecompType.AGENDA_EMPTY == dec.type:
                action = CM.Action.create_passive(agent, "IDLE")
                dec.type = CM.DecompType.OK
        
        # If OK
        else:

            # get PT operator
            if not s_ag.has_operator_for(dec.PT):
                raise Exception("Agent {} doesn't have an operator for {}".format(agent, dec.PT))
            op = s_ag.operators[dec.PT.name]
            
            # Copy current state to apply effects
            new_state = deepcopy(state)

            # Apply operator
            result = op.apply(new_state, dec.PT)
            if CM.OpType.NOT_APPLICABLE == result:
                dec.new_agenda = [dec.PT] + dec.new_agenda
                action = CM.Action.create_passive(agent, "WAIT")
            else:
                new_state, cost, shared_resource = result
                action = CM.Action.cast_PT2A(dec.PT, cost, shared_resource)

        new_agenda = dec.new_agenda + dec.subtasks[1:]

        # new PState
        new_pstate = CM.PState()
        CM.g_PSTATES[new_pstate.id] = new_pstate
        if agent=='R':
            new_pstate.R_agenda = new_agenda
            new_pstate.H_agenda = CM.g_PSTATES[ipstate].H_agenda
            new_pstate.state = new_state
        elif agent=='H':
            new_pstate.R_agenda = CM.g_PSTATES[ipstate].R_agenda
            new_pstate.H_agenda = new_agenda
            new_pstate.state = new_state

        # new APState
        new_apstate = CM.APState()
        new_apstate.action = action
        new_apstate.ipstate = new_pstate.id

        # Update apstates
        apstates.append(new_apstate)

        # Links
        # current_pstate.children.append(action)
        # action.parent = current_pstate.id
        # new_pstate.parents = [action]
        # action.children.append(new_pstate.id)


    return apstates

def refine_agenda(agent_name, state, agenda) -> CM.Refinement:
    """
    Refines the agenda of the given agent until reaching a primitive task.
    Return a refinement, including decompositions for each applied different method.
    """

    static_agent = CM.g_static_agents[agent_name]
    new_agenda = agenda[:]

    refinement = CM.Refinement()
    refinement.add(CM.Decomposition([]))    

    # Check if agenda is empty (no task to refine)
    if new_agenda == []:
        refinement.decompos[0].new_agenda = []
        refinement.decompos[0].type = CM.DecompType.AGENDA_EMPTY
    else:
        next_task = new_agenda.pop(0)
        # print("Task to refine: {}".format(next_task))
        
        refinement.decompos[0].subtasks = [next_task]
        refinement.decompos[0].new_agenda = new_agenda

        i=0
        # While we didn't reach the end of each decomposition, we start with one decomposition
        while i<len(refinement.decompos):
            current_decomp = refinement.decompos[i]
            # print("decomp i= {}".format(i))
            # While first subtask of current decomposition isn't a PT we keep refining
            while not current_decomp.first_task_is_PT_not_done(agent_name, state):
                task = current_decomp.subtasks[0]
                next_subtasks = current_decomp.subtasks[1:]

                # Either already refine the task with methods or 
                if task.is_abstract and static_agent.has_method_for(task):
                    list_decompo = refine_method(task, state, new_agenda)
                elif not task.is_abstract and static_agent.has_operator_for(task): 
                    list_decompo = [CM.Decomposition([task], agenda=new_agenda)]
                else:
                    raise Exception("task={} can't be handled by agent {}.".format(task, agent_name))

                # END, If no method is applicable
                if list_decompo == []:
                    current_decomp.subtasks = next_subtasks
                    current_decomp.new_agenda = [task] + new_agenda
                    current_decomp.type = CM.DecompType.NO_APPLICABLE_METHOD
                    # lg.debug("\t{} => {}".format(task, current_decomp.type))
                    break
                # There are applicable methods
                else:
                    # If we continue to refine with next tasks
                    need_continue = False
                    # If current method refines into nothing
                    if list_decompo[0].subtasks==[]:
                        # lg.debug(CM.bcolors.OKGREEN + "\trefines into nothing" + CM.bcolors.ENDC)
                        need_continue = True
                    # If next task is an operator already done
                    elif current_decomp.first_task_is_PT_done(agent_name, state): # CHECK list_decomp ? 
                        # lg.debug(CM.bcolors.OKGREEN + "\talready done" + CM.bcolors.ENDC)
                        need_continue = True
                    if need_continue:
                        # print("NEED_CONTINUE")
                        # If there are other subtasks we continue by refining the next one
                        if len(next_subtasks)>0:
                            # lg.debug("\tcontinue .. next_subtasks={}".format(next_subtasks))
                            current_decomp.subtasks = next_subtasks
                        # No other subtasks, we have to pop the next task in agenda to continue
                        else:
                            # END, If the agendas are empty
                            if new_agenda==[]:
                                current_decomp.subtasks = next_subtasks
                                current_decomp.type = CM.DecompType.AGENDA_EMPTY
                                # lg.debug("\t{} => {}".format(task, current_decomp.type))
                                break
                            # Agenda isn't empty, we can continue with next task in agenda
                            else:
                                next_task = new_agenda.pop(0)
                                # lg.debug("\tcontinue with next_task popped from agenda {}".format(next_task))
                                current_decomp.subtasks = [next_task]
                    # Update subtasks list and add new decompositions for each additional applicable methods
                    else:
                        current_decomp.subtasks = list_decompo[0].subtasks + next_subtasks
                        for j in range(1, len(list_decompo)):
                            j_subtasks = list_decompo[j].subtasks + next_subtasks
                            # print("\t\tdecomposition {} : created : {}".format(j, j_subtasks))
                            refinement.add(CM.Decomposition(j_subtasks, agenda=new_agenda))

            # End of the decomposition reached, we look for the next one
            # print("\tend {}".format(i))
            if len(current_decomp.subtasks)>0:
                current_decomp.PT = current_decomp.subtasks[0]
            i+=1

    return refinement

def refine_method(task_to_refine, state, new_agenda):
    agent_name = task_to_refine.agent
    static_agent = CM.g_static_agents[agent_name]

    # get methods
    if not static_agent.has_method_for(task_to_refine):
        raise Exception("{} has no methods for {}".format(agent_name, task_to_refine))
    methods = static_agent.methods[task_to_refine.name]

    # apply each method to get decompositions
    list_decomps = []
    for i,m in enumerate(methods):
        if m.is_done(state, task_to_refine):
            list_decomps.append(CM.Decomposition([]))
        elif m.is_applicable(state, task_to_refine):
            # dec_tuple = m.get_decomp(state, task_to_refine) # list(list(tuple(task_name: str, *params: Any)))
            multi_dec_tuple = m.get_decomp(state, task_to_refine) # list(list(tuple(task_name: str, *params: Any)))
            for dec_tuple in multi_dec_tuple:
                subtasks = []
                for tuple in dec_tuple:
                    task = tuple[0]
                    params = tuple[1:]
                    if task in static_agent.methods:
                        subtasks.append(CM.AbstractTask(task, params, task_to_refine, i, agent_name))
                    elif task in static_agent.operators:
                        subtasks.append(CM.PrimitiveTask(task, params, task_to_refine, i, agent_name))
                    else:
                        raise Exception("{} isn't known by agent {}".format(task, agent_name))

                list_decomps.append(CM.Decomposition(subtasks, agenda=new_agenda))

    return list_decomps


#############
## METRICS ##
#############
g_prefs = {
    "cart_pref1": [
        ("AxelsFirst",              True),
        ("TimeEndHumanDuty",        False),
        ("HumanEffort",             False),
        ("GlobalEffort",            False),
        ("TimeTaskCompletion",      False),
        ("PassiveWhileHolding",     False),
    ],
    "cart_esti11": [
        ("BodyFirst",               True),
        ("TimeTaskCompletion",      False),
        ("TimeEndHumanDuty",        False),
        ("HumanEffort",             False),
        ("GlobalEffort",            False),
        ("PassiveWhileHolding",     False),
    ],
    "cart_esti12": [
        ("TimeTaskCompletion",      False),
        ("TimeEndHumanDuty",        False),
        ("HumanEffort",             False),
        ("GlobalEffort",            False),
        ("TimeTaskCompletion",      False),
        ("PassiveWhileHolding",     False),
    ],

    "human_min_work": [
        ("Annoying",                True),
        ("HumanEffort",             False),
        ("GlobalEffort",            False),
        ("PassiveWhileHolding",     False),
        ("TimeTaskCompletion",      False),
        ("TimeEndHumanDuty",        False),
        ("NbDrop",                  False),
    ],

    "fake_human_free_early": [
        ("PlaceFirstBar",           True),
        ("TimeEndHumanDuty",        False),
        ("HumanEffort",             False),
        ("GlobalEffort",            False),
        ("TimeTaskCompletion",      False),
        ("PassiveWhileHolding",     False),
        ("NbDrop",                  False),
    ],

    "real_human_free_early": [
        ("TimeEndHumanDuty",        False),
        ("HumanEffort",             False),
        ("GlobalEffort",            False),
        ("TimeTaskCompletion",      False),
        ("PassiveWhileHolding",     False),
        ("NbDrop",                  False),
    ],

    "task_end_early": [
        ("TimeTaskCompletion",      False),
        ("TimeEndHumanDuty",        False),
        ("HumanEffort",             False),
        ("GlobalEffort",            False),
        ("PassiveWhileHolding",     False),
        ("NbDrop",                  False),
    ],
}

def compare_metrics(m1, m2, criteria):
    """ Returns True if m1 if better than m2 """
    if m1==None:
        return False
    elif m2==None:
        return True
    
    for m,maxi in criteria:
        # maxi = not maxi
        if m1[m] < m2[m]:
            return not maxi
        elif m1[m] > m2[m]:
            return maxi
        else:
            continue
    # If equal
    return True


############
## HELPER ##
############
def check_list(list, cond):
    """
    Returns None if the given condition (cond) is False for every element of the list
    Otherwise, return the first element for which the condition is True
    """
    for x in list:
        if cond(x):
            return x

#############
## DUMPING ##
#############
def dumping_solution():
    lg.info("Dumping solution...")
    s_t = time.time()
    sys.setrecursionlimit(100000)


    file_name = "search_space.p"

    dill.dump( (CM.g_domain_name, CM.g_PSTATES, CM.g_FINAL_IPSTATES, CM.g_BACK_EDGES) , open(CM.path + file_name, "wb"))
    lg.info("Solution dumped! - %.2fs" %(time.time()-s_t))

    f = open(CM.path + "dom_name.p", "w")
    f.write(f"domain_name: \"{CM.g_domain_name}\"")
    f.close()
