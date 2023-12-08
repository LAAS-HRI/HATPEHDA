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
    state.holding[agent] = color
o_pick = CM.Operator("pick", pre_cond=o_pick_precond, effects=o_pick_effects)

## place ##
def o_place_precond(state, agent, color, place_to):
    return is_target_ready(place_to, state)
def o_place_effects(state, agent, color, place_to):
    state.locations[place_to] = color
    state.holding[agent] = None
o_place = CM.Operator("place", pre_cond=o_place_precond, effects=o_place_effects)

## push ##
def o_push_effects(state, agent):
    state.locations["l3"] = state.holding[agent]
    state.holding[agent] = None
o_push = CM.Operator("push", effects=o_push_effects)


common_ops = [o_pick, o_place]
robot_ops = common_ops + [o_push]
human_ops = common_ops + []


######################################################
################### Abstract Tasks ###################
######################################################

#############
#           #
# R  G  B/R #
#           #
#############

## Stack ##
def m_Stack_donecond(state, agent):
    nb_placed = get_nb_placed(state)
    if nb_placed >= 2:
        return True
    if False: # If one placed and other hold a cube
        return True
    return False
def m_Stack_multi_decomp(state, agent):
    multi_subtasks = []
    side_name = "R" if agent=="R" else "H"

    for color in state.color_cubes:
        if is_there_reachable_color_cubes_from(side_name, color, state)\
            or is_there_reachable_color_cubes_from("C", color, state):
            multi_subtasks.append( [ ("Pick", color), ("Place",), ("Stack",)] )

    if multi_subtasks==[]:
        multi_subtasks=[[]]
    return multi_subtasks
m_Stack = CM.Method("Stack", pre_cond=None, done_cond=m_Stack_donecond, multi_decomp=m_Stack_multi_decomp)

## Pick ##
def m_Pick_precond(state, agent, color_needed):
    side_name = "R" if agent=="R" else "H"
    if is_there_reachable_color_cubes_from(side_name, color_needed, state):
        return True
    if is_there_reachable_color_cubes_from("C", color_needed, state):
        return True
    return False
def m_Pick_multi_decomp(state, agent, color_needed):
    multi_subtasks = []

    if is_there_reachable_color_cubes_from("C", color_needed, state):
        subtasks = [("pick", color_needed, "C")]
        multi_subtasks.append(subtasks)
    side_name = "R" if agent=="R" else "H"
    if is_there_reachable_color_cubes_from(side_name, color_needed, state):
        subtasks = [("pick", color_needed, side_name)]
        multi_subtasks.append(subtasks)

    if multi_subtasks==[]:
        multi_subtasks=[[]]
    return multi_subtasks
m_Pick = CM.Method("Pick", pre_cond=m_Pick_precond, done_cond=None, multi_decomp=m_Pick_multi_decomp)

## Place_H ##
def m_Place_H_precond(state, agent):
    if state.holding[agent]==None:
        return False
    color = state.holding[agent]
    targets = get_targets(color, state, agent)
    for t in targets:
        if is_target_ready(t, state):
            return True
    return False
def m_Place_H_multi_decomp(state, agent):
    multi_subtasks = []
    color = state.holding[agent]
    targets = get_targets(color, state, agent)

    for t in targets:
        if is_target_ready(t, state):
            multi_subtasks.append( [("place", color, t)] )

    if multi_subtasks==[]:
        multi_subtasks=[[]]
    return multi_subtasks
m_Place_H = CM.Method("Place", pre_cond=m_Place_H_precond, done_cond=None, multi_decomp=m_Place_H_multi_decomp)

## Place_R ##
def m_Place_R_precond(state, agent):
    if state.holding[agent]==None:
        return False
    color = state.holding[agent]
    targets = get_targets(color, state, agent)
    for t in targets:
        if t=="l3":
            return True
        if is_target_ready(t, state):
            return True
    return False
def m_Place_R_multi_decomp(state, agent):
    multi_subtasks = []
    color = state.holding[agent]
    targets = get_targets(color, state, agent)

    if color=="b" and not is_target_ready("l3", state):
        multi_subtasks.append( [("push",)] )

    for t in targets:
        if is_target_ready(t, state):
            multi_subtasks.append( [("place", color, t)] )

    if multi_subtasks==[]:
        multi_subtasks=[[]]
    return multi_subtasks
m_Place_R = CM.Method("Place", pre_cond=m_Place_R_precond, done_cond=None, multi_decomp=m_Place_R_multi_decomp)


common_methods = [("Stack",m_Stack), ("Pick",m_Pick)]
robot_methods = common_methods + [("Place",m_Place_R)]
human_methods = common_methods + [("Place",m_Place_H)]

######################################################
###################### Triggers ######################
######################################################

common_triggers = []
robot_triggers = common_triggers + []
human_triggers = common_triggers + []


######################################################
###################### Helpers #######################
######################################################

def get_nb_placed(state):
    nb_placed = 0
    for l in state.locations:
        if state.locations[l]!=None:
            nb_placed+=1
    return nb_placed

def human_only_has_one_cube(state):
    nb_cube = 0
    for color in state.color_cubes:
        nb_cube += state.color_cubes[color]["H"]
    return nb_cube==1

def is_there_reachable_color_cubes_from(pick_from, color, state):
    return state.color_cubes[color][pick_from]>0

def is_target_ready(loc, state):
    return state.locations[loc] == None

def get_targets(color, state, agent):
    targets = []

    if color == "r":
        targets.append("l1")
        if agent=="H":
            targets.append("l3")

    if color == "g":
        targets.append("l2")

    if color == "b":
        targets.append("l3")

    return targets


######################################################
################## Goal Condition ####################
######################################################

def goal_condition(state):
    nb_placed = get_nb_placed(state)
    if nb_placed >= 2:
        return True
    return False


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
    initial_state.create_static_fluent("base_locations", ["l1", "l2", "l3"])

    # Dynamic properties
    initial_state.create_dyn_fluent("color_cubes", {
        "r": {"R":0, "C":1, "H":0},
        "g": {"R":0, "C":1, "H":0},
        "b": {"R":0, "C":1, "H":0},
    })
    initial_state.create_dyn_fluent("locations", {})
    for l in initial_state.base_locations:
        initial_state.locations[l] = None
    initial_state.create_dyn_fluent("holding", {"R":None, "H":None})
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