#!/usr/bin/env python3
import sys
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

#####################################################
################### Obs functions ###################
#####################################################

def isObs(state, agent_a, agent_b):
    """ Boolean test, True if action of agent_a can be observed by agent_b, currently always True """
    return True


######################################################
################### Primitive tasks ##################
######################################################

def moveTo(agents, self_state, self_name, loc):
    for ag in agents.values():
        ag.state.at[self_name] = loc

    # print("=== op> {}_moveTo={}".format(self_name[0], loc))
    return agents, 15.0

# moveTo #
def moveToCost(agents, state, agent, loc):
    return 15.0
def moveToPostEff(agents, state, agent, loc):
    state.at[agent] = loc
moveToAg = hatpehda.OperatorAg("moveTo", cost=moveToCost, post_obs_eff=moveToPostEff)

def pick(agents, self_state, self_name, obj):
    if not isReachable(self_state, self_name, obj):
        return False
    if self_state.holding[self_name] != None and self_state.holding[self_name] != []:
        return False
    if obj in self_state.holding[self_state.otherAgent[self_name]]:
        return False

    for ag in agents.values():
        ag.state.holding[self_name].append(obj)
        ag.state.at[obj] = self_name

    # print("=== op> {}_pick={}".format(self_name[0], obj))
    return agents, 1.0

# pick #
def pickPrecond(agents, state, agent, obj):
    if not isReachable(state, agent, obj):
        return False
    if state.holding[agent] != None and state.holding[agent] != []:
        return False
    if obj in state.holding[state.otherAgent[agent]]:
        return False
    return True
def pickPostEff(agents, state, agent, obj):
    state.holding[agent].append(obj)
    state.at[obj] = agent
pickAg = hatpehda.OperatorAg("pick", precond=pickPrecond, post_obs_eff=pickPostEff)

def place(agents, self_state, self_name, obj, loc):
    if self_state.at[self_name] != self_state.locStack[self_name]:
        return False
    if obj not in self_state.holding[self_name]:
        return False

    # Verif ordre stack
    if loc in self_state.locations["bridge"]:
        b1_placed, b2_placed = isBaseBuilt(self_state, self_name)
        if not b1_placed or not b2_placed:
            return False
    if loc == "t1":
        if not isBridgeBuilt(self_state, self_name):
            return False
    if loc == "t2":
        previous_block_ok = False
        for key, val in self_state.at.items():
            if val == "t1":
                previous_block_ok = True
                break
        if not previous_block_ok:
            return False

    # S'il y a deja un objet placé à l'emplacement voulu dans la stack (mais pas de contrainte pour sur la table)
    for key, value in self_state.at.items():
        if value == loc and (loc not in self_state.locations["table"]):
            return False

    # Check if stack_slots has to be updated
    update = False
    if loc in self_state.stack_slots:
        update = True

    for ag in agents.values():
        ag.state.holding[self_name].remove(obj)
        ag.state.at[obj] = loc
        if update:
            ag.state.stack_slots[loc] = obj

    # print("=== op> {}_place obj={} loc={}".format(self_name[0], obj, loc))
    return agents, 1.0

# place #
def placePrecond(agents, state, agent, obj, loc):
    if state.at[agent] != state.locStack[agent]:
        return False
    if obj not in state.holding[agent]:
        return False

    # Verif ordre stack
    if loc in state.locations["bridge"]:
        b1_placed, b2_placed = isBaseBuilt(state, agent)
        if not b1_placed or not b2_placed:
            return False
    if loc == "t1":
        if not isBridgeBuilt(state, agent):
            return False
    if loc == "t2":
        previous_block_ok = False
        for key, val in state.at.items():
            if val == "t1":
                previous_block_ok = True
                break
        if not previous_block_ok:
            return False

    # S'il y a deja un objet placé à l'emplacement voulu dans la stack (mais pas de contrainte pour sur la table)
    for key, value in state.at.items():
        if value == loc and (loc not in state.locations["table"]):
            return False

    return True
