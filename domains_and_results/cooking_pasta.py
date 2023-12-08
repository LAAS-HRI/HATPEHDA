#!/usr/bin/env python3
import sys

sys.path.append("/home/afavier/ws/HATPEHDA/hatpehda")

import hatpehda as htpa
import CommonModule as CM
import NodeModule as NM
import gui
from copy import deepcopy
import time
import pickle

import cProfile
import pstats
# pr = cProfile.Profile()
# pr.enable()
# pr.disable()
# stats = pstats.Stats(pr).sort_stats("tottime")
# stats.dump_stats(filename="profiling.prof")
# # $ snakeviz profiling.prof

r_node = None

######################################################
################### Obs functions ###################
######################################################

def isObs(state, agent_a, agent_b):
    """ Boolean test, True if action of agent_a can be observed by agent_b, currently True if they are in the same room"""
    return get_at(state, agent_a) == get_at(state, agent_b)


######################################################
################### Primitive tasks ##################
######################################################

# salt #
def SaltCost(agents, state, agent):
    cost = 1.0
    return cost
def SaltPrecond(agents, state, agent):
    return get_at(state, agent)=="kitchen"
def SaltDonecond(agents, state, agent):
    return state.salt_added.val == True
def SaltEff(agents, state_in, state_out, agent):
    state_out.salt_added.val = True
saltAg = htpa.OperatorAg("add_salt", cost=SaltCost, donecond=SaltDonecond, effects=SaltEff)

# turn_on_pot_fire #
def TurnOnPotFirePrecond(agents, state, agent):
    return state.pot_fire.val == "off" and get_at(state, agent)=="kitchen"
def TurnOnPotFireDonecond(agents, state, agent):
    return state.pot_fire.val == "on"
def TurnOnPotFireEff(agents, state_in, state_out, agent):
    state_out.pot_fire.val = "on"
turnOnPotFireAg = htpa.OperatorAg("turn_on_pot_fire", precond=TurnOnPotFirePrecond, donecond=TurnOnPotFireDonecond, effects=TurnOnPotFireEff)

# move #
def MoveDonecond(agents, state, agent, place):
    return get_at(state, agent) == place
def MoveEff(agents, state_in, state_out, agent, place):
    agents.set_fluent_loc("at_"+agent, place)
    if state_in.at_pasta.val == agent:
        agents.set_fluent_loc("at_pasta", place)
    set_at(state_out, agent, place)
moveAg = htpa.OperatorAg("move", donecond=MoveDonecond, effects=MoveEff)

# grab pasta #
def GrabPastaPrecond(agents, state, agent):
    return get_at(state, agent) == get_at(state, "pasta")
def GrabPastaDonecond(agents, state, agent):
    return get_at(state, "pasta") == agent
def GrabPastaEff(agents, state_in, state_out, agent):
    set_at(state_out, "pasta", agent)
grabPastaAg = htpa.OperatorAg("grab_pasta", precond=GrabPastaPrecond, donecond=GrabPastaDonecond, effects=GrabPastaEff)

# pour pasta #
def PourPastaPrecond(agents, state, agent):
    return get_at(state, "pasta") == agent and get_at(state, agent)=="kitchen" and state.salt_added.val and state.pot_fire.val=="on"
def PourPastaEff(agents, state_in, state_out, agent):
    set_at(state_out, "pasta", get_at(state_in, agent))
pourPastaAg = htpa.OperatorAg("pour_pasta", precond=PourPastaPrecond, effects=PourPastaEff)

# cleanCounter #
def CleanCounterPrecond(agents, state, agent):
    return get_at(state, agent)=="kitchen"
def CleanCounterEffects(agents, state_in, state_out, agent):
    state_out.counter_clean.val = True
cleanCounterAg = htpa.OperatorAg("clean_counter", precond=CleanCounterPrecond, effects=CleanCounterEffects)

common_ag = [saltAg, turnOnPotFireAg, moveAg]
robot_operator_ag = common_ag + [cleanCounterAg]
human_operator_ag = common_ag +  [grabPastaAg, pourPastaAg]


######################################################
################### Abstract Tasks ###################
######################################################

def dec_cook_R_1(agents, state, agent):
    if state.salt_added.val == True and state.pot_fire.val == "on":
        return []
    if state.salt_added.val == True and state.pot_fire.val == "off":
        return [("come_turn_on_pot_fire",)]
    if state.salt_added.val == False and state.pot_fire.val == "on":
        return [("come_add_salt",)]
    if state.salt_added.val != True and state.pot_fire.val != "on":
        return [("come_add_salt",), ("come_turn_on_pot_fire",)]

def dec_cook_R_2(agents, state, agent):
    if state.salt_added.val != True and state.pot_fire.val != "on":
        return [("come_turn_on_pot_fire",), ("come_add_salt",)]
    return False

def dec_cook_H_1(agents, state, agent):
    if state.salt_added.val == True:
        return [("get_pasta",), ("come_pour_pasta",)]
    else:
        return [("get_pasta",), ("come_add_salt",), ("come_pour_pasta",)]

