#!/usr/bin/env python3
import sys
# from HATPEHDA.hatpehda.hatpehda import multi_decomposition
import hatpehda
from copy import deepcopy
from hatpehda import gui
import time
from hatpehda.causal_links_post_treatment import compute_causal_links
import pickle

import cProfile
import pstats

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

# slice #
def SliceCost(agents, state, agent, obj):
    return 1.0
def SlicePrecond(agents, state, agent, obj):
    return state.vegetables_state[obj] == "unsliced"
def SliceDonecond(agents, state, agent, obj):
    return state.vegetables_state[obj] == "sliced"
def SlicePostObsEff(agents, state, agent, obj):
    state.vegetables_state[obj] = "sliced"
sliceAg = hatpehda.OperatorAg("slice", cost=SliceCost, precond=SlicePrecond, donecond=SliceDonecond, post_obs_eff=SlicePostObsEff)

# put_vegetables_in_the_pot #
def PutVegInPotCost(agents, state, agent):
    return 1.0
def PutVegInPotPrecond(agents, state, agent):
    ok = True
    for veg in state.objects["vegetables"]:
        if state.at[veg] == "pot":
            ok = False
            break
    return ok
def PutVegInPotDonecond(agents, state, agent):
    done = True
    for veg in state.objects["vegetables"]:
        if state.at[veg] != "pot":
            done = False
            break
    return done
def PutVegInPotPostObsEff(agents, state, agent):
    for veg in state.objects["vegetables"]:
        state.at[veg] = "pot"
putVegInPotAg = hatpehda.OperatorAg("put_vegetables_in_the_pot", cost=PutVegInPotCost, precond=PutVegInPotPrecond, donecond=PutVegInPotDonecond, post_obs_eff=PutVegInPotPostObsEff)

# salt #
def SaltCost(agents, state, agent):
    cost = 1.0
    if agents[hatpehda.get_robot_name()].state.salted:
        cost = 10.0
    return cost
def SaltInstObsEff(agents, state, agent):
    state.salted = True
saltAg = hatpehda.OperatorAg("salt", cost=SaltCost, inst_obs_eff=SaltInstObsEff)

# turn_on_pot_fire #
def TurnOnPotFireCost(agents, state, agent):
    return 1.0
def TurnOnPotFirePrecond(agents, state, agent):
    return state.pot_fire_on == False
def TurnOnPotFireDonecond(agents, state, agent):
    return state.pot_fire_on == True
def TurnOnPotFirePostObsEff(agents, state, agent):
    state.pot_fire_on = True
turnOnPotFireAg = hatpehda.OperatorAg("turn_on_pot_fire", cost=TurnOnPotFireCost, precond=TurnOnPotFirePrecond, donecond=TurnOnPotFireDonecond, post_obs_eff=TurnOnPotFirePostObsEff)

# slice_meat #
def SliceMeatCost(agents, state, agent):
    return 1.0
def SliceMeatPrecond(agents, state, agent):
    return state.meat_sliced == False
def SliceMeatDonecond(agents, state, agent):
    return state.meat_sliced == True
def SliceMeatPostObsEff(agents, state, agent):
    state.meat_sliced = True
sliceMeatAg = hatpehda.OperatorAg("slice_meat", cost=SliceMeatCost, precond=SliceMeatPrecond, donecond=SliceMeatDonecond, post_obs_eff=SliceMeatPostObsEff)

# place_meat_pan #
def PlaceMeatPanCost(agents, state, agent):
    return 1.0
def PlaceMeatPanPrecond(agents, state, agent):
    return state.at["meat"] != "pan"
def PlaceMeatPanDonecond(agents, state, agent):
    return state.at["meat"] == "pan"
def PlaceMeatPanPostObsEff(agents, state, agent):
    state.at["meat"] = "pan"
placeMeatPanAg = hatpehda.OperatorAg("place_meat_pan", cost=PlaceMeatPanCost, precond=PlaceMeatPanPrecond, donecond=PlaceMeatPanDonecond, post_obs_eff=PlaceMeatPanPostObsEff)

# turn_on_pan_fire #
def TurnOnPanFireCost(agents, state, agent):
    return 1.0
def TurnOnPanFirePrecond(agents, state, agent):
    return state.pan_fire_on == False
def TurnOnPanFireDonecond(agents, state, agent):
    return state.pan_fire_on == True
def TurnOnPanFirePostObsEff(agents, state, agent):
    state.pan_fire_on = True
turnOnPanFireAg = hatpehda.OperatorAg("turn_on_pan_fire", cost=TurnOnPanFireCost, precond=TurnOnPanFirePrecond, donecond=TurnOnPanFireDonecond, post_obs_eff=TurnOnPanFirePostObsEff)

