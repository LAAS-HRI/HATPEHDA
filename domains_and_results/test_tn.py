#!/usr/bin/env python3
import sys
from hatpehda.task_network import TaskNetworkSingle as TNS
from hatpehda.task_network import TaskNetworkUnOrdered as TNU
from hatpehda.task_network import TaskNetworkOrdered as TNO
from hatpehda.task_network import show_tn
import hatpehda as htpa
from copy import deepcopy
import time

r_node = None

######################################################
################### Obs functions ###################
######################################################


######################################################
################### Primitive tasks ##################
######################################################

# pick #
def PickPrecond(agents, state, agent, cube):
    return cube not in state.reachable.val[agent]
def PickDonecond(agents, state, agent, cube):
    return cube in state.holding.val[agent]
def PickEff(agents, state_in, state_out, agent, cube):
    state_out.holding.val[agent].append(cube)
    state_out.at.val[cube] = agent
pickAg = htpa.OperatorAg("pick", precond=PickPrecond, donecond=PickDonecond, effects=PickEff)

# place #
def PlacePrecond(agents, state, agent, cube, place):
    return cube in state.holding.val[agent] and place_empty(state, place) and place_ready(state, place)
def PlaceEff(agents, state_in, state_out, agent, cube, place):
    state_out.holding.val[agent].remove(cube)
    state_out.at.val[cube] = place
placeAg = htpa.OperatorAg("place", precond=PlacePrecond, effects=PlaceEff)

common_ag = [pickAg, placeAg]
robot_operator_ag = common_ag + []
human_operator_ag = common_ag + []


######################################################
################### Abstract Tasks ###################
######################################################

def dec_stack(agents, state, agent):
    # return [("BuildBase",), ("BuildBridge",), ("BuildTop",)]
    return TNO( TNS("BuildBase"), TNS("BuildBridge"), TNS("BuildTop") )


def dec_build_base(agents, state, agent):
    # return [("BuildBaseL1",), ("BuildBaseL2",)]
    return TNU( TNS("BuildBaseL1"), TNS("BuildBaseL2") )

def dec_build_base_r1_l1(agents, state, agent):
    if state.at.val["r1"] == "table":
        # return [("PickPlace", "r1", "l1")]
        return TNS("PickPlace", "r1", "l1")
    return False

def dec_build_base_r2_l1(agents, state, agent):
    if state.at.val["r2"] == "table":
        # return [("PickPlace", "r2", "l1")]
        return TNS("PickPlace", "r2", "l1")
    return False

def dec_build_base_r1_l2(agents, state, agent):
    if state.at.val["r1"] == "table":
        # return [("PickPlace", "r1", "l2")]
        return TNS("PickPlace", "r1", "l2")
    return False

def dec_build_base_r2_l2(agents, state, agent):
    if state.at.val["r2"] == "table":
        # return [("PickPlace", "r2", "l2")]
        return TNS("PickPlace", "r2", "l2")
    return False


def dec_build_base_r1_l1(agents, state, agent):
    if state.at.val["r1"] == "table":
        # return [("PickPlace", "r1", "l1")]
        return TNS("PickPlace", "r1", "l1")
    return False

def dec_build_base_r3_l1(agents, state, agent):
    if state.at.val["r3"] == "table":
        # return [("PickPlace", "r3", "l1")]
        return TNS("PickPlace", "r3", "l1")
    return False

def dec_build_base_r1_l2(agents, state, agent):
    if state.at.val["r1"] == "table":
        # return [("PickPlace", "r1", "l2")]
        return TNS("PickPlace", "r1", "l2")
    return False

def dec_build_base_r3_l2(agents, state, agent):
    if state.at.val["r3"] == "table":
        # return [("PickPlace", "r3", "l2")]
        return TNS("PickPlace", "r3", "l2")
    return False


def dec_build_bridge(agents, state, agent):
    if state.at.val["g1"] == "table":
        # return [("PickPlace", "g1", "l3")]
        return TNS("PickPlace", "g1", "l3")
    return False

def dec_build_top(agents, state, agent):
    if state.at.val["y1"] == "table":
        # return [("PickPlace", "y1", "l4")]
        return TNS("PickPlace", "y1", "l4")
    return False

def dec_pick_place(agents, state, agent, cube, place):
    # return [("pick", cube), ("place", cube, place)]
    return TNO(("pick", cube), ("place", cube, place))

