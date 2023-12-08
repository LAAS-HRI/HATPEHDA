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

######################################################
################### Cost functions ###################
######################################################

# None


######################################################
################### Primitive tasks ##################
######################################################

def moveTo(agents, self_state, self_name, loc):
    for ag in agents.values():
        ag.state.at[self_name] = loc

    # print("=== op> {}_moveTo={}".format(self_name[0], loc))
    return agents, 10.0

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

    for ag in agents.values():
        ag.state.holding[self_name].remove(obj)
        ag.state.at[obj] = loc

    # print("=== op> {}_place obj={} loc={}".format(self_name[0], obj, loc))
    return agents, 1.0

def wait(agents, sef_state, self_name):
    # print("=== op> {}_wait".format(self_name[0]))
    return agents, 1.0

## ROBOT ##
def r_askPunctualHelp(agents, self_state, self_name, task, obj, loc):
    # print("=== op> {}_askPunctualHelp".format(self_name[0]))

    if len(agents[self_name].tasks) > 3:
        agents[self_name].tasks = agents[self_name].tasks[:3]

    for ag in agents.values():
        ag.state.numberAsk["help"] += 1

    return agents, 5.0 * self_state.numberAsk["help"] * self_state.numberAsk["help"]

def r_askSharedGoal(agents, self_state, self_name, task):
    # print("=== op> {}_askSharedGoal".format(self_name[0]))

    if len(agents[self_name].tasks) > 4 :
        agents[self_name].tasks = agents[self_name].tasks[:1] + agents[self_name].tasks[4:]
    else:
        agents[self_name].tasks = agents[self_name].tasks[:1]

    for ag in agents.values():
        ag.state.numberAsk["help"] += 1

    return agents, 10.0 * self_state.numberAsk["help"] * self_state.numberAsk["help"]

ctrl_operators =    [wait, moveTo, pick, place, r_askPunctualHelp, r_askSharedGoal]
unctrl_operators =  [wait, moveTo, pick, place]


######################################################
################### Abstract Tasks ###################
######################################################

def stack(agents, self_state, self_name):
    t1_placed, t2_placed = isTopBuilt(self_state, self_name)
    br_placed = isBridgeBuilt(self_state, self_name)
    b1_placed, b2_placed = isBaseBuilt(self_state, self_name)
    if t1_placed and t2_placed:
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
    return [("pickAndPlace", "red", "base"), ("pickAndPlace", "red", "base")]

def buildBridge(agents, self_state, self_name):
    # If already built
    if isBridgeBuilt(self_state, self_name):
        return []
    return [("pickAndPlace", "green", "bridge")]

def buildTop(agents, self_state, self_name):
    return [("pickAndPlace", "blue", "top"), ("pickAndPlace", "yellow", "top")]

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

        for cube in possible_cubes:
            if isReachable(self_state, self_name, cube):
                obj = cube
                break
        # If there are pickable cubes not none reachable from current position
        if obj == None and possible_cubes != []:
            obj = possible_cubes[0]

    # print("getPlace color_obj={} loc={}".format(color_obj, loc))
    # print("getPlace obj={}".format(obj))
    if obj == None:
        # print("done")
        return []

    if self_name == "robot":
        tasks = [("r_checkReachable", "pickAndPlace", obj, loc)]
    else:
        tasks = [("h_makeReachable", obj)]
    tasks = tasks + [("pickCheckNotHeld", obj), ("makeStackReachable",), ("placeUndef", obj,loc)]

    return tasks

def makeStackReachable(agents, self_state, self_name):
    if self_state.at[self_name] == self_state.locStack[self_name]:
        return []
    return [("moveTo", self_state.locStack[self_name])]

def placeUndef(agents, self_state, self_name, obj, loc):

    # print("placeUndef obj={} loc={}".format(obj, loc))

    # Check if object already defined
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

    # # Check before
    # if loc_found == "t1":
    #     bridge_ok = False
    #     for key, value in self_state.at.items():
    #         if value == "br":
    #             bridge_ok = True
    #             break
    #     if bridge_ok:
    #         return [("place", obj, loc_found)]
    #     else:
    #         on_its_way = False
    #         for hold_obj in self_state.holding[self_state.otherAgent[self_name]]:
    #             if hold_obj in self_state.cubes[self_state.solution["br"]]:
    #                 on_its_way = True
    #                 break
    #         if on_its_way:
    #             return [("wait",), ("placeUndef", obj, loc)]
    #         else:
    #             return False

    return [("place", obj, loc_found)]

