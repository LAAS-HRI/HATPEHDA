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

NB_BALL = 2

######################################################
################### Obs functions ###################
######################################################

def isObs(state, agent_a, agent_b):
    """ Boolean test, True if action of agent_a can be observed by agent_b, currently True if they are in the same room"""
    return get_at(state, agent_a) == get_at(state, agent_b)


######################################################
################### Primitive tasks ##################
######################################################

# add ball #
def AddBallPrecond(agents, state, agent, box):
    return state.nb_bucket.val>0 and box_missing_ball(state, box)
def AddBallEff(agents, state_in, state_out, agent, box):
    state_out.nb_bucket.val-=1
    set_nb_box(state_out, box, get_nb_box(state_in, box)+1)
addBallAg = htpa.OperatorAg("add_ball", precond=AddBallPrecond, effects=AddBallEff)

# add sticker #
def AddStickerPrecond(agents, state, agent, box):
    return box_missing_stick(state, box)
def AddStickerEff(agents, state_in, state_out, agent, box):
    if box=="box1":
        state_out.stick_box1.val = True
    elif box=="box2":
        state_out.stick_box2.val = True
    elif box=="box3":
        state_out.stick_box3.val = True
addStickAg = htpa.OperatorAg("add_sticker", precond=AddStickerPrecond, effects=AddStickerEff)

# send box #
def SendPrecond(agents, state, agent, box):
    return not box_missing_ball(state, box) and not box_missing_stick(state, box)
def SendEff(agents, state_in, state_out, agent, box):
    if box=="box1":
        state_out.box1_sent.val = True
    elif box=="box2":
        state_out.box2_sent.val = True
    elif box=="box3":
        state_out.box3_sent.val = True
sendAg = htpa.OperatorAg("send", precond=SendPrecond, effects=SendEff)

# get more #
def GetMoreEff(agents, state_in, state_out, agent):
    agents.set_fluent_loc("at_"+agent, "place2")
    # agents.set_fluent_loc("at_bucket", "place2")

    set_at(state_out, agent, "place2")
    # state_out.at_bucket.val = "place2"
    # state_out.nb_bucket.val = 10
getMoreAg = htpa.OperatorAg("get_more", effects=GetMoreEff)

# back refill back #
def BackRefillEff(agents, state_in, state_out, agent):
    agents.set_fluent_loc("at_"+agent, "place1")
    # agents.set_fluent_loc("at_bucket", "place1")

    set_at(state_out, agent, "place1")
    # state_out.at_bucket.val = "place1"
    state_out.nb_bucket.val += 10
backRefillBackAg = htpa.OperatorAg("back_refill", effects=BackRefillEff)

common_ag = [addBallAg]
robot_operator_ag = common_ag + [addStickAg]
human_operator_ag = common_ag +  [sendAg, getMoreAg, backRefillBackAg]


######################################################
################### Abstract Tasks ###################
######################################################

# Task #
def dec_task_b1(agents, state, agent):
    if not state.box1_sent.val:
        return [("prepare","box1"),]
    return False
def dec_task_b2(agents, state, agent):
    if state.box1_sent.val and not state.box2_sent.val:
        return [("prepare","box2"),]
    return False
def dec_task_b3(agents, state, agent):
    if state.box1_sent.val and state.box2_sent.val and not state.box3_sent.val:
        return [("prepare","box3"),]
    return False
def dec_task_done(agents, state, agent):
    if state.box1_sent.val and state.box2_sent.val and state.box3_sent.val:
        return []
    return False

# Prepare #
def dec_H_missing_ball(agents, state, agent, box):
    if box_missing_ball(state, box) and state.nb_bucket.val>1:
        return [("add_ball", box), ("task",)]
    return False
def dec_H_need_refill(agents, state, agent, box):
    if state.nb_bucket.val<=1:
        return [("get_more",), ("back_refill",), ("task",)]
    return False
def dec_H_box_done_send(agents, state, agent, box):
    if not box_missing_ball(state, box) and not box_missing_stick(state, box) and bucket_ready(state):
        return [("send", box), ("task",)]
    return False
def dec_R_missing_ball(agents, state, agent, box):
    if box_missing_ball(state, box) and bucket_ready(state):
        return [("add_ball", box), ("task",)]
    return False
def dec_R_missing_sticker(agents, state, agent, box):
    print("s={} b={} b_r={}".format(box_missing_stick(state, box), box_missing_ball(state, box), bucket_ready(state)))
    if box_missing_stick(state, box) and ( (not box_missing_ball(state, box)) or (not bucket_ready(state)) ):
        return [("add_sticker", box), ("task",)]
    return False
def dec_R_next_box(agents, state, agent, box):
    if not box_missing_stick(state, box) and ( (not box_missing_ball(state, box)) or (box_missing_ball(state, box) and not bucket_ready(state)) ):
        if box=="box1":
            return [("prepare", "box2")]
        elif box=="box2":
            return [("prepare", "box3")]
        elif box=="box3":
            return []
    return False

common_methods = [
            ("task", dec_task_b1, dec_task_b2, dec_task_b3, dec_task_done), 
]
ctrl_methods = common_methods + [
            ("prepare", dec_R_missing_ball, dec_R_missing_sticker, dec_R_next_box),
]
unctrl_methods = common_methods + [
            ("prepare", dec_H_missing_ball, dec_H_need_refill, dec_H_box_done_send),
]


######################################################
###################### Triggers ######################
######################################################

