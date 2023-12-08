#!/usr/bin/env python3
import sys
# from HATPEHDA.hatpehda.hatpehda import multi_decomposition
import hatpehda
from copy import deepcopy
from hatpehda import gui
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
    return state.at[agent_a] == state.at[agent_b]

######################################################
################### Primitive tasks ##################
######################################################

# go_to_breaker #
def GoToBreakerDone(agents, state, agent):
    return state.at[agent]=="breaker"
def GoToBreakerPostObsEff(agents, state_in, state_out, agent):
    state_out.at[agent]="breaker"
GoToBreakerAg = hatpehda.OperatorAg("go_to_breaker", donecond=GoToBreakerDone, post_obs_eff=GoToBreakerPostObsEff)
    
# come_back #
def ComeBackDone(agents, state, agent):
    return state.at[agent]=="room"
def ComeBackPostObsEff(agents, state_in, state_out, agent):
    state_out.at[agent]="room"
ComeBackAg = hatpehda.OperatorAg("come_back", donecond=ComeBackDone, post_obs_eff=ComeBackPostObsEff)

# switch_off_power #
def SwitchOffPowerPrecond(agents, state, agent):
    return state.at[agent]=="breaker"
def SwitchOffPowerDonecond(agents, state, agent):
    return state.power_on==False
def SwitchOffPowerPostObsEff(agents, state_in, state_out, agent):
    state_out.power_on=False
SwitchOffPowerAg = hatpehda.OperatorAg("switch_off_power", precond=SwitchOffPowerPrecond, donecond=SwitchOffPowerDonecond, post_obs_eff=SwitchOffPowerPostObsEff)

# switch_on_power #
def SwitchOnPowerPrecond(agents, state, agent):
    return state.at[agent]=="breaker"
def SwitchOnPowerDonecond(agents, state, agent):
    return state.power_on==True
def SwitchOnPowerPostObsEff(agents, state_in, state_out, agent):
    state_out.power_on=True
SwitchOnPowerAg = hatpehda.OperatorAg("switch_on_power", precond=SwitchOnPowerPrecond, donecond=SwitchOnPowerDonecond, post_obs_eff=SwitchOnPowerPostObsEff)

# remove_lightbulb #
def RemoveLightbulbPrecond(agents, state, agent):
    return state.old_lightbulb_placed==True and state.power_on==False
def RemoveLightbulbDonecond(agents, state, agent):
    return state.old_lightbulb_placed==False
def RemoveLightbulbPostObsEff(agents, state_in, state_out, agent):
    state_out.old_lightbulb_placed=False
RemoveLightbulbAg = hatpehda.OperatorAg("remove_lightbulb", precond=RemoveLightbulbPrecond, donecond=RemoveLightbulbDonecond, post_obs_eff=RemoveLightbulbPostObsEff)

# place_new_lightbulb #
def PlaceNewLightbulbPrecond(agents, state, agent):
    return state.old_lightbulb_placed==False and state.new_lightbulb_placed==False and state.power_on==False
def PlaceNewLightbulbDonecond(agents, state, agent):
    return state.new_lightbulb_placed==True
def PlaceNewLightbulbPostObsEff(agents, state_in, state_out, agent):
    state_out.new_lightbulb_placed=True
PlaceNewLightbulbAg = hatpehda.OperatorAg("place_new_lightbulb", precond=PlaceNewLightbulbPrecond, donecond=PlaceNewLightbulbDonecond, post_obs_eff=PlaceNewLightbulbPostObsEff)

# check_proper_functionning #
def CheckProperFunctionningPrecond(agents, state, agent):
    return state.proper_functionning_checked==False and state.new_lightbulb_placed==True and state.power_on==True
def CheckProperFunctionningDonecond(agents, state, agent):
    return state.proper_functionning_checked==True
def CheckProperFunctionningPostObsEff(agents, state_in, state_out, agent):
    state_out.proper_functionning_checked=True
CheckProperFunctionningAg = hatpehda.OperatorAg("check_proper_functionning", precond=CheckProperFunctionningPrecond, donecond=CheckProperFunctionningDonecond, post_obs_eff=CheckProperFunctionningPostObsEff)

def MeanwhilePostObsEff(agents, state_in, state_out, agent):
    state_out.meanwhile_prop = True
MeanwhileAg = hatpehda.OperatorAg("meanwhile", post_obs_eff=MeanwhilePostObsEff)