def placePostEff(agents, state, agent, obj, loc):
    # Check if stack_slots has to be updated
    update = False
    if loc in state.stack_slots:
        update = True

    state.holding[agent].remove(obj)
    state.at[obj] = loc
    if update:
        state.stack_slots[loc] = obj
placeAg = hatpehda.OperatorAg("place", precond=placePrecond, post_obs_eff=placePostEff)


def wait(agents, sef_state, self_name):
    # print("=== op> {}_wait".format(self_name[0]))
    return agents, 1.0

# wait #
waitAg = hatpehda.OperatorAg("wait")

# first_wait #
def firstWaitAgenda(agents, agendas, state, agent):
    agendas["robot"] = agendas["robot"][:1] + agendas["robot"][4:]
firstWaitAg = hatpehda.OperatorAg("first_wait", agenda_change=firstWaitAgenda)

## ROBOT ##
def r_askPunctualHelp(agents, self_state, self_name, task, obj, loc):
    # print("=== op> {}_askPunctualHelp".format(self_name[0]))

    if len(agents[self_name].agenda) > 3:
        agents[self_name].agenda = agents[self_name].agenda[:3]

    for ag in agents.values():
        ag.state.numberAsk["help"] += 1
        ag.state.asked_punctual = True
        ag.state.params_asked = [task, obj, loc]

    return agents, 5.0 * self_state.numberAsk["help"] * self_state.numberAsk["help"]

# r_askPunctualHelp #
def r_askPunctualHelpCost(agents, state, agent, task, obj, loc):
    return 5.0 * agents["robot"].state.numberAsk["help"] * agents["robot"].state.numberAsk["help"]
def r_askPunctualHelpPostEff(agents, state, agent, task, obj, loc):

    state.numberAsk["help"] += 1
    state.asked_punctual = True
    state.params_asked = [task, obj, loc]
def r_askPunctualHelpAgenda(agents, agendas, state, agent, task, obj, loc):
    agendas["robot"] = agendas["robot"][:1] + agendas["robot"][4:]
r_askPunctualHelpAg = hatpehda.OperatorAg("r_askPunctualHelp", cost=r_askPunctualHelpCost, post_obs_eff=r_askPunctualHelpPostEff, agenda_change=r_askPunctualHelpAgenda)

def r_askSharedGoal(agents, self_state, self_name, task):
    # print("=== op> {}_askSharedGoal".format(self_name[0]))

    if len(agents[self_name].agenda) > 4 :
        agents[self_name].agenda = agents[self_name].agenda[:1] + agents[self_name].agenda[4:]
    else:
        agents[self_name].agenda = agents[self_name].agenda[:1]

    for ag in agents.values():
        ag.state.numberAsk["help"] += 1
        ag.state.asked_shared = True
        ag.state.params_asked = [task]

    return agents, 10.0 * self_state.numberAsk["help"] * self_state.numberAsk["help"]

# r_askSharedGoal #
def r_askSharedGoalCost(agents, state, agent, task):
    return 10.0 * state.numberAsk["help"] * state.numberAsk["help"]
def r_askSharedGoalPostEff(agents, state, agent, task):

    state.numberAsk["help"] += 1
    state.asked_shared = True
    state.params_asked = [task]
def r_askSharedGoalAgenda(agents, agendas, state, agent, task):
    agendas["robot"] = agendas["robot"][3:]
r_askSharedGoalAg = hatpehda.OperatorAg("r_askSharedGoal", cost=r_askSharedGoalCost, post_obs_eff=r_askSharedGoalPostEff, agenda_change=r_askSharedGoalAgenda)


robot_operator_ag = [moveToAg, pickAg, placeAg, waitAg, firstWaitAg, r_askPunctualHelpAg, r_askSharedGoalAg]
human_operator_ag = [moveToAg, pickAg, placeAg, waitAg]

