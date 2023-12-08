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

# slice #
def SlicePrecond(agents, state, agent, obj):
    return state.vegetables_state[obj] == "unsliced"
def SliceDonecond(agents, state, agent, obj):
    return state.vegetables_state[obj] == "sliced"
def SlicePostObsEff(agents, state_in, state_out, agent, obj):
    state_out.vegetables_state[obj] = "sliced"
sliceAg = hatpehda.OperatorAg("slice", precond=SlicePrecond, donecond=SliceDonecond, post_obs_eff=SlicePostObsEff)

# put_vegetables_in_the_pot #
def PutVegInPotPrecond(agents, state, agent):
    for veg in state.objects["vegetables"]:
        if state.at[veg] == "pot":
            return False
    return True
def PutVegInPotDonecond(agents, state, agent):
    for veg in state.objects["vegetables"]:
        if state.at[veg] != "pot":
            return False
    return True
def PutVegInPotPostObsEff(agents, state_in, state_out, agent):
    for veg in state_in.objects["vegetables"]:
        state_out.at[veg] = "pot"
putVegInPotAg = hatpehda.OperatorAg("put_vegetables_in_the_pot", precond=PutVegInPotPrecond, donecond=PutVegInPotDonecond, post_obs_eff=PutVegInPotPostObsEff)

# salt #
def SaltCost(agents, state, agent):
    cost = 1.0
    return cost
def SaltDonecond(agents, state, agent):
    return state.salted == True
def SaltInstObsEff(agents, state_in, state_out, agent):
    state_out.salted = True
saltAg = hatpehda.OperatorAg("salt", cost=SaltCost, donecond=SaltDonecond, inst_obs_eff=SaltInstObsEff)

# turn_on_pot_fire #
def TurnOnPotFirePrecond(agents, state, agent):
    return state.pot_fire_on == False
def TurnOnPotFireDonecond(agents, state, agent):
    return state.pot_fire_on == True
def TurnOnPotFirePostObsEff(agents, state_in, state_out, agent):
    state_out.pot_fire_on = True
    state_out.hot["pot"] = True
turnOnPotFireAg = hatpehda.OperatorAg("turn_on_pot_fire", precond=TurnOnPotFirePrecond, donecond=TurnOnPotFireDonecond, post_obs_eff=TurnOnPotFirePostObsEff)

# slice_meat #
def SliceMeatPrecond(agents, state, agent):
    return state.meat_sliced == False
def SliceMeatDonecond(agents, state, agent):
    return state.meat_sliced == True
def SliceMeatPostObsEff(agents, state_in, state_out, agent):
    state_out.meat_sliced = True
sliceMeatAg = hatpehda.OperatorAg("slice_meat", precond=SliceMeatPrecond, donecond=SliceMeatDonecond, post_obs_eff=SliceMeatPostObsEff)

# place_meat_pan #
def PlaceMeatPanPrecond(agents, state, agent):
    return state.at["meat"] != "pan" and state.meat_bag_open==True
def PlaceMeatPanDonecond(agents, state, agent):
    return state.at["meat"] == "pan"
def PlaceMeatPanPostObsEff(agents, state_in, state_out, agent):
    state_out.at["meat"] = "pan"
placeMeatPanAg = hatpehda.OperatorAg("place_meat_pan", precond=PlaceMeatPanPrecond, donecond=PlaceMeatPanDonecond, post_obs_eff=PlaceMeatPanPostObsEff)

# turn_on_pan_fire #
def TurnOnPanFirePrecond(agents, state, agent):
    return state.pan_fire_on == False
def TurnOnPanFireDonecond(agents, state, agent):
    return state.pan_fire_on == True
def TurnOnPanFirePostObsEff(agents, state_in, state_out, agent):
    state_out.pan_fire_on = True
    state_out.hot["pan"] = True
turnOnPanFireAg = hatpehda.OperatorAg("turn_on_pan_fire", precond=TurnOnPanFirePrecond, donecond=TurnOnPanFireDonecond, post_obs_eff=TurnOnPanFirePostObsEff)

# leave_room #
def LeaveRoomPrecond(agents, state, agent):
    return state.at[agent] == "room"
def LeaveRoomDonecond(agents, state, agent):
    return state.at[agent] == "far"
