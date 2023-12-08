#!/usr/bin/env python3
import sys
import os
from copy import deepcopy
import time


import CommonModule as CM
import ConcurrentModule as ConM

import cProfile
import pstats

######################################################
################### Primitive tasks ##################
######################################################

## PP ##
def o_PP_precond(state, agent, color, pick_from, place_to):
    return is_there_reachable_color_cubes_from(pick_from, color, state) and is_target_ready(place_to, state)
def o_PP_shared_resource(state, agent, color, pick_from, place_to):
    return None
    return pick_from
def o_PP_effects(state, agent, color, pick_from, place_to):
    state.color_cubes[color][pick_from] -= 1
    state.locations[place_to] = color
o_PP = CM.Operator("PP", pre_cond=o_PP_precond, effects=o_PP_effects, shared_resource=o_PP_shared_resource)

## open_box ##
def o_open_box_effects(state, agent):
    state.box_state = "open"
    for c in state.color_cubes:
        state.color_cubes[c]["R"] += state.color_cubes[c]["BR"]
        state.color_cubes[c]["BR"] = 0 
o_open_box = CM.Operator("open_box", effects=o_open_box_effects)

## push ##
def o_push_precond(state, agent, color):
    return color=="b" and is_there_reachable_color_cubes_from("H", "b", state)
def o_push_effects(state, agent, color):
    state.color_cubes["b"]["H"] -= 1
    state.color_cubes["b"]["T"] += 1
o_push = CM.Operator("push", pre_cond=o_push_precond, effects=o_push_effects)

common_ops = [o_PP]
robot_ops = common_ops + [o_open_box]
human_ops = common_ops + [o_push]


######################################################
################### Abstract Tasks ###################
######################################################

## Stack ##
def m_Stack_precond(state, agent):
    if agent=="H" and state.robot_opening_box:
        return False
    if agent=="H" and human_only_has_one_cube(state) and is_there_reachable_color_cubes_from("H", "b", state):
        return True
    for l in state.locations:
        if state.locations[l]==None: 
            if is_target_ready(l, state):
                color_needed = state.solution[l]["color"]
                side_name = "R" if agent=="R" else "H"
                if is_there_reachable_color_cubes_from("T", color_needed, state)\
                or is_there_reachable_color_cubes_from(side_name, color_needed, state):
                    return True
                elif agent=="R" and is_there_reachable_color_cubes_from("BR", color_needed, state):
                    return True
    return False
def m_Stack_donecond(state, agent):
    for l in state.locations:
        if state.locations[l]==None: 
            return False
    return True
def m_Stack_multi_decomp(state, agent):
    multi_subtasks = []
    for l in state.locations:
        if state.locations[l]==None: 
            if is_target_ready(l, state):
                color_needed = state.solution[l]["color"]
                if is_there_reachable_color_cubes_from("T", color_needed, state):
                    subtasks = [("PP", color_needed, "T", l), ("Stack",)]
                    multi_subtasks.append(subtasks)
                side_name = "R" if agent=="R" else "H"
                if is_there_reachable_color_cubes_from(side_name, color_needed, state):
                    subtasks = [("PP", color_needed, side_name, l), ("Stack",)]
                    multi_subtasks.append(subtasks)
                if agent=="R" and is_there_reachable_color_cubes_from("BR", color_needed, state):
                    subtasks = [("open_box",), ("Stack",)]
                    multi_subtasks.append(subtasks)
    
    # if agent=="H" and human_only_has_one_cube(state) and is_there_reachable_color_cubes_from("H", "b", state):
    #     subtasks = [("push","b"), ("Stack",)]
    #     multi_subtasks.append(subtasks)
        
    if multi_subtasks==[]:
        multi_subtasks=[[]]

    return multi_subtasks
m_Stack = CM.Method("Stack", pre_cond=m_Stack_precond, done_cond=m_Stack_donecond, multi_decomp=m_Stack_multi_decomp)


common_methods = [("Stack",m_Stack)]
robot_methods = common_methods + []
human_methods = common_methods + []

######################################################
###################### Triggers ######################
######################################################

common_triggers = []
robot_triggers = common_triggers + []
human_triggers = common_triggers + []


######################################################
###################### Helpers #######################
######################################################

def human_only_has_one_cube(state):
    nb_cube = 0
    for color in state.color_cubes:
        nb_cube += state.color_cubes[color]["H"]
    return nb_cube==1

def is_there_reachable_color_cubes_from(pick_from, color, state):
    return state.color_cubes[color][pick_from]>0

def is_target_ready(loc, state):
    on_locs = state.solution[loc]["on"]
    if len(on_locs)==1 and on_locs[0] in ["center", "right"]:
        return True
    else:
        for on_loc in on_locs:
            if state.locations[on_loc]==None:
                return False
        return True

######################################################
######################## MAIN ########################
######################################################