common_methods = [
            ("Stack", dec_stack),
            ("BuildBridge", dec_build_bridge),
            ("BuildTop", dec_build_top),
            ("PickPlace", dec_pick_place),
]
ctrl_methods = common_methods + [
            ("BuildBase", dec_build_base),
            ("BuildBaseL1", dec_build_base_r1_l1, dec_build_base_r2_l1),
            ("BuildBaseL2", dec_build_base_r1_l2, dec_build_base_r2_l2),
]
unctrl_methods = common_methods + [
            ("BuildBase", dec_build_base_r1_l1, dec_build_base_r3_l1, dec_build_base_r1_l2, dec_build_base_r3_l2),
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

def place_empty(state, place):
    for cube in state.cubes.val:
        if state.at.val[cube] == place:
            return False
    return True

def place_ready(state, place):
    if "l1" == place:
        return True
    if "l2" == place:
        return True
    if "l3" == place:
        return not place_empty(state, "l1") and not place_empty(state, "l2")
    if "l4" == place:
        return not place_empty(state, "l3")
    raise Exception("place {} unknown".format(place))

######################################################
######################## MAIN ########################
######################################################

def initDomain():
    robot_name = "robot"
    human_name = "human"
    htpa.set_robot_name(robot_name)
    htpa.set_human_name(human_name)
    htpa.init_other_agent_name()

    # Initial state
    initial_state = htpa.State("init")

    # Static properties
    initial_state.create_fluent("self_name", "None", htpa.ObsType.OBS, "none", False)
    initial_state.create_fluent("other_agent_name", {robot_name:human_name, human_name:robot_name}, htpa.ObsType.OBS, "none", False) 
    initial_state.create_fluent("cubes", ["r1", "r2", "r3", "g1", "y1"], htpa.ObsType.OBS, "none", False)

    # Generate initial state
    n=0

    # Dynamic properties
    initial_state.create_fluent("reachable",  {robot_name:["r1, r2, g1, y1"], human_name:["r1, r3, g1, y1"]},         htpa.ObsType.OBS, "dummy",  True)
    initial_state.create_fluent("holding",    {robot_name:[], human_name:[]},                                         htpa.ObsType.OBS, "dummy",  True)
    initial_state.create_fluent("at",         {"r1":"table", "r2":"table", "r3":"table", "g1":"table", "y1":"table"}, htpa.ObsType.OBS, "dummy",  True)
    initial_state.create_fluent("at_robot", "dummy", htpa.ObsType.OBS, "dummy", True)
    initial_state.create_fluent("at_human", "dummy", htpa.ObsType.OBS, "dummy", True)
    
    # Robot
    htpa.declare_operators_ag(robot_name, robot_operator_ag)
    for me in ctrl_methods:
        htpa.declare_methods(robot_name, *me)
    htpa.declare_triggers(robot_name, *robot_triggers)
    robot_state = deepcopy(initial_state)
    robot_state.self_name.val = robot_name
    robot_state.__name__ = robot_name + "_init"
    htpa.set_state(robot_name, robot_state)
    # htpa.add_tasks(robot_name, [("Stack",)])
    htpa.initTn(robot_name, TNS("Stack"))

    # Human
    htpa.declare_operators_ag(human_name, human_operator_ag)
    for me in unctrl_methods:
        htpa.declare_methods(human_name, *me)
    htpa.declare_triggers(human_name, *human_triggers)
    human_state = deepcopy(initial_state)
    human_state.__name__ = human_name + "_init"
    human_state.reset_fluent_locs()
    human_state.self_name.val = human_name
    htpa.set_state(human_name, human_state)
    # htpa.add_tasks(human_name, [("Stack",)])

    # Starting Agent
    htpa.set_starting_agent(robot_name)

def node_explo(with_contrib, with_graph, with_delay):
    robot_name = htpa.get_robot_name()
    human_name = htpa.get_human_name()

    print("INITIAL STATES")
    htpa.show_init()

    htpa.set_debug(True)
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
    htpa.show_belief_alignmen(first_node)

    # Show final plans
    htpa.show_plans_str(first_node)

    # htpa.show_plans_str_selection(first_node)


    view = True
    if with_graph:
        htpa.gui.show_all(htpa.get_last_nodes_action(first_node), robot_name, human_name, 0, with_contrib, with_delay, with_begin="false", with_abstract="false", view=view)
        # htpa.gui.show_tree(first_node, "sol", view=view)

if __name__ == "__main__":

    # print("TESTING")

    # tn1 = TNS( ("Stack") )
    # tn3 = TNO( TNS("BuildBase"), TNS("BuildBridge"), TNS("BuildTop") )
    # tn2 = TNU( TNS("BuildBaseL1"), TNS("BuildBaseL2") )
    # tn4 = TNO( tn2, TNS("BuildBridge"), TNS("BuildTop") )


    # print(tn3.getFirstTasks())
    # tf = tn3.getFirstTasks()[0]
    # tn3.replaceTaskByTN(tf, tn2)
    # tf = tn3.getFirstTasks()[0]
    # tn3.replaceTaskByTN(tf, TNS("PickPlace", "r1", "l1"))
    # show_tn(tn3)
    # input()

    # first_tasks = tn3.getFirstTasks()
    # last_tasks = tn3.getLastTasks()
    # tn3.removeTask(first_tasks[0])
    # tn3.removeTask(last_tasks[0])
    # show_tn(tn3)

    # exit()

    with_contrib = True
    with_graph = True
    with_delay = False

    initDomain()
    htpa.set_with_contrib(with_contrib)
    htpa.set_with_delay(with_delay)

    node_explo(with_contrib, with_graph, with_delay)