def LeaveRoomPostObsEff(agents, state_in, state_out, agent):
    state_out.at[agent] = "far"
leaveRoomAg = hatpehda.OperatorAg("leave_room", precond=LeaveRoomPrecond, donecond=LeaveRoomDonecond, post_obs_eff=LeaveRoomPostObsEff)

# do_stuff_far #
def doStuffFarPrecond(agents, state, agent):
    return state.at[agent] == "far"
def doStuffFarPostObsEff(agents, state_in, state_out, agent):
    state_out.stuff_done_far = True
doStuffFarAg = hatpehda.OperatorAg("do_stuff_far", precond=doStuffFarPrecond, post_obs_eff=doStuffFarPostObsEff)

# wait #
waitAg = hatpehda.OperatorAg("wait")

# pouet #
pouetAg = hatpehda.OperatorAg("pouet")

# aie #
aieAg = hatpehda.OperatorAg("aie")

# come back #
def ComeBackPrecond(agents, state, agent):
    return state.at[agent] == "far"
def ComeBackDonecond(agents, state, agent):
    return state.at[agent] == "room"
def ComeBackPostObsEff(agents, state_in, state_out, agent):
    state_out.at[agent] = "room"
comeBackAg = hatpehda.OperatorAg("come_back", precond=ComeBackPrecond, donecond=ComeBackDonecond, post_obs_eff=ComeBackPostObsEff)

# open bottle #
def OpenBottleDonecond(agents, state, agent):
    return state.bottle_open == True
def OpenBottlePostObsEff(agents, state_in, state_out, agent):
    state_out.bottle_open = True
openBottleAg = hatpehda.OperatorAg("open_bottle", donecond=OpenBottleDonecond, post_obs_eff=OpenBottlePostObsEff)

# fill glass #
def FillGlassDonecond(agents, state, agent):
    return state.glass_filled == True
def FillGlassPostObsEff(agents, state_in, state_out, agent):
    state_out.glass_filled = True
fillGlassAg = hatpehda.OperatorAg("fill_glass", donecond=FillGlassDonecond, post_obs_eff=FillGlassPostObsEff)

# drink #
def DrinkPrecond(agents, state, agent):
    return state.glass_filled
def DrinkPostObsEff(agents, state_in, state_out, agent):
    state_out.glass_filled = False
drinkAg = hatpehda.OperatorAg("drink", precond=DrinkPrecond, post_obs_eff=DrinkPostObsEff)

# grab_pan_A #
def grabPanACost(agents, state, agent):
    return 5.0
def grabPanAPrecond(agents, state, agent):
    return state.holding[agent] == None and state.at["pan"] in state.objects["storage"]["cupboardA"]
def grabPanADonecond(agents, state, agent):
    return state.holding[agent] == "pan"
def grabPanAPostObsEff(agents, state_in, state_out, agent):
    if state_in.holding[agent]!="potholder" and state_in.hot["pan"]:
        state_out.human_got_burned = True
    state_out.holding[agent] = "pan"
    state_out.at["pan"] = agent
grabPanAAg = hatpehda.OperatorAg("grab_pan_A", cost=grabPanACost, precond=grabPanAPrecond, donecond=grabPanADonecond, post_obs_eff=grabPanAPostObsEff)

# grab_pan_B #
def grabPanBPrecond(agents, state, agent):
    return state.holding[agent] == None and state.at["pan"] in state.objects["storage"]["cupboardB"]
def grabPanBDonecond(agents, state, agent):
    return state.holding[agent] == "pan"
def grabPanBPostObsEff(agents, state_in, state_out, agent):
    if state_in.holding[agent]!="potholder" and state_in.hot["pan"]:
        state_out.human_got_burned = True
    state_out.holding[agent] = "pan"
    state_out.at["pan"] = agent
grabPanBAg = hatpehda.OperatorAg("grab_pan_B", precond=grabPanBPrecond, donecond=grabPanBDonecond, post_obs_eff=grabPanBPostObsEff)

# place_pan #
def placePanPrecond(agents, state, agent):
    return state.holding[agent] == "pan" and state.at["pot"] != "hotplate"
def placePanDonecond(agents, state, agent):
    return state.holding[agent] == None and state.at["pot"] == "hotplate"