# leave_room #
def LeaveRoomCost(agents, state, agent):
    return 1.0
def LeaveRoomPrecond(agents, state, agent):
    return state.at[agent] == "room"
def LeaveRoomDonecond(agents, state, agent):
    return state.at[agent] == "far"
def LeaveRoomPostObsEff(agents, state, agent):
    state.at[agent] = "far"
leaveRoomAg = hatpehda.OperatorAg("leave_room", cost=LeaveRoomCost, precond=LeaveRoomPrecond, donecond=LeaveRoomDonecond, post_obs_eff=LeaveRoomPostObsEff)

# wait #
def WaitCost(agents, state, agent):
    return 1.0
waitAg = hatpehda.OperatorAg("wait", cost=WaitCost)

# come back #
def ComeBackCost(agents, state, agent):
    return 1.0
def ComeBackPrecond(agents, state, agent):
    return state.at[agent] == "far"
def ComeBackDonecond(agents, state, agent):
    return state.at[agent] == "room"
def ComeBackPostObsEff(agents, state, agent):
    state.at[agent] = "room"
comeBackAg = hatpehda.OperatorAg("come_back", cost=ComeBackCost, precond=ComeBackPrecond, donecond=ComeBackDonecond, post_obs_eff=ComeBackPostObsEff)

# open bottle #
def OpenBottlePostObsEff(agents, state, agent):
    state.bottle_open = True
openBottleAg = hatpehda.OperatorAg("open_bottle", post_obs_eff=OpenBottlePostObsEff)

# fill glass #
def FillGlassPostObsEff(agents, state, agent):
    state.glass_filled = True
fillGlassAg = hatpehda.OperatorAg("fill_glass", post_obs_eff=FillGlassPostObsEff)

# drink #
def DrinkPrecond(agents, state, agent):
    return state.glass_filled
def DrinkPostObsEff(agents, state, agent):
    state.glass_filled = False
drinkAg = hatpehda.OperatorAg("drink", precond=DrinkPrecond, post_obs_eff=DrinkPostObsEff)

robot_operator_ag = [sliceAg, putVegInPotAg, saltAg, turnOnPotFireAg, sliceMeatAg, placeMeatPanAg, turnOnPanFireAg, leaveRoomAg, waitAg, comeBackAg, openBottleAg, fillGlassAg]
human_operator_ag = [sliceAg, putVegInPotAg, saltAg, turnOnPotFireAg, sliceMeatAg, placeMeatPanAg, turnOnPanFireAg, leaveRoomAg, waitAg, comeBackAg, drinkAg]


######################################################
################### Abstract Tasks ###################
######################################################

def dec_cook(agents, self_state, self_name):
    return [("cook_vegetables",), ("following",)]

def dec_R_cook_vegetables(agents, self_state, self_name):
    return [("slice_vegetables",), ("check_veg_in_pot",), ("spice_and_cook",)]

def dec_H_cook_vegetables(agents, self_state, self_name):
    return [("slice_vegetables",), ("check_veg_in_pot",), ("go_away",), ("spice_and_cook",)]

def dec_slice_vegetables(agents, self_state, self_name):
    for veg in self_state.vegetables_state:
        if self_state.vegetables_state[veg] == "unsliced":
            return [("slice", veg), ("slice_vegetables",)]
    return []

def dec_check_veg_in_pot(agents, self_state, self_name):
    if self_state.at[self_state.objects["vegetables"][0]] == "pot":
        return []
    else:
        return [("put_vegetables_in_the_pot",)]

def dec_go_away(agents, self_state, self_name):
    return [("leave_room", ), ("wait",), ("come_back",)]

def dec_spice_and_cook(agents, self_state, self_name):
    return [("check_pot_turned_on",), ("check_salted",)] 

def dec_check_pot_turned_on(agents, self_state, self_name):
    if self_state.pot_fire_on == True:
        return []
    else:
        return [("turn_on_pot_fire",)]

def dec_check_salted(agents, self_state, self_name):
    if self_state.salted == True:
        return []
    else:
        return [("salt",)]

def dec_cook_meat(agents, self_state, self_name):
    # return [("check_slice_meat",), ("check_place_meat_pan",), ("check_pan_turned_on",)]
    return [("check_place_meat_pan",), ("check_pan_turned_on",)]

def dec_check_slice_meat(agents, self_state, self_name):
    if self_state.meat_sliced == True:
        return []
    else:
        return [("slice_meat",)]

def dec_check_place_meat_pan(agents, self_state, self_name):
    if self_state.at["meat"] == "pan":
        return []
    else:
        return [("place_meat_pan",)]

def dec_check_pan_turned_on(agents, self_state, self_name):
    if self_state.pan_fire_on == True:
        return []
    else:
        return [("turn_on_pan_fire",)]

