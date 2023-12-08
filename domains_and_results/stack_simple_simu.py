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

## pick ##
def o_pick_precond(state, agent, color, pick_from):
    return is_there_reachable_color_cubes_from(pick_from, color, state)
def o_pick_effects(state, agent, color, pick_from):
    state.color_cubes[color][pick_from] -= 1
o_pick = CM.Operator("pick", pre_cond=o_pick_precond, effects=o_pick_effects)

## place ##
def o_place_precond(state, agent, color, place_to):
    return is_target_ready(place_to, state)
def o_place_effects(state, agent, color, place_to):
    state.locations[place_to] = color
o_place = CM.Operator("place", pre_cond=o_place_precond, effects=o_place_effects)

## push ##
def o_push_precond(state, agent, color):
    return color=="b" and is_there_reachable_color_cubes_from("H", "b", state)
def o_push_effects(state, agent, color):
    state.color_cubes["b"]["H"] -= 1
    state.color_cubes["b"]["T"] += 1
o_push = CM.Operator("push", pre_cond=o_push_precond, effects=o_push_effects)


common_ops = [o_pick, o_place]
robot_ops = common_ops + []
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
    return False
def m_Stack_donecond(state, agent):
    nb_placed = 0
    for l in state.locations:
        if state.locations[l]!=None: 
            nb_placed+=1
        
        if nb_placed>=2:
            return True
    return False
def m_Stack_multi_decomp(state, agent):
    multi_subtasks = []
    for l in state.locations:
        if state.locations[l]==None: 
            if is_target_ready(l, state):
                color_needed = state.solution[l]["color"]
                if is_there_reachable_color_cubes_from("T", color_needed, state):
                    subtasks = [("pick", color_needed, "T"), ("place", color_needed, l), ("Stack",)]
                    multi_subtasks.append(subtasks)
                side_name = "R" if agent=="R" else "H"
                if is_there_reachable_color_cubes_from(side_name, color_needed, state):
                    subtasks = [("pick", color_needed, side_name), ("place", color_needed, l), ("Stack",)]
                    multi_subtasks.append(subtasks)
    
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
    if len(on_locs)==1 and on_locs[0] in state.base_locations:
        return True
    else:
        for on_loc in on_locs:
            if state.locations[on_loc]==None:
                return False
        return True

######################################################
######################## MAIN ########################
######################################################

def initDomain():
    # Set domain name
    domain_name = os.path.basename(__file__)[:-3]
    CM.set_domain_name(domain_name)

    # Initial state
    initial_state = CM.State("init")

    # Static properties
    initial_state.create_static_fluent("self_name", "None")
    initial_state.create_static_fluent("base_locations", ["b1", "b2", "b3", "b4"])
    initial_state.create_static_fluent("solution", {
        "l1" :{"color":"r", "on":["b1"]},
        "l2" :{"color":"g", "on":["b2"]},
        "l3" :{"color":"b", "on":["b3"]},
        "l4" :{"color":"b", "on":["b4"]},
    })

    # Dynamic properties
    initial_state.create_dyn_fluent("color_cubes", {
        "r": {"R":0, "BR":0, "T":1, "H":0},
        "g": {"R":0, "BR":0, "T":1, "H":0},
        "b": {"R":0, "BR":0, "T":1, "H":0},
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

def main( ):
    sys.setrecursionlimit(100000)
    initDomain()
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
    
    sol = main()

    # ConM.show_solution(sol)
    ConM.dumping_solution(sol)