def placePanPostObsEff(agents, state_in, state_out, agent):
    state_out.holding[agent] = None
    state_out.at["pan"] = "hotplate"
placePanAg = hatpehda.OperatorAg("place_pan", precond=placePanPrecond, post_obs_eff=placePanPostObsEff)

# grab_potholder #
def grabPotholderPrecond(agents, state, agent):
    return state.holding[agent] == None
def grabPotholderDonecond(agents, state, agent):
    return state.holding[agent] == "potholder"
def grabPotholderPostObsEff(agents, state_in, state_out, agent):
    state_out.holding[agent] = "potholder"
grabPotholderAg = hatpehda.OperatorAg("grab_potholder", precond=grabPotholderPrecond, donecond=grabPotholderDonecond, post_obs_eff=grabPotholderPostObsEff)

# remove_pot #
def removePotPrecond(agents, state, agent):
    return state.at["pot"] == "hotplate"
def removePotDonecond(agents, state, agent):
    return state.at["pot"] != "hotplate"
def removePotPostObsEff(agents, state_in, state_out, agent):
    if agent!="robot" and state_in.hot["pot"]==True and state_in.holding[agent]!="potholder":
        state_out.human_got_burned = True
        state_out.hot["pot"] = True
    state_out.at["pot"] = "table"
    state_out.holding[agent] = None
removePotAg = hatpehda.OperatorAg("remove_pot", precond=removePotPrecond, donecond=removePotDonecond, post_obs_eff=removePotPostObsEff)

# grab_scissors_d1 #
def grabScirssorsD1Cost(agents, state, agent, obj):
    return 2.0
def grabScissorsD1Precond(agents, state, agent, obj):
    return state.at[obj]=="drawer1"
def grabScissorsD1Donecond(agents, state, agent, obj):
    return state.holding[agent]==obj or state.holding[state.other_agent_name[agent]]==obj
def grabScissorsD1PostObsEff(agents, state_in, state_out, agent, obj):
    state_out.holding[agent]=obj
    state_out.at[obj]=agent
grabScissorsD1Ag = hatpehda.OperatorAg("grab_scissors_d1", cost=grabScirssorsD1Cost, precond=grabScissorsD1Precond, donecond=grabScissorsD1Donecond, post_obs_eff=grabScissorsD1PostObsEff)

# grab_scissors_d3 #
def grabScissorsD3Cost(agents, state, agent, obj):
    return 10.0
def grabScissorsD3Precond(agents, state, agent, obj):
    return state.at[obj]=="drawer3"
def grabScissorsD3Donecond(agents, state, agent, obj):
    return state.holding[agent]==obj or state.holding[state.other_agent_name[agent]]==obj
def grabScissorsD3PostObsEff(agents, state_in, state_out, agent, obj):
    state_out.holding[agent]=obj
    state_out.at[obj]=agent
grabScissorsD3Ag = hatpehda.OperatorAg("grab_scissors_d3", cost=grabScissorsD3Cost, precond=grabScissorsD3Precond, donecond=grabScissorsD3Donecond, post_obs_eff=grabScissorsD3PostObsEff)

# grab_scissors_d4 #
def grabScissorsD4Cost(agents, state, agent, obj):
    return 10.0
def grabScissorsD4Precond(agents, state, agent, obj):
    return state.at[obj]=="drawer4"
def grabScissorsD4Donecond(agents, state, agent, obj):
    return state.holding[agent]==obj or state.holding[state.other_agent_name[agent]]==obj
def grabScissorsD4PostObsEff(agents, state_in, state_out, agent, obj):
    state_out.holding[agent]=obj
    state_out.at[obj]=agent
grabScissorsD4Ag = hatpehda.OperatorAg("grab_scissors_d4", cost=grabScissorsD4Cost, precond=grabScissorsD4Precond, donecond=grabScissorsD4Donecond, post_obs_eff=grabScissorsD4PostObsEff)

# grab_knife #
def grabKinfeCost(agents, state, agent):
    return 2.0
def grabKnifePrecond(agents, state, agent):
    return state.at["knife1"]=="drawer2"
def grabKnifeDonecond(agents, state, agent):
    return state.holding[agent]=="knife1" or state.holding[state.other_agent_name[agent]]=="knife1"