def dec_following_meat(agents, self_stte, self_name):
    return [("cook_meat",)]

def dec_following_drinks(agents, self_state, self_name):
    return [("prepare_drinks",)]

def dec_prepare_drinks(agents, self_state, self_name):
    return [("open_bottle",), ("fill_glass",)]

common_methods = [
            ("cook", dec_cook),
            ("slice_vegetables", dec_slice_vegetables),
            ("check_veg_in_pot", dec_check_veg_in_pot),
            ("go_away", dec_go_away),
            ("spice_and_cook", dec_spice_and_cook),
            ("check_pot_turned_on", dec_check_pot_turned_on),
            ("check_salted", dec_check_salted),
            ("cook_meat", dec_cook_meat),
            ("check_slice_meat", dec_check_slice_meat),
            ("check_place_meat_pan", dec_check_place_meat_pan),
            ("check_pan_turned_on", dec_check_pan_turned_on),        
]
ctrl_methods = common_methods + [
            ("cook_vegetables", dec_R_cook_vegetables),
            ("following", dec_following_meat, dec_following_drinks),
            ("prepare_drinks", dec_prepare_drinks),
]
unctrl_methods = common_methods + [
            ("cook_vegetables", dec_H_cook_vegetables),
            ("following", dec_following_meat),
]


######################################################
###################### Triggers ######################
######################################################

def t_glass_filled(agents, self_state, self_name):
    if agents[self_name].state.glass_filled:
        return [("drink",)]
    return False

ctrl_triggers = []
unctrl_triggers = [t_glass_filled]


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
    initial_state.create_static_prop("objects", {"vegetables":["carrot", "leek", "cabbage", "turnip"]})

    # Dynamic properties
    initial_state.create_dynamic_prop("at", {robot_name:"room", human_name:"room", "meat":"table"})
    initial_state.create_dynamic_prop("vegetables_state", {})
    for veg in initial_state.objects["vegetables"]:
        initial_state.vegetables_state[veg] = "unsliced"
        initial_state.at[veg] = "table"
    initial_state.create_dynamic_prop("last_check_away", False)
    initial_state.create_dynamic_prop("meat_sliced", False)
    initial_state.create_dynamic_prop("pot_fire_on", False)
    initial_state.create_dynamic_prop("pan_fire_on", False)
    initial_state.create_dynamic_prop("salted", False)
    initial_state.create_dynamic_prop("bottle_open", False)
    initial_state.create_dynamic_prop("glass_filled", False)

    # Robot
    hatpehda.declare_operators_ag(robot_name, robot_operator_ag)
    for me in ctrl_methods:
        hatpehda.declare_methods(robot_name, *me)
    hatpehda.declare_triggers(robot_name, *ctrl_triggers)
    hatpehda.set_observable_function("robot", isObs)
    robot_state = deepcopy(initial_state)
    robot_state.self_name = robot_name
    robot_state.__name__ = robot_name + "_init"
    hatpehda.set_state(robot_name, robot_state)
    hatpehda.add_tasks(robot_name, [("cook",)])

    # Human
    hatpehda.declare_operators_ag(human_name, human_operator_ag)
    for me in unctrl_methods:
        hatpehda.declare_methods(human_name, *me)
    hatpehda.declare_triggers(human_name, *unctrl_triggers)
    hatpehda.set_observable_function("human", isObs)
    human_state = deepcopy(initial_state)
    human_state.self_name = human_name
    human_state.__name__ = human_name + "_init"
    hatpehda.set_state(human_name, human_state)
    hatpehda.add_tasks(human_name, [("cook",)])

    print("INITIAL STATES")
    hatpehda.print_agent(robot_name)
    hatpehda.print_agent(human_name)

def node_explo():
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

    pr = cProfile.Profile()
    pr.enable()

    # hatpehda.test_copy()

    first_node, Ns, u_flagged_nodes, n_plot = hatpehda.heuristic_exploration(robot_name, n_plot)
    first_explo_dur = int((time.time() - first_explo_dur)*1000)
    print("\t=> time spent first exploration = {}ms".format(first_explo_dur))
    
    pr.disable()
    stats = pstats.Stats(pr).sort_stats("tottime")
    stats.dump_stats(filename="profiling.prof")

    # gui.show_tree(first_node, "sol", view=True)
    # gui.show_all(hatpehda.get_last_nodes_action(first_node), robot_name, human_name, with_begin="false", with_abstract="true")

    # exit(0)

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
    input()

    print("Total duration = {}ms".format(first_explo_dur+refine_u_dur))

if __name__ == "__main__":

    initDomain()

    # hatpehda.exploreAg(hatpehda.get_human_name())
    node_explo()