def dec_cook_H_2(agents, state, agent):
    if state.salt_added.val==False:
        # return [("come_add_salt",), ("get_pasta",), ("come_pour_pasta",)]
        return [("add_salt",), ("get_pasta",), ("come_pour_pasta",)]
    return False

def dec_come_add_salt_close(agents, state, agent):
    if get_at(state, agent)=="kitchen":
        return [("add_salt",)]
    return False

def dec_come_add_salt_far(agents, state, agent):
    if get_at(state, agent)!="kitchen":
        return [("move", "kitchen"), ("add_salt",)]
    return False

def dec_come_clean_close(agents, state, agent):
    if get_at(state, agent)=="kitchen":
        return [("clean_counter",)]
    return False

def dec_come_clean_far(agents, state, agent):
    if get_at(state, agent)!="kitchen":
        return [("move", 'kitchen'), ("add_salt",)]
    return False

def dec_come_turn_pot_fire_on_close(agents, state, agent):
    if get_at(state, agent)=="kitchen":
        return [("turn_on_pot_fire",)]
    return False

def dec_come_turn_pot_fire_on_far(agents, state, agent):
    if get_at(state, agent)!="kitchen":
        return [("move", "kitchen"), ("turn_on_pot_fire",)]
    return False

def dec_get_pasta_close(agents, state, agent):
    if get_at(state, agent)==get_at(state, "pasta"):
        return [("grab_pasta",)]
    return False

def dec_get_pasta_far(agents, state, agent):
    if get_at(state, agent)!=get_at(state, "pasta"):
        return [("move", get_at(state, "pasta")), ("grab_pasta",)]
    return False

def dec_come_pour_pasta_close(agents, state, agent):
    if get_at(state, agent)=="kitchen":
        return [("pour_pasta",)]
    return False

def dec_come_pour_pasta_far(agents, state, agent):
    if get_at(state, agent)!="kitchen":
        return [("move", "kitchen"), ("pour_pasta",)]
    return False

common_methods = []
ctrl_methods = common_methods + [
            ("cook", dec_cook_R_1, dec_cook_R_2),
            ("come_clean_counter", dec_come_clean_close, dec_come_clean_far),
            ("come_add_salt", dec_come_add_salt_close, dec_come_add_salt_far),
            ("come_turn_on_pot_fire", dec_come_turn_pot_fire_on_close, dec_come_turn_pot_fire_on_far),
]
unctrl_methods = common_methods + [
            ("get_pasta", dec_get_pasta_close, dec_get_pasta_far),
            ("come_add_salt", dec_come_add_salt_close, dec_come_add_salt_far),
            ("come_pour_pasta", dec_come_pour_pasta_close, dec_come_pour_pasta_far),
            ("cook", dec_cook_H_1, dec_cook_H_2),
]


######################################################
###################### Triggers ######################
######################################################

common_triggers = []
robot_triggers = common_triggers + []
human_triggers = common_triggers + []


######################################################
################## Helper functions ##################
######################################################

def get_bin_array(n, max):
    array = [int(x) for x in bin(n)[2:]]
    if len(array)<max:
        for i in range(max-len(array)):
            array = [0] + array
    return array

def get_at(state, agent):
    if agent=="robot":
        return state.at_robot.val
    elif agent=="human":
        return state.at_human.val
    elif agent=="pasta":
        return state.at_pasta.val
    else:
        raise Exception("get at {} not in state.at !".format(agent))

def set_at(state, agent, at):
    if agent=="robot":
        state.at_robot.val = at
    elif agent=="human":
        state.at_human.val = at
    elif agent=="pasta":
        state.at_pasta.val = at
    else:
        raise Exception("set at {} not in state.at !".format(agent))


######################################################
######################## MAIN ########################
######################################################