def grabKnifePostObsEff(agents, state_in, state_out, agent):
    state_out.holding[agent]="knife1"
    state_out.at["knife1"]=agent
grabKnifeAg = hatpehda.OperatorAg("grab_knife", cost=grabKinfeCost, precond=grabKnifePrecond, donecond=grabKnifeDonecond, post_obs_eff=grabKnifePostObsEff)

# cut_bag_scissors #
def cutBagScissorsCost(agents, state, agent):
    return 1.0
def cutBagScissorsPrecond(agents, state, agent):
    return state.meat_bag_open==False and state.holding[agent] in state.objects["scissors"]
def cutBagScissorsDonecond(agents, state, agent):
    return state.meat_bag_open
def cutBagScissorsPostObsEff(agents, state_in, state_out, agent):
    state_out.meat_bag_open=True
cutBagScissorsAg = hatpehda.OperatorAg("cut_bag_scissors", cost=cutBagScissorsCost, precond=cutBagScissorsPrecond, donecond=cutBagScissorsDonecond, post_obs_eff=cutBagScissorsPostObsEff)

# cut_bag_knife #
def cutBagKnifeCost(agents, state, agent):
    return 4.0
def cutBagKnifePrecond(agents, state, agent):
    return state.meat_bag_open==False and state.holding[agent] in state.objects["knife"]
def cutBagKnifeDonecond(agents, state, agent):
    return state.meat_bag_open
def cutBagKnifePostObsEff(agents, state_in, state_out, agent):
    state_out.meat_bag_open=True
cutBagKnifeAg = hatpehda.OperatorAg("cut_bag_knife", cost=cutBagKnifeCost, precond=cutBagKnifePrecond, donecond=cutBagKnifeDonecond, post_obs_eff=cutBagKnifePostObsEff)

# drop_scissors #
def dropScissorsPrecond(agents, state, agent):
    return state.holding[agent] in state.objects["scissors"]
def dropScissorsDonecond(agents, state, agent):
    return state.holding[agent]==None
def dropScissorsPostObsEff(agents, state_in, state_out, agent):
    state_out.at[state_out.holding[agent]]="table"
    state_out.holding[agent]=None
dropScissorsAg = hatpehda.OperatorAg("drop_scissors", precond=dropScissorsPrecond, donecond=dropScissorsDonecond, post_obs_eff=dropScissorsPostObsEff)

# drop_knife #
def dropKnifePrecond(agents, state, agent):
    return state.holding[agent] in state.objects["knife"]
def dropKnifeDonecond(agents, state, agent):
    return state.holding[agent]==None
def dropKnifePostObsEff(agents, state_in, state_out, agent):
    state_out.at[state_out.holding[agent]]="table"
    state_out.holding[agent]=None
dropKnifeAg = hatpehda.OperatorAg("drop_knife", precond=dropKnifePrecond, donecond=dropKnifeDonecond, post_obs_eff=dropKnifePostObsEff)

common_ag = [sliceAg, putVegInPotAg, saltAg, turnOnPotFireAg, sliceMeatAg, placeMeatPanAg, turnOnPanFireAg, leaveRoomAg, waitAg, comeBackAg, grabPanAAg, grabPanBAg, placePanAg, grabPotholderAg, removePotAg, openBottleAg, fillGlassAg, pouetAg, grabScissorsD1Ag, grabScissorsD3Ag, grabScissorsD4Ag, grabKnifeAg, cutBagScissorsAg, cutBagKnifeAg, dropScissorsAg, dropKnifeAg, doStuffFarAg]
robot_operator_ag = common_ag
human_operator_ag = common_ag +  [drinkAg, aieAg]


######################################################
################### Abstract Tasks ###################
######################################################

def dec_cook(agents, self_state, self_name):
    return [("cook_vegetables",), ("following",)]

def dec_R_cook_vegetables(agents, self_state, self_name):
    return [("slice_vegetables",), ("put_vegetables_in_the_pot",), ("spice_and_cook",)]

def dec_H_cook_vegetables(agents, self_state, self_name):
    return [("slice_vegetables",), ("put_vegetables_in_the_pot",), ("go_away",), ("spice_and_cook",)]