ctrl_operators =    [wait, moveTo, pick, place, r_askPunctualHelp, r_askSharedGoal]
unctrl_operators =  [wait, moveTo, pick, place]


######################################################
################### Abstract Tasks ###################
######################################################

def stack(agents, self_state, self_name):
    i_first_free = isTopBuilt(self_state, self_name)
    br_placed = isBridgeBuilt(self_state, self_name)
    b1_placed, b2_placed = isBaseBuilt(self_state, self_name)
    if i_first_free == -1:
        # print("(1)")
        return []
    elif br_placed:
        # print("(2)")
        return [("buildTop",)]
    elif b1_placed and b2_placed:
        # print("(3)")
        return [("buildBridge",), ("buildTop",)]
    else:
        # print("(4)")
        return [("buildBase",), ("buildBridge",), ("buildTop",)]

def buildBase(agents, self_state, self_name):
    b1_placed, b2_placed = isBaseBuilt(self_state, self_name)
    if b1_placed and b2_placed:
        return []
    elif b1_placed==False and b2_placed==False:
        return [("pickAndPlace", "red", "base"), ("buildBase",)]
    else:
        # If other agent is holding a cube
        if self_state.holding[self_state.otherAgent[self_name]] != []:
            # Get color_pick
            cube = self_state.holding[self_state.otherAgent[self_name]][0]
            color_pick = None
            for key, val in self_state.cubes.items():
                if cube in val:
                    color_pick = key
                    break
            
            # Get color_sol
            if b1_placed==False:
                color_sol = self_state.solution["b1"]
            elif b2_placed==False: # else
                color_sol = self_state.solution["b2"]

            # If the color of the held cube match the solution (infer other agent will stack it)
            if color_pick == color_sol:
                return []
            else:
                return [("pickAndPlace", "red", "base"), ("buildBase",)]
        else:
            return [("pickAndPlace", "red", "base"), ("buildBase",)]       

def buildBridge(agents, self_state, self_name):
    # If already built
    if isBridgeBuilt(self_state, self_name):
        return []
    else:
        # If other agent is holding a cube
        if self_state.holding[self_state.otherAgent[self_name]] != []:
            cube = self_state.holding[self_state.otherAgent[self_name]][0]
            color_pick = None
            for key, val in self_state.cubes.items():
                if cube in val:
                    color_pick = key
                    break
            # If the color of the held cube match the solution (infer other agent will stack it)
            if color_pick == self_state.solution["br"]:
                return []
            else:
                return [("pickAndPlace", "green", "bridge")]
        else:
            return [("pickAndPlace", "green", "bridge")]

def buildTop(agents, self_state, self_name):
    # print("Build_Top {}".format(self_name))
    i_first_free = isTopBuilt(self_state, self_name)

    if i_first_free == -1:
        # print("top built")
        return []
    else:
        i_pick = i_first_free

        # Check if other is holding an object
        cube = self_state.holding[self_state.otherAgent[self_name]]
        if cube != []:
            cube = cube[0]
            # print("other is holding something cube={}".format(cube))
            color_slot = self_state.solution[self_state.locations["top"][i_first_free]]
            color_hold = None
            for key, val in self_state.cubes.items():
                if cube in val:
                    color_hold = key
                    break
            # print("color_hold = {} colord_slot = {}".format(color_hold, color_slot))
            # If other hold right color we pick the next cube
            if color_hold == color_slot:
                # print("other is holding right color")
                # If the other has the last cube of top, task is over
                if i_first_free==len(self_state.locations["top"])-1:
                    # print("but it is the last cube of top so it's over")
                    return []
                # Else we pick the next one
                else:
                    # print("thus we pick the next one")
                    i_pick = i_first_free+1
            
        color_pick = self_state.solution[self_state.locations["top"][i_pick]]
        return [("pickAndPlace", color_pick, "top"), ("buildTop",)]