def pickCheckNotHeld(agents, self_state, self_name, obj):
    # If already in the other's hands
    if obj in self_state.holding[self_state.otherAgent[self_name]]:
        # We remove the next 2 tasks : makeStackReachable and placeUndef
        # because they are not necessary anymore
        agents[self_name].tasks = agents[self_name].tasks[2:]
        return []
    return [("pick", obj)]

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

def r_moveToDec(agents, self_state, self_name, task, obj, loc):
    return [("moveTo", self_state.at[obj])]

def r_askPunctualHelpDec(agents, self_state, self_name, task, obj, loc):
    return [("r_askPunctualHelp", task, obj, loc), ("wait",), ("stack",)]

def r_askSharedGoalDec(agents, self_state, self_name, task, obj, loc):
    return [("r_askSharedGoal", "stack")]

## HUMAN ##
def h_makeReachable(agents, self_state, self_name, obj):
    # print("in h_makeReachable")
    if obj in self_state.holding[self_state.otherAgent[self_name]]:
        return False
    if isReachable(self_state, self_name, obj):
        return []
    # print("reachable move to ={}".format(self_state.at[obj]))
    return [("moveTo", self_state.at[obj])]

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
                ("r_makeReachable", r_moveToDec, r_involveHuman),
                ("r_involveHuman", r_askPunctualHelpDec, r_askSharedGoalDec),
                ("makeStackReachable", makeStackReachable),
                ("placeUndef", placeUndef),
                ("pickCheckNotHeld", pickCheckNotHeld)]
unctrl_methods = [("stack", stack),
                ("buildBase", buildBase),
                ("buildBridge", buildBridge),
                ("buildTop", buildTop),
                ("pickAndPlace", pickAndPlace),
                ("h_makeReachable", h_makeReachable),
                ("makeStackReachable", makeStackReachable),
                ("h_punctuallyHelpRobot", h_punctuallyHelpRobot),
                ("pickCheckNotHeld", pickCheckNotHeld),
                ("placeUndef", placeUndef)]


######################################################
###################### Triggers ######################
######################################################

def h_acceptPunctualHelp(agents, self_state, self_name):
    if agents["robot"].plan[-1].name == "r_askPunctualHelp":
        task = agents["robot"].plan[-1].parameters[0]
        obj = agents["robot"].plan[-1].parameters[1]
        loc = agents["robot"].plan[-1].parameters[2]
        return [("h_punctuallyHelpRobot", task, obj, loc)]
    return False

def h_acceptSharedGoal(agents, self_state, self_name):
    if agents["robot"].plan[-1].name == "r_askSharedGoal":
        task = agents["robot"].plan[-1].parameters[0]
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

    t1_placed = False
    for key, value in self_state.at.items():
        if value == "t1" and key in self_state.cubes["blue"]:
            t1_placed = True

    t2_placed = False
    for key, value in self_state.at.items():
        if value == "t2" and key in self_state.cubes["yellow"]:
            t2_placed = True

    return t1_placed, t2_placed

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