ID_DOMAIN = 1

def initDomain(id_domain = ID_DOMAIN):
    domains = [
    initDomain1,
    initDomain2,
    initDomain3,
    initDomain4,
    ]
    domains[id_domain-1]()

def initDomain1():
    # Set domain name
    domain_name = os.path.basename(__file__)[:-3]
    CM.set_domain_name(domain_name)

    # Initial state
    initial_state = CM.State("init")

    # Static properties
    initial_state.create_static_fluent("self_name", "None")
    initial_state.create_static_fluent("solution", {
        "l1" :{"color":"r", "on":["center"]},
        "l2" :{"color":"y", "on":["center"]},
        "l3" :{"color":"p", "on":["l1","l2"]},
        "l4" :{"color":"w", "on":["l3"]},
        "l5" :{"color":"b", "on":["l3"]},
    })

    # Dynamic properties
    initial_state.create_dyn_fluent("color_cubes", {
        "r": {"R":1, "BR":0, "T":0, "H":0},
        "o": {"R":0, "BR":0, "T":0, "H":0},
        "y": {"R":0, "BR":0, "T":1, "H":0},
        "p": {"R":0, "BR":0, "T":0, "H":1},
        "w": {"R":1, "BR":0, "T":0, "H":0},
        "b": {"R":0, "BR":1, "T":0, "H":1},
        "g": {"R":0, "BR":0, "T":0, "H":0},
    })
    initial_state.create_dyn_fluent("locations", {})
    for l in initial_state.solution:
        initial_state.locations[l] = None
    initial_state.create_dyn_fluent("box_state", "closed")
    initial_state.create_dyn_fluent("robot_opening_box", False)
    CM.set_state(initial_state)

    # Robot init #
    CM.declare_operators("R", robot_ops)
    CM.declare_methods("R", robot_methods)
    # htpa.declare_triggers("R", *robot_triggers)
    CM.add_tasks("R", [("Stack",)])

    # Human init #
    CM.declare_operators("H", human_ops)
    CM.declare_methods("H", human_methods)
    CM.add_tasks("H", [("Stack",)])

    # Starting Agent
    CM.set_starting_agent("R")

def initDomain2():
    # Set domain name
    domain_name = os.path.basename(__file__)[:-3]
    CM.set_domain_name(domain_name)

    # Initial state
    initial_state = CM.State("init")

    # Static properties
    initial_state.create_static_fluent("self_name", "None")
    initial_state.create_static_fluent("solution", {
        "l1" :{"color":"r", "on":["center"]},
        "l2" :{"color":"y", "on":["center"]},
        "l3" :{"color":"g", "on":["l1"]},
        "l4" :{"color":"r", "on":["l2"]},
        "l5" :{"color":"p", "on":["l3","l4"]},
        "l6" :{"color":"w", "on":["l5"]},
        "l7" :{"color":"b", "on":["l5"]},
        "l8" :{"color":"p", "on":["l6","l7"]},
        "l9" :{"color":"r", "on":["l8"]},
    })

    # Dynamic properties
    initial_state.create_dyn_fluent("color_cubes", {
        "r": {"R":2, "BR":0, "T":0, "H":1},
        "o": {"R":0, "BR":0, "T":0, "H":0},
        "y": {"R":0, "BR":0, "T":1, "H":0},
        "p": {"R":1, "BR":0, "T":0, "H":1},
        "w": {"R":0, "BR":0, "T":1, "H":0},
        "b": {"R":0, "BR":1, "T":0, "H":1},
        "g": {"R":0, "BR":0, "T":0, "H":1},
    })
    initial_state.create_dyn_fluent("locations", {})
    for l in initial_state.solution:
        initial_state.locations[l] = None
    initial_state.create_dyn_fluent("box_state", "closed")
    initial_state.create_dyn_fluent("robot_opening_box", False)
    CM.set_state(initial_state)

    # Robot init #
    CM.declare_operators("R", robot_ops)
    CM.declare_methods("R", robot_methods)
    # htpa.declare_triggers("R", *robot_triggers)
    CM.add_tasks("R", [("Stack",)])

    # Human init #
    CM.declare_operators("H", human_ops)
    CM.declare_methods("H", human_methods)
    CM.add_tasks("H", [("Stack",)])

    # Starting Agent
    CM.set_starting_agent("R")