def pickAndPlace(agents, self_state, self_name, color_obj, loc):
    # print("start {}_pickAndPlace {} {}".format(self_name[0], color_obj, loc))

    # Check if object already defined
    defined = False
    # print("color_obj={}".format(color_obj))
    for key, value in self_state.cubes.items():
        # print("value={}".format(value))
        if color_obj in value:
            defined = True
            # print("defined")
            break

    # Get obj
    if defined:
        obj = color_obj
    else:
        obj = None
        possible_cubes = []
        for cube in self_state.cubes[color_obj]:
            # print("cube={}".format(cube))
            # print("cube at={}".format(self_state.at[cube]))
            if cube not in self_state.holding[self_state.otherAgent[self_name]]:
                if self_state.at[cube] not in self_state.locations["base"] and self_state.at[cube] not in self_state.locations["bridge"] and self_state.at[cube] not in self_state.locations["top"]:
                    possible_cubes.append(cube)

        # print("possible_cubes={}".format(possible_cubes))

        # Compute which cubes are reachable or cubes
        reachable_cubes = []
        only_reachable_cubes = []
        unreachable_cubes = deepcopy(possible_cubes)
        for cube in possible_cubes:
            if isReachable(self_state, self_name, cube):
                reachable_cubes.append(cube)
                unreachable_cubes.remove(cube)
        
        # If some cubes are reachable
        if reachable_cubes != []:
            # Check which are only reachable by the agent, they are prioritized
            for rc in reachable_cubes:
                if self_state.at[rc] == self_state.locStack[self_name]:
                    only_reachable_cubes.append(rc)
            # If some cubes are only reachable by the agent, it is selected
            if only_reachable_cubes != []:
                obj = only_reachable_cubes[0]
            # Else a common cube is selected
            else:
                obj = reachable_cubes[0]
        # None reachable cubes but some are unreachable at the current position, 1rst one is selected
        elif unreachable_cubes != []:
            obj = unreachable_cubes[0]
        # There is no cube to achieve the action, we assume it is done
        else:
            obj = None

        # print("PICK&PLACE {}".format(self_name))
        # print("possible_cubes={} reachable_cubes={} unreachable_cubes={} only_reachable={}".format(possible_cubes, reachable_cubes, unreachable_cubes, only_reachable_cubes))

    # print("getPlace color_obj={} loc={}".format(color_obj, loc))
    # print("getPlace obj={}".format(obj))
    if obj == None:
        # print("done")
        return []

    if self_name == "robot":
        tasks = [("r_checkReachable", "pickAndPlace", obj, loc)]
    else:
        tasks = [("h_checkReachable", "pickAndPlace", obj, loc)]
    tasks = tasks + [("pickCheckNotHeld", obj), ("makeStackReachable",), ("placeUndef", obj,loc)]

    return tasks

def makeStackReachable(agents, self_state, self_name):
    if self_state.at[self_name] == self_state.locStack[self_name]:
        return []
    return [("moveTo", self_state.locStack[self_name])]

def placeUndef(agents, self_state, self_name, obj, loc):

    # print("placeUndef obj={} loc={}".format(obj, loc))

    # Check if already defined
    defined = False
    for key, value in self_state.locations.items():
        if loc in value:
            defined = True

    # Get loc
    if defined:
        loc_found = loc
    else:
        loc_found = None
        for l in self_state.locations[loc]:
            already = False
            for key, value in self_state.at.items():
                if value == l:
                    already = True
                    break
            if already:
                continue
            else:
                loc_found = l
                break
        if loc_found == None:
            return False

    color = None
    for key, val in self_state.cubes.items():
        if obj in val:
            color = key
            break
    if color == None:
        print("ERROR : Color can't be None")
        return False

    if loc_found in self_state.solution and self_state.solution[loc_found] != color:
        return [("wait",), ("placeUndef", obj, loc)]

    return [("place", obj, loc_found)]

