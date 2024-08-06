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

        self.best_metrics = None
        self.best = False
        self.best_compliant = False
        self.best_compliant_h = False

    def __lt__(self, other):
        return compare_metrics(self.best_metrics, other.best_metrics, get_exec_prefs()[G_POLICY_NAME])

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

class HumanOption:
    __slots__ = ('action_pairs', 'in_step', 'human_action', 'robot_actions', 'robot_choice')
    def __init__(self, pairs: List[ActionPair]):
        self.action_pairs = pairs                   #type: List[ActionPair]
        self.in_step = None                         #type: Step | None
        self.human_action = pairs[0].human_action   #type: CM.Action
        self.robot_actions = []                     #type: List[CM.Action]
        
        # inits
        for p in pairs:
            self.robot_actions.append(p.robot_action)
            p.in_human_option = self
        self.robot_choice = None

    def getBestPair(self):
        return getattr(self, "best_pair_"+G_POLICY_NAME, None)
    def setBestPair(self, pair):
        setattr(self, "best_pair_"+G_POLICY_NAME, pair)

    def get_str(self):
        # ─ ┌ ┐ ├ ┤ │ └ ┘
        human_action_name = self.human_action.name if self.human_action.name!="PASSIVE" else "P"
        str_h = f"┌H{self.human_action.id}-{human_action_name}{self.human_action.parameters}┐"
        str_r = "│"
        sra_present = False
        for i, ra in enumerate(self.robot_actions):
            robot_action_name = ra.name if ra.name!="PASSIVE" else "P"
            str_r += f"R{ra.id}-{robot_action_name}{ra.parameters}│"

        l_h = len(str_h)
        l_r = len(str_r)

        if l_h<l_r:
            diff = l_r-l_h
            padding = ""
            for i in range(int(diff/2)):
                padding+="─"
            
            str_h = str_h[1:-1]
            if diff%2==1:
                str_h = "┌" + padding + str_h + padding + "─┐"
            else:
                str_h = "┌" + padding + str_h + padding + "┐"
        elif l_h>l_r:
            str_r = str_r[:-1]
            diff = l_h-l_r
            padding_f = ""
            for i in range(diff//2):
                padding_f+=" "
            padding_e = ""
            for i in range(diff-diff//2):
                padding_e+=" "
            str_r = str_r[0] + padding_f + str_r[1:] + padding_e + "│"

        l_end = max(len(str_h), len(str_r))-2
        str_end = ""
        for i in range(l_end):
            str_end+="─"
        str_end = "└" + str_end + "┘"

        return str_h, str_r, str_end
        
    def show(self):
        str_1, str_2, str_3 = self.get_str()
        print(str_1)
        print(str_2)
        print(str_3)

class BaseStep:
    __ID = 0 #type: int
    
    __slots__ = ('id', 'human_options', 'CRA', 'from_pair')
    def __init__(self):
        self.id = BaseStep.__ID
        BaseStep.__ID += 1
        self.human_options = []  #type: List[HumanOption]
        self.CRA = []                       #type: List[CM.Action] # Common Robot Actions
        self.from_pair = None

    def init(self, human_options: List[HumanOption], from_pair: ActionPair):
        self.human_options = human_options  #type: List[HumanOption]
        self.from_pair = from_pair
        # inits
        for ho in human_options:
            ho.in_step = self
        # Set next/previous of each pairs from new_step
        # Connect new pairs and expanded/select pair
        if from_pair!=None:
            all_step_pairs = self.get_pairs()
            from_pair.next += all_step_pairs
            for p in all_step_pairs:
                p.previous = from_pair

    def getBestPair(self):
        return getattr(self, "best_pair_"+G_POLICY_NAME, None)
    def setBestPair(self, pair):
        setattr(self, "best_pair_"+G_POLICY_NAME, pair)
        
    def isRInactive(self):
        for p in self.get_pairs():
            if not p.robot_action.is_passive():
                return False
        return True
    
    def isHInactive(self):
        for p in self.get_pairs():
            if not p.human_action.is_passive():
                return False
        return True

    def is_passive(self):
        return self.isRInactive() and self.isHInactive()
    
    def is_final(self):
        pairs = self.get_pairs()
        if len(pairs)==1:
            if pairs[0].is_final():
                return True
        return False

    def __lt__(self, other):
        return compare_metrics(self.get_f_leaf().branch_metrics, other.get_f_leaf().branch_metrics, get_exec_prefs()[G_POLICY_NAME])

    def get_nb_states(self):
        begin_pair = self.get_pairs()[0]
        return self.rec_get_nb_states(begin_pair)

    def rec_get_nb_states(self, p : ActionPair):
        nb_state = 1
        for c in p.next:
            nb_state += self.rec_get_nb_states(c)
        return nb_state

    def get_f_leaf(self):
        if not self.is_final():
            raise Exception("Not a final step!")
        return self.get_pairs()[0]
    
    def get_pairs(self) -> List[ActionPair]:
        pairs = [] #type: List[ActionPair]
        for ha in self.human_options:
            pairs += ha.action_pairs
        return pairs

    def get_final_leaves(self, tt_explore=False):
        leaves = []
        for leaf in self.leaves:
            if leaf.is_final():
                leaves.append(leaf)
        return leaves

    def show(self, last_line=True):
        print(self.str(last_line=last_line))

    def str(self, last_line=True):
        out_str = ""
        a_from = "" if self.from_pair==None else f"-{self.from_pair.get_short_str()}"
        out_str += f"========= Step{self}{a_from} =========\n"
        ho_l1, ho_l2, ho_l3 = [], [], []
        for ho in self.human_options:
            l1, l2, l3 = ho.get_str()
            ho_l1.append(l1)
            ho_l2.append(l2)
            ho_l3.append(l3)
        str_1, str_2, str_3 = "", "", ""
        for i in range(len(self.human_options)):
            str_1 += ho_l1[i] + " "
            str_2 += ho_l2[i] + " "
            str_3 += ho_l3[i] + " "
        out_str += str_1+"\n"
        out_str += str_2+"\n"
        out_str += str_3+"\n"
        if last_line:
            out_str += f"===============================\n"
        return out_str

    def get_str(self, with_bold=True):
        start_flags = ""
        end_flags = ""
        if self.is_final() and with_bold:
            # start_flags = CM.bcolors.BOLD + CM.bcolors.OKBLUE
            # end_flags = CM.bcolors.ENDC
            start_flags = "#"
            end_flags = "#"
        return start_flags + f"({self.id})" + end_flags

    def __repr__(self) -> str:
        return self.get_str()

class Step(BaseStep, NodeMixin):  # Add Node feature
    def __init__(self, *params, parent=None, children=None):
        super(Step, self).__init__(*params)
        self.parent = parent
        if children:
            self.children = children

def simplify_solution(s: Step):
    # simplify step
    for p in s.get_pairs():
        p.end_agents = None

    # base case
    if s.children==[]:
        return

    # recursion
    for c in s.children:
        simplify_solution(c)

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
def get_str_ranked_branches(ranked_leaves):
    lines = []
    i=0
    nb_same_rank = 0
    while i<len(ranked_leaves):
        line = ""
        leaf = ranked_leaves[i] #type: Step
        rank = leaf.get_f_leaf().getBestRank()
        
        metrics=""
        for m in leaf.get_f_leaf().branch_metrics.values():
            metrics+=f"{m} "
        line = f"\t#{rank}: [{metrics[:-1]}]:({leaf.id})"
        while i+1<len(ranked_leaves) and ranked_leaves[i].get_f_leaf().branch_metrics == ranked_leaves[i+1].get_f_leaf().branch_metrics:
            line += f",({ranked_leaves[i+1].id})"
            i+=1
            nb_same_rank += 1
        i+=1
        lines.append(line)

    str = ""
    for l in lines[::-1]:
        str += l + "\n"
    return str, nb_same_rank

def sorting_branches(final_leaves: List[Step]): # only for robot
    criteria = get_exec_prefs()[G_POLICY_NAME]

    x = np.array( final_leaves )
    ranked_leaves = np.sort(x)
    
    # Set ranks of final leafs
    for i, ranked_leaf in enumerate(ranked_leaves):
        same = True
        for m in criteria:
            if ranked_leaf.get_f_leaf().branch_metrics[m[0]] != ranked_leaves[i-1].get_f_leaf().branch_metrics[m[0]]:
                same=False
                break
        if i>0 and same:
            ranked_leaf.get_f_leaf().setBestRank( ranked_leaves[i-1].get_f_leaf().getBestRank() )
        else:
            ranked_leaf.get_f_leaf().setBestRank(i+1)


    return ranked_leaves

def get_exec_prefs():
    prefs = {
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

    return prefs

def update_robot_choices(init_step: Step):
    
    # Recursively compute the metrics of each pair of a human option

    # Compute best choice of a step:
    # for each human option, compute metrics of all pairs 
    #   (either by computing best choice of below and take metrics, or either by reasoning on double passive, or if pair.next is final just take metrics), then compare them to find best choice. 
    # Compare the best choices of each HO and find the best choice of the step (to be used in upper steps)
    
    init_step.setBestPair(init_step.get_pairs()[0])
    init_step.human_options[0].setBestPair(init_step.get_pairs()[0])
    
    step_one = init_step.children[0]
    compute_best_rank_from_step_robot(step_one)

def update_human_choices(init_step: Step):
    raise Exception("obsolete...")

def compute_best_rank_from_step_robot(step: Step):
    best_step_pair = None
    for ho in step.human_options:
        best_pair = None
        for pair in ho.action_pairs:
            # check if pair is double passive, if so don't consider it as a potential best pair
            if pair.is_passive() and not pair.human_action.is_wait_turn() and not pair.robot_action.is_wait_turn():
                continue
            elif pair.next == []:
                continue
            elif pair.next[0].is_final():
                pair.setBestRank( pair.next[0].getBestRank() )
            else:
                pair.setBestRank( compute_best_rank_from_step_robot(pair.next[0].get_in_step()) )

            if pair.getBestRank() == None:
                continue
            if best_pair==None or pair.getBestRank() <= best_pair.getBestRank():
                best_pair = pair    
            ho.setBestPair(best_pair)

        if ho.getBestPair() ==None:
            continue
        if best_step_pair==None or ho.getBestPair().getBestRank() <= best_step_pair.getBestRank():
            best_step_pair = ho.getBestPair()
    step.setBestPair(best_step_pair)

    result = best_step_pair.getBestRank() if best_step_pair!=None else None
    return result

def compute_best_rank_from_step_human(step: Step):
    raise Exception("Obsolete ....")

def compare_metrics(m1, m2, criteria):
    """ Returns True if m1 if better than m2 """
    if m1==None:
        return False
    elif m2==None:
        return True
    
    for m,maxi in criteria:
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


###########
## PRINT ##
###########
def show_solution(init_step: Step):
    lg.info(f"\n### SOLUTION ### [domain:{CM.g_domain_name}]")
    lg.info(RenderTree(init_step))
    for s in init_step.descendants:
        if not s.is_leaf:
            lg.info(f"{s.str(last_line=False)}")
    lg.info(f"Number of branches: {len(init_step.get_final_leaves())}")


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
