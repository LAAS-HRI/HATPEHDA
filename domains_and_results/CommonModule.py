from copy import deepcopy, copy
from typing import Any, Dict, List, Type
from enum import Enum
import sys

###############
## CONSTANTS ##
###############
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class DecompType(Enum):
    OK = 0
    NO_APPLICABLE_METHOD = 1
    AGENDA_EMPTY = 2
    BOTH_AGENDAS_EMPTY = 3
class OpType(Enum):
    NOT_APPLICABLE = 0
    DONE = 1

DEFAULT_ACTION_COST = 1.0
LRD_ACTION_COST = 1.0

path = "/home/afavier/ws/HATPEHDA/domains_and_results/"

#############
## CLASSES ##
#############
## Task ##
class Task:
    __ID = 0
    
    def __init__(self, name: str, parameters: list, is_abstract: bool, why, method_number: int, agent: str):
        self.id = Task.__ID
        Task.__ID += 1
        self.name = name
        self.parameters = parameters
        self.agent = agent

        # From which task it is decomposed, and how (number/id of method used)
        # self.why = why  # From which task it is decomposed
        self.method_number = method_number

        self.is_abstract = is_abstract

        # self.previous = None
        # self.next = []
        self.current_plan_cost = -1.0

    def assign_next_id(self):
        self.id = Task.__ID
        Task.__ID += 1
    
    def __repr__(self):
        abs_str = "A" if self.is_abstract else "P"
        return "{}-{}{}-{}{}".format(self.id, self.agent, abs_str, self.name, self.parameters)

    def show(self):
        print(self)

class AbstractTask(Task):
    def __init__(self, name: str, parameters: list, why, method_number: int, agent: str):
        super().__init__(name, parameters, True, why, method_number, agent)

    def __repr__(self):
        return "{}-{}AT-{}{}".format(self.id, self.agent, self.name, self.parameters)

class Method:
    __slots__ = ('AT_name', 'done_cond', 'pre_cond', 'decomp', 'multi_decomp')
    def __init__(self, AT_name, done_cond=None, pre_cond=None, decomp=None, multi_decomp=None):
        self.AT_name = AT_name
        self.done_cond = done_cond
        self.pre_cond = pre_cond
        self.decomp = decomp
        self.multi_decomp = multi_decomp

    def is_done(self, state, AT):
        return self.done_cond(state, AT.agent, *AT.parameters) if self.done_cond!=None else False

    def is_applicable(self, state, AT):
        return self.pre_cond(state, AT.agent, *AT.parameters) if self.pre_cond!=None else True
    
    def get_decomp(self, state, AT):
        if self.multi_decomp==None:
            return [self.decomp(state, AT.agent, *AT.parameters)] if self.decomp!=None else [[]]
        else:
            return self.multi_decomp(state, AT.agent, *AT.parameters)
            
class PrimitiveTask(Task):
    def __init__(self, name: str, parameters: list, why, method_number: int, agent: str) -> None:
        super().__init__(name, parameters, False, why, method_number, agent)
    
    def __repr__(self):
        return "{}-{}PT-{}{}".format(self.id, self.agent, self.name, self.parameters)