def dec_slice_vegetables(agents, self_state, self_name):
    list_to_be_sliced = []
    for veg in self_state.vegetables_state:
        list_to_be_sliced.append(("slice", veg))
    return list_to_be_sliced

def dec_go_away(agents, self_state, self_name):
    if self_state.at[self_name]=="room":
        return [("leave_room", ), ("do_stuff_far",), ("come_back",)]
    return []

def dec_spice_and_cook(agents, self_state, self_name):
    return [("turn_on_pot_fire",), ("salt",)] 

def dec_cook_meat(agents, self_state, self_name):
    if self_state.at["pan"]!="hotplate":
        return False
    if self_state.at["meat"]=="pan" and self_state.pan_fire_on==True:
        return []
    return [("turn_on_pan_fire",), ("check_open_meat_bag",), ("place_meat_pan",)]

def dec_setup_pan(agents, self_state, self_name):
    if self_state.at["pan"] == "hotplate":
        return []
    # return [("clear_spot",), ("grab_pan",), ("place_pan",)]
    return [("remove_pot",), ("get_pan",), ("place_pan",)]

def dec_clear_without(agents, self_state, self_name):
    if self_state.hot["pot"]==False:
        return [("remove_pot",)]
    return False

def dec_clear_with(agents, self_state, self_name):
    if self_state.hot["pot"]==True:
        return [("grab_potholder",), ("remove_pot",)]
    return False

def dec_clear(agents, self_state, self_name):
    return [("remove_pot",)]

def dec_prepare_meat(agents, self_state, self_name):
    if otherAlreadySettingUpPan(agents, self_state, self_name):
            return [("cook_meat",)]
    return [("setup_pan",), ("cook_meat",)]

def dec_get_pan_A(agents, self_state, self_name):
    if self_state.at["pan"] in self_state.objects["storage"]["cupboardA"]:
        return [("grab_pan_A",)]
    return False
    
def dec_get_pan_B(agents, self_state, self_name):
    if not self_state.at["pan"] in self_state.objects["storage"]["cupboardA"]:
        return [("grab_pan_B",)]
    return False

def dec_prepare_drinks(agents, self_state, self_name):
    return [("open_bottle",), ("fill_glass",)]

def dec_open_meat_bag_scissors(agents, self_state, self_name):
    return [("get_scissors",), ("cut_bag_scissors",), ("drop_scissors",)]

def dec_get_scissors_d1(agents, self_state, self_name):
    if self_state.at["scissors1"]=="drawer1":
        return [("grab_scissors_d1", "scissors1")]
    if self_state.at["scissors2"]=="drawer1":
        return [("grab_scissors_d1", "scissors2")]
    return False

def dec_get_scissors_d3(agents, self_state, self_name):
    if not(self_state.at["scissors1"]=="drawer1" or self_state.at["scissors2"]=="drawer1"):
        if self_state.at["scissors1"]=="drawer3":
            return [("grab_scissors_d3", "scissors1")]
        elif self_state.at["scissors2"]=="drawer3":
            return [("grab_scissors_d3", "scissors2")]
    return False

def dec_get_scissors_d4(agents, self_state, self_name):
    if not(self_state.at["scissors1"]=="drawer1" or self_state.at["scissors2"]=="drawer1"):
        if not(self_state.at["scissors1"]=="drawer3" or self_state.at["scissors2"]=="drawer3"):
            if self_state.at["scissors1"]=="drawer4":
                return [("grab_scissors_d4", "scissors1")]
            elif self_state.at["scissors2"]=="drawer4":
                return [("grab_scissors_d4", "scissors2")]
    return False

def dec_open_meat_bag_knife(agents, self_state, self_name):
    return [("grab_knife",), ("cut_bag_knife",), ("drop_knife",)]

def dec_check_open_meat_bag(agents, self_state, self_name):
    other_holding = self_state.holding[self_state.other_agent_name[self_name]]
    if other_holding!=None:
        if "knife1" in other_holding:
            return []
        if "scissors1" in other_holding:
            return []
        if "scissors2" in other_holding:
            return []
    return [("open_meat_bag",)]