common_ag = []
robot_operator_ag = common_ag + [RemoveLightbulbAg, PlaceNewLightbulbAg, CheckProperFunctionningAg, MeanwhileAg]
human_operator_ag = common_ag +  [GoToBreakerAg, ComeBackAg, SwitchOffPowerAg, SwitchOnPowerAg]


######################################################
################### Abstract Tasks ###################
######################################################

def dec_human_power(agents, self_state, self_name):
    return [("make_power_off",), ("make_power_on",)]

def dec_robot_lightbulb(agents, self_state, self_name):
    return [("meanwhile",), ("remove_lightbulb",), ("place_new_lightbulb",), ("check_proper_functionning",)]

def dec_make_power_off(agents, self_state, self_name):
    return [("go_to_breaker",), ("switch_off_power",), ("come_back",)]

def dec_make_power_on(agents, self_state, self_name):
    if self_state.new_lightbulb_placed:
        return [("go_to_breaker",), ("switch_on_power",), ("come_back",)]
    return False

common_methods = [
]
ctrl_methods = common_methods + [
            ("change_lightbulb", dec_robot_lightbulb),
]
unctrl_methods = common_methods + [
            ("change_lightbulb", dec_human_power),
            ("make_power_off", dec_make_power_off),
            ("make_power_on", dec_make_power_on),
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

######################################################
######################## MAIN ########################
######################################################

def initDomain():
    robot_name = "robot"
    human_name = "human"
    hatpehda.set_robot_name(robot_name)
    hatpehda.set_human_name(human_name)
    hatpehda.init_other_agent_name()

    # Initial state
    initial_state = hatpehda.State("init")

    # Static properties
    initial_state.create_static_prop("self_name", None)
    initial_state.create_static_prop("other_agent_name", {robot_name:human_name, human_name:robot_name}) 

    # Dynamic properties
    initial_state.create_dynamic_prop("at", {robot_name:"room", human_name:"room"})
    initial_state.create_dynamic_prop("power_on", True)
    initial_state.create_dynamic_prop("old_lightbulb_placed", True)
    initial_state.create_dynamic_prop("new_lightbulb_placed", False)
    initial_state.create_dynamic_prop("proper_functionning_checked", False)
    initial_state.create_dynamic_prop("meanwhile_prop", False)

    # Robot
    hatpehda.declare_operators_ag(robot_name, robot_operator_ag)
    for me in ctrl_methods:
        hatpehda.declare_methods(robot_name, *me)
    hatpehda.declare_triggers(robot_name, *robot_triggers)
    hatpehda.set_observable_function("robot", isObs)
    robot_state = deepcopy(initial_state)
    robot_state.self_name = robot_name
    robot_state.__name__ = robot_name + "_init"
    hatpehda.set_state(robot_name, robot_state)
    hatpehda.add_tasks(robot_name, [("change_lightbulb",)])

    # Human
    hatpehda.declare_operators_ag(human_name, human_operator_ag)
    for me in unctrl_methods:
        hatpehda.declare_methods(human_name, *me)
    hatpehda.declare_triggers(human_name, *human_triggers)
    hatpehda.set_observable_function("human", isObs)
    human_state = deepcopy(initial_state)
    human_state.self_name = human_name
    human_state.__name__ = human_name + "_init"
    hatpehda.set_state(human_name, human_state)
    hatpehda.add_tasks(human_name, [("change_lightbulb",)])
    
    # Starting Agent
    hatpehda.set_starting_agent(human_name)
    # hatpehda.set_starting_agent(robot_name)

def node_explo():
    robot_name = hatpehda.get_robot_name()
    human_name = hatpehda.get_human_name()

    print("INITIAL STATES")
    hatpehda.print_agent(robot_name, with_static=True)
    hatpehda.print_agent(human_name, with_static=True)

    hatpehda.set_debug(True)
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
    # gui.show_tree(first_node, "sol", view=True)
    # gui.show_all(hatpehda.get_last_nodes_action(first_node), robot_name, human_name, with_begin="false", with_abstract="true")
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
    gui.show_all(hatpehda.get_last_nodes_action(first_node), robot_name, human_name, with_begin="false", with_abstract="true")
    gui.show_tree(first_node, "sol", view=True)
    print("Total duration = {}ms".format(first_explo_dur+refine_u_dur))
    input()

if __name__ == "__main__":

    initDomain()

    node_explo()