def pickCheckNotHeld(agents, self_state, self_name, obj):
    # If already in the other's hands
    if obj in self_state.holding[self_state.otherAgent[self_name]]:
        # We remove the next 2 tasks : makeStackReachable and placeUndef
        # because they are not necessary anymore
        agents[self_name].agenda = agents[self_name].agenda[2:]
        return []
    return [("pick", obj)]

def firstWaitOther(agents, self_state, self_name, task, obj, loc):
    if self_state.shared_goal["shared_goal"] == False:
        return False

    else:
        color = obj
        for key, val in self_state.cubes.items():
            if obj in val:
                color = key
                break

        # print("======> color = {}".format(color))
        if self_state.holding[self_state.otherAgent[self_name]] != [] and self_state.holding[self_state.otherAgent[self_name]][0] in self_state.cubes[color]:
                return []
        else:
            # print("========> wait")
            return [("first_wait",), ("waitOtherPick", task, obj, loc)]

def waitOtherPick(agents, self_state, self_name, task, obj, loc):
    # print("============> waitOtherPick {}".format(obj))
    if self_state.shared_goal["shared_goal"] == False:
        return False

    else:
        color = obj
        for key, val in self_state.cubes.items():
            if obj in val:
                color = key
                break

        # print("======> color = {}".format(color))
        if self_state.holding[self_state.otherAgent[self_name]] != [] and self_state.holding[self_state.otherAgent[self_name]][0] in self_state.cubes[color]:
                return []
        else:
            # print("========> wait")
            return [("wait",), ("waitOtherPick", task, obj, loc)]

def moveToDec(agents, self_state, self_name, task, obj, loc):
    return [("moveTo", self_state.at[obj])]

## ROBOT ##
def r_checkReachable(agents, self_state, self_name, task, obj, loc):
    if obj in self_state.holding[self_state.otherAgent[self_name]]:
        return []
    if isReachable(self_state, self_name, obj):
        return []

    # print("reachable move to ={}".format(self_state.at[obj]))
    return [("r_makeReachable", task, obj, loc)]

def r_involveHuman(agents, self_state, self_name, task, obj, loc):
    if self_state.at[self_state.otherAgent[self_name]] == "far":
        return False

    color = None
    for key, val in self_state.cubes.items():
        if obj in val:
            color = key
            break

    return [("r_involveHuman", task, color, loc)]

def r_askPunctualHelpDec(agents, self_state, self_name, task, obj, loc):
    if self_state.shared_goal["shared_goal"]:
        return False
    # return [("r_askPunctualHelp", task, obj, loc), ("wait",), ("stack",)]
    return [("r_askPunctualHelp", task, obj, loc), ("wait",)]

def r_askSharedGoalDec(agents, self_state, self_name, task, obj, loc):
    if self_state.shared_goal["shared_goal"]:
        return False
    return [("r_askSharedGoal", "stack")]

## HUMAN ##
def h_checkReachable(agents, self_state, self_name, task, obj, loc):
    if obj in self_state.holding[self_state.otherAgent[self_name]]:
        return []
    if isReachable(self_state, self_name, obj):
        return []

    # print("reachable move to ={}".format(self_state.at[obj]))
    return [("h_makeReachable", task, obj, loc)]

@hatpehda.multi_decomposition
def h_punctuallyHelpRobot(agents, self_state, self_name, task, obj, loc):

    # print("help punctual Robot obj={}".format(obj))

    tasks = []

    color = None
    for key, val in self_state.cubes.items():
        if obj in val:
            color = key
            break
    # print("help punctual Robot color={}".format(color))

    for key, val in self_state.solution.items():
        if val == color:
            # Check if not already something there
            for key2, val2 in self_state.at.items():
                if val2 == key :
                    continue
                else:
                    loc = key
                    break
    # print("help punctual Robot loc={}".format(loc))

    tasks.append( [("pickAndPlace", obj, loc)] )
    tasks.append( [("pickAndPlace", obj, "middle")])
    return tasks