def failed(agents, state, agent):
    if state.nb_box1.val>NB_BALL or state.nb_box2.val>NB_BALL or state.nb_box3.val>NB_BALL: 
        raise Exception("{} thinks there is too many balls in a box!".format(agent))
    return False

common_triggers = []
robot_triggers = common_triggers + []
human_triggers = common_triggers + [failed]


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
    else:
        raise Exception("get at {} not in state.at !".format(agent))

def set_at(state, agent, at):
    if agent=="robot":
        state.at_robot.val = at
    elif agent=="human":
        state.at_human.val = at
    else:
        raise Exception("set at {} not in state.at !".format(agent))

def get_nb_box(state, box):
    if box=="box1":
        return state.nb_box1.val
    elif box=="box2":
        return state.nb_box2.val
    elif box=="box3":
        return state.nb_box3.val

def set_nb_box(state, box, nb):
    if box=="box1":
        state.nb_box1.val = nb
    elif box=="box2":
        state.nb_box2.val = nb
    elif box=="box3":
        state.nb_box3.val = nb

def box_done(state, box):
    return not box_missing_ball(state, box) and not box_missing_stick(state, box)

def box_missing_ball(state, box):
    if box=="box1":
        return state.nb_box1.val<NB_BALL
    elif box=="box2":
        return state.nb_box2.val<NB_BALL
    elif box=="box3":
        return state.nb_box3.val<NB_BALL

def box_missing_stick(state, box):
    if box=="box1":
        return state.stick_box1.val==False
    elif box=="box2":
        return state.stick_box2.val==False
    elif box=="box3":
        return state.stick_box3.val==False

def bucket_ready(state):
    return state.at_bucket.val == "place1" and state.nb_bucket.val>0

######################################################
######################## MAIN ########################
######################################################

def initDomain(n):
    robot_name = "robot"
    human_name = "human"
    CM.set_robot_name(robot_name)
    CM.set_human_name(human_name)
    CM.init_other_agent_name()

    # Initial state
    initial_state = htpa.State("init")

    # Generate initial state
    domains = {
        "nb_bucket":        [6, 2],
        "nb_ball":          [2, 3],
        "nb_box1":          [0, 1],
        "nb_box2":          [0, 1],
        "stick_box1":       [False, True],
        "h_stick_box1":     [False, True],
        "h_nb_box1":        [0, 1],
        "h_nb_box2":        [0, 1],
        "starting_agent":   [robot_name, human_name],
    }
    bin_array = get_bin_array(n, max=len(domains))

    values = {}
    for i,f in enumerate(domains):
        values[f] = domains[f][bin_array[i]]

    # Static properties
    initial_state.create_fluent("self_name", "None", htpa.ObsType.OBS, "none", False)
    initial_state.create_fluent("other_agent_name", {robot_name:human_name, human_name:robot_name}, htpa.ObsType.OBS, "none", False) 
    NB_BALL = values["nb_ball"]
    print("NB_BALL=", NB_BALL)

    # Dynamic properties
    initial_state.create_fluent("at_robot",         "place1",               htpa.ObsType.OBS, "place1", True)
    initial_state.create_fluent("at_human",         "place1",               htpa.ObsType.OBS, "place1", True) 
    initial_state.create_fluent("at_bucket",        "place1",               htpa.ObsType.OBS, "place1", True)
    initial_state.create_fluent("nb_bucket",        values["nb_bucket"],    htpa.ObsType.OBS, "place1", True)
    initial_state.create_fluent("nb_box1",          values["nb_box1"],      htpa.ObsType.INF, "place1", True)
    initial_state.create_fluent("nb_box2",          values["nb_box2"],      htpa.ObsType.INF, "place1", True)
    initial_state.create_fluent("nb_box3",          0,                      htpa.ObsType.INF, "place1", True)
    initial_state.create_fluent("stick_box1",       values["stick_box1"],                  htpa.ObsType.OBS, "place1", True)
    initial_state.create_fluent("stick_box2",       False,                  htpa.ObsType.OBS, "place1", True)
    initial_state.create_fluent("stick_box3",       False,                  htpa.ObsType.OBS, "place1", True)
    initial_state.create_fluent("box1_sent",        False,                  htpa.ObsType.OBS, "place1", True)
    initial_state.create_fluent("box2_sent",        False,                  htpa.ObsType.OBS, "place1", True)
    initial_state.create_fluent("box3_sent",        False,                  htpa.ObsType.OBS, "place1", True)

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
    htpa.add_tasks(robot_name, [("task",)])

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
    human_state.nb_box1.val = values["h_nb_box1"] 
    # human_state.nb_box2.val = values["h_nb_box1"] 
    human_state.stick_box1.val = values["h_stick_box1"] 
    # human_state.stick_box2.val = values["h_stick_box2"] 
    htpa.set_state(human_name, human_state)
    htpa.add_tasks(human_name, [("task",)])

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

    print("\n=> Start refining u nodes <=")
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
    # NM.filter_delay_traces(first_node)
    print(NM.get_best_traces(first_node))
    print("best_metrics:")
    print(first_node.best_metrics)


    view = False
    if with_graph:
        gui.show_all(NM.get_last_nodes_action(first_node), robot_name, human_name, n, with_contrib, with_delay, with_begin="false", with_abstract="false", view=view)
        # htpa.gui.show_tree(first_node, "sol", view=view)

if __name__ == "__main__":
    
    # sys.argv = ['/home/afavier/ws/HATPEHDA/domains_and_results/box_prepare.py', 'with_c', 'with_g', 'with_d', 0]

    if len(sys.argv) != 5:
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