class Operator:
    __slots__ = ('PT_name', 'done_cond', 'pre_cond', 'effects', 'cost_function', 'shared_resource')
    def __init__(self, PT_name, done_cond=None, pre_cond=None, effects=None, cost_function=None, shared_resource=None):
        self.PT_name = PT_name
        self.done_cond = done_cond
        self.pre_cond = pre_cond
        self.effects = effects
        self.cost_function = cost_function
        self.shared_resource = shared_resource

    def is_done(self, state, PT):
        return self.done_cond(state, PT.agent, *PT.parameters) if self.done_cond!=None else False

    def get_shared_resource(self, state, PT):
        return self.shared_resource(state, PT.agent, *PT.parameters) if self.shared_resource!=None else None

    def is_applicable(self, state, PT):
        return self.pre_cond(state, PT.agent, *PT.parameters) if self.pre_cond!=None else True

    def get_cost(self, state, PT):
        return self.cost_function(state, PT.agent, *PT.parameters) if self.cost_function!=None else DEFAULT_ACTION_COST

    def apply_effects(self, state, agent: str, parameters):
        if self.effects!=None:
            self.effects(state, agent, *parameters)

    def apply(self, state, PT):

        # Check Done and Pre conditions
        if self.is_done(state, PT):
            print(bcolors.WARNING + "already done!" + bcolors.ENDC)
            return OpType.DONE
        if not self.is_applicable(state, PT):
            # print(bcolors.WARNING + str(PT) + " not applicable!" + bcolors.ENDC)
            return OpType.NOT_APPLICABLE

        # Compute cost
        cost = self.get_cost(state, PT)

        # Apply effects to acting and other agent beliefs
        self.apply_effects(state, PT.agent, PT.parameters)

        shared_resource = self.get_shared_resource(state, PT)

        return state, cost, shared_resource

class Action(PrimitiveTask):
    def __init__(self) -> None:
        super().__init__(None, None, None, None, None)

    def cast_PT2A(PT: PrimitiveTask, cost: float, shared_resource: str):
        """PT is modified!!"""
        PT.__class__ = Action
        PT.cost = cost
        PT.shared_resource = shared_resource
        return PT
    
    def minimal_init(self, id, name, parameters, agent):
        super().__init__(name, parameters, None, -1, agent)
        self.id = id

    def is_idle(self):
        return self.is_passive() and "IDLE" in self.parameters
    
    def is_pass(self):
        return self.is_passive() and "PASS" in self.parameters
    
    def is_wait(self):
        return self.is_passive() and "WAIT" in self.parameters
    
    def is_wait_turn(self):
        return self.is_passive() and "WAIT_TURN" in self.parameters

    def is_passive(self):
        return self.name=="PASSIVE"

    def create_passive(agent: str, type: str):
        return Action.cast_PT2A(PrimitiveTask("PASSIVE", [type], None, 0, agent), g_wait_cost[agent], None)

    def are_similar(A1, A2):
        if A1.is_passive() and A2.is_passive():
            return True
        elif A1.name==A2.name:
            if A1.parameters==A2.parameters:
                if A1.cost==A2.cost:
                    if A1.agent==A2.agent:
                        return True
        return False

    def short_str(self):
        return f"{self.agent}{self.id}"

    def __repr__(self):
        # return "{}-{}A-{}{}-{}".format(self.id, self.agent, self.name, self.parameters, self.cost)
        return "{}-{}A-{}{}".format(self.id, self.agent, self.name, self.parameters)

class Trigger:
    __slots__ = ('pre_cond', 'decomp')
    def __init__(self, pre_cond, decomp):
        self.pre_cond = pre_cond
        self.decomp = decomp

## State ##
g_dyn_fluent_names = set()
g_static_fluent_names = set()
StateClass = None # None | Type
class InitState:
    def create_static_fluent(self, name, value):
        global g_static_fluent_names
        g_static_fluent_names.add(name)
        setattr(self, name, value)

    def create_dyn_fluent(self, name, value):
        global g_dyn_fluent_names
        g_dyn_fluent_names.add(name)
        setattr(self, name, value)

    def get_state_conversion(self):
        global StateClass
        class State:
            __slots__ = g_dyn_fluent_names.union(g_static_fluent_names)
            def __deepcopy__(self, memo):
                cp = StateClass()
                # static part
                for f in g_static_fluent_names:
                    setattr(cp, f, getattr(self, f))
                # dynamic part
                for f in g_dyn_fluent_names:
                    setattr(cp, f, deepcopy(getattr(self, f)))

                return cp

        StateClass = State
        s = StateClass()
        for f in StateClass.__slots__:
            setattr(s, f, getattr(self, f))
        return s