def on_new_plan_req(ctrl_agents, unctrl_agent):
    print("Request received !")
    
    # hatpehda.reset_planner()

    # if len(ctrl_agents.keys()) != 1:
    #     print("Only supports one ctrlable agent")
    #     return
    # if len(unctrl_agent.keys()) != 1:
    #     print("Only supports one unctrlable agent")
    #     return
    # robot_name = list(ctrl_agents.keys())[0]
    # human_name = list(unctrl_agent.keys())[0]
    robot_name = "robot"
    human_name = "human"

    # Initial state
    initial_state = hatpehda.State("init")
    initial_state.locations = {"base":["b1", "b2"], "bridge":["br"], "top":["t1", "t2"], "table":["side_r", "side_h", "middle", "side_right"]}
    initial_state.cubes = {"red":["red1", "red2"], "green":["green1"], "blue":["blue1"], "yellow":["yellow1"]}
    initial_state.otherAgent = {robot_name: human_name, human_name: robot_name}
    initial_state.locStack = {robot_name: "side_r", human_name: "side_h"}
    initial_state.solution = {"b1":"red", "b2":"red", "br":"green", "t1":"blue", "t2":"yellow"}
    initial_state.set_static_props(['locations', 'cubes', 'otherAgent', 'locStack', 'solution'])

    initial_state.at = {robot_name:"side_r",
                        human_name:"side_h",
                        "red1":"side_r",
                        "red2":"side_h",
                        "green1":"middle",
                        "blue1":"side_h",
                        "yellow1":"middle"}
    initial_state.holding = {robot_name:[], human_name:[]}
    initial_state.numberAsk = {"help" : 0}
    initial_state.set_dynamic_props(['at', 'holding', 'numberAsk'])

    # Robot
    hatpehda.declare_operators(robot_name, *ctrl_operators)
    for me in ctrl_methods:
        hatpehda.declare_methods(robot_name, *me)
    hatpehda.declare_triggers(robot_name, *ctrl_triggers)
    robot_state = deepcopy(initial_state)
    robot_state.__name__ = robot_name + "_init"
    hatpehda.set_state(robot_name, robot_state)
    hatpehda.add_tasks(robot_name, [("stack",)])

    # Human
    hatpehda.declare_operators(human_name, *unctrl_operators)
    for me in unctrl_methods:
        hatpehda.declare_methods(human_name, *me)
    hatpehda.declare_triggers(human_name, *unctrl_triggers)
    human_state = deepcopy(initial_state)
    human_state.__name__ = human_name + "_init"
    hatpehda.set_state(human_name, human_state)
    # hatpehda.add_tasks(human_name, [("stack",)])

    # SEEK ALL POSSIBLE PLANS #
    sols = []
    fails = []
    print("Start exploring ...")
    start_explore = time.time()
    hatpehda.seek_plan_robot(hatpehda.agents, robot_name, sols, human_name, fails)
    end_explore = time.time()
    print("Done exploration time : {}".format(end_explore-start_explore))
    gui.show_all(sols, robot_name, human_name, with_begin="false", with_abstract="false")
    input()

    # file = open("dump.dump", "wb")
    # pickle.dump(sols, file)

    # file = open("1_unreach_H_far.txt", "rb")
    # file = open("1_unreach_H_here.txt", "rb")
    # file = open("2_unreach_H_here.txt", "rb")
    # file = open("dump.dump", "rb")
    # sols = pickle.load(file)
    # gui.show_all(sols, "robot", "human", with_begin="false", with_abstract="false", causal_links="without")
    # input()

    # SELECT THE BEST PLAN FROM THE ONES FOUND ABOVE #
    # print("Select plan with costs")
    print("Start selecting a plan ...")
    start_select = time.time()
    best_plan, best_cost, all_branches, all_costs = hatpehda.select_conditional_plan(sols, robot_name, human_name)
    end_select = time.time()
    print("Done plan selection time  : {}".format(end_select-start_select))
    for i, cost in enumerate(all_costs):
        print("({}) {}".format(i, cost))
    gui.show_all(hatpehda.get_last_actions(best_plan), robot_name, human_name, with_begin="false", with_abstract="false")
    input()
    # r_node.send_plan(hatpehda.get_last_actions(best_plan), robot_name, human_name)

    # print("Start computing causal links ...")
    # start_causal = time.time()
    # supports, threats = compute_causal_links(hatpehda.agents, best_plan)
    # end_causal = time.time()
    # print("Done causal links time : {}".format(end_causal-start_causal))
    # if len(sys.argv) >= 4 :
    #     with_begin_p = sys.argv[1].lower()
    #     with_abstract_p = sys.argv[2].lower()
    #     causal_links_p = sys.argv[3].lower()
    #     constraint_causal_edges_p = sys.argv[4].lower() if len(sys.argv) >= 5 else "true"
    #     gui.show_all(hatpehda.get_last_actions(best_plan), "robot", "human", supports=supports, threats=threats,
    #         with_begin=with_begin_p, with_abstract=with_abstract_p, causal_links=causal_links_p, constraint_causal_edges=constraint_causal_edges_p)
    # else:
    #     gui.show_all(hatpehda.get_last_actions(best_plan), "robot", "human", supports=supports, threats=threats,
    #         with_begin="false", with_abstract="false", causal_links="true", constraint_causal_edges="false")
    # print("Request done.")

if __name__ == "__main__":
    # r_node = ros.RosNode.start_ros_node("planner", on_new_request = on_new_plan_req)
    # print("Waiting for request ...")
    on_new_plan_req(None, None)
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