ctrl_methods = [("stack", stack),
                ("buildBase", buildBase),
                ("buildBridge", buildBridge),
                ("buildTop", buildTop),
                ("pickAndPlace", pickAndPlace),
                ("r_checkReachable", r_checkReachable),
                ("r_makeReachable", moveToDec, r_involveHuman),
                ("r_involveHuman", r_askSharedGoalDec, r_askPunctualHelpDec, firstWaitOther),
                ("waitOtherPick", waitOtherPick),
                ("makeStackReachable", makeStackReachable),
                ("placeUndef", placeUndef),
                ("pickCheckNotHeld", pickCheckNotHeld)]
unctrl_methods = [("stack", stack),
                ("buildBase", buildBase),
                ("buildBridge", buildBridge),
                ("buildTop", buildTop),
                ("pickAndPlace", pickAndPlace),
                ("h_checkReachable", h_checkReachable),
                ("h_makeReachable", moveToDec, waitOtherPick),
                ("waitOtherPick", waitOtherPick),
                ("makeStackReachable", makeStackReachable),
                ("h_punctuallyHelpRobot", h_punctuallyHelpRobot),
                ("pickCheckNotHeld", pickCheckNotHeld),
                ("placeUndef", placeUndef)]

# ("r_makeReachable", r_involveHuman),

######################################################
###################### Triggers ######################
######################################################

def h_acceptPunctualHelp(agents, state, agent):
    if state.asked_punctual:
        for ag in agents.values():
            ag.state.asked_punctual = False
        task = state.params_asked[0]
        obj = state.params_asked[1]
        loc = state.params_asked[2]
        return [("h_punctuallyHelpRobot", task, obj, loc)]
    return False

def h_acceptSharedGoal(agents, state, agent):
    if state.asked_shared:
        for ag in agents.values():
            ag.state.asked_shared = False
            ag.state.shared_goal["shared_goal"] = True
        task = state.params_asked[0]
        return [(task,)]
    return False

ctrl_triggers = []
unctrl_triggers = [h_acceptPunctualHelp, h_acceptSharedGoal]


######################################################
################## Helper functions ##################
######################################################

def isBaseBuilt(self_state, self_name):

    b1_placed = False
    for key, value in self_state.at.items():
        if value == "b1" and key in self_state.cubes["red"]:
            b1_placed = True

    b2_placed = False
    for key, value in self_state.at.items():
        if value == "b2" and key in self_state.cubes["red"]:
            b2_placed = True

    return b1_placed, b2_placed

def isBridgeBuilt(self_state, self_name):

    br_placed = False
    for key, value in self_state.at.items():
        if value == "br" and key in self_state.cubes["green"]:
            br_placed = True

    return br_placed

def isTopBuilt(self_state, self_name):
    # Find last free slot in top
    i_first_free = -1 # If top built, no free slots
    for i, t in enumerate(self_state.locations["top"]):
        if self_state.stack_slots[t] == "":
            i_first_free = i
            break

    return i_first_free

def isReachable(self_state, self_name, obj):
    loc_obj = self_state.at[obj]
    loc_agent = self_state.at[self_name]

    reachable = False
    if loc_obj in self_state.locations["table"]:
        reachable = loc_obj=="middle" or loc_obj==loc_agent

    # print("isReachable obj={} for={} {}".format(obj, self_name, reachable))

    return reachable


######################################################
######################## MAIN ########################
######################################################