common_methods = [
            ("cook", dec_cook),
            # ("following", dec_prepare_drinks, dec_prepare_meat),
            ("following", dec_prepare_meat),
            ("slice_vegetables", dec_slice_vegetables),
            ("go_away", dec_go_away),
            ("spice_and_cook", dec_spice_and_cook),
            ("cook_meat", dec_cook_meat),
            ("setup_pan", dec_setup_pan),
            # ("clear_spot", dec_clear),
            ("clear_spot", dec_clear_without, dec_clear_with),
            ("prepare_meat", dec_prepare_meat),
            ("get_pan", dec_get_pan_A, dec_get_pan_B),
            ("prepare_drinks", dec_prepare_drinks),
            ("check_open_meat_bag", dec_check_open_meat_bag),
            ("open_meat_bag", dec_open_meat_bag_scissors, dec_open_meat_bag_knife),
            ("get_scissors", dec_get_scissors_d1, dec_get_scissors_d3, dec_get_scissors_d4)
]
ctrl_methods = common_methods + [
            ("cook_vegetables", dec_R_cook_vegetables),
]
unctrl_methods = common_methods + [
            ("cook_vegetables", dec_H_cook_vegetables),
]


######################################################
###################### Triggers ######################
######################################################

def t_drink(agents, self_state, self_name):
    if self_state.glass_filled:
        return [("drink",)]
    return False

def t_pouet(agents, self_state, self_name):
    self_planned_actions = agents[self_name].planned_actions
    other_planned_actions = agents[self_state.other_agent_name[self_name]].planned_actions
    if len(other_planned_actions)>0 and other_planned_actions[-1][0] == "drink" and len(self_planned_actions)>0 and self_planned_actions[-1][0] != "pouet":
        return [("pouet",)]
    return False

def t_burned(agents, self_state, self_name):
    if self_state.human_got_burned and self_state.complain_burned==False:
        self_state.complain_burned=True
        return [("aie",)]
    return False

common_triggers = []
robot_triggers = common_triggers + [t_pouet]
human_triggers = common_triggers + [t_drink, t_burned]


######################################################
################## Helper functions ##################
######################################################

def otherAlreadySettingUpPan(agents, self_state, self_name):
    if len(agents[self_state.other_agent_name[self_name]].agenda)>0:
        next_other_action_name = agents[self_state.other_agent_name[self_name]].agenda[0].name
        if next_other_action_name in ["get_pan", "grab_pan_A", "grab_pan_B", "place_pan", "grab_potholder", "remove_pot"]:
            return True
    return False

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
    initial_state.create_static_prop("self_name", "None")
    initial_state.create_static_prop("other_agent_name", {robot_name:human_name, human_name:robot_name}) 
    initial_state.create_static_prop("objects", {"vegetables":["carrot", "leek"], "storage":{"cupboardA":["shelf1A", "shelf2A"], "cupboardB":["shelf1B", "shelf2B"]}, "scissors":["scissors1", "scissors2"], "knife":["knife1"]})

    # Dynamic properties
    initial_state.create_dynamic_prop("at", {robot_name:"room", human_name:"room", "meat":"table", "pan":"shelf1A", "pot":"hotplate", "scissors1":"drawer1", "scissors2":"drawer4", "knife1":"drawer2"})
    initial_state.create_dynamic_prop("vegetables_state", {})
    for veg in initial_state.objects["vegetables"]:
        initial_state.vegetables_state[veg] = "unsliced"
        initial_state.at[veg] = "table"
    initial_state.create_dynamic_prop("meat_sliced", False)
    initial_state.create_dynamic_prop("pot_fire_on", False)
    initial_state.create_dynamic_prop("pan_fire_on", False)
    initial_state.create_dynamic_prop("salted", False)
    initial_state.create_dynamic_prop("bottle_open", False)
    initial_state.create_dynamic_prop("glass_filled", False)
    initial_state.create_dynamic_prop("holding", {robot_name:None, human_name:None})
    initial_state.create_dynamic_prop("hot", {"pan":False, "pot":False})
    initial_state.create_dynamic_prop("human_got_burned", False)
    initial_state.create_dynamic_prop("complain_burned", False)
    initial_state.create_dynamic_prop("meat_bag_open", False)
    initial_state.create_dynamic_prop("stuff_done_far", False)


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

    hatpehda.add_shared_tasks([("cook",)])
    
    # Starting Agent
    # hatpehda.set_starting_agent(human_name)
    hatpehda.set_starting_agent(robot_name)