## Planning State ##
class PState:
    __ID = 0
    def __init__(self) -> None:
        self.state = None 
        self.R_agenda = [] #Type: List[Task]
        self.H_agenda = [] #Type: List[Task]
        
        self.id = PState.__ID
        PState.__ID += 1

        self.best_metrics = None

        # Structure
        self.parents = [] # list of ConM.ActionPair
        self.children = [] # list of ConM.ActionPair
    
    def are_similar(ips1: int, ips2: int):
        ps1 = g_PSTATES[ips1]
        ps2 = g_PSTATES[ips2]
        similar = True

        # Compare H_Agendas
        if similar:
            if len(ps1.H_agenda)!=len(ps2.H_agenda):
                similar = False
            else:
                for i,t1 in enumerate(ps1.H_agenda):
                    t2 = ps2.H_agenda[i]
                    if t1.name!=t2.name or t1.parameters!=t2.parameters or t1.agent!=t2.agent:
                        similar = False
                        break

        # Compare R_Agendas
        if similar:
            if len(ps1.R_agenda)!=len(ps2.R_agenda):
                similar = False
            else:
                for i,t1 in enumerate(ps1.R_agenda):
                    t2 = ps2.R_agenda[i]
                    if t1.name!=t2.name or t1.parameters!=t2.parameters or t1.agent!=t2.agent:
                        similar = False
                        break

        # Compare states
        if similar:
            for f in g_dyn_fluent_names:

                o1 = getattr(ps1.state, f)
                if is_instance_userdefined_and_newclass(o1):
                    o2 = getattr(ps2.state, f)
                    for s in o1.__slots__:
                        if getattr(o1, s) != getattr(o2, s):
                            similar = False
                            break

                else:
                    if getattr(ps1.state, f) != getattr(ps2.state, f):
                        similar = False
                
                if not similar:
                    break

        return similar
    
    def isRInactive(self):
        # look in children and find non passive robot action
        for c in self.children:
            if not c.robot_action.is_passive():
                return False
        return True
    
    def isHInactive(self):
        # look in children and find non passive human action
        for c in self.children:
            if not c.human_action.is_passive():
                return False
        return True

    def __deepcopy__(self, memo):
        cp = PState()
        cp.H_agenda = copy(self.H_agenda)
        cp.R_agenda = copy(self.R_agenda)
        cp.state = deepcopy(self.state)
        cp.parents = self.parents
        cp.children = self.children

    def __repr__(self) -> str:
        return f"(ID:{self.id})"


g_PSTATES = {0: PState()} 
g_FINAL_IPSTATES = []
g_BACK_EDGES = []

def is_instance_userdefined_and_newclass(inst):
    cls = inst.__class__
    if hasattr(cls, '__class__'):
        return ('__dict__' in dir(cls) or hasattr(cls, '__slots__'))
    return False

def set_initial_state(initial_state: InitState):
    state = initial_state.get_state_conversion()
    g_PSTATES[0].state = state

def declare_R_methods(method_list):
    declare_methods('R', method_list)
def declare_H_methods(method_list):
    declare_methods('H', method_list)
def declare_methods(agent, method_list):
    s_ag = g_static_agents[agent]
    s_ag.methods = {}
    for m in method_list:
        if m.AT_name in s_ag.methods:
            s_ag.methods[m.AT_name].append(m)
        else:
            s_ag.methods[m.AT_name] = [m]

def declare_R_operators(op_list):
    declare_operators('R', op_list)
def declare_H_operators(op_list):
    declare_operators('H', op_list)
def declare_operators(agent, op_list):
    s_ag = g_static_agents[agent]
    s_ag.operators = {}
    for o in op_list:
        s_ag.operators[o.PT_name] = o

def set_initial_R_agenda(tasks):
    set_initial_agenda('R', tasks)
def set_initial_H_agenda(tasks):
    set_initial_agenda('H', tasks)
def set_initial_agenda(agent, tasks):
    s_ag = g_static_agents[agent]
    agenda = []
    for t in tasks:
        if t[0] in s_ag.methods:
            agenda.append(AbstractTask(t[0], t[1:], None, 0, agent))
        elif t[0] in s_ag.operators:
            agenda.append(PrimitiveTask(t[0], t[1:], None, 0, agent))
        else:
            raise Exception("{} isn't known by agent {}".format(t[0], agent))
    
    if agent=='R':
        g_PSTATES[0].R_agenda = agenda
    elif agent=='H':
        g_PSTATES[0].H_agenda = agenda


