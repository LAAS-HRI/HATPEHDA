"""
HATPEHDA, version 1.0.0 -- an HTN planner emulating human decisions and actions written in Python, inspired from PyHop (under Apache 2.0 License)
Author: Guilhem Buisan

Copyright 2020 Guilhem Buisan

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from copy import deepcopy
import sys
from enum import Enum
from typing import Any, Dict

sys.path.append("/home/afavier/ws/HATPEHDA/hatpehda")

import gui

import CommonModule as CM
import NodeModule as NM


############################################################

class DecompType(Enum):
    OK = 0
    NO_APPLICABLE_METHOD = 1
    AGENDA_EMPTY = 2
    BOTH_AGENDAS_EMPTY = 3
class OpType(Enum):
    OPERATOR_NOT_APPLICABLE = 0
    OPERATOR_DONE = 1
class ObsType(Enum):
    NON_OBS = 0
    INF = 1
    OBS = 2


class Task:
    __ID = 0
    def __init__(self, name, parameters, why, decompo_number, agent):
        self.id = Task.__ID
        Task.__ID += 1
        self.name = name
        self.parameters = parameters
        self.agent = agent
        self.why = why  # From which task it is decomposed
        self.decompo_number = decompo_number  # The number of the decomposition from the abstract task (self.why)
        self.applicable = True
        self.previous = None
        self.next = []

    def assign_next_id(self):
        self.id = Task.__ID
        Task.__ID += 1
    
    def __repr__(self):
        if self.agent == CM.g_human_name:
            return "{}-{}-{}{}".format(self.id, "H", self.name, self.parameters)
        elif self.agent == CM.g_robot_name:
            return "{}-{}-{}{}".format(self.id, "R", self.name, self.parameters)
        else:
            return "{}-{}-{}{}".format(self.id, self.agent, self.name, self.parameters)

    def show(self):
        print(self)

class Operator(Task):
    COST_COM = 3.0

    def __init__(self, *args):
        if len(args) == 5:
            name = args[0]
            parameters = args[1]
            agent = args[2]
            why = args[3]
            decompo_number = args[4]
            super().__init__(name, parameters, why, decompo_number, agent)
        elif len(args) == 1:
            t = args[0]
            self.name = t.name
            self.parameters = t.parameters
            self.agent = t.agent
            self.why = t.why
            self.decompo_number = t.decompo_number
        self.cost = 0.0
        self.current_plan_cost = 0.0
        self.branching_name = ""
        self.agent_agendas = {"robot":[], "human":[]}

    @staticmethod
    def copy_new_id(other):
        new = deepcopy(other)
        new.assign_next_id()
        return new

    def __repr__(self):
        if self.agent == CM.g_human_name:
            return "{}-{}P-{}{}-{}".format(self.id, "H", self.name, self.parameters, self.cost)
        elif self.agent == CM.g_robot_name:
            return "{}-{}P-{}{}-{}".format(self.id, "R", self.name, self.parameters, self.cost)
        else:
            return "{}-{}P-{}{}-{}".format(self.id, self.agent, self.name, self.parameters, self.cost)

    def copy_and_init(self, cost, current_cost, branching_name, previous_action):
        action = Operator.copy_new_id(self)
        action.cost = cost
        action.branching_name = branching_name
        action.current_plan_cost = current_cost + action.cost
        action.previous = previous_action
        if action.previous!=None:
            action.previous.next.append(action)
        return action
    
    def create_inactivity_op(name, cost, agent_name, previous_action, current_cost, branching_name=None):
        action = Operator(name, [], agent_name, None, 0)
        action.cost = cost
        action.previous = previous_action
        if action.previous!=None:
            action.previous.next.append(action)
        action.current_plan_cost = current_cost + action.cost
        if branching_name==None:
            action.branching_name = previous_action.branching_name
        else:
            action.branching_name = branching_name
        return action
    
    def insert_com_action(divergences, current_cost, aligned_agents, previous_action):
        com_info = []
        for div in divergences.divergences:
            com_info.append("{}-{}".format(div.property, div.r_val))
        com_action = Operator("COM_ALIGN", com_info, CM.g_robot_name, None, 0)
        com_action.cost = Operator.COST_COM
        com_action.previous = previous_action
        if com_action.previous!=None:
            com_action.previous.next.append(com_action)
        com_action.current_plan_cost = current_cost
        com_action.branching_name = previous_action.branching_name
        aligned_agents[CM.g_robot_name].planned_actions.append(
            (com_action.name, com_action.agent, com_action.parameters))

        return com_action

    def apply(agents, action_task, acting_agent, agent_state_in, agent_state_out):
        # print("ApplyOperator {}".format(action_task))

        # acting_agent = action_task.agent
        params = action_task.parameters

        # Check if the Operator is known by the agent
        if action_task.name not in g_agents[acting_agent].operatorsAg:
            raise Exception("OpAg {} unknown for agent {}".format(action_task.name, acting_agent))
        opAg = g_agents[acting_agent].operatorsAg[action_task.name]

        state_in = agents[agent_state_in].state
        state_out = agents[agent_state_out].state

        # Check if already done
        if CM.g_with_contrib and opAg.donecond!=None and opAg.donecond(agents, state_in, acting_agent, *params):
            print(CM.bcolors.WARNING + "already done" + CM.bcolors.ENDC)
            # raise Exception("Operator already done, should have been refined further.")
        # Check the precondition
        if opAg.precond!=None and not opAg.precond(agents, state_in, acting_agent, *params):
            print(CM.bcolors.WARNING + str(action_task) + " not applicable" + CM.bcolors.ENDC)
            return OpType.OPERATOR_NOT_APPLICABLE

        # Compute cost
        cost_action = 1.0 if opAg.cost == None else opAg.cost(agents, state_in, acting_agent, *params)

        opAg.apply_effects(agents, state_in, state_out, acting_agent, *params)

        return cost_action

    def precond(agents, state, action_task):
        params = action_task.parameters
        acting_agent = action_task.agent

        # Check if the Operator is known by the agent
        if action_task.name not in g_agents[acting_agent].operatorsAg:
            raise Exception("OpAg {} unknown for agent {}".format(action_task.name, acting_agent))
        opAg = g_agents[acting_agent].operatorsAg[action_task.name]

        return True if opAg.precond==None else opAg.precond(agents, state, acting_agent, *params)

class OperatorAg:
    def __init__(self, name, cost=None, precond=None, donecond=None, effects=None):
        self.name = name # type: str
        self.precond = precond # type: function
        self.donecond = donecond # type: function
        self.effects = effects # type: function
        self.cost = cost # type: function

    def __str__(self):
        return self.name

    def apply_effects(self, agents, state_in, state_out, acting_agent, *params):
        if self.effects != None:
            self.effects(agents, state_in, state_out, acting_agent, *params)

class AbstractTask(Task):
    def __init__(self, *args):
        if len(args) == 7:
            name = args[0]
            parameters = args[1]
            agent = args[2]
            why = args[3]
            decompo_number = args[4]
            super().__init__(name, parameters, why, decompo_number, agent)
            how = args[5]
            number_of_decompo = args[6]
            self.how = how  # List of task networks this task has been decomposed into (after each decompo function has been called)
            self.number_of_decompo = number_of_decompo  # How many decomposition this task has (maybe not successful ones)
        elif len(args) == 3:
            t = args[0]
            self.name = t.name
            self.parameters = t.parameters
            self.agent = t.agent
            self.why = t.why
            self.decompo_number = t.decompo_number
            self.how = args[1]
            self.number_of_decompo = args[2]
    
    def __repr__(self):
        if self.agent == CM.g_human_name:
            return "{}-{}A-{}{}".format(self.id, "H", self.name, self.parameters)
        elif self.agent == CM.g_robot_name:
            return "{}-{}A-{}{}".format(self.id, "R", self.name, self.parameters)
        else:
            return "{}-{}A-{}{}".format(self.id, self.agent, self.name, self.parameters)

class Fluent:
    def __init__(self, name, value, obs_type, loc, is_dyn):
        self.name = name
        self.val = value
        self.is_dyn = is_dyn
        self.obs = obs_type
        self.loc = loc

    def __repr__(self):
        return "{} = {} {} {}".format(self.name, self.val, self.obs, self.loc)

class State:
    def __init__(self, name):
        self.__name__ = name
        self.fluent_names = []

    def create_fluent(self, name, value, obs_type, loc, is_dyn):
        self.fluent_names.append(name)
        setattr(self, name, Fluent(name, value, obs_type, loc, is_dyn))

    def get_fluent(self, fluent_name):
        return getattr(self, fluent_name)

    def reset_fluent_locs(self):
        for fluent_name in self.fluent_names:
            fluent = self.get_fluent(fluent_name)
            fluent.loc = "empty"

class StateModification:
    def __init__(self, property, key, previous_value, next_value):
        self.property = property
        self.key = key
        self.previous_value = previous_value
        self.next_value = next_value

    def __eq__(self, other_modif):
        if self.property!=other_modif.property:
            return False
        if self.key!=other_modif.key:
            return False
        if self.previous_value!=other_modif.previous_value:
            return False
        if self.next_value!=other_modif.next_value:
            return False
        return True

    def __ne__(self, other_modif):
        return not(self == other_modif)

    def __str__(self):
        return "{}[{}]={}->{}".format(self.property, self.key, self.previous_value, self.next_value)

class StateModifications:
    def __init__(self, state_previous, state_next):
        self.modifications = []
        for fluent_name in state_previous.fluent_names:
            previous_value = state_previous.get_fluent(fluent_name).val
            next_value = state_next.get_fluent(fluent_name).val
            if previous_value != next_value:
                if type(next_value) == dict:
                    common_keys = []
                    for key in next_value:
                        if key not in previous_value:
                            # not treated for now
                            print("dict found {}:{}: H={} R=".format(fluent_name, key, next_value[key]))
                        else:
                            if key not in common_keys:
                                common_keys.append(key)
                    for key in previous_value:
                        if key not in next_value:
                            # not treated for now
                            print("dict found {}:{}: H= R={}".format(fluent_name, key, previous_value[key]))
                        else:
                            if key not in common_keys:
                                common_keys.append(key)
                    for key in common_keys:
                        if next_value[key] != previous_value[key]:
                            modif = StateModification(fluent_name, key, previous_value[key], next_value[key])
                            if not modif in self.modifications:
                                self.modifications.append(modif)
                elif type(next_value) == list:
                    # not treated for now
                    for e in next_value:
                        if e not in previous_value:
                            print("list found {}: R missing {}".format(fluent_name, e))
                    for e in previous_value:
                        if e not in next_value:
                            print("list found {}: H missing {}".format(fluent_name, e))
                else:
                    modif = StateModification(fluent_name, None, previous_value, next_value)
                    if not modif in self.modifications: 
                        self.modifications.append(modif)

    def get_modifications(self):
        return self.modifications

    def __eq__(self, other_state_modifications):
        other_modifications = other_state_modifications.get_modifications()
        if len(self.modifications)!=len(other_modifications):
            return False
        else:
            for i in range(len(self.modifications)):
                if self.modifications[i] != other_modifications[i]:
                    return False
        return True

    def __ne__(self, other_state_modifications):
        return not(self == other_state_modifications)

    def show(self):
        for m in self.modifications:
            print("\t- {}".format(m))

class Decomposition:
    def __init__(self, subtasks, agents, branching_name):
        self.subtasks = subtasks
        self.agents = agents
        self.branching_name = branching_name
        self.type = DecompType.OK
        self.next_action = None
    
    def show(self):
        print(self)

    def __str__(self):
        dec_str = "["
        if self.type != DecompType.OK:
            dec_str += str(self.type)
        else:
            for i, task in enumerate(self.subtasks):
                dec_str += str(task)
                if i < len(self.subtasks)-1:
                    dec_str += " - "
        dec_str += "]"
        return dec_str

    def first_task_is_operator_not_done(self, agent_name, agent_state):
        if self.subtasks[0].name in g_agents[agent_name].operatorsAg:
            donecond = g_agents[agent_name].operatorsAg[self.subtasks[0].name].donecond
            if not (donecond!=None and donecond(self.agents, self.agents[agent_state].state, agent_name, *self.subtasks[0].parameters)):
                return True
        return False
    
    def first_task_is_operator_done(self, agent_name, agent_state):
        if self.subtasks[0].name in g_agents[agent_name].operatorsAg:
            donecond = g_agents[agent_name].operatorsAg[self.subtasks[0].name].donecond
            if donecond!=None and donecond(self.agents, self.agents[agent_state].state, agent_name, *self.subtasks[0].parameters):
                return True
        return False

class Refinement:
    def __init__(self, decomp=None):
        self.decompos = [] # type: list[Decomposition]
        if decomp!=None:
            self.decompos.append(decomp)
        
        # Returns
        self.kill_branch = False
        self.current_cost = -1
        self.relevant_divergences = None
    
    def set_returns(self, kill_branch=None, current_cost=None, relevant_divergences=None):
        if kill_branch!=None:
            self.kill_branch = kill_branch
        if current_cost!=None:
            self.current_cost = current_cost
        if relevant_divergences!=None:
            self.relevant_divergences = relevant_divergences

    def add(self, decomp):
        self.decompos.append(decomp)
    
    def show(self):
        print("[\n", end="")
        for decomp in self.decompos:
            print("\t{}: {}".format(decomp.branching_name, decomp))
        print("]")

    def show_next_actions(self):
        print("next actions:")
        for decomp in self.decompos:
            if decomp.next_action != None:
                print("\t- {}".format(decomp.next_action))
        print("")

class BeliefDivergence:
    def __init__(self, property, key, h_val, r_val):
        self.property = property
        self.key = key
        self.h_val = h_val
        self.r_val = r_val

    def show(self):
        print(self)

    def __repr__(self):
        return "{}:{}: H={} R={}".format(self.property, self.key, self.h_val, self.r_val)

    def align_state(self, state):
        fluent = state.get_fluent(self.property)
        if self.key == None:
            fluent.val = self.r_val
        else:
            fluent.val[self.key] = self.r_val

    def in_agents(self, agents):
        f_r = agents[CM.g_robot_name].state.get_fluent(self.property)
        f_h = agents[CM.g_human_name].state.get_fluent(self.property)
        return f_r.val==self.r_val and f_h.val==self.h_val

class BeliefDivergences:
    def __init__(self):
        self.divergences = [] # type: list[BeliefDivergence]

    def add(self, belief_div):
        self.divergences.append(belief_div)

    def show(self):
        print(self)

    def __repr__(self):
        dstr = ""
        for div in self.divergences:
            dstr += "\t{}\n".format(div)
        return dstr

    def isIn(self, belief_div):
        for div in self.divergences:
            if div.property == belief_div.property and div.key == belief_div.key and div.h_val == belief_div.h_val and div.r_val == belief_div.r_val:
                return True
        return False

    def get_divergences(self):
        return self.divergences

    def update(self, newagents):
        print("\n# UPDATE belief divergences")
        self.divergences = []
        for fluent_name in newagents[CM.g_robot_name].state.fluent_names:
            r_fluent = newagents[CM.g_robot_name].state.get_fluent(fluent_name)
            h_fluent = newagents[CM.g_human_name].state.get_fluent(fluent_name)
            if not r_fluent.is_dyn:
                continue
            h_value = h_fluent.val
            r_value = r_fluent.val
            if h_value != r_value:
                if type(h_value) == dict:
                    common_keys = []
                    for key in h_value:
                        if key not in r_value:
                            # not treated for now
                            print("dict found {}:{}: H={} R=".format(fluent_name, key, h_value[key]))
                        else:
                            if key not in common_keys:
                                common_keys.append(key)
                    for key in r_value:
                        if key not in h_value:
                            # not treated for now
                            print("dict found {}:{}: H= R={}".format(fluent_name, key, r_value[key]))
                        else:
                            if key not in common_keys:
                                common_keys.append(key)
                    for key in common_keys:
                        if h_value[key] != r_value[key]:
                            belief_div = BeliefDivergence(fluent_name, key, h_value[key], r_value[key])
                            if not self.isIn(belief_div):
                                self.add(belief_div)
                                # print("dict found {}:{}: H={} R={}".format(belief_div.property, belief_div.key, belief_div.h_val, belief_div.r_val))
                elif type(h_value) == list:
                    # not treated for now
                    for e in h_value:
                        if e not in r_value:
                            print("list found {}: R missing {}".format(fluent_name, e))
                    for e in r_value:
                        if e not in h_value:
                            print("list found {}: H missing {}".format(fluent_name, e))
                else:
                    belief_div = BeliefDivergence(fluent_name, None, h_value, r_value)
                    if not self.isIn(belief_div):
                        # print("plain found {}: H={} R={}".format(property, h_value, r_value))
                        self.add(belief_div)

############################################################
# Agents
class Agent:
# Mandatory to match the static or dynamic fields in __init__ and deepcopy 

    def __init__(self, name):
        #####################
        # Static part
        self.name = name # type: str
        self.operators = {} # type: Dict[str, function]
        self.methods = {} # type: Dict[str, function]
        self.triggers = [] # type: list[function]
        self.operatorsAg = {} # type: Dict[str, OperatorAg]
        self.observability_function = None # type: function

        #####################
        # Dynamic part
        self.state = None # type: State
        self.agenda = [] # type: list[Task]
        self.planned_actions = [] # (id:str, action_name:str, agent:str, parameters:list[Any])
    
    #####################
    # Methods/Functions -> Static
    def isObservableBy(self, agent, state):
        return self.observability_function(state, self.name, agent)

    def __str__(self):
        return "OpsAg:{}".format(self.operatorsAg)

    def show_planned_actions(self):
        print("{} planned actions:".format(self.name))
        for a in self.planned_actions:
            print("\t-{}".format(a))
    
    #####################
    # Deepcopy 
    def __deepcopy__(self, memo):
        cp = Agent(self.name)
        #####################
        # Static part
        cp.operators = self.operators
        cp.methods = self.methods
        cp.triggers = self.triggers
        cp.operatorsAg = self.operatorsAg
        cp.observability_function = self.observability_function

        #####################
        # Dynamic part
        cp.state = deepcopy(self.state)
        cp.agenda = deepcopy(self.agenda)
        cp.planned_actions = deepcopy(self.planned_actions)

        return cp

class Agents:
    def __init__(self):
        self.agents = {}

    def exist(self, name):
        return name in self.agents
    
    def create_agent(self, name):
        if not self.exist(name): 
            self.agents[name] = Agent(name)

    def __getitem__(self, subscript):
        return self.agents[subscript]

    def __setitem__(self, subscript, item):
        self.agents[subscript] = item

    def __delitem__(self, subscript):
        del self.agents[subscript]

    def get_fluent_loc(self, fluent_name):
        return self.agents[CM.g_robot_name].state.get_fluent(fluent_name).loc
    
    def set_fluent_loc(self, fluent_name, loc):
        self.agents[CM.g_robot_name].state.get_fluent(fluent_name).loc = loc

    def get_fluent_obs(self, fluent_name):
        return self.agents[CM.g_robot_name].state.get_fluent(fluent_name).obs

    def set_fluent_obs(self, fluent_name, obs):
        if type(obs) != ObsType:
            raise Exception("set_fluent_obs: {} not of {} type!".format(obs, ObsType))
        self.agents[CM.g_robot_name].state.get_fluent(fluent_name).obs = obs

    def copresent(self):
        return self.get_fluent_loc("at_robot")==self.get_fluent_loc("at_human")

g_agents = Agents()

############################################################
# print_state and print_goal are identical except for the name
def print_state(state, indent=4, with_static=False):
    """Print each variable in state, indented by indent spaces."""
    if state != False:
        for fluent_name in state.fluent_names:
            fluent = state.get_fluent(fluent_name)
            if fluent.is_dyn or fluent.is_dyn==False and with_static:
                print("||", end='')
                for x in range(indent): sys.stdout.write(' ')
                sys.stdout.write(state.__name__ + '.' + fluent.name)
                if state.__name__ == "human_init":
                    print(' = {}'.format(fluent.val))
                else:
                    print(' = {} \t{} \tloc={}'.format(fluent.val, fluent.obs, fluent.loc))
    else:
        print('False')

def print_agent(agent, with_static=False):
    print("\n")
    print_agenda(g_agents, agent)
    print("|STATE {} = ".format(agent))
    print_state(g_agents[agent].state, with_static=with_static)
    print("")

def print_agent_s(agent, agents):
    print_agenda(agents, agent)
    print("|STATE {} = ".format(agent))
    print_state(agents[agent].state)

def show_init():
    print_agents_step(g_agents, with_static=True)

def print_agenda_tn(agents, agent):
    print("| AGENDA {} =".format(agent))
    print("||\t ", agents[agent].agenda.tasks)
    print("||\t ", agents[agent].agenda.constraints)

def print_agenda(agent):
    print("| AGENDA {} =".format(agent.name))
    for t in agent.agenda:
        print("||\t-{}".format(t))

def print_agendas(agents):
    print_agenda(agents[CM.g_robot_name])
    print_agenda(agents[CM.g_human_name])

def print_agents_step(agents, with_static=False):
    print("__________________________________________________________________________")
    print_agendas(agents)
    print("|------------------------------------------------------------------------")
    print("| STATE {} =".format(CM.g_robot_name))
    print_state(agents[CM.g_robot_name].state, with_static)
    print("| STATE {} =".format(CM.g_human_name))
    print_state(agents[CM.g_human_name].state, with_static)
    print("|________________________________________________________________________")

############################################################
# Helper functions that may be useful in domain models
def forall(seq, cond):
    """True if cond(x) holds for all x in seq, otherwise False."""
    for x in seq:
        if not cond(x): return False
    return True

def find_if(cond, seq):
    """
    Return the first x in seq such that cond(x) holds, if there is one.
    Otherwise return None.
    """
    for x in seq:
        if cond(x): return x
    return None


############################################################
# Commands to tell Pyhop what the operators and methods are

def declare_methods(agent, task_name, *method_list):
    """
    Call this once for each task, to tell Pyhop what the methods are.
    task_name must be a string.
    method_list must be a list of functions, not strings.
    """
    if not g_agents.exist(agent):
        g_agents.create_agent(agent)
    g_agents[agent].methods.update({task_name: list(method_list)})

def declare_triggers(agent, *triggers):
    if not g_agents.exist(agent):
        g_agents.create_agent(agent)
    g_agents[agent].triggers += triggers

def set_state(agent, state):
    if not g_agents.exist(agent):
        g_agents.create_agent(agent)
    g_agents[agent].state = state

def get_state(agent):
    return g_agents[agent].state

def declare_operators_ag(agent, operatorsAg):
    if not g_agents.exist(agent):
        g_agents.create_agent(agent)
    g_agents.agents[agent].operatorsAg.update({opAg.name: opAg for opAg in operatorsAg})

def add_tasks(agent, tasks):
    if not g_agents.exist(agent):
        g_agents.create_agent(agent)

    for t in tasks:
        if t[0] in g_agents[agent].operatorsAg:
            g_agents[agent].agenda.append(Operator(t[0], t[1:], agent, None, None))
        elif t[0] in g_agents[agent].methods:
            g_agents[agent].agenda.append(AbstractTask(t[0], t[1:], agent, None, None, [], len(g_agents[agent].methods[t[0]])))
        else:
            raise TypeError("Asked to add task '{}' to agent '{}' but it is not defined "
                            "neither in its operators nor methods.".format(t[0], agent))

def initTn(agent, tn):
    if not g_agents.exist(agent):
        g_agents.create_agent(agent)
    
    g_agents[agent].agenda = tn

def set_observable_function(agent, function):
    if not g_agents.exist(agent):
        g_agents.create_agent(agent)
    g_agents[agent].observability_function = function

def reset_agents_tasks():
    for agent in g_agents.agents:
        g_agents[agent].agenda = []

def reset_planner():
    global g_agents, trigger_id
    g_agents = Agents()
    trigger_id = 0


############################################################
# The actual planner

## Exploration related
def createFirstNode(agents):
    if CM.g_starting_agent == CM.g_robot_name or CM.g_starting_agent=="":
        begin_agent = CM.g_human_name
    elif CM.g_starting_agent == CM.g_human_name:
        begin_agent = CM.g_robot_name
    begin_action = Operator("BEGIN", [], begin_agent, None, None)

    first_node = NM.createFirstNode(agents, begin_action)
    
    return first_node

def heuristic_exploration(n_plot):
    e_flagged_nodes=[]
    u_flagged_nodes=[]
    new_e_flagged_nodes=[]
    Ns=None # Current solution node

    ###################### ALGO ########################
    # Create the first E flagged incomplete node with the BEGIN action
    # Loop while there are still some E flagged nodes
        # Pick the cheappest E node to explore
        # Explore this node 

        # Solution check #
        # Check the new final nodes to update the solution node #
        # Seek the cheapest final node (Nf) from the new E flagged nodes
        # If there is a new final node
            # If Nf is cheaper than Ns (or if Ns doesn't exist)
                # Ns is flagged with F and Nf is flagged S 
        # Check if the E nodes are more expensive than the current Ns #
        # If Ns exists
            # for every E node
                # If E node cost is >= Ns cost
                    # If node is final then flagged F
                    # Else then flagged U
    ####################################################

    # Initial Situation Assessment
    if CM.g_with_contrib:
        situation_assessment(g_agents)

    # Create the first E flagged node
    first_node = createFirstNode(g_agents)
    e_flagged_nodes.append(first_node)
    if CM.g_debug:
        print("first node = ", end="")
        NM.show_node(first_node)
    if CM.g_compute_gui:
        n_plot += 1
        gui.show_tree(first_node, str(n_plot), view=CM.g_view_gui)
        gui.show_all(NM.get_last_nodes_action(first_node), CM.g_robot_name, CM.g_human_name, 0, CM.g_with_contrib, with_begin="false", with_abstract="false")
    if CM.g_stop_input:
        input()
    
    # Loop while there are still some E flagged nodes
    while len(e_flagged_nodes)>0:
        # Merge nodes if needed
        merge_nodes(first_node, e_flagged_nodes, u_flagged_nodes)

        # Pick the cheappest E node to explore
        picked_node = NM.pick_cheapest_node(e_flagged_nodes)
        if CM.g_debug:
            print("\n<@> picked node = ", end="")
            NM.show_node(picked_node)

        # Explore this node #
        explore_node(picked_node, e_flagged_nodes, new_e_flagged_nodes, u_flagged_nodes, Ns)
        if CM.g_debug:
            print("node explored = ", end="")
            NM.show_node(picked_node)
            print("new_e_flagged_nodes : ")
            NM.show_nodes(new_e_flagged_nodes)
            print("e_flagged_nodes :")
            NM.show_nodes(e_flagged_nodes)

        # Solution check #
        # Check the new final nodes to update the solution node #
        if CM.g_debug:
            print("Ns before check = ", end="")
            NM.show_node(Ns)
        # Seek the cheapest final node (Nf) from the new E flagged nodes
        Nf = NM.pick_cheapest_final_node(new_e_flagged_nodes)
        if CM.g_debug:
            print("Nf = ", end="")
            NM.show_node(Nf)
        # If there is a new final node
        if Nf != None:
            #  If Nf is cheaper than Ns or if Ns doesn't exist
            if Ns==None or Nf.cost < Ns.cost:
                if CM.g_debug:
                    print("new Ns!")
                # Ns is flagged with F and Nf is flagged S 
                if Ns!=None:
                    Ns.flag = NM.Node.Flag.F
                Nf.flag = NM.Node.Flag.S
                Ns = Nf
                e_flagged_nodes.remove(Ns)
        if CM.g_debug:
            print("Ns after check = ", end="")
            NM.show_node(Ns)

        # Check if the E nodes are more expensive than the current Ns #
        # If Ns exists
        if Ns != None:
            # for every E Node
            nodes_to_remove = []
            for n in e_flagged_nodes:
                # If node cost >= Ns cost
                if n.cost >= Ns.cost:
                    # If node is final then flagged F
                    if n.type == NM.Node.Type.F:
                        n.flag=NM.Node.Flag.F
                    # Else then flagged U
                    # else:
                    #     n.flag=NM.Node.Flag.U
                    #     u_flagged_nodes.append(n)
                    nodes_to_remove.append(n)
            for n in nodes_to_remove:
                e_flagged_nodes.remove(n)
        first_node.compute_fcost()
        if CM.g_debug:
            print("e_flagged_nodes after check solution:")
            NM.show_nodes(e_flagged_nodes)
        if CM.g_compute_gui:
            n_plot+=1
            gui.show_tree(first_node, str(n_plot), view=CM.g_view_gui)
            gui.show_all(NM.get_last_nodes_action(first_node), CM.g_robot_name, CM.g_human_name, 0, CM.g_with_contrib, with_begin="false", with_abstract="true")
        if CM.g_stop_input:
            input()

    return first_node, Ns, u_flagged_nodes, n_plot

def explore_node(node, e_flagged_nodes, new_e_flagged_nodes, u_flagged_nodes, Ns):

    ################## EXPLORE NODE ##################
    # While end not reached
        
        # Get refinement with refine_agenda
        # Apply the refinement with applyRefinement (apply found actions or create inactivity actions)
        
        # END1- If there are several decomposition in the refinement
            # Update current node (depth, type H/R, flag F)
            # Update E flagged lists
            # For each decomposition in applied_refinement
                # If both agendas are empty
                    # Update current to solution (type F, flag E, update e flag lists)
                # Else
                    # Create incomplete node (previous, cost, depth, next, flag E)
                    # If inactivity deadlock
                        # flag D
                    # Else
                        # Update E flag lists
        
        # Elif there is only one decomposition
            # END2- If both agendas are empty
                # update current node to solution (type F, flag E, depth, update e flag list)
            # END3- If the cost is higher than current solution
                # flag U, remove from e flag list
            # END4- If inactivity deadlock
                # flag D, remove from e flag list
            # Else, we continue exploring the node
                # update previous action, state, current cost, node length
        
        # Else
            # Raise exception, shouldn't occur

    # Exploration is done
    # Update cost, end action, end state, e flag list
    ##################################################

    previous_action = node.end_action
    newagents = node.end_agents
    current_cost = node.cost
    new_e_flagged_nodes.clear()

    while True:
        # Get next agent name ("human" or "robot")
        if previous_action.agent == CM.g_robot_name:
            next_agent_name = CM.g_human_name
            next_agent_name_short = "H"
        elif previous_action.agent == CM.g_human_name:
            next_agent_name = CM.g_robot_name
            next_agent_name_short = "R"

        print("=> {} step explo ==================================================================================".format(next_agent_name_short))
        print_agents_step(newagents)

        # Get next actions and states for the next agent name
        # Get applied refinements
        if node.type==NM.Node.Type.D and newagents.copresent():
            node.type=NM.Node.Type.I

        rel_divs = None
        agts_before_com = None
        applied_refinement = get_applied_refinement(next_agent_name, newagents, previous_action, current_cost, delaying=(node.type==NM.Node.Type.D))
        while not isinstance(applied_refinement, Refinement):
            #returned com action
            com_action = applied_refinement[0]
            aligned_agents = applied_refinement[1]
            rel_divs = applied_refinement[2]
            agts_before_com = deepcopy(newagents)
            previous_action = com_action
            newagents = aligned_agents
            applied_refinement = get_applied_refinement(next_agent_name, newagents, com_action, current_cost, delaying=(node.type==NM.Node.Type.D))


        if applied_refinement.current_cost != -1:
            current_cost = applied_refinement.current_cost
        kill_branch = applied_refinement.kill_branch
        # rel_divs = applied_refinement.relevant_divergences

        # Branching for delay
        if rel_divs!=None and CM.g_with_delay:
            if len(rel_divs.divergences)==1 and newagents.get_fluent_obs(rel_divs.divergences[0].property)==ObsType.INF:
                node = create_delay_branch(node, rel_divs, agts_before_com, previous_action.previous, current_cost, e_flagged_nodes, new_e_flagged_nodes, u_flagged_nodes, "e")
        if kill_branch:
            e_flagged_nodes.remove(node)
            if Ns==node:
                Ns = None
            NM.kill_delay_branch(node)
            return 

        print("applied refinement = ")
        applied_refinement.show_next_actions()

        # END1- If there are several decomposition in the refinement
        if len(applied_refinement.decompos)>1:
            # Update current node (depth, type H/R, flag F)
            if previous_action.agent == CM.g_robot_name:
                node.type = NM.Node.Type.H
            elif previous_action.agent == CM.g_human_name:
                node.type = NM.Node.Type.R
            node.flag = NM.Node.Flag.F
            node.depth += node.length

            # Update E flagged lists
            e_flagged_nodes.remove(node)

            for decomp in applied_refinement.decompos:
                # If both agendas are empty
                if decomp.type == DecompType.BOTH_AGENDAS_EMPTY:
                    # Update current to solution (type F, flag E, update e flag lists)
                    node.type = NM.Node.Type.F
                    node.flag = NM.Node.Flag.E
                    new_e_flagged_nodes.append(node)
                else:
                    # Create incomplete node (previous, cost, depth, next, flag E)
                    next_node = NM.create_incomplete_node_dec(decomp, node, current_cost+decomp.subtasks[0].cost, node.depth)
                    node.next_nodes.append(next_node)

                    if checkInactivityDeadlockDec(decomp):
                        node.Flag = NM.Node.Flag.D
                    else:
                        new_e_flagged_nodes.append(next_node)
            # print("END1")
            # input()
            break

        # Elif there is only one decomposition
        elif len(applied_refinement.decompos)==1:
            decomp = applied_refinement.decompos[0]

            # END2- If both agendas are empty
            if decomp.type == DecompType.BOTH_AGENDAS_EMPTY:
                node.type = NM.Node.Type.F
                node.flag = NM.Node.Flag.E
                node.depth += node.length
                e_flagged_nodes.remove(node)
                new_e_flagged_nodes.append(node)
                # print("END2")
                # input()
                break

            # END3- If the cost is higher than the current solution (if existing)
            # elif Ns!=None and current_cost+decomp.next_action.cost>Ns.cost:
            #     action = decomp.next_action
            #     dec_agents = decomp.agents

            #     current_cost += action.cost
            #     previous_action = action
            #     newagents = dec_agents
            #     node.flag = NM.Node.Flag.U
            #     e_flagged_nodes.remove(node)
            #     u_flagged_nodes.append(node)
            #     # print("END3")
            #     # input()
            #     break

            # END4- If inactivity deadlock is detected
            elif checkInactivityDeadlockDec(decomp):
                node.Flag = NM.Node.Flag.D
                print(CM.bcolors.WARNING + "## ERROR ## Inactivity deadlock detected." + CM.bcolors.ENDC)
                raise Exception("Deadlock: too many consecutive IDLE or WAIT. IDL")
                break

            # Else, we continue exploring the node
            else:
                print("continue ..")
                action = decomp.next_action
                dec_agents = decomp.agents

                # update previous action, state, current cost, node length
                current_cost += action.cost
                previous_action = action
                newagents = dec_agents
                node.length += 1
                # print_agent_s(next_agent_name, newagents)

        else:
            raise Exception("Explore_node: case not handled.")

        # print("Step..", end="")
        # input()
    
    # When end is reached
    node.cost = current_cost
    node.end_action = previous_action
    node.end_agents = newagents
    e_flagged_nodes += new_e_flagged_nodes
    print("=> end explo")

def refine_u_nodes(first_node, u_flagged_nodes, n_plot):
    while u_flagged_nodes!=[]:
        # Pick the cheapest U node to explore
        node = NM.pick_cheapest_node(u_flagged_nodes)
        print("u_nodes remaining : {}".format(len(u_flagged_nodes)))
        if CM.g_debug:
            print("\n<@> picked node = ", end="")
            NM.show_node(node)
        explore_u_node(node, u_flagged_nodes)
        first_node.compute_fcost()
        if CM.g_debug:
            print("node explored")
        if CM.g_compute_gui:
            n_plot+=1
            gui.show_tree(first_node, str(n_plot), view=CM.g_view_gui)
            gui.show_all(NM.get_last_nodes_action(first_node), CM.g_robot_name, CM.g_human_name, with_begin="false", with_abstract="true")
        if CM.g_stop_input:
            input()

def explore_u_node(node, u_flagged_nodes):
    previous_action = node.end_action
    newagents = node.end_agents
    current_cost = node.cost

    if CM.g_debug:
        print("=> start u explo node cost = {}".format(current_cost))
    while True:
        # Get next agent name ("human" or "robot")
        if previous_action.agent == CM.g_robot_name:
            next_agent_name = CM.g_human_name
            next_agent_name_short = "H"
        elif previous_action.agent == CM.g_human_name:
            next_agent_name = CM.g_robot_name
            next_agent_name_short = "R"

        print("=> {} step u explo ==================================================================================".format(next_agent_name_short))
        print_agents_step(newagents)

        # Get next actions and states for the next agent name
        if node.type==NM.Node.Type.D and newagents.copresent():
            node.type=NM.Node.Type.I
        applied_refinement = get_applied_refinement(next_agent_name, newagents, previous_action, current_cost, delaying=(node.type==NM.Node.Type.D))
        if applied_refinement.current_cost != -1:
            current_cost = applied_refinement.current_cost
        kill_branch = applied_refinement.kill_branch
        rel_divs = applied_refinement.relevant_divergences

        # Branching for delay
        if rel_divs!=None and len(rel_divs.divergences)==1 and newagents.get_fluent_obs(rel_divs.divergences[0].property)==ObsType.INF:
            node = create_delay_branch(node, rel_divs, newagents, previous_action, current_cost, [], [], u_flagged_nodes, "u")
        if kill_branch:
            u_flagged_nodes.remove(node)
            if Ns==node:
                Ns = None
            NM.kill_delay_branch(node)
            return 

        print("applied refinement = ")
        applied_refinement.show_next_actions()

        # Check the 2 possibles ends
        # END1-If it's a final node (all agenda are empty)
        # END2-Else if there is a choice (several next_actions)
        # END3-else if too many consecutive IDLE and WAIT (deadlock)

        # END1- If there are several decomposition in the refinement
        if len(applied_refinement.decompos)>1:
            # Update current node (depth, type H/R, flag F)
            if previous_action.agent == CM.g_robot_name:
                node.type = NM.Node.Type.H
            elif previous_action.agent == CM.g_human_name:
                node.type = NM.Node.Type.R
            node.flag = NM.Node.Flag.F
            node.depth += node.length

            for decomp in applied_refinement.decompos:
                # If both agendas are empty
                if decomp.type == DecompType.BOTH_AGENDAS_EMPTY:
                    # Update current to solution (type F, flag E, update e flag lists)
                    node.type = NM.Node.Type.F
                    node.flag = NM.Node.Flag.E
                else:
                    # Create incomplete node (previous, cost, depth, next, flag E)
                    next_node = NM.create_incomplete_node_dec(decomp, node, current_cost, node.depth)
                    node.next_nodes.append(next_node)

                    if checkInactivityDeadlockDec(decomp):
                        node.Flag = NM.Node.Flag.D
                    else:
                        next_node.flag = NM.Node.Flag.U
                        u_flagged_nodes.append(next_node)
            break

        # Elif there is only one decomposition
        elif len(applied_refinement.decompos)==1:
            decomp = applied_refinement.decompos[0]

            # END2- If both agendas are empty
            if decomp.type == DecompType.BOTH_AGENDAS_EMPTY:
                node.type = NM.Node.Type.F
                node.flag = NM.Node.Flag.F
                node.depth += node.length
                break

            # END3- If inactivity deadlock is detected
            elif checkInactivityDeadlockDec(decomp):
                node.Flag = NM.Node.Flag.D
                print(CM.bcolors.WARNING + "## ERROR ## Inactivity deadlock detected." + CM.bcolors.ENDC)
                raise Exception("Deadlock: too many consecutive IDLE or WAIT. IDL")
                break

            # Else, we continue exploring the node
            else:
                print("continue ..")
                action = decomp.next_action
                dec_agents = decomp.agents

                # update previous action, state, current cost, node length
                current_cost += action.cost
                previous_action = action
                newagents = dec_agents
                node.length += 1
                # print_agent_s(next_agent_name, newagents)

        else:
            raise Exception("Explore_u_node: case not handled.")

        # print("Step..", end="")
        # input()

    # If end_reached
    u_flagged_nodes.remove(node)
    node.cost = current_cost
    node.end_action = previous_action
    node.end_agents = newagents
    if CM.g_debug:
        print("=> end explo")

def checkInactivityDeadlockDec(decomp):
    max_consecutive = 4
    deadlock = False

    H_planned_actions = decomp.agents[CM.g_human_name].planned_actions
    R_planned_actions = decomp.agents[CM.g_robot_name].planned_actions
    
    if len(H_planned_actions)>=2 and len(R_planned_actions)>=2:
        h_stuck_1 = H_planned_actions[-1][1] == "IDLE" or H_planned_actions[-1][1] == "WAIT"
        h_stuck_2 = H_planned_actions[-2][1] == "IDLE" or H_planned_actions[-2][1] == "WAIT"
        r_stuck_1 = R_planned_actions[-1][1] == "IDLE" or R_planned_actions[-1][1] == "WAIT"
        r_stuck_2 = R_planned_actions[-2][1] == "IDLE" or R_planned_actions[-2][1] == "WAIT"

        if h_stuck_1 and h_stuck_2 and r_stuck_1 and r_stuck_2:
            deadlock = True

    return deadlock

trigger_id = 0
def check_triggers(agents):
    global trigger_id

    # CHECK TRIGGERS OF OTHER AGENTS
    for a in g_agents.agents:
        # if a == agent_name:
        #     continue
        for t in g_agents[a].triggers:
            triggered = t(agents, agents[a].state, a)
            if triggered != False:
                triggered_subtasks = []
                for sub in triggered:
                    if sub[0] in g_agents[a].methods:
                        triggered_subtasks.append(AbstractTask(sub[0], sub[1:], a, t.__name__+str(trigger_id), None, [], len(g_agents[a].methods[sub[0]])))
                    elif sub[0] in g_agents[a].operatorsAg:
                        triggered_subtasks.append(Operator(sub[0], sub[1:], a, t.__name__+str(trigger_id), None))
                    else:
                        raise TypeError(
                            "Error: the trigger function '{}'"
                            "returned a subtask '{}' which is neither in the methods nor in the operators "
                            "of agent '{}'".format(t.__name__, sub[0], a)
                        )
                trigger_id+=1
                agents[a].agenda = triggered_subtasks + agents[a].agenda
                print("Triggered {} : {}".format(a, triggered_subtasks))
                break


## Refinement related
def get_applied_refinement(agent_name, agents, previous_action, current_cost, delaying=False):
    com_action_added=False # Check when last action is a com action (when com action makes H agenda empty)
    HUMAN = agent_name==CM.g_human_name
    ROBOT = agent_name==CM.g_robot_name

    if ROBOT and delaying and agents.copresent() and CM.g_with_contrib:
        delaying = False

    if ROBOT and delaying and not agents.copresent() and CM.g_with_contrib:
        if agents[CM.g_human_name].agenda==[]:
            ref = Refinement()
            ref.set_returns(current_cost=current_cost, kill_branch=True)
            return ref
        else:
            delay_action = Operator.create_inactivity_op("DELAY", 0.0, agent_name, previous_action, current_cost)
            agents[agent_name].planned_actions.append( (delay_action.id, delay_action.name, delay_action.agent, delay_action.parameters) )
            decomp = Decomposition([delay_action], agents, previous_action.branching_name)
            decomp.next_action = delay_action
            ref = Refinement(decomp=decomp)
            ref.set_returns(current_cost=current_cost)
            return ref

    print("{}- Refine agenda".format(agent_name))
    refinement = refine_agenda(agent_name, agents, previous_action.branching_name, agent_state=agent_name)

    if HUMAN and CM.g_with_contrib:
        print("{}- Refine agenda with r_beliefs".format(agent_name))
        refinement_r_beliefs = refine_agenda(agent_name, agents, previous_action.branching_name, agent_state=CM.g_robot_name)

        # CHECK DIVERGENCE HERE
        if need_belief_alignment(refinement_r_beliefs, refinement):
            print("NEED of belief alignment!")

            # find relevant divergence to correct (for now this the current domain structure assumption that only one divergence fixes)
            result = find_and_correct_relevant_divergence(agents, CM.g_human_name, refinement_r_beliefs)
            if result == False:
                raise Exception("Relevant divergence not found for refinement !")
            divergences, aligned_agents = result
            print("Relevant divergences to correct : {}".format(divergences))

            # insert communication action before (done by robot) to correct the human belief
            current_cost += Operator.COST_COM
            com_action = Operator.insert_com_action(divergences, current_cost, aligned_agents, previous_action)
            print("COM: com action added = {}".format(com_action))
            return (com_action, aligned_agents, divergences)

            previous_action = com_action
            com_action_added = True
            print("COM: com action added = {}".format(com_action))
            
            # Refine again with aligned agents
            refinement = refine_agenda(agent_name, aligned_agents, previous_action.branching_name, agent_state=CM.g_human_name)
            refinement.set_returns(current_cost=current_cost, relevant_divergences=divergences)
        else:
            print("No relevant belief divergence for refinement")

    print("refinement = ")
    refinement.show()

    for decomp in refinement.decompos:
        # TODO check if no triggers are forgotten when creating inactivity actions
        if DecompType.NO_APPLICABLE_METHOD == decomp.type:
            print("NO_APPLICABLE_METHOD => WAIT added")
            wait_action = Operator.create_inactivity_op("WAIT", CM.g_wait_cost[agent_name], agent_name, previous_action, current_cost)
            decomp.agents[agent_name].planned_actions.append( (wait_action.id, wait_action.name, wait_action.agent, wait_action.parameters) )
            decomp.subtasks = [wait_action] + decomp.subtasks
            decomp.agents[agent_name].agenda = decomp.subtasks[1:] + decomp.agents[agent_name].agenda
            decomp.next_action = wait_action
            decomp.type = DecompType.OK
            check_triggers(decomp.agents)
        elif DecompType.AGENDA_EMPTY == decomp.type:
            print("AGENDA_EMPTY => IDLE added")
            idle_action = Operator.create_inactivity_op("IDLE", CM.g_idle_cost[agent_name], agent_name, previous_action, current_cost)
            decomp.agents[agent_name].planned_actions.append( (idle_action.id, idle_action.name, idle_action.agent, idle_action.parameters) )
            decomp.subtasks = [idle_action] + decomp.subtasks
            decomp.next_action = idle_action
            decomp.type = DecompType.OK
            check_triggers(decomp.agents)
        elif DecompType.BOTH_AGENDAS_EMPTY == decomp.type:
            print("BOTH_AGENDAS_EMPTY")
            if HUMAN and com_action_added:
                decomp.agents = aligned_agents
                decomp.agents[agent_name].agenda = decomp.agents[agent_name].agenda[1:] 
                decomp.subtasks = [com_action]
                decomp.next_action = com_action
                decomp.type = DecompType.OK
        elif DecompType.OK == decomp.type:
            print("Decomp OK")
            newagents = decomp.agents
            action = decomp.subtasks[0]

            if CM.g_with_contrib and ROBOT and check_diff_effects(newagents, action):
                # find relevant divergence to correct (for now this the current domain structure assumption that only one divergence fixes)
                # check if a robot action has different effects w.r.t. Bh
                # if so -> is relevant => find and correct the divergence
                result = find_div_for_same_eff(agents, CM.g_human_name, action)
                if result == False:
                    raise Exception("No relevant divergence found !")
                divergences, aligned_agents = result
                print("Relevant divergences to correct : {}".format(divergences))

                # insert communication action before (done by robot) to correct the human belief
                current_cost += Operator.COST_COM
                com_action = Operator.insert_com_action(divergences, current_cost, aligned_agents, previous_action)
                print("COM: com action added eff = {}".format(com_action))
                return (com_action, aligned_agents, divergences)
                # 
                # 
                # 
                previous_action = com_action
                com_action_added = True
                print("COM: com action added eff = {}".format(com_action))
                newagents = aligned_agents
                refinement.set_returns(current_cost=current_cost, relevant_divergences=divergences)


            # Apply operator for acting agent
            action.agent = agent_name
            print("apply acting agent")
            result = Operator.apply(newagents, action, agent_name, agent_state_in=agent_name, agent_state_out=agent_name)
            if OpType.OPERATOR_NOT_APPLICABLE == result:
                print(action.name + " not feasible...")
                wait_action = Operator.create_inactivity_op("WAIT", CM.g_wait_cost[agent_name], agent_name, previous_action, current_cost)
                decomp.agents[agent_name].planned_actions.append( (wait_action.id, wait_action.name, wait_action.agent, wait_action.parameters) )
                decomp.subtasks = [wait_action] + decomp.subtasks
                decomp.agents[agent_name].agenda = decomp.subtasks[1:] + decomp.agents[agent_name].agenda
                decomp.next_action = wait_action
                check_triggers(decomp.agents)
            else:
                result_cost = result

                # check applicability with others beliefs
                if not Operator.precond(newagents, newagents[CM.g_other_agent_name[agent_name]].state, action):
                    raise Exception(str(action) + " not applicable with other's beliefs RNA")
                else:
                    print("applicable with other's beliefs")

                # Update other's beliefs, either all effects (R) or only inf effects if action attended
                print("Update other's beliefs")
                if CM.g_with_contrib:
                    if ROBOT:
                        apply_inferable_effects(newagents, action)
                    elif HUMAN:
                        Operator.apply(newagents, action, agent_name, agent_state_in=CM.g_other_agent_name[agent_name], agent_state_out=CM.g_other_agent_name[agent_name])
                else:
                    if ROBOT:
                        Operator.apply(newagents, action, agent_name, agent_state_in=CM.g_other_agent_name[agent_name], agent_state_out=CM.g_other_agent_name[agent_name])
                    elif HUMAN:
                        res = Operator.apply(newagents, action, agent_name, agent_state_in=CM.g_other_agent_name[agent_name], agent_state_out=CM.g_other_agent_name[agent_name])
                        if OpType.OPERATOR_NOT_APPLICABLE == res:
                            print(CM.bcolors.WARNING + str(action) + " not applicable with ground truth" + CM.bcolors.ENDC)
                            raise Exception(str(action) + " not applicable with ground truth RNA")


                # Get applied action and added to planned_actions
                action = action.copy_and_init(result_cost, current_cost, decomp.branching_name, previous_action)
                newagents[agent_name].planned_actions.append( (action.id, action.name, action.agent, action.parameters) )

                # Update agent's agenda
                newagents[agent_name].agenda = decomp.subtasks[1:] + newagents[agent_name].agenda

                if CM.g_with_contrib:
                    situation_assessment(newagents)

                check_triggers(newagents)
                
                decomp.subtasks = [action] + decomp.subtasks[1:]
                decomp.next_action = action
                decomp.agents = newagents

    for dec in refinement.decompos:
        if dec.type==DecompType.OK:
            dec.next_action.agent_agendas[CM.g_robot_name] = dec.agents[CM.g_robot_name].agenda
            dec.next_action.agent_agendas[CM.g_human_name] = dec.agents[CM.g_human_name].agenda
    return refinement

def refine_agenda(agent_name, in_agents, branching_name, agent_state=None):
    """
    Refine the given task executed by given agent in the given state.
    Decompose the task until reaching a primitive task.
    Return a list of subtasks for each possible decomposition.
    """
    # print("REFINE_UNTIL branching = {}".format(branching_name))
    # print("Start refine until {} {} {}".format(agent_name, task.name, agent_state))

    if agent_state==None:
        agent_state = agent_name
    agents = deepcopy(in_agents)
    other_agent_name = CM.g_other_agent_name[agent_name]

    refinement = Refinement()
    refinement.add(Decomposition([], agents, branching_name))    
    # refinement = [Decomposition([], agents, branching_name)]

    # Check if agenda is empty (no task to refine)
    if agents[agent_name].agenda == []:
        # Check if other's agenda is also empty
        if agents[other_agent_name].agenda == []:
            refinement.decompos[0].type = DecompType.BOTH_AGENDAS_EMPTY
        else:
            refinement.decompos[0].type = DecompType.AGENDA_EMPTY
    else:
        next_task = agents[agent_name].agenda.pop(0)
        print("Task to refine: {}".format(next_task))
        refinement.decompos[0].subtasks = [next_task]

        i=0
        # While we didn't reach the end of each decomposition, we start with one decomposition
        while i<len(refinement.decompos):
            current_decomp = refinement.decompos[i]
            print("decomp i= {} : {}".format(i, current_decomp.branching_name))
            # While first subtask of current decomposition isn't an OperatorAg we keep refining
            while not current_decomp.first_task_is_operator_not_done(agent_name, agent_state):
                task = current_decomp.subtasks[0]
                agents = current_decomp.agents
                next_subtasks = current_decomp.subtasks[1:]

                if task.name in g_agents[agent_name].methods:
                    list_decompo = refine_method(task, agent_name, agents, agent_state=agent_state)
                elif task.name in g_agents[agent_name].operatorsAg:
                    list_decompo = [Decomposition([task], agents, task.branching_name)]
                else:
                    raise Exception("task={}, task name neither in methods nor operators".format(task))

                # END, If no method is applicable
                if list_decompo == []:
                    current_decomp.subtasks = next_subtasks
                    current_decomp.agents[agent_name].agenda = [task] + current_decomp.agents[agent_name].agenda
                    current_decomp.type = DecompType.NO_APPLICABLE_METHOD
                    print("\t{} => {}".format(task, current_decomp.type))
                    break
                # There are applicable methods
                else:
                    # Update agents
                    current_decomp.agents = list_decompo[0].agents
                    # If there are several applicable methods, update branching name
                    if len(list_decompo)>1:
                        current_decomp.branching_name = list_decompo[0].branching_name
                        print("\tmultiple decs for {}: ".format(task), end="")
                        for dec in list_decompo:
                            print(" {} ".format(dec.branching_name), end="")
                        print("")
                    print("\t{} => {} : {}".format(task, list_decompo[0], list_decompo[0].branching_name))

                    # If we continue to refine with next tasks
                    need_continue = False
                    # If current method refines into nothing
                    if list_decompo[0].subtasks==[]:
                        print(CM.bcolors.OKGREEN + "\trefines into nothing" + CM.bcolors.ENDC)
                        need_continue = True
                    # If next task is an operator already done
                    elif current_decomp.first_task_is_operator_done(agent_name, agent_state): # CHECK list_decomp ? 
                        print(CM.bcolors.OKGREEN + "\talready done" + CM.bcolors.ENDC)
                        need_continue = True
                    if need_continue:
                        # print("NEED_CONTINUE")
                        # If there are other subtasks we continue by refining the next one
                        if len(next_subtasks)>0:
                            print("\tcontinue .. next_subtasks={}".format(next_subtasks))
                            current_decomp.subtasks = next_subtasks
                        # No other subtasks, we have to pop the next task in agenda to continue
                        else:
                            # END, If the agendas are empty
                            if list_decompo[0].agents[agent_name].agenda==[]:
                                current_decomp.subtasks = next_subtasks
                                if list_decompo[0].agents[other_agent_name].agenda==[]:
                                    current_decomp.type = DecompType.BOTH_AGENDAS_EMPTY
                                else:
                                    current_decomp.type = DecompType.AGENDA_EMPTY
                                print("\t{} => {}".format(task, current_decomp.type))
                                break
                            # Agenda isn't empty, we can continue with next task in agenda
                            else:
                                next_task = list_decompo[0].agents[agent_name].agenda.pop(0)
                                print("\tcontinue with next_task popped from agenda {}".format(next_task))
                                current_decomp.subtasks = [next_task]
                    # Update subtasks list and add new decompositions for each additional applicable methods
                    else:
                        current_decomp.subtasks = list_decompo[0].subtasks + next_subtasks
                        for j in range(1, len(list_decompo)):
                            j_subtasks = list_decompo[j].subtasks + next_subtasks
                            print("\t\tdecomposition {} : {} created : {}".format(j, list_decompo[j].branching_name, j_subtasks))
                            refinement.add(Decomposition(j_subtasks, list_decompo[j].agents, list_decompo[j].branching_name))

            # End of the decomposition reached, we look for the next one
            print("\tend {}".format(i))
            i+=1

    return refinement

def refine_method(task, agent_name, agents, agent_state=None):
    if agent_state==None:
        agent_state=agent_name

    decompos = g_agents[agent_name].methods[task.name]
    
    list_decompo_with_agents = []
    for i, decompo in enumerate(decompos):
        newagentsdecompo = deepcopy(agents)
        result = decompo(newagentsdecompo, newagentsdecompo[agent_state].state, agent_name, *task.parameters)
        if result is None:
            raise TypeError(
                "Error: the decomposition function: {} of task {} has returned None. It should return a list or False.".format(decompo.__name__,  task.name))
        elif result != False: # result==False => method not applicable
            multi_decompos = None
            branching_name = decompo.__name__
            if result != [] and isinstance(result[0], str) and result[0] == "MULTI":
                multi_decompos = result[1]
                branching_name = "multi"
            else:
                multi_decompos = [result]
            for multi_decompo in multi_decompos:
                newagents = deepcopy(newagentsdecompo)
                subtasks_obj = []
                for sub in multi_decompo:
                    if sub[0] in g_agents[agent_name].methods:
                        subtasks_obj.append(AbstractTask(sub[0], sub[1:], task.agent, task, i, [], len(g_agents[agent_name].methods[sub[0]])))
                    elif sub[0] in g_agents[agent_name].operatorsAg:
                        subtasks_obj.append(Operator(sub[0], sub[1:], task.agent, task, i))
                    else:
                        raise TypeError(
                            "Error: the decomposition function '{}' of task '{}' "
                            "returned a subtask '{}' which is neither in the methods nor in the operators "
                            "of agent '{}'".format(decompo.__name__, task.name, sub[0], agent_name)
                        )
                
                list_decompo_with_agents.append(Decomposition(subtasks_obj, newagents, branching_name))

    return list_decompo_with_agents


## Observability related
def situation_assessment(agents):
    # Not effective on the robot, only other agents
    # Thus, for now, only applied to human

    ground_truth = agents[CM.g_robot_name].state
    human_state = agents[CM.g_human_name].state

    human_loc = ground_truth.at_human.val

    for fluent_name in human_state.fluent_names:
        if agents.get_fluent_obs(fluent_name)==ObsType.OBS and agents.get_fluent_loc(fluent_name)==human_loc:
            if human_state.get_fluent(fluent_name).val != ground_truth.get_fluent(fluent_name).val:
                print("SA: human assessed {} <- {}".format(fluent_name, ground_truth.get_fluent(fluent_name).val))
                human_state.get_fluent(fluent_name).val = ground_truth.get_fluent(fluent_name).val

def apply_inferable_effects(agents, action):
    if not agents.copresent():
        return

    human_state = agents[CM.g_human_name].state
    # cp_agents = deepcopy(agents)
    # Operator.apply(cp_agents, action, CM.g_robot_name, agent_state_in=CM.g_human_name, agent_state_out=CM.g_human_name)
    Operator.apply(agents, action, CM.g_robot_name, agent_state_in=CM.g_human_name, agent_state_out=CM.g_human_name)

    # modif = StateModifications(agents[CM.g_human_name].state, cp_agents[CM.g_human_name].state)
    modif = StateModifications(agents[CM.g_human_name].state, agents[CM.g_human_name].state)
    
    for modif in modif.modifications:
        if agents.get_fluent_obs(modif.property)==ObsType.INF:
            print("INF: human attended inferable effects! {} <- {}".format(modif.property, modif.next_value))
            if modif.key == None:
                human_state.get_fluent(modif.property).val = modif.next_value
            else:
                human_state.get_fluent(modif.property).val[modif.key] == modif.next_value

def need_belief_alignment(refinement_r_beliefs, refinement_h_beliefs):
    # check if same number of decompositions
    if len(refinement_r_beliefs.decompos) != len(refinement_h_beliefs.decompos):
        print("Different number of decomposition")
        return True
    for i in range(len(refinement_h_beliefs.decompos)):
        decomp_h = refinement_h_beliefs.decompos[i]
        decomp_r = refinement_r_beliefs.decompos[i]

        # check if same type
        if decomp_h.type != decomp_r.type:
            print("Not same type of decomposition")
            return True

        # check if same number of tasks in the decomposition
        if len(decomp_h.subtasks) != len(decomp_r.subtasks):
            print("Not same number of subtasks")
            return True
        # check if same tasks
        for j in range(len(decomp_h.subtasks)):
            task_h = decomp_h.subtasks[j]
            task_r = decomp_r.subtasks[j]
            if task_h.name != task_r.name:
                print("Not same task name")
                return True
            elif task_h.parameters != task_r.parameters:
                print("Not same task parameters")
                return True

        # Check if action has the same effects
        if len(decomp_h.subtasks)>0:
            if check_diff_effects(decomp_h.agents, decomp_h.subtasks[0]):
                return True

    return False

def check_diff_effects(agents, action):
    agents_h = deepcopy(agents)
    agents_r = deepcopy(agents)

    result_h = Operator.apply(agents_h, action, action.agent, agent_state_in=CM.g_human_name, agent_state_out=CM.g_robot_name)
    if result_h!=OpType.OPERATOR_NOT_APPLICABLE:
        result_h = Operator.apply(agents_h, action, action.agent, agent_state_in=CM.g_human_name, agent_state_out=CM.g_human_name)
    result_r = Operator.apply(agents_r, action, action.agent, agent_state_in=CM.g_robot_name, agent_state_out=CM.g_human_name)
    if result_r!=OpType.OPERATOR_NOT_APPLICABLE:
        result_r = Operator.apply(agents_r, action, action.agent, agent_state_in=CM.g_robot_name, agent_state_out=CM.g_robot_name)

    # Check applicability
    if result_h==OpType.OPERATOR_NOT_APPLICABLE or result_r==OpType.OPERATOR_NOT_APPLICABLE:
        if not(result_h==OpType.OPERATOR_NOT_APPLICABLE and result_r==OpType.OPERATOR_NOT_APPLICABLE):
            print("Operator isn't applicable with only one of the beliefs")
            return True
    else:
        # Check cost
        cost_h = result_h
        cost_r = result_r
        if cost_h != cost_r:
            print("Not same cost_h={} != cost_r={}".format(cost_h, cost_r))
            return True

        # Check states
        state_human_previous = agents[CM.g_human_name].state
        state_robot_previous = agents[CM.g_robot_name].state
        state_human_h_beliefs = agents_h[CM.g_human_name].state
        state_robot_h_beliefs = agents_h[CM.g_robot_name].state
        state_human_r_beliefs = agents_r[CM.g_human_name].state
        state_robot_r_beliefs = agents_r[CM.g_robot_name].state
        modifs_human_with_h_beliefs = StateModifications(state_human_previous, state_human_h_beliefs)
        modifs_human_with_r_beliefs = StateModifications(state_human_previous, state_human_r_beliefs)
        modifs_robot_with_h_beliefs = StateModifications(state_robot_previous, state_robot_h_beliefs)
        modifs_robot_with_r_beliefs = StateModifications(state_robot_previous, state_robot_r_beliefs)
        if modifs_human_with_h_beliefs!=modifs_human_with_r_beliefs or modifs_robot_with_h_beliefs!=modifs_robot_with_r_beliefs:
            print("Not same effects")
            print("modifs_human_with_h_beliefs=")
            modifs_human_with_h_beliefs.show()
            print("modifs_human_with_r_beliefs=")
            modifs_human_with_r_beliefs.show()
            print("modifs_robot_with_h_beliefs=")
            modifs_robot_with_h_beliefs.show()
            print("modifs_robot_with_r_beliefs=")
            modifs_robot_with_r_beliefs.show()
            return True

def find_and_correct_relevant_divergence(agents, agent_name, refinement_r_beliefs):
    belief_divergences = BeliefDivergences()
    belief_divergences.update(agents) 
    belief_divergences.show()

    relevant_divergences = BeliefDivergences()

    divs = belief_divergences.get_divergences()

    # Look for one relevant divergence
    print("Testing with 1 relevant divergence")
    for divergence in divs:
        print("divergence tested = ", end="")
        divergence.show()

        newagents = deepcopy(agents)
        divergence.align_state(newagents[agent_name].state)
        refinement_aligned = refine_agenda(agent_name, newagents, "", agent_state=agent_name)

        if not need_belief_alignment(refinement_r_beliefs, refinement_aligned):
            print("\tdivergence is relevant!")
            relevant_divergences.add(divergence)
            return relevant_divergences, newagents
        else:
            print("\tdivergence isn't relevant")
            continue

    # Look for two relevant divergence
    if len(divs)<2:
        return False
    print("Testing with 2 relevant divergences")
    for i in range(len(divs)-1):
        for j in range(i+1, len(divs)):
            div1 = divs[i]
            div2 = divs[j]

            print("divs tested :")
            div1.show()
            div2.show()

            newagents = deepcopy(agents)
            div1.align_state(newagents[agent_name].state)
            div2.align_state(newagents[agent_name].state)
            refinement_aligned = refine_agenda(agent_name, newagents, "", agent_state=agent_name)

            if not need_belief_alignment(refinement_r_beliefs, refinement_aligned):
                print("\tdivergences are relevant!")
                relevant_divergences.add(div1)
                relevant_divergences.add(div2)
                return relevant_divergences, newagents
            else:
                print("\tdivergences aren't relevant")
                continue

    # Look for three relevant divergence
    print("Testing with 3 relevant divergences")
    if len(divs)<3:
        return False
    for i in range(len(divs)-2):
        for j in range(i+1, len(divs)-1):
            for k in range(j+1, len(divs)):
                div1 = divs[i]
                div2 = divs[j]
                div3 = divs[k]

                print("divs tested :")
                div1.show()
                div2.show()
                div3.show()

                newagents = deepcopy(agents)
                div1.align_state(newagents[agent_name].state)
                div2.align_state(newagents[agent_name].state)
                div3.align_state(newagents[agent_name].state)
                refinement_aligned = refine_agenda(agent_name, newagents, "", agent_state=agent_name)

                if not need_belief_alignment(refinement_r_beliefs, refinement_aligned):
                    print("\tdivergences are relevant!")
                    relevant_divergences.add(div1)
                    relevant_divergences.add(div2)
                    relevant_divergences.add(div3)
                    return relevant_divergences, newagents
                else:
                    print("\tdivergences aren't relevant")
                    continue

    # Look for three relevant divergence
    print("Testing with 4 relevant divergences")
    if len(divs)<3:
        return False
    for i in range(len(divs)-3):
        for j in range(i+1, len(divs)-2):
            for k in range(j+1, len(divs)-1):
                for l in range(k+1, len(divs)): 
                    div1 = divs[i]
                    div2 = divs[j]
                    div3 = divs[k]
                    div4 = divs[l]

                    print("divs tested :")
                    div1.show()
                    div2.show()
                    div3.show()
                    div4.show()

                    newagents = deepcopy(agents)
                    div1.align_state(newagents[agent_name].state)
                    div2.align_state(newagents[agent_name].state)
                    div3.align_state(newagents[agent_name].state)
                    div4.align_state(newagents[agent_name].state)
                    refinement_aligned = refine_agenda(agent_name, newagents, "", agent_state=agent_name)

                    if not need_belief_alignment(refinement_r_beliefs, refinement_aligned):
                        print("\tdivergences are relevant!")
                        relevant_divergences.add(div1)
                        relevant_divergences.add(div2)
                        relevant_divergences.add(div3)
                        relevant_divergences.add(div4)
                        return relevant_divergences, newagents
                    else:
                        print("\tdivergences aren't relevant")
                        continue

    return False

def find_div_for_same_eff(agents, agent_name, action):
    belief_divergences = BeliefDivergences()
    belief_divergences.update(agents) 
    belief_divergences.show()

    divs = belief_divergences.get_divergences()

    relevant_divergences = BeliefDivergences()

    # Look for one relevant divergence
    print("Testing with 1 relevant divergence")
    for divergence in divs:
        print("divergence tested = ", end="")
        divergence.show()

        newagents = deepcopy(agents)
        divergence.align_state(newagents[agent_name].state)
        refinement_aligned = refine_agenda(agent_name, newagents, "", agent_state=agent_name)

        if not check_diff_effects(newagents, action):
            print("\tdivergence is relevant!")
            relevant_divergences.add(divergence)
            return relevant_divergences, newagents
        else:
            print("\tdivergence isn't relevant")
            continue

    # Look for two relevant divergence
    if len(divs)<2:
        return False
    print("Testing with 2 relevant divergences")
    for i in range(len(divs)-1):
        for j in range(i+1, len(divs)):
            div1 = divs[i]
            div2 = divs[j]

            print("divs tested :")
            div1.show()
            div2.show()

            newagents = deepcopy(agents)
            div1.align_state(newagents[agent_name].state)
            div2.align_state(newagents[agent_name].state)
            refinement_aligned = refine_agenda(agent_name, newagents, "", agent_state=agent_name)

            if not check_diff_effects(newagents, action):
                print("\tdivergences are relevant!")
                relevant_divergences.add(div1)
                relevant_divergences.add(div2)
                return relevant_divergences, newagents
            else:
                print("\tdivergences aren't relevant")
                continue

    return False

## Delay
def create_delay_branch(node, rel_divs, newagents, previous_action, current_cost, e_flagged_nodes, new_e_flagged_nodes, u_flagged_nodes, phase):
    print("Trying to create delaying branch")
    # input()
    
    first_node = node.get_first_node()
    initial_agents = first_node.start_agents

    #TODO Check if divs is only one div on INF
    # Check if more than one div
    print("rel_divs=", rel_divs)
    if len(rel_divs.divergences) > 1:
        print("\tMore than one div")
        return node
    # Check if div is on INF attribute
    div = rel_divs.divergences[0]
    if initial_agents.get_fluent_obs(div.property)!=ObsType.INF:
        print("\tDiv not on INF attribute")
        return node

    # check if relevant divs aren't initial
    # If div not initial, find action creating div
    if div.in_agents(initial_agents):
        print("\tinitial div ..")
        return node
    else:
        print("\tdiv not initial!")
        # input()

        # From current node, compare start/end agents while going back (previous_node)
        # Identify in which node div is created
        found = False
        n = node
        n.end_agents = newagents
        n.end_action = previous_action.next[0]
        n.cost = current_cost
        while not found:
            print("\t\ttesting n=", n)
            agts =  n.start_agents if n.previous_node==None else n.previous_node.end_agents
            if not div.in_agents(agts) and div.in_agents(n.end_agents):
                found=True
            else:
                if n.previous_node == None:
                    raise Exception("div node not found!")
                n = n.previous_node
        div_node = n
        print("\tdiv node identified : ", div_node)
        # input()

        # Now find diverging action from start of node by applying actions
        div_action_found = False
        agts =  div_node.start_agents if div_node.previous_node==None else div_node.previous_node.end_agents
        find_agents = deepcopy(agts)
        action = div_node.start_action
        if action.name == "BEGIN":
            # print("action=", action)
            # print("action.next=", action.next)
            # print("div_node.end_agents[CM.g_other_agent_name[action.agent]].planned_actions=", div_node.end_agents[CM.g_other_agent_name[action.agent]].planned_actions)
            for a in action.next:
                if a.id == div_node.end_agents[CM.g_other_agent_name[action.agent]].planned_actions[0][0]:
                    action = a
                    break
        length_div_node_top = 0
        while not div_action_found:
            # apply action
            print("\ttesting action=", action)
            print("\t\tR-Agenda in {}".format(action.agent_agendas[CM.g_robot_name]))
            print("\t\tH-Agenda in {}".format(action.agent_agendas[CM.g_human_name]))
            if action.name in ["BEGIN", "WAIT", "IDLE"]:
                action = action.next[0]
                continue
            if action.name == "COM_ALIGN":
                result = action.parameters[0].split("-")
                if len(result)==3:
                    prop,key,val = result
                elif len(result)==2:
                    prop,val = result
                else:
                    raise Exception("spliting failed...")
                f = find_agents[CM.g_human_name].state.get_fluent(prop)
                try:
                    f.val = int(val)
                except ValueError:
                    f.val = val
                action = action.next[0]
                continue
            # print_agents_step(find_agents)
            acting_agent = action.agent
            agents_before_div = deepcopy(find_agents)
            print("before acting")
            Operator.apply(find_agents, action, acting_agent, agent_state_in=acting_agent, agent_state_out=acting_agent)
            print("after acting")
            print_agents_step(find_agents)
            if CM.g_robot_name==acting_agent:
                apply_inferable_effects(find_agents, action)
            elif CM.g_human_name==acting_agent:
                Operator.apply(find_agents, action, acting_agent, agent_state_in=CM.g_other_agent_name[acting_agent], agent_state_out=CM.g_other_agent_name[acting_agent])
            print("after other")
            print_agents_step(find_agents)
            # check if div
            if div.in_agents(find_agents):
                div_action_found = True
            else:
                length_div_node_top += 1
                print("action.next=", action.next)
                if action == div_node.end_action:
                    raise Exception("div action not found...")
                if len(action.next)==0:
                    raise Exception("empty next actions ...")
                if len(action.next)!=1:
                    raise Exception("several next actions inside a node ...")
                action = action.next[0]
        div_action = action
        print("agendas:")
        print("div_action.agent_agendas[CM.g_human_name]=", div_action.agent_agendas[CM.g_human_name])
        print("div_action.agent_agendas[CM.g_robot_name]=", div_action.agent_agendas[CM.g_robot_name])
        agents_before_div[CM.g_human_name].agenda = div_action.agent_agendas[CM.g_human_name]
        agents_before_div[CM.g_robot_name].agenda = [div_action] + div_action.agent_agendas[CM.g_robot_name]
        print("\tdiv action identified : ", div_action)
        print_agents_step(agents_before_div)
        # input()

        # Create delaying branch before div_action
        if div_node.start_action != div_action:
            print("\tBranching:")
            # Div node bottom
            div_node_bottom = NM.Node()
            div_node_bottom.start_agents = agents_before_div
            div_node_bottom.start_action = div_action
            div_node_bottom.previous_node = div_node
            div_node_bottom.end_agents = div_node.end_agents
            div_node_bottom.end_action = div_node.end_action
            div_node_bottom.next_nodes = div_node.next_nodes
            div_node_bottom.type = div_node.type
            div_node_bottom.flag = div_node.flag
            div_node_bottom.cost = current_cost
            print("BRANCHING current_cost=", current_cost)
            div_node_bottom.length = div_node.length - length_div_node_top
            div_node_bottom.depth = div_node.depth
            node = div_node_bottom
            if phase=="e":
                e_flagged_nodes.append(node)
            elif phase=="u":
                u_flagged_nodes.append(node)
            else:
                raise Exception("phase unknown !")
            print("\tdiv_node_bottom created => ", div_node_bottom)
            
            # Delay node
            delay_current_cost = div_action.previous.current_plan_cost + CM.g_delay_cost[CM.g_robot_name]
            delay_action = Operator.create_inactivity_op("DELAY", CM.g_delay_cost[CM.g_robot_name], CM.g_robot_name, div_action.previous, delay_current_cost, branching_name="delaying")
            end_agents_delay = deepcopy(agents_before_div)
            end_agents_delay[CM.g_robot_name].planned_actions.append( (delay_action.id, delay_action.name, delay_action.agent, delay_action.parameters) )
            delay_node = NM.Node()
            delay_node.start_agents = agents_before_div
            delay_node.start_action = delay_action
            delay_node.previous_node = div_node
            delay_node.end_agents = end_agents_delay
            delay_node.end_action = delay_action
            delay_node.next_nodes = []
            delay_node.type = NM.Node.Type.D
            delay_node.flag = NM.Node.Flag.E
            delay_node.cost = delay_current_cost
            delay_node.length = 1
            delay_node.depth = div_node.depth - div_node_bottom.length + delay_node.length
            if phase=="e":
                new_e_flagged_nodes.append(delay_node)
            elif phase=="u":
                u_flagged_nodes.append(node)
            else:
                raise Exception("phase unknown !")
            print("\tdelay_node created => ", delay_node)

            # Div node top
            div_node.start_agents = div_node.start_agents #
            div_node.start_action = div_node.start_action #
            div_node.previous_node = div_node.previous_node #
            div_node.end_agents = agents_before_div
            div_node.end_action = div_action.previous
            div_node.next_nodes = [div_node_bottom, delay_node]
            div_node.type = NM.Node.Type.R
            div_node.flag = NM.Node.Flag.F
            div_node.cost = div_action.previous.current_plan_cost
            div_node.length = length_div_node_top
            div_node.depth = div_node.depth - div_node_bottom.length
            if phase=="e":
                e_flagged_nodes.remove(div_node)
            elif phase=="u":
                u_flagged_nodes.remove(node)
            else:
                raise Exception("phase unknown !")
            print("\tdiv_node edited => ", div_node)
            # input()
        else:
            print("\tBranching:")
            
            # Delay node
            delay_current_cost = div_action.previous.current_plan_cost + CM.g_delay_cost[CM.g_robot_name]
            delay_action = Operator.create_inactivity_op("DELAY", CM.g_delay_cost[CM.g_robot_name], CM.g_robot_name, div_action.previous, delay_current_cost, branching_name="delaying")
            end_agents_delay = deepcopy(agents_before_div)
            end_agents_delay[CM.g_robot_name].planned_actions.append( (delay_action.id, delay_action.name, delay_action.agent, delay_action.parameters) )
            delay_node = NM.Node()
            delay_node.start_agents = agents_before_div
            delay_node.start_action = delay_action
            delay_node.previous_node = div_node.previous_node
            div_node.previous_node.next_nodes.append(delay_node)
            delay_node.end_agents = end_agents_delay
            delay_node.end_action = delay_action
            delay_node.next_nodes = []
            delay_node.type = NM.Node.Type.D
            delay_node.flag = NM.Node.Flag.E
            delay_node.cost = delay_current_cost
            delay_node.length = 1
            # delay_node.depth = div_node.depth - div_node_bottom.length + delay_node.length
            if phase=="e":
                new_e_flagged_nodes.append(delay_node)
            elif phase=="u":
                u_flagged_nodes.append(node)
            else:
                raise Exception("phase unknown !")
            print("\tdelay_node created => ", delay_node)

        return node

def merge_nodes(n, e_flagged_nodes, u_flagged_nodes):
    if len(n.next_nodes)>0:
        if len(n.next_nodes)==1:
            nn = n.next_nodes[0]
            print("Node #{} merged into Node #{}".format(nn.id, n.id))

            n.next_nodes = nn.next_nodes
            n.end_action = nn.end_action
            n.end_agents = nn.end_agents
            n.length += nn.length
            n.cost += nn.cost
            n.type = nn.type
            n.flag = nn.flag

            if nn in e_flagged_nodes:
                e_flagged_nodes.remove(nn)
                e_flagged_nodes.append(n)
            if nn in u_flagged_nodes:
                u_flagged_nodes.remove(nn) 
                u_flagged_nodes.append(n) 
        for next_node in n.next_nodes:
            merge_nodes(next_node, e_flagged_nodes, u_flagged_nodes)

def kill_delay_branch(node):
    n = node
    while n.previous_node.type==NM.Type.D:
        n = n.previous_node
    n.previous_node.next_nodes.remove(n)