def initDomain(n):
    robot_name = "robot"
    human_name = "human"
    CM.set_robot_name
    CM.set_robot_name(robot_name)
    CM.set_human_name(human_name)
    CM.init_other_agent_name()

    # Initial state
    initial_state = htpa.State("init")

    # Static properties
    initial_state.create_fluent("self_name", "None", htpa.ObsType.OBS, "none", False)
    initial_state.create_fluent("other_agent_name", {robot_name:human_name, human_name:robot_name}, htpa.ObsType.OBS, "none", False) 

    # Generate initial state
    domains = {
        "at_robot":         ["kitchen", "room"], # add h_at_robot ?
        "at_human":         ["kitchen", "room"],
        "at_pasta":         ["kitchen", "room"],
        "salt_added":       [False, True],
        "pot_fire":         ["off", "on"],
        "h_at_pasta":       ["kitchen", "room"],
        "h_salt_added":     [False, True],
        "h_pot_fire":       ["off", "on"],
        "starting_agent":   [robot_name, human_name],
    }
    bin_array = get_bin_array(n, max=len(domains))

    values = {}
    for i,f in enumerate(domains):
        values[f] = domains[f][bin_array[i]]

    # Dynamic properties
    initial_state.create_fluent("at_robot",     values["at_robot"],     htpa.ObsType.OBS, values["at_robot"],   True)
    initial_state.create_fluent("at_human",     values["at_human"],     htpa.ObsType.OBS, values["at_human"],   True) 
    initial_state.create_fluent("at_pasta",     values["at_pasta"],     htpa.ObsType.OBS, values["at_pasta"],   True)
    initial_state.create_fluent("salt_added",   values["salt_added"],   htpa.ObsType.INF, "kitchen",            True)
    initial_state.create_fluent("pot_fire",     values["pot_fire"],     htpa.ObsType.OBS, "kitchen",            True)
    initial_state.create_fluent("counter_clean", False,                 htpa.ObsType.INF, "kichen",             True)

    # Robot
    htpa.declare_operators_ag(robot_name, robot_operator_ag)
    for me in ctrl_methods:
        htpa.declare_methods(robot_name, *me)
    htpa.declare_triggers(robot_name, *robot_triggers)
    htpa.set_observable_function("robot", isObs)
    robot_state = deepcopy(initial_state)
    robot_state.self_name.val = robot_name
    robot_state.__name__ = robot_name + "_init"
    htpa.set_state(robot_name, robot_state)
    htpa.add_tasks(robot_name, [("cook",), ("come_clean_counter",)])

    # Human
    htpa.declare_operators_ag(human_name, human_operator_ag)
    for me in unctrl_methods:
        htpa.declare_methods(human_name, *me)
    htpa.declare_triggers(human_name, *human_triggers)
    htpa.set_observable_function("human", isObs)
    human_state = deepcopy(initial_state)
    human_state.__name__ = human_name + "_init"
    human_state.reset_fluent_locs()
    human_state.self_name.val = human_name
    human_state.at_pasta.val = values["h_at_pasta"]
    human_state.salt_added.val = values["h_salt_added"]
    human_state.pot_fire.val = values["h_pot_fire"]
    htpa.set_state(human_name, human_state)
    htpa.add_tasks(human_name, [("cook",)])

    # Starting Agent
    CM.set_starting_agent(values["starting_agent"])

def node_explo(with_contrib, with_graph, with_delay, n):
    robot_name = CM.get_robot_name()
    human_name = CM.get_human_name()

    print("INITIAL STATES")
    htpa.show_init()

    CM.set_debug(True)
    # htpa.set_compute_gui(True)
    # htpa.set_view_gui(True)
    # htpa.set_stop_input(True)
    # htpa.set_debug_agenda(True)
    # htpa.set_stop_input_agenda(True)

    n_plot = 0
    print("Start first exploration")
    first_explo_dur = time.time()
    first_node, Ns, u_flagged_nodes, n_plot = htpa.heuristic_exploration(n_plot)
    first_explo_dur = int((time.time() - first_explo_dur)*1000)
    print("\t=> time spent first exploration = {}ms".format(first_explo_dur))
    # htpa.gui.show_tree(first_node, "sol", view=True)
    # htpa.gui.show_all(htpa.get_last_nodes_action(first_node), robot_name, human_name, with_begin="false", with_abstract="true")
    # input()

    # htpa.set_debug(True)
    # htpa.set_compute_gui(True)
    # htpa.set_view_gui(True)
    # htpa.set_stop_input(True)
    # htpa.set_debug_agenda(True)
    # htpa.set_stop_input_agenda(True)

    print("Start refining u nodes")
    refine_u_dur = time.time()
    htpa.refine_u_nodes(first_node, u_flagged_nodes, n_plot)
    refine_u_dur = int((time.time() - refine_u_dur)*1000)
    print("\t=> time spent refining = {}ms".format(refine_u_dur))
    print("Total duration = {}ms".format(first_explo_dur+refine_u_dur))

    # Are beliefs aligned ?
    NM.show_belief_alignmen(first_node)

    # Show final plans
    NM.show_plans_str(first_node)

    print("best_traces:")
    NM.compute_node_metrics(first_node)
    NM.filter_delay_traces(first_node)
    print(NM.get_best_traces(first_node))
    print("best_metrics:")
    print(first_node.best_metrics)



    view = False
    if with_graph:
        gui.show_all(NM.get_last_nodes_action(first_node), robot_name, human_name, n, with_contrib, with_delay, with_begin="false", with_abstract="false", view=view)
        # htpa.gui.show_tree(first_node, "sol", view=view)

if __name__ == "__main__":

    # sys.argv = ['/home/afavier/ws/HATPEHDA/domains_and_results/cooking_pasta.py', 'with_c', 'with_g', 'with_d', 65]
    if len(sys.argv) != 5:
        print("argv({})={}".format(len(sys.argv), sys.argv))
        raise Exception("Missing arguements! (with_contrib, with_graph, with_delay, n)")
    with_contrib = sys.argv[1]=="with_c"
    with_graph = sys.argv[2]=="with_g"
    with_delay = sys.argv[3]=="with_d"
    n = int(sys.argv[4])

    print("RUN N={} With={}".format(n, with_contrib))
    initDomain(n)
    CM.set_with_contrib(with_contrib)
    CM.set_with_delay(with_delay)

    node_explo(with_contrib, with_graph, with_delay, n)