## StaticAgents ##
class StaticAgent:
    def __init__(self) -> None:
        self.operators = {}
        self.methods = {}

    def has_operator_for(self, PT):
        return PT.name in self.operators

    def has_method_for(self, AT):
        return AT.name in self.methods
g_static_agents = {'H':StaticAgent(), 'R':StaticAgent()}


## APState ##
class APState:
    def __init__(self) -> None:
        self.action = None #type: Action
        self.ipstate = None #type: int

## AAPState ##
class AAPState:
    def __init__(self, action_pair, ipstate) -> None:
        self.action_pair = action_pair #type: ActionPair
        self.ipstate = ipstate #type: int
    
    def __repr__(self) -> str:
        return f"{self.action_pair.human_action.name}{self.action_pair.human_action.parameters}|{self.action_pair.robot_action.name}{self.action_pair.robot_action.parameters}"

## Refinement ##
class Decomposition:
    def __init__(self, subtasks, agenda=None):
        self.type = DecompType.OK
        
        self.subtasks = subtasks
        self.new_agenda = agenda
        self.PT = None if subtasks==[] else subtasks[0]
        self.next_action = None 


        # self.end_agents = None
        # self.next_pstate = None # new agendas and state inside
    
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

    def first_task_is_PT_and_has_op(self, agent_name):
        # checks if first task is primitive and has an operator
        first_task = self.subtasks[0]
        
        if first_task.is_abstract==False and g_static_agents[agent_name].has_operator_for(first_task):
            self.PT = self.subtasks[0]
            return True
        return False

    def first_task_is_PT_not_done(self, agent_name, state):
        # checks if first task is primitive, has an operator, is not done
        if self.first_task_is_PT_and_has_op(agent_name):
            op = g_static_agents[agent_name].operators[self.subtasks[0].name]
            return not op.is_done(state, self.PT)
        return False
    
    def first_task_is_PT_done(self, agent_name, state):
        # checks if first task is primitive, has an operator, is done
        if self.first_task_is_PT_and_has_op(agent_name):
            op = g_static_agents[agent_name].operators[self.subtasks[0].name]
            return op.is_done(state, self.PT)
        return False

class Refinement:
    __slots__ = ('decompos')
    def __init__(self, decomp=None):
        self.decompos = [] # type: list[Decomposition]
        if decomp!=None:
            self.decompos.append(decomp)
        
    def add(self, decomp):
        self.decompos.append(decomp)
    
    def show(self):
        print("[\n", end="")
        for decomp in self.decompos:
            print("\t{}".format(decomp))
        print("]")

    def show_next_actions(self):
        print("next actions:")
        for decomp in self.decompos:
            if decomp.PT != None:
                print("\t- {}".format(decomp.PT))
        print("")


##################################
## GLOBAL VARIABLES AND SETTERS ##
##################################
g_domain_name=""
def set_domain_name(dom_name):
    global g_domain_name
    g_domain_name = dom_name
g_other_agent_name={"H":"R", "R":"H"}
g_wait_cost = {"R":0.0, "H":2.0}
g_idle_cost = {"R":0.0, "H":0.0}
g_starting_agent = "R"
def set_starting_agent(agent):
    global g_starting_agent
    g_starting_agent = agent
g_debug = False
def set_debug(val):
    global g_debug
    g_debug = val
g_compute_gui = False
def set_compute_gui(val):
    global g_compute_gui
    g_compute_gui = val
g_view_gui = False
def set_view_gui(val):
    global g_view_gui
    g_view_gui = val


############
## PRINTS ##
############
# ─ ┌ ┐ ├ ┤ │ └ ┘
def show_init():
    print("┌────────────────────────────────────────────────────────────────────────┐")
    print("│ #INIT#                                                                 │")
    print("├────────────────────────────────────────────────────────────────────────┘")
    print_agendas_states(g_static_agents, with_static=True)