def init_domain(old=False):
    robot_name = "robot"
    human_name = "human"

    # Initial state
    initial_state = hatpehda.State("init")
    initial_state.create_static_prop("selfName", "None")
    initial_state.create_static_prop("otherAgent", {robot_name: human_name, human_name: robot_name})
    initial_state.create_static_prop("locations", {"base":["b1", "b2"], "bridge":["br"], "top":["t1", "t2", "t3", "t4"], "table":["side_r", "side_h", "middle", "side_right"]})
    initial_state.create_static_prop("cubes", {"red":["red1", "red2", "red3"], "green":["green1", "green2"], "blue":["blue1"], "yellow":["yellow1"]})
    initial_state.create_static_prop("solution", {"b1":"red", "b2":"red", "br":"green", "t1":"blue", "t2":"red", "t3":"yellow", "t4":"green"})
    initial_state.create_static_prop("locStack", {robot_name: "side_r", human_name: "side_h"})

    initial_state.create_dynamic_prop("stack_slots", {})
    for l in initial_state.solution:
        initial_state.stack_slots[l] = ""
    initial_state.create_dynamic_prop("at", {robot_name:"side_r",
                                            human_name:"side_h",
                                            "red1":"side_r",
                                            "red2":"side_h",
                                            "red3":"side_h",
                                            "green1":"middle",
                                            "green2":"side_r",
                                            # "green3":"side_h",
                                            "blue1":"side_h",
                                            "yellow1":"middle"})
    initial_state.create_dynamic_prop("holding", {robot_name:[], human_name:[]})
    initial_state.create_dynamic_prop("numberAsk", {"help" : 0})
    initial_state.create_dynamic_prop("shared_goal", {"shared_goal": False})
    initial_state.create_dynamic_prop("asked_punctual", False)
    initial_state.create_dynamic_prop("asked_shared", False)
    initial_state.create_dynamic_prop("params_asked", [])

    # Robot
    hatpehda.declare_operators_ag(robot_name, robot_operator_ag)
    for me in ctrl_methods:
        hatpehda.declare_methods(robot_name, *me)
    hatpehda.declare_triggers(robot_name, *ctrl_triggers)
    hatpehda.set_observable_function("robot", isObs)
    robot_state = deepcopy(initial_state)
    robot_state.__name__ = robot_name + "_init"
    robot_state.selfName = robot_name
    if old:
        hatpehda.set_state_old(robot_name, robot_state)
        hatpehda.add_tasks_old(robot_name, [("stack",)])
    else:
        hatpehda.set_state(robot_name, robot_state)
        hatpehda.add_tasks(robot_name, [("stack",)])

    # Human
    hatpehda.declare_operators_ag(human_name, human_operator_ag)
    for me in unctrl_methods:
        hatpehda.declare_methods(human_name, *me)
    hatpehda.declare_triggers(human_name, *unctrl_triggers)
    hatpehda.set_observable_function("human", isObs)
    human_state = deepcopy(initial_state)
    human_state.__name__ = human_name + "_init"
    human_state.selfName = human_name
    if old:
        hatpehda.set_state_old(human_name, human_state)
        # hatpehda.add_tasks_old(human_name, [("stack",)])
    else:
        hatpehda.set_state(human_name, human_state)
        # hatpehda.add_tasks(human_name, [("stack",)])

    hatpehda.set_robot_name(robot_name)
    hatpehda.set_human_name(human_name)