def initDomain3():
    # Set domain name
    domain_name = os.path.basename(__file__)[:-3]
    CM.set_domain_name(domain_name)

    # Initial state
    initial_state = CM.State("init")

    # Static properties
    initial_state.create_static_fluent("self_name", "None")
    initial_state.create_static_fluent("solution", {
        "l1" :{"color":"r", "on":["center"]},
        "l2" :{"color":"y", "on":["center"]},
        "l3" :{"color":"b", "on":["center"]},
        "l4" :{"color":"g", "on":["l1","l2"]},
        "l5" :{"color":"r", "on":["l3"]},
        "l6" :{"color":"r", "on":["l4"]},
        # "l7" :{"color":"g", "on":["l4","l5"]},
        # "l8" :{"color":"r", "on":["l6"]},
        # "l9" :{"color":"r", "on":["l7"]},
        # "l10":{"color":"r", "on":["l7"]},
        # "l11":{"color":"g", "on":["l8","l9"]},
        # "l12":{"color":"r", "on":["l10"]},
        # "l13":{"color":"g", "on":["l11","l12"]},
    })

    # Dynamic properties
    initial_state.create_dyn_fluent("color_cubes", {
        "r": {"R":5, "BR":0, "T":2, "H":5},
        "o": {"R":0, "BR":0, "T":0, "H":0},
        "y": {"R":2, "BR":0, "T":0, "H":0},
        "p": {"R":0, "BR":0, "T":0, "H":0},
        "w": {"R":0, "BR":0, "T":0, "H":0},
        "b": {"R":0, "BR":0, "T":0, "H":1},
        "g": {"R":2, "BR":0, "T":2, "H":2},
    })
    initial_state.create_dyn_fluent("locations", {})
    for l in initial_state.solution:
        initial_state.locations[l] = None
    initial_state.create_dyn_fluent("box_state", "closed")
    initial_state.create_dyn_fluent("robot_opening_box", False)
    CM.set_state(initial_state)

    # Robot init #
    CM.declare_operators("R", robot_ops)
    CM.declare_methods("R", robot_methods)
    # htpa.declare_triggers("R", *robot_triggers)
    CM.add_tasks("R", [("Stack",)])

    # Human init #
    CM.declare_operators("H", human_ops)
    CM.declare_methods("H", human_methods)
    CM.add_tasks("H", [("Stack",)])

    # Starting Agent
    CM.set_starting_agent("R")

def initDomain4():
    # Set domain name
    domain_name = os.path.basename(__file__)[:-3]
    CM.set_domain_name(domain_name)

    # Initial state
    initial_state = CM.State("init")

    # Static properties
    initial_state.create_static_fluent("self_name", "None")
    initial_state.create_static_fluent("solution", {
        "l1" :{"color":"r", "on":["center"]},
        "l2" :{"color":"y", "on":["center"]},
        "l3" :{"color":"b", "on":["center"]},
        "l4" :{"color":"g", "on":["l1","l2"]},
        "l5" :{"color":"r", "on":["l3"]},
        "l6" :{"color":"b", "on":["l4"]},
        "l7" :{"color":"p", "on":["l4","l5"]},
        "l8" :{"color":"r", "on":["l6"]},
    })

    # Dynamic properties
    initial_state.create_dyn_fluent("color_cubes", {
        "r": {"R":2, "BR":0, "T":0, "H":1},
        "o": {"R":0, "BR":0, "T":0, "H":0},
        "y": {"R":1, "BR":0, "T":0, "H":0},
        "p": {"R":0, "BR":1, "T":0, "H":1},
        "w": {"R":0, "BR":0, "T":0, "H":0},
        "b": {"R":1, "BR":0, "T":0, "H":1},
        "g": {"R":0, "BR":0, "T":1, "H":0},
    })
    initial_state.create_dyn_fluent("locations", {})
    for l in initial_state.solution:
        initial_state.locations[l] = None
    initial_state.create_dyn_fluent("box_state", "closed")
    initial_state.create_dyn_fluent("robot_opening_box", False)
    CM.set_state(initial_state)

    # Robot init #
    CM.declare_operators("R", robot_ops)
    CM.declare_methods("R", robot_methods)
    # htpa.declare_triggers("R", *robot_triggers)
    CM.add_tasks("R", [("Stack",)])

    # Human init #
    CM.declare_operators("H", human_ops)
    CM.declare_methods("H", human_methods)
    CM.add_tasks("H", [("Stack",)])

    # Starting Agent
    CM.set_starting_agent("R")

def main( id_domain ):
    sys.setrecursionlimit(100000)
    initDomain(id_domain)
    # pr = cProfile.Profile()
    # pr.enable()


    start = time.time()
    sol = ConM.explore()
    end = time.time()
    print(f"time to explore: \n{end - start}")
    print(f"Number of leaves: {len(sol.get_final_leaves())}")
    print(f"Nb states = {sol.get_nb_states()}")
    
    # pr.disable()
    # stats = pstats.Stats(pr).sort_stats("tottime")
    # stats.dump_stats(filename="profiling.prof")
    return sol

if __name__ == "__main__":
    
    if len(sys.argv)>1:
        sol = main( int(sys.argv[1]) )
    else:
        sol = main(ID_DOMAIN)

    # ConM.show_solution(sol)
    ConM.dumping_solution(sol)