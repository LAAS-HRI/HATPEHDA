#!/usr/bin/env python3
import sys
# from HATPEHDA.hatpehda.hatpehda import multi_decomposition
import hatpehda
from copy import deepcopy
from hatpehda import gui
import time
from hatpehda.causal_links_post_treatment import compute_causal_links
import pickle
import rospy
from hatpehda import ros
from hatpehda.ros import RosNode


r_node = None

######################################################
################### Obs functions ###################
######################################################

def isObs(state, agent_a, agent_b):
    """ Boolean test, True if action of agent_a can be observed by agent_b, currently True if they are in the same room"""
    return state.room[agent_a] == state.room[agent_b]

######################################################
################### Primitive tasks ##################
######################################################

# move #
def MovePrecond(state, agent, place_from, place_to):
    return state.at[agent] == place_from
def MoveDonecond(state, agent, place_from, place_to):
    return state.at[agent] == place_to
def MovePostObsEff(state, agent, place_from, place_to):
    state.at[agent] = place_to
moveAg = hatpehda.OperatorAg("move", precond=MovePrecond, donecond=MoveDonecond, post_obs_eff=MovePostObsEff)

# pick #
def PickPrecond(state, agent, obj):
    return state.at[agent] == state.at[obj]
def PickDonecond(state, agent, obj):
    return obj in state.carry[agent]
def PickPostObsEff(state, agent, obj):
    state.carry[agent].append(obj)
pickAg = hatpehda.OperatorAg("pick", precond=PickPrecond, donecond=PickDonecond, post_obs_eff=PickPostObsEff)


common_operators = []
ctrl_operators = common_operators
unctrl_operators = common_operators

robot_operator_ag = [moveAg, pickAg]
human_operator_ag = [moveAg, pickAg]


######################################################
################### Abstract Tasks ###################
######################################################

def dec_get_coffee(agents, self_state, self_name):
    task_list = []
    if self_state.at[self_name] != self_state.at["coffee"]:
        task_list.append(("move", self_state.at[self_name], self_state.at["coffee"]))
    task_list.append(("pick", "coffee"))
    return task_list

common_methods = [
            ("get_coffee", dec_get_coffee),
]
ctrl_methods = common_methods 
unctrl_methods = common_methods 


######################################################
###################### Triggers ######################
######################################################

ctrl_triggers = []
unctrl_triggers = []


######################################################
################## Helper functions ##################
######################################################


######################################################
######################## MAIN ########################
######################################################

def initDomain():
    robot_name = "robot"
    human_name = "human"
    hatpehda.set_robot_name(robot_name)
    hatpehda.set_human_name(human_name)

    # Initial state
    initial_state = hatpehda.State("init")

    # Static properties
    initial_state.create_static_prop("self_name", "None")
    initial_state.create_static_prop("otherAgent", {robot_name:human_name, human_name:robot_name})
    initial_state.create_static_prop("objects", {"places":["placeA", "placeB", "placeC"]})

    # Dynamic properties
    initial_state.create_dynamic_prop("room", {robot_name:"room1", human_name:"room2"})
    initial_state.create_dynamic_prop("at", {robot_name:"placeC", human_name:"placeC", "coffee":"placeB"})
    initial_state.create_dynamic_prop("carry", {robot_name:[], human_name:[]})

    # Robot
    hatpehda.declare_operators(robot_name, *ctrl_operators)
    hatpehda.declare_operators_ag(robot_name, robot_operator_ag)
    for me in ctrl_methods:
        hatpehda.declare_methods(robot_name, *me)
    hatpehda.declare_triggers(robot_name, *ctrl_triggers)
    hatpehda.set_observable_function("robot", isObs)
    robot_state = deepcopy(initial_state)
    robot_state.self_name = robot_name
    robot_state.__name__ = robot_name + "_init"
    hatpehda.set_state(robot_name, robot_state)

    # Human
    hatpehda.declare_operators(human_name, *unctrl_operators)
    hatpehda.declare_operators_ag(human_name, human_operator_ag)
    for me in unctrl_methods:
        hatpehda.declare_methods(human_name, *me)
    hatpehda.declare_triggers(human_name, *unctrl_triggers)
    hatpehda.set_observable_function("human", isObs)
    human_state = deepcopy(initial_state)
    human_state.self_name = human_name
    human_state.__name__ = human_name + "_init"
    human_state.at["coffee"] = "placeA"
    hatpehda.set_state(human_name, human_state)
    hatpehda.add_tasks(human_name, [("get_coffee",)])

    print("INITIAL STATES")
    hatpehda.print_agent(robot_name)
    hatpehda.print_agent(human_name)

def node_explo(starting_agent):
    robot_name = hatpehda.get_robot_name()
    human_name = hatpehda.get_human_name()

    # hatpehda.set_debug(True)
    # hatpehda.set_compute_gui(True)
    # hatpehda.set_view_gui(True)
    # hatpehda.set_stop_input(True)
    # hatpehda.set_debug_agenda(True)
    # hatpehda.set_stop_input_agenda(True)

    n_plot = 0
    print("Start first exploration")
    first_explo_dur = time.time()
    first_node, Ns, u_flagged_nodes, n_plot = hatpehda.heuristic_exploration(starting_agent, n_plot)
    first_explo_dur = int((time.time() - first_explo_dur)*1000)
    print("\t=> time spent first exploration = {}ms".format(first_explo_dur))
    # gui.show_tree(first_node, "sol", view=True)
    gui.show_all(hatpehda.get_last_nodes_action(first_node), robot_name, human_name, with_begin="false", with_abstract="true")
    # input()

    # hatpehda.set_debug(True)
    # hatpehda.set_compute_gui(True)
    # hatpehda.set_view_gui(True)
    # hatpehda.set_stop_input(True)
    # hatpehda.set_debug_agenda(True)
    # hatpehda.set_stop_input_agenda(True)

    print("Start refining u nodes")
    refine_u_dur = time.time()
    hatpehda.refine_u_nodes(first_node, u_flagged_nodes, n_plot)
    refine_u_dur = int((time.time() - refine_u_dur)*1000)
    print("\t=> time spent refining = {}ms".format(refine_u_dur))
    # gui.show_tree(first_node, "sol", view=True)
    # gui.show_all(hatpehda.get_last_nodes_action(first_node), robot_name, human_name, with_begin="false", with_abstract="true")
    # input()

    print("Total duration = {}ms".format(first_explo_dur+refine_u_dur))

if __name__ == "__main__":

    initDomain()

    node_explo("human")