def example1_init():
    robot_name = hatpehda.get_robot_name()
    human_name = hatpehda.get_human_name()
    hatpehda.reset_agents_tasks()

    hatpehda.add_shared_tasks([("cook_vegetables",)])

    hatpehda.set_starting_agent(robot_name)

def example2_init():
    robot_name = hatpehda.get_robot_name()
    human_name = hatpehda.get_human_name()
    hatpehda.reset_agents_tasks()

    human_state = hatpehda.get_state(human_name)
    robot_state = hatpehda.get_state(robot_name)

    ## Initial State modifications ##
    robot_state.hot["pot"] = True
    human_state.hot["pot"] = True

    ## False beliefs ##########################
    human_state.hot["pot"] = False          
    human_state.at["pan"] = "shelf2B"       
    ###########################################

    hatpehda.add_tasks(human_name, [("setup_pan",)])

    hatpehda.set_starting_agent(human_name)

def example3_init():
    robot_name = hatpehda.get_robot_name()
    human_name = hatpehda.get_human_name()
    hatpehda.reset_agents_tasks()

    human_state = hatpehda.get_state(human_name)
    robot_state = hatpehda.get_state(robot_name)

    ## Initial state modifications ##
    human_state.vegetables_state["carrot"] = "sliced"
    robot_state.vegetables_state["carrot"] = "sliced"
    human_state.vegetables_state["leek"] = "sliced"
    robot_state.vegetables_state["leek"] = "sliced"
    human_state.at["carrot"] = "pot"
    robot_state.at["carrot"] = "pot"
    human_state.at["leek"] = "pot"
    robot_state.at["leek"] = "pot"
    human_state.hot["pot"] = True
    robot_state.hot["pot"] = True
    human_state.pot_fire_on = True
    robot_state.pot_fire_on = True
    human_state.stuff_done_far = True
    robot_state.stuff_done_far = True
    human_state.salted = True
    robot_state.salted = True

    ## False beliefs ##
    human_state.at["scissors1"] = "far"

    hatpehda.add_tasks(human_name, [("open_meat_bag",)])

    hatpehda.set_starting_agent(human_name)

def example3_bis_init():
    robot_name = hatpehda.get_robot_name()
    human_name = hatpehda.get_human_name()
    hatpehda.reset_agents_tasks()

    human_state = hatpehda.get_state(human_name)
    robot_state = hatpehda.get_state(robot_name)

    ## Initial state modifications ##
    robot_state.at["scissors1"] = "drawer3"
    human_state.at["scissors1"] = "drawer3"
    human_state.vegetables_state["carrot"] = "sliced"
    robot_state.vegetables_state["carrot"] = "sliced"
    human_state.vegetables_state["leek"] = "sliced"
    robot_state.vegetables_state["leek"] = "sliced"
    human_state.at["carrot"] = "pot"
    robot_state.at["carrot"] = "pot"
    human_state.at["leek"] = "pot"
    robot_state.at["leek"] = "pot"
    human_state.hot["pot"] = True
    robot_state.hot["pot"] = True
    human_state.pot_fire_on = True
    robot_state.pot_fire_on = True
    human_state.stuff_done_far = True
    robot_state.stuff_done_far = True
    human_state.salted = True
    robot_state.salted = True

    ## False beliefs ##
    human_state.at["scissors1"] = "far"

    hatpehda.add_tasks(human_name, [("open_meat_bag",)])

    hatpehda.set_starting_agent(human_name)

def example4_shared():
    robot_name = hatpehda.get_robot_name()
    human_name = hatpehda.get_human_name()
    hatpehda.reset_agents_tasks()

    hatpehda.add_shared_tasks([("cook_vegetables",)])
    hatpehda.add_tasks(robot_name, [("open_bottle",), ("fill_glass",)])
    hatpehda.add_tasks(human_name, [("wait",)])

    hatpehda.set_starting_agent(robot_name)

def node_explo():
    robot_name = hatpehda.get_robot_name()
    human_name = hatpehda.get_human_name()

    print("INITIAL STATES")
    hatpehda.show_init()

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

if __name__ == "__main__":

    initDomain()

    # example1_init()
    # example2_init()
    # example3_init()
    # example3_bis_init()
    # example4_shared()

    node_explo()