def old_on_new_plan_req(ctrl_agents, unctrl_agent):
    # SEEK ALL POSSIBLE PLANS #
    sols = []
    fails = []
    print("Start exploring ...")
    start_explore = time.time()
    hatpehda.seek_plan_robot(hatpehda.agents, hatpehda.get_robot_name(), sols, hatpehda.get_human_name(), fails)
    end_explore = time.time()
    print("Done exploration time : {}".format(end_explore-start_explore))
    gui.show_all(sols, hatpehda.get_robot_name(), hatpehda.get_human_name(), with_begin="false", with_abstract="false")
    input()

    # SELECT THE BEST PLAN FROM THE ONES FOUND ABOVE #
    # print("Select plan with costs")
    print("Start selecting a plan ...")
    start_select = time.time()
    best_plan, best_cost, all_branches, all_costs = hatpehda.select_conditional_plan(sols, hatpehda.get_robot_name(), hatpehda.get_human_name())
    end_select = time.time()
    print("Done plan selection time  : {}".format(end_select-start_select))
    for i, cost in enumerate(all_costs):
        print("({}) {}".format(i, cost))
    gui.show_all(hatpehda.get_last_actions(best_plan), hatpehda.get_robot_name(), hatpehda.get_human_name(), with_begin="false", with_abstract="false")
    input()

    # r_node.send_plan(hatpehda.get_last_actions(best_plan), hatpehda.get_robot_name(), human_name)

    print("Start computing causal links ...")
    start_causal = time.time()
    supports, threats = compute_causal_links(hatpehda.agents, best_plan)
    end_causal = time.time()
    print("Done causal links time : {}".format(end_causal-start_causal))
    if len(sys.argv) >= 4 :
        with_begin_p = sys.argv[1].lower()
        with_abstract_p = sys.argv[2].lower()
        causal_links_p = sys.argv[3].lower()
        constraint_causal_edges_p = sys.argv[4].lower() if len(sys.argv) >= 5 else "true"
        gui.show_all(hatpehda.get_last_actions(best_plan), "robot", "human", supports=supports, threats=threats,
            with_begin=with_begin_p, with_abstract=with_abstract_p, causal_links=causal_links_p, constraint_causal_edges=constraint_causal_edges_p)
    else:
        gui.show_all(hatpehda.get_last_actions(best_plan), "robot", "human", supports=supports, threats=threats,
            with_begin="false", with_abstract="false", causal_links="true", constraint_causal_edges="false")
    print("Request done.")

def on_new_plan_req(ctrl_agents, unctrl_agent):

    #########################################
    # FIRST EXPLORATION, FIND BEST SOLUTION #
    #########################################

    # hatpehda.set_debug(True)
    # hatpehda.set_compute_gui(True)
    # hatpehda.set_view_gui(True)
    # hatpehda.set_stop_input(True)
    # hatpehda.set_debug_agenda(True)
    # hatpehda.set_stop_input_agenda(True)

    n_plot = 0
    print("Start first exploration")
    first_explo_dur = time.time()
    first_node, Ns, u_flagged_nodes, n_plot = hatpehda.heuristic_exploration(hatpehda.get_robot_name(), n_plot)
    first_explo_dur = int((time.time() - first_explo_dur)*1000)
    print("\t=> time spent first exploration = {}ms".format(first_explo_dur))
    gui.show_tree(first_node, "sol", view=True)
    gui.show_all(hatpehda.get_last_nodes_action(first_node), hatpehda.get_robot_name(), hatpehda.get_human_name(), with_begin="false", with_abstract="true")
    # gui.show_all([Ns.end_action], hatpehda.get_robot_name(), hatpehda.get_human_name(), with_begin="false", with_abstract="true", render_name="sol_all")
    input()

    ##########################
    # REFINE REMAINING NODES #
    ##########################

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
    gui.show_tree(first_node, "sol", view=True)
    gui.show_all(hatpehda.get_last_nodes_action(first_node), hatpehda.get_robot_name(), hatpehda.get_human_name(), with_begin="false", with_abstract="false")
    # gui.show_all([Ns.end_action], hatpehda.get_robot_name(), hatpehda.get_human_name(), with_begin="false", with_abstract="true", render_name="sol_all")
    input()

    print("Total duration = {}ms".format(first_explo_dur+refine_u_dur))

    return False

if __name__ == "__main__":
    # r_node = ros.RosNode.start_ros_node("planner", on_new_request = on_new_plan_req)
    # print("Waiting for request ...")

    init_domain(old=False)
    on_new_plan_req(None, None)

    # init_domain(old=True)
    # old_on_new_plan_req(None, None)

    # r_node.wait_for_request()

    # PROBLEM
    # hatpehda.add_tasks("robot", [("stack",)])
    # hatpehda.add_tasks("human", [("stack",)])
    # initial_state.at = {"robot":"side_r",
    #                     "human":"side_h",
    #                     "red1":"side_h",
    #                     "red2":"side_h",
    #                     "green1":"side_right",
    #                     "blue1":"middle",
    #                     "yellow1":"middle"}
    # Fix => # Check before in placeUndef ....

    None