def str_init():
    out_str = ""
    out_str += "┌────────────────────────────────────────────────────────────────────────┐\n"
    out_str += "│ #INIT#                                                                 │\n"
    out_str += "├────────────────────────────────────────────────────────────────────────┘\n"
    out_str += str_agendas_states(g_static_agents, with_static=True)
    return out_str

def str_agents(agents):
    out_str = ""
    out_str += "┌────────────────────────────────────────────────────────────────────────┐\n"
    out_str += "│ #AGENTS#                                                               │\n"
    out_str += "├────────────────────────────────────────────────────────────────────────┘\n"
    out_str += str_agendas_states(agents)
    return out_str

def show_agents(agents):
    print("┌────────────────────────────────────────────────────────────────────────┐")
    print("│ #AGENTS#                                                               │")
    print("├────────────────────────────────────────────────────────────────────────┘")
    print_agendas_states(agents)

def str_agendas_states(agents, with_static=False):
    out_str = ""
    out_str += str_agendas(agents)
    out_str += "├─────────────────────────────────────────────────────────────────────────\n"
    out_str += "│ STATE =\n"
    out_str += str_state(agents.state, with_static=with_static)
    out_str += "└─────────────────────────────────────────────────────────────────────────\n"
    return out_str

def print_agendas_states(agents, with_static=False):
    print_agendas(agents)
    print("├─────────────────────────────────────────────────────────────────────────")
    print("│ STATE =")
    print_state(agents.state, with_static)
    print("└─────────────────────────────────────────────────────────────────────────")

def str_agendas(agents):
    out_str = ""
    out_str += str_agenda(agents["R"])
    out_str += str_agenda(agents["H"])
    return out_str

def print_agendas(agents):
    print_agenda(agents["R"])
    print_agenda(agents["H"])

def str_agenda(agent):
    out_str = ""
    out_str +=  "│ AGENDA {} =\n".format(agent.name)
    if len(agent.agenda)==0:
        out_str += "││\t*empty*\n"
    for t in agent.agenda:
        out_str += ("││\t{}\n".format(t))
    return out_str

def print_agenda(agent):
    print("│ AGENDA {} =".format(agent.name))
    if len(agent.agenda)==0:
        print("││\t*empty*")
    for t in agent.agenda:
        print("││\t-{}".format(t))

def str_state(state, indent=4, with_static=False):
    """Print each variable in state, indented by indent spaces."""
    out_str = ""
    if state != False:
        for f in state.fluents:
            if state.fluents[f].is_dyn or state.fluents[f].is_dyn==False and with_static:
                out_str += "││"
                for x in range(indent): out_str += " "
                out_str += f"{f}"
                out_str += ' = {}\n'.format(getattr(state, f))
    else:
        out_str += 'False\n'
    return out_str

def print_state(state, indent=4, with_static=False):
    """Print each variable in state, indented by indent spaces."""
    if state != False:
        for f in state.fluents:
            if state.fluents[f].is_dyn or state.fluents[f].is_dyn==False and with_static:
                print("││", end='')
                for x in range(indent): sys.stdout.write(' ')
                sys.stdout.write(state.__name__ + '.' + f)
                print(' = {}'.format(getattr(state,f)))
    else:
        print('False')

def print_solutions(begin_action: Action):
    print("Solutions:")
    last_actions = get_last_actions(begin_action)

    plans = []

    for last_action in last_actions:
        plan=[]
        action = last_action
        while action != begin_action:
            plan.append(action)
            action = action.previous
        plans.append(plan)

    for plan in plans:
        print("\nPLAN:")
        n=0
        for x in plan:
            n-=1
            print(plan[n], end=" - ") if x!=plan[-1] else print(plan[n])


############
## HELPER ##
############

def get_last_actions(begin_action: Action):
    if begin_action.next==[]:
        return [begin_action]
    else:
        last_actions = []
        for next in begin_action.next:
            last_actions += get_last_actions(next)

        return last_actions
