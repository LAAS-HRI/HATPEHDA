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

P1Ag= hatpehda.OperatorAg("P1")

P2Ag= hatpehda.OperatorAg("P2")

P3Ag= hatpehda.OperatorAg("P3")

P4Ag= hatpehda.OperatorAg("P4")

P5Ag= hatpehda.OperatorAg("P5")

P6Ag= hatpehda.OperatorAg("P6")

P7Ag= hatpehda.OperatorAg("P7")

common_operators = []
ctrl_operators = common_operators + []
unctrl_operators = common_operators + []

common_operator_ag = [P1Ag, P2Ag, P3Ag, P4Ag, P5Ag, P6Ag, P7Ag]
robot_operator_ag = common_operator_ag + []
human_operator_ag = common_operator_ag + []


######################################################
################### Abstract Tasks ###################
######################################################

def dec_ab1_1(agents, self_state, self_name):
    return [("Ab2",)]

def dec_ab1_2(agents, self_state, self_name):
    return [("Ab3",)]

def dec_ab1_3(agents, self_state, self_name):
    return [("Ab4",)]

def dec_ab2(agents, self_state, self_name):
    if not self_state.prop==True:
        return False
    return [("P2",)]

def dec_ab3(agents, self_state, self_name):
    return [("P1",)]

def dec_ab4(agents, self_state, self_name):
    return []

def dec_ab5(agents, self_state, self_name):
    return []

def dec_ab6_1(agents, self_state, self_name):
    return [("Ab7",)]

def dec_ab6_2(agents, self_state, self_name):
    return [("Ab8",)]

def dec_ab7(agents, self_state, self_name):
    return [("P3",)]

def dec_ab8(agents, self_state, self_name):
    return [("P4",), ("Ab9",)]

def dec_ab9(agents, self_state, self_name):
    return [("P7",)]

common_methods = [
            ("Ab1", dec_ab1_1, dec_ab1_2, dec_ab1_3),
            ("Ab2", dec_ab2),
            ("Ab3", dec_ab3),
            ("Ab4", dec_ab4),
            ("Ab5", dec_ab5),
            ("Ab6", dec_ab6_1, dec_ab6_2),
            ("Ab7", dec_ab7),
            ("Ab8", dec_ab8),
            ("Ab9", dec_ab9),
]
ctrl_methods = common_methods + []
unctrl_methods = common_methods + []


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
"""
     	     Ab1
            / | \
           /  |  \
          P1 Ab2 Ab3
           // | \   \
          //  |  \   \
         Ab6 Ab4 Ab5 P5
       // |   | \   \
      //  |   |  \   \
     Ab7 Ab8  P1  P2  P6
      |   | \
      |   |  \
     P3  P4  Ab9
              |
	          |
             P7

[ [P1 P1 P2 P6 P5] [P1 P3 P5] [P1 P4 P7 P5] ]
"""

def initDomain():
    robot_name = "robot"
    human_name = "human"
    hatpehda.set_robot_name(robot_name)
    hatpehda.set_human_name(human_name)

    # Initial state
    initial_state = hatpehda.State("init")

    # Static properties
    initial_state.create_static_prop("self_name", "None")
    initial_state.create_static_prop("other_agent_name", {robot_name:human_name, human_name:robot_name})

    # Dynamic properties
    initial_state.create_dynamic_prop("useless_prop1", "a")
    initial_state.create_dynamic_prop("useless_prop2", "a")
    initial_state.create_dynamic_prop("prop", False)
    initial_state.create_dynamic_prop("room", {robot_name:"room1", human_name:"room1"})

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
    hatpehda.add_tasks(robot_name, [("Ab5",), ("Ab1",)])

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
    human_state.prop = True
    human_state.useless_prop1 = "b"
    human_state.useless_prop2 = "c"
    hatpehda.set_state(human_name, human_state)

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
    first_node, Ns, u_flagged_nodes, n_plot = hatpehda.heuristic_exploration(n_plot)
    first_explo_dur = int((time.time() - first_explo_dur)*1000)
    print("\t=> time spent first exploration = {}ms".format(first_explo_dur))
    gui.show_tree(first_node, "sol", view=True)
    gui.show_all(hatpehda.get_last_nodes_action(first_node), robot_name, human_name, with_begin="false", with_abstract="true")
    input()

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